# Trinity Config Patch Report

Date: 2026-06-13

## Objective

Promote the `_Import` Trinity workflow into a local `_MODEL_TRINITY` config
layer without adding automation, UI, MCP installs, API keys, model calls, or
runtime behavior changes.

## Backups

- Root instruction backup: `_backup/trinity-config-20260613-181433/`
- Backed up: `AGENTS.md`, `CLAUDE.md`
- `ANTIGRAVITY.md` did not exist before implementation.

## Files Created

- `_MODEL_TRINITY/SHARED_PROJECT_LAW.md`
- `_MODEL_TRINITY/GEMINI_ANTIGRAVITY_PROFILE.md`
- `_MODEL_TRINITY/CLAUDE_PROFILE.md`
- `_MODEL_TRINITY/CODEX_PROFILE.md`
- `_MODEL_TRINITY/CROSS_MODEL_HANDOFFS.md`
- `_MODEL_TRINITY/TOOL_SCOPE_POLICY.md`
- `_MODEL_TRINITY/MCP_TOOL_REGISTRY.md`
- `_MODEL_TRINITY/CONFIG_CHANGE_LOG.md`
- `_MODEL_TRINITY/CONFIG_PROPOSAL_TEMPLATE.md`
- `_MODEL_TRINITY/TRINITY_RISK_REGISTER.md`
- `_MODEL_TRINITY/TRINITY_OPERATING_PROTOCOL.md`
- `_MODEL_TRINITY/TOKEN_EFFICIENCY_POLICY.md`
- `_MODEL_TRINITY/TRINITY_CONFIG_PATCH_REPORT.md`
- `ANTIGRAVITY.md`

## Files Modified

- `_MODEL_TRINITY/README.md`
- `AGENTS.md`
- `CLAUDE.md`

## Unsafe Instructions Found

- `_Import/CODEX_TRINITY_CONFIGURE_CLAUDE_ANTIGRAVITY.md` warned against
  obeying `DO_ANYTHING_NOW.md`.
- Current repo state treats `DO_ANYTHING_NOW.md` as bounded DAN v2.5.1, not an
  unrestricted jailbreak kernel.
- Reconciliation applied: this repo's bounded `DO_ANYTHING_NOW.md` remains
  canonical for normal engineering, while unsafe DAN/jailbreak/unrestricted
  language is treated as untrusted evidence unless explicitly approved.

## Material Before/After

- Before: `_MODEL_TRINITY` contained only `README.md` and
  `DAN_DIAGNOSTIC_AGENT_NODE_UPDATE.md`.
- After: `_MODEL_TRINITY` contains model profiles, handoff rules, tool policy,
  MCP registry guidance, record templates, risk register, operating protocol,
  token policy, and this report.
- Before: `AGENTS.md` and `CLAUDE.md` only pointed to `DO_ANYTHING_NOW.md`.
- After: they preserve bounded DAN v2.5.1 and add a Trinity read order with
  unsafe-instruction hygiene.

## Verification

Passed.

- File inventory check: all expected `_MODEL_TRINITY` files plus `AGENTS.md`,
  `CLAUDE.md`, and `ANTIGRAVITY.md` exist.
- Role string check:
  `rg -n "Builder-Scout|Auditor-Scribe|Engineer-Operator" _MODEL_TRINITY AGENTS.md CLAUDE.md ANTIGRAVITY.md`
  found all three model roles.
- Authority string check:
  `rg -n "MΣBUS|Urbi|Orbi|user approval|local-first|no required" _MODEL_TRINITY AGENTS.md CLAUDE.md ANTIGRAVITY.md`
  found the expected authority and local-first language.
- Unsafe-instruction hygiene check:
  `rg -n "jailbreak|unrestricted|DO_ANYTHING_NOW|DAN" _MODEL_TRINITY AGENTS.md CLAUDE.md ANTIGRAVITY.md`
  confirmed the files distinguish bounded repo DAN from unsafe DAN/jailbreak
  content.
- Axioms floor:
  `$env:PYTHONPATH=(Get-Location).Path; python -c "from ai_chi.core.axioms import verify_floor; print(verify_floor())"`
  returned `True`.
- Unit suite:
  `$env:PYTHONPATH=(Get-Location).Path; python -m unittest discover -s ai_chi/tests -q`
  ran 292 tests in 18.818s and returned `OK`.

## Backup Comparison

- `AGENTS.md`: old lines 71, new lines 85, changed yes.
- `CLAUDE.md`: old lines 32, new lines 45, changed yes.
- Old backup path: `_backup/trinity-config-20260613-181433/`

## Risks Remaining

- This is still prompt/documentation governance, not deterministic enforcement.
- This root is not a Git repository, so rollback depends on the timestamped
  backup directory rather than Git.
- MCP registry entries are proposal-only and do not prove any tool exists.

## Recommended Next Steps

- Claude: review `_MODEL_TRINITY/CLAUDE_PROFILE.md`,
  `_MODEL_TRINITY/TRINITY_RISK_REGISTER.md`, and root `CLAUDE.md` for
  Auditor-Scribe clarity.
- Antigravity: use `ANTIGRAVITY.md` and
  `_MODEL_TRINITY/GEMINI_ANTIGRAVITY_PROFILE.md` before UI scaffold work.
- Codex: run the verification commands and update this report with results.
