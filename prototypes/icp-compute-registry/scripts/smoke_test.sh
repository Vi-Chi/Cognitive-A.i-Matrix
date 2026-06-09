#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

command -v dfx >/dev/null 2>&1 || {
  echo "dfx is required but was not found on PATH." >&2
  exit 127
}

"$ROOT/scripts/deploy_local.sh"

CALLER="$(dfx identity get-principal)"
MARKET_ID="$(dfx canister id job_market)"
FUTURE_DEADLINE="4102444800000000000"
AGENT_ID="did:icp:${CALLER}"
JOB_ID="job-smoke-001"
REFUND_JOB_ID="job-smoke-refund-001"
BID_ID="bid-smoke-001"
PROVIDER_ID="provider-smoke-001"
PUBLIC_PROC_JOB_ID="job-smoke-public-procurement"
DATA_ASSET_ID="asset-smoke-001"

dfx canister call identity_registry registerAgent "(record {
  agent_id = \"$AGENT_ID\";
  display_name = \"Smoke Agent\";
  operator_principal = principal \"$CALLER\";
  hardware_platform = variant { raspberry_pi };
  privacy_tier = variant { sovereign };
  compute_types = vec { \"inference\"; \"embedding\" };
  model_support = vec { \"llama3\"; \"nomic-embed\" };
  benchmark_tflops = 1.25;
  maritime_metadata = null;
  registered_at = 0;
  last_seen = 0;
  active = true;
})"

dfx canister call identity_registry verify "(\"$AGENT_ID\")" | grep -q "true"

dfx canister call compute_registry registerProvider "(record {
  provider_id = \"$PROVIDER_ID\";
  agent_id = opt \"$AGENT_ID\";
  display_name = \"Smoke Provider\";
  provider_class = variant { sovereign_local };
  location_class = null;
  privacy_tier = null;
  endpoint = null;
  compute_types = vec { \"inference\"; \"embedding\" };
  model_support = vec { \"llama3\" };
  hardware_summary = null;
  capacity_summary = null;
  max_concurrent_jobs = 2;
  pricing_model = \"per_credit\";
  base_price_credits = 10;
  constraints = null;
  reputation_score = null;
  metadata = null;
  availability = 0.95;
  last_heartbeat = 0;
  active = true;
})"

dfx canister call compute_ledger mint "(principal \"$CALLER\", 1000 : nat)"
dfx canister call compute_ledger mint "(principal \"$MARKET_ID\", 1000 : nat)"
dfx canister call compute_ledger transfer "(principal \"$MARKET_ID\", 10 : nat)"
dfx canister call compute_ledger stake "(100 : nat)"
dfx canister call compute_ledger getStake "(principal \"$CALLER\")" | grep -q "100"
dfx canister call compute_ledger lockEscrow "(\"$REFUND_JOB_ID\", principal \"$MARKET_ID\", 5 : nat)"
dfx canister call compute_ledger refundEscrow "(\"$REFUND_JOB_ID\")"
dfx canister call compute_ledger getEscrow "(\"$REFUND_JOB_ID\")" | grep -q "released = true"

dfx canister call job_market postJob "(record {
  job_id = \"$JOB_ID\";
  posted_by = principal \"$CALLER\";
  task_type = \"inference\";
  task_subtype = null;
  description = \"smoke inference job\";
  request_summary = null;
  input_descriptor = null;
  required_compute_types = vec { \"inference\" };
  privacy_tier = variant { sovereign };
  preferred_tier = null;
  fallback_allowed = null;
  budget_credits = 100;
  deadline_ns = $FUTURE_DEADLINE;
  expiry_at = null;
  integrity_required = null;
  human_approval_required = null;
  audit_required = null;
  verification_method = variant { deterministic };
  status = variant { open };
  sigbus_envelope_id = null;
  parent_job_id = null;
  tags = null;
  lifecycle_audit = null;
  created_at = 0;
  updated_at = 0;
})"

dfx canister call job_market submitBid "(record {
  bid_id = \"$BID_ID\";
  job_id = \"$JOB_ID\";
  agent_id = \"$AGENT_ID\";
  agent_principal = principal \"$CALLER\";
  price_credits = 80;
  estimated_completion_ns = 1000000000;
  submitted_at = 0;
})"

dfx canister call job_market acceptBid "(\"$JOB_ID\", \"$BID_ID\")"
dfx canister call compute_ledger getEscrow "(\"$JOB_ID\")" | grep -q "released = false"

