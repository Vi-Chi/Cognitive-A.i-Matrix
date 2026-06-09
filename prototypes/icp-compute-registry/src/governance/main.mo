import Array "mo:base/Array";
import Int "mo:base/Int";
import Nat "mo:base/Nat";
import Principal "mo:base/Principal";
import Text "mo:base/Text";
import Time "mo:base/Time";

persistent actor Governance {
  public type ProposalId = Text;
  public type ParameterKey = Text;
  public type ParameterValue = Text;

  public type ProposalStatus = {
    #pending;
    #approved;
    #rejected;
    #enacted;
    #expired;
  };

  public type PoolPhase = {
    #simulation;
    #micro_pool;
    #open_pool;
    #institutional;
  };

  public type Proposal = {
    proposal_id : ProposalId;
    target_canister : Text;
    parameter : ParameterKey;
    current_value : ParameterValue;
    proposed_value : ParameterValue;
    justification : Text;
    proposed_by : Principal;
    proposed_at : Time.Time;
    status : ProposalStatus;
    enacted_at : ?Time.Time;
    approved_by : [Principal];
    rejected_by : [Principal];
  };

  public type PhaseAdvanceRequirements = {
    min_jobs_completed : Nat;
    zero_integrity_failures_days : Nat;
    external_audit_required : Bool;
    multisig_required : Bool;
  };

  public type GovernanceConfig = {
    version : Text;
    admin : Principal;
    authorized : [Principal];
    required_approvals : Nat;
    proposal_expiry_ns : Nat;
  };

  public type IntegrityAlert = {
    alert_id : Text;
    trigger_event_id : Text;
    canister : Text;
    operation : Text;
    veto_exercised : Bool;
    economic_pressure_detected : Bool;
    recorded_at : Time.Time;
  };

  public type Stats = {
    total_proposals : Nat;
    enacted : Nat;
    pending : Nat;
    integrity_alerts : Nat;
    current_phase : PoolPhase;
  };

  public type Result<T, E> = {
    #ok : T;
    #err : E;
  };

  type CapitalPool = actor {
    setPhase : shared PoolPhase -> async Result<(), Text>;
    setMaxUtilizationRate : shared Nat -> async Result<(), Text>;
    setUnderwritingFeeRate : shared Nat -> async Result<(), Text>;
    setScienceAllocationRate : shared Nat -> async Result<(), Text>;
    setMicroPoolCap : shared Nat -> async Result<(), Text>;
  };

  type SigmaBus = actor {
    emitEvent : shared SigmaBusEnvelope -> async Result<Text, Text>;
  };

  type Source = {
    agent_id : Text;
    node_id : Text;
    platform : Text;
    location_class : Text;
  };

  type ProvenanceEntry = {
    agent_id : Text;
    action : Text;
    timestamp : Text;
    signature : ?Text;
  };

  type Routing = {
    target : Text;
    topic : Text;
    priority : Text;
    delivery : Text;
  };

  type SigmaBusEnvelope = {
    event_id : Text;
    schema_version : Text;
    emitted_at : Text;
    expires_at : ?Text;
    privacy_tier : Text;
    lens_state : Text;
    event_type : Text;
    source : Source;
    provenance_chain : [ProvenanceEntry];
    routing : Routing;
    payload_type : Text;
    payload : Text;
  };

  private stable var configVersion : Text = "v0_single_admin";
  private stable var admin : ?Principal = null;
  private stable var authorized : [Principal] = [];
  private stable var requiredApprovals : Nat = 1;
  private stable var proposalExpiryNs : Nat = 604_800_000_000_000;
  private stable var proposals : [Proposal] = [];
  private stable var currentPhase : PoolPhase = #simulation;
  private stable var integrityAlerts : [IntegrityAlert] = [];
  private stable var parameterRegistry : [(ParameterKey, ParameterValue)] = [
    ("capital_pool.phase", "simulation"),
    ("capital_pool.max_utilization_rate", "80"),
    ("capital_pool.underwriting_fee_rate", "10"),
    ("capital_pool.science_allocation_rate", "5"),
    ("capital_pool.micro_pool_cap", "100000000"),
    ("procurement_router.max_daily_spend_credits", "100000"),
  ];
  private stable var jobsCompletedCount : Nat = 0;
  private stable var integrityFailuresCount : Nat = 0;
  private stable var externalAuditConfirmed : Bool = false;
  private stable var externalAuditRef : ?Text = null;
  private stable var capitalPoolCanister : ?Principal = null;
  private stable var sigmaBusCanister : ?Principal = null;
  private stable var auditLogCanister : ?Principal = null;
  private stable var nextProposalId : Nat = 0;

  private func anonymousPrincipal() : Principal {
    Principal.fromText("2vxsx-fae");
  };

  private func effectiveAdmin() : Principal {
    switch (admin) {
      case (?principal) { principal };
      case null { anonymousPrincipal() };
    };
  };

  private func isAdmin(caller : Principal) : Bool {
    switch (admin) {
      case (?principal) { caller == principal };
      case null { false };
    };
  };

  private func ensureAdmin(caller : Principal) {
    switch (admin) {
      case null { admin := ?caller };
      case _ {};
    };
  };

  private func containsPrincipal(values : [Principal], principal : Principal) : Bool {
    for (value in values.vals()) {
      if (value == principal) {
        return true;
      };
    };
    false;
  };

  private func isAuthorized(caller : Principal) : Bool {
    isAdmin(caller) or containsPrincipal(authorized, caller);
  };

  private func requireAuthorized(caller : Principal) : Result<(), Text> {
    ensureAdmin(caller);
    if (isAuthorized(caller)) { #ok(()) } else { #err("not authorized") };
  };

  private func requireAdmin(caller : Principal) : Result<(), Text> {
    ensureAdmin(caller);
    if (isAdmin(caller)) { #ok(()) } else { #err("admin only") };
  };

  private func proposalExpired(proposal : Proposal) : Bool {
    proposal.status == #pending and Time.now() > proposal.proposed_at + proposalExpiryNs;
  };

  private func statusMatches(status : ?ProposalStatus, proposal : Proposal) : Bool {
    switch (status) {
      case null { true };
      case (?wanted) { proposal.status == wanted };
    };
  };

  private func findProposal(proposalId : ProposalId) : ?Proposal {
    for (proposal in proposals.vals()) {
      if (proposal.proposal_id == proposalId) {
        return ?proposal;
      };
    };
    null;
  };

  private func replaceProposal(next : Proposal) {
    proposals := Array.map<Proposal, Proposal>(
      proposals,
      func(proposal : Proposal) : Proposal {
        if (proposal.proposal_id == next.proposal_id) { next } else { proposal };
      },
    );
  };

  private func getParameterValue(key : ParameterKey) : ?ParameterValue {
    for ((paramKey, value) in parameterRegistry.vals()) {
      if (paramKey == key) {
        return ?value;
      };
    };
    null;
  };

  private func putParameterValue(key : ParameterKey, value : ParameterValue) {
    var found = false;
    let updated = Array.map<(ParameterKey, ParameterValue), (ParameterKey, ParameterValue)>(
      parameterRegistry,
      func(entry : (ParameterKey, ParameterValue)) : (ParameterKey, ParameterValue) {
        if (entry.0 == key) {
          found := true;
          (key, value);
        } else {
          entry;
        };
      },
    );
    parameterRegistry := if (found) {
      updated;
    } else {
      Array.append<(ParameterKey, ParameterValue)>(updated, [(key, value)]);
    };
  };

  private func nextId(prefix : Text) : Text {
    nextProposalId += 1;
    prefix # "-" # Nat.toText(nextProposalId);
  };

  private func phaseText(phase : PoolPhase) : Text {
    switch (phase) {
      case (#simulation) { "simulation" };
      case (#micro_pool) { "micro_pool" };
      case (#open_pool) { "open_pool" };
      case (#institutional) { "institutional" };
    };
  };

  private func parsePhase(value : Text) : ?PoolPhase {
    if (value == "simulation") { return ?#simulation };
    if (value == "micro_pool") { return ?#micro_pool };
    if (value == "open_pool") { return ?#open_pool };
    if (value == "institutional") { return ?#institutional };
    null;
  };

  private func containsIntegrityGateParameter(target : Text, parameter : Text) : Bool {
    Text.contains(target, #text "integrity_gate") or Text.contains(parameter, #text "integrity_gate");
  };

  private func canisterActor() : ?CapitalPool {
    switch (capitalPoolCanister) {
      case null { null };
      case (?canisterId) {
        let actorRef : CapitalPool = actor (Principal.toText(canisterId));
        ?actorRef;
      };
    };
  };

  private func sigmaActor() : ?SigmaBus {
    switch (sigmaBusCanister) {
      case null { null };
      case (?canisterId) {
        let actorRef : SigmaBus = actor (Principal.toText(canisterId));
        ?actorRef;
      };
    };
  };

  private func phaseRequirements(targetPhase : PoolPhase) : PhaseAdvanceRequirements {
    switch (targetPhase) {
      case (#simulation) {
        { min_jobs_completed = 0; zero_integrity_failures_days = 0; external_audit_required = false; multisig_required = false };
      };
      case (#micro_pool) {
        { min_jobs_completed = 100; zero_integrity_failures_days = 30; external_audit_required = false; multisig_required = false };
      };
      case (#open_pool) {
        { min_jobs_completed = 100; zero_integrity_failures_days = 30; external_audit_required = true; multisig_required = true };
      };
      case (#institutional) {
        { min_jobs_completed = 1000; zero_integrity_failures_days = 90; external_audit_required = true; multisig_required = true };
      };
    };
  };

  private func applyParameter(proposal : Proposal) : async Result<(), Text> {
    if (proposal.target_canister != "capital_pool") {
      putParameterValue(proposal.parameter, proposal.proposed_value);
      return #ok(());
    };
    switch (canisterActor()) {
      case null { return #err("capital_pool canister not configured") };
      case (?capitalPool) {
        if (proposal.parameter == "capital_pool.phase") {
          switch (parsePhase(proposal.proposed_value)) {
            case null { return #err("invalid pool phase") };
            case (?phase) {
              switch (await capitalPool.setPhase(phase)) {
                case (#err(message)) { return #err(message) };
                case (#ok(())) { currentPhase := phase };
              };
            };
          };
        } else {
          switch (Nat.fromText(proposal.proposed_value)) {
            case null { return #err("proposed value must be a Nat") };
            case (?value) {
              let result = if (proposal.parameter == "capital_pool.max_utilization_rate") {
                await capitalPool.setMaxUtilizationRate(value);
              } else if (proposal.parameter == "capital_pool.underwriting_fee_rate") {
                await capitalPool.setUnderwritingFeeRate(value);
              } else if (proposal.parameter == "capital_pool.science_allocation_rate") {
                await capitalPool.setScienceAllocationRate(value);
              } else if (proposal.parameter == "capital_pool.micro_pool_cap") {
                await capitalPool.setMicroPoolCap(value);
              } else {
                return #err("unsupported capital_pool parameter");
              };
              switch (result) {
                case (#err(message)) { return #err(message) };
                case (#ok(())) {};
              };
            };
          };
        };
      };
    };
    putParameterValue(proposal.parameter, proposal.proposed_value);
    #ok(());
  };

  private func emitGovernanceEvent(eventType : Text, proposal : Proposal) : async () {
    switch (sigmaActor()) {
      case null {};
      case (?sigma) {
        let now = Int.toText(Time.now());
        ignore await sigma.emitEvent({
          event_id = "governance-" # eventType # "-" # proposal.proposal_id;
          schema_version = "1.0.0";
          emitted_at = now;
          expires_at = null;
          privacy_tier = "internal";
          lens_state = "none";
          event_type = eventType;
          source = {
            agent_id = "canister:governance";
            node_id = "governance";
            platform = "icp_canister";
            location_class = "sovereign_local";
          };
          provenance_chain = [{
            agent_id = "canister:governance";
            action = "originated";
            timestamp = now;
            signature = null;
          }];
          routing = {
            target = "bus_topic";
            topic = "system.governance";
            priority = "high";
            delivery = "at_least_once";
          };
          payload_type = "GovernanceProposalPayload";
          payload = "{ \"proposal_id\": \"" # proposal.proposal_id # "\", \"target_canister\": \"" # proposal.target_canister # "\", \"parameter\": \"" # proposal.parameter # "\", \"proposed_value\": \"" # proposal.proposed_value # "\" }";
        });
      };
    };
  };

  private func enactById(proposalId : ProposalId, caller : Principal) : async Result<(), Text> {
    switch (findProposal(proposalId)) {
      case null { #err("proposal not found") };
      case (?proposal) {
        if (proposalExpired(proposal)) {
          replaceProposal({
            proposal_id = proposal.proposal_id;
            target_canister = proposal.target_canister;
            parameter = proposal.parameter;
            current_value = proposal.current_value;
            proposed_value = proposal.proposed_value;
            justification = proposal.justification;
            proposed_by = proposal.proposed_by;
            proposed_at = proposal.proposed_at;
            status = #expired;
            enacted_at = null;
            approved_by = proposal.approved_by;
            rejected_by = proposal.rejected_by;
          });
          return #err("proposal expired");
        };
        if (proposal.status == #enacted) {
          return #err("proposal already enacted");
        };
        if (proposal.status == #rejected) {
          return #err("proposal rejected");
        };
        if (not isAdmin(caller) and proposal.approved_by.size() < requiredApprovals) {
          return #err("approval threshold not met");
        };
        switch (await applyParameter(proposal)) {
          case (#err(message)) { #err(message) };
          case (#ok(())) {
            let enacted = {
              proposal_id = proposal.proposal_id;
              target_canister = proposal.target_canister;
              parameter = proposal.parameter;
              current_value = proposal.current_value;
              proposed_value = proposal.proposed_value;
              justification = proposal.justification;
              proposed_by = proposal.proposed_by;
              proposed_at = proposal.proposed_at;
              status = #enacted;
              enacted_at = ?Time.now();
              approved_by = proposal.approved_by;
              rejected_by = proposal.rejected_by;
            };
            replaceProposal(enacted);
            await emitGovernanceEvent("system.governance.enacted", enacted);
            #ok(());
          };
        };
      };
    };
  };

  public query func getConfig() : async GovernanceConfig {
    {
      version = configVersion;
      admin = effectiveAdmin();
      authorized = authorized;
      required_approvals = requiredApprovals;
      proposal_expiry_ns = proposalExpiryNs;
    };
  };

  public query func getProposal(proposalId : ProposalId) : async ?Proposal {
    findProposal(proposalId);
  };

  public query func listProposals(status : ?ProposalStatus) : async [Proposal] {
    Array.filter<Proposal>(proposals, func(proposal : Proposal) : Bool { statusMatches(status, proposal) });
  };

  public query func getCurrentPhase() : async PoolPhase {
    currentPhase;
  };

  public query func getParameter(key : ParameterKey) : async ?ParameterValue {
    getParameterValue(key);
  };

  public query func listParameters() : async [(ParameterKey, ParameterValue)] {
    parameterRegistry;
  };

  public query func getPhaseRequirements(targetPhase : PoolPhase) : async PhaseAdvanceRequirements {
    phaseRequirements(targetPhase);
  };

  public query func canAdvancePhase(targetPhase : PoolPhase) : async Result<(), Text> {
    let requirements = phaseRequirements(targetPhase);
    if (jobsCompletedCount < requirements.min_jobs_completed) {
      return #err("insufficient completed jobs for target phase");
    };
    if (integrityFailuresCount > 0) {
      return #err("integrity failures must be zero for the required window");
    };
    if (requirements.external_audit_required and not externalAuditConfirmed) {
      return #err("external audit confirmation required");
    };
    if (requirements.multisig_required and configVersion != "v1_multisig") {
      return #err("multisig governance must be active");
    };
    #ok(());
  };

  public query func getIntegrityAlerts(limit : Nat) : async [IntegrityAlert] {
    let count = if (limit < integrityAlerts.size()) { limit } else { integrityAlerts.size() };
    let start = integrityAlerts.size() - count;
    Array.tabulate<IntegrityAlert>(
      count,
      func(index : Nat) : IntegrityAlert { integrityAlerts[start + index] },
    );
  };

  public query func getStats() : async Stats {
    var enacted = 0;
    var pending = 0;
    for (proposal in proposals.vals()) {
      if (proposal.status == #enacted) { enacted += 1 };
      if (proposal.status == #pending) { pending += 1 };
    };
    {
      total_proposals = proposals.size();
      enacted = enacted;
      pending = pending;
      integrity_alerts = integrityAlerts.size();
      current_phase = currentPhase;
    };
  };

  public shared ({ caller }) func propose(
    target_canister : Text,
    parameter : ParameterKey,
    proposed_value : ParameterValue,
    justification : Text,
  ) : async Result<ProposalId, Text> {
    switch (requireAuthorized(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (containsIntegrityGateParameter(target_canister, parameter)) {
      return #err("Constitutional: integrity gate parameters are not subject to governance");
    };
    switch (getParameterValue(parameter)) {
      case null { return #err("parameter is not registered") };
      case (?currentValue) {
        let proposalId = nextId("proposal");
        let proposal = {
          proposal_id = proposalId;
          target_canister = target_canister;
          parameter = parameter;
          current_value = currentValue;
          proposed_value = proposed_value;
          justification = justification;
          proposed_by = caller;
          proposed_at = Time.now();
          status = #pending;
          enacted_at = null;
          approved_by = [];
          rejected_by = [];
        };
        proposals := Array.append<Proposal>(proposals, [proposal]);
        await emitGovernanceEvent("system.governance.proposed", proposal);
        #ok(proposalId);
      };
    };
  };

  public shared ({ caller }) func approve(proposalId : ProposalId) : async Result<(), Text> {
    switch (requireAuthorized(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    switch (findProposal(proposalId)) {
      case null { #err("proposal not found") };
      case (?proposal) {
        if (proposal.proposed_by == caller) {
          return #err("caller cannot approve own proposal");
        };
        if (containsPrincipal(proposal.approved_by, caller)) {
          return #err("caller already approved proposal");
        };
        let approved = {
          proposal_id = proposal.proposal_id;
          target_canister = proposal.target_canister;
          parameter = proposal.parameter;
          current_value = proposal.current_value;
          proposed_value = proposal.proposed_value;
          justification = proposal.justification;
          proposed_by = proposal.proposed_by;
          proposed_at = proposal.proposed_at;
          status = #approved;
          enacted_at = proposal.enacted_at;
          approved_by = Array.append<Principal>(proposal.approved_by, [caller]);
          rejected_by = proposal.rejected_by;
        };
        replaceProposal(approved);
        if (approved.approved_by.size() >= requiredApprovals) {
          await enactById(proposalId, caller);
        } else {
          #ok(());
        };
      };
    };
  };

  public shared ({ caller }) func reject(proposalId : ProposalId) : async Result<(), Text> {
    switch (requireAuthorized(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    switch (findProposal(proposalId)) {
      case null { #err("proposal not found") };
      case (?proposal) {
        let rejected = {
          proposal_id = proposal.proposal_id;
          target_canister = proposal.target_canister;
          parameter = proposal.parameter;
          current_value = proposal.current_value;
          proposed_value = proposal.proposed_value;
          justification = proposal.justification;
          proposed_by = proposal.proposed_by;
          proposed_at = proposal.proposed_at;
          status = #rejected;
          enacted_at = proposal.enacted_at;
          approved_by = proposal.approved_by;
          rejected_by = Array.append<Principal>(proposal.rejected_by, [caller]);
        };
        replaceProposal(rejected);
        #ok(());
      };
    };
  };

  public shared ({ caller }) func enact(proposalId : ProposalId) : async Result<(), Text> {
    switch (requireAuthorized(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    await enactById(proposalId, caller);
  };

  public shared ({ caller }) func proposePhaseAdvance(targetPhase : PoolPhase, evidence : Text) : async Result<ProposalId, Text> {
    switch (requireAuthorized(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    switch (await canAdvancePhase(targetPhase)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    await propose("capital_pool", "capital_pool.phase", phaseText(targetPhase), evidence);
  };

  public shared ({ caller }) func enactPhaseAdvance(proposalId : ProposalId) : async Result<(), Text> {
    await enactById(proposalId, caller);
  };

  public shared func receiveIntegrityAlert(alert : IntegrityAlert) : async Result<(), Text> {
    integrityAlerts := Array.append<IntegrityAlert>(integrityAlerts, [alert]);
    if (integrityAlerts.size() > 500) {
      let start = integrityAlerts.size() - 500;
      integrityAlerts := Array.tabulate<IntegrityAlert>(
        500,
        func(index : Nat) : IntegrityAlert { integrityAlerts[start + index] },
      );
    };
    if (alert.veto_exercised) {
      integrityFailuresCount += 1;
    };
    #ok(());
  };

  public shared func reportJobCompleted() : async Result<(), Text> {
    jobsCompletedCount += 1;
    #ok(());
  };

  public shared ({ caller }) func confirmExternalAudit(auditRef : Text) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (Text.size(auditRef) == 0) {
      return #err("auditRef must not be empty");
    };
    externalAuditConfirmed := true;
    externalAuditRef := ?auditRef;
    #ok(());
  };

  public shared ({ caller }) func addAuthorized(principal : Principal) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (containsPrincipal(authorized, principal)) {
      return #err("principal already authorized");
    };
    authorized := Array.append<Principal>(authorized, [principal]);
    #ok(());
  };

  public shared ({ caller }) func removeAuthorized(principal : Principal) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    authorized := Array.filter<Principal>(authorized, func(value : Principal) : Bool { value != principal });
    #ok(());
  };

  public shared ({ caller }) func setRequiredApprovals(n : Nat) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (n == 0) {
      return #err("required approvals must be greater than zero");
    };
    requiredApprovals := n;
    #ok(());
  };

  public shared ({ caller }) func upgradeToMultisig(nextAuthorized : [Principal], required : Nat) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (required == 0 or required > nextAuthorized.size()) {
      return #err("required approvals must be between 1 and authorized size");
    };
    authorized := nextAuthorized;
    requiredApprovals := required;
    configVersion := "v1_multisig";
    #ok(());
  };

  public shared ({ caller }) func setCanisters(
    capitalPool : Principal,
    sigmaBus : Principal,
    auditLog : Principal,
  ) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    capitalPoolCanister := ?capitalPool;
    sigmaBusCanister := ?sigmaBus;
    auditLogCanister := ?auditLog;
    #ok(());
  };
};
