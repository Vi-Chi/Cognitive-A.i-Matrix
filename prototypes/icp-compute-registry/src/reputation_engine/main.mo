import Array "mo:base/Array";
import Float "mo:base/Float";
import HashMap "mo:base/HashMap";
import Iter "mo:base/Iter";
import Nat "mo:base/Nat";
import Order "mo:base/Order";
import Principal "mo:base/Principal";
import Text "mo:base/Text";
import Time "mo:base/Time";

persistent actor ReputationEngine {
  public type Outcome = {
    #success;
    #failure;
    #dispute_won;
    #dispute_lost;
  };

  public type ReputationRecord = {
    agent_id : Text;
    score : Float;
    jobs_completed : Nat;
    jobs_failed : Nat;
    jobs_disputed : Nat;
    total_credits_earned : Nat;
    last_updated : Time.Time;
  };

  public type OutcomeEvent = {
    job_id : Text;
    agent_id : Text;
    outcome : Outcome;
    credits_earned : Nat;
    latency_ns : Nat;
    quality_score : Float;
    recorded_at : Time.Time;
  };

  public type Endorsement = {
    from_agent : Text;
    to_agent : Text;
    context : Text;
    weight : Float;
    created_at : Time.Time;
  };

  public type Result<T, E> = {
    #ok : T;
    #err : E;
  };

  type IdentityRegistry = actor {
    verify : shared query (Text) -> async Bool;
  };

  private stable var stableRecords : [(Text, ReputationRecord)] = [];
  private stable var stableHistory : [(Text, [OutcomeEvent])] = [];
  private stable var stableEndorsements : [(Text, [Endorsement])] = [];
  private stable var identityRegistryId : ?Principal = null;

  private transient let records = HashMap.HashMap<Text, ReputationRecord>(0, Text.equal, Text.hash);
  private transient let history = HashMap.HashMap<Text, [OutcomeEvent]>(0, Text.equal, Text.hash);
  private transient let endorsements = HashMap.HashMap<Text, [Endorsement]>(0, Text.equal, Text.hash);

  system func preupgrade() {
    stableRecords := Iter.toArray(records.entries());
    stableHistory := Iter.toArray(history.entries());
    stableEndorsements := Iter.toArray(endorsements.entries());
  };

  system func postupgrade() {
    for ((id, record) in stableRecords.vals()) { records.put(id, record) };
    for ((id, events) in stableHistory.vals()) { history.put(id, events) };
    for ((id, values) in stableEndorsements.vals()) { endorsements.put(id, values) };
    stableRecords := [];
    stableHistory := [];
    stableEndorsements := [];
  };

  private func identityActor() : ?IdentityRegistry {
    switch (identityRegistryId) {
      case null { null };
      case (?canisterId) {
        let actorRef : IdentityRegistry = actor (Principal.toText(canisterId));
        ?actorRef;
      };
    };
  };

  private func clamp(value : Float) : Float {
    if (value < 0.0) {
      0.0;
    } else if (value > 1.0) {
      1.0;
    } else {
      value;
    };
  };

  private func minNat(a : Nat, b : Nat) : Nat {
    if (a < b) { a } else { b };
  };

  private func baseRecord(agentId : Text) : ReputationRecord {
    {
      agent_id = agentId;
      score = 0.5;
      jobs_completed = 0;
      jobs_failed = 0;
      jobs_disputed = 0;
      total_credits_earned = 0;
      last_updated = Time.now();
    };
  };

  private func recalculate(record : ReputationRecord, event : OutcomeEvent) : ReputationRecord {
    let completed = record.jobs_completed + (switch (event.outcome) { case (#success) 1; case (#dispute_won) 1; case _ 0 });
    let failed = record.jobs_failed + (switch (event.outcome) { case (#failure) 1; case (#dispute_lost) 1; case _ 0 });
    let disputed = record.jobs_disputed + (switch (event.outcome) { case (#dispute_won) 1; case (#dispute_lost) 1; case _ 0 });
    let total = completed + failed + disputed;
    let base = if (total == 0) {
      0.5;
    } else {
      Float.fromInt(completed) / Float.fromInt(total);
    };
    let latencyAdjusted = if (event.latency_ns == 0) {
      base;
    } else if (event.latency_ns < 1_000_000_000) {
      base + 0.02;
    } else if (event.latency_ns > 2_000_000_000) {
      base - 0.05;
    } else {
      base;
    };
    let quality = clamp(event.quality_score);
    let qualityAdjusted = latencyAdjusted * (0.8 + (0.2 * quality));
    {
      agent_id = record.agent_id;
      score = clamp(qualityAdjusted);
      jobs_completed = completed;
      jobs_failed = failed;
      jobs_disputed = disputed;
      total_credits_earned = record.total_credits_earned + event.credits_earned;
      last_updated = Time.now();
    };
  };

  private func decayRecord(record : ReputationRecord, now : Time.Time) : ReputationRecord {
    let monthNs : Int = 30 * 24 * 60 * 60 * 1_000_000_000;
    let elapsed = now - record.last_updated;
    if (elapsed < monthNs) {
      return record;
    };
    let periods = Float.fromInt(elapsed / monthNs);
    let factor = periods * 0.01;
    let target = 0.5;
    let moved = if (record.score > target) {
      record.score - ((record.score - target) * factor);
    } else {
      record.score + ((target - record.score) * factor);
    };
    {
      agent_id = record.agent_id;
      score = clamp(moved);
      jobs_completed = record.jobs_completed;
      jobs_failed = record.jobs_failed;
      jobs_disputed = record.jobs_disputed;
      total_credits_earned = record.total_credits_earned;
      last_updated = now;
    };
  };

  public shared func configureExchange(identityCanister : ?Principal) : async Result<(), Text> {
    identityRegistryId := identityCanister;
    #ok(());
  };

  public query func getReputation(agentId : Text) : async ?ReputationRecord {
    records.get(agentId);
  };

  public query func getHistory(agentId : Text) : async [OutcomeEvent] {
    switch (history.get(agentId)) {
      case null { [] };
      case (?events) { events };
    };
  };

  public query func getEndorsements(agentId : Text) : async [Endorsement] {
    switch (endorsements.get(agentId)) {
      case null { [] };
      case (?values) { values };
    };
  };

  public query func getRanking(limit : Nat) : async [ReputationRecord] {
    let sorted = Array.sort<ReputationRecord>(
      Iter.toArray(records.vals()),
      func(a : ReputationRecord, b : ReputationRecord) : Order.Order {
        if (a.score > b.score) { #less } else if (a.score < b.score) { #greater } else { #equal };
      },
    );
    Array.tabulate<ReputationRecord>(
      minNat(limit, sorted.size()),
      func(index : Nat) : ReputationRecord { sorted[index] },
    );
  };

  public shared func recordOutcome(event : OutcomeEvent) : async Result<(), Text> {
    if (Text.size(event.job_id) == 0) { return #err("job_id must not be empty") };
    if (Text.size(event.agent_id) == 0) { return #err("agent_id must not be empty") };
    if (event.quality_score < 0.0 or event.quality_score > 1.0) {
      return #err("quality_score must be between 0.0 and 1.0");
    };
    let current = switch (records.get(event.agent_id)) {
      case null { baseRecord(event.agent_id) };
      case (?record) { record };
    };
    let updated = recalculate(current, event);
    records.put(event.agent_id, updated);
    let events : [OutcomeEvent] = switch (history.get(event.agent_id)) {
      case null { [] };
      case (?values) { values };
    };
    history.put(event.agent_id, Array.append<OutcomeEvent>(events, [event]));
    #ok(());
  };

  public shared func endorse(endorsement : Endorsement) : async Result<(), Text> {
    if (Text.size(endorsement.from_agent) == 0 or Text.size(endorsement.to_agent) == 0) {
      return #err("endorsement agents must not be empty");
    };
    if (endorsement.weight < 0.0 or endorsement.weight > 1.0) {
      return #err("endorsement weight must be between 0.0 and 1.0");
    };
    switch (identityActor()) {
      case null {};
      case (?identity) {
        if (not (await identity.verify(endorsement.from_agent))) {
          return #err("from_agent is not registered or active");
        };
      };
    };
    let values : [Endorsement] = switch (endorsements.get(endorsement.to_agent)) {
      case null { [] };
      case (?existing) { existing };
    };
    endorsements.put(endorsement.to_agent, Array.append<Endorsement>(values, [endorsement]));
    #ok(());
  };

  public shared func applyDecay() : async () {
    let now = Time.now();
    for ((agentId, record) in records.entries()) {
      records.put(agentId, decayRecord(record, now));
    };
  };
};
