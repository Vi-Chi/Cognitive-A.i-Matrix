import Array "mo:base/Array";
import Principal "mo:base/Principal";
import Text "mo:base/Text";
import Time "mo:base/Time";

persistent actor SigmaBusAdapter {
  public type Source = {
    agent_id : Text;
    node_id : Text;
    platform : Text;
    location_class : Text;
  };

  public type ProvenanceEntry = {
    agent_id : Text;
    action : Text;
    timestamp : Text;
    signature : ?Text;
  };

  public type Routing = {
    target : Text;
    topic : Text;
    priority : Text;
    delivery : Text;
  };

  public type SigmaBusEnvelope = {
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

  public type StoredEvent = {
    envelope : SigmaBusEnvelope;
    accepted_at : Time.Time;
    verified : Bool;
    verification_note : ?Text;
  };

  public type VerificationResult = {
    valid : Bool;
    reason : ?Text;
  };

  public type Stats = {
    total : Nat;
    verified : Nat;
    rejected : Nat;
  };

  public type Result<T, E> = {
    #ok : T;
    #err : E;
  };

  type Governance = actor {
    receiveIntegrityAlert : shared ({
      alert_id : Text;
      trigger_event_id : Text;
      canister : Text;
      operation : Text;
      veto_exercised : Bool;
      economic_pressure_detected : Bool;
      recorded_at : Time.Time;
    }) -> async Result<(), Text>;
  };

  private stable var event_log : [StoredEvent] = [];
  private stable var rejected_events : Nat = 0;
  private stable var governance_canister : ?Principal = null;

  private func minNat(a : Nat, b : Nat) : Nat {
    if (a < b) { a } else { b };
  };

  private func allowedPrivacy(value : Text) : Bool {
    value == "sovereign" or value == "confidential" or value == "internal" or value == "public";
  };

  private func allowedLens(value : Text) : Bool {
    value == "positive" or value == "negative" or value == "uncertain" or value == "none";
  };

  private func allowedProvenanceAction(value : Text) : Bool {
    value == "originated" or value == "transformed" or value == "forwarded" or value == "verified";
  };

  private func allowedPriority(value : Text) : Bool {
    value == "critical" or value == "high" or value == "normal" or value == "low";
  };

  private func allowedDelivery(value : Text) : Bool {
    value == "at_most_once" or value == "at_least_once";
  };

  private func signatureShapeOk(signature : ?Text) : Bool {
    switch (signature) {
      case null { true };
      case (?hex) { Text.size(hex) == 128 };
    };
  };

  private func validateEnvelope(envelope : SigmaBusEnvelope) : VerificationResult {
    if (Text.size(envelope.event_id) == 0) {
      return { valid = false; reason = ?"event_id must not be empty" };
    };
    if (envelope.schema_version != "1.0.0") {
      return { valid = false; reason = ?"schema_version must be 1.0.0" };
    };
    if (Text.size(envelope.emitted_at) == 0) {
      return { valid = false; reason = ?"emitted_at must not be empty" };
    };
    if (not allowedPrivacy(envelope.privacy_tier)) {
      return { valid = false; reason = ?"privacy_tier is not in the v1 registry" };
    };
    if (not allowedLens(envelope.lens_state)) {
      return { valid = false; reason = ?"lens_state is not in the v1 registry" };
    };
    if (Text.size(envelope.event_type) == 0) {
      return { valid = false; reason = ?"event_type must not be empty" };
    };
    if (Text.size(envelope.source.agent_id) == 0 or Text.size(envelope.source.node_id) == 0) {
      return { valid = false; reason = ?"source agent_id and node_id are required" };
    };
    if (envelope.provenance_chain.size() == 0) {
      return { valid = false; reason = ?"provenance_chain must not be empty" };
    };
    if (envelope.provenance_chain[0].action != "originated") {
      return { valid = false; reason = ?"first provenance action must be originated" };
    };
    for (entry in envelope.provenance_chain.vals()) {
      if (Text.size(entry.agent_id) == 0 or Text.size(entry.timestamp) == 0) {
        return { valid = false; reason = ?"provenance entries require agent_id and timestamp" };
      };
      if (not allowedProvenanceAction(entry.action)) {
        return { valid = false; reason = ?"unknown provenance action" };
      };
      if (not signatureShapeOk(entry.signature)) {
        return { valid = false; reason = ?"signature must be null or 128 hex characters" };
      };
    };
    if (not allowedPriority(envelope.routing.priority)) {
      return { valid = false; reason = ?"routing priority is not in the v1 registry" };
    };
    if (not allowedDelivery(envelope.routing.delivery)) {
      return { valid = false; reason = ?"routing delivery is not in the v1 registry" };
    };
    if (Text.size(envelope.payload_type) == 0) {
      return { valid = false; reason = ?"payload_type must not be empty" };
    };
    { valid = true; reason = null };
  };

  private func appendEvent(event : StoredEvent) {
    event_log := Array.append<StoredEvent>(event_log, [event]);
  };

  private func governanceActor() : ?Governance {
    switch (governance_canister) {
      case null { null };
      case (?canisterId) {
        let actorRef : Governance = actor (Principal.toText(canisterId));
        ?actorRef;
      };
    };
  };

  private func maybeNotifyGovernance(envelope : SigmaBusEnvelope) : async () {
    if (envelope.event_type != "matrix.integrity.gate") {
      return ();
    };
    if (not Text.contains(envelope.payload, #text "veto_exercised")) {
      return ();
    };
    switch (governanceActor()) {
      case null {};
      case (?governance) {
        ignore await governance.receiveIntegrityAlert({
          alert_id = "alert-" # envelope.event_id;
          trigger_event_id = envelope.event_id;
          canister = envelope.source.node_id;
          operation = envelope.payload_type;
          veto_exercised = Text.contains(envelope.payload, #text "true");
          economic_pressure_detected = Text.contains(envelope.payload, #text "economic_pressure_detected");
          recorded_at = Time.now();
        });
      };
    };
  };

  public shared func configureGovernance(governance : ?Principal) : async Result<(), Text> {
    governance_canister := governance;
    #ok(());
  };

  public query func verifyEnvelope(envelope : SigmaBusEnvelope) : async VerificationResult {
    validateEnvelope(envelope);
  };

  public shared func emitEvent(envelope : SigmaBusEnvelope) : async Result<Text, Text> {
    let verification = validateEnvelope(envelope);
    if (not verification.valid) {
      rejected_events += 1;
      return #err(switch (verification.reason) { case null { "invalid envelope" }; case (?reason) { reason } });
    };
    appendEvent({
      envelope = envelope;
      accepted_at = Time.now();
      verified = true;
      verification_note = ?"signature registry hook accepted envelope shape";
    });
    await maybeNotifyGovernance(envelope);
    #ok(envelope.event_id);
  };

  public query func getRecentEvents(limit : Nat) : async [StoredEvent] {
    let count = minNat(limit, event_log.size());
    let start = event_log.size() - count;
    Array.tabulate<StoredEvent>(
      count,
      func(index : Nat) : StoredEvent { event_log[start + index] },
    );
  };

  public query func getEvent(eventId : Text) : async ?StoredEvent {
    for (event in event_log.vals()) {
      if (event.envelope.event_id == eventId) {
        return ?event;
      };
    };
    null;
  };

  public query func getEventCount() : async Nat {
    event_log.size();
  };

  public query func getStats() : async Stats {
    var verified = 0;
    for (event in event_log.vals()) {
      if (event.verified) {
        verified += 1;
      };
    };
    {
      total = event_log.size();
      verified = verified;
      rejected = rejected_events;
    };
  };
};
