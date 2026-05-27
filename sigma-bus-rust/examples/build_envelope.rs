use ed25519_dalek::SigningKey;
use serde_json::json;
use sigma_bus_rust::{DeliveryMode, SigmaBusEnvelope, SigmaRouting, SigmaSource};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let signing_key = SigningKey::from_bytes(&[7_u8; 32]);
    let source = SigmaSource::new(
        "canister:compute_ledger",
        "compute_ledger",
        "icp_canister",
        "sovereign_local",
    );

    let mut envelope =
        SigmaBusEnvelope::builder("treasury.escrow.locked", "EscrowLockedPayload", source)
            .routing(
                SigmaRouting::new("bus_topic", "treasury.escrow.locked")
                    .delivery(DeliveryMode::AtLeastOnce),
            )
            .payload(&json!({
                "job_id": "job-001",
                "payer": "aaaaa-aa",
                "payee": "bbbbbb-bb",
                "amount": "1000"
            }))?
            .build()?;

    envelope.sign_last_provenance(&signing_key)?;
    println!("{}", serde_json::to_string_pretty(&envelope)?);
    Ok(())
}
