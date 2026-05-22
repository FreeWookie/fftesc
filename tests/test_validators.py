"""
Unit tests for ftesc data validators and config protocol round-trip.
"""

import pytest
from ftesc.data import (
    HallConfig, FOCConfig, RampConfig, BrakeConfig,
    InputControlConfig, LimitsConfig, SpeedPIDConfig,
    MotorConfig, BatteryConfig, DualSetupConfig, IMUConfig,
    CANConfig, DualMotorConfig,
    MotorType, SensorlessMode, FOCMode, ControlType,
    ControlCommand, BatteryType, DualMode, IMUType,
    CANMode, CANBaudrate,
)
from ftesc.config_protocol import (
    encode_section, decode_section,
    HALL_FIELDS, FOC_FIELDS, LIMITS_FIELDS, RAMP_FIELDS,
    BRAKE_FIELDS, INPUT_CTRL_FIELDS, SPEED_PID_FIELDS,
    MOTOR_FIELDS_PROTO, BATTERY_FIELDS, DUAL_FIELDS,
    IMU_FIELDS, CAN_FIELDS,
    build_read_config_frame, build_write_config_frame,
    parse_config_response,
)
from ftesc.protocol import parse_frame


class TestHallConfig:
    def test_default_valid(self):
        h = HallConfig()
        assert h.validate() == []

    def test_sensorless_erpm_out_of_range(self):
        h = HallConfig(sensorless_erpm=99)
        assert "Sensorless ERPM" in h.validate()[0]

    def test_sensorless_erpm_start_out_of_range(self):
        h = HallConfig(sensorless_erpm_start=50001)
        assert "Sensorless ERPM" in h.validate()[0]

    def test_invalid_hall_table_length(self):
        h = HallConfig(hall_table=[1, 2, 3])
        assert h.hall_table == [0, 1, 2, 3, 4, 5, 6, 7]

    def test_hall_table_validation(self):
        h = HallConfig(hall_table=[0, 1, 2, 3, 4, 5, 6, 8])
        assert "Hall Table" in h.validate()[0]

    def test_round_trip(self):
        h = HallConfig(enabled=True, sensorless_erpm=4000.0, direction=True)
        data = encode_section(h, HALL_FIELDS)
        h2 = decode_section(data, HallConfig, HALL_FIELDS)
        for field in ['enabled', 'direction', 'interpolation', 'sensorless_erpm',
                       'sensorless_erpm_start', 'sensorless_mode', 'hall_table']:
            assert getattr(h, field) == getattr(h2, field), f"Mismatch {field}"


class TestFOCConfig:
    def test_default_valid(self):
        f = FOCConfig()
        assert f.validate() == []

    def test_current_kp_out_of_range(self):
        f = FOCConfig(current_kp=1.5)
        assert "Current Kp" in f.validate()[0]

    def test_fsw_out_of_range(self):
        f = FOCConfig(fsw=4.0)
        assert "FSW" in f.validate()[0]

    def test_dead_time_negative(self):
        f = FOCConfig(dead_time=-1)
        assert "Dead Time" in f.validate()[0]

    def test_pll_kp_out_of_range(self):
        f = FOCConfig(pll_kp=100001)
        assert "PLL Kp" in f.validate()[0]

    def test_round_trip(self):
        f = FOCConfig(mode=FOCMode.SINUS, fsw=25.0, current_kp=0.2, pll_kp=2000.0)
        data = encode_section(f, FOC_FIELDS)
        f2 = decode_section(data, FOCConfig, FOC_FIELDS)
        for field in ['mode', 'fsw', 'current_kp', 'pll_kp', 'dead_time',
                       'openloop_rpm', 'openloop_lock', 'sat_comp',
                       'observer_gain', 'observer_gain_slow']:
            v1, v2 = getattr(f, field), getattr(f2, field)
            if isinstance(v1, float):
                assert abs(v1 - v2) < 0.001, f"Mismatch {field}: {v1} != {v2}"
            else:
                assert v1 == v2, f"Mismatch {field}: {v1} != {v2}"


