# Trinity Config Change Log

Every cross-model profile or config change must be recorded here.

## Entry Template

### YYYY-MM-DD HH:MM - Short Title

- Proposed by:
- Target model/profile:
- Files changed:
- Reason:
- Expected improvement:
- Risk:
- Rollback:
- Requires user/MΣBUS approval: yes/no
- Review status:
- Final status:

## 2026-06-13 18:14 - Promote Trinity Config Layer

- Proposed by: user via Codex plan
- Target model/profile: shared, Codex, Claude, Antigravity
- Files changed: root agent files and `_MODEL_TRINITY/` config docs
- Reason: promote `_Import` Trinity workflow into a versioned local config layer
- Expected improvement: clearer cross-model roles, handoffs, risks, and tool boundaries
- Risk: instruction drift if future agents treat workbench profiles as canonical law
- Rollback: restore root files from `_backup/trinity-config-20260613-181433/` and remove newly added `_MODEL_TRINITY` files
- Requires user/MΣBUS approval: user approval supplied for config-layer implementation
- Review status: Codex implemented and ran documented checks
- Final status: implemented

## 2026-06-13 16:50Z - Add Local Trinity Bridge

- Proposed by: user
- Target model/profile: shared, Codex, Claude, Antigravity
- Files changed: `scripts/trinity_bridge.py`, `_MODEL_TRINITY/bridge/`, bridge docs, script/config READMEs, bridge tests
- Reason: provide an automatic local three-way bridge for Codex, Claude, and Antigravity
- Expected improvement: agents can exchange serialized handoff packets through a shared inbox/outbox without live service coupling
- Risk: future users may mistake routed packets for approved actions
- Rollback: remove `scripts/trinity_bridge.py`, `ai_chi/tests/test_trinity_bridge.py`, and `_MODEL_TRINITY/bridge/`; revert README additions
- Requires user/MΣBUS approval: user approved local bridge build; MΣBUS/Urbi/user gates still required for action promotion
- Review status: Codex implemented and verified
- Final status: implemented

## 2026-06-13 18:57 - Add Safe Trinity Executor

- Proposed by: user
- Target model/profile: shared, Codex, Claude, Antigravity
- Files changed: `scripts/trinity_executor.py`, executor tests, bridge docs/config, Trinity policy docs
- Reason: support safe automatic execution of compact agent verification requests to share workload and reduce token usage
- Expected improvement: agents can request known local checks by task ID and receive compact `ExecutionRecord` packets instead of re-sending long instructions or logs
- Risk: executor scope creep into general shell or Orbi Executor behavior
- Rollback: restore docs/config from `_backup/trinity-executor-20260613-185727/` and remove `scripts/trinity_executor.py`, `ai_chi/tests/test_trinity_executor.py`, and the executor bridge docs/sample
- Requires user/MΣBUS approval: user requested safe automatic execution; canonical Orbi action authority remains stop-gated
- Review status: Codex implemented; focused Trinity tests, live sample execution, Axioms floor, and full `ai_chi` suite passed
- Final status: implemented

## 2026-06-13 19:30 - Add Foreground Trinity+DAN Cycle Runner

- Proposed by: user
- Target model/profile: shared, Codex, Claude, Antigravity
- Files changed: `scripts/trinity_dan_cycle.py`, cycle tests, bridge policy/report docs, Trinity policy docs/config
- Reason: automate the Trinity and DAN protocol loop inside each app's own workspace/sandbox boundary without granting unrestricted system control
- Expected improvement: one local command can route handoffs, process safe execution requests, run optional DAN checks, write cycle state, and emit compact summaries
- Risk: future users may mistake the foreground runner for an approved hidden service or global app automation
- Rollback: restore docs/config from `_backup/trinity-dan-cycle-20260613-193048/` and remove `scripts/trinity_dan_cycle.py`, `ai_chi/tests/test_trinity_dan_cycle.py`, and cycle bridge docs
- Requires user/MΣBUS approval: user requested enhancement; scheduling/hooks/MCP/app config changes remain approval-gated
- Review status: Codex implemented; verification recorded in final completion report
- Final status: implemented

## 2026-06-13 19:43 - Add Trinity Arbitration Layer

