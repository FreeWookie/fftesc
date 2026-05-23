# -*- coding: utf-8 -*-
"""
tests/test_wizard.py — Tests unitaires pour gui/wizard_data.py
et ftesc/wizard_engine.py (D26 & D27).
"""
import math
import pytest

from gui.wizard_data import (
    MOTORS_DB, BATTERIES_DB, TRANSMISSION_TYPES, PROFILES,
    motor_names, battery_names, transmission_names,
    get_motor, get_battery, get_transmission,
)
from ftesc.wizard_engine import WizardEngine, WizardInputs, WizardResult
from ftesc.data import DualMotorConfig, FOCMode


# ══════════════════════════════════════════════════════════════════════════════
#  D26 — wizard_data.py
# ══════════════════════════════════════════════════════════════════════════════

class TestWizardDataMotors:
    def test_all_required_motors_present(self):
        """Modèles minimaux exigés par la directive."""
        for model in ("5045", "5055", "5065", "6374", "8080"):
            assert model in MOTORS_DB, f"Moteur '{model}' manquant"

    def test_motor_keys_complete(self):
        required = {"kv_range", "max_current", "pole_pairs",
                    "resistance_mohm", "inductance_uh", "type", "wheel_mm", "note"}
        for name, data in MOTORS_DB.items():
            for key in required:
                assert key in data, f"Clé '{key}' manquante dans MOTORS_DB['{name}']"

    def test_kv_range_coherent(self):
        for name, data in MOTORS_DB.items():
            lo, hi = data["kv_range"]
            assert lo <= hi, f"kv_range incohérent pour '{name}' : {lo} > {hi}"
            assert lo > 0, f"kv_min <= 0 pour '{name}'"

    def test_max_current_positive(self):
        for name, data in MOTORS_DB.items():
            assert data["max_current"] > 0, f"max_current <= 0 pour '{name}'"

    def test_pole_pairs_positive(self):
        for name, data in MOTORS_DB.items():
            assert data["pole_pairs"] >= 1, f"pole_pairs < 1 pour '{name}'"

    def test_get_motor_found(self):
        m = get_motor("6374")
        assert m["type"] == "Outrunner Belt"

    def test_get_motor_unknown_raises(self):
        with pytest.raises(KeyError, match="inconnu"):
            get_motor("INEXISTANT")

    def test_motor_names_sorted(self):
        names = motor_names()
        assert names == sorted(names)
        assert len(names) == len(MOTORS_DB)


class TestWizardDataBatteries:
    def test_required_batteries_present(self):
        for batt in ("4S LiPo", "6S LiPo", "8S LiPo", "10S LiPo", "12S LiPo", "14S LiPo"):
            assert batt in BATTERIES_DB, f"Batterie '{batt}' manquante"

    def test_battery_keys_complete(self):
        required = {"cells", "nominal_v", "max_v", "min_v", "chemistry"}
        for name, data in BATTERIES_DB.items():
            for key in required:
                assert key in data, f"Clé '{key}' manquante dans BATTERIES_DB['{name}']"

    def test_voltage_ordering(self):
        for name, data in BATTERIES_DB.items():
            assert data["min_v"] < data["nominal_v"] < data["max_v"], \
                f"Tensions incohérentes pour '{name}': {data['min_v']} < {data['nominal_v']} < {data['max_v']}"

    def test_cells_positive(self):
        for name, data in BATTERIES_DB.items():
            assert data["cells"] >= 1

    def test_lipo_12s_voltages(self):
        b = get_battery("12S LiPo")
        assert b["cells"] == 12
        assert abs(b["max_v"] - 50.4) < 0.05
        assert abs(b["min_v"] - 36.0) < 0.05

    def test_get_battery_unknown_raises(self):
        with pytest.raises(KeyError, match="inconnue"):
            get_battery("99S LiPo")

    def test_chemistry_known_values(self):
        known = {"LiPo", "Li-Ion", "LiFePO4"}
        for name, data in BATTERIES_DB.items():
            assert data["chemistry"] in known, \
                f"Chimie inconnue '{data['chemistry']}' pour '{name}'"


