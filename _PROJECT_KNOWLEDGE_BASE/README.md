# A.i — Project Knowledge Base

_Curated interpretation layer for `C:\Users\Vi Chi\Desktop\Projectz\A.i`.
Non-destructive: it describes and links source files, it does not replace them.
Current as of 2026-06-14, with the Autopoiesis economics promotion,
drift synthesis, and Trinity liveness state linked below._

> **⭐ Start here for current state:** **[STATE_OF_SYSTEM_2026-06-14.md](STATE_OF_SYSTEM_2026-06-14.md)**
> — what's built & green (the live `ai_chi/` monorepo, **434 tests, self-contained**),
> what's canon, what's RADAR, and the next action. Supersedes the 06-12 snapshot.
> New term unsure? **[GLOSSARY.md](GLOSSARY.md)** defines every named concept.

> **Codex Phase 2 Reconstruction:** `_PROJECT_KNOWLEDGE_BASE/codex_reconstruction_2026-06-12/`
> contains the filled clean-room reconstruction, relation graph, concept lineage,
> old-to-new crosscheck, contradiction/drift map, and Claude KB cross-examination.
> Treat relation edges as inferred navigation hints, not authority.
> Read next for handoff: `reports/CODEX_CLEANROOM_RECON_AND_CLAUDE_BRIEF_2026-06-12.md`.
> 2026-06-14 drift synthesis: `reports/CODEX_GRAND_PLAN_RECONSTRUCTION_DRIFT_SYNTHESIS_2026-06-14.md`
> updates the story after DreamLens evaluation, transport/persistence, local ledger,
> NATS hardening, and Accelerated DAN work; use it before refreshing the state snapshot.
> 2026-06-14 scanner patch: `reports/CODEX_GRAND_PLAN_SCANNER_SUPERSESSION_2026-06-14.md`
> records the current-state preference and stale-report downranking.
> 2026-06-14 quota guard: `docs/TRINITY_QUOTA_GUARD.md` documents local
> quota/session status routing, downtime records, and metadata-only quota pokes.
> 2026-06-14 cycle liveness gate: `reports/CODEX_TRINITY_CYCLE_LIVENESS_GATE_2026-06-14.md`
> records the volume-only cycle-runner liveness wiring and R8 verification.
> 2026-06-14 SMTIS redaction digest hardening:
> `reports/CODEX_SMTIS_REDACTION_DIGEST_HARDENING_2026-06-14.md`
> records the Codex production ownership pass that moved raw metadata
> fingerprints onto redacted snapshots and documented the A3 boundary.
> 2026-06-14 Trinity bridge TTL/lockfile hardening:
> `reports/CODEX_TRINITY_BRIDGE_TTL_LOCKFILE_2026-06-14.md`
> records the router debug pass that rejects expired packets and prevents
> concurrent mutating bridge routes with `.bridge.lock`.
> 2026-06-14 graveyard redaction + Orbi executor guard:
> `reports/CODEX_GRAVEYARD_REDACTION_AND_ORBI_EXECUTOR_GUARD_2026-06-14.md`
> records the redacted SQLite rebuild and the target/args exclusion-zone hardening.
> 2026-06-14 Codex DAN GitHub readiness:
> `reports/CODEX_DAN_GITHUB_READINESS_2026-06-14.md`
> records the no-push GitHub readiness pass, current 434/434 test evidence,
> pre-publish gate result, and root publication gate.
> 2026-06-14 Google Workspace stewardship:
> `reports/CODEX_GOOGLE_WORKSPACE_STEWARDSHIP_2026-06-14.md`
> records the read-only Drive connector probe, service-write gates, and private
> staging plan for Google Drive / Docs / Sheets.

## Read order (orientation → canon → current)

**Canon (locked decisions):**
0. **[AXIOMS_OF_OMNI.md](AXIOMS_OF_OMNI.md)** — the constitutional floor: the 12 Axioms
   of Omni (read-only, architect-only), now executable in `ai_chi/core/axioms.py`. The
   *why* beneath the Triad. Five axioms map 1:1 to built invariants.
1. **[MEBUS_RESOLVED_DECISIONS_2026-06-06.md](MEBUS_RESOLVED_DECISIONS_2026-06-06.md)** —
   authoritative: MΣBUS = Membrane Sigma Bus, the 7-field protocol, Ω₈, language
   allocation. Where any doc disagrees, that doc is superseded.
2. **[URBI_ORBI_MEBUS_BALANCE_CONSTITUTION_2026-06-08.md](URBI_ORBI_MEBUS_BALANCE_CONSTITUTION_2026-06-08.md)** —
   the Triad Constitution (Urbi judges · Orbi acts · MΣBUS gates; no component holds two).
3. **[M_ENVELOPE_VS_PAYLOAD.md](M_ENVELOPE_VS_PAYLOAD.md)** — the two `M` layers
   (transport envelope vs cognition payload). Rule: extend via π, never widen M.
3a. **[../docs/ECONOMIC_CONSTITUTION.md](../docs/ECONOMIC_CONSTITUTION.md)** —
   ACTIVE Autopoiesis documentation floor, not runtime-enforced law: Urbi judges
   value, Orbi spends compute, MΣBUS meters authority, ICP anchors proof,
   ΣCredit accounts cognition.

**Orientation:**
4. **[AGENT_ORIENTATION.md](AGENT_ORIENTATION.md)** — agent landing page (folder
   routing, evidence labels, CM5 gates). _Note: predates the 2026-06-11 vendoring +
   `_Import` archival; use STATE_OF_SYSTEM for current layout._
5. **[ECOSYSTEM_MAP.md](ECOSYSTEM_MAP.md)** — the four pillars (Omni-AI · Cognitive
   Matrix · ΣBUS · Autopoiesis) on one page.
