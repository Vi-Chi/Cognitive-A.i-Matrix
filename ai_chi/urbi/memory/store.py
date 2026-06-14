"""MemoryStore — filesystem-first tiered memory with a core-write monopoly.

Each tier is an append-only JSONL file under ``<base>/memory/<tier>.jsonl``. This is
deliberately filesystem-first (no DB) so it runs offline on the CM5 and needs no
transport/persistence decision yet; LMDB/RocksDB can back this later behind the same
interface.

Constitutional property: **only the Promoter may write the CORE tier.** A direct
``append`` to CORE is refused — promotion to trusted memory must go through the
audit-gated membrane (`promotion.Promoter`). This is the anti-self-poisoning rule.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator

from ai_chi.urbi.memory.records import CANDIDATE_TIERS, MemoryRecord, Tier

_CORE_TOKEN = object()  # opaque capability the Promoter holds; not exported


class CoreWriteForbidden(PermissionError):
    """Raised when something other than the Promoter tries to write CORE."""


class MemoryStore:
    def __init__(self, base_dir: str | Path = "data/urbi_memory") -> None:
        self.dir = Path(base_dir) / "memory"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, tier: Tier) -> Path:
        return self.dir / f"{tier.value}.jsonl"

    def append(self, record: MemoryRecord, *, _core_token: object | None = None) -> Path:
        """Append a record to its tier. CORE requires the Promoter's token."""
        if record.tier is Tier.CORE and _core_token is not _CORE_TOKEN:
            raise CoreWriteForbidden(
                "CORE is write-protected — promote via promotion.Promoter, not direct append")
        path = self._path(record.tier)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_payload(), ensure_ascii=False, sort_keys=True) + "\n")
        return path

    def read(self, tier: Tier) -> list[dict]:
        path = self._path(tier)
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def iter_candidates(self) -> Iterator[dict]:
        """Yield records across all candidate tiers (everything except CORE/NEGATIVE)."""
        for tier in CANDIDATE_TIERS:
            yield from self.read(tier)

    def tiers(self) -> Iterable[Tier]:
        return list(Tier)
