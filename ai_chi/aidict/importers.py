"""LocalSubtitleImportAdapter — user-supplied text/transcripts into AIDICT.

The doc is explicit: AIDICT is **not** built around video scraping. It is built
around ``SubtitleFile -> TranscriptRecord -> ClaimRecord`` over files the user
already has (manual export, JDownloader, yt-dlp, official transcript). This
module ships the importer only — no downloader.

Supported inputs: ``.srt`` and ``.vtt`` (timestamps preserved), ``.txt`` (plain
transcript), ``.json`` (best-effort transcript exports). Output is a
``SourceRecord`` plus a list of timestamped ``Segment``s.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ai_chi.aidict.schemas import SourceRecord

_TS = r"\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}"
_ARROW = re.compile(rf"({_TS})\s*-->\s*({_TS})")
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")


@dataclass
class Segment:
    text: str
    start: str = ""
    end: str = ""
    index: int = 0


@dataclass
class ImportedSource:
    source: SourceRecord
    segments: list[Segment] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return " ".join(s.text for s in self.segments).strip()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _file_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _clean(line: str) -> str:
    line = re.sub(r"<[^>]+>", "", line)          # strip vtt cue tags
    return line.strip()


def parse_srt(text: str) -> list[Segment]:
    segments: list[Segment] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        start = end = ""
        body: list[str] = []
        for ln in lines:
            m = _ARROW.search(ln)
            if m:
                start, end = m.group(1), m.group(2)
            elif ln.strip().isdigit() and not body:
                continue  # sequence number
            else:
                cleaned = _clean(ln)
                if cleaned:
                    body.append(cleaned)
        if body:
            segments.append(Segment(text=" ".join(body), start=start, end=end,
                                    index=len(segments)))
    return segments


def parse_vtt(text: str) -> list[Segment]:
    # VTT is SRT-like; drop the WEBVTT header + NOTE/STYLE blocks, then reuse SRT.
    text = re.sub(r"^WEBVTT.*?(\n\n|\Z)", "", text, flags=re.S)
    text = re.sub(r"^(NOTE|STYLE).*?(\n\n|\Z)", "", text, flags=re.S | re.M)
    return parse_srt(text)


def parse_txt(text: str) -> list[Segment]:
    segments: list[Segment] = []
    for para in re.split(r"\n\s*\n", text.strip()):
        para = " ".join(para.split())
        if para:
            segments.append(Segment(text=para, index=len(segments)))
    if not segments and text.strip():
        segments.append(Segment(text=" ".join(text.split()), index=0))
    return segments


def parse_json(text: str) -> list[Segment]:
    """Best-effort across common transcript-export shapes."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return parse_txt(text)

    items = None
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ("transcript", "segments", "events", "results", "items"):
            if isinstance(data.get(key), list):
                items = data[key]
                break

    segments: list[Segment] = []
    if items is None:
        return parse_txt(json.dumps(data))
    for it in items:
        if isinstance(it, str):
            seg_text = it
            start = end = ""
        elif isinstance(it, dict):
            seg_text = str(it.get("text") or it.get("content") or it.get("transcript") or "").strip()
            start = str(it.get("start") or it.get("start_time") or it.get("timestamp") or "")
            end = str(it.get("end") or it.get("end_time") or "")
        else:
            continue
        seg_text = " ".join(seg_text.split())
        if seg_text:
            segments.append(Segment(text=seg_text, start=start, end=end, index=len(segments)))
    return segments


_PARSERS = {".srt": parse_srt, ".vtt": parse_vtt, ".txt": parse_txt, ".json": parse_json}


def import_file(
    path: str | Path,
    *,
    source_type: str = "transcript",
    source_name: str = "",
    source_url: str = "",
    author_or_channel: str = "",
    acquisition_method: str = "manual",
    language: str = "",
) -> ImportedSource:
    """Read a transcript-like file into a SourceRecord + Segments."""
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    parser = _PARSERS.get(p.suffix.lower(), parse_txt)
    segments = parser(text)
    caption_type = "manual" if p.suffix.lower() == ".txt" else "unknown"

    source = SourceRecord(
        source_type=source_type,
        source_name=source_name or p.name,
        source_url=source_url,
        author_or_channel=author_or_channel,
        collected_at=_now_iso(),
        acquisition_method=acquisition_method,
        language=language,
        caption_type=caption_type,
        file_hash=_file_hash(text),
        quality_notes=f"{len(segments)} segments from {p.suffix or 'txt'}",
    )
    return ImportedSource(source=source, segments=segments)


def split_sentences(segment_text: str) -> list[str]:
    """Cheap, deterministic sentence segmentation for claim candidates."""
    parts = _SENT.split(segment_text.strip())
    return [s.strip() for s in parts if s.strip()]
