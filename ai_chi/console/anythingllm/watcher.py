"""Passive AnythingLLM file watcher for the A.i console membrane."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

from ai_chi.core.loop import RealityLoop
from ai_chi.core.observe.intake import BaseObserver
from ai_chi.bus import MMessage, Mode


class AnythingLLMWorkspaceObserver(BaseObserver):
    """Turn new RAG workspace text files into canonical observations."""

    def __init__(self, watch_dir: str | Path = "/opt/Omni-ai/storage/documents") -> None:
        super().__init__(domain="observe.console.workspace_files")
        self.watch_dir = Path(watch_dir)
        self.processed_files: set[str] = set()

    def observe(self, file_path: Path, *, mode: Mode = Mode.WAKE) -> MMessage:
        payload = {
            "raw_data": f"Bridge packet {file_path.name} routed.",
            "source_type": "bridge_packet",
            "provenance_uri": f"urn:console:bridge:{file_path.name}",
            "sensor_confidence": 0.85,
        }
        return MMessage(
            sigma="ext.observation",
            payload=payload,
            destination="urbi",
            context={
                "trust_score": 0.85,
                "domain": self.domain,
                "provenance": [payload["provenance_uri"]],
            },
            mode=mode,
        ).validate()

    def candidates(self) -> Iterable[Path]:
        yield from self.watch_dir.glob("*.json")


def run_watcher(watch_dir: str | Path | None = None) -> None:
    observer = AnythingLLMWorkspaceObserver(watch_dir or "/opt/Omni-ai/storage/documents")
    if not observer.watch_dir.exists():
        observer.watch_dir = Path("data/sim_console_uploads")
        observer.watch_dir.mkdir(parents=True, exist_ok=True)

    loop = RealityLoop()
    print(f"Routing packets from {observer.watch_dir}")
    
    for file_path in observer.candidates():
        if file_path.name.endswith(".acked"):
            continue
            
        obs = observer.observe(file_path)
        loop.bus.publish(obs)
        loop.ledger.record_envelope(obs)
        audit = loop.urbi.audit_observation(obs)
        loop.ledger.record_envelope(audit)
        
        # Ack the packet
        ack_path = file_path.with_suffix(file_path.suffix + ".acked")
        file_path.rename(ack_path)
        print(f"Audited and acked {file_path.name}: {audit.sigma}")
        
    print("A.i console watcher bounded pass complete")
