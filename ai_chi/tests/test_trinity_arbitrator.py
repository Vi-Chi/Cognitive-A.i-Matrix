import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARBITRATOR_PATH = ROOT / "scripts" / "trinity_arbitrator.py"


spec = importlib.util.spec_from_file_location("trinity_arbitrator", ARBITRATOR_PATH)
trinity_arbitrator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = trinity_arbitrator
spec.loader.exec_module(trinity_arbitrator)


class TrinityArbitratorTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name) / "bridge"
        self.config_path = self.root / "trinity-bridge.config.json"
        self.config = trinity_arbitrator.trinity_bridge.ensure_bridge(self.root, self.config_path)
        trinity_arbitrator.ensure_arbitrator(self.root, self.config)

    def write_outbox(self, source, packet):
        path = self.root / "outbox" / source / f"{packet['handoff_id']}.json"
        trinity_arbitrator.trinity_bridge.atomic_write_json(path, packet)
        return path

    def read_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def handoff_packet(self, handoff_id="handoff_safe"):
        return {
            "schema": trinity_arbitrator.trinity_bridge.SCHEMA,
            "handoff_id": handoff_id,
            "from": "codex",
            "to": ["claude"],
            "kind": "handoff",
            "priority": "MEDIUM",
            "objective": "Review arbitration",
            "summary": "Compact state should be written.",
            "body": "Please review the arbitration record.",
        }

    def test_safe_packet_gets_claim_and_compact_delta(self):
        path = self.write_outbox("codex", self.handoff_packet())

        records = trinity_arbitrator.arbitrate_once(self.root, self.config)

        self.assertEqual(records[0]["classification"], "safe")
        self.assertTrue(path.exists())
        rewritten = self.read_json(path)
        self.assertEqual(rewritten["arbitration"]["classification"], "safe")
        self.assertTrue(Path(records[0]["claim_path"]).exists())
        self.assertTrue(Path(records[0]["compact_path"]).exists())
        self.assertTrue((self.root / "ledger" / "arbitration-ledger.jsonl").exists())
        self.assertTrue((self.root / "state" / "latest-arbitration.json").exists())

    def test_action_like_packet_without_approval_moves_to_needs_human(self):
        packet = self.handoff_packet("needs_human_tool")
        packet["from"] = "claude"
        packet["to"] = ["codex"]
        packet["kind"] = "tool_request"
        path = self.write_outbox("claude", packet)

        records = trinity_arbitrator.arbitrate_once(self.root, self.config)

        self.assertEqual(records[0]["classification"], "needs-human")
        self.assertFalse(path.exists())
        moved = list((self.root / "needs_human" / "claude").glob("*.json"))
        self.assertEqual(len(moved), 1)
        self.assertTrue(Path(str(moved[0]) + ".reason.txt").exists())

    def test_expired_packet_moves_to_stale(self):
        packet = self.handoff_packet("old_packet")
        packet["expires_at"] = "2000-01-01T00:00:00Z"
        path = self.write_outbox("codex", packet)

        records = trinity_arbitrator.arbitrate_once(self.root, self.config)

        self.assertEqual(records[0]["classification"], "stale")
        self.assertFalse(path.exists())
        self.assertEqual(len(list((self.root / "stale" / "codex").glob("*.json"))), 1)

    def test_superseded_packet_is_quarantined_and_replacement_stays_safe(self):
        old_path = self.write_outbox("codex", self.handoff_packet("old_packet"))
        replacement = self.handoff_packet("new_packet")
        replacement["supersedes"] = ["old_packet"]
        new_path = self.write_outbox("codex", replacement)

        records = trinity_arbitrator.arbitrate_once(self.root, self.config)
        by_id = {record["handoff_id"]: record["classification"] for record in records}

        self.assertEqual(by_id["old_packet"], "superseded")
        self.assertEqual(by_id["new_packet"], "safe")
        self.assertFalse(old_path.exists())
        self.assertTrue(new_path.exists())
        self.assertEqual(len(list((self.root / "superseded" / "codex").glob("*.json"))), 1)

    def test_allowlisted_execution_request_is_safe(self):
        packet = {
            "schema": trinity_arbitrator.trinity_bridge.SCHEMA,
            "handoff_id": "safe_execution",
            "from": "claude",
            "to": ["codex"],
            "kind": "execution_request",
            "objective": "Run bridge status",
            "summary": "Safe structured request.",
            "body": "Do not use body as shell.",
            "execution": {
                "schema": trinity_arbitrator.trinity_executor.REQUEST_SCHEMA,
                "task_id": "bridge_status",
                "args": {},
            },
        }
        self.write_outbox("claude", packet)

        records = trinity_arbitrator.arbitrate_once(self.root, self.config)

        self.assertEqual(records[0]["classification"], "safe")
        self.assertTrue((self.root / "outbox" / "claude" / "safe_execution.json").exists())

    def test_unknown_execution_task_is_rejected(self):
        packet = {
            "schema": trinity_arbitrator.trinity_bridge.SCHEMA,
            "handoff_id": "bad_execution",
            "from": "claude",
            "to": ["codex"],
            "kind": "execution_request",
            "objective": "Run anything",
            "execution": {
                "schema": trinity_arbitrator.trinity_executor.REQUEST_SCHEMA,
                "task_id": "shell_anything",
                "args": {},
            },
        }
        path = self.write_outbox("claude", packet)

        records = trinity_arbitrator.arbitrate_once(self.root, self.config)

        self.assertEqual(records[0]["classification"], "invalid")
        self.assertFalse(path.exists())
        self.assertEqual(len(list((self.root / "arbitration_rejected" / "claude").glob("*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
