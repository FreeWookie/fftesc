import customtkinter as ctk
from ftesc import (
    MotorConfig, MotorType, HallConfig, SensorlessMode,
    FOCConfig, FOCMode, RampConfig, BrakeConfig,
    InputControlConfig, ControlType, ControlCommand,
    LimitsConfig, SpeedPIDConfig, BatteryConfig, BatteryType,
    DualSetupConfig, DualMode, IMUConfig, IMUType,
    CANConfig, CANMode, CANBaudrate, PeripheralConfig,
    DualMotorConfig, UartCommand, build_frame,
)
from ftesc.config_protocol import (
    SEC_MOTOR, SEC_HALL, SEC_FOC, SEC_LIMITS, SEC_RAMP, SEC_BRAKE,
    SEC_INPUT_CTRL, SEC_SPEED_PID, SEC_BATTERY, SEC_DUAL, SEC_IMU, SEC_CAN,
    SECTION_NAMES,
    build_read_config_frame, build_write_config_frame,
    parse_config_response, decode_section_response,
)
from gui.styles.colors import COLORS
from gui.widgets.motor_selector import MotorSelector
from gui.tooltip import TooltipManager
from gui.descriptions import get_description as _get_description
from gui.widgets.helpers import disable_button_temp
from gui.i18n import _

_tooltip_mgr = TooltipManager()

def _get_tooltip(section_key: str, field_key: str) -> str | None:
    return _get_description(section_key, field_key)

SECTION_DISPLAY_NAMES = {
    "motor": _("config.section.motor"),
    "hall": _("config.section.hall"),
    "foc": _("config.section.foc"),
    "limits": _("config.section.limits"),
    "ramp": _("config.section.ramp"),
    "brake": _("config.section.brake"),
    "input_control": _("config.section.input_control"),
    "speed_pid": _("config.section.speed_pid"),
    "battery": _("config.section.battery"),
    "dual_setup": _("config.section.dual_setup"),
    "imu": _("config.section.imu"),
    "can": _("config.section.can"),
    "peripherals": _("config.section.peripherals"),
}

SECTION_CONFIG_CLS = {
    "motor": MotorConfig, "hall": HallConfig, "foc": FOCConfig,
    "limits": LimitsConfig, "ramp": RampConfig, "brake": BrakeConfig,
    "input_control": InputControlConfig, "speed_pid": SpeedPIDConfig,
    "battery": BatteryConfig, "dual_setup": DualSetupConfig,
    "imu": IMUConfig, "can": CANConfig, "peripherals": PeripheralConfig,
}

