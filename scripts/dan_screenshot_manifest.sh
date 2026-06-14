#!/usr/bin/env bash
set -euo pipefail

dir="${1:-}"
if [ -z "$dir" ] || [ ! -d "$dir" ]; then
  echo "Usage: $0 artifacts/evidence/YYYY-MM-DD_slug" >&2
  exit 1
fi

manifest="$dir/screenshots/SCREENSHOT_MANIFEST.md"
mkdir -p "$dir/screenshots"
{
  echo "# Screenshot Manifest"
  echo
  echo "- Evidence folder: $dir"
  echo "- Generated: $(date -Is)"
  echo
  echo "| File | Description | Data type real/sample/synthetic | Public-safe? | Redaction needed | Claim supported |"
  echo "|---|---|---|---|---|---|"
  find "$dir/screenshots" -maxdepth 1 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' \) 2>/dev/null | sort | while read -r f; do
    base="$(basename "$f")"
    echo "| $base |  |  | no-review-required |  |  |"
  done
} > "$manifest"

echo "$manifest"
