"""ContractFactory — turn a typed ClaimRecord into an investigation contract.

Each claim type maps to a contract type, a validation checklist, the evidence
that would satisfy it, and the verification tasks that would gather that
evidence. Risk and learning_value are derived from hype, self-contradiction,
and claim type (learning_value feeds Autopoiesis curiosity budgeting).

If an Urbi verdict is available, it sets the opening contract status:
    [+] confirmed -> partially_satisfied   (source asserts it; primary evidence still owed)
    [-] rejected  -> contradicted          (a 3-6-9 lens fired — overconfidence/contradiction)
    [=] suspended -> open                   (the precious state: genuinely needs verification)
"""
from __future__ import annotations

from ai_chi.aidict.detectors import Detection, self_contradiction
from ai_chi.aidict.schemas import ClaimRecord, ContractRecord, VerificationTask

# claim_type -> (contract_type, validation_requirements, required_evidence, task_specs)
# task_specs: list of (task_type, query_template, priority)
_CONTRACT_MAP: dict[str, tuple[str, list[str], list[str], list[tuple[str, str, str]]]] = {
    "benchmark_claim": (
        "benchmark_validation",
        ["Find primary source", "Check benchmark method", "Check independent reproduction"],
        ["paper", "benchmark result", "independent test"],
        [("check_arxiv", "paper for: {claim}", "high"),
         ("check_benchmark", "benchmark method + leaderboard for: {entities}", "high"),
         ("check_independent_replication", "independent replication of: {claim}", "medium")],
    ),
    "open_source_claim": (
        "license_validation",
        ["Check license terms", "Check weights availability"],
        ["license", "model card", "official repo"],
        [("check_license", "license terms for: {entities}", "high"),
         ("check_huggingface", "weights + model card for: {entities}", "medium")],
    ),
    "license_claim": (
        "license_validation",
        ["Resolve license conflict", "Check exact license text"],
        ["license", "official repo"],
        [("check_license", "exact license + commercial terms for: {entities}", "critical"),
         ("check_github", "LICENSE file in repo for: {entities}", "high")],
    ),
    "hardware_requirement_claim": (
        "hardware_validation",
        ["Check hardware feasibility", "Check quantization options"],
        ["model card", "benchmark result"],
        [("check_hardware_feasibility", "VRAM/compute needs for: {claim}", "high"),
         ("check_huggingface", "quantized variants for: {entities}", "medium")],
    ),
    "local_inference_claim": (
        "hardware_validation",
        ["Check local hardware feasibility", "Check quantization"],
        ["model card", "independent test"],
        [("check_hardware_feasibility", "edge feasibility (CM5/Hailo) for: {claim}", "high")],
    ),
    "model_release": (
        "release_validation",
        ["Find primary source", "Check model availability"],
        ["official lab post", "model card", "official repo"],
        [("check_official_lab_post", "official announcement of: {claim}", "high"),
         ("check_huggingface", "released weights for: {entities}", "medium")],
    ),
    "prediction": (
        "prediction_validation",
        ["Define measurable condition", "Set review date"],
        ["future outcome"],
        [("check_primary_source", "track measurable condition of: {claim}", "low")],
    ),
    "rumor": (
        "release_validation",
        ["Find primary source"],
        ["official lab post"],
        [("check_primary_source", "confirm/deny: {claim}", "medium")],
    ),
    "technical_report": (
        "release_validation",
        ["Find primary source"],
        ["paper", "official repo"],
        [("check_primary_source", "primary source for: {claim}", "low")],
    ),
    "opinion": (
        "prediction_validation",
        ["No verification (opinion) — monitor only"],
        [],
        [],
    ),
}

_RISK = {"critical": 4, "high": 3, "medium": 2, "low": 1}
_RISK_INV = {v: k for k, v in _RISK.items()}

# Urbi tri-state verdict -> attached audit signal (never a contract state).
_AUDIT_SIGNAL = {
    "+": "audit_support_signal",
    "-": "audit_contradiction_signal",
    "=": "audit_suspended",
    "": "pending",
}


def _entities_str(claim: ClaimRecord) -> str:
    return ", ".join(claim.entities) if claim.entities else claim.normalized_claim[:60]


def build_contract(
    claim: ClaimRecord,
    detection: Detection,
    *,
    verdict: str = "",
    verdict_reason: str = "",
) -> tuple[ContractRecord, list[VerificationTask]]:
    """Build a ContractRecord + its VerificationTasks for one claim."""
    spec = _CONTRACT_MAP.get(claim.claim_type, _CONTRACT_MAP["technical_report"])
    contract_type, requirements, required_evidence, task_specs = spec

    tasks: list[VerificationTask] = []
    for task_type, template, priority in task_specs:
        query = template.format(claim=claim.normalized_claim, entities=_entities_str(claim))
        tasks.append(VerificationTask(
            claim_id=claim.claim_id,
            task_type=task_type,
            query=query,
            reason=f"{claim.claim_type} requires primary-source validation",
            priority=priority,
        ))

    # --- risk + learning value ---
    contradiction = self_contradiction(detection)
    risk_score = 2
    if detection.hype_markers:
        risk_score += 1
    if contradiction:
        risk_score += 1
    if claim.claim_type in ("license_claim", "benchmark_claim"):
        risk_score += 1
    risk_score = min(4, risk_score)
    risk_level = _RISK_INV[risk_score]

    # Learning value: hardware/edge + contradictions + hype are most worth testing
    # locally on the CM5 (Vento-Vivere relevance).
    lv = 0.4
    if claim.claim_type in ("local_inference_claim", "hardware_requirement_claim"):
        lv += 0.3
    if contradiction:
        lv += 0.2
    if detection.hype_markers:
        lv += 0.1
    learning_value = round(min(1.0, lv), 3)

    # Balance-constitution §7.3: Urbi's verdict is an ATTACHED AUDIT SIGNAL, it does
    # NOT mutate the contract's legal/scientific state. Contract status is
    # EVIDENCE-DRIVEN — it stays `open` until a ValidationRecord satisfies it. Only
    # the absence of any investigation path (opinions) marks a contract `expired`.
    audit_signal = _AUDIT_SIGNAL.get(verdict, "pending")
    status = "open"
    if claim.claim_type == "opinion" and not task_specs:
        status = "expired"  # nothing to investigate; not a verdict-driven state

    requirements = list(requirements)
    if contradiction:
        requirements = [f"Resolve internal contradiction: {contradiction}"] + requirements

    contract = ContractRecord(
        claim_id=claim.claim_id,
        contract_type=contract_type,
        validation_requirements=requirements,
        required_evidence=required_evidence,
        verification_task_ids=[t.task_id for t in tasks],
        current_status=status,
        risk_level=risk_level,
        learning_value=learning_value,
        audit_verdict=verdict,
        audit_signal=audit_signal,
        audit_reason=verdict_reason,
        audit_required=bool(task_specs),
    )
    return contract, tasks
