# Cognitive Matrix Agent Model and System Config Analysis

Generated: 2026-05-02 14:28 CEST
Host: `ViChi@<host>` (`<hostname>`)
Base path: `/home/<user>/cognitive_matrix`
Service: `cognitive-matrix.service`
Purpose: review-ready analysis of the agent model, runtime system, configuration surface, model stack, persistence, security posture, and operational risks.

## Executive Summary

The Cognitive Matrix agent is running successfully as a systemd service and the current foundation layer is loaded end to end. The Python modules compile, the JSON knowledge files validate, `/identity` exposes the formula, 12 axioms, and 15 omniversal entries, and the local Ollama model inventory is present.

The system is functionally alive but not yet hardened. The highest application risk is that the HTTP agent listens on `0.0.0.0:8888` without authentication and exposes state-changing endpoints, including `/clear`, `/audit`, `/ask`, and `/dream/run`. The highest hardware risk is current thermal throttling: the Pi reported `temp=84.2'C` and `throttled=0xf0008`, which includes active soft temperature limiting.

## Scope

Reviewed components:

```text
/home/<user>/cognitive_matrix/agent.py
/home/<user>/cognitive_matrix/audit.py
/home/<user>/cognitive_matrix/identity.py
/home/<user>/cognitive_matrix/formula.py
/home/<user>/cognitive_matrix/agents/connector.py
/home/<user>/cognitive_matrix/axioms.json
/home/<user>/cognitive_matrix/knowledge/omniversal.json
/home/<user>/cognitive_matrix/context_store.json
/etc/systemd/system/cognitive-matrix.service
HTTP endpoints on localhost:8888
Ollama model inventory on localhost:11434
```

Review mode: read-only discovery plus report creation. No service behavior was modified during this report pass.

## Architecture Summary

The system is currently organized into five layers:

```text
1. Foundation layer
   axioms.json, formula.py, identity.py, knowledge/omniversal.json

2. Audit layer
   audit.py: L3 coherence, L6 contradiction, L9 integrity, tri-state output

3. Agent loop
   agent.py: HTTP server, observe/score/act/reflect, dream cycle thread

4. Connector layer
   agents/connector.py: Ollama, Gordon, Claude, OpenAI-compatible, Groq registry

5. Runtime service layer
   cognitive-matrix.service: starts agent.py under user ViChi
```

Current design intent is coherent: the audit layer is separate from the connector layer, the identity layer loads the foundation data, and external model answers are routed through audit before they can become confirmed context.

## Live Service State

Systemd status:

```text
Loaded: loaded (/etc/systemd/system/cognitive-matrix.service; enabled; preset: enabled)
Active: active (running) since Sat 2026-05-02 11:50:21 CEST
Main PID: 2200363 (python3)
Tasks: 2
Memory: 12.6M (peak: 21.8M)
ExecStart: /usr/bin/python3 /home/<user>/cognitive_matrix/agent.py
```

Unit configuration:

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

Listening sockets:

```text
127.0.0.1:11434  Ollama API
172.17.0.1:11434 Docker bridge Ollama API
0.0.0.0:8888     Cognitive Matrix HTTP agent
```

## Endpoint Review

Endpoint checks succeeded:

```text
/status   OK
/agents   OK
/identity OK
/dream    OK
/context  OK
```

`/status` summary:

```text
status=online
confirmed=1
rejected=0
total=1
dream_pending=0
reason_model=qwen2.5:1.5b
embed_model=nomic-embed-text
```

`/agents` summary:

```text
ollama:qwen2.5:1.5b healthy=True trust=0.5 queries=0
ollama:gemma3:1b    healthy=True trust=0.5 queries=0
ollama:tinyllama    healthy=True trust=0.5 queries=0
gordon:docker       healthy=True trust=0.5 queries=0
```

`/identity` summary:

```text
identity=Omni
formula=Ω = f(A, K, T, Φ, Δ, Ξ, Λ)
axioms=12
omniversal=15
uptime=54h 21m 5s
```

`/dream` summary:

```text
pending=0
```

`/context` summary:

```text
confirmed=1
claim=The sky is blue
```

## Model and Connector Analysis

Installed Ollama models:

```text
qwen2.5:1.5b               986 MB
nomic-embed-text:latest    274 MB
tinyllama:latest           637 MB
gemma3:1b                  815 MB
```

Configured model roles:

```text
Reasoning model: qwen2.5:1.5b
Embedding model: nomic-embed-text
Fallback local agents: gemma3:1b, tinyllama:latest
Gordon connector: configured but not actually usable
```

