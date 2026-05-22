# -*- coding: utf-8 -*-
"""
gui/wizard_data.py — Base de données statique des matériels courants
pour l'assistant de configuration (Wizard).

Sources techniques :
  - Fiches constructeurs moteurs hub / outrunner classiques
  - Chimie LiPo (4.2 V/cell max, 3.0 V/cell cut-off standard)
  - Chimie LiFePO4 (3.65 V/cell max, 2.5 V/cell cut-off)
  - Ratios de transmission typiques eSK8 / trottinette électrique
"""
from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────────────
#  MOTEURS
#
#  Clés :
#    kv_range        : (kv_min, kv_max)  – plage KV typique du modèle
#    max_current     : A – courant moteur maximal absolu (limite physique)
#    pole_pairs      : nombre de paires de pôles (typique)
#    resistance_mohm : mΩ – résistance phase-phase typique
#    inductance_uh   : µH – inductance typique
#    type            : catégorie (Hub / Outrunner / Belt / Chain)
#    wheel_mm        : diamètre de roue intégré (None si moteur seul)
#    note            : information complémentaire
# ──────────────────────────────────────────────────────────────────────────────
MOTORS_DB: dict[str, dict] = {
    # ── Hubs moteurs (roue intégrée) ─────────────────────────────────────────
    "5045": {
        "kv_range":        (200, 320),
        "max_current":     40,
        "pole_pairs":      7,
        "resistance_mohm": 180,
        "inductance_uh":   15,
        "type":            "Hub Compact",
        "wheel_mm":        130,
        "note":            "Hub moteur 5\" – trottinette légère",
    },
    "5055": {
        "kv_range":        (150, 250),
        "max_current":     50,
        "pole_pairs":      7,
        "resistance_mohm": 140,
        "inductance_uh":   18,
        "type":            "Hub Mid",
        "wheel_mm":        140,
        "note":            "Hub moteur 5.5\" – polyvalent",
    },
    "5065": {
        "kv_range":        (100, 200),
        "max_current":     60,
        "pole_pairs":      10,
        "resistance_mohm": 110,
        "inductance_uh":   22,
        "type":            "Hub Large",
        "wheel_mm":        165,
        "note":            "Hub moteur 6.5\" – skateboard électrique",
    },
    "6374": {
        "kv_range":        (80, 170),
        "max_current":     80,
        "pole_pairs":      7,
        "resistance_mohm": 60,
        "inductance_uh":   35,
        "type":            "Outrunner Belt",
        "wheel_mm":        None,
        "note":            "Outrunner standard eSK8 – courroie",
    },
    "6384": {
        "kv_range":        (70, 150),
        "max_current":     90,
        "pole_pairs":      7,
        "resistance_mohm": 50,
        "inductance_uh":   40,
        "type":            "Outrunner Belt",
        "wheel_mm":        None,
        "note":            "Outrunner haute puissance – courroie ou direct",
    },
    "8080": {
        "kv_range":        (50, 120),
        "max_current":     100,
        "pole_pairs":      10,
        "resistance_mohm": 35,
        "inductance_uh":   55,
        "type":            "Hub Heavy Duty",
        "wheel_mm":        200,
        "note":            "Hub moteur 8\" – tout-terrain lourd",
    },
    # ── Hubs grande roue (trottinette urbaine) ───────────────────────────────
    "10inch_hub": {
        "kv_range":        (40, 90),
        "max_current":     120,
        "pole_pairs":      12,
        "resistance_mohm": 25,
        "inductance_uh":   70,
        "type":            "Hub XL",
        "wheel_mm":        255,
        "note":            "Hub moteur 10\" – cargo / trottinette lourde",
    },
    # ── Outrunners compacts (DIY belt) ───────────────────────────────────────
    "5045_out": {
        "kv_range":        (270, 400),
        "max_current":     35,
        "pole_pairs":      7,
        "resistance_mohm": 200,
        "inductance_uh":   12,
        "type":            "Outrunner Belt",
        "wheel_mm":        None,
        "note":            "Outrunner compact – mini eSK8 / onewheel",
    },
    "4055": {
        "kv_range":        (300, 500),
        "max_current":     25,
        "pole_pairs":      7,
        "resistance_mohm": 250,
        "inductance_uh":   10,
        "type":            "Outrunner Belt",
        "wheel_mm":        None,
        "note":            "Petit outrunner – prototype / test",
    },
    # ── Moteurs chaîne / transmission rigide ─────────────────────────────────
    "8085_chain": {
        "kv_range":        (45, 100),
        "max_current":     110,
        "pole_pairs":      12,
        "resistance_mohm": 28,
        "inductance_uh":   65,
        "type":            "Outrunner Chain",
        "wheel_mm":        None,
        "note":            "Outrunner transmission chaîne – moto électrique légère",
    },
    "mid_drive_750w": {
        "kv_range":        (25, 60),
        "max_current":     80,
        "pole_pairs":      16,
        "resistance_mohm": 40,
        "inductance_uh":   90,
        "type":            "Mid Drive",
        "wheel_mm":        None,
        "note":            "Moteur milieu de pédalier – vélo cargo",
    },
}

