# ai_chi/_vendor — vendored runtime dependencies

Self-contained copies so `ai_chi` imports without an external `Ai_Stack/`:
- `mebus/`  — MΣBUS package (7-field envelope, MMessage, MembraneBus, PredictionRecord).
  Source of record: the MEBUS repo (was `_Import/MEBUS/mebus/src/mebus`).
- `bridge/` — Urbi↔MΣBUS bridge package (UrbiMebusBridge, gate_emit/Ω invariants).
  Source of record: the Urbi cognitive_matrix_repo (was `_Import/Urbi/.../bridge`).

`ai_chi/_paths.ensure_dependency_paths()` adds this folder to sys.path so
`import mebus` and `import bridge` resolve here. Update from source repos when
those advance; keep the public surface identical.

## audit.py (added 2026-06-12)
The Urbi v2.1 tri-state 3-6-9 `TriStateAuditor` (source: the Urbi cognitive_matrix_repo).
The bridge's `import audit` resolves here, so the original Urbi audit path is now
self-contained (no external Ai_Stack/repo). It degrades gracefully when Ollama is
offline (returns a fallback verdict). Two write paths are env-overridable so tests
and deployments don't write into the package:
`URBI_CONTEXT_STORE` (default `_vendor/context_store.json`) and
`URBI_DREAM_LOG` (default `_vendor/dream_layer.log`).
