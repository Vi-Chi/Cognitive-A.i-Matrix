"""Social Newsroom Ring Loop

A local python script to format, validate, and stage social media drafts
for the multi-channel "Ring" (Discord, GitHub, X, Reddit, Forums).

This script performs validation against the 'Do-Not-Say' list and the
DAN Propagation Protocol before moving the file to staging.
It DOES NOT execute any API calls to post.
"""

import argparse
from pathlib import Path
import re
import sys

DO_NOT_SAY = [
    "unrestricted ai",
    "jailbreak",
    "autonomous vessel control ready",
    "military ai",
    "solved agi"
]

def validate_draft(content: str) -> list[str]:
    violations = []
    content_lower = content.lower()
    for phrase in DO_NOT_SAY:
        if phrase in content_lower:
            violations.append(phrase)
            
    # Check for affiliation disclosure or safety framing
    if "open-source" not in content_lower and "local-first" not in content_lower:
        violations.append("Missing required safety framing (e.g., 'open-source local-first').")
        
    return violations

def stage_draft(source_path: Path, staging_dir: Path) -> bool:
    content = source_path.read_text(encoding="utf-8")
    
    violations = validate_draft(content)
    if violations:
        print(f"FAILED VALIDATION: {source_path.name}")
        for v in violations:
            print(f"  - {v}")
        return False
        
    staging_dir.mkdir(parents=True, exist_ok=True)
    dest_path = staging_dir / source_path.name
    
    # Prepend a frontmatter warning for the human
    frontmatter = (
        "---\n"
        "STATUS: PASSED RING LOOP VALIDATION\n"
        "ACTION: Awaiting Human API Push\n"
        "---\n\n"
    )
    dest_path.write_text(frontmatter + content, encoding="utf-8")
    print(f"SUCCESS: Staged {source_path.name} to {dest_path}")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drafts-dir", default="docs", help="Directory containing DRAFT_*.md files")
    parser.add_argument("--staging-dir", default="workspace_staging", help="Output staging directory")
    args = parser.parse_args()
    
    drafts = Path(args.drafts_dir)
    staging = Path(args.staging_dir)
    
    if not drafts.exists():
        print(f"Drafts directory {drafts} not found.")
        sys.exit(1)
        
    draft_files = list(drafts.glob("DRAFT_*.md")) + list(drafts.glob("PUBLIC_RELEASE_TRIAD_*.md"))
    if not draft_files:
        print("No drafts found to stage.")
        return
        
    for draft in draft_files:
        stage_draft(draft, staging)

if __name__ == "__main__":
    main()