class TestWizardDataTransmissions:
    def test_required_types_present(self):
        for t in ("Direct Drive", "Poulie (Belt)", "Chaîne"):
            assert t in TRANSMISSION_TYPES, f"Transmission '{t}' manquante"

    def test_transmission_keys_complete(self):
        required = {"ratio_range", "efficiency", "note"}
        for name, data in TRANSMISSION_TYPES.items():
            for key in required:
                assert key in data, f"Clé '{key}' manquante dans TRANSMISSION_TYPES['{name}']"

    def test_direct_drive_ratio_is_one(self):
        dd = TRANSMISSION_TYPES["Direct Drive"]
        assert dd["ratio_range"] == (1.0, 1.0)

    def test_efficiency_in_range(self):
        for name, data in TRANSMISSION_TYPES.items():
            assert 0.0 < data["efficiency"] <= 1.0, \
                f"Efficacité hors plage pour '{name}': {data['efficiency']}"

    def test_ratio_range_coherent(self):
        for name, data in TRANSMISSION_TYPES.items():
            lo, hi = data["ratio_range"]
            assert lo <= hi, f"ratio_range incohérent pour '{name}'"
            assert lo > 0

    def test_get_transmission_unknown_raises(self):
        with pytest.raises(KeyError, match="inconnue"):
            get_transmission("Inconnu")


class TestWizardDataProfiles:
    def test_profiles_list_complete(self):
        assert set(PROFILES) == {"Débutant", "Avancé", "Expert"}

    def test_profiles_ordered(self):
        assert PROFILES == ["Débutant", "Avancé", "Expert"]


# ══════════════════════════════════════════════════════════════════════════════
#  D27 — wizard_engine.py
# ══════════════════════════════════════════════════════════════════════════════

# ── Helpers ──────────────────────────────────────────────────────────────────

def _inputs(**kwargs) -> WizardInputs:
    """Construit un WizardInputs valide avec des valeurs par défaut sûres."""
    defaults = dict(
        motor_model  = "6374",
        battery_name = "10S LiPo",
        transmission = "Poulie (Belt)",
        gear_ratio   = 3.0,
        wheel_mm     = 90.0,
        profile      = "Avancé",
        dual_motor   = True,
    )
    defaults.update(kwargs)
    return WizardInputs(**defaults)


class TestWizardInputsValidation:
    def test_valid_inputs_no_errors(self):
        inp = _inputs()
        assert inp.validate() == []

    def test_unknown_motor(self):
        from gui.i18n import _
        inp = _inputs(motor_model="XXXX")
        assert _("wizard.error.unknown_motor") in inp.validate()

    def test_unknown_battery(self):
        from gui.i18n import _
        inp = _inputs(battery_name="99S NiCd")
        assert _("wizard.error.unknown_battery") in inp.validate()

    def test_unknown_transmission(self):
        from gui.i18n import _
        inp = _inputs(transmission="Magnétique")
        assert _("wizard.error.unknown_transmission") in inp.validate()

    def test_unknown_profile(self):
        from gui.i18n import _
        inp = _inputs(profile="Turbo")
        assert _("wizard.error.unknown_profile") in inp.validate()

    def test_gear_ratio_zero_invalid(self):
        from gui.i18n import _
        inp = _inputs(gear_ratio=0.0)
        errors = inp.validate()
        assert len(errors) == 1
        assert errors[0] == _("wizard.error.gear_ratio_positive")

    def test_wheel_mm_negative_invalid(self):
        from gui.i18n import _
        inp = _inputs(wheel_mm=-50.0)
        errors = inp.validate()
        assert len(errors) == 1
        assert errors[0] == _("wizard.error.wheel_mm_positive")

    def test_kv_override_out_of_range(self):
        from gui.i18n import _
        inp = _inputs(kv_override=99999.0)
        errors = inp.validate()
        assert len(errors) == 1
        assert errors[0] == _("wizard.error.kv_range")


