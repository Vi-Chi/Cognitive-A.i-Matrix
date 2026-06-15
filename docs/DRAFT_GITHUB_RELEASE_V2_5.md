# Draft: Triad v2.5 Architecture Launch (GitHub Release)

**Target:** GitHub Release / Public Repository README
**Claims Level:** OBSERVED / VERIFIED (backed by 446/446 local tests)
**Redaction Status:** CLEAN (No secrets, no physical vessel identifiers, no raw API tokens)

## Title: DigiViCHI A.i Core: Triad v2.5 (The Autonomous Self-Auditing Baseline)

### Summary
We are releasing the baseline v2.5 of the A.i cognitive architecture. This marks the culmination of the "Triad" model: Urbi (Auditor), Orbi (Executor), and MΣBUS (Enforcer). No single component holds more than one power, strictly bounded by the 12 Axioms of Omni. This is an open-source local-first AI research stack exploring auditable agents, explicit action gates, and safety-bounded orchestration.

### Key Highlights
- **Self-Auditing Core:** 446/446 test baseline passed. The framework actively doubts itself, trapping false positives and hallucinations in fail-closed cycles.
- **Trinity Bridge (Agent Coordination):** Agents (Claude, Codex, Antigravity) coordinate locally via file-system ledgers (append-only JSONL), respecting TTL limits, single-instance lockfiles, and strict quota states.
- **Fail-Closed Redaction:** PII and secret-shaped metadata are redacted before reaching the core logic or observation logs.
- **Inert Scaffold:** All real-world executions (shell commands, network sockets, physical actuators) are actively stop-gated and require exact, explicit human approval.

### Changelog (Since v2.4)
- Added `SafeShellValidator` restricting command execution to a rigorous allowlist.
- Implemented robust `trinity_quota_guard.py` ensuring no automated runaway agent spending.
- Hardened SMTIS metadata ingest (single-pass signal state machine, fully offline).
- Rebuilt Graveyard index dropping all potential legacy credential exposure.

### Safety Note
This repository contains the software baseline *only*. It remains deliberately disconnected from any live sensor or physical hardware until manually approved and configured by the operator.
