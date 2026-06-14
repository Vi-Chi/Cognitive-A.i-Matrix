#!/usr/bin/env bash
# DAN pre-publish gate — FAIL-CLOSED secret/PII scan.
# Unlike the *_scan.sh reporters (which only print), this gate EXITS NON-ZERO when a
# match is found, so it can block a commit/push/publish. Doctrine §15 fail_closed=true,
# §34.5 redaction gate. Exit codes: 0 clean · 1 hits found · 2 usage/setup error.
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT" || { echo "gate: cannot cd to '$ROOT'" >&2; exit 2; }

# Defer to the precision Python scanner
python.exe scripts/dan_pre_publish_gate.py "$ROOT"
