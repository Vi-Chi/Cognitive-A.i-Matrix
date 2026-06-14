"""Tests for the AIDICT Scout pipeline and its MΣBUS/ledger integration.

Deterministic, offline (no Hailo / Ollama). Helper functions are prefixed
``mk_`` to avoid colliding with unittest.TestCase internals (lesson from the
``_outcome`` collision in the P0 suite).
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_chi.aidict import importers
from ai_chi.aidict.contracts import build_contract
from ai_chi.aidict.detectors import classify, self_contradiction
from ai_chi.aidict.ledger import AidictLedger
from ai_chi.aidict.normalize import normalize_terms
from ai_chi.aidict.patterns import detect_patterns
from ai_chi.aidict.scout import AidictScout, persist_report, reality_loop_audit_fn
from ai_chi.aidict.schemas import (
    ClaimRecord,
    SIGMA_CLAIM,
    SIGMA_CONTRACT,
    SIGMA_PATTERN,
    SIGMA_SEGMENT,
    SIGMA_SOURCE,
    SIGMA_VERIFICATION,
)

SAMPLE = Path(__file__).resolve().parent.parent / "aidict" / "examples" / "sample_transcript.srt"


def mk_claim(text: str, **kw) -> ClaimRecord:
    det = classify(text)
    return ClaimRecord(
        source_id="src_test",
        claim_text=text,
        normalized_claim=normalize_terms(text),
        claim_type=det.claim_type,
        entities=det.entities,
        hype_markers=det.hype_markers,
        **kw,
    )


class TestNormalizer(unittest.TestCase):
    def test_asr_mutations(self):
        self.assertIn("qwen", normalize_terms("the Quinn model").lower())
        self.assertIn("swe-bench", normalize_terms("scores on sweet bench").lower())
        self.assertIn("hailo", normalize_terms("running on the Halo chip").lower())


class TestImporters(unittest.TestCase):
    def test_srt_timestamps(self):
        segs = importers.parse_srt(SAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(len(segs), 6)
        self.assertTrue(segs[0].start.startswith("00:00:01"))
        self.assertIn("Qwen", segs[0].text)

    def test_vtt_falls_back_to_srt_shape(self):
        vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello Qwen world.\n"
        segs = importers.parse_vtt(vtt)
        self.assertEqual(len(segs), 1)
        self.assertEqual(segs[0].start, "00:00:01.000")

    def test_sentence_split(self):
        out = importers.split_sentences("A is true. B beats C! Is D real?")
        self.assertEqual(len(out), 3)


class TestDetectors(unittest.TestCase):
    def test_benchmark_claim(self):
        det = classify("The new Qwen model beats GPT-4 on SWE-bench.")
        self.assertEqual(det.claim_type, "benchmark_claim")
        self.assertIn("qwen", det.entities)
        self.assertIn("gpt-4", det.entities)

    def test_hype_is_flagged_not_truth(self):
        det = classify("This is absolutely revolutionary and insane.")
        self.assertTrue(det.hype_markers)
        self.assertIn("hype", det.flags)

    def test_license_self_contradiction(self):
        det = classify("It is fully open source but the license is non-commercial only.")
        self.assertEqual(self_contradiction(det), "open_source vs restrictive_license")

    def test_local_vs_heavy_hardware_contradiction(self):
        det = classify("It runs locally on a laptop but really requires 8x H100 to serve.")
        self.assertEqual(self_contradiction(det), "runs_locally vs heavy_hardware")

    def test_prediction_detection(self):
        det = classify("By 2027 open-weight models will replace closed labs.")
        self.assertTrue(det.claim_type == "prediction" or "prediction" in det.flags)

    def test_noise_has_no_signal(self):
        det = classify("Anyway the weather has been really nice this week.")
        self.assertFalse(det.entities or det.flags or det.hype_markers)


class TestContracts(unittest.TestCase):
    def test_benchmark_contract_and_tasks(self):
        claim = mk_claim("Qwen beats GPT-4 on SWE-bench.")
        det = classify(claim.normalized_claim)
        contract, tasks = build_contract(claim, det)
        self.assertEqual(contract.contract_type, "benchmark_validation")
        self.assertTrue(tasks)
        self.assertEqual(len(contract.verification_task_ids), len(tasks))

    def test_verdict_sets_audit_signal_not_status(self):
        # Constitution §7.3: verdict -> attached audit_signal; status stays evidence-driven (open).
        claim = mk_claim("Qwen beats GPT-4 on SWE-bench.")
        det = classify(claim.normalized_claim)
        c_plus, _ = build_contract(claim, det, verdict="+")
        c_minus, _ = build_contract(claim, det, verdict="-")
        c_susp, _ = build_contract(claim, det, verdict="=")
        c_none, _ = build_contract(claim, det, verdict="")
        self.assertEqual(c_plus.audit_signal, "audit_support_signal")
        self.assertEqual(c_minus.audit_signal, "audit_contradiction_signal")
        self.assertEqual(c_susp.audit_signal, "audit_suspended")
        self.assertEqual(c_none.audit_signal, "pending")
        # No verdict moves the contract off `open` — only ValidationRecords do.
        for c in (c_plus, c_minus, c_susp, c_none):
            self.assertEqual(c.current_status, "open")

    def test_contradiction_raises_requirement(self):
        claim = mk_claim("Open source but non-commercial only license.")
        det = classify(claim.normalized_claim)
        contract, _ = build_contract(claim, det)
        self.assertTrue(any("contradiction" in r.lower()
                            for r in contract.validation_requirements))


class TestPatterns(unittest.TestCase):
    def test_repeated_and_hype(self):
        c1 = mk_claim("The Qwen model beats GPT-4 on SWE-bench, insane.")
        c2 = mk_claim("Qwen beats GPT-4 on SWE-bench and it is insane.")
        dets = {c1.claim_id: classify(c1.normalized_claim),
                c2.claim_id: classify(c2.normalized_claim)}
        pats = detect_patterns([c1, c2], dets, repeat_threshold=0.5)
        kinds = {p.pattern_type for p in pats}
        self.assertIn("repeated_claim", kinds)


class TestScoutEndToEnd(unittest.TestCase):
    def test_offline_pipeline(self):
        report = AidictScout().analyze_file(SAMPLE)
        self.assertEqual(report.segment_count, 6)
        self.assertGreaterEqual(report.noise_count, 1)        # the weather line
        self.assertTrue(report.claims)
        self.assertTrue(report.contracts)
        self.assertTrue(report.tasks)
        # contradiction patterns should surface for qwen (open/restrict, local/heavy)
        kinds = {p.pattern_type for p in report.patterns}
        self.assertTrue({"contradiction_cluster", "repeated_claim"} & kinds)
        # markdown + jsonl render without error
        self.assertIn("AIDICT Scout", report.render_markdown())

    def test_messages_are_valid_envelopes(self):
        report = AidictScout().analyze_file(SAMPLE)
        sigmas = {m.sigma for m in report.to_messages()}
        self.assertIn(SIGMA_SOURCE, sigmas)
        self.assertIn(SIGMA_SEGMENT, sigmas)
        self.assertIn(SIGMA_CLAIM, sigmas)
        self.assertIn(SIGMA_CONTRACT, sigmas)
        self.assertIn(SIGMA_VERIFICATION, sigmas)
        for m in report.to_messages():
            m.validate()                      # raises if any envelope is malformed
            self.assertFalse(m.is_action)     # AIDICT never emits action-class

    def test_ledger_routes_all_streams(self):
        report = AidictScout().analyze_file(SAMPLE)
        with tempfile.TemporaryDirectory() as d:
            ledger = AidictLedger(d)
            n = persist_report(report, ledger)
            self.assertGreater(n, 0)
            self.assertTrue((Path(d) / "sources.jsonl").exists())
            self.assertTrue((Path(d) / "segments.jsonl").exists())
            self.assertTrue((Path(d) / "claims.jsonl").exists())
            self.assertTrue((Path(d) / "evidence.jsonl").exists())
            self.assertTrue((Path(d) / "contracts.jsonl").exists())
            self.assertTrue((Path(d) / "verification_tasks.jsonl").exists())


class TestRealityLoopAudit(unittest.TestCase):
    def test_fake_auditor_routes_claims(self):
        from ai_chi.core.loop import RealityLoop
        from ai_chi.run_core import FakeSuspendingAuditor

        with tempfile.TemporaryDirectory() as d:
            loop = RealityLoop(ledger_dir=str(Path(d) / "ledger"),
                               auditor=FakeSuspendingAuditor())
            scout = AidictScout(audit_fn=reality_loop_audit_fn(loop))
            report = scout.analyze_file(SAMPLE)
            # FakeSuspendingAuditor returns "=" -> contracts stay open, audited.
            audited = [c for c in report.contracts if c.audit_verdict == "="]
            self.assertTrue(audited)
            # the loop wrote belief/prediction envelopes to its own ledger
            self.assertTrue((Path(d) / "ledger" / "predictions.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
