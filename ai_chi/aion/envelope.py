"""MΣBUS envelope adapter — M := (v, σ, π, δ, κ, τ).

AION records ride the bus as payloads. No raw action payload may be accepted
without σ (class), κ (provenance/trust), and a causal parent in τ. The bus
transports and enforces; it does NOT invent an Urbi verdict (acceptance test 7).
"""
from __future__ import annotations

import time


class EnvelopeError(Exception):
    pass


def wrap(sigma: str, pi: dict, *, delta: dict = None, kappa: dict = None,
         tau: dict = None, v: int = 1) -> dict:
    return {
        "v": v,
        "sigma": sigma,
        "pi": pi,
        "delta": delta or {},
        "kappa": kappa or {},
        "tau": tau or {"created_at": time.time(), "causal_parent": None},
    }


# Verdict authority belongs to Urbi alone. The bus may carry a verdict that Urbi
# produced, but may not originate one.
_AUDIT_KEYS = ("audit_verdict", "urbi_verdict", "verdict")


def require_action_envelope(env: dict) -> None:
    """Raise unless an action-class envelope carries σ, κ-provenance and causal parent."""
    if not env.get("sigma"):
        raise EnvelopeError("missing sigma (class)")
    kappa = env.get("kappa") or {}
    if "provenance" not in kappa and "trust" not in kappa:
        raise EnvelopeError("action payload requires kappa provenance/trust")
    tau = env.get("tau") or {}
    if tau.get("causal_parent") in (None, ""):
        raise EnvelopeError("action payload requires a causal parent in tau")


def assert_no_invented_verdict(env: dict) -> None:
    """The bus must not originate an Urbi verdict (acceptance test 7).

    A verdict may ride the envelope only if kappa names urbi as its authority.
    """
    pi = env.get("pi") or {}
    carries = any(k in pi for k in _AUDIT_KEYS)
    if not carries:
        return
    authority = (env.get("kappa") or {}).get("verdict_authority")
    if str(authority).lower() != "urbi":
        raise EnvelopeError(
            "envelope carries an audit verdict without urbi authority — "
            "MΣBUS cannot invent an Urbi verdict"
        )
