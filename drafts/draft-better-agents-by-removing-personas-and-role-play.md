# Better Agents by Removing Personas and Role Play

*By Chris Borkert · Draft · September 2026*

> *Note: This is an ongoing study on the effectiveness of removing role play and anthropomorphic suggestions from LLM guidance. It will be followed up by more extensive studies across additional model architectures and benchmark suites.*

---

Standard prompt engineering advice often includes a persona: *"You are an expert Principal Software Engineer... empathize with the user, use human developer intuition, and take pride in crafting clean code."*

I ran a controlled $N=20$ benchmark (40 multi-turn agent runs) across five categories of programming tasks to measure what happens when you strip away the persona and treat the model as a deterministic execution engine:

- **Accuracy**: Unit-test pass rate jumped from **50.0% to 70.0%** (+20 percentage points / +40% relative).
- **Token Usage**: Total tokens dropped **23.3%**, with completion tokens falling **24.2%**.
- **Wall-Clock Latency**: Total runtime dropped **28.1%**.
- **Turn Economy**: Average turns to solve decreased from **5.40 to 4.80**.

---

## Designing a Fair Test

To isolate the effect of persona framing, the benchmark shared an identical operational core across both conditions:

```
+-----------------------------------------------------------------------------------+
|                        SHARED OPERATIONAL CORE (100% IDENTICAL)                   |
|  • Native Python Tools: read_file(path), write_file(path, code), run_command(cmd) |
|  • Strict Termination Mandate: "Verify all unit tests pass with exit code 0"     |
|  • Strict JSON Schema: {"thought": "...", "action": "...", "action_input": "..."} |
|  • Search Budget: Max 6 ReAct turns, temperature = 0.0                            |
+-----------------------------------------------------------------------------------+
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
   [ Condition A: Expert Role-Play ]               [ Condition B: Objective Engine ]
   "You are a Principal Software Engineer          "System Role: Deterministic Code
    and Staff Architect. Approach this task         Generation and Verification Engine.
    with the problem-solving mindset, domain        Execute task specifications by analyzing
    intuition, and rigorous quality standards       inputs, generating implementations, and
    of an experienced senior human developer..."    evaluating formal constraints..."
```

Both agents had the exact same native file tools (`read_file`, `write_file`, `run_command`), the same 6-turn limit, the same temperature ($0.0$), and the same mandate to check exit codes before finishing. The only independent variable was the persona framing.

---

## The Benchmark Suite ($N = 20$ Tasks)

The benchmark evaluated 20 diverse, self-contained Python tasks:

1. **Data Structures (3 tasks)**: Bounded Priority Queue with TTL and FIFO tie-breaking, LRU Cache with sliding-window expiration and tag invalidation, Ranked Prefix Trie.
2. **Algorithms (2 tasks)**: Non-overlapping Interval Merger & Inserter, Directed Graph Topological Sorter with cycle detection.
3. **Bug Fixing & Concurrency (5 tasks)**: Distributed Monotonic Lease Manager (fencing token race conditions & float precision boundaries), Token Bucket Rate Limiter, Deadlock-Safe Multi-Account Bank Transfer, Sliding-Window Event Counter, Circuit Breaker State Machine.
4. **Parsing & Text (5 tasks)**: Recursive arithmetic expression evaluator without `eval()`, Text tokenizer with contraction handling, JSON dot-notation flattener/unflattener, Semantic Version comparator, In-memory SQL `WHERE` clause AST evaluator.
5. **Systems & State Machines (5 tasks)**: Event-driven pipeline with onion middleware and Dead Letter Queue, Undo/Redo command manager, FSM workflow engine with transition guards, Consistent Hashing ring with virtual nodes, Binary tree pre-order serializer/deserializer.

---

## The Results

Every task was evaluated against automated unit tests running in an isolated temporary directory.

| Metric | Condition A: Expert Role-Play | Condition B: Objective Engine | Delta |
| :--- | :--- | :--- | :--- |
| **Pass Rate / Accuracy** | **10 / 20 (50.0%)** | **14 / 20 (70.0%)** | **+20.0% (+40% relative)** |
| **Premature False Finishes** | **0 / 20 (0%)** | **0 / 20 (0%)** | **0 (Both respected exit code rule)** |
| **Avg Turns to Solve** | **5.40 turns** | **4.80 turns** | **-11.1% turns** |
| **Avg Completion Tokens** | **1,244.8 tokens** | **943.5 tokens** | **-24.2% completion tokens** |
| **Total Tokens Consumed** | **150,260 tokens** | **115,247 tokens** | **-23.3% total tokens** |
| **Wall-Clock Latency** | **467.04s** (23.35s/task) | **335.97s** (16.80s/task) | **-28.1% faster** |
| **Avg Thought Length** | **257.3 chars** | **203.9 chars** | **-20.8% thought length** |

