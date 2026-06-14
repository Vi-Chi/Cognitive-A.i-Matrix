#!/usr/bin/env bash
set -euo pipefail

evidence_dir="${1:-}"
cat <<EOF
### Evidence / PoC / Benchmark Capture

- PoC built: yes/no
- PoC level: P0/P1/P2/P3/P4/P5
- Evidence folder: ${evidence_dir:-}
- Commands captured:
- Logs captured:
- Metrics captured:
- Screenshots captured:
- Environment captured:
- Failures captured:
- Public-safe assets prepared:
- Private/sensitive assets flagged:
- Claim classification:
- Reproducibility status:
- Suggested public use:
- Next evidence step:
EOF
