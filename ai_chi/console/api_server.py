"""Optional FastAPI sidecar for A.i Core."""
from __future__ import annotations

from typing import Any

from ai_chi.core.loop import RealityLoop, message_confidence, message_record_id

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except Exception:  # pragma: no cover - optional runtime surface
    FastAPI = None  # type: ignore[assignment]
    HTTPException = Exception  # type: ignore[assignment]
    BaseModel = object  # type: ignore[assignment]


if FastAPI is not None:
    app = FastAPI(
        title="A.i Core Console Sidecar",
        description="Domain-agnostic interface for the Urbi audit loop over canonical MΣBUS.",
    )
    loop = RealityLoop()

    class ClaimInput(BaseModel):  # type: ignore[misc,valid-type]
        text_payload: str
        provenance: str = "urn:console:anythingllm:user"

    class OutcomeInput(BaseModel):  # type: ignore[misc,valid-type]
        prediction_id: str
        original_confidence: float
        actual_state: str
        matched: bool

    @app.post("/api/core/claim", tags=["Cognition"])
    async def submit_claim(req: ClaimInput) -> dict[str, Any]:
        try:
            _, audit = loop.submit_claim(req.text_payload, provenance=req.provenance)
            return {
                "status": "success",
                "envelope_class": audit.sigma,
                "verdict_data": audit.payload,
                "prediction_id": message_record_id(audit),
                "confidence": message_confidence(audit),
                "tau": audit.tau,
            }
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Core execution halt: {exc}") from exc

    @app.post("/api/core/outcome", tags=["Calibration"])
    async def submit_outcome(req: OutcomeInput) -> dict[str, Any]:
        _, cal = loop.record_outcome(
            prediction_id=req.prediction_id,
            confidence=req.original_confidence,
            actual_state=req.actual_state,
            matched=req.matched,
        )
        return {"status": "evaluated", "calibration_triggered": cal.sigma, "cal_data": cal.payload}

    @app.get("/api/core/ledger/{tail_length}", tags=["Memory"])
    async def get_raw_ledger(tail_length: int = 10) -> dict[str, list[dict]]:
        return {
            "evidence": loop.ledger.retrieve_tail("evidence.jsonl", lines=tail_length),
            "audit_verdicts": loop.ledger.retrieve_tail("audit_verdicts.jsonl", lines=tail_length),
            "predictions": loop.ledger.retrieve_tail("predictions.jsonl", lines=tail_length),
            "outcomes": loop.ledger.retrieve_tail("outcomes.jsonl", lines=tail_length),
            "calibration": loop.ledger.retrieve_tail("calibration.jsonl", lines=tail_length),
        }

    @app.get("/api/core/health", tags=["Status"])
    async def get_system_health() -> dict[str, Any]:
        obs = loop.observe_system()
        return {"system": "online", "metrics_latest": obs.payload}
else:
    app = None
