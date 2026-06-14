"""Tests for AutopoiesisLedger"""
import tempfile
import unittest
from pathlib import Path

from ai_chi.bus.transports.file_transport import (
    FINGERPRINT_FIELD,
    PREV_FINGERPRINT_FIELD,
    FileBackedSigmaTransport,
    record_fingerprint,
)
from ai_chi.core.ledger.autopoiesis_ledger import (
    COMPUTE_RECEIPT_SCHEMA,
    COMPUTE_RECEIPT_SIGMA,
    AutopoiesisLedger,
)
from ai_chi.orbi.policy_gate import CONTRADICTION, SUPPORT, Disposition, PolicyGate
from ai_chi.orbi.schemas import ActionProposal


class TestAutopoiesisLedger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name)
        self.transport = FileBackedSigmaTransport(self.storage_path)
        self.ledger = AutopoiesisLedger(self.transport)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _records(self):
        return list(self.transport.read_stream(self.ledger.stream_name))

    def test_meter_action_denied(self):
        receipt = self.ledger.meter_action({
            "proposal_id": "act_denied",
            "actor_id": "ghost_x",
            "action_type": "fs.write",
            "target": "blocked.txt",
            "risk_level": "medium",
            "provenance": ["ghost_x"],
        }, allowed=False)

        self.assertEqual(receipt["schema"], COMPUTE_RECEIPT_SCHEMA)
        self.assertEqual(receipt["route_used"], "refused")
        self.assertEqual(receipt["error_signal"], "gate_denied")
        self.assertEqual(receipt["actual_cost"]["sigma_credit"], 0.0)
        self.assertEqual(receipt["settlement_ref"], "local-simulation-only")

        [stored] = self._records()
        self.assertEqual(stored["σ"], COMPUTE_RECEIPT_SIGMA)
        self.assertEqual(stored["π"], receipt)
        self.assertEqual(stored[PREV_FINGERPRINT_FIELD], "")
        self.assertEqual(stored[FINGERPRINT_FIELD], record_fingerprint(stored))

    def test_meter_action_allowed(self):
        receipt = self.ledger.meter_action({
            "proposal_id": "act_allowed",
            "actor_id": "ghost_x",
            "action_type": "fs.write",
            "target": "note.txt",
            "risk_level": "medium",
            "args": {
                "mock_compute_units": 2,
                "runtime_ms": 17,
                "storage_bytes": 128,
            },
            "provenance": ["ghost_x"],
        }, allowed=True)

        self.assertEqual(receipt["route_used"], "local_context")
        self.assertEqual(receipt["error_signal"], "none")
        self.assertGreater(receipt["actual_cost"]["sigma_credit"], 0.0)
        self.assertEqual(receipt["actual_cost"]["sigma_credit"], 6.0)
        self.assertEqual(receipt["actual_cost"]["runtime_ms"], 17)
        self.assertEqual(receipt["actual_cost"]["storage_bytes"], 128)
        self.assertEqual(receipt["actual_cost"]["network_bytes"], 0)

        [stored] = self._records()
        self.assertEqual(stored["π"]["proposal_id"], "act_allowed")
        self.assertEqual(stored["π"]["actual_cost"]["sigma_credit"], 6.0)

    def test_policy_gate_meters_allowed_and_denied_actions(self):
        gate = PolicyGate.with_local_autopoiesis_ledger(self.storage_path)
        allowed = ActionProposal(
            actor_id="ghost_x",
            action_type="fs.read",
            target="note.txt",
            actor_role="ghost",
            provenance=["ghost_x"],
        )
        denied = ActionProposal(
            actor_id="ghost_x",
            action_type="fs.write",
            target="note.txt",
            actor_role="ghost",
            provenance=["ghost_x"],
        )

        allowed_decision = gate.evaluate(allowed, audit_signal=SUPPORT, trust=1.0)
        denied_decision = gate.evaluate(denied, audit_signal=CONTRADICTION, trust=1.0)

        self.assertIs(allowed_decision.disposition, Disposition.ALLOW)
        self.assertIs(denied_decision.disposition, Disposition.DENY)
        records = self._records()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[1][PREV_FINGERPRINT_FIELD], records[0][FINGERPRINT_FIELD])
        self.assertTrue(self.transport.verify_stream_integrity(self.ledger.stream_name)["ok"])
        self.assertGreater(records[0]["π"]["actual_cost"]["sigma_credit"], 0.0)
        self.assertEqual(records[1]["π"]["actual_cost"]["sigma_credit"], 0.0)
        self.assertEqual(records[1]["π"]["route_used"], "refused")

    def test_policy_gate_metering_failure_is_passive(self):
        class FailingLedger:
            def meter_action(self, action_intent, allowed):
                raise RuntimeError("ledger offline")

        gate = PolicyGate(autopoiesis_ledger=FailingLedger())
        proposal = ActionProposal(
            actor_id="ghost_x",
            action_type="fs.read",
            target="note.txt",
            actor_role="ghost",
            provenance=["ghost_x"],
        )

        decision = gate.evaluate(proposal, audit_signal=SUPPORT, trust=1.0)

        self.assertIs(decision.disposition, Disposition.ALLOW)
        self.assertIn("RuntimeError", gate.last_metering_error)


if __name__ == "__main__":
    unittest.main()