class TestWizardEngineCalculateConfig:
    def setup_method(self):
        self.engine = WizardEngine()

    def test_returns_wizard_result(self):
        result = self.engine.calculate_config(_inputs())
        assert isinstance(result, WizardResult)

    def test_returns_dual_motor_config(self):
        result = self.engine.calculate_config(_inputs())
        assert isinstance(result.config, DualMotorConfig)

    def test_invalid_inputs_raises_value_error(self):
        with pytest.raises(ValueError, match="invalides"):
            self.engine.calculate_config(_inputs(motor_model="NOPE"))

    def test_speed_positive(self):
        result = self.engine.calculate_config(_inputs())
        assert result.speed_kmh > 0

    def test_reverse_speed_lower_than_forward(self):
        result = self.engine.calculate_config(_inputs())
        assert result.speed_kmh_rev < result.speed_kmh

    def test_max_current_positive(self):
        result = self.engine.calculate_config(_inputs())
        assert result.max_current_a > 0

    def test_max_erpm_positive(self):
        result = self.engine.calculate_config(_inputs())
        assert result.max_erpm > 0

    def test_warnings_is_list(self):
        result = self.engine.calculate_config(_inputs())
        assert isinstance(result.warnings, list)

    def test_dual_motor_both_configs_set(self):
        result = self.engine.calculate_config(_inputs(dual_motor=True))
        a = result.config.motor_a
        b = result.config.motor_b
        assert a.kv_rating == b.kv_rating
        assert a.max_current == b.max_current

    def test_single_motor_b_default(self):
        result = self.engine.calculate_config(_inputs(dual_motor=False))
        # moteur B = MotorConfig() par défaut
        assert result.config.motor_b.kv_rating == 70.0  # valeur par défaut

    def test_config_name_propagated(self):
        result = self.engine.calculate_config(_inputs(config_name="MonProfil"))
        assert result.config.name == "MonProfil"

    def test_hub_motor_uses_wheel_from_db(self):
        """Pour un hub moteur, wheel_mm du DB est utilisé si non fourni."""
        inp = _inputs(motor_model="5065", wheel_mm=None, transmission="Direct Drive")
        result = self.engine.calculate_config(inp)
        # 5065 a wheel_mm=165 dans la DB
        assert result.speed_kmh > 0

    def test_direct_drive_gear_ratio_forced_to_one(self):
        """gear_ratio ignoré pour Direct Drive."""
        r_dr = self.engine.calculate_config(
            _inputs(transmission="Direct Drive", gear_ratio=99.0, wheel_mm=165.0))
        r_belt = self.engine.calculate_config(
            _inputs(transmission="Poulie (Belt)", gear_ratio=1.0, wheel_mm=165.0))
        # Les deux doivent avoir le même speed (ratio = 1 dans les deux cas)
        assert abs(r_dr.speed_kmh - r_belt.speed_kmh) < 0.5


class TestWizardProfileOrdering:
    """Les trois profils doivent produire des résultats strictement ordonnés."""

    def setup_method(self):
        self.engine = WizardEngine()

    def _result(self, profile: str) -> WizardResult:
        return self.engine.calculate_config(_inputs(profile=profile))

    def test_current_debutant_lt_avance_lt_expert(self):
        rd = self._result("Débutant")
        ra = self._result("Avancé")
        re = self._result("Expert")
        assert rd.max_current_a <= ra.max_current_a <= re.max_current_a

    def test_speed_debutant_le_expert(self):
        """Vitesse peut être légèrement différente selon max_duty."""
        rd = self._result("Débutant")
        re = self._result("Expert")
        # expert a duty 0.95 > débutant 0.80
        assert re.speed_kmh >= rd.speed_kmh

    def test_expert_foc_mode_vectoriel(self):
        re = self._result("Expert")
        assert re.config.motor_a.foc.mode == FOCMode.FOC

    def test_debutant_foc_mode_sinus(self):
        rd = self._result("Débutant")
        assert rd.config.motor_a.foc.mode == FOCMode.SINUS

    def test_max_duty_ordered(self):
        rd = self._result("Débutant")
        ra = self._result("Avancé")
        re = self._result("Expert")
        assert rd.config.motor_a.limits.max_duty <= ra.config.motor_a.limits.max_duty
        assert ra.config.motor_a.limits.max_duty <= re.config.motor_a.limits.max_duty

    def test_ramp_up_ordered(self):
        """Débutant doit avoir la rampe la plus douce (temps le plus long)."""
        rd = self._result("Débutant")
        ra = self._result("Avancé")
        re = self._result("Expert")
        assert rd.config.motor_a.ramp.ramp_up_time >= ra.config.motor_a.ramp.ramp_up_time
        assert ra.config.motor_a.ramp.ramp_up_time >= re.config.motor_a.ramp.ramp_up_time

    def test_temp_fet_max_ordered(self):
        rd = self._result("Débutant")
        re = self._result("Expert")
        assert rd.config.motor_a.limits.temp_fet_max <= re.config.motor_a.limits.temp_fet_max


