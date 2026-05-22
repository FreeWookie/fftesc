# -*- coding: utf-8 -*-
"""
ftesc/logger.py — Enregistreur de données FFTESC

Écrit les données temps réel dans un fichier CSV
pour analyse ultérieure ou debug.

Format CSV :
    timestamp, motor, voltage, input_current, motor_current,
    rpm, duty, temp_fet, temp_motor, cpu_load, encoder_angle, fault
"""

import csv
import time
import os
from pathlib import Path
from typing import Optional
from .data import FtescDualData, FtescRealtimeData


class FtescDataLogger:
    """
    Logger CSV pour données FTESC.
    
    Usage :
        logger = FtescDataLogger("session_001.csv")
        logger.start()
        # ... les données arrivent ...
        logger.log_dual(dual_data)
        # ... plus tard ...
        logger.stop()
    """
    
    # En-têtes du CSV
    HEADERS = [
        'timestamp',
        'motor',
        'controller_id',
        'voltage',
        'input_current',
        'motor_current',
        'rpm',
        'duty',
        'temp_fet',
        'temp_motor',
        'cpu_load',
        'encoder_angle',
        'fault'
    ]
    
    def __init__(self, filename: Optional[str] = None, output_dir: str = "logs"):
        """
        Args:
            filename: Nom du fichier (auto-généré si None)
            output_dir: Dossier de sortie
        """
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(exist_ok=True)
        
        if filename:
            self._filepath = self._output_dir / filename
        else:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self._filepath = self._output_dir / f"fftesc_{timestamp}.csv"
        
        self._file = None
        self._writer = None
        self._row_count = 0
        self._is_running = False
    
    @property
    def filepath(self) -> str:
        return str(self._filepath)
    
    @property
    def row_count(self) -> int:
        return self._row_count
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    def start(self) -> bool:
        """Ouvre le fichier CSV et écrit les en-têtes."""
        try:
            self._file = open(self._filepath, 'w', newline='', encoding='utf-8')
            self._writer = csv.DictWriter(self._file, fieldnames=self.HEADERS)
            self._writer.writeheader()
            self._is_running = True
            self._row_count = 0
            return True
        except Exception as e:
            print(f"Erreur ouverture log : {e}")
            return False
    
    def stop(self):
        """Ferme le fichier CSV proprement."""
        if self._file:
            self._file.close()
            self._file = None
            self._writer = None
        self._is_running = False
    
    def log_motor(self, data: FtescRealtimeData, motor_label: str = "A"):
        """Enregistre les données d'un moteur."""
        if not self._is_running or not self._writer:
            return
        
        row = {
            'timestamp': f"{time.time():.3f}",
            'motor': motor_label,
            'controller_id': data.controller_id,
            'voltage': f"{data.inp_voltage:.2f}",
            'input_current': f"{data.input_current:.3f}",
            'motor_current': f"{data.motor_current:.3f}",
            'rpm': f"{data.rpm:.1f}",
            'duty': f"{data.duty_cycle_now:.4f}",
            'temp_fet': f"{data.temp_fet:.1f}",
            'temp_motor': f"{data.temp_motor:.1f}",
            'cpu_load': f"{data.cpu_load:.4f}",
            'encoder_angle': f"{data.encoder_angle:.2f}",
            'fault': f"0x{data.fault:02X}"
        }
        
        self._writer.writerow(row)
        self._row_count += 1
        
        # Flush toutes les 50 lignes pour ne pas perdre de données
        if self._row_count % 50 == 0:
            self._file.flush()
    
    def log_dual(self, dual: FtescDualData):
        """Enregistre les données des deux moteurs."""
        self.log_motor(dual.motor_a, "A")
        self.log_motor(dual.motor_b, "B")
