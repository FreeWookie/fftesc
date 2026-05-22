# -*- coding: utf-8 -*-
"""
ftesc/config_protocol.py — Serialization des configurations moteur vers/depuis UART.
"""

from typing import Callable
from .data import (
    MotorConfig, HallConfig, FOCConfig, LimitsConfig, RampConfig,
    BrakeConfig, InputControlConfig, SpeedPIDConfig,
    BatteryConfig, DualSetupConfig, IMUConfig, CANConfig, PeripheralConfig,
    DualMotorConfig,
    MotorType, SensorlessMode, FOCMode, ControlType, ControlCommand,
    BatteryType, DualMode, IMUType, CANMode, CANBaudrate,
)
from .protocol import (
    UartCommand, build_frame, parse_frame,
    decompose_u8, decompose_u16, decompose_u32, decompose_i32,
    decompose_f16, decompose_f32,
    compose_u8, compose_u16, compose_u32, compose_i32,
    compose_f16, compose_f32,
)


CTRL_MOTOR_A = 0
CTRL_MOTOR_B = 1
CTRL_GLOBAL = 2

SEC_MOTOR = 0
SEC_HALL = 1
SEC_FOC = 2
SEC_LIMITS = 3
SEC_RAMP = 4
SEC_BRAKE = 5
SEC_INPUT_CTRL = 6
SEC_SPEED_PID = 7
SEC_BATTERY = 8
SEC_DUAL = 9
SEC_IMU = 10
SEC_CAN = 11
SEC_PERIPHERALS = 13
SEC_ALL = 255


class Field:
    __slots__ = ('key', 'enc', 'dec', 'eargs', 'dargs')
    def __init__(self, key: str, enc: Callable, dec: Callable, eargs=(), dargs=()):
        self.key = key
        self.enc = enc
        self.dec = dec
        self.eargs = eargs
        self.dargs = dargs


def _enc_bool(v: bool) -> bytes:
    return bytes([1 if v else 0])

def _dec_bool(data: bytes, off: int) -> tuple:
    return data[off] != 0, off + 1

def _enc_u8(v: int) -> bytes:
    return decompose_u8(v)

def _dec_u8(data: bytes, off: int) -> tuple:
    return data[off], off + 1

def _enc_u16(v: int) -> bytes:
    return decompose_u16(v)

def _dec_u16(data: bytes, off: int) -> tuple:
    return compose_u16(data, off)

def _enc_u32(v: int) -> bytes:
    return decompose_u32(v)

def _dec_u32(data: bytes, off: int) -> tuple:
    return compose_u32(data, off)

def _enc_i32(v: int) -> bytes:
    return decompose_i32(v)

def _dec_i32(data: bytes, off: int) -> tuple:
    return compose_i32(data, off)

def _enc_f16(v: float, m: float = 100.0) -> bytes:
    return decompose_f16(v, m)

def _dec_f16(data: bytes, off: int, m: float = 100.0) -> tuple:
    return compose_f16(data, m, off)

def _enc_f32(v: float, m: float = 1000000.0) -> bytes:
    return decompose_f32(v, m)

def _dec_f32(data: bytes, off: int, m: float = 1000000.0) -> tuple:
    return compose_f32(data, m, off)

def _enc_curve(v: list) -> bytes:
    buf = b''
    for x in v:
        buf += decompose_f32(x, 1000000.0)
    return buf

def _dec_curve(data: bytes, off: int, n: int = 6) -> tuple:
    vals = []
    for _ in range(n):
        v, off = compose_f32(data, 1000000.0, off)
        vals.append(v)
    return vals, off

def _enc_hall_table(v: list) -> bytes:
    return bytes(v)

def _dec_hall_table(data: bytes, off: int) -> tuple:
    return list(data[off:off+8]), off + 8


HALL_FIELDS = [
    Field("enabled", _enc_bool, _dec_bool),
    Field("hall_table", _enc_hall_table, _dec_hall_table),
    Field("direction", _enc_bool, _dec_bool),
    Field("interpolation", _enc_bool, _dec_bool),
    Field("sensorless_mode", lambda v: _enc_u8(list(SensorlessMode).index(v)),
          lambda d, o: (list(SensorlessMode)[d[o]], o + 1)),
    Field("sensorless_erpm", lambda v: _enc_f32(v, 1.0), lambda d, o: _dec_f32(d, o, 1.0)),
    Field("sensorless_erpm_start", lambda v: _enc_f32(v, 1.0), lambda d, o: _dec_f32(d, o, 1.0)),
]

