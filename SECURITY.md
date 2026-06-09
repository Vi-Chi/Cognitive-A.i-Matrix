# Security Policy

## Supported State

Project Autopoiesis is in Phase 0. It is a private research repository and
defaults to simulation mode.

## Hard Rules

- Do not commit secrets, tokens, credentials, private keys, wallet material, or
  private local service URLs.
- Do not commit private Cognitive Matrix memory, Omni-AI logs, unpublished RAG
  corpora, vessel telemetry, or personal documents.
- Do not enable real spending, chain writes, external compute, public services,
  or private-memory export without explicit owner approval for that task.
- Treat all provider and treasury data as simulated unless a document states
  otherwise and includes an approval record.

## Reporting

Report security issues privately to the repository owner. Include the affected
file, the data class involved, and a suggested containment step.

## Validation

Run this before committing:

```powershell
python scripts/validate_project.py
```