Connector health issue:

```text
docker ai 'health check'
docker: unknown command: docker ai
Run 'docker --help' for more information
```

`GordonAgent.health_check()` checks `docker version`, not `docker ai`, so `/agents` currently reports Gordon healthy even though Gordon queries fail. This is a model registry correctness issue.

Ollama query timeout in `agents/connector.py` is currently `120` seconds. That is appropriate for RPi4-scale local models, but `/ask` can tie up the single-threaded HTTP server during long requests.

## Foundation Data Review

Foundation files validate:

```text
JSON_OK axioms.json count=12
JSON_OK context_store.json count=1
JSON_OK knowledge/omniversal.json count=15
```

`axioms.json`:

```text
-r--r--r-- ViChi:ViChi 10230 /home/<user>/cognitive_matrix/axioms.json
```

The read-only mode is correct for a first guard. It is not a hard trust boundary because the file is owned by `ViChi`, and the service also runs as `ViChi`.

`formula.py` verification:

```text
Ω = f(A, K, T, Φ, Δ, Ξ, Λ)
Φ(c) = Ξ [ L3(c) ∧ L6(c,K) ∧ L9(c) ]
[+] iff L3 ∧ L6 ∧ L9 ∧ M(c)·P(c)≠∅ ∧ Δ(c) complete
apex(Ω) = undefined
Architect: ViChi | Built: Planet Earth, The Netherlands, 2026
Axioms loaded: True
Axiom count: 12
```

`identity.py` now exposes:

```text
identity
hardware
runtime
statement
axioms
omniversal
formula
```

This makes `/identity` a full self-description and foundation export endpoint.

## Code Health

Python compile check:

```text
PY_COMPILE_OK
```

Compiled modules:

```text
audit.py
agent.py
identity.py
formula.py
agents/connector.py
```

Code sizes:

```text
agent.py             375 lines
audit.py             420 lines
identity.py          477 lines
formula.py           411 lines
agents/connector.py  468 lines
```

These files are still small enough to review manually, but they are approaching the point where test files and explicit interfaces would be useful.

## Runtime Data and Persistence

Main persistent stores:

```text
context_store.json       confirmed/rejected context with embeddings
dream_layer.log          dream recapitulation log
agent.log                service/application log
.omni_start_time         persisted Omni uptime seed
axioms.json              read-only foundation
knowledge/omniversal.json omniversal knowledge base
```

Current context store:

```text
entries=1
size=20802 bytes
```

The current context store size is already about `20 KB` for one confirmed claim because the full embedding vector is stored inline. This will scale poorly as confirmed knowledge grows.

## Logging Review

`agent.log` size:

```text
5473107 bytes
```

Recent log pattern:

```text
[DREAM] Cycle: nothing pending
```

The dream layer logs every 60 seconds even when idle. `agent.py` also writes directly to `agent.log` and prints the same lines, while systemd appends stdout/stderr to the same file. This explains duplicated and sometimes concatenated log lines.

## Hardware and OS Runtime

Disk and memory:

```text
/dev/sda1: 469G total, 54G used, 391G available, 13% used
RAM: 7.6Gi total, 5.4Gi available
Swap: 2.0Gi total, 3.5Mi used
```

Thermal and throttling:

```text
throttled=0xf0008
temp=84.2'C
```

Interpretation:

```text
0x8     current soft temperature limit active
0xf0000 historical under-voltage / frequency cap / throttling / soft-temp events occurred
0xf0008 current soft-temp plus historical throttle flags
```

This is the most urgent hardware issue. The software stack is lightweight, but the Pi is hot enough to throttle.

## Security Review

Secret scan result:

```text
No raw secret values were found in active source/config files.
Matches are code references to env var names and authorization header construction.
```

Relevant code references:

```text
ANTHROPIC_API_KEY
OPENAI_API_KEY
GROQ_API_KEY
Authorization: Bearer {self.api_key}
x-api-key: self.api_key
```

Primary security issue:

```text
agent.py binds HTTPServer to 0.0.0.0:8888
No auth is enforced by the app
State-changing endpoints are exposed
```

Impact:

```text
POST /clear      can delete context and dream queue
POST /audit      can write confirmed context entries
POST /ask        can trigger model work and resource usage
POST /dream/run  can mutate dream queue state
GET /identity    exports full foundation and runtime identity
```

## Findings

### P0: Active thermal throttling on Pi

The Pi reported `temp=84.2'C` and `throttled=0xf0008`. This includes current soft temperature limiting. Sustained operation at this temperature can reduce model performance and destabilize long requests.

