"""CAL / Ω4 windowed calibration monitor.

This is intentionally dependency-free. It tracks a population of resolved
prediction records and emits HALT only on sustained drift, not on one sample.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import fmean
from typing import Deque, Mapping, Any

from ai_chi.bus import MMessage, Mode


@dataclass(frozen=True)
class CalibrationSample:
    prediction_id: str
    confidence: float
    matched: bool
    actual_state: str
    brier_score: float
    signed_error: float


class CalibrationMonitor:
    """Windowed reliability monitor for Ω4."""

    def __init__(
        self,
        *,
        window_size: int = 20,
        min_window: int = 5,
        epsilon_cal: float = 0.25,
        brier_halt_threshold: float = 0.45,
        domain_label: str = "urbi.core.cal.omega4",
        cal_bins: int = 5,
        ece_threshold: float = 0.10,
        high_conf: float = 0.8,
    ) -> None:
        if min_window < 1 or window_size < min_window:
            raise ValueError("window_size must be >= min_window >= 1")
        self.samples: Deque[CalibrationSample] = deque(maxlen=window_size)
        self.min_window = min_window
        self.epsilon_cal = epsilon_cal
        self.brier_halt_threshold = brier_halt_threshold
        self.domain = domain_label
        self.cal_bins = max(1, cal_bins)
        self.ece_threshold = ece_threshold
        self.high_conf = high_conf

    def evaluate(
        self,
        prediction_id: str,
        confidence: float,
        *,
        matched: bool | None = None,
        actual_state: str = "",
        outcome: MMessage | Mapping[str, Any] | None = None,
        mode: Mode = Mode.WAKE,
    ) -> MMessage:
        """Record a resolved prediction and emit ``m.calibration`` or ``cm.alert``."""
        if outcome is not None:
            payload = outcome.payload if isinstance(outcome, MMessage) else dict(outcome)
            matched = bool(payload["matched"])
            actual_state = str(payload.get("actual_state", actual_state))
            prediction_id = str(payload.get("target_prediction_id", prediction_id))
        if matched is None:
            raise ValueError("matched must be supplied when outcome is not supplied")
        confidence = max(0.0, min(1.0, float(confidence)))
        truth = 1.0 if matched else 0.0
        signed_error = confidence - truth
        brier = signed_error * signed_error

        sample = CalibrationSample(
            prediction_id=prediction_id,
            confidence=confidence,
            matched=matched,
            actual_state=actual_state,
            brier_score=round(brier, 6),
            signed_error=round(signed_error, 6),
        )
        self.samples.append(sample)

        errors = [s.signed_error for s in self.samples]
        briers = [s.brier_score for s in self.samples]
        mean_error = fmean(errors)
        mean_abs_error = fmean(abs(e) for e in errors)
        mean_brier = fmean(briers)
        enough = len(self.samples) >= self.min_window

        shift = "calibrated"
        if enough and mean_error >= self.epsilon_cal:
            shift = "overconfident"
        elif enough and mean_error <= -self.epsilon_cal:
            shift = "underconfident"

        halt = bool(enough and mean_brier >= self.brier_halt_threshold)
        if halt:
            shift = "divergent_halt"

        # --- ECE / MCE / reliability (adaptive equal-mass bins) ---
        # Calibration of stated confidence vs. empirical correctness, the standard
        # instrument beyond Brier. Equal-mass binning has lower bias than fixed-width,
        # especially on skewed confidences. ECE < ece_threshold ≈ well-calibrated.
        ece, mce, bins, high_conf_fail = self._reliability(
            [(s.confidence, 1.0 if s.matched else 0.0) for s in self.samples])
        well_calibrated = bool(enough and ece < self.ece_threshold)

        payload = {
            "target_prediction_id": sample.prediction_id,
            "confidence": sample.confidence,
            "actual_state": sample.actual_state,
            "matched": sample.matched,
            "brier_score": sample.brier_score,
            "window_size": len(self.samples),
            "mean_signed_error": round(mean_error, 6),
            "mean_abs_error": round(mean_abs_error, 6),
            "mean_brier_score": round(mean_brier, 6),
            "ece": round(ece, 6),
            "mce": round(mce, 6),
            "reliability_bins": bins,
            "high_conf_failure_rate": round(high_conf_fail, 6),
            "well_calibrated": well_calibrated,
            "epsilon_cal": self.epsilon_cal,
            "ece_threshold": self.ece_threshold,
            "epistemic_shift": shift,
            "halt": halt,
        }
        return MMessage(
            sigma="cm.alert" if halt else "m.calibration",
            payload=payload,
            destination="urbi",
            context={
                "trust_score": 1.0,
                "domain": self.domain,
                "provenance": ["cal", "omega4"],
            },
            mode=mode,
        ).validate()

    def _reliability(
        self, pairs: list[tuple[float, float]]
    ) -> tuple[float, float, list[dict], float]:
        """Adaptive (equal-mass) ECE + MCE + reliability bins + high-conf failure rate.

        ``pairs`` = [(confidence, correct∈{0,1})]. Bins hold ~equal counts (lower bias
        than fixed-width on skewed confidence). Returns (ece, mce, bins, high_conf_fail).
        """
        n = len(pairs)
        if n == 0:
            return 0.0, 0.0, [], 0.0
        ordered = sorted(pairs, key=lambda p: p[0])
        n_bins = max(1, min(self.cal_bins, n))
        ece = 0.0
        mce = 0.0
        bins: list[dict] = []
        i = 0
        b = 0
        while i < n:
            hi = max(i + 1, min(n, round((b + 1) * n / n_bins)))
            # Ties must not split: samples with identical confidence share a bin
            # (you can't distinguish them). This also makes a constant-confidence
            # stream collapse to one bin -> ECE = |mean_conf - mean_acc| (no artifact).
            while hi < n and ordered[hi][0] == ordered[hi - 1][0]:
                hi += 1
            chunk = ordered[i:hi]
            conf = fmean(c for c, _ in chunk)
            acc = fmean(o for _, o in chunk)
            gap = abs(conf - acc)
            ece += (len(chunk) / n) * gap
            mce = max(mce, gap)
            bins.append({"n": len(chunk), "confidence": round(conf, 4),
                         "accuracy": round(acc, 4), "gap": round(gap, 4)})
            i = hi
            b += 1
        high = [(c, o) for c, o in pairs if c >= self.high_conf]
        high_conf_fail = (sum(1 for _, o in high if o == 0.0) / len(high)) if high else 0.0
        return ece, mce, bins, high_conf_fail
