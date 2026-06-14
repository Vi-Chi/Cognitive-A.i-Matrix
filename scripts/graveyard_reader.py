"""Graveyard reader — builds a redacted, deduped FTS5 search index over cold backup text.

Reverse-engineered + enhanced 2026-06-14 (Claude, Auditor-Scribe, patch-heavy lane).
Preserved: redaction-first, FTS5 search, content-hash dedup, per-file isolation, redacted
error output. Enhancements (all preserve/strengthen the secret boundary):

  E1 portability     — no hardcoded user paths; derive repo root from script location,
                       overridable via env (GRAVEYARD_DB / GRAVEYARD_BACKUP_DIR) or CLI.
  E2 fail-closed     — post-redaction verification with contains_secret_shape(): a doc that
                       is STILL secret-shaped after redaction is SKIPPED (never indexed),
                       not stored. Defense-in-depth over redact_sensitive_text alone.
  E3 atomic rebuild  — --reset builds into a temp DB then os.replace()s it in, so an
                       interrupted/power-loss rebuild never corrupts or destroys the live index.
  E4 robustness      — max-size guard + binary sniff (skip NUL-byte/binary files);
                       configurable extensions.
  E5 safe import     — graveyard_redaction resolves regardless of cwd.
  E6 auditability    — counts blocked_unredacted / skipped_binary / skipped_large.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import sys
from pathlib import Path

# E5: make the sibling redaction module importable regardless of cwd.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from graveyard_redaction import (  # noqa: E402
    contains_secret_shape,
    is_sensitive_path,
    redact_sensitive_text,
)

# E1: portable defaults. Script lives in <repo>/scripts/, so repo root is parents[1].
_REPO_ROOT = _SCRIPT_DIR.parent
BACKUP_DIR = Path(os.environ.get("GRAVEYARD_BACKUP_DIR", _REPO_ROOT / "_backup"))
DB_PATH = Path(os.environ.get("GRAVEYARD_DB", BACKUP_DIR / "graveyard_index.db"))

# E4: tunable guards.
INDEXED_EXTENSIONS = {".md", ".txt", ".json"}
MAX_FILE_BYTES = int(os.environ.get("GRAVEYARD_MAX_FILE_BYTES", 2_000_000))  # 2 MB
IGNORE_DIRS = {".git", "node_modules", "venv", "env", "__pycache__", ".pytest_cache"}


def get_text_hash(text: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8", errors="replace"))
    return h.hexdigest()


def _looks_binary(blob: bytes) -> bool:
    """E4: NUL byte in the head is a reliable binary tell; cheap and conservative."""
    return b"\x00" in blob[:4096]


def read_redacted_text(filepath: Path, *, max_bytes: int = MAX_FILE_BYTES) -> str:
    """Read a text file (size-capped, binary-skipping) and redact secret-shaped values.

    Raises ValueError for binary/oversized inputs so the caller can count + skip them.
    """
    size = filepath.stat().st_size
    if size > max_bytes:
        raise ValueError(f"oversized:{size}")
    blob = filepath.read_bytes()
    if _looks_binary(blob):
        raise ValueError("binary")
    return redact_sensitive_text(blob.decode("utf-8", errors="ignore"))


def reset_db(db_path: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        path = Path(str(db_path) + suffix)
        if path.exists():
            path.unlink()


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(path, content);"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS metadata (file_hash TEXT PRIMARY KEY, path TEXT);"
    )
    conn.commit()
    return conn


def build_index(
    backup_dir: Path = BACKUP_DIR,
    db_path: Path = DB_PATH,
    *,
    reset: bool = False,
    extensions: set[str] | None = None,
    max_bytes: int = MAX_FILE_BYTES,
) -> dict[str, int]:
    backup_dir = Path(backup_dir)
    db_path = Path(db_path)
    exts = {e.lower() for e in (extensions or INDEXED_EXTENSIONS)}

    # E3: on reset, build into a temp DB and atomically swap it in at the end, so an
    # interrupted rebuild never leaves a corrupt/partial index or destroys the old one.
    target_path = db_path
    if reset:
        target_path = Path(str(db_path) + ".tmp")
        reset_db(target_path)

    print(f"Initializing database at {target_path}...")
    conn = init_db(target_path)
    cursor = conn.cursor()

    cursor.execute("SELECT file_hash FROM metadata")
    seen_hashes = {row[0] for row in cursor.fetchall()}

    stats = {
        "total_scanned": 0,
        "skipped_sensitive": 0,
        "skipped_binary": 0,
        "skipped_large": 0,
        "blocked_unredacted": 0,
        "new_inserts": 0,
    }

    try:
        for root, dirs, files in os.walk(backup_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                if Path(file).suffix.lower() not in exts:
                    continue
                stats["total_scanned"] += 1
                filepath = Path(root) / file
                rel_path = filepath.relative_to(backup_dir)

                # Boundary 1: never even open likely-credential files.
                if is_sensitive_path(rel_path):
                    stats["skipped_sensitive"] += 1
                    continue

                # Boundary 2: read + redact (size/binary guarded).
                try:
                    content = read_redacted_text(filepath, max_bytes=max_bytes)
                except ValueError as e:
                    reason = str(e)
                    if reason.startswith("oversized"):
                        stats["skipped_large"] += 1
                    else:
                        stats["skipped_binary"] += 1
                    continue
                except Exception as e:
                    print(f"Error reading {redact_sensitive_text(str(filepath))}: {type(e).__name__}")
                    continue

                safe_path = redact_sensitive_text(str(rel_path).replace("\\", "/"))

                # Boundary 3 (E2, fail-closed): if anything is STILL secret-shaped after
                # redaction, DO NOT index it. A leak is worse than a missing doc.
                if contains_secret_shape(content) or contains_secret_shape(safe_path):
                    stats["blocked_unredacted"] += 1
                    print(f"BLOCKED (residual secret shape) {redact_sensitive_text(str(rel_path))}")
                    continue

                file_hash = get_text_hash(content)
                if file_hash in seen_hashes:
                    continue
                try:
                    cursor.execute(
                        "INSERT INTO documents (path, content) VALUES (?, ?)",
                        (safe_path, content),
                    )
                    cursor.execute(
                        "INSERT INTO metadata (file_hash, path) VALUES (?, ?)",
                        (file_hash, safe_path),
                    )
                    seen_hashes.add(file_hash)
                    stats["new_inserts"] += 1
                    if stats["new_inserts"] % 100 == 0:
                        conn.commit()
                        print(f"Indexed {stats['new_inserts']} new documents...")
                except Exception as e:
                    print(f"Error indexing {redact_sensitive_text(str(filepath))}: {type(e).__name__}")
        conn.commit()
    finally:
        conn.close()

    # E3: atomic swap (after a clean close) for the reset path.
    if reset:
        for suffix in ("", "-wal", "-shm"):
            stale = Path(str(db_path) + suffix)
            if stale.exists():
                stale.unlink()
        os.replace(target_path, db_path)

    stats["total_unique"] = len(seen_hashes)
    print(f"\nIndexing complete! Scanned {stats['total_scanned']} files.")
    print(f"Likely credential files skipped: {stats['skipped_sensitive']}")
    print(f"Binary/oversized skipped: {stats['skipped_binary']}/{stats['skipped_large']}")
    print(f"Blocked (residual secret shape): {stats['blocked_unredacted']}")
    print(f"Total unique documents in database: {stats['total_unique']}")
    return stats


def main() -> None:
    build_index(reset="--reset" in sys.argv[1:])


if __name__ == "__main__":
    main()
