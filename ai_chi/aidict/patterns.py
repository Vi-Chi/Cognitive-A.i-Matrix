"""Pattern engine v0 — deterministic, embedding-free, offline.

Layer-1 of the doc's layered pattern stack (deterministic before semantic).
Detects across a batch of ClaimRecords:
  * repeated_claim          — near-duplicate claims (token Jaccard >= threshold)
  * hype_wave               — many hype-flagged claims about the same entity
  * contradiction_cluster   — claims with opposing flags about a shared entity
  * entity_cooccurrence     — entities that recur together
  * technical_term_mutation — ASR/spelling mutations seen across the source

Semantic similarity (SentenceTransformers) and burst detection (Kleinberg) are
explicit later layers; this stays stdlib so it runs on the CM5 with no model.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from itertools import combinations

from ai_chi.aidict.detectors import Detection
from ai_chi.aidict.schemas import ClaimRecord, PatternRecord

_WORD = re.compile(r"[a-z0-9-]+")
_STOP = {"the", "a", "an", "is", "are", "to", "of", "and", "on", "in", "it",
         "this", "that", "for", "with", "will", "be", "as", "at", "by"}


def _tokens(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP and len(w) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def detect_patterns(
    claims: list[ClaimRecord],
    detections: dict[str, Detection],
    *,
    repeat_threshold: float = 0.6,
) -> list[PatternRecord]:
    """Return PatternRecords across a batch. ``detections`` keyed by claim_id."""
    patterns: list[PatternRecord] = []
    if not claims:
        return patterns

    token_sets = {c.claim_id: _tokens(c.normalized_claim) for c in claims}

    # --- repeated_claim (transitive grouping via union-find-lite) ---
    parent: dict[str, str] = {c.claim_id: c.claim_id for c in claims}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in combinations(claims, 2):
        if _jaccard(token_sets[a.claim_id], token_sets[b.claim_id]) >= repeat_threshold:
            parent[find(a.claim_id)] = find(b.claim_id)

    groups: dict[str, list[str]] = defaultdict(list)
    for c in claims:
        groups[find(c.claim_id)].append(c.claim_id)
    for members in groups.values():
        if len(members) >= 2:
            patterns.append(PatternRecord(
                pattern_type="repeated_claim",
                pattern_name=f"repeated×{len(members)}",
                description="Near-duplicate claims grouped by token overlap.",
                linked_claims=members,
                novelty_score=round(1.0 / len(members), 3),
                evidence_strength=round(min(1.0, 0.4 + 0.1 * len(members)), 3),
            ))

    # --- hype_wave (per entity) ---
    hype_by_entity: dict[str, list[str]] = defaultdict(list)
    for c in claims:
        det = detections.get(c.claim_id)
        if det and det.hype_markers:
            for ent in (c.entities or ["<no-entity>"]):
                hype_by_entity[ent].append(c.claim_id)
    for ent, ids in hype_by_entity.items():
        if len(ids) >= 2:
            patterns.append(PatternRecord(
                pattern_type="hype_wave",
                pattern_name=f"hype:{ent}",
                description=f"Multiple hype-flagged claims about {ent}.",
                linked_claims=ids,
                linked_entities=[ent],
                hype_score=round(min(1.0, 0.3 + 0.2 * len(ids)), 3),
                evidence_strength=0.3,
            ))

    # --- contradiction_cluster (opposing flags on a shared entity) ---
    flags_by_entity: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for c in claims:
        det = detections.get(c.claim_id)
        if not det:
            continue
        for ent in c.entities:
            for fl in det.flags:
                flags_by_entity[ent][fl].add(c.claim_id)
    _OPPOSED = [("open_source", "license_restrict"),
                ("local_inference", "heavy_hardware"),
                ("release", "unavailable")]
    for ent, byflag in flags_by_entity.items():
        for fa, fb in _OPPOSED:
            if byflag.get(fa) and byflag.get(fb):
                ids = sorted(byflag[fa] | byflag[fb])
                patterns.append(PatternRecord(
                    pattern_type="contradiction_cluster",
                    pattern_name=f"contradiction:{ent}:{fa}/{fb}",
                    description=f"Claims about {ent} assert both {fa} and {fb}.",
                    linked_claims=ids,
                    linked_entities=[ent],
                    evidence_strength=0.7,
                ))

    # --- entity_cooccurrence ---
    co_claims: dict[tuple[str, str], list[str]] = defaultdict(list)
    for c in claims:
        for pair in combinations(sorted(set(c.entities)), 2):
            co_claims[pair].append(c.claim_id)
    for (e1, e2), ids in co_claims.items():
        if len(ids) >= 2:
            patterns.append(PatternRecord(
                pattern_type="entity_cooccurrence",
                pattern_name=f"{e1}+{e2}",
                description=f"{e1} and {e2} co-occur across {len(ids)} claims.",
                linked_claims=ids,
                linked_entities=[e1, e2],
                evidence_strength=round(min(1.0, 0.3 + 0.1 * len(ids)), 3),
            ))

    # --- technical_term_mutation ---
    muts: Counter = Counter()
    mut_claims: dict[str, list[str]] = defaultdict(list)
    for c in claims:
        det = detections.get(c.claim_id)
        if det:
            for m in det.mutations:
                muts[m] += 1
                mut_claims[m].append(c.claim_id)
    for surface, n in muts.items():
        patterns.append(PatternRecord(
            pattern_type="technical_term_mutation",
            pattern_name=f"mutation:{surface}",
            description=f"Surface form '{surface}' normalised across {n} claim(s).",
            linked_claims=mut_claims[surface],
            evidence_strength=0.4,
        ))

    return patterns
