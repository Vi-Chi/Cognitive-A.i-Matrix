"""DPHA Heralds: contracts, names/titles/tiers, constitutional guards, registry merge."""
import unittest

from ai_chi.orbi.herald import (
    HeraldArchetype, HeraldContract, HeraldContractError, COURT_OF_HERALDS,
    herald_templates, HERALD_NAMES, HERALD_TITLES, HERALD_TIERS, by_name,
)
from ai_chi.orbi.registry import AgentTemplate
from ai_chi.bus.realms import CognitiveRealm


class HeraldTests(unittest.TestCase):
    def test_court_has_six(self):
        self.assertEqual(len(COURT_OF_HERALDS), 6)
        self.assertEqual({c.archetype for c in COURT_OF_HERALDS.values()}, set(HeraldArchetype))

    def test_canonical_names_titles_tiers(self):
        self.assertEqual({c.name for c in COURT_OF_HERALDS.values()},
                         {"Lumen", "Mneme", "Logos", "Artifex", "Noctis", "Nomos"})
        sight = COURT_OF_HERALDS["h1.sight.v0"]
        self.assertEqual(sight.name, "Lumen")
        self.assertEqual(sight.title, "Herald of Sight")
        self.assertEqual(sight.memory_tier, "T0")
        # canon: Forge->Making, Shadow->Night; tiers T0..T5
        self.assertEqual(COURT_OF_HERALDS["h4.forge.v0"].title, "Herald of Making")
        self.assertEqual(COURT_OF_HERALDS["h5.shadow.v0"].title, "Herald of Night")
        self.assertEqual({c.memory_tier for c in COURT_OF_HERALDS.values()},
                         {"T0", "T1", "T2", "T3", "T4", "T5"})
        self.assertEqual(HERALD_TIERS[HeraldArchetype.LAW], "T5")

    def test_by_name_lookup(self):
        self.assertIs(by_name("Logos"), COURT_OF_HERALDS["h3.meaning.v0"])
        self.assertEqual(by_name("artifex").archetype, HeraldArchetype.FORGE)
        self.assertIsNone(by_name("nobody"))

    def test_lowers_to_agent_template(self):
        t = COURT_OF_HERALDS["h1.sight.v0"].to_template()
        self.assertIsInstance(t, AgentTemplate)
        self.assertEqual(t.trust_tier, "herald_lumen")

    def test_shadow_embodied_vetoed(self):
        with self.assertRaises(HeraldContractError):
            HeraldContract("x", HeraldArchetype.SHADOW, "n", "o",
                           allowed_realms=frozenset({CognitiveRealm.EMBODIED}))

    def test_shadow_must_forbid_memory_write(self):
        with self.assertRaises(HeraldContractError):
            HeraldContract("x", HeraldArchetype.SHADOW, "n", "o",
                           allowed_realms=frozenset({CognitiveRealm.POSSIBILITY}),
                           forbidden_tools=frozenset())

    def test_grantable_strips_forbidden(self):
        granted = COURT_OF_HERALDS["h1.sight.v0"].grantable(["fs.read", "maritime.actuation"])
        self.assertIn("fs.read", granted)
        self.assertNotIn("maritime.actuation", granted)

    def test_registry_merges_heralds_additively(self):
        reg = herald_templates()
        self.assertEqual(len(reg), 6)
        for tid in COURT_OF_HERALDS:
            self.assertIn(tid, reg)


if __name__ == "__main__":
    unittest.main()
