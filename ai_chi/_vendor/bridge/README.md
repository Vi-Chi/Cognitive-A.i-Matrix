# Urbi ↔ MΣBUS bridge

Wires the **running v2.1 tri-state 3-6-9 auditor** (`../audit.py`) onto the built **MΣBUS**
membrane. This is the first slice of the Urbi prototype core: Urbi (Yin / 3-6-9, *audits, never
acts*) emitting audited belief on the same wire Orbi (Yang / 2-4-6-8) and Autopoiesis speak.

It does **not** modify `audit.py`. The auditor is imported as-is; only its Ollama endpoint is
repointed at runtime (see `endpoint.py`).

## Verdict → M-protocol mapping

| 3-6-9 verdict | σ class emitted | Why |
|---|---|---|
| `[+]` confirmed | `m.belief` | audited belief, surfaced |
| `[-]` rejected | `m.belief` | audited belief, rejected |
| `[=]` suspended | `m.prediction_record` | the dream-layer synapse → ΦΔ (the `[=]` state is *precious*: model indecision ≠ epistemic uncertainty) |

All emissions are **cognition (`m.*`)**, never **action** — so Ω₈ never suppresses Urbi belief
(cognition flows even in DREAM), and `inv.gate_emit` refuses any action-class σ from Urbi.

## Invariants enforced at emit (`inv.py`)

- **Ω₆** payload is structured, not a natural-language blob (`m.belief` must carry `{state, confidence}`).
- **Ω₇** every emission carries provenance / causal parents.
- **Urbi-non-actuation** — Urbi may never emit an action-class σ (the 3-6-9 axis governs the loop, it does not enter it).
- **Ω₈** (mode-gate) is enforced downstream by `MembraneBus.publish`.

`OMEGA` in `inv.py` lists the full Ω₁–Ω₈ registry with the owner of each (Ω₄ Calibration Monitor is the next to build).

## Install / run

```bash
# from the repo root (cognitive_matrix_repo/)
pip install -e ../../MEBUS/mebus          # or set PYTHONPATH to MEBUS/mebus/src
PYTHONPATH=.:../../MEBUS/mebus/src python -m unittest bridge.tests.test_bridge -v
```

Tests fake the auditor, so **no Ollama is required** to run them.

## Use

```python
from mebus import MembraneBus, Mode
from bridge import UrbiMebusBridge, apply_to_auditor

apply_to_auditor()                 # point audit.py at Hailo-Ollama (10H) or CPU-Ollama fallback
bus = MembraneBus()
urbi = UrbiMebusBridge(bus)        # live TriStateAuditor constructed lazily
urbi.subscribe_requests()          # answer inbound m.audit_request on the bus
result = urbi.audit_and_publish("the AIS target is on a steady bearing")
```

## Endpoint (Hailo-Ollama)

`endpoint.resolve_ollama_base()` prefers Hailo-Ollama (the 10H, Ollama-API-compatible) then falls
back to CPU-Ollama. Set the node-specific URL once the 10H runtime is verified:

```bash
export URBI_HAILO_OLLAMA=http://127.0.0.1:<hailo-ollama-port>   # set after `hailortcli fw-control identify`
export URBI_CPU_OLLAMA=http://127.0.0.1:11434                    # fallback (default)
```

Until `URBI_HAILO_OLLAMA` is set, the auditor uses CPU-Ollama, so the core runs before the 10H
benchmark lands.

## Status

P0 slice — **built, unit-tested (faked auditor)**. Not yet run against the live Pi auditor or the
10H. Next: Ω₄ Calibration Monitor (CAL) for drift→HALT, and the node bring-up benchmark.
