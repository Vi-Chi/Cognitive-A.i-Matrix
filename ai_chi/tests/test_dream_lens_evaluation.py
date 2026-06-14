"""Fixture-driven DreamLens evaluation tests."""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from ai_chi.urbi.dream.eval_harness import run_fixture_harness
from ai_chi.urbi.dream.evaluation import (
    DEFAULT_FIXTURE_DIR,
    evaluate_fixture,
    load_fixtures,
)
import ai_chi.urbi.dream.lens as lens_module


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "dream_lens"


class TestDreamLensEvaluationFixtures(unittest.TestCase):
    def _result(self, filename):
        fixture = load_fixture(filename)
        return evaluate_fixture(fixture)

    def test_fixture_loader_works(self):
        fixtures = load_fixtures(FIXTURE_DIR)
        self.assertGreaterEqual(len(fixtures), 10)
        names = {fixture["name"] for fixture in fixtures}
        self.assertIn("prediction_error_basic", names)
        self.assertIn("offline_degrades_empty", names)

    def test_valid_prediction_error_accepted(self):
        result = self._result("prediction_error_basic.json")
        self.assertEqual(result.scores["accepted_count"], 1)
        self.assertEqual(result.accepted[0].kind.value, "prediction_error")
        self.assertEqual(result.scores["precision"], 1.0)
        self.assertFalse(result.action_allowed)

    def test_valid_belief_conflict_accepted(self):
        result = self._result("belief_conflict_basic.json")
        self.assertEqual(result.accepted[0].kind.value, "belief_conflict")
        self.assertEqual(result.scores["coverage_by_kind"]["belief_conflict"], 1)

    def test_valid_simulacrum_accepted(self):
        result = self._result("simulacrum_loop_basic.json")
        self.assertEqual(result.accepted[0].kind.value, "simulacrum")
        self.assertEqual(result.scores["coverage_by_kind"]["simulacrum"], 1)

    def test_unresolved_uncertainty_accepted(self):
        result = self._result("unresolved_uncertainty_basic.json")
        self.assertEqual(result.accepted[0].kind.value, "unresolved_uncertainty")
        self.assertEqual(result.scores["coverage_by_kind"]["unresolved_uncertainty"], 1)

    def test_mixed_hints_score_correctly(self):
        result = self._result("mixed_hints_basic.json")
        self.assertEqual(result.scores["accepted_count"], 3)
        self.assertEqual(result.scores["true_positive_count"], 2)
        self.assertEqual(result.scores["false_positive_count"], 1)
        self.assertEqual(result.scores["false_negative_count"], 1)
        self.assertAlmostEqual(result.scores["precision"], 0.666667)
        self.assertAlmostEqual(result.scores["recall"], 0.666667)

    def test_invented_claim_ids_rejected(self):
        result = self._result("invented_claim_id_rejected.json")
        self.assertEqual(result.scores["accepted_count"], 0)
        self.assertEqual(result.scores["invented_claim_id_count"], 1)
        self.assertEqual(result.rejected[0].reason, "invented_claim_id")

    def test_unknown_kind_normalized(self):
        result = self._result("unknown_kind_normalized.json")
        self.assertEqual(result.scores["accepted_count"], 1)
        self.assertEqual(result.scores["normalized_kind_count"], 1)
        self.assertEqual(result.accepted[0].kind.value, "unresolved_uncertainty")

    def test_malformed_json_degrades_safely(self):
        result = self._result("malformed_json_degrades_empty.json")
        self.assertEqual(result.scores["accepted_count"], 0)
        self.assertEqual(result.scores["malformed_output_count"], 1)
        self.assertEqual(result.rejected[0].reason, "malformed_json")

    def test_action_tool_permission_output_rejected(self):
        result = self._result("action_request_rejected.json")
        self.assertEqual(result.scores["accepted_count"], 0)
        self.assertEqual(result.scores["unsafe_output_count"], 1)
        self.assertEqual(result.rejected[0].reason, "unsafe_action_leakage")
        self.assertFalse(result.action_allowed)

    def test_offline_none_degrades_empty(self):
        result = self._result("offline_degrades_empty.json")
        self.assertEqual(result.scores["accepted_count"], 0)
        self.assertEqual(result.scores["offline_degradation_count"], 1)
        self.assertEqual(result.rejected[0].reason, "offline_none")

    def test_no_network_required_for_harness(self):
        with mock.patch.object(lens_module.urllib.request, "urlopen", side_effect=AssertionError("network")):
            payload = run_fixture_harness(FIXTURE_DIR)
        self.assertEqual(payload["summary"]["fixtures"], 10)
        self.assertFalse(payload["action_allowed"])

    def test_dreamlens_evaluation_cannot_grant_action(self):
        payload = run_fixture_harness(FIXTURE_DIR)
        self.assertFalse(payload["action_allowed"])
        self.assertFalse(payload["summary"]["action_allowed"])
        self.assertTrue(all(not result["action_allowed"] for result in payload["results"]))


def load_fixture(filename):
    import json

    return json.loads((FIXTURE_DIR / filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
