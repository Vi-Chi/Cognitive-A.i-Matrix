import sqlite3
import re
from pathlib import Path
from datetime import datetime

DB_PATH = Path(r"C:\Users\Vi Chi\Desktop\Projectz\A.i\_backup\graveyard_index.db")
OUTPUT_PATH = Path(r"C:\Users\Vi Chi\.gemini\antigravity\brain\22725a2a-4043-4b05-bb86-33c1c00221d6\chronological_reading_queue.md")

def extract_date(text):
    # Match YYYY-MM-DD or YYYYMMDD
    match = re.search(r'(202[0-9])[-_]?([0-1][0-9])[-_]?([0-3][0-9])', text)
    if match:
        try:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass
    return None

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT path, content FROM documents WHERE path LIKE '%.md'")
    rows = cursor.fetchall()
    
    docs = []
    
    for path, content in rows:
        # First try to find date in filename
        date_obj = extract_date(path)
        
        # If not in filename, check first 500 chars of content
        if not date_obj:
            date_obj = extract_date(content[:500])
            
        # If still no date, assign a default based on folder structure
        if not date_obj:
            if '!Modules' in path:
                # !Modules is the oldest era (pre-cleanroom)
                date_obj = datetime(2026, 5, 1) # Default old date
            else:
                date_obj = datetime(2026, 6, 12) # Default middle date
                
        docs.append({
            'path': path,
            'date': date_obj,
            'size': len(content)
        })
        
    # Sort chronologically
    docs.sort(key=lambda x: x['date'])
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write("# Chronological Reading Queue\n\n")
        f.write(f"**Total original markdown files:** {len(docs)}\n\n")
        
        batch_size = 10
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i+batch_size]
            f.write(f"## Batch {i//batch_size + 1} (Files {i+1} to {i+len(batch)})\n")
            for doc in batch:
                f.write(f"- `{doc['path']}` (Est. Date: {doc['date'].strftime('%Y-%m-%d')}, {doc['size']} bytes)\n")
            f.write("\n")
            
    print(f"Generated queue at {OUTPUT_PATH}")
    
if __name__ == "__main__":
    main()
