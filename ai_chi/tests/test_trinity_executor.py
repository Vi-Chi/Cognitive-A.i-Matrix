import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXECUTOR_PATH = ROOT / "scripts" / "trinity_executor.py"


spec = importlib.util.spec_from_file_location("trinity_executor", EXECUTOR_PATH)
trinity_executor = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = trinity_executor
spec.loader.exec_module(trinity_executor)


class TrinityExecutorTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name) / "bridge"
        self.config_path = self.root / "trinity-bridge.config.json"
        self.config = trinity_executor.trinity_bridge.ensure_bridge(self.root, self.config_path)
        trinity_executor.ensure_executor(self.root)

    def write_inbox(self, packet):
        path = self.root / "inbox" / "codex" / f"{packet['handoff_id']}.json"
        trinity_executor.trinity_bridge.atomic_write_json(path, packet)
        return path

    def read_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def execution_packet(self, task_id="bridge_status"):
        return {
            "schema": trinity_executor.trinity_bridge.SCHEMA,
            "handoff_id": f"handoff_{task_id}",
            "from": "claude",
            "to": ["codex"],
            "kind": "execution_request",
            "priority": "LOW",
            "objective": f"Run {task_id}",
            "summary": "Request a safe local executor task.",
            "body": "Use the structured execution object only.",
            "execution": {
                "schema": trinity_executor.REQUEST_SCHEMA,
                "task_id": task_id,
                "reason": "unit test",
                "args": {},
            },
        }

    def test_executes_allowlisted_bridge_status_request(self):
        posted = self.write_inbox(self.execution_packet("bridge_status"))

        events = trinity_executor.process_once(self.root, self.config, repo_root=ROOT)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "executed")
        self.assertEqual(events[0]["task_id"], "bridge_status")
        self.assertFalse(posted.exists())
        self.assertEqual(len(list((self.root / "executed" / "codex").glob("*.json"))), 1)

        result_files = list((self.root / "outbox" / "codex").glob("*.json"))
        self.assertEqual(len(result_files), 1)
        result = self.read_json(result_files[0])
        self.assertEqual(result["kind"], "execution_result")
        self.assertEqual(result["to"], ["claude"])
        self.assertEqual(result["execution_result"]["status"], "SUCCEEDED")
        self.assertEqual(result["execution_result"]["task_id"], "bridge_status")
        self.assertIn("bridge-status", result["execution_result"]["stdout"])

        ledger = self.root / "ledger" / "execution-ledger.jsonl"
        self.assertTrue(ledger.exists())
        self.assertIn('"event": "executed"', ledger.read_text(encoding="utf-8"))

    def test_rejects_execution_request_without_structured_execution(self):
        packet = self.execution_packet("bridge_status")
        packet.pop("execution")
        posted = self.write_inbox(packet)

        events = trinity_executor.process_once(self.root, self.config, repo_root=ROOT)

        self.assertEqual(events[0]["event"], "execution_rejected")
        self.assertIn("structured execution object", events[0]["reason"])
        self.assertFalse(posted.exists())
        self.assertEqual(len(list((self.root / "execution_rejected" / "codex").glob("*.json"))), 1)

        result = self.read_json(list((self.root / "outbox" / "codex").glob("*.json"))[0])
        self.assertEqual(result["execution_result"]["status"], "REJECTED")

    def test_rejects_unknown_task_id(self):
        posted = self.write_inbox(self.execution_packet("shell_anything"))

        events = trinity_executor.process_once(self.root, self.config, repo_root=ROOT)

        self.assertEqual(events[0]["event"], "execution_rejected")
        self.assertIn("unknown execution.task_id", events[0]["reason"])
        self.assertFalse(posted.exists())
        self.assertEqual(len(list((self.root / "executed" / "codex").glob("*.json"))), 0)

    def test_leaves_non_execution_handoff_in_inbox(self):
        packet = {
            "schema": trinity_executor.trinity_bridge.SCHEMA,
            "handoff_id": "handoff_review",
            "from": "claude",
            "to": ["codex"],
            "kind": "handoff",
            "objective": "Manual Codex review",
            "body": "This is not an execution request.",
        }
        posted = self.write_inbox(packet)

        events = trinity_executor.process_once(self.root, self.config, repo_root=ROOT)

        self.assertEqual(events, [])
        self.assertTrue(posted.exists())

    def test_task_catalog_is_all_non_approval_by_default(self):
        catalog = trinity_executor.task_catalog()
        task_ids = {item["task_id"] for item in catalog}
        self.assertIn("bridge_status", task_ids)
        self.assertIn("axioms_floor", task_ids)
        self.assertTrue(all(item["requires_user_approval"] is False for item in catalog))


if __name__ == "__main__":
    unittest.main()
