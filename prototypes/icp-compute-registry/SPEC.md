# Autopoiesis Exchange Specification

## Purpose

Autopoiesis Exchange is an ICP canister set for coordinating AI compute work
without putting private memory or local control paths on-chain. It gives agents
persistent identities, lets users post compute jobs, lets providers bid and
settle jobs, and records reputation and credit accounting.

## Safety Boundary

This prototype targets a local replica. Mainnet deploys, real cycles, paid
provider execution, wallet integration, and private-memory export are outside
scope.

## Shared Types

### AgentId

Text DID string. Recommended form:

```text
did:icp:<principal>
```

### PrivacyTier

```motoko
{ #sovereign; #confidential; #internal; #public_tier }
```

### Result

All Motoko update functions use:

```motoko
{ #ok : T; #err : Text }
```

Rust ledger updates use:

```rust
Result<T, String>
```

## Canister Wiring

Each Motoko canister that calls another canister exposes:

```motoko
configureExchange(...)
```

The local deploy script calls these methods after `dfx deploy`, using the local
canister IDs returned by `dfx canister id`.

The deploy script also configures `governance`, wires `sigma_bus_adapter` to
governance for Integrity Gate alerts, and configures `compute_ledger` to emit
treasury Sigma Bus events to the adapter.

## identity_registry

Stores AI agent identities and capability profiles.

`HardwarePlatform` includes `#wibo_maritime`. `AgentCapability` includes optional
`maritime_metadata` with `vessel_name`, optional `mmsi`, optional `home_port`,
and `deployment_context`.

### Validation

- `agent_id` must not be empty.
- `display_name` must not be empty.
- `operator_principal` must match `caller`.
- `benchmark_tflops` must be greater than zero.
- Capability and model arrays must be non-empty for registration.

### Public Queries

- `getAgent(agentId) -> ?AgentCapability`
- `listAgents() -> [AgentCapability]`
- `listByComputeType(computeType) -> [AgentCapability]`
- `getStats() -> { total; active }`
- `verify(agentId) -> Bool`

### Updates

- `registerAgent(profile) -> Result<AgentId, Text>`
- `updateLastSeen(agentId) -> Result<(), Text>`
- `deactivateAgent(agentId) -> Result<(), Text>`
- `updateCapabilities(agentId, computeTypes, modelSupport) -> Result<(), Text>`

## job_market

Posts jobs, accepts bids, manages assignments, and enforces lifecycle
transitions.

`JobSpec` includes additive optional fields from `JobLifecycleRecord`, including
`task_subtype`, `request_summary`, `input_descriptor`, `preferred_tier`,
fallback/integrity/human/audit flags, `sigbus_envelope_id`, `parent_job_id`,
`tags`, and `lifecycle_audit`.

### Lifecycle

```text
open -> bidding -> accepted -> in_progress -> delivered -> verified -> settled
open -> cancelled
bidding -> cancelled
accepted -> disputed
in_progress -> disputed
delivered -> disputed
verified -> disputed
disputed -> cancelled
```

### Validation

- Job budget must be greater than zero.
- Deadline must be in the future.
- Task type and job ID must not be empty.
- Bids are accepted only while a job is `open` or `bidding`.
- Only the poster can accept a bid or cancel an open job.
- Only the poster or assigned agent can update status.
- Assignments lock escrow when the ledger canister is configured.
- Settlement releases escrow once and records reputation when those canisters
  are configured.

## reputation_engine

Tracks outcome history, endorsements, decay, and rankings.

### Score Formula

1. Start from success ratio:
   `(jobs_completed + dispute_won) / total_outcomes`
2. Apply latency modifier:
   - `+0.02` when actual latency is under the promised latency.
   - `-0.05` when actual latency is more than 2x promised latency.
3. Apply quality multiplier:
   `score * (0.8 + 0.2 * quality_score)`
4. Apply decay:
   score moves 1 percent toward `0.5` for each 30 days of inactivity.
5. Clamp to `[0.0, 1.0]`.

## compute_registry

Stores provider profiles, discovery metadata, and science-pool entries.

`ProviderProfile` is also exposed as `ProviderCapabilityProfile` and includes
additive optional fields from the full provider schema: `location_class`,
`privacy_tier`, `hardware_summary`, `capacity_summary`, `constraints`,
`reputation_score`, and `metadata`.

