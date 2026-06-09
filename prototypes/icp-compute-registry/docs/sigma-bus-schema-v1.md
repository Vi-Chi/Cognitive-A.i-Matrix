# Sigma Bus Schema v1

Generated: 2026-05-27

This document defines the formal Sigma Bus envelope used by the Autopoiesis ICP exchange. It connects local Rust nodes, the Cognitive Matrix, Wibo maritime agents, and on-chain canisters through one signed, provenance-carrying event shape.

## Core Envelope

JSON schema identifier: `sigma_bus/v1/envelope`

```json
{
  "$schema": "sigma_bus/v1/envelope",
  "envelope": {
    "event_id": "uuid-v4",
    "schema_version": "1.0.0",
    "emitted_at": "ISO-8601 nanosecond UTC",
    "expires_at": "ISO-8601 or null",
    "privacy_tier": "sovereign | confidential | internal | public",
    "lens_state": "positive | negative | uncertain | none",
    "event_type": "string",
    "source": {
      "agent_id": "did:icp:<principal> or local:<name>",
      "node_id": "string",
      "platform": "hailo8 | hailo10h | jetson | rpi4 | rpi5 | wibo_maritime | icp_canister | cloud",
      "location_class": "sovereign_local | vessel | marina | cloud | unknown"
    },
    "provenance_chain": [
      {
        "agent_id": "string",
        "action": "originated | transformed | forwarded | verified",
        "timestamp": "ISO-8601",
        "signature": "ed25519 hex or null"
      }
    ],
    "routing": {
      "target": "broadcast | agent_id | canister_id | bus_topic",
      "topic": "string",
      "priority": "critical | high | normal | low",
      "delivery": "at_most_once | at_least_once"
    },
    "payload_type": "string",
    "payload": {}
  }
}
```

The ICP canister representation stores `payload` as JSON text because Candid does not carry arbitrary JSON objects directly. The Rust client crate serializes typed payloads into that field.

## Provenance Chain Rules

1. The origin node MUST set `provenance_chain[0]` with `action: "originated"`.
2. Any transformer MUST append a new entry with `action: "transformed"`.
3. Any forwarder MUST append a new entry with `action: "forwarded"`.
4. Any ICP canister that accepts an on-chain write SHOULD append or mirror an entry with `action: "verified"`.
5. The chain is append-only. No entry can be removed or modified.
6. The privacy tier cannot be downgraded through the chain. `sovereign` cannot become `public`, `confidential`, or `internal`.
7. The lens state cannot be modified by economic systems at any hop.

## Event Type Registry

### Compute / Autopoiesis

- `compute.job.posted`
- `compute.job.bid`
- `compute.job.accepted`
- `compute.job.completed`
- `compute.job.failed`
- `compute.decision.made`
- `compute.procurement.started`
- `compute.procurement.settled`
- `compute.provider.registered`
- `compute.provider.heartbeat`

### Treasury / Capital

- `treasury.credit.earned`
- `treasury.credit.spent`
- `treasury.escrow.locked`
- `treasury.escrow.released`
- `treasury.escrow.slashed`
- `treasury.pool.deposited`
- `treasury.pool.withdrawn`
- `treasury.science.donated`
- `treasury.policy.updated`

### Cognitive Matrix

- `matrix.memory.stored`
- `matrix.memory.clustered`
- `matrix.memory.decayed`
- `matrix.audit.triggered`
- `matrix.audit.result`
- `matrix.dream.started`
- `matrix.dream.completed`
- `matrix.integrity.gate`
- `matrix.lens.transition`

### Observe / Sensor

- `observe.sensor.reading`
- `observe.nmea.sentence`
- `observe.position.updated`
- `observe.weather.reading`
- `observe.vessel.state`
- `observe.alert.triggered`

### System / Infrastructure

- `system.agent.registered`
- `system.agent.heartbeat`
- `system.canister.upgraded`
- `system.bus.error`
- `system.governance.proposed`
- `system.governance.enacted`

## Payload Schemas

### ComputeDecisionPayload

