from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, List

from .intake import FileRecord


DANGEROUS_KEYWORDS = [
    "subprocess", "os.system", "eval(", "exec(", "rm -rf", "curl | sh",
    "Invoke-Expression", "powershell", "chmod 777", "sudo ", "delete_emails",
    "send_email", "network_send", "actuate", "spawn", "control"
]

OVERCLAIM_KEYWORDS = [
    "production-ready", "fully self-contained", "complete implementation",
    "ready for production", "all code is complete", "no further work needed",
    "/home/workdir", "sandbox path", "attached as downloadable"
]


def detect_manifest_quality(records: List[FileRecord]) -> str:
    manifest_paths = [r.path.lower() for r in records if "manifest" in Path(r.path).name.lower()]
    if not manifest_paths:
        return "missing"
    return "present_unverified"


def scan_zip_text(zip_path: Path, records: List[FileRecord]) -> Dict[str, List[Dict]]:
    dangerous: List[Dict] = []
    overclaims: List[Dict] = []

    with zipfile.ZipFile(zip_path, "r") as z:
        for rec in records:
            if rec.file_class not in {"documentation", "code", "schema_config_data"}:
                continue
            try:
                text = z.read(rec.path).decode("utf-8", errors="replace")
            except Exception:
                continue

            lower = text.lower()
            for keyword in DANGEROUS_KEYWORDS:
                if keyword.lower() in lower:
                    dangerous.append({"path": rec.path, "keyword": keyword})

            for keyword in OVERCLAIM_KEYWORDS:
                if keyword.lower() in lower:
                    overclaims.append({"path": rec.path, "keyword": keyword})

    return {"dangerous": dangerous, "overclaims": overclaims}


def recommend_status(records: List[FileRecord], manifest_quality: str, dangerous_count: int, overclaim_count: int) -> str:
    if not records:
        return "reject"
    if dangerous_count > 0:
        return "quarantine"
    if manifest_quality == "missing" or overclaim_count > 0:
        return "partial_import_recommended"
    return "accept_candidate"
