# Cognitive Matrix Config Analysis Report

Generated: 2026-05-02 14:24 CEST
Host: `ViChi@<host>` (`<hostname>`)
Scope: `/home/<user>/cognitive_matrix`, `cognitive-matrix.service`, HTTP agent on port `8888`, local Ollama on port `11434`

## Executive Summary

The Cognitive Matrix service is online and the current foundation files are structurally valid. Python modules compile, JSON stores parse, the systemd service is enabled and running, Ollama models are installed, and the `/identity` surface loads the formula, 12 axioms, and 15 omniversal entries.

The main risks are operational hardening rather than functional breakage. The HTTP agent listens on all interfaces without authentication, including a destructive `/clear` endpoint. Logging is duplicated into the same file through both application-level writes and systemd stdout append. The read-only axiom file is mode `444`, but it is still owned by the same user that runs the service, so the protection is advisory rather than a true integrity boundary.

## Live Status

Service status:

```text
● cognitive-matrix.service - Cognitive Matrix Agent
Loaded: loaded (/etc/systemd/system/cognitive-matrix.service; enabled; preset: enabled)
Active: active (running) since Sat 2026-05-02 11:50:21 CEST
Main PID: 2200363 (python3)
Memory: 12.6M (peak: 21.8M)
ExecStart: /usr/bin/python3 /home/<user>/cognitive_matrix/agent.py
```

Listening ports:

```text
127.0.0.1:11434  Ollama API
172.17.0.1:11434 Docker bridge Ollama API
0.0.0.0:8888     Cognitive Matrix HTTP agent
```

Endpoint checks:

```text
/status  OK: online, confirmed=1, rejected=0, total=1, dream pending=0
/agents  OK: 4 registered agents
/dream   OK: pending=0
/context OK: confirmed=1
```

Installed Ollama models:

```text
qwen2.5:1.5b
nomic-embed-text:latest
tinyllama:latest
gemma3:1b
```

## File Inventory

Important files:

```text
-r--r--r-- /home/<user>/cognitive_matrix/axioms.json
-rw-rw-r-- /home/<user>/cognitive_matrix/formula.py
-rw-rw-r-- /home/<user>/cognitive_matrix/identity.py
-rw-rw-r-- /home/<user>/cognitive_matrix/audit.py
-rw-rw-r-- /home/<user>/cognitive_matrix/agent.py
-rw-rw-r-- /home/<user>/cognitive_matrix/agents/connector.py
-rw-rw-r-- /home/<user>/cognitive_matrix/knowledge/omniversal.json
-rw-rw-r-- /home/<user>/cognitive_matrix/context_store.json
-rw-r--r-- /home/<user>/cognitive_matrix/agent.log
```

Validation results:

```text
PY_COMPILE_OK: audit.py, agent.py, identity.py, formula.py, agents/connector.py
JSON_OK axioms.json axioms=12
JSON_OK context_store.json entries=1
JSON_OK knowledge/omniversal.json prime_connections=15
```

Current code sizes:

```text
agent.py 375 lines
audit.py 420 lines
identity.py 477 lines
formula.py 411 lines
agents/connector.py 468 lines
```

## Systemd Configuration

Unit file: `/etc/systemd/system/cognitive-matrix.service`

```ini
[Service]
Type=simple
User=ViChi
WorkingDirectory=/home/<user>/cognitive_matrix
ExecStart=/usr/bin/python3 /home/<user>/cognitive_matrix/agent.py
Restart=on-failure
RestartSec=5
StandardOutput=append:/home/<user>/cognitive_matrix/agent.log
StandardError=append:/home/<user>/cognitive_matrix/agent.log
```

The service is enabled and starts correctly. It runs as `ViChi`, which matches the project ownership and avoids the earlier log permission failure.

## Configuration Surface

### `agent.py`

Role: HTTP interface and autonomous loop.

Key configuration:

