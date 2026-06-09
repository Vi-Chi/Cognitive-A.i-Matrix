# MΣBUS cm.* coordination layer

Recovered from the ΣBUS-CM spec and `sigmabus/schemas/{aid,cm-message}.schema.json`, ported into the
MEBUS core (`src/mebus/coordination.py`, stdlib-only). This is the `cm.*` half of the bus — how
autonomous agents identify themselves and negotiate. Coordination bodies ride inside the envelope's
π; trust/provenance project into κ; routing is by σ = `cm.<type>`.

## AID — Agent Identity Descriptor

The agent's verifiable passport. `uid` format `agt-{platform}-{role}-NNN`; `tier` 1–3
(rule <100 ms / small-LLM ~500 ms / large-LLM 1–5 s); capability manifest (`perceives` patterns,
`controls` exact paths — **no wildcards**), `trust_class`, ed25519 `pubkey`, and the inalienable
`human_override_path` / `emergency_stop_path` (P7). `AID.announce()` broadcasts it as `cm.announce`.

| trust_class | meaning |
|-------------|---------|
| `sovereign` | platform-native, CA-signed, full trust (cert required) |
| `trusted_peer` | known peer |
| `federated` | external, limited trust (cert required) |
| `claimed` | self-signed, reduced trust |
| `anonymous` | unauthenticated, lowest trust |

## The 15 CM message types (`CMType`)

Lifecycle `ANNOUNCE · WITHDRAW · HEARTBEAT` · query `QUERY · INFORM` · action
`REQUEST · CONFIRM · FAIL` · negotiation `PROPOSE · AGREE · REFUSE · RETRACT` · control
`DELEGATE · RESUME` · `ALERT`. Each becomes σ = `cm.<type>`. The action/negotiation/control set is
the **Ω₈ action layer** (suppressed in DREAM); `ANNOUNCE/HEARTBEAT/QUERY/INFORM/ALERT` are info and
flow even in DREAM.

## Safety properties (carried verbatim)

- **P6 — `PROPOSE` MUST carry a `fallback`.** If the `proposal_ttl_ns` lapses with no `AGREE`, the
  agent executes the fallback autonomously. `CMMessage.validate()` rejects a fallback-less PROPOSE;
  `proposal_expired()` is the TTL check.
- **P7 — human authority is inalienable.** Encoded as required AID override/e-stop paths.
- **Trust gate.** ΣBUS-CM §9: `effective_trust = clamp(trust_score − age_decay − anomaly·0.5 +
  cross_val_bonus)`, discard `< 0.1` — already enforced by `MembraneBus` (see protocol core).

## CM addressing (§4.4) & reserved domains (§4.2)

`cm_broadcast/direct/role/federation()` build the `cm.{platform}.…` paths. `RESERVED_DOMAINS` =
`nav engine power comms safety environment agent meta cmd` (data-path namespace; `meta.*`/`cmd.*`
reserved).

## Signing

Production AIDs/envelopes are **ed25519-signed by the Rust hot-path `sigma-bus-rust`** (canonical
JSON, sorted keys, no whitespace, excluding the `signature` field). This stdlib reference ships an
HMAC-SHA256 `sign()`/`verify()` over the same canonical form for tests and offline use.

## Schemas

`schemas/aid.schema.json` and `schemas/cm_message.schema.json` are the authoritative JSON Schemas,
ported unchanged from the ΣBUS-CM prototype.
