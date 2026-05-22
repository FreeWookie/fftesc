# -*- coding: utf-8 -*-
"""
ftesc/data.py — Structures de données FTESC
"""

from dataclasses import dataclass, field
from enum import Enum
import time


class MotorType(Enum):
    BLDC = "BLDC"
    DC = "DC"
    FOC = "FOC"


class SensorlessMode(Enum):
    HYBRID = "Hybrid"
    ALWAYS = "Always"


class FOCMode(Enum):
    SINUS = 0
    TRAPEZOID = 1
    FOC = 2


class ControlType(Enum):
    DUTY = "Duty"
    CURRENT = "Current"
    RPM = "RPM"
    POSITION = "Position"


class ControlCommand(Enum):
    PPM = "PPM"
    ADC = "ADC"
    UART = "UART"
    NRF = "NRF"


class BatteryType(Enum):
    LI_ION = "LiIon"
    LI_PO = "LiPo"
    LI_FE_PO4 = "LiFePO4"
    LEAD = "Lead"


class DualMode(Enum):
    INDEPENDENT = "Independent"
    MASTER_SLAVE = "Master-Slave"
    TRACTION = "Traction"


class IMUType(Enum):
    NONE = "None"
    MPU6050 = "MPU6050"
    BMI160 = "BMI160"
    ICM42688 = "ICM42688"


class CANMode(Enum):
    OFF = "OFF"
    VESC = "VESC"
    CUSTOM = "Custom"


class CANBaudrate(Enum):
    R125K = "125k"
    R250K = "250k"
    R500K = "500k"
    R1M = "1M"


