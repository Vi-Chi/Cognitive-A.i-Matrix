"""Zero-dependency stdlib inter-process file lock.

Portably leverages `os.O_CREAT | os.O_EXCL` which is atomic on both Windows
and POSIX platforms. Used to secure MΣBUS ledger appends against concurrent
process writers (e.g., Urbi and Orbi).
"""
from __future__ import annotations

import os
import time
from pathlib import Path


class InterprocessLock:
    """A blocking file lock context manager."""

    def __init__(self, target_path: Path | str, *, timeout: float = 10.0, retry_ms: float = 10.0) -> None:
        self.target_path = Path(target_path)
        # Sibling lock file (e.g. "ledger.jsonl.lock")
        self.lock_path = self.target_path.with_name(self.target_path.name + ".lock")
        self.timeout = timeout
        self.retry_ms = retry_ms
        self._fd = None

    def __enter__(self) -> InterprocessLock:
        start = time.monotonic()
        while True:
            try:
                # O_CREAT | O_EXCL guarantees atomic creation
                self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return self
            except FileExistsError:
                if time.monotonic() - start > self.timeout:
                    raise TimeoutError(f"Failed to acquire lock for {self.target_path} within {self.timeout}s")
                time.sleep(self.retry_ms / 1000.0)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
            try:
                self.lock_path.unlink(missing_ok=True)
            except Exception:
                pass
