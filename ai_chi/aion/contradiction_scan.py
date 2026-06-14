"""Contradiction scanner (AIONCM section 16 / task 4, P0).

Detects, without acting:
  * allowed_use / forbidden_use overlap in a contract
  * a symbolic-source pattern being promoted to action
  * missing provenance for a pattern claiming >= STRUCTURAL evidence
  * a target module/contract requiring a higher transfer level than the pattern
"""
from __future__ import annotations

from dataclasses import dataclass

from .ontology import EvidenceLevel, is_symbolic
from .schema import AIONPattern, AIONContract


@dataclass
class Contradiction:
    code: str
    detail: str


class ContradictionScanner:
    def scan(self, pattern: AIONPattern, contract: AIONContract = None):
        found = []

        if pattern.evidence_level >= EvidenceLevel.STRUCTURAL and not pattern.source_refs:
            found.append(Contradiction(
                "missing_provenance",
                f"evidence {pattern.evidence_level.label} with no source_refs",
            ))

        if is_symbolic(pattern.domains) and (
            pattern.action_allowed or (contract and contract.world_action_allowed)
        ):
            found.append(Contradiction(
                "symbolic_to_action",
                f"symbolic domain {pattern.domains} routed toward world action",
            ))

        if contract is not None:
            overlap = set(map(str, contract.allowed_use)) & set(map(str, contract.forbidden_use))
            if overlap:
                found.append(Contradiction(
                    "allowed_forbidden_overlap",
                    f"uses in both allowed and forbidden: {sorted(overlap)}",
                ))
            if contract.required_transfer_level > pattern.transfer_level:
                found.append(Contradiction(
                    "transfer_too_low",
                    f"contract needs {contract.required_transfer_level.name} but "
                    f"pattern is at {pattern.transfer_level.name}",
                ))
            if contract.required_evidence_level > pattern.evidence_level:
                found.append(Contradiction(
                    "evidence_too_low",
                    f"contract needs {contract.required_evidence_level.label} but "
                    f"pattern is {pattern.evidence_level.label}",
                ))

        return found
