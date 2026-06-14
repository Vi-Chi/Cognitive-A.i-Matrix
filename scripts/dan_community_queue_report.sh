#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
mkdir -p docs
QUEUE="docs/COMMUNITY_OUTREACH_QUEUE.md"
FEEDBACK="docs/COMMUNITY_FEEDBACK_LEDGER.md"
CHANNELS="docs/COMMUNITY_CHANNEL_MAP.md"
[[ -e "$QUEUE" ]] || cp "docs/COMMUNITY_OUTREACH_QUEUE_TEMPLATE.md" "$QUEUE" 2>/dev/null || printf '# COMMUNITY_OUTREACH_QUEUE.md

' > "$QUEUE"
[[ -e "$FEEDBACK" ]] || cp "docs/COMMUNITY_FEEDBACK_LEDGER_TEMPLATE.md" "$FEEDBACK" 2>/dev/null || printf '# COMMUNITY_FEEDBACK_LEDGER.md

' > "$FEEDBACK"
[[ -e "$CHANNELS" ]] || cp "docs/COMMUNITY_CHANNEL_MAP_TEMPLATE.md" "$CHANNELS" 2>/dev/null || printf '# COMMUNITY_CHANNEL_MAP.md

' > "$CHANNELS"
cat <<REPORT
# DAN Community Queue Report
Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)

Files ensured:
- $QUEUE
- $FEEDBACK
- $CHANNELS

Reminder: draft and queue only unless explicit approval or COMMUNITY_POSTING_POLICY.md authorizes the exact channel/action.
REPORT
