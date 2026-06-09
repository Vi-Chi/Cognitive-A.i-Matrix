import Array "mo:base/Array";
import HashMap "mo:base/HashMap";
import Iter "mo:base/Iter";
import Principal "mo:base/Principal";
import Text "mo:base/Text";
import Time "mo:base/Time";

persistent actor JobMarket {
  public type JobId = Text;

  public type PrivacyTier = {
    #sovereign;
    #confidential;
    #internal;
    #public_tier;
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

  public type VerificationMethod = {
    #deterministic;
    #statistical_sample;
    #quorum;
    #human_gate;
  };

  public type LifecycleAuditEntry = {
    at : Time.Time;
    actor_principal : ?Principal;
    action : Text;
    note : ?Text;
  };

  public type JobSpec = {
    job_id : JobId;
    posted_by : Principal;
    task_type : Text;
    task_subtype : ?Text;
    description : Text;
    request_summary : ?Text;
    input_descriptor : ?Text;
    required_compute_types : [Text];
    privacy_tier : PrivacyTier;
    preferred_tier : ?Text;
    fallback_allowed : ?Bool;
    budget_credits : Nat;
    deadline_ns : Time.Time;
    expiry_at : ?Time.Time;
    integrity_required : ?Bool;
    human_approval_required : ?Bool;
    audit_required : ?Bool;
    verification_method : VerificationMethod;
    status : JobStatus;
    sigbus_envelope_id : ?Text;
    parent_job_id : ?Text;
    tags : ?[Text];
    lifecycle_audit : ?[LifecycleAuditEntry];
    created_at : Time.Time;
    updated_at : Time.Time;
  };

  public type JobLifecycleRecord = JobSpec;

  public type Bid = {
    bid_id : Text;
    job_id : JobId;
    agent_id : Text;
    agent_principal : Principal;
    price_credits : Nat;
    estimated_completion_ns : Nat;
    submitted_at : Time.Time;
  };

  public type JobAssignment = {
    job_id : JobId;
    assigned_agent_id : Text;
    assigned_principal : Principal;
    agreed_price : Nat;
    accepted_at : Time.Time;
  };

  public type Stats = {
    total : Nat;
    open : Nat;
    inProgress : Nat;
    completed : Nat;
  };

  public type Result<T, E> = {
    #ok : T;
    #err : E;
  };

  type IdentityRegistry = actor {
    verify : shared query (Text) -> async Bool;
  };

  type Ledger = actor {
    lockEscrow : shared (Text, Principal, Nat) -> async { #Ok : (); #Err : Text };
    releaseEscrow : shared (Text) -> async { #Ok : (); #Err : Text };
  };

  type Reputation = actor {
    recordOutcome : shared (OutcomeEvent) -> async { #ok : (); #err : Text };
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

  private stable var stableJobs : [(JobId, JobSpec)] = [];
  private stable var stableBids : [(JobId, [Bid])] = [];
  private stable var stableAssignments : [(JobId, JobAssignment)] = [];
  private stable var identityRegistryId : ?Principal = null;
  private stable var ledgerId : ?Principal = null;
  private stable var reputationId : ?Principal = null;
  private stable var gateLog : [(Time.Time, Text, Bool)] = [];

  private transient let jobs = HashMap.HashMap<JobId, JobSpec>(0, Text.equal, Text.hash);
  private transient let bids = HashMap.HashMap<JobId, [Bid]>(0, Text.equal, Text.hash);
  private transient let assignments = HashMap.HashMap<JobId, JobAssignment>(0, Text.equal, Text.hash);

  system func preupgrade() {
    stableJobs := Iter.toArray(jobs.entries());
    stableBids := Iter.toArray(bids.entries());
    stableAssignments := Iter.toArray(assignments.entries());
  };

  system func postupgrade() {
    for ((id, job) in stableJobs.vals()) { jobs.put(id, job) };
    for ((id, jobBids) in stableBids.vals()) { bids.put(id, jobBids) };
    for ((id, assignment) in stableAssignments.vals()) { assignments.put(id, assignment) };
    stableJobs := [];
    stableBids := [];
    stableAssignments := [];
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

  private func ledgerActor() : ?Ledger {
    switch (ledgerId) {
      case null { null };
      case (?canisterId) {
        let actorRef : Ledger = actor (Principal.toText(canisterId));
        ?actorRef;
      };
    };
  };

  private func reputationActor() : ?Reputation {
    switch (reputationId) {
      case null { null };
      case (?canisterId) {
        let actorRef : Reputation = actor (Principal.toText(canisterId));
        ?actorRef;
      };
    };
  };

  private func minNat(a : Nat, b : Nat) : Nat {
    if (a < b) { a } else { b };
  };

  private func isExternalTarget(target : Text) : Bool {
    target == "external" or target == "external_provider";
  };

  private func appendGateLog(operation : Text, allowed : Bool) {
    let entry = (Time.now(), operation, allowed);
    let next = Array.append<(Time.Time, Text, Bool)>(gateLog, [entry]);
    if (next.size() <= 1000) {
      gateLog := next;
    } else {
      let start = next.size() - 1000;
      gateLog := Array.tabulate<(Time.Time, Text, Bool)>(
        1000,
        func(index : Nat) : (Time.Time, Text, Bool) { next[start + index] },
      );
    };
  };

  private func integrityGate(operation : Text, privacyTier : PrivacyTier, targetCanister : ?Text) : Bool {
    var allowed = true;
    switch (privacyTier, targetCanister) {
      case (#sovereign, ?target) {
        if (isExternalTarget(target)) { allowed := false };
      };
      case _ {};
    };
    if (operation == "memory_leak") { allowed := false };
    appendGateLog(operation, allowed);
    allowed;
  };

  private func hasBid(jobId : JobId, bidId : Text) : ?Bid {
    let existing : [Bid] = switch (bids.get(jobId)) {
      case null { [] };
      case (?values) { values };
    };
    for (bid in existing.vals()) {
      if (bid.bid_id == bidId) {
        return ?bid;
      };
    };
    null;
  };

  private func putStatus(job : JobSpec, status : JobStatus) {
    jobs.put(job.job_id, {
      job_id = job.job_id;
      posted_by = job.posted_by;
      task_type = job.task_type;
      task_subtype = job.task_subtype;
      description = job.description;
      request_summary = job.request_summary;
      input_descriptor = job.input_descriptor;
      required_compute_types = job.required_compute_types;
      privacy_tier = job.privacy_tier;
      preferred_tier = job.preferred_tier;
      fallback_allowed = job.fallback_allowed;
      budget_credits = job.budget_credits;
      deadline_ns = job.deadline_ns;
      expiry_at = job.expiry_at;
      integrity_required = job.integrity_required;
      human_approval_required = job.human_approval_required;
      audit_required = job.audit_required;
      verification_method = job.verification_method;
      status = status;
      sigbus_envelope_id = job.sigbus_envelope_id;
      parent_job_id = job.parent_job_id;
      tags = job.tags;
      lifecycle_audit = job.lifecycle_audit;
      created_at = job.created_at;
      updated_at = Time.now();
    });
  };

  private func validTransition(current : JobStatus, next : JobStatus) : Bool {
    switch (current, next) {
      case (#open, #bidding) { true };
      case (#open, #cancelled) { true };
      case (#bidding, #accepted) { true };
      case (#bidding, #cancelled) { true };
      case (#accepted, #in_progress) { true };
      case (#accepted, #disputed) { true };
      case (#in_progress, #delivered) { true };
      case (#in_progress, #disputed) { true };
      case (#delivered, #verified) { true };
      case (#delivered, #disputed) { true };
      case (#verified, #settled) { true };
      case (#verified, #disputed) { true };
      case (#disputed, #cancelled) { true };
      case _ { false };
    };
  };

  private func completed(status : JobStatus) : Bool {
    switch (status) {
      case (#verified) { true };
      case (#settled) { true };
      case _ { false };
    };
  };

  public shared func configureExchange(
    identityCanister : ?Principal,
    ledgerCanister : ?Principal,
    reputationCanister : ?Principal,
  ) : async Result<(), Text> {
    identityRegistryId := identityCanister;
    ledgerId := ledgerCanister;
    reputationId := reputationCanister;
    #ok(());
  };

  public query func getJob(jobId : JobId) : async ?JobSpec {
    jobs.get(jobId);
  };

  public query func listOpenJobs() : async [JobSpec] {
    Array.filter<JobSpec>(
      Iter.toArray(jobs.vals()),
      func(job : JobSpec) : Bool {
        job.status == #open or job.status == #bidding;
      },
    );
  };

  public query func listJobsByType(taskType : Text) : async [JobSpec] {
    Array.filter<JobSpec>(
      Iter.toArray(jobs.vals()),
      func(job : JobSpec) : Bool {
        job.task_type == taskType;
      },
    );
  };

  public query func getBidsForJob(jobId : JobId) : async [Bid] {
    switch (bids.get(jobId)) {
      case null { [] };
      case (?values) { values };
    };
  };

  public query func getAssignment(jobId : JobId) : async ?JobAssignment {
    assignments.get(jobId);
  };

  public query func getStats() : async Stats {
    var openCount = 0;
    var inProgressCount = 0;
    var completedCount = 0;
    for (job in jobs.vals()) {
      if (job.status == #open or job.status == #bidding) {
        openCount += 1;
      };
      if (job.status == #accepted or job.status == #in_progress) {
        inProgressCount += 1;
      };
      if (completed(job.status)) {
        completedCount += 1;
      };
    };
    {
      total = jobs.size();
      open = openCount;
      inProgress = inProgressCount;
      completed = completedCount;
    };
  };

  public query func getGateLog(limit : Nat) : async [(Time.Time, Text, Bool)] {
    let count = minNat(limit, gateLog.size());
    let start = gateLog.size() - count;
    Array.tabulate<(Time.Time, Text, Bool)>(
      count,
      func(index : Nat) : (Time.Time, Text, Bool) { gateLog[start + index] },
    );
  };

  public shared ({ caller }) func postJob(spec : JobSpec) : async Result<JobId, Text> {
    if (Text.size(spec.job_id) == 0) { return #err("job_id must not be empty") };
    if (Text.size(spec.task_type) == 0) { return #err("task_type must not be empty") };
    if (spec.budget_credits == 0) { return #err("budget_credits must be greater than zero") };
    if (spec.deadline_ns <= Time.now()) { return #err("deadline must be in the future") };
    if (spec.posted_by != caller) { return #err("posted_by must match caller") };
    switch (jobs.get(spec.job_id)) {
      case (?_) { return #err("job_id already exists") };
      case null {};
    };
    if (not integrityGate("post_job", spec.privacy_tier, null)) {
      return #err("integrity gate blocked operation");
    };

    let now = Time.now();
    jobs.put(spec.job_id, {
      job_id = spec.job_id;
      posted_by = caller;
      task_type = spec.task_type;
      task_subtype = spec.task_subtype;
      description = spec.description;
      request_summary = spec.request_summary;
      input_descriptor = spec.input_descriptor;
      required_compute_types = spec.required_compute_types;
      privacy_tier = spec.privacy_tier;
      preferred_tier = spec.preferred_tier;
      fallback_allowed = spec.fallback_allowed;
      budget_credits = spec.budget_credits;
      deadline_ns = spec.deadline_ns;
      expiry_at = spec.expiry_at;
      integrity_required = spec.integrity_required;
      human_approval_required = spec.human_approval_required;
      audit_required = spec.audit_required;
      verification_method = spec.verification_method;
      status = #open;
      sigbus_envelope_id = spec.sigbus_envelope_id;
      parent_job_id = spec.parent_job_id;
      tags = spec.tags;
      lifecycle_audit = spec.lifecycle_audit;
      created_at = now;
      updated_at = now;
    });
    #ok(spec.job_id);
  };

  public shared func submitBid(bid : Bid) : async Result<(), Text> {
    switch (jobs.get(bid.job_id)) {
      case null { #err("job not found") };
      case (?job) {
        if (not (job.status == #open or job.status == #bidding)) {
          return #err("job is not open for bids");
        };
        if (Text.size(bid.bid_id) == 0) { return #err("bid_id must not be empty") };
        if (Text.size(bid.agent_id) == 0) { return #err("agent_id must not be empty") };
        if (bid.price_credits == 0) { return #err("price_credits must be greater than zero") };
        if (bid.price_credits > job.budget_credits) { return #err("bid exceeds job budget") };
        switch (identityActor()) {
          case null {};
          case (?identity) {
            if (not (await identity.verify(bid.agent_id))) {
              return #err("agent is not registered or active");
            };
          };
        };

        let existing : [Bid] = switch (bids.get(bid.job_id)) {
          case null { [] };
          case (?values) { values };
        };
        bids.put(bid.job_id, Array.append<Bid>(existing, [bid]));
        if (job.status == #open) {
          putStatus(job, #bidding);
        };
        #ok(());
      };
    };
  };

  public shared ({ caller }) func acceptBid(jobId : JobId, bidId : Text) : async Result<(), Text> {
    switch (jobs.get(jobId), hasBid(jobId, bidId)) {
      case (null, _) { #err("job not found") };
      case (_, null) { #err("bid not found") };
      case (?job, ?bid) {
        if (job.posted_by != caller) { return #err("only job poster can accept bid") };
        if (not (job.status == #bidding)) { return #err("job must be bidding") };
        if (not integrityGate("accept_bid", job.privacy_tier, null)) {
          return #err("integrity gate blocked operation");
        };
        switch (ledgerActor()) {
          case null {};
          case (?ledger) {
            switch (await ledger.lockEscrow(jobId, bid.agent_principal, bid.price_credits)) {
              case (#Ok(())) {};
              case (#Err(message)) { return #err("ledger escrow failed: " # message) };
            };
          };
        };
        assignments.put(jobId, {
          job_id = jobId;
          assigned_agent_id = bid.agent_id;
          assigned_principal = bid.agent_principal;
          agreed_price = bid.price_credits;
          accepted_at = Time.now();
        });
        putStatus(job, #accepted);
        #ok(());
      };
    };
  };

  public shared ({ caller }) func updateStatus(jobId : JobId, newStatus : JobStatus) : async Result<(), Text> {
    switch (jobs.get(jobId)) {
      case null { #err("job not found") };
      case (?job) {
        let assignment = assignments.get(jobId);
        let assignedCaller = switch (assignment) {
          case null { false };
          case (?value) { value.assigned_principal == caller };
        };
        if (not (job.posted_by == caller or assignedCaller)) {
          return #err("only poster or assigned agent can update status");
        };
        if (not validTransition(job.status, newStatus)) {
          return #err("invalid status transition");
        };
        if (not integrityGate("update_status", job.privacy_tier, null)) {
          return #err("integrity gate blocked operation");
        };
        if (newStatus == #settled) {
          switch (ledgerActor()) {
            case null {};
            case (?ledger) {
              switch (await ledger.releaseEscrow(jobId)) {
                case (#Ok(())) {};
                case (#Err(message)) { return #err("ledger release failed: " # message) };
              };
            };
          };
          switch (reputationActor(), assignment) {
            case (?rep, ?value) {
              ignore await rep.recordOutcome({
                job_id = jobId;
                agent_id = value.assigned_agent_id;
                outcome = #success;
                credits_earned = value.agreed_price;
                latency_ns = 0;
                quality_score = 1.0;
                recorded_at = Time.now();
              });
            };
            case _ {};
          };
        };
        putStatus(job, newStatus);
        #ok(());
      };
    };
  };

  public shared ({ caller }) func cancelJob(jobId : JobId) : async Result<(), Text> {
    switch (jobs.get(jobId)) {
      case null { #err("job not found") };
      case (?job) {
        if (job.posted_by != caller) { return #err("only poster can cancel job") };
        if (not (job.status == #open or job.status == #bidding)) {
          return #err("only open or bidding jobs can be cancelled");
        };
        if (not integrityGate("cancel_job", job.privacy_tier, null)) {
          return #err("integrity gate blocked operation");
        };
        putStatus(job, #cancelled);
        #ok(());
      };
    };
  };
};
