import shutil
from pathlib import Path


TRINITY_BRIDGE_RUNTIME_DIRS = {
    "acks",
    "arbitration_rejected",
    "blocked",
    "claims",
    "executed",
    "execution_rejected",
    "handoffs",
    "health",
    "inbox",
    "ledger",
    "needs_human",
    "outbox",
    "processed",
    "rejected",
    "samples",
    "stale",
    "state",
    "superseded",
}

TARGETS = [
    "ai_chi",
    "scripts",
    "docs",
    "DO_ANYTHING_NOW.md",
    "_PROJECT_KNOWLEDGE_BASE/README.md",
    "_MODEL_TRINITY",
]


def ignore_publishable_runtime(dir_path, names):
    path = Path(dir_path)
    if path.name == "bridge" and path.parent.name == "_MODEL_TRINITY":
        return {name for name in names if name in TRINITY_BRIDGE_RUNTIME_DIRS}
    ignored = {"__pycache__", ".pytest_cache"}
    return {name for name in names if name in ignored or name.endswith(".pyc")}


def export_curated_slice(root_dir: Path) -> Path:
    root_dir = root_dir.resolve()
    export_dir = root_dir / "_export" / "publishable_slice"

    export_dir.mkdir(parents=True, exist_ok=True)

    for item in TARGETS:
        src = root_dir / item
        dst = export_dir / item
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                if dst.is_dir():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            if src.is_dir():
                shutil.copytree(src, dst, ignore=ignore_publishable_runtime)
            else:
                shutil.copy2(src, dst)
            print(f"Copied {item}")
        else:
            print(f"Skipped {item} (not found)")

    print(f"\nCurated slice successfully exported to: {export_dir}")
    return export_dir


def main():
    export_curated_slice(Path(__file__).resolve().parents[1])

if __name__ == "__main__":
    main()
