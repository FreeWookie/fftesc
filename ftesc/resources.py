# -*- coding: utf-8 -*-
"""Resource path resolver for PyInstaller frozen mode."""

import sys
import os


def get_resource_path(*relative_parts: str) -> str:
    """Resolve a resource path, handling PyInstaller --onefile mode.

    When frozen via PyInstaller, resources are extracted to a temporary
    directory accessible via sys._MEIPASS. This function returns the
    correct absolute path in both development and frozen modes.

    Usage:
        get_resource_path("docs", "param_descriptions.json")
        get_resource_path("fftesc_logo.svg")
        get_resource_path("gui", "i18n", "fr.json")
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *relative_parts)
