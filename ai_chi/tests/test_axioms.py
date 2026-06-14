"""The 12 Axioms of Omni — the constitutional floor, tested as canon.

These tests turn the floor from declared data into an enforced invariant: it must
have exactly 12 axioms across four faces, be structurally immutable, be read-only,
and every axiom must trace to the built code that enforces it.
"""
import dataclasses
import unittest

from ai_chi.core import axioms as ax


class TestTheFloor(unittest.TestCase):
    def test_exactly_twelve_axioms(self):
        self.assertEqual(len(ax.AXIOMS), 12)
        self.assertEqual(sorted(a.id for a in ax.AXIOMS), list(range(1, 13)))

    def test_four_faces_three_each(self):
        groups = {f: ax.by_face(f) for f in ax.FACES}
        self.assertEqual({f: len(g) for f, g in groups.items()},
                         {"I": 3, "II": 3, "III": 3, "IV": 3})
        # face IV is the hidden, load-bearing base: axioms 10, 11, 12
        self.assertEqual([a.id for a in groups["IV"]], [10, 11, 12])

    def test_axioms_are_immutable(self):
        a = ax.by_id(1)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            a.statement = "tampered"  # type: ignore[misc]

    def test_floor_is_read_only_and_architect_owned(self):
        self.assertTrue(ax.floor_is_read_only())
        self.assertIn("ViChi", str(ax.THE_FLOOR.get("modifiable_by", "")))

    def test_every_axiom_traces_to_enforcing_code(self):
        for a in ax.AXIOMS:
            self.assertIn(a.id, ax.AXIOM_ENFORCEMENT)
            self.assertTrue(ax.enforcement_for(a.id).strip())

    def test_load_bearing_axioms_present(self):
        # axioms that map directly onto already-built invariants
        self.assertEqual(ax.by_id(4).statement, "The = state is the ground condition")
        self.assertEqual(ax.by_id(10).statement,
                         "The authentication layer operates outside the generative loop")

    def test_verify_floor(self):
        self.assertTrue(ax.verify_floor())


if __name__ == "__main__":
    unittest.main()
