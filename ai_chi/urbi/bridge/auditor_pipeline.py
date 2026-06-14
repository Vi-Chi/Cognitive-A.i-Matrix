"""A.i Core wrapper around the existing Urbi <-> MΣBUS bridge."""
from __future__ import annotations

from typing import Any, Optional, Protocol

from ai_chi._paths import ensure_dependency_paths
from ai_chi.bus import MMessage, MembraneBus, Mode

ensure_dependency_paths()

import bridge as urbi_bridge  # noqa: E402


class Auditor(Protocol):
    def audit(self, claim: str, **kwargs: Any) -> dict: ...


class UrbiAuditorBridge:
    """Audit observations using the real v2.1 bridge, not a prompt stub."""

    def __init__(
        self,
        bus: Optional[MembraneBus] = None,
        auditor: Optional[Auditor] = None,
        *,
        destination: str = "orbi",
        mode: Mode = Mode.WAKE,
    ) -> None:
        self.bus = bus or MembraneBus()
        self._bridge = urbi_bridge.UrbiMebusBridge(
            self.bus,
            auditor,
            destination=destination,
            mode=mode,
        )

    def audit_observation(self, obs_env: MMessage, *, strict: bool = False) -> MMessage:
        """Convert an ``ext.observation`` into Urbi audited belief/prediction."""
        obs_env.validate()
        if obs_env.sigma != "ext.observation":
            raise ValueError(f"Urbi bridge expects ext.observation, got {obs_env.sigma}")
        claim = str(obs_env.payload.get("raw_data", ""))
        if not claim:
            raise ValueError("Observation payload missing raw_data")
        result = self._bridge.audit_and_publish(claim, mode=obs_env.mode, strict=strict)
        return result["message"]

    def set_mode(self, mode: Mode) -> None:
        self._bridge.set_mode(mode)
