import Array "mo:base/Array";
import HashMap "mo:base/HashMap";
import Iter "mo:base/Iter";
import Nat "mo:base/Nat";
import Principal "mo:base/Principal";
import Text "mo:base/Text";
import Time "mo:base/Time";

persistent actor CapitalPool {
  public type InvestorId = Principal;
  public type PoolShares = Nat;
  public type Credits = Nat;

  public type Currency = {
    #icp;
    #ck_usdc;
    #internal_credit;
  };

  public type PrivacyTier = {
    #sovereign;
    #confidential;
    #internal;
    #public_tier;
  };

  public type InvestorPosition = {
    investor : InvestorId;
    shares : PoolShares;
    deposited_credits : Credits;
    yield_earned : Credits;
    deposited_at : Time.Time;
    last_updated : Time.Time;
  };

  public type PoolState = {
    total_shares : PoolShares;
    total_capital : Credits;
    deployed_capital : Credits;
    available_capital : Credits;
    science_pool_balance : Credits;
    total_yield_distributed : Credits;
    max_utilization_rate : Nat;
    underwriting_fee_rate : Nat;
    science_allocation_rate : Nat;
  };

  public type BalanceTier = {
    tier_name : Text;
    min_credits : Credits;
    max_credits : ?Credits;
    reserve_pct : Nat;
  };

  public type ApprovalThreshold = {
    operation : Text;
    max_auto_approve_credits : Credits;
    approval_required : Bool;
  };

  public type RefusalCondition = {
    condition_id : Text;
    description : Text;
    active : Bool;
  };

  public type TreasuryPolicy = {
    policy_id : Text;
    version : Text;
    effective_from : Time.Time;
    currency : Currency;
    reserve_floor_credits : Credits;
    operating_budget_credits : Credits;
    reinvestment_rate_pct : Nat;
    balance_tiers : [BalanceTier];
    approval_thresholds : [ApprovalThreshold];
    lockdown_enabled : Bool;
    refusal_conditions : [RefusalCondition];
    audit_required : Bool;
  };

  public type TreasurySnapshot = {
    policy_id : Text;
    total_capital : Credits;
    available_capital : Credits;
    deployed_capital : Credits;
    science_pool_balance : Credits;
    reserve_floor_credits : Credits;
    utilization_rate : Nat;
    lockdown_enabled : Bool;
    captured_at : Time.Time;
  };

  public type UnderwritingOutcome = {
    #success;
    #failure;
  };

  public type UnderwritingRecord = {
    record_id : Text;
    job_id : Text;
    amount : Credits;
    underwritten_at : Time.Time;
    settled : Bool;
    outcome : ?UnderwritingOutcome;
    fee_earned : Credits;
    loss_absorbed : Credits;
    simulated : Bool;
  };

  public type ScienceDonation = {
    donor : InvestorId;
    amount : Credits;
    science_domain : Text;
    donated_at : Time.Time;
  };

  public type ScienceDisbursement = {
    to : Principal;
    amount : Credits;
    science_domain : Text;
    disbursed_at : Time.Time;
    simulated : Bool;
  };

  public type PoolPhase = {
    #simulation;
    #micro_pool;
    #open_pool;
    #institutional;
  };

  public type Result<T, E> = {
    #ok : T;
    #err : E;
  };

  type Ledger = actor {
    transfer : shared (Principal, Nat) -> async { #Ok : Nat; #Err : Text };
  };

  private stable var phase : PoolPhase = #simulation;
  private stable var poolState : PoolState = {
    total_shares = 0;
    total_capital = 0;
    deployed_capital = 0;
    available_capital = 0;
    science_pool_balance = 0;
    total_yield_distributed = 0;
    max_utilization_rate = 80;
    underwriting_fee_rate = 10;
    science_allocation_rate = 5;
  };
  private stable var stablePositions : [(InvestorId, InvestorPosition)] = [];
  private stable var stableUnderwriting : [(Text, UnderwritingRecord)] = [];
  private stable var scienceDonations : [ScienceDonation] = [];
  private stable var scienceDisbursements : [ScienceDisbursement] = [];
  private stable var admin : ?Principal = null;
  private stable var jobMarketCanister : ?Principal = null;
  private stable var computeLedgerCanister : ?Principal = null;
  private stable var governanceCanister : ?Principal = null;
  private stable var microPoolCap : Credits = 100_000_000;
  private stable var nextRecordId : Nat = 0;
  private stable var gateLog : [(Time.Time, Text, Bool)] = [];
  private stable var treasuryPolicy : TreasuryPolicy = {
    policy_id = "treasury-policy-default";
    version = "0.1.0";
    effective_from = 0;
    currency = #internal_credit;
    reserve_floor_credits = 0;
    operating_budget_credits = 0;
    reinvestment_rate_pct = 0;
    balance_tiers = [];
    approval_thresholds = [];
    lockdown_enabled = false;
    refusal_conditions = [];
    audit_required = true;
  };

  private transient let positions = HashMap.HashMap<InvestorId, InvestorPosition>(0, Principal.equal, Principal.hash);
  private transient let underwriting = HashMap.HashMap<Text, UnderwritingRecord>(0, Text.equal, Text.hash);

  system func preupgrade() {
    stablePositions := Iter.toArray(positions.entries());
    stableUnderwriting := Iter.toArray(underwriting.entries());
  };

  system func postupgrade() {
    for ((investor, position) in stablePositions.vals()) {
      positions.put(investor, position);
    };
    for ((recordId, record) in stableUnderwriting.vals()) {
      underwriting.put(recordId, record);
    };
    stablePositions := [];
    stableUnderwriting := [];
  };

  private func ledgerActor() : ?Ledger {
    switch (computeLedgerCanister) {
      case null { null };
      case (?canisterId) {
        let actorRef : Ledger = actor (Principal.toText(canisterId));
        ?actorRef;
      };
    };
  };

  private func requireAdmin(caller : Principal) : Result<(), Text> {
    switch (admin) {
      case null {
        admin := ?caller;
        #ok(());
      };
      case (?principal) {
        if (principal == caller) {
          #ok(());
        } else {
          switch (governanceCanister) {
            case (?governance) {
              if (caller == governance) { #ok(()) } else { #err("admin only") };
            };
            case null { #err("admin only") };
          };
        };
      };
    };
  };

  private func isSettlementCaller(caller : Principal) : Bool {
    switch (jobMarketCanister, computeLedgerCanister) {
      case (?jobMarket, _) {
        if (caller == jobMarket) { return true };
      };
      case _ {};
    };
    switch (computeLedgerCanister) {
      case (?ledger) { caller == ledger };
      case null { false };
    };
  };

  private func isJobMarket(caller : Principal) : Bool {
    switch (jobMarketCanister) {
      case (?jobMarket) { caller == jobMarket };
      case null { false };
    };
  };

  private func simulation() : Bool {
    switch (phase) {
      case (#simulation) { true };
      case _ { false };
    };
  };

  private func invariantHolds(state : PoolState) : Bool {
    if (state.available_capital + state.deployed_capital != state.total_capital) {
      return false;
    };
    state.deployed_capital <= (state.total_capital * state.max_utilization_rate) / 100;
  };

  private func utilizationAfterUnderwrite(amount : Credits) : Nat {
    if (poolState.total_capital == 0) {
      0;
    } else {
      ((poolState.deployed_capital + amount) * 100) / poolState.total_capital;
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

  private func currentUtilizationRate() : Nat {
    if (poolState.total_capital == 0) {
      0;
    } else {
      (poolState.deployed_capital * 100) / poolState.total_capital;
    };
  };

  private func treasuryAllows(amount : Credits) : Result<(), Text> {
    if (treasuryPolicy.lockdown_enabled) {
      return #err("treasury policy is in lockdown");
    };
    if (poolState.available_capital < amount) {
      return #err("insufficient available capital");
    };
    if (poolState.available_capital - amount < treasuryPolicy.reserve_floor_credits) {
      return #err("treasury reserve floor would be violated");
    };
    if (treasuryPolicy.operating_budget_credits > 0 and amount > treasuryPolicy.operating_budget_credits) {
      return #err("treasury operating budget exceeded");
    };
    for (condition in treasuryPolicy.refusal_conditions.vals()) {
      if (condition.active) {
        return #err("active refusal condition: " # condition.condition_id);
      };
    };
    #ok(());
  };

  private func nextId(jobId : Text) : Text {
    nextRecordId += 1;
    "underwrite-" # Nat.toText(nextRecordId) # "-" # jobId;
  };

  private func distributeYield(amount : Credits) : Credits {
    if (amount == 0 or poolState.total_shares == 0) {
      return 0;
    };
    let entries = Iter.toArray(positions.entries());
    var distributed : Credits = 0;
    for ((investor, position) in entries.vals()) {
      let share = (amount * position.shares) / poolState.total_shares;
      if (share > 0) {
        distributed += share;
        positions.put(investor, {
          investor = investor;
          shares = position.shares;
          deposited_credits = position.deposited_credits;
          yield_earned = position.yield_earned + share;
          deposited_at = position.deposited_at;
          last_updated = Time.now();
        });
      };
    };
    distributed;
  };

  public shared ({ caller }) func configureExchange(
    jobMarket : ?Principal,
    computeLedger : ?Principal,
  ) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    jobMarketCanister := jobMarket;
    computeLedgerCanister := computeLedger;
    #ok(());
  };

  public shared ({ caller }) func configureGovernance(governance : ?Principal) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    governanceCanister := governance;
    #ok(());
  };

  public query func getPoolState() : async PoolState {
    poolState;
  };

  public query func getPosition(investor : InvestorId) : async ?InvestorPosition {
    positions.get(investor);
  };

  public query func listPositions() : async [InvestorPosition] {
    Iter.toArray(positions.vals());
  };

  public query func getUnderwritingRecord(recordId : Text) : async ?UnderwritingRecord {
    underwriting.get(recordId);
  };

  public query func listActiveUnderwriting() : async [UnderwritingRecord] {
    Array.filter<UnderwritingRecord>(
      Iter.toArray(underwriting.vals()),
      func(record : UnderwritingRecord) : Bool { not record.settled },
    );
  };

  public query func getUtilizationRate() : async Nat {
    currentUtilizationRate();
  };

  public query func estimateYield(credits : Credits, days : Nat) : async Credits {
    (credits * poolState.underwriting_fee_rate * days) / (100 * 365);
  };

  public query func getScienceDonations() : async [ScienceDonation] {
    scienceDonations;
  };

  public query func getScienceDisbursements() : async [ScienceDisbursement] {
    scienceDisbursements;
  };

  public query func getPhase() : async PoolPhase {
    phase;
  };

  public query func getTreasuryPolicy() : async TreasuryPolicy {
    treasuryPolicy;
  };

  public query func getTreasurySnapshot() : async TreasurySnapshot {
    {
      policy_id = treasuryPolicy.policy_id;
      total_capital = poolState.total_capital;
      available_capital = poolState.available_capital;
      deployed_capital = poolState.deployed_capital;
      science_pool_balance = poolState.science_pool_balance;
      reserve_floor_credits = treasuryPolicy.reserve_floor_credits;
      utilization_rate = currentUtilizationRate();
      lockdown_enabled = treasuryPolicy.lockdown_enabled;
      captured_at = Time.now();
    };
  };

  public query func spendAllowed(amount : Credits) : async Result<(), Text> {
    treasuryAllows(amount);
  };

  public query func getGateLog(limit : Nat) : async [(Time.Time, Text, Bool)] {
    let count = minNat(limit, gateLog.size());
    let start = gateLog.size() - count;
    Array.tabulate<(Time.Time, Text, Bool)>(
      count,
      func(index : Nat) : (Time.Time, Text, Bool) { gateLog[start + index] },
    );
  };

  public shared ({ caller }) func deposit(amount : Credits, currency : Currency) : async Result<PoolShares, Text> {
    if (amount == 0) { return #err("amount must be greater than zero") };
    switch (phase) {
      case (#micro_pool) {
        if (poolState.total_capital + amount > microPoolCap) {
          return #err("micro pool cap exceeded");
        };
      };
      case _ {};
    };
    let shares = if (poolState.total_shares == 0 or poolState.total_capital == 0) {
      amount;
    } else {
      (amount * poolState.total_shares) / poolState.total_capital;
    };
    if (shares == 0) { return #err("deposit too small to mint shares") };
    let now = Time.now();
    let current = switch (positions.get(caller)) {
      case null {
        {
          investor = caller;
          shares = 0;
          deposited_credits = 0;
          yield_earned = 0;
          deposited_at = now;
          last_updated = now;
        };
      };
      case (?position) { position };
    };
    positions.put(caller, {
      investor = caller;
      shares = current.shares + shares;
      deposited_credits = current.deposited_credits + amount;
      yield_earned = current.yield_earned;
      deposited_at = current.deposited_at;
      last_updated = now;
    });
    let nextState = {
      total_shares = poolState.total_shares + shares;
      total_capital = poolState.total_capital + amount;
      deployed_capital = poolState.deployed_capital;
      available_capital = poolState.available_capital + amount;
      science_pool_balance = poolState.science_pool_balance;
      total_yield_distributed = poolState.total_yield_distributed;
      max_utilization_rate = poolState.max_utilization_rate;
      underwriting_fee_rate = poolState.underwriting_fee_rate;
      science_allocation_rate = poolState.science_allocation_rate;
    };
    if (not invariantHolds(nextState)) {
      return #err("pool invariant violation after deposit");
    };
    poolState := nextState;
    ignore currency;
    #ok(shares);
  };

  public shared ({ caller }) func withdraw(shares : PoolShares) : async Result<Credits, Text> {
    if (shares == 0) { return #err("shares must be greater than zero") };
    if (poolState.total_shares == 0 or poolState.total_capital == 0) {
      return #err("pool is empty");
    };
    switch (positions.get(caller)) {
      case null { #err("position not found") };
      case (?position) {
        if (position.shares < shares) { return #err("insufficient shares") };
        let credits = (shares * poolState.total_capital) / poolState.total_shares;
        if (poolState.available_capital < credits) {
          return #err("withdrawal blocked: capital is deployed");
        };
        let redeemedYield = if (position.shares == 0) {
          0;
        } else {
          (position.yield_earned * shares) / position.shares;
        };
        let remainingShares = position.shares - shares;
        if (remainingShares == 0) {
          positions.delete(caller);
        } else {
          positions.put(caller, {
            investor = caller;
            shares = remainingShares;
            deposited_credits = if (position.deposited_credits > credits) { position.deposited_credits - credits } else { 0 };
            yield_earned = if (position.yield_earned > redeemedYield) { position.yield_earned - redeemedYield } else { 0 };
            deposited_at = position.deposited_at;
            last_updated = Time.now();
          });
        };
        let nextState = {
          total_shares = poolState.total_shares - shares;
          total_capital = poolState.total_capital - credits;
          deployed_capital = poolState.deployed_capital;
          available_capital = poolState.available_capital - credits;
          science_pool_balance = poolState.science_pool_balance;
          total_yield_distributed = poolState.total_yield_distributed;
          max_utilization_rate = poolState.max_utilization_rate;
          underwriting_fee_rate = poolState.underwriting_fee_rate;
          science_allocation_rate = poolState.science_allocation_rate;
        };
        if (not invariantHolds(nextState)) {
          return #err("pool invariant violation after withdraw");
        };
        poolState := nextState;
        #ok(credits);
      };
    };
  };

  public shared ({ caller }) func underwrite_job(job_id : Text, amount : Credits) : async Result<Text, Text> {
    if (not isJobMarket(caller)) { return #err("only job_market can underwrite jobs") };
    if (Text.size(job_id) == 0) { return #err("job_id must not be empty") };
    if (amount == 0) { return #err("amount must be greater than zero") };
    if (not integrityGate("underwrite_job", #internal, null)) {
      return #err("integrity gate blocked operation");
    };
    switch (treasuryAllows(amount)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (poolState.available_capital < amount) { return #err("insufficient available capital") };
    if (utilizationAfterUnderwrite(amount) > poolState.max_utilization_rate) {
      return #err("max utilization rate exceeded");
    };
    let recordId = nextId(job_id);
    let nextState = {
      total_shares = poolState.total_shares;
      total_capital = poolState.total_capital;
      deployed_capital = poolState.deployed_capital + amount;
      available_capital = poolState.available_capital - amount;
      science_pool_balance = poolState.science_pool_balance;
      total_yield_distributed = poolState.total_yield_distributed;
      max_utilization_rate = poolState.max_utilization_rate;
      underwriting_fee_rate = poolState.underwriting_fee_rate;
      science_allocation_rate = poolState.science_allocation_rate;
    };
    if (not invariantHolds(nextState)) {
      return #err("pool invariant violation after underwrite");
    };
    poolState := nextState;
    underwriting.put(recordId, {
      record_id = recordId;
      job_id = job_id;
      amount = amount;
      underwritten_at = Time.now();
      settled = false;
      outcome = null;
      fee_earned = 0;
      loss_absorbed = 0;
      simulated = simulation();
    });
    #ok(recordId);
  };

  public shared ({ caller }) func settle_underwriting(
    record_id : Text,
    outcome : UnderwritingOutcome,
    settlement_credits : Credits,
  ) : async Result<(), Text> {
    if (not isSettlementCaller(caller)) {
      return #err("only job_market or compute_ledger can settle underwriting");
    };
    switch (underwriting.get(record_id)) {
      case null { #err("underwriting record not found") };
      case (?record) {
        if (record.settled) { return #err("underwriting already settled") };
        let fee = switch (outcome) {
          case (#success) { (settlement_credits * poolState.underwriting_fee_rate) / 100 };
          case (#failure) { 0 };
        };
        let science = (fee * poolState.science_allocation_rate) / 100;
        let yieldPool = fee - science;
        let returned = switch (outcome) {
          case (#success) { record.amount };
          case (#failure) { minNat(settlement_credits, record.amount) };
        };
        let loss = record.amount - returned;
        let distributed = distributeYield(yieldPool);
        let nextState = {
          total_shares = poolState.total_shares;
          total_capital = poolState.total_capital + distributed - loss;
          deployed_capital = poolState.deployed_capital - record.amount;
          available_capital = poolState.available_capital + returned + distributed;
          science_pool_balance = poolState.science_pool_balance + science;
          total_yield_distributed = poolState.total_yield_distributed + distributed;
          max_utilization_rate = poolState.max_utilization_rate;
          underwriting_fee_rate = poolState.underwriting_fee_rate;
          science_allocation_rate = poolState.science_allocation_rate;
        };
        if (not invariantHolds(nextState)) {
          return #err("pool invariant violation after settlement");
        };
        poolState := nextState;
        underwriting.put(record_id, {
          record_id = record.record_id;
          job_id = record.job_id;
          amount = record.amount;
          underwritten_at = record.underwritten_at;
          settled = true;
          outcome = ?outcome;
          fee_earned = fee;
          loss_absorbed = loss;
          simulated = record.simulated;
        });
        #ok(());
      };
    };
  };

  public shared ({ caller }) func donateToSciencePool(amount : Credits, domain : Text) : async Result<(), Text> {
    if (amount == 0) { return #err("amount must be greater than zero") };
    if (Text.size(domain) == 0) { return #err("science domain must not be empty") };
    switch (positions.get(caller)) {
      case null { #err("position not found") };
      case (?position) {
        if (position.yield_earned < amount) {
          return #err("insufficient earned yield");
        };
        positions.put(caller, {
          investor = caller;
          shares = position.shares;
          deposited_credits = position.deposited_credits;
          yield_earned = position.yield_earned - amount;
          deposited_at = position.deposited_at;
          last_updated = Time.now();
        });
        poolState := {
          total_shares = poolState.total_shares;
          total_capital = poolState.total_capital;
          deployed_capital = poolState.deployed_capital;
          available_capital = poolState.available_capital;
          science_pool_balance = poolState.science_pool_balance + amount;
          total_yield_distributed = poolState.total_yield_distributed;
          max_utilization_rate = poolState.max_utilization_rate;
          underwriting_fee_rate = poolState.underwriting_fee_rate;
          science_allocation_rate = poolState.science_allocation_rate;
        };
        scienceDonations := Array.append<ScienceDonation>(scienceDonations, [{
          donor = caller;
          amount = amount;
          science_domain = domain;
          donated_at = Time.now();
        }]);
        #ok(());
      };
    };
  };

  public shared ({ caller }) func withdrawFromSciencePool(
    to : Principal,
    amount : Credits,
    domain : Text,
  ) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (amount == 0) { return #err("amount must be greater than zero") };
    if (poolState.science_pool_balance < amount) { return #err("insufficient science pool balance") };
    if (not integrityGate("withdraw_science_pool", #internal, null)) {
      return #err("integrity gate blocked operation");
    };
    switch (phase) {
      case (#simulation) {};
      case (#micro_pool) {};
      case _ {
        switch (ledgerActor()) {
          case null { return #err("compute ledger canister is not configured") };
          case (?ledger) {
            switch (await ledger.transfer(to, amount)) {
              case (#Ok(_balance)) {};
              case (#Err(message)) { return #err("ledger transfer failed: " # message) };
            };
          };
        };
      };
    };
    poolState := {
      total_shares = poolState.total_shares;
      total_capital = poolState.total_capital;
      deployed_capital = poolState.deployed_capital;
      available_capital = poolState.available_capital;
      science_pool_balance = poolState.science_pool_balance - amount;
      total_yield_distributed = poolState.total_yield_distributed;
      max_utilization_rate = poolState.max_utilization_rate;
      underwriting_fee_rate = poolState.underwriting_fee_rate;
      science_allocation_rate = poolState.science_allocation_rate;
    };
    scienceDisbursements := Array.append<ScienceDisbursement>(scienceDisbursements, [{
      to = to;
      amount = amount;
      science_domain = domain;
      disbursed_at = Time.now();
      simulated = simulation();
    }]);
    #ok(());
  };

  public shared ({ caller }) func setPhase(nextPhase : PoolPhase) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    phase := nextPhase;
    #ok(());
  };

  public shared ({ caller }) func setTreasuryPolicy(nextPolicy : TreasuryPolicy) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (Text.size(nextPolicy.policy_id) == 0) {
      return #err("policy_id must not be empty");
    };
    if (Text.size(nextPolicy.version) == 0) {
      return #err("version must not be empty");
    };
    if (nextPolicy.reinvestment_rate_pct > 100) {
      return #err("reinvestment_rate_pct must be between 0 and 100");
    };
    for (tier in nextPolicy.balance_tiers.vals()) {
      if (tier.reserve_pct > 100) {
        return #err("balance tier reserve_pct must be between 0 and 100");
      };
      switch (tier.max_credits) {
        case null {};
        case (?maxCredits) {
          if (maxCredits < tier.min_credits) {
            return #err("balance tier max_credits cannot be below min_credits");
          };
        };
      };
    };
    treasuryPolicy := nextPolicy;
    #ok(());
  };

  public shared ({ caller }) func setMaxUtilizationRate(rate : Nat) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (rate > 100) { return #err("rate must be between 0 and 100") };
    let nextState = {
      total_shares = poolState.total_shares;
      total_capital = poolState.total_capital;
      deployed_capital = poolState.deployed_capital;
      available_capital = poolState.available_capital;
      science_pool_balance = poolState.science_pool_balance;
      total_yield_distributed = poolState.total_yield_distributed;
      max_utilization_rate = rate;
      underwriting_fee_rate = poolState.underwriting_fee_rate;
      science_allocation_rate = poolState.science_allocation_rate;
    };
    if (not invariantHolds(nextState)) {
      return #err("new utilization rate violates deployed capital invariant");
    };
    poolState := nextState;
    #ok(());
  };

  public shared ({ caller }) func setUnderwritingFeeRate(rate : Nat) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (rate > 50) { return #err("underwriting fee rate must be between 0 and 50") };
    poolState := {
      total_shares = poolState.total_shares;
      total_capital = poolState.total_capital;
      deployed_capital = poolState.deployed_capital;
      available_capital = poolState.available_capital;
      science_pool_balance = poolState.science_pool_balance;
      total_yield_distributed = poolState.total_yield_distributed;
      max_utilization_rate = poolState.max_utilization_rate;
      underwriting_fee_rate = rate;
      science_allocation_rate = poolState.science_allocation_rate;
    };
    #ok(());
  };

  public shared ({ caller }) func setScienceAllocationRate(rate : Nat) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (rate > 100) { return #err("science allocation rate must be between 0 and 100") };
    poolState := {
      total_shares = poolState.total_shares;
      total_capital = poolState.total_capital;
      deployed_capital = poolState.deployed_capital;
      available_capital = poolState.available_capital;
      science_pool_balance = poolState.science_pool_balance;
      total_yield_distributed = poolState.total_yield_distributed;
      max_utilization_rate = poolState.max_utilization_rate;
      underwriting_fee_rate = poolState.underwriting_fee_rate;
      science_allocation_rate = rate;
    };
    #ok(());
  };

  public shared ({ caller }) func setMicroPoolCap(cap : Credits) : async Result<(), Text> {
    switch (requireAdmin(caller)) {
      case (#err(message)) { return #err(message) };
      case (#ok(())) {};
    };
    if (cap < poolState.total_capital) {
      return #err("cap cannot be below current total capital");
    };
    microPoolCap := cap;
    #ok(());
  };
};
