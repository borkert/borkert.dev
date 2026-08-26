#!/usr/bin/env bash
# ==============================================================================
# verify-setup.sh — Pre-flight audit verification for containerized benchmarks
# ==============================================================================
set -euo pipefail

cd "$(dirname "$0")"

echo "=================================================================="
echo " [Pre-Flight Check] Verifying Benchmark Setup & Audit Readiness"
echo "=================================================================="

# 1. Check Docker Daemon
echo -n "1. Docker Daemon: "
if docker info >/dev/null 2>&1; then
  echo "OK ($(docker --version))"
else
  echo "FAILED. Please ensure Docker is running."
  exit 1
fi

# 2. Check .env configuration
echo -n "2. Environment File (.env): "
if [ -f .env ]; then
  source .env
  if [ -z "${OPENROUTER_API_KEY:-}" ] || [ "${OPENROUTER_API_KEY:-}" = "sk-or-v1-YOUR_KEY_HERE" ]; then
    echo "WARNING (.env found, but OPENROUTER_API_KEY is not set)"
  else
    echo "OK (API Key configured)"
  fi
else
  echo "NOT FOUND. Creating from .env.example..."
  cp .env.example .env
  echo "Created .env. Please insert your OPENROUTER_API_KEY."
fi

# 3. Check Directory Structure & Permissions
echo -n "3. Trace & Results Directories: "
mkdir -p results/{evalplus,aider,bigcodebench,livebench} traces/{evalplus,aider,bigcodebench,livebench}
echo "OK"

# 4. Check Docker Images
echo "4. Container Images Check:"
CONTAINERS=("benchmarks-evalplus" "benchmarks-aider" "benchmarks-bigcodebench" "benchmarks-livebench")
for IMG in "${CONTAINERS[@]}"; do
  if docker image inspect "$IMG" >/dev/null 2>&1; then
    DIGEST=$(docker image inspect "$IMG" --format='{{.Id}}' | cut -c1-19)
    echo "   - $IMG: READY ($DIGEST)"
  else
    echo "   - $IMG: BUILDING/PENDING (run: docker compose build)"
  fi
done

# 5. OpenRouter API Ping (if key configured)
if [ -n "${OPENROUTER_API_KEY:-}" ] && [ "${OPENROUTER_API_KEY:-}" != "sk-or-v1-YOUR_KEY_HERE" ]; then
  echo -n "5. OpenRouter Connectivity: "
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" \
    https://openrouter.ai/api/v1/auth/key || echo "000")
  if [ "$HTTP_STATUS" = "200" ]; then
    echo "OK (Authenticated)"
  else
    echo "WARNING (HTTP $HTTP_STATUS — check API key)"
  fi
fi

echo "=================================================================="
echo " Pre-flight check complete. System is configured for clean runs."
echo " When ready to run, execute: ./run-all.sh"
echo "=================================================================="
