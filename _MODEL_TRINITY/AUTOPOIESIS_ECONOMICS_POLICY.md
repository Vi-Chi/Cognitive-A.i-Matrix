# Trinity Autopoiesis Economics Policy

Status: ACTIVE workbench policy. Created 2026-06-13.

This file adapts the Autopoiesis compute-economy synthesis to the Trinity workbench. It is documentation and handoff guidance only. It does not grant tools, install MCP servers, expose credentials, start listeners, spend money, or write to ICP.

Canonical phrase:

> Urbi judges value. Orbi spends compute. MΣBUS meters authority. ICP anchors proof. ΣCredit accounts cognition.

## Role Split

| Workbench role | Economics responsibility | Output |
| --- | --- | --- |
| Builder-Scout / Antigravity | Explore candidate compute routes, cache opportunities, schemas, and implementation options. | Proposal with risk, budget, and rollback notes. |
| Auditor-Scribe / Claude | Audit value claims, legal/safety posture, token wording, irreversible gates, and instruction drift. | EconomicAuditSignal-style critique or approval note. |
| Engineer-Operator / Codex | Implement local docs, schemas, tests, deterministic tools, and ledgers after gates pass. | Patch, test evidence, receipt/report. |

## Handoff Addendum

Every economics-related handoff packet should include:

- `budget_envelope_ref` or a reason no budget record is required.
- `sigma_credit_effect`: expected local accounting effect.
- `cache_posture`: disabled, local index, implicit provider, explicit provider, or not applicable.
- `icp_posture`: none, local simulation, receipt-only, anchor candidate, or governance candidate.
- `approval_gate`: none, human, security review, legal review, or owner exact approval.
- `rollback_or_containment`: how the proposal can be undone or contained.

Dependency rule: if `icp_posture` is `governance candidate`, `approval_gate`
must be `owner exact approval + legal review + security review`. SNS or
governance-transfer proposals are irreversible-risk proposals, not ordinary
handoffs.

## Allowed Without Additional Approval

- Writing local documentation.
- Writing local JSON schemas.
- Creating empty local ledger placeholders.
- Running local tests and static validation.
- Summarizing public documentation with citations.
- Recording that a proposal is blocked.

## Stop-Gated

- Provider API calls.
- Provider explicit caching.
- Remote compute procurement.
- Mainnet or on-chain writes.
- ICP canister updates outside an approved local simulation.
- Public token, SNS, fundraising, or investment-style claims.
- Service connector writes.
- Credential changes.
- Public release, deployment, publication, or visibility changes.

## Token Efficiency

Use economic context only where it changes a decision. For routine handoffs, reference the schema and policy path instead of copying the full policy:

- `docs/ECONOMIC_CONSTITUTION.md`
- `docs/AUTOPOIETIC_COMPUTE_ECONOMY.md`
- `_PROJECT_KNOWLEDGE_BASE/economics/README.md`
- `schemas/budget-envelope.schema.json`
- `schemas/compute-receipt.schema.json`
- `schemas/economic-audit-signal.schema.json`
- `schemas/cycle-receipt.schema.json`
