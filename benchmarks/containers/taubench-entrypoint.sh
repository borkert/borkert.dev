#!/usr/bin/env bash
set -eo pipefail

MODEL="${1:-google/gemini-3.7-flash}"
ENV_NAME="${2:-retail}"
NUM_TRIALS="${3:-10}"
DIR_TRACES="/workspace/traces"
DIR_RESULTS="/workspace/results"

mkdir -p "$DIR_TRACES" "$DIR_RESULTS"
SAFE_NAME=$(echo "$MODEL" | tr '/' '_')

echo "=================================================================="
echo " [tau-bench] Stateful Tool Agent Benchmark"
echo " Model: $MODEL"
echo " Environment: $ENV_NAME"
echo " Trials: $NUM_TRIALS"
echo " API Base: ${OPENAI_API_BASE:-https://openrouter.ai/api/v1}"
echo "=================================================================="

# Support local model endpoints (e.g. Ollama http://host.docker.internal:11434/v1)
export OPENAI_API_BASE="${OPENAI_API_BASE:-https://openrouter.ai/api/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-$OPENROUTER_API_KEY}"

python -m tau_bench.run \
    --model "$MODEL" \
    --env "$ENV_NAME" \
    --num-trials "$NUM_TRIALS" \
    --log-dir "$DIR_TRACES/taubench_${SAFE_NAME}_${ENV_NAME}" \
    --output "$DIR_RESULTS/taubench_${SAFE_NAME}_${ENV_NAME}.json" \
    2>&1 | tee "$DIR_TRACES/taubench_${SAFE_NAME}-raw.log" || true

echo "[tau-bench] Run finished. Results saved to $DIR_RESULTS/ and traces to $DIR_TRACES/"
