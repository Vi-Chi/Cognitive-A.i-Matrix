"""Autopoiesis ledger interceptor for local MΣBUS accounting.

This module deliberately performs no provider calls, no chain writes, and no
payment activity. It only emits local ComputeReceipt payloads into a
FileBackedSigmaTransport stream.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from ai_chi.bus import MMessage, Mode, monotonic_tau
from ai_chi.bus.transports.protocols import LedgerBackend


COMPUTE_RECEIPT_SCHEMA = "digivichi.autopoiesis.compute-receipt.v0"
COMPUTE_RECEIPT_SIGMA = "m.autopoiesis.compute_receipt"
DEFAULT_STREAM_NAME = "autopoiesis_ledger"

_RISK_MULTIPLIERS = {
    "low": 1.0,
    "medium": 2.0,
    "high": 4.0,
    "critical": 8.0,
}

_ACTION_BASE_COSTS = {
    "fs.read": 1.0,
    "fs.write": 1.5,
    "shell": 3.0,
    "spawn_ghost": 2.5,
    "net": 5.0,
    "api": 5.0,
}


class AutopoiesisLedger:
    """Meters Orbi action decisions and emits offline ComputeReceipts."""

    def __init__(
        self,
        transport: LedgerBackend,
        *,
        stream_name: str = DEFAULT_STREAM_NAME,
    ) -> None:
        self.transport = transport
        self.stream_name = stream_name

    def meter_action(self, action_intent: Mapping[str, Any] | Any, allowed: bool) -> dict[str, Any]:
        """Calculate mock ΣCredit cost and persist a ComputeReceipt envelope."""
        intent = _coerce_intent(action_intent)
        cost = _mock_sigma_credit_cost(intent, allowed=allowed)
        receipt = _build_compute_receipt(intent, allowed=allowed, sigma_credit=cost)
        message = MMessage(
            sigma=COMPUTE_RECEIPT_SIGMA,
            payload=receipt,
            destination="autopoiesis.local",
            context={
                "trust_score": 1.0,
                "domain": "autopoiesis.local_simulation",
                "receipt_type": "ComputeReceipt",
            },
            mode=Mode.WAKE,
            tau=monotonic_tau(),
        ).validate()
        self.transport.append(self.stream_name, message)
        return receipt


def _coerce_intent(action_intent: Mapping[str, Any] | Any) -> dict[str, Any]:
    if hasattr(action_intent, "to_payload"):
        action_intent = action_intent.to_payload()
    elif not isinstance(action_intent, Mapping) and hasattr(action_intent, "__dict__"):
        action_intent = vars(action_intent)
    if not isinstance(action_intent, Mapping):
        raise TypeError("action_intent must be a mapping or expose to_payload()")

    intent = dict(action_intent)
    args = intent.get("args")
    intent["args"] = dict(args) if isinstance(args, Mapping) else {}
    return intent


def _mock_sigma_credit_cost(intent: Mapping[str, Any], *, allowed: bool) -> float:
    if not allowed:
        return 0.0

    action_type = str(intent.get("action_type", "")).lower()
    base = _ACTION_BASE_COSTS.get(action_type, 1.25)
    if action_type.startswith("fs."):
        base = _ACTION_BASE_COSTS.get(action_type, 1.25)
    elif action_type.startswith("net.") or action_type.startswith("api."):
        base = 5.0

    risk = str(intent.get("risk_level", "low")).lower()
    multiplier = _RISK_MULTIPLIERS.get(risk, _RISK_MULTIPLIERS["low"])
    args = intent.get("args", {})
    estimated_units = _nonnegative_number(args.get("mock_compute_units", 1.0), default=1.0)
    return round(base * multiplier * estimated_units, 6)


def _build_compute_receipt(
    intent: Mapping[str, Any],
    *,
    allowed: bool,
    sigma_credit: float,
) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    proposal_id = str(intent.get("proposal_id") or _stable_id("proposal", intent))
    args = intent.get("args", {})

    receipt_seed = {
        "proposal_id": proposal_id,
        "action_type": intent.get("action_type", ""),
        "target": intent.get("target", ""),
        "allowed": bool(allowed),
        "sigma_credit": sigma_credit,
        "created_at": created_at,
    }

    return {
        "schema": COMPUTE_RECEIPT_SCHEMA,
        "receipt_id": _stable_id("receipt", receipt_seed),
        "proposal_id": proposal_id,
        "created_at": created_at,
        "budget_envelope_hash": "local-simulation:" + _digest({
            "proposal_id": proposal_id,
            "action_type": intent.get("action_type", ""),
            "risk_level": intent.get("risk_level", "low"),
            "args": args,
        })[:16],
        "executor": _executor(intent),
        "route_used": "local_context" if allowed else "refused",
        "actual_cost": {
            "sigma_credit": sigma_credit,
            "prompt_tokens": _nonnegative_int(args.get("prompt_tokens", 0)),
            "completion_tokens": _nonnegative_int(args.get("completion_tokens", 0)),
            "icp_cycles": 0,
            "runtime_ms": _nonnegative_int(args.get("runtime_ms", 0)),
            "storage_bytes": _nonnegative_int(args.get("storage_bytes", 0)),
            "network_bytes": 0,
        },
        "cache_result": {
            "mode": "none",
            "hit": False,
            "cached_token_count": 0,
            "provider": "local",
            "ttl_observed_seconds": 0,
        },
        "output_hash": "",
        "error_signal": "none" if allowed else "gate_denied",
        "quality_signal": "unverified",
        "settlement_ref": "local-simulation-only",
        "promotion_target": "none",
        "provenance_refs": _provenance_refs(intent),
    }


def _executor(intent: Mapping[str, Any]) -> str:
    requested = str(intent.get("executor", "")).lower()
    allowed_executors = {
        "none",
        "human",
        "codex",
        "claude",
        "antigravity",
        "orbi",
        "local_script",
        "local_test",
        "provider_model",
        "icp_canister",
    }
    if requested in allowed_executors:
        return requested
    return "orbi"


def _provenance_refs(intent: Mapping[str, Any]) -> list[str]:
    provenance = intent.get("provenance")
    if isinstance(provenance, list) and provenance:
        return [str(item) for item in provenance if str(item)]
    actor_id = str(intent.get("actor_id", "")).strip()
    return [actor_id] if actor_id else ["local-policy-gate"]


def _nonnegative_number(value: Any, *, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number >= 0 else default


def _nonnegative_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, number)


def _stable_id(prefix: str, value: Any) -> str:
    return f"{prefix}_{_digest(value)[:16]}"


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
