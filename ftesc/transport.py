#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 19 13:45:46 2026

@author: wook
"""

"""
ftesc/transport.py — Couche de transport UART/Série pour FFTESC
"""

import serial
import serial.tools.list_ports
import threading
import queue
import time
import logging
from typing import Callable, Optional, List
from dataclasses import dataclass
from enum import Enum

from .protocol import parse_frame, FRAME_HEADER_SHORT, FRAME_HEADER_LONG, FRAME_FOOTER, UartCommand, build_frame


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ftesc.transport')


class ConnectionState(Enum):
    DISCONNECTED = "Déconnecté"
    CONNECTING = "Connexion..."
    CONNECTED = "Connecté"
    ERROR = "Erreur"
    RECONNECTING = "Reconnexion..."


@dataclass
class SerialConfig:
    port: str = "AUTO"
    baudrate: int = 115200
    timeout: float = 1.0
    write_timeout: float = 1.0
    parity: str = 'N'
    stopbits: int = 1
    bytesize: int = 8


class FtescTransport:
    def __init__(self):
        self._serial: Optional[serial.Serial] = None
        self._config = SerialConfig()
        self._state = ConnectionState.DISCONNECTED
        self._read_thread: Optional[threading.Thread] = None
        self._running = False
        self._data_queue: queue.Queue = queue.Queue()
        self._event_queue: queue.Queue = queue.Queue()
        self._response_queue: queue.Queue = queue.Queue()

        self.on_data_received: Optional[Callable[[bytes], None]] = None
        self.on_connection_changed: Optional[Callable[[ConnectionState, str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

        self._rx_buffer = bytearray()
        self._max_buffer_size = 4096

        self._bytes_sent = 0
        self._bytes_received = 0
        self._frames_received = 0
        self._crc_errors = 0

    @staticmethod
    def list_available_ports() -> List[str]:
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    @staticmethod
    def get_port_info(port: str) -> dict:
        for p in serial.tools.list_ports.comports():
            if p.device == port:
                return {
                    'device': p.device,
                    'description': p.description,
                    'hwid': p.hwid,
                    'manufacturer': p.manufacturer,
                    'product': p.product
                }
        return {}

    def connect(self, port="AUTO", baudrate: int = 115200, timeout: float = 1.0) -> bool:
        # Accepte un SerialConfig ou des arguments individuels
        if isinstance(port, SerialConfig):
            cfg      = port
            port     = cfg.port if cfg.port else "AUTO"
            baudrate = cfg.baudrate
            timeout  = cfg.timeout
            self._config = cfg

        if self._state == ConnectionState.CONNECTED:
            logger.warning("Déjà connecté")
            return True

        self._set_state(ConnectionState.CONNECTING, "Ouverture du port...")

        if port == "AUTO":
            available_ports = self.list_available_ports()
            if not available_ports:
                self._set_state(ConnectionState.ERROR, "Aucun port série détecté")
                return False

            for p in available_ports:
                info = self.get_port_info(p)
                if any(keyword in info.get('description', '').lower()
                       for keyword in ['usb', 'serial', 'ftdi', 'cp210x', 'ch340']):
                    port = p
                    logger.info(f"Port détecté automatiquement : {port}")
                    break
            else:
                port = available_ports[0]
                logger.warning(f"Aucun port USB-TTL détecté, utilisant : {port}")

        try:
            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                write_timeout=timeout,
                parity=serial.PARITY_NONE if self._config.parity == 'N' else
                       serial.PARITY_EVEN if self._config.parity == 'E' else
                       serial.PARITY_ODD,
                stopbits=serial.STOPBITS_ONE if self._config.stopbits == 1 else
                         serial.STOPBITS_TWO,
                bytesize=self._config.bytesize
            )

            time.sleep(0.1)
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()

            self._config.port = port
            self._config.baudrate = baudrate
            self._config.timeout = timeout

            self._running = True
            self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._read_thread.start()

            self._set_state(ConnectionState.CONNECTED, f"Connecté à {port}@{baudrate}")
            logger.info(f"Connexion établie : {port} @ {baudrate} bauds")
            return True

        except serial.SerialException as e:
            error_msg = f"Erreur de connexion : {e}"
            logger.error(error_msg)
            self._set_state(ConnectionState.ERROR, error_msg)
            return False
        except Exception as e:
            error_msg = f"Erreur inattendue : {e}"
            logger.error(error_msg)
            self._set_state(ConnectionState.ERROR, error_msg)
            return False

    def disconnect(self) -> bool:
        if self._state == ConnectionState.DISCONNECTED:
            return True

        self._running = False

        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2.0)

        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture : {e}")

        self._serial = None
        self._rx_buffer.clear()
        self._set_state(ConnectionState.DISCONNECTED, "Déconnecté")
        logger.info("Connexion fermée")
        return True

    def reconnect(self) -> bool:
        self.disconnect()
        time.sleep(0.5)
        return self.connect(self._config.port, self._config.baudrate, self._config.timeout)

    def _read_loop(self):
        logger.debug("Thread de lecture démarré")

        while self._running and self._serial and self._serial.is_open:
            try:
                if self._serial.in_waiting > 0:
                    data = self._serial.read(self._serial.in_waiting)
                    self._bytes_received += len(data)

                    self._rx_buffer.extend(data)

                    if len(self._rx_buffer) > self._max_buffer_size:
                        logger.warning("Buffer de réception trop grand, reset")
                        self._rx_buffer.clear()

                    if self.on_data_received:
                        self.on_data_received(bytes(data))

                    self._parse_frames()

                else:
                    time.sleep(0.01)

            except serial.SerialException as e:
                logger.error(f"Erreur de lecture : {e}")
                self._set_state(ConnectionState.ERROR, f"Erreur série : {e}")
                self._running = False
                break

            except Exception as e:
                logger.error(f"Erreur inattendue dans read_loop : {e}")
                self._running = False
                break

        logger.debug("Thread de lecture arrêté")

    def _parse_frames(self):
        processed = False

        while len(self._rx_buffer) >= 6:
            header_pos = -1
            for i in range(len(self._rx_buffer)):
                if self._rx_buffer[i] in (FRAME_HEADER_SHORT, FRAME_HEADER_LONG):
                    header_pos = i
                    break

            if header_pos == -1:
                self._rx_buffer.clear()
                break

            if self._rx_buffer[header_pos] == FRAME_HEADER_SHORT:
                if header_pos + 1 >= len(self._rx_buffer):
                    break
                expected_length = self._rx_buffer[header_pos + 1]
                frame_end = header_pos + 1 + expected_length + 2 + 1
            else:
                if header_pos + 2 >= len(self._rx_buffer):
                    break
                expected_length = (self._rx_buffer[header_pos + 1] << 8) | self._rx_buffer[header_pos + 2]
                frame_end = header_pos + 2 + expected_length + 2 + 1

            if len(self._rx_buffer) < frame_end:
                break

            frame_data = bytes(self._rx_buffer[header_pos:frame_end])

            command, payload, status = parse_frame(frame_data)

            if status == 'OK':
                self._frames_received += 1
                self._response_queue.put((command, payload))
                logger.debug(f"Trame valide reçue : commande={command}, payload={len(payload)} octets")
            else:
                if status == 'CRC_ERROR':
                    self._crc_errors += 1
                    logger.warning(f"Erreur CRC sur une trame")

            del self._rx_buffer[:frame_end]
            processed = True

        if processed and self._rx_buffer:
            pass

    def send(self, data: bytes) -> bool:
        if not self._serial or not self._serial.is_open:
            logger.error("Port non ouvert")
            return False

        try:
            written = self._serial.write(data)
            self._bytes_sent += written
            logger.debug(f"Envoyé {written} octets")
            return written == len(data)
        except serial.SerialException as e:
            logger.error(f"Erreur d'envoi : {e}")
            return False

    def send_command(self, command_bytes: bytes) -> bool:
        return self.send(command_bytes)

    def flush(self):
        if self._serial and self._serial.is_open:
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
            self._rx_buffer.clear()

    def _set_state(self, new_state: ConnectionState, message: str):
        old_state = self._state
        self._state = new_state

        if self.on_connection_changed:
            self.on_connection_changed(new_state, message)

        if new_state == ConnectionState.ERROR and self.on_error:
            self.on_error(message)

        logger.info(f"État : {old_state.value} -> {new_state.value} ({message})")

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def is_connected(self) -> bool:
        return self._state == ConnectionState.CONNECTED

    def get_statistics(self) -> dict:
        return {
            'bytes_sent': self._bytes_sent,
            'bytes_received': self._bytes_received,
            'frames_received': self._frames_received,
            'crc_errors': self._crc_errors,
            'state': self._state.value
        }

    def enter_bootloader(self):
        """Envoie la commande pour redémarrer en mode bootloader."""
        if not self.is_connected:
            raise ConnectionError("Transport not connected")
        frame = build_frame(UartCommand.ENTER_BOOTLOADER, b'')
        self.send(frame)
        # Attendre 2 secondes avant de couper la connexion
        time.sleep(2)
        self.disconnect()

    def check_mcu_health(self):
        """Vérifie l'état du MCU via la commande CHECK_MCU_HEALTH.
        Retourne une chaîne : 'Sain', 'Corrompu', 'Erreur' ou 'Inconnu'.
        """
        if not self.is_connected:
            raise ConnectionError("Transport not connected")
        frame = build_frame(UartCommand.CHECK_MCU_HEALTH, b'')
        self.send(frame)
        # Attendre la réponse (les trames sont traitées dans _read_loop et mises dans _response_queue)
        # Nous allons attendre jusqu'à 2 secondes pour une réponse.
        start_time = time.time()
        timeout = 2.0
        while time.time() - start_time < timeout:
            try:
                # Non-blocking get with timeout of 0.1 to allow checking for timeout
                response = self._response_queue.get(timeout=0.1)
                if response:
                    command, payload = response
                    if command != UartCommand.CHECK_MCU_HEALTH:
                        # Wrong command, ignore and continue waiting
                        continue
                    # Le premier octet de la payload est l'état de santé
                    if len(payload) < 1:
                        continue  # Ignore malformed response
                    health_byte = payload[0]
                    if health_byte == 0:
                        return "Sain"
                    elif health_byte == 1:
                        return "Corrompu"
                    elif health_byte == 2:
                        return "Inconnu"
                    else:
                        return f"Erreur (octet inconnu: {health_byte})"
            except queue.Empty:
                continue
        raise TimeoutError("No response from MCU within timeout")

    def reset_statistics(self):
        self._bytes_sent = 0
        self._bytes_received = 0
        self._frames_received = 0
        self._crc_errors = 0