### Matching

`findBestMatch(taskType, budget, privacyTier)` filters active providers by
compute type, price, privacy tier, and availability. It ranks candidates by:

```text
availability / max(base_price_credits, 1)
```

## agent_runtime

Template canister for a persistent agent presence. It stores local job state and
bridges to the market and reputation canisters.

### Guardrails

- `configure` can run only once.
- Only the configured operator can mutate runtime state.
- Active jobs cannot exceed `max_concurrent_jobs`.
- Task type must be accepted by the agent configuration.

## compute_ledger

Rust ledger for compute credits.

### Invariants

- Balances never go negative.
- Transfers spend only available balance, not staked credits.
- Escrow lock deducts balance before creating the escrow entry.
- Escrow release is once-only.
- Escrow refund is once-only and returns funds to payer.
- Stake cannot be transferred while staked.
- Slashing reduces stake first and never underflows.
- Total supply changes only through admin minting.
- Science-pool donation burns spendable balance into a tracked pool balance.

### Admin

The init caller becomes the ledger admin. Only admin can mint and slash.

### Sigma Bus Events

`compute_ledger` keeps a bounded local treasury event trail and can forward the
same event as a Sigma Bus v1 envelope when `configureSigmaBus` is set.

Public methods:

- `configureSigmaBus(canister) -> Result<(), String>` admin only.
- `getSigmaBusCanister() -> ?Principal`
- `getSigmaEvents(limit) -> [LedgerSigmaEvent]`

Financial mutations emit:

- `treasury.credit.earned` on mint and unstake.
- `treasury.credit.spent` on transfer, stake, and science-pool donation.
- `treasury.escrow.locked` on escrow lock.
- `treasury.escrow.released` on escrow release and refund.
- `treasury.escrow.slashed` on stake slashing.
- `treasury.science.donated` on science-pool donation.

## capital_pool

Investment and underwriting pool for exchange liquidity. All capital, share,
fee, yield, and science-pool accounting is `Nat`; no `Float` is used in balance
mutation paths.

### Types

- `InvestorId = Principal`
- `PoolShares = Nat`
- `Credits = Nat`
- `Currency = { #icp; #ck_usdc; #internal_credit }`
- `PoolPhase = { #simulation; #micro_pool; #open_pool; #institutional }`
- `PoolState` tracks total shares, total capital, deployed capital, available
  capital, science balance, distributed yield, utilization cap, fee rate, and
  science allocation rate.
- `UnderwritingRecord` tracks job ID, amount, settlement status, outcome, fee,
  loss, and whether the record came from simulation phase.

### Queries

- `getPoolState() -> PoolState`
- `getPosition(investor) -> ?InvestorPosition`
- `listPositions() -> [InvestorPosition]`
- `getUnderwritingRecord(recordId) -> ?UnderwritingRecord`
- `listActiveUnderwriting() -> [UnderwritingRecord]`
- `getUtilizationRate() -> Nat`
- `estimateYield(credits, days) -> Credits`
- `getScienceDonations() -> [ScienceDonation]`
- `getScienceDisbursements() -> [ScienceDisbursement]`
- `getPhase() -> PoolPhase`
- `getTreasuryPolicy() -> TreasuryPolicy`
- `getTreasurySnapshot() -> TreasurySnapshot`
- `spendAllowed(amount) -> Result<(), Text>`
- `getGateLog(limit) -> [(Time.Time, Text, Bool)]`

### Updates

- `configureExchange(jobMarket, computeLedger) -> Result<(), Text>`
- `deposit(amount, currency) -> Result<PoolShares, Text>`
- `withdraw(shares) -> Result<Credits, Text>`
- `underwrite_job(jobId, amount) -> Result<Text, Text>`
- `settle_underwriting(recordId, outcome, settlementCredits) -> Result<(), Text>`
- `donateToSciencePool(amount, domain) -> Result<(), Text>`
- `withdrawFromSciencePool(to, amount, domain) -> Result<(), Text>`
- `setPhase(phase) -> Result<(), Text>`
- `setTreasuryPolicy(policy) -> Result<(), Text>`
- `setMaxUtilizationRate(rate) -> Result<(), Text>`
- `setUnderwritingFeeRate(rate) -> Result<(), Text>`
- `setScienceAllocationRate(rate) -> Result<(), Text>`
- `setMicroPoolCap(cap) -> Result<(), Text>`

