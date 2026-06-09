# ΣBUS_CM.txt → MEBUS core — coverage review

**Question:** after building the MΣBUS v0.1 core, did we miss anything in the origin design?
**Source:** `_Documentation/ΣBUS_CM.txt` (5006-line origin conversation; byte-identical copies in
`MEBUS/sigmabus/` and `MEBUS/ΣBUS_CM_files/`). **Reviewed:** 2026-06-07.

**Answer:** the v0.1 core faithfully implements the *envelope + routing + Ω₈ + adapters +
PredictionRecord*. But the origin file specifies a much larger **agent-coordination layer** that
the canonical v0.1 deliberately deferred — and **three small behaviours that the shipped docs
claim but the code did not do**. The three slips are now implemented (additive, tested). The
larger layer is catalogued below as the build backlog.

---

## A · Now fixed — behaviours the docs promised but v0.1 didn't enforce

| # | Origin spec | v0.1 gap | Fix (this build) |
|---|-------------|----------|------------------|
| A1 | `SemanticEnvelope.effective_trust()` + old `sigmabus_core.is_actionable` / `TRUST_FLOOR=0.1`; PROTOCOL.md §4 says *"below 0.1 → discard"* | `MembraneBus.publish()` never computed trust or discarded — docs/code mismatch | `effective_trust()` + `MMessage.effective_trust()`; bus discards below `trust_floor` (audited; `strict` → `TrustFloorDiscarded`). `cross_validated` bonus + `anomaly` penalty honoured. Default trust = 1.0 so existing traffic is unaffected. |
| A2 | `SemanticEnvelope.t_expires` + `is_valid()`; κ schema has `t_expires` (ns) | freshness never checked | `MMessage.is_fresh(now)`; bus discards expired (audited; `strict` → `MessageExpired`). |
| A3 | `μ` LIMINAL = *"delivered but flagged advisory"* | `publish()` only branched on DREAM; LIMINAL == WAKE | LIMINAL action messages deliver but are audit-flagged `advisory=True`. |

Audit entries now carry `suppressed · expired · trust · trust_blocked · advisory · delivered`.

---

## B · The ΣBUS-CM coordination layer — **NOW BUILT** (2026-06-07)

> B1–B6 implemented in `src/mebus/coordination.py` (AID, 15 CM types, CMMessage, negotiation
> fallback+TTL, CM addressing, HMAC-ref signing; schemas ported). B7 ed25519 = production via
> `sigma-bus-rust`. B8–B12 (full trust decay/persistence, schema registry, richer κ, conformance
> asserts, wire serialisation) remain.

The origin file fully specifies these; PROTOCOL.md §7 already lists them as "next". They are the
`cm.*` half of the bus and are **not yet built**. Source schemas already exist in the prototype
(`MEBUS/sigmabus/schemas/aid.schema.json`, `cm-message.schema.json`).

| # | Element | What the origin spec defines | Status |
|---|---------|------------------------------|--------|
| B1 | **AID — Agent Identity Descriptor** | the agent "passport": `uid, vessel_id, role, tier`, capability manifest (`perceives / controls / reasoning_domains`), performance contract (`latency_p50/p99, update_rate_hz, offline_capable`), `trust_class` (sovereign/federated/external/untrusted), `pubkey ed25519`, `signed_by` CA | **missing** (prototype `aid.schema.json` not ported to MEBUS) |
| B2 | **15 CM message types** | ANNOUNCE · WITHDRAW · HEARTBEAT · QUERY · INFORM · REQUEST · CONFIRM · FAIL · PROPOSE · AGREE · REFUSE · RETRACT · DELEGATE · RESUME · ALERT | only σ strings in docs; no typed vocabulary/constructors (old `CM_MESSAGE_TYPES` set dropped) |
| B3 | **CMMessage agent fields** | `sender_uid/tier, receiver_uid, reply_to, conversation_id/step, subject, proposal_id, proposal_ttl, constraints, trust_required, urgency, signature` | missing |
| B4 | **Conversation state machines** | DISCOVERY · QUERY/INFORM · REQUEST/CONFIRM/FAIL · PROPOSE/AGREE/REFUSE/RETRACT · DELEGATE/RESUME | missing |
| B5 | **Negotiation fallback (safety property)** | every PROPOSE carries a `fallback`; on `proposal_ttl` expiry with no AGREE → **execute fallback autonomously**. The property that makes autonomous negotiation safe at sea | missing — highest-value next item |
| B6 | **Discovery + liveness** | ANNOUNCE on join; HEARTBEAT (default 10s); 3× missed → mark absent; gateway is bandwidth-aware (only ALERT/PROPOSE/AGREE/REFUSE cross a vessel boundary; INFORM/HEARTBEAT stay local) | missing |
| B7 | **Security** | ed25519 signing mandatory, `signature` field, replay protection, rate limiting, platform-CA trust classes, signature-fail → trust −0.50; human authority inalienable | missing (MMessage has no signature field) |
| B8 | **Trust model (full)** | trust initialised by class, modified by track record, **decays over time**, persisted across sessions | partial — gate + bonus/anomaly in; class init, track-record, time-decay-from-τ, persistence still missing |
| B9 | **Schema Registry / path addressing** | dotted `WHO.WHAT.WHY` path namespace; central schema library with versioned evolution; MatrixBus windowing/CEP/anomaly scoring; MatrixRegistry health/world-model | missing (architectural; larger) |
| B10 | **Richer envelope classification** | `data_class` (sensor/derived/inferred/command/negotiation), `retention` (realtime/voyage/permanent/ephemeral), `consumer_acl`, agent `annotations` shadow-stream, `priority/urgency` | κ is currently a loose dict; these fields unmodelled |
| B11 | **Conformance levels L1/L2/L3** | minimal / standard / gateway tiers | documented, not asserted by tests |
| B12 | **Serialisation bindings** | JSON now; Cap'n Proto / FlatBuffers / msgpack for the wire; NATS JetStream / ZeroMQ / MQTT / serial transports | reference is in-process dict only; Rust hot-path lives in Autopoiesis |

---

## Recommended build order (next)

1. **B1 + B2 + B3** — port `aid.schema.json` + `cm-message.schema.json`, add the typed CM
   vocabulary and a `CMMessage`/AID dataclass. Small, unblocks everything else.
2. **B5** — PROPOSE/AGREE/REFUSE with mandatory fallback + TTL-expiry autonomous fallback (safety).
3. **B6** — discovery + heartbeat liveness + gateway bandwidth filter.
4. **B7** — ed25519 signing + `signature` field + replay/rate-limit.
5. **B8–B12** — full trust decay/persistence, schema registry + path addressing, richer κ, conformance asserts, wire serialisation.

Nothing above changes the v0.1 core contract; each is additive on the membrane.
