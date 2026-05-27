use chrono::{DateTime, SecondsFormat, Utc};
use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use serde::{Deserialize, Serialize};
use std::cell::RefCell;
use thiserror::Error;
use uuid::Uuid;

pub const SIGMA_BUS_SCHEMA_VERSION: &str = "1.0.0";

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PrivacyTier {
    Sovereign,
    Confidential,
    Internal,
    Public,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LensState {
    Positive,
    Negative,
    Uncertain,
    None,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProvenanceAction {
    Originated,
    Transformed,
    Forwarded,
    Verified,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RoutingPriority {
    Critical,
    High,
    Normal,
    Low,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DeliveryMode {
    AtMostOnce,
    AtLeastOnce,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct SigmaSource {
    pub agent_id: String,
    pub node_id: String,
    pub platform: String,
    pub location_class: String,
}

impl SigmaSource {
    pub fn new(
        agent_id: impl Into<String>,
        node_id: impl Into<String>,
        platform: impl Into<String>,
        location_class: impl Into<String>,
    ) -> Self {
        Self {
            agent_id: agent_id.into(),
            node_id: node_id.into(),
            platform: platform.into(),
            location_class: location_class.into(),
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct SigmaProvenanceEntry {
    pub agent_id: String,
    pub action: ProvenanceAction,
    pub timestamp: String,
    pub signature: Option<String>,
}

impl SigmaProvenanceEntry {
    pub fn new(
        agent_id: impl Into<String>,
        action: ProvenanceAction,
        timestamp: impl Into<String>,
    ) -> Self {
        Self {
            agent_id: agent_id.into(),
            action,
            timestamp: timestamp.into(),
            signature: None,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct SigmaRouting {
    pub target: String,
    pub topic: String,
    pub priority: RoutingPriority,
    pub delivery: DeliveryMode,
}

impl SigmaRouting {
    pub fn new(target: impl Into<String>, topic: impl Into<String>) -> Self {
        Self {
            target: target.into(),
            topic: topic.into(),
            priority: RoutingPriority::Normal,
            delivery: DeliveryMode::AtLeastOnce,
        }
    }

    pub fn priority(mut self, priority: RoutingPriority) -> Self {
        self.priority = priority;
        self
    }

    pub fn delivery(mut self, delivery: DeliveryMode) -> Self {
        self.delivery = delivery;
        self
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct SigmaBusEnvelope {
    pub event_id: String,
    pub schema_version: String,
    pub emitted_at: String,
    pub expires_at: Option<String>,
    pub privacy_tier: PrivacyTier,
    pub lens_state: LensState,
    pub event_type: String,
    pub source: SigmaSource,
    pub provenance_chain: Vec<SigmaProvenanceEntry>,
    pub routing: SigmaRouting,
    pub payload_type: String,
    pub payload: String,
}

impl SigmaBusEnvelope {
    pub fn builder(
        event_type: impl Into<String>,
        payload_type: impl Into<String>,
        source: SigmaSource,
    ) -> SigmaEnvelopeBuilder {
        SigmaEnvelopeBuilder::new(event_type, payload_type, source)
    }

    pub fn validate(&self) -> Result<(), SigmaBusError> {
        if self.schema_version != SIGMA_BUS_SCHEMA_VERSION {
            return Err(SigmaBusError::UnsupportedSchemaVersion(
                self.schema_version.clone(),
            ));
        }
        require_non_empty("event_id", &self.event_id)?;
        require_non_empty("emitted_at", &self.emitted_at)?;
        require_non_empty("event_type", &self.event_type)?;
        require_non_empty("source.agent_id", &self.source.agent_id)?;
        require_non_empty("source.node_id", &self.source.node_id)?;
        require_non_empty("source.platform", &self.source.platform)?;
        require_non_empty("source.location_class", &self.source.location_class)?;
        require_non_empty("routing.target", &self.routing.target)?;
        require_non_empty("routing.topic", &self.routing.topic)?;
        require_non_empty("payload_type", &self.payload_type)?;
        require_non_empty("payload", &self.payload)?;

        if self.provenance_chain.is_empty() {
            return Err(SigmaBusError::MissingProvenance);
        }
        if self.provenance_chain[0].action != ProvenanceAction::Originated {
            return Err(SigmaBusError::InvalidProvenance(
                "first entry must be originated".to_string(),
            ));
        }
        for entry in &self.provenance_chain {
            if entry.agent_id.trim().is_empty() || entry.timestamp.trim().is_empty() {
                return Err(SigmaBusError::InvalidProvenance(
                    "agent_id and timestamp are required".to_string(),
                ));
            }
            if let Some(signature) = &entry.signature {
                if !is_hex_signature(signature) {
                    return Err(SigmaBusError::InvalidSignature(
                        "signature must be null or 128 lowercase/uppercase hex characters"
                            .to_string(),
                    ));
                }
            }
        }

        serde_json::from_str::<serde_json::Value>(&self.payload)
            .map_err(|err| SigmaBusError::InvalidPayloadJson(err.to_string()))?;
        Ok(())
    }

    pub fn canonical_signing_bytes_for(
        &self,
        provenance_index: usize,
    ) -> Result<Vec<u8>, SigmaBusError> {
        if provenance_index >= self.provenance_chain.len() {
            return Err(SigmaBusError::ProvenanceIndexOutOfBounds {
                index: provenance_index,
                len: self.provenance_chain.len(),
            });
        }

        let mut canonical = self.clone();
        canonical.provenance_chain[provenance_index].signature = None;
        serde_json::to_vec(&canonical).map_err(|err| SigmaBusError::Serialization(err.to_string()))
    }

    pub fn sign_provenance_entry(
        &mut self,
        provenance_index: usize,
        signing_key: &SigningKey,
    ) -> Result<String, SigmaBusError> {
        let bytes = self.canonical_signing_bytes_for(provenance_index)?;
        let signature = signing_key.sign(&bytes);
        let encoded = hex::encode(signature.to_bytes());
        self.provenance_chain[provenance_index].signature = Some(encoded.clone());
        Ok(encoded)
    }

    pub fn sign_last_provenance(
        &mut self,
        signing_key: &SigningKey,
    ) -> Result<String, SigmaBusError> {
        let index = self
            .provenance_chain
            .len()
            .checked_sub(1)
            .ok_or(SigmaBusError::MissingProvenance)?;
        self.sign_provenance_entry(index, signing_key)
    }

    pub fn verify_provenance_entry(
        &self,
        provenance_index: usize,
        verifying_key: &VerifyingKey,
    ) -> Result<(), SigmaBusError> {
        if provenance_index >= self.provenance_chain.len() {
            return Err(SigmaBusError::ProvenanceIndexOutOfBounds {
                index: provenance_index,
                len: self.provenance_chain.len(),
            });
        }

        let signature_hex = self.provenance_chain[provenance_index]
            .signature
            .as_ref()
            .ok_or(SigmaBusError::MissingSignature)?;
        let signature_bytes = hex::decode(signature_hex)
            .map_err(|err| SigmaBusError::InvalidSignature(err.to_string()))?;
        let signature_array: [u8; 64] = signature_bytes.as_slice().try_into().map_err(|_| {
            SigmaBusError::InvalidSignature("signature must be 64 bytes".to_string())
        })?;
        let signature = Signature::from_bytes(&signature_array);
        let bytes = self.canonical_signing_bytes_for(provenance_index)?;
        verifying_key
            .verify(&bytes, &signature)
            .map_err(|err| SigmaBusError::InvalidSignature(err.to_string()))
    }
}

pub struct SigmaEnvelopeBuilder {
    event_id: String,
    emitted_at: String,
    expires_at: Option<String>,
    event_type: String,
    payload_type: String,
    payload: Option<String>,
    source: SigmaSource,
    provenance_chain: Vec<SigmaProvenanceEntry>,
    privacy_tier: PrivacyTier,
    lens_state: LensState,
    routing: SigmaRouting,
}

impl SigmaEnvelopeBuilder {
    pub fn new(
        event_type: impl Into<String>,
        payload_type: impl Into<String>,
        source: SigmaSource,
    ) -> Self {
        Self {
            event_id: format!("sig-{}", Uuid::new_v4()),
            emitted_at: now_rfc3339(),
            expires_at: None,
            event_type: event_type.into(),
            payload_type: payload_type.into(),
            payload: None,
            source,
            provenance_chain: Vec::new(),
            privacy_tier: PrivacyTier::Internal,
            lens_state: LensState::None,
            routing: SigmaRouting::new("bus_topic", "sigma.events"),
        }
    }

    pub fn event_id(mut self, event_id: impl Into<String>) -> Self {
        self.event_id = event_id.into();
        self
    }

    pub fn emitted_at(mut self, emitted_at: impl Into<String>) -> Self {
        self.emitted_at = emitted_at.into();
        self
    }

    pub fn expires_at(mut self, expires_at: impl Into<String>) -> Self {
        self.expires_at = Some(expires_at.into());
        self
    }

    pub fn privacy_tier(mut self, privacy_tier: PrivacyTier) -> Self {
        self.privacy_tier = privacy_tier;
        self
    }

    pub fn lens_state(mut self, lens_state: LensState) -> Self {
        self.lens_state = lens_state;
        self
    }

    pub fn routing(mut self, routing: SigmaRouting) -> Self {
        self.routing = routing;
        self
    }

    pub fn provenance_chain(
        mut self,
        provenance_chain: impl IntoIterator<Item = SigmaProvenanceEntry>,
    ) -> Self {
        self.provenance_chain = provenance_chain.into_iter().collect();
        self
    }

    pub fn add_provenance(mut self, entry: SigmaProvenanceEntry) -> Self {
        self.provenance_chain.push(entry);
        self
    }

    pub fn payload_json(mut self, payload: impl Into<String>) -> Self {
        self.payload = Some(payload.into());
        self
    }

    pub fn payload<T: Serialize>(mut self, payload: &T) -> Result<Self, SigmaBusError> {
        self.payload = Some(
            serde_json::to_string(payload)
                .map_err(|err| SigmaBusError::Serialization(err.to_string()))?,
        );
        Ok(self)
    }

    pub fn build(mut self) -> Result<SigmaBusEnvelope, SigmaBusError> {
        if self.provenance_chain.is_empty() {
            self.provenance_chain.push(SigmaProvenanceEntry::new(
                self.source.agent_id.clone(),
                ProvenanceAction::Originated,
                self.emitted_at.clone(),
            ));
        }

        let envelope = SigmaBusEnvelope {
            event_id: self.event_id,
            schema_version: SIGMA_BUS_SCHEMA_VERSION.to_string(),
            emitted_at: self.emitted_at,
            expires_at: self.expires_at,
            privacy_tier: self.privacy_tier,
            lens_state: self.lens_state,
            event_type: self.event_type,
            source: self.source,
            provenance_chain: self.provenance_chain,
            routing: self.routing,
            payload_type: self.payload_type,
            payload: self.payload.ok_or(SigmaBusError::MissingPayload)?,
        };
        envelope.validate()?;
        Ok(envelope)
    }
}

pub trait SigmaBusTransport {
    type Error;

    fn publish(&self, envelope: &SigmaBusEnvelope) -> Result<(), Self::Error>;
}

#[derive(Default)]
pub struct InMemoryTransport {
    events: RefCell<Vec<SigmaBusEnvelope>>,
}

impl InMemoryTransport {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn events(&self) -> Vec<SigmaBusEnvelope> {
        self.events.borrow().clone()
    }
}

impl SigmaBusTransport for InMemoryTransport {
    type Error = SigmaBusError;

    fn publish(&self, envelope: &SigmaBusEnvelope) -> Result<(), Self::Error> {
        envelope.validate()?;
        self.events.borrow_mut().push(envelope.clone());
        Ok(())
    }
}

#[derive(Debug, Error)]
pub enum SigmaBusError {
    #[error("field {0} is required")]
    MissingField(&'static str),
    #[error("payload is required")]
    MissingPayload,
    #[error("at least one provenance entry is required")]
    MissingProvenance,
    #[error("unsupported schema version {0}")]
    UnsupportedSchemaVersion(String),
    #[error("invalid provenance: {0}")]
    InvalidProvenance(String),
    #[error("payload must be valid JSON: {0}")]
    InvalidPayloadJson(String),
    #[error("serialization failed: {0}")]
    Serialization(String),
    #[error("missing provenance signature")]
    MissingSignature,
    #[error("invalid signature: {0}")]
    InvalidSignature(String),
    #[error("provenance index {index} out of bounds for {len} entries")]
    ProvenanceIndexOutOfBounds { index: usize, len: usize },
}

pub fn now_ns() -> u64 {
    let now: DateTime<Utc> = Utc::now();
    (now.timestamp() as u64)
        .saturating_mul(1_000_000_000)
        .saturating_add(now.timestamp_subsec_nanos() as u64)
}

pub fn now_rfc3339() -> String {
    format_ns_rfc3339(now_ns())
}

pub fn format_ns_rfc3339(timestamp_ns: u64) -> String {
    let seconds = (timestamp_ns / 1_000_000_000) as i64;
    let nanos = (timestamp_ns % 1_000_000_000) as u32;
    DateTime::<Utc>::from_timestamp(seconds, nanos)
        .map(|dt| dt.to_rfc3339_opts(SecondsFormat::Nanos, true))
        .unwrap_or_else(|| "1970-01-01T00:00:00.000000000Z".to_string())
}

fn require_non_empty(field: &'static str, value: &str) -> Result<(), SigmaBusError> {
    if value.trim().is_empty() {
        Err(SigmaBusError::MissingField(field))
    } else {
        Ok(())
    }
}

fn is_hex_signature(value: &str) -> bool {
    value.len() == 128 && value.as_bytes().iter().all(u8::is_ascii_hexdigit)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn source() -> SigmaSource {
        SigmaSource::new(
            "canister:compute_ledger",
            "compute_ledger",
            "icp_canister",
            "sovereign_local",
        )
    }

    #[test]
    fn builder_creates_valid_envelope() {
        let envelope =
            SigmaBusEnvelope::builder("treasury.credit.earned", "CreditEarnedPayload", source())
                .event_id("event-test-001")
                .emitted_at("2026-05-27T00:00:00.000000000Z")
                .routing(
                    SigmaRouting::new("bus_topic", "treasury.credit.earned")
                        .delivery(DeliveryMode::AtLeastOnce),
                )
                .payload(&json!({
                    "account": "aaaaa-aa",
                    "amount": "42",
                    "source": "mint"
                }))
                .expect("serialize payload")
                .build()
                .expect("build envelope");

        assert_eq!(envelope.schema_version, SIGMA_BUS_SCHEMA_VERSION);
        assert_eq!(
            envelope.provenance_chain[0].action,
            ProvenanceAction::Originated
        );
        envelope.validate().expect("valid envelope");
    }

    #[test]
    fn signing_roundtrip_verifies() {
        let signing_key = SigningKey::from_bytes(&[7_u8; 32]);
        let verifying_key = signing_key.verifying_key();
        let mut envelope =
            SigmaBusEnvelope::builder("compute.decision.made", "ComputeDecisionPayload", source())
                .event_id("event-test-002")
                .emitted_at("2026-05-27T00:00:00.000000000Z")
                .payload(&json!({
                    "decision_id": "decision-001",
                    "selected_provider": "provider-001"
                }))
                .expect("serialize payload")
                .build()
                .expect("build envelope");

        let signature = envelope
            .sign_last_provenance(&signing_key)
            .expect("sign provenance");

        assert_eq!(signature.len(), 128);
        envelope
            .verify_provenance_entry(0, &verifying_key)
            .expect("verify signature");
    }

    #[test]
    fn in_memory_transport_validates_and_stores_events() {
        let transport = InMemoryTransport::new();
        let envelope = SigmaBusEnvelope::builder(
            "system.governance.proposed",
            "GovernanceProposalPayload",
            source(),
        )
        .payload_json(r#"{"proposal_id":"proposal-1"}"#)
        .build()
        .expect("build envelope");

        transport.publish(&envelope).expect("publish envelope");

        let events = transport.events();
        assert_eq!(events.len(), 1);
        assert_eq!(events[0].event_type, "system.governance.proposed");
    }

    #[test]
    fn invalid_payload_json_is_rejected() {
        let err = SigmaBusEnvelope::builder("bad.event", "BadPayload", source())
            .payload_json("{not json")
            .build()
            .expect_err("invalid JSON should fail");

        assert!(matches!(err, SigmaBusError::InvalidPayloadJson(_)));
    }
}
