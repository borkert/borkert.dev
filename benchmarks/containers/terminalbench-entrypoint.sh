#!/usr/bin/env bash
set -eo pipefail

MODEL="${1:-google/gemini-3.7-flash}"
MAX_TASKS="${2:-10}"
DIR_TRACES="/workspace/traces"
DIR_RESULTS="/workspace/results"

mkdir -p "$DIR_TRACES" "$DIR_RESULTS"
SAFE_NAME=$(echo "$MODEL" | tr '/' '_')

echo "=================================================================="
echo " [Terminal-Bench] Agentic Terminal Execution Benchmark"
echo " Model: $MODEL"
echo " Max Tasks: $MAX_TASKS"
echo " API Base: ${OPENAI_API_BASE:-https://openrouter.ai/api/v1}"
echo "=================================================================="

export OPENAI_API_BASE="${OPENAI_API_BASE:-https://openrouter.ai/api/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-$OPENROUTER_API_KEY}"

echo "[Terminal-Bench] Initialized sandbox. Ready for local/hosted task execution."
