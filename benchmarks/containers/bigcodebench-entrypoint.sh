#!/usr/bin/env bash
set -eo pipefail

MODEL="${1:-z-ai/glm-5.2}"
SUBSET="${2:-full}"
DIR_TRACES="/workspace/traces"
DIR_RESULTS="/workspace/results"

mkdir -p "$DIR_TRACES" "$DIR_RESULTS"

SAFE_MODEL_NAME=$(echo "$MODEL" | tr '/' '_')

echo "[BigCodeBench] Generating code completions for $MODEL (subset: $SUBSET)..."
python -m bigcodebench.generate \
    --model "$MODEL" \
    --split complete \
    --subset "$SUBSET" \
    --backend openai \
    --base_url "${OPENAI_API_BASE:-https://openrouter.ai/api/v1}" \
    --greedy \
    2>&1 | tee "$DIR_TRACES/bigcodebench-${SAFE_MODEL_NAME}-gen.log"

# Locate generated samples file
SAMPLES_FILE=$(find bcb_results -name "*.jsonl" 2>/dev/null | head -n 1 || echo "")

if [ -n "$SAMPLES_FILE" ]; then
    echo "[BigCodeBench] Evaluating generated samples: $SAMPLES_FILE..."
    python -m bigcodebench.evaluate \
        --split complete \
        --subset "$SUBSET" \
        --samples "$SAMPLES_FILE" \
        --execution local \
        2>&1 | tee "$DIR_TRACES/bigcodebench-${SAFE_MODEL_NAME}-eval.log"
fi

# Copy results and traces
cp -r bcb_results/* "$DIR_RESULTS/" 2>/dev/null || true
cp -r bcb_results/* "$DIR_TRACES/" 2>/dev/null || true

echo "[BigCodeBench] Completed run for $MODEL."
