use candid::{CandidType, Encode, Principal};
use ic_cdk::{init, query, update};
use serde::{Deserialize, Serialize};
use std::cell::RefCell;
use std::collections::HashMap;

type Credits = u128;

#[derive(Clone, Debug, CandidType, Deserialize, Serialize)]
pub struct EscrowEntry {
    pub job_id: String,
    pub payer: Principal,
    pub payee: Principal,
    pub amount: Credits,
    pub locked_at: u64,
    pub released: bool,
}

#[derive(Clone, Debug, CandidType, Deserialize, Serialize)]
pub struct LedgerEntry {
    pub account: Principal,
    pub balance: Credits,
    pub staked: Credits,
    pub last_updated: u64,
}

#[derive(Clone, Debug, CandidType, Deserialize, Serialize)]
pub struct SigmaSource {
    pub agent_id: String,
    pub node_id: String,
    pub platform: String,
    pub location_class: String,
}

#[derive(Clone, Debug, CandidType, Deserialize, Serialize)]
pub struct SigmaProvenanceEntry {
    pub agent_id: String,
    pub action: String,
    pub timestamp: String,
    pub signature: Option<String>,
}

#[derive(Clone, Debug, CandidType, Deserialize, Serialize)]
pub struct SigmaRouting {
    pub target: String,
    pub topic: String,
    pub priority: String,
    pub delivery: String,
}

#[derive(Clone, Debug, CandidType, Deserialize, Serialize)]
pub struct SigmaBusEnvelope {
    pub event_id: String,
    pub schema_version: String,
    pub emitted_at: String,
    pub expires_at: Option<String>,
    pub privacy_tier: String,
    pub lens_state: String,
    pub event_type: String,
    pub source: SigmaSource,
    pub provenance_chain: Vec<SigmaProvenanceEntry>,
    pub routing: SigmaRouting,
    pub payload_type: String,
    pub payload: String,
}

#[derive(Clone, Debug, CandidType, Deserialize, Serialize)]
pub struct LedgerSigmaEvent {
    pub event_id: String,
    pub event_type: String,
    pub payload_type: String,
    pub payload: String,
    pub emitted_at: u64,
}

#[derive(Default)]
struct State {
    admin: Option<Principal>,
    sigma_bus: Option<Principal>,
    balances: HashMap<Principal, LedgerEntry>,
    escrows: HashMap<String, EscrowEntry>,
    total_supply: Credits,
    science_pool_balance: Credits,
    sigma_events: Vec<LedgerSigmaEvent>,
    next_sigma_event_id: u64,
}

thread_local! {
    static STATE: RefCell<State> = RefCell::new(State::default());
}

#[init]
fn init() {
    STATE.with(|state| {
        state.borrow_mut().admin = Some(ic_cdk::api::msg_caller());
    });
}

fn now() -> u64 {
    ic_cdk::api::time()
}

fn zero_entry(account: Principal) -> LedgerEntry {
    LedgerEntry {
        account,
        balance: 0,
        staked: 0,
        last_updated: now(),
    }
}

fn is_admin(principal: Principal) -> bool {
    STATE.with(|state| state.borrow().admin == Some(principal))
}

fn available(entry: &LedgerEntry) -> Credits {
    entry.balance.saturating_sub(entry.staked)
}

fn json_escape(value: &str) -> String {
    value
        .replace('\\', "\\\\")
        .replace('"', "\\\"")
        .replace('\n', "\\n")
        .replace('\r', "\\r")
        .replace('\t', "\\t")
}

fn json_field(name: &str, value: &str) -> String {
    format!("\"{}\":\"{}\"", name, json_escape(value))
}

fn principal_field(name: &str, value: Principal) -> String {
    json_field(name, &value.to_text())
}

fn amount_field(name: &str, value: Credits) -> String {
    format!("\"{}\":\"{}\"", name, value)
}

fn time_field(name: &str, value: u64) -> String {
    format!("\"{}\":{}", name, value)
}

