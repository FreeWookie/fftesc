# -*- coding: utf-8 -*-
"""
ftesc/wizard_engine.py — Logique de calcul automatique du Wizard de configuration.

Usage minimal :
    from ftesc.wizard_engine import WizardEngine, WizardInputs

    inputs = WizardInputs(
        motor_model   = "6374",
        battery_name  = "10S LiPo",
        transmission  = "Poulie (Belt)",
        gear_ratio    = 3.0,
        wheel_mm      = 90,
        profile       = "Avancé",
    )
    engine = WizardEngine()
    result = engine.calculate_config(inputs)
    # result.config      → DualMotorConfig prêt à envoyer
    # result.speed_kmh   → vitesse max théorique (km/h)
    # result.warnings    → liste d'avertissements texte
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from ftesc.data import (
    MotorConfig, BatteryConfig, DualMotorConfig,
    LimitsConfig, RampConfig, BrakeConfig,
    FOCConfig, HallConfig, SpeedPIDConfig, InputControlConfig,
    DualSetupConfig,
    MotorType, FOCMode, BatteryType,
)
from gui.wizard_data import (
    MOTORS_DB, BATTERIES_DB, TRANSMISSION_TYPES,
    get_motor, get_battery, get_transmission, PROFILES,
)
from gui.i18n import _

# ──────────────────────────────────────────────────────────────────────────────
#  LIMITES PHYSIQUES ABSOLUES DU CONTRÔLEUR FTESC (hardware)
#
#  Ces valeurs NE DOIVENT JAMAIS être dépassées, quel que soit le profil.
#  Elles correspondent aux limites physiques du silicium / des composants.
# ──────────────────────────────────────────────────────────────────────────────
HARD_LIMITS: dict[str, float] = {
    # Courant moteur — les MOS du FTESC ne supportent pas plus de 120 A en continu
    "max_motor_current_a":    120.0,
    # Courant batterie absolu
    "max_battery_current_a":  100.0,
    # Courant absolu (pic)
    "max_absolute_current_a": 150.0,
    # Tension d'entrée maximale (condensateurs et MOSFETs 60 V)
    "max_voltage_v":           58.0,
    # Température FET — destruction des MOSFETs au-delà
    "max_temp_fet_c":          95.0,
    # Température moteur — dégradation irréversible de l'aimant
    "max_temp_motor_c":        90.0,
    # ERPM maximum supporté par le firmware
    "max_erpm":             200_000.0,
    # Duty cycle maximum absolu (firmware)
    "max_duty":                 0.95,
    # Rapport cyclique minimum (en dessous, le firmware ignore)
    "min_duty":                 0.01,
}

# ──────────────────────────────────────────────────────────────────────────────
#  TABLES DES PROFILS
# ──────────────────────────────────────────────────────────────────────────────

_PROFILE_PARAMS: dict[str, dict] = {
    "Débutant": {
        # Courant moteur : 70 % du maximum physique du moteur
        "current_factor":      0.70,
        # Max duty (rapport cyclique maximum)
        "max_duty":            0.80,
        # Température FET : seuil de déclenchement / max absolu
        "temp_fet_start":      60.0,
        "temp_fet_max":        70.0,
        # Température moteur : seuil / max
        "temp_motor_start":    55.0,
        "temp_motor_max":      60.0,
        # Rampe d'accélération (secondes)
        "ramp_up_time":        3.0,
        "ramp_down_time":      2.5,
        # Courant de freinage : fraction du courant moteur calculé
        "brake_factor":        0.50,
        # FOC : mode sinus (le plus stable)
        "foc_mode":            FOCMode.SINUS,
        # Courbe de gaz (linéaire douce)
        "throttle_curve":      [0.0, 0.10, 0.25, 0.45, 0.70, 1.0],
        # Deadband gaz (5 %)
        "throttle_deadband":   0.08,
        # PID speed – gains conservateurs
        "pid_kp":              0.05,
        "pid_ki":              0.008,
        "pid_kd":              0.0005,
    },
    "Avancé": {
        "current_factor":      0.90,
        "max_duty":            0.90,
        "temp_fet_start":      75.0,
        "temp_fet_max":        85.0,
        "temp_motor_start":    70.0,
        "temp_motor_max":      75.0,
        "ramp_up_time":        1.5,
        "ramp_down_time":      1.2,
        "brake_factor":        0.60,
        "foc_mode":            FOCMode.SINUS,
        "throttle_curve":      [0.0, 0.15, 0.35, 0.58, 0.80, 1.0],
        "throttle_deadband":   0.05,
        "pid_kp":              0.10,
        "pid_ki":              0.015,
        "pid_kd":              0.001,
    },
    "Expert": {
        "current_factor":      1.00,       # 100 % – limite physique du moteur
        "max_duty":            0.95,
        "temp_fet_start":      85.0,
        "temp_fet_max":        95.0,
        "temp_motor_start":    80.0,
        "temp_motor_max":      85.0,
        "ramp_up_time":        0.5,
        "ramp_down_time":      0.4,
        "brake_factor":        0.70,
        "foc_mode":            FOCMode.FOC,    # FOC vectoriel complet
        "throttle_curve":      [0.0, 0.20, 0.42, 0.65, 0.85, 1.0],
        "throttle_deadband":   0.03,
        "pid_kp":              0.18,
        "pid_ki":              0.025,
        "pid_kd":              0.002,
    },
}

# ──────────────────────────────────────────────────────────────────────────────
#  STRUCTURES D'ENTRÉE / SORTIE
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class WizardInputs:
    """
    Paramètres fournis par l'utilisateur via le Wizard.

    Attributs
    ---------
    motor_model             : clé dans MOTORS_DB (ex. "6374")
    battery_name            : clé dans BATTERIES_DB (ex. "10S LiPo")
    transmission            : clé dans TRANSMISSION_TYPES (ex. "Poulie (Belt)")
    gear_ratio              : rapport de réduction manuel (ex. 3.0 pour 3:1).
                              Ignoré si pinion_teeth ET wheel_teeth sont renseignés.
                              Ignoré si transmission == "Direct Drive" (forcé à 1.0).
    wheel_mm                : diamètre de la roue de traction en millimètres.
                              Si None, utilise wheel_mm du moteur (hub) ou 90 mm par défaut.
    profile                 : "Débutant" | "Avancé" | "Expert"
    dual_motor              : True → configurer les deux moteurs identiquement
    config_name             : nom du profil de sortie
    kv_override             : KV personnalisé (None = milieu de kv_range)
    pinion_teeth            : dents du pignon moteur (10–30). Prioritaire sur gear_ratio.
    wheel_teeth             : dents de la poulie/couronne roue (40–120). Prioritaire sur gear_ratio.
    wheel_unit              : "mm" | "inches" — unité du champ wheel_mm
    speed_unit              : "km/h" | "mph" — unité de la vitesse affichée
    transmission_efficiency : efficacité mécanique 0.70–0.95 (défaut 0.85)
    """
    motor_model:             str
    battery_name:            str
    transmission:            str   = "Direct Drive"
    gear_ratio:              float = 1.0
    wheel_mm:                Optional[float] = None
    profile:                 str   = "Avancé"
    dual_motor:              bool  = True
    config_name:             str   = "Wizard"
    kv_override:             Optional[float] = None
    # ── Nouveaux champs D30 ──────────────────────────────────────────────────
    pinion_teeth:            Optional[int]   = None    # dents pignon moteur
    wheel_teeth:             Optional[int]   = None    # dents poulie roue
    wheel_unit:              str             = "mm"    # "mm" | "inches"
    speed_unit:              str             = "km/h"  # "km/h" | "mph"
    transmission_efficiency: float           = 0.85    # 0.70–0.95

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.motor_model not in MOTORS_DB:
            errors.append(_("wizard.error.unknown_motor"))
        if self.battery_name not in BATTERIES_DB:
            errors.append(_("wizard.error.unknown_battery"))
        if self.transmission not in TRANSMISSION_TYPES:
            errors.append(_("wizard.error.unknown_transmission"))
        if self.profile not in PROFILES:
            errors.append(_("wizard.error.unknown_profile"))
        if self.gear_ratio <= 0:
            errors.append(_("wizard.error.gear_ratio_positive"))
        if self.wheel_mm is not None and self.wheel_mm <= 0:
            errors.append(_("wizard.error.wheel_mm_positive"))
        if self.kv_override is not None:
            if not (1 <= self.kv_override <= 10000):
                errors.append(_("wizard.error.kv_range"))
        # Pinion teeth validation (if provided)
        if self.pinion_teeth is not None:
            if not (10 <= self.pinion_teeth <= 30):
                errors.append(_("wizard.error.pinion_teeth_range"))
        # Wheel teeth validation (if provided)
        if self.wheel_teeth is not None:
            if not (40 <= self.wheel_teeth <= 120):
                errors.append(_("wizard.error.wheel_teeth_range"))
        # Wheel unit validation
        if self.wheel_unit not in ("mm", "inches"):
            errors.append(_("wizard.error.wheel_unit"))
        # Speed unit validation
        if self.speed_unit not in ("km/h", "mph"):
            errors.append(_("wizard.error.speed_unit"))
        # Efficiency validation
        if not (0.70 <= self.transmission_efficiency <= 0.95):
            errors.append(_("wizard.error.efficiency_range"))
        # Battery voltage zero -> block calculation
        batt = BATTERIES_DB.get(self.battery_name)
        if batt and batt.get("max_v", 0) <= 0:
            errors.append(_("wizard.error.battery_voltage_zero"))
        return errors

    def effective_gear_ratio(self) -> float:
        """
        Calcule le ratio effectif.
        Priorité : pignon/poulie > gear_ratio manuel > Direct Drive = 1.0.
        """
        if self.transmission == "Direct Drive":
            return 1.0
        if self.pinion_teeth and self.wheel_teeth:
            return self.wheel_teeth / self.pinion_teeth
        return max(self.gear_ratio, 0.1)

    def effective_wheel_mm(self, motor_db: dict) -> float:
        """Retourne le diamètre de roue en mm, quelle que soit l'unité saisie."""
        if self.wheel_mm is not None:
            raw = float(self.wheel_mm)
            if self.wheel_unit == "inches":
                return raw * 25.4
            return raw
        hub = motor_db.get("wheel_mm")
        if hub:
            return float(hub)
        return 90.0


