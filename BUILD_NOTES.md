# MΣBUS core — build notes

**Built:** 2026-06-07 · **Status:** v0.1 core materialized locally, verified green, +1 forward increment.

## What this is

A faithful, runnable materialization of the canonical **MΣBUS v0.1 core** (the `Vi-Chi/MEBUS`
GitHub repo, commit `4151dc2`) plus one roadmap increment. The seven-field membrane protocol,
the mode-gated bus (Ω₈), the adapter/translation layer, and the PredictionRecord synapse —
all stdlib-only Python, no third-party dependencies.

## Why it was needed (coverage gap)

The working core lived **only on GitHub**. The local `MEBUS/` folder contained only the
*superseded* `sigmabus/` prototype (Apache-2.0 draft spec, `sigmabus_core.py` trust-gate stub,
no `MMessage`, no Ω₈, no `mebus` package) plus the `ΣBUS_CM_files/` archive bundle. There was
no local copy of the actual v0.1 implementation to run or build on. This build closes that gap.

## What was built

| File | Source | Notes |
|------|--------|-------|
| `src/mebus/protocol.py` | canonical | `MMessage`, `Mode`, `MembraneBus`, Ω₈, `is_action_layer`, errors |
| `src/mebus/adapter.py` | canonical | `Adapter`, `AdapterRegistry`, `JSONAdapter`, `SignalKAdapter`, `wrap_external` |
| `src/mebus/records.py` | canonical | `PredictionRecord` cognition synapse |
| `src/mebus/__init__.py` | canonical + export | adds `NMEAAdapter`, `nmea_checksum` |
| `src/mebus/adapter_nmea.py` | **NEW** | NMEA 0183 GGA/RMC → typed `m.state`; unknown sentences → `ext.nmea`; checksum-validated |
| `tests/test_protocol.py` | canonical | 14 tests |
| `tests/test_adapter.py` | canonical | 6 tests |
| `tests/test_nmea.py` | **NEW** | 8 tests |
| `schemas/*.json`, `docs/*.md`, `README`, `ARCHITECTURE`, `pyproject`, `LICENSE`, `.gitignore` | canonical | |

## Forward increment — NMEA 0183 adapter

Maritime is the primary deployment (Wibo 835 / Vento-Vivere) and an NMEA adapter is roadmap item #1
for the Observe layer. `NMEAAdapter`:
- parses **GGA** (position + fix quality) and **RMC** (position + SOG/COG) into decimal-degree
  `m.state` messages tagged `maritime.nav`;
- validates the NMEA checksum when present (mismatch → `MessageValidationError`);
- falls back to the **universal carrier** (`ext.nmea`) for unsupported sentence types — so nothing
  is ever dropped, consistent with the "transport anything" membrane principle;
- retains the raw sentence in `κ.raw` for loss-free `emit` (gateway round-trip).

It is purely additive — the canonical core contract is unchanged.

## Verification

```
python -m unittest discover -s tests -v   →   Ran 28 tests ... OK
```

20 canonical tests (Ω₈ suppression, action/cognition gating, round-trip, fingerprint,
adapters, PredictionRecord routing) + 8 NMEA tests, all passing on Python 3.10.

## Notes / open items

- **Keep this tree off Drive `.git`.** Per the project's own rule (Drive sync corrupts `.git`,
  GitHub is source of truth) this local copy is shipped **without** a `.git` directory. Commit
  from a non-Drive checkout, or push files via the GitHub path.
- The superseded `sigmabus/` prototype still has **11 uncommitted changes and no remote** — back it
  up before deleting; its ΣBUS-CM spec content is the source for the future `cm.*` payload schemas.
- Next increments: MQTT/NATS transport bindings, SDR/MCP/GUI adapters, the `cm.*` coordination
  payload schemas (from `SIGMABUS-CM-SPEC.md`), and the Autopoiesis-hosted Rust hot-path.

---

## Update 2026-06-07 — ΣBUS_CM.txt review + recovered gates

Read the full origin design (`ΣBUS_CM.txt`, 5006 lines). It specifies a large agent-coordination
layer (AID, 15 CM message types, negotiation+fallback, discovery, ed25519 security) that v0.1
deferred — plus **three behaviours the docs claimed but the code didn't enforce**, now implemented
and tested:

- **Effective-trust gate** — discard below `TRUST_FLOOR` (0.1); `cross_validated` bonus, `anomaly` penalty.
- **Message freshness** — discard once `κ.t_expires` (ns) has passed.
- **LIMINAL advisory** — action delivered but audit-flagged advisory (only DREAM suppresses).

Suite now **39 tests, all passing**. Full origin-vs-built comparison and the build backlog are in
`docs/SIGMABUS_CM_GAP_REVIEW.md`.

---

## Update 2026-06-07 (2) — M-Protocol prototype review + m.* cognition payload

Read `M-Protocol + Sigma Bus_prototype.txt` (the Pydantic implementation the README cites). It is a
**second M-tuple with the geometric-cognition meaning** — the `m.*` payload carried inside the
envelope, not a competing envelope. Built it stdlib-only as `src/mebus/cognition.py`
(`DomainTag`, `UncertaintyDist`, `CausalRef`, `CognitionPayload`) and upgraded `PredictionRecord`
to the superset (error_type, tau window, reversal/void flags, replay predicates). Dropped the
pydantic/numpy/msgpack deps (msgpack optional). Fixed a `self.kappa` bug from the source prototype.
Suite now **48 tests, all passing**. Detail: `docs/M_PROTOCOL_PROTOTYPE_REVIEW.md`.

---

## Update 2026-06-07 (3) — _Documentation sweep + cm.* coordination layer

Swept all of `_Documentation` for uncaptured bus data. Biggest finds: the authoritative
`aid.schema.json` / `cm-message.schema.json` in `sigmabus/schemas/`, the ΣBUS-CM reserved domains +
CM addressing scheme, the effective-trust formula (confirms the trust gate built earlier is
faithful), and `icp&more.txt` confirming `sigma-bus-rust` does **ed25519 envelope signing**.

Built the **cm.* coordination layer** (`src/mebus/coordination.py`, stdlib-only): `AID` (passport +
validate + sign/verify + announce), `CMType` (15 types), `CMMessage` (negotiation envelope with the
P6 PROPOSE-needs-fallback safety property + TTL expiry), CM addressing helpers, reserved domains,
and an HMAC-SHA256 reference signer (ed25519 is the production path via `sigma-bus-rust`). Ported the
two JSON schemas. Suite now **62 tests, all passing**. Detail: `docs/CM_COORDINATION.md`.
