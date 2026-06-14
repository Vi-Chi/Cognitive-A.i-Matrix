import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trinity_bridge.health.heartbeat import write_heartbeat
from trinity_bridge.quota_guard import (
    append_jsonl,
    atomic_write_json,
    compute_agent_state,
    decision_for_state,
    load_config,
    run_once,
)


NOW = datetime(2026, 6, 14, 7, 0, 0, tzinfo=timezone.utc)


class TrinityQuotaGuardTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name) / "bridge"

    def read_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def read_jsonl(self, path):
        return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]

    def write_event(self, record):
        append_jsonl(self.root / "quota" / "events" / "manual.jsonl", record)

    def test_missing_config_uses_safe_defaults(self):
        config = load_config(self.root)

        self.assertEqual(config["poll_interval_seconds"], 60)
        self.assertEqual(config["stale_heartbeat_seconds"], 600)
        self.assertFalse(config["paid_overflow_default"])
        self.assertFalse(config["auto_top_up_allowed"])
        self.assertFalse(config["agents"]["claude"]["paid_overflow_allowed"])
        self.assertEqual(config["agents"]["claude"]["session_window_hours"], 5)

    def test_claude_session_reset_is_inferred_from_configured_window(self):
        config = load_config(self.root)
        hit_at = NOW - timedelta(hours=1)
        self.write_event(
            {
                "agent": "claude",
                "reason": "session_limit_hit",
                "limit_hit_at": hit_at.isoformat().replace("+00:00", "Z"),
            }
        )

        state = compute_agent_state(self.root, "claude", config, now=NOW)

        self.assertEqual(state["status"], "COOLDOWN_UNTIL_RESET")
        self.assertTrue(state["reset_inferred"])
        self.assertEqual(state["reset_at"], (hit_at + timedelta(hours=5)).isoformat().replace("+00:00", "Z"))

    def test_codex_usage_limit_reset_is_not_guessed_without_evidence(self):
        config = load_config(self.root)
        self.write_event(
            {
                "agent": "codex",
                "reason": "usage_limit_hit",
                "limit_hit_at": NOW.isoformat().replace("+00:00", "Z"),
            }
        )

        state = compute_agent_state(self.root, "codex", config, now=NOW)

        self.assertEqual(state["status"], "EXHAUSTED")
        self.assertIsNone(state["reset_at"])
        self.assertEqual(state["requires"], "REQUIRE_PROVIDER_STATUS_OR_MANUAL_RESET")

    def test_stale_heartbeat_produces_offline(self):
        config = load_config(self.root)
        write_heartbeat(self.root, agent="antigravity", now=NOW - timedelta(seconds=700))

        state = compute_agent_state(self.root, "antigravity", config, now=NOW)

        self.assertEqual(state["status"], "OFFLINE")
        self.assertEqual(state["reason"], "heartbeat stale")

    def test_reset_probable_emits_one_poke_then_throttles(self):
        config = load_config(self.root)
        hit_at = NOW - timedelta(hours=6)
        write_heartbeat(self.root, agent="claude", now=NOW - timedelta(seconds=700))
        self.write_event(
            {
                "agent": "claude",
                "reason": "session_limit_hit",
                "limit_hit_at": hit_at.isoformat().replace("+00:00", "Z"),
            }
        )

        first = run_once(self.root, config=config, now=NOW, write=True)
        second = run_once(self.root, config=config, now=NOW + timedelta(seconds=60), write=True)

        self.assertEqual(first["agents"]["claude"]["status"], "RESET_PROBABLE")
        self.assertEqual(first["poke_events"][0]["event"], "quota_poke_emitted")
        self.assertEqual(second["poke_events"][0]["event"], "quota_poke_throttled")
        pokes = list((self.root / "inbox" / "claude").glob("*quota_poke*.json"))
        self.assertEqual(len(pokes), 1)
        packet = self.read_json(pokes[0])
        self.assertEqual(packet["type"], "quota_poke")
        self.assertFalse(packet["authority"]["may_execute_tools"])
        self.assertFalse(packet["authority"]["may_mutate_config"])
        self.assertFalse(packet["authority"]["may_spend_credits"])

    def test_paid_overflow_requires_human_approval(self):
        state = {
            "agent": "claude",
            "status": "COOLDOWN_UNTIL_RESET",
            "confidence": 0.7,
            "next_check_at": "2026-06-14T12:00:00Z",
        }

        decision = decision_for_state(state, "HEAVY", paid_allowed=True)

        self.assertEqual(decision["decision"], "REQUIRE_HUMAN")
        self.assertIn("human approval", decision["reason"])

    def test_downtime_start_and_end_records_are_appended(self):
        config = load_config(self.root)
        snapshot_path = self.root / "quota" / "snapshots" / "claude.latest.json"
        atomic_write_json(snapshot_path, {"agent": "claude", "status": "EXHAUSTED", "reason": "quota_exhausted"})
        run_once(self.root, config=config, now=NOW, write=True)
        atomic_write_json(snapshot_path, {"agent": "claude", "status": "READY"})
        run_once(self.root, config=config, now=NOW + timedelta(seconds=30), write=True)

        events = self.read_jsonl(self.root / "quota" / "downtime" / "2026-06-14.downtime.jsonl")
        self.assertEqual(events[0]["event"], "DOWNTIME_STARTED")
        self.assertEqual(events[1]["event"], "DOWNTIME_ENDED")
        self.assertEqual(events[1]["duration_seconds"], 30)

    def test_router_allows_status_only_but_blocks_heavy_during_cooldown(self):
        state = {
            "agent": "claude",
            "status": "COOLDOWN_UNTIL_RESET",
            "confidence": 0.75,
            "next_check_at": "2026-06-14T12:00:00Z",
        }

        status_only = decision_for_state(state, "STATUS_ONLY")
        heavy = decision_for_state(state, "HEAVY")

        self.assertEqual(status_only["decision"], "ALLOW_STATUS")
        self.assertEqual(heavy["decision"], "DEFER")

    def test_packet_body_text_is_not_read_for_keyword_detection(self):
        config = load_config(self.root)
        inbox = self.root / "inbox" / "codex"
        inbox.mkdir(parents=True, exist_ok=True)
        atomic_write_json(
            inbox / "body-only.json",
            {
                "from": "claude",
                "to": "codex",
                "kind": "handoff",
                "body": "usage_limit_hit should not be detected from raw body text",
            },
        )

        state = compute_agent_state(self.root, "codex", config, now=NOW)

        self.assertNotIn("usage_limit_hit", state["detected_keywords"])
        self.assertTrue(state["evidence"]["packet_metadata_records"])

    def test_generic_packet_summary_is_not_quota_failure_evidence(self):
        config = load_config(self.root)
        inbox = self.root / "inbox" / "codex"
        inbox.mkdir(parents=True, exist_ok=True)
        atomic_write_json(
            inbox / "summary-only.json",
            {
                "from": "claude",
                "to": "codex",
                "kind": "handoff",
                "summary": "Claude session limit note for human context, not a Codex quota event.",
                "objective": "Record bridge context.",
            },
        )

        state = compute_agent_state(self.root, "codex", config, now=NOW)

        self.assertNotIn("session_limit_hit", state["detected_keywords"])


if __name__ == "__main__":
    unittest.main()
