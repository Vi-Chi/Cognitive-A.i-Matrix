# AION — Archetypal Intelligence Ontology Network

Cognitive Matrix ontology layer. Organizes, classifies, compares and **gates**
recurring patterns from any domain (physics, neuroscience, myth, SIGINT, code,
telemetry) before they may influence Orbi action.

> **Core rule:** Pattern recognition must be audited before it becomes power.
> AION may discover patterns everywhere, but only Urbi-audited, MΣBUS-gated,
> evidence-ranked patterns may influence Orbi action.

Status: **P0, RADAR.** Stdlib-only, no external deps. Built 2026-06-11 from the
assimilated `AIONCM.md` sandbox thesis (evidence, not truth). Sits *under* the
Triad Constitution — needs no sign-off, only a build-priority decision.

## Layout

```
ai_chi/aion/
  ontology.py        EvidenceLevel 0-5, TransferLevel T0-T5, RiskClass, TrustState, Authority
  schema.py          AIONPattern / AIONInstance / AIONMapping / AIONContract (strict from_dict)
  decision.py        Verdict / Decision
  classifier.py      EvidenceClassifier  — Urbi's evidence-level classifier (symbolic cap, provenance)
  transfer_gate.py   AnalogyTransferGate — transfer level <= evidence ceiling; symbolic capped T1
  promotion_gate.py  PromotionGate       — block action <ev4; constitutional needs ev5 + Vi approval
  contradiction_scan.py  ContradictionScanner
  provenance.py      ProvenanceStore     — sqlite3, append-only audits + promotion attempts
  envelope.py        MΣBUS M:=(v,σ,π,δ,κ,τ) adapter
  cli.py / __main__.py
  search/            AION-SEARCH (open-web memory membrane)
    models.py        SerpSnapshot, RankingObservation, SourceLineageEdge, SearchClaim, PromotionState
    ranking_memory.py  SERP snapshot ledger ("ranking memory"); engine divergence preserved
    lineage.py       CLAIMS/CITES/COPIES/LAUNDERS_SOURCE edges; laundering detection (anti-slop)
    retrieval.py     three-index (lexical + vector-STUB + graph) + ranking-explanation contract
    promotion.py     OBSERVED->CITED->CORROBORATED->AUDITED->PROMOTED (no rung skipping; Urbi-only audit)
```

## Run

```bash
PYTHONPATH=. python -m ai_chi.aion classify --in pattern.json
PYTHONPATH=. python -m ai_chi.aion scan     --in pattern.json [--contract c.json]
PYTHONPATH=. python -m ai_chi.aion gate      --in pattern.json [--contract c.json] [--vi-approval] [--db aion.db]
PYTHONPATH=. python -m ai_chi.aion ingest    --in pattern.json --db aion.db
```

## Tests

```bash
PYTHONPATH=. python -m unittest discover -s ai_chi/tests -t . -p 'test_*.py'
```

28 tests, including the 10 acceptance tests from AIONCM section 17.

## Integration seams (when dropped into the live ai_chi/ tree)

- `envelope.py` mirrors the documented MΣBUS envelope. Replace with imports from
  `ai_chi.mebus` once co-located; the field shape (v,σ,π,δ,κ,τ) is unchanged.
- `provenance.ProvenanceStore` is standalone sqlite3; can later share the MEBUS
  ledger. Audits are Urbi-only and append-only by construction.
- AION-SEARCH's vector index is a deterministic **STUB** (hashed token-bag cosine)
  — swap for a real embedder (Qdrant per the memory-stack decision) behind
  `ThreeIndexRetriever`.

## Known non-goals (P0)

No world action, no auto-merge, no network calls. Deterministic and boring by
design (the forge doctrine). AION-SEARCH does not fetch the web; it ingests SERP
snapshots you provide.
