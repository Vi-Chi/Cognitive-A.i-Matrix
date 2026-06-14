"""Redaction helpers for generated graveyard indexes.

The graveyard tools may scan cold backup text. Secret-shaped material must be
treated as toxic and replaced before it reaches a report, SQLite index, or
terminal output.
"""
from __future__ import annotations

import re
from pathlib import Path


REDACTED_SECRET = "<REDACTED_SECRET>"
REDACTED_ASSIGNMENT = "<REDACTED>"
REDACTED_EMAIL = "<REDACTED_EMAIL>"

# PII patterns — redacted in place (privacy-first), NOT added to SECRET_PATTERNS, so an
# email does not trip the fail-closed secret block; the doc still indexes, with the
# personal contact scrubbed. (Privacy analog of the secret redaction; P-G1 fix.)
PII_PATTERNS = (
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
)

SECRET_PATTERNS = (
    re.compile(r"\bsk(?:-[A-Za-z0-9][A-Za-z0-9_-]{7,})+\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\b(?:ghp_|github_pat_)[0-9A-Za-z_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"https://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9._-]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{10,}"),
)

SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|token|secret|password|credential|webhook|authorization)\b"
    r"\s*[:=]\s*([\"']?)([^\s,\"']+)"
)

SAFE_ASSIGNMENT_VALUES = {
    REDACTED_SECRET.lower(),
    REDACTED_ASSIGNMENT.lower(),
    "<redacted>".lower(),
    "none",
    "null",
    "false",
    "true",
    "required",
    "optional",
    "missing",
    "present",
    "not_requested",
    "redacted",
    "placeholder",
    "example",
}

SENSITIVE_PATH_MARKERS = (
    ".env",
    ".env.",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "auth_token",
    "credentials",
    "credential",
    "oauth",
    "private_key",
    "private-key",
    "service-account",
    "service_account",
    "vapid-keys",
    "webhook",
)

SENSITIVE_EXACT_PARTS = {".env", ".secrets", "secrets", "credentials", "credential"}


def _looks_like_assignment_secret(value: str) -> bool:
    candidate = value.strip().strip("\"'")
    lowered = candidate.lower()
    if not candidate or lowered in SAFE_ASSIGNMENT_VALUES:
        return False
    if candidate.startswith("{") and candidate.endswith("}"):
        return False
    if lowered.startswith("<redacted") or lowered.startswith("redacted_"):
        return False
    if any(pattern.search(candidate) for pattern in SECRET_PATTERNS):
        return True
    if len(candidate) < 8:
        return False
    return (
        len(candidate) >= 16
        or any(ch.isdigit() for ch in candidate)
        or any(ch in candidate for ch in "._~+/=-")
    )


def _redact_assignment(match: re.Match[str]) -> str:
    if not _looks_like_assignment_secret(match.group(3)):
        return match.group(0)
    return f"{match.group(1)}={REDACTED_ASSIGNMENT}"


def redact_sensitive_text(value: object) -> str:
    """Return text with secret-shaped values replaced by generic markers."""
    text = "" if value is None else str(value)
    text = SECRET_ASSIGNMENT_RE.sub(_redact_assignment, text)
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(REDACTED_SECRET, text)
    for pattern in PII_PATTERNS:
        text = pattern.sub(REDACTED_EMAIL, text)
    return text


def contains_secret_shape(value: object) -> bool:
    """Return True when text contains a known raw secret shape."""
    text = "" if value is None else str(value)
    for match in SECRET_ASSIGNMENT_RE.finditer(text):
        assigned = match.group(3)
        if _looks_like_assignment_secret(assigned):
            return True
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def is_sensitive_path(path: Path | str) -> bool:
    """Identify likely credential files before opening them."""
    raw_parts = Path(path).parts if not isinstance(path, Path) else path.parts
    parts = [part.lower() for part in raw_parts]
    if any(part in SENSITIVE_EXACT_PARTS for part in parts):
        return True
    lowered = "/".join(parts)
    return any(marker in lowered for marker in SENSITIVE_PATH_MARKERS)
