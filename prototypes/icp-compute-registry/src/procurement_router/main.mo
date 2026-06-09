import Array "mo:base/Array";
import HashMap "mo:base/HashMap";
import Iter "mo:base/Iter";
import Nat "mo:base/Nat";
import Principal "mo:base/Principal";
import Text "mo:base/Text";
import Time "mo:base/Time";

persistent actor ProcurementRouter {
  public type JobId = Text;
  public type ProviderId = Text;

  public type PrivacyTier = {
    #sovereign;
    #confidential;
    #internal;
    #public_tier;
  };

  public type ExternalProvider = {
    #akash;
    #golem;
    #cloud_api;
    #filecoin;
    #cloudflare_r2;
  };

  public type PriceQuote = {
    provider : ExternalProvider;
    job_id : JobId;
    price_credits : Nat;
    price_icp : ?Nat;
    estimated_completion_ns : Nat;
    quote_expires_at : Time.Time;
    quote_id : Text;
  };

  public type ProcurementStatus = {
    #quoting;
    #approved;
    #deployed;
    #awaiting_result;
    #completed;
    #failed;
    #cancelled;
  };

  public type ProcurementRecord = {
    record_id : Text;
    job_id : JobId;
    provider : ExternalProvider;
    external_id : Text;
    quote_id : Text;
    cost_credits : Nat;
    cost_icp : ?Nat;
    privacy_tier : Text;
    procured_at : Time.Time;
    status : ProcurementStatus;
    result_hash : ?Text;
    outcome_recorded_at : ?Time.Time;
    error_message : ?Text;
  };

  public type TriggerCondition = {
    #no_internal_match;
    #capacity_exceeded;
    #hardware_unavailable;
    #external_cheaper;
  };

  public type RouterConfig = {
    match_timeout_ns : Nat;
    price_threshold_pct : Nat;
    max_spend_per_job_credits : Nat;
    max_daily_spend_credits : Nat;
    auto_approve_under_credits : Nat;
    enabled : Bool;
  };

  public type ProcurementRequest = {
    job_id : JobId;
    task_type : Text;
    budget_credits : Nat;
    privacy_tier : PrivacyTier;
    trigger : TriggerCondition;
    job_spec_hash : Text;
  };

  public type SpendState = {
    daily_spend : Nat;
    daily_spend_reset_at : Time.Time;
    remaining : Nat;
  };

  public type Result<T, E> = {
    #ok : T;
    #err : E;
  };

  private stable var config : RouterConfig = {
    match_timeout_ns = 30_000_000_000;
    price_threshold_pct = 20;
    max_spend_per_job_credits = 10_000;
    max_daily_spend_credits = 100_000;
    auto_approve_under_credits = 500;
    enabled = true;
  };
  private stable var stableRecords : [(Text, ProcurementRecord)] = [];
  private stable var stableJobToRecord : [(JobId, Text)] = [];
  private stable var dailySpend : Nat = 0;
  private stable var dailySpendResetAt : Time.Time = 0;
  private stable var admin : ?Principal = null;
  private stable var jobMarketCanister : ?Principal = null;
  private stable var capitalPoolCanister : ?Principal = null;
  private stable var computeRegistryCanister : ?Principal = null;
  private stable var reputationCanister : ?Principal = null;
  private stable var nextRecordId : Nat = 0;
  private stable var gateLog : [(Time.Time, Text, Bool)] = [];

  private transient let records = HashMap.HashMap<Text, ProcurementRecord>(0, Text.equal, Text.hash);
  private transient let jobToRecord = HashMap.HashMap<JobId, Text>(0, Text.equal, Text.hash);

  system func preupgrade() {
    stableRecords := Iter.toArray(records.entries());
    stableJobToRecord := Iter.toArray(jobToRecord.entries());
  };

  system func postupgrade() {
    for ((recordId, record) in stableRecords.vals()) {
      records.put(recordId, record);
    };
    for ((jobId, recordId) in stableJobToRecord.vals()) {
      jobToRecord.put(jobId, recordId);
    };
    stableRecords := [];
    stableJobToRecord := [];
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

  private func minNat(a : Nat, b : Nat) : Nat {
    if (a < b) { a } else { b };
  };

  private func nextId(jobId : JobId) : Text {
    nextRecordId += 1;
    "procure-" # Nat.toText(nextRecordId) # "-" # jobId;
  };

  private func privacyText(tier : PrivacyTier) : Text {
    switch (tier) {
      case (#sovereign) { "sovereign" };
      case (#confidential) { "confidential" };
      case (#internal) { "internal" };
      case (#public_tier) { "public" };
    };
  };

  private func isExternalTarget(target : Text) : Bool {
    target == "external" or target == "external_provider" or target == "akash" or target == "golem" or target == "cloud_api" or target == "filecoin" or target == "cloudflare_r2";
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

  private func procurementPrivacyGate(tier : PrivacyTier) : Result<Text, Text> {
    switch (tier) {
      case (#sovereign) { #err("sovereign jobs cannot be externally procured") };
      case (#confidential) { #err("confidential jobs cannot be externally procured") };
      case (#internal) { #ok("internal") };
      case (#public_tier) { #ok("public") };
    };
  };

  private func resetDailySpendIfNeeded() {
    let now = Time.now();
    let dayNs : Int = 24 * 60 * 60 * 1_000_000_000;
    if (dailySpendResetAt == 0 or now >= dailySpendResetAt) {
      dailySpend := 0;
      dailySpendResetAt := now + dayNs;
    };
  };

  private func canSpend(amount : Nat) : Result<(), Text> {
    if (amount > config.max_spend_per_job_credits) {
      return #err("max spend per job exceeded");
    };
    if (dailySpend + amount > config.max_daily_spend_credits) {
      return #err("max daily spend exceeded");
    };
    #ok(());
  };

  private func bestQuote(quotes : [PriceQuote]) : ?PriceQuote {
    var best : ?PriceQuote = null;
    for (quote in quotes.vals()) {
      switch (best) {
        case null { best := ?quote };
        case (?current) {
          if (quote.price_credits < current.price_credits) {
            best := ?quote;
          };
        };
      };
    };
    best;
  };

  private func providerName(provider : ExternalProvider) : Text {
    switch (provider) {
      case (#akash) { "akash" };
      case (#golem) { "golem" };
      case (#cloud_api) { "cloud-api" };
      case (#filecoin) { "filecoin" };
      case (#cloudflare_r2) { "cloudflare-r2" };
    };
  };

  private func akash_queryPrice(task_type : Text, budget : Nat) : async ?PriceQuote {
    // TODO: replace with ic.http_request call to Akash provider REST endpoint https://<provider-host>/lease/<owner>/<dseq>/<gseq>/<oseq>/status.
    ?{
      provider = #akash;
      job_id = "quote-" # task_type;
      price_credits = if (budget > 0) { budget / 2 } else { 1 };
      price_icp = null;
      estimated_completion_ns = 5_000_000_000;
      quote_expires_at = Time.now() + 300_000_000_000;
      quote_id = "akash-" # task_type # "-" # Nat.toText(budget);
    };
  };

  private func akash_deployWorkload(quote : PriceQuote, job_spec_hash : Text) : async Result<Text, Text> {
    // TODO: replace with ic.http_request call to Akash provider deploy endpoint https://<provider-host>/deployment/<dseq>/manifest.
    if (Text.size(job_spec_hash) == 0) { return #err("job_spec_hash must not be empty") };
    #ok("akash-deployment-" # quote.quote_id);
  };

  private func akash_checkStatus(deployment_id : Text) : async ProcurementStatus {
    // TODO: replace with ic.http_request call to Akash provider status endpoint https://<provider-host>/lease/<owner>/<dseq>/<gseq>/<oseq>/status.
    ignore deployment_id;
    #awaiting_result;
  };

  private func golem_queryMarket(task_type : Text) : async [PriceQuote] {
    // TODO: replace with ic.http_request call to Yagna Requestor REST API http://127.0.0.1:7465/requestor-api/v1/market/proposals through a selected gateway.
    [{
      provider = #golem;
      job_id = "quote-" # task_type;
      price_credits = 250;
      price_icp = null;
      estimated_completion_ns = 8_000_000_000;
      quote_expires_at = Time.now() + 300_000_000_000;
      quote_id = "golem-" # task_type;
    }];
  };

  private func golem_createAgreement(quote : PriceQuote) : async Result<Text, Text> {
    // TODO: replace with ic.http_request call to Yagna Requestor REST API http://127.0.0.1:7465/requestor-api/v1/agreements through a selected gateway.
    #ok("golem-agreement-" # quote.quote_id);
  };

  private func cloudapi_queryPrice(model : Text, estimated_tokens : Nat) : async ?PriceQuote {
    // TODO: replace with ic.http_request call to OpenAI-compatible pricing/execution endpoint https://api.openai.com/v1/chat/completions.
    ?{
      provider = #cloud_api;
      job_id = "quote-" # model;
      price_credits = 100 + (estimated_tokens / 1_000);
      price_icp = null;
      estimated_completion_ns = 2_000_000_000;
      quote_expires_at = Time.now() + 300_000_000_000;
      quote_id = "cloud-api-" # model # "-" # Nat.toText(estimated_tokens);
    };
  };

  private func cloudapi_execute(quote : PriceQuote, prompt_hash : Text) : async Result<Text, Text> {
    // TODO: replace with ic.http_request call to OpenAI-compatible execution endpoint https://api.openai.com/v1/chat/completions.
    if (Text.size(prompt_hash) == 0) { return #err("prompt_hash must not be empty") };
    #ok("cloud-api-request-" # quote.quote_id);
  };

  private func filecoin_storeDeal(data_hash : Text, duration_days : Nat) : async Result<Text, Text> {
    // TODO: replace with ic.http_request JSON-RPC call to Filecoin Lotus endpoint https://api.node.glif.io/rpc/v1 using Filecoin.ClientStartDeal.
    if (Text.size(data_hash) == 0) { return #err("data_hash must not be empty") };
    #ok("filecoin-deal-" # data_hash # "-" # Nat.toText(duration_days));
  };

  private func filecoin_retrieveDeal(deal_id : Text) : async Result<Text, Text> {
    // TODO: replace with ic.http_request JSON-RPC call to Filecoin Lotus endpoint https://api.node.glif.io/rpc/v1 using Filecoin.ClientRetrieve.
    if (Text.size(deal_id) == 0) { return #err("deal_id must not be empty") };
    #ok("retrieved-" # deal_id);
  };

  private func r2_store(data_hash : Text, bucket : Text) : async Result<Text, Text> {
    // TODO: replace with ic.http_request S3-compatible PUT to Cloudflare R2 endpoint https://<account_id>.r2.cloudflarestorage.com/<bucket>/<key>.
    if (Text.size(data_hash) == 0 or Text.size(bucket) == 0) {
      return #err("data_hash and bucket must not be empty");
    };
    #ok("r2-object-" # bucket # "-" # data_hash);
  };

  private func deployQuote(quote : PriceQuote, request : ProcurementRequest) : async Result<Text, Text> {
    switch (quote.provider) {
      case (#akash) { await akash_deployWorkload(quote, request.job_spec_hash) };
      case (#golem) { await golem_createAgreement(quote) };
      case (#cloud_api) { await cloudapi_execute(quote, request.job_spec_hash) };
      case (#filecoin) { await filecoin_storeDeal(request.job_spec_hash, 30) };
      case (#cloudflare_r2) { await r2_store(request.job_spec_hash, "autopoiesis-results") };
    };
  };

  public shared ({ caller }) func configureExchange(
    jobMarket : ?Principal,
    capitalPool : ?Principal,
    computeRegistry : ?Principal,
    reputation : ?Principal,
  ) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    jobMarketCanister := jobMarket;
    capitalPoolCanister := capitalPool;
    computeRegistryCanister := computeRegistry;
    reputationCanister := reputation;
    #ok(());
  };

  public query func getProcurementRecord(recordId : Text) : async ?ProcurementRecord {
    records.get(recordId);
  };

  public query func getRecordByJobId(jobId : JobId) : async ?ProcurementRecord {
    switch (jobToRecord.get(jobId)) {
      case null { null };
      case (?recordId) { records.get(recordId) };
    };
  };

  public query func listRecords(limit : Nat) : async [ProcurementRecord] {
    let all = Iter.toArray(records.vals());
    Array.tabulate<ProcurementRecord>(
      minNat(limit, all.size()),
      func(index : Nat) : ProcurementRecord { all[index] },
    );
  };

  public query func listByStatus(status : ProcurementStatus) : async [ProcurementRecord] {
    Array.filter<ProcurementRecord>(
      Iter.toArray(records.vals()),
      func(record : ProcurementRecord) : Bool { record.status == status },
    );
  };

  public query func getRouterConfig() : async RouterConfig {
    config;
  };

  public query func getSpendState() : async SpendState {
    let remaining = if (dailySpend >= config.max_daily_spend_credits) {
      0;
    } else {
      config.max_daily_spend_credits - dailySpend;
    };
    {
      daily_spend = dailySpend;
      daily_spend_reset_at = dailySpendResetAt;
      remaining = remaining;
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

  public shared ({ caller }) func updateConfig(nextConfig : RouterConfig) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (nextConfig.price_threshold_pct > 100) { return #err("price_threshold_pct must be 0-100") };
    if (nextConfig.max_spend_per_job_credits > nextConfig.max_daily_spend_credits) {
      return #err("per-job spend cannot exceed daily spend");
    };
    config := nextConfig;
    #ok(());
  };

  public shared func triggerProcurement(request : ProcurementRequest) : async Result<Text, Text> {
    let gateAllowed = integrityGate("external_procurement", request.privacy_tier, ?"external_provider");
    if (not gateAllowed) {
      switch (request.privacy_tier) {
        case (#sovereign) { return #err("sovereign jobs cannot be externally procured") };
        case (#confidential) { return #err("confidential jobs cannot be externally procured") };
        case _ { return #err("integrity gate blocked operation") };
      };
    };
    switch (procurementPrivacyGate(request.privacy_tier)) {
      case (#err(message)) { return #err(message) };
      case (#ok(_allowed)) {};
    };
    if (not config.enabled) { return #err("procurement router disabled") };
    if (Text.size(request.job_id) == 0) { return #err("job_id must not be empty") };
    if (Text.size(request.task_type) == 0) { return #err("task_type must not be empty") };
    if (request.budget_credits == 0) { return #err("budget must be greater than zero") };
    switch (jobToRecord.get(request.job_id)) {
      case (?_) { return #err("procurement already exists for job") };
      case null {};
    };
    resetDailySpendIfNeeded();
    switch (canSpend(request.budget_credits)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };

    var quotes : [PriceQuote] = [];
    switch (await akash_queryPrice(request.task_type, request.budget_credits)) {
      case null {};
      case (?quote) { quotes := Array.append<PriceQuote>(quotes, [quote]) };
    };
    quotes := Array.append<PriceQuote>(quotes, await golem_queryMarket(request.task_type));
    switch (await cloudapi_queryPrice(request.task_type, request.budget_credits * 10)) {
      case null {};
      case (?quote) { quotes := Array.append<PriceQuote>(quotes, [quote]) };
    };

    switch (bestQuote(quotes)) {
      case null { #err("no external quote available") };
      case (?quote) {
        if (quote.price_credits > request.budget_credits) {
          return #err("best external quote exceeds budget");
        };
        switch (canSpend(quote.price_credits)) {
          case (#err(message)) { return #err(message) };
          case (#ok(())) {};
        };
        let recordId = nextId(request.job_id);
        let autoApproved = quote.price_credits <= config.auto_approve_under_credits;
        var externalId = "";
        var status : ProcurementStatus = #quoting;
        var errorMessage : ?Text = null;
        if (autoApproved) {
          switch (await deployQuote(quote, request)) {
            case (#ok(id)) {
              externalId := id;
              status := #awaiting_result;
              dailySpend += quote.price_credits;
            };
            case (#err(message)) {
              status := #failed;
              errorMessage := ?message;
            };
          };
        } else {
          status := #approved;
        };
        let record = {
          record_id = recordId;
          job_id = request.job_id;
          provider = quote.provider;
          external_id = externalId;
          quote_id = quote.quote_id;
          cost_credits = quote.price_credits;
          cost_icp = quote.price_icp;
          privacy_tier = privacyText(request.privacy_tier);
          procured_at = Time.now();
          status = status;
          result_hash = null;
          outcome_recorded_at = null;
          error_message = errorMessage;
        };
        records.put(recordId, record);
        jobToRecord.put(request.job_id, recordId);
        #ok(recordId);
      };
    };
  };

  public shared ({ caller }) func approveProcurement(recordId : Text) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    switch (records.get(recordId)) {
      case null { #err("procurement record not found") };
      case (?record) {
        if (not (record.status == #approved or record.status == #quoting)) {
          return #err("record is not awaiting approval");
        };
        resetDailySpendIfNeeded();
        switch (canSpend(record.cost_credits)) {
          case (#err(message)) { return #err(message) };
          case (#ok(())) {};
        };
        dailySpend += record.cost_credits;
        records.put(recordId, {
          record_id = record.record_id;
          job_id = record.job_id;
          provider = record.provider;
          external_id = providerName(record.provider) # "-manual-" # record.record_id;
          quote_id = record.quote_id;
          cost_credits = record.cost_credits;
          cost_icp = record.cost_icp;
          privacy_tier = record.privacy_tier;
          procured_at = record.procured_at;
          status = #awaiting_result;
          result_hash = record.result_hash;
          outcome_recorded_at = record.outcome_recorded_at;
          error_message = null;
        });
        #ok(());
      };
    };
  };

  public shared func completeProcurement(recordId : Text, resultHash : Text) : async Result<(), Text> {
    if (Text.size(resultHash) == 0) { return #err("resultHash must not be empty") };
    switch (records.get(recordId)) {
      case null { #err("procurement record not found") };
      case (?record) {
        if (record.status == #cancelled) { return #err("procurement is cancelled") };
        records.put(recordId, {
          record_id = record.record_id;
          job_id = record.job_id;
          provider = record.provider;
          external_id = record.external_id;
          quote_id = record.quote_id;
          cost_credits = record.cost_credits;
          cost_icp = record.cost_icp;
          privacy_tier = record.privacy_tier;
          procured_at = record.procured_at;
          status = #completed;
          result_hash = ?resultHash;
          outcome_recorded_at = ?Time.now();
          error_message = null;
        });
        #ok(());
      };
    };
  };

  public shared func failProcurement(recordId : Text, message : Text) : async Result<(), Text> {
    switch (records.get(recordId)) {
      case null { #err("procurement record not found") };
      case (?record) {
        records.put(recordId, {
          record_id = record.record_id;
          job_id = record.job_id;
          provider = record.provider;
          external_id = record.external_id;
          quote_id = record.quote_id;
          cost_credits = record.cost_credits;
          cost_icp = record.cost_icp;
          privacy_tier = record.privacy_tier;
          procured_at = record.procured_at;
          status = #failed;
          result_hash = record.result_hash;
          outcome_recorded_at = ?Time.now();
          error_message = ?message;
        });
        #ok(());
      };
    };
  };

  public shared ({ caller }) func cancelProcurement(recordId : Text) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    switch (records.get(recordId)) {
      case null { #err("procurement record not found") };
      case (?record) {
        records.put(recordId, {
          record_id = record.record_id;
          job_id = record.job_id;
          provider = record.provider;
          external_id = record.external_id;
          quote_id = record.quote_id;
          cost_credits = record.cost_credits;
          cost_icp = record.cost_icp;
          privacy_tier = record.privacy_tier;
          procured_at = record.procured_at;
          status = #cancelled;
          result_hash = record.result_hash;
          outcome_recorded_at = record.outcome_recorded_at;
          error_message = record.error_message;
        });
        #ok(());
      };
    };
  };
};