dfx canister call job_market updateStatus "(\"$JOB_ID\", variant { in_progress })"
dfx canister call job_market updateStatus "(\"$JOB_ID\", variant { delivered })"
dfx canister call job_market updateStatus "(\"$JOB_ID\", variant { verified })"
dfx canister call job_market updateStatus "(\"$JOB_ID\", variant { settled })"
dfx canister call compute_ledger getEscrow "(\"$JOB_ID\")" | grep -q "released = true"
dfx canister call compute_ledger releaseEscrow "(\"$JOB_ID\")" | grep -q "escrow already released"
dfx canister call compute_ledger slashStake "(principal \"$CALLER\", 25 : nat)"
dfx canister call compute_ledger getStake "(principal \"$CALLER\")" | grep -q "75"
dfx canister call compute_ledger unstake "(25 : nat)"
dfx canister call compute_ledger getStake "(principal \"$CALLER\")" | grep -q "50"
LEDGER_SIGMA_OUTPUT="$(dfx canister call compute_ledger getSigmaEvents "(20 : nat64)")"
grep "treasury.escrow.locked" <<<"$LEDGER_SIGMA_OUTPUT" >/dev/null

dfx canister call reputation_engine getReputation "(\"$AGENT_ID\")" | grep -q "jobs_completed"

dfx canister call agent_runtime configure "(record {
  agent_id = \"$AGENT_ID\";
  operator = principal \"$CALLER\";
  registry_canister = principal \"$(dfx canister id identity_registry)\";
  market_canister = principal \"$(dfx canister id job_market)\";
  reputation_canister = principal \"$(dfx canister id reputation_engine)\";
  max_concurrent_jobs = 2;
  auto_bid = false;
  min_job_budget = 1;
  accepted_task_types = vec { \"inference\"; \"embedding\" };
})"

dfx canister call agent_runtime getSummary

dfx canister call capital_pool deposit "(10000 : nat, variant { internal_credit })"
dfx canister call capital_pool getPoolState | grep -q "total_capital = 10_000"
dfx canister call capital_pool getUtilizationRate | grep -q "0"
dfx canister call capital_pool setMaxUtilizationRate "(80 : nat)"

dfx canister call procurement_router triggerProcurement "(record {
  job_id = \"job-smoke-sovereign-procurement\";
  task_type = \"inference\";
  budget_credits = 100;
  privacy_tier = variant { sovereign };
  trigger = variant { no_internal_match };
  job_spec_hash = \"hash-sovereign\";
})" | grep -q "sovereign jobs cannot be externally procured"

dfx canister call procurement_router triggerProcurement "(record {
  job_id = \"job-smoke-confidential-procurement\";
  task_type = \"inference\";
  budget_credits = 100;
  privacy_tier = variant { confidential };
  trigger = variant { no_internal_match };
  job_spec_hash = \"hash-confidential\";
})" | grep -q "confidential jobs cannot be externally procured"

dfx canister call procurement_router triggerProcurement "(record {
  job_id = \"$PUBLIC_PROC_JOB_ID\";
  task_type = \"inference\";
  budget_credits = 500;
  privacy_tier = variant { public_tier };
  trigger = variant { no_internal_match };
  job_spec_hash = \"hash-public\";
})"
dfx canister call procurement_router getRecordByJobId "(\"$PUBLIC_PROC_JOB_ID\")" | grep -q "privacy_tier = \"public\""

dfx canister call data_orchestrator validateStoragePolicy "(variant { sovereign }, variant { ipfs })" | grep -q "sovereign data cannot use external storage"
dfx canister call data_orchestrator validateStoragePolicy "(variant { confidential }, variant { cloudflare_r2 })" | grep -q "confidential data cannot use public or external storage"
dfx canister call data_orchestrator validateStoragePolicy "(variant { public_tier }, variant { ipfs })" | grep -q "ok"
dfx canister call data_orchestrator registerAsset "(record {
  asset_id = \"$DATA_ASSET_ID\";
  owner = principal \"$CALLER\";
  privacy_tier = variant { public_tier };
  storage_target = variant { ipfs };
  data_hash = \"hash-public-data\";
  byte_size = 42;
  created_at = 0;
  stage = variant { registered };
  error_message = null;
})"
dfx canister call data_orchestrator getAsset "(\"$DATA_ASSET_ID\")" | grep -q "policy_checked"