- Proposed by: user via "build all files and documentation"
- Target model/profile: shared, Codex, Claude, Antigravity
- Files changed: `scripts/trinity_arbitrator.py`, arbitrator tests, bridge capability manifest, arbitration docs/schema/sample, cycle integration, safe task catalog, and Trinity policy docs
- Reason: turn the synthesis/conjecture into a governed local work queue with schema checks, claim locks, stale/superseded handling, compact handoffs, and capability manifests
- Expected improvement: agents can share work with less repeated context while unsafe, approval-gated, stale, blocked, or invalid packets are quarantined before routing
- Risk: future agents may treat `safe` arbitration as execution approval
- Rollback: restore docs/config from `_backup/trinity-arbitrator-20260613-194312/` and remove the arbitrator script, tests, policy/report, manifest, config section, and cycle integration
- Requires user/MΣBUS approval: user requested local build; action promotion still requires MΣBUS/Urbi/Orbi/user gates
- Review status: Codex implemented; py_compile, focused Trinity tests, Axioms floor, full `ai_chi` suite, and live quick cycle passed
- Final status: implemented

## 2026-06-13 20:00 - Promote Autopoiesis Economics Layer

- Proposed by: user via Trinity Autopoiesis economics synthesis/conjecture import
- Target model/profile: shared, Codex, Claude, Antigravity
- Files changed: `docs/ECONOMIC_CONSTITUTION.md`, `docs/AUTOPOIETIC_COMPUTE_ECONOMY.md`, `schemas/`, `_PROJECT_KNOWLEDGE_BASE/economics/`, `_MODEL_TRINITY/AUTOPOIESIS_ECONOMICS_POLICY.md`, KB indexes/glossary/blueprint, and `ai_chi/tests/test_economic_schemas.py`
- Reason: promote the imported compute-economy conjecture into local docs, schemas, policy JSON, empty ledgers, and validation tests
- Expected improvement: Trinity agents can discuss BudgetEnvelope, ComputeReceipt, EconomicAuditSignal, CycleReceipt, ΣCredit, ICP posture, and cache economics without granting runtime authority
- Risk: future agents may mistake economic docs for permission to spend, call providers, cache secrets, launch SNS, or write to ICP
- Rollback: restore edited index/profile files from `_backup/trinity-autopoiesis-economics-20260613-200043/` and remove the added docs, schemas, economics directory, report, and test file
- Requires user/MΣBUS approval: user requested local documentation build; spending, provider calls, ICP writes, SNS/token work, and service writes remain stop-gated
- Review status: Codex implemented; focused economics tests, Axioms floor, content sweeps, file-list check, and full `ai_chi` suite passed
- Final status: implemented

## 2026-06-13 18:30 - Reject Trinity Bridge Source Spoofing

- Proposed by: Claude Auditor-Scribe review packet `review_20260613T182024Z_8d8666ad`
- Target model/profile: shared bridge, Codex implementation
- Files changed: `scripts/trinity_bridge.py`, `ai_chi/tests/test_trinity_bridge.py`, `_MODEL_TRINITY/bridge/SOURCE_AUTHORITY_PATCH_REPORT.md`
- Reason: prevent a packet's self-declared `from` field from overriding the outbox directory authority
- Expected improvement: closes bridge impersonation / authority-laundering vector where `outbox/codex` could route as `claude`
- Risk: old malformed packets with mismatched `from` fields now reject instead of routing with a warning
- Rollback: restore files from `_backup/trinity-bridge-f1-source-auth-20260613-183000/`
- Requires user/MΣBUS approval: no extra approval needed for local safety patch; action promotion remains gated
- Review status: Codex implemented; py_compile, focused bridge tests, Trinity tests, Axioms floor, and full `ai_chi` suite passed
- Final status: implemented

## 2026-06-13 18:55 - Apply Claude Economics Wording And Next-Session Grant

- Proposed by: user plus Claude economics audit packet `review_20260613T184647Z_f740e305`
- Target model/profile: Claude, Trinity economics docs
- Files changed: `docs/ECONOMIC_CONSTITUTION.md`, `_MODEL_TRINITY/AUTOPOIESIS_ECONOMICS_POLICY.md`, `_PROJECT_KNOWLEDGE_BASE/README.md`, `CLAUDE.md`, `_MODEL_TRINITY/CLAUDE_PROFILE.md`, `_MODEL_TRINITY/CLAUDE_NEXT_SESSION_AUTHORITY_2026-06-13.md`, `_MODEL_TRINITY/CLAUDE_NEXT_SESSION_AUTHORITY_REPORT_2026-06-13.md`
- Reason: harden wording around no-runtime-authority, ΣCredit non-convertibility, ICP governance approval gates, and Claude's next-session bounded authority
- Expected improvement: reduces risk that economics docs or "full authority" language are misread as runtime, install, spending, credential, ICP, deployment, or public-token approval
- Risk: dated next-session grant could be read after expiry if future agents ignore the expiry section
- Rollback: restore files from `_backup/20260613-continue-economics-claude-authority/` and remove the dated next-session grant/report
- Requires user/MΣBUS approval: user requested the grant; stop-gated actions still require exact target approval
- Review status: Codex implemented; verification recorded in report/final response
- Final status: implemented

