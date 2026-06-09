import Array "mo:base/Array";
import Text "mo:base/Text";
import Time "mo:base/Time";

persistent actor AuditLog {
  public type PrivacyTier = {
    #sovereign;
    #confidential;
    #internal;
    #public_tier;
  };

  public type ComputeDecision = {
    #approve_local;
    #approve_external;
    #defer;
    #reject;
    #human_review;
    #simulate;
  };

  public type CostBreakdown = {
    local_credits : Nat;
    icp_cycles_estimate : ?Nat;
    akash_credits : ?Nat;
    golem_credits : ?Nat;
    human_review_credits : ?Nat;
    total_credits : Nat;
  };

  public type ValueBreakdown = {
    expected_value_credits : Nat;
    science_value_credits : Nat;
    urgency_multiplier_pct : Nat;
    confidence_pct : Nat;
  };

  public type IntegrityGateResult = {
    allowed : Bool;
    reason : ?Text;
    policy_checks : [Text];
    checked_at : Time.Time;
  };

  public type TreasurySnapshot = {
    total_capital : Nat;
    available_capital : Nat;
    deployed_capital : Nat;
    reserve_floor_credits : ?Nat;
    utilization_rate_pct : Nat;
    captured_at : Time.Time;
  };

  public type ProviderSelectionRecord = {
    provider_id : ?Text;
    provider_class : Text;
    privacy_tier : PrivacyTier;
    estimated_completion_ns : ?Nat;
    quoted_credits : ?Nat;
    rationale : Text;
  };

  public type TreasuryImpact = {
    escrow_delta_credits : Int;
    reserve_delta_credits : Int;
    projected_available_credits : Nat;
  };

  public type IcpCost = {
    cycles_estimate : Nat;
    credits_equivalent : Nat;
    subnet_type : ?Text;
  };

  public type AkashCost = {
    provider_quote_id : ?Text;
    credits_equivalent : Nat;
    lease_duration_ns : ?Nat;
  };

  public type DreamOffloadMetadata = {
    dream_id : ?Text;
    matrix_thread_id : ?Text;
    local_summary_hash : ?Text;
  };

  public type LearningSignal = {
    outcome_recorded : Bool;
    quality_score : ?Float;
    notes : ?Text;
  };

  public type ComputeDecisionRecord = {
    decision_id : Text;
    job_id : Text;
    attempt_number : Nat;
    evaluated_at : Time.Time;
    evaluator : Text;
    cost_breakdown : CostBreakdown;
    value_breakdown : ValueBreakdown;
    net_value_credits : Int;
    net_value_is_positive : Bool;
    integrity_gate : IntegrityGateResult;
    treasury_state_before : TreasurySnapshot;
    provider_selection : ?ProviderSelectionRecord;
    decision : ComputeDecision;
    decision_rationale : Text;
    policy_rules_applied : [Text];
    overrides : [Text];
    treasury_impact : ?TreasuryImpact;
    icp_cost : ?IcpCost;
    akash_cost : ?AkashCost;
    dream_offload_metadata : ?DreamOffloadMetadata;
    learning_signal : ?LearningSignal;
  };

  public type Stats = {
    total : Nat;
    allowed : Nat;
    rejected : Nat;
  };

  public type Result<T, E> = {
    #ok : T;
    #err : E;
  };

  private stable var decision_log : [ComputeDecisionRecord] = [];

  private func minNat(a : Nat, b : Nat) : Nat {
    if (a < b) { a } else { b };
  };

  private func exists(decisionId : Text) : Bool {
    for (record in decision_log.vals()) {
      if (record.decision_id == decisionId) {
        return true;
      };
    };
    false;
  };

  public shared func recordDecision(record : ComputeDecisionRecord) : async Result<Text, Text> {
    if (Text.size(record.decision_id) == 0) {
      return #err("decision_id must not be empty");
    };
    if (Text.size(record.job_id) == 0) {
      return #err("job_id must not be empty");
    };
    if (Text.size(record.decision_rationale) == 0) {
      return #err("decision_rationale must not be empty");
    };
    if (exists(record.decision_id)) {
      return #err("decision_id already recorded");
    };
    decision_log := Array.append<ComputeDecisionRecord>(decision_log, [record]);
    #ok(record.decision_id);
  };

  public query func getDecision(decisionId : Text) : async ?ComputeDecisionRecord {
    for (record in decision_log.vals()) {
      if (record.decision_id == decisionId) {
        return ?record;
      };
    };
    null;
  };

  public query func listDecisions(limit : Nat) : async [ComputeDecisionRecord] {
    let count = minNat(limit, decision_log.size());
    let start = decision_log.size() - count;
    Array.tabulate<ComputeDecisionRecord>(
      count,
      func(index : Nat) : ComputeDecisionRecord { decision_log[start + index] },
    );
  };

  public query func listByJob(jobId : Text) : async [ComputeDecisionRecord] {
    Array.filter<ComputeDecisionRecord>(
      decision_log,
      func(record : ComputeDecisionRecord) : Bool { record.job_id == jobId },
    );
  };

  public query func getStats() : async Stats {
    var allowed = 0;
    var rejected = 0;
    for (record in decision_log.vals()) {
      if (record.integrity_gate.allowed) {
        allowed += 1;
      } else {
        rejected += 1;
      };
    };
    {
      total = decision_log.size();
      allowed = allowed;
      rejected = rejected;
    };
  };
};
