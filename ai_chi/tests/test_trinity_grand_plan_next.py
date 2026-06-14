import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "trinity_grand_plan_next.py"
BRIDGE_PATH = ROOT / "scripts" / "trinity_bridge.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


grand_plan = load_module("trinity_grand_plan_next", SCRIPT_PATH)
trinity_bridge = load_module("trinity_bridge_for_grand_plan_tests", BRIDGE_PATH)


class TrinityGrandPlanNextTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        (self.root / "scripts").mkdir()
        (self.root / "_MODEL_TRINITY" / "bridge").mkdir(parents=True)
        (self.root / "_PROJECT_KNOWLEDGE_BASE" / "reports").mkdir(parents=True)
        (self.root / "docs").mkdir()

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_selects_safe_local_task_from_backlog(self):
        self.write(
            "docs/ROADMAP.md",
            "# Roadmap\n\nTODO: add local validation tests for the Grand Plan scanner.\n",
        )
        self.write(
            "LIVE_CAPABILITY_APPROVALS.md",
            "NEXT: call provider API after credential adoption.\n",
        )

        report = grand_plan.build_report(self.root, limit=3)

        self.assertEqual(report["schema"], grand_plan.SCHEMA)
        self.assertGreaterEqual(len(report["selected_tasks"]), 1)
        top = report["selected_tasks"][0]
        self.assertTrue(top["safe_for_local_execution"])
        self.assertIn("validation tests", top["title"])
        approval_tasks = [task for task in report["selected_tasks"] if task["source_type"] == "live_capability_approvals"]
        self.assertTrue(all(task["allowed_actions"] == ["draft approval packet only", "do not execute gated action"] for task in approval_tasks))

    def test_bridge_inbox_metadata_is_used_without_body_required(self):
        inbox = self.root / "_MODEL_TRINITY" / "bridge" / "inbox" / "codex"
        inbox.mkdir(parents=True)
        packet = {
            "objective": "Implement local schema test",
            "summary": "Add tests for repo-contained handoff packet validation.",
            "body": "This body is intentionally not needed by the scanner.",
            "requested_output": "Patch",
            "files_in_scope": ["ai_chi/tests/test_schema.py"],
        }
        (inbox / "handoff.json").write_text(json.dumps(packet), encoding="utf-8")

        report = grand_plan.build_report(self.root, role="codex", limit=1)

        self.assertEqual(report["selected_tasks"][0]["source_type"], "bridge_inbox")
        self.assertIn("schema test", report["selected_tasks"][0]["title"])

    def test_superseded_state_snapshot_is_down_ranked(self):
        self.write(
            "_PROJECT_KNOWLEDGE_BASE/STATE_OF_SYSTEM_2026-06-12.md",
            "# Old State\n\nNext safe task: build the already completed old harness.\n",
        )
        self.write(
            "_PROJECT_KNOWLEDGE_BASE/STATE_OF_SYSTEM_2026-06-14.md",
            "# New State\n\nSupersedes `STATE_OF_SYSTEM_2026-06-12.md`.\n\nNext: patch the scanner supersession heuristic.\n",
        )

        report = grand_plan.build_report(self.root, limit=3)

        top = report["selected_tasks"][0]
        self.assertEqual(top["source_path"], "_PROJECT_KNOWLEDGE_BASE/STATE_OF_SYSTEM_2026-06-14.md")
        self.assertIn("scanner supersession heuristic", top["title"])
        old = [task for task in report["selected_tasks"] if task["source_path"].endswith("STATE_OF_SYSTEM_2026-06-12.md")]
        self.assertTrue(old)
        self.assertTrue(all(task["superseded_source"] for task in old))

    def test_completion_hints_are_down_ranked_below_open_work(self):
        self.write(
            "_PROJECT_KNOWLEDGE_BASE/reports/OLD_REPORT.md",
            "Next safe task: DreamLens evaluation harness completed and verified.\n",
        )
        self.write(
            "docs/ROADMAP.md",
            "NEXT: add local scanner regression tests.\n",
        )

        report = grand_plan.build_report(self.root, limit=2)

        self.assertIn("scanner regression tests", report["selected_tasks"][0]["title"])
        completed = [task for task in report["selected_tasks"] if "DreamLens" in task["title"]]
        self.assertTrue(completed)
        self.assertTrue(completed[0]["completion_hint"])

    def test_current_state_numbered_open_items_outrank_stale_reports(self):
        self.write(
            "_PROJECT_KNOWLEDGE_BASE/reports/CLAUDE_SESSION_CLOSE_HANDOFF_2026-06-13.md",
            "Next safe task: draft the already landed transport persistence ADR.\n",
        )
        self.write(
            "_PROJECT_KNOWLEDGE_BASE/STATE_OF_SYSTEM_2026-06-14.md",
            "\n".join(
                [
                    "# New State",
                    "",
                    "### Now",
                    "1. Codex (open): add local cycle-runner liveness queueing tests.",
                    "2. Before liveness feeds the cycle runner: confirm volume-only gates.",
                    "",
                    "- **Open (Codex):** keep old status summary out of ranked work.",
                ]
            ),
        )

        report = grand_plan.build_report(self.root, limit=3)

        top = report["selected_tasks"][0]
        self.assertEqual(top["source_path"], "_PROJECT_KNOWLEDGE_BASE/STATE_OF_SYSTEM_2026-06-14.md")
        self.assertTrue(top["current_state_source"])
        self.assertIn("liveness", top["title"])
        stale = [task for task in report["selected_tasks"] if task["source_type"] == "report"]
        self.assertTrue(stale)
        self.assertTrue(stale[0]["stale_source"])
        self.assertFalse(any("old status summary" in task["title"] for task in report["selected_tasks"]))

    def test_bridge_completion_hints_are_down_ranked_below_open_work(self):
        self.write(
            "docs/ROADMAP.md",
            "NEXT: add local bridge inbox triage tests.\n",
        )
        inbox = self.root / "_MODEL_TRINITY" / "bridge" / "inbox" / "codex"
        inbox.mkdir(parents=True)
        packet = {
            "objective": "ACK Trinity bridge source authority patch",
            "summary": "Patch accepted and verified; none required.",
            "requested_output": "NoAction",
            "files_in_scope": ["scripts/trinity_bridge.py"],
        }
        (inbox / "ack.json").write_text(json.dumps(packet), encoding="utf-8")

        report = grand_plan.build_report(self.root, role="codex", limit=2)

        self.assertIn("bridge inbox triage tests", report["selected_tasks"][0]["title"])
        ack = [task for task in report["selected_tasks"] if task["source_type"] == "bridge_inbox"]
        self.assertTrue(ack)
        self.assertTrue(ack[0]["completion_hint"])

    def test_grand_plan_packet_routes_as_non_action_handoff(self):
        report = {
            "mode": "Accelerated DAN / Grand Plan Local Operator Mode",
            "created_at": "2026-06-14T00:00:00Z",
            "selected_tasks": [
                {
                    "rank": 1,
                    "title": "Add local docs test",
                    "evidence": "docs/ROADMAP.md:3",
                    "recommended_model": "claude",
                    "safe_for_local_execution": True,
                }
            ],
            "still_forbidden_without_exact_approval": ["provider/API calls"],
        }
        packet = grand_plan.report_to_packet(report, "claude,antigravity")
        bridge_root = self.root / "_MODEL_TRINITY" / "bridge"
        config_path = bridge_root / "trinity-bridge.config.json"
        config = trinity_bridge.ensure_bridge(bridge_root, config_path)

        posted = trinity_bridge.post_packet(bridge_root, packet)
        events = trinity_bridge.route_once(bridge_root, config)

        self.assertFalse(posted.exists())
        self.assertEqual(events[0]["event"], "routed")
        self.assertEqual(events[0]["targets"], ["claude", "antigravity"])
        delivered = list((bridge_root / "inbox" / "claude").glob("*.json"))
        self.assertEqual(len(delivered), 1)
        routed = json.loads(delivered[0].read_text(encoding="utf-8"))
        self.assertEqual(routed["requested_output"], "GrandPlanNextTasks")
        self.assertFalse(routed["requires_user_approval"])


if __name__ == "__main__":
    unittest.main()