## 2026-06-13 19:30 - Implement File-Backed Sigma Transport

- Proposed by: Gemini/Antigravity Builder-Scout handoff
- Target model/profile: shared transport/persistence, Codex implementation
- Files changed: `ai_chi/bus/transports/file_transport.py`, `ai_chi/tests/test_file_transport.py`, `_PROJECT_KNOWLEDGE_BASE/blueprints/TRANSPORT_PERSISTENCE_ADR.md`, `_MODEL_TRINITY/bridge/CODEX_TRANSPORT_HANDOFF.md`, `_PROJECT_KNOWLEDGE_BASE/reports/CODEX_FILE_BACKED_SIGMA_TRANSPORT_2026-06-13.md`
- Reason: implement the local JSONL transport/persistence primitive selected by the transport ADR scaffold
- Expected improvement: MΣBUS and Autopoiesis gain a zero-dependency, append-only local record transport for future ledgers without external services
- Risk: future agents may overextend the JSONL primitive into high-concurrency runtime routing before a broker/database ADR
- Rollback: restore files from `_backup/transport-file-jsonl-20260613-193000/`
- Requires user/MΣBUS approval: user requested Codex continuation; runtime wiring remains a separate promotion gate
- Review status: Codex implemented; focused transport tests and axiom floor passed, full-suite result recorded in final/report
- Final status: implemented

## 2026-06-13 19:40 - Implement Autopoiesis Ledger Local Simulation

- Proposed by: Gemini/Antigravity Builder-Scout bridge handoff `handoff_20260613T193820Z_d50c6a6b`
- Target model/profile: Codex implementation, shared Autopoiesis/Orbi/MΣBUS layer
- Files changed: `ai_chi/core/ledger/autopoiesis_ledger.py`, `ai_chi/core/ledger/__init__.py`, `ai_chi/orbi/policy_gate.py`, `ai_chi/tests/test_autopoiesis_ledger.py`, `_MODEL_TRINITY/bridge/CODEX_AUTOPOIESIS_HANDOFF.md`, `_PROJECT_KNOWLEDGE_BASE/reports/CODEX_AUTOPOIESIS_LEDGER_LOCAL_SIM_2026-06-13.md`
- Reason: complete the Antigravity scaffold by metering PolicyGate action decisions into local ComputeReceipt JSONL envelopes
- Expected improvement: Orbi decisions can now produce mock local ΣCredit accounting receipts through FileBackedSigmaTransport without provider calls, spending, or ICP writes
- Risk: future agents may mistake local ΣCredit receipts for spendable credit, settlement, or permission to call external compute
- Rollback: restore files from `_backup/autopoiesis-ledger-local-sim-20260613-194000/` and remove `_PROJECT_KNOWLEDGE_BASE/reports/CODEX_AUTOPOIESIS_LEDGER_LOCAL_SIM_2026-06-13.md`
- Requires user/MΣBUS approval: local-only implementation was requested; provider calls, real spending, service writes, app config mutation, MCP installs, public deployment, and ICP/on-chain writes remain stop-gated
- Review status: Codex implemented; `py_compile`, focused Autopoiesis/Orbi/transport/economics tests, `verify_floor()`, and full `ai_chi` suite passed
- Final status: implemented

## 2026-06-13 20:00 - Create Phase 7.1 Redacted Secret Reference Ops Layer

- Proposed by: user via Phase 7.1 import and "carry on Codex"
- Target model/profile: Codex active operator, Claude reauthorization, Gemini Antigravity adoption
- Files changed: `_PROJECT_KNOWLEDGE_BASE/trinity_live_ops_2026-06-13/`, `scripts/check_trinity_secret_refs.py`, `ai_chi/tests/test_trinity_secret_refs.py`, `_PROJECT_KNOWLEDGE_BASE/reports/CODEX_PHASE_7_1_SECRET_ADOPTION_AND_REAUTHORIZATION_REPORT_2026-06-13.md`
- Reason: prepare safe local secret-reference adoption and model reauthorization artifacts without copying raw secrets into project files
- Expected improvement: Claude, Gemini Antigravity, and Codex can coordinate around environment/key references, stop-gate records, and redacted verification without prompt-stored secrets
- Risk: future agents may mistake reference presence or fingerprints for approval to run provider calls, rotate credentials, mutate app configs, or perform service writes
- Rollback: restore `_MODEL_TRINITY/CONFIG_CHANGE_LOG.md` from `_backup/phase7-1-secret-ops-20260613-200000/` and remove the new ops folder, checker script, checker test, and Phase 7.1 report
- Requires user/MΣBUS approval: local redacted artifacts and presence-only checks were performed; fingerprint mode, raw secret reads, provider smoke tests, service writes, app config mutation, MCP installs, credential rotation, and public posting remain stop-gated
- Review status: Codex implemented; checker tests, presence-only checker, targeted Markdown secret-pattern scan, Discord tests, and full `ai_chi` suite passed
- Final status: implemented

