# Chris Borkert — AI Systems & Agentic Infrastructure

> Software engineer and researcher working on AI agent infrastructure, declarative tool protocols, deterministic sandboxes, and empirical evaluation systems. Work emphasizes simple primitives, inspectable state machines, and Unix-style composability over heavyweight framework abstractions.

- **Website**: [https://borkert.dev](https://borkert.dev)
- **GitHub**: [https://github.com/digplan](https://github.com/digplan)
- **Email**: [chris@borkert.dev](mailto:chris@borkert.dev)
- **LLM Index**: [https://borkert.dev/llms.txt](https://borkert.dev/llms.txt)
- **Full LLM Context**: [https://borkert.dev/llms-full.txt](https://borkert.dev/llms-full.txt)
- **Agent Instructions**: [https://borkert.dev/agent-instructions.md](https://borkert.dev/agent-instructions.md)

---

## 01. Systems & Software

### apicat
- **Type**: YAML · CLI · JavaScript/TypeScript · LLM Tooling
- **Summary**: APIs as executable definitions. Keeps API specifications in concise, human-readable YAML and compiles them into a tiny CLI and TypeScript library.
- **Description**: Instead of teaching language models dozens of bespoke SDK wrappers, *apicat* gives agents a compact, machine-readable vocabulary for making HTTP and WebSocket calls. This minimizes context token usage, eliminates boilerplate code generation, and allows agents to reason over inspectable interface definitions.
- **Source**: [https://github.com/digplan/apicat](https://github.com/digplan/apicat)
- **Package**: [https://www.npmjs.com/package/apicat](https://www.npmjs.com/package/apicat)

```yaml
# apicat definition: openai.chat.yaml
name: openai.chat
description: Standard completion endpoint for reasoning agents
request:
  method: POST
  url: https://api.openai.com/v1/chat/completions
  headers:
    Authorization: "Bearer ${OPENAI_API_KEY}"
  body:
    model: "${MODEL:-gpt-4o}"
    messages: "${MESSAGES}"
    temperature: 0.2
```

### prolific
- **Type**: Coding Agent · Bun · apicat Tooling · Terminal UI · Evaluation
- **Summary**: A minimal, environment-scoped coding agent. Run by Bun and compatible with any OpenAI-compatible LLM backend (Ollama, local endpoints, or cloud providers).
- **Description**: All HTTP and model calls are routed through *apicat* using each environment's declarative `apicat.yaml` definitions. Features environment-specific persistence (`SYSTEM.md`, `MEMORY.md`, `tools.yaml`, `context.json`), an interactive React/Ink terminal interface with a `/` command menu, managed background jobs (`!cmd &`), prompt-to-command approval caching, and integrated `/bench` task harness reporting per-task timing, TTFT, tokens/sec, and deterministic reward scripts.
- **Source**: [https://github.com/digplan/prolific](https://github.com/digplan/prolific)

```bash
# Run the minimal coding agent with environment-scoped context
$ bun link && agent --env default
[prolific] Active environment: default (ctx 4.2k | bg 0)
[prolific] Endpoint: http://127.0.0.1:11434 (model: qwen3:8b)
/bench    # Runs deterministic reward evaluation suite under bench-tasks/
/debug    # Toggles raw .http request/response logging
```

### benchforge
- **Type**: Evaluation Harness · Benchmark Infrastructure · Pass@K
- **Summary**: Benchmark infrastructure and repeatable evaluation workflows for AI systems.
- **Description**: Provides standardized harness orchestration for measuring model performance across coding, reasoning, and tool-use tasks. Enforces deterministic execution verifiers (compiler assertions, test suite exit codes) to ground evaluation metrics in observable reality rather than purely subjective ratings.
- **Source**: [https://github.com/digplan/benchforge](https://github.com/digplan/benchforge)

### llm-scorer
- **Type**: Automated Judges · Multi-metric Grading · Calibration
- **Summary**: Primitives for scoring model outputs and validating reasoning steps.
- **Description**: A narrow, composable library designed for LLM-as-a-judge pipelines. Implements confidence scoring, position-bias permutation testing, and rubrics for step-by-step chain-of-thought verification.
- **Source**: [https://github.com/digplan/llm-scorer](https://github.com/digplan/llm-scorer)

### compare-llms
- **Type**: Model Probing · Divergence Analysis · Evaluation
- **Summary**: Tools for empirical model comparison and reasoning divergence.
- **Description**: A focused experiment and visual interface for comparing model outputs, analyzing chain-of-thought branching paths, and evaluating how different architectures handle edge cases in structured extraction and code generation.
- **Source**: [https://github.com/digplan/compare-llms](https://github.com/digplan/compare-llms)

### vanilla-light
- **Type**: No-Build Full-Stack · Bun · Reactive Client
- **Summary**: A no-build, dependency-free full-stack web framework.
- **Description**: Reactive browser client paired with an HTTPS Bun server, plugin-driven backend architecture, auth, file storage, and built-in OpenAI-compatible LLM inference primitives. Designed without bundlers or heavy build steps to maximize operational transparency.
- **Source**: [https://github.com/digplan/vanilla-light](https://github.com/digplan/vanilla-light)

### workflow
- **Type**: Graph Execution · Unix Pipes · Minimalist Automation
- **Summary**: Tooling for expressing and executing composable workflows.
- **Description**: Emphasizes clean Unix-style pipelining and inspectable intermediate states over opaque, monolithic orchestration platforms.
- **Source**: [https://github.com/digplan/workflow](https://github.com/digplan/workflow)

---

## 02. Research Notes & Writing

- **The Case for Declarative API Schemas in Agentic Systems (2026)**: Why machine-readable YAML definitions beat bespoke SDK wrappers and heavy framework abstractions by providing models with a compact, deterministic tool vocabulary.
- **Environment-Scoped Memory and Declarative Execution in Coding Agents (2026)**: Why isolating LLM guidance, conversation context, and tool definitions per environment prevents cross-task context pollution and enables repeatable agent evaluation.
- **Calibrating Automated LLM Judges with Verifiable Execution Feedback (2025)**: Mitigating position and self-preference bias in synthetic evaluation harnesses by anchoring model ratings to deterministic compiler and test suite artifacts.
- **Minimalist AI Systems: Composing Unix Primitives with Foundation Models (2025)**: Why standard POSIX streams, plain text files, and simple HTTP endpoints provide a more resilient foundation for agent tooling than complex multi-layered frameworks.

---

## 03. Working Principles

1. **Ground all reasoning in verifiable execution.** Language models generate plausible text; compilers, linters, and unit test suites provide ground truth. Agent reasoning loops must always be verified against deterministic runtime feedback.
2. **Use the smallest useful abstraction.** Frameworks accumulate technical debt and obscure failure modes. Prefer declarative schemas, known APIs, Unix primitives, and inspectable intermediate states.
3. **Empirical benchmarking before optimization.** Never tune prompts or agent architectures based on intuition alone. Build automated evaluation loops, measure baseline variance, and iterate methodically.

---

## 04. Background & Timeline

- **Current (NOW)**: AI Systems & Agent Infrastructure Research — Building open-source tooling for declarative tool use (apicat), environment-scoped coding agents (prolific), and reproducible evaluation harnesses (benchforge).
- **Previous**: Systems Engineering & Developer Tooling — Focused on API tooling, minimal web frameworks (vanilla-light), distributed automation pipelines, and model evaluation utilities.
- **Method**: Build → Benchmark → Evaluate → Simplify → Repeat.
