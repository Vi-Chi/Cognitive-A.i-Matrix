"""SQLite append-only provenance ledger (AIONCM task 5, P0).

Stores patterns, instances, mappings, contracts, audits, and promotion attempts.
Audits and promotion attempts are APPEND-ONLY — no UPDATE, no DELETE — so the
record of every decision (including denied ones) is preserved. This mirrors the
Cognitive Matrix rule "rollback is allowed, erasure is forbidden".

sqlite3 only. Default path ":memory:" for tests.
"""
from __future__ import annotations

import json
import sqlite3
import time

from .schema import AIONPattern, AIONInstance, AIONMapping, AIONContract

_SCHEMA = """
CREATE TABLE IF NOT EXISTS patterns (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS instances (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL, pattern_id TEXT NOT NULL, payload TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS mappings (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL, pattern_id TEXT NOT NULL, payload TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS contracts (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL, pattern_id TEXT NOT NULL, payload TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audits (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT NOT NULL, authority TEXT NOT NULL, verdict TEXT NOT NULL,
    detail TEXT, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS promotion_attempts (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT NOT NULL, contract_id TEXT, verdict TEXT NOT NULL,
    vi_approval INTEGER NOT NULL, reasons TEXT, created_at REAL NOT NULL
);
"""


class AuthorityError(Exception):
    """Raised when a record is stamped by a forbidden authority."""


class ProvenanceStore:
    def __init__(self, path: str = ":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    # ---- patterns (versioned; new version appended, old kept) ----
    def add_pattern(self, pattern: AIONPattern) -> int:
        cur = self.conn.execute(
            "SELECT MAX(version) AS v FROM patterns WHERE id = ?", (pattern.id,)
        )
        prev = cur.fetchone()["v"]
        version = (prev or 0) + 1
        self.conn.execute(
            "INSERT INTO patterns (id, version, payload, created_at) VALUES (?,?,?,?)",
            (pattern.id, version, json.dumps(pattern.to_dict()), time.time()),
        )
        self.conn.commit()
        return version

    def get_pattern(self, pattern_id: str):
        cur = self.conn.execute(
            "SELECT payload FROM patterns WHERE id = ? ORDER BY version DESC LIMIT 1",
            (pattern_id,),
        )
        row = cur.fetchone()
        return AIONPattern.from_dict(json.loads(row["payload"])) if row else None

    def add_instance(self, inst: AIONInstance):
        self.conn.execute(
            "INSERT INTO instances (id, pattern_id, payload, created_at) VALUES (?,?,?,?)",
            (inst.id, inst.pattern_id, json.dumps(inst.to_dict()), time.time()),
        )
        self.conn.commit()

    def add_mapping(self, m: AIONMapping):
        self.conn.execute(
            "INSERT INTO mappings (id, pattern_id, payload, created_at) VALUES (?,?,?,?)",
            (m.id, m.pattern_id, json.dumps(m.to_dict()), time.time()),
        )
        self.conn.commit()

    def add_contract(self, c: AIONContract):
        self.conn.execute(
            "INSERT INTO contracts (id, pattern_id, payload, created_at) VALUES (?,?,?,?)",
            (c.id, c.pattern_id, json.dumps(c.to_dict()), time.time()),
        )
        self.conn.commit()

    # ---- audits (append-only; authority must be urbi) ----
    def record_audit(self, pattern_id: str, authority: str, verdict: str,
                     detail: str = "") -> None:
        if str(authority).lower() != "urbi":
            raise AuthorityError(
                f"only Urbi may record an audit verdict (got {authority!r})"
            )
        self.conn.execute(
            "INSERT INTO audits (pattern_id, authority, verdict, detail, created_at) "
            "VALUES (?,?,?,?,?)",
            (pattern_id, "urbi", verdict, detail, time.time()),
        )
        self.conn.commit()

    # ---- promotion attempts (append-only; ALL attempts, incl. denied) ----
    def record_promotion_attempt(self, pattern_id, contract_id, verdict,
                                 vi_approval, reasons) -> None:
        self.conn.execute(
            "INSERT INTO promotion_attempts "
            "(pattern_id, contract_id, verdict, vi_approval, reasons, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (pattern_id, contract_id, verdict, 1 if vi_approval else 0,
             json.dumps(list(reasons)), time.time()),
        )
        self.conn.commit()

    def promotion_attempts(self, pattern_id: str = None):
        if pattern_id:
            cur = self.conn.execute(
                "SELECT * FROM promotion_attempts WHERE pattern_id = ? ORDER BY row_id",
                (pattern_id,),
            )
        else:
            cur = self.conn.execute("SELECT * FROM promotion_attempts ORDER BY row_id")
        return [dict(r) for r in cur.fetchall()]

    def audits(self, pattern_id: str = None):
        if pattern_id:
            cur = self.conn.execute(
                "SELECT * FROM audits WHERE pattern_id = ? ORDER BY row_id", (pattern_id,)
            )
        else:
            cur = self.conn.execute("SELECT * FROM audits ORDER BY row_id")
        return [dict(r) for r in cur.fetchall()]

    def close(self):
        self.conn.close()
