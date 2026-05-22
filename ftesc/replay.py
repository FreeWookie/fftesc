# -*- coding: utf-8 -*-
"""
ftesc/replay.py — Rejeu chronométré d'un fichier CSV enregistré par FtescDataLogger.

Format CSV attendu (colonnes définies par FtescDataLogger.HEADERS) :
    timestamp, motor, controller_id, voltage, input_current, motor_current,
    rpm, duty, temp_fet, temp_motor, cpu_load, encoder_angle, fault

Usage :
    thread = CsvReplayThread("session.csv", callback)
    thread.start()
    # ...
    thread.stop()

Le callback reçoit un FtescDualData reconstruit à partir de chaque paire
de lignes A+B du CSV, avec le même écart temporel que lors de l'enregistrement.
"""

import csv
import threading
import time
from typing import Callable, Optional

from .data import FtescRealtimeData, FtescDualData


def _parse_fault(fault_str: str) -> int:
    """Convertit '0x04' ou '4' en entier."""
    try:
        s = fault_str.strip()
        if s.startswith("0x") or s.startswith("0X"):
            return int(s, 16)
        return int(s)
    except (ValueError, AttributeError):
        return 0


def _row_to_realtime(row: dict) -> FtescRealtimeData:
    """Convertit une ligne CSV en FtescRealtimeData."""
    return FtescRealtimeData(
        controller_id  = int(float(row.get("controller_id", 0))),
        fault          = _parse_fault(row.get("fault", "0")),
        inp_voltage    = float(row.get("voltage", 0.0)),
        input_current  = float(row.get("input_current", 0.0)),
        motor_current  = float(row.get("motor_current", 0.0)),
        rpm            = float(row.get("rpm", 0.0)),
        duty_cycle_now = float(row.get("duty", 0.0)),
        temp_fet       = float(row.get("temp_fet", 0.0)),
        temp_motor     = float(row.get("temp_motor", 0.0)),
        cpu_load       = float(row.get("cpu_load", 0.0)),
        encoder_angle  = float(row.get("encoder_angle", 0.0)),
    )


class CsvReplayThread(threading.Thread):
    """
    Thread de rejeu chronométré d'un fichier CSV FFTESC.

    Regroupe les lignes par timestamp : chaque instant produit un
    FtescDualData (moteur A + moteur B).  L'écart entre deux instants
    est respecté (limité à 2 s max par pas pour éviter de longues pauses).

    Paramètres
    ----------
    filepath   : chemin vers le fichier CSV
    on_data    : callable(FtescDualData) — appelé pour chaque instant reconstitué
    speed      : facteur de vitesse (1.0 = temps réel, 2.0 = double vitesse)
    """

    MAX_STEP_S = 2.0    # pause max entre deux instants (évite les longues attentes)

    def __init__(
        self,
        filepath: str,
        on_data: Callable[[FtescDualData], None],
        speed: float = 1.0,
    ):
        super().__init__(daemon=True)
        self._filepath = filepath
        self._on_data  = on_data
        self._speed    = max(0.01, speed)
        self._stop_evt = threading.Event()

    # ── API publique ──────────────────────────────────────────────────────────

    def stop(self):
        """Demande l'arrêt propre du thread."""
        self._stop_evt.set()

    def is_alive(self) -> bool:
        return super().is_alive()

    # ── Boucle principale ─────────────────────────────────────────────────────

    def run(self):
        try:
            groups = self._load_csv()
        except Exception as e:
            print(f"[Replay] Erreur lecture CSV '{self._filepath}': {e}")
            return

        if not groups:
            print(f"[Replay] Fichier vide ou sans données valides : {self._filepath}")
            return

        prev_ts: Optional[float] = None

        for ts, data_a, data_b in groups:
            if self._stop_evt.is_set():
                break

            # Respect du timing original
            if prev_ts is not None:
                delta = (ts - prev_ts) / self._speed
                delta = min(delta, self.MAX_STEP_S)
                if delta > 0:
                    self._stop_evt.wait(timeout=delta)
                    if self._stop_evt.is_set():
                        break

            dual = FtescDualData(
                motor_a   = data_a,
                motor_b   = data_b,
                timestamp = ts,
            )
            try:
                self._on_data(dual)
            except Exception as e:
                print(f"[Replay] Erreur callback : {e}")

            prev_ts = ts

    # ── Lecture et regroupement du CSV ────────────────────────────────────────

    def _load_csv(self) -> list[tuple[float, FtescRealtimeData, FtescRealtimeData]]:
        """
        Lit le CSV et retourne une liste de (timestamp, data_A, data_B) triée.

        Stratégie de regroupement :
        - Les lignes sont groupées par timestamp identique (deux lignes A+B
          enregistrées au même moment par log_dual).
        - Si un groupe n'a qu'une ligne (moteur A ou B seulement), l'autre
          est complété avec un FtescRealtimeData par défaut.
        - Les timestamps sont horodatés en secondes Unix (float).
        """
        groups: dict[float, dict[str, FtescRealtimeData]] = {}

        with open(self._filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts    = float(row["timestamp"])
                    motor = row.get("motor", "A").strip().upper()
                    data  = _row_to_realtime(row)
                except (KeyError, ValueError):
                    continue   # ligne corrompue → ignorée

                if ts not in groups:
                    groups[ts] = {}
                groups[ts][motor] = data

        if not groups:
            return []

        # Tri chronologique + reconstitution paire A/B
        result: list[tuple[float, FtescRealtimeData, FtescRealtimeData]] = []
        for ts in sorted(groups):
            pair = groups[ts]
            data_a = pair.get("A", FtescRealtimeData(controller_id=0))
            data_b = pair.get("B", FtescRealtimeData(controller_id=1))
            result.append((ts, data_a, data_b))

        return result
