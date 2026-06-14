"""
Cognitive Matrix - Tri-State Audit Module v2.1
Fixes:
- Explicit negation detection in Lens 6 before semantic check
- Tighter embedding similarity threshold (0.82)
- LLM contradiction prompt hardened with examples
- Context no longer stores claims that contradict existing + entries
"""

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 ViChi - https://github.com/ViChi

import json
import time
import re
import math
import urllib.request
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONTEXT_STORE_PATH = Path(os.environ.get("URBI_CONTEXT_STORE", BASE_DIR / "context_store.json"))
DREAM_LOG_PATH = Path(os.environ.get("URBI_DREAM_LOG", BASE_DIR / "dream_layer.log"))

OLLAMA_BASE = "http://localhost:11434"
REASON_MODEL = "qwen2.5:1.5b"
EMBED_MODEL = "nomic-embed-text"

# Tighter threshold — only flag HIGH similarity + negation mismatch
SIMILARITY_THRESHOLD = 0.82


# ─── Ollama Interface ─────────────────────────────────────────────────────────

def ollama_generate(prompt: str, model: str = REASON_MODEL) -> str:
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 10}
    }).encode()
    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            return data.get("response", "").strip().upper()
    except Exception as e:
        return f"ERROR:{e}"


def ollama_embed(text: str) -> list:
    payload = json.dumps({
        "model": EMBED_MODEL,
        "prompt": text
    }).encode()
    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            return data.get("embedding", [])
    except Exception:
        return []


