# ADR-0001: Transport & Persistence for MΣBUS messages and the audit ledger

**Status:** Proposed (design-only; no infra mutation in this cycle)
**Date:** 2026-06-14
**Author:** Claude (Trinity Auditor-Scribe) · **Deciders:** Vi (owner, final authority); Codex (implementation lane)
**Classification:** ACTIVE design doc — *not* runtime-enforced law. No executor, no network dependency introduced.

## Context

Today the system is **in-process and filesystem-first**, by deliberate design:

- **Transport** is synchronous and in-memory. `MembraneRouter.deliver(msg)` validates the 7-field
  envelope, applies the gates **in order — Ω₈ (action suppressed in DREAM) → freshness (κ.t_expires) →
  effective-trust floor** — and routes to subscribers within the same process. There is no broker, no socket,
  no cross-process delivery.
- **Persistence** is append-only JSONL. `LedgerWriter` writes canonical envelopes to five P0 streams
  (`evidence / audit_verdicts / predictions / outcomes / calibration`) via a `σ → stream` route map, stamping
  each record with `envelope.fingerprint()` (SHA-256). `MemoryStore` is one append-only JSONL per tier with a
  core-write monopoly, and already documents the intended escape hatch: *"LMDB/RocksDB can back this later
  behind the same interface."* Economics ledgers are JSONL too.

Forces now in play that make this worth deciding *before* building:

1. **SMTIS P1** will introduce real, asynchronous, lossy external feeds (Signal-K WebSocket, AIS UDP, weather)
   — a producer/consumer rate mismatch the synchronous in-process bus does not model.
2. The **DREAM Replay Auditor** already consumes `predictions.jsonl` + `outcomes.jsonl` as its timeline, so
   persistence *is* the replay substrate; its durability and ordering guarantees are constitutional, not cosmetic.
3. The **CM5 / Wibo-835** target is offline, single-board, salt-and-power-hostile. Any answer must run with
   **zero required network and zero required external daemon**, and must degrade safely on power loss.
4. Constitutional invariants that the transport/persistence layer must **never** be able to weaken:
   the 7-field envelope is fixed (extend via π, never widen M); **gates are enforced at the membrane, not the
   transport** (a transport must not be a path that bypasses Ω₈/freshness/trust); fingerprint integrity and
   append-only auditability must hold; no component gains a second power.

Hard constraints: stdlib-only behavioral core; offline failure behavior stays benign (`[]`, not crash); any
network bind is a **stop-gated** firewall/public-exposure decision (owner approval, localhost-default, off by
default) — out of scope to *enable* here, in scope to *design for*.

## Current reality (verified in-sandbox 2026-06-14 — the seam is partly built)

This ADR is **not greenfield**. Auditing `ai_chi/bus/transports/` before writing it revealed Codex has already
begun the transport seam, and it is constitutionally well-behaved:

- **`FileBackedSigmaTransport`** (`file_transport.py`) — a zero-dependency, append-only JSONL transport for
  envelopes, already wired into `AutopoiesisLedger` and `orbi/policy_gate.py`. This is Option E's persistence
  plane, in use today.
- **`NatsTransportBridge`** (`nats_bridge.py`) — a CM5↔RPi4 federation bridge. Verified safe: `nats-py` is an
  **optional** import (the module imports cleanly offline — confirmed), default URL is **localhost**
  (`nats://127.0.0.1:4222`), it **lazy-connects only on explicit `.start()`** (no import- or construction-time
  socket), raises a clear error if the lib is absent, and it federates **through `MembraneBus`** — i.e. gates
  stay at the membrane, exactly the anti-bypass rule below. The code existing is fine; *starting* it (the socket
  connect) is the stop-gated act requiring owner approval.

So the decision below largely **ratifies and names** an architecture that is already emerging, rather than
introducing it — and confirms its direction is sound.

⚠ **One real defect found while verifying (Codex-lane, routed):** `core/ledger/autopoiesis_ledger.py:12` does
`from datetime import UTC`, which exists only in **Python ≥ 3.11**. On this 3.10 sandbox the module fails to
import, which fails the test loader for `test_autopoiesis_ledger` (the suite otherwise runs clean; `verify_floor()`
True). RPi OS Bookworm ships 3.11 so the *target* is likely unaffected, but it breaks the "self-contained /
portable" property and any 3.10 host. One-line fix: `from datetime import datetime, timezone` and use
`timezone.utc`. See action item 0.

## Decision

