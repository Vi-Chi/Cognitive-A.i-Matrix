# Trinity Bridge Source Authority Patch Report

Status: IMPLEMENTED. Created 2026-06-13.

## Trigger

Claude Auditor-Scribe returned `review_20260613T182024Z_8d8666ad` with a PASS architecture review and one MEDIUM finding:

`validate_packet` allowed a packet's self-declared `from` field to override the outbox directory it was found in. A packet placed in `outbox/codex` with `"from": "claude"` could be routed as Claude.

## Fix

Codex patched `scripts/trinity_bridge.py` so the outbox directory is authoritative:

- `source_hint` is normalized and validated against known agents.
- Missing `from` defaults to `source_hint`.
- Present `from` must match `source_hint`.
- A mismatch now raises `BridgeError` and the packet is rejected into the source outbox owner's rejected lane.
- Routed packets are normalized to `from := source_hint`.

## Regression Test

Added `test_outbox_source_is_authoritative` to `ai_chi/tests/test_trinity_bridge.py`.

The test writes a packet directly into `outbox/codex` while claiming `"from": "claude"`, then verifies:

- the packet is rejected,
- the rejection source is `codex`,
- no target inbox delivery is written,
- no Claude processed packet is created,
- the rejected packet lands under `rejected/codex`.

## Verification

Passed:

- `python -m py_compile scripts/trinity_bridge.py`
- `$env:PYTHONPATH=(Get-Location).Path; python -m unittest ai_chi.tests.test_trinity_bridge -q` ran 5 tests, OK.
- `$env:PYTHONPATH=(Get-Location).Path; python -c "from ai_chi.core.axioms import verify_floor; print(verify_floor())"` returned `True`.
- `$env:PYTHONPATH=(Get-Location).Path; python -m unittest ai_chi.tests.test_trinity_bridge ai_chi.tests.test_trinity_executor ai_chi.tests.test_trinity_arbitrator ai_chi.tests.test_trinity_dan_cycle -q` ran 21 tests, OK.
- `$env:PYTHONPATH=(Get-Location).Path; python -m unittest discover -s ai_chi/tests -q` ran 323 tests, OK.

## Backup

Pre-patch backups were written to:

`_backup/trinity-bridge-f1-source-auth-20260613-183000/`

## Boundary

No MCP servers, plugins, provider calls, hidden listeners, service writes, credentials, or app configs were changed.