6. **[GLOSSARY.md](GLOSSARY.md)** — canonical vocabulary (triad, envelope, gates,
   AION, DPHA/heralds/Omni, realms, labels, RADAR modules).

**Reference:**
- **[SMTIS_MARITIME_APP.md](SMTIS_MARITIME_APP.md)** — the maritime app (Sea·Map·Tactical·
  Intelligence): read-only advisory overlay, the WAKE-side `PredictionRecord` producer that
  feeds Urbi audit + the Dream Replay Auditor; LIVE/SIM/REPLAY ↔ WAKE/POSSIBILITY/DREAM.
- **[RESEARCH_LIBRARY.md](RESEARCH_LIBRARY.md)** — the nine external deep-research
  dossiers (agent memory, maritime edge hardware, geospatial/ATAK, error-correcting
  codes, the Computational-ToE philosophy, OS agents, maritime OSes) distilled to
  design principles + axiom/module hooks. RADAR; dated 2026, source-observed not verified.
- **[../docs/AUTOPOIETIC_COMPUTE_ECONOMY.md](../docs/AUTOPOIETIC_COMPUTE_ECONOMY.md)** —
  local compute-economy design, ledger flow, routing ladder, ICP phases, and cache
  posture. ACTIVE documentation; no runtime authority.

**Current state & how it wires:**
7. **[STATE_OF_SYSTEM_2026-06-14.md](STATE_OF_SYSTEM_2026-06-14.md)** — current snapshot.
8. **[STATE_OF_SYSTEM_2026-06-12.md](STATE_OF_SYSTEM_2026-06-12.md)** — superseded snapshot.
8a. **[STATE_OF_SYSTEM_2026-06-11.md](STATE_OF_SYSTEM_2026-06-11.md)** — superseded snapshot.
9. **[analysis/REVERSE_ENGINEERING_A_I_2026-06-11.md](analysis/REVERSE_ENGINEERING_A_I_2026-06-11.md)** —
   the whole tree reconstructed: dependency graph, enforced invariants, upgrade paths.

## The knowledge base, by folder

- **`blueprints/`** — one build brief per module: `00_BLUEPRINT_INDEX.md`, Urbi, Orbi,
  MEBUS, Autopoiesis, DPHA (heralds/12-fold).
- **`analysis/`** — deep syntheses: corpus learnings, design-decision timeline, the
  MEBUS/ΣBUS deep-dive, the GitHub repo map, the 2026-06-11 sandbox-assimilation /
  prototype-RE / `.doc` sweep / new-intake docs, and the full-tree reverse-engineering.
- **`reports/`** — dated build & verification records: AION built, AION-SEARCH, Urbi
  primitives, CM-Realm+DPHA landed, Omni center, bypass suite, dan-verification, the
  forge audits, CM5 benchmarks, Trinity hardening, register/indexer work, and
  pre-publish gate precision. Newest first by date in filename.
- **`economics/`** — local Autopoiesis economics ledger scaffold: policy JSON,
  empty JSONL ledgers, and record-flow guidance.
- **`index/`** — `PROJECT_INDEX.md` (historical file-tree snapshot, 2026-06-07; for
  current layout see STATE_OF_SYSTEM) + `FILE_INVENTORY.csv`.
- root docs — the canon + handover/runbook docs above.

## Current status (2026-06-14)

| Area | State |
|------|-------|
| **Live core `ai_chi/`** | **434 tests green, self-contained** (vendored mebus+bridge+audit) — see STATE_OF_SYSTEM_2026-06-14 |
| Built & green | MΣBUS · Reality Loop+CAL · Urbi auditor/memory/primitives/audit-signal · AIDICT · Orbi v0+PolicyGate · **AION+search** · **CM-Realm** · **DPHA heralds** · **Omni** · **bypass suite** · **DREAM Replay Auditor** · **DreamLens prompt/config** · **MSDT Capability Gate** · **SMTIS bridge** |
| CANON naming | Triad · 7-field envelope+Ω₈ · DPHA 12-fold (Lumen…Nomos + Omni/Aegis/Nexus/Taijitu) |
| ACTIVE economics | Autopoiesis economic constitution, compute-economy docs, ΣCredit local accounting, BudgetEnvelope/ComputeReceipt/EconomicAuditSignal/CycleReceipt schemas; no runtime writes |
| RADAR (candidate) | SMTIS P1 real sensors · Aegis/Nexus/Taijitu · LOGOS_GRAPH · DataVision · Control Gap · JEPA/GSS/formula layer · transport/persistence stack |
| Sign-off only | 10 Core CM Laws as numbered law-set · AION evidence levels as constitutional gates · Orbi Executor live handlers (simulated stub only is built) |
| `_Import` | 2026-06-12 intake read; credential-like token redacted; DreamLens patch applied; smart recon scaffold generated |
| Codex reconstruction | `_PROJECT_KNOWLEDGE_BASE/codex_reconstruction_2026-06-12/` is filled through Phase 2: clean-room reconstruction, relation graph, concept lineage, old-to-new crosscheck, contradiction/drift map, and Claude KB cross-examination. Relation edges are inferred navigation hints, not authority |

## Handling rules

- Treat `_PROJECT_KNOWLEDGE_BASE` as the **curated interpretation**, the live
  `ai_chi/` tree as the **behavioural source of truth**, `_backup/` as cold provenance.
- Label new docs CANON / ACTIVE / WIP / RADAR / OBSOLETE. Sandbox exports enter as
  **RADAR** (evidence, not truth) and earn promotion only via the audit ladder.
- Don't merge Urbi and Orbi; extend the envelope via π, never new fields.
