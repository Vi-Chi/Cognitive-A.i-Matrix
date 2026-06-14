#!/usr/bin/env bash
set -euo pipefail

echo "# DAN Stewardship Scan"
echo
echo "## Location"
echo "PWD: $PWD"
echo
echo "## Git State"
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git status --short || true
  echo
  echo "## Recent Commits"
  git log --oneline --decorate -n 15 || true
else
  echo "Not inside a git repository or git unavailable."
fi

echo
echo "## Top-Level Tree"
find . -maxdepth 2 -type f \
  ! -path './.git/*' ! -path './node_modules/*' ! -path './target/*' ! -path './dist/*' ! -path './build/*' \
  | sort | sed 's#^./##' | head -300

echo
echo "## Candidate Canon / State Docs"
for f in AGENTS.md CLAUDE.md DO_ANYTHING_NOW.md README.md LICENSE docs/PROJECT_STATE.md docs/KNOWLEDGE_INDEX.md docs/ROADMAP.md docs/RISKS.md; do
  [ -e "$f" ] && echo "FOUND: $f"
done

echo
echo "## Stack Signals"
for f in package.json pnpm-lock.yaml yarn.lock package-lock.json pyproject.toml requirements.txt Cargo.toml go.mod dfx.json Dockerfile docker-compose.yml compose.yml Makefile; do
  [ -e "$f" ] && echo "FOUND: $f"
done

echo
echo "## Documentation Signals"
if command -v rg >/dev/null 2>&1; then
  rg -n --hidden --glob '!{.git,node_modules,target,dist,build,.venv,venv}/**' \
    'CANON|ACTIVE|WIP|RADAR|OBSOLETE|UNKNOWN|RISK|canon|deprecated|obsolete|architecture|invariant|contract|schema|threat|safety|rollback|TODO|FIXME|ADR|RFC|Urbi|Orbi|MΣBUS|PredictionRecord|CAL|Ω|κ|μ|τ' . || true
else
  echo "ripgrep unavailable; skipping signal scan."
fi

echo
echo "## Suggested Next Step"
echo "Create/update docs/KNOWLEDGE_INDEX.md, then select one safe high-value improvement cycle."
