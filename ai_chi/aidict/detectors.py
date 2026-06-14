"""Deterministic v0 detectors — the cheap, reliable extraction layer.

Per the doc, AIDICT runs deterministic detectors *first* (regex + dictionaries),
before any LLM. These detectors:
  * type a claim (model_release / benchmark_claim / license_claim / ...),
  * extract entities (models, orgs, benchmarks, hardware),
  * flag hype language (audit-required, not false),
  * spot prediction phrases and obvious contradictions.

A sentence becomes a ``ClaimRecord`` only when it carries at least one signal
(an entity or a detector hit). Sentences with nothing are counted as noise —
classified, not discarded.

Extraction confidence is heuristic: how strongly the surface features indicate
the source actually made this claim. It is NOT a truth estimate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ai_chi.aidict.normalize import normalize_terms, normalized_mutations

# --- entity dictionaries (canonical tokens, post-normalisation) -------------
MODELS = {
    "gpt-4", "gpt-4o", "gpt-5", "o1", "o3", "claude", "llama", "qwen", "deepseek",
    "mistral", "mixtral", "gemini", "gemma", "phi", "r1", "grok", "command-r",
}
ORGS = {
    "openai", "anthropic", "google", "deepmind", "meta", "mistral", "alibaba",
    "hailo", "nvidia", "microsoft", "xai", "cohere",
}
BENCHMARKS = {
    "mmlu", "mmlu-pro", "swe-bench", "humaneval", "gsm8k", "arc", "gpqa",
    "mt-bench", "lmsys", "aime", "math",
}
HARDWARE = {
    "h100", "a100", "gpu", "cpu", "npu", "tpu", "hailo", "raspberry-pi", "cm5",
    "jetson", "coral", "rtx", "vram",
}
ALL_ENTITIES = MODELS | ORGS | BENCHMARKS | HARDWARE

# --- lexical signal banks ---------------------------------------------------
HYPE = {
    "revolutionary", "game changer", "game-changer", "agi", "kills all", "sota",
    "state of the art", "state-of-the-art", "leaked", "secret", "insane",
    "unbelievable", "100x", "10x", "no one is talking about", "mind-blowing",
    "breakthrough", "destroys", "obliterates", "crazy",
}
PREDICTION = {
    "will", "going to", "by 2026", "by 2027", "by 2028", "within a year",
    "within months", "soon", "next generation", "next-gen", "will replace",
    "will become", "is going to", "expect", "predict", "in the future",
}
OPEN_SOURCE = {"open source", "open-source", "open weights", "open-weights",
               "apache", "mit license", "permissive"}
LICENSE_RESTRICT = {"non-commercial", "noncommercial", "research only",
                    "research-only", "not for commercial", "restricted license",
                    "custom license", "no commercial use"}
LOCAL_INFER = {"runs locally", "run locally", "on-device", "on device", "edge",
               "offline", "local inference", "runs on a laptop", "single gpu"}
HEAVY_HW = {"8x h100", "8xh100", "cluster", "datacenter", "data center",
            "requires h100", "multiple gpus", "80gb", "needs a100"}
RELEASE = {"released", "launch", "launched", "now available", "shipping",
           "out now", "drops", "announced", "unveiled"}
UNAVAILABLE = {"not available", "not released", "no weights", "coming soon",
               "waitlist", "no public", "closed"}
BENCH_VERB = {"beats", "outperforms", "surpasses", "tops", "scores",
              "achieves", "sets a record", "best on", "leads on"}


@dataclass
class Detection:
    claim_type: str
    confidence: float
    entities: list[str] = field(default_factory=list)
    hype_markers: list[str] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)
    mutations: list[str] = field(default_factory=list)


def _hits(text_lc: str, bank: set[str]) -> list[str]:
    return sorted({term for term in bank if term in text_lc})


def find_entities(text_lc: str) -> list[str]:
    found = set()
    for ent in ALL_ENTITIES:
        # word-ish boundary; entities contain - and digits
        if re.search(rf"(?<![\w-]){re.escape(ent)}(?![\w-])", text_lc):
            found.add(ent)
    return sorted(found)


def classify(sentence: str) -> Detection:
    """Run all deterministic detectors on a single normalized sentence."""
    norm = normalize_terms(sentence)
    lc = norm.lower()

    entities = find_entities(lc)
    hype = _hits(lc, HYPE)
    mutations = normalized_mutations(sentence)

    flags: set[str] = set()
    if _hits(lc, OPEN_SOURCE):
        flags.add("open_source")
    if _hits(lc, LICENSE_RESTRICT):
        flags.add("license_restrict")
    if _hits(lc, LOCAL_INFER):
        flags.add("local_inference")
    if _hits(lc, HEAVY_HW):
        flags.add("heavy_hardware")
    if _hits(lc, RELEASE):
        flags.add("release")
    if _hits(lc, UNAVAILABLE):
        flags.add("unavailable")
    if _hits(lc, BENCH_VERB) and (entities or "benchmark" in lc):
        flags.add("benchmark")
    if _hits(lc, PREDICTION):
        flags.add("prediction")

    # --- claim typing (priority order) ---
    # Benchmark claim beats most things; prediction beats opinion.
    if "benchmark" in flags or (set(BENCHMARKS) & set(entities)):
        claim_type = "benchmark_claim"
        conf = 0.8
    elif "license_restrict" in flags and "open_source" in flags:
        claim_type = "license_claim"
        conf = 0.85
    elif "license_restrict" in flags:
        claim_type = "license_claim"
        conf = 0.75
    elif "open_source" in flags:
        claim_type = "open_source_claim"
        conf = 0.75
    elif "heavy_hardware" in flags or (set(HARDWARE) & set(entities)):
        claim_type = "hardware_requirement_claim"
        conf = 0.75
    elif "local_inference" in flags:
        claim_type = "local_inference_claim"
        conf = 0.75
    elif "release" in flags:
        claim_type = "model_release"
        conf = 0.7
    elif "unavailable" in flags:
        claim_type = "rumor"
        conf = 0.6
    elif "prediction" in flags:
        claim_type = "prediction"
        conf = 0.7
    elif entities:
        claim_type = "technical_report"
        conf = 0.55
    else:
        claim_type = "opinion"
        conf = 0.3

    # Hype raises *audit-required* salience but does NOT raise truth confidence.
    if hype:
        flags.add("hype")
        conf = min(0.95, conf + 0.05)

    return Detection(
        claim_type=claim_type,
        confidence=round(conf, 3),
        entities=entities,
        hype_markers=hype,
        flags=flags,
        mutations=mutations,
    )


# --- intra-sentence contradiction (self-contradicting claim) ----------------
def self_contradiction(detection: Detection) -> str:
    """Return a contradiction label if a single claim asserts opposing things."""
    f = detection.flags
    if "open_source" in f and "license_restrict" in f:
        return "open_source vs restrictive_license"
    if "local_inference" in f and "heavy_hardware" in f:
        return "runs_locally vs heavy_hardware"
    if "release" in f and "unavailable" in f:
        return "released vs not_available"
    return ""


def is_prediction(detection: Detection) -> bool:
    return detection.claim_type == "prediction" or "prediction" in detection.flags
