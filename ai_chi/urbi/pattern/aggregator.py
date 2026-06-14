# aicore/urbi/pattern/aggregator.py
# -------------------------------------------------------------------------
# Φ_AGG: Cross-Agent Disagreement Matrix / The Pattern Subsystem
# Goal: Never average outputs. Map Pairwise-Friction & output variance as the cognitive cue.
# -------------------------------------------------------------------------
import logging
from typing import Dict, List, Tuple

# Pure MΣBUS constraint implementations imported naturally
from ai_chi.bus import MembraneBus, MMessage, monotonic_tau, Mode

from ai_chi.urbi.pattern.agents import (
    PhiCorAgent, PhiStaAgent, PhiDisAgent, PhiStrAgent, PhiLeaAgent
)

class PhiAggregator:
    def __init__(self, bus: MembraneBus):
        self.bus = bus
        self.agents = [
            PhiCorAgent(), PhiStaAgent(), PhiDisAgent(), 
            PhiStrAgent(), PhiLeaAgent()
        ]
        
        # Subscribes to MΣBUS Intake Streams naturally checking observational reality:
        self.bus.subscribe("ext.observation", self._on_raw_observation)
        
    def _on_raw_observation(self, msg: MMessage):
        """Cross-correlates external reality across all diverse geometric models simultaneously."""
        payload = msg.payload if isinstance(msg.payload, dict) else msg.payload.get("raw_data", str(msg.payload))
        target_str = str(payload.get("raw_data", payload)) if isinstance(payload, dict) else payload

        results: Dict[str, Tuple[float, float]] = {
            a.identifier: a.process_feature(target_str) for a in self.agents
        }
        
        # Construct the Matrix evaluating internal subsystem failure-correlation (pairwise)
        identifiers = list(results.keys())
        size = len(identifiers)
        disagreement_matrix = [[0.0] * size for _ in range(size)]
        
        systemic_friction_sum = 0.0
        comparisons = 0

        for i, source in enumerate(identifiers):
            val_a, conf_a = results[source]
            for j, dest in enumerate(identifiers):
                if i == j:
                    disagreement_matrix[i][j] = 0.0  # Perfect baseline zero disagreement with self
                    continue
                    
                val_b, conf_b = results[dest]
                
                # Pairwise Variance heavily emphasized when Confidences hold highly contrary outputs 
                friction = abs(val_a - val_b) * (conf_a * conf_b)
                disagreement_matrix[i][j] = round(friction, 3)

                if j > i: # Uniq evaluations tracked structurally only
                    systemic_friction_sum += friction
                    comparisons += 1
        
        overall_discordance = systemic_friction_sum / comparisons if comparisons > 0 else 0.0

        # Construct specific 'evidence' layer geometry avoiding payload flattening / standard "AI prompt averages" 
        payload_frame = {
            "origin": "Φ_AGG_MATRIX",
            "evaluated_agents": identifiers,
            "raw_agent_scalars": results,
            "covariance_divergence_matrix": disagreement_matrix, 
            "friction_tensor": round(overall_discordance, 4)
        }

        # Issue Output exactly bound by Built API variables - integers over versions, strict Monotonic causal ns checks
        agg_msg = MMessage(
            version=1,
            sigma="m.evidence", # Emits explicit contextual matrix maps. Never commands actuation 
            payload=payload_frame,
            destination="urbi.core.auditor",
            context={"calibrated_friction_threshold": overall_discordance},
            tau=monotonic_tau(),
            mode=Mode.WAKE      
        )

        # Single Argument push executing flawlessly against MEBUS Protocol
        self.bus.publish(agg_msg)

        if overall_discordance > 0.40:
            logging.info(f"Φ_AGG Matrix Friction high ({overall_discordance:.2f}). Pushing raw epistemic discord out!")