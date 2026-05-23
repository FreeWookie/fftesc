"""
ftesc/motor_detection.py — Détection de moteur par rotation libre (KV + pôles)
"""

import time
import logging
import queue
from dataclasses import dataclass, field
from typing import Optional

from .protocol import (
    UartCommand, build_frame, decompose_f16, parse_realtime_data,
)
from .transport import FtescTransport
from .data import FtescRealtimeData

logger = logging.getLogger('ftesc.motor_detection')


class MotorDetectionError(Exception):
    pass


@dataclass
class DetectionSample:
    duty: float
    v_bat: float
    rpm_elec: float
    current: float


@dataclass
class MotorDetectionResult:
    kv_elec: float = 0.0
    kv_mech: float = 0.0
    pole_pairs: int = 0
    samples: list[DetectionSample] = field(default_factory=list)
    motor_type_hint: str = ""
    success: bool = False
    error: str = ""


class MotorDetector:
    MAX_DUTY = 0.10
    MAX_CURRENT = 8.0
    STABILIZE_S = 1.5
    SAMPLE_INTERVAL = 0.05
    SAMPLES_PER_POINT = 5

    def __init__(self, transport: FtescTransport):
        self._transport = transport

    def _flush_queue(self):
        while True:
            try:
                self._transport._response_queue.get_nowait()
            except queue.Empty:
                break

    def _listen_passive(self, timeout: float = 1.0) -> Optional[FtescRealtimeData]:
        """Écoute toute trame OBTAIN_DATA_ONCE arrivant de l'ESC
        (auto-obtain, réponse différée, etc.)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                cmd, payload = self._transport._response_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            logger.debug("Trame passive cmd=%d len=%d hex=%s",
                         cmd, len(payload), payload.hex()[:80])
            if cmd == UartCommand.OBTAIN_DATA_ONCE and len(payload) >= 2:
                try:
                    data = parse_realtime_data(payload)
                    return data
                except Exception as e:
                    logger.warning("Impossible de parser OBTAIN_DATA_ONCE: %s", e)
        return None

    def _obtain_once(self, timeout: float = 2.0, retries: int = 3) -> Optional[FtescRealtimeData]:
        # Vide les trames périmées
        self._flush_queue()
        for attempt in range(retries):
            raw = build_frame(UartCommand.OBTAIN_DATA_ONCE, b'')
            self._transport.send(raw)
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    cmd, payload = self._transport._response_queue.get(timeout=0.05)
                except queue.Empty:
                    continue
                if cmd == UartCommand.OBTAIN_DATA_ONCE:
                    if len(payload) < 2:
                        logger.warning("Payload OBTAIN_DATA_ONCE trop court: %s", payload.hex())
                        continue
                    data = parse_realtime_data(payload)
                    return data
                # Log toute autre trame reçue pour debug
                logger.debug("Trame reçue (cmd=%d, len=%d): %s", cmd, len(payload), payload.hex()[:60])
            logger.warning("Tentative %d/%d: pas de réponse OBTAIN_DATA_ONCE", attempt + 1, retries)
        return None

    def _set_duty(self, duty: float):
        payload = decompose_f16(duty, 10000.0)
        frame = build_frame(UartCommand.SET_DUTY, payload)
        self._transport.send(frame)

    def _stop_motor(self):
        payload = decompose_f16(0.0, 10000.0)
        frame = build_frame(UartCommand.SET_DUTY, payload)
        self._transport.send(frame)

    def _read_sample(self, duty: float) -> Optional[DetectionSample]:
        self._set_duty(duty)
        time.sleep(self.STABILIZE_S)
        rpm_sum = 0.0
        v_sum = 0.0
        i_sum = 0.0
        ok = 0
        for _ in range(self.SAMPLES_PER_POINT):
            data = self._obtain_once()
            if data is None:
                continue
            if data.motor_current > self.MAX_CURRENT:
                logger.warning("Courant trop élevé: %.1f A", data.motor_current)
                self._stop_motor()
                return None
            rpm_sum += data.rpm
            v_sum += data.inp_voltage
            i_sum += data.motor_current
            ok += 1
            time.sleep(self.SAMPLE_INTERVAL)
        if ok < 2:
            self._stop_motor()
            return None
        return DetectionSample(
            duty=duty,
            v_bat=v_sum / ok,
            rpm_elec=rpm_sum / ok,
            current=i_sum / ok,
        )

    def detect(self) -> MotorDetectionResult:
        result = MotorDetectionResult()
        try:
            if not self._transport.is_connected:
                raise MotorDetectionError("Transport non connecté")

            data0 = self._obtain_once()
            # Si OBTAIN_DATA_ONCE ne répond pas, tenter d'écouter
            # les trames déjà dans la queue (auto-obtain, etc.)
            if data0 is None:
                logger.info("OBTAIN_DATA_ONCE sans réponse, écoute passive...")
                data0 = self._listen_passive(timeout=1.0)
            if data0 is None:
                raise MotorDetectionError(
                    "Aucune réponse de l'ESC. Vérifiez que l'ESC est "
                    "alimenté et que le câblage UART est correct.")
            logger.info("Vbat initiale: %.2f V, RPM: %.0f", data0.inp_voltage, data0.rpm)

            duty_steps = [0.03, 0.05, 0.07, 0.10]
            samples: list[DetectionSample] = []

            for duty in duty_steps:
                logger.info("Mesure à duty=%.0f%%...", duty * 100)
                s = self._read_sample(duty)
                if s is None:
                    if duty <= 0.05:
                        raise MotorDetectionError(
                            "Aucun RPM mesuré. Vérifiez que le moteur est "
                            "branché et libre de tourner.")
                    logger.info("Pas d'accrochage à %.0f%%, on arrête", duty * 100)
                    break
                if s.rpm_elec < 50:
                    if duty <= 0.05:
                        raise MotorDetectionError(
                            "RPM trop faible. Le moteur ne tourne pas.")
                    break
                samples.append(s)
                logger.info("  → %.0f RPM elec, %.2f V, %.2f A",
                            s.rpm_elec, s.v_bat, s.current)

            if not samples:
                raise MotorDetectionError("Aucune mesure valide")

            # Ajustement linéaire: RPM_elec = KV_elec × V_bat × duty
            # On prend la moyenne des KV_elec calculés sur chaque point
            kv_sum = 0.0
            for s in samples:
                v_app = s.v_bat * s.duty
                if v_app > 0.5:
                    kv_sum += s.rpm_elec / v_app
            result.kv_elec = kv_sum / len(samples)
            result.samples = samples

            # Chercher dans wizard_data la meilleure correspondance
            best_match, best_poles, best_score = self._match_motor(result.kv_elec)
            if best_match:
                result.pole_pairs = best_poles
                result.kv_mech = result.kv_elec / best_poles
                result.motor_type_hint = best_match
                logger.info("Correspondance: %s (%.0f KV, %d pôles)",
                            best_match, result.kv_mech, best_poles)
            else:
                # Estimation: pôles typiques pour un outrunner ~7
                result.pole_pairs = 7
                result.kv_mech = result.kv_elec / 7
                result.motor_type_hint = "Inconnu (estimation 7 pôles)"

            result.success = True

        except MotorDetectionError as e:
            result.success = False
            result.error = str(e)
            logger.error("Détection échouée: %s", e)
        except Exception as e:
            self._stop_motor()
            result.success = False
            result.error = f"Erreur inattendue: {e}"
            logger.exception("Erreur de détection")

        self._stop_motor()
        return result

    @staticmethod
    def _match_motor(kv_elec: float) -> tuple[Optional[str], int, float]:
        try:
            from gui.wizard_data import MOTORS_DB
        except ImportError:
            return None, 0, 0.0
        best_name = None
        best_poles = 0
        best_score = float('inf')
        for name, data in MOTORS_DB.items():
            kv_min, kv_max = data.get("kv_range", (0, 0))
            poles = data.get("pole_pairs", 0)
            kv_elec_min = kv_min * poles
            kv_elec_max = kv_max * poles
            if kv_elec_min <= kv_elec <= kv_elec_max:
                mid = (kv_elec_min + kv_elec_max) / 2
                score = abs(kv_elec - mid) / max(mid, 1)
                if score < best_score:
                    best_score = score
                    best_name = name
                    best_poles = poles
        # Si aucun match exact, chercher le plus proche
        if best_name is None:
            for name, data in MOTORS_DB.items():
                kv_min, kv_max = data.get("kv_range", (0, 0))
                poles = data.get("pole_pairs", 0)
                kv_elec_min = kv_min * poles
                kv_elec_max = kv_max * poles
                mid = (kv_elec_min + kv_elec_max) / 2
                score = abs(kv_elec - mid) / max(mid, 1)
                if score < best_score:
                    best_score = score
                    best_name = name
                    best_poles = poles
        if best_name and best_score < 0.5:
            return best_name, best_poles, best_score
        return (best_name, best_poles, best_score) if best_name else (None, 0, 0.0)

    @staticmethod
    def match_by_kv(kv_mech: float, pole_pairs: int) -> tuple[Optional[str], float]:
        """Cherche le moteur le plus proche dans la base à partir du KV mécanique."""
        kv_elec = kv_mech * pole_pairs
        name, _, score = MotorDetector._match_motor(kv_elec)
        return name, score