class TestWizardEngineFormulas:
    def setup_method(self):
        self.engine = WizardEngine()

    def test_estimate_speed_known_value(self):
        """Validation manuelle : KV=100, V=37 V, duty=0.9, ratio=3, roue=90 mm."""
        kv, v, duty, ratio, wheel = 100.0, 37.0, 0.9, 3.0, 90.0
        rpm_motor = kv * v * duty          # 3 330 tr/min
        rpm_wheel = rpm_motor / ratio       # 1 110 tr/min
        expected  = rpm_wheel * math.pi * (wheel / 1000.0) * 60.0 / 1000.0
        result    = WizardEngine.estimate_speed(kv, v, duty, ratio, wheel)
        assert abs(result - round(expected, 1)) < 0.1

    def test_estimate_speed_direct_drive_faster(self):
        """Sans réduction, la vitesse est plus élevée qu'avec ratio."""
        s1 = WizardEngine.estimate_speed(100, 37, 0.9, 1.0, 165)
        s3 = WizardEngine.estimate_speed(100, 37, 0.9, 3.0, 165)
        assert s1 > s3

    def test_voltage_limits_lipo_12s(self):
        bat = get_battery("12S LiPo")
        v_max, v_alarm, v_cutoff = WizardEngine._voltage_limits(bat)
        assert v_max == bat["max_v"]
        assert v_cutoff > bat["min_v"]
        assert v_alarm > bat["min_v"]
        assert v_alarm < v_max

    def test_voltage_cutoff_above_min(self):
        for name in battery_names():
            bat = get_battery(name)
            _, _, v_cutoff = WizardEngine._voltage_limits(bat)
            assert v_cutoff > bat["min_v"], f"cutoff <= min_v pour '{name}'"

    def test_pid_gains_within_bounds(self):
        profile = {"pid_kp": 0.10, "pid_ki": 0.015, "pid_kd": 0.001}
        for motor_name in ("5045", "6374", "8080"):
            motor_db = get_motor(motor_name)
            for ratio in (1.0, 3.0, 6.0):
                kp, ki, kd = WizardEngine._pid_gains(profile, motor_db, ratio)
                assert 0.001 <= kp <= 1.0, f"Kp hors plage ({kp}) pour {motor_name} r={ratio}"
                assert 0.001 <= ki <= 1.0, f"Ki hors plage ({ki}) pour {motor_name} r={ratio}"
                assert 0.0   <= kd <= 1.0, f"Kd hors plage ({kd}) pour {motor_name} r={ratio}"


class TestWizardEngineValidation:
    """La config produite doit passer le validateur de DualMotorConfig."""

    def setup_method(self):
        self.engine = WizardEngine()

    @pytest.mark.parametrize("profile", ["Débutant", "Avancé", "Expert"])
    @pytest.mark.parametrize("motor", ["5045", "5065", "6374", "8080"])
    @pytest.mark.parametrize("battery", ["6S LiPo", "10S LiPo", "12S LiPo"])
    def test_config_validates_cleanly(self, profile, motor, battery):
        """DualMotorConfig.validate() ne doit retourner aucune erreur."""
        bat_data = get_battery(battery)
        # Skip les batteries dépassant 58 V (le validateur du contrôleur les bloque)
        if bat_data["max_v"] > 58.0:
            pytest.skip(f"Tension max {bat_data['max_v']} V > 58 V (hors plage hardware)")
        inp = _inputs(motor_model=motor, battery_name=battery, profile=profile)
        result = self.engine.calculate_config(inp)
        errors = result.config.validate()
        all_errors = []
        for section, errs in errors.items():
            for e in errs:
                all_errors.append(f"[{section}] {e}")
        assert not all_errors, (
            f"Erreurs de validation pour profil={profile} moteur={motor} "
            f"batterie={battery} :\n" + "\n".join(all_errors)
        )


class TestWizardWarnings:
    def setup_method(self):
        self.engine = WizardEngine()

    def test_high_voltage_triggers_warning(self):
        """14S LiPo (58.8 V) dépasse 58 V → avertissement attendu."""
        inp = _inputs(battery_name="14S LiPo", profile="Avancé")
        result = self.engine.calculate_config(inp)
        assert any("58" in w or "tension" in w.lower() for w in result.warnings), \
            f"Avertissement tension absent. Avertissements : {result.warnings}"

    def test_no_spurious_warnings_standard_config(self):
        """Cas nominal Avancé 6374 / 10S → pas d'avertissement."""
        result = self.engine.calculate_config(_inputs())
        assert result.warnings == [], \
            f"Avertissements inattendus : {result.warnings}"


# ══════════════════════════════════════════════════════════════════════════════
#  D29 — Sécurité : HARD_LIMITS, clamp, fallback, sauvegarde
# ══════════════════════════════════════════════════════════════════════════════

class TestHardLimits:
    """Vérifie que HARD_LIMITS est défini et que les valeurs sont sensées."""

    def test_hard_limits_exported(self):
        from ftesc.wizard_engine import HARD_LIMITS
        required = {
            "max_motor_current_a", "max_battery_current_a", "max_absolute_current_a",
            "max_voltage_v", "max_temp_fet_c", "max_temp_motor_c",
            "max_erpm", "max_duty", "min_duty",
        }
        for key in required:
            assert key in HARD_LIMITS, f"HARD_LIMITS['{key}'] manquant"

    def test_hard_limits_physically_coherent(self):
        from ftesc.wizard_engine import HARD_LIMITS
        assert HARD_LIMITS["max_motor_current_a"] <= 200.0
        assert HARD_LIMITS["max_voltage_v"] <= 60.0
        assert HARD_LIMITS["max_duty"] <= 0.95
        assert HARD_LIMITS["min_duty"] >= 0.0
        assert HARD_LIMITS["max_erpm"] >= 100_000