fn object(fields: &[String]) -> String {
    format!("{{{}}}", fields.join(","))
}

fn push_sigma_event(event_type: &str, payload_type: &str, payload: String) {
    let emitted_at = now();
    let (event, sigma_bus) = STATE.with(|state| {
        let mut state = state.borrow_mut();
        state.next_sigma_event_id = state.next_sigma_event_id.saturating_add(1);
        let event = LedgerSigmaEvent {
            event_id: format!("ledger-{}-{}", emitted_at, state.next_sigma_event_id),
            event_type: event_type.to_string(),
            payload_type: payload_type.to_string(),
            payload,
            emitted_at,
        };
        state.sigma_events.push(event.clone());
        if state.sigma_events.len() > 1000 {
            let overflow = state.sigma_events.len() - 1000;
            state.sigma_events.drain(0..overflow);
        }
        (event, state.sigma_bus)
    });

    if let Some(canister_id) = sigma_bus {
        let envelope = SigmaBusEnvelope {
            event_id: event.event_id.clone(),
            schema_version: "1.0.0".to_string(),
            emitted_at: event.emitted_at.to_string(),
            expires_at: None,
            privacy_tier: "internal".to_string(),
            lens_state: "none".to_string(),
            event_type: event.event_type.clone(),
            source: SigmaSource {
                agent_id: format!("canister:{}", ic_cdk::api::canister_self().to_text()),
                node_id: "compute_ledger".to_string(),
                platform: "icp_canister".to_string(),
                location_class: "sovereign_local".to_string(),
            },
            provenance_chain: vec![SigmaProvenanceEntry {
                agent_id: "canister:compute_ledger".to_string(),
                action: "originated".to_string(),
                timestamp: event.emitted_at.to_string(),
                signature: None,
            }],
            routing: SigmaRouting {
                target: "bus_topic".to_string(),
                topic: "treasury".to_string(),
                priority: "normal".to_string(),
                delivery: "at_least_once".to_string(),
            },
            payload_type: event.payload_type.clone(),
            payload: event.payload.clone(),
        };
        if let Ok(args) = Encode!(&envelope) {
            ic0::call_new_oneway(canister_id.as_slice(), "emitEvent");
            ic0::call_data_append(&args);
            let _ = ic0::call_perform();
        }
    }
}

fn with_entry<F, R>(account: Principal, f: F) -> R
where
    F: FnOnce(&mut LedgerEntry) -> R,
{
    STATE.with(|state| {
        let mut state = state.borrow_mut();
        let entry = state
            .balances
            .entry(account)
            .or_insert_with(|| zero_entry(account));
        f(entry)
    })
}

#[query(name = "getBalance")]
fn get_balance(account: Principal) -> Credits {
    STATE.with(|state| {
        state
            .borrow()
            .balances
            .get(&account)
            .map(|entry| entry.balance)
            .unwrap_or(0)
    })
}

#[query(name = "getStake")]
fn get_stake(account: Principal) -> Credits {
    STATE.with(|state| {
        state
            .borrow()
            .balances
            .get(&account)
            .map(|entry| entry.staked)
            .unwrap_or(0)
    })
}

#[query(name = "getLedgerEntry")]
fn get_ledger_entry(account: Principal) -> LedgerEntry {
    STATE.with(|state| {
        state
            .borrow()
            .balances
            .get(&account)
            .cloned()
            .unwrap_or_else(|| zero_entry(account))
    })
}

#[query(name = "getTotalSupply")]
fn get_total_supply() -> Credits {
    STATE.with(|state| state.borrow().total_supply)
}

#[query(name = "getEscrow")]
fn get_escrow(job_id: String) -> Option<EscrowEntry> {
    STATE.with(|state| state.borrow().escrows.get(&job_id).cloned())
}

#[query(name = "getSciencePoolBalance")]
fn get_science_pool_balance() -> Credits {
    STATE.with(|state| state.borrow().science_pool_balance)
}

