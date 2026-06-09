# MERGE REPORT - Cognitive Matrix Unified (2026-06-09)

- cognitive_matrix: 42 files
- cognitive-matrix: 11 files
- cognitive-matrix-proto: 7 files
- union distinct paths: 56
- conflicts (same path, differing content): 3  ->  .gitattributes, LICENSE, README.md

## Conflict handling
Every conflicting path keeps all variants verbatim under _conflicts/<repo>/<path>.
Bare LICENSE / .gitattributes at root = cognitive_matrix version (canonical/richest).
Root README.md is a generated index; all original READMEs preserved in _conflicts/.

## File manifest (path | source(s) | note)
| path | source(s) | note |
|---|---|---|
| .claude\CLAUDE.md | cognitive-matrix-proto | unique |
| .env.example | cognitive_matrix | unique |
| .gitattributes | cognitive_matrix,cognitive-matrix | CONFLICT canonical=cognitive_matrix; variants in _conflicts |
| .gitignore | cognitive_matrix | unique |
| agent.py | cognitive_matrix | unique |
| AGENTS.md | cognitive-matrix-proto | unique |
| agents\__init__.py | cognitive_matrix | unique |
| agents\connector.py | cognitive_matrix | unique |
| audit.py | cognitive_matrix | unique |
| axioms.json | cognitive_matrix | unique |
| context_store.example.json | cognitive_matrix | unique |
| core\audit.py | cognitive-matrix | unique |
| core\matrix_listener.py | cognitive-matrix | unique |
| core\sigma_bus.py | cognitive-matrix | unique |
| doc\A Final Thought.txt | cognitive_matrix | unique |
| doc\ai-religion-and-sci-fi-toe-matrix.md | cognitive_matrix | unique |
| doc\anyllmagent.txt | cognitive_matrix | unique |
| doc\C_M_LLM_SOURCE_DISPOSITION_2026-04-27.md | cognitive_matrix | unique |
| doc\cm and omni.txt | cognitive_matrix | unique |
| doc\cm_module .txt | cognitive_matrix | unique |
| doc\codex.txt | cognitive_matrix | unique |
| doc\Cognitive Matrix & AI Design Discussion.txt | cognitive_matrix | unique |
| doc\cognitive_matrix.md | cognitive_matrix | unique |
| doc\COGNITIVE_MATRIX_MODULE_2026-05-17.md | cognitive_matrix | unique |
| doc\crew_ai.txt | cognitive_matrix | unique |
| doc\grkanal.txt | cognitive_matrix | unique |
| doc\llm_ecosystem.txt | cognitive_matrix | unique |
| doc\lmm_stuff.txt | cognitive_matrix | unique |
| doc\OLLM.txt | cognitive_matrix | unique |
| doc\PROJECTZ_AI_CONTROL_PLANE_MODEL_2026-05-11.md | cognitive_matrix | unique |
| doc\question.txt | cognitive_matrix | unique |
| doc\religion.txt | cognitive_matrix | unique |
| doc\REPOSITORY_MANIFEST.md | cognitive_matrix | unique |
| doc\sf_novel.txt | cognitive_matrix | unique |
| doc\the-architectural-evolution-of-persistent-state-in-agentic-artificial-intelligence-systems-mechanisms-and-cognitive-integration.md | cognitive_matrix | unique |
| doc\ToE Matrix for AI.txt | cognitive_matrix | unique |
| doc\toegrk.txt | cognitive_matrix | unique |
| doc\toe-matrix-for-ai.md | cognitive_matrix | unique |
| doc\WIBO_COGNITIVE_MATRIX.md | cognitive_matrix | unique |
| docs\MASTER_SYNTHESIS_V2.md | cognitive-matrix | unique |
| formula.py | cognitive_matrix | unique |
| identity.py | cognitive_matrix | unique |
| knowledge\omniversal.json | cognitive_matrix | unique |
| LICENSE | cognitive_matrix,cognitive-matrix | CONFLICT canonical=cognitive_matrix; variants in _conflicts |
| README.md | cognitive_matrix,cognitive-matrix,cognitive-matrix-proto | CONFLICT generated index; originals in _conflicts |
| reports\agent_model_system_analysis_20260502.md | cognitive_matrix | unique |
| reports\config_analysis_20260502.md | cognitive_matrix | unique |
| research\omniversal.json | cognitive-matrix | unique |
| schemas\__init__.py | cognitive-matrix | unique |
| schemas\m_protocol.py | cognitive-matrix | unique |
| schemas\prediction_record.py | cognitive-matrix | unique |
| SECURITY.md | cognitive_matrix | unique |
| skills\.gitkeep | cognitive-matrix-proto | unique |
| specs\.gitkeep | cognitive-matrix-proto | unique |
| src\cm\.gitkeep | cognitive-matrix-proto | unique |
| tests\.gitkeep | cognitive-matrix-proto | unique |

## Clean merge update (2026-06-09)
README.md: all three READMEs merged into one (unique sections from legacy + proto folded into the live core README). .gitattributes: union of both variants. LICENSE: single GPLv3 (identical license in all repos; only one kept). _conflicts/ removed -- everything is now in single root files; originals remain in _github_backup/ with full history.