MOTOR_FIELDS = [
    (_("config.field.motor.motor_type"), "motor_type", "option", [(e.value, e) for e in MotorType]),
    (_("config.field.motor.pole_pairs"), "pole_pairs", "int", (1, 100)),
    (_("config.field.motor.resistance"), "resistance", "float", (0.001, 10.0)),
    (_("config.field.motor.inductance"), "inductance", "float", (0.001, 100.0)),
    (_("config.field.motor.kv_rating"), "kv_rating", "float", (1, 10000)),
    (_("config.field.motor.max_current"), "max_current", "float", (0, 200)),
    (_("config.field.motor.max_brake_current"), "max_brake_current", "float", (0, 200)),
    (_("config.field.motor.current_ramp_step"), "current_ramp_step", "float", (0.1, 100)),
    (_("config.field.motor.temp_motor_max"), "temp_motor_max", "float", (50, 150)),
    (_("config.field.motor.temp_motor_start"), "temp_motor_start", "float", (40, 130)),
]
HALL_FIELDS = [
    (_("config.field.hall.enabled"), "enabled", "bool"),
    (_("config.field.hall.direction"), "direction", "bool"),
    (_("config.field.hall.interpolation"), "interpolation", "bool"),
    (_("config.field.hall.sensorless_mode"), "sensorless_mode", "option", [(e.value, e) for e in SensorlessMode]),
    (_("config.field.hall.sensorless_erpm"), "sensorless_erpm", "float", (100, 50000)),
    (_("config.field.hall.sensorless_erpm_start"), "sensorless_erpm_start", "float", (100, 50000)),
    (_("config.field.hall.hall_table"), "hall_table", "table"),
]
FOC_FIELDS = [
    (_("config.field.foc.mode"), "mode", "option", [(str(e.value), e) for e in FOCMode]),
    (_("config.field.foc.fsw"), "fsw", "float", (5, 50)),
    (_("config.field.foc.dead_time"), "dead_time", "float", (0, 500)),
    (_("config.field.foc.openloop_rpm"), "openloop_rpm", "float", (100, 5000)),
    (_("config.field.foc.openloop_lock"), "openloop_lock", "bool"),
    (_("config.field.foc.current_kp"), "current_kp", "float", (0, 1)),
    (_("config.field.foc.current_ki"), "current_ki", "float", (0, 1)),
    (_("config.field.foc.observer_gain"), "observer_gain", "float", (0, 100)),
    (_("config.field.foc.observer_gain_slow"), "observer_gain_slow", "float", (0, 100)),
    (_("config.field.foc.pll_kp"), "pll_kp", "float", (0, 100000)),
    (_("config.field.foc.pll_ki"), "pll_ki", "float", (0, 100000)),
    (_("config.field.foc.antiwindup"), "antiwindup", "float", (0, 1)),
    (_("config.field.foc.duty_kp"), "duty_kp", "float", (0, 1)),
    (_("config.field.foc.duty_ki"), "duty_ki", "float", (0, 1)),
    (_("config.field.foc.sat_comp"), "sat_comp", "bool"),
]
LIMITS_FIELDS = [
    (_("config.field.limits.max_erpm"), "max_erpm", "float", (100, 200000)),
    (_("config.field.limits.max_erpm_reverse"), "max_erpm_reverse", "float", (100, 200000)),
    (_("config.field.limits.max_duty"), "max_duty", "float", (0, 0.95)),
    (_("config.field.limits.min_duty"), "min_duty", "float", (0, 0.5)),
    (_("config.field.limits.max_input_voltage"), "max_input_voltage", "float", (10, 100)),
    (_("config.field.limits.min_input_voltage"), "min_input_voltage", "float", (5, 80)),
    (_("config.field.limits.max_battery_current"), "max_battery_current", "float", (0, 200)),
    (_("config.field.limits.max_battery_current_rev"), "max_battery_current_rev", "float", (0, 200)),
    (_("config.field.limits.max_motor_current"), "max_motor_current", "float", (0, 200)),
    (_("config.field.limits.max_motor_current_rev"), "max_motor_current_rev", "float", (0, 200)),
    (_("config.field.limits.max_absolute_current"), "max_absolute_current", "float", (0, 300)),
    (_("config.field.limits.temp_fet_max"), "temp_fet_max", "float", (60, 120)),
    (_("config.field.limits.temp_fet_start"), "temp_fet_start", "float", (50, 110)),
    (_("config.field.limits.slow_abs_overvoltage"), "slow_abs_overvoltage", "bool"),
    (_("config.field.limits.slow_abs_undervoltage"), "slow_abs_undervoltage", "bool"),
]
RAMP_FIELDS = [
    (_("config.field.ramp.ramp_up_time"), "ramp_up_time", "float", (0, 10)),
    (_("config.field.ramp.ramp_down_time"), "ramp_down_time", "float", (0, 10)),
    (_("config.field.ramp.startup_speed"), "startup_speed", "float", (0, 100)),
    (_("config.field.ramp.cool_down_time"), "cool_down_time", "float", (0, 60)),
    (_("config.field.ramp.acceleration_current"), "acceleration_current", "float", (0, 200)),
    (_("config.field.ramp.deceleration_current"), "deceleration_current", "float", (0, 200)),
]
BRAKE_FIELDS = [
    (_("config.field.brake.brake_current"), "brake_current", "float", (0, 200)),
    (_("config.field.brake.brake_current_ramp"), "brake_current_ramp", "float", (0, 100)),
    (_("config.field.brake.regen_braking"), "regen_braking", "bool"),
    (_("config.field.brake.regen_voltage_max"), "regen_voltage_max", "float", (0, 100)),
    (_("config.field.brake.brake_temperature_limit"), "brake_temperature_limit", "float", (50, 150)),
]
INPUT_CONTROL_FIELDS = [
    (_("config.field.input_control.control_type"), "control_type", "option", [(e.value, e) for e in ControlType]),
    (_("config.field.input_control.input_voltage_min"), "input_voltage_min", "float", (5, 80)),
    (_("config.field.input_control.input_voltage_max"), "input_voltage_max", "float", (10, 100)),
    (_("config.field.input_control.throttle_curve"), "throttle_curve", "table"),
    (_("config.field.input_control.brake_curve"), "brake_curve", "table"),
    (_("config.field.input_control.throttle_center"), "throttle_center", "float", (0, 1)),
    (_("config.field.input_control.throttle_deadband"), "throttle_deadband", "float", (0, 0.5)),
    (_("config.field.input_control.control_deadband"), "control_deadband", "float", (0, 0.5)),
    (_("config.field.input_control.control_command"), "control_command", "option", [(e.value, e) for e in ControlCommand]),
    (_("config.field.input_control.ppm_pulse_min"), "ppm_pulse_min", "float", (0.5, 2.0)),
    (_("config.field.input_control.ppm_pulse_max"), "ppm_pulse_max", "float", (1.0, 3.0)),
    (_("config.field.input_control.ppm_pulse_center"), "ppm_pulse_center", "float", (1.0, 2.0)),
    (_("config.field.input_control.adc_voltage_min"), "adc_voltage_min", "float", (0, 3.3)),
    (_("config.field.input_control.adc_voltage_max"), "adc_voltage_max", "float", (0, 3.3)),
    (_("config.field.input_control.adc_voltage_center"), "adc_voltage_center", "float", (0, 3.3)),
]
SPEED_PID_FIELDS = [
    (_("config.field.speed_pid.kp"), "kp", "float", (0, 1)),
    (_("config.field.speed_pid.ki"), "ki", "float", (0, 1)),
    (_("config.field.speed_pid.kd"), "kd", "float", (0, 1)),
    (_("config.field.speed_pid.min_erpm"), "min_erpm", "float", (0, 50000)),
    (_("config.field.speed_pid.max_erpm"), "max_erpm", "float", (0, 200000)),
    (_("config.field.speed_pid.error_tolerance"), "error_tolerance", "float", (0, 1)),
]
BATTERY_FIELDS = [
    (_("config.field.battery.battery_type"), "battery_type", "option", [(e.value, e) for e in BatteryType]),
    (_("config.field.battery.cells"), "cells", "int", (1, 20)),
    (_("config.field.battery.capacity"), "capacity", "float", (1, 100)),
    (_("config.field.battery.voltage_max"), "voltage_max", "float", (10, 100)),
    (_("config.field.battery.voltage_min"), "voltage_min", "float", (5, 80)),
    (_("config.field.battery.cutoff_start"), "cutoff_start", "float", (5, 80)),
    (_("config.field.battery.cutoff_end"), "cutoff_end", "float", (5, 80)),
    (_("config.field.battery.charge_max"), "charge_max", "float", (0, 200)),
    (_("config.field.battery.internal_resistance"), "internal_resistance", "float", (0, 1)),
]
DUAL_FIELDS = [
    (_("config.field.dual.mode"), "mode", "option", [(e.value, e) for e in DualMode]),
    (_("config.field.dual.sync_duty"), "sync_duty", "bool"),
    (_("config.field.dual.sync_current"), "sync_current", "bool"),
    (_("config.field.dual.sync_rpm"), "sync_rpm", "bool"),
    (_("config.field.dual.balance_factor"), "balance_factor", "float", (0, 1)),
    (_("config.field.dual.torque_bias"), "torque_bias", "float", (-1, 1)),
    (_("config.field.dual.speed_differential"), "speed_differential", "float", (0, 100)),
    (_("config.field.dual.motor_direction_a"), "motor_direction_a", "bool"),
    (_("config.field.dual.motor_direction_b"), "motor_direction_b", "bool"),
    (_("config.field.dual.mirror_controls"), "mirror_controls", "bool"),
    (_("config.field.dual.traction_control"), "traction_control", "bool"),
    (_("config.field.dual.traction_slip"), "traction_slip", "float", (0, 50)),
    (_("config.field.dual.traction_sensitivity"), "traction_sensitivity", "float", (0, 1)),
    (_("config.field.dual.beep_on_startup"), "beep_on_startup", "bool"),
]
IMU_FIELDS = [
    (_("config.field.imu.imu_type"), "imu_type", "option", [(e.value, e) for e in IMUType]),
    (_("config.field.imu.sample_rate"), "sample_rate", "float", (1, 1000)),
    (_("config.field.imu.pitch_kp"), "pitch_kp", "float", (0, 10)),
    (_("config.field.imu.pitch_ki"), "pitch_ki", "float", (0, 10)),
    (_("config.field.imu.roll_kp"), "roll_kp", "float", (0, 10)),
    (_("config.field.imu.roll_ki"), "roll_ki", "float", (0, 10)),
    (_("config.field.imu.yaw_kp"), "yaw_kp", "float", (0, 10)),
    (_("config.field.imu.yaw_ki"), "yaw_ki", "float", (0, 10)),
]
CAN_FIELDS = [
    (_("config.field.can.mode"), "mode", "option", [(e.value, e) for e in CANBaudrate]),
    (_("config.field.can.id_a"), "id_a", "int", (0, 255)),
    (_("config.field.can.id_b"), "id_b", "int", (0, 255)),
    (_("config.field.can.baudrate"), "baudrate", "option", [(e.value, e) for e in CANBaudrate]),
    (_("config.field.can.status_1"), "status_1", "bool"),
    (_("config.field.can.status_2"), "status_2", "bool"),
    (_("config.field.can.status_3"), "status_3", "bool"),
    (_("config.field.can.status_4"), "status_4", "bool"),
    (_("config.field.can.fwd"), "fwd", "int", (0, 255)),
]
PERIPHERAL_FIELDS = [
    (_("config.field.peripherals.headlight_on"), "headlight_on", "bool"),
    (_("config.field.peripherals.headlight_intensity"), "headlight_intensity", "int", (0, 100)),
    (_("config.field.peripherals.brakelight_on"), "brakelight_on", "bool"),
    (_("config.field.peripherals.brakelight_mode"), "brakelight_mode", "option",
     [(_("config.field.peripherals.brakelight_fixed"), 0),
      (_("config.field.peripherals.brakelight_flashing"), 1)]),
]

