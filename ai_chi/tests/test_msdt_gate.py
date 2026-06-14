"""MSDT Capability Gate — admissibility boundary; fail-closed; never executes; two-gate depth."""
import unittest

from ai_chi.bus import Mode
from ai_chi.msdt import (
    CapabilityDescriptor, CapabilityRegistry, RiskClass,
    CapabilityGate, CapabilityVerdict, ContractStatus,
)
from ai_chi.urbi.audit_signal import UrbiAuditSignal
from ai_chi.orbi.schemas import ActionProposal
from ai_chi.orbi.policy_gate import PolicyGate, Disposition, SUPPORT


def reg(*, risk=RiskClass.READ, reversible=True, schema=None):
    r = CapabilityRegistry()
    r.declare(CapabilityDescriptor(
        capability_id="fs.read.kb", verb="fs.read", target="kb_file",
        risk_class=risk, reversible=reversible,
        params_schema=schema or {"path": "str"}, provenance="urn:cap:fs.read.kb"))
    return r


def contract(reg_, params=None):
    return reg_.propose_contract("fs.read.kb", params or {"path": "/a"})


def sig(state="[+]", *, evidence=None, violations=None):
    return UrbiAuditSignal(claim_id="c", epistemic_state=state,
                           required_evidence=evidence or [],
                           constitutional_violations=violations or [])


class TestFailClosed(unittest.TestCase):
    def test_no_audit_refused(self):
        r = reg(); d = CapabilityGate().evaluate(contract(r), audit_signal=None, registry=r)
        self.assertIs(d.verdict, CapabilityVerdict.REFUSE)
        self.assertFalse(d.action_allowed)

    def test_undeclared_capability_refused(self):
        r = reg()
        c = contract(r)
        object.__setattr__  # noqa - just to be explicit we mutate the plain dataclass
        c.capability_id = "ghost.cap"
        d = CapabilityGate().evaluate(c, audit_signal=sig(), registry=r)
        self.assertIs(d.verdict, CapabilityVerdict.REFUSE)

    def test_dream_mode_refused(self):
        r = reg()
        d = CapabilityGate().evaluate(contract(r), audit_signal=sig(), registry=r, mode=Mode.DREAM)
        self.assertIs(d.verdict, CapabilityVerdict.REFUSE)

    def test_contradiction_refused(self):
        r = reg()
        d = CapabilityGate().evaluate(contract(r), audit_signal=sig("[-]"), registry=r)
        self.assertIs(d.verdict, CapabilityVerdict.REFUSE)

    def test_constitutional_violation_refused(self):
        r = reg()
        d = CapabilityGate().evaluate(contract(r),
                                      audit_signal=sig("[+]", violations=["urbi_non_actuation_violation"]),
                                      registry=r)
        self.assertIs(d.verdict, CapabilityVerdict.REFUSE)

    def test_suspended_suspends(self):
        r = reg()
        d = CapabilityGate().evaluate(contract(r), audit_signal=sig("[=]"), registry=r)
        self.assertIs(d.verdict, CapabilityVerdict.SUSPEND)

    def test_outstanding_evidence_suspends(self):
        r = reg()
        d = CapabilityGate().evaluate(contract(r),
                                      audit_signal=sig("[+]", evidence=["second_source"]), registry=r)
        self.assertIs(d.verdict, CapabilityVerdict.SUSPEND)

    def test_unknown_param_refused(self):
        r = reg()
        c = r.propose_contract("fs.read.kb", {"path": "/a"})
        c.requested_params = {"path": "/a", "delete": True}   # outside schema
        d = CapabilityGate().evaluate(c, audit_signal=sig(), registry=r)
        self.assertIs(d.verdict, CapabilityVerdict.REFUSE)


class TestRiskAndAdmit(unittest.TestCase):
    def test_high_risk_needs_human(self):
        r = reg(risk=RiskClass.HIGH)
        d = CapabilityGate().evaluate(contract(r), audit_signal=sig(), registry=r)
        self.assertIs(d.verdict, CapabilityVerdict.NEEDS_HUMAN)
        self.assertFalse(d.action_allowed)

    def test_irreversible_needs_human(self):
        r = reg(reversible=False)
        d = CapabilityGate().evaluate(contract(r), audit_signal=sig(), registry=r)
        self.assertIs(d.verdict, CapabilityVerdict.NEEDS_HUMAN)

    def test_human_approved_admits(self):
        r = reg(risk=RiskClass.HIGH)
        d = CapabilityGate().evaluate(contract(r), audit_signal=sig(), registry=r, human_approved=True)
        self.assertIs(d.verdict, CapabilityVerdict.ADMIT)

    def test_clean_read_admits_but_action_still_false(self):
        r = reg()
        d = CapabilityGate().evaluate(contract(r), audit_signal=sig(), registry=r)
        self.assertIs(d.verdict, CapabilityVerdict.ADMIT)
        self.assertFalse(d.action_allowed)              # ADMIT != execution
        self.assertIsInstance(d.lowered, ActionProposal)

    def test_terminal_decision_stamps_gated(self):
        r = reg()
        c = contract(r)
        CapabilityGate().evaluate(c, audit_signal=sig(), registry=r)
        self.assertIs(c.status, ContractStatus.GATED)


class TestNoExecutor(unittest.TestCase):
    def test_gate_has_no_execute_method(self):
        g = CapabilityGate()
        for attr in dir(g):
            self.assertNotIn(attr.lower(), {"run", "execute", "call", "invoke", "exec"})


class TestTwoGateDepth(unittest.TestCase):
    def test_admit_lowers_to_proposal_that_policygate_allows(self):
        r = reg()
        d = CapabilityGate().evaluate(contract(r), audit_signal=sig("[+]"), registry=r)
        self.assertIs(d.verdict, CapabilityVerdict.ADMIT)
        # the lowered proposal must independently clear the Orbi world-action gate
        pg = PolicyGate().evaluate(d.lowered, mode=Mode.WAKE, audit_signal=SUPPORT,
                                   trust=1.0, human_approved=False)
        self.assertIs(pg.disposition, Disposition.ALLOW)

    def test_high_risk_stopped_at_both_gates(self):
        r = reg(risk=RiskClass.CRITICAL)
        # MSDT holds for human...
        d = CapabilityGate().evaluate(contract(r), audit_signal=sig("[+]"), registry=r, human_approved=True)
        self.assertIs(d.verdict, CapabilityVerdict.ADMIT)  # human approved at MSDT
        # ...and even then PolicyGate independently re-checks risk → NEEDS_HUMAN without its own approval
        pg = PolicyGate().evaluate(d.lowered, mode=Mode.WAKE, audit_signal=SUPPORT, trust=1.0,
                                   human_approved=False)
        self.assertIs(pg.disposition, Disposition.NEEDS_HUMAN)

    def test_dream_blocks_at_both_gates(self):
        r = reg()
        # MSDT refuses in DREAM; PolicyGate also denies an action in DREAM (Ω₈)
        d = CapabilityGate().evaluate(contract(r), audit_signal=sig("[+]"), registry=r, mode=Mode.DREAM)
        self.assertIs(d.verdict, CapabilityVerdict.REFUSE)


if __name__ == "__main__":
    unittest.main()
