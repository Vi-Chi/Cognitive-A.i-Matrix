#!/usr/bin/env bash
set -euo pipefail

printf "# DAN Preflight\n\n"
printf "## Location\n"
printf "PWD: %s\n\n" "$PWD"

printf "## Git State\n"
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git status --short || true
else
  printf "Not inside a git repository or git unavailable.\n"
fi
printf "\n"

printf "## Canonical Docs\n"
for f in README.md LICENSE AGENTS.md CLAUDE.md DO_ANYTHING_NOW.md docs/architecture docs docs/runbooks; do
  if [ -e "$f" ]; then printf "FOUND: %s\n" "$f"; fi
done
printf "\n"

printf "## Research/Architecture Signals\n"
if command -v rg >/dev/null 2>&1; then
  rg -n --hidden --glob '!{.git,node_modules,target,dist,build,.venv,venv}/**' \
    'canon|deprecated|obsolete|architecture|invariant|contract|schema|threat|safety|rollback|TODO|FIXME|Urbi|Orbi|MΣBUS|PredictionRecord|CAL|Ω|κ|μ|τ' . || true
else
  printf "ripgrep not available; skipping research signal scan.\n"
fi
printf "\n"

printf "## Stack Signals\n"
for f in package.json pnpm-lock.yaml yarn.lock package-lock.json pyproject.toml requirements.txt Cargo.toml go.mod dfx.json Dockerfile docker-compose.yml compose.yml Makefile; do
  if [ -e "$f" ]; then printf "FOUND: %s\n" "$f"; fi
done
printf "\n"

printf "## Candidate Test Commands\n"
[ -e package.json ] && printf "- npm test / npm run lint / npm run build, inspect package.json first\n"
[ -e pyproject.toml ] || [ -e requirements.txt ] && printf "- python -m pytest, if pytest is configured\n"
[ -e Cargo.toml ] && printf "- cargo test\n"
[ -e go.mod ] && printf "- go test ./...\n"
[ -e Makefile ] && printf "- make test, inspect Makefile first\n"
[ -e dfx.json ] && printf "- dfx deploy --dry-run or local replica flow, inspect dfx.json first\n"
printf "\n"

printf "## Credential-like File Hits (filenames only)\n"
if command -v rg >/dev/null 2>&1; then
  rg -l --hidden --glob '!{.git,node_modules,target,dist,build,.venv,venv}/**' \
    '(api[_-]?key|secret|token|password|BEGIN PRIVATE KEY|tskey-|sk-[A-Za-z0-9]|OPENAI_API_KEY|ANTHROPIC_API_KEY)' . || true
else
  printf "ripgrep not available; skipping secret filename scan.\n"
fi
printf "\n"

printf "## DAN Reminder\n"
printf "Discover → choose safe mode → make smallest valuable move → verify → report.\n"
