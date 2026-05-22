# -*- coding: utf-8 -*-
"""
ftesc/simulator.py — Simulateur de données FT85BD

Génère des données réalistes pour tester l'interface
sans avoir le contrôleur branché.

Simule :
- Deux moteurs indépendants (A et B)
- Variations réalistes (bruit, rampes, défauts)
- Réponse aux commandes (duty, courant)
"""

import math
import random
import time
import threading
from typing import Callable, Optional
from .data import FtescRealtimeData, FtescDualData
from .protocol import UartCommand, build_frame, decompose_u8, decompose_u16, parse_frame


class FtescSimulator:
    """
    Simulateur de contrôleur FT85BD double moteur.
    
    Génère des données temps réel réalistes avec :
    - Variation sinusoïdale + bruit gaussien
    - Réponse aux commandes (duty, courant)
    - Défauts aléatoires (rares)
    - Thermique réaliste (inertie thermique)
    
    Usage :
        sim = FtescSimulator()
        sim.on_data = lambda dual: print(dual)
        sim.start()
        # ... plus tard ...
        sim.stop()
    """
    
    def __init__(self):
        # Callback
        self.on_data: Optional[Callable[[FtescDualData], None]] = None
        
        # État interne
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._start_time = 0.0
        self._tick = 0
        
        # Paramètres moteur A
        self._duty_a = 0.0
        self._target_current_a = 0.0
        
        # Paramètres moteur B
        self._duty_b = 0.0
        self._target_current_b = 0.0
        
        # Thermique (inertie)
        self._temp_fet_a = 35.0
        self._temp_motor_a = 30.0
        self._temp_fet_b = 35.0
        self._temp_motor_b = 30.0

        # Paramètres de simulation (configurable)
        self.noise_level: float = 0.05
        self._battery_voltage: float = 48.0
        self.fault_probability: float = 0.001
        self.update_rate_hz: float = 10.0

        # État périphériques (initialisé pour _handle_command)
        self._headlight_on: bool = False
        self._headlight_intensity: int = 100
        self._brakelight_on: bool = False
        self._brakelight_mode: int = 0
        self._buzzer_active: bool = False
        self._buzzer_stop_time: float = 0.0

        # Callback pour les commandes UART reçues
        self.on_command: Optional[Callable[[UartCommand, bytes], None]] = None

    def handle_frame(self, frame: bytes) -> Optional[bytes]:
        cmd, payload, status = parse_frame(frame)
        if status != 'OK' or cmd is None:
            return None
        return self._handle_command(cmd, payload)

    def _handle_command(self, cmd: UartCommand, payload: bytes) -> Optional[bytes]:
        if cmd == UartCommand.SET_LIGHTS:
            if len(payload) >= 5:
                self._headlight_on = payload[1] != 0
                self._headlight_intensity = max(0, min(100, payload[2]))
                self._brakelight_on = payload[3] != 0
                self._brakelight_mode = payload[4]
            return self._build_ack(cmd)
        elif cmd == UartCommand.SET_BUZZER:
            if len(payload) >= 4:
                dur = (payload[2] << 8) | payload[3]
                self._buzzer_active = True
                self._buzzer_stop_time = time.time() + dur / 1000.0
            return self._build_ack(cmd)
        elif cmd == UartCommand.SET_HEADLIGHT:
            if len(payload) >= 2:
                self._headlight_on = payload[1] != 0
            return self._build_ack(cmd)
        elif cmd == UartCommand.SET_BRAKELIGHT:
            if len(payload) >= 2:
                self._brakelight_on = payload[1] != 0
            return self._build_ack(cmd)
        elif cmd == UartCommand.GET_LIGHTS_STATUS:
            payload = bytes([
                1 if self._headlight_on else 0,
                self._headlight_intensity,
                1 if self._brakelight_on else 0,
                self._brakelight_mode,
                1 if self._buzzer_active else 0,
            ])
            return build_frame(cmd, payload)
        elif cmd == UartCommand.SAVE_EEPROM:
            return self._build_ack(cmd)
        elif cmd == UartCommand.OBTAIN_ALL_FTESC_ID:
            responses = bytearray()
            for esc_id, major, minor, patch, model in [
                (0, 3, 2, 1, 1),
                (1, 3, 2, 1, 1),
            ]:
                payload = bytes([esc_id, major, minor, patch, model])
                responses.extend(build_frame(cmd, payload))
            return bytes(responses)
        elif cmd == UartCommand.OBTAIN_FIRMWARE_VERSION:
            payload = bytes([0, 3, 2, 1, 1])
            return build_frame(cmd, payload)
        return None

    def _build_ack(self, cmd: UartCommand) -> bytes:
        payload = bytes([cmd])
        return build_frame(cmd, payload)

    def start(self):
        """Démarre la simulation."""
        if self._running:
            return
        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Arrête la simulation."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
    
    def set_duty(self, motor: str, duty: float):
        """Définit le rapport cyclique d'un moteur.
        
        Args:
            motor: 'A' ou 'B'
            duty: -1.0 à 1.0 (-100% à +100%)
        """
        duty = max(-1.0, min(1.0, duty))
        if motor.upper() == 'A':
            self._duty_a = duty
        else:
            self._duty_b = duty
    
    def set_current(self, motor: str, current: float):
        """Définit le courant cible d'un moteur."""
        if motor.upper() == 'A':
            self._target_current_a = current
        else:
            self._target_current_b = current
    
    def _generate_motor_data(self, motor: str) -> FtescRealtimeData:
        """Génère des données réalistes pour un moteur."""
        t = time.time() - self._start_time
        
        if motor == 'A':
            duty = self._duty_a
            target_current = self._target_current_a
            temp_fet = self._temp_fet_a
            temp_motor = self._temp_motor_a
        else:
            duty = self._duty_b
            target_current = self._target_current_b
            temp_fet = self._temp_fet_b
            temp_motor = self._temp_motor_b
        
        # Bruit gaussien
        noise = lambda scale=1.0: random.gauss(0, self.noise_level * scale)
        
        # Tension d'entrée (batterie avec légère variation)
        load_drop = abs(duty) * 2.0  # Chute de tension sous charge
        inp_voltage = self._battery_voltage - load_drop + noise(0.5)
        
        # Courant (proportionnel au duty + bruit)
        abs_duty = abs(duty)
        motor_current = target_current * abs_duty + noise(0.5)
        motor_current = max(0.0, motor_current)
        input_current = motor_current * abs_duty * 0.9 + noise(0.3)
        input_current = max(0.0, input_current)
        
        # RPM (proportionnel au duty avec inertie)
        base_rpm = 3000.0 * duty
        rpm_variation = 200.0 * math.sin(t * 0.5)  # Oscillation lente
        rpm = base_rpm + rpm_variation + noise(50.0)
        
        # Thermique (inertie : monte lentement, descend lentement)
        heat_generated = motor_current * 0.3  # Simplification
        cooling = 0.05 * (temp_fet - 25.0)    # Refroidissement naturel
        temp_fet_new = temp_fet + (heat_generated - cooling) * 0.1
        temp_fet_new = max(25.0, min(120.0, temp_fet_new))
        
        temp_motor_new = temp_motor + (heat_generated * 0.5 - cooling * 0.3) * 0.1
        temp_motor_new = max(25.0, min(120.0, temp_motor_new))
        
        # Mise à jour de l'état thermique
        if motor == 'A':
            self._temp_fet_a = temp_fet_new
            self._temp_motor_a = temp_motor_new
        else:
            self._temp_fet_b = temp_fet_new
            self._temp_motor_b = temp_motor_new
        
        # Charge CPU (aléatoire faible)
        cpu_load = 0.1 + 0.05 * math.sin(t * 2.0) + noise(0.02)
        cpu_load = max(0.0, min(1.0, cpu_load))
        
        # Angle encodeur (tourne avec le RPM)
        encoder_angle = (t * abs(rpm) * 0.01) % 360.0
        
        # Défauts (rares)
        fault = 0
        if random.random() < self.fault_probability:
            fault = random.choice([0x01, 0x02, 0x04, 0x08, 0x10])
        
        # Défauts thermiques automatiques
        if temp_fet_new > 90.0:
            fault |= 0x04  # Surtemp FET
        if temp_motor_new > 85.0:
            fault |= 0x08  # Surtemp moteur
        
        return FtescRealtimeData(
            controller_id=0 if motor == 'A' else 1,
            fault=fault,
            inp_voltage=inp_voltage,
            input_current=input_current,
            motor_current=motor_current,
            rpm=rpm,
            duty_cycle_now=duty,
            temp_fet=temp_fet_new,
            temp_motor=temp_motor_new,
            cpu_load=cpu_load,
            encoder_angle=encoder_angle
        )
    
    def _loop(self):
        """Boucle principale de simulation."""
        while self._running:
            # Générer les données des deux moteurs
            data_a = self._generate_motor_data('A')
            data_b = self._generate_motor_data('B')
            
            dual = FtescDualData(
                motor_a=data_a,
                motor_b=data_b,
                timestamp=time.time()
            )
            
            # Envoyer via callback
            if self.on_data:
                self.on_data(dual)
            
            self._tick += 1
            
            # Attendre le prochain tick
            time.sleep(1.0 / self.update_rate_hz)
