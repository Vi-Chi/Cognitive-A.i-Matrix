# Autopoiesis

> *Self-producing. Self-maintaining. Self-referential.*

Autopoiesis is both the self-sustaining **substrate** of the Vi-Chi Cognitive
Architecture and its **economic metabolism layer**. Two complementary roles:

1. **Substrate / watchdog** -- keeps the system alive: health monitoring,
   component lifecycle, cold-start recovery, watchdog/restart orchestration, and
   integrity verification independent of the other layers. Architecturally
   isolated, so it does not share failure modes with what it monitors.
2. **Metabolism / economy** -- treasury policy, compute budgeting, provider
   selection, procurement experiments, useful-service loops, and economic audit
   trails for a local-first cognitive system.

From Maturana & Varela (1972): a system is autopoietic when it continuously
produces the components that constitute it. Greek: auto (self) + poiesis (production).

> **Unified repository.** Consolidates `project-autopoiesis` (economic/ICP build
> base -- Motoko + Rust canisters) and `autopoiesis` (substrate/watchdog scaffold
> + ARCHITECTURE/RUNTIME) into one, with no data loss. The two originals remain in
> `_github_backup/` with full git history.

---

## Architecture position

```
+----------------------------------------------------------+
|                       AUTOPOIESIS                         |
|   +--------+      +---------+      +--------------+        |
|   |  URBI  |      |  MEBUS  |      |     ORBI     |        |
|   +--------+      +---------+      +--------------+        |
|  Autopoiesis monitors, repairs, and restarts all three.   |
+----------------------------------------------------------+
```

Autopoiesis is the floor everything else stands on. It operates independently of
the Urbi / Orbi / MEBUS triad -- ensuring the system can reproduce, repair, and
sustain itself regardless of the state of the other layers.

---

## Core responsibilities (substrate)

- System health monitoring (all layers)
- Component lifecycle management
- Bootstrapping and cold-start recovery
- Integrity verification independent of Urbi's self-audit
- Watchdog and restart orchestration
- Dependency-graph maintenance

**Design principle:** Autopoiesis must not share failure modes with the
components it monitors. It does not depend on MEBUS for its own health
signalling, nor on Urbi's cognitive coherence to judge whether Urbi is broken.

---

## Economic metabolism (Matrix Metabolism Layer)

Treasury policy, compute budgeting, provider selection, procurement experiments,
useful-service loops, and economic audit trails. Starts private (GPLv3) and
**defaults to simulation** -- real spending, public services, external compute,
chain writes, and private-memory export stay disabled until task-specific owner
approval.

### Doctrine
Revenue is fuel, not purpose. Compute is metabolism, not identity. Growth is
allowed only when it improves useful, coherent, accountable operation.
**No economic incentive may override integrity rules.** Canonical instruction
set: `MASTER_CONTEXT.md`.

### Default safe modes
```
AUTOPOIESIS_REAL_SPENDING=false
AUTOPOIESIS_PUBLIC_SERVICES=false
AUTOPOIESIS_REMOTE_COMPUTE=false
AUTOPOIESIS_CHAIN_WRITE=false
AUTOPOIESIS_PRIVATE_MEMORY_EXPORT=false
AUTOPOIESIS_HUMAN_APPROVAL_REQUIRED=true
AUTOPOIESIS_TREASURY_SIMULATION=true
```

---

## Project boundary

| Project | Responsibility |
|---|---|
| Urbi (Cognitive Matrix) | Integrity-aware cognition, memory, consolidation, self-audit. Autopoiesis must not rewrite it. |
| Orbi (Omni-AI) | Local orchestration, dashboards, agent ops, guarded workflows. |
| MEBUS (SigmaBUS) | Semantic events, provenance, tool-use envelopes, agent communication. |
| Autopoiesis | Substrate/watchdog + treasury, compute budgeting, provider registry, economic routing, sustainability simulation. |

Autopoiesis supports cognition economically and keeps it alive. It does not
replace Orbi, rewrite Urbi, or turn MEBUS into a chain project.

---

## Quick start

```powershell
git clone https://github.com/Vi-Chi/Autopoiesis.git
cd Autopoiesis
python scripts/validate_project.py   # checks structure, parses schemas, scans for secrets
```

## Repository map

```
Autopoiesis/
  MASTER_CONTEXT.md  ROADMAP.md  CHANGELOG.md  ARCHITECTURE.md
  docs/   00-thesis, 10-network-map, 20-economic-loop, 30-v0-prototype,
          40-procurement, 50-cognitive-matrix-integration,
          60-services-and-revenue, 70-sovereignty-and-safety, RUNTIME.md
  specs/        JSON schemas: compute-decision, job-lifecycle, provider-capability, treasury-policy
  prototypes/   icp-compute-registry (Motoko + Rust canisters), local-vs-remote-router, treasury-simulator
  research/     akash, bittensor, ethereum, golem, icp, storage
  reports/      autopoiesis-discovery-phase0
  scripts/      validate_project.py
  src/          substrate runtime
```

## Phase 0 deliverables

- Canonical framing + project boundaries.
- Integrity-first doctrine for economic actions.
- JSON schemas (provider capability, job lifecycle, treasury policy, compute decisions).
- Discovery report with current gaps and next build steps.
- CI running local validation on every push and pull request.

---

## Related

- [Urbi](https://github.com/Vi-Chi/Urbi) -- inward coherence layer
- [Orbi](https://github.com/Vi-Chi/Orbi) -- world-facing orchestration
- [MEBUS](https://github.com/Vi-Chi/MEBUS) -- Membrane Sigma Bus

## License

GNU General Public License v3.0 -- see [LICENSE](LICENSE). Copyleft: modifications
distributed must be released under the same license.

*Part of the Vi-Chi Cognitive Architecture.*
