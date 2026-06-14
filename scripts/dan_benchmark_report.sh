#!/usr/bin/env bash
set -euo pipefail

dir="${1:-}"
if [ -z "$dir" ] || [ ! -d "$dir" ]; then
  echo "Usage: $0 artifacts/evidence/YYYY-MM-DD_slug" >&2
  exit 1
fi

report="$dir/benchmark_summary.md"
{
  echo "# Benchmark Summary"
  echo
  echo "- Evidence folder: $dir"
  echo "- Generated: $(date -Is)"
  echo
  echo "## Available Logs"
  find "$dir/logs" -type f 2>/dev/null | sort | sed 's/^/- /' || true
  echo
  echo "## Available Metrics"
  find "$dir/metrics" -type f 2>/dev/null | sort | sed 's/^/- /' || true
  echo
  echo "## Available Screenshots"
  find "$dir/screenshots" -type f 2>/dev/null | sort | sed 's/^/- /' || true
  echo
  echo "## Agent Notes"
  echo
  echo "- What was measured:"
  echo "- Why it matters:"
  echo "- Claim classification:"
  echo "- Limitations:"
  echo "- Public-safe assets:"
  echo "- Next benchmark step:"
} > "$report"

echo "$report"
