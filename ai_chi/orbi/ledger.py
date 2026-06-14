"""OrbiLedger — the core LedgerWriter extended with Orbi execution streams.

Non-invasive (like AidictLedger): the verified `core/ledger/writer.py` is untouched.
Every spawn, grant, action, and ghost event is appended to the black-box so the
full execution history is auditable — a constitutional requirement (Orbi writes the
ledger; nothing it does is unlogged).
"""
from __future__ import annotations

from ai_chi.core.ledger import LedgerWriter
from ai_chi.orbi import sigma as S


class OrbiLedger(LedgerWriter):
    """LedgerWriter with Orbi execution-record streams registered."""

    ORBI_ROUTES: dict[str, str] = {
        S.SIGMA_SPAWN_REQUEST: "spawns.jsonl",
        S.SIGMA_SPAWN_APPROVED: "spawns.jsonl",
        S.SIGMA_SPAWN_DENIED: "spawns.jsonl",
        S.SIGMA_INSTANCE_STARTED: "spawns.jsonl",
        S.SIGMA_INSTANCE_CLOSED: "spawns.jsonl",
        S.SIGMA_TOOL_GRANT: "grants.jsonl",
        S.SIGMA_TOOL_REVOKED: "grants.jsonl",
        S.SIGMA_ACTION_PROPOSAL: "actions.jsonl",
        S.SIGMA_ACTION_RESULT: "actions.jsonl",
        S.SIGMA_GHOST_SPAWN: "ghosts.jsonl",
        S.SIGMA_GHOST_SNAPSHOT: "ghosts.jsonl",
        S.SIGMA_GHOST_PLAN: "ghosts.jsonl",
        S.SIGMA_GHOST_ACTION: "actions.jsonl",
        S.SIGMA_GHOST_RESULT: "ghosts.jsonl",
        S.SIGMA_GHOST_TERMINATED: "ghosts.jsonl",
        S.SIGMA_GHOST_MERGE_CANDIDATE: "merge_candidates.jsonl",
        S.SIGMA_GHOST_REJECTED_MERGE: "merge_candidates.jsonl",
        S.SIGMA_A2A_TASK_REQUEST: "actions.jsonl",
        S.SIGMA_A2A_ARTIFACT: "actions.jsonl",
    }

    ROUTE_MAP = {**LedgerWriter.ROUTE_MAP, **ORBI_ROUTES}
    STREAMS = LedgerWriter.STREAMS + (
        "spawns.jsonl",
        "grants.jsonl",
        "actions.jsonl",
        "ghosts.jsonl",
        "merge_candidates.jsonl",
    )
