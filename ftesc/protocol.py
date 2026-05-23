# -*- coding: utf-8 -*-
"""
ftesc/protocol.py — Coeur du protocole de communication FTESC
"""

import struct
import math
from enum import IntEnum
from typing import Optional
from .data import FtescRealtimeData, FtescFirmwareInfo


# ============================================================
#  COMMANDES UART
# ============================================================

class UartCommand(IntEnum):
    OBTAIN_DATA_ONCE = 0
    CONTROL_AND_OBTAIN_DATA_ONCE = 2
    SET_DUTY = 3
    SET_CURRENT = 4
    SET_CURRENT_GEAR = 5
    SET_BRAKE_CURRENT = 6
    CAN_FWARD = 16
    OBTAIN_FIRMWARE_VERSION = 17
    KEEP_LIVE = 25
    SET_AUTO_OBTAIN_REALTIME_DATA = 26
    RESET_AND_REBOOT_FTESC = 29
    OBTAIN_ALL_FTESC_ID = 30
    SET_CURRENT_GEAR_AND_OBTAIN_DATA = 32
    REBOOT_FTESC = 35
    SET_ID_CURRENT = 37
    SET_POSITION = 38
    SET_SPEED = 39
    READ_CONFIG = 40
    WRITE_CONFIG = 41
    READ_ALL_CONFIG = 42
    WRITE_ALL_CONFIG = 43
    SET_HEADLIGHT = 44
    SET_BRAKELIGHT = 45
    SET_BUZZER = 46
    GET_LIGHTS_STATUS = 48
    SET_LIGHTS = 49
    SAVE_EEPROM = 51
    ENTER_BOOTLOADER = 60
    CHECK_MCU_HEALTH = 61


# ============================================================
#  TABLES CRC16
# ============================================================

_AUC_CRC_HI = (
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40,
)

_AUC_CRC_LO = (
    0x00, 0xC0, 0xC1, 0x01, 0xC3, 0x03, 0x02, 0xC2, 0xC6, 0x06, 0x07, 0xC7,
    0x05, 0xC5, 0xC4, 0x04, 0xCC, 0x0C, 0x0D, 0xCD, 0x0F, 0xCF, 0xCE, 0x0E,
    0x0A, 0xCA, 0xCB, 0x0B, 0xC9, 0x09, 0x08, 0xC8, 0xD8, 0x18, 0x19, 0xD9,
    0x1B, 0xDB, 0xDA, 0x1A, 0x1E, 0xDE, 0xDF, 0x1F, 0xDD, 0x1D, 0x1C, 0xDC,
    0x14, 0xD4, 0xD5, 0x15, 0xD7, 0x17, 0x16, 0xD6, 0xD2, 0x12, 0x13, 0xD3,
    0x11, 0xD1, 0xD0, 0x10, 0xF0, 0x30, 0x31, 0xF1, 0x33, 0xF3, 0xF2, 0x32,
    0x36, 0xF6, 0xF7, 0x37, 0xF5, 0x35, 0x34, 0xF4, 0x3C, 0xFC, 0xFD, 0x3D,
    0xFF, 0x3F, 0x3E, 0xFE, 0xFA, 0x3A, 0x3B, 0xFB, 0x39, 0xF9, 0xF8, 0x38,
    0x28, 0xE8, 0xE9, 0x29, 0xEB, 0x2B, 0x2A, 0xEA, 0xEE, 0x2E, 0x2F, 0xEF,
    0x2D, 0xED, 0xEC, 0x2C, 0xE4, 0x24, 0x25, 0xE5, 0x27, 0xE7, 0xE6, 0x26,
    0x22, 0xE2, 0xE3, 0x23, 0xE1, 0x21, 0x20, 0xE0, 0xA0, 0x60, 0x61, 0xA1,
    0x63, 0xA3, 0xA2, 0x62, 0x66, 0xA6, 0xA7, 0x67, 0xA5, 0x65, 0x64, 0xA4,
    0x6C, 0xAC, 0xAD, 0x6D, 0xAF, 0x6F, 0x6E, 0xAE, 0xAA, 0x6A, 0x6B, 0xAB,
    0x69, 0xA9, 0xA8, 0x68, 0x78, 0xB8, 0xB9, 0x79, 0xBB, 0x7B, 0x7A, 0xBA,
    0xBE, 0x7E, 0x7F, 0xBF, 0x7D, 0xBD, 0xBC, 0x7C, 0xB4, 0x74, 0x75, 0xB5,
    0x77, 0xB7, 0xB6, 0x76, 0x72, 0xB2, 0xB3, 0x73, 0xB1, 0x71, 0x70, 0xB0,
    0x50, 0x90, 0x91, 0x51, 0x93, 0x53, 0x52, 0x92, 0x96, 0x56, 0x57, 0x97,
    0x55, 0x95, 0x94, 0x54, 0x9C, 0x5C, 0x5D, 0x9D, 0x5F, 0x9F, 0x9E, 0x5E,
    0x5A, 0x9A, 0x9B, 0x5B, 0x99, 0x59, 0x58, 0x98, 0x88, 0x48, 0x49, 0x89,
    0x4B, 0x8B, 0x8A, 0x4A, 0x4E, 0x8E, 0x8F, 0x4F, 0x8D, 0x4D, 0x4C, 0x8C,
    0x44, 0x84, 0x85, 0x45, 0x87, 0x47, 0x46, 0x86, 0x82, 0x42, 0x43, 0x83,
    0x41, 0x81, 0x80, 0x40,
)