```json
{
  "job_id": "string",
  "decision": "approved | rejected | deferred",
  "rejection_reason": "null | integrity_gate | insufficient_credits | privacy_violation | policy | no_provider",
  "cost_estimate_credits": "Nat",
  "value_estimate": "float 0.0-1.0",
  "net_value": "float",
  "integrity_gate_result": "pass | fail | override_attempted",
  "selected_provider_id": "string or null",
  "selected_tier": "sovereign_local | confidential | internal | public",
  "lens_state_at_decision": "positive | negative | uncertain",
  "override_attempted": "bool",
  "decided_by": "agent_id",
  "decided_at": "ISO-8601"
}
```

### IntegrityGatePayload

```json
{
  "gate_id": "uuid",
  "operation": "string",
  "canister": "string",
  "privacy_tier": "string",
  "lens_state": "string",
  "result": "pass | fail",
  "reason": "string",
  "economic_pressure_detected": "bool",
  "veto_exercised": "bool"
}
```

### SensorReadingPayload

```json
{
  "sensor_id": "string",
  "sensor_type": "pressure | temperature | humidity | wind_speed | wind_direction | heading | depth | gps | ais | voltage | current",
  "unit": "string",
  "value": "float",
  "raw_nmea": "string or null",
  "vessel_state": "at_anchor | underway | marina | moored | unknown",
  "signal_quality": "float 0.0-1.0"
}
```

### LensTransitionPayload

```json
{
  "from_lens": "positive | negative | uncertain",
  "to_lens": "positive | negative | uncertain",
  "trigger": "string",
  "confidence": "float 0.0-1.0",
  "economic_influence_detected": "bool",
  "audit_369_clear": "bool"
}
```

### EscrowLockedPayload

```json
{
  "job_id": "string",
  "payer": "principal",
  "payee": "principal",
  "amount": "u128",
  "locked_at": "u64 nanoseconds since epoch"
}
```

### EscrowReleasedPayload

```json
{
  "job_id": "string",
  "payer": "principal",
  "payee": "principal",
  "amount": "u128",
  "released_at": "u64 nanoseconds since epoch"
}
```

### EscrowSlashedPayload

```json
{
  "account": "principal",
  "amount": "u128",
  "slashed_at": "u64 nanoseconds since epoch",
  "remaining_stake": "u128"
}
```

### CreditEarnedPayload

```json
{
  "account": "principal",
  "amount": "u128",
  "new_balance": "u128",
  "earned_at": "u64 nanoseconds since epoch",
  "source": "mint | escrow_release | refund"
}
```

### CreditSpentPayload

```json
{
  "account": "principal",
  "counterparty": "principal or null",
  "amount": "u128",
  "new_balance": "u128",
  "spent_at": "u64 nanoseconds since epoch",
  "reason": "transfer | escrow_lock | stake | donate_to_science"
}
```

### PoolDepositedPayload

```json
{
  "investor": "principal",
  "amount": "u128",
  "shares_minted": "u128",
  "deposited_at": "u64 nanoseconds since epoch"
}
```

### PoolWithdrawnPayload

```json
{
  "investor": "principal",
  "shares_burned": "u128",
  "credits_redeemed": "u128",
  "withdrawn_at": "u64 nanoseconds since epoch"
}
```

### GovernanceProposalPayload

```json
{
  "proposal_id": "string",
  "target_canister": "string",
  "parameter": "string",
  "current_value": "string",
  "proposed_value": "string",
  "justification": "string",
  "proposed_by": "principal",
  "proposed_at": "ISO-8601",
  "enacted_at": "ISO-8601 or null"
}
```

### GovernanceEnactedPayload

```json
{
  "proposal_id": "string",
  "target_canister": "string",
  "parameter": "string",
  "current_value": "string",
  "proposed_value": "string",
  "justification": "string",
  "proposed_by": "principal",
  "proposed_at": "ISO-8601",
  "enacted_at": "ISO-8601 or null"
}
```

## Signature Rules

- The signature algorithm is Ed25519.
- The signed bytes are the canonical JSON representation of the envelope with the signing provenance entry's `signature` set to `null`.
- Hex signatures are lowercase and 128 hex characters.
- Signature verification failure MUST NOT silently mutate an event into a trusted event. The adapter records verification status separately.
- Signature verification hooks are present in the canister adapter; production key registry integration remains a follow-up.

## Privacy And Lens Invariants

- `sovereign` and `confidential` events must not be routed to public external providers.
- Economic systems may record the current lens state but must not change it.
- Integrity gate failures and override attempts are first-class events through `matrix.integrity.gate`.
- Governance cannot disable or override integrity-gate vetoes.
