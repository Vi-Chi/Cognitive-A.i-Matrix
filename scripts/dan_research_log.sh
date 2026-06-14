#!/usr/bin/env bash
set -euo pipefail

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="reports/dan-research-${stamp}.md"
mkdir -p reports
cat > "$out" <<'EOF'
# DAN Research Log

## Objective

## Research Depth
R0 / R1 / R2 / R3 / R4

## Internal Documents Searched

## External Sources Checked

## Facts Verified

## Inferences Made

## Contradictions Found

## Missing Evidence

## Adoption Recommendation
Adopt now / test-only / watch / reject

## Follow-up Queries
EOF
printf "Created %s\n" "$out"
