# ConfigProposalRecord Template

Use this template for substantial Trinity profile, tool-scope, handoff, prompt,
safety-rule, or MCP-registry changes.

```yaml
proposal_id: config_prop_<timestamp>
proposed_by: <codex|claude|antigravity|user>
target_model: <codex|claude|antigravity|shared>
change_type: <profile|tool_scope|handoff|prompt|safety_rule|mcp_registry>
affected_files:
  - <path>
reason: |
  <why this change is needed>
expected_improvement: |
  <what should improve>
risk: <low|medium|high|critical>
risk_notes: |
  <what could go wrong>
rollback: |
  <how to undo>
requires_user_approval: true
requires_urbi_review: true
requires_m_sigma_bus_review: true
status: draft
```

Do not mark a proposal approved merely because another model agrees with it.
Approval must come from the user or the appropriate canonical gate.
