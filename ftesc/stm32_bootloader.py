"""
ftesc/stm32_bootloader.py — STM32 System Bootloader Protocol Client

Implements the STM32 USART bootloader protocol for flashing firmware
to FT85BD ESC after entering bootloader mode via ENTER_BOOTLOADER (cmd 60).

Protocol reference: AN2606 (STM32 microcontroller system memory boot mode)
"""

import time, struct, serial
from typing import Optional


# STM32 bootloader commands
CMD_GET      = 0x00  # Get bootloader version + supported commands
CMD_GET_ID   = 0x02  # Get chip ID
CMD_READ     = 0x11  # Read memory
CMD_GO       = 0x21  # Jump to address
CMD_WRITE    = 0x31  # Write memory
CMD_ERASE    = 0x43  # Extended erase (0xFF 0xFF 0x00 = erase all)
CMD_WRITE_NOCRC = 0x44  # Write without CRC

ACK  = 0x79
NACK = 0x1F


class Stm32BootloaderError(Exception):
    pass


class Stm32Bootloader:
    def __init__(self, port: str, baud: int = 115200, timeout: float = 2.0):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._ser: Optional[serial.Serial] = None

    def connect(self):
        self._ser = serial.Serial(
            port=self.port,
            baudrate=self.baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
        )
        time.sleep(0.1)
        self._ser.reset_input_buffer()

    def disconnect(self):
        if self._ser and self._ser.is_open:
            self._ser.close()

    def _send_byte(self, b: int):
        self._ser.write(bytes([b]))

    def _send_cmd(self, cmd: int):
        self._send_byte(cmd)
        self._send_byte(cmd ^ 0xFF)  # XOR check byte

    def _read_response(self) -> bytes:
        resp = self._ser.read(1)
        if not resp:
            raise Stm32BootloaderError("No response from bootloader")
        return resp

    def _expect_ack(self):
        resp = self._read_response()
        if resp[0] == NACK:
            raise Stm32BootloaderError("NACK received")
        if resp[0] != ACK:
            raise Stm32BootloaderError(f"Unexpected byte: 0x{resp[0]:02x}")

    def sync(self):
        """Send sync byte 0x7F and expect ACK."""
        self._send_byte(0x7F)
        resp = self._ser.read(1)
        if not resp:
            raise Stm32BootloaderError("No sync response")
        if resp[0] == ACK:
            return
        raise Stm32BootloaderError(f"Sync failed, got 0x{resp[0]:02x}")

    def get_version(self):
        """Get bootloader version and supported commands."""
        self._send_cmd(CMD_GET)
        self._expect_ack()
        # Version byte + supported commands count + commands
        data = self._ser.read(1)
        if not data:
            raise Stm32BootloaderError("No version response")
        version = data[0]
        n_cmds = self._ser.read(1)[0]
        cmds = self._ser.read(n_cmds + 1)
        self._expect_ack()
        return version, list(cmds)

    def get_id(self):
        """Get chip identification."""
        self._send_cmd(CMD_GET_ID)
        self._expect_ack()
        n_bytes = self._ser.read(1)[0]
        pid = self._ser.read(n_bytes + 1)
        self._expect_ack()
        return pid

    def extended_erase_all(self):
        """Erase all flash pages (extended erase)."""
        self._send_cmd(CMD_ERASE)
        self._expect_ack()
        self._send_byte(0xFF)  # Global erase (all pages)
        self._send_byte(0xFF)
        self._send_byte(0x00)
        self._expect_ack()

    def extended_erase_sectors(self, sectors: list):
        """Erase specific flash sectors (extended erase).
        
        For STM32F405: sector 4 = 0x08010000 (64KB app firmware).
        """
        n = len(sectors) - 1
        payload = bytes([n])
        for s in sectors:
            payload += struct.pack('>H', s)
        xor = 0
        for b in payload:
            xor ^= b
        payload += bytes([xor])
        self._send_cmd(CMD_ERASE)
        self._expect_ack()
        self._ser.write(payload)
        self._expect_ack()

    def write_memory(self, address: int, data: bytes):
        """Write data to flash memory at given address."""
        # Max payload per write is 256 bytes (including checksum)
        chunk_size = 256
        offset = 0
        while offset < len(data):
            chunk = data[offset:offset + chunk_size]
            self._write_chunk(address + offset, chunk)
            offset += len(chunk)

    def _write_chunk(self, address: int, data: bytes):
        n = len(data) - 1  # N = number of bytes - 1
        payload = struct.pack('>I', address) + bytes([n]) + data
        checksum = 0
        for b in payload:
            checksum ^= b
        payload += bytes([checksum])

        self._send_cmd(CMD_WRITE)
        self._expect_ack()
        self._ser.write(payload)
        self._expect_ack()

    def go(self, address: int):
        """Jump to given address to execute code."""
        payload = struct.pack('>I', address)
        checksum = 0
        for b in payload:
            checksum ^= b
        payload += bytes([checksum])
        self._send_cmd(CMD_GO)
        self._expect_ack()
        self._ser.write(payload)
        self._expect_ack()

    def flash_firmware_bin(self, firmware_path: str, flash_addr: int = 0x08010000,
                           erase_sectors: list = None):
        """Flash a .bin firmware file to the ESC.
        
        For FT85BD (STM32F405): firmware goes at 0x08010000 (sector 4, 64KB).
        Bootloader in sectors 0-3 (0x08000000-0x0800FFFF) is preserved.
        
        Args:
            firmware_path: Path to .bin firmware file
            flash_addr: Flash address to write firmware (default: 0x08010000)
            erase_sectors: List of sector numbers to erase. Default: [4] (STM32F405)
        """
        if erase_sectors is None:
            erase_sectors = [4]  # sector 4 = 0x08010000, 64KB on STM32F405
        with open(firmware_path, 'rb') as f:
            firmware = f.read()
        print(f"Firmware size: {len(firmware)} bytes")
        print(f"Flash address: 0x{flash_addr:08X}")
        print(f"Erasing sectors {erase_sectors}...")
        self.extended_erase_sectors(erase_sectors)
        print("Erase complete. Writing firmware...")
        self.write_memory(flash_addr, firmware)
        print("Write complete!")
