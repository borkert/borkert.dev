# Chris Borkert — AI Systems & Agent Infrastructure

> Software engineer and researcher working on declarative tool protocols ([apicat](https://github.com/digplan/apicat)), environment-scoped coding agents ([prolific](https://github.com/digplan/prolific)), and deterministic evaluation harnesses ([benchforge](https://github.com/digplan/benchforge)).

- **Website**: [https://borkert.dev](https://borkert.dev)
- **GitHub**: [https://github.com/digplan](https://github.com/digplan)
- **Email**: [chris@borkert.dev](mailto:chris@borkert.dev)
- **LLM Index**: [https://borkert.dev/llms.txt](https://borkert.dev/llms.txt)

---

## 01. Working Principles

1. **Ground all reasoning in verifiable execution.** Language models generate plausible text; compilers, linters, and unit test suites provide ground truth. Agent reasoning loops must always be verified against deterministic runtime feedback.
2. **Use the smallest useful abstraction.** Frameworks accumulate technical debt and obscure failure modes. Prefer declarative schemas, known APIs, Unix primitives, and inspectable intermediate states.
3. **Empirical benchmarking before optimization.** Never tune prompts or agent architectures based on intuition alone. Build automated evaluation loops, measure baseline variance, and iterate methodically.

---

## 02. Writing & Research

- **[Making Agent API Calls 10x Faster with Cached Definitions](/drafts/draft-in-memory-mcp-vs-cli.md)** (August 2026): Why running shell commands to call web APIs causes slow execution, wasted context tokens, and escaping bugs, and how in-memory MCP servers with TLS connection pooling deliver sub-second tool execution.
- **[Model Leaderboards Mean Nothing Without the Harness](/drafts/draft-benchmarks-without-harness.md)** (August 2026): Why coding benchmarks reflect the prompt scaffolding, edit protocol, and feedback harness rather than raw model capability in isolation.
- **[Agentic Variation Operators: Evolutionary Search in Local Sandboxes](/drafts/draft-avo-local-harness.md)** (August 2026): Using Level-1 git sandboxes for sub-millisecond rollback on failed edits and Level-4 meta-supervisors to break stagnation loops in coding agents.
- **[Building Full-Stack Web Apps Without Bundlers or Build Steps](/drafts/draft-zero-build-frontend.md)** (2026): Simplifying web applications using modern browser standards, vanilla JavaScript, and Bun HTTPS servers without build steps or complex toolchains.
