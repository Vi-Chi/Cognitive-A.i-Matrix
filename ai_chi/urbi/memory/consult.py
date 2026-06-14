"""Memory consultation — read-only lookups Orbi uses to decide better.

Two queries against Urbi memory that make Orbi's gate *smarter*:
  * ``negative_matches`` — does this mission/action resemble a known-bad path?
    (NEGATIVE tier). Used to **force-deny** a spawn — stricter only, never permissive.
  * ``procedural_skills`` — are there learned skills relevant to this mission?
    (PROCEDURAL tier). Surfaced to the ghost as context (informational; reusing a
    skill's *tools* still requires a normal grant — no capability without its gate).

Pure reads; no writes; no truth claims. Matching is deterministic + conservative.
"""
from __future__ import annotations

import re

from ai_chi.urbi.memory.store import MemoryStore
from ai_chi.urbi.memory.records import Tier

_WORD = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "to", "of", "and", "on", "in", "it", "for", "this",
         "that", "with", "is", "are", "be", "do", "my", "we"}


def _strings(content) -> list[str]:
    out: list[str] = []
    if isinstance(content, dict):
        for v in content.values():
            if isinstance(v, str):
                out.append(v)
            elif isinstance(v, (list, tuple)):
                out += [x for x in v if isinstance(x, str)]
    elif isinstance(content, str):
        out.append(content)
    return out


def _tokens(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP and len(w) > 3}


def negative_matches(store: MemoryStore, text: str) -> list[dict]:
    """NEGATIVE-tier records whose phrasing appears in ``text`` (known-bad path)."""
    t = text.lower()
    hits: list[dict] = []
    for rec in store.read(Tier.NEGATIVE):
        for v in _strings(rec.get("content", {})):
            # conservative: a substantive phrase from a known-bad record occurs in text
            if len(v) >= 6 and v.lower() in t:
                hits.append(rec)
                break
    return hits


def procedural_skills(store: MemoryStore, text: str, *, min_overlap: int = 1) -> list[dict]:
    """PROCEDURAL-tier skills whose name/keywords overlap the mission tokens."""
    qt = _tokens(text)
    if not qt:
        return []
    out: list[dict] = []
    for rec in store.read(Tier.PROCEDURAL):
        skill_tokens: set[str] = set()
        for v in _strings(rec.get("content", {})):
            skill_tokens |= _tokens(v)
        if len(qt & skill_tokens) >= min_overlap:
            out.append(rec)
    return out
