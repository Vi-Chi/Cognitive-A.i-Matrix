import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BRIDGE_PATH = ROOT / "scripts" / "trinity_bridge.py"


spec = importlib.util.spec_from_file_location("trinity_bridge", BRIDGE_PATH)
trinity_bridge = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(trinity_bridge)


class TrinityBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name) / "bridge"
        self.config_path = self.root / "trinity-bridge.config.json"
        self.config = trinity_bridge.ensure_bridge(self.root, self.config_path)

    def read_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def test_post_and_route_to_two_targets(self):
        packet = {
            "schema": trinity_bridge.SCHEMA,
            "handoff_id": "handoff_test",
            "from": "codex",
            "to": ["claude", "antigravity"],
            "kind": "handoff",
            "objective": "Review bridge",
            "body": "Check docs and tests.",
        }

        posted = trinity_bridge.post_packet(self.root, packet)
        self.assertTrue(posted.exists())

        events = trinity_bridge.route_once(self.root, self.config)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "routed")
        self.assertEqual(events[0]["targets"], ["claude", "antigravity"])
        self.assertFalse(posted.exists())

        claude_inbox = list((self.root / "inbox" / "claude").glob("*.json"))
        antigravity_inbox = list((self.root / "inbox" / "antigravity").glob("*.json"))
        self.assertEqual(len(claude_inbox), 1)
        self.assertEqual(len(antigravity_inbox), 1)
        self.assertEqual(self.read_json(claude_inbox[0])["handoff_id"], "handoff_test")

        ledger = self.root / "ledger" / "route-ledger.jsonl"
        self.assertTrue(ledger.exists())
        self.assertIn('"event": "routed"', ledger.read_text(encoding="utf-8"))

    def test_unknown_target_is_rejected(self):
        packet = {
            "schema": trinity_bridge.SCHEMA,
            "handoff_id": "handoff_bad_target",
            "from": "codex",
            "to": ["nobody"],
            "kind": "handoff",
            "objective": "Bad target",
        }
        posted = trinity_bridge.post_packet(self.root, packet)

        events = trinity_bridge.route_once(self.root, self.config)
        self.assertEqual(events[0]["event"], "rejected")
        self.assertIn("unknown target", events[0]["reason"])
        self.assertFalse(posted.exists())
        rejected = list((self.root / "rejected" / "codex").glob("*.json"))
        self.assertEqual(len(rejected), 1)
        self.assertTrue(Path(str(rejected[0]) + ".reason.txt").exists())

    def test_action_like_packet_requires_user_approval(self):
        packet = {
            "schema": trinity_bridge.SCHEMA,
            "handoff_id": "handoff_action",
            "from": "claude",
            "to": ["codex"],
            "kind": "tool_request",
            "objective": "Run a tool",
            "body": "Please run this.",
            "requires_user_approval": False,
        }
        trinity_bridge.post_packet(self.root, packet)

        events = trinity_bridge.route_once(self.root, self.config)
        self.assertEqual(events[0]["event"], "rejected")
        self.assertIn("requires requires_user_approval=true", events[0]["reason"])
        self.assertEqual(len(list((self.root / "inbox" / "codex").glob("*.json"))), 0)

    def test_outbox_source_is_authoritative(self):
        packet = {
            "schema": trinity_bridge.SCHEMA,
            "handoff_id": "handoff_spoof",
            "from": "claude",
            "to": ["antigravity"],
            "kind": "handoff",
            "objective": "Spoof sender",
        }
        spoof_path = self.root / "outbox" / "codex" / "handoff_spoof.json"
        trinity_bridge.atomic_write_json(spoof_path, packet)

        events = trinity_bridge.route_once(self.root, self.config)

        self.assertEqual(events[0]["event"], "rejected")
        self.assertEqual(events[0]["source"], "codex")
        self.assertIn("differs from outbox", events[0]["reason"])
        self.assertEqual(len(list((self.root / "inbox" / "antigravity").glob("*.json"))), 0)
        self.assertEqual(len(list((self.root / "processed" / "claude").glob("*.json"))), 0)
        self.assertEqual(len(list((self.root / "rejected" / "codex").glob("*.json"))), 1)

    def test_status_counts_queues(self):
        packet = {
            "schema": trinity_bridge.SCHEMA,
            "handoff_id": "handoff_status",
            "from": "antigravity",
            "to": ["codex"],
            "kind": "handoff",
            "objective": "Status test",
        }
        trinity_bridge.post_packet(self.root, packet)
        report = trinity_bridge.status(self.root, self.config)
        self.assertEqual(report["outbox"]["antigravity"], 1)
        self.assertEqual(report["inbox"]["codex"], 0)

    def test_target_quota_limited_is_rejected(self):
        packet = {
            "schema": trinity_bridge.SCHEMA,
            "handoff_id": "handoff_quota",
            "from": "claude",
            "to": ["codex"],
            "kind": "handoff",
            "objective": "Heavy task",
            "body": "Do work.",
        }
        posted = trinity_bridge.post_packet(self.root, packet)
        
        quota_path = self.root / "quota" / "codex" / "quota_state.json"
        quota_path.parent.mkdir(parents=True, exist_ok=True)
        quota_path.write_text(json.dumps({"status": "quota_limited"}), encoding="utf-8")
        
        events = trinity_bridge.route_once(self.root, self.config)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "rejected")
        self.assertIn("quota_limited", events[0]["reason"])
        self.assertEqual(len(list((self.root / "inbox" / "codex").glob("*.json"))), 0)

    def test_expired_ttl_packet_is_rejected(self):
        old_created_at = (
            datetime.now(timezone.utc) - timedelta(seconds=120)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        packet = {
            "schema": trinity_bridge.SCHEMA,
            "handoff_id": "handoff_expired",
            "created_at": old_created_at,
            "ttl_seconds": 1,
            "from": "codex",
            "to": ["claude"],
            "kind": "handoff",
            "objective": "Expired packet",
            "body": "This should not route.",
        }
        posted = trinity_bridge.post_packet(self.root, packet)

        events = trinity_bridge.route_once(self.root, self.config)

        self.assertEqual(events[0]["event"], "rejected")
        self.assertIn("ttl_expired", events[0]["reason"])
        self.assertFalse(posted.exists())
        self.assertEqual(len(list((self.root / "inbox" / "claude").glob("*.json"))), 0)

    def test_invalid_created_at_is_rejected(self):
        packet = {
            "schema": trinity_bridge.SCHEMA,
            "handoff_id": "handoff_bad_created_at",
            "created_at": "not-a-date",
            "from": "codex",
            "to": ["claude"],
            "kind": "handoff",
            "objective": "Invalid timestamp",
        }
        trinity_bridge.post_packet(self.root, packet)

        events = trinity_bridge.route_once(self.root, self.config)

        self.assertEqual(events[0]["event"], "rejected")
        self.assertIn("invalid created_at", events[0]["reason"])
        self.assertEqual(len(list((self.root / "inbox" / "claude").glob("*.json"))), 0)

    def test_existing_bridge_lock_blocks_route_once(self):
        lock_path = self.root / ".bridge.lock"
        lock_path.write_text("already locked\n", encoding="utf-8")
        packet = {
            "schema": trinity_bridge.SCHEMA,
            "handoff_id": "handoff_locked",
            "from": "codex",
            "to": ["claude"],
            "kind": "handoff",
            "objective": "Locked route",
        }
        trinity_bridge.post_packet(self.root, packet)

        with self.assertRaises(trinity_bridge.BridgeError) as raised:
            trinity_bridge.route_once(self.root, self.config)

        self.assertIn("bridge lock already exists", str(raised.exception))
        self.assertTrue(lock_path.exists())
        self.assertEqual(len(list((self.root / "inbox" / "claude").glob("*.json"))), 0)

    def test_bridge_lock_is_cleaned_after_rejection(self):
        packet = {
            "schema": trinity_bridge.SCHEMA,
            "handoff_id": "handoff_bad_target_with_lock",
            "from": "codex",
            "to": ["nobody"],
            "kind": "handoff",
            "objective": "Rejected while locked",
        }
        trinity_bridge.post_packet(self.root, packet)

        events = trinity_bridge.route_once(self.root, self.config)

        self.assertEqual(events[0]["event"], "rejected")
        self.assertFalse((self.root / ".bridge.lock").exists())

    def test_max_payload_bytes_is_rejected(self):
        packet = {
            "schema": trinity_bridge.SCHEMA,
            "handoff_id": "handoff_too_large",
            "from": "codex",
            "to": ["claude"],
            "kind": "handoff",
            "objective": "Test size limit",
            "body": "A" * (trinity_bridge.MAX_PAYLOAD_BYTES + 10)
        }
        posted = trinity_bridge.post_packet(self.root, packet)
        
        events = trinity_bridge.route_once(self.root, self.config)
        self.assertEqual(events[0]["event"], "rejected")
        self.assertIn("Payload too large", events[0]["reason"])
        self.assertFalse(posted.exists())
        self.assertEqual(len(list((self.root / "inbox" / "claude").glob("*.json"))), 0)


if __name__ == "__main__":
    unittest.main()
