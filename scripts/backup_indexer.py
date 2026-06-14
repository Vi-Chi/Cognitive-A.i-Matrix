import os
import hashlib
import sys
from pathlib import Path

from graveyard_redaction import is_sensitive_path, redact_sensitive_text


def get_text_hash(text: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8", errors="replace"))
    return h.hexdigest()


def read_redacted_text(filepath: Path) -> str:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return redact_sensitive_text(f.read())

def extract_headings_and_summary(filepath: Path) -> tuple[list[str], str]:
    headings = []
    summary_lines = []
    try:
        for line in read_redacted_text(filepath).splitlines()[:50]:
            sline = line.strip()
            if sline.startswith('#'):
                headings.append(sline)
            elif sline and len(summary_lines) < 2 and not sline.startswith(('>', '-', '*', '|')):
                summary_lines.append(sline)
    except Exception:
        pass
    
    summary = " ".join(summary_lines)[:150]
    if len(summary) == 150:
        summary += "..."
    return headings, summary

def main():
    backup_dir = Path(r"C:\Users\Vi Chi\Desktop\Projectz\A.i\_backup")
    output_file = Path(r"C:\Users\Vi Chi\.gemini\antigravity\brain\22725a2a-4043-4b05-bb86-33c1c00221d6\backup_content_index.md")
    
    # Ignore patterns
    ignore_dirs = {'.git', 'node_modules', 'venv', 'env', '__pycache__', '.pytest_cache'}
    
    seen_hashes = {}
    total_files = 0
    skipped_sensitive = 0
    unique_files = 0
    
    print(f"Scanning {backup_dir}...")
    
    for root, dirs, files in os.walk(backup_dir):
        # Mutate dirs in-place to avoid traversing ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            if file.endswith('.md') or file.endswith('.txt'):
                total_files += 1
                filepath = Path(root) / file
                rel_path = filepath.relative_to(backup_dir)
                if is_sensitive_path(rel_path):
                    skipped_sensitive += 1
                    continue
                
                try:
                    redacted_text = read_redacted_text(filepath)
                    file_hash = get_text_hash(redacted_text)
                except Exception as e:
                    print(f"Error reading {redact_sensitive_text(filepath)}: {type(e).__name__}")
                    continue
                    
                if file_hash not in seen_hashes:
                    unique_files += 1
                    headings, summary = extract_headings_and_summary(filepath)
                    seen_hashes[file_hash] = {
                        'path': redact_sensitive_text(rel_path),
                        'size': filepath.stat().st_size,
                        'headings': headings,
                        'summary': summary
                    }
                else:
                    pass # It's a duplicate
                    
    print(f"Found {total_files} total files, {unique_files} unique.")
    
    # Group by primary folder (e.g., !Modules, or timestamped dirs)
    grouped = {}
    for data in seen_hashes.values():
        parts = Path(data['path']).parts
        if parts:
            primary = parts[0]
        else:
            primary = "Root"
            
        if primary not in grouped:
            grouped[primary] = []
        grouped[primary].append(data)
        
    print(f"Writing report to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write(f"# Backup Index Report\n\n")
        out.write(f"**Total files scanned:** {total_files}\n")
        out.write(f"**Likely credential files skipped:** {skipped_sensitive}\n")
        out.write(f"**Unique files identified:** {unique_files}\n\n")
        
        for primary, items in sorted(grouped.items()):
            out.write(f"## {primary}\n")
            # Sort items by size descending to highlight bigger docs
            items.sort(key=lambda x: x['size'], reverse=True)
            for item in items:
                # Convert path to posix for markdown link
                pstr = str(item['path']).replace('\\', '/')
                out.write(f"### `{pstr}` ({item['size']} bytes)\n")
                if item['headings']:
                    out.write(f"**Headings:** {', '.join(item['headings'][:3])}\n")
                if item['summary']:
                    out.write(f"**Summary:** {item['summary']}\n")
                out.write("\n")
                
    print("Done!")

if __name__ == "__main__":
    main()
