import sqlite3
import sys
import os
import argparse
from pathlib import Path
from typing import TextIO

from graveyard_redaction import redact_sensitive_text

# Fix Windows printing
sys.stdout.reconfigure(encoding='utf-8')

def search(query: str, db_path: Path, limit: int = 10, stream: TextIO = sys.stdout):
    safe_query = redact_sensitive_text(query)
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}. Run graveyard_reader.py first.", file=stream)
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    sql = """
        SELECT path, snippet(documents, 1, '>>', '<<', '...', 64) 
        FROM documents 
        WHERE documents MATCH ? 
        ORDER BY rank 
        LIMIT ?
    """
    
    try:
        cursor.execute(sql, (query, limit))
        results = cursor.fetchall()
        
        if not results:
            print(f"No results found for query: '{safe_query}'", file=stream)
            return
            
        print(f"--- Top {len(results)} matches for '{safe_query}' ---", file=stream)
        for idx, (path, snippet) in enumerate(results, 1):
            print(f"\n{idx}. MATCH IN: {redact_sensitive_text(path)}", file=stream)
            print(f"   {redact_sensitive_text(snippet)}", file=stream)
            
    except sqlite3.OperationalError as e:
        print(f"Search error: {type(e).__name__}", file=stream)
        print("Note: FTS5 queries support match operators like AND, OR, NOT. Example: '\"exact phrase\"'", file=stream)
        
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Graveyard FTS Search Tool")
    parser.add_argument("query", help="The text or FTS5 phrase to search for")
    parser.add_argument("--db", type=Path, help="Path to the graveyard_index.db SQLite file")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results to return")
    
    args = parser.parse_args()
    
    db_path = args.db
    if not db_path:
        env_db = os.environ.get("GRAVEYARD_DB")
        if env_db:
            db_path = Path(env_db)
        else:
            # Fallback to default
            db_path = Path(__file__).parent.parent / "_backup" / "graveyard_index.db"
            
    search(args.query, db_path=db_path, limit=args.limit)