@dataclass
class HallConfig:
    enabled: bool = False
    hall_table: list = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6, 7])
    direction: bool = False
    interpolation: bool = True
    sensorless_mode: SensorlessMode = SensorlessMode.HYBRID
    sensorless_erpm: float = 3000.0
    sensorless_erpm_start: float = 500.0

    def __post_init__(self):
        if len(self.hall_table) != 8:
            self.hall_table = [0, 1, 2, 3, 4, 5, 6, 7]

    def validate(self) -> list[str]:
        errors = []
        if self.sensorless_mode not in SensorlessMode:
            errors.append("Mode sensorless invalide")
        if not 100 <= self.sensorless_erpm <= 50000:
            errors.append("Sensorless ERPM doit être entre 100 et 50000")
        if not 100 <= self.sensorless_erpm_start <= 50000:
            errors.append("Sensorless ERPM Start doit être entre 100 et 50000")
        if len(self.hall_table) != 8 or any(v < 0 or v > 7 for v in self.hall_table):
            errors.append("Hall Table doit contenir 8 valeurs entre 0 et 7")
        return errors

    def to_dict(self) -> dict:
        return {
            'enabled': self.enabled,
            'hall_table': self.hall_table,
            'direction': self.direction,
            'interpolation': self.interpolation,
            'sensorless_mode': self.sensorless_mode.value,
            'sensorless_erpm': self.sensorless_erpm,
            'sensorless_erpm_start': self.sensorless_erpm_start,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'HallConfig':
        table = d.get('hall_table', [0, 1, 2, 3, 4, 5, 6, 7])
        if isinstance(table, list) and len(table) != 8:
            table = [0, 1, 2, 3, 4, 5, 6, 7]
        return cls(
            enabled=d.get('enabled', False),
            hall_table=table,
            direction=d.get('direction', False),
            interpolation=d.get('interpolation', True),
            sensorless_mode=SensorlessMode(d.get('sensorless_mode', 'Hybrid')),
            sensorless_erpm=d.get('sensorless_erpm', 3000.0),
            sensorless_erpm_start=d.get('sensorless_erpm_start', 500.0),
        )


@dataclass
class FOCConfig:
    mode: FOCMode = FOCMode.FOC
    current_kp: float = 0.1
    current_ki: float = 0.01
    fsw: float = 20.0
    dead_time: float = 50.0
    openloop_rpm: float = 300.0
    openloop_lock: bool = True
    observer_gain: float = 10.0
    observer_gain_slow: float = 5.0
    pll_kp: float = 1000.0
    pll_ki: float = 100.0
    antiwindup: float = 0.5
    duty_kp: float = 0.1
    duty_ki: float = 0.01
    sat_comp: bool = True

    def validate(self) -> list[str]:
        errors = []
        if self.mode not in FOCMode:
            errors.append("Mode FOC invalide")
        if not 0 <= self.current_kp <= 1:
            errors.append("FOC Current Kp doit être entre 0 et 1")
        if not 0 <= self.current_ki <= 1:
            errors.append("FOC Current Ki doit être entre 0 et 1")
        if not 5 <= self.fsw <= 50:
            errors.append("FOC FSW doit être entre 5 et 50 kHz")
        if not 0 <= self.dead_time <= 500:
            errors.append("FOC Dead Time doit être entre 0 et 500 ns")
        if not 100 <= self.openloop_rpm <= 5000:
            errors.append("FOC Openloop RPM doit être entre 100 et 5000")
        if not 0 <= self.observer_gain <= 100:
            errors.append("FOC Observer Gain doit être entre 0 et 100")
        if not 0 <= self.observer_gain_slow <= 100:
            errors.append("FOC Observer Gain Slow doit être entre 0 et 100")
        if not 0 <= self.pll_kp <= 100000:
            errors.append("FOC PLL Kp doit être entre 0 et 100000")
        if not 0 <= self.pll_ki <= 100000:
            errors.append("FOC PLL Ki doit être entre 0 et 100000")
        if not 0 <= self.antiwindup <= 1:
            errors.append("FOC Antiwindup doit être entre 0 et 1")
        if not 0 <= self.duty_kp <= 1:
            errors.append("FOC Duty Kp doit être entre 0 et 1")
        if not 0 <= self.duty_ki <= 1:
            errors.append("FOC Duty Ki doit être entre 0 et 1")
        return errors

    def to_dict(self) -> dict:
        return {
            'mode': self.mode.value,
            'current_kp': self.current_kp,
            'current_ki': self.current_ki,
            'fsw': self.fsw,
            'dead_time': self.dead_time,
            'openloop_rpm': self.openloop_rpm,
            'openloop_lock': self.openloop_lock,
            'observer_gain': self.observer_gain,
            'observer_gain_slow': self.observer_gain_slow,
            'pll_kp': self.pll_kp,
            'pll_ki': self.pll_ki,
            'antiwindup': self.antiwindup,
            'duty_kp': self.duty_kp,
            'duty_ki': self.duty_ki,
            'sat_comp': self.sat_comp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'FOCConfig':
        return cls(
            mode=FOCMode(d.get('mode', 2)),
            current_kp=d.get('current_kp', 0.1),
            current_ki=d.get('current_ki', 0.01),
            fsw=d.get('fsw', 20.0),
            dead_time=d.get('dead_time', 50.0),
            openloop_rpm=d.get('openloop_rpm', 300.0),
            openloop_lock=d.get('openloop_lock', True),
            observer_gain=d.get('observer_gain', 10.0),
            observer_gain_slow=d.get('observer_gain_slow', 5.0),
            pll_kp=d.get('pll_kp', 1000.0),
            pll_ki=d.get('pll_ki', 100.0),
            antiwindup=d.get('antiwindup', 0.5),
            duty_kp=d.get('duty_kp', 0.1),
            duty_ki=d.get('duty_ki', 0.01),
            sat_comp=d.get('sat_comp', True),
        )


@dataclass
class RampConfig:
    ramp_up_time: float = 1.0
    ramp_down_time: float = 1.0
    startup_speed: float = 10.0
    cool_down_time: float = 5.0
    acceleration_current: float = 60.0
    deceleration_current: float = 40.0

    def validate(self) -> list[str]:
        errors = []
        if not 0 <= self.ramp_up_time <= 10:
            errors.append("Ramp Up Time doit être entre 0 et 10 s")
        if not 0 <= self.ramp_down_time <= 10:
            errors.append("Ramp Down Time doit être entre 0 et 10 s")
        if not 0 <= self.startup_speed <= 100:
            errors.append("Startup Speed doit être entre 0 et 100 %")
        if not 0 <= self.cool_down_time <= 60:
            errors.append("Cool Down Time doit être entre 0 et 60 s")
        if not 0 <= self.acceleration_current <= 200:
            errors.append("Acceleration Current doit être entre 0 et 200 A")
        if not 0 <= self.deceleration_current <= 200:
            errors.append("Deceleration Current doit être entre 0 et 200 A")
        return errors

    def to_dict(self) -> dict:
        return {
            'ramp_up_time': self.ramp_up_time,
            'ramp_down_time': self.ramp_down_time,
            'startup_speed': self.startup_speed,
            'cool_down_time': self.cool_down_time,
            'acceleration_current': self.acceleration_current,
            'deceleration_current': self.deceleration_current,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'RampConfig':
        return cls(
            ramp_up_time=d.get('ramp_up_time', 1.0),
            ramp_down_time=d.get('ramp_down_time', 1.0),
            startup_speed=d.get('startup_speed', 10.0),
            cool_down_time=d.get('cool_down_time', 5.0),
            acceleration_current=d.get('acceleration_current', 60.0),
            deceleration_current=d.get('deceleration_current', 40.0),
        )


@dataclass
class BrakeConfig:
    brake_current: float = 40.0
    brake_current_ramp: float = 10.0
    regen_braking: bool = True
    regen_voltage_max: float = 25.0
    brake_temperature_limit: float = 100.0

    def validate(self) -> list[str]:
        errors = []
        if not 0 <= self.brake_current <= 200:
            errors.append("Brake Current doit être entre 0 et 200 A")
        if not 0 <= self.brake_current_ramp <= 100:
            errors.append("Brake Current Ramp doit être entre 0 et 100 A/s")
        if not 0 <= self.regen_voltage_max <= 100:
            errors.append("Regen Voltage Max doit être entre 0 et 100 V")
        if not 50 <= self.brake_temperature_limit <= 150:
            errors.append("Brake Temperature Limit doit être entre 50 et 150 °C")
        return errors

    def to_dict(self) -> dict:
        return {
            'brake_current': self.brake_current,
            'brake_current_ramp': self.brake_current_ramp,
            'regen_braking': self.regen_braking,
            'regen_voltage_max': self.regen_voltage_max,
            'brake_temperature_limit': self.brake_temperature_limit,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'BrakeConfig':
        return cls(
            brake_current=d.get('brake_current', 40.0),
            brake_current_ramp=d.get('brake_current_ramp', 10.0),
            regen_braking=d.get('regen_braking', True),
            regen_voltage_max=d.get('regen_voltage_max', 25.0),
            brake_temperature_limit=d.get('brake_temperature_limit', 100.0),
        )


@dataclass
class InputControlConfig:
    control_type: ControlType = ControlType.CURRENT
    input_voltage_min: float = 20.0
    input_voltage_max: float = 57.0
    throttle_curve: list = field(default_factory=lambda: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    brake_curve: list = field(default_factory=lambda: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    throttle_center: float = 0.5
    throttle_deadband: float = 0.05
    control_deadband: float = 0.05
    control_command: ControlCommand = ControlCommand.PPM
    ppm_pulse_min: float = 1.0
    ppm_pulse_max: float = 2.0
    ppm_pulse_center: float = 1.5
    adc_voltage_min: float = 0.0
    adc_voltage_max: float = 3.3
    adc_voltage_center: float = 1.65

    def __post_init__(self):
        if len(self.throttle_curve) != 6:
            self.throttle_curve = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        if len(self.brake_curve) != 6:
            self.brake_curve = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    def validate(self) -> list[str]:
        errors = []
        if self.control_type not in ControlType:
            errors.append("Control Type invalide")
        if not 5 <= self.input_voltage_min <= 80:
            errors.append("Input Voltage Min doit être entre 5 et 80 V")
        if not 10 <= self.input_voltage_max <= 100:
            errors.append("Input Voltage Max doit être entre 10 et 100 V")
        if not 0 <= self.throttle_center <= 1:
            errors.append("Throttle Center doit être entre 0 et 1")
        if not 0 <= self.throttle_deadband <= 0.5:
            errors.append("Throttle Deadband doit être entre 0 et 0.5")
        if not 0 <= self.control_deadband <= 0.5:
            errors.append("Control Deadband doit être entre 0 et 0.5")
        if self.control_command not in ControlCommand:
            errors.append("Control Command invalide")
        if not 0.5 <= self.ppm_pulse_min <= 2.0:
            errors.append("PPM Pulse Min doit être entre 0.5 et 2.0 ms")
        if not 1.0 <= self.ppm_pulse_max <= 3.0:
            errors.append("PPM Pulse Max doit être entre 1.0 et 3.0 ms")
        if not 1.0 <= self.ppm_pulse_center <= 2.0:
            errors.append("PPM Pulse Center doit être entre 1.0 et 2.0 ms")
        if not 0 <= self.adc_voltage_min <= 3.3:
            errors.append("ADC Voltage Min doit être entre 0 et 3.3 V")
        if not 0 <= self.adc_voltage_max <= 3.3:
            errors.append("ADC Voltage Max doit être entre 0 et 3.3 V")
        if not 0 <= self.adc_voltage_center <= 3.3:
            errors.append("ADC Voltage Center doit être entre 0 et 3.3 V")
        if any(v < 0 or v > 1 for v in self.throttle_curve):
            errors.append("Throttle Curve doit contenir 6 valeurs entre 0 et 1")
        if any(v < 0 or v > 1 for v in self.brake_curve):
            errors.append("Brake Curve doit contenir 6 valeurs entre 0 et 1")
        return errors

    def to_dict(self) -> dict:
        return {
            'control_type': self.control_type.value,
            'input_voltage_min': self.input_voltage_min,
            'input_voltage_max': self.input_voltage_max,
            'throttle_curve': self.throttle_curve,
            'brake_curve': self.brake_curve,
            'throttle_center': self.throttle_center,
            'throttle_deadband': self.throttle_deadband,
            'control_deadband': self.control_deadband,
            'control_command': self.control_command.value,
            'ppm_pulse_min': self.ppm_pulse_min,
            'ppm_pulse_max': self.ppm_pulse_max,
            'ppm_pulse_center': self.ppm_pulse_center,
            'adc_voltage_min': self.adc_voltage_min,
            'adc_voltage_max': self.adc_voltage_max,
            'adc_voltage_center': self.adc_voltage_center,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'InputControlConfig':
        tc = d.get('throttle_curve', [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        bc = d.get('brake_curve', [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        return cls(
            control_type=ControlType(d.get('control_type', 'Current')),
            input_voltage_min=d.get('input_voltage_min', 20.0),
            input_voltage_max=d.get('input_voltage_max', 57.0),
            throttle_curve=tc if len(tc) == 6 else [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            brake_curve=bc if len(bc) == 6 else [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            throttle_center=d.get('throttle_center', 0.5),
            throttle_deadband=d.get('throttle_deadband', 0.05),
            control_deadband=d.get('control_deadband', 0.05),
            control_command=ControlCommand(d.get('control_command', 'PPM')),
            ppm_pulse_min=d.get('ppm_pulse_min', 1.0),
            ppm_pulse_max=d.get('ppm_pulse_max', 2.0),
            ppm_pulse_center=d.get('ppm_pulse_center', 1.5),
            adc_voltage_min=d.get('adc_voltage_min', 0.0),
            adc_voltage_max=d.get('adc_voltage_max', 3.3),
            adc_voltage_center=d.get('adc_voltage_center', 1.65),
        )


@dataclass
class LimitsConfig:
    max_erpm: float = 60000.0
    max_erpm_reverse: float = 30000.0
    max_duty: float = 0.95
    min_duty: float = 0.05
    max_input_voltage: float = 57.0
    min_input_voltage: float = 20.0
    max_battery_current: float = 80.0
    max_battery_current_rev: float = 40.0
    max_motor_current: float = 80.0
    max_motor_current_rev: float = 40.0
    max_absolute_current: float = 150.0
    temp_fet_max: float = 90.0
    temp_fet_start: float = 80.0
    slow_abs_overvoltage: bool = True
    slow_abs_undervoltage: bool = True

    def validate(self) -> list[str]:
        errors = []
        if not 100 <= self.max_erpm <= 200000:
            errors.append("Max ERPM doit être entre 100 et 200000")
        if not 100 <= self.max_erpm_reverse <= 200000:
            errors.append("Max ERPM Reverse doit être entre 100 et 200000")
        if not 0 <= self.max_duty <= 0.95:
            errors.append("Max Duty doit être entre 0 et 0.95")
        if not 0 <= self.min_duty <= 0.5:
            errors.append("Min Duty doit être entre 0 et 0.5")
        if self.min_duty > self.max_duty:
            errors.append("Min Duty ne peut pas dépasser Max Duty")
        if not 10 <= self.max_input_voltage <= 100:
            errors.append("Max Input Voltage doit être entre 10 et 100 V")
        if not 5 <= self.min_input_voltage <= 80:
            errors.append("Min Input Voltage doit être entre 5 et 80 V")
        if self.min_input_voltage > self.max_input_voltage:
            errors.append("Min Input Voltage ne peut pas dépasser Max Input Voltage")
        if not 0 <= self.max_battery_current <= 200:
            errors.append("Max Battery Current doit être entre 0 et 200 A")
        if not 0 <= self.max_battery_current_rev <= 200:
            errors.append("Max Battery Current Rev doit être entre 0 et 200 A")
        if not 0 <= self.max_motor_current <= 200:
            errors.append("Max Motor Current doit être entre 0 et 200 A")
        if not 0 <= self.max_motor_current_rev <= 200:
            errors.append("Max Motor Current Rev doit être entre 0 et 200 A")
        if not 0 <= self.max_absolute_current <= 300:
            errors.append("Max Absolute Current doit être entre 0 et 300 A")
        if not 60 <= self.temp_fet_max <= 120:
            errors.append("Temp FET Max doit être entre 60 et 120 °C")
        if not 50 <= self.temp_fet_start <= 110:
            errors.append("Temp FET Start doit être entre 50 et 110 °C")
        if self.temp_fet_start > self.temp_fet_max:
            errors.append("Temp FET Start ne peut pas dépasser Temp FET Max")
        return errors

    def to_dict(self) -> dict:
        return {
            'max_erpm': self.max_erpm,
            'max_erpm_reverse': self.max_erpm_reverse,
            'max_duty': self.max_duty,
            'min_duty': self.min_duty,
            'max_input_voltage': self.max_input_voltage,
            'min_input_voltage': self.min_input_voltage,
            'max_battery_current': self.max_battery_current,
            'max_battery_current_rev': self.max_battery_current_rev,
            'max_motor_current': self.max_motor_current,
            'max_motor_current_rev': self.max_motor_current_rev,
            'max_absolute_current': self.max_absolute_current,
            'temp_fet_max': self.temp_fet_max,
            'temp_fet_start': self.temp_fet_start,
            'slow_abs_overvoltage': self.slow_abs_overvoltage,
            'slow_abs_undervoltage': self.slow_abs_undervoltage,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'LimitsConfig':
        return cls(
            max_erpm=d.get('max_erpm', 60000.0),
            max_erpm_reverse=d.get('max_erpm_reverse', 30000.0),
            max_duty=d.get('max_duty', 0.95),
            min_duty=d.get('min_duty', 0.05),
            max_input_voltage=d.get('max_input_voltage', 57.0),
            min_input_voltage=d.get('min_input_voltage', 20.0),
            max_battery_current=d.get('max_battery_current', 80.0),
            max_battery_current_rev=d.get('max_battery_current_rev', 40.0),
            max_motor_current=d.get('max_motor_current', 80.0),
            max_motor_current_rev=d.get('max_motor_current_rev', 40.0),
            max_absolute_current=d.get('max_absolute_current', 150.0),
            temp_fet_max=d.get('temp_fet_max', 90.0),
            temp_fet_start=d.get('temp_fet_start', 80.0),
            slow_abs_overvoltage=d.get('slow_abs_overvoltage', True),
            slow_abs_undervoltage=d.get('slow_abs_undervoltage', True),
        )


@dataclass
class SpeedPIDConfig:
    kp: float = 0.1
    ki: float = 0.01
    kd: float = 0.001
    min_erpm: float = 500.0
    max_erpm: float = 60000.0
    error_tolerance: float = 0.05

    def validate(self) -> list[str]:
        errors = []
        if not 0 <= self.kp <= 1:
            errors.append("Speed PID Kp doit être entre 0 et 1")
        if not 0 <= self.ki <= 1:
            errors.append("Speed PID Ki doit être entre 0 et 1")
        if not 0 <= self.kd <= 1:
            errors.append("Speed PID Kd doit être entre 0 et 1")
        if not 0 <= self.min_erpm <= 50000:
            errors.append("Speed PID Min ERPM doit être entre 0 et 50000")
        if not 0 <= self.max_erpm <= 200000:
            errors.append("Speed PID Max ERPM doit être entre 0 et 200000")
        if not 0 <= self.error_tolerance <= 1:
            errors.append("Speed PID Error doit être entre 0 et 1")
        return errors

    def to_dict(self) -> dict:
        return {
            'kp': self.kp,
            'ki': self.ki,
            'kd': self.kd,
            'min_erpm': self.min_erpm,
            'max_erpm': self.max_erpm,
            'error_tolerance': self.error_tolerance,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'SpeedPIDConfig':
        return cls(
            kp=d.get('kp', 0.1),
            ki=d.get('ki', 0.01),
            kd=d.get('kd', 0.001),
            min_erpm=d.get('min_erpm', 500.0),
            max_erpm=d.get('max_erpm', 60000.0),
            error_tolerance=d.get('error_tolerance', 0.05),
        )


@dataclass
class MotorConfig:
    motor_type: MotorType = MotorType.BLDC
    pole_pairs: int = 14
    resistance: float = 0.1
    inductance: float = 0.05
    kv_rating: float = 70.0
    max_current: float = 80.0
    max_brake_current: float = 40.0
    current_ramp_step: float = 10.0
    temp_motor_max: float = 90.0
    temp_motor_start: float = 80.0
    hall: HallConfig = field(default_factory=HallConfig)
    foc: FOCConfig = field(default_factory=FOCConfig)
    ramp: RampConfig = field(default_factory=RampConfig)
    brake: BrakeConfig = field(default_factory=BrakeConfig)
    input_control: InputControlConfig = field(default_factory=InputControlConfig)
    limits: LimitsConfig = field(default_factory=LimitsConfig)
    speed_pid: SpeedPIDConfig = field(default_factory=SpeedPIDConfig)

    def validate(self) -> list[str]:
        errors = []
        if self.motor_type not in MotorType:
            errors.append("Type de moteur invalide")
        if not 1 <= self.pole_pairs <= 100:
            errors.append("Pole Pairs doit être entre 1 et 100")
        if not 0.001 <= self.resistance <= 10.0:
            errors.append("Résistance doit être entre 0.001 et 10 Ω")
        if not 0.001 <= self.inductance <= 100.0:
            errors.append("Inductance doit être entre 0.001 et 100 mH")
        if not 1 <= self.kv_rating <= 10000:
            errors.append("KV Rating doit être entre 1 et 10000")
        if not 0 <= self.max_current <= 200:
            errors.append("Max Current doit être entre 0 et 200 A")
        if not 0 <= self.max_brake_current <= 200:
            errors.append("Max Brake Current doit être entre 0 et 200 A")
        if not 0.1 <= self.current_ramp_step <= 100:
            errors.append("Current Ramp Step doit être entre 0.1 et 100 A/s")
        if not 50 <= self.temp_motor_max <= 150:
            errors.append("Temp Motor Max doit être entre 50 et 150 °C")
        if not 40 <= self.temp_motor_start <= 130:
            errors.append("Temp Motor Start doit être entre 40 et 130 °C")
        if self.temp_motor_start > self.temp_motor_max:
            errors.append("Temp Motor Start ne peut pas dépasser Temp Motor Max")
        errors.extend(self.hall.validate())
        errors.extend(self.foc.validate())
        errors.extend(self.ramp.validate())
        errors.extend(self.brake.validate())
        errors.extend(self.input_control.validate())
        errors.extend(self.limits.validate())
        errors.extend(self.speed_pid.validate())
        return errors

    def to_dict(self) -> dict:
        return {
            'motor_type': self.motor_type.value,
            'pole_pairs': self.pole_pairs,
            'resistance': self.resistance,
            'inductance': self.inductance,
            'kv_rating': self.kv_rating,
            'max_current': self.max_current,
            'max_brake_current': self.max_brake_current,
            'current_ramp_step': self.current_ramp_step,
            'temp_motor_max': self.temp_motor_max,
            'temp_motor_start': self.temp_motor_start,
            'hall': self.hall.to_dict(),
            'foc': self.foc.to_dict(),
            'ramp': self.ramp.to_dict(),
            'brake': self.brake.to_dict(),
            'input_control': self.input_control.to_dict(),
            'limits': self.limits.to_dict(),
            'speed_pid': self.speed_pid.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'MotorConfig':
        return cls(
            motor_type=MotorType(d.get('motor_type', 'BLDC')),
            pole_pairs=d.get('pole_pairs', 14),
            resistance=d.get('resistance', 0.1),
            inductance=d.get('inductance', 0.05),
            kv_rating=d.get('kv_rating', 70.0),
            max_current=d.get('max_current', 80.0),
            max_brake_current=d.get('max_brake_current', 40.0),
            current_ramp_step=d.get('current_ramp_step', 10.0),
            temp_motor_max=d.get('temp_motor_max', 90.0),
            temp_motor_start=d.get('temp_motor_start', 80.0),
            hall=HallConfig.from_dict(d.get('hall', {})),
            foc=FOCConfig.from_dict(d.get('foc', {})),
            ramp=RampConfig.from_dict(d.get('ramp', {})),
            brake=BrakeConfig.from_dict(d.get('brake', {})),
            input_control=InputControlConfig.from_dict(d.get('input_control', {})),
            limits=LimitsConfig.from_dict(d.get('limits', {})),
            speed_pid=SpeedPIDConfig.from_dict(d.get('speed_pid', {})),
        )


@dataclass
class BatteryConfig:
    battery_type: BatteryType = BatteryType.LI_PO
    cells: int = 12
    capacity: float = 10.0
    voltage_max: float = 50.4
    voltage_min: float = 37.8
    cutoff_start: float = 39.0
    cutoff_end: float = 37.0
    charge_max: float = 10.0
    internal_resistance: float = 0.05

    def validate(self) -> list[str]:
        errors = []
        if self.battery_type not in BatteryType:
            errors.append("Battery Type invalide")
        if not 1 <= self.cells <= 20:
            errors.append("Battery Cells doit être entre 1 et 20S")
        if not 1 <= self.capacity <= 100:
            errors.append("Battery Capacity doit être entre 1 et 100 Ah")
        if not 10 <= self.voltage_max <= 100:
            errors.append("Battery Voltage Max doit être entre 10 et 100 V")
        if not 5 <= self.voltage_min <= 80:
            errors.append("Battery Voltage Min doit être entre 5 et 80 V")
        if not 5 <= self.cutoff_start <= 80:
            errors.append("Battery Cutoff Start doit être entre 5 et 80 V")
        if not 5 <= self.cutoff_end <= 80:
            errors.append("Battery Cutoff End doit être entre 5 et 80 V")
        if self.cutoff_end > self.cutoff_start:
            errors.append("Cutoff End ne peut pas dépasser Cutoff Start")
        if not 0 <= self.charge_max <= 200:
            errors.append("Battery Charge Max doit être entre 0 et 200 A")
        if not 0 <= self.internal_resistance <= 1:
            errors.append("Battery Internal Resistance doit être entre 0 et 1 Ω")
        return errors

    def to_dict(self) -> dict:
        return {
            'battery_type': self.battery_type.value,
            'cells': self.cells,
            'capacity': self.capacity,
            'voltage_max': self.voltage_max,
            'voltage_min': self.voltage_min,
            'cutoff_start': self.cutoff_start,
            'cutoff_end': self.cutoff_end,
            'charge_max': self.charge_max,
            'internal_resistance': self.internal_resistance,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'BatteryConfig':
        return cls(
            battery_type=BatteryType(d.get('battery_type', 'LiPo')),
            cells=d.get('cells', 12),
            capacity=d.get('capacity', 10.0),
            voltage_max=d.get('voltage_max', 50.4),
            voltage_min=d.get('voltage_min', 37.8),
            cutoff_start=d.get('cutoff_start', 39.0),
            cutoff_end=d.get('cutoff_end', 37.0),
            charge_max=d.get('charge_max', 10.0),
            internal_resistance=d.get('internal_resistance', 0.05),
        )


@dataclass
class DualSetupConfig:
    mode: DualMode = DualMode.INDEPENDENT
    sync_duty: bool = False
    sync_current: bool = False
    sync_rpm: bool = False
    balance_factor: float = 0.5
    torque_bias: float = 0.0
    speed_differential: float = 0.0
    motor_direction_a: bool = True
    motor_direction_b: bool = True
    mirror_controls: bool = False
    traction_control: bool = False
    traction_slip: float = 10.0
    traction_sensitivity: float = 0.5
    beep_on_startup: bool = True

    def validate(self) -> list[str]:
        errors = []
        if self.mode not in DualMode:
            errors.append("Dual Mode invalide")
        if not 0 <= self.balance_factor <= 1:
            errors.append("Balance Factor doit être entre 0 et 1")
        if not -1 <= self.torque_bias <= 1:
            errors.append("Torque Bias doit être entre -1 et 1")
        if not 0 <= self.speed_differential <= 100:
            errors.append("Speed Differential doit être entre 0 et 100 %")
        if not 0 <= self.traction_slip <= 50:
            errors.append("Traction Slip doit être entre 0 et 50 %")
        if not 0 <= self.traction_sensitivity <= 1:
            errors.append("Traction Sensitivity doit être entre 0 et 1")
        return errors

    def to_dict(self) -> dict:
        return {
            'mode': self.mode.value,
            'sync_duty': self.sync_duty,
            'sync_current': self.sync_current,
            'sync_rpm': self.sync_rpm,
            'balance_factor': self.balance_factor,
            'torque_bias': self.torque_bias,
            'speed_differential': self.speed_differential,
            'motor_direction_a': self.motor_direction_a,
            'motor_direction_b': self.motor_direction_b,
            'mirror_controls': self.mirror_controls,
            'traction_control': self.traction_control,
            'traction_slip': self.traction_slip,
            'traction_sensitivity': self.traction_sensitivity,
            'beep_on_startup': self.beep_on_startup,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'DualSetupConfig':
        return cls(
            mode=DualMode(d.get('mode', 'Independent')),
            sync_duty=d.get('sync_duty', False),
            sync_current=d.get('sync_current', False),
            sync_rpm=d.get('sync_rpm', False),
            balance_factor=d.get('balance_factor', 0.5),
            torque_bias=d.get('torque_bias', 0.0),
            speed_differential=d.get('speed_differential', 0.0),
            motor_direction_a=d.get('motor_direction_a', True),
            motor_direction_b=d.get('motor_direction_b', True),
            mirror_controls=d.get('mirror_controls', False),
            traction_control=d.get('traction_control', False),
            traction_slip=d.get('traction_slip', 10.0),
            traction_sensitivity=d.get('traction_sensitivity', 0.5),
            beep_on_startup=d.get('beep_on_startup', True),
        )


@dataclass
class IMUConfig:
    imu_type: IMUType = IMUType.NONE
    sample_rate: float = 100.0
    pitch_kp: float = 1.0
    pitch_ki: float = 0.1
    roll_kp: float = 1.0
    roll_ki: float = 0.1
    yaw_kp: float = 1.0
    yaw_ki: float = 0.1

    def validate(self) -> list[str]:
        errors = []
        if self.imu_type not in IMUType:
            errors.append("IMU Type invalide")
        if not 1 <= self.sample_rate <= 1000:
            errors.append("IMU Sample Rate doit être entre 1 et 1000 Hz")
        if not 0 <= self.pitch_kp <= 10:
            errors.append("Pitch Kp doit être entre 0 et 10")
        if not 0 <= self.pitch_ki <= 10:
            errors.append("Pitch Ki doit être entre 0 et 10")
        if not 0 <= self.roll_kp <= 10:
            errors.append("Roll Kp doit être entre 0 et 10")
        if not 0 <= self.roll_ki <= 10:
            errors.append("Roll Ki doit être entre 0 et 10")
        if not 0 <= self.yaw_kp <= 10:
            errors.append("Yaw Kp doit être entre 0 et 10")
        if not 0 <= self.yaw_ki <= 10:
            errors.append("Yaw Ki doit être entre 0 et 10")
        return errors

    def to_dict(self) -> dict:
        return {
            'imu_type': self.imu_type.value,
            'sample_rate': self.sample_rate,
            'pitch_kp': self.pitch_kp,
            'pitch_ki': self.pitch_ki,
            'roll_kp': self.roll_kp,
            'roll_ki': self.roll_ki,
            'yaw_kp': self.yaw_kp,
            'yaw_ki': self.yaw_ki,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'IMUConfig':
        return cls(
            imu_type=IMUType(d.get('imu_type', 'None')),
            sample_rate=d.get('sample_rate', 100.0),
            pitch_kp=d.get('pitch_kp', 1.0),
            pitch_ki=d.get('pitch_ki', 0.1),
            roll_kp=d.get('roll_kp', 1.0),
            roll_ki=d.get('roll_ki', 0.1),
            yaw_kp=d.get('yaw_kp', 1.0),
            yaw_ki=d.get('yaw_ki', 0.1),
        )


@dataclass
class CANConfig:
    mode: CANMode = CANMode.OFF
    id_a: int = 0
    id_b: int = 1
    baudrate: CANBaudrate = CANBaudrate.R500K
    status_1: bool = True
    status_2: bool = True
    status_3: bool = False
    status_4: bool = False
    fwd: int = 0

    def validate(self) -> list[str]:
        errors = []
        if self.mode not in CANMode:
            errors.append("CAN Mode invalide")
        if not 0 <= self.id_a <= 255:
            errors.append("CAN ID A doit être entre 0 et 255")
        if not 0 <= self.id_b <= 255:
            errors.append("CAN ID B doit être entre 0 et 255")
        if self.baudrate not in CANBaudrate:
            errors.append("CAN Baudrate invalide")
        if not 0 <= self.fwd <= 255:
            errors.append("CAN Fwd doit être entre 0 et 255")
        return errors

    def to_dict(self) -> dict:
        return {
            'mode': self.mode.value,
            'id_a': self.id_a,
            'id_b': self.id_b,
            'baudrate': self.baudrate.value,
            'status_1': self.status_1,
            'status_2': self.status_2,
            'status_3': self.status_3,
            'status_4': self.status_4,
            'fwd': self.fwd,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'CANConfig':
        return cls(
            mode=CANMode(d.get('mode', 'OFF')),
            id_a=d.get('id_a', 0),
            id_b=d.get('id_b', 1),
            baudrate=CANBaudrate(d.get('baudrate', '500k')),
            status_1=d.get('status_1', True),
            status_2=d.get('status_2', True),
            status_3=d.get('status_3', False),
            status_4=d.get('status_4', False),
            fwd=d.get('fwd', 0),
        )


@dataclass
class PeripheralConfig:
    headlight_on: bool = False
    headlight_intensity: int = 100
    brakelight_on: bool = False
    brakelight_mode: int = 0

    def validate(self) -> list[str]:
        errors = []
        if not 0 <= self.headlight_intensity <= 100:
            errors.append("Intensité feu avant doit être entre 0 et 100")
        if self.brakelight_mode not in (0, 1):
            errors.append("Mode feu stop doit être 0 (Fixe) ou 1 (Clignotant)")
        return errors

    def to_dict(self) -> dict:
        return {
            'headlight_on': self.headlight_on,
            'headlight_intensity': self.headlight_intensity,
            'brakelight_on': self.brakelight_on,
            'brakelight_mode': self.brakelight_mode,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'PeripheralConfig':
        return cls(
            headlight_on=d.get('headlight_on', False),
            headlight_intensity=d.get('headlight_intensity', 100),
            brakelight_on=d.get('brakelight_on', False),
            brakelight_mode=d.get('brakelight_mode', 0),
        )


@dataclass
class DualMotorConfig:
    motor_a: MotorConfig = field(default_factory=MotorConfig)
    motor_b: MotorConfig = field(default_factory=MotorConfig)
    battery: BatteryConfig = field(default_factory=BatteryConfig)
    dual_setup: DualSetupConfig = field(default_factory=DualSetupConfig)
    imu: IMUConfig = field(default_factory=IMUConfig)
    can: CANConfig = field(default_factory=CANConfig)
    peripherals: PeripheralConfig = field(default_factory=PeripheralConfig)
    name: str = "Standard"

    def validate(self) -> dict[str, list[str]]:
        return {
            'motor_a': self.motor_a.validate(),
            'motor_b': self.motor_b.validate(),
            'battery': self.battery.validate(),
            'dual_setup': self.dual_setup.validate(),
            'imu': self.imu.validate(),
            'can': self.can.validate(),
            'peripherals': self.peripherals.validate(),
        }

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'motor_a': self.motor_a.to_dict(),
            'motor_b': self.motor_b.to_dict(),
            'battery': self.battery.to_dict(),
            'dual_setup': self.dual_setup.to_dict(),
            'imu': self.imu.to_dict(),
            'can': self.can.to_dict(),
            'peripherals': self.peripherals.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'DualMotorConfig':
        return cls(
            name=d.get('name', 'Standard'),
            motor_a=MotorConfig.from_dict(d.get('motor_a', {})),
            motor_b=MotorConfig.from_dict(d.get('motor_b', {})),
            battery=BatteryConfig.from_dict(d.get('battery', {})),
            dual_setup=DualSetupConfig.from_dict(d.get('dual_setup', {})),
            imu=IMUConfig.from_dict(d.get('imu', {})),
            can=CANConfig.from_dict(d.get('can', {})),
            peripherals=PeripheralConfig.from_dict(d.get('peripherals', {})),
        )

    @classmethod
    def create_default(cls) -> 'DualMotorConfig':
        return cls()


DEFAULT_MOTOR_CONFIG = MotorConfig()

DEFAULT_DUAL_CONFIG = DualMotorConfig()


@dataclass
class FtescRealtimeData:
    controller_id: int = 0
    fault: int = 0
    inp_voltage: float = 0.0
    input_current: float = 0.0
    motor_current: float = 0.0
    rpm: float = 0.0
    duty_cycle_now: float = 0.0
    temp_fet: float = 0.0
    temp_motor: float = 0.0
    cpu_load: float = 0.0
    encoder_angle: float = 0.0
    firmware_version: str = ""


@dataclass
class FtescFault:
    FAULT_OVERVOLTAGE = 0x01
    FAULT_UNDERVOLTAGE = 0x02
    FAULT_OVERTEMP_FET = 0x04
    FAULT_OVERTEMP_MOTOR = 0x08
    FAULT_OVERCURRENT = 0x10
    FAULT_ENCODER = 0x20

    @staticmethod
    def decode(fault_code: int) -> list[str]:
        faults = []
        labels = {
            0x01: "Surtension",
            0x02: "Sous-tension",
            0x04: "Surtempérature FET",
            0x08: "Surtempérature moteur",
            0x10: "Surcourant",
            0x20: "Défaut encodeur",
        }
        for bit, label in labels.items():
            if fault_code & bit:
                faults.append(label)
        return faults if faults else ["Aucun défaut"]


@dataclass
class FtescFirmwareInfo:
    """Informations firmware du contrôleur."""
    controller_id: int = 0
    version_major: int = 0
    version_minor: int = 0
    version_patch: int = 0
    model_type: int = 0  # 0=FT60BD, 1=FT85BD, 2=FT85KS, etc.

    @property
    def version_string(self) -> str:
        return f"{self.version_major}.{self.version_minor}.{self.version_patch}"

    @property
    def model_name(self) -> str:
        models = {0: "FT60BD", 1: "FT85BD", 2: "FT85KS", 3: "FT80BD"}
        return models.get(self.model_type, f"Unknown({self.model_type})")


@dataclass
class FtescDualData:
    motor_a: FtescRealtimeData
    motor_b: FtescRealtimeData
    timestamp: float = 0.0

    @classmethod
    def create_empty(cls):
        return cls(
            motor_a=FtescRealtimeData(),
            motor_b=FtescRealtimeData(),
            timestamp=time.time()
        )
