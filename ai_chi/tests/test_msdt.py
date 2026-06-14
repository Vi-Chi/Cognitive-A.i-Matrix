"""MSDT capability descriptors — typed, inert, fail-closed machine control plane seed."""
import unittest

from ai_chi.bus import Mode, is_action_layer
from ai_chi.msdt import (
    CapabilityDescriptor, CapabilityRegistry, ExecutionContract, ContractStatus,
    RiskClass, MsdtError, SIGMA_CONTRACT,
)


def cap():
    return CapabilityDescriptor(
        capability_id="fs.read.kb", verb="fs.read", target="kb_file",
        risk_class=RiskClass.READ, reversible=True,
        params_schema={"path": "str"}, required_evidence=("path_in_workspace",))


class TestCapabilities(unittest.TestCase):
    def test_descriptor_requires_dotted_verb(self):
        with self.assertRaises(MsdtError):
            CapabilityDescriptor(capability_id="x", verb="noverb", target="t")

    def test_registry_declare_and_propose(self):
        reg = CapabilityRegistry(); reg.declare(cap())
        c = reg.propose_contract("fs.read.kb", {"path": "/a"})
        self.assertIsInstance(c, ExecutionContract)
        self.assertEqual(c.status, ContractStatus.DECLARED)

    def test_unknown_param_refused(self):
        reg = CapabilityRegistry(); reg.declare(cap())
        with self.assertRaises(MsdtError):
            reg.propose_contract("fs.read.kb", {"path": "/a", "rm": True})

    def test_unknown_capability_refused(self):
        with self.assertRaises(MsdtError):
            CapabilityRegistry().propose_contract("ghost", {})

    def test_contract_action_always_false(self):
        reg = CapabilityRegistry(); reg.declare(cap())
        c = reg.propose_contract("fs.read.kb", {"path": "/a"})
        self.assertFalse(c.action_allowed)
        c.attach_audit("urbi:abc123")          # auditing never grants action
        self.assertEqual(c.status, ContractStatus.AUDITED)
        self.assertFalse(c.action_allowed)
        self.assertFalse(c.to_payload()["action_allowed"])

    def test_contract_rides_bus_as_cognition(self):
        reg = CapabilityRegistry(); reg.declare(cap())
        c = reg.propose_contract("fs.read.kb", {"path": "/a"}, mode=Mode.WAKE)
        msg = c.to_message()
        self.assertEqual(msg.sigma, SIGMA_CONTRACT)
        self.assertFalse(msg.is_action)
        self.assertFalse(is_action_layer(SIGMA_CONTRACT))


if __name__ == "__main__":
    unittest.main()
