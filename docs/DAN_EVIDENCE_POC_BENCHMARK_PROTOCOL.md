# DAN Evidence / PoC / Benchmark Protocol

Status: Active companion to `DO_ANYTHING_NOW.md` v2.5.

## Purpose

Agents should not only change code and write summaries. When work becomes meaningful, visible, measurable, or public-worthy, agents should create proof: local PoCs, screenshots, logs, benchmarks, and reproducible notes.

The goal is credible stewardship, not forced bureaucracy.

## Trigger Conditions

Capture evidence when the work includes any of these:

- visible UI/dashboard/map/console/demo behavior,
- performance or accuracy claims,
- AI model/RAG/audit/memory/PredictionRecord behavior,
- hardware, embedded, NPU/GPU/CPU, or constrained-device results,
- public/community release material,
- surprising success or failure,
- changed assumptions,
- anything that future agents may need to verify.

## Evidence Loop

```text
prototype → run → measure → screenshot/log → classify → document → queue public use
```

## Required Minimum for Benchmark Claims

- command(s),
- environment,
- raw output,
- metric definition,
- sample/dataset/prompt set,
- number of runs,
- limitation notes,
- claim classification,
- redaction check.

## Screenshot Requirements

Screenshots must be checked for secrets, private documents, private URLs, internal IPs, location/vessel identifiers, billing/account data, wallets/exchanges, and unsafe hardware/security details.

Private screenshots may be stored as evidence, but public screenshots must be redacted or recreated with safe sample data.

## Output Location

Prefer:

```text
artifacts/evidence/YYYY-MM-DD_<task-slug>/
```

If a repo already has `reports/`, `docs/evidence/`, `benchmarks/results/`, or CI artifacts, use the local convention and explain it.

## Failure Evidence

Do not hide failed runs. Store them under `logs/` or `notes/failures.md`, and explain what was learned.
