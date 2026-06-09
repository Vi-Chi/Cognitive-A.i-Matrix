import Array "mo:base/Array";
import HashMap "mo:base/HashMap";
import Iter "mo:base/Iter";
import Principal "mo:base/Principal";
import Text "mo:base/Text";
import Time "mo:base/Time";

persistent actor IdentityRegistry {
  public type AgentId = Text;

  public type HardwarePlatform = {
    #raspberry_pi;
    #hailo8;
    #jetson;
    #cloud_gpu;
    #icp_canister;
    #wibo_maritime;
    #unknown;
  };

  public type PrivacyTier = {
    #sovereign;
    #confidential;
    #internal;
    #public_tier;
  };

  public type MaritimeMetadata = {
    vessel_name : Text;
    mmsi : ?Text;
    home_port : ?Text;
    deployment_context : Text;
  };

  public type AgentCapability = {
    agent_id : AgentId;
    display_name : Text;
    operator_principal : Principal;
    hardware_platform : HardwarePlatform;
    privacy_tier : PrivacyTier;
    compute_types : [Text];
    model_support : [Text];
    benchmark_tflops : Float;
    maritime_metadata : ?MaritimeMetadata;
    registered_at : Time.Time;
    last_seen : Time.Time;
    active : Bool;
  };

  public type Stats = {
    total : Nat;
    active : Nat;
  };

  public type Result<T, E> = {
    #ok : T;
    #err : E;
  };

  private stable var stableAgents : [(AgentId, AgentCapability)] = [];
  private transient let agents = HashMap.HashMap<AgentId, AgentCapability>(0, Text.equal, Text.hash);

  system func preupgrade() {
    stableAgents := Iter.toArray(agents.entries());
  };

  system func postupgrade() {
    for ((agentId, profile) in stableAgents.vals()) {
      agents.put(agentId, profile);
    };
    stableAgents := [];
  };

  private func contains(xs : [Text], needle : Text) : Bool {
    for (value in xs.vals()) {
      if (value == needle) {
        return true;
      };
    };
    false;
  };

  private func countActive() : Nat {
    var count = 0;
    for (profile in agents.vals()) {
      if (profile.active) {
        count += 1;
      };
    };
    count;
  };

  private func withFreshTimes(profile : AgentCapability) : AgentCapability {
    let now = Time.now();
    {
      agent_id = profile.agent_id;
      display_name = profile.display_name;
      operator_principal = profile.operator_principal;
      hardware_platform = profile.hardware_platform;
      privacy_tier = profile.privacy_tier;
      compute_types = profile.compute_types;
      model_support = profile.model_support;
      benchmark_tflops = profile.benchmark_tflops;
      maritime_metadata = profile.maritime_metadata;
      registered_at = now;
      last_seen = now;
      active = true;
    };
  };

  public query func getAgent(agentId : AgentId) : async ?AgentCapability {
    agents.get(agentId);
  };

  public query func listAgents() : async [AgentCapability] {
    Iter.toArray(agents.vals());
  };

  public query func listByComputeType(computeType : Text) : async [AgentCapability] {
    Array.filter<AgentCapability>(
      Iter.toArray(agents.vals()),
      func(profile : AgentCapability) : Bool {
        profile.active and contains(profile.compute_types, computeType);
      },
    );
  };

  public query func getStats() : async Stats {
    {
      total = agents.size();
      active = countActive();
    };
  };

  public shared query func verify(agentId : AgentId) : async Bool {
    switch (agents.get(agentId)) {
      case (?profile) { profile.active };
      case null { false };
    };
  };

  public shared ({ caller }) func registerAgent(profile : AgentCapability) : async Result<AgentId, Text> {
    if (Text.size(profile.agent_id) == 0) {
      return #err("agent_id must not be empty");
    };
    if (Text.size(profile.display_name) == 0) {
      return #err("display_name must not be empty");
    };
    if (profile.operator_principal != caller) {
      return #err("operator_principal must match caller");
    };
    if (profile.benchmark_tflops <= 0.0) {
      return #err("benchmark_tflops must be greater than zero");
    };
    if (profile.compute_types.size() == 0) {
      return #err("compute_types must not be empty");
    };
    if (profile.model_support.size() == 0) {
      return #err("model_support must not be empty");
    };

    let normalized = withFreshTimes(profile);
    agents.put(normalized.agent_id, normalized);
    #ok(normalized.agent_id);
  };

  public shared ({ caller }) func updateLastSeen(agentId : AgentId) : async Result<(), Text> {
    switch (agents.get(agentId)) {
      case null { #err("agent not found") };
      case (?profile) {
        if (profile.operator_principal != caller) {
          return #err("only operator can update last_seen");
        };
        agents.put(agentId, {
          agent_id = profile.agent_id;
          display_name = profile.display_name;
          operator_principal = profile.operator_principal;
          hardware_platform = profile.hardware_platform;
          privacy_tier = profile.privacy_tier;
          compute_types = profile.compute_types;
          model_support = profile.model_support;
          benchmark_tflops = profile.benchmark_tflops;
          maritime_metadata = profile.maritime_metadata;
          registered_at = profile.registered_at;
          last_seen = Time.now();
          active = profile.active;
        });
        #ok(());
      };
    };
  };

  public shared ({ caller }) func deactivateAgent(agentId : AgentId) : async Result<(), Text> {
    switch (agents.get(agentId)) {
      case null { #err("agent not found") };
      case (?profile) {
        if (profile.operator_principal != caller) {
          return #err("only operator can deactivate agent");
        };
        agents.put(agentId, {
          agent_id = profile.agent_id;
          display_name = profile.display_name;
          operator_principal = profile.operator_principal;
          hardware_platform = profile.hardware_platform;
          privacy_tier = profile.privacy_tier;
          compute_types = profile.compute_types;
          model_support = profile.model_support;
          benchmark_tflops = profile.benchmark_tflops;
          maritime_metadata = profile.maritime_metadata;
          registered_at = profile.registered_at;
          last_seen = Time.now();
          active = false;
        });
        #ok(());
      };
    };
  };

  public shared ({ caller }) func updateCapabilities(
    agentId : AgentId,
    computeTypes : [Text],
    modelSupport : [Text],
  ) : async Result<(), Text> {
    if (computeTypes.size() == 0) {
      return #err("compute_types must not be empty");
    };
    if (modelSupport.size() == 0) {
      return #err("model_support must not be empty");
    };
    switch (agents.get(agentId)) {
      case null { #err("agent not found") };
      case (?profile) {
        if (profile.operator_principal != caller) {
          return #err("only operator can update capabilities");
        };
        agents.put(agentId, {
          agent_id = profile.agent_id;
          display_name = profile.display_name;
          operator_principal = profile.operator_principal;
          hardware_platform = profile.hardware_platform;
          privacy_tier = profile.privacy_tier;
          compute_types = computeTypes;
          model_support = modelSupport;
          benchmark_tflops = profile.benchmark_tflops;
          maritime_metadata = profile.maritime_metadata;
          registered_at = profile.registered_at;
          last_seen = Time.now();
          active = profile.active;
        });
        #ok(());
      };
    };
  };
};
