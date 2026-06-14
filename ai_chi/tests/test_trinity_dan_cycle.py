import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CYCLE_PATH = ROOT / "scripts" / "trinity_dan_cycle.py"


spec = importlib.util.spec_from_file_location("trinity_dan_cycle", CYCLE_PATH)
trinity_dan_cycle = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = trinity_dan_cycle
spec.loader.exec_module(trinity_dan_cycle)


class TrinityDanCycleTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name) / "bridge"
        self.config_path = self.root / "trinity-bridge.config.json"
        self.config = trinity_dan_cycle.trinity_bridge.ensure_bridge(self.root, self.config_path)
        trinity_dan_cycle.trinity_executor.ensure_executor(self.root)

    def read_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def post_execution_request(self):
        packet = {
            "schema": trinity_dan_cycle.trinity_bridge.SCHEMA,
            "handoff_id": "cycle_exec_request",
            "from": "claude",
            "to": ["codex"],
            "kind": "execution_request",
            "priority": "LOW",
            "objective": "Run bridge status",
            "summary": "Cycle runner should process this.",
            "body": "Structured execution only.",
            "execution": {
                "schema": trinity_dan_cycle.trinity_executor.REQUEST_SCHEMA,
                "task_id": "bridge_status",
                "args": {},
            },
        }
        path = self.root / "outbox" / "claude" / "cycle_exec_request.json"
        trinity_dan_cycle.trinity_bridge.atomic_write_json(path, packet)
        return path

    def post_unknown_execution_request(self):
        packet = {
            "schema": trinity_dan_cycle.trinity_bridge.SCHEMA,
            "handoff_id": "cycle_unknown_exec_request",
            "from": "claude",
            "to": ["codex"],
            "kind": "execution_request",
            "priority": "LOW",
            "objective": "Run unknown task",
            "summary": "ALIVE liveness must not authorize this.",
            "body": "Structured execution only.",
            "execution": {
                "schema": trinity_dan_cycle.trinity_executor.REQUEST_SCHEMA,
                "task_id": "not_allowlisted",
                "args": {},
            },
        }
        path = self.root / "inbox" / "codex" / "cycle_unknown_exec_request.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        trinity_dan_cycle.trinity_bridge.atomic_write_json(path, packet)
        return path

    def write_health_summary(self, *, created_at=None, statuses=None):
        current = created_at or datetime.now(timezone.utc).replace(microsecond=0)
        statuses = statuses or {"codex": "ALIVE", "claude": "ALIVE", "antigravity": "ALIVE"}
        agents = {}
        queue_only_for = []
        compact_for = []
        send_new_work_to = []
        for agent, status in statuses.items():
            token_weight = 1.0 if status == "ALIVE" else 0.25
            agents[agent] = {
                "status": status,
                "last_seen_utc": current.isoformat().replace("+00:00", "Z"),
                "seconds_since_seen": 0,
                "token_automation_weight": token_weight,
                "lease_expires_utc": (current + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
                "mode": "test",
            }
            if status == "ALIVE":
                send_new_work_to.append(agent)
            else:
                queue_only_for.append(agent)
                compact_for.append(agent)
        summary = {
            "schema_version": "digivichi.trinity.health.summary.v0",
            "created_at_utc": current.isoformat().replace("+00:00", "Z"),
            "overall_status": "ALIVE" if all(status == "ALIVE" for status in statuses.values()) else "DEGRADED",
            "thresholds": {
                "alive_window_seconds": 300,
                "stale_after_seconds": 900,
                "down_after_seconds": 1800,
                "long_down_after_seconds": 7200,
                "clock_skew_tolerance_seconds": 60,
            },
            "agents": agents,
            "routing_recommendation": {
                "send_new_work_to": send_new_work_to,
                "queue_only_for": queue_only_for,
                "compact_summaries_for": compact_for,
                "avoid_repeated_pokes_before_utc": {},
            },
            "authority_boundary": {
                "capabilities_are_advisory": True,
                "liveness_gates_volume_not_authority": True,
                "provider_calls": False,
                "secret_reads": False,
                "app_config_mutation": False,
                "network_listener_start": False,
                "service_writes": False,
            },
        }
        trinity_dan_cycle.trinity_bridge.atomic_write_json(self.root / "health" / "health_summary.json", summary)
        return summary

    def test_cycle_routes_and_executes_request(self):
        source = self.post_execution_request()

        cycle = trinity_dan_cycle.run_cycle(self.root, self.config, repo_root=ROOT, check_mode="none")

        self.assertEqual(cycle["status"], "SUCCEEDED")
        self.assertFalse(source.exists())
        self.assertEqual(cycle["route_summary"], {"routed": 1})
        self.assertEqual(cycle["executor_summary"], {"executed": 1})
        self.assertEqual(cycle["failed_checks"], 0)
        self.assertTrue((self.root / "state" / "latest-cycle.json").exists())
        self.assertTrue((self.root / "ledger" / "cycle-ledger.jsonl").exists())
        self.assertEqual(len(list((self.root / "executed" / "codex").glob("*.json"))), 1)
        self.assertEqual(len(list((self.root / "inbox" / "claude").glob("*execution_result*.json"))), 1)
        self.assertFalse(cycle["liveness_routing"]["authority_boundary"]["alive_grants_authority"])
        self.assertTrue(cycle["safety"]["liveness_gates_volume_not_authority"])

    def test_dry_run_does_not_move_or_write_cycle_state(self):
        source = self.post_execution_request()

        cycle = trinity_dan_cycle.run_cycle(
            self.root,
            self.config,
            repo_root=ROOT,
            check_mode="quick",
            dry_run=True,
        )

        self.assertEqual(cycle["status"], "DRY_RUN")
        self.assertTrue(source.exists())
        self.assertEqual(cycle["route_summary"], {"would_route": 1})
        self.assertEqual(cycle["executor_summary"], {})
        self.assertEqual(cycle["checks"][0]["status"], "SKIPPED")
        self.assertFalse((self.root / "state" / "latest-cycle.json").exists())
        self.assertFalse((self.root / "ledger" / "cycle-ledger.jsonl").exists())

    def test_quick_check_runs_axioms_floor(self):
        cycle = trinity_dan_cycle.run_cycle(self.root, self.config, repo_root=ROOT, check_mode="quick")

        self.assertEqual(cycle["status"], "SUCCEEDED")
        self.assertEqual([check["name"] for check in cycle["checks"]], ["axioms_floor"])
        self.assertEqual(cycle["checks"][0]["status"], "SUCCEEDED")
        self.assertIn("True", cycle["checks"][0]["stdout_tail"])

    def test_post_summary_routes_to_targets(self):
        cycle = trinity_dan_cycle.run_cycle(
            self.root,
            self.config,
            repo_root=ROOT,
            check_mode="none",
            post_summary=True,
            summary_targets="claude,antigravity",
        )

        self.assertEqual(cycle["status"], "SUCCEEDED")
        self.assertEqual(cycle["summary_route_summary"], {"routed": 1})
        self.assertEqual(len(list((self.root / "inbox" / "claude").glob("*cycle_summary*.json"))), 1)
        self.assertEqual(len(list((self.root / "inbox" / "antigravity").glob("*cycle_summary*.json"))), 1)

    def test_status_includes_latest_cycle_after_run(self):
        trinity_dan_cycle.run_cycle(self.root, self.config, repo_root=ROOT, check_mode="none")

        report = trinity_dan_cycle.status(self.root, self.config)

        self.assertTrue(report["latest_state_exists"])
        self.assertIsNotNone(report["latest_cycle"])
        self.assertEqual(report["latest_cycle"]["schema"], trinity_dan_cycle.SCHEMA)

    def test_missing_health_summary_uses_conservative_liveness_routing(self):
        cycle = trinity_dan_cycle.run_cycle(self.root, self.config, repo_root=ROOT, check_mode="none")

        routing = cycle["liveness_routing"]
        self.assertEqual(routing["source_status"], "CONSERVATIVE_FALLBACK")
        self.assertEqual(routing["reason"], "health_summary_missing")
        self.assertTrue(routing["agents"]["claude"]["queue_only"])
        self.assertEqual(routing["agents"]["claude"]["context_mode"], "compact")
        self.assertFalse(routing["agents"]["claude"]["may_auto_execute"])

    def test_unreadable_health_summary_uses_conservative_liveness_routing(self):
        path = self.root / "health" / "health_summary.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not-json", encoding="utf-8")

        cycle = trinity_dan_cycle.run_cycle(self.root, self.config, repo_root=ROOT, check_mode="none")

        self.assertEqual(cycle["liveness_routing"]["source_status"], "CONSERVATIVE_FALLBACK")
        self.assertEqual(cycle["liveness_routing"]["reason"], "health_summary_unreadable")

    def test_alive_liveness_does_not_authorize_unknown_execution_task(self):
        self.write_health_summary()
        self.post_unknown_execution_request()

        cycle = trinity_dan_cycle.run_cycle(self.root, self.config, repo_root=ROOT, check_mode="none")

        self.assertEqual(cycle["liveness_routing"]["agents"]["claude"]["status"], "ALIVE")
        self.assertEqual(cycle["liveness_routing"]["agents"]["claude"]["context_mode"], "normal")
        self.assertFalse(cycle["liveness_routing"]["agents"]["claude"]["may_auto_execute"])
        self.assertEqual(cycle["executor_summary"], {"execution_rejected": 1})
        rejected = list((self.root / "execution_rejected" / "codex").glob("*.json"))
        self.assertEqual(len(rejected), 1)

    def test_post_summary_uses_compact_digest_for_queue_only_target(self):
        self.write_health_summary(statuses={"codex": "ALIVE", "claude": "DOWN", "antigravity": "UNKNOWN"})

        cycle = trinity_dan_cycle.run_cycle(
            self.root,
            self.config,
            repo_root=ROOT,
            check_mode="none",
            post_summary=True,
            summary_targets="claude,antigravity",
        )

        self.assertEqual(cycle["summary_route_summary"], {"routed": 1})
        delivered = list((self.root / "inbox" / "claude").glob("*cycle_summary*.json"))
        self.assertEqual(len(delivered), 1)
        packet = self.read_json(delivered[0])
        self.assertIn("cycle_result_digest", packet)
        self.assertNotIn("cycle_result", packet)
        self.assertEqual(packet["cycle_result_digest"]["liveness_source"], "HEALTH_SUMMARY")
        self.assertEqual(packet["liveness_routing"]["agents"]["claude"]["context_mode"], "compact")


if __name__ == "__main__":
    unittest.main()
