# -*- coding: utf-8 -*-
"""
ftesc/config.py — Gestionnaire de configuration FFTESC
"""

import json
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = Path("config.json")

DEFAULT_CONFIG = {
    "default_port": "AUTO",
    "default_baudrate": 115200,
    "auto_connect": False,
    "theme": "dark",
    "chart_refresh_rate_ms": 100,
    "log_directory": "logs",
    "safety": {
        "max_temp_fet": 90.0,
        "max_temp_motor": 85.0,
        "max_current": 80.0,
        "max_voltage": 60.0,
        "estop_on_overtemp": True
    }
}


class FtescConfig:
    """Gestionnaire de configuration."""
    
    def __init__(self, filepath: str = None):
        self._filepath = Path(filepath) if filepath else CONFIG_FILE
        self._data: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> bool:
        """Charge la configuration depuis le fichier."""
        if self._filepath.exists():
            try:
                with open(self._filepath, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                return True
            except Exception as e:
                print(f"Erreur chargement config : {e}")
        
        self._data = DEFAULT_CONFIG.copy()
        return False
    
    def save(self) -> bool:
        """Sauvegarde la configuration dans le fichier."""
        try:
            with open(self._filepath, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=4)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde config : {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur de configuration."""
        keys = key.split('.')
        value = self._data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Définit une valeur de configuration."""
        keys = key.split('.')
        data = self._data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value
    
    @property
    def data(self) -> Dict[str, Any]:
        return self._data
    
    def reset(self):
        """Remet la configuration par défaut."""
        self._data = DEFAULT_CONFIG.copy()
        self.save()
