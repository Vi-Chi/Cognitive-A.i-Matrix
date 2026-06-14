"""Core logic for the Advanced Register & Indexer.

Implements H1 (Aggregate Sensitivity Tiering), H3 (Mandatory fail-closed redaction),
and H5 (Tamper-evident JSONL Ledger).
"""
import json
import hashlib
import os
from dataclasses import dataclass, asdict
from typing import Any, Optional, Protocol, runtime_checkable
from datetime import datetime

# We reuse the graveyard redaction tools to enforce H3
try:
    from graveyard_redaction import contains_secret_shape, redact_sensitive_text
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from graveyard_redaction import contains_secret_shape, redact_sensitive_text

@dataclass
class SystemSnapshotRecord:
    record_type: str
    snapshot_id: str
    host_alias: str
    scope_id: str
    scan_mode: str
    started_at: str
    completed_at: str
    collector_version: str
    redaction_policy: str
    source_hashes: list[str]
    stats: dict[str, int]
    atlas_sensitivity_tier: str  # H1: The composite sensitivity

@dataclass
class FileNodeRecord:
    record_type: str
    path: str
    node_type: str
    size_bytes: int
    mtime: str
    mode: str
    owner: str
    content_hash: str
    classification: list[str]
    index_policy: str
    
@dataclass
class ConfigRecord:
    record_type: str
    path: str
    path_hash: str
    kind: str
    owner: str
    mode: str
    mtime: str
    content_hash_redacted: str
    parser: str
    sensitive: bool
    indexed_text_ref: str

@runtime_checkable
class ReadOnlyCollector(Protocol):
    """
    H2: Structural read-only guarantee.
    Collectors must be pure functions returning a list of records.
    The collector layer imports no write/exec/network-mutation capability.
    """
    def collect(self) -> list[Any]:
        ...

class SecurityMapClassifier:
    """Implements H1: Aggregate Sensitivity."""
    
    TIERS = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "LOCAL_ONLY"]
    
    def __init__(self):
        self.categories_seen = set()
        self.max_record_tier_index = 0
        
    def observe_category(self, category: str):
        """Observe a functional category (e.g., network, firewall, users, services, autostart)."""
        self.categories_seen.add(category.lower())
        
    def observe_record_tier(self, tier: str):
        """Observe an individual record's sensitivity."""
        try:
            idx = self.TIERS.index(tier.upper())
            self.max_record_tier_index = max(self.max_record_tier_index, idx)
        except ValueError:
            pass
            
    def compute_atlas_tier(self) -> str:
        """H1: The composite index inherits max(sensitivity) and is bumped if spanning multiple systems."""
        critical_categories = {"network", "services", "users", "firewall", "autostart"}
        overlap_count = len(self.categories_seen.intersection(critical_categories))
        
        tier_idx = self.max_record_tier_index
        if overlap_count >= 2:
            tier_idx = min(len(self.TIERS) - 1, tier_idx + 1)
            
        return self.TIERS[tier_idx]

class TamperEvidentLedgerWriter:
    """Implements H5: Tamper-evident ledger with fsync and H3: Fail-closed redaction."""
    
    def __init__(self, path: str):
        self.path = path
        self.prev_fingerprint = "GENESIS"
        self._f = open(path, "a", encoding="utf-8")
        
    def _hash_payload(self, json_bytes: bytes, prev: str) -> str:
        h = hashlib.sha256()
        h.update(prev.encode('utf-8'))
        h.update(b"||")
        h.update(json_bytes)
        return h.hexdigest()
        
    def append_record(self, record: Any) -> bool:
        """
        Write a dataclass or dict to the ledger.
        Returns False if dropped due to H3 (secret shapes).
        """
        if hasattr(record, "__dataclass_fields__"):
            data = asdict(record)
        else:
            data = dict(record)
            
        json_str = json.dumps(data, sort_keys=True)
        
        # H3: Mandatory fail-closed redaction before writing
        if contains_secret_shape(json_str):
            # Attempt to automatically redact it
            redacted_str = redact_sensitive_text(json_str)
            # Re-check. If STILL secret shaped, we drop it.
            if contains_secret_shape(redacted_str):
                return False
            json_str = redacted_str
            
        json_bytes = json_str.encode('utf-8')
        fingerprint = self._hash_payload(json_bytes, self.prev_fingerprint)
        
        envelope = {
            "payload": json.loads(json_str),
            "prev_fingerprint": self.prev_fingerprint,
            "fingerprint": fingerprint
        }
        
        envelope_str = json.dumps(envelope)
        self._f.write(envelope_str + "\n")
        self._f.flush()
        os.fsync(self._f.fileno())
        
        self.prev_fingerprint = fingerprint
        return True
        
    def close(self):
        self._f.close()