# ──────────────────────────────────────────────────────────────────────────────
#  BATTERIES
#
#  Clés :
#    cells       : nombre de cellules en série
#    nominal_v   : tension nominale totale (V) = cells × 3.7 (LiPo)
#    max_v       : tension max de charge (V)  = cells × 4.2 (LiPo)
#    min_v       : tension cut-off (V)        = cells × 3.0 (LiPo standard)
#    chemistry   : "LiPo" | "LiFePO4" | "Li-Ion"
#
#  Note : tensions arrondies à 1 décimale pour éviter les flottants parasites.
# ──────────────────────────────────────────────────────────────────────────────
BATTERIES_DB: dict[str, dict] = {
    # ── LiPo ─────────────────────────────────────────────────────────────────
    "4S LiPo": {
        "cells":      4,
        "nominal_v":  14.8,
        "max_v":      16.8,
        "min_v":      12.0,
        "chemistry":  "LiPo",
    },
    "6S LiPo": {
        "cells":      6,
        "nominal_v":  22.2,
        "max_v":      25.2,
        "min_v":      18.0,
        "chemistry":  "LiPo",
    },
    "8S LiPo": {
        "cells":      8,
        "nominal_v":  29.6,
        "max_v":      33.6,
        "min_v":      24.0,
        "chemistry":  "LiPo",
    },
    "10S LiPo": {
        "cells":      10,
        "nominal_v":  37.0,
        "max_v":      42.0,
        "min_v":      30.0,
        "chemistry":  "LiPo",
    },
    "12S LiPo": {
        "cells":      12,
        "nominal_v":  44.4,
        "max_v":      50.4,
        "min_v":      36.0,
        "chemistry":  "LiPo",
    },
    "14S LiPo": {
        "cells":      14,
        "nominal_v":  51.8,
        "max_v":      58.8,
        "min_v":      42.0,
        "chemistry":  "LiPo",
    },
    "16S LiPo": {
        "cells":      16,
        "nominal_v":  59.2,
        "max_v":      67.2,
        "min_v":      48.0,
        "chemistry":  "LiPo",
    },
    # ── Li-Ion (21700 / 18650 packs) – cellule 4.2 V / 2.5 V cut ────────────
    "10S Li-Ion": {
        "cells":      10,
        "nominal_v":  36.0,
        "max_v":      42.0,
        "min_v":      25.0,
        "chemistry":  "Li-Ion",
    },
    "13S Li-Ion": {
        "cells":      13,
        "nominal_v":  46.8,
        "max_v":      54.6,
        "min_v":      32.5,
        "chemistry":  "Li-Ion",
    },
    "14S Li-Ion": {
        "cells":      14,
        "nominal_v":  50.4,
        "max_v":      58.8,
        "min_v":      35.0,
        "chemistry":  "Li-Ion",
    },
    # ── LiFePO4 – cellule 3.65 V max / 2.5 V cut ─────────────────────────────
    "8S LiFePO4": {
        "cells":      8,
        "nominal_v":  25.6,
        "max_v":      29.2,
        "min_v":      20.0,
        "chemistry":  "LiFePO4",
    },
    "16S LiFePO4": {
        "cells":      16,
        "nominal_v":  51.2,
        "max_v":      58.4,
        "min_v":      40.0,
        "chemistry":  "LiFePO4",
    },
}

