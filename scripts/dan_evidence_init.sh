#!/usr/bin/env bash
set -euo pipefail

slug="${1:-manual-evidence}"
slug="$(printf '%s' "$slug" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$//')"
stamp="$(date +%F_%H%M%S)"
dir="artifacts/evidence/${stamp}_${slug}"

mkdir -p "$dir"/{env,commands,logs,metrics,screenshots,notes}

{
  echo "# Evidence Folder"
  echo
  echo "- Task: $slug"
  echo "- Created: $(date -Is)"
  echo "- Working directory: $(pwd)"
  echo "- PoC level: UNKNOWN"
  echo "- Public-safe by default: no, review required"
  echo
  echo "## Summary"
  echo
  echo "## Evidence Index"
  echo
  echo "## Claim Classification"
  echo
  echo "## Redaction Notes"
  echo
  echo "## Next Step"
} > "$dir/README.md"

{
  echo "{"
  echo "  \"task\": \"$slug\","
  echo "  \"created_at\": \"$(date -Is)\","
  echo "  \"poc_level\": \"UNKNOWN\","
  echo "  \"public_safe\": false,"
  echo "  \"claim_classification\": []"
  echo "}"
} > "$dir/manifest.json"

{
  echo "# Commands"
  echo
  echo '```bash'
  echo "# paste exact commands here"
  echo '```'
} > "$dir/commands/commands.md"

{
  echo "# Observations"
  echo
} > "$dir/notes/observations.md"

{
  echo "# Failures / Anomalies"
  echo
} > "$dir/notes/failures.md"

{
  echo "# Public Claims"
  echo
  echo "| Claim | Evidence | Classification | Public-safe? |"
  echo "|---|---|---|---|"
} > "$dir/notes/public_claims.md"

# Best-effort environment capture; never fail the initializer on missing commands.
{
  echo "# System"
  date -Is || true
  uname -a || true
  printf '\n## CPU\n' || true
  (lscpu 2>/dev/null || sysctl -a 2>/dev/null | grep -E 'machdep.cpu|hw.memsize' || true)
  printf '\n## Memory\n' || true
  (free -h 2>/dev/null || vm_stat 2>/dev/null || true)
} > "$dir/env/system.txt"

{
  echo "# Git"
  git rev-parse --show-toplevel 2>/dev/null || true
  git branch --show-current 2>/dev/null || true
  git rev-parse HEAD 2>/dev/null || true
  git status --short 2>/dev/null || true
} > "$dir/env/git.txt"

{
  echo "# Versions"
  for cmd in python python3 node npm pnpm yarn rustc cargo go docker git; do
    if command -v "$cmd" >/dev/null 2>&1; then
      echo "## $cmd"
      "$cmd" --version 2>&1 || true
    fi
  done
} > "$dir/env/versions.txt"

echo "$dir"
