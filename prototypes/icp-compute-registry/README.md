# Autopoiesis Exchange ICP Prototype

This prototype is the public coordination and economic control-plane layer for
Project Autopoiesis. It models agent identity, job posting, provider discovery,
reputation, per-agent runtime state, and compute-credit accounting on a local
Internet Computer replica.

The prototype is not a mainnet deployment. It does not spend real cycles, route
private memory, or enable autonomous treasury behavior.

## Canisters

| Canister | Language | Responsibility |
| --- | --- | --- |
| `identity_registry` | Motoko | Agent DIDs, capability profiles, operator ownership, hardware and privacy tiers. |
| `job_market` | Motoko | Job posting, bids, assignment, lifecycle transitions, escrow hooks. |
| `reputation_engine` | Motoko | Outcome history, score updates, decay, endorsements, ranking. |
| `compute_registry` | Motoko | Provider catalog, discovery, availability, science pool metadata. |
| `agent_runtime` | Motoko | Per-agent local job state and bridge calls to market and reputation canisters. |
| `compute_ledger` | Rust | Credit balances, stake, escrow, release, refund, slashing, and science-pool accounting. |
| `capital_pool` | Motoko | Investment pool, utilization caps, underwriting records, fee yield, science donations. |
| `procurement_router` | Motoko | External compute procurement with hard privacy gates and typed provider stubs. |
| `data_orchestrator` | Motoko | Data pipeline planning with compile-covered privacy/storage routing policy. |
| `governance` | Motoko | Parameter control, phase advancement, multisig-ready approvals, and Integrity Gate alerts. |
| `sigma_bus_adapter` | Motoko | Local Sigma Bus v1 envelope bridge with verification and append-only event storage. |
| `audit_log` | Motoko | Append-only `ComputeDecisionRecord` audit trail. |

## Layout

```text
prototypes/icp-compute-registry/
├── dfx.json
├── Cargo.toml
├── README.md
├── SPEC.md
├── src/
│   ├── identity_registry/main.mo
│   ├── job_market/main.mo
│   ├── reputation_engine/main.mo
│   ├── compute_registry/main.mo
│   ├── agent_runtime/main.mo
│   ├── capital_pool/main.mo
│   ├── procurement_router/main.mo
│   ├── data_orchestrator/main.mo
│   ├── governance/main.mo
│   ├── sigma_bus_adapter/main.mo
│   ├── audit_log/main.mo
│   └── compute_ledger/
│       ├── Cargo.toml
│       ├── compute_ledger.did
│       └── src/lib.rs
├── scripts/
│   ├── deploy_local.sh
│   └── smoke_test.sh
├── docs/
│   ├── autopoiesis-folder-inventory.md
│   ├── gap-report-autopoiesis-vs-build.md
│   ├── sigma-bus-schema-v1.md
│   └── dfx-install-windows.md
└── tests/
    └── integration_notes.md
```

## Prerequisites

- `dfx`
- Rust with `wasm32-unknown-unknown`
- Git Bash, WSL, Linux, or macOS shell for the scripts

On this Windows workstation, the prototype files can be edited locally, but the
current PATH must expose `dfx`, `cargo`, and `rustc` before the completion gate
can pass.

For Windows, use the WSL2 path in `docs/dfx-install-windows.md`; install `dfx`
inside WSL and run the scripts from the `/mnt/c/...` checkout path.

## Build

```bash
cd prototypes/icp-compute-registry
dfx build
```

## Local Deploy

```bash
./scripts/deploy_local.sh
```

The deploy script starts a clean local replica, deploys all canisters, and wires
their canister IDs through `configureExchange`, governance, and Sigma Bus
configuration calls.

## Smoke Test

```bash
./scripts/smoke_test.sh
```

The smoke test checks:

- agent registration and provider registration
- ledger mint, transfer, stake, escrow lock, release, refund, and slashing guards
- job posting, bidding, assignment, status transitions, and cancellation guards
- reputation outcome recording and ranking
- agent runtime configuration, active job tracking, completion, and failure
- capital-pool deposits, integer utilization, and governance parameter guards
- procurement-router hard rejects for sovereign and confidential external work
- public external procurement through typed mock provider stubs
- data-orchestrator storage-policy rejects for illegal privacy/target pairs
- governance constitutional rejects, parameter enactment, and phase gates
- Sigma Bus v1 event logging, ledger treasury events, and append-only compute-decision audit logging
- treasury policy/snapshot queries and Integrity Gate log queries
- stats queries across all Motoko canisters

## Safety Posture

- Local replica only.
- No mainnet deployment commands.
- No real cycles.
- No wallet integration.
- No private-memory export.
- Ledger accounting uses unsigned integer credits, never floats.
- Escrow cannot release twice.
- Transfers cannot spend staked credits.
- Balances are checked before every debit.
- Capital-pool accounting uses `Nat` only; utilization is integer percent.
- Sovereign and confidential jobs cannot enter external procurement.
- Sovereign data cannot route to external storage targets.
- Confidential data cannot route to public or external storage targets.
- Integrity Gate decisions are logged in bounded last-1000 logs on sensitive canisters.
- Compute decision records are append-only in `audit_log`.
- `identity_registry` supports optional Wibo/maritime metadata without requiring vessel identifiers.
- `governance` rejects Integrity Gate parameter changes through a constitutional guard.
- `sigma_bus_adapter` rejects malformed v1 envelopes before storing them.

## External Provider Stubs

`procurement_router` includes typed mock stubs for Akash, Golem, generic
OpenAI-compatible cloud APIs, Filecoin, and Cloudflare R2. The stubs do not make
network calls and do not contain API keys. Each stub has a `TODO` comment with
the intended HTTPS endpoint shape for a future `ic.http_request` implementation.
