# -*- coding: utf-8 -*-
"""
ftesc/profiles.py — Gestion des profils de configuration moteur.

Permet de sauvegarder et charger des configurations complètes
(MotorConfig A & B) dans des fichiers JSON.
"""

import json
from pathlib import Path
from typing import Optional

from .data import DualMotorConfig, MotorConfig, MotorType

PROFILES_DIR = Path.home() / ".fftesc_profiles"
PROFILES_DIR.mkdir(exist_ok=True)


def save_profile(name: str, config: DualMotorConfig) -> bool:
    """Sauvegarde un profil nommé."""
    filepath = PROFILES_DIR / f"{name}.json"
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=4)
        return True
    except Exception as e:
        print(f"Erreur sauvegarde profil : {e}")
        return False


def load_profile(name: str) -> Optional[DualMotorConfig]:
    """Charge un profil nommé."""
    filepath = PROFILES_DIR / f"{name}.json"
    if not filepath.exists():
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return DualMotorConfig.from_dict(data)
    except Exception as e:
        print(f"Erreur chargement profil : {e}")
        return None


def list_profiles() -> list[str]:
    """Liste tous les profils disponibles."""
    return sorted(f.stem for f in PROFILES_DIR.glob("*.json"))


def delete_profile(name: str) -> bool:
    """Supprime un profil."""
    filepath = PROFILES_DIR / f"{name}.json"
    if filepath.exists():
        try:
            filepath.unlink()
            return True
        except:
            return False
    return False

def export_profile(name: str, filepath: str) -> bool:
    """Exporte un profil vers un fichier externe."""
    config = load_profile(name)
    if config is None:
        return False
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=4)
        return True
    except Exception as e:
        print(f"Erreur export profil : {e}")
        return False

def import_profile(filepath: str) -> Optional[DualMotorConfig]:
    """Importe un profil depuis un fichier externe."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return DualMotorConfig.from_dict(data)
    except Exception as e:
        print(f"Erreur import profil : {e}")
        return None
