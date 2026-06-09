from pydantic import BaseModel, Field
from typing import Optional
from .m_protocol import MProtocolMessage, DomainTag

class PredictionRecord(BaseModel):
    record_id: str
    belief_state: MProtocolMessage 
    predicted_outcome: MProtocolMessage
    actual_outcome: Optional[MProtocolMessage] = None
    prediction_error: Optional[float] = None
    domain: DomainTag
    reversal_candidate: bool = False
    void_related: bool = False

    def is_high_confidence_wrong(self) -> bool:
        return self.belief_state.kappa > 0.85 and (self.prediction_error or 0) > 0.3
