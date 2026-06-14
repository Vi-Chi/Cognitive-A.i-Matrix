from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .intake import FileRecord, file_records_as_dicts


def build_report(
    project: str,
    zip_path: Path,
    records: List[FileRecord],
    manifest_quality: str,
    scans: Dict,
    status: str,
) -> Dict:
    class_counts = Counter(r.file_class for r in records)
    recommendations = []

    if manifest_quality == "missing":
        recommendations.append("Generate or request a stronger EXPORT_MANIFEST.md with file tree, sizes, timestamps, and SHA256 hashes.")
    if scans.get("dangerous"):
        recommendations.append("Keep archive in quarantine until dangerous-code findings are manually reviewed.")
    if scans.get("overclaims"):
        recommendations.append("Downgrade claims of completeness; mark as reconstructed or provisional.")
    if not recommendations:
        recommendations.append("Candidate for reviewed/ import after human inspection.")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": project,
        "archive": str(zip_path),
        "status": status,
        "file_count": len(records),
        "class_counts": dict(class_counts),
        "manifest_quality": manifest_quality,
        "files": file_records_as_dicts(records),
        "dangerous_findings": scans.get("dangerous", []),
        "overclaim_findings": scans.get("overclaims", []),
        "recommendations": recommendations,
    }


def write_json_report(report: Dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
