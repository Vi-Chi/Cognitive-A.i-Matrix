"""DREAM Lens — optional model-assisted proposer. Proposes; never disposes.

A Lens may surface extra contradiction *hints*; the deterministic engine decides. A Lens
can never grant action: it only emits `Contradiction` findings (audit signals), and every
field is sanitized against a closed vocabulary. The offline default (`NullDreamLens`)
proposes nothing, so the auditor runs fully local with no model.

`OllamaDreamLens` calls a local Ollama model (guarded, short timeout) and degrades to []
on any failure — offline, bad JSON, unknown fields. The transport is injectable so tests
need no running model.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import urllib.request
from typing import Callable, Optional, Protocol, runtime_checkable

from ai_chi.bus import PredictionRecord
from ai_chi.urbi.dream.records import Contradiction, ContradictionKind

_LOG = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"
_VALID_SEVERITY = frozenset({"low", "medium", "high"})
DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "urbi_lens_prompt.md"

LENS_SYSTEM = (
    "You are Urbi-369 Dream Lens. Output ONLY a JSON array of contradiction hints. "
    "Each item: {\"claim_id\": str, \"kind\": one of "
    "[prediction_error, belief_conflict, simulacrum, unresolved_uncertainty], "
    "\"severity\": one of [low, medium, high], \"detail\": str}. "
    "Preserve uncertainty. Do NOT grant permissions, call tools, write files, or alter state."
)


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _normalize_base_url(base_url: str) -> str:
    return (base_url or OLLAMA_BASE).rstrip("/")


def load_lens_prompt(path: str | os.PathLike[str] | None = None) -> str:
    """Load the optional DreamLens prompt; fall back to the safe built-in prompt."""
    candidates: list[Path] = []
    env_path = os.getenv("URBI_DREAM_LENS_PROMPT")
    if env_path:
        candidates.append(Path(env_path))
    if path:
        candidates.append(Path(path))
    candidates.append(DEFAULT_PROMPT_PATH)

    for candidate in candidates:
        try:
            text = candidate.read_text(encoding="utf-8").strip()
        except OSError as exc:
            _LOG.debug("DreamLens prompt load failed for %s: %s", candidate, exc)
            continue
        if text:
            return text
    return LENS_SYSTEM


@runtime_checkable
class DreamLens(Protocol):
    def propose(self, records: list[PredictionRecord]) -> list[Contradiction]:
        ...


class NullDreamLens:
    """Offline default: proposes nothing. The deterministic core stands alone."""

    def propose(self, records) -> list[Contradiction]:
        return []


def _ollama_transport(prompt: str, *, model: str, timeout: float, base_url: str) -> str:
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "format": "json"}).encode("utf-8")
    req = urllib.request.Request(f"{_normalize_base_url(base_url)}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8")).get("response", "")


def sanitize_dream_lens_hints(raw: str, *, valid_ids: set[str]) -> list[Contradiction]:
    """Parse candidate hint output into Contradictions under a closed vocabulary.

    Public, model-agnostic sanitizer shared by the OllamaDreamLens proposer and the
    offline evaluation harness. Pure: no network, no model, no action, no memory. It
    drops anything malformed, refuses claim_ids not in ``valid_ids`` (the lens cannot
    invent claims), maps unknown kinds to UNRESOLVED, and clamps severity to the closed
    set. Returns audit *findings* only — it never grants action.
    """
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if isinstance(data, dict):
        data = data.get("contradictions") or data.get("items") or [data]
    if not isinstance(data, list):
        return []
    out: list[Contradiction] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("claim_id", "")).strip()
        if cid not in valid_ids:          # the lens cannot invent claims
            continue
        try:
            kind = ContradictionKind(str(item.get("kind", "")).strip())
        except ValueError:
            kind = ContradictionKind.UNRESOLVED   # unknown -> safe default, never dropped silently
        sev = str(item.get("severity", "medium")).strip().lower()
        if sev not in _VALID_SEVERITY:
            sev = "medium"
        detail = str(item.get("detail", ""))[:300]
        out.append(Contradiction(claim_id=cid, kind=kind, severity=sev,
                                 detail=f"[lens] {detail}".strip()))
    return out


class OllamaDreamLens:
    """Local-model contradiction proposer. Proposes Contradictions; never grants action.

    transport(prompt) -> raw_text. Defaults to a guarded Ollama call; inject a fake in tests.
    Any failure (offline, timeout, malformed) yields [] — the deterministic kernel is unaffected.
    """

    def __init__(self, *, model: str | None = None, timeout: float | None = None,
                 transport: Optional[Callable[[str], str]] = None,
                 max_records: int | None = None,
                 base_url: str | None = None,
                 prompt_path: str | os.PathLike[str] | None = None,
                 system_prompt: str | None = None) -> None:
        self.model = model or os.getenv("URBI_DREAM_LENS_MODEL", "llama3.2")
        self.timeout = timeout if timeout is not None else _env_float("URBI_DREAM_LENS_TIMEOUT", 20.0)
        self.max_records = max_records if max_records is not None else _env_int("URBI_DREAM_LENS_MAX_RECORDS", 40)
        self.base_url = _normalize_base_url(base_url or os.getenv("URBI_DREAM_LENS_BASE", OLLAMA_BASE))
        self.system_prompt = system_prompt or load_lens_prompt(prompt_path)
        self._transport = transport or (
            lambda p: _ollama_transport(p, model=self.model, timeout=self.timeout,
                                        base_url=self.base_url)
        )

    def available(self) -> bool:
        try:
            urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=3)
            return True
        except Exception:
            return False

    def _prompt(self, records) -> str:
        rows = []
        for r in records[: self.max_records]:
            rows.append({
                "claim_id": str(r.record_id), "domain": r.domain,
                "confidence": r.confidence, "prediction_error": r.prediction_error,
                "predicted": r.predicted_outcome, "actual": r.actual_outcome,
            })
        return self.system_prompt + "\n\nRECORDS:\n" + json.dumps(rows, default=str)

    def propose(self, records) -> list[Contradiction]:
        records = list(records)
        if not records:
            return []
        try:
            raw = self._transport(self._prompt(records))
        except Exception as e:  # offline / timeout / transport error
            _LOG.debug("OllamaDreamLens transport failed (degrading to []): %s", e)
            return []
        return self._sanitize(raw, valid_ids={str(r.record_id) for r in records})

    def _sanitize(self, raw: str, *, valid_ids: set[str]) -> list[Contradiction]:
        """Back-compat shim; delegates to the public sanitize_dream_lens_hints()."""
        return sanitize_dream_lens_hints(raw, valid_ids=valid_ids)
