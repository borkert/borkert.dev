#!/usr/bin/env bash
set -eo pipefail

MODEL="${1:-stealth/ox-alpha}"
DIR_TRACES="/workspace/traces"
DIR_RESULTS="/workspace/results"

mkdir -p "$DIR_TRACES" "$DIR_RESULTS"

echo "[LiveBench] Generating answers for $MODEL..."
python -m livebench.gen_api_answer \
    --model "$MODEL" \
    --api-base "${OPENAI_API_BASE:-https://openrouter.ai/api/v1}" \
    --parallel 2 \
    2>&1 | tee "$DIR_TRACES/livebench-$(echo "$MODEL" | tr '/' '_')-gen.log"

echo "[LiveBench] Evaluating answers for $MODEL..."
python -m livebench.gen_ground_truth_judgment \
    --model "$MODEL" \
    2>&1 | tee "$DIR_TRACES/livebench-$(echo "$MODEL" | tr '/' '_')-eval.log"

# Copy raw model answers, CoT reasoning traces, and judgments to traces
cp -r data/model_answer/* "$DIR_TRACES/" 2>/dev/null || true
cp -r data/model_judgment/* "$DIR_RESULTS/" 2>/dev/null || true

echo "[LiveBench] Finished evaluation for $MODEL."
