#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

command -v dfx >/dev/null 2>&1 || {
  echo "dfx is required but was not found on PATH." >&2
  exit 127
}

dfx start --background --clean
dfx deploy

IDENTITY_ID="$(dfx canister id identity_registry)"
MARKET_ID="$(dfx canister id job_market)"
REPUTATION_ID="$(dfx canister id reputation_engine)"
COMPUTE_REGISTRY_ID="$(dfx canister id compute_registry)"
LEDGER_ID="$(dfx canister id compute_ledger)"
CAPITAL_POOL_ID="$(dfx canister id capital_pool)"
PROCUREMENT_ROUTER_ID="$(dfx canister id procurement_router)"
DATA_ORCHESTRATOR_ID="$(dfx canister id data_orchestrator)"
SIGMA_BUS_ADAPTER_ID="$(dfx canister id sigma_bus_adapter)"
AUDIT_LOG_ID="$(dfx canister id audit_log)"
GOVERNANCE_ID="$(dfx canister id governance)"

dfx canister call job_market configureExchange \
  "(opt principal \"$IDENTITY_ID\", opt principal \"$LEDGER_ID\", opt principal \"$REPUTATION_ID\")"

dfx canister call reputation_engine configureExchange \
  "(opt principal \"$IDENTITY_ID\")"

dfx canister call compute_registry configureExchange \
  "(opt principal \"$IDENTITY_ID\")"

dfx canister call agent_runtime configureExchange \
  "(principal \"$IDENTITY_ID\", principal \"$MARKET_ID\", principal \"$REPUTATION_ID\")"

dfx canister call capital_pool configureExchange \
  "(opt principal \"$MARKET_ID\", opt principal \"$LEDGER_ID\")"

dfx canister call capital_pool configureGovernance \
  "(opt principal \"$GOVERNANCE_ID\")"

dfx canister call procurement_router configureExchange \
  "(opt principal \"$MARKET_ID\", opt principal \"$CAPITAL_POOL_ID\", opt principal \"$COMPUTE_REGISTRY_ID\", opt principal \"$REPUTATION_ID\")"

dfx canister call data_orchestrator configureExchange \
  "(opt principal \"$MARKET_ID\", opt principal \"$PROCUREMENT_ROUTER_ID\")"

dfx canister call sigma_bus_adapter configureGovernance \
  "(opt principal \"$GOVERNANCE_ID\")"

dfx canister call compute_ledger configureSigmaBus \
  "(opt principal \"$SIGMA_BUS_ADAPTER_ID\")"

dfx canister call governance setCanisters \
  "(principal \"$CAPITAL_POOL_ID\", principal \"$SIGMA_BUS_ADAPTER_ID\", principal \"$AUDIT_LOG_ID\")"

echo "Autopoiesis Exchange deployed locally."
echo "identity_registry=$IDENTITY_ID"
echo "job_market=$MARKET_ID"
echo "reputation_engine=$REPUTATION_ID"
echo "compute_registry=$COMPUTE_REGISTRY_ID"
echo "agent_runtime=$(dfx canister id agent_runtime)"
echo "compute_ledger=$LEDGER_ID"
echo "capital_pool=$CAPITAL_POOL_ID"
echo "procurement_router=$PROCUREMENT_ROUTER_ID"
echo "data_orchestrator=$DATA_ORCHESTRATOR_ID"
echo "sigma_bus_adapter=$SIGMA_BUS_ADAPTER_ID"
echo "audit_log=$AUDIT_LOG_ID"
echo "governance=$GOVERNANCE_ID"