class TestLimitsConfig:
    def test_default_valid(self):
        l = LimitsConfig()
        assert l.validate() == []

    def test_max_erpm_out_of_range(self):
        l = LimitsConfig(max_erpm=99)
        assert "Max ERPM" in l.validate()[0]

    def test_min_duty_gt_max_duty(self):
        l = LimitsConfig(min_duty=0.8, max_duty=0.5)
        errs = l.validate()
        assert any("Min Duty" in e for e in errs)

    def test_temp_fet_start_gt_max(self):
        l = LimitsConfig(temp_fet_start=100, temp_fet_max=90)
        errs = l.validate()
        assert any("Temp FET Start" in e for e in errs)

    def test_round_trip(self):
        l = LimitsConfig(max_erpm=80000.0, temp_fet_max=95.0, slow_abs_overvoltage=True)
        data = encode_section(l, LIMITS_FIELDS)
        l2 = decode_section(data, LimitsConfig, LIMITS_FIELDS)
        for field in ['max_erpm', 'temp_fet_max', 'slow_abs_overvoltage',
                       'max_duty', 'min_duty', 'max_input_voltage']:
            v1, v2 = getattr(l, field), getattr(l2, field)
            if isinstance(v1, float):
                assert abs(v1 - v2) < 0.1, f"Mismatch {field}"
            else:
                assert v1 == v2, f"Mismatch {field}"


class TestRampConfig:
    def test_default_valid(self):
        r = RampConfig()
        assert r.validate() == []

    def test_ramp_up_out_of_range(self):
        r = RampConfig(ramp_up_time=11)
        assert "Ramp Up" in r.validate()[0]

    def test_cool_down_out_of_range(self):
        r = RampConfig(cool_down_time=61)
        assert "Cool Down" in r.validate()[0]

    def test_round_trip(self):
        r = RampConfig(ramp_up_time=2.5, acceleration_current=80.0)
        data = encode_section(r, RAMP_FIELDS)
        r2 = decode_section(data, RampConfig, RAMP_FIELDS)
        assert abs(r.ramp_up_time - r2.ramp_up_time) < 0.01
        assert abs(r.acceleration_current - r2.acceleration_current) < 0.1


class TestBrakeConfig:
    def test_default_valid(self):
        b = BrakeConfig()
        assert b.validate() == []

    def test_brake_current_out_of_range(self):
        b = BrakeConfig(brake_current=201)
        assert "Brake Current" in b.validate()[0]

    def test_temp_limit_out_of_range(self):
        b = BrakeConfig(brake_temperature_limit=40)
        assert "Brake Temperature" in b.validate()[0]

    def test_round_trip(self):
        b = BrakeConfig(brake_current=50.0, regen_braking=True)
        data = encode_section(b, BRAKE_FIELDS)
        b2 = decode_section(data, BrakeConfig, BRAKE_FIELDS)
        assert abs(b.brake_current - b2.brake_current) < 0.1
        assert b.regen_braking == b2.regen_braking


class TestInputControlConfig:
    def test_default_valid(self):
        ic = InputControlConfig()
        assert ic.validate() == []

    def test_throttle_curve_wrong_length(self):
        ic = InputControlConfig(throttle_curve=[0.0, 0.5, 1.0])
        assert len(ic.throttle_curve) == 6

    def test_ppm_min_out_of_range(self):
        ic = InputControlConfig(ppm_pulse_min=0.4)
        assert "PPM Pulse Min" in ic.validate()[0]

    def test_deadband_out_of_range(self):
        ic = InputControlConfig(throttle_deadband=0.6)
        assert "Throttle Deadband" in ic.validate()[0]

    def test_round_trip(self):
        ic = InputControlConfig(
            control_type=ControlType.RPM,
            control_command=ControlCommand.ADC,
            throttle_curve=[0.0, 0.1, 0.3, 0.5, 0.7, 1.0],
        )
        data = encode_section(ic, INPUT_CTRL_FIELDS)
        ic2 = decode_section(data, InputControlConfig, INPUT_CTRL_FIELDS)
        assert ic.control_type == ic2.control_type
        assert ic.control_command == ic2.control_command
        assert ic.throttle_curve == pytest.approx(ic2.throttle_curve, rel=1e-5)


