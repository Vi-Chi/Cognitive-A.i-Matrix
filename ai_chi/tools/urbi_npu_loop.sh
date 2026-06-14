#!/usr/bin/env bash
# Urbi Reality Loop launcher — hybrid NPU auditing by default.
#   reason/generate -> Hailo-10H :8000 (HEF) ; embeddings -> CPU-Ollama :11434
# Usage (on the CM5):  bash aicore/tools/urbi_npu_loop.sh [run_core args...]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"   # .../aicore-live
export PYTHONPATH="${ROOT}:${ROOT}/mebus_src:${ROOT}/cm_repo"
export URBI_HYBRID="${URBI_HYBRID:-1}"
export URBI_HAILO_OLLAMA="${URBI_HAILO_OLLAMA:-http://127.0.0.1:8000}"
export URBI_CPU_OLLAMA="${URBI_CPU_OLLAMA:-http://127.0.0.1:11434}"
# Optional reason-model parity once pulled as HEF:
# export URBI_HAILO_REASON_MODEL=qwen2.5-instruct:1.5b
exec python3 -m aicore.run_core "$@"
