"""The 12 Axioms of Omni — the constitutional floor, made executable.

Reverse-engineered from `axioms.json` (architect: ViChi; "the floor that prevents
the fall"). The JSON is the canonical, architect-editable data; this module loads it
**read-only and immutable** (frozen dataclasses — "nothing overwrites this") and maps
each axiom to the built code/invariant that enforces it, so the floor is traceable to
the gates, not just declared.

Faces: I Identity/Ground (1–3) · II Epistemology/Trust (4–6) · III Structure/Time
(7–9) · IV The Hidden Base — load-bearing, invisible in operation (10–12).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_AXIOMS_PATH = Path(__file__).resolve().parent / "axioms.json"
FACES = ("I", "II", "III", "IV")


@dataclass(frozen=True)
class Axiom:
    id: int
    face: str
    domain: str
    statement: str
    edge_1: str
    edge_2: str
    synthesis: str


def _load():
    data = json.loads(_AXIOMS_PATH.read_text(encoding="utf-8"))
    axioms = tuple(
        Axiom(id=a["id"], face=a["face"], domain=a["domain"], statement=a["statement"],
              edge_1=a["edge_1"], edge_2=a["edge_2"], synthesis=a["synthesis"])
        for a in data["axioms"]
    )
    return data["_meta"], axioms, dict(data["the_floor"])


META, AXIOMS, THE_FLOOR = _load()

# Traceability: each axiom -> the built invariant / module that enforces it.
# This is what makes the floor *executable* rather than merely declared.
AXIOM_ENFORCEMENT: dict[int, str] = {
    1:  "non-anthropomorphic core; identity-as-process (geometry/causality inside, language at the membrane)",
    2:  "MΣBUS envelope encodes structure before expression — cognition rides in π",
    3:  "observer-in-loop — audit changes the system; PredictionRecord + out-of-loop CAL/Ω₄",
    4:  "the [=] suspended state is first-class — urbi/audit_369, UrbiAuditSignal, tri-state",
    5:  "trust earned, not declared — agents start neutral (Omni/AION origin UNKNOWN; AION promotion ladder)",
    6:  "both edges evaluated — [+] and [-]; contradiction_scan, tri-state audit",
    7:  "base holds while apex emerges — gates are the base; the RADAR layer grows from them",
    8:  "past/present/future as three faces — CM-Realm ARCHIVE/EMBODIED/POSSIBILITY (bus/realms.py)",
    9:  "meaning+purpose — a claim earns [+] only with both (audit reason_code + required_evidence)",
    10: "auth outside the generative loop — Urbi 3-6-9 out-of-loop; separation of powers; ∂Ξ/∂K=0",
    11: "compression preserves structure — BUILT: urbi/dream PRESERVE_OUTLIER (Divergence Preservation); quarantine seals, never deletes",
    12: "the scale never tips — BUILT: urbi/dream Simulacrum detector flags self-confirmation; no [+] accumulation; fail-closed gates",
}


def by_id(axiom_id: int) -> Axiom:
    for a in AXIOMS:
        if a.id == axiom_id:
            return a
    raise KeyError(f"no axiom {axiom_id}")


def by_face(face: str) -> tuple[Axiom, ...]:
    return tuple(a for a in AXIOMS if a.face == face)


def floor_is_read_only() -> bool:
    return bool(THE_FLOOR.get("read_only"))


def enforcement_for(axiom_id: int) -> str:
    return AXIOM_ENFORCEMENT[axiom_id]


def verify_floor() -> bool:
    """Assert the floor is intact: 12 axioms, four faces, read-only, fully traced."""
    if len(AXIOMS) != 12:
        raise AssertionError(f"expected 12 axioms, got {len(AXIOMS)}")
    if {a.face for a in AXIOMS} != set(FACES):
        raise AssertionError("axiom faces must be exactly I, II, III, IV")
    if THE_FLOOR.get("read_only") is not True:
        raise AssertionError("the floor must be read_only")
    missing = [a.id for a in AXIOMS if a.id not in AXIOM_ENFORCEMENT]
    if missing:
        raise AssertionError(f"axioms without an enforcement trace: {missing}")
    return True