Recommended action: improve cooling or reduce model load before expanding `/ask` usage. Re-check `vcgencmd measure_temp` and `vcgencmd get_throttled` after cooling changes.

### P1: HTTP API is LAN-exposed without authentication

The agent listens on `0.0.0.0:8888` and exposes state-changing endpoints. This is acceptable only on a fully trusted lab LAN. It is not migration-ready infrastructure yet.

Recommended action: add bearer token auth for all POST endpoints and optionally bind the service to `127.0.0.1` behind nginx or another controlled reverse proxy.

### P1: Gordon connector health is inaccurate

`/agents` reports `gordon:docker` healthy because Docker is installed. Actual Gordon query path uses `docker ai`, which is not available.

Recommended action: change `GordonAgent.health_check()` to validate `docker ai` specifically, or disable Gordon registration until the CLI exists.

### P2: Single-threaded HTTP server can block during model calls

`HTTPServer` handles one request at a time. `/ask` can wait up to 120 seconds for Ollama. During that time, other requests may wait behind it.

Recommended action: switch to `ThreadingHTTPServer` or queue long `/ask` jobs. Keep `/status` and `/identity` responsive under load.

### P2: Logging is duplicated and unbounded

Application log writes and systemd stdout append target the same file. Idle dream cycles produce one log line per minute.

Recommended action: use one logging path, add log rotation, and suppress or aggregate idle dream-cycle logs.

### P2: Foundation immutability is advisory

`axioms.json` is mode `444`, but service and file owner are both `ViChi`. A compromised service process could chmod it.

Recommended action: make `axioms.json` root-owned and read-only, or apply immutable attributes if operationally acceptable.

### P2: Context store embeds full vectors inline

One entry is already about `20 KB`. Embedding vectors in JSON are simple but inefficient.

Recommended action: split embeddings into a separate vector/embedding store and keep `context_store.json` as metadata plus audit trail.

### P3: Backup artifacts are mixed into runtime directory

Backup files exist in the live runtime directory, including malformed timestamp names from earlier shell quoting issues.

Recommended action: move backups into `/home/<user>/cognitive_matrix/backups/` after review.

### P3: systemd hardening is minimal

The service has no hardening directives. This is normal during prototyping but weak for LAN exposure.

Recommended action: after endpoint auth is implemented, add hardening options such as `NoNewPrivileges=true`, `PrivateTmp=true`, restricted write paths, and limited filesystem access.

## Recommended Hardening Plan

1. Cool the Pi and clear thermal throttling before heavier model use.
2. Add authentication to POST endpoints.
3. Fix Gordon health check or disable Gordon until `docker ai` exists.
4. Convert `HTTPServer` to `ThreadingHTTPServer` or queue `/ask` jobs.
5. Normalize logging and add rotation.
6. Move `axioms.json` ownership to root for a real read-only boundary.
7. Split embeddings from `context_store.json` before knowledge growth.
8. Move backup files into a dedicated backup directory.
9. Add focused tests for `/audit`, `/clear`, `/identity`, and connector health.
10. Add a cheap `/healthz` endpoint that does not call every agent health check.

## Review Checklist

Use this list for the next implementation pass:

```text
[ ] Decide LAN exposure model: localhost-only or authenticated LAN API
[ ] Add API auth token handling and masked config
[ ] Protect /clear, /audit, /ask, /dream/run
[ ] Fix Gordon health check
[ ] Add ThreadingHTTPServer or background job queue
[ ] Add log rotation or journald-only logging
[ ] Reduce idle dream logs
[ ] Make axioms root-owned or immutable
[ ] Move backups to backups/
[ ] Create smoke tests for core endpoints
[ ] Re-check temp and throttling after cooling
```

## Commands Used

```text
sudo systemctl status cognitive-matrix --no-pager
sudo systemctl cat cognitive-matrix
ss -ltnp | grep -E '(:8888|:11434)'
ollama list
python3 -m py_compile audit.py agent.py identity.py formula.py agents/connector.py
find /home/<user>/cognitive_matrix -maxdepth 3 -printf ...
curl http://localhost:8888/status
curl http://localhost:8888/agents
curl http://localhost:8888/identity
curl http://localhost:8888/dream
curl http://localhost:8888/context
python3 -m json.tool axioms.json
python3 -m json.tool context_store.json
python3 -m json.tool knowledge/omniversal.json
df -h /home/<user>/cognitive_matrix
free -h
vcgencmd get_throttled
vcgencmd measure_temp
docker ai 'health check'
tail -40 agent.log
```