Adopt a **two-plane model with a pluggable backend behind a stable interface**, and keep the current
implementation as the default:

1. **Separate the transport plane from the persistence plane.** They have different guarantees (delivery/
   ordering vs. durability/replay) and should evolve independently. Conflating them is what makes broker
   choices feel load-bearing when they are not.
2. **Persistence = the source of truth; transport = a delivery optimization.** The append-only fingerprinted
   ledger is the black box; any transport is replaceable and must be reconstructable from the ledger.
3. **Backend behind an interface (the pattern `MemoryStore` already names).** Define a `LedgerBackend`
   (`append(stream, record) / read(stream) / tail(stream, n)`) and a `Transport`
   (`publish(msg) / subscribe(σ, handler)`) protocol. Ship `JsonlLedgerBackend` + `InProcessTransport` as the
   defaults — i.e. refactor today's code *to* the interface, change no behavior.
4. **Gates stay at the membrane.** `MembraneRouter.deliver` remains the single chokepoint; a `Transport` may
   only move bytes between processes — it is wired *underneath* the router, never around it. Ω₈/freshness/trust
   are re-applied on the consuming side after any cross-process hop. This is the anti-bypass rule.
5. **Phase the heavier options as opt-in, off by default, behind the stop-gate** — chosen only when a concrete
   need (P1 backpressure, multi-process) is demonstrated.

## Options Considered

### Option A: In-process bus + JSONL ledger (status quo, formalized behind interfaces)
| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Cost / deps | Zero (stdlib) |
| Scalability | Single-process only; synchronous; no backpressure |
| Offline / CM5 fit | Excellent |
| Team familiarity | Native — it's the current code |

**Pros:** No daemon, no socket, no attack surface; crash-safe via append-only + fsync; already the replay
substrate; gates trivially un-bypassable (one process). **Cons:** No async producer/consumer decoupling for P1
feeds; no cross-process or multi-host; a slow consumer blocks the bus.

### Option B: NATS / JetStream (broker transport, optional persistence)
| Dimension | Assessment |
|-----------|------------|
| Complexity | High |
| Cost / deps | External daemon + client lib; network bind |
| Scalability | Excellent (subjects, queue groups, durable streams) |
| Offline / CM5 fit | Poor as a *requirement*; acceptable as opt-in localhost |
| Team familiarity | Low |

**Pros:** Mature pub/sub + durable replay; subject hierarchy maps cleanly onto `σ`; backpressure handled.
**Cons:** Violates "zero required daemon" if made mandatory; introduces a network bind (**stop-gated**); a second
durable store competing with the ledger for "source of truth" — splits the black box; operational weight wrong
for a sailboat SBC.

### Option C: ZeroMQ (brokerless sockets, no persistence)
| Dimension | Assessment |
|-----------|------------|
| Complexity | Medium |
| Cost / deps | Library; socket bind; you build durability/replay yourself |
| Scalability | Good for transport; nothing for persistence |
| Offline / CM5 fit | Acceptable as opt-in localhost/IPC |
| Team familiarity | Low |

