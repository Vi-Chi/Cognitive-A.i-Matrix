"""
Cognitive Matrix - Agent Loop v1
Observe → Parse → Link → Score → Act → Reflect

Runs an HTTP server on port 8888.
Anything can POST a claim to it.
The matrix audits it and returns a result.
Dream layer runs on a background cycle.
No external dependencies — stdlib only.
"""

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 ViChi - https://github.com/ViChi

import json
import time
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle each request in a separate thread.
    Prevents long /ask LLM calls from blocking /status checks."""
    daemon_threads = True

# Import the audit engine
import sys
sys.path.insert(0, str(Path(__file__).parent))
from audit import TriStateAuditor, DreamLayer, load_context, save_context
from agents.connector import build_default_registry, OllamaAgent

BASE_DIR = Path(__file__).parent
AGENT_LOG = BASE_DIR / "agent.log"

PORT = 8888
DREAM_CYCLE_SECONDS = 60  # recapitulation every 60 seconds


# ─── Logging ──────────────────────────────────────────────────────────────────

def log(msg: str):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}", flush=True)


def load_api_key() -> str:
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("OMNI_API_KEY="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("OMNI_API_KEY", "")


OMNI_API_KEY = load_api_key()


# ─── Global State ─────────────────────────────────────────────────────────────

auditor = TriStateAuditor()
dream = DreamLayer()
registry = build_default_registry()


# ─── Dream Cycle Thread ───────────────────────────────────────────────────────

def dream_cycle():
    """
    Background recapitulation loop.
    Runs every DREAM_CYCLE_SECONDS.
    Re-audits suspended claims.
    This is the Reflect step of the agent loop.
    """
    while True:
        time.sleep(DREAM_CYCLE_SECONDS)
        pending = len(dream.queue)
        if pending > 0:
            log(f"[DREAM] Starting recapitulation cycle — {pending} pending")
            dream.process_cycle()
            log(f"[DREAM] Cycle complete — {len(dream.queue)} still pending")
        else:
            log("[DREAM] Cycle: nothing pending")


# ─── HTTP Request Handler ─────────────────────────────────────────────────────

class MatrixHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Suppress default HTTP logs — we use our own
        pass

    def send_json(self, code: int, data: dict):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def is_authorized(self) -> bool:
        if not OMNI_API_KEY:
            return True  # no key set = open (dev mode)
        auth = self.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "").strip()
        return token == OMNI_API_KEY

    def deny(self):
        self.send_json(401, {
            "error": "Unauthorized",
            "hint": "Include header: Authorization: Bearer <key>"
        })

    def do_GET(self):
        if not self.is_authorized():
            self.deny()
            return

        """
        GET /status  — agent health and stats
        GET /context — all confirmed claims
        GET /dream   — current dream layer queue
        """
        if self.path == "/status":
            ctx = load_context()
            confirmed = [e for e in ctx if e.get("state") == "+"]
            rejected = [e for e in ctx if e.get("state") == "-"]
            self.send_json(200, {
                "status": "online",
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "context": {
                    "confirmed": len(confirmed),
                    "rejected": len(rejected),
                    "total": len(ctx)
                },
                "dream_layer": {
                    "pending": len(dream.queue)
                },
                "models": {
                    "reason": "qwen2.5:1.5b",
                    "embed": "nomic-embed-text"
                }
            })

        elif self.path == "/context":
            ctx = load_context()
            confirmed = [
                {
                    "claim": e["claim"],
                    "timestamp": time.strftime(
                        '%Y-%m-%d %H:%M:%S',
                        time.localtime(e["timestamp"])
                    )
                }
                for e in ctx if e.get("state") == "+"
            ]
            self.send_json(200, {"confirmed": confirmed})

        elif self.path == "/dream":
            self.send_json(200, {
                "pending": len(dream.queue),
                "claims": [
                    {
                        "claim": item["claim"],
                        "cycles": item["cycles"],
                        "age_seconds": int(time.time() - item["received"])
                    }
                    for item in dream.queue
                ]
            })

        elif self.path == "/agents":
            self.send_json(200, {
                "agents": registry.status_all()
            })

        elif self.path == "/identity":
            from identity import get_full_identity
            ctx = load_context()
            report = get_full_identity(
                context_store=ctx,
                dream_queue=dream.queue,
                registry=registry
            )
            self.send_json(200, report)

        else:
            self.send_json(404, {"error": "Unknown endpoint"})

    def do_POST(self):
        if not self.is_authorized():
            self.deny()
            return

        """
        POST /audit  — submit a claim for auditing
        POST /clear  — clear the context store
        POST /dream/run — trigger a dream cycle manually
        Body for /audit: {"claim": "your claim here"}
        """
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        if self.path == "/audit":
            try:
                body = json.loads(raw_body)
                claim = body.get("claim", "").strip()
                past = body.get("past", "").strip()
                future = body.get("future", "").strip()
            except Exception:
                self.send_json(400, {"error": "Invalid JSON body"})
                return

            if not claim:
                self.send_json(400, {"error": "No claim provided"})
                return

            log(f"[OBSERVE] Received: {claim[:80]}")

            # ── The core agent loop ──────────────────────────────
            # Step 1: Observe  — received above
            # Step 2: Parse    — extract the claim string
            # Step 3: Link     — Lens 6 checks against context
            # Step 4: Score    — audit() runs all 3 lenses
            # Step 5: Act      — route based on state
            # Step 6: Reflect  — dream layer handles [=]
            # ────────────────────────────────────────────────────

            result = auditor.audit(claim, past=past, future=future)
            state = result["state"]

            log(
                f"[SCORE] {state} | "
                f"{result['confidence']:.0%} | "
                f"{result['reason'][:60]}"
            )

            # Act: route the result
            if state == "=":
                dream.receive(claim)
                log(f"[ACT] Routed to Dream Layer: {claim[:60]}")
            elif state == "+":
                log(f"[ACT] Confirmed and stored: {claim[:60]}")
            else:
                log(f"[ACT] Rejected: {claim[:60]}")

            self.send_json(200, {
                "claim": claim,
                "state": state,
                "confidence": result["confidence"],
                "reason": result["reason"],
                "route": result["route"]
            })

        elif self.path == "/clear":
            save_context([])
            auditor.refresh()
            cleared_dream = len(dream.queue)
            dream.queue.clear()
            log(f"[SYSTEM] Context store cleared by request")
            log(f"[SYSTEM] Dream queue cleared — {cleared_dream} claims removed")
            self.send_json(200, {
                "status": "cleared",
                "context": "emptied",
                "dream_queue_removed": cleared_dream
            })

        elif self.path == "/dream/run":
            pending_before = len(dream.queue)
            dream.process_cycle()
            pending_after = len(dream.queue)
            resolved = pending_before - pending_after
            log(f"[DREAM] Manual cycle: {resolved} resolved, "
                f"{pending_after} still pending")
            self.send_json(200, {
                "resolved": resolved,
                "still_pending": pending_after
            })

        elif self.path == "/ask":
            try:
                body = json.loads(raw_body)
                question = body.get("question", "").strip()
                agent_name = body.get("agent", None)
                from identity import get_identity_statement
                ctx = load_context()
                default_system = get_identity_statement(
                    context_store=ctx,
                    dream_queue=dream.queue,
                    registry=registry
                )
                system_prompt = body.get("system", default_system)
            except Exception:
                self.send_json(400, {"error": "Invalid JSON"})
                return

            if not question:
                self.send_json(400, {"error": "No question provided"})
                return

            # Select agent
            if agent_name:
                agent = registry.get(agent_name)
                if not agent:
                    self.send_json(404, {
                        "error": f"Agent '{agent_name}' not found"
                    })
                    return
            else:
                # Auto-select: highest trust healthy agent
                agent = registry.best_available()
                if not agent:
                    self.send_json(503, {
                        "error": "No healthy agents available"
                    })
                    return

            log(f"[ASK] Question: {question[:80]}")
            log(f"[ASK] Routing to: {agent.name}")

            # Query the agent
            result = agent.query(question, system=system_prompt)

            if result["error"]:
                log(f"[ASK] Agent error: {result['error']}")
                self.send_json(502, {
                    "error": f"Agent error: {result['error']}"
                })
                return

            response_text = result["response"]
            log(f"[ASK] Response ({result['latency_s']}s): "
                f"{response_text[:80]}")

            # Audit the response before surfacing
            # The agent's answer must earn its state
            audit_result = auditor.audit(response_text)
            audit_state = audit_result["state"]

            # Record result against agent trust score
            agent.record_audit_result(audit_state)

            log(f"[AUDIT] {agent.name} response: "
                f"{audit_state} | {audit_result['reason'][:60]}")

            # Route based on audit state
            if audit_state == "=":
                dream.receive(response_text)
                log(f"[ACT] Agent response suspended to dream layer")
            elif audit_state == "+":
                log(f"[ACT] Agent response confirmed and stored")
            else:
                log(f"[ACT] Agent response rejected")

            self.send_json(200, {
                "question": question,
                "agent": agent.name,
                "agent_trust": agent.trust_score,
                "response": response_text,
                "latency_s": result["latency_s"],
                "audit": {
                    "state": audit_state,
                    "confidence": audit_result["confidence"],
                    "reason": audit_result["reason"],
                    "route": audit_result["route"]
                }
            })

        else:
            self.send_json(404, {"error": "Unknown endpoint"})


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log("=== Cognitive Matrix Agent v1 starting ===")
    # Record service start time for uptime tracking
    _start_file = BASE_DIR / ".omni_start_time"
    if not _start_file.exists():
        _start_file.write_text(str(time.time()))
        log("[OMNI] Start time recorded")
    else:
        log("[OMNI] Resuming — start time preserved")
    log(f"Listening on port {PORT}")
    log(f"Dream cycle: every {DREAM_CYCLE_SECONDS}s")

    # Start dream cycle in background
    dream_thread = threading.Thread(
        target=dream_cycle,
        daemon=True,
        name="DreamLayer"
    )
    dream_thread.start()
    log("[DREAM] Background recapitulation thread started")

    # Start HTTP server
    server = ThreadedHTTPServer(("127.0.0.1", PORT), MatrixHandler)
    log(f"[AGENT] Online at http://10.0.0.1:{PORT}")
    log("[AGENT] Endpoints:")
    log("  GET  /status     — health and stats")
    log("  GET  /context    — confirmed claims")
    log("  GET  /dream      — suspended claims")
    log("  POST /audit      — submit claim")
    log("  POST /clear      — clear context")
    log("  POST /dream/run  — trigger recapitulation")
    log("")
    log("Ready. Waiting for input.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("[AGENT] Shutting down.")
        server.server_close()
