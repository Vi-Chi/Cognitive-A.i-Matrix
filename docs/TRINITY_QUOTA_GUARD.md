# Trinity Quota Guard

Status: ACTIVE local coordination tool.

`tools/trinity_quota_guard.py` is a stdlib-only quota and liveness guard for the
local Trinity bridge. It helps Codex, Claude, and Antigravity route work around
session limits, quota exhaustion, cooldowns, stale heartbeats, and offline
periods without direct model-to-model control.

It is foreground repo-local automation. It is not installed as a hidden service.

## Boundaries

The quota guard does not:

- read API keys, auth tokens, cookies, credential files, or provider dashboards;
- call OpenAI, Anthropic, Google, or any other provider;
- enable paid credits, spending, or auto top-up;
- mutate Claude, Codex, Antigravity, MCP, or app config files;
- start sockets, brokers, listeners, daemons, or external services;
- execute model prompts as health checks;
- grant authority from one model to another.

The guard reads local bridge records only and treats provider limits as
configuration or evidence, never as hardcoded universal truth.

## Files

- `trinity_bridge/quota_guard.py` - config loading, state computation, downtime
  logging, quota poke writing, router decision, and CLI implementation.
- `trinity_bridge/quota_schema.py` - constants and normalizers.
- `tools/trinity_quota_guard.py` - CLI wrapper.
- `_MODEL_TRINITY/bridge/quota/config/quota_guard.config.example.json` -
  safe example config.
- `ai_chi/tests/test_trinity_quota_guard.py` - deterministic unit tests.

Runtime state under the bridge root:

```text
quota/config/quota_guard.config.json
quota/config/quota_guard.config.example.json
quota/snapshots/<agent>.latest.json
quota/events/*.jsonl
quota/downtime/YYYY-MM-DD.downtime.jsonl
quota/state/quota_guard_status.json
quota/state/downtime_state.json
quota/state/poke_state.json
```

## Commands

Run one local pass:

```powershell
python tools/trinity_quota_guard.py --bridge _MODEL_TRINITY\bridge --once
```

Print a compact table:

```powershell
python tools/trinity_quota_guard.py --bridge _MODEL_TRINITY\bridge --status
```

Run a foreground loop:

```powershell
python tools/trinity_quota_guard.py --bridge _MODEL_TRINITY\bridge --interval 60
```

The foreground loop is manual. Do not install it as a hidden service without a
separate explicit approval and service design review.

## Status Model

The guard computes one advisory status per agent:

- `READY`
- `LOW_BUDGET`
- `EXHAUSTED`
- `COOLDOWN_UNTIL_RESET`
- `RESET_PROBABLE`
- `OFFLINE`
- `UNKNOWN`

Failure keywords are normalized from short local fields only:

```text
usage_limit_hit
quota_exhausted
rate_limited
session_limit_hit
weekly_limit_hit
daily_limit_hit
token_budget_exceeded
credit_required
provider_unavailable
```

Packet `body` text is not read. If `body` is a JSON object, only short status
fields such as `reason`, `status`, `error`, `last_error`, `reset_at`, and
`limit_hit_at` are inspected.

## Reset Inference

Claude session resets may be inferred when all of these are true:

- a `session_limit_hit` event exists;
- `reset_at` is missing;
- `session_window_hours` is configured.

Codex reset timing is not guessed from a usage-limit hit. Without explicit
provider/manual reset evidence, the state reason becomes
`REQUIRE_PROVIDER_STATUS_OR_MANUAL_RESET`.

If a reset time has passed and the agent heartbeat is stale, the guard emits a
throttled metadata-only `quota_poke` packet into that agent inbox. The packet
asks for a heartbeat/status snapshot only and grants no tool, config, spending,
or execution authority.

## Router Decision

Use:

```python
from trinity_bridge.quota_guard import can_accept

decision = can_accept("claude", "SMALL")
```

The return record includes:

```json
{
  "decision": "ALLOW_FULL | ALLOW_SMALL | ALLOW_STATUS | DEFER | REROUTE | REQUIRE_HUMAN",
  "reason": "...",
  "agent": "claude",
  "status": "READY",
  "confidence": 0.7,
  "next_check_at": "..."
}
```

`STATUS_ONLY` work is allowed during cooldowns so agents can report status
without starting heavy work. Heavy work is deferred during cooldown/exhaustion.
Paid overflow still requires exact human approval.
