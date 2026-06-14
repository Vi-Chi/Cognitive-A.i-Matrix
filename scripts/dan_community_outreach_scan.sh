#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
echo "# DAN Community Outreach Scan"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo
echo "## Public/community docs present"
for f in README.md LICENSE SECURITY.md CONTRIBUTING.md CHANGELOG.md docs/PUBLICATION_QUEUE.md docs/COMMUNITY_OUTREACH_QUEUE.md docs/COMMUNITY_FEEDBACK_LEDGER.md docs/COMMUNITY_CHANNEL_MAP.md docs/COMMUNITY_POSTING_POLICY.md docs/PUBLIC_ROADMAP.md docs/FAQ.md docs/DEMO_SCRIPT.md; do
  if [[ -e "$f" ]]; then echo "- present: $f"; else echo "- missing: $f"; fi
done
echo
echo "## Potential postable milestones"
find . -maxdepth 3 -type f \( -iname 'CHANGELOG.md' -o -iname '*release*notes*.md' -o -iname '*demo*.md' -o -iname '*benchmark*.md' -o -iname '*build*log*.md' -o -iname 'README.md' \) \
  ! -path './.git/*' ! -path './node_modules/*' | sort | sed 's#^#- #' || true
echo
echo "## Risk patterns to check before community publishing"
grep -RInE '(api[_-]?key|secret|token|password|passwd|bearer |sk-[A-Za-z0-9]|ghp_[A-Za-z0-9]|BEGIN (RSA|OPENSSH|EC|PRIVATE) KEY|seed phrase|mnemonic|marina|berth|home address|private link|discord token|cookie)' . \
  --exclude-dir=.git --exclude='dan_community_outreach_scan.sh' || true
echo
echo "## Reminder"
echo "Check platform and community rules manually/currently. This script is local-only and does not verify online rules."
