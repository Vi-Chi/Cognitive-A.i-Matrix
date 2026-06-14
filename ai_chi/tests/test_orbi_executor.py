"""Tests for the OrbiExecutor and its constitutional enforcement."""

import unittest

from ai_chi.orbi.schemas import ActionProposal
from ai_chi.orbi.policy_gate import PolicyGate
from ai_chi.orbi.executor import OrbiExecutor
from ai_chi.bus import Mode

class TestOrbiExecutor(unittest.TestCase):
    def setUp(self):
        self.gate = PolicyGate(trust_floor=0.7)
        self.executor = OrbiExecutor(self.gate)
        self.base_proposal = ActionProposal(
            actor_id="ghost_1",
            action_type="fs.read",
            target="/tmp/test.txt",
            actor_role="agent",
            provenance=["ghost_1"]
        )

    def test_executor_fail_closed_on_missing_audit(self):
        """Missing or PENDING audit signal MUST deny action."""
        result = self.executor.execute(
            self.base_proposal,
            mode=Mode.WAKE,
            audit_signal="pending",
            trust=0.9
        )
        self.assertEqual(result.status, "deny")
        self.assertIn("no Urbi support signal", result.disposition_reason)

    def test_executor_allows_valid_signal(self):
        """A SUPPORT signal with good trust and provenance executes successfully."""
        result = self.executor.execute(
            self.base_proposal,
            mode=Mode.WAKE,
            audit_signal="audit_support_signal",
            trust=0.9
        )
        self.assertEqual(result.status, "executed")
        self.assertEqual(result.output, {"content": "simulated read of /tmp/test.txt"})

    def test_executor_restricts_hardware_targets(self):
        """Exclusion zones MUST reject even with a valid SUPPORT signal."""
        restricted_proposal = ActionProposal(
            actor_id="ghost_1",
            action_type="fs.write",
            target="/dev/can0",
            actor_role="agent",
            provenance=["ghost_1"]
        )
        result = self.executor.execute(
            restricted_proposal,
            mode=Mode.WAKE,
            audit_signal="audit_support_signal",
            trust=0.9
        )
        self.assertEqual(result.status, "error")
        self.assertIn("restricted by constitutional exclusion zones", result.disposition_reason)

    def test_executor_restricts_dangerous_args(self):
        """Exclusion zones MUST scan args before handlers ever become real."""
        restricted_proposal = ActionProposal(
            actor_id="ghost_1",
            action_type="shell.run",
            target="echo",
            args={"command": "cat /etc/passwd", "notes": ["diagnostic"]},
            actor_role="agent",
            provenance=["ghost_1"]
        )
        result = self.executor.execute(
            restricted_proposal,
            mode=Mode.WAKE,
            audit_signal="audit_support_signal",
            trust=0.9
        )
        self.assertEqual(result.status, "error")
        self.assertIn("restricted by constitutional exclusion zones", result.disposition_reason)

    def test_executor_action_monopoly(self):
        """Urbi cannot propose actions; executor must deny."""
        urbi_proposal = ActionProposal(
            actor_id="urbi_kernel",
            action_type="shell.run",
            target="echo 'hello'",
            actor_role="urbi",
            provenance=["urbi_kernel"]
        )
        result = self.executor.execute(
            urbi_proposal,
            mode=Mode.WAKE,
            audit_signal="audit_support_signal",
            trust=0.9
        )
        self.assertEqual(result.status, "deny")
        self.assertIn("action monopoly", result.disposition_reason)

if __name__ == "__main__":
    unittest.main()