SECTION_FIELDS_MAP = {
    "motor": MOTOR_FIELDS, "hall": HALL_FIELDS, "foc": FOC_FIELDS,
    "limits": LIMITS_FIELDS, "ramp": RAMP_FIELDS, "brake": BRAKE_FIELDS,
    "input_control": INPUT_CONTROL_FIELDS, "speed_pid": SPEED_PID_FIELDS,
    "battery": BATTERY_FIELDS, "dual_setup": DUAL_FIELDS,
    "imu": IMU_FIELDS, "can": CAN_FIELDS, "peripherals": PERIPHERAL_FIELDS,
}
SECTION_IDS = {v: k for k, v in SECTION_NAMES.items()}

MOTOR_SECTIONS = [
    ("motor", MOTOR_FIELDS, True),
    ("hall", HALL_FIELDS, True),
    ("foc", FOC_FIELDS, True),
    ("limits", LIMITS_FIELDS, True),
    ("ramp", RAMP_FIELDS, True),
    ("brake", BRAKE_FIELDS, True),
]
GLOBAL_SECTIONS = [
    ("input_control", INPUT_CONTROL_FIELDS, False),
    ("speed_pid", SPEED_PID_FIELDS, False),
    ("battery", BATTERY_FIELDS, False),
    ("dual_setup", DUAL_FIELDS, False),
    ("imu", IMU_FIELDS, False),
    ("can", CAN_FIELDS, False),
    ("peripherals", PERIPHERAL_FIELDS, False),
]

TAB_MODULES = {
    _("config.tab.motors"):    "motors",
    _("config.tab.limits"):    "limits",
    _("config.tab.dual"):      "dual",
    _("config.tab.inputs"):    "inputs",
    _("config.tab.battery"):   "battery",
    _("config.tab.comms"):     "comms",
    _("config.tab.advanced"):  "advanced",
    _("config.tab.lights"):    "lights",
}


def _validate_entry_range(entry, var, min_val, max_val, ftype, orig_border):
    try:
        val = ftype(var.get())
    except (ValueError, TypeError):
        entry.configure(border_color=COLORS['danger'])
        entry._ftesc_valid = False
        return False
    if min_val <= val <= max_val:
        entry.configure(border_color=orig_border)
        entry._ftesc_valid = True
        return True
    else:
        entry.configure(border_color=COLORS['danger'])
        entry._ftesc_valid = False
        return False