#[query(name = "getSigmaEvents")]
fn get_sigma_events(limit: u64) -> Vec<LedgerSigmaEvent> {
    STATE.with(|state| {
        let state = state.borrow();
        let len = state.sigma_events.len();
        let count = std::cmp::min(limit as usize, len);
        state.sigma_events[len - count..].to_vec()
    })
}

#[query(name = "getSigmaBusCanister")]
fn get_sigma_bus_canister() -> Option<Principal> {
    STATE.with(|state| state.borrow().sigma_bus)
}

#[update(name = "configureSigmaBus")]
fn configure_sigma_bus(canister: Option<Principal>) -> Result<(), String> {
    if !is_admin(ic_cdk::api::msg_caller()) {
        return Err("only admin can configure sigma bus".to_string());
    }
    STATE.with(|state| {
        state.borrow_mut().sigma_bus = canister;
    });
    Ok(())
}

#[update]
fn mint(to: Principal, amount: Credits) -> Result<Credits, String> {
    if amount == 0 {
        return Err("amount must be greater than zero".to_string());
    }
    if !is_admin(ic_cdk::api::msg_caller()) {
        return Err("only admin can mint".to_string());
    }

    let new_balance = STATE.with(|state| {
        let mut state = state.borrow_mut();
        let new_balance = {
            let entry = state.balances.entry(to).or_insert_with(|| zero_entry(to));
            entry.balance = entry
                .balance
                .checked_add(amount)
                .ok_or_else(|| "balance overflow".to_string())?;
            entry.last_updated = now();
            entry.balance
        };
        state.total_supply = state
            .total_supply
            .checked_add(amount)
            .ok_or_else(|| "total supply overflow".to_string())?;
        Ok::<Credits, String>(new_balance)
    })?;
    push_sigma_event(
        "treasury.credit.earned",
        "CreditEarnedPayload",
        object(&[
            principal_field("account", to),
            amount_field("amount", amount),
            amount_field("new_balance", new_balance),
            time_field("earned_at", now()),
            json_field("source", "mint"),
        ]),
    );
    Ok(new_balance)
}

#[update]
fn transfer(to: Principal, amount: Credits) -> Result<Credits, String> {
    if amount == 0 {
        return Err("amount must be greater than zero".to_string());
    }
    let from = ic_cdk::api::msg_caller();
    if from == to {
        return Err("cannot transfer to self".to_string());
    }

    let new_sender_balance = STATE.with(|state| {
        let mut state = state.borrow_mut();
        let new_sender_balance = {
            let sender = state
                .balances
                .entry(from)
                .or_insert_with(|| zero_entry(from));
            if available(sender) < amount {
                return Err("insufficient spendable balance".to_string());
            }
            sender.balance -= amount;
            sender.last_updated = now();
            sender.balance
        };

        let receiver = state.balances.entry(to).or_insert_with(|| zero_entry(to));
        receiver.balance = receiver
            .balance
            .checked_add(amount)
            .ok_or_else(|| "receiver balance overflow".to_string())?;
        receiver.last_updated = now();
        Ok::<Credits, String>(new_sender_balance)
    })?;
    push_sigma_event(
        "treasury.credit.spent",
        "CreditSpentPayload",
        object(&[
            principal_field("account", from),
            principal_field("counterparty", to),
            amount_field("amount", amount),
            amount_field("new_balance", new_sender_balance),
            time_field("spent_at", now()),
            json_field("reason", "transfer"),
        ]),
    );
    Ok(new_sender_balance)
}

