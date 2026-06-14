"""GhostRuntime — a bounded, read-only virtual self-instance (v0: Level 0/1).

A ghost is forked by Orbi with a mission, a tool grant, an expiry, and a scratch
boundary. v0 implements the two safe levels the docs recommend first:

  * Level 0 — **prompt ghost**: no tools; returns a plan only.
  * Level 1 — **process ghost (inspection)**: read-only filesystem inspection of a
    provided allow-list of files; produces findings + merge candidates.

Hard rules (enforced here + by the gate):
  * The ghost may only use granted tools; any action beyond its grant is proposed to
    the PolicyGate, which denies it.
  * No writes, no network, no shell mutation in the inspection/simulation tiers.
  * The ghost **never auto-merges** — it emits MergeCandidate(accepted=False); ΦΔ /
    human decides. (Avoids self-reinforcing bias.)

Execution-tier ghosts (container/VM, level 2/3) are intentionally not built here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from ai_chi.orbi.policy_gate import GateDecision, PolicyGate
from ai_chi.orbi.schemas import ActionProposal, GhostInstanceRecord, MergeCandidate

# A gate-check callback the ghost must use for anything outside its grant.
GateCheck = Callable[[ActionProposal], GateDecision]


@dataclass
class GhostResult:
    ghost_id: str
    status: str                       # completed|denied|error
    findings: dict = field(default_factory=dict)
    merge_candidates: list[MergeCandidate] = field(default_factory=list)
    denied_actions: list[str] = field(default_factory=list)


class GhostRuntime:
    """Runs a bounded inspection/simulation ghost. Pure-Python, offline, read-only."""

    def __init__(self, instance: GhostInstanceRecord, gate_check: Optional[GateCheck] = None) -> None:
        self.instance = instance
        self.gate_check = gate_check
        self._steps = 0

    def _can(self, tool: str) -> bool:
        return tool in self.instance.allowed_tools and tool not in self.instance.forbidden_tools

    def _propose(self, action_type: str, target: str) -> GateDecision | None:
        """Route an out-of-grant action through the gate (it will deny in v0 tiers)."""
        if self.gate_check is None:
            return None
        proposal = ActionProposal(actor_id=self.instance.ghost_id, action_type=action_type,
                                  target=target, actor_role="ghost",
                                  provenance=[self.instance.ghost_id])
        return self.gate_check(proposal)

    def run_inspection(self, files: Optional[list[str]] = None) -> GhostResult:
        """Read-only inspection over an allow-list of files (Level 1), or plan (Level 0)."""
        result = GhostResult(ghost_id=self.instance.ghost_id, status="completed")

        # Level 0 — prompt ghost: no tools, return a plan only.
        if self.instance.level == 0 or self.instance.tier == "simulation":
            result.findings = {"plan": f"(sim) reason about: {self.instance.mission}",
                               "tools_used": []}
            result.merge_candidates.append(MergeCandidate(
                ghost_id=self.instance.ghost_id, kind="finding",
                content={"plan_only": True, "mission": self.instance.mission}))
            return result

        # Level 1 — inspection ghost: requires fs.read grant.
        if not self._can("fs.read"):
            # Try (and fail) through the gate to record the refusal honestly.
            self._propose("fs.read", "filesystem")
            result.status = "denied"
            result.denied_actions.append("fs.read (not granted)")
            return result

        inspected: dict[str, dict] = {}
        for fp in (files or [])[: self.instance.max_steps]:
            self._steps += 1
            p = Path(fp)
            try:
                text = p.read_text(encoding="utf-8", errors="replace")  # read-only
                inspected[p.name] = {
                    "lines": text.count("\n") + 1,
                    "bytes": len(text.encode("utf-8")),
                }
            except Exception as exc:  # never let a bad path kill the ghost
                inspected[str(fp)] = {"error": str(exc)}

        result.findings = {"inspected": inspected, "files": len(inspected),
                           "tools_used": ["fs.read"]}
        # Demonstrate containment: a write is outside grant -> gate denies it.
        wd = self._propose("fs.write", "any")
        if wd is not None and not wd.allowed:
            result.denied_actions.append(f"fs.write -> {wd.disposition.value}: {wd.reason}")

        result.merge_candidates.append(MergeCandidate(
            ghost_id=self.instance.ghost_id, kind="finding",
            content={"summary": f"inspected {len(inspected)} file(s)"}))
        return result
