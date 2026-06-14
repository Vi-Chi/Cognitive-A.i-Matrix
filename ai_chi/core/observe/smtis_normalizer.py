"""SMTIS normalization layer.

Converts raw NMEA/Signal-K dictionaries into SMTIS-shaped advisory dictionaries.
The output is cognition only: `audit.safe_for_action` is always False.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any


_ALLOWED_MODES = {"LIVE", "SIMULATION", "REPLAY"}
_SENSITIVE_KEY_TERMS = {
    "authorization",
    "credential",
    "password",
    "secret",
    "token",
    "webhook",
    "api_key",
    "apikey",
    "access_key",
    "access_token",
    "refresh_token",
    "auth",
    "bearer",
    "cookie",
    "session",
}
_SECRET_VALUE_PATTERNS = (
    re.compile(r"\b[Bb]earer\s+\S+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|webhook)\s*[:=]\s*\S+"),
)

_MARITIME_PII_KEYS = {
    "mmsi",
    "imo",
    "callsign",
    "name",
    "vesselname",
    "destination",
}

_MMSI_PATTERN = re.compile(r"\b([0-9]{9})\b")
_IMO_PATTERN = re.compile(r"(?i)\bIMO[\s]*([0-9]{7})\b")


class SmtisNormalizer:
    """Normalizes raw maritime sensor data into safe cognitive records."""

    @staticmethod
    def normalize_sensor_reading(domain: str, raw_data: Mapping[str, Any] | Any) -> dict[str, Any]:
        """
        Convert raw sensor input into an advisory SMTIS dictionary.

        The returned dictionary is suitable for `prediction_record_from_smtis`.
        It never trusts action or audit fields supplied by the raw feed.
        """
        domain_value = _clean_domain(domain)
        valid_raw = isinstance(raw_data, Mapping)
        raw_metadata = _raw_metadata(raw_data) if valid_raw else {"raw_type": type(raw_data).__name__}
        observations = _extract_observations(raw_data) if valid_raw else []
        timestamp = _extract_timestamp(raw_data) if valid_raw else None
        source = _extract_source(raw_data) if valid_raw else "invalid-input"
        path = _extract_primary_path(observations, raw_data if valid_raw else None)
        raw_mapping = raw_data if valid_raw else {}
        stale = _is_truthy(raw_mapping.get("stale")) if valid_raw else True
        mode = _clean_mode(raw_mapping.get("mode")) if valid_raw else "LIVE"
        confidence = _clean_confidence(raw_mapping.get("confidence"), default=0.85 if valid_raw else 0.0)

        source_input = {
            "source": source,
            "domain": domain_value,
            "path": path,
            "timestamp": timestamp,
            "observations": observations,
            "raw": raw_metadata,
            "valid": valid_raw,
        }

        summary = _summary(domain_value, path, source, stale=stale, valid=valid_raw)
        record_seed = {
            "domain": domain_value,
            "mode": mode,
            "path": path,
            "source": source,
            "timestamp": timestamp,
            "observations": observations,
        }

        return {
            "id": "smtis_" + _digest(record_seed)[:16],
            "mode": mode,
            "kind": "sensor_reading",
            "summary": summary,
            "confidence": confidence if valid_raw and not stale else 0.0,
            "risk_score": 0.0,
            "prediction_for": domain_value,
            "source_inputs": [source_input],
            "alternatives": [],
            "actual_outcome": {
                "state": "observed" if valid_raw and not stale else "degraded",
                "path": path,
                "observations": observations,
                "timestamp": timestamp,
            },
            "prediction_error": None,
            "audit": {
                "safe_for_display": bool(valid_raw and not stale),
                "safe_for_action": False,
                "requires_human_confirmation": True,
                "stale_inputs": bool(stale),
                "conflicting_sources": False,
                "invalid_input": not valid_raw,
                "normalizer": "SmtisNormalizer.v1",
            },
        }


def _clean_domain(domain: str) -> str:
    value = str(domain or "").strip()
    return value if value else "maritime.unknown"


def _clean_mode(value: Any) -> str:
    mode = str(value or "LIVE").upper()
    return mode if mode in _ALLOWED_MODES else "LIVE"


def _clean_confidence(value: Any, *, default: float) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = default
    return max(0.0, min(1.0, confidence))


def _extract_observations(raw_data: Mapping[str, Any]) -> list[dict[str, Any]]:
    if "updates" in raw_data and isinstance(raw_data["updates"], list):
        observations: list[dict[str, Any]] = []
        for update in raw_data["updates"]:
            if not isinstance(update, Mapping):
                continue
            values = update.get("values", [])
            if not isinstance(values, list):
                continue
            update_timestamp = update.get("timestamp")
            for item in values:
                if not isinstance(item, Mapping):
                    continue
                observations.append({
                    "path": str(item.get("path") or "unknown"),
                    "value": _json_safe(item.get("value"), key_context=str(item.get("path") or "")),
                    "timestamp": str(update_timestamp) if update_timestamp else None,
                })
        return observations

    if "path" in raw_data or "value" in raw_data:
        return [{
            "path": str(raw_data.get("path") or "unknown"),
            "value": _json_safe(raw_data.get("value"), key_context=str(raw_data.get("path") or "")),
            "timestamp": str(raw_data.get("timestamp")) if raw_data.get("timestamp") else None,
        }]

    ignored = {"audit", "mode", "confidence", "source", "$source", "timestamp", "stale"}
    observations = []
    for key, value in raw_data.items():
        if key in ignored or _is_sensitive_key(key):
            continue
        observations.append({"path": str(key), "value": _json_safe(value, key_context=str(key)), "timestamp": None})
    return observations


def _extract_timestamp(raw_data: Mapping[str, Any]) -> str | None:
    timestamp = raw_data.get("timestamp")
    if timestamp:
        return str(timestamp)
    updates = raw_data.get("updates")
    if isinstance(updates, list):
        for update in updates:
            if isinstance(update, Mapping) and update.get("timestamp"):
                return str(update["timestamp"])
    return None


def _extract_source(raw_data: Mapping[str, Any]) -> str:
    source = raw_data.get("source") or raw_data.get("$source")
    if isinstance(source, Mapping):
        label = source.get("label") or source.get("src") or source.get("type")
        return str(label or "signal-k")
    if source:
        return str(source)
    updates = raw_data.get("updates")
    if isinstance(updates, list):
        for update in updates:
            if isinstance(update, Mapping) and update.get("source"):
                nested = update["source"]
                if isinstance(nested, Mapping):
                    label = nested.get("label") or nested.get("src") or nested.get("type")
                    return str(label or "signal-k")
                return str(nested)
    return "unknown"


def _extract_primary_path(observations: list[dict[str, Any]], raw_data: Mapping[str, Any] | None) -> str:
    if observations:
        return str(observations[0].get("path") or "unknown")
    if raw_data is not None and raw_data.get("path"):
        return str(raw_data["path"])
    return "unknown"


def _summary(domain: str, path: str, source: str, *, stale: bool, valid: bool) -> str:
    if not valid:
        return f"SMTIS rejected malformed sensor input for {domain}"
    freshness = "stale" if stale else "observed"
    return f"SMTIS {freshness} sensor reading for {domain}: {path} from {source}"


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "stale"}


def _json_safe(value: Any, key_context: str = "") -> Any:
    if key_context and _is_maritime_pii_key(key_context):
        if "mmsi" in key_context.lower():
            return f"<vessel_id: {_digest(value)[:8]}>"
        return "<redacted-n1>"

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            clean_key = str(key)
            if _is_sensitive_key(clean_key):
                out[clean_key] = "<redacted>"
            else:
                out[clean_key] = _json_safe(item, key_context=clean_key)
        return out
    if isinstance(value, (list, tuple)):
        return [_json_safe(item, key_context=key_context) for item in value]
    if isinstance(value, str):
        if _looks_sensitive_value(value):
            return "<redacted>"
        redacted = _IMO_PATTERN.sub("<redacted-n1>", value)
        redacted = _MMSI_PATTERN.sub(lambda m: f"<vessel_id: {_digest(m.group(1))[:8]}>", redacted)
        return redacted
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return repr(value)


def _raw_metadata(raw_data: Mapping[str, Any]) -> dict[str, Any]:
    keys = [str(key) for key in raw_data.keys()]
    return {
        "type": "mapping",
        "sha256": _digest(_raw_digest_payload(raw_data)),
        "keys": ["<redacted>" if _is_sensitive_key(key) else key for key in keys],
        "values_embedded": False,
    }


def _raw_digest_payload(raw_data: Mapping[str, Any]) -> Any:
    """Build the value snapshot used for raw metadata fingerprints."""
    return _json_safe(raw_data)


def _is_sensitive_key(key: Any) -> bool:
    clean = str(key).strip().lower().replace("-", "_")
    compact = clean.replace("_", "")
    if clean in _SENSITIVE_KEY_TERMS or compact in _SENSITIVE_KEY_TERMS:
        return True

    words = set(re.findall(r"[a-z0-9]+", clean))
    return any(term in words for term in _SENSITIVE_KEY_TERMS)


def _is_maritime_pii_key(key: Any) -> bool:
    clean = str(key).strip().lower().replace("-", "_")
    compact = clean.replace("_", "")
    return clean in _MARITIME_PII_KEYS or compact in _MARITIME_PII_KEYS


def _looks_sensitive_value(value: str) -> bool:
    return any(pattern.search(value) for pattern in _SECRET_VALUE_PATTERNS)


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
