import Array "mo:base/Array";
import Float "mo:base/Float";
import HashMap "mo:base/HashMap";
import Iter "mo:base/Iter";
import Nat "mo:base/Nat";
import Principal "mo:base/Principal";
import Text "mo:base/Text";
import Time "mo:base/Time";

persistent actor ComputeRegistry {
  public type ProviderId = Text;

  public type PrivacyTier = {
    #sovereign;
    #confidential;
    #internal;
    #public_tier;
  };

  public type ProviderClass = {
    #sovereign_local;
    #decentralized_market;
    #cloud_burst;
    #icp_canister;
    #science_pool;
  };

  public type ProviderProfile = {
    provider_id : ProviderId;
    agent_id : ?Text;
    display_name : Text;
    provider_class : ProviderClass;
    location_class : ?Text;
    privacy_tier : ?PrivacyTier;
    endpoint : ?Text;
    compute_types : [Text];
    model_support : [Text];
    hardware_summary : ?Text;
    capacity_summary : ?Text;
    max_concurrent_jobs : Nat;
    pricing_model : Text;
    base_price_credits : Nat;
    constraints : ?[Text];
    reputation_score : ?Float;
    metadata : ?[(Text, Text)];
    availability : Float;
    last_heartbeat : Time.Time;
    active : Bool;
  };

  public type ProviderCapabilityProfile = ProviderProfile;

  public type SciencePoolEntry = {
    provider_id : ProviderId;
    donated_credits : Nat;
    science_domain : Text;
    donor_agent_id : Text;
  };

  public type Stats = {
    total : Nat;
    active : Nat;
    sciencePoolSize : Nat;
  };

  public type Result<T, E> = {
    #ok : T;
    #err : E;
  };

  type IdentityRegistry = actor {
    verify : shared query (Text) -> async Bool;
  };

  private stable var stableProviders : [(ProviderId, ProviderProfile)] = [];
  private stable var sciencePool : [SciencePoolEntry] = [];
  private stable var identityRegistryId : ?Principal = null;
  private stable var gateLog : [(Time.Time, Text, Bool)] = [];

  private transient let providers = HashMap.HashMap<ProviderId, ProviderProfile>(0, Text.equal, Text.hash);

  system func preupgrade() {
    stableProviders := Iter.toArray(providers.entries());
  };

  system func postupgrade() {
    for ((providerId, profile) in stableProviders.vals()) {
      providers.put(providerId, profile);
    };
    stableProviders := [];
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

  private func contains(xs : [Text], needle : Text) : Bool {
    for (value in xs.vals()) {
      if (value == needle) { return true };
    };
    false;
  };

  private func minNat(a : Nat, b : Nat) : Nat {
    if (a < b) { a } else { b };
  };

  private func isExternalTarget(target : Text) : Bool {
    target == "external" or target == "external_provider";
  };

  private func providerTarget(profile : ProviderProfile) : ?Text {
    switch (profile.provider_class) {
      case (#sovereign_local) { null };
      case (#icp_canister) { null };
      case _ { ?"external_provider" };
    };
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

  private func activeCount() : Nat {
    var count = 0;
    for (profile in providers.vals()) {
      if (profile.active) { count += 1 };
    };
    count;
  };

  private func normalize(profile : ProviderProfile) : ProviderProfile {
    {
      provider_id = profile.provider_id;
      agent_id = profile.agent_id;
      display_name = profile.display_name;
      provider_class = profile.provider_class;
      location_class = profile.location_class;
      privacy_tier = profile.privacy_tier;
      endpoint = profile.endpoint;
      compute_types = profile.compute_types;
      model_support = profile.model_support;
      hardware_summary = profile.hardware_summary;
      capacity_summary = profile.capacity_summary;
      max_concurrent_jobs = profile.max_concurrent_jobs;
      pricing_model = profile.pricing_model;
      base_price_credits = profile.base_price_credits;
      constraints = profile.constraints;
      reputation_score = profile.reputation_score;
      metadata = profile.metadata;
      availability = profile.availability;
      last_heartbeat = Time.now();
      active = true;
    };
  };

  private func compatiblePrivacy(profile : ProviderProfile, privacyTier : PrivacyTier) : Bool {
    switch (privacyTier, profile.provider_class) {
      case (#sovereign, #sovereign_local) { true };
      case (#confidential, #sovereign_local) { true };
      case (#internal, #sovereign_local) { true };
      case (#internal, #icp_canister) { true };
      case (#public_tier, _) { true };
      case _ { false };
    };
  };

  private func better(a : ProviderProfile, b : ProviderProfile) : Bool {
    let aPrice = if (a.base_price_credits == 0) { 1.0 } else { Float.fromInt(a.base_price_credits) };
    let bPrice = if (b.base_price_credits == 0) { 1.0 } else { Float.fromInt(b.base_price_credits) };
    (a.availability / aPrice) > (b.availability / bPrice);
  };

  public shared func configureExchange(identityCanister : ?Principal) : async Result<(), Text> {
    identityRegistryId := identityCanister;
    #ok(());
  };

  public query func getProvider(providerId : ProviderId) : async ?ProviderProfile {
    providers.get(providerId);
  };

  public query func listProviders() : async [ProviderProfile] {
    Iter.toArray(providers.vals());
  };

  public query func listByClass(providerClass : ProviderClass) : async [ProviderProfile] {
    Array.filter<ProviderProfile>(
      Iter.toArray(providers.vals()),
      func(profile : ProviderProfile) : Bool {
        profile.provider_class == providerClass;
      },
    );
  };

  public query func listByComputeType(computeType : Text) : async [ProviderProfile] {
    Array.filter<ProviderProfile>(
      Iter.toArray(providers.vals()),
      func(profile : ProviderProfile) : Bool {
        profile.active and contains(profile.compute_types, computeType);
      },
    );
  };

  public query func findBestMatch(taskType : Text, budget : Nat, privacyTier : PrivacyTier) : async ?ProviderProfile {
    var best : ?ProviderProfile = null;
    for (profile in providers.vals()) {
      if (
        profile.active and
        contains(profile.compute_types, taskType) and
        profile.base_price_credits <= budget and
        compatiblePrivacy(profile, privacyTier)
      ) {
        switch (best) {
          case null { best := ?profile };
          case (?current) {
            if (better(profile, current)) {
              best := ?profile;
            };
          };
        };
      };
    };
    best;
  };

  public query func getSciencePool() : async [SciencePoolEntry] {
    sciencePool;
  };

  public query func getStats() : async Stats {
    {
      total = providers.size();
      active = activeCount();
      sciencePoolSize = sciencePool.size();
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

  public shared func registerProvider(profile : ProviderProfile) : async Result<ProviderId, Text> {
    if (Text.size(profile.provider_id) == 0) { return #err("provider_id must not be empty") };
    if (Text.size(profile.display_name) == 0) { return #err("display_name must not be empty") };
    if (profile.compute_types.size() == 0) { return #err("compute_types must not be empty") };
    if (profile.max_concurrent_jobs == 0) { return #err("max_concurrent_jobs must be greater than zero") };
    if (profile.availability < 0.0 or profile.availability > 1.0) {
      return #err("availability must be between 0.0 and 1.0");
    };
    switch (profile.privacy_tier) {
      case null {};
      case (?tier) {
        if (not integrityGate("register_provider", tier, providerTarget(profile))) {
          return #err("integrity gate blocked operation");
        };
      };
    };
    switch (profile.agent_id, identityActor()) {
      case (?agentId, ?identity) {
        if (not (await identity.verify(agentId))) {
          return #err("linked agent is not registered or active");
        };
      };
      case _ {};
    };
    let normalized = normalize(profile);
    providers.put(normalized.provider_id, normalized);
    #ok(normalized.provider_id);
  };

  public shared func updateAvailability(providerId : ProviderId, availability : Float) : async Result<(), Text> {
    if (availability < 0.0 or availability > 1.0) {
      return #err("availability must be between 0.0 and 1.0");
    };
    switch (providers.get(providerId)) {
      case null { #err("provider not found") };
      case (?profile) {
        providers.put(providerId, {
          provider_id = profile.provider_id;
          agent_id = profile.agent_id;
          display_name = profile.display_name;
          provider_class = profile.provider_class;
          location_class = profile.location_class;
          privacy_tier = profile.privacy_tier;
          endpoint = profile.endpoint;
          compute_types = profile.compute_types;
          model_support = profile.model_support;
          hardware_summary = profile.hardware_summary;
          capacity_summary = profile.capacity_summary;
          max_concurrent_jobs = profile.max_concurrent_jobs;
          pricing_model = profile.pricing_model;
          base_price_credits = profile.base_price_credits;
          constraints = profile.constraints;
          reputation_score = profile.reputation_score;
          metadata = profile.metadata;
          availability = availability;
          last_heartbeat = Time.now();
          active = availability > 0.0;
        });
        #ok(());
      };
    };
  };

  public shared func heartbeat(providerId : ProviderId) : async Result<(), Text> {
    switch (providers.get(providerId)) {
      case null { #err("provider not found") };
      case (?profile) {
        let now = Time.now();
        providers.put(providerId, {
          provider_id = profile.provider_id;
          agent_id = profile.agent_id;
          display_name = profile.display_name;
          provider_class = profile.provider_class;
          location_class = profile.location_class;
          privacy_tier = profile.privacy_tier;
          endpoint = profile.endpoint;
          compute_types = profile.compute_types;
          model_support = profile.model_support;
          hardware_summary = profile.hardware_summary;
          capacity_summary = profile.capacity_summary;
          max_concurrent_jobs = profile.max_concurrent_jobs;
          pricing_model = profile.pricing_model;
          base_price_credits = profile.base_price_credits;
          constraints = profile.constraints;
          reputation_score = profile.reputation_score;
          metadata = profile.metadata;
          availability = profile.availability;
          last_heartbeat = now;
          active = true;
        });
        #ok(());
      };
    };
  };

  public shared func donateToSciencePool(entry : SciencePoolEntry) : async Result<(), Text> {
    if (Text.size(entry.provider_id) == 0) { return #err("provider_id must not be empty") };
    if (entry.donated_credits == 0) { return #err("donated_credits must be greater than zero") };
    if (Text.size(entry.science_domain) == 0) { return #err("science_domain must not be empty") };
    sciencePool := Array.append<SciencePoolEntry>(sciencePool, [entry]);
    #ok(());
  };

  public shared func deactivateProvider(providerId : ProviderId) : async Result<(), Text> {
    switch (providers.get(providerId)) {
      case null { #err("provider not found") };
      case (?profile) {
        providers.put(providerId, {
          provider_id = profile.provider_id;
          agent_id = profile.agent_id;
          display_name = profile.display_name;
          provider_class = profile.provider_class;
          location_class = profile.location_class;
          privacy_tier = profile.privacy_tier;
          endpoint = profile.endpoint;
          compute_types = profile.compute_types;
          model_support = profile.model_support;
          hardware_summary = profile.hardware_summary;
          capacity_summary = profile.capacity_summary;
          max_concurrent_jobs = profile.max_concurrent_jobs;
          pricing_model = profile.pricing_model;
          base_price_credits = profile.base_price_credits;
          constraints = profile.constraints;
          reputation_score = profile.reputation_score;
          metadata = profile.metadata;
          availability = 0.0;
          last_heartbeat = Time.now();
          active = false;
        });
        #ok(());
      };
    };
  };
};