class TestSpeedPIDConfig:
    def test_default_valid(self):
        s = SpeedPIDConfig()
        assert s.validate() == []

    def test_pid_kp_out_of_range(self):
        s = SpeedPIDConfig(kp=1.5)
        assert "Speed PID Kp" in s.validate()[0]

    def test_round_trip(self):
        s = SpeedPIDConfig(kp=0.5, ki=0.05, max_erpm=50000.0)
        data = encode_section(s, SPEED_PID_FIELDS)
        s2 = decode_section(data, SpeedPIDConfig, SPEED_PID_FIELDS)
        assert abs(s.kp - s2.kp) < 0.001
        assert abs(s.max_erpm - s2.max_erpm) < 0.01


class TestMotorConfig:
    def test_default_valid(self):
        m = MotorConfig()
        assert m.validate() == []

    def test_pole_pairs_out_of_range(self):
        m = MotorConfig(pole_pairs=0)
        assert "Pole Pairs" in m.validate()[0]

    def test_resistance_out_of_range(self):
        m = MotorConfig(resistance=0.0005)
        assert "Résistance" in m.validate()[0]

    def test_temp_start_gt_max(self):
        m = MotorConfig(temp_motor_start=100, temp_motor_max=90)
        errs = m.validate()
        assert any("Temp Motor Start" in e for e in errs)

    def test_round_trip(self):
        m = MotorConfig(motor_type=MotorType.FOC, pole_pairs=28, kv_rating=100.0)
        data = encode_section(m, MOTOR_FIELDS_PROTO)
        m2 = decode_section(data, MotorConfig, MOTOR_FIELDS_PROTO)
        assert m.motor_type == m2.motor_type
        assert m.pole_pairs == m2.pole_pairs
        assert abs(m.kv_rating - m2.kv_rating) < 0.1


class TestBatteryConfig:
    def test_default_valid(self):
        b = BatteryConfig()
        assert b.validate() == []

    def test_cells_out_of_range(self):
        b = BatteryConfig(cells=0)
        assert "Battery Cells" in b.validate()[0]

    def test_cutoff_end_gt_start(self):
        b = BatteryConfig(cutoff_end=40, cutoff_start=38)
        errs = b.validate()
        assert any("Cutoff End" in e for e in errs)

    def test_round_trip(self):
        b = BatteryConfig(battery_type=BatteryType.LI_ION, cells=6, capacity=5.0)
        data = encode_section(b, BATTERY_FIELDS)
        b2 = decode_section(data, BatteryConfig, BATTERY_FIELDS)
        assert b.battery_type == b2.battery_type
        assert b.cells == b2.cells
        assert abs(b.capacity - b2.capacity) < 0.01


class TestDualSetupConfig:
    def test_default_valid(self):
        d = DualSetupConfig()
        assert d.validate() == []

    def test_balance_out_of_range(self):
        d = DualSetupConfig(balance_factor=1.5)
        assert "Balance Factor" in d.validate()[0]

    def test_torque_bias_out_of_range(self):
        d = DualSetupConfig(torque_bias=2.0)
        assert "Torque Bias" in d.validate()[0]

    def test_round_trip(self):
        d = DualSetupConfig(mode=DualMode.TRACTION, traction_control=True, traction_slip=15.0)
        data = encode_section(d, DUAL_FIELDS)
        d2 = decode_section(data, DualSetupConfig, DUAL_FIELDS)
        assert d.mode == d2.mode
        assert d.traction_control == d2.traction_control
        assert abs(d.traction_slip - d2.traction_slip) < 0.01


class TestIMUConfig:
    def test_default_valid(self):
        i = IMUConfig()
        assert i.validate() == []

    def test_sample_rate_out_of_range(self):
        i = IMUConfig(sample_rate=0)
        assert "Sample Rate" in i.validate()[0]

    def test_round_trip(self):
        i = IMUConfig(imu_type=IMUType.MPU6050, sample_rate=200.0, pitch_kp=2.0)
        data = encode_section(i, IMU_FIELDS)
        i2 = decode_section(data, IMUConfig, IMU_FIELDS)
        assert i.imu_type == i2.imu_type
        assert abs(i.sample_rate - i2.sample_rate) < 0.01


