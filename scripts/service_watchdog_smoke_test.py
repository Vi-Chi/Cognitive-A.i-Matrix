"""Smoke-test scripts/service-watchdog.ts without external services.

The test starts one temporary localhost HTTP endpoint and points one TCP check at
a closed localhost port. Expected result: one ONLINE service, one OFFLINE
service, one fallback ProposalRecord, and a nonzero watchdog exit code.
"""

from __future__ import annotations

import contextlib
import http.server
import json
import socket
import subprocess
import tempfile
import threading
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WATCHDOG = ROOT / "scripts" / "service-watchdog.ts"


class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path != "/status":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, *_args: object) -> None:
        return


def free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> int:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    online_port = int(server.server_address[1])
    closed_port = free_port()
    config = {
        "services": [
            {
                "id": "fixture_http",
                "name": "Fixture HTTP",
                "kind": "http",
                "url": f"http://127.0.0.1:{online_port}/status",
                "expectedStatus": [200],
                "timeoutMs": 800,
                "retries": 0,
                "critical": False,
                "tags": ["fixture"],
            },
            {
                "id": "fixture_tcp_closed",
                "name": "Fixture Closed TCP",
                "kind": "tcp",
                "host": "127.0.0.1",
                "port": closed_port,
                "timeoutMs": 500,
                "retries": 0,
                "critical": False,
                "tags": ["fixture"],
                "fallback": [
                    {
                        "id": "fixture_manual_review",
                        "label": "Manual Review",
                        "reason": "Closed fixture port should create a proposal.",
                        "mode": "manual",
                        "requiresApproval": True,
                    }
                ],
            },
        ]
    }

    try:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "service-registry.fixture.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = subprocess.run(
                ["node", str(WATCHDOG), "--config", str(config_path), "--full"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        if result.returncode != 1:
            raise AssertionError(f"expected exit 1, got {result.returncode}: {result.stderr}")
        report = json.loads(result.stdout)
        summary = report["summary"]
        assert summary["total"] == 2, summary
        assert summary["online"] == 1, summary
        assert summary["offline"] == 1, summary
        assert summary["criticalOffline"] == 0, summary
        assert summary["proposals"] == 1, summary
        proposal_ids = [proposal["proposal_id"] for proposal in report["proposals"]]
        assert len(proposal_ids) == len(set(proposal_ids)), proposal_ids
        print("service_watchdog_smoke_test: OK")
        print(report["tokenBudget"]["compactSummary"])
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
