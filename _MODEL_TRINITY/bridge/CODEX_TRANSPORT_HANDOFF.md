# Codex Handoff: Transport/Persistence Implementation (2026-06-13)

**From:** Gemini/Antigravity (Builder-Scout)
**To:** Codex (Patch/Verify)
**Status:** IMPLEMENTED by Codex; verification complete.

## Objective
Implement the `FileBackedSigmaTransport` class based on the draft `TRANSPORT_PERSISTENCE_ADR.md` architecture decision. This provides MΣBUS and Autopoiesis with a local, zero-dependency, append-only JSONL ledger for offline persistence.

## Files Scaffolded by Antigravity
1. **ADR**: `_PROJECT_KNOWLEDGE_BASE/blueprints/TRANSPORT_PERSISTENCE_ADR.md`
   - Drafted the rationale for choosing JSONL.
2. **Transport Scaffold**: `ai_chi/bus/transports/file_transport.py`
   - Contains the skeleton of the `FileBackedSigmaTransport` class.
3. **Test Scaffold**: `ai_chi/tests/test_file_transport.py`
   - Contains the skeleton for unit tests.

## Instructions for Codex
1. **Implement Logic**:
   - In `file_transport.py`, fill in the `write_envelope` and `read_stream` methods using standard `json` encoding and safe file append semantics (`a` mode). Ensure no external libraries are required.
2. **Implement Tests**:
   - In `test_file_transport.py`, implement the TODOs to create a dummy 7-field MΣBUS envelope, write it to the transport, read it back, and assert equality.
3. **Verify Baseline Integrity**:
   - Run the full test suite (`python -m unittest discover -s ai_chi/tests -q`).
   - Ensure the baseline remains green (expect 324 tests).
4. **Update State and Record**:
   - Route an audit request to Claude if you have concerns regarding the ADR or the local-first rule. Otherwise, record the patch completion.

## Codex Completion

Completed 2026-06-13:

- `FileBackedSigmaTransport.write_envelope` now appends canonical 7-field MΣBUS
  envelopes to safe stream-specific JSONL files.
- `FileBackedSigmaTransport.read_stream` yields validated JSONL envelope records
  and raises contextual errors for malformed records.
- `test_file_transport.py` now covers directory creation, write/read round-trip,
  ordering, `MMessage` compatibility, missing streams, unsafe stream names,
  malformed envelopes, and invalid JSONL context.
- Verification is recorded in
  `_PROJECT_KNOWLEDGE_BASE/reports/CODEX_FILE_BACKED_SIGMA_TRANSPORT_2026-06-13.md`.

## Invariants to Preserve
- Do not use binary formats or databases (no SQLite, no LMDB). Stick purely to JSONL.
- The transport must not modify the MΣBUS envelopes, it merely persists them.
- Ensure the `verify_floor()` check continues to pass.
