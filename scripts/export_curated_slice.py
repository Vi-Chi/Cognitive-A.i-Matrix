import os
import shutil
from pathlib import Path

def main():
    root_dir = Path(r"C:\Users\Vi Chi\Desktop\Projectz\A.i")
    export_dir = root_dir / "_export" / "publishable_slice"
    
    # Clean export dir
    if export_dir.exists():
        shutil.rmtree(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Whitelisted folders and files
    targets = [
        "ai_chi",
        "scripts",
        "docs",
        "DO_ANYTHING_NOW.md",
        "_PROJECT_KNOWLEDGE_BASE/README.md",
        "_MODEL_TRINITY"
    ]
    
    for item in targets:
        src = root_dir / item
        dst = export_dir / item
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache'))
            else:
                shutil.copy2(src, dst)
            print(f"Copied {item}")
        else:
            print(f"Skipped {item} (not found)")
            
    print(f"\nCurated slice successfully exported to: {export_dir}")

if __name__ == "__main__":
    main()
