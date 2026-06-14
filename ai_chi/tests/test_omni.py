"""Omni center — governs the Court of Heralds, never acts directly.

Tests the mebus-free governance core (plan/roster/resolve/realm pre-check/tool
narrowing) and the delegation path via a FakeSpawner + injected request class.
"""
import unittest
from dataclasses import dataclass, field

from ai_chi.orbi.omni import OmniCenter, OmniError, ConveneOrder
from ai_chi.bus.realms import CognitiveRealm


# --- lightweight fakes so the delegation path runs without mebus ---
@dataclass
class FakeRequest:
    agent_template: str
    mission: str
    actor_role: str = "orbi"
    requested_tools: list = field(default_factory=list)
    risk_level: str = "low"
    context_refs: list = field(default_factory=list)


class FakeSpawner:
    def __init__(self):
        self.registry = {}
        self.calls = []

    def spawn(self, request, **kwargs):
        self.calls.append((request, kwargs))
        return ("instance", "result", "decision")


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.omni = OmniCenter()  # plan-only (no spawner)

    def test_roster_has_six_named(self):
        names = set(self.omni.names())
        self.assertEqual(names, {"Lumen", "Mneme", "Logos", "Artifex", "Noctis", "Nomos"})
        self.assertEqual(len(self.omni.roster()), 6)

    def test_resolve_by_name_and_template_id(self):
        self.assertEqual(self.omni.resolve("Logos").template_id, "h3.meaning.v0")
        self.assertEqual(self.omni.resolve("h5.shadow.v0").name, "Noctis")
        with self.assertRaises(OmniError):
            self.omni.resolve("Ghost")

    def test_plan_defaults_to_primary_realm(self):
        # Lumen is EMBODIED-only -> primary EMBODIED; Noctis has no EMBODIED -> POSSIBILITY
        self.assertIs(self.omni.plan("Lumen", "look").origin_realm, CognitiveRealm.EMBODIED)
        self.assertIs(self.omni.plan("Noctis", "hunt").origin_realm, CognitiveRealm.POSSIBILITY)

    def test_plan_refuses_out_of_realm(self):
        # Lumen may not operate in POSSIBILITY (DPHA boundary)
        with self.assertRaises(OmniError) as ctx:
            self.omni.plan("Lumen", "dream", origin_realm="possibility")
        self.assertIn("does not operate in realm", str(ctx.exception))

    def test_plan_narrows_tools_and_strips_forbidden(self):
        order = self.omni.plan("Lumen", "observe", requested_tools=["fs.read", "maritime.actuation"])
        self.assertIn("fs.read", order.granted_tools)
        self.assertNotIn("maritime.actuation", order.granted_tools)

    def test_plan_requires_mission(self):
        with self.assertRaises(OmniError):
            self.omni.plan("Lumen", "   ")

    def test_convene_order_carries_realm_context_and_authority(self):
        order = self.omni.plan("Noctis", "red-team")
        self.assertEqual(order.realm_context["origin_realm"], "possibility")
        self.assertEqual(order.realm_context["crossing_authority"], "omni.noctis")
        self.assertEqual(order.risk_level, "low")  # simulation tier

    def test_forge_is_medium_risk(self):
        self.assertEqual(self.omni.plan("Artifex", "build").risk_level, "medium")  # execution tier


class DelegationTests(unittest.TestCase):
    def test_convene_without_spawner_refuses(self):
        with self.assertRaises(OmniError):
            OmniCenter().convene("Lumen", "x")

    def test_convene_delegates_to_spawner_gated(self):
        spawner = FakeSpawner()
        omni = OmniCenter(spawner=spawner)
        result = omni.convene("Mneme", "recall lineage", request_cls=FakeRequest)
        self.assertEqual(result, ("instance", "result", "decision"))
        self.assertEqual(len(spawner.calls), 1)
        req, _ = spawner.calls[0]
        self.assertEqual(req.agent_template, "h2.memory.v0")
        self.assertEqual(req.actor_role, "orbi")  # Omni convenes via the Orbi substrate
        self.assertIn("omni:Mneme", req.context_refs)
        # herald auto-registered as a spawnable template
        self.assertIn("h2.memory.v0", spawner.registry)

    def test_convene_passes_realm_refusal_up(self):
        omni = OmniCenter(spawner=FakeSpawner())
        with self.assertRaises(OmniError):
            omni.convene("Lumen", "dream", origin_realm="possibility", request_cls=FakeRequest)

    def test_convene_many_preserves_divergence(self):
        spawner = FakeSpawner()
        omni = OmniCenter(spawner=spawner)
        out = omni.convene_many(
            [{"herald": "Lumen", "mission": "see"}, {"herald": "Noctis", "mission": "hunt"}],
            request_cls=FakeRequest,
        )
        self.assertEqual([n for n, _ in out], ["Lumen", "Noctis"])
        self.assertEqual(len(spawner.calls), 2)  # two separate branches, never merged


if __name__ == "__main__":
    unittest.main()
