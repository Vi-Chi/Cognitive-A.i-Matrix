"""Ranking memory — the SERP snapshot ledger (the original AION-SEARCH layer).

Stores how engines ranked URLs for queries OVER TIME. Append-only: a snapshot is
a fossil, never edited. Lets you ask "how did this URL's visibility change?" and
"how do two engines disagree?" — engines are preserved as epistemic branches,
never merged.
"""
from __future__ import annotations

import json
import sqlite3
import time

from .models import SerpSnapshot, RankingObservation

_SCHEMA = """
CREATE TABLE IF NOT EXISTS serp_snapshots (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL, engine TEXT NOT NULL,
    captured_at REAL NOT NULL, payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rank_observations (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL, engine TEXT NOT NULL, url TEXT NOT NULL,
    rank INTEGER NOT NULL, captured_at REAL NOT NULL
);
"""


class RankingMemory:
    def __init__(self, path: str = ":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def record_snapshot(self, snapshot: SerpSnapshot) -> int:
        payload = {
            "query": snapshot.query, "engine": snapshot.engine,
            "captured_at": snapshot.captured_at,
            "observations": [o.__dict__ for o in snapshot.observations],
        }
        cur = self.conn.execute(
            "INSERT INTO serp_snapshots (query, engine, captured_at, payload) "
            "VALUES (?,?,?,?)",
            (snapshot.query, snapshot.engine, snapshot.captured_at, json.dumps(payload)),
        )
        for o in snapshot.observations:
            self.conn.execute(
                "INSERT INTO rank_observations (query, engine, url, rank, captured_at) "
                "VALUES (?,?,?,?,?)",
                (o.query, o.engine, o.url, o.rank, o.captured_at),
            )
        self.conn.commit()
        return cur.lastrowid

    def rank_history(self, url: str, query: str = None, engine: str = None):
        sql = "SELECT query, engine, url, rank, captured_at FROM rank_observations WHERE url = ?"
        params = [url]
        if query:
            sql += " AND query = ?"; params.append(query)
        if engine:
            sql += " AND engine = ?"; params.append(engine)
        sql += " ORDER BY captured_at"
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def engine_divergence(self, query: str, url: str) -> dict:
        """Latest rank of a url per engine — preserved divergence, not merged."""
        rows = self.conn.execute(
            "SELECT engine, rank, MAX(captured_at) AS captured_at "
            "FROM rank_observations WHERE query = ? AND url = ? GROUP BY engine",
            (query, url),
        ).fetchall()
        return {r["engine"]: r["rank"] for r in rows}

    def close(self):
        self.conn.close()