### Invariants

- `available_capital + deployed_capital == total_capital`.
- New underwriting cannot push deployed capital above the integer utilization
  cap.
- Withdrawals can redeem only available capital, never deployed capital.
- Phase 0 and 1 science withdrawals are logged as simulated disbursements and
  do not call the ledger.
- Treasury policy uses `Nat` fields for reserves, operating budgets, and rates.
- Treasury lockdown or active refusal conditions block spend checks.

## procurement_router

Autonomous external procurement layer. The canister keeps provider records and
spend limits, but v0 provider calls are typed mock stubs only.

### Privacy Gate

`triggerProcurement` first pattern-matches the privacy tier. `#sovereign`
returns `#err("sovereign jobs cannot be externally procured")`; `#confidential`
returns `#err("confidential jobs cannot be externally procured")`. This happens
before config checks, spend checks, quote selection, or provider-specific code.

### Queries

- `getProcurementRecord(recordId) -> ?ProcurementRecord`
- `getRecordByJobId(jobId) -> ?ProcurementRecord`
- `listRecords(limit) -> [ProcurementRecord]`
- `listByStatus(status) -> [ProcurementRecord]`
- `getRouterConfig() -> RouterConfig`
- `getSpendState() -> SpendState`
- `getGateLog(limit) -> [(Time.Time, Text, Bool)]`

### Updates

- `configureExchange(jobMarket, capitalPool, computeRegistry, reputation) -> Result<(), Text>`
- `updateConfig(config) -> Result<(), Text>`
- `triggerProcurement(request) -> Result<Text, Text>`
- `approveProcurement(recordId) -> Result<(), Text>`
- `completeProcurement(recordId, resultHash) -> Result<(), Text>`
- `failProcurement(recordId, message) -> Result<(), Text>`
- `cancelProcurement(recordId) -> Result<(), Text>`

### Provider Stubs

- Akash price/deploy/status stubs.
- Golem market/agreement stubs.
- OpenAI-compatible cloud price/execute stubs.
- Filecoin store/retrieve stubs.
- Cloudflare R2 store stub.

All stubs return typed mock data and include endpoint TODO comments. There are no
API keys and no live HTTPS outcalls.

## data_orchestrator

Data pipeline planner and storage policy gate.

### Typed Storage Policy

`validateStoragePolicy` and every write path call the same typed pattern match:

- `#sovereign` allows only `#local_agent`.
- `#confidential` allows only `#local_agent` and `#encrypted_canister`.
- `#internal` allows local, encrypted canister, ICP asset, Filecoin, and
  Cloudflare R2, but rejects public IPFS.
- `#public_tier` allows all storage targets.

Because the policy is a variant tuple match over `(PrivacyTier, StorageTarget)`,
new privacy tiers or storage targets force compiler-visible policy handling.

### Queries

- `validateStoragePolicy(tier, target) -> Result<(), Text>`
- `getAsset(assetId) -> ?DataAsset`
- `listAssets(limit) -> [DataAsset]`
- `listByStage(stage) -> [DataAsset]`
- `getStats() -> Stats`
- `getGateLog(limit) -> [(Time.Time, Text, Bool)]`

### Updates

- `configureExchange(jobMarket, procurementRouter) -> Result<(), Text>`
- `registerAsset(asset) -> Result<Text, Text>`
- `planPipeline(request) -> Result<Text, Text>`
- `routeStorage(assetId, target) -> Result<(), Text>`
- `completeAsset(assetId) -> Result<(), Text>`

## Integrity Gate

Sensitive Motoko canisters include a private:

```motoko
integrityGate(operation : Text, privacyTier : PrivacyTier, targetCanister : ?Text) : Bool
```

The gate blocks sovereign operations that target external providers/storage and
blocks operations explicitly marked `memory_leak`. Each decision is written to a
stable bounded log that keeps the last 1000 entries.

## governance

Parameter control canister for capital-pool phase movement and shared treasury
parameters. The first authorized caller becomes admin; later control can be
expanded through authorized principals, required approvals, and multisig-style
configuration.

### Controlled Parameters

