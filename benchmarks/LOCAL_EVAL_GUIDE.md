# Local Model Evaluation Guide

This directory provides containerized harnesses for evaluating both cloud APIs and **local open-weight models** (running via Ollama, vLLM, LM Studio, or llama.cpp) across deterministic and agentic benchmarks.

---

## 1. Available Harnesses

| Benchmark | Type | Container Service | Typical Target |
| :--- | :--- | :--- | :--- |
| **EvalPlus** | Isolated unit test fuzzing (HumanEval+, MBPP+) | `evalplus` | Zero-shot functional coding |
| **Aider Bench** | Multi-turn git repo refactoring with `pytest` | `aider` | Interactive diff & edit recovery |
| **BigCodeBench** | Package composition (139+ packages) | `bigcodebench` | Real-world library syntax |
| **LiveBench** | Zero-shot multi-domain reasoning | `livebench` | General problem solving |
| **$\tau$-bench** | Stateful tool calling (Retail, Airline, Banking) | `taubench` | Transactional agent autonomy |
| **SWE-bench Lite** | GitHub issue & PR resolver | `swebench-lite` | Long-horizon software engineering |
| **Terminal-Bench** | Bash CLI execution sandbox | `terminalbench` | System admin & command orchestration |

---

## 2. Pointing at Local Models

All containers accept standard OpenAI-compatible API base URLs. When running locally:

### Option A: Ollama (`http://localhost:11434`)
```bash
# In your .env file or command override:
OPENAI_API_BASE=http://host.docker.internal:11434/v1
OPENAI_API_KEY=ollama
```

### Option B: vLLM or llama.cpp Server (`http://localhost:8000`)
```bash
OPENAI_API_BASE=http://host.docker.internal:8000/v1
OPENAI_API_KEY=dummy
```

### Option C: LM Studio (`http://localhost:1234`)
```bash
OPENAI_API_BASE=http://host.docker.internal:1234/v1
OPENAI_API_KEY=lm-studio
```

---

## 3. Running Single-Harness Evaluations On Demand

Because the agentic benchmarks (`taubench`, `swebench-lite`, `terminalbench`) are isolated under Docker Compose profiles, you can run them selectively without incurring large token bills:

### Run $\tau$-bench on a Local or Cloud Model
```bash
# Evaluates tool calling in the simulated retail environment (10 trials)
docker compose run --rm taubench "qwen2.5-coder:7b" "retail" 10
```

### Run Aider Bench on a Local Model
```bash
docker compose run --rm aider "openrouter/deepseek/deepseek-v4-flash-0731"
```

### Run SWE-bench Lite on a Specific Model
```bash
docker compose run --rm swebench-lite "meta-llama/llama-3.3-70b-instruct" "lite" 10
```

---

## 4. Where Results and Traces Go

* **Evaluated Scores & Metadata**: Saved in `benchmarks/results/<harness>/`
* **Raw Execution Logs & CoT Traces**: Saved in `benchmarks/traces/<harness>/`