```text
PORT = 8888
DREAM_CYCLE_SECONDS = 60
HTTPServer(("0.0.0.0", PORT), MatrixHandler)
```

Exposed endpoints:

```text
GET  /status
GET  /context
GET  /dream
GET  /agents
GET  /identity
POST /audit
POST /clear
POST /dream/run
POST /ask
```

Important behavior:

- `/clear` empties both `context_store.json` and the in-memory dream queue.
- Dream cycle logs every 60 seconds even when no claims are pending.
- Application writes directly to `agent.log` and also prints to stdout.

### `audit.py`

Role: tri-state audit engine.

Important behavior:

- `add_to_context()` stores `claim`, `state`, `timestamp`, `embedding`, and temporal `time.past/present/future`.
- `TriStateAuditor.audit(claim, **kwargs)` forwards `past` and `future` into confirmed context entries.
- Confirmed entries include full embedding vectors, so `context_store.json` will grow quickly as entries accumulate.

### `identity.py`

Role: identity, hardware introspection, runtime state, foundation loaders.

Current behavior:

- Loads `axioms.json` through `load_axioms()`.
- Loads `knowledge/omniversal.json` through `load_omniversal()`.
- `/identity` now returns `identity`, `hardware`, `runtime`, `statement`, `axioms`, `omniversal`, and `formula`.
- Uptime is persisted through `.omni_start_time`.

### `formula.py`

Role: formal declaration of Omega structure.

Current verification:

```text
Ω = f(A, K, T, Φ, Δ, Ξ, Λ)
Axioms loaded: True
Axiom count: 12
Architect: ViChi | Built: Planet Earth, The Netherlands, 2026
```

### `agents/connector.py`

Role: multi-agent connector registry.

Registered local agents:

```text
ollama:qwen2.5:1.5b
ollama:gemma3:1b
ollama:tinyllama:latest
gordon:docker
```

Important mismatch:

- Docker is installed and `docker version` works.
- `docker ai` is not installed: `docker: unknown command: docker ai`.
- `GordonAgent.health_check()` only checks `docker version`, so `/agents` reports `gordon:docker` healthy even though Gordon queries cannot work.

## Resource State

Disk and memory:

```text
Filesystem /dev/sda1: 469G total, 54G used, 391G available, 13% used
RAM: 7.6Gi total, 5.8Gi available
Swap: 2.0Gi total, 3.5Mi used
```

Thermal/throttling:

```text
temp=68.6'C
throttled=0xf0000
```

The Pi has enough disk and memory. Temperature is high but not immediately fatal. The throttling flag indicates historical or active power/thermal throttling risk and should remain on the infrastructure risk list.

## Security Review

Secret scan:

```text
No literal secret values were found in the scanned project files.
Matches were code references to env var names and authorization headers in connector.py.
```

Relevant references:

```text
ANTHROPIC_API_KEY
OPENAI_API_KEY
GROQ_API_KEY
Authorization: Bearer {self.api_key}
x-api-key: self.api_key
```

Primary exposure:

- The agent binds to `0.0.0.0:8888`, so it is reachable from the LAN.
- There is no authentication, authorization, or origin restriction in `agent.py`.
- `POST /clear` can erase context and dream queue remotely.
- `POST /ask` can trigger local model work and may run for up to 120 seconds per Ollama request.

Axioms integrity:

- `axioms.json` is mode `444`, which prevents normal writes.
- It is owned by `ViChi`, and the service also runs as `ViChi`.
- Because the owner can chmod the file, mode `444` is not a hard trust boundary. It is a policy marker unless ownership is moved away from the runtime user or immutable attributes are applied.

## Findings

### P1: Unauthenticated LAN write/destructive API

`agent.py` exposes the HTTP server on `0.0.0.0:8888`. The `/clear` endpoint clears persisted context and the dream queue without authentication. Any LAN client that can reach the port can modify or destroy runtime knowledge state.

