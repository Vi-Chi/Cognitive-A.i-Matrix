#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

echo "# DAN Public Release Scan"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

echo "## Public artifact candidates"
find . -maxdepth 3 -type f \
  \( -iname 'README.md' -o -iname 'CHANGELOG.md' -o -iname 'LICENSE*' -o -iname 'SECURITY.md' -o -iname 'CONTRIBUTING.md' -o -path './docs/*' \) \
  | sort | sed 's#^#- #' || true

echo

echo "## High-risk token patterns"
# Heuristic only. Does not replace secret scanning.
grep -RInE '(api[_-]?key|secret|token|password|passwd|bearer |sk-[A-Za-z0-9]|ghp_[A-Za-z0-9]|BEGIN (RSA|OPENSSH|EC|PRIVATE) KEY|seed phrase|mnemonic)' . \
  --exclude-dir=.git --exclude='dan_public_release_scan.sh' || true

echo

echo "## Public release files present"
for f in README.md LICENSE SECURITY.md CONTRIBUTING.md CHANGELOG.md docs/PUBLICATION_QUEUE.md docs/PUBLIC_RELEASE_LEDGER.md docs/PUBLIC_ROADMAP.md docs/PRESS_KIT.md; do
  if [[ -e "$f" ]]; then
    echo "- present: $f"
  else
    echo "- missing: $f"
  fi
done

echo

echo "## Reminder"
echo "This scan is heuristic. Do not publish without human review, redaction, license/provenance check, and approval."
