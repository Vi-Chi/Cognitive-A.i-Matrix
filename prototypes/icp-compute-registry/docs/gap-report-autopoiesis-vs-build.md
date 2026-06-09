# Gap Report: Autopoiesis_Project vs ICP Build
Generated: 2026-05-26

## Inventory Summary

- Read-first files inventoried: 188
- Read-first total size: 638670 bytes
- Design-bearing sources: root `.txt`/`.md` docs, full JSON schemas, `PAY_icp_design_files.zip`, project repo docs/specs, and ICP prototype source files from Tasks 1 and 2.
- Key schemas found: `ProviderCapabilityProfile`, `JobLifecycleRecord`, `ComputeDecisionRecord`, `TreasuryPolicy`, `IntegrityGateResult`, `TreasurySnapshot`, `ProviderSelectionRecord`, `AuditEntry`.
- Key architecture concepts found: local-first sovereignty, Integrity Gate before economics, SigmaBUS event/envelope fabric, immutable compute-decision audit trail, treasury/cycles simulation, external procurement only for lower privacy tiers, Wibo/maritime hardware context.

## Type / Schema Gaps

| Concept | Found in folder | In build? | Action |
| --- | --- | --- | --- |
| `ProviderCapabilityProfile` | `PAY_icp_design_files.zip/provider-capability.schema.json` | Partially via `compute_registry.ProviderProfile` | Implemented additive optional fields plus `ProviderCapabilityProfile` alias in `compute_registry`. |
| `JobLifecycleRecord` | `PAY_icp_design_files.zip/job-lifecycle.schema.json` | Partially via `job_market.JobSpec`, `Bid`, `JobAssignment` | Implemented additive optional lifecycle/audit fields plus `JobLifecycleRecord` alias in `job_market`. |
| `ComputeDecisionRecord` | root `compute-decision.schema.json`, ZIP schema, docs | Not previously implemented as an append-only ledger | Implemented new append-only `audit_log` canister. |
| `IntegrityGateResult` | root/ZIP compute-decision schemas and docs | Previously only implicit in privacy gates | Implemented explicit gate function/logs in sensitive Motoko canisters. |
| `TreasuryPolicy` | root `treasury-policy.schema.json`, compact repo spec | Partially via `capital_pool` rates/caps | Implemented additive policy/snapshot fields and query/update functions in `capital_pool`. |
| SigmaBUS envelope/event fabric | many docs and `sigbus_envelope_id` in job schema | Not previously implemented | Implemented conservative `sigma_bus_adapter` canister because event fabric is repeatedly defined, though no standalone event JSON schema exists. |
| Wibo/maritime agent metadata | docs mention maritime/Wibo/Hailo stack; no formal WiboAgent JSON schema | Not previously implemented | Implemented optional `maritime_metadata` and `#wibo_maritime` variant in `identity_registry`. |
| `MetabolismLedger` | Mentioned conceptually as metabolism/economic layer | Not a concrete schema | Not implemented as a separate ledger; mapped to `audit_log` plus `capital_pool` pending a formal schema. |
| Cognitive Matrix hooks | Repeated docs | Not explicit canister type | Represented through SigmaBUS event source/provenance and audit records. |

## Architectural Gaps

- Integrity Gate was defined as a first-class veto layer in the folder but was only implicit in Tasks 1 and 2. It is now present as bounded gate logs and private guard functions in `job_market`, `compute_registry`, `procurement_router`, `data_orchestrator`, and `capital_pool`.
- SigmaBUS is repeatedly described as the event/provenance fabric. No standalone JSON event schema exists in the folder, but the architecture requires an adapter boundary for local Omni-AI/Wibo events to reach the ICP audit/control plane. `sigma_bus_adapter` now provides that stub boundary.
- ComputeDecisionRecord audit trail was absent. `audit_log` now stores append-only decision records linked to jobs, treasury state, integrity gate results, and provider selection.
- TreasuryPolicy is more detailed than the prior `capital_pool`; missing pieces included reserve floor, approval limits, lockdown flag, snapshot cadence, and policy metadata. `capital_pool` now exposes conservative policy and snapshot functions without replacing existing Nat-only accounting.
- Provider capability and job lifecycle schemas were richer than the current canister records. Current build now includes additive optional fields while keeping the original operational flow.
- Wibo/maritime hardware context was present as a domain direction but not a complete formal type. The build now uses optional metadata only and does not require vessel identifiers.

## Config / Deployment Gaps

- No alternate `dfx.json`, `mops.toml`, `vessel.dhall`, or canister package config was found outside the prototype.
- Task 1/2 build gate remains blocked on this Windows host because `dfx` is not available on PATH.
- Added `docs/dfx-install-windows.md` with the WSL2 install/run path.
- Updated `dfx.json` to add `sigma_bus_adapter` and `audit_log`.
- Updated `deploy_local.sh` and `smoke_test.sh` to include the new canisters and additive fields.

## Documentation Gaps

- The canister docs previously did not mention the folder reconciliation, SigmaBUS adapter, audit-log canister, Integrity Gate logs, or Wibo/maritime optional metadata.
- The prototype docs previously did not provide WSL2 install/run guidance for `dfx` on this Windows host.
- The source-priority gap between compact repo schemas and full ZIP/root schemas is now explicit in this report.

## Conflicts Requiring Human Review

- Provider schema naming conflict: full schema uses `ProviderCapabilityProfile`, compact repo spec uses `ProviderCapability`, build uses `ProviderProfile`. Implemented an alias and optional fields instead of renaming the build type.
- Job schema conflict: full schema uses `JobLifecycleRecord` with `privacy_level`, `preferred_tier`, `max_budget_credits`, dispatch/outcome/audit fields; build uses `JobSpec` with `privacy_tier`, `budget_credits`, bids and assignments as separate records. Implemented additive fields only.
- Decision schema conflict: compact repo `ComputeDecision` is much smaller than root/ZIP `ComputeDecisionRecord`; root/ZIP is treated as richer but not silently substituted in existing files. Implemented a new canister.
- Treasury schema conflict: compact repo `TreasuryPolicy` is minimal, root schema has detailed reserves, approvals, lockdown and audit policy. Implementation extends `capital_pool` conservatively, not a full policy engine.
- SigmaBUS conflict: architecture clearly defines an event fabric, but no standalone formal SigmaBUS event schema is present. The adapter stub uses conservative generic fields and needs review before live integration.
- Maritime/Wibo conflict: folder mentions maritime/Wibo context but does not define a formal WiboAgent schema. Optional metadata is implemented, but no vessel identifier is required.
- Language recommendation conflict: some design notes prefer Rust for core ICP surfaces, while Tasks 1 and 2 built Motoko canisters with a Rust ledger. Task 3 preserves the existing mixed-language build.
- Cycles/accounting conflict: several docs discuss ICP cycles and internal credits at different abstraction levels. Task 3 did not add real cycles spending or mainnet behavior.

## Recommended Actions

1. P1 type alignment: completed for provider, job lifecycle, compute decision audit, treasury policy, and maritime identity fields using additive-only changes.
2. P2 Integrity Gate: completed in sensitive canisters with bounded last-1000 gate logs.
3. P3 SigmaBUS adapter stub: completed as `sigma_bus_adapter`.
4. P4 ComputeDecisionRecord audit trail: completed as append-only `audit_log`.
5. P5 treasury extension: completed as conservative policy/snapshot functions in `capital_pool`.
6. P6 Wibo/maritime agent type: completed in `identity_registry`.
7. Human review: settle the unresolved naming/source-priority conflicts before promoting schemas to production Candid contracts.
