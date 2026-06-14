# Codex Handoff: DreamLens Evaluation Harness (2026-06-13)

**From:** Gemini/Antigravity (Builder-Scout)
**To:** Codex (Patch/Verify)
**Status:** Scaffolding complete; execution and verification required.

## Objective
The `STATE_OF_SYSTEM_2026-06-12.md` outlined the need for a DreamLens evaluation harness to test the `OllamaDreamLens` proposer offline using fixtures and an evidence log. 

I have scaffolded the necessary files. Your task is to apply these to the verified baseline, ensure tests pass, execute the harness if local models are available, and formally record the results.

## Files Created by Antigravity
1. **Fixtures**: `ai_chi/tests/fixtures/dream_lens_eval_records.json`
   - Contains 3 distinct `PredictionRecord` items (clean, conflict, simulacrum) designed to trigger the different Contradiction kinds.
2. **Evaluation Tool**: `ai_chi/tools/evaluate_dream_lens.py`
   - A python script that loads the fixtures, sends them to the local `OllamaDreamLens`, and dumps the parsed `Contradiction` hints into `_PROJECT_KNOWLEDGE_BASE/reports/DREAM_LENS_EVALUATION_<timestamp>.jsonl`.

## Instructions for Codex

1. **Verify Baseline Integrity**:
   - Run the full test suite (`python -m unittest discover -s ai_chi/tests -q`).
   - Ensure the baseline remains exactly **279 tests green**. The scaffolding should not have broken anything.
   - Run the dry-run of the evaluation harness (`python ai_chi/tools/evaluate_dream_lens.py --dry-run`).

2. **Execute Harness (If possible)**:
   - Try running `python ai_chi/tools/evaluate_dream_lens.py` without `--dry-run`. 
   - If Ollama is running and `llama3.2` is available, this will generate a real `JSONL` report in `_PROJECT_KNOWLEDGE_BASE/reports/`. 
   - If Ollama is NOT available or times out, the tool gracefully exits. This is expected "offline-degrading" behavior as per system design.

3. **Update State and Record**:
   - Create or update the relevant state document or report indicating that the Evaluation Harness is built and active.
   - You do NOT need to write a new feature; simply verify my scaffold, run it, and file the report.

## Invariants to Preserve
- Do not modify `OllamaDreamLens` to grant actions. It must remain a **proposer only**.
- Do not merge Orbi and Urbi functions.
- Ensure the `verify_floor()` check continues to pass.
