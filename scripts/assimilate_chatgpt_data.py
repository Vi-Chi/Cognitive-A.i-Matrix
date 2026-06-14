import json
import os
import re
from pathlib import Path
from datetime import datetime

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
IMPORT_FILE = ROOT_DIR / "_Import" / "chatgpt_export" / "conversations.json"
OUTPUT_DIR = ROOT_DIR / "_backup" / "chatgpt_archive"

def sanitize_filename(name):
    # Remove invalid characters for windows filenames
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip()
    return name[:150] if len(name) > 150 else name

def extract_text_from_message(message):
    if not message:
        return None
    author = message.get("author", {}).get("role", "unknown")
    content = message.get("content", {})
    content_type = content.get("content_type", "")
    
    text = ""
    if content_type == "text" and "parts" in content:
        text = "".join([str(p) for p in content["parts"] if isinstance(p, str)])
    elif content_type == "multimodal_text" and "parts" in content:
        for part in content["parts"]:
            if isinstance(part, str):
                text += part
            elif isinstance(part, dict) and part.get("content_type") == "text":
                text += part.get("text", "")
    
    if text.strip():
        return f"**{author.upper()}**:\n{text}\n"
    return None

def process_conversations():
    if not IMPORT_FILE.exists():
        print(f"Error: {IMPORT_FILE} not found.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Loading conversations.json (this might take a moment)...")
    with open(IMPORT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Found {len(data)} conversations. Processing...")
    
    for count, conv in enumerate(data):
        title = conv.get("title", "Untitled")
        create_time = conv.get("create_time", 0)
        date_str = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d")
        
        safe_title = sanitize_filename(title)
        filename = f"{date_str}_{safe_title}.txt"
        filepath = OUTPUT_DIR / filename
        
        mapping = conv.get("mapping", {})
        current_node_id = conv.get("current_node")
        
        if not current_node_id or not mapping:
            continue
            
        # Reconstruct path from leaf to root
        lineage = []
        node_id = current_node_id
        while node_id:
            node = mapping.get(node_id)
            if not node:
                break
            lineage.append(node)
            node_id = node.get("parent")
            
        # Reverse to get chronological order
        lineage.reverse()
        
        # Build the document
        doc_lines = [f"# {title}\n", f"Date: {date_str}\n\n"]
        for node in lineage:
            msg = node.get("message")
            text = extract_text_from_message(msg)
            if text:
                doc_lines.append(text)
                doc_lines.append("-" * 40 + "\n")
                
        # Write to file if it contains actual messages
        if len(doc_lines) > 2:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(doc_lines))
                
        if (count + 1) % 100 == 0:
            print(f"Processed {count + 1}/{len(data)} conversations...")

    print(f"Done! All conversations extracted to {OUTPUT_DIR}")

if __name__ == "__main__":
    process_conversations()
