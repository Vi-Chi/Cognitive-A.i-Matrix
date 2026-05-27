# sigma-bus-rust

Rust client types and helpers for Sigma Bus v1 envelopes.

This crate provides a small, transport-neutral surface:

- Typed envelope, source, provenance, routing, privacy, and lens-state models.
- Builder helpers that create valid `schema_version = "1.0.0"` envelopes.
- JSON payload-text validation before publish.
- Ed25519 signing and verification hooks for provenance entries.
- A transport trait plus an in-memory transport for tests and local adapters.

## Quick Start

```rust
use serde_json::json;
use sigma_bus_rust::{DeliveryMode, SigmaBusEnvelope, SigmaRouting, SigmaSource};

let source = SigmaSource::new(
    "canister:compute_ledger",
    "compute_ledger",
    "icp_canister",
    "sovereign_local",
);
let envelope = SigmaBusEnvelope::builder(
    "treasury.credit.earned",
    "CreditEarnedPayload",
    source,
)
.routing(SigmaRouting::new("bus_topic", "treasury.credit.earned").delivery(DeliveryMode::AtLeastOnce))
.payload(&json!({
    "account": "aaaaa-aa",
    "amount": "100",
    "source": "mint"
}))?
.build()?;
# Ok::<(), Box<dyn std::error::Error>>(())
```

## Signature Model

`sign_provenance_entry` signs the canonical JSON bytes of the envelope with the target provenance entry signature cleared. The signature is stored as a 128-character lowercase hex Ed25519 signature in `provenance_chain`.

Production transports should treat signature verification failures as hard rejects before the event is routed or stored.

## License

GPL-3.0-only, matching the parent Sigma Bus repository.
