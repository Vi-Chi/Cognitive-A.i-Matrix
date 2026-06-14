# Public Release Blockers

## 2026-06-14 — GitHub Root Publication Gate

- Status: Gated.
- Artifact: root `A.i` lane / GitHub release draft.
- Blocker: the lane root is not currently a live git working tree. GitHub authentication is available for read/write-capable tooling, but this cycle intentionally did not run `git init`, attach a remote, push, change visibility, or publish a release.
- Required before publication:
  - confirm exact target repository and visibility,
  - confirm whether the root `A.i` lane should become one GitHub repo or remain a staging/workbench that feeds the existing `Vi-Chi/*` repo family,
  - run `scripts/dan_pre_publish_gate.py` on the final publishable set,
  - keep `_backup/`, `scratch_outbox/`, runtime ledgers, archives, nested `.git` directories, credential-like files, and local state excluded,
  - install the pre-push hook if a root repo is initialized,
  - obtain explicit owner approval for the exact push/release/visibility action.
- Claim boundary: local readiness evidence does not equal publication approval.

## 2026-06-13 — CM5 + Hailo Benchmark Package

- Status: Blocked.
- Artifact: `_PROJECT_KNOWLEDGE_BASE/cm5_hailo_benchmarks_2026-06-13/public/CM5_HAILO_BENCHMARK_REPORT.md`
- Blocker: this public package does not yet contain embedded raw-backed CM5/Hailo benchmark data. Internal 2026-06-08 live reports contain OBSERVED CM5/Hailo evidence, but the package still needs raw outputs integrated or rerun, redaction, and approval.
- Required before publication:
  - run the CM5 collector on the actual node or integrate prior raw CM5 outputs,
  - capture HailoRT/device context,
  - capture raw-backed `hailortcli` benchmark output,
  - capture thermal/throttling context,
  - update public report/CSV/JSON,
  - rerun redaction,
  - Vi approves exact platform/account/channel and final text.
- Claim boundary: not an official Raspberry Pi, Hailo, or MLPerf result.
