"""Ollama endpoint resolution: Hailo-Ollama (10H, preferred) with CPU-Ollama fallback.

The v2.1 auditor (audit.py) reads OLLAMA_BASE as a module global at call time, so
`apply_to_auditor()` can repoint it at runtime without editing the auditor. Hailo-Ollama is
Ollama-API-compatible, so qwen2.5:1.5b served by the 10H is a drop-in for the CPU path.

Env:
  URBI_OLLAMA_BASE    hard override (skip probing)
  URBI_HAILO_OLLAMA   Hailo-Ollama base URL — set after `fw-control identify` + install on the node
  URBI_CPU_OLLAMA     CPU-Ollama base URL (default http://127.0.0.1:11434)
"""
from __future__ import annotations

import os
import urllib.request

CPU_OLLAMA = os.environ.get("URBI_CPU_OLLAMA", "http://127.0.0.1:11434")
# Node-specific — left empty until the 10H runtime is verified and Hailo-Ollama is installed.
HAILO_OLLAMA = os.environ.get("URBI_HAILO_OLLAMA", "")


def _reachable(base: str, timeout: float = 1.5) -> bool:
    if not base:
        return False
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=timeout) as r:
            return getattr(r, "status", 200) == 200
    except Exception:
        return False


def resolve_ollama_base() -> tuple[str, str]:
    """Return (base_url, which): override -> hailo-10h (if reachable) -> cpu-ollama."""
    override = os.environ.get("URBI_OLLAMA_BASE")
    if override:
        return override, "override"
    if _reachable(HAILO_OLLAMA):
        return HAILO_OLLAMA, "hailo-10h"
    return CPU_OLLAMA, "cpu-ollama"


# Reason model served as HEF on the Hailo-10H (the GenAI zoo has no embedding model,
# so embeddings always stay on CPU-Ollama). Override via env if a different HEF is loaded.
HAILO_REASON_MODEL = os.environ.get("URBI_HAILO_REASON_MODEL", "qwen2:1.5b")


def _import_audit():
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    import audit  # type: ignore[import-not-found]
    return audit


def apply_hybrid(*, reason_base: str | None = None, embed_base: str | None = None,
                 reason_model: str | None = None) -> dict:
    """Split routing: LLM *generate* -> Hailo-10H NPU; *embeddings* -> CPU-Ollama.

    The Hailo GenAI zoo serves reason models (qwen2/qwen2.5-coder, HEF) but no embedding
    model, so Lens-6 semantic embeddings must use CPU. Leaves audit.py source unmodified —
    only repoints OLLAMA_BASE (embeddings) and wraps ollama_generate (reason -> NPU).
    """
    import json, urllib.request
    reason_base = reason_base or (HAILO_OLLAMA or "http://127.0.0.1:8000")
    embed_base = embed_base or CPU_OLLAMA
    reason_model = reason_model or HAILO_REASON_MODEL
    audit = _import_audit()
    audit.OLLAMA_BASE = embed_base            # embeddings + ollama_available() -> CPU
    audit.REASON_MODEL = reason_model         # reason default -> the HEF model

    def _npu_generate(prompt: str, model: str = reason_model) -> str:
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                              "options": {"temperature": 0.0, "num_predict": 10}}).encode()
        try:
            req = urllib.request.Request(reason_base + "/api/generate", data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read()).get("response", "").strip().upper()
        except Exception as e:  # mirror audit.ollama_generate's error contract
            return f"ERROR:{e}"

    audit.ollama_generate = _npu_generate
    return {"reason": {"base": reason_base, "model": reason_model},
            "embed": {"base": embed_base, "model": getattr(audit, "EMBED_MODEL", "nomic-embed-text")}}


def apply_to_auditor(base: str | None = None) -> str:
    """Point the v2.1 auditor at an endpoint. With URBI_HYBRID set and Hailo reachable,
    splits reason->NPU / embed->CPU; otherwise points everything at the resolved base."""
    if base is None and os.environ.get("URBI_HYBRID") and _reachable(HAILO_OLLAMA):
        info = apply_hybrid()
        return info["embed"]["base"]
    if base is None:
        base, _ = resolve_ollama_base()
    audit = _import_audit()
    audit.OLLAMA_BASE = base
    return base