#[update(name = "lockEscrow")]
fn lock_escrow(job_id: String, payee: Principal, amount: Credits) -> Result<(), String> {
    if job_id.trim().is_empty() {
        return Err("job_id must not be empty".to_string());
    }
    if amount == 0 {
        return Err("amount must be greater than zero".to_string());
    }
    let payer = ic_cdk::api::msg_caller();

    STATE.with(|state| {
        let mut state = state.borrow_mut();
        if state.escrows.contains_key(&job_id) {
            return Err("escrow already exists".to_string());
        }

        let payer_entry = state
            .balances
            .entry(payer)
            .or_insert_with(|| zero_entry(payer));
        if available(payer_entry) < amount {
            return Err("insufficient spendable balance".to_string());
        }
        payer_entry.balance -= amount;
        payer_entry.last_updated = now();

        state.escrows.insert(
            job_id.clone(),
            EscrowEntry {
                job_id: job_id.clone(),
                payer,
                payee,
                amount,
                locked_at: now(),
                released: false,
            },
        );
        Ok::<(), String>(())
    })?;
    push_sigma_event(
        "treasury.escrow.locked",
        "EscrowLockedPayload",
        object(&[
            json_field("job_id", &job_id),
            principal_field("payer", payer),
            principal_field("payee", payee),
            amount_field("amount", amount),
            time_field("locked_at", now()),
        ]),
    );
    Ok(())
}

#[update(name = "releaseEscrow")]
fn release_escrow(job_id: String) -> Result<(), String> {
    let (payer, payee, amount) = STATE.with(|state| {
        let mut state = state.borrow_mut();
        let (payer, payee, amount) = {
            let escrow = state
                .escrows
                .get_mut(&job_id)
                .ok_or_else(|| "escrow not found".to_string())?;
            if escrow.released {
                return Err("escrow already released".to_string());
            }
            escrow.released = true;
            (escrow.payer, escrow.payee, escrow.amount)
        };

        let payee_entry = state
            .balances
            .entry(payee)
            .or_insert_with(|| zero_entry(payee));
        payee_entry.balance = payee_entry
            .balance
            .checked_add(amount)
            .ok_or_else(|| "payee balance overflow".to_string())?;
        payee_entry.last_updated = now();
        Ok::<(Principal, Principal, Credits), String>((payer, payee, amount))
    })?;
    push_sigma_event(
        "treasury.escrow.released",
        "EscrowReleasedPayload",
        object(&[
            json_field("job_id", &job_id),
            principal_field("payer", payer),
            principal_field("payee", payee),
            amount_field("amount", amount),
            time_field("released_at", now()),
        ]),
    );
    Ok(())
}

#[update(name = "refundEscrow")]
fn refund_escrow(job_id: String) -> Result<(), String> {
    let (payer, payee, amount) = STATE.with(|state| {
        let mut state = state.borrow_mut();
        let (payer, payee, amount) = {
            let escrow = state
                .escrows
                .get_mut(&job_id)
                .ok_or_else(|| "escrow not found".to_string())?;
            if escrow.released {
                return Err("escrow already released".to_string());
            }
            escrow.released = true;
            (escrow.payer, escrow.payee, escrow.amount)
        };

        let payer_entry = state
            .balances
            .entry(payer)
            .or_insert_with(|| zero_entry(payer));
        payer_entry.balance = payer_entry
            .balance
            .checked_add(amount)
            .ok_or_else(|| "payer balance overflow".to_string())?;
        payer_entry.last_updated = now();
        Ok::<(Principal, Principal, Credits), String>((payer, payee, amount))
    })?;
    push_sigma_event(
        "treasury.escrow.released",
        "EscrowReleasedPayload",
        object(&[
            json_field("job_id", &job_id),
            principal_field("payer", payer),
            principal_field("payee", payee),
            amount_field("amount", amount),
            time_field("released_at", now()),
            json_field("release_kind", "refund"),
        ]),
    );
    Ok(())
}

