# AIDICT — A.I. Development Investigation Contract Tracker

**Scientific evidence/claim ledger · local-first · GPLv3 · CM5/RPi5 + Hailo-10H aware**

AIDICT turns noisy AI-development signal (transcripts, subtitles, social text,
model cards, papers) into **auditable investigation contracts**. It is **not a new
system** — it is the existing A.i Core P0 Reality Loop pointed at a new sensor
stream. It reuses the MΣBUS membrane, the Urbi 3-6-9 auditor, the JSONL ledger,
the CAL/Ω₄ monitor, and the ΦΔ dream layer rather than forking a fact-checker.

## Design law (from `AIDICT.txt`)

- Social/transcript data is **signal, not truth**. Noise is *classified*, not discarded.
- `confidence` everywhere = **extraction** confidence ("did the source make this
  claim"), never truth confidence.
- The LLM is an **extractor only**, never an authority.
- Every claim becomes an **investigation contract**: what evidence would validate
  or contradict it, and what future condition can be tested.

## Record stack → M-protocol σ-class

| Record | σ-class | Ledger stream |
|---|---|---|
| `SourceRecord` | `ext.source` | `sources.jsonl` |
| `SegmentRecord` | `ext.segment` | `segments.jsonl` |
| `ClaimRecord` | `ext.claim` | `claims.jsonl` |
| `EvidenceRecord` | `m.evidence` (reused) | `evidence.jsonl` |
| `ContractRecord` (central) | `m.contract` | `contracts.jsonl` |
| `PatternRecord` | `m.pattern` | `patterns.jsonl` |
| `VerificationTask` | `m.verification_task` | `verification_tasks.jsonl` |
| `ValidationRecord` | `m.validation` | `validations.jsonl` |
| `PredictionRecord` | `m.prediction_record` (reused) | `predictions.jsonl` |

**Provenance reaches the span:** `SourceRecord` → `SegmentRecord` (timestamped) →
`ClaimRecord`/`EvidenceRecord`. Provenance is first-class, per AIDICT's first law.

**Contract status is evidence-driven (Balance Constitution §7.3).** Urbi's tri-state
verdict is attached to the contract as an `audit_signal`
(`audit_support_signal` / `audit_contradiction_signal` / `audit_suspended`); it never
mutates `current_status`. A contract stays `open` until a `ValidationRecord` (real
primary-source evidence) moves it to `partially_satisfied` / `satisfied` /
`contradicted`. Urbi audits, never acts.

**Acquisition boundary (law).** AIDICT imports user-supplied or permissioned text
artifacts only. It ships **no mass-platform downloader** in v0. The
`acquisition_method` is recorded, never hidden (manual / jdownloader / yt_dlp / api /
rss / copy_paste / unknown).

All new σ values are **cognition/ext** (never action), so Ω₈ never suppresses
them — auditing and evidence keep flowing in `WAKE`/`LIMINAL`/`DREAM`. The ledger
is the unmodified core `LedgerWriter`, subclassed (`AidictLedger`) to register the
new streams — `core/ledger/writer.py` is untouched.

## Pipeline

```
file (.srt/.vtt/.txt/.json)
  → SourceRecord + timestamped segments        (importers.py — no downloader)
  → sentence segmentation
  → TermNormalizer + 8 deterministic detectors  (normalize.py / detectors.py)
  → ClaimRecord (typed, evidence span, signal-gated; noise counted)
  → [optional] Urbi 3-6-9 audit per claim       (scout.reality_loop_audit_fn)
       [+] → partially_satisfied · [-] → contradicted · [=] → open (dream synapse)
  → ContractRecord + VerificationTasks          (contracts.py)
  → PatternEngine across the batch              (patterns.py)
  → ScoutReport → analysis.md + records.jsonl + verification_tasks.jsonl
       → optionally onto MΣBUS / AidictLedger
```

The deterministic pass is **fully offline** (stdlib only) — runs on any box with
no Hailo/Ollama. Audit is opt-in.

## Usage

```bash
# Offline deterministic extraction
python -m aicore.aidict analyze --input talk.srt --output outbox

# Also append every record to the AIDICT JSONL black-box
python -m aicore.aidict analyze --input talk.srt --output outbox --ledger

# Route every claim through the live Urbi 3-6-9 auditor (CM5)
python -m aicore.aidict analyze --input talk.srt --output outbox --audit

# Exercise the audit path with the offline suspending auditor (no model)
python -m aicore.aidict analyze --input talk.srt --output outbox --fake-auditor
```

Library:

```python
from aicore.aidict import AidictScout
from aicore.aidict.scout import reality_loop_audit_fn
from aicore.core.loop import RealityLoop

loop = RealityLoop(ledger_dir="data/ledger")          # live Urbi auditor
scout = AidictScout(audit_fn=reality_loop_audit_fn(loop))
report = scout.analyze_file("talk.srt")
print(report.render_markdown())
```

## Deterministic detectors (v0)

TermNormalizer · HypeLanguageDetector · PredictionPhraseDetector ·
LicenseConflictDetector · HardwareFeasibilityDetector · BenchmarkClaimDetector ·
OpenSourceClaimDetector · EntityCooccurrenceDetector.

Pattern engine v0 (embedding-free): `repeated_claim`, `hype_wave`,
`contradiction_cluster`, `entity_cooccurrence`, `technical_term_mutation`.

## Later layers (explicit, not built here)

Semantic similarity (SentenceTransformers, quantized on Hailo), Kleinberg burst
detection, graph layer, source-reputation learning, API collectors
(arXiv OAI-PMH / GitHub / HF). These are deliberately deferred per the doc's
disciplined MVP path.

## Tests

`aicore/tests/test_aidict.py` — 18 tests (parse, normalize, detect, contradiction,
contract lifecycle, pattern detection, schema/envelope validation, ledger routing,
fake-auditor Reality-Loop wiring). Run with the A.i root + MEBUS src + Urbi repo on
`PYTHONPATH`.
