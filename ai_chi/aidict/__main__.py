"""Enable ``python -m ai_chi.aidict``."""
from __future__ import annotations

import sys

from ai_chi.aidict.cli import main

if __name__ == "__main__":
    sys.exit(main())
