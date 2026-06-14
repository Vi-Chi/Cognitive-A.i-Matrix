"""MΣBUS m.* cognition payloads — the geometric M-tuple carried inside the envelope.

Recovered from `_Documentation/M-Protocol + Sigma Bus_prototype.txt` (the Pydantic prototype the
MEBUS README cites as canonical). That tuple shares the field letters (v,σ,π,δ,κ,τ,μ) with the
MΣBUS transport envelope but means the *cognition* reading — and per the envelope-vs-payload
reconciliation it is a **payload** carried inside the envelope's π, dispatched by σ-class `m.*`:

    v  vector        list[float]      geometry / GSS embedding (default 2048-d)
    σ  uncertainty   UncertaintyDist  epistemic distribution (never optional)
    π  provenance    list[CausalRef]  causal genealogy chain
    δ  domain        DomainTag        routing/domain key
    κ  confidence     float[0,1]      calibrated (Brier) confidence
    τ  causal order   int             monotonic counter (not wall-clock)
    μ  mode           Mode            WAKE / LIMINAL / DREAM

Stdlib-only. The prototype's pydantic/numpy/msgpack deps are deliberately dropped; msgpack is an
optional fast-path only (guarded import).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional

from .protocol import MMessage, Mode, MessageValidationError, monotonic_tau


class DomainTag(str, Enum):
    """Routing/domain key (δ of the cognition tuple)."""
    MARITIME_NAV = "maritime.nav"
    MARITIME_SITUATIONAL = "maritime.situational"
    MARITIME_WEATHER = "maritime.weather"
    MARITIME_VESSEL = "maritime.vessel"
    DIGITAL_GUI = "digital.gui"
    MODEL_INTERACTION = "model.interaction"
    SYSTEM_AUDIT = "system.audit"
    CURIOSITY = "curiosity"


class UncertaintyType(str, Enum):
    POINT = "point"
    GAUSSIAN = "gaussian"
    CATEGORICAL = "categorical"
    DIRICHLET = "dirichlet"
    MULTIVARIATE = "multivariate"


@dataclass
class UncertaintyDist:
    """σ — a structured epistemic uncertainty distribution (never optional in cognition)."""
    type: UncertaintyType
    params: dict = field(default_factory=dict)
    support: Optional[list] = None

    @classmethod
    def point(cls, value: Any) -> "UncertaintyDist":
        return cls(UncertaintyType.POINT, {"value": value})

    @classmethod
    def gaussian(cls, mean: float, var: float) -> "UncertaintyDist":
        return cls(UncertaintyType.GAUSSIAN, {"mean": mean, "var": var})

    def to_dict(self) -> dict:
        return {"type": self.type.value, "params": self.params, "support": self.support}


@dataclass
class CausalRef:
    """π element — one link in the causal provenance genealogy."""
    node_id: str
    timestamp: int            # causal order, not wall-clock
    agent: str
    confidence: float = 1.0
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CognitionPayload:
    """The geometric m-tuple, carried as the π of an `m.*` MΣBUS message."""
    v: list                                  # geometry vector
    sigma: UncertaintyDist                   # σ uncertainty
    delta: DomainTag                         # δ domain
    kappa: float                             # κ calibrated confidence [0,1]
    tau: int = field(default_factory=monotonic_tau)
    mu: Mode = Mode.WAKE
    pi: list = field(default_factory=list)   # list[CausalRef]
    v_dim: int = 2048
    metadata: dict = field(default_factory=dict)

    def validate(self) -> "CognitionPayload":
        if not 0.0 <= self.kappa <= 1.0:
            raise MessageValidationError(f"κ (confidence) must be in [0,1], got {self.kappa}")
        if self.v and len(self.v) != self.v_dim:
            raise MessageValidationError(f"v has {len(self.v)} dims, v_dim={self.v_dim}")
        if not isinstance(self.sigma, UncertaintyDist):
            raise MessageValidationError("σ must be an UncertaintyDist")
        if not isinstance(self.mu, Mode):
            raise MessageValidationError("μ must be a Mode")
        return self

    def to_payload(self) -> dict:
        return {
            "v": list(self.v), "v_dim": self.v_dim,
            "sigma": self.sigma.to_dict(),
            "pi": [r.to_dict() for r in self.pi],
            "delta": self.delta.value,
            "kappa": self.kappa,
            "tau": self.tau,
            "mu": self.mu.value,
            "metadata": self.metadata,
        }

    def to_message(self, *, sigma: str = "m.state", destination: str = "urbi") -> MMessage:
        """Wrap as an MΣBUS m.* message (payload in π, domain/provenance in κ)."""
        self.validate()
        ctx = {
            "domain": self.delta.value,
            "provenance": [r.node_id for r in self.pi],
            "trust_score": self.kappa,
        }
        return MMessage(sigma=sigma, payload=self.to_payload(),
                        destination=destination, mode=self.mu, context=ctx).validate()

    # Optional fast binary path (only if msgpack is installed).
    def to_msgpack(self) -> bytes:
        import msgpack  # optional dependency
        return msgpack.packb(self.to_payload(), use_bin_type=True)