## 2026-06-13 20:05 - Implement SMTIS P1 Normalizer

- Proposed by: Gemini/Antigravity Builder-Scout bridge handoff `handoff_20260613T195116Z_d4fc9dc8`
- Target model/profile: Codex implementation, SMTIS observe layer
- Files changed: `ai_chi/core/observe/smtis_normalizer.py`, `ai_chi/tests/test_smtis_normalizer.py`, `_MODEL_TRINITY/bridge/CODEX_SMTIS_NORMALIZER_HANDOFF.md`, `_PROJECT_KNOWLEDGE_BASE/reports/CODEX_SMTIS_NORMALIZER_P1_2026-06-13.md`
- Reason: convert raw/simple and Signal-K-shaped sensor dictionaries into SMTIS advisory records that preserve `safe_for_action=False`
- Expected improvement: P1 ingest can normalize local sensor payloads into bridge-admissible cognition without adding sockets, listeners, or action authority
- Risk: future agents may mistake deterministic normalization for approval to enable real WebSocket/UDP ingest
- Rollback: restore files from `_backup/smtis-normalizer-20260613-200500/` and remove `_PROJECT_KNOWLEDGE_BASE/reports/CODEX_SMTIS_NORMALIZER_P1_2026-06-13.md`
- Requires user/MΣBUS approval: local normalization was requested; real listeners, service starts, API calls, app config mutation, public exposure, and vessel/actuator control remain stop-gated
- Review status: Codex implemented; `py_compile`, focused SMTIS tests, `verify_floor()`, full `ai_chi` suite, and Discord scaffold tests passed
- Final status: implemented

## 2026-06-14 01:20Z - Update Claude Wake Context After Codex Hardening

- Proposed by: user via "DAN Enhance & update claude"
- Target model/profile: Claude Auditor-Scribe
- Files changed: `CLAUDE.md`, `_MODEL_TRINITY/CLAUDE_PROFILE.md`, `_MODEL_TRINITY/CLAUDE_NEXT_SESSION_HANDOFF_2026-06-14.md`, `_MODEL_TRINITY/CONFIG_CHANGE_LOG.md`
- Reason: give Claude a compact current-state brief after Phase 7.1 review, SMTIS redaction hardening, transport protocolization, and NATS/Omega-8 hardening
- Expected improvement: Claude can wake into the next audit cycle without re-reading full bridge history, while preserving stop gates and avoiding stale one-cycle authority wording
- Risk: future agents may mistake the dated handoff for live authority if they skip its boundary section
- Rollback: restore files from `_backup/20260614-claude-update/` and remove `_MODEL_TRINITY/CLAUDE_NEXT_SESSION_HANDOFF_2026-06-14.md`
- Requires user/MΣBUS approval: user requested the Claude update; no new live authority granted
- Review status: Codex implemented with local content checks and bridge handoff
- Final status: implemented

## 2026-06-14 01:50Z - Add Windows Signal Watch Protocol

- Proposed by: user via Windows notification/DAN handoff automation request
- Target model/profile: shared, Claude, Codex
- Files changed: `_MODEL_TRINITY/WINDOWS_SIGNAL_WATCH_PROTOCOL.md`, `_MODEL_TRINITY/README.md`, `_MODEL_TRINITY/CLAUDE_NEXT_SESSION_HANDOFF_2026-06-14.md`, `_MODEL_TRINITY/CONFIG_CHANGE_LOG.md`
- Reason: let Claude and Codex use low-risk Windows notification/event metadata and scoped Claude log hints to accelerate DAN handoffs and session-limit recovery
- Expected improvement: faster bridge-first handoff processing through the Codex heartbeat `trinity-claude-signal-watch`, now every 5 minutes, while keeping privacy and stop gates explicit
- Risk: future agents may overread "watch notifications" as permission to scrape raw notification bodies or mutate app/service config
- Rollback: restore files from `_backup/20260614-windows-signal-watch-protocol/`, remove `_MODEL_TRINITY/WINDOWS_SIGNAL_WATCH_PROTOCOL.md`, and pause/delete the Codex app heartbeat `trinity-claude-signal-watch`
- Requires user/MΣBUS approval: user requested workflow automation; raw notification bodies, credential reads, app config mutation, MCP/plugin installs, services, sockets, provider calls, service writes, deployment, and spending remain stop-gated
- Review status: Codex implemented; probe, content, bridge, and secret-reference checks passed
- Final status: implemented

