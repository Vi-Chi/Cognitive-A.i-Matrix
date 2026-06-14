# Tool Scope Policy

## Default

Read-only by default. Proposal-only for action-like outputs.

## Allowed Early Tools

- project file read/search;
- git status, diff, and log when a Git repository exists;
- documentation generation;
- static code analysis;
- test/build/lint commands that do not mutate tracked files;
- allowlisted Trinity executor tasks documented in
  `_MODEL_TRINITY/bridge/EXECUTOR_POLICY.md`;
- pre-route Trinity arbitration documented in
  `_MODEL_TRINITY/bridge/ARBITRATION_POLICY.md`;
- foreground Trinity+DAN cycles documented in
  `_MODEL_TRINITY/bridge/CYCLE_POLICY.md`;
- mock data editing within approved patches;
- local provider placeholder editing.

## Restricted Tools

Require explicit approval or a task-specific instruction:

- dependency installation;
- package updates;
- file moves or deletions;
- branch resets;
- generated code replacement;
- network access;
- backend server exposure changes;
- service connector writes;
- MCP/plugin installation or persistent configuration.

## Forbidden By Default

- unrestricted shell execution;
- free-form prompt text interpreted as shell;
- hidden always-on Trinity or DAN loops;
- bypassing arbitration quarantine folders to auto-route approval-gated work;
- Docker control;
- filesystem writes outside the repository;
- secret reading;
- credential scanning that prints secret values;
- live hardware control;
- navigation or actuator endpoints;
- external data exfiltration;
- hidden background agents.

## Cloud Policy

Cloud tools may be used for development assistance only when explicitly approved.
They must not become required runtime dependencies.
