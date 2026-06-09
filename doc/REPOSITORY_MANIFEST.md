# Repository Manifest

Snapshot date: 2026-05-19

## Purpose

This repository contains the Cognitive Matrix module as a source tree rather than as an opaque archive. It is structured for private GitHub version control, review, and future deployment work.

## Tracked Content

- `agent.py` - HTTP server, agent loop, and dream-cycle runner.
- `audit.py` - tri-state claim audit engine and context persistence helpers.
- `formula.py` - formal data model and formula declarations.
- `identity.py` - runtime identity and host-state reporting layer.
- `agents/connector.py` - LLM connector adapters for local and remote models.
- `axioms.json` - read-only epistemic floor for the module.
- `knowledge/omniversal.json` - bundled knowledge artifact.
- `doc/*.md`, `doc/*.txt` - design notes, source dispositions, and project context.
- `reports/*.md` - previous analysis reports retained as project provenance.
- `.env.example` - safe environment template.
- `context_store.example.json` - empty runtime store template.

## Intentionally Excluded

- `.env` and other secret-bearing files.
- `context_store.json`, `dream_layer.log`, `.omni_start_time`, and `agent.log`.
- `__pycache__`, compiled Python files, and local editor files.
- `*.bak`, `*.bak_*`, and other development backup snapshots.
- Large duplicate Office documents where Markdown equivalents are available.
- Packaged binary `.skill` exports.
- The original `cognitive_matrix.7z` archive.

## Local Validation

Run from the repository root:

```powershell
python -m py_compile agent.py audit.py formula.py identity.py agents\connector.py
python - <<'PY'
import json
for path in ["axioms.json", "knowledge/omniversal.json", "context_store.example.json"]:
    with open(path, encoding="utf-8") as handle:
        json.load(handle)
print("json ok")
PY
```
