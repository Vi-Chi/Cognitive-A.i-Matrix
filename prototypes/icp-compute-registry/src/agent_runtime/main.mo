import Array "mo:base/Array";
import HashMap "mo:base/HashMap";
import Iter "mo:base/Iter";
import Principal "mo:base/Principal";
import Text "mo:base/Text";
import Time "mo:base/Time";

persistent actor AgentRuntime {
  public type AgentConfig = {
    agent_id : Text;
    operator : Principal;
    registry_canister : Principal;
    market_canister : Principal;
    reputation_canister : Principal;
    max_concurrent_jobs : Nat;
    auto_bid : Bool;
    min_job_budget : Nat;
    accepted_task_types : [Text];
  };

  public type LocalJobState = {
    job_id : Text;
    status : Text;
    started_at : Time.Time;
    last_update : Time.Time;
    result_hash : ?Text;
  };

  public type Summary = {
    agent_id : Text;
    active_jobs : Nat;
    total_run : Nat;
    credits_earned : Nat;
  };

  public type Result<T, E> = {
    #ok : T;
    #err : E;
  };

  public type JobStatus = {
    #open;
    #bidding;
    #accepted;
    #in_progress;
    #delivered;
    #verified;
    #settled;
    #disputed;
    #cancelled;
  };

  public type Outcome = {
    #success;
    #failure;
    #dispute_won;
    #dispute_lost;
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

  type JobMarket = actor {
    updateStatus : shared (Text, JobStatus) -> async { #ok : (); #err : Text };
  };

  type Reputation = actor {
    recordOutcome : shared (OutcomeEvent) -> async { #ok : (); #err : Text };
  };

  private stable var config : ?AgentConfig = null;
  private stable var stableJobs : [(Text, LocalJobState)] = [];
  private stable var totalJobsRun : Nat = 0;
  private stable var totalCreditsEarned : Nat = 0;
  private stable var registryCanister : ?Principal = null;
  private stable var marketCanister : ?Principal = null;
  private stable var reputationCanister : ?Principal = null;

  private transient let localJobs = HashMap.HashMap<Text, LocalJobState>(0, Text.equal, Text.hash);

  system func preupgrade() {
    stableJobs := Iter.toArray(localJobs.entries());
  };

  system func postupgrade() {
    for ((jobId, state) in stableJobs.vals()) {
      localJobs.put(jobId, state);
    };
    stableJobs := [];
  };

  private func contains(xs : [Text], needle : Text) : Bool {
    for (value in xs.vals()) {
      if (value == needle) { return true };
    };
    false;
  };

  private func activeCount() : Nat {
    var count = 0;
    for (state in localJobs.vals()) {
      if (state.status == "accepted" or state.status == "in_progress") {
        count += 1;
      };
    };
    count;
  };

  private func marketActor() : ?JobMarket {
    switch (marketCanister) {
      case null { null };
      case (?canisterId) {
        let actorRef : JobMarket = actor (Principal.toText(canisterId));
        ?actorRef;
      };
    };
  };

  private func reputationActor() : ?Reputation {
    switch (reputationCanister) {
      case null { null };
      case (?canisterId) {
        let actorRef : Reputation = actor (Principal.toText(canisterId));
        ?actorRef;
      };
    };
  };

  private func requireConfig(caller : Principal) : Result<AgentConfig, Text> {
    switch (config) {
      case null { #err("agent runtime is not configured") };
      case (?cfg) {
        if (cfg.operator != caller) {
          #err("only configured operator can mutate runtime");
        } else {
          #ok(cfg);
        };
      };
    };
  };

  public shared func configureExchange(
    identityCanister : Principal,
    jobMarketCanister : Principal,
    repCanister : Principal,
  ) : async Result<(), Text> {
    registryCanister := ?identityCanister;
    marketCanister := ?jobMarketCanister;
    reputationCanister := ?repCanister;
    #ok(());
  };

  public query func getConfig() : async ?AgentConfig {
    config;
  };

  public query func getActiveJobs() : async [LocalJobState] {
    Array.filter<LocalJobState>(
      Iter.toArray(localJobs.vals()),
      func(state : LocalJobState) : Bool {
        state.status == "accepted" or state.status == "in_progress";
      },
    );
  };

  public query func getJobState(jobId : Text) : async ?LocalJobState {
    localJobs.get(jobId);
  };

  public query func getSummary() : async Summary {
    let agentId = switch (config) {
      case null { "" };
      case (?cfg) { cfg.agent_id };
    };
    {
      agent_id = agentId;
      active_jobs = activeCount();
      total_run = totalJobsRun;
      credits_earned = totalCreditsEarned;
    };
  };

  public shared ({ caller }) func configure(newConfig : AgentConfig) : async Result<(), Text> {
    switch (config) {
      case (?_) { return #err("agent runtime already configured") };
      case null {};
    };
    if (newConfig.operator != caller) { return #err("operator must match caller") };
    if (Text.size(newConfig.agent_id) == 0) { return #err("agent_id must not be empty") };
    if (newConfig.max_concurrent_jobs == 0) {
      return #err("max_concurrent_jobs must be greater than zero");
    };
    if (newConfig.accepted_task_types.size() == 0) {
      return #err("accepted_task_types must not be empty");
    };
    config := ?newConfig;
    registryCanister := ?newConfig.registry_canister;
    marketCanister := ?newConfig.market_canister;
    reputationCanister := ?newConfig.reputation_canister;
    #ok(());
  };

  public shared ({ caller }) func acceptJob(jobId : Text, taskType : Text) : async Result<(), Text> {
    switch (requireConfig(caller)) {
      case (#err(message)) { #err(message) };
      case (#ok(cfg)) {
        if (Text.size(jobId) == 0) { return #err("job_id must not be empty") };
        if (not contains(cfg.accepted_task_types, taskType)) {
          return #err("task type not accepted by this agent");
        };
        if (activeCount() >= cfg.max_concurrent_jobs) {
          return #err("max_concurrent_jobs reached");
        };
        let now = Time.now();
        localJobs.put(jobId, {
          job_id = jobId;
          status = "in_progress";
          started_at = now;
          last_update = now;
          result_hash = null;
        });
        switch (marketActor()) {
          case null {};
          case (?market) {
            switch (await market.updateStatus(jobId, #in_progress)) {
              case (#ok(())) {};
              case (#err(message)) { return #err("market status update failed: " # message) };
            };
          };
        };
        #ok(());
      };
    };
  };

  public shared ({ caller }) func reportCompletion(
    jobId : Text,
    resultHash : Text,
    qualityScore : Float,
  ) : async Result<(), Text> {
    switch (requireConfig(caller)) {
      case (#err(message)) { #err(message) };
      case (#ok(cfg)) {
        if (Text.size(resultHash) == 0) { return #err("resultHash must not be empty") };
        if (qualityScore < 0.0 or qualityScore > 1.0) {
          return #err("qualityScore must be between 0.0 and 1.0");
        };
        switch (localJobs.get(jobId)) {
          case null { return #err("job not tracked by this runtime") };
          case (?state) {
            localJobs.put(jobId, {
              job_id = state.job_id;
              status = "delivered";
              started_at = state.started_at;
              last_update = Time.now();
              result_hash = ?resultHash;
            });
          };
        };
        switch (marketActor()) {
          case null {};
          case (?market) {
            switch (await market.updateStatus(jobId, #delivered)) {
              case (#ok(())) {};
              case (#err(message)) { return #err("market status update failed: " # message) };
            };
          };
        };
        switch (reputationActor()) {
          case null {};
          case (?rep) {
            ignore await rep.recordOutcome({
              job_id = jobId;
              agent_id = cfg.agent_id;
              outcome = #success;
              credits_earned = 0;
              latency_ns = 0;
              quality_score = qualityScore;
              recorded_at = Time.now();
            });
          };
        };
        totalJobsRun += 1;
        #ok(());
      };
    };
  };

  public shared ({ caller }) func reportFailure(jobId : Text, reason : Text) : async Result<(), Text> {
    switch (requireConfig(caller)) {
      case (#err(message)) { #err(message) };
      case (#ok(cfg)) {
        switch (localJobs.get(jobId)) {
          case null { return #err("job not tracked by this runtime") };
          case (?state) {
            localJobs.put(jobId, {
              job_id = state.job_id;
              status = "failed:" # reason;
              started_at = state.started_at;
              last_update = Time.now();
              result_hash = state.result_hash;
            });
          };
        };
        switch (marketActor()) {
          case null {};
          case (?market) {
            ignore await market.updateStatus(jobId, #disputed);
          };
        };
        switch (reputationActor()) {
          case null {};
          case (?rep) {
            ignore await rep.recordOutcome({
              job_id = jobId;
              agent_id = cfg.agent_id;
              outcome = #failure;
              credits_earned = 0;
              latency_ns = 0;
              quality_score = 0.0;
              recorded_at = Time.now();
            });
          };
        };
        #ok(());
      };
    };
  };
};
