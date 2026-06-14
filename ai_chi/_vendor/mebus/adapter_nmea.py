"""NMEA 0183 adapter — forward increment on MΣBUS v0.1 (roadmap adapter #1).

Maritime is the primary deployment context (Wibo 835 / Vento-Vivere), so the first
new membrane translator after the v0.1 foundation is NMEA 0183. It parses the two
position-bearing sentences the Observe layer needs first — GGA (fix) and RMC
(position + SOG/COG) — into typed maritime cognition (`m.state`, domain `maritime.nav`).

- Known sentence types  -> typed `m.state` with decimal-degree position.
- Unknown sentence types -> carried verbatim as `ext.nmea` (universal-carrier fallback).
- Checksum (when present) is validated; a mismatch raises MessageValidationError.

Same core inside, context-specific surface outside. Stdlib-only.
"""
from __future__ import annotations

from typing import Any

from .protocol import MMessage, Mode, MessageValidationError
from .adapter import Adapter, wrap_external

_TYPED = {"GGA", "RMC"}


def nmea_checksum(sentence: str) -> str:
    """XOR of all chars between '$' and '*'. Returns two-char uppercase hex."""
    body = sentence
    if body.startswith("$"):
        body = body[1:]
    if "*" in body:
        body = body.split("*", 1)[0]
    cs = 0
    for ch in body:
        cs ^= ord(ch)
    return f"{cs:02X}"


def _to_decimal(value: str, hemi: str) -> float | None:
    """ddmm.mmmm + hemisphere -> signed decimal degrees."""
    if not value:
        return None
    deg_len = 2 if hemi in ("N", "S") else 3
    degrees = int(value[:deg_len])
    minutes = float(value[deg_len:])
    dec = degrees + minutes / 60.0
    if hemi in ("S", "W"):
        dec = -dec
    return round(dec, 6)


class NMEAAdapter(Adapter):
    """Translate NMEA 0183 GGA/RMC sentences into typed maritime cognition (m.state)."""
    name = "nmea"

    def ingest(self, external: Any, *, mode: Mode = Mode.WAKE) -> MMessage:
        sentence = external.decode() if isinstance(external, (bytes, bytearray)) else str(external)
        sentence = sentence.strip()

        # Validate checksum when present.
        if "*" in sentence:
            body, _, given = sentence.partition("*")
            given = given.strip().upper()
            if given and given != nmea_checksum(body):
                raise MessageValidationError(
                    f"NMEA checksum mismatch: got *{given}, expected *{nmea_checksum(body)}"
                )
            fields = body.split(",")
        else:
            fields = sentence.split(",")

        head = fields[0]                       # e.g. "$GPRMC"
        stype = head[3:] if len(head) >= 6 else head.lstrip("$")

        if stype not in _TYPED:
            # Universal carrier: unknown sentence crosses the bus intact.
            return wrap_external("nmea", {"sentence": sentence, "type": stype}, mode=mode)

        lat = lon = sog = cog = fix = None
        if stype == "GGA":
            lat = _to_decimal(fields[2], fields[3]) if len(fields) > 5 else None
            lon = _to_decimal(fields[4], fields[5]) if len(fields) > 5 else None
            fix = int(fields[6]) if len(fields) > 6 and fields[6] else None
        elif stype == "RMC":
            lat = _to_decimal(fields[3], fields[4]) if len(fields) > 6 else None
            lon = _to_decimal(fields[5], fields[6]) if len(fields) > 6 else None
            sog = float(fields[7]) if len(fields) > 7 and fields[7] else None
            cog = float(fields[8]) if len(fields) > 8 and fields[8] else None

        value: dict = {"latitude": lat, "longitude": lon}
        if sog is not None:
            value["sog_knots"] = sog
        if cog is not None:
            value["cog_deg"] = cog
        if fix is not None:
            value["fix_quality"] = fix

        return MMessage(
            sigma="m.state",
            payload={"path": "navigation.position", "value": value, "nmea_type": stype},
            destination="urbi", mode=mode,
            context={"provenance": [f"nmea.{stype.lower()}"], "domain": "maritime.nav", "raw": sentence},
        ).validate()

    def emit(self, msg: MMessage) -> str:
        raw = msg.context.get("raw")
        if raw:
            return raw
        sentence = msg.payload.get("sentence")
        if sentence:
            return sentence
        raise MessageValidationError("NMEAAdapter.emit: no raw sentence retained to re-emit")
