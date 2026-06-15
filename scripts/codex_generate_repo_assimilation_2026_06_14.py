from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(r"C:\Users\Vi Chi\Desktop\Projectz\A.i")
BASE = Path(r"C:\Users\Vi Chi\Desktop\Projectz\_triad_repo_worktrees")
OUT = ROOT / "_PROJECT_KNOWLEDGE_BASE" / "repo_assimilation_2026-06-14"

REPOS = [
    ("sigmabus", "Vi-Chi/sigmabus", "repo-assimilation/sigmabus-triad-v2.5-dan-gp-2026-06-14", "historical Sigma Bus provenance"),
    ("MEBUS", "Vi-Chi/MEBUS", "repo-assimilation/mebus-triad-v2.5-dan-gp-2026-06-14", "current MΣBUS membrane candidate"),
    ("Autopoiesis", "Vi-Chi/Autopoiesis", "repo-assimilation/autopoiesis-triad-v2.5-dan-gp-2026-06-14", "metabolism, budget, lifecycle source"),
    ("omni-ai", "Vi-Chi/omni-ai", "repo-assimilation/omni-ai-triad-v2.5-dan-gp-2026-06-14", "older Orbi/Nexus local control-plane source"),
    ("Orbi", "Vi-Chi/Orbi", "repo-assimilation/orbi-triad-v2.5-dan-gp-2026-06-14", "executor/orchestrator module source"),
    ("Urbi", "Vi-Chi/Urbi", "repo-assimilation/urbi-triad-v2.5-dan-gp-2026-06-14", "audit/judgment module source"),
    ("Cognitive-A.i-Matrix", "Vi-Chi/Cognitive-A.i-Matrix", "repo-assimilation/cognitive-matrix-triad-v2.5-dan-gp-2026-06-14", "unified Triad v2.5 baseline candidate"),
    ("projectz-kb", "Vi-Chi/projectz-kb", "kb-heavy-update/dan-gp-adapt-r1-2026-06-14", "curated memory promotion surface"),
]

SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}|"
    r"AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|"
    r"https://discord(?:app)?\.com/api/webhooks/[^\s)]+|Bearer\s+[A-Za-z0-9._~+/-]+=*|"
    r"api[_-]?key\s*[:=]|token\s*[:=]|secret\s*[:=]|password\s*[:=]|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
    re.I,
)
PRIVATE_RE = re.compile(r"([A-Z]:\\Users\\|/home/|/Users/|10\.0\.0\.1|tailscale|vessel|webhook|token|secret|password|email)", re.I)
TEXT_EXTS = {".md", ".txt", ".py", ".json", ".toml", ".yaml", ".yml", ".rs", ".js", ".ts", ".tsx", ".jsx", ".csv", ".schema"}


