# A.i Core â€” Taiji Triad Runtime

`ai_chi` is the total runtime formed by **Urbi**, **Orbi**, and **MÎ£BUS**.

It uses a Taiji-like balance metaphor:

- **Urbi** is the still / auditing / veto pole.
- **Orbi** is the active / executing / world-facing pole.
- **MÎ£BUS** is the living membrane that preserves separation, routing, provenance,
  and trust-floor enforcement.

This is **not** a yin-yang duality. It is a **triadic runtime**: two complementary
powers fused by an active membrane.

> Governed by `_PROJECT_KNOWLEDGE_BASE/URBI_ORBI_MEBUS_BALANCE_CONSTITUTION_2026-06-08.md`
> â€” asymmetric separation of powers, Î©â‚ˆ mode-gating, "no capability without its gate."

## Packages

| Package | Role |
|---|---|
| `ai_chi.bus` | canonical MÎ£BUS re-export (membrane) |
| `ai_chi.core` | P0 Reality Loop: observe -> audit -> ledger -> outcome -> CAL/Î©â‚„ |
| `ai_chi.urbi` | Urbi cognition: bridge to the 3-6-9 auditor, dream, pattern, memory |
| `ai_chi.orbi` | Orbi execution: PolicyGate, spawner, ghost runtime, ledger |
| `ai_chi.aidict` | AIDICT investigation-contract scout |
| `ai_chi.tests` | full offline test suite |

Run the P0 loop: `python -m ai_chi.run_core`  (add `--fake-auditor` for an offline smoke test).
