from __future__ import annotations

import argparse
from pathlib import Path

from .audit import detect_manifest_quality, recommend_status, scan_zip_text
from .intake import inspect_zip
from .report import build_report, write_json_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Cognitive Matrix Artifact Forge P0 zip auditor.")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Inspect an AI sandbox export zip without executing it.")
    ingest.add_argument("--zip", required=True, help="Path to export zip.")
    ingest.add_argument("--project", default="unknown", help="Project label.")
    ingest.add_argument("--out", default="reports/import_audit.json", help="Output JSON report.")

    args = parser.parse_args()

    if args.command == "ingest":
        zip_path = Path(args.zip)
        records = inspect_zip(zip_path)
        manifest_quality = detect_manifest_quality(records)
        scans = scan_zip_text(zip_path, records)
        status = recommend_status(
            records,
            manifest_quality,
            dangerous_count=len(scans.get("dangerous", [])),
            overclaim_count=len(scans.get("overclaims", [])),
        )
        report = build_report(args.project, zip_path, records, manifest_quality, scans, status)
        write_json_report(report, Path(args.out))
        print(f"Artifact audit complete -> {args.out}")
        print(f"status={status} files={len(records)} manifest={manifest_quality}")


if __name__ == "__main__":
    main()