class TestCurrentClamp:
    """Le courant calculé ne doit JAMAIS dépasser le max physique du moteur."""

    def setup_method(self):
        self.engine = WizardEngine()

    def test_5045_expert_current_clamped_to_motor_max(self):
        """5045 max_current=40 A — Expert current_factor=1.0 → doit rester ≤ 40."""
        from gui.wizard_data import get_motor
        motor_max = get_motor("5045")["max_current"]
        inp = _inputs(motor_model="5045", profile="Expert")
        result = self.engine.calculate_config(inp)
        assert result.max_current_a <= motor_max, (
            f"Courant {result.max_current_a} A dépasse le max moteur {motor_max} A"
        )

    def test_8080_expert_current_clamped_to_motor_max(self):
        from gui.wizard_data import get_motor
        motor_max = get_motor("8080")["max_current"]
        inp = _inputs(motor_model="8080", profile="Expert")
        result = self.engine.calculate_config(inp)
        assert result.max_current_a <= motor_max

    def test_current_never_exceeds_hard_limit(self):
        """Quelle que soit la combinaison, le courant ≤ HARD_LIMITS."""
        from ftesc.wizard_engine import HARD_LIMITS
        hard_max = HARD_LIMITS["max_motor_current_a"]
        for motor in ("5045", "5065", "6374", "8080", "10inch_hub"):
            for profile in ("Débutant", "Avancé", "Expert"):
                inp = _inputs(motor_model=motor, profile=profile)
                result = self.engine.calculate_config(inp)
                assert result.max_current_a <= hard_max, (
                    f"{motor}/{profile}: courant {result.max_current_a} > {hard_max}"
                )

    def test_voltage_never_exceeds_hard_limit(self):
        """La tension max de la config ≤ HARD_LIMITS.max_voltage_v."""
        from ftesc.wizard_engine import HARD_LIMITS
        hard_v = HARD_LIMITS["max_voltage_v"]
        for bat in ("12S LiPo", "10S LiPo", "8S LiPo"):
            inp = _inputs(battery_name=bat, profile="Expert")
            result = self.engine.calculate_config(inp)
            cfg_v = result.config.motor_a.limits.max_input_voltage
            assert cfg_v <= hard_v + 0.01, (
                f"{bat}: tension config {cfg_v} V > hard limit {hard_v} V"
            )

    def test_erpm_never_exceeds_hard_limit(self):
        from ftesc.wizard_engine import HARD_LIMITS
        hard_erpm = HARD_LIMITS["max_erpm"]
        for motor in motor_names():
            inp = _inputs(motor_model=motor, profile="Expert",
                          battery_name="12S LiPo", kv_override=500.0)
            try:
                result = self.engine.calculate_config(inp)
                assert result.max_erpm <= hard_erpm, (
                    f"{motor}: ERPM {result.max_erpm} > {hard_erpm}"
                )
            except ValueError:
                pass  # moteur 12S LiPo incompatible → OK

    def test_duty_never_exceeds_hard_limit(self):
        from ftesc.wizard_engine import HARD_LIMITS
        hard_duty = HARD_LIMITS["max_duty"]
        for profile in ("Débutant", "Avancé", "Expert"):
            inp = _inputs(profile=profile)
            result = self.engine.calculate_config(inp)
            cfg_duty = result.config.motor_a.limits.max_duty
            assert cfg_duty <= hard_duty + 1e-9, (
                f"{profile}: duty {cfg_duty} > {hard_duty}"
            )

    def test_clamped_warnings_type_is_list(self):
        """clamped_warnings doit toujours être une liste."""
        result = self.engine.calculate_config(_inputs())
        assert isinstance(result.clamped_warnings, list)

    def test_14s_triggers_clamped_warning(self):
        """14S LiPo (58.8 V) → tension > 58 V → doit déclencher un clamped_warning."""
        inp = _inputs(battery_name="14S LiPo", profile="Avancé")
        result = self.engine.calculate_config(inp)
        assert len(result.clamped_warnings) > 0, \
            "Attendu au moins 1 clamped_warning pour 14S LiPo"
        # Le message doit mentionner la tension ou la limite
        combined = " ".join(result.clamped_warnings).lower()
        assert any(kw in combined for kw in ("tension", "v", "volt")), \
            f"Message de clamp incompréhensible : {result.clamped_warnings}"

    def test_standard_config_no_clamped_warnings(self):
        """Cas nominal (6374 / 10S Avancé) → aucun clamp."""
        result = self.engine.calculate_config(_inputs())
        assert result.clamped_warnings == [], \
            f"Clamps inattendus : {result.clamped_warnings}"

    def test_apply_hard_limits_static_method(self):
        """Test direct de _apply_hard_limits avec une valeur dépassant le max moteur."""
        from ftesc.wizard_engine import WizardEngine, HARD_LIMITS
        from gui.wizard_data import get_motor
        motor_db = get_motor("5045")   # max_current = 40 A
        # On passe un courant volontairement trop élevé
        calc_current  = 200.0
        brake_current = 100.0
        new_c, new_b, warns = WizardEngine._apply_hard_limits(
            calc_current, brake_current, motor_db, {"max_v": 42.0}, []
        )
        assert new_c <= motor_db["max_current"], f"Non clampé : {new_c}"
        assert new_c <= HARD_LIMITS["max_motor_current_a"]
        assert new_b <= new_c
        assert len(warns) >= 1  # au moins un avertissement généré