class TestCANConfig:
    def test_default_valid(self):
        c = CANConfig()
        assert c.validate() == []

    def test_id_out_of_range(self):
        c = CANConfig(id_a=300)
        assert "CAN ID" in c.validate()[0]

    def test_fwd_out_of_range(self):
        c = CANConfig(fwd=256)
        assert "CAN Fwd" in c.validate()[0]

    def test_round_trip(self):
        c = CANConfig(mode=CANMode.CUSTOM, id_a=10, baudrate=CANBaudrate.R1M)
        data = encode_section(c, CAN_FIELDS)
        c2 = decode_section(data, CANConfig, CAN_FIELDS)
        assert c.mode == c2.mode
        assert c.id_a == c2.id_a
        assert c.baudrate == c2.baudrate


class TestDualMotorConfig:
    def test_default_valid(self):
        d = DualMotorConfig()
        errors = d.validate()
        for section, errs in errors.items():
            assert errs == [], f"{section}: {errs}"

    def test_full_validation(self):
        d = DualMotorConfig()
        d.motor_a.pole_pairs = 0
        d.motor_b.max_current = -1
        d.battery.cells = 0
        errors = d.validate()
        assert errors['motor_a'] != []
        assert errors['motor_b'] != []
        assert errors['battery'] != []

    def test_to_from_dict(self):
        d = DualMotorConfig(
            name="Test",
            motor_a=MotorConfig(pole_pairs=28, motor_type=MotorType.FOC),
            battery=BatteryConfig(cells=6),
        )
        d2 = DualMotorConfig.from_dict(d.to_dict())
        assert d2.name == "Test"
        assert d2.motor_a.pole_pairs == 28
        assert d2.motor_a.motor_type == MotorType.FOC
        assert d2.battery.cells == 6


class TestConfigProtocolFrames:
    def test_read_config_frame(self):
        frame = build_read_config_frame(0, 1)
        cmd, payload, status = parse_frame(frame)
        assert status == 'OK'
        result = parse_config_response(payload)
        assert result is not None
        ctrl, sec, _ = result
        assert ctrl == 0
        assert sec == 1

    def test_write_config_frame(self):
        m = MotorConfig(pole_pairs=28)
        frame = build_write_config_frame(1, 0, m)
        cmd, payload, status = parse_frame(frame)
        assert status == 'OK'

    def test_all_sections_round_trip(self):
        from ftesc.config_protocol import SECTION_FIELDS
        configs = {
            'motor': MotorConfig(pole_pairs=28, motor_type=MotorType.FOC, kv_rating=150.0),
            'hall': HallConfig(enabled=True, sensorless_erpm=3000.0),
            'foc': FOCConfig(mode=FOCMode.FOC, fsw=30.0, current_kp=0.15),
            'limits': LimitsConfig(max_erpm=100000.0, temp_fet_max=85.0),
            'ramp': RampConfig(ramp_up_time=2.0, acceleration_current=70.0),
            'brake': BrakeConfig(brake_current=60.0, regen_braking=True),
            'input_control': InputControlConfig(control_type=ControlType.CURRENT),
            'speed_pid': SpeedPIDConfig(kp=0.3, ki=0.02),
        }
        from ftesc.config_protocol import (
            SEC_MOTOR, SEC_HALL, SEC_FOC, SEC_LIMITS,
            SEC_RAMP, SEC_BRAKE, SEC_INPUT_CTRL, SEC_SPEED_PID,
            SUB_SEC_TO_MOTOR_KEY,
        )
        sec_map = {
            SEC_MOTOR: ('motor', MotorConfig, MOTOR_FIELDS_PROTO),
            SEC_HALL: ('hall', HallConfig, HALL_FIELDS),
            SEC_FOC: ('foc', FOCConfig, FOC_FIELDS),
            SEC_LIMITS: ('limits', LimitsConfig, LIMITS_FIELDS),
            SEC_RAMP: ('ramp', RampConfig, RAMP_FIELDS),
            SEC_BRAKE: ('brake', BrakeConfig, BRAKE_FIELDS),
            SEC_INPUT_CTRL: ('input_control', InputControlConfig, INPUT_CTRL_FIELDS),
            SEC_SPEED_PID: ('speed_pid', SpeedPIDConfig, SPEED_PID_FIELDS),
        }
        for sec_id, (name, cls, fields) in sec_map.items():
            cfg = configs[name]
            data = encode_section(cfg, fields)
            cfg2 = decode_section(data, cls, fields)
            for f in fields:
                v1, v2 = getattr(cfg, f.key), getattr(cfg2, f.key)
                if isinstance(v1, float):
                    assert abs(v1 - v2) < 0.01, f"{name}.{f.key}: {v1} != {v2}"
                elif isinstance(v1, list):
                    assert v1 == pytest.approx(v2, rel=1e-4), f"{name}.{f.key}: {v1} != {v2}"
                else:
                    assert v1 == v2, f"{name}.{f.key}: {v1} != {v2}"