@dataclass
class WizardResult:
    """
    Résultat retourné par WizardEngine.calculate_config().

    Attributs
    ---------
    config          : DualMotorConfig complet, prêt à envoyer au contrôleur
    speed_kmh       : vitesse max théorique en km/h (sens avant, duty max)
    speed_kmh_rev   : vitesse max théorique en marche arrière (km/h)
    max_current_a   : courant moteur calculé après application du profil (A)
    max_erpm        : ERPM maximum calculé
    warnings        : liste de messages d'avertissement (non bloquants)
    clamped_warnings: liste de valeurs recadrées par les limites physiques absolues
    inputs_used     : copie des WizardInputs utilisés
    """
    config:                   DualMotorConfig
    speed_kmh:                float   # toujours en km/h (référence interne)
    speed_display:            float   # dans l'unité choisie par l'utilisateur
    speed_unit:               str     # "km/h" | "mph"
    speed_kmh_rev:            float
    speed_display_rev:        float
    max_current_a:            float
    max_erpm:                 float
    gear_ratio_used:          float   # ratio effectif (calculé ou manuel)
    transmission_efficiency:  float   # 0.70–0.95
    warnings:                 list[str]
    clamped_warnings:         list[str]
    inputs_used:              WizardInputs


# ──────────────────────────────────────────────────────────────────────────────
#  MOTEUR DU CALCUL
# ──────────────────────────────────────────────────────────────────────────────