## 2026-06-14 02:00Z - Clarify Explicit DAN Continuation vs Passive Heartbeat

- Proposed by: user via "why does Codex say bounded DAN ... it knows it should carry on with the grand plan when the others are offline"
- Target model/profile: Codex Engineer-Operator, shared Trinity workflow
- Files changed: `_MODEL_TRINITY/WINDOWS_SIGNAL_WATCH_PROTOCOL.md`, `_MODEL_TRINITY/bridge/CYCLE_POLICY.md`, `_MODEL_TRINITY/TRINITY_OPERATING_PROTOCOL.md`, `_MODEL_TRINITY/CONFIG_CHANGE_LOG.md`
- Reason: fix the behavior gap where passive heartbeat "do not invent work" wording could be over-applied to an explicit user `DAN` continuation request
- Expected improvement: passive heartbeats stay quiet when no packet exists, while direct user DAN requests bridge-check first and then continue the project through evidence-backed Continuous Stewardship when Claude or Antigravity are offline
- Risk: future agents may overinterpret continuation as permission for hidden background mutation; docs now restate that the rule applies only to active explicit user requests and keeps stop gates active
- Rollback: restore files from `_backup/20260614-explicit-dan-continuation/`
- Requires user/MΣBUS approval: no new external authority; local docs/protocol clarification only
- Review status: Codex implemented; content checks, Axioms floor, and secret-reference scan passed
- Final status: implemented

## 2026-06-14 02:10Z - Promote Accelerated DAN / Grand Plan Local Operator Mode

- Proposed by: user via "Update DAN behavior from bounded queue-drain mode to Accelerated Local Grand Plan mode"
- Target model/profile: Codex Engineer-Operator with Claude and Antigravity handoff awareness
- Files changed: `DO_ANYTHING_NOW.md`, `AGENTS.md`, `CLAUDE.md`, `ANTIGRAVITY.md`, `docs/DAN_CONTINUOUS_STEWARDSHIP.md`, `_MODEL_TRINITY/GRAND_PLAN_LOCAL_OPERATOR_MODE.md`, `_MODEL_TRINITY/README.md`, `_MODEL_TRINITY/WINDOWS_SIGNAL_WATCH_PROTOCOL.md`, `_MODEL_TRINITY/TRINITY_OPERATING_PROTOCOL.md`, `_MODEL_TRINITY/CROSS_MODEL_HANDOFFS.md`, `_MODEL_TRINITY/CLAUDE_NEXT_SESSION_HANDOFF_2026-06-14.md`, `_MODEL_TRINITY/bridge/CYCLE_POLICY.md`, `scripts/trinity_grand_plan_next.py`, `scripts/README.md`, `ai_chi/tests/test_trinity_grand_plan_next.py`, `_MODEL_TRINITY/CONFIG_CHANGE_LOG.md`
- Reason: make empty bridge outboxes trigger safe repo-contained Grand Plan task selection during explicit user DAN cycles instead of ending after a quick health summary
- Expected improvement: Codex continues local documentation, schemas, tests, patch plans, bridge packets, risk reports, dry-run scripts, and validation work while other models are offline, then leaves compact handoffs for them
- Risk: future agents may confuse accelerated local repo work with external authority; mode docs and scanner preserve stop gates and label `LIVE_CAPABILITY_APPROVALS.md` as draft-only
- Rollback: restore files from `_backup/20260614-accelerated-dan-grand-plan/` and remove `_MODEL_TRINITY/GRAND_PLAN_LOCAL_OPERATOR_MODE.md`, `scripts/trinity_grand_plan_next.py`, and `ai_chi/tests/test_trinity_grand_plan_next.py`
- Requires user/MΣBUS approval: local repo-contained acceleration is user-authorized; provider/API calls, secrets, MCP/plugin installs, app config mutation, network listeners/brokers, public posting, GitHub push/merge, Docker/service/firewall/live-stack mutation, spending, destructive operations, and physical actuation remain stop-gated
- Review status: Codex implemented; py_compile, focused Grand Plan tests, content checks, Axioms floor, full `ai_chi` discovery, and secret-reference scan passed
- Final status: implemented
