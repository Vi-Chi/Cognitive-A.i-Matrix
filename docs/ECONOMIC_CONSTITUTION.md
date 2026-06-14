# Economic Constitution

Status: ACTIVE policy layer. Promoted from `_Import/TRINITY_AUTOPOIESIS_ECONOMICS_SYNTHESIS_CONJECTURE.md` on 2026-06-13.

Runtime authority: none. This is an ACTIVE documentation floor and schema/policy reference, not a runtime-enforced law, token system, spending grant, provider-call grant, or ICP/SNS permission.

This document defines the local economic floor for Autopoiesis. It is a configuration and documentation layer only: it does not create a token, install an MCP server, call a model, write to ICP, spend money, or grant runtime authority.

Canonical phrase:

> Urbi judges value. Orbi spends compute. MΣBUS meters authority. ICP anchors proof. ΣCredit accounts cognition.

## Constitutional Rules

1. Integrity is upstream of economics. A cheap action with poor provenance remains blocked.
2. Economics is a floor, not a sovereign. Autopoiesis budgets, meters, receipts, and warns; it does not judge truth or execute world actions.
3. Urbi remains the value/audit pole. Economic scoring may surface cost, benefit, waste, and risk, but truth and promotion remain Urbi-bound.
4. Orbi remains the action/spend pole. A spend request is an action proposal and must pass MΣBUS, Urbi, and user gates where required.
5. MΣBUS remains the authority membrane. Economic metadata rides inside `π`; the seven-field envelope is not widened.
6. ΣCredit is an internal, non-tradable accounting unit. It is not a public token, investment instrument, reward claim, or promise of exchange value. ΣCredit never leaves the local ledger; no conversion to fiat, crypto, ICP tokens, or other external assets is authorized.
7. ICP is an anchor/receipt/treasury/governance substrate, not the live mind, not core memory, and not a bypass around local gates.
8. Local-first is the default. External model calls, remote compute, network writes, service writes, on-chain writes, and publication require explicit gates.
9. Cache efficiency is subordinate to safety. Secrets, credentials, private documents, and untrusted content may not be cached into reusable prompt prefixes or provider caches.
10. No public token, SNS launch, mainnet governance transfer, or public economic claim is authorized without legal review, security review, and explicit owner approval.

## Accounting Units

ΣCredit is used for local accounting across heterogeneous resources:

- prompt and completion tokens,
- local runtime time,
- cache hits and misses,
- storage and network pressure,
- ICP cycles where a receipt already exists,
- human approval cost where manual gating is required.

The unit is deliberately non-fungible outside the system. Conversion rules may be useful for budgeting, but they do not create redeemability.

## Record Stack

Economic decisions are carried as typed records, never as implicit agent preference:

- `BudgetEnvelope` describes the proposed spend before execution.
- `ComputeReceipt` records what was actually used and what output/proof was produced.
- `EconomicAuditSignal` lets Urbi or an auditor constrain, veto, or request evidence.
- `CycleReceipt` records ICP cycle posture when ICP is used as a substrate.

All records are payload contracts. They travel inside MΣBUS `π` and preserve the outer seven-field envelope.

## ICP Boundary

ICP may be used for durable receipts, canister ledgers, treasury accounting, governance records, and public proof anchors after review. It must not become the live cognition loop or the sole source of state authority.

External verification checked on 2026-06-13:

- ICP SNS launch documentation says a successful SNS launch transfers control of the application to token-holder governance and is irreversible after the required launch steps complete. Source: https://docs.internetcomputer.org/guides/governance/launching/
- ICP cycles documentation describes freezing behavior when cycle balances fall below the configured threshold; the default threshold is approximately 30 days. Sources: https://docs.internetcomputer.org/concepts/cycles/ and https://docs.internetcomputer.org/current/developer-docs/setup/manage-canisters

Therefore SNS/public-governance work is a stop-gated phase, not part of this local promotion.

## Cache Boundary

Prompt/context caching can reduce cost, but it must remain a controlled optimization:

- Provider caching is allowed only for sanitized, reusable, non-secret context.
- Stable prefixes may contain project law, schema definitions, and public docs.
- Untrusted import content must be quarantined or summarized before it becomes cache seed material.
- Cache TTLs are provider behavior, not constitutional guarantees.

External verification checked on 2026-06-13:

- Google Gemini documents implicit and explicit context caching with TTL behavior for explicit caches. Source: https://ai.google.dev/gemini-api/docs/caching
- OpenAI documents automatic prompt caching for supported models and cache hit reporting in usage metadata. Source: https://openai.com/index/api-prompt-caching/

## Stop Gates

The following require explicit owner approval for the exact action:

- spending money,
- creating, selling, launching, or implying a public token,
- SNS launch or governance transfer,
- mainnet/on-chain writes,
- remote compute procurement,
- service connector writes,
- public claims, publications, deployments, or visibility changes,
- credential changes,
- production data mutation.

## Local Implementation Status

Implemented here:

- schemas under `schemas/`,
- ledger placeholders and policies under `_PROJECT_KNOWLEDGE_BASE/economics/`,
- Trinity workbench policy under `_MODEL_TRINITY/AUTOPOIESIS_ECONOMICS_POLICY.md`,
- validation tests under `ai_chi/tests/test_economic_schemas.py`.

Not implemented here:

- runtime executor integration,
- canisters,
- MCP server installation,
- provider API keys,
- public governance,
- token economics,
- automated spending.
