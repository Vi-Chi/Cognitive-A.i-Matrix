# M-Protocol + Sigma Bus_prototype.txt → MEBUS — coverage review

**Question:** the MEBUS README names this file as the canonical 7-field implementation. Did the
build miss it? **Reviewed:** 2026-06-07.

## The core finding: two M-tuples, same letters, different meaning

This file defines a **second concrete `M := (v,σ,π,δ,κ,τ,μ)` implementation** (Pydantic v2) whose
fields mean the *geometric-cognition* reading, not the transport reading we built:

| | MEBUS envelope (built) | This prototype (cognition) |
|--|------------------------|----------------------------|
| v | version (int) | **ℝ²⁰⁴⁸ geometry vector** |
| σ | signature (dotted str) | **UncertaintyDist** (point/gaussian/categorical/dirichlet/multivariate) |
| π | payload (dict) | **list[CausalRef]** provenance chain |
| δ | destination (str) | **DomainTag** enum (maritime.nav, …) |
| κ | context (trust/prov/expiry) | **calibrated [0,1] confidence** (Brier) |
| τ | ns timestamp | **causal-order counter** (uint64) |
| μ | mode | mode (same) |

Per the envelope-vs-payload reconciliation, this is **not** a competing envelope — it is the
**`m.*` cognition payload** that rides *inside* the MEBUS envelope's π, dispatched by σ-class `m.*`.
The build hadn't modeled it; it's exactly the "`m.*` payload schema" PROTOCOL.md §7 deferred.

## What was missing — now built (`src/mebus/cognition.py`, stdlib-only)

- **`DomainTag`** enum — canonical routing/domain keys (maritime.nav/situational/weather/vessel,
  digital.gui, model.interaction, system.audit, curiosity). `DomainTag.MARITIME_NAV.value` equals
  the `"maritime.nav"` string the NMEA/SignalK adapters already emit, so they line up.
- **`UncertaintyDist`** (σ) — structured epistemic uncertainty (the "never optional" σ), with
  `point()` / `gaussian()` constructors.
- **`CausalRef`** (π) — one structured link in the causal-provenance genealogy.
- **`CognitionPayload`** — the geometric m-tuple; `.to_message(sigma="m.state"|"m.belief")` wraps it
  as an MΣBUS `m.*` message (payload in π, domain+provenance+confidence projected into κ). Validated:
  κ∈[0,1], `v_dim` consistency, σ/μ types.
- **`PredictionRecord`** upgraded to the **superset** of the v0.1 record and this prototype's:
  added `error_type`, `tau_start/tau_end`, `reversal_candidate`, `void_related`, plus
  `is_high_confidence_wrong()` and `classify_error()` (the Dream-Layer replay-priority predicates).
  All new fields optional → existing callers unaffected. Schema updated to match.

## Deliberately NOT copied

- **pydantic / numpy / msgpack** — the prototype's deps. The MEBUS core is stdlib-only; `msgpack`
  is kept as an optional fast-path (`CognitionPayload.to_msgpack`, guarded import) only.
- The prototype's **async `SigmaBusRouter` routing by `delta`** — MEBUS routes by full σ signature
  (richer); domain remains available in `κ.domain` as a secondary index. Not a regression.

## Bug spotted in the source prototype (not ported)

`PredictionRecord.is_high_confidence_wrong()` referenced `self.kappa`, but that record has no
`kappa` field (κ lives on the nested `belief_state`). The MEBUS version reads `self.confidence`,
which is the intended field — so the rebuilt predicate is correct where the prototype's would
`AttributeError`.

Suite now **48 tests, all passing**.