dfx canister call sigma_bus_adapter emitEvent "(record {
  event_id = \"event-smoke-001\";
  schema_version = \"1.0.0\";
  emitted_at = \"2026-05-27T00:00:00.000000000Z\";
  expires_at = null;
  privacy_tier = \"public\";
  lens_state = \"none\";
  event_type = \"compute.decision.made\";
  source = record {
    agent_id = \"local:smoke_test\";
    node_id = \"smoke_test\";
    platform = \"icp_canister\";
    location_class = \"sovereign_local\";
  };
  provenance_chain = vec {
    record {
      agent_id = \"local:smoke_test\";
      action = \"originated\";
      timestamp = \"2026-05-27T00:00:00.000000000Z\";
      signature = null;
    };
  };
  routing = record {
    target = \"bus_topic\";
    topic = \"compute.decisions\";
    priority = \"normal\";
    delivery = \"at_least_once\";
  };
  payload_type = \"ComputeDecisionPayload\";
  payload = \"{\\\"job_id\\\":\\\"$JOB_ID\\\",\\\"decision\\\":\\\"approved\\\"}\";
})"
SIGMA_RECENT_OUTPUT="$(dfx canister call sigma_bus_adapter getRecentEvents "(10 : nat)")"
grep "event-smoke-001" <<<"$SIGMA_RECENT_OUTPUT" >/dev/null
dfx canister call sigma_bus_adapter getStats | grep -q "verified"

dfx canister call audit_log recordDecision "(record {
  decision_id = \"decision-smoke-001\";
  job_id = \"$JOB_ID\";
  attempt_number = 1 : nat;
  evaluated_at = 0;
  evaluator = \"smoke_test\";
  cost_breakdown = record {
    local_credits = 10 : nat;
    icp_cycles_estimate = null;
    akash_credits = null;
    golem_credits = null;
    human_review_credits = null;
    total_credits = 10 : nat;
  };
  value_breakdown = record {
    expected_value_credits = 60 : nat;
    science_value_credits = 0 : nat;
    urgency_multiplier_pct = 100 : nat;
    confidence_pct = 90 : nat;
  };
  net_value_credits = 50 : int;
  net_value_is_positive = true;
  integrity_gate = record {
    allowed = true;
    reason = null;
    policy_checks = vec { \"smoke\" };
    checked_at = 0;
  };
  treasury_state_before = record {
    total_capital = 10000 : nat;
    available_capital = 10000 : nat;
    deployed_capital = 0 : nat;
    reserve_floor_credits = null;
    utilization_rate_pct = 0 : nat;
    captured_at = 0;
  };
  provider_selection = null;
  decision = variant { approve_local };
  decision_rationale = \"smoke path stays local\";
  policy_rules_applied = vec { \"privacy_sovereign_local\" };
  overrides = vec {};
  treasury_impact = null;
  icp_cost = null;
  akash_cost = null;
  dream_offload_metadata = null;
  learning_signal = null;
})"
AUDIT_LIST_OUTPUT="$(dfx canister call audit_log listByJob "(\"$JOB_ID\")")"
grep "decision-smoke-001" <<<"$AUDIT_LIST_OUTPUT" >/dev/null

dfx canister call identity_registry getStats
dfx canister call job_market getStats
dfx canister call reputation_engine getRanking "(10 : nat)"
dfx canister call compute_registry getStats
dfx canister call compute_ledger getTotalSupply
dfx canister call capital_pool getScienceDonations
dfx canister call capital_pool getTreasuryPolicy
dfx canister call capital_pool getTreasurySnapshot
dfx canister call capital_pool spendAllowed "(1 : nat)"
dfx canister call governance getConfig
dfx canister call governance propose "(\"capital_pool\", \"integrity_gate.enabled\", \"false\", \"smoke constitutional rejection\")" | grep -q "Constitutional"
dfx canister call governance propose "(\"capital_pool\", \"capital_pool.max_utilization_rate\", \"77\", \"smoke governance parameter update\")"
dfx canister call governance enact "(\"proposal-1\")"
dfx canister call governance getParameter "(\"capital_pool.max_utilization_rate\")" | grep -q "77"
dfx canister call governance canAdvancePhase "(variant { micro_pool })" | grep -q "insufficient completed jobs"
dfx canister call governance getStats | grep -q "enacted = 1"
dfx canister call procurement_router getSpendState
dfx canister call procurement_router getGateLog "(10 : nat)"
dfx canister call data_orchestrator getStats
dfx canister call data_orchestrator getGateLog "(10 : nat)"
dfx canister call sigma_bus_adapter getEventCount
dfx canister call audit_log getStats

echo "SMOKE_OK"