- `capital_pool.phase`
- `capital_pool.max_utilization_rate`
- `capital_pool.underwriting_fee_rate`
- `capital_pool.science_allocation_rate`
- `capital_pool.micro_pool_cap`
- `procurement_router.max_daily_spend_credits`

Any proposal whose target or parameter contains `integrity_gate` is rejected by
a constitutional rule. The Integrity Gate is observed and logged, not weakened
through governance.

### Public Methods

- `getConfig() -> GovernanceConfig`
- `getProposal(proposalId) -> ?Proposal`
- `listProposals(status) -> [Proposal]`
- `getCurrentPhase() -> PoolPhase`
- `getParameter(key) -> ?Text`
- `listParameters() -> [(Text, Text)]`
- `getPhaseRequirements(targetPhase) -> PhaseAdvanceRequirements`
- `canAdvancePhase(targetPhase) -> Result<(), Text>`
- `getIntegrityAlerts(limit) -> [IntegrityAlert]`
- `getStats() -> Stats`
- `propose(targetCanister, parameter, proposedValue, rationale) -> Result<Text, Text>`
- `approve(proposalId) -> Result<(), Text>`
- `reject(proposalId) -> Result<(), Text>`
- `enact(proposalId) -> Result<(), Text>`
- `proposePhaseAdvance(targetPhase, evidence) -> Result<Text, Text>`
- `enactPhaseAdvance(proposalId) -> Result<(), Text>`
- `receiveIntegrityAlert(alert) -> Result<(), Text>`
- `reportJobCompleted() -> Result<(), Text>`
- `confirmExternalAudit(auditRef) -> Result<(), Text>`
- `addAuthorized(principal) -> Result<(), Text>`
- `removeAuthorized(principal) -> Result<(), Text>`
- `setRequiredApprovals(n) -> Result<(), Text>`
- `upgradeToMultisig(principals, required) -> Result<(), Text>`
- `setCanisters(capitalPool, sigmaBusAdapter, auditLog) -> Result<(), Text>`

## sigma_bus_adapter

Bridge for local Sigma Bus events from the Omni-AI/Wibo stack into the ICP
audit/control plane. The adapter accepts the formal v1 envelope defined in
`docs/sigma-bus-schema-v1.md`, verifies required fields and enum-like text
values, stores accepted events, and counts rejected envelopes.

### Envelope

- `event_id`, `schema_version`, `emitted_at`, `event_type`, `payload_type`, and
  `payload` are required text fields.
- `privacy_tier` accepts `sovereign`, `confidential`, `internal`, or `public`.
- `lens_state` accepts `positive`, `negative`, `uncertain`, or `none`.
- `provenance_chain` must be non-empty and begin with `originated`.
- signatures are optional now, but any supplied signature must be 128 hex
  characters.

### Public Methods

- `configureGovernance(governance) -> Result<(), Text>`
- `verifyEnvelope(envelope) -> VerificationResult`
- `emitEvent(envelope) -> Result<Text, Text>`
- `getRecentEvents(limit) -> [StoredEvent]`
- `getEvent(eventId) -> ?StoredEvent`
- `getEventCount() -> Nat`
- `getStats() -> Stats`

## audit_log

Append-only `ComputeDecisionRecord` canister. It stores cost/value breakdowns,
Integrity Gate result, treasury snapshot, optional provider selection, decision,
policy rules, optional provider-specific costs, and optional learning signal.

### Public Methods

- `recordDecision(record) -> Result<Text, Text>`
- `getDecision(decisionId) -> ?ComputeDecisionRecord`
- `listDecisions(limit) -> [ComputeDecisionRecord]`
- `listByJob(jobId) -> [ComputeDecisionRecord]`
- `getStats() -> Stats`

There are no delete or update methods for decision records.

## Extended Wiring

`deploy_local.sh` wires:

- `capital_pool` to `job_market` and `compute_ledger`.
- `procurement_router` to `job_market`, `capital_pool`, `compute_registry`, and
  `reputation_engine`.
- `data_orchestrator` to `job_market` and `procurement_router`.
- `capital_pool` and `sigma_bus_adapter` to `governance`.
- `compute_ledger` to `sigma_bus_adapter` for treasury event emission.
- `governance` to `capital_pool`, `sigma_bus_adapter`, and `audit_log`.
- `audit_log` deploys as an append-only standalone logging surface.