**Pros:** Light, brokerless, fast; `ipc://` needs no network bind; good for in-box multi-process.
**Cons:** Transport-only — replay/durability remain your problem (so it pairs with the JSONL/LMDB ledger, it
doesn't replace it); still a new dependency and bind to manage; no message durability if a consumer is down.

### Option D: LMDB journal (persistence upgrade, no transport change)
| Dimension | Assessment |
|-----------|------------|
| Complexity | Medium |
| Cost / deps | Single embedded lib; no daemon, no socket |
| Scalability | Excellent read/replay; ACID; bounded memory-mapped |
| Offline / CM5 fit | Excellent |
| Team familiarity | Low–Medium |

**Pros:** Crash-safe ACID, fast indexed replay (helps the Dream auditor at volume), no network surface, fits
the "behind the same interface" hatch already named in `MemoryStore`. **Cons:** Binary store is less
grep-able / human-auditable than JSONL (mitigate: keep JSONL as the human-readable mirror, LMDB as the index);
a dependency; does nothing for async transport.

### Option E (recommended): Hybrid, phased — JSONL/LMDB for audit persistence, optional local transport for P1
| Dimension | Assessment |
|-----------|------------|
| Complexity | Low now, Medium later (opt-in) |
| Cost / deps | Zero now; embedded/optional later |
| Scalability | Grows only when a need is proven |
| Offline / CM5 fit | Excellent (defaults stay stdlib + offline) |
| Team familiarity | Native now |

Keep the JSONL ledger as the canonical black box (add LMDB as an *index/replay accelerator behind
`LedgerBackend`* only if/when replay volume demands it, JSONL remaining the human-readable truth). Keep
`InProcessTransport` as default; introduce an **opt-in local transport** (ZeroMQ `ipc://` preferred over NATS for
the single-box case — no daemon, no network bind) **only** when SMTIS P1 demonstrates a real backpressure /
multi-process need. Everything off by default, localhost/IPC-only, behind the stop-gate.

## Trade-off Analysis

The decision that actually matters is **not which broker** — it's **refusing to let a broker become the source
of truth**. The append-only fingerprinted ledger is what makes the Dream auditor, Urbi audit, and after-the-fact
verification possible; a broker's durable stream would either duplicate or quietly supersede it, splitting the
black box and creating a second authority — a constitutional smell (no component should hold two powers).

So persistence and transport are decided separately. On **persistence**, JSONL wins now on auditability and
zero-dep; LMDB is a *later, behind-interface* accelerator, never a replacement, with JSONL kept as the readable
mirror. On **transport**, the in-process router wins now; if P1 forces async decoupling, **ZeroMQ `ipc://`
beats NATS for this target** because it adds no daemon and no network bind — the lightest thing that removes the
slow-consumer-blocks-bus problem. NATS earns reconsideration only if multi-host (boat ↔ shore) delivery becomes
a real requirement, at which point it returns as an explicit stop-gated ADR of its own.

The load-bearing rule across all options: **gates live at the membrane.** Whatever moves bytes, Ω₈/freshness/
trust are re-applied by `MembraneRouter.deliver` on the consuming side — a transport is never a hole around the
gate. This keeps the safety property invariant under any future transport swap.

## Consequences

**Easier:** swapping persistence/transport later without touching call sites (interface seam); proving the
safety invariant once at the membrane regardless of transport; P1 async ingest when needed, without a rewrite;
staying fully offline by default.

**Harder / costs:** one indirection layer (protocols + default impls) added now for optionality not yet
exercised; if LMDB is later added, a dual-write (JSONL mirror + LMDB index) consistency concern to test;
discipline required to keep the ledger — not any future broker — as the single source of truth.

**To revisit:** trigger points — (a) SMTIS P1 shows the synchronous bus dropping/blocking on real feeds →
implement opt-in ZeroMQ `ipc://` transport; (b) Dream replay over large histories gets slow → add LMDB index
behind `LedgerBackend`; (c) boat↔shore multi-host delivery becomes a requirement → new stop-gated ADR for NATS.

## Action Items
0. [x] (Codex, priority) Fix `autopoiesis_ledger.py:12` `from datetime import UTC` → `timezone.utc` (Python 3.11+
       → 3.9+ portable); restores import + test loader on 3.10. Blocking the clean suite on non-3.11 hosts.
1. [x] (Codex) Promote the emerging seam to explicit protocols: define `LedgerBackend` + `Transport`, with
       `FileBackedSigmaTransport` (already built) and the in-process router as the default implementations, and
       `LedgerWriter` adapted to `LedgerBackend` — **zero behavior change** (existing suite stays green).
2. [x] (Codex) Add a membrane-side conformance test asserting Ω₈/freshness/trust are re-applied on delivery
       through **every** transport including `NatsTransportBridge`, so federation can never bypass the gate.
3. [ ] (Claude/Auditor) Add a ledger-integrity check (fingerprint chain + append-only) to the verification suite;
       audit `NatsTransportBridge` end-to-end before it is ever started (its socket connect is the stop-gated act).
4. [ ] (Deferred, stop-gated) Enabling `NatsTransportBridge` for boat↔shore federation — owner approval before
       any `.start()`/socket connect; keep localhost-default, off by default. (Code present, dormant.)
5. [ ] (Deferred) LMDB replay-index behind `LedgerBackend`, JSONL retained as readable mirror — only if replay
       volume demands it.

No infrastructure was created or mutated by this ADR. Network binds, brokers, and daemons remain **stop-gated**
and require explicit owner approval per the project boundaries.

Cross-refs: `ai_chi/core/ledger/writer.py`, `ai_chi/urbi/memory/store.py`, `ai_chi/_vendor/mebus/protocol.py`
(Ω₈ + gates), `ai_chi/urbi/dream/replay.py`, `_Import/claude_update.md` §7, `AXIOMS_OF_OMNI.md`,
`URBI_ORBI_MEBUS_BALANCE_CONSTITUTION_2026-06-08.md`.