# ============================================================
#  CRC16
# ============================================================

def crc16_ftesc(buf: bytes) -> int:
    uc_crc_hi = 0xFF
    uc_crc_lo = 0xFF
    for byte in buf:
        i_index = uc_crc_lo ^ byte
        uc_crc_lo = (uc_crc_hi ^ _AUC_CRC_HI[i_index]) & 0xFF
        uc_crc_hi = _AUC_CRC_LO[i_index]
    return (uc_crc_hi << 8) | uc_crc_lo


# ============================================================
#  DECOMPOSITION
# ============================================================

def decompose_u8(value: int) -> bytes:
    return bytes([value & 0xFF])

def decompose_i16(value: int) -> bytes:
    return struct.pack('>h', value)

def decompose_u16(value: int) -> bytes:
    return struct.pack('>H', value)

def decompose_i24(value: int) -> bytes:
    value = value & 0xFFFFFF
    if value & 0x800000:
        value |= 0xFF000000
    return bytes([(value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF])

def decompose_u24(value: int) -> bytes:
    return bytes([(value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF])

def decompose_i32(value: int) -> bytes:
    return struct.pack('>i', value)

def decompose_u32(value: int) -> bytes:
    return struct.pack('>I', value)

def decompose_f16(value: float, multiple: float = 100.0) -> bytes:
    return decompose_i16(int(value * multiple))

def decompose_f32(value: float, multiple: float = 1000000.0) -> bytes:
    return decompose_i32(int(value * multiple))

def decompose_af32(value: float) -> bytes:
    frexpf_t, exp = math.frexp(value)
    frexpf_abs = abs(frexpf_t)
    frexpf_uint = 0
    if frexpf_abs >= 0.5:
        frexpf_uint = int((frexpf_abs - 0.5) * 2.0 * 8388608.0)
        exp += 126
    retval = ((exp & 0xFF) << 23) | (frexpf_uint & 0x7FFFFF)
    if frexpf_t < 0:
        retval |= 1 << 31
    return decompose_u32(retval)


# ============================================================
#  COMPOSITION
# ============================================================

def compose_u8(data: bytes, offset: int = 0) -> tuple:
    return data[offset], offset + 1

def compose_i16(data: bytes, offset: int = 0) -> tuple:
    value = struct.unpack('>h', data[offset:offset+2])[0]
    return value, offset + 2

def compose_u16(data: bytes, offset: int = 0) -> tuple:
    value = struct.unpack('>H', data[offset:offset+2])[0]
    return value, offset + 2

def compose_i24(data: bytes, offset: int = 0) -> tuple:
    b0, b1, b2 = data[offset], data[offset+1], data[offset+2]
    value = (b0 << 16) | (b1 << 8) | b2
    if value & 0x800000:
        value -= 0x1000000
    return value, offset + 3

def compose_u24(data: bytes, offset: int = 0) -> tuple:
    b0, b1, b2 = data[offset], data[offset+1], data[offset+2]
    value = (b0 << 16) | (b1 << 8) | b2
    return value, offset + 3

def compose_i32(data: bytes, offset: int = 0) -> tuple:
    value = struct.unpack('>i', data[offset:offset+4])[0]
    return value, offset + 4

def compose_u32(data: bytes, offset: int = 0) -> tuple:
    value = struct.unpack('>I', data[offset:offset+4])[0]
    return value, offset + 4

def compose_f16(data: bytes, multiple: float = 100.0, offset: int = 0) -> tuple:
    int_value, new_offset = compose_i16(data, offset)
    return int_value / multiple, new_offset

def compose_f32(data: bytes, multiple: float = 1000000.0, offset: int = 0) -> tuple:
    int_value, new_offset = compose_i32(data, offset)
    return int_value / multiple, new_offset

def compose_af32(data: bytes, offset: int = 0) -> tuple:
    retval, new_offset = compose_u32(data, offset)
    exp = (retval >> 23) & 0xFF
    frexpf_uint = retval & 0x7FFFFF
    negative = retval & (1 << 31)
    frexpf_t = 0.0
    if exp != 0 or frexpf_uint != 0:
        frexpf_t = frexpf_uint / (8388608.0 * 2.0) + 0.5
        exp -= 126
    if negative:
        frexpf_t = -frexpf_t
    result = frexpf_t * (2 ** exp)
    return result, new_offset


# ============================================================
#  TRAMES
# ============================================================

FRAME_HEADER_SHORT = 0xAA
FRAME_HEADER_LONG = 0xBB
FRAME_FOOTER = 0xDD


def build_frame(command: UartCommand, payload: bytes) -> bytes:
    full_payload = bytes([command]) + payload
    length = len(full_payload)
    frame = bytearray()
    if length <= 255:
        frame.append(FRAME_HEADER_SHORT)
        frame.append(length)
    else:
        frame.append(FRAME_HEADER_LONG)
        frame.append((length >> 8) & 0xFF)
        frame.append(length & 0xFF)
    frame.extend(full_payload)
    crc = crc16_ftesc(bytes(full_payload))
    frame.append((crc >> 8) & 0xFF)
    frame.append(crc & 0xFF)
    frame.append(FRAME_FOOTER)
    return bytes(frame)


def parse_frame(data: bytes) -> tuple:
    if len(data) < 6:
        return None, b'', 'TOO_SHORT'
    header = data[0]
    if header == FRAME_HEADER_SHORT:
        length = data[1]
        payload_start = 2
    elif header == FRAME_HEADER_LONG:
        length = (data[1] << 8) | data[2]
        payload_start = 3
    else:
        return None, b'', 'INVALID_HEADER'
    payload = data[payload_start:payload_start + length]
    crc_received = (data[payload_start + length] << 8) | data[payload_start + length + 1]
    crc_calculated = crc16_ftesc(payload)
    if crc_calculated != crc_received:
        return None, b'', 'CRC_ERROR'
    footer_index = payload_start + length + 2
    if footer_index >= len(data) or data[footer_index] != FRAME_FOOTER:
        return None, b'', 'INVALID_FOOTER'
    command = UartCommand(payload[0])
    payload_data = payload[1:]
    return command, payload_data, 'OK'


def build_obtain_all_ids_frame() -> bytes:
    return build_frame(UartCommand.OBTAIN_ALL_FTESC_ID, b'')


def build_set_id_frame(new_id: int, current_ma: int = 0) -> bytes:
    """Construit une trame SET_ID_CURRENT (cmd 37).
    
    Payload: [new_id (1B), current_mA (4B, big-endian int32)]
    Si current_ma > 0, seul l'ESC qui détecte ce courant sur ses phases
    change d'ID (permet d'identifier physiquement l'ESC cible sur un bus
    UART partagé). Si current_ma == 0, changement d'ID direct (utilisable
    quand un seul ESC est connecté au bus UART).
    """
    payload = bytes([new_id & 0xFF]) + struct.pack('>i', current_ma)
    return build_frame(UartCommand.SET_ID_CURRENT, payload)


def parse_obtain_all_ids(payload: bytes) -> list[int]:
    """Parse la réponse OBTAIN_ALL_FTESC_ID.
    
    Retourne une liste d'IDs de contrôleurs détectés.
    Chaque ID est un octet: [ctrl_id_0, ctrl_id_1, ...]
    """
    ids = []
    for b in payload:
        ids.append(b)
    return ids


def parse_realtime_data(payload: bytes) -> Optional[FtescRealtimeData]:
    try:
        offset = 0
        controller_id = payload[offset]
        offset += 1
        fault = payload[offset]
        offset += 1
        inp_voltage, offset = compose_f16(payload, 100.0, offset)
        input_current, offset = compose_f32(payload, 1000000.0, offset)
        motor_current, offset = compose_f32(payload, 1000000.0, offset)
        rpm, offset = compose_f32(payload, 1.0, offset)
        duty_cycle_now, offset = compose_f16(payload, 10000.0, offset)
        temp_fet, offset = compose_f16(payload, 100.0, offset)
        temp_motor, offset = compose_f16(payload, 100.0, offset)
        cpu_load, offset = compose_f16(payload, 10000.0, offset)
        encoder_angle, offset = compose_f32(payload, 1000000.0, offset)
        return FtescRealtimeData(
            controller_id=controller_id,
            fault=fault,
            inp_voltage=inp_voltage,
            input_current=input_current,
            motor_current=motor_current,
            rpm=rpm,
            duty_cycle_now=duty_cycle_now,
            temp_fet=temp_fet,
            temp_motor=temp_motor,
            cpu_load=cpu_load,
            encoder_angle=encoder_angle
        )
    except (IndexError, ValueError) as e:
        print(f"Erreur de decodage : {e}")
        return None


def parse_firmware_info(payload: bytes) -> Optional[FtescFirmwareInfo]:
    try:
        # Expected format: [controller_id, version_major, version_minor, version_patch, model_type] (5 bytes)
        if len(payload) < 5:
            print(f"⚠️ parse_firmware_info: payload trop court ({len(payload)} octets) : {payload.hex()}")
            return None
        offset = 0
        controller_id = payload[offset]; offset += 1
        version_major = payload[offset]; offset += 1
        version_minor = payload[offset]; offset += 1
        version_patch = payload[offset]; offset += 1
        model_type = payload[offset]; offset += 1
        return FtescFirmwareInfo(
            controller_id=controller_id,
            version_major=version_major,
            version_minor=version_minor,
            version_patch=version_patch,
            model_type=model_type,
        )
    except (IndexError, ValueError, TypeError) as e:
        print(f"⚠️ Erreur parse_firmware_info: {e} (payload: {len(payload)} octets, hex: {payload.hex()})")
        return None
