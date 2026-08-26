# Benchmark Audit Specification & Trace Verification Standard

This document defines the strict audit trail and verification requirements for every benchmark run in this project.

## 1. Audit Principles
Every model-to-model benchmark execution must be:
1. **Fully Deterministic & Replayable**: Parameter settings (`temperature=0.0`, `seed=42` where available, `top_p=1.0`) must be locked and recorded.
2. **Environmentally Isolated**: Every benchmark must run inside an immutable Docker container with pinned dependencies.
3. **End-to-End Traced**: All raw requests, responses, reasoning traces, git patches, compiler outputs, and assertion tracebacks must be preserved.
4. **Cryptographically / Structurally Auditable**: Each run logs container image IDs, run manifests, timestamps, and input/output hashes.

---

## 2. Directory Layout for Audit Artifacts

```
benchmarks/
├── traces/
│   └── runs_<timestamp>/
│       ├── manifest.json              # Full environment, container, and parameter audit record
│       ├── evalplus_<model>.log       # Raw stdout/stderr of EvalPlus run
│       ├── evalplus_<model>_samples.jsonl # Complete completions and test verdicts
│       ├── aider_<model>.log          # Raw stdout/stderr of Aider benchmark
│       ├── aider_<model>_chat.history.md # Full conversational turn history with model
│       ├── bigcodebench_<model>.log   # Raw execution log for BigCodeBench
│       ├── bigcodebench_<model>_eval.json # Full per-task assertion results
│       ├── livebench_<model>_gen.log  # Generation log with CoT tokens
│       ├── livebench_<model>_eval.log # Ground-truth scoring evaluation log
│       └── livebench_<model>_answers.jsonl # Raw answer payloads
└── results/
    ├── summary_table.md               # Generated Markdown summary
    └── run_matrix_<timestamp>.json    # Machine-readable evaluation matrix
```

---

## 3. Run Manifest Schema (`manifest.json`)

Each execution automatically records:
- `timestamp`: ISO-8601 execution start time.
- `host_info`: OS version, CPU architecture, Docker daemon version.
- `container_digests`: SHA-256 digests of container images used.
- `models_evaluated`: Exact OpenRouter model IDs and endpoint configurations.
- `benchmark_configs`: Task subsets, timeout limits, attempt counts ($pass@k$).
- `token_usage_accounting`: Estimated prompt and completion tokens.
- `integrity_check`: Verification that all 4 harnesses executed to completion without unhandled exceptions.