FOC_FIELDS = [
    Field("mode", lambda v: _enc_u8(v.value),
          lambda d, o: (FOCMode(d[o]), o + 1)),
    Field("current_kp", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("current_ki", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("fsw", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("dead_time", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("openloop_rpm", lambda v: _enc_f32(v, 1.0), lambda d, o: _dec_f32(d, o, 1.0)),
    Field("openloop_lock", _enc_bool, _dec_bool),
    Field("observer_gain", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("observer_gain_slow", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("pll_kp", lambda v: _enc_f32(v, 1.0), lambda d, o: _dec_f32(d, o, 1.0)),
    Field("pll_ki", lambda v: _enc_f32(v, 1.0), lambda d, o: _dec_f32(d, o, 1.0)),
    Field("antiwindup", lambda v: _enc_f16(v, 10000.0), lambda d, o: _dec_f16(d, o, 10000.0)),
    Field("duty_kp", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("duty_ki", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("sat_comp", _enc_bool, _dec_bool),
]

LIMITS_FIELDS = [
    Field("max_erpm", lambda v: _enc_f32(v, 1.0), lambda d, o: _dec_f32(d, o, 1.0)),
    Field("max_erpm_reverse", lambda v: _enc_f32(v, 1.0), lambda d, o: _dec_f32(d, o, 1.0)),
    Field("max_duty", lambda v: _enc_f16(v, 10000.0), lambda d, o: _dec_f16(d, o, 10000.0)),
    Field("min_duty", lambda v: _enc_f16(v, 10000.0), lambda d, o: _dec_f16(d, o, 10000.0)),
    Field("max_input_voltage", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("min_input_voltage", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("max_battery_current", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("max_battery_current_rev", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("max_motor_current", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("max_motor_current_rev", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("max_absolute_current", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("temp_fet_max", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("temp_fet_start", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("slow_abs_overvoltage", _enc_bool, _dec_bool),
    Field("slow_abs_undervoltage", _enc_bool, _dec_bool),
]

RAMP_FIELDS = [
    Field("ramp_up_time", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("ramp_down_time", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("startup_speed", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("cool_down_time", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("acceleration_current", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("deceleration_current", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
]

BRAKE_FIELDS = [
    Field("brake_current", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("brake_current_ramp", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("regen_braking", _enc_bool, _dec_bool),
    Field("regen_voltage_max", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("brake_temperature_limit", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
]

INPUT_CTRL_FIELDS = [
    Field("control_type", lambda v: _enc_u8(list(ControlType).index(v)),
          lambda d, o: (list(ControlType)[d[o]], o + 1)),
    Field("input_voltage_min", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("input_voltage_max", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("throttle_curve", _enc_curve, lambda d, o: _dec_curve(d, o, 6)),
    Field("brake_curve", _enc_curve, lambda d, o: _dec_curve(d, o, 6)),
    Field("throttle_center", lambda v: _enc_f16(v, 10000.0), lambda d, o: _dec_f16(d, o, 10000.0)),
    Field("throttle_deadband", lambda v: _enc_f16(v, 10000.0), lambda d, o: _dec_f16(d, o, 10000.0)),
    Field("control_deadband", lambda v: _enc_f16(v, 10000.0), lambda d, o: _dec_f16(d, o, 10000.0)),
    Field("control_command", lambda v: _enc_u8(list(ControlCommand).index(v)),
          lambda d, o: (list(ControlCommand)[d[o]], o + 1)),
    Field("ppm_pulse_min", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("ppm_pulse_max", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("ppm_pulse_center", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("adc_voltage_min", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("adc_voltage_max", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("adc_voltage_center", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
]

SPEED_PID_FIELDS = [
    Field("kp", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("ki", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("kd", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("min_erpm", lambda v: _enc_f32(v, 1.0), lambda d, o: _dec_f32(d, o, 1.0)),
    Field("max_erpm", lambda v: _enc_f32(v, 1.0), lambda d, o: _dec_f32(d, o, 1.0)),
    Field("error_tolerance", lambda v: _enc_f16(v, 10000.0), lambda d, o: _dec_f16(d, o, 10000.0)),
]

MOTOR_FIELDS_PROTO = [
    Field("motor_type", lambda v: _enc_u8(list(MotorType).index(v)),
          lambda d, o: (list(MotorType)[d[o]], o + 1)),
    Field("pole_pairs", _enc_u16, _dec_u16),
    Field("resistance", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("inductance", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("kv_rating", lambda v: _enc_f32(v, 1.0), lambda d, o: _dec_f32(d, o, 1.0)),
    Field("max_current", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("max_brake_current", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("current_ramp_step", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
    Field("temp_motor_max", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("temp_motor_start", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
]

BATTERY_FIELDS = [
    Field("battery_type", lambda v: _enc_u8(list(BatteryType).index(v)),
          lambda d, o: (list(BatteryType)[d[o]], o + 1)),
    Field("cells", _enc_u16, _dec_u16),
    Field("capacity", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("voltage_max", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("voltage_min", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("cutoff_start", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("cutoff_end", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("charge_max", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("internal_resistance", lambda v: _enc_f32(v), lambda d, o: _dec_f32(d, o)),
]

DUAL_FIELDS = [
    Field("mode", lambda v: _enc_u8(list(DualMode).index(v)),
          lambda d, o: (list(DualMode)[d[o]], o + 1)),
    Field("sync_duty", _enc_bool, _dec_bool),
    Field("sync_current", _enc_bool, _dec_bool),
    Field("sync_rpm", _enc_bool, _dec_bool),
    Field("balance_factor", lambda v: _enc_f16(v, 10000.0), lambda d, o: _dec_f16(d, o, 10000.0)),
    Field("torque_bias", lambda v: _enc_f16(v, 10000.0), lambda d, o: _dec_f16(d, o, 10000.0)),
    Field("speed_differential", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("motor_direction_a", _enc_bool, _dec_bool),
    Field("motor_direction_b", _enc_bool, _dec_bool),
    Field("mirror_controls", _enc_bool, _dec_bool),
    Field("traction_control", _enc_bool, _dec_bool),
    Field("traction_slip", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("traction_sensitivity", lambda v: _enc_f16(v, 10000.0), lambda d, o: _dec_f16(d, o, 10000.0)),
    Field("beep_on_startup", _enc_bool, _dec_bool),
]

IMU_FIELDS = [
    Field("imu_type", lambda v: _enc_u8(list(IMUType).index(v)),
          lambda d, o: (list(IMUType)[d[o]], o + 1)),
    Field("sample_rate", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("pitch_kp", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("pitch_ki", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("roll_kp", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("roll_ki", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("yaw_kp", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
    Field("yaw_ki", lambda v: _enc_f16(v, 100.0), lambda d, o: _dec_f16(d, o, 100.0)),
]

CAN_FIELDS = [
    Field("mode", lambda v: _enc_u8(list(CANMode).index(v)),
          lambda d, o: (list(CANMode)[d[o]], o + 1)),
    Field("id_a", _enc_u8, _dec_u8),
    Field("id_b", _enc_u8, _dec_u8),
    Field("baudrate", lambda v: _enc_u8(list(CANBaudrate).index(v)),
          lambda d, o: (list(CANBaudrate)[d[o]], o + 1)),
    Field("status_1", _enc_bool, _dec_bool),
    Field("status_2", _enc_bool, _dec_bool),
    Field("status_3", _enc_bool, _dec_bool),
    Field("status_4", _enc_bool, _dec_bool),
    Field("fwd", _enc_u8, _dec_u8),
]

PERIPHERAL_FIELDS = [
    Field("headlight_on", _enc_bool, _dec_bool),
    Field("headlight_intensity", _enc_u8, _dec_u8),
    Field("brakelight_on", _enc_bool, _dec_bool),
    Field("brakelight_mode", _enc_u8, _dec_u8),
]

SECTION_FIELDS = {
    SEC_MOTOR: MOTOR_FIELDS_PROTO,
    SEC_HALL: HALL_FIELDS,
    SEC_FOC: FOC_FIELDS,
    SEC_LIMITS: LIMITS_FIELDS,
    SEC_RAMP: RAMP_FIELDS,
    SEC_BRAKE: BRAKE_FIELDS,
    SEC_INPUT_CTRL: INPUT_CTRL_FIELDS,
    SEC_SPEED_PID: SPEED_PID_FIELDS,
    SEC_BATTERY: BATTERY_FIELDS,
    SEC_DUAL: DUAL_FIELDS,
    SEC_IMU: IMU_FIELDS,
    SEC_CAN: CAN_FIELDS,
    SEC_PERIPHERALS: PERIPHERAL_FIELDS,
}

SUB_SEC_TO_MOTOR_KEY = {
    SEC_HALL: "hall",
    SEC_FOC: "foc",
    SEC_LIMITS: "limits",
    SEC_RAMP: "ramp",
    SEC_BRAKE: "brake",
    SEC_INPUT_CTRL: "input_control",
    SEC_SPEED_PID: "speed_pid",
}

SECTION_NAMES = {
    SEC_MOTOR: "motor",
    SEC_HALL: "hall",
    SEC_FOC: "foc",
    SEC_LIMITS: "limits",
    SEC_RAMP: "ramp",
    SEC_BRAKE: "brake",
    SEC_INPUT_CTRL: "input_control",
    SEC_SPEED_PID: "speed_pid",
    SEC_BATTERY: "battery",
    SEC_DUAL: "dual_setup",
    SEC_IMU: "imu",
    SEC_CAN: "can",
    SEC_PERIPHERALS: "peripherals",
}


def encode_section(config_obj, fields: list) -> bytes:
    buf = b''
    for f in fields:
        val = getattr(config_obj, f.key)
        buf += f.enc(val)
    return buf


def decode_section(data: bytes, config_cls, fields: list):
    vals = {}
    off = 0
    for f in fields:
        val, off = f.dec(data, off)
        vals[f.key] = val
    return config_cls(**vals)


def build_read_config_frame(controller_id: int, section_id: int) -> bytes:
    payload = decompose_u8(controller_id) + decompose_u8(section_id)
    return build_frame(UartCommand.READ_CONFIG, payload)


def build_write_config_frame(controller_id: int, section_id: int, config_obj) -> bytes:
    fields = SECTION_FIELDS[section_id]
    payload = decompose_u8(controller_id) + decompose_u8(section_id)
    payload += encode_section(config_obj, fields)
    return build_frame(UartCommand.WRITE_CONFIG, payload)


def parse_config_response(payload: bytes):
    """Parse a READ_CONFIG or WRITE_CONFIG response.

    Returns (controller_id, section_id, data_bytes) or None on error.
    """
    if len(payload) < 2:
        return None
    ctrl_id = payload[0]
    sec_id = payload[1]
    return ctrl_id, sec_id, payload[2:]


def decode_section_response(controller_id: int, section_id: int, data: bytes):
    """Decode section data from a READ_CONFIG response into a config object."""
    if section_id == SEC_MOTOR:
        return decode_section(data, MotorConfig, MOTOR_FIELDS_PROTO)
    elif section_id == SEC_HALL:
        return decode_section(data, HallConfig, HALL_FIELDS)
    elif section_id == SEC_FOC:
        return decode_section(data, FOCConfig, FOC_FIELDS)
    elif section_id == SEC_LIMITS:
        return decode_section(data, LimitsConfig, LIMITS_FIELDS)
    elif section_id == SEC_RAMP:
        return decode_section(data, RampConfig, RAMP_FIELDS)
    elif section_id == SEC_BRAKE:
        return decode_section(data, BrakeConfig, BRAKE_FIELDS)
    elif section_id == SEC_INPUT_CTRL:
        return decode_section(data, InputControlConfig, INPUT_CTRL_FIELDS)
    elif section_id == SEC_SPEED_PID:
        return decode_section(data, SpeedPIDConfig, SPEED_PID_FIELDS)
    elif section_id == SEC_BATTERY:
        return decode_section(data, BatteryConfig, BATTERY_FIELDS)
    elif section_id == SEC_DUAL:
        return decode_section(data, DualSetupConfig, DUAL_FIELDS)
    elif section_id == SEC_IMU:
        return decode_section(data, IMUConfig, IMU_FIELDS)
    elif section_id == SEC_CAN:
        return decode_section(data, CANConfig, CAN_FIELDS)
    elif section_id == SEC_PERIPHERALS:
        return decode_section(data, PeripheralConfig, PERIPHERAL_FIELDS)
    return None


def build_read_all_config_frame(controller_id: int) -> bytes:
    payload = decompose_u8(controller_id)
    return build_frame(UartCommand.READ_ALL_CONFIG, payload)


def build_write_all_config_frame(controller_id: int, config: MotorConfig) -> bytes:
    payload = decompose_u8(controller_id)
    for sec_id in range(SEC_MOTOR, SEC_SPEED_PID + 1):
        fields = SECTION_FIELDS[sec_id]
        if sec_id == SEC_MOTOR:
            obj = config
        else:
            obj = getattr(config, SUB_SEC_TO_MOTOR_KEY[sec_id])
        payload += encode_section(obj, fields)
    return build_frame(UartCommand.WRITE_ALL_CONFIG, payload)


def encode_global_config(battery: BatteryConfig, dual: DualSetupConfig, imu: IMUConfig, can: CANConfig, peripherals: PeripheralConfig | None = None) -> bytes:
    buf = b''
    buf += encode_section(battery, BATTERY_FIELDS)
    buf += encode_section(dual, DUAL_FIELDS)
    buf += encode_section(imu, IMU_FIELDS)
    buf += encode_section(can, CAN_FIELDS)
    if peripherals is not None:
        buf += encode_section(peripherals, PERIPHERAL_FIELDS)
    return buf


def build_write_all_global_frame(config: DualMotorConfig) -> bytes:
    payload = decompose_u8(CTRL_GLOBAL)
    payload += encode_global_config(config.battery, config.dual_setup, config.imu, config.can, config.peripherals)
    return build_frame(UartCommand.WRITE_ALL_CONFIG, payload)
