#!/usr/bin/env bash
set -eo pipefail

MODEL="${1:-openrouter/stealth/ox-alpha}"
DIR_TRACES="/workspace/traces"
DIR_RESULTS="/workspace/results"

mkdir -p "$DIR_TRACES" "$DIR_RESULTS"

SAFE_NAME=$(echo "$MODEL" | tr '/' '_')
RUN_DIR="/workspace/traces/aider_${SAFE_NAME}"

echo "[Aider Bench] Running benchmark for $MODEL..."
python benchmark.py \
    "$RUN_DIR" \
    --model "$MODEL" \
    --edit-format diff \
    --exercises-dir exercism \
    --languages python \
    --threads 2 \
    --new \
    --verbose \
    2>&1 | tee "$DIR_TRACES/aider-${SAFE_NAME}-raw.log"

# Copy benchmark results and per-task chat histories/traces to mounted workspace
cp -r .aider.results.json "$DIR_RESULTS/" 2>/dev/null || true
cp -r .aider* "$DIR_TRACES/" 2>/dev/null || true

echo "[Aider Bench] Completed run for $MODEL. Traces saved to $DIR_TRACES."
