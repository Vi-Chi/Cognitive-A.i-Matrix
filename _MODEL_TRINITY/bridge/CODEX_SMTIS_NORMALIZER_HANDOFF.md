# Codex Handoff: SMTIS P1 Ingest Normalization (2026-06-13)

**From:** Gemini/Antigravity (Builder-Scout)
**To:** Codex (Patch/Verify)
**Status:** Codex implemented and verified on 2026-06-13.

## Objective
Implement the `SmtisNormalizer` layer to convert raw sensor feeds (like Signal-K dicts) into safe, immutable `PredictionRecord` payloads, honoring the `safe_for_action=False` invariant.

## Files Scaffolded by Antigravity
1. **Normalizer Scaffold**: `ai_chi/core/observe/smtis_normalizer.py`
   - Contains the skeleton of the `SmtisNormalizer.normalize_sensor_reading` static method.
2. **Test Scaffold**: `ai_chi/tests/test_smtis_normalizer.py`
   - Contains tests enforcing that emitted records never allow action.

## Instructions for Codex
1. **Implement the Logic**:
   - In `smtis_normalizer.py`, parse the `raw_data` dict into the `PredictionRecord` fields. You can place the raw data inside the `predicted_outcome` or `actual_outcome` dictionaries.
   - Crucially, hardcode `safe_for_action=False` and `requires_human_confirmation=True` onto the `AuditFlags`.
2. **Implement Tests**:
   - In `test_smtis_normalizer.py`, implement tests to prove that malformed data is gracefully rejected or normalized, and that the audit flags are unconditionally secure.
3. **Verify Baseline Integrity**:
   - Run the full test suite (`python -m unittest discover -s ai_chi/tests -q`).
   - Ensure the baseline remains green.

## Invariants to Preserve
- Do not build or run any WebSocket or UDP listeners yet. This task is purely for the deterministic python normalization logic.
- Ensure the `verify_floor()` check continues to pass.

## Codex Completion

- Implemented `SmtisNormalizer.normalize_sensor_reading()` for simple dictionaries and Signal-K delta-shaped payloads.
- Preserved `audit.safe_for_action=False` and `audit.requires_human_confirmation=True` unconditionally.
- Added tests for Signal-K normalization, malformed input, stale input, source snapshot copying, sensitive key redaction, and bridge admission.
- Verification passed: `py_compile`, focused SMTIS tests, `verify_floor() == True`, full `ai_chi` suite (`347` tests OK), and Discord scaffold tests (`29` tests OK).
- Report: `_PROJECT_KNOWLEDGE_BASE/reports/CODEX_SMTIS_NORMALIZER_P1_2026-06-13.md`
