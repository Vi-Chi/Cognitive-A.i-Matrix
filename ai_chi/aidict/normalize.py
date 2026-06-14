"""TermNormalizer — canonicalise AI terms, model/org/benchmark/hardware names.

Subtitles and social text mutate technical terms (ASR errors, casual spelling):
"Quinn" -> qwen, "sweet bench" -> swe-bench, "Halo" -> hailo. The doc flags this
as load-bearing: extraction quality on noisy ASR depends on a strong normalizer.
This v0 is deterministic (dictionaries + word-boundary regex), stdlib-only, so it
runs offline on the CM5 with no model dependency.
"""
from __future__ import annotations

import re

# Surface form (lowercased) -> canonical token. Order-independent; applied as
# whole-word replacements.
_TERM_MAP: dict[str, str] = {
    # model families / ASR mutations
    "quinn": "qwen", "qwenn": "qwen",
    "lama": "llama", "llamma": "llama", "lamma": "llama",
    "deepseek": "deepseek", "deep seek": "deepseek",
    "mixture of experts": "moe",
    "lora": "lora",  # canonicalise casing (LoRa -> lora) — distinct from LoRa radio in context
    "rlaif": "rlaif", "rlhf": "rlhf",
    # benchmarks
    "sweet bench": "swe-bench", "swe bench": "swe-bench", "swebench": "swe-bench",
    "human eval": "humaneval", "human-eval": "humaneval",
    "mmlu pro": "mmlu-pro",
    # hardware
    "halo": "hailo",  # common ASR mutation of Hailo
    "h 100": "h100", "h-100": "h100", "a 100": "a100",
    "raspberry pi": "raspberry-pi", "rasberry pi": "raspberry-pi",
    "cm 5": "cm5", "compute module 5": "cm5",
    # licensing
    "open weights": "open-weights", "open-weight": "open-weights",
}

# Build one regex alternation, longest-first so multiword forms win.
_SORTED = sorted(_TERM_MAP, key=len, reverse=True)
_PATTERN = re.compile(r"\b(" + "|".join(re.escape(t) for t in _SORTED) + r")\b", re.IGNORECASE)


def normalize_terms(text: str) -> str:
    """Return text with known surface forms replaced by canonical tokens."""

    def _sub(m: re.Match) -> str:
        return _TERM_MAP[m.group(0).lower()]

    return _PATTERN.sub(_sub, text)


def normalized_mutations(text: str) -> list[str]:
    """List the surface forms that were mutated (for technical_term_mutation patterns)."""
    found: list[str] = []
    for m in _PATTERN.finditer(text):
        surface = m.group(0).lower()
        if surface != _TERM_MAP[surface]:
            found.append(surface)
    return sorted(set(found))
