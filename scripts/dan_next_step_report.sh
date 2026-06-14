#!/usr/bin/env bash
set -euo pipefail
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="reports/dan-next-step-${stamp}.md"
mkdir -p reports
cat > "$out" <<'EOF'
# DAN Next Step / Stewardship Report

## Current Objective

## Repo State

## Canonical Docs Read

## Knowledge Index Status
- Updated: no
- Canon files:
- Radar/obsolete files:

## Diagnosed Gaps

## Candidate Tasks
- [ ] Task
  - Why it matters:
  - Evidence/source:
  - Risk level:
  - Suggested mode:
  - Verification:
  - Stop gate:

## Selected Next Safe Task

## Work Completed This Cycle

## Verification

## Open Risks

## Do Not Touch Yet

## Next Agent Handoff
- Current objective:
- Repo state:
- Canonical docs read:
- Files changed:
- Tests run:
- Open risks:
- Next safe task:
- Do not touch yet:
EOF
echo "Created $out"
