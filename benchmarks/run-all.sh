#!/usr/bin/env bash
# ==============================================================================
# run-all.sh — High-Performance Parallel Benchmark Runner & Trace Auditor
# ==============================================================================
set -euo pipefail

cd "$(dirname "$0")"

# Verify pre-flight checks
./verify-setup.sh

# Run parallel matrix orchestrator (default 4 workers, override with PARALLEL_WORKERS)
export PARALLEL_WORKERS="${PARALLEL_WORKERS:-4}"

echo ""
echo "Launching parallel benchmark matrix with $PARALLEL_WORKERS concurrent container workers..."
python3 run_matrix.py "$@"
