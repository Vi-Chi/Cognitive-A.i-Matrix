"""OrbiExecutor — the dumb terminal that executes validated ActionProposals.

The executor itself possesses zero judgment. It is a dumb terminal that only fires
if it receives a mathematically valid UrbiAuditSignal endorsing the action (via the PolicyGate).
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Optional

from ai_chi.bus import Mode
from ai_chi.orbi.schemas import ActionProposal, ActionResult
from ai_chi.orbi.policy_gate import PolicyGate, GateDecision, Disposition

# Hardcoded exclusion zones (fail-safe)
_RESTRICTED_TARGETS = {
    "/opt/omni-ai",
    "/etc",
    "/dev",
    "/boot",
    "docker",
    "pixhawk",
    "can0",
    "can1",
    "~/.ssh",
    ".ssh",
    ".env",
    "network",
    "0.0.0.0",
    "/sys",
    "/proc"
}

class ExecutionError(RuntimeError):
    pass

class OrbiExecutor:
    """The final mile of the Orbi action plane."""

    def __init__(self, policy_gate: PolicyGate) -> None:
        self.policy_gate = policy_gate
        self._handlers: Dict[str, Callable[[ActionProposal], Any]] = {
            "fs.read": self._handle_fs_read,
            "fs.write": self._handle_fs_write,
            "shell.run": self._handle_shell_run,
        }

    def _restricted_strings(self, value: Any) -> Iterable[str]:
        if value is None:
            return
        if isinstance(value, dict):
            for key, item in value.items():
                yield str(key)
                yield from self._restricted_strings(item)
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                yield from self._restricted_strings(item)
            return
        if isinstance(value, (str, int, float, bool)):
            yield str(value)

    def _is_restricted_target(self, target: str) -> bool:
        """Enforces the STOP-GATED hardware and root mutation exclusions."""
        if not target:
            return False
        lower_target = target.lower()
        for restricted in _RESTRICTED_TARGETS:
            if restricted in lower_target:
                return True
        return False

    def _restricted_surface(self, proposal: ActionProposal) -> Optional[str]:
        if self._is_restricted_target(proposal.target):
            return "target"
        for value in self._restricted_strings(proposal.args):
            if self._is_restricted_target(value):
                return "args"
        return None

    def execute(
        self,
        proposal: ActionProposal,
        *,
        mode: Mode = Mode.WAKE,
        audit_signal: str,
        trust: float = 1.0,
        human_approved: bool = False
    ) -> ActionResult:
        """Gate check and execute the proposal."""
        decision: GateDecision = self.policy_gate.evaluate(
            proposal,
            mode=mode,
            audit_signal=audit_signal,
            trust=trust,
            human_approved=human_approved
        )

        if not decision.allowed:
            return ActionResult(
                proposal_id=proposal.proposal_id,
                status=decision.disposition.value,
                disposition_reason=decision.reason
            )

        restricted_surface = self._restricted_surface(proposal)
        if restricted_surface:
            return ActionResult(
                proposal_id=proposal.proposal_id,
                status="error",
                disposition_reason=f"Action {restricted_surface} are restricted by constitutional exclusion zones."
            )

        handler = self._handlers.get(proposal.action_type)
        if not handler:
            return ActionResult(
                proposal_id=proposal.proposal_id,
                status="error",
                disposition_reason=f"Unsupported action_type: {proposal.action_type}"
            )

        try:
            output = handler(proposal)
            return ActionResult(
                proposal_id=proposal.proposal_id,
                status="executed",
                disposition_reason=decision.reason,
                output=output if isinstance(output, dict) else {"result": output}
            )
        except Exception as e:
            return ActionResult(
                proposal_id=proposal.proposal_id,
                status="error",
                disposition_reason=f"Execution failed: {type(e).__name__}: {str(e)}"
            )

    def _handle_fs_read(self, proposal: ActionProposal) -> Any:
        """Simulated fs read."""
        return {"content": f"simulated read of {proposal.target}"}

    def _handle_fs_write(self, proposal: ActionProposal) -> Any:
        """Simulated fs write."""
        return {"bytes_written": len(str(proposal.args.get("content", "")))}

    def _handle_shell_run(self, proposal: ActionProposal) -> Any:
        """Simulated shell run with SafeShellValidator gating."""
        command = proposal.target
        if "command" in proposal.args:
            command = proposal.args["command"]
            
        from ai_chi.orbi.safe_shell import SafeShellValidator
        validator = SafeShellValidator()
        result = validator.validate(command)
        
        if not result.allowed:
            raise ExecutionError(f"Command failed safety validation: {result.reason}")
            
        return {"stdout": f"simulated execution of safe command: {command}", "stderr": "", "returncode": 0}
