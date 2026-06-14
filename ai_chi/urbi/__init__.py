"""Urbi adapters — deterministic judgment primitives + the canonical audit signal.

The Core Validator ("Lens proposes, Core disposes"), the 3-6-9 audit kernel, the
proof-carrying UrbiAuditSignal (URBI_369 §11.2), and the UrbiAuditor that ties them
into one emittable kernel. All carry the Urbi invariant: action_allowed = False.
"""
from ai_chi.urbi.core_validator import (
    validate_urbi_audit_signal, force_veto, preserve_uncertainty,
    UrbiAuditSignal as LensAuditSignal, VALID_EPISTEMIC_STATES,
)
from ai_chi.urbi.audit_369 import AuditInput, AuditResult, Urbi369Audit
from ai_chi.urbi.audit_signal import UrbiAuditSignal, AuditSignalError
from ai_chi.urbi.auditor import UrbiAuditor, SIGMA_AUDIT

__all__ = [
    "validate_urbi_audit_signal", "force_veto", "preserve_uncertainty",
    "VALID_EPISTEMIC_STATES", "LensAuditSignal",
    "AuditInput", "AuditResult", "Urbi369Audit",
    "UrbiAuditSignal", "AuditSignalError",
    "UrbiAuditor", "SIGMA_AUDIT",
]