class WizardEngine:
    """
    Calcule une DualMotorConfig complète à partir de WizardInputs.

    Méthodes publiques
    ------------------
    calculate_config(inputs)  → WizardResult
    estimate_speed(...)       → float (km/h)
    """

    # ── API publique ──────────────────────────────────────────────────────────

    def calculate_config(self, inputs: WizardInputs) -> WizardResult:
        """
        Point d'entrée principal.

        Valide les entrées, applique les formules, retourne un WizardResult.
        Lève ValueError si les entrées sont invalides.
        """
        errors = inputs.validate()
        if errors:
            raise ValueError("Entrées invalides :\n" + "\n".join(f"  • {e}" for e in errors))

        motor_db   = get_motor(inputs.motor_model)
        battery_db = get_battery(inputs.battery_name)
        trans_db   = get_transmission(inputs.transmission)
        profile    = _PROFILE_PARAMS[inputs.profile]
        warnings:         list[str] = []
        clamped_warnings: list[str] = []

        # ── 1. Paramètres électriques de base ─────────────────────────────
        kv         = self._resolve_kv(inputs, motor_db)
        gear_ratio = inputs.effective_gear_ratio()
        wheel_mm   = inputs.effective_wheel_mm(motor_db)
        efficiency = inputs.transmission_efficiency

        # ── 1b. Warnings de cohérence (Directive 33) ────────────────────────
        if kv > 200 and battery_db.get("cells", 0) > 10:
            warnings.append(_("wizard.warning.high_kv"))
        if inputs.pinion_teeth is not None and inputs.pinion_teeth < 12:
            warnings.append(_("wizard.warning.pinion_too_small"))

        # ── 2. Courant moteur après profil ────────────────────────────────
        motor_max_a   = float(motor_db["max_current"])
        calc_current  = round(motor_max_a * profile["current_factor"], 1)
        brake_current = round(calc_current * profile["brake_factor"], 1)

        # ── 2b. Clamp sécurité — limite physique absolue du contrôleur ───
        calc_current, brake_current, clamped_warnings = self._apply_hard_limits(
            calc_current, brake_current, motor_db, battery_db, clamped_warnings,
        )

        # ── 3. Limites de tension ─────────────────────────────────────────
        voltage_max, voltage_min, voltage_cutoff = self._voltage_limits(battery_db)
        # Clamp tension sur la limite hardware absolue
        if voltage_max > HARD_LIMITS["max_voltage_v"]:
            clamped_warnings.append(
                f"⚠️ Tension max réduite de {voltage_max} V → "
                f"{HARD_LIMITS['max_voltage_v']} V (limite hardware FTESC)."
            )
            voltage_max = HARD_LIMITS["max_voltage_v"]

        # ── 4. ERPM max : RPM_moteur × pole_pairs
        #       RPM_moteur ≈ KV × V_nominale × duty_max
        duty_clamped = min(profile["max_duty"], HARD_LIMITS["max_duty"])
        rpm_motor_max = kv * battery_db["nominal_v"] * duty_clamped
        pole_pairs    = int(motor_db["pole_pairs"])
        erpm_raw      = round(rpm_motor_max * pole_pairs)
        erpm_max      = int(min(erpm_raw, HARD_LIMITS["max_erpm"]))
        if erpm_raw > HARD_LIMITS["max_erpm"]:
            clamped_warnings.append(
                f"⚠️ ERPM réduit de {erpm_raw:,} → {erpm_max:,} (limite firmware)."
            )
        erpm_rev = round(erpm_max * 0.60)   # marche arrière : 60 % de l'avant

        # ── 5. Vitesse max théorique (avec efficacité transmission) ──────────
        speed_kmh_raw = self.estimate_speed(
            kv, battery_db["nominal_v"], duty_clamped,
            gear_ratio, wheel_mm,
        )
        speed_kmh     = round(speed_kmh_raw * efficiency, 1)
        speed_kmh_rev = round(speed_kmh * 0.60, 1)

        # Conversion unité affichage
        if inputs.speed_unit == "mph":
            speed_display     = round(speed_kmh     / 1.60934, 1)
            speed_display_rev = round(speed_kmh_rev / 1.60934, 1)
        else:
            speed_display     = speed_kmh
            speed_display_rev = speed_kmh_rev

        # ── 6. Courant batterie (estimation : I_bat ≈ I_moteur × duty) ───
        duty_avg    = duty_clamped * 0.70   # usage moyen estimé
        bat_current = round(calc_current * duty_avg, 1)
        bat_current = min(bat_current, HARD_LIMITS["max_battery_current_a"])

        # ── 7. PID Speed – gain adaptatif selon inertie estimée ──────────
        kp, ki, kd = self._pid_gains(profile, motor_db, gear_ratio)

        # ── 8. Cohérence / avertissements ────────────────────────────────
        warnings.extend(self._check_compatibility(
            motor_db, battery_db, calc_current, speed_kmh, inputs.profile, gear_ratio,
        ))

        # ── 9. Construction des objets de config ─────────────────────────
        motor_cfg = self._build_motor_config(
            motor_db, kv, calc_current, brake_current,
            voltage_max, voltage_min, voltage_cutoff,
            erpm_max, erpm_rev, bat_current,
            profile, kp, ki, kd,
        )
        battery_cfg = self._build_battery_config(battery_db, bat_current)

        motor_a = motor_cfg
        motor_b = motor_cfg if inputs.dual_motor else MotorConfig()

        dual_config = DualMotorConfig(
            motor_a    = motor_a,
            motor_b    = motor_b,
            battery    = battery_cfg,
            dual_setup = DualSetupConfig(),
            name       = inputs.config_name,
        )

        return WizardResult(
            config                  = dual_config,
            speed_kmh               = speed_kmh,
            speed_display           = speed_display,
            speed_unit              = inputs.speed_unit,
            speed_kmh_rev           = speed_kmh_rev,
            speed_display_rev       = speed_display_rev,
            max_current_a           = calc_current,
            max_erpm                = erpm_max,
            gear_ratio_used         = gear_ratio,
            transmission_efficiency = efficiency,
            warnings                = warnings,
            clamped_warnings        = clamped_warnings,
            inputs_used             = inputs,
        )

    # ── Sécurité : clamp sur les limites physiques absolues ──────────────────

    @staticmethod
    def _apply_hard_limits(
        calc_current: float,
        brake_current: float,
        motor_db: dict,
        battery_db: dict,
        clamped_warnings: list[str],
    ) -> tuple[float, float, list[str]]:
        """
        Ramène calc_current et brake_current dans les limites physiques du
        contrôleur FTESC ET dans les limites du moteur sélectionné.

        Toute valeur recadrée génère un avertissement visible dans le résumé.
        """
        motor_physical_max = float(motor_db["max_current"])
        hard_max           = HARD_LIMITS["max_motor_current_a"]

        # Limite 1 : ne jamais dépasser le max physique du moteur (DB)
        if calc_current > motor_physical_max:
            clamped_warnings.append(
                f"⚠️ Courant ramené de {calc_current} A → {motor_physical_max} A "
                f"(limite physique du moteur {motor_db.get('type','')})."
            )
            calc_current = motor_physical_max

        # Limite 2 : ne jamais dépasser la limite absolue hardware du FTESC
        if calc_current > hard_max:
            clamped_warnings.append(
                f"⚠️ Courant ramené de {calc_current} A → {hard_max} A "
                f"(limite hardware absolue FTESC)."
            )
            calc_current = hard_max

        # Recalcule brake_current proportionnellement si le courant a changé
        brake_current = min(brake_current, calc_current)

        # Limite 3 : brake_current ne dépasse jamais la moitié du courant moteur
        brake_max = round(calc_current * 0.70, 1)
        if brake_current > brake_max:
            brake_current = brake_max

        return round(calc_current, 1), round(brake_current, 1), clamped_warnings

    # ── Formule vitesse max ───────────────────────────────────────────────────

    @staticmethod
    def estimate_speed(
        kv: float,
        voltage: float,
        duty: float,
        gear_ratio: float,
        wheel_mm: float,
    ) -> float:
        """
        Vitesse max théorique (km/h).

        Formule : V (km/h) = (KV × V_bat × duty × π × Ø_roue_m) / (ratio × 60 × 1000)

        Équivalent développé :
            RPM_moteur = KV × V × duty
            RPM_roue   = RPM_moteur / ratio
            V_kmh      = RPM_roue × π × Ø_m × 60 / 1000
        """
        wheel_m    = wheel_mm / 1000.0
        rpm_motor  = kv * voltage * duty
        rpm_wheel  = rpm_motor / gear_ratio
        # circonférence × RPM_roue → m/min → km/h
        speed_kmh  = rpm_wheel * math.pi * wheel_m * 60.0 / 1000.0
        return round(speed_kmh, 1)

    # ── Résolution des paramètres d'entrée ────────────────────────────────────

    @staticmethod
    def _resolve_kv(inputs: WizardInputs, motor_db: dict) -> float:
        if inputs.kv_override is not None:
            return float(inputs.kv_override)
        kv_min, kv_max = motor_db["kv_range"]
        return float((kv_min + kv_max) / 2)

    @staticmethod
    def _resolve_gear_ratio(inputs: WizardInputs, trans_db: dict) -> float:
        if inputs.transmission == "Direct Drive":
            return 1.0
        return max(inputs.gear_ratio, 0.1)

    @staticmethod
    def _resolve_wheel(inputs: WizardInputs, motor_db: dict) -> float:
        if inputs.wheel_mm is not None:
            return float(inputs.wheel_mm)
        hub_wheel = motor_db.get("wheel_mm")
        if hub_wheel is not None:
            return float(hub_wheel)
        return 90.0   # valeur par défaut si non renseigné

    # ── Limites de tension ────────────────────────────────────────────────────

    @staticmethod
    def _voltage_limits(battery_db: dict) -> tuple[float, float, float]:
        """
        Retourne (voltage_max, voltage_min, voltage_cutoff).

        voltage_max    : limite haute (tension de charge complète)
        voltage_min    : tension de démarrage alarme (min_v + 5 %)
        voltage_cutoff : coupure basse avec marge de sécurité (+1 V)
        """
        v_max    = battery_db["max_v"]
        v_min    = battery_db["min_v"]
        v_cutoff = round(v_min + 1.0, 1)       # coupure 1 V au-dessus du minimum absolu
        v_alarm  = round(v_min + (v_max - v_min) * 0.05, 1)   # alarme à 5 % au-dessus du min
        return v_max, v_alarm, v_cutoff

    # ── Gains PID adaptatifs ──────────────────────────────────────────────────

    @staticmethod
    def _pid_gains(profile: dict, motor_db: dict, gear_ratio: float) -> tuple[float, float, float]:
        """
        Estime Kp, Ki, Kd à partir de l'inertie relative.

        Heuristique : plus le moteur est grand (max_current élevé) et plus
        le ratio est grand, plus l'inertie est forte → gains plus faibles.
        On applique un facteur d'échelle sur les gains de référence du profil.
        """
        # Inertie relative (normalisée autour de 80 A / ratio 3.0)
        inertia_factor = (motor_db["max_current"] / 80.0) * (gear_ratio / 3.0)
        # Clamper entre 0.5 et 2.5 pour éviter les extrêmes
        inertia_factor = max(0.5, min(2.5, inertia_factor))

        kp_base = profile["pid_kp"]
        ki_base = profile["pid_ki"]
        kd_base = profile["pid_kd"]

        # Plus l'inertie est grande, plus les gains sont réduits
        scale = 1.0 / inertia_factor
        kp = round(kp_base * scale, 5)
        ki = round(ki_base * scale, 5)
        kd = round(kd_base * scale, 5)

        # Clamper dans les plages acceptées par LimitsConfig / SpeedPIDConfig
        kp = max(0.001, min(1.0, kp))
        ki = max(0.001, min(1.0, ki))
        kd = max(0.0,   min(1.0, kd))

        return kp, ki, kd

    # ── Construction de MotorConfig ───────────────────────────────────────────

    @staticmethod
    def _build_motor_config(
        motor_db: dict,
        kv: float,
        calc_current: float,
        brake_current: float,
        voltage_max: float,
        voltage_min: float,
        voltage_cutoff: float,
        erpm_max: float,
        erpm_rev: float,
        bat_current: float,
        profile: dict,
        kp: float,
        ki: float,
        kd: float,
    ) -> MotorConfig:
        """Construit un MotorConfig cohérent depuis les valeurs calculées."""

        resistance = motor_db["resistance_mohm"] / 1000.0      # mΩ → Ω (valeur phase-phase)
        inductance = motor_db["inductance_uh"] / 1000.0         # µH → mH

        abs_current = round(calc_current * 1.25, 1)    # 25 % de marge au-dessus du nominal

        limits = LimitsConfig(
            max_erpm             = float(erpm_max),
            max_erpm_reverse     = float(erpm_rev),
            max_duty             = profile["max_duty"],
            min_duty             = 0.03,
            max_input_voltage    = voltage_max,
            min_input_voltage    = voltage_cutoff,
            max_battery_current  = bat_current,
            max_battery_current_rev = round(bat_current * 0.5, 1),
            max_motor_current    = calc_current,
            max_motor_current_rev = round(calc_current * 0.5, 1),
            max_absolute_current = min(abs_current, 200.0),
            temp_fet_max         = profile["temp_fet_max"],
            temp_fet_start       = profile["temp_fet_start"],
            slow_abs_overvoltage = True,
            slow_abs_undervoltage= True,
        )

        ramp = RampConfig(
            ramp_up_time         = profile["ramp_up_time"],
            ramp_down_time       = profile["ramp_down_time"],
            startup_speed        = 8.0,
            cool_down_time       = 5.0,
            acceleration_current = calc_current,
            deceleration_current = brake_current,
        )

        brake_cfg = BrakeConfig(
            brake_current        = brake_current,
            brake_current_ramp   = round(brake_current * 0.3, 1),
            regen_braking        = True,
            regen_voltage_max    = voltage_max * 0.95,
            brake_temperature_limit = profile["temp_motor_max"] + 15.0,
        )

        foc = FOCConfig(
            mode              = profile["foc_mode"],
            current_kp        = 0.1,
            current_ki        = 0.01,
            fsw               = 20.0,
            dead_time         = 50.0,
            openloop_rpm      = 300.0,
            openloop_lock     = True,
            observer_gain     = 10.0,
            observer_gain_slow= 5.0,
            pll_kp            = 1000.0,
            pll_ki            = 100.0,
            antiwindup        = 0.5,
            duty_kp           = 0.1,
            duty_ki           = 0.01,
            sat_comp          = True,
        )

        hall = HallConfig(
            enabled           = True,
            direction         = False,
            interpolation     = True,
        )

        speed_pid = SpeedPIDConfig(
            kp               = kp,
            ki               = ki,
            kd               = kd,
            min_erpm         = 500.0,
            max_erpm         = float(erpm_max),
            error_tolerance  = 0.05,
        )

        input_ctrl = InputControlConfig(
            throttle_curve   = profile["throttle_curve"],
            throttle_deadband= profile["throttle_deadband"],
        )

        # Clamp temp_motor_start / max dans les plages valides du validateur
        temp_max   = max(50.0, min(150.0, profile["temp_motor_max"]))
        temp_start = max(40.0, min(130.0, profile["temp_motor_start"]))
        if temp_start > temp_max:
            temp_start = temp_max - 5.0

        return MotorConfig(
            motor_type        = MotorType.BLDC,
            pole_pairs        = int(motor_db["pole_pairs"]),
            resistance        = max(0.001, min(10.0, resistance)),
            inductance        = max(0.001, min(100.0, inductance)),
            kv_rating         = round(kv, 1),
            max_current       = calc_current,
            max_brake_current = brake_current,
            current_ramp_step = round(calc_current * 0.15, 1),
            temp_motor_max    = temp_max,
            temp_motor_start  = temp_start,
            hall              = hall,
            foc               = foc,
            ramp              = ramp,
            brake             = brake_cfg,
            input_control     = input_ctrl,
            limits            = limits,
            speed_pid         = speed_pid,
        )

    # ── Construction de BatteryConfig ────────────────────────────────────────

    @staticmethod
    def _build_battery_config(battery_db: dict, bat_current: float) -> BatteryConfig:
        chemistry_map = {
            "LiPo":     BatteryType.LI_PO,
            "Li-Ion":   BatteryType.LI_ION,
            "LiFePO4":  BatteryType.LI_FE_PO4,
        }
        btype = chemistry_map.get(battery_db["chemistry"], BatteryType.LI_PO)
        cutoff_end   = round(battery_db["min_v"] + 0.5, 1)
        cutoff_start = round(battery_db["min_v"] + 2.0, 1)
        return BatteryConfig(
            battery_type       = btype,
            cells              = int(battery_db["cells"]),
            capacity           = 5.0,     # inconnu → valeur par défaut prudente
            voltage_max        = battery_db["max_v"],
            voltage_min        = battery_db["min_v"],
            cutoff_start       = cutoff_start,
            cutoff_end         = cutoff_end,
            charge_max         = round(bat_current * 0.3, 1),
            internal_resistance= 0.05,
        )

    # ── Contrôles de cohérence ────────────────────────────────────────────────

    @staticmethod
    def _check_compatibility(
        motor_db: dict,
        battery_db: dict,
        calc_current: float,
        speed_kmh: float,
        profile_name: str,
        gear_ratio: float,
    ) -> list[str]:
        warnings: list[str] = []
        v_max    = battery_db["max_v"]
        hw_v_max = HARD_LIMITS["max_voltage_v"]
        hw_i_max = HARD_LIMITS["max_motor_current_a"]

        # Tension dépassant la limite hardware
        if v_max > hw_v_max:
            warnings.append(
                f"Tension max {v_max} V dépasse la limite recommandée du FTESC "
                f"({hw_v_max} V). Vérifiez la tension max du contrôleur."
            )

        # Courant élevé (proche de la limite hardware)
        if calc_current > hw_i_max * 0.85:
            warnings.append(
                f"Courant calculé ({calc_current} A) proche de la limite hardware "
                f"({hw_i_max} A). Assurez-vous que le FTESC supporte ce niveau."
            )

        # Vitesse > 80 km/h en profil Débutant → incohérence
        if profile_name == "Débutant" and speed_kmh > 60.0:
            warnings.append(
                f"Vitesse théorique élevée ({speed_kmh} km/h) pour un profil Débutant. "
                "Envisagez un ratio de transmission plus grand."
            )

        # Vitesse > 120 km/h → alerte générale
        if speed_kmh > 120.0:
            warnings.append(
                f"Vitesse théorique très élevée ({speed_kmh} km/h). "
                "Vérifiez le ratio de transmission et le diamètre de roue."
            )

        # Directive 32 : Avertissement si vitesse très élevée (seuil configurable)
        if speed_kmh > 80.0:
            warnings.append(_("wizard.warning.speed_high"))

        # Directive 32 : Avertissement si rapport de réduction extrême
        if gear_ratio < 1.5 or gear_ratio > 6.0:
            warnings.append(_("wizard.warning.gear_ratio_extreme"))

        # Courant quasi-nul (moteur très faible + profil débutant)
        if calc_current < 5.0:
            warnings.append(
                f"Courant calculé très faible ({calc_current} A). "
                "Performances probablement insuffisantes."
            )

        return warnings
