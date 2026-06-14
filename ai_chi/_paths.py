"""Local dependency path bootstrap for the A.i workspace.

Self-contained: mebus + bridge are vendored inside the core (ai_chi/_vendor), so
`import mebus` / `import bridge` resolve without an external Ai_Stack/.
"""
from __future__ import annotations

import sys
from pathlib import Path

AICORE_DIR = Path(__file__).resolve().parent
AI_ROOT = AICORE_DIR.parent
VENDOR = AICORE_DIR / "_vendor"
# Legacy external locations (kept as fallbacks; harmless if absent).
AI_STACK = AI_ROOT / "Ai_Stack"
MEBUS_SRC = AI_STACK / "MEBUS" / "mebus" / "src"
URBI_REPO = AI_STACK / "Urbi" / "cognitive_matrix_repo"


def ensure_dependency_paths() -> None:
    """Make the vendored (and any legacy external) dependency packages importable."""
    for path in (VENDOR, MEBUS_SRC, URBI_REPO):
        if path.exists():
            value = str(path)
            if value not in sys.path:
                sys.path.insert(0, value)
