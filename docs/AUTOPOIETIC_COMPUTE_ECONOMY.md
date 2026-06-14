# Autopoietic Compute Economy

Status: ACTIVE design record. Local documentation and schema promotion only.

Autopoiesis supplies the substrate that keeps A.i alive: health, budget discipline, receipts, recovery posture, and long-run compute viability. The economic layer does not replace Urbi, Orbi, or MΣBUS. It gives them a shared accounting language for deciding when compute should be spent, deferred, cached, localized, or escalated.

## Model

The local compute economy has five layers:

1. Proposal: an actor asks for work, evidence, generation, verification, or procurement.
2. Budget: a `BudgetEnvelope` estimates cost, risk, route, cache posture, and approval gates.
3. Gate: MΣBUS checks authority and Urbi can audit value, uncertainty, and integrity.
4. Execution receipt: a `ComputeReceipt` records the actual route, cost, cache result, output hash, and error/quality signals.
5. Audit feedback: `EconomicAuditSignal` and `CycleReceipt` records constrain future routing.

The economy is autopoietic only when it improves future self-maintenance. It must reduce waste, expose runway, preserve local operation, and prevent economic incentives from overriding truth.

## Roles

| Role | Economic responsibility | Forbidden shortcut |
| --- | --- | --- |
| Urbi | Judge value, uncertainty, evidence, and promotion readiness. | Spending compute or executing actions. |
| Orbi | Spend bounded compute after gates pass. | Self-judging value or bypassing audit. |
| MΣBUS | Meter authority, trust, provenance, mode, and route. | Expanding the envelope shape for economic convenience. |
| Autopoiesis | Track budgets, receipts, cache policy, cycles, and runway. | Becoming a sovereign controller. |
| ICP | Anchor receipts, treasury records, and governance after approval. | Acting as live cognition or unreviewed mainnet authority. |

## Ledgers

Local economics ledgers live under `_PROJECT_KNOWLEDGE_BASE/economics/`:

- `compute_decisions.jsonl` for budget decisions and route choices.
- `compute_receipts.jsonl` for actual cost and output receipts.
- `economic_audit_signals.jsonl` for Urbi/economic audit feedback.
- `budget_policy.json` for default stop gates and cost ceilings.
- `cache_policy.json` for context-cache safety.

The JSONL ledgers are intentionally empty at promotion time. They are placeholders for future deterministic writers, not evidence that execution occurred.

## Routing Ladder

Routing is local-first:

1. Reuse current context or local indexed docs.
2. Use deterministic scripts/tests.
3. Use local model or offline model-assisted proposal tools when allowed.
4. Use provider model calls only when owner-approved or already within a scoped session policy.
5. Use remote/decentralized compute only after explicit task approval.
6. Use ICP writes only after security/legal review and exact owner approval.

RouteLLM-style model routing research supports the general idea that cheaper models can handle simpler requests while preserving quality on some benchmarks. That is evidence for cautious routing design, not authority to make provider calls. Source checked 2026-06-13: https://github.com/lm-sys/RouteLLM and https://openreview.net/forum?id=8sSqNntaMr

## Cache Policy

Cache opportunities are budget signals:

- stable project law can be cache seed material,
- volatile work queues and private source content need freshness checks,
- untrusted imports must be summarized and quarantined before reuse,
- cache hits are receipts, not proof of correctness,
- cache savings may never bypass Urbi audit or MΣBUS gates.

## ICP Phases

| Phase | Allowed posture | Stop gate |
| --- | --- | --- |
| Local receipt | Docs, schemas, local JSONL ledger placeholders. | None beyond normal file edits. |
| Local canister simulation | Test-only canisters, no real funds, no public claims. | Owner approval for exact command set. |
| Mainnet anchor | Receipt hash or treasury record write. | Security review and explicit approval. |
| Governance/SNS | Public governance transfer or tokenized control. | Legal review, security review, owner approval, rollback/irreversibility briefing. |

## Record Flow

```text
proposal
  -> BudgetEnvelope
  -> MΣBUS gate + Urbi audit
  -> Orbi bounded execution or refusal
  -> ComputeReceipt
  -> EconomicAuditSignal
  -> future route/cache/budget policy update
```

If ICP is involved:

```text
ComputeReceipt
  -> local receipt hash
  -> CycleReceipt
  -> optional reviewed anchor
```

## Promotion Rule

New economic behavior is promoted only when it has:

- a schema,
- a local ledger representation,
- an audit signal,
- a rollback or containment story,
- a stop-gate analysis,
- tests or deterministic validation.