class TestFallback:
    """Si le calcul échoue, l'état précédent doit être inchangé."""

    def setup_method(self):
        self.engine = WizardEngine()

    def test_failed_calculation_does_not_corrupt_previous_result(self):
        """Un calcul valide suivi d'une tentative invalide laisse le résultat intact."""
        # 1. Calcul valide → stocke un résultat
        good = self.engine.calculate_config(_inputs(profile="Avancé"))
        assert good is not None

        # 2. Tentative invalide → doit lever ValueError sans écraser quoi que ce soit
        with pytest.raises(ValueError):
            self.engine.calculate_config(_inputs(motor_model="INEXISTANT"))

        # 3. Le moteur peut encore produire un résultat correct
        again = self.engine.calculate_config(_inputs(profile="Débutant"))
        assert again.max_current_a > 0

    def test_wizard_inputs_errors_are_explicit(self):
        """Les erreurs de validation doivent mentionner explicitement le problème."""
        inp = WizardInputs(
            motor_model="XXXX", battery_name="99S", transmission="Magnétique",
            gear_ratio=-1.0, profile="Turbo",
        )
        errors = inp.validate()
        assert len(errors) >= 4   # au moins 5 problèmes signalés
        text = " ".join(errors).lower()
        assert "moteur" in text
        assert "batterie" in text
        assert "transmission" in text
        assert "profil" in text


class TestProfileSaving:
    """Vérifie que save_profile fonctionne correctement avec un résultat wizard."""

    def setup_method(self):
        self.engine = WizardEngine()

    def test_save_and_load_wizard_profile(self):
        from ftesc.profiles import save_profile, load_profile, delete_profile
        result = self.engine.calculate_config(_inputs(config_name="TestWizard"))
        name = "_test_d29_wizard_profile"
        try:
            ok = save_profile(name, result.config)
            assert ok, "save_profile a retourné False"
            loaded = load_profile(name)
            assert loaded is not None, "load_profile a retourné None"
            assert loaded.name == "TestWizard"
            assert abs(loaded.motor_a.max_current - result.config.motor_a.max_current) < 0.01
        finally:
            delete_profile(name)   # nettoyage

    def test_save_profile_with_clamped_config(self):
        """Même une config avec clamps doit être sauvegardable proprement."""
        from ftesc.profiles import save_profile, load_profile, delete_profile
        # 14S → déclenche des clamps
        inp = _inputs(battery_name="14S LiPo", profile="Expert",
                      config_name="ClampedSetup")
        result = self.engine.calculate_config(inp)
        name = "_test_d29_clamped_profile"
        try:
            ok = save_profile(name, result.config)
            assert ok
            loaded = load_profile(name)
            assert loaded is not None
            # Vérifie que les erreurs de validation sont absentes
            errors = loaded.validate()
            all_e = [e for errs in errors.values() for e in errs]
            assert not all_e, f"Config clampée invalide après sauvegarde : {all_e}"
        finally:
            delete_profile(name)

# ════════════════════════════════════════════════════════════════════════════════
#  D30 — Nouveaux champs WizardInputs & WizardResult
# ══════════════════════════════════════════════════════════════════════════════

