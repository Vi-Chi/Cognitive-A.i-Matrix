# MCP Tool Registry

MCP is an integration layer, not an authority layer. MΣBUS, Urbi, Orbi, and user
gates remain final.

This file is documentation-only. It does not configure MCP servers.

## Proposed Namespaces

- `mcp.project.read`
- `mcp.project.patch_proposal`
- `mcp.git.readonly`
- `mcp.tests.runner`
- `mcp.docs.generator`
- `mcp.discord.mirror`
- `mcp.openplotter.readonly`
- `mcp.signalk.readonly`
- `mcp.atak.cot_readonly`
- `mcp.worldwideview.readonly`
- `mcp.aidict.records`
- `mcp.dream.replay`
- `mcp.quarantine.inspect`

## Disabled Namespaces

- `mcp.shell.execute`
- `mcp.docker.control`
- `mcp.filesystem.write_anywhere`
- `mcp.network.unrestricted`
- `mcp.secrets.read`
- `mcp.hardware.control`

## Registry Row Template

```yaml
tool_id: mcp.namespace.tool_name
status: proposed|verified|disabled|rejected
scope: short description
read_write_behavior: read-only|proposal-only|write-gated|forbidden
risk_level: low|medium|high|critical
allowed_models:
  - codex
  - claude
  - antigravity
approval_requirement: none|user|MΣBUS|Urbi|user+MΣBUS+Urbi
output_record_type: RecordTypeName
rollback_or_containment: short note
verification_method: exact command or connector check
last_checked: YYYY-MM-DD
```

Only verified tools may be treated as dependencies. Candidate tools remain
planning guidance until checked in the current session or recorded in an
approved registry.