# ──────────────────────────────────────────────────────────────────────────────
#  TYPES DE TRANSMISSION
#
#  Chaque entrée expose :
#    ratio_range : (ratio_min, ratio_max) – ratio de réduction typique
#    efficiency  : rendement mécanique moyen (0–1)
#    note        : description
# ──────────────────────────────────────────────────────────────────────────────
TRANSMISSION_TYPES: dict[str, dict] = {
    "Direct Drive": {
        "ratio_range": (1.0, 1.0),
        "efficiency":  1.0,
        "note":        "Pas de réduction – moteur hub intégré à la roue",
    },
    "Poulie (Belt)": {
        "ratio_range": (2.0, 5.0),
        "efficiency":  0.92,
        "note":        "Courroie crantée GT2/GT3 – eSK8 / trottinette outrunner",
    },
    "Chaîne": {
        "ratio_range": (3.0, 8.0),
        "efficiency":  0.97,
        "note":        "Chaîne #25 ou #35 – transmission robuste tout-terrain",
    },
    "Engrenages (Gear)": {
        "ratio_range": (4.0, 12.0),
        "efficiency":  0.85,
        "note":        "Réducteur planétaire ou droit – torque élevé, plus bruyant",
    },
}

# ──────────────────────────────────────────────────────────────────────────────
#  PROFILS UTILISATEUR
#
#  Identifiants canoniques utilisés par WizardEngine.
# ──────────────────────────────────────────────────────────────────────────────
PROFILES: list[str] = ["Débutant", "Avancé", "Expert"]

# ──────────────────────────────────────────────────────────────────────────────
#  FONCTIONS UTILITAIRES
# ──────────────────────────────────────────────────────────────────────────────

def motor_names() -> list[str]:
    """Retourne la liste triée des modèles moteurs disponibles."""
    return sorted(MOTORS_DB.keys())


def battery_names() -> list[str]:
    """Retourne la liste triée des configurations batterie disponibles."""
    return sorted(BATTERIES_DB.keys())


def transmission_names() -> list[str]:
    """Retourne la liste des types de transmission (ordre de déclaration)."""
    return list(TRANSMISSION_TYPES.keys())


def get_motor(name: str) -> dict:
    """
    Retourne les données d'un moteur par son nom.
    Lève KeyError si le modèle est inconnu.
    """
    if name not in MOTORS_DB:
        raise KeyError(f"Moteur inconnu : '{name}'. Disponibles : {motor_names()}")
    return MOTORS_DB[name]


def get_battery(name: str) -> dict:
    """
    Retourne les données d'une batterie par son nom.
    Lève KeyError si la configuration est inconnue.
    """
    if name not in BATTERIES_DB:
        raise KeyError(f"Batterie inconnue : '{name}'. Disponibles : {battery_names()}")
    return BATTERIES_DB[name]


def get_transmission(name: str) -> dict:
    """
    Retourne les données d'un type de transmission par son nom.
    Lève KeyError si le type est inconnu.
    """
    if name not in TRANSMISSION_TYPES:
        raise KeyError(
            f"Transmission inconnue : '{name}'. Disponibles : {transmission_names()}")
    return TRANSMISSION_TYPES[name]