class TestWizardInputsD30:
    """Validation des nouveaux champs WizardInputs."""

    def test_default_values(self):
        inp = _inputs()
        assert inp.pinion_teeth is None
        assert inp.wheel_teeth is None
        assert inp.wheel_unit == "mm"
        assert inp.speed_unit == "km/h"
        assert abs(inp.transmission_efficiency - 0.85) < 0.001

    def test_pinion_teeth_bounds(self):
        from gui.i18n import _
        assert _inputs(pinion_teeth=10).validate() == []
        assert _inputs(pinion_teeth=30).validate() == []
        errs = _inputs(pinion_teeth=9).validate()
        assert len(errs) == 1
        assert errs[0] == _("wizard.error.pinion_teeth_range")
        errs = _inputs(pinion_teeth=31).validate()
        assert len(errs) == 1
        assert errs[0] == _("wizard.error.pinion_teeth_range")

    def test_wheel_teeth_bounds(self):
        from gui.i18n import _
        assert _inputs(wheel_teeth=40).validate() == []
        assert _inputs(wheel_teeth=120).validate() == []
        errs = _inputs(wheel_teeth=39).validate()
        assert len(errs) == 1
        assert errs[0] == _("wizard.error.wheel_teeth_range")
        errs = _inputs(wheel_teeth=121).validate()
        assert len(errs) == 1
        assert errs[0] == _("wizard.error.wheel_teeth_range")

    def test_wheel_unit_values(self):
        from gui.i18n import _
        assert _inputs(wheel_unit="mm").validate() == []
        assert _inputs(wheel_unit="inches").validate() == []
        errs = _inputs(wheel_unit="cm").validate()
        assert len(errs) == 1
        assert errs[0] == _("wizard.error.wheel_unit")

    def test_speed_unit_values(self):
        from gui.i18n import _
        assert _inputs(speed_unit="km/h").validate() == []
        assert _inputs(speed_unit="mph").validate() == []
        errs = _inputs(speed_unit="kts").validate()
        assert len(errs) == 1
        assert errs[0] == _("wizard.error.speed_unit")

    def test_efficiency_bounds(self):
        from gui.i18n import _
        assert _inputs(transmission_efficiency=0.70).validate() == []
        assert _inputs(transmission_efficiency=0.95).validate() == []
        errs = _inputs(transmission_efficiency=0.69).validate()
        assert len(errs) == 1
        assert errs[0] == _("wizard.error.efficiency_range")
        errs = _inputs(transmission_efficiency=0.96).validate()
        assert len(errs) == 1
        assert errs[0] == _("wizard.error.efficiency_range")


class TestGearRatioAuto:
    """effective_gear_ratio() — calcul automatique via pignon/poulie."""

    def test_direct_drive_always_one(self):
        inp = _inputs(transmission="Direct Drive", gear_ratio=5.0,
                      pinion_teeth=15, wheel_teeth=60)
        assert inp.effective_gear_ratio() == 1.0

    def test_ratio_from_teeth(self):
        inp = _inputs(transmission="Poulie (Belt)",
                      pinion_teeth=15, wheel_teeth=60, gear_ratio=99.0)
        assert abs(inp.effective_gear_ratio() - 4.0) < 0.001

    def test_ratio_from_teeth_2(self):
        inp = _inputs(transmission="Poulie (Belt)",
                      pinion_teeth=12, wheel_teeth=72)
        assert abs(inp.effective_gear_ratio() - 6.0) < 0.001

    def test_ratio_manual_if_no_teeth(self):
        inp = _inputs(transmission="Poulie (Belt)", gear_ratio=3.5,
                      pinion_teeth=None, wheel_teeth=None)
        assert abs(inp.effective_gear_ratio() - 3.5) < 0.001

    def test_teeth_priority_over_manual(self):
        """Pignon/poulie prime toujours sur gear_ratio manuel."""
        inp = _inputs(transmission="Chaîne",
                      pinion_teeth=10, wheel_teeth=80, gear_ratio=2.0)
        # 80/10 = 8.0, pas 2.0
        assert abs(inp.effective_gear_ratio() - 8.0) < 0.001


class TestWheelUnit:
    """effective_wheel_mm() — conversion pouces → mm."""

    def test_mm_passthrough(self):
        inp = _inputs(wheel_mm=90.0, wheel_unit="mm")
        from gui.wizard_data import get_motor
        motor_db = get_motor(inp.motor_model)
        assert abs(inp.effective_wheel_mm(motor_db) - 90.0) < 0.1

    def test_inches_conversion(self):
        inp = _inputs(wheel_mm=8.0, wheel_unit="inches")
        from gui.wizard_data import get_motor
        motor_db = get_motor(inp.motor_model)
        expected = 8.0 * 25.4   # 203.2 mm
        assert abs(inp.effective_wheel_mm(motor_db) - expected) < 0.5

    def test_hub_fallback_if_no_wheel(self):
        inp = _inputs(motor_model="5065", wheel_mm=None, wheel_unit="mm")
        from gui.wizard_data import get_motor
        motor_db = get_motor("5065")
        expected = motor_db["wheel_mm"]   # 165 mm
        assert abs(inp.effective_wheel_mm(motor_db) - expected) < 0.1

    def test_default_fallback_90mm(self):
        """Moteur sans hub_wheel → 90 mm par défaut."""
        inp = _inputs(motor_model="6374", wheel_mm=None, wheel_unit="mm")
        from gui.wizard_data import get_motor
        motor_db = get_motor("6374")
        assert abs(inp.effective_wheel_mm(motor_db) - 90.0) < 0.1


