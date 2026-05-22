"""Chargeur de traduction i18n pour FFTESC.

Usage:
    from gui.i18n import _, lang, available_langs, set_language

    # Dans un widget CTk :
    ctk.CTkLabel(root, text=_("connection.connect"))
"""

import json
import os
from typing import Optional
from ftesc.resources import get_resource_path

_TRANSLATIONS: dict[str, str] = {}
_CURRENT_LANG: str = "fr"
_FALLBACK: dict[str, str] = {}

_AVAILABLE_LANGS = {
    "fr": "Français",
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
    "pl": "Polski",
    "it": "Italiano",
}


def _load_json(lang: str) -> dict[str, str]:
    path = get_resource_path("gui", "i18n", f"{lang}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def set_language(lang: str) -> bool:
    global _TRANSLATIONS, _CURRENT_LANG
    data = _load_json(lang)
    if not data:
        return False
    _TRANSLATIONS = data
    _CURRENT_LANG = lang
    return True


def _(key: str) -> str:
    return _TRANSLATIONS.get(key, _FALLBACK.get(key, key))


def lang() -> str:
    return _CURRENT_LANG


def available_langs() -> dict[str, str]:
    return dict(_AVAILABLE_LANGS)


# Chargement par défaut
_FALLBACK = _load_json("fr")
if not _FALLBACK:
    _FALLBACK = {}
set_language("fr")
