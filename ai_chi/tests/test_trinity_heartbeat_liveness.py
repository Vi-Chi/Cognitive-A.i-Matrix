import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trinity_bridge.health.heartbeat import write_heartbeat
from trinity_bridge.health.models import HealthError, PokeBackoffError
from trinity_bridge.health.poke import send_poke
from trinity_bridge.health.summary import overall_status, summarize_health


NOW = datetime(2026, 6, 14, 6, 0, 0, tzinfo=timezone.utc)


class TrinityHeartbeatLivenessTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name) / "bridge"

    def read_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def read_ndjson(self, path):
        return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_heartbeat_writes_current_and_history(self):
        record = write_heartbeat(self.root, agent="codex", now=NOW, cycle_id="cycle-1")

        current = self.read_json(self.root / "health" / "codex" / "heartbeat.json")
        history = self.read_ndjson(self.root / "health" / "codex" / "heartbeat_history.ndjson")
        self.assertEqual(current["schema_version"], "digivichi.trinity.health.heartbeat.v0")
        self.assertEqual(current["agent"], "codex")
        self.assertEqual(current["cycle_id"], "cycle-1")
        self.assertEqual(history[-1], record)
        self.assertFalse(current["capabilities"]["can_call_provider"])
        self.assertFalse(current["capabilities"]["can_mutate_app_config"])

    def test_missing_heartbeat_is_unknown(self):
        summary = summarize_health(self.root, now=NOW, write=False)
        self.assertEqual(summary["agents"]["codex"]["status"], "UNKNOWN")
        self.assertIsNone(summary["agents"]["codex"]["seconds_since_seen"])

    def test_fresh_heartbeat_is_alive(self):
        write_heartbeat(self.root, agent="codex", now=NOW)
        summary = summarize_health(self.root, now=NOW + timedelta(seconds=60), write=False)
        self.assertEqual(summary["agents"]["codex"]["status"], "ALIVE")

    def test_old_heartbeat_is_stale(self):
        write_heartbeat(self.root, agent="claude", now=NOW - timedelta(seconds=1000))
        summary = summarize_health(self.root, now=NOW, write=False)
        self.assertEqual(summary["agents"]["claude"]["status"], "STALE")

    def test_very_old_heartbeat_is_down(self):
        write_heartbeat(self.root, agent="antigravity", now=NOW - timedelta(seconds=1900))
        summary = summarize_health(self.root, now=NOW, write=True)
        self.assertEqual(summary["agents"]["antigravity"]["status"], "DOWN")

    def test_resource_pressure_is_degraded(self):
        write_heartbeat(
            self.root,
            agent="codex",
            now=NOW,
            resource_notes={"cooldown": True, "quota_limited": True, "last_error": "quota"},
        )
        summary = summarize_health(self.root, now=NOW + timedelta(seconds=30), write=False)
        self.assertEqual(summary["agents"]["codex"]["status"], "DEGRADED")

    def test_down_started_is_not_duplicated(self):
        write_heartbeat(self.root, agent="claude", now=NOW - timedelta(seconds=2000))
        summarize_health(self.root, now=NOW, write=True)
        summarize_health(self.root, now=NOW + timedelta(seconds=10), write=True)

        events = self.read_ndjson(self.root / "health" / "downtime_events.ndjson")
        down_events = [event for event in events if event["event"] == "DOWN_STARTED" and event["agent"] == "claude"]
        self.assertEqual(len(down_events), 1)

    def test_recovered_is_not_duplicated(self):
        write_heartbeat(self.root, agent="claude", now=NOW - timedelta(seconds=2000))
        summarize_health(self.root, now=NOW, write=True)
        write_heartbeat(self.root, agent="claude", now=NOW + timedelta(seconds=1))
        summarize_health(self.root, now=NOW + timedelta(seconds=2), write=True)
        summarize_health(self.root, now=NOW + timedelta(seconds=3), write=True)

        events = self.read_ndjson(self.root / "health" / "downtime_events.ndjson")
        recovered = [event for event in events if event["event"] == "RECOVERED" and event["agent"] == "claude"]
        self.assertEqual(len(recovered), 1)

    def test_poke_backoff_works(self):
        send_poke(self.root, from_agent="codex", to_agent="claude", now=NOW, correlation_id="poke-1")
        with self.assertRaises(PokeBackoffError):
            send_poke(self.root, from_agent="codex", to_agent="claude", now=NOW + timedelta(seconds=60))

    def test_poke_packet_does_not_grant_authority(self):
        result = send_poke(self.root, from_agent="codex", to_agent="claude", now=NOW, correlation_id="poke-2")
        packet = self.read_json(result["packet_path"])
        self.assertEqual(packet["type"], "liveness_poke")
        self.assertEqual(packet["schema"], "digivichi.trinity.handoff.v0")
        self.assertEqual(packet["from"], "codex")
        self.assertEqual(packet["kind"], "liveness_poke")
        self.assertFalse(packet["may_execute_commands"])
        self.assertFalse(packet["may_mutate_peer_config"])
        self.assertFalse(packet["may_read_secrets"])
        self.assertTrue(packet["requires_user_approval_for_escalation"])
        self.assertEqual(result["route_event"]["event"], "routed")

    def test_summary_produces_token_routing_recommendation(self):
        write_heartbeat(self.root, agent="codex", now=NOW)
        write_heartbeat(self.root, agent="claude", now=NOW - timedelta(seconds=1000))
        summary = summarize_health(self.root, now=NOW, write=True)
        self.assertEqual(summary["overall_status"], "DEGRADED")
        self.assertIn("codex", summary["routing_recommendation"]["send_new_work_to"])
        self.assertIn("claude", summary["routing_recommendation"]["queue_only_for"])
        self.assertEqual(summary["agents"]["codex"]["token_automation_weight"], 1.0)
        self.assertTrue(summary["authority_boundary"]["capabilities_are_advisory"])
        self.assertTrue((self.root / "health" / "health_summary.json").exists())

    def test_overall_status_is_advisory_aggregate(self):
        self.assertEqual(overall_status({"codex": "ALIVE", "claude": "ALIVE"}), "ALIVE")
        self.assertEqual(overall_status({"codex": "ALIVE", "claude": "UNKNOWN"}), "DEGRADED")
        self.assertEqual(overall_status({"codex": "ALIVE", "claude": "STALE"}), "DEGRADED")
        self.assertEqual(overall_status({"codex": "ALIVE", "claude": "DOWN"}), "DOWN")

    def test_expired_lease_downgrades_frozen_alive_record(self):
        write_heartbeat(self.root, agent="codex", now=NOW, lease_seconds=300)
        summary = summarize_health(self.root, now=NOW + timedelta(seconds=400), write=False)
        self.assertEqual(summary["agents"]["codex"]["status"], "STALE")

    def test_records_reject_obvious_secret_values_and_do_not_dump_raw_logs(self):
        raw_value = ("sk" + "-") + "1234567890abcdef"
        with self.assertRaises(HealthError):
            write_heartbeat(self.root, agent="codex", now=NOW, notes=f"token={raw_value}")
        write_heartbeat(self.root, agent="codex", now=NOW, notes="short safe note\nwithout raw logs")
        send_poke(self.root, from_agent="codex", to_agent="claude", now=NOW, correlation_id="poke-3")
        summary = summarize_health(self.root, now=NOW, write=True)
        text = json.dumps(summary, sort_keys=True)
        self.assertNotIn(raw_value, text)
        self.assertNotIn("Traceback (most recent call last)", text)


if __name__ == "__main__":
    unittest.main()
