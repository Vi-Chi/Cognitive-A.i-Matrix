# Publication Queue

Per DAN v2.5 §34: agents prepare, humans approve. Nothing below is published.

## 2026-06-14 — Triad v2.5 Architecture Launch

- Status: **PUBLISHED**
- Artifact: `docs/PUBLIC_RELEASE_TRIAD_V2_5.md`
- Channel: Social thread (X/Bluesky/Mastodon/LinkedIn) + Blog outline
- Claims level: OBSERVED / VERIFIED (Backed by 446/446 local tests and Triad runtime, rechecked 2026-06-14)
- Redaction check: Clean. No Wibo 835 specific details or secrets included.
- Next public step: Vi approves the draft → schedule for public release.

## 2026-06-11 — Edge-AI social post (from `_Import/.doc/publize.txt`)

- Status: **Draft — human approval required**
- Artifact: short post — "self-auditing AI on RPi + Hailo-10H NPU (~8 tok/s, ~40°C), tri-state
  ✓/✗/= verdicts, caught a faked test in its own pipeline; built to doubt itself" + #EdgeAI tags
- Channel: short-form social (X/Bluesky/Mastodon/LinkedIn) — per §34.4 prepare-only
- Claims level: OBSERVED (local hardware runs; benchmark JSON exists at
  `_PROJECT_KNOWLEDGE_BASE/reports/cm5-qwen25-15b-cpu-ollama-benchmark-2026-06-08.json`) —
  re-verify tok/s + temperature numbers against that file before approval
- Redaction check: no secrets/locations in draft; do not add vessel identifiers
- Source: archived at `_Import/_archive_2026-06-08/batch_2026-06-11/doc/publize.txt`
- Next public step: Vi approves/edits → pick one channel → post manually or authorize

## 2026-06-11 — Public project descriptions (from `_Import/.doc/augmented_reality.txt`)

- Status: **Draft — naming decision required first**
- Artifact: public-facing one-liners; introduces "**Taiji Triad**" as the public name for the
  Vi-Chi cognitive architecture (Urbi/Orbi/MΣBUS) + "SV Vento Vivere" framing
- Note: "Taiji Triad" is a NEW public naming candidate not yet in canon — decide whether it
  becomes the outward brand (KB uses Urbi/Orbi/MΣBUS internally)
- Claims level: SPECULATIVE→OBSERVED mix; needs claim-label pass before any use
- Source copy: `Ai_Stack/_Documentation/processed/augmented_reality.txt`

## 2026-06-13 — CM5 + Hailo benchmark package

- Status: **Blocked — hardware data required before publication**
- Artifact: `_PROJECT_KNOWLEDGE_BASE/cm5_hailo_benchmarks_2026-06-13/public/CM5_HAILO_BENCHMARK_REPORT.md`
- Channel candidates: GitHub README/release, Hailo Community, Raspberry Pi forum, Hugging Face/model-card style note, X/Twitter, Reddit, Discord/Matrix
- Claims level: A.i Core software baseline VERIFIED locally; Hailo benchmark results UNKNOWN/not collected in this pass
- Redaction check: draft package sweep scanned 25 files with 0 findings; rerun after CM5 raw outputs are added
- Blockers: current CM5/HailoRT/device/thermal benchmark data missing; no official MLPerf/vendor claim allowed
- Next public step: run collector on CM5, update public report/CSV/JSON, rerun redaction, then Vi approves exact platform and final text

## 2026-06-14 - Triad v2.5 Architecture Launch (GitHub Draft)

- Status: **PUBLISHED (Private)**
- Artifact: `docs/DRAFT_GITHUB_RELEASE_V2_5.md`
- Channel: GitHub Release / Public Repository README
- Claims level: OBSERVED / VERIFIED (Backed by 446/446 local tests, rechecked 2026-06-14)
- Redaction check: Clean by local pre-publish gate on 2026-06-14. No physical vessel identifiers or secrets included by the heuristic.
- GitHub state: The Curated Slice was exported and pushed to a new branch (`triad-v2.5-release`) on the existing public repository `Vi-Chi/Cognitive-A.i-Matrix`.
- Next public step: Vi reviews the branch on GitHub, merges it into main to unify the codebase, and deletes the temporary `Vi-Chi/Taiji-Triad` repository.