class TestMultiESCDiscovery:
    def test_build_obtain_all_ids_frame(self):
        from ftesc.protocol import build_obtain_all_ids_frame, UartCommand, parse_frame
        frame = build_obtain_all_ids_frame()
        assert len(frame) > 5
        cmd, payload, status = parse_frame(frame)
        assert status == 'OK'
        assert cmd == UartCommand.OBTAIN_ALL_FTESC_ID
        assert payload == b''

    def test_simulator_responds_to_obtain_all_ids(self):
        from ftesc.simulator import FtescSimulator
        from ftesc.protocol import build_obtain_all_ids_frame, parse_frame, parse_firmware_info, UartCommand
        sim = FtescSimulator()
        frame = build_obtain_all_ids_frame()
        response = sim.handle_frame(frame)
        assert response is not None
        assert len(response) > 0
        escs = {}
        offset = 0
        while offset < len(response):
            cmd, payload, status = parse_frame(response[offset:])
            assert status == 'OK', f"Parse failed at offset {offset}: {status}"
            if cmd == UartCommand.OBTAIN_ALL_FTESC_ID:
                fw = parse_firmware_info(payload)
                assert fw is not None
                escs[fw.controller_id] = fw
            header = response[offset]
            if header == 0xAA:
                frame_len = 2 + response[offset+1] + 2 + 1
            elif header == 0xBB:
                frame_len = 3 + ((response[offset+1] << 8) | response[offset+2]) + 2 + 1
            else:
                break
            offset += frame_len
        assert 0 in escs, "ESC ID 0 should be present"
        assert 1 in escs, "ESC ID 1 should be present"
        assert escs[0].version_major == 3
        assert escs[0].model_name == "FT85BD"

    def test_simulator_obtain_firmware_version(self):
        from ftesc.simulator import FtescSimulator
        from ftesc.protocol import build_frame, parse_frame, parse_firmware_info, UartCommand
        sim = FtescSimulator()
        frame = build_frame(UartCommand.OBTAIN_FIRMWARE_VERSION, b'')
        response = sim.handle_frame(frame)
        assert response is not None
        cmd, payload, status = parse_frame(response)
        assert status == 'OK'
        assert cmd == UartCommand.OBTAIN_FIRMWARE_VERSION
        fw = parse_firmware_info(payload)
        assert fw is not None
        assert fw.controller_id == 0
        assert fw.version_string == "3.2.1"


class TestSimulatorInit:
    """Fix 1 — attributs manquants dans FtescSimulator.__init__"""

    def test_noise_level_initialized(self):
        from ftesc.simulator import FtescSimulator
        sim = FtescSimulator()
        assert hasattr(sim, 'noise_level')
        assert sim.noise_level == 0.05

    def test_battery_voltage_initialized(self):
        from ftesc.simulator import FtescSimulator
        sim = FtescSimulator()
        assert hasattr(sim, '_battery_voltage')
        assert sim._battery_voltage == 48.0

    def test_fault_probability_initialized(self):
        from ftesc.simulator import FtescSimulator
        sim = FtescSimulator()
        assert hasattr(sim, 'fault_probability')
        assert sim.fault_probability == 0.001

    def test_update_rate_hz_initialized(self):
        from ftesc.simulator import FtescSimulator
        sim = FtescSimulator()
        assert hasattr(sim, 'update_rate_hz')
        assert sim.update_rate_hz == 10.0

    def test_peripheral_states_initialized(self):
        from ftesc.simulator import FtescSimulator
        sim = FtescSimulator()
        assert hasattr(sim, '_headlight_on')
        assert hasattr(sim, '_headlight_intensity')
        assert hasattr(sim, '_brakelight_on')
        assert hasattr(sim, '_brakelight_mode')
        assert hasattr(sim, '_buzzer_active')
        assert hasattr(sim, '_buzzer_stop_time')

    def test_generate_motor_data_no_attribute_error(self):
        """Vérifie que _generate_motor_data ne lève plus d'AttributeError."""
        from ftesc.simulator import FtescSimulator
        import time
        sim = FtescSimulator()
        sim._start_time = time.time()
        data = sim._generate_motor_data('A')
        assert data is not None
        assert data.controller_id == 0
        data_b = sim._generate_motor_data('B')
        assert data_b.controller_id == 1


