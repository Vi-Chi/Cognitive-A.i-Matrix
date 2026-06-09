# C_M_LLM_Module Source Disposition

Date: `2026-04-27`
Updated: `2026-05-11`

Purpose: define how each local module source should be used by `ai_llm_agents_stack`.

## Disposition Classes

| Class | Meaning |
| --- | --- |
| `include` | safe to promote as curated Markdown |
| `summarize` | useful source, but promote only a curated digest |
| `split` | contains multiple ownership domains; separate before ingestion |
| `reference` | keep available, but do not ingest by default |
| `exclude` | weak fit, stale, noisy, or unsafe for default retrieval |

## File Decisions

| File | Class | Promotion Target |
| --- | --- | --- |
| `AGENTS.md` | include | `00_overview` policy reference |
| `PROJECTZ_AI_BACKBONE_RPI4_RPI5.md` | summarize | `00_overview` architecture baseline |
| `PROJECTZ_INDEX.md` | summarize | `00_overview` workspace map |
| `RPI4_ADMIN_SCAN_2026-04-27.md` | summarize | `00_overview` sanitized admin findings |
| `AI_LLM_AGENT_KNOWLEDGE_BASE/**` | include | matching `ai_llm_agents_stack` folders |
| `ANYTHINGLLM_ENHANCEMENT_PACK/**` | include | `02_prompts`, `03_orchestration`, `05_memory`, ops notes |
| `AI Agent Memory and Continuous Learning.docx` | summarize | `05_memory` memory research digest |
| `Executive Summary.docx` | summarize | `05_memory` memory research digest |
| `The Architectural Evolution...docx` | summarize | `05_memory` memory research digest |
| `cognitive_matrix.md` | include | `05_memory/cognitive_matrix` |
| `cognitive_matrix/audit.py` | reference | prototype under orchestration/runtime after review |
| `cognitive_matrix/context_store.json` | reference | example only |
| `lmm_stuff.txt` | summarize | source digest only |
| `llm_ecosystem.txt` | summarize | source digest only |
| `cm_module .txt` | summarize | cognitive-matrix transcript digest |
| `Cognitive Matrix & AI Design Discussion.txt` | summarize | cognitive-matrix transcript digest |
| `lmmmm.txt` | split | generic AI vs Wibo/safety content |
| `question.txt` | exclude | generated general Q&A, low operational value |
| `CLAUDE.md` | reference | Wibo-specific identity; not generic AI-stack identity |
| `Codex.md` | reference | compatibility note |
| `SYSTEM.md` | include | local operator behavior note |
| `Directory structure - the vault.txt` | reference | historical layout only |

## Raw Source Rules

Raw source may stay in `01_documents_raw` only when it is useful for provenance. Retrieval should prefer curated Markdown unless the task specifically needs raw review.

Before direct ingestion:

1. Scan for secret-like strings.
2. Remove or mask credentials and live tokens.
3. Mark the file as source, not authoritative truth.
4. Add a dated summary that explains what the source is good for.
5. Keep Wibo/marine material out of generic AI-stack retrieval unless it is explicitly about shared AI infrastructure.

## Trust Defaults

| Source Type | Default Trust |
| --- | --- |
| live system evidence | high for current state |
| dated runbooks and change logs | medium-high |
| curated audit docs | medium-high |
| extracted `.docx` research | medium until citations are checked |
| OCR/extracted notes | low-medium |
| raw transcripts | low until summarized |
| generated answers | low unless externally verified |

## Recommended RAG Behavior

When answering from this corpus:

- cite curated docs first
- mention source date
- mark unverified tool/model claims as research leads
- do not infer secrets from partial strings
- do not treat old path layouts as current without live verification
- keep generic AI infrastructure separate from Wibo vessel-domain knowledge

## 2026-05-11 `.MD` Corpus Decisions

The folder `C_M_LLM_Module\.MD` was reviewed as a curated Markdown source set. It is safer than the older raw text and Word/OCR material, but some files still contain dated scan facts and temporally unstable model claims.

| File | Disposition | Notes |
| --- | --- | --- |
| `AI_LLM_AGENT_KB_CURATED.md` | reference | broad seed; overlaps newer curated seed |
| `AI_LLM_AGENT_KB_CURATED_2026-04-27.md` | include | concise generic AI/LLM stack seed |
| `GORDON_ANYTHINGLLM_CODEX_INTEGRATION_BLUEPRINT_2026-04-27.md` | include | promote into Projectz control-plane model |
| `PROJECTZ_AI_BACKBONE_RPI4_RPI5.md` | include with caution | architecture is useful; model and benchmark claims require revalidation |
| `REVERSE_ENGINEERED_PROJECTZ_AI_STACK_2026-04-27.md` | include with caution | sample compose must remain a pattern, not a drop-in replacement |
| `RPI4_ADMIN_SCAN_2026-04-27.md` | include as historical evidence | verify current live state before acting on ports, packages, duplicates, or throttling |

New curated outputs from this pass:

- `00_overview/MD_CORPUS_SYNTHESIS_2026-05-11.md`
- `02_architecture/PROJECTZ_AI_CONTROL_PLANE_MODEL_2026-05-11.md`
- `05_ingestion/MD_CORPUS_RAG_MANIFEST_2026-05-11.md`