Recommended fix: add a simple bearer token or bind to `127.0.0.1` and expose only through a controlled reverse proxy. At minimum, protect `/clear`, `/dream/run`, `/audit`, and `/ask`.

### P1: Gordon health check is incorrect

`/agents` reports `gordon:docker` as healthy because `GordonAgent.health_check()` checks `docker version`. Actual query path uses `docker ai`, which is unavailable on this Pi.

Evidence:

```text
docker version: 29.4.1
docker ai: docker: unknown command: docker ai
```

Recommended fix: change Gordon health check to test `docker ai --help` or a harmless `docker ai` probe, and mark the agent unhealthy when the subcommand is missing.

### P2: Log duplication and unbounded log growth

`agent.py` writes to `agent.log` directly and also prints the same line. systemd appends stdout and stderr to the same file. This creates duplicate log entries and occasional concatenated lines. The dream cycle also logs every minute even when idle.

Evidence: `agent.log` is already about `5.4 MB` and contains repeated `[DREAM] Cycle: nothing pending` lines.

Recommended fix: choose one logging path. Prefer stdout to journald or a single rotating file handler, not both. Suppress idle dream logs or reduce them to periodic summaries.

### P2: Axioms are read-only by convention, not by hard isolation

`axioms.json` is correctly mode `444`, but it is owned by the same user that runs the service. The runtime user could chmod and edit it if a code path or compromised process did so.

Recommended fix: make `axioms.json` root-owned with mode `444`, or apply immutable protection if the filesystem supports it and operational workflow allows it.

### P2: Context store will grow quickly

Each confirmed claim stores a full embedding vector directly in `context_store.json`. With one entry, the store is already about `20 KB`. This is acceptable for a prototype but will become inefficient as confirmed knowledge grows.

Recommended fix: split embeddings into a separate store or compress/index them separately. Keep `context_store.json` as metadata and audit trail.

### P3: Backup files have drift/noise

There are multiple backup files in the runtime directory, including malformed names from earlier shell quoting issues:

```text
identity.py.bak_20260430_
audit.py.bak_20260430_
audit.py.bak_20260430_1802
formula.py.bak_20260502_1148
identity.py.bak_20260502_1148
```

Recommended fix: move backups into `/home/<user>/cognitive_matrix/backups/` with consistent timestamp names. Do not delete until reviewed.

### P3: systemd hardening is minimal

The service unit has no hardening options such as `NoNewPrivileges`, `ProtectSystem`, `PrivateTmp`, or restricted write paths. This is acceptable for early development but weak for a LAN-exposed service.

Recommended fix: after API auth is added, harden the service unit with explicit writable paths and privilege restrictions.

## Recommended Next Steps

1. Add authentication to write/action endpoints.
2. Fix Gordon health check to reflect `docker ai` availability.
3. Normalize logging to one path and add rotation.
4. Move or harden immutable foundation files (`axioms.json`) away from runtime write authority.
5. Move backup artifacts into a dedicated backup directory.
6. Plan a storage split for embeddings before context grows beyond prototype scale.
7. Add a `/healthz` endpoint that does not trigger expensive agent health checks.

## Review Commands Used

```text
find /home/<user>/cognitive_matrix -maxdepth 3 -printf ...
sudo systemctl status cognitive-matrix --no-pager
sudo systemctl cat cognitive-matrix
python3 -m py_compile audit.py agent.py identity.py formula.py agents/connector.py
python3 -m json.tool axioms.json
python3 -m json.tool context_store.json
python3 -m json.tool knowledge/omniversal.json
ss -ltnp | grep -E '(:8888|:11434)'
curl http://localhost:8888/status
curl http://localhost:8888/agents
curl http://localhost:8888/dream
curl http://localhost:8888/context
ollama list
docker ai 'health check'
df -h /home/<user>/cognitive_matrix
free -h
vcgencmd get_throttled
vcgencmd measure_temp
```