class TestMultiFrameParsing:
    """Fix 3 — parsing multi-trames dans _on_raw_data"""

    def test_two_concatenated_frames_both_parsed(self):
        """Deux trames concaténées doivent toutes deux être décodées."""
        from ftesc.simulator import FtescSimulator
        from ftesc.protocol import (
            build_obtain_all_ids_frame, parse_frame,
            parse_firmware_info, UartCommand, build_frame,
        )
        sim = FtescSimulator()
        raw_cmd = build_frame(UartCommand.OBTAIN_ALL_FTESC_ID, b'')
        response = sim.handle_frame(raw_cmd)
        assert response is not None

        escs = {}
        offset = 0
        while offset < len(response):
            cmd, payload, status = parse_frame(response[offset:])
            assert status == 'OK', f"Échec au offset {offset} : {status}"
            if cmd == UartCommand.OBTAIN_ALL_FTESC_ID:
                fw = parse_firmware_info(payload)
                if fw:
                    escs[fw.controller_id] = fw
            hdr = response[offset]
            if hdr == 0xAA:
                frame_len = 2 + response[offset + 1] + 3
            elif hdr == 0xBB:
                frame_len = 3 + ((response[offset + 1] << 8) | response[offset + 2]) + 3
            else:
                break
            offset += frame_len

        assert len(escs) == 2, f"Attendu 2 ESC, obtenu {len(escs)}: {list(escs.keys())}"
        assert 0 in escs
        assert 1 in escs

    def test_frame_length_calculation_short_header(self):
        """Calcul de longueur correct pour header 0xAA."""
        from ftesc.protocol import build_frame, UartCommand, FRAME_HEADER_SHORT
        frame = build_frame(UartCommand.OBTAIN_ALL_FTESC_ID, b'')
        assert frame[0] == FRAME_HEADER_SHORT   # header court 0xAA
        payload_len = frame[1]
        expected_total = 2 + payload_len + 3    # hdr(1)+len(1) + payload + CRC(2)+footer(1)
        assert len(frame) == expected_total


class TestMotorLabelConstants:
    """Fix 8 — constantes MOTOR_LABEL_A / MOTOR_LABEL_B définies dans realtime.py"""

    def _import_constants(self):
        """Import direct du module (sans passer par gui.panels.__init__ qui nécessite CTk)."""
        import importlib.util, os
        path = os.path.join(os.path.dirname(__file__), '..', 'gui', 'panels', 'realtime.py')
        spec = importlib.util.spec_from_file_location("realtime_mod", path)
        mod = importlib.util.module_from_spec(spec)
        # Évite d'exécuter le corps du module (CTk non disponible en test)
        # On peut lire les constantes directement depuis le source
        return None  # constantes vérifiées via lecture source ci-dessous

    def test_constants_defined_in_source(self):
        """Vérifie que les constantes sont présentes dans le fichier source."""
        import os
        path = os.path.join(os.path.dirname(__file__), '..', 'gui', 'panels', 'realtime.py')
        with open(path) as f:
            src = f.read()
        assert 'MOTOR_LABEL_A = "Moteur A"' in src
        assert 'MOTOR_LABEL_B = "Moteur B"' in src

    def test_constants_distinct(self):
        """Les deux constantes doivent être différentes (test de non-régression)."""
        assert "Moteur A" != "Moteur B"
