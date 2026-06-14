"""Urbi Dream Layer (ΦΔ) — offline consolidation.

Canon-correct rewrite of the Gemini draft against the BUILT mebus (Mode enum, bus.publish(msg),
no version arg, monotonic τ). Runs only under μ=DREAM. Replays *prediction errors*, not raw
episodes (jumping-spider proof). Five sub-engines: REC / CTN / GEO / REP / COH (cm_rem_sleep canon).

Mode signalling: subscribes to `sys.mode` (sys.* control) with payload {"mode": "<MODE>"}.
On DREAM it consolidates queued errors and emits a cognition-class `m.belief` patch to SMC
(cognition flows in DREAM under Ω₈; SMC gates the actual COMPILE).
"""
from __future__ import annotations

import logging
from typing import Any

from ai_chi.bus import MMessage, MembraneBus, Mode

_LOG = logging.getLogger(__name__)
COH_EXIT = 0.75  # coherence exit threshold (cm_rem_sleep)


class DreamConsolidator:
    def __init__(self, bus: MembraneBus) -> None:
        self.bus = bus
        self.error_queue: list[MMessage] = []
        bus.subscribe("ext.outcome", self._queue_prediction_errors)
        bus.subscribe("sys.mode", self._on_mode)

    def _queue_prediction_errors(self, msg: MMessage) -> None:
        """Queue ONLY failed predictions (matched is False) for dream replay."""
        if not bool((msg.payload or {}).get("matched", True)):
            self.error_queue.append(msg)

    def _on_mode(self, msg: MMessage) -> None:
        mode = str((msg.payload or {}).get("mode", "")).upper()
        if mode == Mode.DREAM.value:
            _LOG.info("μ=DREAM acknowledged — engaging ΦΔ consolidation")
            self.run_cycle()

    def run_cycle(self) -> int:
        """Consolidate queued errors. Returns the number of patches committed to the bus."""
        committed = 0
        for err in list(self.error_queue):
            context = self._rec(err)            # REC — recapitulate provenance to the error
            void = self._ctn(context, err)       # CTN — counterpart / void shape of what's missing
            patch = self._geo(void)              # GEO — geometric repopulation offsets
            self._rep(patch)                     # REP — propagate into episodic indices
            if self._coh(patch) > COH_EXIT:      # COH — coherence verify before proposing
                self.bus.publish(MMessage(
                    sigma="m.belief",            # cognition-class patch (flows in DREAM)
                    payload={"patch": patch, "provenance": ["phi_delta"], "source": "dream"},
                    destination="sys.smc",
                    context={"trust_score": 1.0, "domain": "urbi.dream", "provenance": ["phi_delta"]},
                    mode=Mode.DREAM,
                ).validate())
                committed += 1
        self.error_queue.clear()
        return committed

    # --- sub-engine skeletons (honest stubs; populate next) ---
    def _rec(self, err: MMessage) -> dict[str, Any]:
        """REC: retrieve episodic topology leading to the error."""
        return {"error_fingerprint": err.fingerprint()}

    def _ctn(self, context: dict, err: MMessage) -> dict[str, Any]:
        """CTN: define the failure void / counterpart structure."""
        return {"void": True, **context}

    def _geo(self, void: dict) -> dict[str, Any]:
        """GEO: geometric repopulation offsets (placeholder diff)."""
        return {"geometry_diff": 0.05, "from": void}

    def _rep(self, patch: dict) -> None:
        """REP: propagate updated geometry into episodic indices (stub)."""
        return None

    def _coh(self, patch: dict) -> float:
        """COH: coherence score; > COH_EXIT means the patch is safe to propose (stub)."""
        return 0.8
