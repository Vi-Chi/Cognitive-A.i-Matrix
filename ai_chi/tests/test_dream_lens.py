"""OllamaDreamLens — proposes contradictions, never grants action; degrades offline."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ai_chi.bus import PredictionRecord
from ai_chi.urbi.dream import OllamaDreamLens, DreamReplayAuditor, ContradictionKind
import ai_chi.urbi.dream.lens as lens_module
from ai_chi.urbi.dream.lens import LENS_SYSTEM, load_lens_prompt


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "urbi_lens_prompt.md"


def rec(rid, **kw):
    base = dict(record_id=rid, belief_state={"k": 1}, predicted_outcome={"v": 1},
                domain="d", confidence=0.5)
    base.update(kw)
    return PredictionRecord(**base)


class TestOllamaDreamLens(unittest.TestCase):
    def test_prompt_file_matches_contradiction_hint_schema(self):
        text = PROMPT_PATH.read_text(encoding="utf-8")
        self.assertIn('"claim_id"', text)
        self.assertIn("prediction_error | belief_conflict | simulacrum | unresolved_uncertainty", text)
        self.assertIn('"severity"', text)
        self.assertNotIn("UrbiAuditSignal", text)

    def test_prompt_loader_falls_back_when_missing(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch.object(lens_module, "DEFAULT_PROMPT_PATH", Path("missing/default.md")):
            self.assertEqual(load_lens_prompt("missing/dreamlens.md"), LENS_SYSTEM)

    def test_env_prompt_override_loads_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "lens.md"
            path.write_text("CUSTOM DREAMLENS PROMPT", encoding="utf-8")
            with mock.patch.dict(os.environ, {"URBI_DREAM_LENS_PROMPT": str(path)}):
                self.assertEqual(load_lens_prompt(), "CUSTOM DREAMLENS PROMPT")

    def test_env_config_does_not_require_network(self):
        with mock.patch.dict(os.environ, {
            "URBI_DREAM_LENS_MODEL": "local-test-model",
            "URBI_DREAM_LENS_TIMEOUT": "7",
            "URBI_DREAM_LENS_MAX_RECORDS": "2",
            "URBI_DREAM_LENS_BASE": "http://127.0.0.1:11434/",
        }):
            lens = OllamaDreamLens(transport=lambda p: "[]")
            self.assertEqual(lens.model, "local-test-model")
            self.assertEqual(lens.timeout, 7.0)
            self.assertEqual(lens.max_records, 2)
            self.assertEqual(lens.base_url, "http://127.0.0.1:11434")
            self.assertEqual(lens.propose([rec("a")]), [])

    def test_offline_degrades_to_empty(self):
        lens = OllamaDreamLens(transport=lambda p: (_ for _ in ()).throw(OSError("offline")))
        self.assertEqual(lens.propose([rec("a")]), [])

    def test_parses_valid_proposals(self):
        raw = '[{"claim_id":"a","kind":"belief_conflict","severity":"high","detail":"x"}]'
        lens = OllamaDreamLens(transport=lambda p: raw)
        out = lens.propose([rec("a")])
        self.assertEqual(len(out), 1)
        self.assertIs(out[0].kind, ContradictionKind.BELIEF_CONFLICT)
        self.assertTrue(out[0].detail.startswith("[lens]"))

    def test_cannot_invent_claim_ids(self):
        raw = '[{"claim_id":"GHOST","kind":"simulacrum","severity":"high"}]'
        lens = OllamaDreamLens(transport=lambda p: raw)
        self.assertEqual(lens.propose([rec("a")]), [])  # GHOST not in batch → dropped

    def test_unknown_kind_becomes_unresolved(self):
        raw = '[{"claim_id":"a","kind":"grant_action","severity":"high"}]'
        lens = OllamaDreamLens(transport=lambda p: raw)
        out = lens.propose([rec("a")])
        self.assertIs(out[0].kind, ContradictionKind.UNRESOLVED)  # no "action" kind exists

    def test_malformed_json_degrades(self):
        lens = OllamaDreamLens(transport=lambda p: "not json {")
        self.assertEqual(lens.propose([rec("a")]), [])

    def test_lens_feeds_auditor_without_granting_action(self):
        raw = '[{"claim_id":"a","kind":"unresolved_uncertainty","severity":"low","detail":"hint"}]'
        a = DreamReplayAuditor(lens=OllamaDreamLens(transport=lambda p: raw))
        report = a.run_cycle([rec("a", confidence=0.9, causal_parents=["p1", "p2"])])
        self.assertTrue(any("hint" in c.detail for c in report.contradictions))
        self.assertFalse(a.to_message(report).is_action)


if __name__ == "__main__":
    unittest.main()


class TestPublicSanitizer(unittest.TestCase):
    """sanitize_dream_lens_hints — the extracted public, model-agnostic sanitizer.

    Same closed-vocabulary contract the OllamaDreamLens proposer and the evaluation
    harness both rely on; pure (no network/model/action)."""

    def test_delegation_matches_method(self):
        from ai_chi.urbi.dream.lens import sanitize_dream_lens_hints, OllamaDreamLens
        raw = '[{"claim_id":"a","kind":"belief_conflict","severity":"high","detail":"x"}]'
        viafn = sanitize_dream_lens_hints(raw, valid_ids={"a"})
        viamethod = OllamaDreamLens(transport=lambda p: "[]")._sanitize(raw, valid_ids={"a"})
        self.assertEqual([(c.claim_id, c.kind, c.severity) for c in viafn],
                         [(c.claim_id, c.kind, c.severity) for c in viamethod])

    def test_refuses_invented_claim(self):
        from ai_chi.urbi.dream.lens import sanitize_dream_lens_hints
        out = sanitize_dream_lens_hints('[{"claim_id":"ghost","kind":"simulacrum"}]', valid_ids={"a"})
        self.assertEqual(out, [])

    def test_unknown_kind_to_unresolved(self):
        from ai_chi.urbi.dream.lens import sanitize_dream_lens_hints
        out = sanitize_dream_lens_hints('[{"claim_id":"a","kind":"grant_action"}]', valid_ids={"a"})
        self.assertEqual(out[0].kind, ContradictionKind.UNRESOLVED)

    def test_malformed_degrades_empty(self):
        from ai_chi.urbi.dream.lens import sanitize_dream_lens_hints
        self.assertEqual(sanitize_dream_lens_hints("not json {", valid_ids={"a"}), [])

    def test_bad_severity_clamped(self):
        from ai_chi.urbi.dream.lens import sanitize_dream_lens_hints
        out = sanitize_dream_lens_hints('[{"claim_id":"a","kind":"unresolved_uncertainty","severity":"nuclear"}]', valid_ids={"a"})
        self.assertEqual(out[0].severity, "medium")
