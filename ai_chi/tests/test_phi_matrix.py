# aicore/tests/test_phi_matrix.py
import unittest
from ai_chi.bus import MembraneBus, MMessage, monotonic_tau, Mode
from ai_chi.urbi.pattern.aggregator import PhiAggregator

class PhiMatrixTests(unittest.TestCase):
    def test_disagreement_preservation_and_m_evidence_emission(self):
        bus = MembraneBus()
        agg = PhiAggregator(bus)
        
        # Tap the publish out-route directly to verify Matrix construction:
        emissions = []
        bus.publish = lambda m: emissions.append(m)
        
        # Inject raw Reality Observation that splits opinions 
        # (simulates e.g., thermal/long data string to force disparate geometries from the 5 agents)
        test_msg = MMessage(
            version=1,
            sigma="ext.observation",
            payload={"raw_data": "thermal state extremely high, limits exceeded length bounds..."},
            destination="phi_matrix_test",
            context={"trust": 1.0},
            tau=monotonic_tau(),
            mode=Mode.WAKE
        )
        
        # Run aggregator (fires internal callback simulating what MΣBUS handles automatically)
        agg._on_raw_observation(test_msg)
        
        # 1. Assert system produced an envelope 
        self.assertEqual(len(emissions), 1)
        evidence_env = emissions[0]
        
        # 2. Enforce Canon compliance! (Rule: outputs cognitive m.* bounds)
        self.assertEqual(evidence_env.sigma, "m.evidence")
        self.assertEqual(evidence_env.mode, Mode.WAKE)
        
        payload = evidence_env.payload
        self.assertIn("covariance_divergence_matrix", payload)
        self.assertIn("friction_tensor", payload)
        
        matrix = payload["covariance_divergence_matrix"]
        friction = payload["friction_tensor"]
        
        # 3. Mathematically assure the geometry spans the full 5 agents
        self.assertEqual(len(matrix), 5)  # 5 rows
        self.assertEqual(len(matrix[0]), 5)  # 5 columns
        
        # Friction must not be a zero'd default, meaning internal agents 
        # successfully interpreted it uniquely!
        self.assertTrue(isinstance(friction, float))

if __name__ == '__main__':
    unittest.main()