#[update]
fn stake(amount: Credits) -> Result<(), String> {
    if amount == 0 {
        return Err("amount must be greater than zero".to_string());
    }
    let account = ic_cdk::api::msg_caller();
    with_entry(account, |entry| {
        if available(entry) < amount {
            return Err("insufficient spendable balance".to_string());
        }
        entry.staked = entry
            .staked
            .checked_add(amount)
            .ok_or_else(|| "stake overflow".to_string())?;
        entry.last_updated = now();
        Ok(())
    })?;
    push_sigma_event(
        "treasury.credit.spent",
        "CreditSpentPayload",
        object(&[
            principal_field("account", account),
            json_field("counterparty", "null"),
            amount_field("amount", amount),
            amount_field("new_balance", get_balance(account)),
            time_field("spent_at", now()),
            json_field("reason", "stake"),
        ]),
    );
    Ok(())
}

#[update]
fn unstake(amount: Credits) -> Result<(), String> {
    if amount == 0 {
        return Err("amount must be greater than zero".to_string());
    }
    let account = ic_cdk::api::msg_caller();
    with_entry(account, |entry| {
        if entry.staked < amount {
            return Err("insufficient stake".to_string());
        }
        entry.staked -= amount;
        entry.last_updated = now();
        Ok(())
    })?;
    push_sigma_event(
        "treasury.credit.earned",
        "CreditEarnedPayload",
        object(&[
            principal_field("account", account),
            amount_field("amount", amount),
            amount_field("new_balance", get_balance(account)),
            time_field("earned_at", now()),
            json_field("source", "unstake"),
        ]),
    );
    Ok(())
}

#[update(name = "slashStake")]
fn slash_stake(account: Principal, amount: Credits) -> Result<(), String> {
    if amount == 0 {
        return Err("amount must be greater than zero".to_string());
    }
    if !is_admin(ic_cdk::api::msg_caller()) {
        return Err("only admin can slash stake".to_string());
    }

    let remaining_stake = STATE.with(|state| {
        let mut state = state.borrow_mut();
        let remaining_stake = {
            let entry = state
                .balances
                .entry(account)
                .or_insert_with(|| zero_entry(account));
            if entry.staked < amount {
                return Err("insufficient staked credits".to_string());
            }
            entry.staked -= amount;
            entry.balance = entry
                .balance
                .checked_sub(amount)
                .ok_or_else(|| "balance underflow".to_string())?;
            entry.last_updated = now();
            entry.staked
        };
        state.total_supply = state
            .total_supply
            .checked_sub(amount)
            .ok_or_else(|| "total supply underflow".to_string())?;
        Ok::<Credits, String>(remaining_stake)
    })?;
    push_sigma_event(
        "treasury.escrow.slashed",
        "EscrowSlashedPayload",
        object(&[
            principal_field("account", account),
            amount_field("amount", amount),
            time_field("slashed_at", now()),
            amount_field("remaining_stake", remaining_stake),
        ]),
    );
    Ok(())
}

#[update(name = "donateToSciencePool")]
fn donate_to_science_pool(amount: Credits) -> Result<(), String> {
    if amount == 0 {
        return Err("amount must be greater than zero".to_string());
    }
    let donor = ic_cdk::api::msg_caller();

    STATE.with(|state| {
        let mut state = state.borrow_mut();
        {
            let donor_entry = state
                .balances
                .entry(donor)
                .or_insert_with(|| zero_entry(donor));
            if available(donor_entry) < amount {
                return Err("insufficient spendable balance".to_string());
            }
            donor_entry.balance -= amount;
            donor_entry.last_updated = now();
        }
        state.science_pool_balance = state
            .science_pool_balance
            .checked_add(amount)
            .ok_or_else(|| "science pool overflow".to_string())?;
        Ok::<(), String>(())
    })?;
    push_sigma_event(
        "treasury.science.donated",
        "CreditSpentPayload",
        object(&[
            principal_field("account", donor),
            json_field("counterparty", "science_pool"),
            amount_field("amount", amount),
            amount_field("new_balance", get_balance(donor)),
            time_field("spent_at", now()),
            json_field("reason", "donate_to_science"),
        ]),
    );
    Ok(())
}

ic_cdk::export_candid!();