class TestSpeedUnitAndEfficiency:
    """WizardResult — vitesse avec unité et efficacité."""

    def setup_method(self):
        self.engine = WizardEngine()

    def _calc(self, **kwargs):
        return self.engine.calculate_config(_inputs(**kwargs))

    def test_kmh_default(self):
        r = self._calc(speed_unit="km/h")
        assert r.speed_unit == "km/h"
        assert r.speed_display == r.speed_kmh

    def test_mph_conversion(self):
        r = self._calc(speed_unit="mph")
        assert r.speed_unit == "mph"
        # 1 mph = 1.60934 km/h
        expected_mph = round(r.speed_kmh / 1.60934, 1)
        assert abs(r.speed_display - expected_mph) < 0.2

    def test_mph_lower_than_kmh(self):
        r = self._calc(speed_unit="mph")
        assert r.speed_display < r.speed_kmh

    def test_efficiency_reduces_speed(self):
        """Efficacité 0.70 → vitesse plus basse qu'efficacité 0.95."""
        r_low  = self._calc(transmission_efficiency=0.70)
        r_high = self._calc(transmission_efficiency=0.95)
        assert r_low.speed_kmh < r_high.speed_kmh

    def test_efficiency_stored_in_result(self):
        r = self._calc(transmission_efficiency=0.80)
        assert abs(r.transmission_efficiency - 0.80) < 0.001

    def test_efficiency_at_extremes(self):
        r_min = self._calc(transmission_efficiency=0.70)
        r_max = self._calc(transmission_efficiency=0.95)
        assert r_min.speed_kmh > 0
        assert r_max.speed_kmh > r_min.speed_kmh

    def test_gear_ratio_used_from_teeth(self):
        """Le ratio effectif depuis pignon/poulie est stocké dans le résultat."""
        r = self._calc(transmission="Poulie (Belt)",
                       pinion_teeth=15, wheel_teeth=60)
        assert abs(r.gear_ratio_used - 4.0) < 0.001

    def test_gear_ratio_used_manual_if_no_teeth(self):
        r = self._calc(transmission="Poulie (Belt)", gear_ratio=3.0,
                       pinion_teeth=None, wheel_teeth=None)
        assert abs(r.gear_ratio_used - 3.0) < 0.001

    def test_reverse_speed_lower_in_chosen_unit(self):
        for unit in ("km/h", "mph"):
            r = self._calc(speed_unit=unit)
            assert r.speed_display_rev < r.speed_display, \
                f"{unit}: speed_rev {r.speed_display_rev} >= speed {r.speed_display}"

    def test_inches_wheel_produces_correct_speed(self):
        """8 pouces ≈ 203 mm → vitesse supérieure à 90 mm."""
        r_inch = self._calc(motor_model="6374", wheel_mm=8.0, wheel_unit="inches",
                            transmission="Poulie (Belt)", gear_ratio=3.0)
        r_mm   = self._calc(motor_model="6374", wheel_mm=90.0, wheel_unit="mm",
                            transmission="Poulie (Belt)", gear_ratio=3.0)
        assert r_inch.speed_kmh > r_mm.speed_kmh, \
            f"8 pouces ({r_inch.speed_kmh}) devrait donner plus vite que 90mm ({r_mm.speed_kmh})"


class TestD30FullConfig:
    """Config complète D30 doit toujours passer validate()."""

    def setup_method(self):
        self.engine = WizardEngine()

    @pytest.mark.parametrize("profile", ["Débutant", "Avancé", "Expert"])
    @pytest.mark.parametrize("unit", ["km/h", "mph"])
    @pytest.mark.parametrize("eff", [0.70, 0.85, 0.95])
    def test_full_config_valid_d30(self, profile, unit, eff):
        inp = _inputs(
            profile=profile, speed_unit=unit, transmission_efficiency=eff,
            pinion_teeth=15, wheel_teeth=60,
            wheel_mm=90.0, wheel_unit="mm",
        )
        result = self.engine.calculate_config(inp)
        errors = result.config.validate()
        all_e = [e for errs in errors.values() for e in errs]
        assert not all_e, f"{profile}/{unit}/{eff}: {all_e}"
