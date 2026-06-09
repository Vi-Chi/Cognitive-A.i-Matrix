# Integration Notes

## Local Replica

Run `scripts/deploy_local.sh` from this directory. It starts a clean local
replica, deploys all canisters, and wires canister IDs into the canisters that
perform inter-canister calls.

## Inter-Canister Calls

- `job_market` calls `identity_registry.verify` when an identity registry is
  configured.
- `job_market.acceptBid` calls `compute_ledger.lockEscrow` when a ledger is
  configured.
- `job_market.updateStatus(... #settled)` calls `compute_ledger.releaseEscrow`
  and `reputation_engine.recordOutcome` when those canisters are configured.
- `reputation_engine.endorse` calls `identity_registry.verify` when configured.
- `compute_registry.registerProvider` calls `identity_registry.verify` when a
  linked `agent_id` is present.
- `agent_runtime` calls `job_market.updateStatus` and
  `reputation_engine.recordOutcome`.
- `capital_pool` authorizes underwriting and settlement callers through
  configured canister principals.
- `procurement_router` stores configured market, capital, registry, and
  reputation canister IDs for the external procurement path.
- `data_orchestrator` calls `procurement_router.triggerProcurement` only after
  its typed storage policy accepts the requested privacy/storage combination.
- `compute_ledger` stores bounded treasury Sigma Bus events locally and forwards
  to `sigma_bus_adapter` when configured.
- `sigma_bus_adapter` can forward Integrity Gate alert payloads to `governance`.
- `governance` applies selected capital-pool parameters and records Integrity
  Gate alerts without allowing the gate itself to be modified.

## Task 2 Checks

The smoke script covers the second canister set:

- `capital_pool.deposit`, `getPoolState`, integer utilization, and governance
  rate validation.
- `procurement_router.triggerProcurement` rejection for `#sovereign` and
  `#confidential` jobs before any external quote path.
- Successful mock external procurement for a `#public_tier` job.
- `data_orchestrator.validateStoragePolicy` rejects illegal sovereign/IPFS and
  confidential/R2 routes, then allows a public/IPFS route.

## Task 4 Checks

The smoke script now also covers:

- `compute_ledger.getSigmaEvents` after escrow and staking mutations.
- `sigma_bus_adapter.emitEvent` with a formal v1 envelope.
- `governance.propose` constitutional rejection for Integrity Gate parameters.
- `governance.enact` for a capital-pool parameter update.
- `governance.canAdvancePhase` rejection while phase requirements are unmet.

## Completion Gate

The handoff task completion gate requires:

1. `dfx build`
2. `scripts/smoke_test.sh`
3. A full file manifest posted back to the handoff task

The current Windows host must have `dfx`, Rust, and a usable shell on PATH before
those checks can pass.
