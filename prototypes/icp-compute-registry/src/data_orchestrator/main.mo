import Array "mo:base/Array";
import HashMap "mo:base/HashMap";
import Iter "mo:base/Iter";
import Principal "mo:base/Principal";
import Text "mo:base/Text";
import Time "mo:base/Time";

persistent actor DataOrchestrator {
  public type PrivacyTier = {
    #sovereign;
    #confidential;
    #internal;
    #public_tier;
  };

  public type StorageTarget = {
    #local_agent;
    #encrypted_canister;
    #icp_asset;
    #ipfs;
    #filecoin;
    #cloudflare_r2;
  };

  public type PipelineStage = {
    #registered;
    #policy_checked;
    #procurement_requested;
    #stored;
    #completed;
    #failed;
  };

  public type TriggerCondition = {
    #no_internal_match;
    #capacity_exceeded;
    #hardware_unavailable;
    #external_cheaper;
  };

  public type DataAsset = {
    asset_id : Text;
    owner : Principal;
    privacy_tier : PrivacyTier;
    storage_target : StorageTarget;
    data_hash : Text;
    byte_size : Nat;
    created_at : Time.Time;
    stage : PipelineStage;
    error_message : ?Text;
  };

  public type PipelineRequest = {
    asset_id : Text;
    task_type : Text;
    storage_target : StorageTarget;
    privacy_tier : PrivacyTier;
    budget_credits : Nat;
    data_hash : Text;
    allow_external_compute : Bool;
  };

  public type ProcurementRequest = {
    job_id : Text;
    task_type : Text;
    budget_credits : Nat;
    privacy_tier : PrivacyTier;
    trigger : TriggerCondition;
    job_spec_hash : Text;
  };

  public type Stats = {
    total : Nat;
    active : Nat;
    failed : Nat;
  };

  public type Result<T, E> = {
    #ok : T;
    #err : E;
  };

  type ProcurementRouter = actor {
    triggerProcurement : shared (ProcurementRequest) -> async { #ok : Text; #err : Text };
  };

  private stable var stableAssets : [(Text, DataAsset)] = [];
  private stable var jobMarketCanister : ?Principal = null;
  private stable var procurementRouterCanister : ?Principal = null;
  private stable var admin : ?Principal = null;
  private stable var gateLog : [(Time.Time, Text, Bool)] = [];

  private transient let assets = HashMap.HashMap<Text, DataAsset>(0, Text.equal, Text.hash);

  system func preupgrade() {
    stableAssets := Iter.toArray(assets.entries());
  };

  system func postupgrade() {
    for ((assetId, asset) in stableAssets.vals()) {
      assets.put(assetId, asset);
    };
    stableAssets := [];
  };

  private func requireAdmin(caller : Principal) : Result<(), Text> {
    switch (admin) {
      case null {
        admin := ?caller;
        #ok(());
      };
      case (?principal) {
        if (principal == caller) { #ok(()) } else { #err("admin only") };
      };
    };
  };

  private func procurementActor() : ?ProcurementRouter {
    switch (procurementRouterCanister) {
      case null { null };
      case (?canisterId) {
        let actorRef : ProcurementRouter = actor (Principal.toText(canisterId));
        ?actorRef;
      };
    };
  };

  private func stageActive(stage : PipelineStage) : Bool {
    switch (stage) {
      case (#registered) { true };
      case (#policy_checked) { true };
      case (#procurement_requested) { true };
      case (#stored) { true };
      case _ { false };
    };
  };

  private func minNat(a : Nat, b : Nat) : Nat {
    if (a < b) { a } else { b };
  };

  private func storageTargetText(target : StorageTarget) : Text {
    switch (target) {
      case (#local_agent) { "local_agent" };
      case (#encrypted_canister) { "encrypted_canister" };
      case (#icp_asset) { "icp_asset" };
      case (#ipfs) { "ipfs" };
      case (#filecoin) { "filecoin" };
      case (#cloudflare_r2) { "cloudflare_r2" };
    };
  };

  private func isExternalTarget(target : Text) : Bool {
    target == "external" or target == "external_provider" or target == "ipfs" or target == "filecoin" or target == "cloudflare_r2";
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

  private func storagePolicy(tier : PrivacyTier, target : StorageTarget) : Result<(), Text> {
    switch (tier, target) {
      case (#sovereign, #local_agent) { #ok(()) };
      case (#sovereign, _) { #err("sovereign data cannot use external storage") };
      case (#confidential, #local_agent) { #ok(()) };
      case (#confidential, #encrypted_canister) { #ok(()) };
      case (#confidential, _) { #err("confidential data cannot use public or external storage") };
      case (#internal, #local_agent) { #ok(()) };
      case (#internal, #encrypted_canister) { #ok(()) };
      case (#internal, #icp_asset) { #ok(()) };
      case (#internal, #filecoin) { #ok(()) };
      case (#internal, #cloudflare_r2) { #ok(()) };
      case (#internal, #ipfs) { #err("internal data must use accountable storage, not public IPFS") };
      case (#public_tier, #local_agent) { #ok(()) };
      case (#public_tier, #encrypted_canister) { #ok(()) };
      case (#public_tier, #icp_asset) { #ok(()) };
      case (#public_tier, #ipfs) { #ok(()) };
      case (#public_tier, #filecoin) { #ok(()) };
      case (#public_tier, #cloudflare_r2) { #ok(()) };
    };
  };

  public shared ({ caller }) func configureExchange(
    jobMarket : ?Principal,
    procurementRouter : ?Principal,
  ) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    jobMarketCanister := jobMarket;
    procurementRouterCanister := procurementRouter;
    #ok(());
  };

  public query func validateStoragePolicy(tier : PrivacyTier, target : StorageTarget) : async Result<(), Text> {
    storagePolicy(tier, target);
  };

  public query func getAsset(assetId : Text) : async ?DataAsset {
    assets.get(assetId);
  };

  public query func listAssets(limit : Nat) : async [DataAsset] {
    let all = Iter.toArray(assets.vals());
    Array.tabulate<DataAsset>(
      if (limit < all.size()) { limit } else { all.size() },
      func(index : Nat) : DataAsset { all[index] },
    );
  };

  public query func listByStage(stage : PipelineStage) : async [DataAsset] {
    Array.filter<DataAsset>(
      Iter.toArray(assets.vals()),
      func(asset : DataAsset) : Bool { asset.stage == stage },
    );
  };

  public query func getStats() : async Stats {
    var activeCount = 0;
    var failedCount = 0;
    for (asset in assets.vals()) {
      if (stageActive(asset.stage)) {
        activeCount += 1;
      };
      if (asset.stage == #failed) {
        failedCount += 1;
      };
    };
    {
      total = assets.size();
      active = activeCount;
      failed = failedCount;
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

  public shared ({ caller }) func registerAsset(asset : DataAsset) : async Result<Text, Text> {
    if (Text.size(asset.asset_id) == 0) { return #err("asset_id must not be empty") };
    if (Text.size(asset.data_hash) == 0) { return #err("data_hash must not be empty") };
    if (asset.owner != caller) { return #err("owner must match caller") };
    switch (assets.get(asset.asset_id)) {
      case (?_) { return #err("asset already exists") };
      case null {};
    };
    if (not integrityGate("register_asset", asset.privacy_tier, ?storageTargetText(asset.storage_target))) {
      return #err("integrity gate blocked operation");
    };
    switch (storagePolicy(asset.privacy_tier, asset.storage_target)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    assets.put(asset.asset_id, {
      asset_id = asset.asset_id;
      owner = caller;
      privacy_tier = asset.privacy_tier;
      storage_target = asset.storage_target;
      data_hash = asset.data_hash;
      byte_size = asset.byte_size;
      created_at = Time.now();
      stage = #policy_checked;
      error_message = null;
    });
    #ok(asset.asset_id);
  };

  public shared ({ caller }) func planPipeline(request : PipelineRequest) : async Result<Text, Text> {
    if (Text.size(request.asset_id) == 0) { return #err("asset_id must not be empty") };
    if (Text.size(request.task_type) == 0) { return #err("task_type must not be empty") };
    if (Text.size(request.data_hash) == 0) { return #err("data_hash must not be empty") };
    if (not integrityGate("plan_pipeline", request.privacy_tier, ?storageTargetText(request.storage_target))) {
      return #err("integrity gate blocked operation");
    };
    if (request.allow_external_compute and not integrityGate("external_compute", request.privacy_tier, ?"external_provider")) {
      return #err("integrity gate blocked operation");
    };
    switch (storagePolicy(request.privacy_tier, request.storage_target)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    let now = Time.now();
    assets.put(request.asset_id, {
      asset_id = request.asset_id;
      owner = caller;
      privacy_tier = request.privacy_tier;
      storage_target = request.storage_target;
      data_hash = request.data_hash;
      byte_size = 0;
      created_at = now;
      stage = #policy_checked;
      error_message = null;
    });
    if (request.allow_external_compute) {
      switch (procurementActor()) {
        case null { return #err("procurement router is not configured") };
        case (?router) {
          switch (await router.triggerProcurement({
            job_id = request.asset_id;
            task_type = request.task_type;
            budget_credits = request.budget_credits;
            privacy_tier = request.privacy_tier;
            trigger = #no_internal_match;
            job_spec_hash = request.data_hash;
          })) {
            case (#ok(recordId)) {
              assets.put(request.asset_id, {
                asset_id = request.asset_id;
                owner = caller;
                privacy_tier = request.privacy_tier;
                storage_target = request.storage_target;
                data_hash = request.data_hash;
                byte_size = 0;
                created_at = now;
                stage = #procurement_requested;
                error_message = null;
              });
              #ok(recordId);
            };
            case (#err(message)) {
              assets.put(request.asset_id, {
                asset_id = request.asset_id;
                owner = caller;
                privacy_tier = request.privacy_tier;
                storage_target = request.storage_target;
                data_hash = request.data_hash;
                byte_size = 0;
                created_at = now;
                stage = #failed;
                error_message = ?message;
              });
              #err(message);
            };
          };
        };
      };
    } else {
      #ok(request.asset_id);
    };
  };

  public shared ({ caller }) func routeStorage(
    assetId : Text,
    target : StorageTarget,
  ) : async Result<(), Text> {
    switch (assets.get(assetId)) {
      case null { #err("asset not found") };
      case (?asset) {
        if (asset.owner != caller) { return #err("only owner can route storage") };
        if (not integrityGate("route_storage", asset.privacy_tier, ?storageTargetText(target))) {
          return #err("integrity gate blocked operation");
        };
        switch (storagePolicy(asset.privacy_tier, target)) {
          case (#err(message)) { return #err(message) };
          case (#ok(())) {};
        };
        assets.put(assetId, {
          asset_id = asset.asset_id;
          owner = asset.owner;
          privacy_tier = asset.privacy_tier;
          storage_target = target;
          data_hash = asset.data_hash;
          byte_size = asset.byte_size;
          created_at = asset.created_at;
          stage = #stored;
          error_message = null;
        });
        #ok(());
      };
    };
  };

  public shared ({ caller }) func completeAsset(assetId : Text) : async Result<(), Text> {
    switch (assets.get(assetId)) {
      case null { #err("asset not found") };
      case (?asset) {
        if (asset.owner != caller) { return #err("only owner can complete asset") };
        assets.put(assetId, {
          asset_id = asset.asset_id;
          owner = asset.owner;
          privacy_tier = asset.privacy_tier;
          storage_target = asset.storage_target;
          data_hash = asset.data_hash;
          byte_size = asset.byte_size;
          created_at = asset.created_at;
          stage = #completed;
          error_message = null;
        });
        #ok(());
      };
    };
  };
};