def cosine_similarity(a: list, b: list) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x**2 for x in a))
    mag_b = math.sqrt(sum(x**2 for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def ollama_available() -> bool:
    try:
        urllib.request.urlopen(f"{OLLAMA_BASE}/api/tags", timeout=3)
        return True
    except Exception:
        return False


# ─── Context Store ────────────────────────────────────────────────────────────

def load_context() -> list:
    if CONTEXT_STORE_PATH.exists():
        with open(CONTEXT_STORE_PATH) as f:
            return json.load(f)
    return []


def save_context(store: list):
    with open(CONTEXT_STORE_PATH, "w") as f:
        json.dump(store, f, indent=2)


def add_to_context(claim: str, state: str,
                   embedding: list = None,
                   past: str = "",
                   future: str = "") -> dict:
    """
    Every confirmed claim carries three time dimensions.
    Past: origin and lineage.
    Present: timestamp and current context (implicit).
    Future: implications and open questions.
    """
    store = load_context()
    entry = {
        "claim": claim,
        "state": state,
        "timestamp": time.time(),
        "embedding": embedding or [],
        "time": {
            "past": past or "origin unspecified",
            "present": time.strftime('%Y-%m-%d %H:%M:%S'),
            "future": future or "implications pending"
        }
    }
    store.append(entry)
    save_context(store)
    return entry


# ─── Negation Utilities ───────────────────────────────────────────────────────

NEGATION_WORDS = {"not", "never", "no", "false", "wrong", "incorrect", "opposite"}


def has_negation(text: str) -> bool:
    return bool(NEGATION_WORDS & set(text.lower().split()))


def share_keywords(a: str, b: str, min_shared: int = 2) -> bool:
    """Check if two claims share meaningful keywords."""
    stop = {"the", "a", "an", "is", "are", "was", "were",
            "it", "this", "that", "and", "or", "of", "to", "in"}
    words_a = set(a.lower().split()) - stop
    words_b = set(b.lower().split()) - stop
    return len(words_a & words_b) >= min_shared


# ─── 369 Audit Lenses ─────────────────────────────────────────────────────────

def lens_3_raw(claim: str) -> tuple:
    """
    Lens 3 - Raw coherence check.
    Fast, no LLM needed.
    """
    claim = claim.strip()
    if not claim:
        return False, "Empty claim"
    if len(claim.split()) < 2:
        return False, "Too short to evaluate"
    return True, "Raw input is coherent"


def lens_6_context(claim: str, context: list, claim_emb: list) -> tuple:
    """
    Lens 6 - Contradiction detection.
    Three-stage check:
      Stage A: Explicit negation + shared keywords (fast, reliable)
      Stage B: Semantic embedding similarity (only on related claims)
      Stage C: LLM direct contradiction check (final arbiter)
    """
    confirmed = [e for e in context if e.get("state") == "+"]
    if not confirmed:
        return True, "No confirmed context to contradict"

    claim_neg = has_negation(claim)

    for entry in confirmed:
        stored = entry.get("claim", "")
        stored_neg = has_negation(stored)

        if claim_neg != stored_neg and share_keywords(claim, stored, min_shared=2):
            return False, f"Negation contradiction with: '{stored[:60]}'"

        if share_keywords(claim, stored, min_shared=2) and claim_emb:
            stored_emb = entry.get("embedding", [])
            if stored_emb:
                sim = cosine_similarity(claim_emb, stored_emb)
                if sim > SIMILARITY_THRESHOLD and claim_neg != stored_neg:
                    return False, (
                        f"Semantic contradiction (sim={sim:.2f}) "
                        f"with: '{stored[:60]}'"
                    )

    if ollama_available() and confirmed:
        context_lines = "\n".join(
            f"- {e['claim']}" for e in confirmed[-5:]
        )
        prompt = (
            f"You are a strict logic checker.\n"
            f"Confirmed facts:\n{context_lines}\n\n"
            f"New claim: \"{claim}\"\n\n"
            f"Does the new claim directly contradict any confirmed fact?\n"
            f"Examples of contradiction: "
            f"'cats are mammals' contradicts 'cats are not mammals'.\n"
            f"Examples of NOT contradiction: "
            f"'dogs bark' does NOT contradict 'cats are mammals'.\n"
            f"Answer with exactly one word: YES or NO."
        )
        response = ollama_generate(prompt)
        if response.startswith("YES"):
            return False, "LLM confirmed contradiction with stored context"

    return True, "No contradictions detected"


def lens_9_integrity(claim: str) -> tuple:
    """
    Lens 9 - Structural integrity. The axis.

    Key principle: UNCERTAIN is not a failure state.
    Only OVERCONFIDENT triggers suspension.
    A small LLM defaulting to UNCERTAIN should not block valid claims.

    Returns:
      (True, reason)  → STABLE or UNCERTAIN → allow [+]
      (False, reason) → OVERCONFIDENT → route to [=]
      (None, reason)  → explicit suspension only on strong signal
    """
    claim_lower = claim.lower()

    # Stage 1: Fast pattern check for obvious overconfidence
    # These patterns are unambiguous — no LLM needed
    overconfidence_patterns = [
        r"\babsolutely certain\b",
        r"\bundeniable\b",
        r"\bproven fact\b",
        r"\bwithout any doubt\b",
        r"\b100 percent certain\b",
        r"\bimpossible to deny\b",
    ]
    hedging_patterns = [
        r"\bmaybe\b", r"\bperhaps\b", r"\bmight\b",
        r"\bcould be\b", r"\bpossibly\b", r"\bI think\b",
        r"\bI believe\b", r"\bseems\b", r"\bappears\b",
        r"\bunclear\b", r"\bsuggests\b", r"\blikely\b"
    ]

    overconfident = any(re.search(p, claim_lower) for p in overconfidence_patterns)
    hedged = any(re.search(p, claim_lower) for p in hedging_patterns)

    if overconfident and not hedged:
        return False, "Overconfident assertion — structurally unstable"

    if not ollama_available():
        return True, "Structural integrity holds (fallback)"

    prompt = (
        f"You are a strict logic auditor.\n"
        f"Evaluate this claim: \"{claim}\"\n\n"
        f"Is this claim making absolute assertions "
        f"without evidence or basis?\n"
        f"Examples of OVERCONFIDENT: "
        f"'This is certainly true', 'Everyone knows this', "
        f"'This is undeniable'.\n"
        f"Examples of NOT OVERCONFIDENT: "
        f"'The sky is blue', 'Perhaps X causes Y', "
        f"'Water boils at 100C'.\n\n"
        f"Answer with exactly one word: YES or NO.\n"
        f"YES = overconfident. NO = not overconfident."
    )

    response = ollama_generate(prompt).strip().upper()

    if response.startswith("YES"):
        return False, "LLM: Overconfident assertion detected"

    return True, "Lens 9 clear"


# ─── Tri-State Auditor ────────────────────────────────────────────────────────

class TriStateAuditor:
    def __init__(self):
        self.context = load_context()
        self.llm_up = ollama_available()
        status = f"{REASON_MODEL} + {EMBED_MODEL}" if self.llm_up else "OFFLINE"
        print(f"  [LLM] {status}")

    def refresh(self):
        self.context = load_context()
        self.llm_up = ollama_available()

    def audit(self, claim: str, **kwargs) -> dict:
        self.refresh()

        claim_emb = ollama_embed(claim) if self.llm_up else []

        l3, r3 = lens_3_raw(claim)
        if not l3:
            return self._out("-", 0.95, f"[L3] {r3}", "reject")

        l6, r6 = lens_6_context(claim, self.context, claim_emb)
        if not l6:
            return self._out("-", 0.88, f"[L6] {r6}", "reject")

        l9, r9 = lens_9_integrity(claim)
        if l9 is False:
            return self._out("=", 0.5, f"[L9] {r9}", "dream_layer")
        if l9 is None:
            return self._out("=", 0.4, f"[L9] {r9}", "dream_layer")

        add_to_context(claim, "+", claim_emb,
                      past=kwargs.get("past", ""),
                      future=kwargs.get("future", ""))
        return self._out("+", 0.92, "All 3 lenses pass", "surface")

    def _out(self, state, conf, reason, route):
        return {
            "state": state,
            "confidence": conf,
            "reason": reason,
            "route": route
        }


# ─── Dream Layer ──────────────────────────────────────────────────────────────

class DreamLayer:
    def __init__(self):
        self.queue = []
        self.auditor = TriStateAuditor()

    def receive(self, claim: str):
        self.queue.append({
            "claim": claim,
            "cycles": 0,
            "received": time.time()
        })
        self._log(f"[=] Received: {claim[:80]}")

    def process_cycle(self):
        still_pending = []
        for item in self.queue:
            item["cycles"] += 1
            result = self.auditor.audit(item["claim"])
            if result["state"] != "=":
                self._log(
                    f"[RESOLVED c{item['cycles']}] "
                    f"{result['state']} | {item['claim'][:60]}"
                )
            else:
                still_pending.append(item)
                self._log(
                    f"[PENDING c{item['cycles']}] {item['claim'][:60]}"
                )
        self.queue = still_pending

    def _log(self, msg):
        with open(DREAM_LOG_PATH, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

    def status(self):
        return f"Dream Layer: {len(self.queue)} suspended claims pending"


# ─── Main Loop ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== Cognitive Matrix v2.1 ===")
    print("States: [+] Confirmed | [-] Rejected | [=] Suspended\n")

    auditor = TriStateAuditor()
    dream = DreamLayer()

    print("\nCommands: 'dream' | 'context' | 'clear' | 'exit'\n")

    while True:
        try:
            user_input = input(">> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Exiting.")
            break

        if user_input.lower() == "clear":
            save_context([])
            auditor.refresh()
            print("  Context store cleared.\n")
            continue

        if user_input.lower() == "dream":
            dream.process_cycle()
            print(dream.status())
            continue

        if user_input.lower() == "context":
            ctx = load_context()
            if not ctx:
                print("  Context store empty.")
            for e in ctx:
                ts = time.strftime('%H:%M:%S', time.localtime(e['timestamp']))
                print(f"  [{e['state']}] {ts} | {e['claim'][:70]}")
            print()
            continue

        result = auditor.audit(user_input)
        state = result["state"]
        symbol = {"+": "[+]", "-": "[-]", "=": "[=]"}[state]
        print(f"\n{symbol} {result['reason']}")
        print(f"    Confidence: {result['confidence']:.0%} "
              f"| Route: {result['route']}\n")

        if state == "=":
            dream.receive(user_input)
            print("    → Routed to Dream Layer\n")
