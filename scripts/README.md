# DAN scripts

Debugged DAN v2.5.1 toolkit (promoted live 2026-06-12). All `set -euo pipefail`, local-only,
no side effects. See `../DO_ANYTHING_NOW.md`.

| Script | Purpose | Blocks? |
|---|---|---|
| `dan_preflight.sh` | repo discovery: git state, canon docs, stack, test cmds, secret-name hits | no |
| `dan_stewardship_scan.sh` | stewardship recon: tree, canon/state docs, doc signals, next step | no |
| `dan_pre_publish_gate.sh` | **fail-closed** secret/PII gate — exit 1 on hit | **yes** |
| `dan_public_release_scan.sh` | heuristic public-artifact + token report | no |
| `dan_community_outreach_scan.sh` | community-docs + risk-pattern report (bug-fixed) | no |
| `dan_evidence_init.sh` | scaffold `artifacts/evidence/<stamp>_<slug>/` | no |
| `service-watchdog.ts` | local HTTP/TCP service health check; emits compact summaries and proposal-only fallback records | yes, exits nonzero on degraded/offline services |
| `service_watchdog_smoke_test.py` | starts a temporary localhost HTTP fixture and verifies ONLINE/OFFLINE/proposal behavior | yes, fails on contract drift |
| `trinity_bridge.py` | local file-backed relay for Codex/Claude/Antigravity handoff packets; routes JSON records, never executes them | no |
| `python -m trinity_bridge.health.cli` | local heartbeat, liveness poke, downtime, and health-summary CLI for the Trinity bridge; writes only under the bridge root | no |
| `tools/trinity_quota_guard.py` | local stdlib quota/session guard; computes READY/LOW_BUDGET/COOLDOWN/OFFLINE status, writes downtime records, and emits throttled metadata-only quota pokes | no |
| `check_ledger_integrity.py` | read-only JSONL ledger hash-chain checker for file-backed ledger streams | yes, exits nonzero on integrity failure |
| `trinity_executor.py` | Codex-side allowlisted executor for structured Trinity `execution_request` packets; never runs free-form body text as shell | yes, fails on unknown/unsafe requests |
| `trinity_arbitrator.py` | pre-route Trinity work-queue arbitrator; validates packets, claims safe work, compacts handoffs, and quarantines stale/superseded/approval-gated records | yes, fails on invalid arbitration setup |
| `trinity_dan_cycle.py` | foreground Trinity+DAN cycle runner; routes packets, processes safe execution requests, optionally runs DAN checks, writes cycle ledger/state | yes, fails on failed checks |
| `trinity_grand_plan_next.py` | Accelerated DAN scanner; ranks safe repo-contained Grand Plan tasks and can emit a non-action `GrandPlanNextTasks` packet | no |
| `dan_completion_report.sh` | new `reports/dan-completion-*.md` skeleton | no |
| `dan_next_step_report.sh` | new `reports/dan-next-step-*.md` skeleton | no |
| `dan_poc_completion_report.sh` · `dan_benchmark_report.sh` · `dan_research_log.sh` · `dan_screenshot_manifest.sh` · `dan_public_queue_report.sh` · `dan_community_queue_report.sh` | report/queue scaffolds | no |

**Fixed in this promotion:** `dan_community_outreach_scan.sh` had a literal `\n` (lines 14/17)
that broke its secret scan (fail-open). Corrected; the enforcing gate is `dan_pre_publish_gate.sh`.
