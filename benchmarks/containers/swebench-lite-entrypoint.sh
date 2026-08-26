#!/usr/bin/env bash
set -eo pipefail

MODEL="${1:-google/gemini-3.7-flash}"
SUBSET="${2:-lite}"
MAX_TASKS="${3:-10}"
DIR_TRACES="/workspace/traces"
DIR_RESULTS="/workspace/results"

mkdir -p "$DIR_TRACES" "$DIR_RESULTS"
SAFE_NAME=$(echo "$MODEL" | tr '/' '_')

echo "=================================================================="
echo " [SWE-bench Lite] Agentic Software Engineering Benchmark"
echo " Model: $MODEL"
echo " Subset: $SUBSET (Tasks: $MAX_TASKS)"
echo " API Base: ${OPENAI_API_BASE:-https://openrouter.ai/api/v1}"
echo "=================================================================="

export OPENAI_API_BASE="${OPENAI_API_BASE:-https://openrouter.ai/api/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-$OPENROUTER_API_KEY}"

# Run agentless or mini-swe-agent pipeline over specified instances
python -m swebench.harness.run_evaluation \
    --dataset_name "princeton-nlp/SWE-bench_Lite" \
    --predictions_path "$DIR_RESULTS/swebench_${SAFE_NAME}_preds.jsonl" \
    --max_workers 2 \
    --run_id "local_${SAFE_NAME}" \
    2>&1 | tee "$DIR_TRACES/swebench_${SAFE_NAME}-raw.log" || true

echo "[SWE-bench] Evaluation complete."
