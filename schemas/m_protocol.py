from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from enum import Enum
import msgpack
from datetime import datetime

class DomainTag(str, Enum):
    MARITIME_NAV = "maritime.nav"
    MARITIME_HAZARD = "maritime.hazard"
    MARITIME_TELEMETRY = "maritime.telemetry"
    SYSTEM_AUDIT = "system.audit"
    CURIOSITY = "curiosity"

class TriStateMode(str, Enum):
    WAKE = "WAKE"
    LIMINAL = "LIMINAL"
    DREAM = "DREAM"

class UncertaintyDist(BaseModel):
    type: str
    params: Dict[str, Any] = Field(default_factory=dict)

class CausalRef(BaseModel):
    node_id: str
    timestamp: float
    confidence: float

class MProtocolMessage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    v: List[float] = Field(..., description="Semantic geometry vector")
    sigma: UncertaintyDist = Field(..., description="Uncertainty distribution")
    pi: List[CausalRef] = Field(default_factory=list, description="Causal provenance")
    delta: DomainTag = Field(..., description="ΣBUS Route identifier")
    kappa: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence")
    tau: int = Field(..., description="Causal ticker sequence")
    mu: TriStateMode = Field(TriStateMode.WAKE, description="Current phase")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_msgpack(self) -> bytes:
        return msgpack.packb(self.model_dump(mode='python'), use_bin_type=True)
