"""Urbi <-> MΣBUS bridge package.

Wires the running v2.1 tri-state 3-6-9 auditor onto the built MΣBUS membrane so Urbi (Yin /
3-6-9, audits-never-acts) emits audited belief on the same wire as Orbi (Yang / 2-4-6-8).
"""
from .bridge import UrbiMebusBridge
from .endpoint import resolve_ollama_base, apply_to_auditor
from .inv import gate_emit, InvViolation, OMEGA

__all__ = [
    "UrbiMebusBridge",
    "resolve_ollama_base",
    "apply_to_auditor",
    "gate_emit",
    "InvViolation",
    "OMEGA",
]
