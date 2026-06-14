"""PolicyGate — the constitutional enforcer of the Urbi · Orbi · MΣBUS balance.

Every world-touching Orbi action passes through here. The gate is **fail-safe by
default**: an action is denied unless *all* conditions are positively met. This is
the code embodiment of the Balance Constitution:

  * Action monopoly      — Urbi may not act; only agent/ghost/orbi roles may propose.
  * Audit-before-action  — an Urbi audit signal must exist; absence = deny (fail-safe).
  * Ω₈ (μ gate)          — world-touching actions are suppressed when μ = DREAM.
  * Trust floor          — effective trust below the floor is denied.
  * Provenance           — no provenance, no action.
  * Human gate           — high/critical risk or explicit flag holds for a human.

"Loss of the auditor fails safe (stop), never fail-open." (constitution §5)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from ai_chi.bus import Mode, TRUST_FLOOR, clamp
from ai_chi.bus.realms import realm_action_gate
from ai_chi.orbi.schemas import ActionProposal

# Urbi tri-state -> audit signal (mirror of AIDICT's mapping; the gate reads signals).
SUPPORT = "audit_support_signal"
CONTRADICTION = "audit_contradiction_signal"
SUSPENDED = "audit_suspended"
PENDING = "pending"

_HIGH_RISK = {"high", "critical"}
# Roles that may propose actions. Urbi is deliberately absent — it holds judgment,
# never action (separation of powers).
_ACTOR_ROLES = {"orbi", "agent", "ghost"}


class Disposition(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    SUSPEND = "suspend"          # genuinely unresolved [=] — no action, route onward
    NEEDS_HUMAN = "needs_human"  # held for human approval


@dataclass(frozen=True)
class GateDecision:
    disposition: Disposition
    reason: str
    proposal_id: str

    @property
    def allowed(self) -> bool:
        return self.disposition is Disposition.ALLOW


class PolicyGate:
    """Decides whether a proposed world-touching action may proceed."""

    def __init__(
        self,
        *,
        trust_floor: float = TRUST_FLOOR,
        autopoiesis_ledger: Optional[Any] = None,
    ) -> None:
        self.trust_floor = trust_floor
        self.autopoiesis_ledger = autopoiesis_ledger
        self.last_metering_error: Optional[str] = None

    @classmethod
    def with_local_autopoiesis_ledger(
        cls,
        storage_dir: str | Path,
        *,
        trust_floor: float = TRUST_FLOOR,
    ) -> "PolicyGate":
        """Create a PolicyGate that records local Autopoiesis ComputeReceipts."""
        from ai_chi.bus.transports.file_transport import FileBackedSigmaTransport
        from ai_chi.core.ledger.autopoiesis_ledger import AutopoiesisLedger

        transport = FileBackedSigmaTransport(storage_dir)
        return cls(
            trust_floor=trust_floor,
            autopoiesis_ledger=AutopoiesisLedger(transport),
        )

    def _record_metering(self, proposal: ActionProposal, decision: GateDecision) -> None:
        if self.autopoiesis_ledger is None:
            return
        try:
            self.autopoiesis_ledger.meter_action(proposal, decision.allowed)
            self.last_metering_error = None
        except Exception as exc:  # pragma: no cover - defensive passive interceptor
            self.last_metering_error = f"{type(exc).__name__}: {exc}"

    def evaluate(
        self,
        proposal: ActionProposal,
        *,
        mode: Mode = Mode.WAKE,
        audit_signal: str = PENDING,
        trust: float = 1.0,
        human_approved: bool = False,
        economic_audit_signal: Optional[dict[str, Any]] = None,
    ) -> GateDecision:
        pid = proposal.proposal_id

        def deny(reason: str) -> GateDecision:
            return GateDecision(Disposition.DENY, reason, pid)

        def finish(decision: GateDecision) -> GateDecision:
            self._record_metering(proposal, decision)
            return decision

        # 1. Action monopoly — Urbi (or anything not an actor role) cannot act.
        role = (proposal.actor_role or "").lower()
        if role not in _ACTOR_ROLES:
            return finish(deny(f"action monopoly: role '{proposal.actor_role}' may not propose actions"))

        # 2. Provenance — no provenance, no action.
        if not (proposal.provenance or proposal.actor_id):
            return finish(deny("no provenance"))

        # 3. Ω₈ — world-touching actions are suppressed in DREAM.
        if mode is Mode.DREAM:
            return finish(deny("Ω₈: action layer suppressed in DREAM"))

        # 3b. Realm boundary (CM-Realm) — a POSSIBILITY/EXTERNAL claim, or a severe
        # contamination, may not drive a world action. Backward-compatible: if the
        # proposal declares no realm in its args, this is a no-op.
        realm_ok, realm_reason = realm_action_gate(proposal.args, is_action=True)
        if not realm_ok:
            return finish(deny(realm_reason))

        # 4. Trust floor.
        if clamp(float(trust)) < self.trust_floor:
            return finish(deny(f"trust {clamp(float(trust)):.2f} below floor {self.trust_floor:.2f}"))

        # 5. Audit-before-action (the heart). Default-deny on missing/unknown audit.
        # Apply economic reducer logic.
        sig = (audit_signal or PENDING).lower()
        needs_human_elevated = False

        if economic_audit_signal:
            eco_verdict = economic_audit_signal.get("verdict", "pending").lower()
            if eco_verdict in ("contradiction", "suspended", "pending"):
                # Economic audit can fail-safe lower the trust of the primary audit
                if eco_verdict == "contradiction":
                    sig = CONTRADICTION
                elif eco_verdict == "suspended" and sig != CONTRADICTION:
                    sig = SUSPENDED
                elif eco_verdict == "pending" and sig not in (CONTRADICTION, SUSPENDED):
                    sig = PENDING

            eco_constraint = economic_audit_signal.get("recommended_constraint", "none").lower()
            if eco_constraint == "deny":
                return finish(deny("Economic audit constraint: deny"))
            if eco_constraint == "defer":
                return finish(GateDecision(Disposition.SUSPEND, "Economic audit constraint: defer", pid))
            if eco_constraint in ("require_human_approval", "require_security_review", "require_legal_review"):
                needs_human_elevated = True

        if sig == CONTRADICTION:
            return finish(deny("Urbi veto: audit_contradiction_signal"))
        if sig == SUSPENDED:
            return finish(GateDecision(Disposition.SUSPEND, "Urbi [=] suspended: insufficient evidence", pid))
        if sig != SUPPORT:
            # pending / unknown / auditor offline -> fail safe
            return finish(deny(f"no Urbi support signal (got '{audit_signal}') — fail-safe stop"))

        # 6. Human gate for high-risk or explicitly flagged actions.
        if (proposal.risk_level in _HIGH_RISK or proposal.requires_human_approval or needs_human_elevated) \
                and not human_approved:
            return finish(GateDecision(Disposition.NEEDS_HUMAN,
                                       f"risk={proposal.risk_level} or economic flag requires human approval", pid))

        return finish(GateDecision(Disposition.ALLOW, "audit-support + trust + mode + provenance ok", pid))