def _build_section_grid(tab, config_obj, section_key, title, icon, color, fields, border_color, visible=True, on_apply=None, on_read=None):
    frame = ctk.CTkFrame(tab, fg_color='transparent')
    if not visible:
        return frame, {}, {}
    ctk.CTkFrame(frame, height=2, fg_color=COLORS['bg_light']).pack(fill='x', padx=10, pady=(5, 0))
    header_frame = ctk.CTkFrame(frame, fg_color='transparent')
    header_frame.pack(fill='x', padx=10, pady=(8, 5))
    header = ctk.CTkLabel(header_frame, text=f"{icon} {title}",
        font=ctk.CTkFont(size=13, weight='bold'), text_color=color)
    header.pack(side='left')
    if on_read:
        read_btn = ctk.CTkButton(header_frame, text=_("config.section.read_button"),
            font=ctk.CTkFont(size=10),
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent_blue'], width=55, height=22)
        read_btn.configure(command=lambda b=read_btn, sk=section_key, co=config_obj: (
            disable_button_temp(b), on_read(sk, co)
        ))
        read_btn.pack(side='right', padx=(0, 4))
    if on_apply:
        apply_btn = ctk.CTkButton(header_frame, text=_("config.section.apply_button"),
            font=ctk.CTkFont(size=10),
            fg_color=color, hover_color=COLORS['accent'], width=80, height=22)
        apply_btn.configure(command=lambda b=apply_btn, sk=section_key, co=config_obj: (
            disable_button_temp(b), on_apply(sk, co)
        ))
        apply_btn.pack(side='right')
    grid = ctk.CTkFrame(frame, fg_color='transparent')
    grid.pack(fill='x', padx=10, pady=(0, 10))
    grid.grid_columnconfigure((0, 1), weight=1)
    grid.grid_columnconfigure(2, weight=1)
    grid.grid_columnconfigure(3, weight=1)
    entries = {}
    widgets = {}
    for i, (label, key, ftype, *meta) in enumerate(fields):
        col = (i % 2) * 2
        r = i // 2
        tooltip = _get_tooltip(section_key, key)
        ctk.CTkLabel(grid, text=label, font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']).grid(row=r, column=col, sticky='w', padx=(0, 2), pady=3)
        if ftype == "bool":
            var = ctk.BooleanVar(value=getattr(config_obj, key))
            sw = ctk.CTkSwitch(grid, variable=var, text="",
                fg_color=COLORS['bg_light'], progress_color=COLORS['accent_green'],
                button_hover_color=COLORS['accent'], onvalue=True, offvalue=False,
                switch_width=36, switch_height=18
            )
            sw.grid(row=r, column=col + 1, sticky='w', padx=(0, 5), pady=3)
            if tooltip:
                _tooltip_mgr.bind(sw, tooltip)
            entries[key] = var
        elif ftype == "option":
            pairs = meta[0]
            var = ctk.StringVar(value=str(getattr(config_obj, key).value if hasattr(getattr(config_obj, key), 'value') else getattr(config_obj, key)))
            om = ctk.CTkOptionMenu(grid, variable=var, values=[p[0] for p in pairs],
                fg_color=COLORS['bg_light'], button_color=color,
                font=ctk.CTkFont(size=11), width=130
            )
            om.grid(row=r, column=col + 1, sticky='w', padx=(0, 5), pady=3)
            if tooltip:
                _tooltip_mgr.bind(om, tooltip)
            entries[key] = (var, pairs)
        elif ftype == "table":
            raw = getattr(config_obj, key, [])
            var = ctk.StringVar(value=",".join(str(v) for v in (raw or [])))
            entry = ctk.CTkEntry(grid, textvariable=var, width=130,
                font=ctk.CTkFont(size=11), fg_color=COLORS['bg_light'], border_color=border_color)
            entry.grid(row=r, column=col + 1, sticky='w', padx=(0, 5), pady=3)
            entry._ftesc_valid = True
            entry._ftesc_range = None
            if tooltip:
                _tooltip_mgr.bind(entry, tooltip)
            entries[key] = var
            widgets[key] = entry
        else:
            var = ctk.StringVar(value=str(getattr(config_obj, key)))
            entry = ctk.CTkEntry(grid, textvariable=var, width=130,
                font=ctk.CTkFont(size=11), fg_color=COLORS['bg_light'], border_color=border_color)
            entry.grid(row=r, column=col + 1, sticky='w', padx=(0, 5), pady=3)
            if tooltip:
                _tooltip_mgr.bind(entry, tooltip)
            if len(meta) > 0:
                rng = meta[0]
                min_v, max_v = rng[0], rng[1]
                py_type = int if ftype == "int" else float
                entry._ftesc_valid = True
                entry._ftesc_range = (min_v, max_v, py_type, border_color)
                entry.bind("<FocusOut>",
                    lambda e, en=entry, va=var, mn=min_v, mx=max_v, ft=py_type, ob=border_color:
                        _validate_entry_range(en, va, mn, mx, ft, ob),
                    add="+")
                entry.bind("<Return>",
                    lambda e, en=entry, va=var, mn=min_v, mx=max_v, ft=py_type, ob=border_color:
                        _validate_entry_range(en, va, mn, mx, ft, ob),
                    add="+")
            else:
                entry._ftesc_valid = True
                entry._ftesc_range = None
            entries[key] = var
            widgets[key] = entry
    return frame, entries, widgets


def _read_section_entries(entries: dict, fields: list) -> dict:
    data = {}
    for label, key, ftype, *meta in fields:
        entry = entries[key]
        if ftype == "bool":
            data[key] = entry.get()
        elif ftype == "option":
            var, pairs = entry
            enum_map = {p[0]: p[1] for p in pairs}
            data[key] = enum_map[var.get()]
        elif ftype == "table":
            raw = entry.get().strip()
            data[key] = [float(v.strip()) for v in raw.split(",") if v.strip()]
        elif ftype == "int":
            data[key] = int(entry.get())
        else:
            data[key] = float(entry.get())
    return data


def _write_section_entries(entries: dict, fields: list, data: dict):
    for label, key, ftype, *meta in fields:
        entry = entries[key]
        if key not in data:
            continue
        value = data[key]
        if ftype == "bool":
            entry.set(bool(value))
        elif ftype == "option":
            var, pairs = entry
            enum_map_inv = {p[1]: p[0] for p in pairs}
            var.set(enum_map_inv.get(value, str(value)))
        elif ftype == "table":
            entry.set(",".join(str(v) for v in value))
        else:
            entry.set(str(value))


class ConfigPanel(ctk.CTkFrame):
    def __init__(self, parent, transport=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._transport = transport
        self._config_a = MotorConfig()
        self._config_b = MotorConfig()
        self._dual_config = DualMotorConfig()
        self._global_input_control = InputControlConfig()
        self._global_speed_pid = SpeedPIDConfig()

        toolbar = ctk.CTkFrame(self, fg_color='transparent')
        toolbar.pack(fill='x', padx=5, pady=(5, 2))
        self._btn_read_tab = ctk.CTkButton(toolbar, text=_("config.toolbar.read_tab"),
            font=ctk.CTkFont(size=10),
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent_blue'], width=90, height=24,
            command=self._read_current_tab)
        self._btn_read_tab.pack(side='left', padx=(0, 4))
        self._btn_write_tab = ctk.CTkButton(toolbar, text=_("config.toolbar.write_tab"),
            font=ctk.CTkFont(size=10),
            fg_color=COLORS['bg_light'], hover_color=COLORS['accent_green'], width=90, height=24,
            command=self._write_current_tab)
        self._btn_write_tab.pack(side='left', padx=(0, 4))
        self._btn_read_all = ctk.CTkButton(toolbar, text=_("config.toolbar.read_all"),
            font=ctk.CTkFont(size=10),
            fg_color=COLORS['accent_blue'], hover_color=COLORS['accent'], width=90, height=24,
            command=self._read_all)
        self._btn_read_all.pack(side='left', padx=(0, 4))
        self._btn_write_all = ctk.CTkButton(toolbar, text=_("config.toolbar.write_all"),
            font=ctk.CTkFont(size=10),
            fg_color=COLORS['accent_green'], hover_color=COLORS['success'], width=90, height=24,
            command=self._write_all)
        self._btn_write_all.pack(side='left', padx=(0, 4))
        self._btn_save_eeprom = ctk.CTkButton(toolbar, text=_("config.toolbar.save_eeprom"),
            font=ctk.CTkFont(size=10),
            fg_color=COLORS['mauve'], hover_color=COLORS['accent_orange'], width=100, height=24,
            command=self._save_to_eeprom)
        self._btn_save_eeprom.pack(side='left')

        self._status_text = ctk.StringVar(value="")
        self._busy = False
        self._bulk_total = 0
        self._bulk_done = 0
        self._bulk_sections: list[str] = []

        self._progress_var = ctk.DoubleVar(value=0)
        self._progress_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_medium'], height=26)
        self._progress_bar = ctk.CTkProgressBar(self._progress_frame,
            variable=self._progress_var, height=12, corner_radius=3,
            fg_color=COLORS['bg_dark'], progress_color=COLORS['accent_blue'])
        self._progress_bar.pack(side='right', padx=(10, 5), pady=4, fill='x', expand=True)
        self._progress_detail_label = ctk.CTkLabel(self._progress_frame, text="",
            font=ctk.CTkFont(size=10), text_color=COLORS['text_secondary'],
            width=220, anchor='e')
        self._progress_detail_label.pack(side='right', padx=(0, 10))

        status_bar = ctk.CTkFrame(self, fg_color=COLORS['bg_medium'], height=24)
        status_bar.pack(fill='x', side='bottom')
        ctk.CTkLabel(status_bar, textvariable=self._status_text,
            font=ctk.CTkFont(size=10),
            text_color=COLORS['text_secondary'], anchor='w').pack(side='left', padx=10)

        self.tabs = ctk.CTkTabview(self, fg_color=COLORS['bg_dark'])
        self.tabs.pack(fill="both", expand=True)

        self._tab_entries: dict = {}
        self._tab_widgets: dict = {}
        self._tab_meta: dict = {}
        self._contents: dict = {}
        self._selector: MotorSelector | None = None

        for tab_name in TAB_MODULES:
            self.tabs.add(tab_name)
            self._tab_entries[tab_name] = {}
            self._tab_widgets[tab_name] = {}

        self.tabs.configure(command=self._on_tab_change)
        self.after(50, lambda: self._load_tab_content(self.tabs.get()))

    def _set_status(self, msg: str):
        self._status_text.set(msg)
        self.update_idletasks()

    def show_progress(self, current: int, total: int, section_key: str = ""):
        self._progress_var.set(current / max(total, 1))
        label = SECTION_DISPLAY_NAMES.get(section_key, "")
        self._progress_detail_label.configure(
            text=_("config.progress.section_format").format(current=current, total=total)
            + (f" \u2014 {label}" if label else ""))
        self._progress_frame.pack(fill='x', side='bottom', before=self.tabs)
        self.update_idletasks()

    def hide_progress(self):
        self._progress_frame.pack_forget()
        self._progress_detail_label.configure(text="")
        self._progress_var.set(0)

    def _start_bulk(self, total: int, section_keys: list[str] | None = None):
        self._busy = True
        self._bulk_total = total
        self._bulk_done = 0
        self._bulk_sections = section_keys or []
        self.show_progress(0, total,
            self._bulk_sections[0] if self._bulk_sections else "")
        self._set_toolbar_state("disabled")

    def _set_toolbar_state(self, state: str):
        for btn in (self._btn_read_tab, self._btn_write_tab,
                    self._btn_read_all, self._btn_write_all,
                    self._btn_save_eeprom):
            try:
                btn.configure(state=state)
            except Exception:
                pass

    def _step_bulk(self, n: int = 1):
        self._bulk_done += n
        done = self._bulk_done
        total = self._bulk_total
        sec = self._bulk_sections[done - 1] if self._bulk_sections and done <= len(self._bulk_sections) else ""
        self.show_progress(done, total, sec)
        self._busy = False

    def _end_bulk(self):
        self._busy = False
        self.show_progress(self._bulk_total, self._bulk_total, "")
        self._set_toolbar_state("normal")
        self.after(1500, lambda: self.hide_progress())

    def _on_tab_change(self, tab_name=None):
        if tab_name is None:
            tab_name = self.tabs.get()
        if tab_name not in self._contents:
            self._load_tab_content(tab_name)

    def _load_tab_content(self, tab_name: str):
        import importlib
        mod_name = TAB_MODULES.get(tab_name)
        if not mod_name:
            return
        mod = importlib.import_module(f"gui.panels.config_tabs.{mod_name}")

        tab_frame = self.tabs.tab(tab_name)
        if tab_frame is None:
            return

        # Wrapper scrollable pour tous les onglets
        scroll = ctk.CTkScrollableFrame(tab_frame, fg_color='transparent')
        scroll.pack(fill='both', expand=True)

        meta = {"motor_specific": getattr(mod, "MOTOR_SPECIFIC", False)}
        if meta["motor_specific"]:
            sel_frame = ctk.CTkFrame(scroll, fg_color='transparent')
            sel_frame.pack(fill='x', padx=10, pady=(8, 4))
            self._selector = MotorSelector(sel_frame)
            self._selector.pack()
        else:
            self._selector = None

        entries = {}
        wmap = {}
        for sec_key, title, color, fields, bcolor in getattr(mod, "SECTIONS", []):
            obj = self._resolve_config_obj(sec_key, meta["motor_specific"])
            if obj is None:
                continue
            frame, sec_entries, sec_widgets = _build_section_grid(
                scroll, obj, sec_key, title, "", color, fields, bcolor,
                visible=True,
                on_apply=lambda sk, co, tn=tab_name: self._on_section_apply(sk, co, tn),
                on_read=lambda sk, co, tn=tab_name: self._on_section_read(sk, co, tn),
            )
            frame.pack(fill='x')
            entries[sec_key] = sec_entries
            if sec_widgets:
                wmap[sec_key] = sec_widgets
        self._tab_entries[tab_name] = entries
        self._tab_widgets[tab_name] = wmap
        self._tab_meta[tab_name] = meta
        self._contents[tab_name] = True
        if hasattr(mod, 'build_ui'):
            mod.build_ui(scroll, self)

    def _resolve_config_obj(self, sec_key: str, motor_specific: bool):
        if motor_specific:
            c = self._config_a
            if sec_key == "motor":
                return c
            return getattr(c, sec_key, None)
        if sec_key in ("input_control", "speed_pid"):
            return getattr(self, f"_global_{sec_key}")
        dual_map = {"battery": "battery", "dual_setup": "dual_setup",
                    "imu": "imu", "can": "can", "peripherals": "peripherals"}
        if sec_key in dual_map:
            return getattr(self._dual_config, dual_map[sec_key])
        return None

    def _on_section_apply(self, section_key: str, config_obj, tab_name: str):
        self.apply_config(section_key, config_obj, tab_name)

    def _on_section_read(self, section_key: str, config_obj, tab_name: str):
        self.read_config(section_key, tab_name)

    def get_target_ids(self, tab_name: str) -> list[int]:
        meta = self._tab_meta.get(tab_name, {})
        if not meta.get("motor_specific"):
            return [127]
        targets = [0, 1]
        if self._selector:
            val = self._selector.get()
            if val == "A":
                return [0]
            elif val == "B":
                return [1]
        return targets

    def _ensure_all_built(self):
        current = self.tabs.get()
        for tab_name in TAB_MODULES:
            if tab_name not in self._contents:
                self._on_tab_change(tab_name)
        if current:
            try:
                self.tabs.set(current)
            except Exception:
                pass

    def apply_config(self, section_key: str, config_obj, tab_name: str):
        self._validate_visible_fields()
        if not self._all_fields_valid():
            self._set_status(_("config.status.invalid_fields"))
            return
        transport = self._get_transport()
        if not transport or not transport.is_connected:
            self._set_status(_("config.status.no_controller"))
            return
        if self._busy:
            self._set_status(_("config.status.busy"))
            return
        sec_id = SECTION_IDS.get(section_key)
        if sec_id is None:
            self._set_status(_("config.status.unknown_section").format(section=section_key))
            return
        self._busy = True
        targets = self.get_target_ids(tab_name)
        for i, ctrl_id in enumerate(targets):
            if ctrl_id > 255:
                continue
            if i == 0:
                try:
                    transport.send(build_write_config_frame(ctrl_id, sec_id, config_obj))
                    self._set_status(_("config.status.write_ok").format(section=section_key, ctrl=ctrl_id))
                except Exception as e:
                    self._set_status(_("config.status.write_error").format(section=section_key, e=e))
            else:
                self.after(50, lambda c=ctrl_id, s=sec_id, o=config_obj: (
                    self._get_transport().send(build_write_config_frame(c, s, o)),
                    self._set_status(_("config.status.write_ok").format(section=section_key, ctrl=c))
                ))
        self.after(1500, lambda: setattr(self, '_busy', False))

    def read_config(self, section_key: str, tab_name: str):
        self._validate_visible_fields()
        transport = self._get_transport()
        if not transport or not transport.is_connected:
            self._set_status(_("config.status.no_controller"))
            return
        if self._busy:
            self._set_status(_("config.status.busy"))
            return
        sec_id = SECTION_IDS.get(section_key)
        if sec_id is None:
            self._set_status(_("config.status.unknown_section").format(section=section_key))
            return
        self._busy = True
        targets = self.get_target_ids(tab_name)
        for i, ctrl_id in enumerate(targets):
            if ctrl_id > 255:
                continue
            if i == 0:
                try:
                    transport.send(build_read_config_frame(ctrl_id, sec_id))
                    self._set_status(_("config.status.read_request").format(section=section_key, ctrl=ctrl_id))
                except Exception as e:
                    self._set_status(_("config.status.read_error").format(section=section_key, e=e))
            else:
                self.after(50, lambda c=ctrl_id, s=sec_id: (
                    self._get_transport().send(build_read_config_frame(c, s)),
                    self._set_status(_("config.status.read_request").format(section=SECTION_NAMES.get(s, '?'), ctrl=c))
                ))
        self.after(1500, lambda: setattr(self, '_busy', False))

    def on_config_read(self, controller_id: int, section_id: int, data_bytes: bytes):
        self._busy = False
        sec_key = SECTION_NAMES.get(section_id)
        if not sec_key:
            return
        config_obj = decode_section_response(controller_id, section_id, data_bytes)
        if config_obj is None:
            self._set_status(_("config.status.decode_error").format(section=sec_key))
            return
        self._update_local_config(controller_id, sec_key, config_obj)
        fields = SECTION_FIELDS_MAP.get(sec_key)
        if not fields:
            return
        data_dict = config_obj.to_dict() if hasattr(config_obj, 'to_dict') else config_obj.__dict__
        for tab_name in self._tab_entries:
            entries = self._tab_entries[tab_name]
            if sec_key in entries:
                _write_section_entries(entries[sec_key], fields, data_dict)
                self._set_status(_("config.status.read_ok").format(section=sec_key, ctrl=controller_id))
                self._step_bulk()
                break

    def _get_tab_sections(self, tab_name: str) -> list:
        try:
            mod = __import__(f"gui.panels.config_tabs.{TAB_MODULES[tab_name]}", fromlist=['SECTIONS'])
            return getattr(mod, "SECTIONS", [])
        except Exception:
            return []

    ALL_SEC_KEYS = ["motor","hall","foc","limits","ramp","brake"]
    ALL_GLOBAL_KEYS = ["input_control","speed_pid","battery","dual_setup","imu","can","peripherals"]

    def _read_all(self):
        transport = self._get_transport()
        if not transport or not transport.is_connected:
            self._set_status(_("config.status.no_controller"))
            return
        if self._busy:
            self._set_status(_("config.status.busy"))
            return
        keys = [sk for sk in self.ALL_SEC_KEYS for _ in (0, 1)] + list(self.ALL_GLOBAL_KEYS)
        total = len(keys)
        self._start_bulk(total, keys)
        idx = 0
        for sk in self.ALL_SEC_KEYS:
            sec_id = SECTION_IDS.get(sk)
            if sec_id is None: continue
            for ctrl_id in (0, 1):
                d = idx * 100
                self.after(d, lambda c=ctrl_id, s=sec_id: (
                    self._get_transport().send(build_read_config_frame(c, s))
                ))
                idx += 1
        for sk in self.ALL_GLOBAL_KEYS:
            sec_id = SECTION_IDS.get(sk)
            if sec_id is None: continue
            d = idx * 100
            self.after(d, lambda s=sec_id: (
                self._get_transport().send(build_read_config_frame(127, s))
            ))
            idx += 1
        self.after(total * 100 + 500, lambda: self._end_bulk())
        self._set_status(_("config.status.reading_all").format(total=total))

    def _write_all(self):
        transport = self._get_transport()
        if not transport or not transport.is_connected:
            self._set_status(_("config.status.no_controller"))
            return
        if self._busy:
            self._set_status(_("config.status.busy"))
            return
        self._validate_visible_fields()
        if not self._all_fields_valid():
            self._set_status(_("config.status.invalid_fields"))
            return
        keys = [sk for sk in self.ALL_SEC_KEYS for _ in (0, 1)] + list(self.ALL_GLOBAL_KEYS)
        total = len(keys)
        self._start_bulk(total, keys)
        idx = 0
        for sk in self.ALL_SEC_KEYS:
            sec_id = SECTION_IDS.get(sk)
            if sec_id is None: continue
            obj = self._resolve_config_obj(sk, True)
            if obj is None: continue
            for ctrl_id in (0, 1):
                d = idx * 100
                self.after(d, lambda c=ctrl_id, s=sec_id, o=obj: (
                    self._get_transport().send(build_write_config_frame(c, s, o)),
                    self._step_bulk()
                ))
                idx += 1
        for sk in self.ALL_GLOBAL_KEYS:
            sec_id = SECTION_IDS.get(sk)
            if sec_id is None: continue
            obj = self._resolve_config_obj(sk, False)
            if obj is None: continue
            d = idx * 100
            self.after(d, lambda s=sec_id, o=obj: (
                self._get_transport().send(build_write_config_frame(127, s, o)),
                self._step_bulk()
            ))
            idx += 1
        self.after(total * 100 + 500, lambda: self._end_bulk())
        self._set_status(_("config.status.writing_all").format(total=total))

    def _save_to_eeprom(self):
        transport = self._get_transport()
        if not transport or not transport.is_connected:
            self._set_status(_("config.status.no_controller"))
            return
        if self._busy:
            self._set_status(_("config.status.busy"))
            return
        import tkinter.messagebox as tkmb
        if not tkmb.askyesno(_("config.save_eeprom.dialog_title"),
            _("config.save_eeprom.confirm")):
            return
        self._busy = True
        self._set_toolbar_state("disabled")
        for i, ctrl_id in enumerate((0, 1, 127)):
            d = i * 50
            self.after(d, lambda c=ctrl_id: (
                self._get_transport().send(build_frame(UartCommand.REBOOT_FTESC, b''))
            ))
        self.after(300, self._save_eeprom_done)

    def _save_eeprom_done(self):
        self._busy = False
        self._set_toolbar_state("normal")
        self._set_status(_("config.status.eeprom_sent"))

    def _read_current_tab(self):
        tab_name = self.tabs.get()
        transport = self._get_transport()
        if not transport or not transport.is_connected:
            self._set_status(_("config.status.no_controller"))
            return
        if self._busy:
            self._set_status(_("config.status.busy"))
            return
        sections = self._get_tab_sections(tab_name)
        if not sections:
            self._set_status(_("config.status.no_sections").format(tab=tab_name))
            return
        s_keys = []
        for sec_key, x1, x2, x3, x4 in sections:
            sec_id = SECTION_IDS.get(sec_key)
            if sec_id is None:
                continue
            targets = self.get_target_ids(tab_name)
            for ctrl_id in targets:
                if ctrl_id > 255:
                    continue
                s_keys.append(sec_key)
        count = len(s_keys)
        self._start_bulk(count, s_keys)
        idx = 0
        for i, (sec_key, x1, x2, x3, x4) in enumerate(sections):
            sec_id = SECTION_IDS.get(sec_key)
            if sec_id is None:
                continue
            targets = self.get_target_ids(tab_name)
            for ctrl_id in targets:
                if ctrl_id > 255:
                    continue
                delay = i * 100 + (50 if ctrl_id != targets[0] else 0)
                self.after(delay, lambda c=ctrl_id, s=sec_id: (
                    self._get_transport().send(build_read_config_frame(c, s)),
                    self._step_bulk()
                ))
                idx += 1
        self.after(count * 100 + 200, lambda: self._end_bulk())
        self._set_status(_("config.status.reading_tab").format(count=count, tab=tab_name))

    def _write_current_tab(self):
        tab_name = self.tabs.get()
        transport = self._get_transport()
        if not transport or not transport.is_connected:
            self._set_status(_("config.status.no_controller"))
            return
        if self._busy:
            self._set_status(_("config.status.busy"))
            return
        self._validate_visible_fields()
        if not self._all_fields_valid():
            self._set_status(_("config.status.invalid_fields"))
            return
        sections = self._get_tab_sections(tab_name)
        if not sections:
            self._set_status(_("config.status.no_sections").format(tab=tab_name))
            return
        s_keys = []
        for sec_key, x1, x2, x3, x4 in sections:
            sec_id = SECTION_IDS.get(sec_key)
            if sec_id is None:
                continue
            targets = self.get_target_ids(tab_name)
            config_obj = self._resolve_config_obj(sec_key,
                self._tab_meta.get(tab_name, {}).get("motor_specific", False))
            if config_obj is None:
                continue
            for ctrl_id in targets:
                if ctrl_id > 255:
                    continue
                s_keys.append(sec_key)
        count = len(s_keys)
        self._start_bulk(count, s_keys)
        idx = 0
        for i, (sec_key, x1, x2, x3, x4) in enumerate(sections):
            sec_id = SECTION_IDS.get(sec_key)
            if sec_id is None:
                continue
            targets = self.get_target_ids(tab_name)
            config_obj = self._resolve_config_obj(sec_key,
                self._tab_meta.get(tab_name, {}).get("motor_specific", False))
            if config_obj is None:
                continue
            for ctrl_id in targets:
                if ctrl_id > 255:
                    continue
                delay = i * 100 + (50 if ctrl_id != targets[0] else 0)
                self.after(delay, lambda c=ctrl_id, s=sec_id, o=config_obj: (
                    self._get_transport().send(build_write_config_frame(c, s, o)),
                    self._step_bulk()
                ))
                idx += 1
        self.after(count * 100 + 200, lambda: self._end_bulk())
        self._set_status(_("config.status.writing_tab").format(count=count, tab=tab_name))

    def _update_local_config(self, controller_id: int, sec_key: str, config_obj):
        if sec_key == "motor":
            if controller_id == 0:
                self._config_a = config_obj
            else:
                self._config_b = config_obj
        elif sec_key in ("input_control", "speed_pid"):
            setattr(self, f"_global_{sec_key}", config_obj)
        elif sec_key in ("battery", "dual_setup", "imu", "can", "peripherals"):
            setattr(self._dual_config, sec_key, config_obj)
        else:
            if controller_id == 0:
                setattr(self._config_a, sec_key, config_obj)
            else:
                setattr(self._config_b, sec_key, config_obj)

    def collect_config_from_ui(self) -> DualMotorConfig:
        self._ensure_all_built()
        self._validate_visible_fields()
        if not self._all_fields_valid():
            raise ValueError(_("config.collect.invalid_fields"))
        mot_a, mot_b = {}, {}
        for sec, fields, _ in MOTOR_SECTIONS:
            entries = self._tab_entries.get(_("config.tab.motors"), {})
            if sec in entries:
                d = _read_section_entries(entries[sec], fields)
            else:
                entries2 = self._tab_entries.get(_("config.tab.limits"), {})
                if sec in entries2:
                    d = _read_section_entries(entries2[sec], fields)
                else:
                    d = {}
            if sec == "motor":
                mot_a.update(d)
                mot_b.update(d)
            else:
                mot_a[sec] = d
                mot_b[sec] = d
        a_fields = {f[1] for f in MOTOR_FIELDS}
        for sec, fields, _ in GLOBAL_SECTIONS:
            entries = self._tab_entries.get(_("config.tab.inputs"), {})
            if sec not in entries:
                for tn in TAB_MODULES:
                    entries = self._tab_entries.get(tn, {})
                    if sec in entries:
                        break
            if sec in entries:
                d = _read_section_entries(entries[sec], fields)
                if sec == "input_control":
                    self._global_input_control = InputControlConfig(**d)
                elif sec == "speed_pid":
                    self._global_speed_pid = SpeedPIDConfig(**d)
                elif sec == "battery":
                    self._dual_config.battery = BatteryConfig(**d)
                elif sec == "dual_setup":
                    self._dual_config.dual_setup = DualSetupConfig(**d)
                elif sec == "imu":
                    self._dual_config.imu = IMUConfig(**d)
                elif sec == "can":
                    self._dual_config.can = CANConfig(**d)
        self._config_a = MotorConfig(**{**self._config_a.to_dict(), **mot_a})
        self._config_b = MotorConfig(**{**self._config_b.to_dict(), **mot_b})
        return DualMotorConfig(
            motor_a=self._config_a,
            motor_b=self._config_b,
            battery=self._dual_config.battery,
            dual_setup=self._dual_config.dual_setup,
            imu=self._dual_config.imu,
            can=self._dual_config.can,
        )

    def _all_fields_valid(self) -> bool:
        for tab_name in TAB_MODULES:
            wmap = self._tab_widgets.get(tab_name, {})
            for sec_key, sec_widgets in wmap.items():
                for field_key, entry in sec_widgets.items():
                    if hasattr(entry, '_ftesc_valid') and not entry._ftesc_valid:
                        return False
        return True

    def _validate_visible_fields(self):
        for tab_name in TAB_MODULES:
            if tab_name not in self._contents:
                continue
            wmap = self._tab_widgets.get(tab_name, {})
            for sec_key, sec_widgets in wmap.items():
                for field_key, entry in sec_widgets.items():
                    if hasattr(entry, '_ftesc_range') and entry._ftesc_range:
                        min_v, max_v, py_type, ob = entry._ftesc_range
                        var = self._tab_entries.get(tab_name, {}).get(sec_key, {}).get(field_key)
                        if var is not None and not isinstance(var, tuple):
                            _validate_entry_range(entry, var, min_v, max_v, py_type, ob)

    def _get_transport(self):
        return self._transport

    def apply_config_to_ui(self, config: DualMotorConfig):
        self._ensure_all_built()
        self._config_a = config.motor_a
        self._config_b = config.motor_b
        self._dual_config = config
        for tab_name, entries_list in [(tn, self._tab_entries.get(tn, {})) for tn in TAB_MODULES]:
            sec_map = {}
            try:
                mod = __import__(f"gui.panels.config_tabs.{TAB_MODULES[tab_name]}", fromlist=['SECTIONS'])
                for sec_key, x1, color, fields, bcolor in mod.SECTIONS:
                    sec_map[sec_key] = fields
            except Exception:
                continue
            for sec_key, sec_entries in entries_list.items():
                obj = self._resolve_config_obj(sec_key,
                    self._tab_meta.get(tab_name, {}).get("motor_specific", False))
                if obj is None:
                    continue
                fields = sec_map.get(sec_key)
                if fields:
                    _write_section_entries(sec_entries, fields,
                        obj.to_dict() if hasattr(obj, 'to_dict') else obj.__dict__)
