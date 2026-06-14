from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


@dataclass
class FileRecord:
    path: str
    size_bytes: int
    sha256: str
    file_class: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify_path(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".md", ".txt", ".rst"}:
        return "documentation"
    if suffix in {".py", ".js", ".ts", ".sh", ".rs", ".go", ".java", ".c", ".cpp"}:
        return "code"
    if suffix in {".json", ".jsonl", ".yaml", ".yml", ".toml", ".xml"}:
        return "schema_config_data"
    if suffix in {".zip", ".tar", ".gz", ".7z"}:
        return "archive"
    if suffix in {".png", ".jpg", ".jpeg", ".svg", ".webp"}:
        return "image"
    return "other"


def inspect_zip(zip_path: Path) -> List[FileRecord]:
    records: List[FileRecord] = []
    with zipfile.ZipFile(zip_path, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue

            # Zip-slip / absolute path guard.
            candidate = Path(info.filename)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise ValueError(f"Unsafe zip path: {info.filename}")

            data = z.read(info.filename)
            records.append(FileRecord(
                path=info.filename,
                size_bytes=len(data),
                sha256=sha256_bytes(data),
                file_class=classify_path(info.filename),
            ))
    return records


def file_records_as_dicts(records: List[FileRecord]) -> List[Dict]:
    return [asdict(r) for r in records]