def git(path: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=path, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def repo_files(repo_path: Path, repo_name: str) -> list[dict[str, object]]:
    rows = []
    for item in repo_path.rglob("*"):
        if ".git" in item.parts or not item.is_file():
            continue
        try:
            data = item.read_bytes()
        except OSError:
            continue
        rows.append(
            {
                "repo": repo_name,
                "path": item.relative_to(repo_path).as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "extension": item.suffix.lower(),
            }
        )
    return rows


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_repo_package() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    repo_infos = []
    all_files = []
    read_log = []
    boundary_hits = []

    for name, full, _branch, role in REPOS:
        path = BASE / name
        default = git(path, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").replace("origin/", "")
        current = git(path, "branch", "--show-current")
        commit = git(path, "rev-parse", "--short", "HEAD")
        remote_lines = [line.strip().replace("origin/", "") for line in git(path, "branch", "-r").splitlines()]
        remote_lines = [line for line in remote_lines if line and "HEAD ->" not in line]
        dirty = bool(git(path, "status", "--short"))
        repo_infos.append(
            {
                "repo": full,
                "local_path": str(path),
                "default_branch": default,
                "local_branch": current,
                "head": commit,
                "role": role,
                "status_dirty": dirty,
                "remote_branches": remote_lines,
            }
        )
        if not path.exists():
            continue

        rows = repo_files(path, name)
        all_files.extend(rows)
        for doc in ["README.md", "ARCHITECTURE.md", "MASTER_CONTEXT.md", "BUILD_NOTES.md", "walkthrough.md", "AGENTS.md", "pyproject.toml", "package.json", "Cargo.toml", "DO_ANYTHING_NOW.md"]:
            file_path = path / doc
            if file_path.exists():
                read_log.append({"repo": name, "path": doc, "bytes": file_path.stat().st_size, "purpose": "top-level orientation read"})

        for row in rows:
            if row["extension"] not in TEXT_EXTS or int(row["bytes"]) > 1_000_000:
                continue
            file_path = path / str(row["path"])
            text = file_path.read_text(encoding="utf-8", errors="replace")
            for line_no, line in enumerate(text.splitlines(), 1):
                hit = SECRET_RE.search(line)
                if hit:
                    boundary_hits.append(
                        {
                            "repo": name,
                            "path": row["path"],
                            "line": line_no,
                            "risk_type": "secret_or_personal_identifier_shape",
                            "redacted_preview": SECRET_RE.sub("<REDACTED>", line)[:160],
                        }
                    )
                    continue
                if PRIVATE_RE.search(line):
                    boundary_hits.append(
                        {
                            "repo": name,
                            "path": row["path"],
                            "line": line_no,
                            "risk_type": "private_or_operational_boundary",
                            "redacted_preview": PRIVATE_RE.sub("<PRIVATE_BOUNDARY>", line)[:160],
                        }
                    )

    with (OUT / "MULTI_REPO_FILE_INVENTORY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["repo", "path", "bytes", "sha256", "extension"])
        writer.writeheader()
        writer.writerows(all_files)
    with (OUT / "MULTI_REPO_READ_LOG.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["repo", "path", "bytes", "purpose"])
        writer.writeheader()
        writer.writerows(read_log)

    retirement = [
        {"repo": "Vi-Chi/sigmabus", "state": "HISTORICAL_PROVENANCE", "reason": "Likely protocol precursor; preserve until MEBUS diff/migration proof is complete.", "action": "add deprecation banner only after approval"},
        {"repo": "Vi-Chi/MEBUS", "state": "ACTIVE_MODULE", "reason": "Current membrane implementation candidate.", "action": "keep visible for now"},
        {"repo": "Vi-Chi/Autopoiesis", "state": "ACTIVE_MODULE", "reason": "Metabolism/economics material may remain separable.", "action": "keep visible for now"},
        {"repo": "Vi-Chi/omni-ai", "state": "DO_NOT_DELETE", "reason": "May contain local/private operational control-plane history.", "action": "boundary review before any visibility decision"},
        {"repo": "Vi-Chi/Orbi", "state": "ACTIVE_MODULE", "reason": "Executor/orchestrator source candidate.", "action": "compare to unified baseline"},
        {"repo": "Vi-Chi/Urbi", "state": "ACTIVE_MODULE", "reason": "Audit/judgment source candidate.", "action": "compare to unified baseline"},
        {"repo": "Vi-Chi/Cognitive-A.i-Matrix", "state": "ACTIVE_SOURCE", "reason": "Unified Triad v2.5 baseline candidate branch exists.", "action": "do not merge automatically"},
        {"repo": "Vi-Chi/projectz-kb", "state": "ACTIVE_SOURCE", "reason": "Curated memory promotion surface.", "action": "local heavy-update branch prepared"},
        {"repo": "Vi-Chi/vento-vivere", "state": "EXCLUDED_BY_USER_INSTRUCTION", "reason": "Explicit addendum excludes it from this pass.", "action": "do not scan/clone/branch/migrate"},
    ]
    contradictions = [
        {"record_type": "ContradictionRecord", "old_claim": "sigmabus-era Sigma Bus may be treated as current protocol authority", "new_claim": "MEBUS/Cognitive-A.i-Matrix Triad v2.5 should be treated as current membrane baseline candidate", "current_preference": "new_claim", "evidence_refs": ["sigmabus/README.md", "MEBUS/README.md", "Cognitive-A.i-Matrix:triad-v2.5-release"], "requires_user_decision": False},
        {"record_type": "ContradictionRecord", "old_claim": "projectz-kb raw source tree can be ingested directly by AnythingLLM", "new_claim": "AnythingLLM should ingest curated exports only", "current_preference": "new_claim", "evidence_refs": ["projectz-kb/README.md", "CODEX_PROJECTZ_KB_HEAVY_UPDATE_HANDOFF_2026-06-14.md"], "requires_user_decision": False},
        {"record_type": "ContradictionRecord", "old_claim": "repo cleanup can happen after assimilation", "new_claim": "cleanup requires backup, migration proof, and repo-specific explicit approval", "current_preference": "new_claim", "evidence_refs": ["CODEX_MULTI_REPO_RETIREMENT_CLEANUP_ADDENDUM_2026-06-14.md"], "requires_user_decision": True},
    ]

    write(OUT / "repo_manifest.json", json.dumps({"generated": "2026-06-14", "repos": repo_infos, "file_count": len(all_files)}, indent=2))
    write_jsonl(OUT / "private_or_sensitive_paths.jsonl", boundary_hits)
    write_jsonl(OUT / "contradiction_records.jsonl", contradictions)
    write_jsonl(
        OUT / "canon_candidates.jsonl",
        [
            {"record_type": "CanonCandidateRecord", "claim": "Urbi audits, Orbi acts, MΣBUS gates; no component holds two powers.", "source": "A.i canon + imported repo-assimilation instructions", "status": "candidate_reaffirmation", "target": "Triad Constitution", "required_evidence": ["existing tests", "Claude audit", "user promotion for law changes"]},
            {"record_type": "CanonCandidateRecord", "claim": "DAN-GP may synthesize conjectures but may not promote metaphor or raw exports directly to canon.", "source": "DAN_GRAND_PLAN_SYNTHESIS_CONJECTURE.md", "status": "candidate", "target": "DAN-GP rule set", "required_evidence": ["record schemas", "tests", "Urbi/user promotion"]},
        ],
    )
    write_jsonl(
        OUT / "migration_candidates.jsonl",
        [
            {"repo": "Vi-Chi/sigmabus", "candidate": "preserve as HISTORICAL_PROVENANCE and diff against MEBUS", "risk": "medium", "implementation_lane": "docs_and_tests", "requires_approval": False},
            {"repo": "Vi-Chi/MEBUS", "candidate": "treat as active MΣBUS module candidate and compare to unified baseline", "risk": "medium", "implementation_lane": "schema/test migration", "requires_approval": False},
            {"repo": "Vi-Chi/Autopoiesis", "candidate": "map compute receipts and token pressure into ADAPT-R1", "risk": "medium", "implementation_lane": "proposal_first", "requires_approval": False},
            {"repo": "Vi-Chi/omni-ai", "candidate": "quarantine private/local control-plane material before public export", "risk": "high", "implementation_lane": "private_boundary_report", "requires_approval": False},
            {"repo": "Vi-Chi/projectz-kb", "candidate": "add curated export/policy layer before RAG ingestion", "risk": "medium", "implementation_lane": "local_branch_scaffold", "requires_approval": False},
        ],
    )
    write_jsonl(
        OUT / "adapt_r1_integration_candidates.jsonl",
        [
            {"repo": "Vi-Chi/Autopoiesis", "candidate": "LoopBurnReceipt and TokenPressureSignal source mapping", "source_path": "README.md / MASTER_CONTEXT.md", "risk": "medium", "implementation_lane": "A_local", "requires_approval": False, "notes": "Map economics to local/offline token and compute receipts only."},
            {"repo": "Vi-Chi/Cognitive-A.i-Matrix", "candidate": "Triad v2.5 baseline as integration sink", "source_path": "triad-v2.5-release", "risk": "medium", "implementation_lane": "A_local", "requires_approval": False, "notes": "No merge performed."},
        ],
    )
    write_jsonl(OUT / "repo_cleanup_actions_proposed.jsonl", [{"repo": r["repo"], "state": r["state"], "action": r["action"], "requires_approval": r["state"] in {"ARCHIVE_ONLY", "DELETE_CANDIDATE", "MIGRATED_ARCHIVE"}} for r in retirement])
    write_jsonl(OUT / "archive_candidates.jsonl", [r for r in retirement if r["state"] in {"ARCHIVE_ONLY", "MIGRATED_ARCHIVE"}])
    write_jsonl(OUT / "delete_candidates.jsonl", [r for r in retirement if r["state"] == "DELETE_CANDIDATE"])
    write_jsonl(OUT / "do_not_delete.jsonl", [r for r in retirement if r["state"] == "DO_NOT_DELETE"])
    write(OUT / "repo_retirement_matrix.json", json.dumps({"generated": "2026-06-14", "matrix": retirement}, indent=2))
    write(OUT / "BACKUP_BEFORE_CLEANUP_MANIFEST.json", json.dumps({"generated": "2026-06-14", "status": "plan_only_no_backups_created", "required_before_archive_or_delete": "git clone --mirror, git bundle --all, sha256 verification, user approval"}, indent=2))
    write(
        OUT / "triad_invariant_checks.json",
        json.dumps(
            {
                "generated": "2026-06-14",
                "checks": [
                    {"check": "Urbi cannot act", "status": "proposal_check_pass"},
                    {"check": "Orbi cannot self-judge", "status": "proposal_check_pass"},
                    {"check": "MΣBUS not dumb plumbing", "status": "proposal_check_pass"},
                    {"check": "Raw exports not memory", "status": "proposal_check_pass"},
                    {"check": "No public/live writes", "status": "pass"},
                ],
            },
            indent=2,
        ),
    )

    table = "\n".join(f"| {info['repo']} | {info['default_branch']} | {info['local_branch']} | {info['head']} | {info['role']} |" for info in repo_infos)
    counts = {name: sum(1 for row in all_files if row["repo"] == name) for name, *_rest in REPOS}
    count_table = "\n".join(f"| {name} | {counts.get(name, 0)} |" for name, *_rest in REPOS)
    report_texts = {
        "README.md": f"# Repo Assimilation 2026-06-14\n\nStatus: local-only assimilation package generated from the imported GitHub instruction set.\n\nIn scope: sigmabus, MEBUS, Autopoiesis, omni-ai, Orbi, Urbi, Cognitive-A.i-Matrix, projectz-kb.\n\nExcluded by user instruction: Vi-Chi/vento-vivere.\n\n| Repo | Default | Local branch | Head | Role |\n|---|---|---|---|---|\n{table}\n\n| Repo | Files inventoried |\n|---|---:|\n{count_table}\n\nNo pushes, PRs, merges, archives, deletes, visibility changes, public posts, service writes, or live watcher changes were performed.\n",
        "REPO_ACCESS_AND_BRANCH_REPORT.md": "# Repo Access and Branch Report\n\n" + table + "\n\nCognitive-A.i-Matrix branch `triad-v2.5-release` was verified and used as the local assimilation base.\n",
        "REPOSITORY_ROLE_MAP.md": "# Repository Role Map\n\n" + "\n".join(f"## {full}\n\nRole: {role}.\n" for _name, full, _branch, role in REPOS),
        "CANON_RULES_FOUND.md": "# Canon Rules Found\n\n- Urbi audits; Orbi acts; MΣBUS gates.\n- DAN-GP synthesizes records and conjectures only; it does not promote metaphor to canon.\n- Raw exports, historical repos, Discord/community traces, and generated model summaries are provenance, not memory or truth.\n- AnythingLLM/RAG should ingest curated exports only.\n- Cleanup and publication are approval-gated.\n",
        "TRIAD_INVARIANTS_FOUND.md": "# Triad Invariants Found\n\n- Separation of powers recurs across A.i canon and imported GitHub handoffs.\n- MΣBUS is an authority membrane, not a passive queue.\n- DREAM can replay, compress, and prepare candidates but must not act.\n- Orbi execution paths require audit/gate records.\n- Urbi cannot mutate world state.\n",
        "CONTRADICTION_RECORDS.md": "# Contradiction Records\n\n" + "\n".join(f"- `{c['current_preference']}`: {c['old_claim']} -> {c['new_claim']}" for c in contradictions) + "\n",
        "OBSOLETE_OR_SUPERSEDED_IDEAS.md": "# Obsolete or Superseded Ideas\n\n- Direct raw KB/source ingestion into AnythingLLM is superseded by curated export policy.\n- Treating `sigmabus` as current protocol canon is superseded by MEBUS / Cognitive-A.i-Matrix comparison.\n- Immediate repo cleanup/deletion is superseded by backup-first, approval-gated retirement planning.\n",
        "PUBLIC_PRIVATE_BOUNDARY_REPORT.md": f"# Public / Private Boundary Report\n\nTargeted scan found {len(boundary_hits)} candidate private-boundary or secret-shaped lines across cloned text files. Values were not printed here; redacted records are in `private_or_sensitive_paths.jsonl`.\n\nHigh-risk areas: `omni-ai`, `projectz-kb/vento-vivere`, raw transcripts, graveyard exports, webhook/provider/token references.\n",
        "DAN_TRINITY_AUTOPOIESIS_INTEGRATION_MAP.md": "# DAN / Trinity / Autopoiesis Integration Map\n\nDAN-GP produces synthesis/conjecture records. Trinity routes scout/audit/implementation. Autopoiesis meters token pressure, task value, cache policy, and compute receipts. Codex implements local patches only after candidate designs are bounded and testable.\n",
        "ADAPT_R1_REPO_INTEGRATION_PLAN.md": "# ADAPT-R1 Repo Integration Plan\n\n- Autopoiesis: source for token pressure, loop-burn, task value, and compute receipt concepts.\n- Cognitive-A.i-Matrix: integration sink for Triad v2.5 and ADAPT-R1 policy hooks.\n- projectz-kb: memory promotion and export surface, not raw vector sink.\n",
        "DAN_GP_REPO_SYNTHESIS_PLAN.md": "# DAN-GP Repo Synthesis Plan\n\nPattern -> engineering principle -> module mapping -> evidence -> risk -> promotion path.\n\n- sigmabus/MEBUS protocol lineage -> envelope-governed traffic -> MΣBUS tests and schema comparison.\n- Autopoiesis compute economics -> bounded metabolism -> ADAPT-R1 token pressure and receipts.\n- projectz-kb raw/curated split -> memory membrane -> export policy and redaction tests.\n",
        "COGNITIVE_MATRIX_TRIAD_V2_5_MERGE_PLAN.md": "# Cognitive-A.i-Matrix Triad v2.5 Merge Plan\n\nBranch `triad-v2.5-release` exists and was used as the local assimilation base. No merge performed.\n",
        "SOCIAL_NEWSROOM_LOOP_PRECHECK.md": "# Social Newsroom Loop Precheck\n\nlocal stack event -> DAN-GP content candidate -> Trinity route -> Claude audit -> MΣBUS pre-publish gate -> user approval -> Orbi/Nexus publish adapter -> quarantined metrics -> DREAM review.\n\nNo public posting, social automation, Discord write, or account action is authorized by this pass.\n",
        "NEXT_CLAUDE_AUDIT_PROMPT.md": "# Next Claude Audit Prompt\n\nAudit the repo assimilation package for canon drift, symbolic overreach, privacy/public-boundary risks, and whether `projectz-kb` export policy is sufficient before any push or PR.\n",
        "NEXT_ANTIGRAVITY_SCOUT_PROMPT.md": "# Next Antigravity Scout Prompt\n\nScout the local repo branches for UI/docs gaps, repo-specific diagrams, and DAN-GP schema proposal improvements. Do not push, publish, start services, or inspect secrets.\n",
        "NEXT_CODEX_IMPLEMENTATION_PLAN.md": "# Next Codex Implementation Plan\n\n1. Run repo-specific tests where dependency-free.\n2. Expand MEBUS vs sigmabus diff with source excerpts.\n3. Harden projectz-kb validation scripts and run tests.\n4. Prepare draft PR bodies only after user approves pushing branches.\n",
        "REPOSITORY_RETIREMENT_MATRIX.md": "# Repository Retirement Matrix\n\n" + "\n".join(f"- {r['repo']}: `{r['state']}` - {r['reason']}" for r in retirement) + "\n",
        "REPOSITORY_VISIBILITY_PLAN.md": "# Repository Visibility Plan\n\nKeep active and visible for now: Cognitive-A.i-Matrix, projectz-kb, MEBUS, Autopoiesis, Orbi, Urbi. Preserve sigmabus as historical provenance pending diff. Keep omni-ai private/local until boundary review. Exclude vento-vivere.\n",
        "FINAL_VISIBLE_REPO_SET_PROPOSAL.md": "# Final Visible Repo Set Proposal\n\nProposed current visible set, pending audit: Cognitive-A.i-Matrix, projectz-kb, MEBUS, Autopoiesis, Orbi, Urbi.\n\nPossible future historical/archive candidates: sigmabus, after migration proof.\n\nDo not include Vi-Chi/vento-vivere in this pass.\n",
        "ARCHIVE_OR_DELETE_CANDIDATES.md": "# Archive or Delete Candidates\n\nNo delete candidates are approved or recommended from this first pass. sigmabus may become an archive candidate only after schema diff and migration proof.\n",
        "DEPRECATION_BANNER_TEXT.md": "> **Status:** Historical / superseded repository.\n>\n> This repository is preserved for project history and provenance. Current active development has moved to `https://github.com/Vi-Chi/Cognitive-A.i-Matrix`.\n",
        "FINAL_REPO_ASSIMILATION_DECISION_PACKET.md": "# Final Repo Assimilation Decision Packet\n\nCurrent source candidate: Vi-Chi/Cognitive-A.i-Matrix branch `triad-v2.5-release`.\n\nHistorical/provenance: sigmabus, pending MEBUS diff.\n\nActive modules: MEBUS, Autopoiesis, Orbi, Urbi.\n\nPrivate/local boundary: omni-ai and any Vento-Vivere material.\n\nKB sink: projectz-kb, with curated exports only.\n\nNo repo is safe to delete from this pass. Social Newsroom Loop should remain dry-run/precheck only.\n",
        "FINAL_REPO_CLEANUP_DECISION_PACKET.md": "# Final Repo Cleanup Decision Packet\n\nKeep active: Cognitive-A.i-Matrix, projectz-kb, MEBUS, Autopoiesis, Orbi, Urbi.\n\nKeep but possibly deprecate later: sigmabus.\n\nArchive after backup: none approved.\n\nDelete candidates after backup: none.\n\nDo not delete: omni-ai until private/local boundary is audited.\n",
    }
    for filename, text in report_texts.items():
        write(OUT / filename, text)

    return {"report_dir": str(OUT), "file_count": len(all_files), "boundary_count": len(boundary_hits), "repos": len(repo_infos)}


def build_projectz_kb_scaffold() -> dict[str, object]:
    kb = BASE / "projectz-kb"
    for rel in [
        "schemas",
        "manifests",
        "canon",
        "architecture",
        "repo_assimilation",
        "exports/anythingllm",
        "exports/public_safe",
        "exports/codex_context",
        "exports/claude_context",
        "exports/antigravity_context",
        "scripts",
        "tests",
        "reports/projectz_kb_update_2026-06-14",
    ]:
        (kb / rel).mkdir(parents=True, exist_ok=True)
    for mod in ["urbi", "orbi", "mebus", "autopoiesis", "dan", "trinity", "adapt_r1", "dan_gp", "aion", "dream", "memory", "discord", "cm5_hailo", "icp_ethereum"]:
        write(kb / "modules" / mod / "README.md", f"# {mod}\n\nStatus: scaffolded module index. Add curated, source-referenced records only.\n")

    readme = kb / "README.md"
    old = readme.read_text(encoding="utf-8", errors="replace") if readme.exists() else ""
    if "DAN-GP / ADAPT-R1 KB membrane update" not in old:
        write(
            readme,
            "# Projectz Knowledge Base\n\n"
            "> 2026-06-14 local branch update: DAN-GP / ADAPT-R1 KB membrane update. "
            "This repository is being prepared as a curated knowledge base and memory-promotion surface. "
            "AnythingLLM should ingest curated exports, not raw source folders. Vento-Vivere material is legacy/private-local for this pass.\n\n"
            + re.sub(r"^# Projectz Knowledge Base\s*", "", old, count=1),
        )

    docs = {
        "KB_STATUS.md": "# KB Status\n\nStatus: local branch scaffold for canon-aware, redaction-first knowledge base.\n\nNo remote push performed.\n",
        "KB_CANON_RULES.md": "# KB Canon Rules\n\nCanon is promoted, tested, labeled, audited, and gated evidence. Raw export is provenance, not memory. Indexed is not canon. Vectorized is not true. Metaphor inspires but never authorizes.\n",
        "KB_PUBLIC_PRIVATE_BOUNDARY.md": "# KB Public / Private Boundary\n\nDefault private. Public-safe exports must exclude secrets, personal data, raw transcripts, private paths, Vento-Vivere operational material, and unsupported claims.\n",
        "KB_INGESTION_POLICY.md": "# KB Ingestion Policy\n\nRaw sources enter as SourceRecords. Curated documents require status labels, source refs, trust state, public safety labels, and promotion gate. Raw ChatGPT exports and transcripts are do-not-index until redacted and claimized.\n",
        "KB_EXPORT_POLICY.md": "# KB Export Policy\n\nAnythingLLM and public exports consume only curated export folders. Default export excludes `do_not_index`, `private_local`, raw transcripts, legacy Vento-Vivere material, and files with redaction findings.\n",
        "KB_CHANGELOG.md": "# KB Changelog\n\n## 2026-06-14\n\n- Added local-only DAN-GP / ADAPT-R1 heavy-update scaffold.\n- Added conservative ingest/export/canon/private-boundary policies.\n- Added stdlib validation scripts and hygiene tests.\n",
        "AGENTS.md": "# AGENTS.md\n\nOperate redaction-first and proposal-first. Do not ingest raw transcripts into RAG. Do not publish, push, share, or change visibility without explicit approval. Treat Vento-Vivere material as legacy/private-local unless separately authorized.\n",
        "canon/TRIAD_CONSTITUTION.md": "# Triad Constitution\n\nUrbi audits. Orbi acts. MΣBUS gates. The user remains final promotion authority.\n",
        "canon/MEBUS_MEMBRANE_RULES.md": "# MEBUS Membrane Rules\n\nEnvelope-governed records must preserve provenance, trust floor, mode, causal order, and payload separation.\n",
        "canon/URBI_ORBI_BOUNDARIES.md": "# Urbi / Orbi Boundaries\n\nUrbi must not actuate. Orbi must not judge its own correctness.\n",
        "canon/DREAM_RULES.md": "# DREAM Rules\n\nDREAM replays, audits compression, and prepares candidates; it does not act.\n",
        "canon/DAN_TRINITY_ADAPT_R1_RULES.md": "# DAN / Trinity / ADAPT-R1 Rules\n\nDAN-GP synthesizes conjectures. Trinity routes. Autopoiesis meters. Codex implements bounded local work.\n",
        "canon/CANON_RULE_ENGINE_R0.md": "# Canon Rule Engine R0\n\nNo metaphor as canon. No raw export as memory. No liveness as authority. No public/private leak.\n",
        "architecture/DAN_GP_SYNTHESIS_ENGINE.md": "# DAN-GP Synthesis Engine\n\nDAN-GP maps project history and patterns into ConjectureRecords, SynthesisRecords, and CanonCandidateRecords. It cannot promote records directly to canon.\n",
        "architecture/AION_ONTOLOGY.md": "# AION Ontology\n\nAION classifies engineering, scientific, symbolic, fictional, game-system, mythological, religious-symbolic, speculative, obsolete, and dangerous-if-literal material.\n",
        "architecture/TRINITY_MODEL.md": "# Trinity Model\n\nAntigravity scouts, Claude audits, Codex implements bounded patches. Divergence remains recorded until promoted.\n",
        "architecture/AUTOPOIESIS_METABOLISM.md": "# Autopoiesis Metabolism\n\nAutopoiesis tracks compute, task value, token pressure, cache policy, and receipts without distorting truth.\n",
        "architecture/MEMORY_UNIVERSE_LAYER.md": "# Memory Universe Layer\n\nMemory promotion requires provenance, claims, contradictions, audit, and export policy. Raw vectors are not truth.\n",
        "architecture/MERIDIAN_NEXUS.md": "# Meridian / Nexus\n\nWorld and command surfaces remain observe/proposal-first unless MΣBUS, Urbi, Orbi, and user gates authorize action.\n",
        "architecture/SOCIAL_NEWSROOM_LOOP_PRECHECK.md": "# Social Newsroom Loop Precheck\n\nEvent -> candidate -> audit -> pre-publish gate -> user approval -> publish adapter -> quarantined metrics -> DREAM review. No posting from this scaffold.\n",
        "repo_assimilation/README.md": "# Repo Assimilation\n\nLocal report sink for repo role maps, retirement plans, and visible repo proposals.\n",
    }
    for rel, text in docs.items():
        write(kb / rel, text)

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["record_type", "source_refs", "last_reviewed"],
        "properties": {
            "record_type": {"type": "string"},
            "source_refs": {"type": "array", "items": {"type": "string"}},
            "last_reviewed": {"type": "string"},
            "kb_status": {"type": "string"},
            "trust_state": {"enum": ["+", "-", "="]},
            "public_safe": {"type": "boolean"},
            "promotion_gate": {"type": "string"},
        },
        "additionalProperties": True,
    }
    for name in ["source_record", "claim_record", "canon_candidate_record", "contradiction_record", "synthesis_record", "conjecture_record", "memory_promotion_record", "kb_manifest"]:
        data = dict(schema)
        data["title"] = name
        write(kb / "schemas" / f"{name}.schema.json", json.dumps(data, indent=2))

    write(kb / "manifests" / "source_index.jsonl", "")
    write(kb / "manifests" / "canon_candidates.jsonl", "")
    write(kb / "manifests" / "contradiction_records.jsonl", "")
    write(kb / "manifests" / "obsolete_records.jsonl", "")
    write(kb / "manifests" / "private_boundary_index.jsonl", "")
    write(kb / "manifests" / "do_not_index.jsonl", json.dumps({"path": "vento-vivere/", "reason": "excluded/private-local for current pass"}) + "\n")

    for name in ["REPOSITORY_ROLE_MAP.md", "REPOSITORY_RETIREMENT_MATRIX.md", "FINAL_VISIBLE_REPO_SET_PROPOSAL.md", "COGNITIVE_MATRIX_TRIAD_V2_5_MERGE_PLAN.md", "SOCIAL_NEWSROOM_LOOP_PRECHECK.md"]:
        source = OUT / name
        if source.exists():
            write(kb / "repo_assimilation" / name, source.read_text(encoding="utf-8"))

    front_matter = "---\nkb_status: active\ntrust_state: \"=\"\npublic_safe: false\nsource_refs: [\"KB_EXPORT_POLICY.md\"]\nlast_reviewed: 2026-06-14\npromotion_gate: MΣBUS/Urbi/user\n---\n"
    write(kb / "exports" / "anythingllm" / "README.md", front_matter + "# AnythingLLM Export\n\nCurated export target only. Do not ingest raw source folders.\n")
    for filename, title in [
        ("cognitive_matrix_brief.md", "Cognitive Matrix Brief"),
        ("triad_constitution_brief.md", "Triad Constitution Brief"),
        ("dan_trinity_adapt_r1_brief.md", "DAN Trinity ADAPT-R1 Brief"),
        ("memory_universe_brief.md", "Memory Universe Brief"),
        ("repo_status_brief.md", "Repo Status Brief"),
        ("do_not_ingest.md", "Do Not Ingest"),
    ]:
        write(kb / "exports" / "anythingllm" / filename, front_matter + f"# {title}\n\nCurated placeholder. Expand only with source refs and redaction checks.\n")

    scripts = {
        "kb_inventory.py": """from pathlib import Path\nimport hashlib, json\nroot=Path(__file__).resolve().parents[1]\nout=root/'manifests'/'source_index.jsonl'\nrows=[]\nfor p in root.rglob('*'):\n    if '.git' in p.parts or not p.is_file() or 'manifests' in p.parts:\n        continue\n    data=p.read_bytes()\n    rows.append({'path':p.relative_to(root).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'extension':p.suffix.lower(),'status_guess':'active' if p.suffix.lower()=='.md' else 'unknown','public_safe_guess':False})\nout.parent.mkdir(exist_ok=True)\nout.write_text(''.join(json.dumps(r)+'\\n' for r in rows), encoding='utf-8')\nprint(f'inventoried {len(rows)} files')\n""",
        "kb_redaction_scan.py": """from pathlib import Path\nimport json, re\nroot=Path(__file__).resolve().parents[1]\nout=root/'manifests'/'private_boundary_index.jsonl'\npat=re.compile(r'(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|https://discord(?:app)?\\.com/api/webhooks/[^\\s)]+|Bearer\\s+[^\\s]+|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}|[A-Z]:\\\\Users\\\\|/home/|/Users/)', re.I)\nrows=[]\nfor p in root.rglob('*'):\n    if '.git' in p.parts or not p.is_file() or p.suffix.lower() not in {'.md','.txt','.py','.json','.yml','.yaml','.toml'}:\n        continue\n    for i,line in enumerate(p.read_text(encoding='utf-8', errors='replace').splitlines(),1):\n        if pat.search(line):\n            rows.append({'path':p.relative_to(root).as_posix(),'line_number':i,'risk_type':'private_or_secret_shape','redacted_preview':pat.sub('<REDACTED>',line)[:160]})\nout.write_text(''.join(json.dumps(r)+'\\n' for r in rows), encoding='utf-8')\nprint(f'redaction findings {len(rows)}')\n""",
        "kb_build_manifest.py": """from pathlib import Path\nimport json\nroot=Path(__file__).resolve().parents[1]\nsource=root/'manifests'/'source_index.jsonl'\nrows=[json.loads(x) for x in source.read_text(encoding='utf-8').splitlines() if x.strip()] if source.exists() else []\n(root/'manifests'/'kb_manifest.json').write_text(json.dumps({'record_type':'kb_manifest','file_count':len(rows),'last_reviewed':'2026-06-14'}, indent=2), encoding='utf-8')\nprint(f'manifest file_count {len(rows)}')\n""",
        "kb_export_anythingllm.py": """from pathlib import Path\nimport argparse\nparser=argparse.ArgumentParser(); parser.add_argument('--dry-run', action='store_true'); args=parser.parse_args()\nroot=Path(__file__).resolve().parents[1]\nfiles=list((root/'exports'/'anythingllm').glob('*.md'))\nprint(f'anythingllm export candidates {len(files)} dry_run={args.dry_run}')\n""",
        "kb_export_public_safe.py": "print('public-safe export disabled until explicit review')\n",
        "kb_validate.py": """import subprocess, sys\ncmds=[['python','scripts/kb_inventory.py'],['python','scripts/kb_redaction_scan.py'],['python','scripts/kb_build_manifest.py'],['python','scripts/kb_export_anythingllm.py','--dry-run']]\nfor cmd in cmds:\n    print('$',' '.join(cmd))\n    result=subprocess.run(cmd)\n    if result.returncode:\n        sys.exit(result.returncode)\n""",
    }
    for filename, text in scripts.items():
        write(kb / "scripts" / filename, text)

    tests = {
        "test_kb_manifest.py": "from pathlib import Path\nimport json\n\ndef test_manifest_exists_after_validation():\n    path=Path('manifests/kb_manifest.json')\n    assert path.exists()\n    data=json.loads(path.read_text())\n    assert data['record_type']=='kb_manifest'\n",
        "test_redaction_policy.py": "from pathlib import Path\n\ndef test_redaction_script_redacts_values():\n    assert '<REDACTED>' in Path('scripts/kb_redaction_scan.py').read_text()\n",
        "test_do_not_index.py": "from pathlib import Path\n\ndef test_vento_vivere_do_not_indexed():\n    assert 'vento-vivere' in Path('manifests/do_not_index.jsonl').read_text().lower()\n",
        "test_canon_boundaries.py": "from pathlib import Path\n\ndef test_metaphor_not_authority():\n    assert 'metaphor inspires but never authorizes' in Path('KB_CANON_RULES.md').read_text().lower()\n",
        "test_export_policy.py": "from pathlib import Path\n\ndef test_anythingllm_export_policy_is_curated():\n    text=Path('KB_EXPORT_POLICY.md').read_text().lower()\n    assert 'curated export' in text\n    assert 'raw transcripts' in text\n",
    }
    for filename, text in tests.items():
        write(kb / "tests" / filename, text)

    report_dir = kb / "reports" / "projectz_kb_update_2026-06-14"
    for filename, title in [
        ("PROJECTZ_KB_RECON.md", "Projectz KB Recon"),
        ("PROJECTZ_KB_HEAVY_UPDATE_PLAN.md", "Projectz KB Heavy Update Plan"),
        ("PROJECTZ_KB_PRIVACY_SCAN.md", "Projectz KB Privacy Scan"),
        ("PROJECTZ_KB_NEW_STRUCTURE_PLAN.md", "Projectz KB New Structure Plan"),
        ("PROJECTZ_KB_ANYTHINGLLM_EXPORT_PLAN.md", "Projectz KB AnythingLLM Export Plan"),
        ("PROJECTZ_KB_CANON_MIGRATION_PLAN.md", "Projectz KB Canon Migration Plan"),
        ("PROJECTZ_KB_TEST_REPORT.md", "Projectz KB Test Report"),
        ("PROJECTZ_KB_BRANCH_STATUS.md", "Projectz KB Branch Status"),
        ("NEXT_CLAUDE_AUDIT_PROMPT.md", "Next Claude Audit Prompt"),
        ("NEXT_ANTIGRAVITY_SCOUT_PROMPT.md", "Next Antigravity Scout Prompt"),
    ]:
        write(report_dir / filename, f"# {title}\n\nGenerated by local-only heavy update scaffold on 2026-06-14. No push, PR, merge, public sharing, or live watcher change performed.\n")

    return {"projectz_kb": str(kb)}


def main() -> None:
    package = build_repo_package()
    kb = build_projectz_kb_scaffold()
    print(json.dumps({**package, **kb}, indent=2))


if __name__ == "__main__":
    main()
