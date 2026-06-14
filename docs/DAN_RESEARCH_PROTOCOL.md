# DAN Research Protocol

This protocol makes curiosity operational for Claude/Codex-style agents.

## Default Rule

Do not treat the repository or prompt as the whole truth. For non-trivial work, inspect internal documents and check current external sources before making durable architecture, tooling, hardware, security, AI-model, maritime, crypto, or dependency recommendations.

## Research Depth

| Depth | Use | Minimum Work |
|---:|---|---|
| R0 | tiny mechanical edit | no research beyond touched file |
| R1 | project-specific task | repo/document search and canonical-vs-obsolete check |
| R2 | current tool/API/hardware fact | official docs, changelog, release notes, source repo |
| R3 | choice between technologies | official docs plus credible independent comparison or implementation evidence |
| R4 | canonical/safety-critical decision | dossier: source map, risks, cost, test plan, rollback |

## Internal Document Sweep

Search for project state before editing:

```bash
find . -maxdepth 4 -type f | sort
rg -n "canon|deprecated|obsolete|architecture|invariant|contract|schema|threat|safety|rollback|TODO|FIXME|Urbi|Orbi|MΣBUS|PredictionRecord|CAL|Ω|κ|μ|τ" .
```

Classify findings:

- Canonical decision
- Tentative concept
- Deprecated/obsolete note
- Contradiction
- Missing evidence
- Missing test
- Useful research seed

## Online Research Sweep

When web/search/MCP/browser tools are available, check current sources for:

- official docs and release notes,
- source repository activity, issues, examples, and changelogs,
- security advisories,
- license compatibility,
- ARM64/RPi feasibility,
- Docker/offline/local support,
- hardware datasheets and real-world reports,
- benchmarks with reproducible method.

If web is unavailable, create a `Research To Verify` section containing exact search queries and likely authoritative sources.

## Evidence Rules

- Cite local file paths/headings/line numbers where possible.
- Cite URLs, doc titles, dates, versions, or commit identifiers for external claims.
- Separate facts from inference and speculation.
- Do not convert social/media/forum claims into canon without reproducible tests.
- Do not hide contradictions; turn them into follow-up tasks.

## Required Report Block

```markdown
### Research Performed
- Research depth: R0/R1/R2/R3/R4
- Internal docs searched:
- External sources checked:
- Facts verified:
- Inferences made:
- Contradictions found:
- Remaining research gaps:
```