### Category Breakdown

```
Category                     Expert Persona        Objective Engine        Delta
─────────────────────────────────────────────────────────────────────────────────
Parsing & Text (5)           3 / 5 (60.0%)         5 / 5 (100.0%)          +40.0%
Bug Fixing / Concurrency (5) 3 / 5 (60.0%)         4 / 5 (80.0%)           +20.0%
Systems & State Machines (5) 2 / 5 (40.0%)         3 / 5 (60.0%)           +20.0%
Algorithms (2)               1 / 2 (50.0%)         1 / 2 (50.0%)            0.0%
Data Structures (3)          1 / 3 (33.3%)         1 / 3 (33.3%)            0.0%
─────────────────────────────────────────────────────────────────────────────────
OVERALL (20 Tasks)          10 / 20 (50.0%)        14 / 20 (70.0%)         +20.0%
```

---

## Why Personas Hurt Coding Agents

Looking through the step-by-step trace logs, three distinct patterns showed up repeatedly in the persona condition.

### 1. Speculative Over-Engineering
When instructed to act like a "Principal Software Engineer and Staff Architect," the model repeatedly over-designed solutions for straightforward problems.

In **Task T11 (Arithmetic Parser without `eval()`)**:
- **The Persona Agent** built multi-class token hierarchies, visitor patterns, and token streams. It spent its iteration budget fixing boilerplate bugs in its class hierarchy and ran out of turns before getting operator precedence working.
- **The Objective Agent** wrote a direct, 30-line recursive descent function. It implemented the parser on Turn 1, ran the unit tests on Turn 2, patched a unary minus edge case on Turn 3, verified all tests passed on Turn 4, and called `finish`.

### 2. Lock Ordering vs. Narrative Distraction
In **Task T08 (Deadlock-Safe Bank Account Transfer)**:
- **The Persona Agent** generated long thoughts analyzing "concurrency paradigms" and "enterprise synchronization standards," but wrote a lock acquisition check that compared account IDs as unformatted strings instead of canonical keys.
- **The Objective Agent** kept thoughts strictly focused on the mechanism (*"Sort account IDs to establish global lock acquisition order and prevent circular wait"*), implemented `locks = sorted([from_acc, to_acc], key=lambda a: a.account_id)`, and passed the test suite on Turn 4.

### 3. Context Window Economics
In an agent loop, every token generated in a `thought` block comes with a cost. It burns time, adds API latency, and pushes earlier compiler errors out of the model's immediate attention window.

The objective prompt produced a **20.8% reduction in thought verbosity** without losing technical clarity. The agent spent less time talking to itself and more turns reacting to actual test output.

---

## Key Observations

Across these 40 evaluation runs, the experimental data shows several clear patterns:

1. **Persona framing degraded accuracy (-20%)**: Asking the model to assume an expert human persona led to over-complicated abstractions and turn exhaustion on tasks that required direct implementations.
2. **Mechanical stopping criteria prevented false positives**: Requiring unit test exit code 0 before finishing kept both conditions from declaring success with failing code.
3. **Factual scratchpads reduced token overhead**: Keeping reasoning focused strictly on immediate tool actions cut reasoning thought length by 20.8% and total completion tokens by 24.2%.
4. **Structured file tools eliminated noise**: Native file read and write operations prevented shell quoting bugs from confounding the evaluation.

---

## What's Next

This $N=20$ benchmark on `gpt-4o-mini` is the first part of a broader study on agent guidance. Future evaluations will expand into:
- **Frontier Reasoning Models**: Comparing prompt sensitivity across Claude 3.5 Sonnet, GPT-4o, DeepSeek-R1, and Gemini 2.0 Flash.
- **Repository-Scale Benchmarks**: Evaluating performance on multi-file SWE-bench tasks.
- **Local Models**: Measuring the effect of de-anthropomorphizing on quantized open models running on Ollama and vLLM.

All harness scripts, benchmark task definitions, and evaluation logs are available at [github.com/digplan/agent-platform](https://github.com/digplan/agent-platform).
