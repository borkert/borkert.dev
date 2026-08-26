#!/usr/bin/env python3
"""
run_matrix.py — Parallel Job Pool Orchestrator for Containerized Benchmark Matrix
Executes a pool of concurrent Docker benchmark containers, tracks progress, and logs audit traces.
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = int(os.environ.get("PARALLEL_WORKERS", 3))
BASE_DIR = Path(__file__).parent.resolve()
RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_DIR = BASE_DIR / "traces" / f"runs_{RUN_TIMESTAMP}"
RUN_DIR.mkdir(parents=True, exist_ok=True)

# Load environment
env_file = BASE_DIR / ".env"
env_vars = {}
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()

MODELS = [
    env_vars.get("MODEL_GLM", "z-ai/glm-5.2"),
    env_vars.get("MODEL_GEMINI", "google/gemini-3.7-flash"),
    env_vars.get("MODEL_DEEPSEEK", "deepseek/deepseek-v4-flash-0731")
]

BASE_URL = env_vars.get("OPENAI_API_BASE", "https://openrouter.ai/api/v1")

def build_job_queue():
    jobs = []
    for model in MODELS:
        safe_m = model.replace("/", "_")
        # 1. EvalPlus (HumanEval+)
        jobs.append({
            "id": f"evalplus_he_{safe_m}",
            "benchmark": "evalplus",
            "model": model,
            "desc": f"EvalPlus (HumanEval+) :: {model}",
            "log_file": RUN_DIR / f"evalplus_he_{safe_m}.log",
            "cmd": [
                "docker", "compose", "run", "--rm", "evalplus",
                "--model", model,
                "--dataset", "humaneval",
                "--parallel", "2",
                "--backend", "openai",
                "--base-url", BASE_URL,
                "--greedy"
            ]
        })
        # 2. EvalPlus (MBPP+)
        jobs.append({
            "id": f"evalplus_mbpp_{safe_m}",
            "benchmark": "evalplus",
            "model": model,
            "desc": f"EvalPlus (MBPP+) :: {model}",
            "log_file": RUN_DIR / f"evalplus_mbpp_{safe_m}.log",
            "cmd": [
                "docker", "compose", "run", "--rm", "evalplus",
                "--model", model,
                "--dataset", "mbpp",
                "--parallel", "2",
                "--backend", "openai",
                "--base-url", BASE_URL,
                "--greedy"
            ]
        })
        # 3. Aider Bench
        jobs.append({
            "id": f"aider_{safe_m}",
            "benchmark": "aider",
            "model": model,
            "desc": f"Aider Diff Edit :: {model}",
            "log_file": RUN_DIR / f"aider_{safe_m}.log",
            "cmd": [
                "docker", "compose", "run", "--rm", "aider",
                f"openrouter/{model}"
            ]
        })
        # 4. BigCodeBench
        jobs.append({
            "id": f"bigcodebench_{safe_m}",
            "benchmark": "bigcodebench",
            "model": model,
            "desc": f"BigCodeBench :: {model}",
            "log_file": RUN_DIR / f"bigcodebench_{safe_m}.log",
            "cmd": [
                "docker", "compose", "run", "--rm", "bigcodebench",
                model,
                "full"
            ]
        })
        # 5. LiveBench
        jobs.append({
            "id": f"livebench_{safe_m}",
            "benchmark": "livebench",
            "model": model,
            "desc": f"LiveBench Suite :: {model}",
            "log_file": RUN_DIR / f"livebench_{safe_m}.log",
            "cmd": [
                "docker", "compose", "run", "--rm", "livebench",
                model
            ]
        })
    return jobs

def run_single_job(job):
    job_id = job["id"]
    log_file = job["log_file"]
    start_time = time.time()
    print(f"▶ [STARTED]  {job['desc']}")

    try:
        with open(log_file, "w") as log_out:
            proc = subprocess.Popen(
                job["cmd"],
                cwd=str(BASE_DIR),
                stdout=log_out,
                stderr=subprocess.STDOUT,
                env={**os.environ, **env_vars}
            )
            proc.wait()
            exit_code = proc.returncode
    except Exception as e:
        exit_code = -1
        with open(log_file, "a") as log_out:
            log_out.write(f"\nExecution Exception: {str(e)}\n")

    elapsed = round(time.time() - start_time, 1)
    status_str = "SUCCESS" if exit_code == 0 else f"FAILED (exit {exit_code})"
    icon = "✔" if exit_code == 0 else "✖"
    print(f"{icon} [{status_str}] {job['desc']} ({elapsed}s)")
    return {
        "job_id": job_id,
        "benchmark": job["benchmark"],
        "model": job["model"],
        "exit_code": exit_code,
        "elapsed_sec": elapsed,
        "log_file": str(log_file.relative_to(BASE_DIR))
    }

def main():
    jobs = build_job_queue()
    total_jobs = len(jobs)

    print("==================================================================")
    print(f" Parallel Benchmark Pool: {total_jobs} Jobs across {len(MODELS)} Models")
    print(f" Concurrency Level: {MAX_WORKERS} Parallel Workers")
    print(f" Audit Run Directory: {RUN_DIR.relative_to(BASE_DIR)}")
    print("==================================================================")

    # Initialize Manifest
    manifest_path = RUN_DIR / "manifest.json"
    manifest_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "local_timestamp": RUN_TIMESTAMP,
        "concurrency": MAX_WORKERS,
        "models": MODELS,
        "total_jobs": total_jobs,
        "jobs": [j["id"] for j in jobs],
        "status": "RUNNING"
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)

    results = []
    pool_start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(run_single_job, job): job for job in jobs}
        for future in as_completed(future_map):
            res = future.result()
            results.append(res)

    total_elapsed = round(time.time() - pool_start, 1)

    # Finalize Manifest
    manifest_data["status"] = "COMPLETED"
    manifest_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    manifest_data["total_elapsed_sec"] = total_elapsed
    manifest_data["results"] = results
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)

    print("\n==================================================================")
    print(f" All {total_jobs} benchmark jobs finished in {total_elapsed} seconds.")
    print(" Compiling scores, tokens, and live costs...")
    print("==================================================================")

    # Run parser
    subprocess.run([sys.executable, "parse-results.py", "--timestamp", RUN_TIMESTAMP], cwd=str(BASE_DIR))

if __name__ == "__main__":
    main()
