"""Filesystem Collector for the Advanced Register.

Performs a read-only, metadata-focused scan of local paths.
Enforces H3 via `graveyard_redaction.is_sensitive_path` and `contains_secret_shape`.
"""
import os
import stat
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import TextIO

from register_core import FileNodeRecord, SystemSnapshotRecord, SecurityMapClassifier, TamperEvidentLedgerWriter, ReadOnlyCollector

# Import redaction logic
import sys
sys.path.append(str(Path(__file__).parent))
from graveyard_redaction import is_sensitive_path

def get_file_hash(path: Path, max_size: int = 10 * 1024 * 1024) -> str:
    """Compute sha256 of file, skipping if too large."""
    if path.stat().st_size > max_size:
        return "sha256:oversized"
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return "sha256:" + h.hexdigest()
    except Exception:
        return "sha256:unreadable"

class FilesystemCollector(ReadOnlyCollector):
    def __init__(self, scan_paths: list[Path], metadata_only: bool = True):
        self.scan_paths = scan_paths
        self.metadata_only = metadata_only
        self.classifier = SecurityMapClassifier()
        self.stats = {
            "files_seen": 0,
            "secrets_blocked": 0,
            "directories_seen": 0
        }
        self.blocked_paths = []

    def collect(self) -> list[FileNodeRecord]:
        records = []
        for scan_path in self.scan_paths:
            for root, dirs, files in os.walk(scan_path):
                root_path = Path(root)
                
                lowered_root = str(root_path).lower()
                if "systemd" in lowered_root or "init" in lowered_root:
                    self.classifier.observe_category("services")
                if "etc" in lowered_root:
                    self.classifier.observe_category("network")
                    
                self.stats["directories_seen"] += 1
                
                for file_name in files:
                    file_path = root_path / file_name
                    self.stats["files_seen"] += 1
                    
                    if is_sensitive_path(file_path):
                        self.stats["secrets_blocked"] += 1
                        self.blocked_paths.append(str(file_path))
                        continue
                        
                    try:
                        st = file_path.stat()
                    except OSError:
                        continue
                        
                    content_hash = "sha256:metadata_only"
                    if not self.metadata_only and stat.S_ISREG(st.st_mode):
                        content_hash = get_file_hash(file_path)
                        
                    record = FileNodeRecord(
                        record_type="FileNodeRecord",
                        path=str(file_path),
                        node_type="file" if stat.S_ISREG(st.st_mode) else "other",
                        size_bytes=st.st_size,
                        mtime=datetime.utcfromtimestamp(st.st_mtime).isoformat() + "Z",
                        mode=oct(stat.S_IMODE(st.st_mode)),
                        owner=str(st.st_uid),
                        content_hash=content_hash,
                        classification=["scanned"],
                        index_policy="metadata_only" if self.metadata_only else "hash_included"
                    )
                    records.append(record)
        return records

def scan_filesystem(
    scan_paths: list[Path], 
    output_dir: Path, 
    host_alias: str = "localhost",
    metadata_only: bool = True
):
    output_dir.mkdir(parents=True, exist_ok=True)
    start_time = datetime.utcnow().isoformat() + "Z"
    
    snapshot_id = f"snap_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{host_alias}"
    snap_dir = output_dir / snapshot_id
    snap_dir.mkdir()
    
    files_jsonl = snap_dir / "files.jsonl"
    blocked_jsonl = snap_dir / "blocked.jsonl"
    
    ledger = TamperEvidentLedgerWriter(str(files_jsonl))
    collector = FilesystemCollector(scan_paths, metadata_only)
    
    records = collector.collect()
    
    for record in records:
        if not ledger.append_record(record):
            collector.stats["secrets_blocked"] += 1
            collector.blocked_paths.append(record.path)
            
    ledger.close()
    
    with open(blocked_jsonl, "w", encoding="utf-8") as bf:
        for bp in collector.blocked_paths:
            bf.write(f"{bp}\n")
            
    end_time = datetime.utcnow().isoformat() + "Z"
    
    snap_record = SystemSnapshotRecord(
        record_type="SystemSnapshotRecord",
        snapshot_id=snapshot_id,
        host_alias=host_alias,
        scope_id="filesystem",
        scan_mode="metadata_only" if metadata_only else "hash_included",
        started_at=start_time,
        completed_at=end_time,
        collector_version="register_indexer_v0.1",
        redaction_policy="graveyard_redaction_v0.1",
        source_hashes=[],
        stats=collector.stats,
        atlas_sensitivity_tier=collector.classifier.compute_atlas_tier()
    )
    
    snap_ledger = TamperEvidentLedgerWriter(str(snap_dir / "snapshot.jsonl"))
    snap_ledger.append_record(snap_record)
    snap_ledger.close()
    
    print(f"Scan complete. Wrote {collector.stats['files_seen']} files to {snapshot_id}")
    print(f"Blocked {collector.stats['secrets_blocked']} sensitive paths.")
    print(f"Atlas Sensitivity Tier: {snap_record.atlas_sensitivity_tier}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", type=Path, required=True, help="Path to scan")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory")
    parser.add_argument("--host-alias", type=str, default="localhost")
    parser.add_argument("--with-hashes", action="store_true", help="Compute file hashes")
    
    args = parser.parse_args()
    scan_filesystem(
        [args.scan], 
        args.output_dir, 
        host_alias=args.host_alias, 
        metadata_only=not args.with_hashes
    )
