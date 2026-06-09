# MERGE REPORT - Autopoiesis Unified (2026-06-09)

- project-autopoiesis: 75 files
- autopoiesis: 9 files
- union distinct paths: 81
- conflicts (same path, differing content): 3 -> .gitignore, LICENSE, README.md

## Conflict handling
README.md: both READMEs merged into one (substrate/watchdog + economic-metabolism facets).
.gitignore: union of both. LICENSE: single GPLv3 (identical license; one kept). .gitattributes: from project-autopoiesis (only repo that had it).
No _conflicts/ folder. Originals remain in _github_backup/ with full history.

## File manifest (path | source(s) | note)
| path | source(s) | note |
|---|---|---|
| .gitattributes | project-autopoiesis | unique |
| .github\ISSUE_TEMPLATE\bug_report.md | autopoiesis | unique |
| .github\ISSUE_TEMPLATE\feature_request.md | autopoiesis | unique |
| .github\ISSUE_TEMPLATE\integrity-review.md | project-autopoiesis | unique |
| .github\ISSUE_TEMPLATE\research-brief.md | project-autopoiesis | unique |
| .github\workflows\validate.yml | project-autopoiesis | unique |
| .gitignore | project-autopoiesis,autopoiesis | CONFLICT -> union of both .gitignore |
| ARCHITECTURE.md | autopoiesis | unique |
| CHANGELOG.md | project-autopoiesis | unique |
| CODE_OF_CONDUCT.md | project-autopoiesis | unique |
| CONTRIBUTING.md | project-autopoiesis | unique |
| docs\.gitkeep | autopoiesis | unique |
| docs\00-thesis\00-autopoiesis-thesis.md | project-autopoiesis | unique |
| docs\00-thesis\01-integrity-vs-economic-pressure.md | project-autopoiesis | unique |
| docs\00-thesis\02-compute-metabolism-model.md | project-autopoiesis | unique |
| docs\10-network-map\10-network-role-map.md | project-autopoiesis | unique |
| docs\10-network-map\11-icp-role-in-autopoiesis.md | project-autopoiesis | unique |
| docs\10-network-map\12-akash-compute-procurement.md | project-autopoiesis | unique |
| docs\10-network-map\13-golem-task-execution.md | project-autopoiesis | unique |
| docs\10-network-map\14-bittensor-usefulness-markets.md | project-autopoiesis | unique |
| docs\10-network-map\15-storage-and-public-memory-options.md | project-autopoiesis | unique |
| docs\20-economic-loop\20-economic-loop.md | project-autopoiesis | unique |
| docs\20-economic-loop\21-compute-cost-estimator.md | project-autopoiesis | unique |
| docs\20-economic-loop\22-task-value-estimator.md | project-autopoiesis | unique |
| docs\20-economic-loop\23-budget-and-treasury-policy.md | project-autopoiesis | unique |
| docs\30-v0-prototype\30-autopoiesis-v0-scope.md | project-autopoiesis | unique |
| docs\30-v0-prototype\31-icp-compute-registry-spec.md | project-autopoiesis | unique |
| docs\40-procurement\40-procurement-experiment-plan.md | project-autopoiesis | unique |
| docs\50-cognitive-matrix-integration\50-cognitive-matrix-integration.md | project-autopoiesis | unique |
| docs\50-cognitive-matrix-integration\51-integrity-gate-for-economic-actions.md | project-autopoiesis | unique |
| docs\50-cognitive-matrix-integration\52-out-of-loop-audit-of-autopoietic-decisions.md | project-autopoiesis | unique |
| docs\60-services-and-revenue\60-safe-service-candidate-filter.md | project-autopoiesis | unique |
| docs\70-sovereignty-and-safety\70-local-sovereignty-and-privacy.md | project-autopoiesis | unique |
| docs\RUNTIME.md | autopoiesis | unique |
| LICENSE | project-autopoiesis,autopoiesis | CONFLICT -> single GPLv3 (project-autopoiesis) |
| MASTER_CONTEXT.md | project-autopoiesis | unique |
| prototypes\icp-compute-registry\.gitignore | project-autopoiesis | unique |
| prototypes\icp-compute-registry\Cargo.lock | project-autopoiesis | unique |
| prototypes\icp-compute-registry\Cargo.toml | project-autopoiesis | unique |
| prototypes\icp-compute-registry\dfx.json | project-autopoiesis | unique |
| prototypes\icp-compute-registry\docs\autopoiesis-folder-inventory.md | project-autopoiesis | unique |
| prototypes\icp-compute-registry\docs\dfx-install-windows.md | project-autopoiesis | unique |
| prototypes\icp-compute-registry\docs\gap-report-autopoiesis-vs-build.md | project-autopoiesis | unique |
| prototypes\icp-compute-registry\docs\sigma-bus-schema-v1.md | project-autopoiesis | unique |
| prototypes\icp-compute-registry\README.md | project-autopoiesis | unique |
| prototypes\icp-compute-registry\scripts\deploy_local.sh | project-autopoiesis | unique |
| prototypes\icp-compute-registry\scripts\smoke_test.sh | project-autopoiesis | unique |
| prototypes\icp-compute-registry\SPEC.md | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\agent_runtime\main.mo | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\audit_log\main.mo | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\capital_pool\main.mo | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\compute_ledger\Cargo.toml | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\compute_ledger\compute_ledger.did | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\compute_ledger\src\lib.rs | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\compute_registry\main.mo | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\data_orchestrator\main.mo | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\governance\main.mo | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\identity_registry\main.mo | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\job_market\main.mo | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\procurement_router\main.mo | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\reputation_engine\main.mo | project-autopoiesis | unique |
| prototypes\icp-compute-registry\src\sigma_bus_adapter\main.mo | project-autopoiesis | unique |
| prototypes\icp-compute-registry\tests\integration_notes.md | project-autopoiesis | unique |
| prototypes\local-vs-remote-router\README.md | project-autopoiesis | unique |
| prototypes\treasury-simulator\README.md | project-autopoiesis | unique |
| README.md | project-autopoiesis,autopoiesis | CONFLICT -> clean-merged README (both facets) |
| reports\autopoiesis-discovery-phase0.md | project-autopoiesis | unique |
| research\akash\README.md | project-autopoiesis | unique |
| research\bittensor\README.md | project-autopoiesis | unique |
| research\ethereum\README.md | project-autopoiesis | unique |
| research\golem\README.md | project-autopoiesis | unique |
| research\icp\README.md | project-autopoiesis | unique |
| research\storage\README.md | project-autopoiesis | unique |
| ROADMAP.md | project-autopoiesis | unique |
| scripts\validate_project.py | project-autopoiesis | unique |
| SECURITY.md | project-autopoiesis | unique |
| specs\compute-decision.schema.json | project-autopoiesis | unique |
| specs\job-lifecycle.schema.json | project-autopoiesis | unique |
| specs\provider-capability.schema.json | project-autopoiesis | unique |
| specs\treasury-policy.schema.json | project-autopoiesis | unique |
| src\.gitkeep | autopoiesis | unique |
