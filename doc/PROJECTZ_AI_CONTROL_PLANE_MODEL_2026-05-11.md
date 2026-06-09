# Projectz AI Control Plane Model

Date: `2026-05-11`

Purpose: model how AnythingLLM, Omni-ai, Gordon, Codex, Cognitive Matrix, and the Raspberry Pi stack should relate as one maintainable AI/LLM operations system.

This document synthesizes the `.MD` corpus into an active architecture reference. It is a documentation model, not a live service change.

## Component Roles

| Component | Primary role | Authority boundary |
| --- | --- | --- |
| AnythingLLM | retrieval UI, assistant surface, workspace Q&A | may retrieve and explain; should not directly mutate Docker, nginx, databases, or secrets |
| Omni-ai | local agent/service layer, health reports, system inventory, migration prep | owns scripts, reports, policy docs, and safe orchestration patterns |
| Cognitive Matrix | memory and reasoning policy layer | defines claims, axioms, formulas, trust posture, and reflection rules; not a shell executor |
| Gordon | guarded local admin console | safe reads and constrained ops notes; mutation only through explicit gates |
| Gordon MCP | structured Gordon/Projectz tool surface | read-oriented by default |
| Docker MCP | Docker inspection and approval-gated management | root-equivalent when mutation is approved; never expose broadly |
| Codex | root-level build engineer and documentation maintainer | executes planned changes after discovery, backup, and verification |
| RPi4 | current control plane and memory node | owns workspace authority, ingestion, services, logs, and dashboards |
| RPi5 + Hailo | future edge inference worker | runs supported local small-model and perception workloads; does not become source of truth |
| External frontier model | hard reasoning and long-context worker | advisory; no direct safety-critical or infrastructure mutation |

## System Formula

```text
reliable Projectz AI operations =
  curated memory
  + live system evidence
  + bounded tool access
  + approval-gated mutation
  + dated change logs
  + post-change verification
```

## Control Flow

1. AnythingLLM retrieves curated docs, runbooks, reports, and source dispositions.
2. Cognitive Matrix policy determines whether a claim is supported, contradicted, or unresolved.
3. Gordon and MCP tools perform read-oriented checks against the live Pi.
4. Codex compares retrieved context to live state.
5. Codex prepares a narrow change plan and backup path.
6. Human approval is required for medium-risk or mutating service actions.
7. Codex applies the smallest safe change.
8. Verification runs from both service and user-facing layers.
9. Results are written back as dated artifacts.

## Data Flow

| Source | Curated output | Retrieval destination |
| --- | --- | --- |
| `.MD` corpus | synthesis docs, control model, RAG manifest | AnythingLLM / Gordon console |
| `/opt/Omni-ai/reports` | health, port, Docker, service reports | AnythingLLM and ops review |
| `/mnt/workspace/Projectz/_shared/ops_logs` | dated change history | persistent memory |
| Cognitive Matrix notes | trust rules, axioms, reflective memory | policy context after curation |
| live service discovery | inventories and verification notes | dated snapshots, not timeless truth |

## Boundaries

AnythingLLM:

- use for "what changed?", "which runbook applies?", "what docs support this?"
- do not use as a direct mutation engine
- keep its API keys and JWT secret out of RAG
- keep `JWT_SECRET` pinned so restarts do not invalidate sessions unexpectedly

Omni-ai:

- keep scripts idempotent and report-oriented
- bind new services to loopback by default
- separate config, runtime data, reports, backups, and logs
- avoid mounting `/opt/Omni-ai/config/nginx` over `/etc/nginx`

Cognitive Matrix:

- keep policy and memory separate from live data stores
- express claims with support/contradiction/unresolved state
- prefer reflection and review over autonomous mutation

Gordon and MCP:

- read first
- write ops notes only in controlled paths
- require explicit approval for Docker or service mutation
- never expose Docker MCP through nginx by default

Codex:

- use live evidence over archived notes
- back up configs before editing
- avoid path drift
- verify after every change
- record files changed, services touched, services not touched, and residual risk

## RPi4 To RPi5 Routing Model

| Task class | Default home | Reason |
| --- | --- | --- |
| indexing, watchers, workspace scans, report generation | RPi4 | deterministic and close to storage |
| AnythingLLM, RAG manifests, source dispositions | RPi4 | memory/control-plane role |
| OCR, vision triage, compact local inference | future RPi5 + Hailo | better edge-inference fit |
| general LLM chat, coding, complex research | external model or stronger host | exceeds Pi-class reliability and thermal budget |
| helm, propulsion, collision, battery protection | deterministic logic and human control | LLMs stay advisory-only |

## Service Preservation Rules

The reverse-engineered stack notes establish these defaults:

- keep host nginx as the canonical reverse proxy
- keep AnythingLLM backend loopback-only
- keep Nextcloud backend loopback-only
- keep database access internal
- use the sample compose only as a pattern
- do not publish phpMyAdmin by default
- do not replace live Nextcloud or MariaDB auth in one unreviewed compose edit
- use named volumes carefully; changing volume names can hide live data

## RAG Model

Preferred retrieval set:

- curated KB Markdown
- dated audits
- source disposition documents
- sanitized admin scans
- service inventories
- architecture and migration docs
- ops logs that do not contain secrets

Avoid by default:

- raw transcripts with credentials
- `.env` files
- private keys
- Docker volume data
- database files
- noisy runtime logs
- old scan facts treated as current truth

## Claim Handling

Use this tri-state layer:

| State | Meaning | Agent behavior |
| --- | --- | --- |
| `+` | supported enough to use | cite evidence and proceed within scope |
| `-` | contradicted, rejected, or unsafe | avoid and document why |
| `=` | unresolved | gather more evidence before acting |

Model availability, benchmark numbers, package-update lists, port exposure, and service-health facts should default to `=` unless verified against current live state.

## Implementation Backlog

Low-risk documentation and report work:

- keep this control-plane model in RAG
- keep `.MD` source disposition current
- add verification questions for AnythingLLM ingestion
- add a current model-landscape revalidation task when model routing is being updated

Approval-gated infrastructure work:

- rotate or move secrets only with service-specific backups
- change nginx or compose only after backup and `config` validation
- alter Docker MCP exposure only after explicit approval
- change Nextcloud/MariaDB/Redis credentials only in a maintenance window

