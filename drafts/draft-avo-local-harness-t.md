# Can NVIDIA’s AVO Make a 7B Local Model a Better Coding Agent?

*Chris Borkert · August 2026 · AI Systems & Evolutionary Search*

A few weeks ago, NVIDIA published **Agentic Variation Operators (AVO)**, an architecture that treats code generation as evolutionary search: generate a candidate, verify it deterministically, checkpoint successful state, roll back failures, and use a meta-controller to detect stagnation.

The original work demonstrated substantial gains with frontier models and large compute environments. I wanted to test a narrower question:

> **Can the same architecture improve coding performance for small local models under constrained compute and context?**

For this experiment, "small local model" means a 7B–14B quantized model that can run entirely on a commodity laptop with 16 GB of RAM, such as `qwen2.5-coder:7b` or `phi4:14b`.

We implemented AVO as a pluggable middleware subsystem in **`agent-platform`** and evaluated it on algorithmic, data-structure, concurrency, and parsing tasks.

The key result is that, on our benchmark, externalizing search state and aggressively discarding failed trajectories substantially improved iterative coding performance.

---

## The Problem: Multi-Turn Context Accumulation

Small coding models tend to degrade under conventional multi-turn refinement:

1. The model generates an implementation.
2. Tests fail.
3. Compiler errors and tracebacks are appended to the conversation.
4. The model modifies the already-broken workspace.
5. Subsequent attempts increasingly resemble previous failures.

This produces a characteristic failure mode:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ Standard Multi-Turn Failure Loop                                           │
├────────────────────────────────────────────────────────────────────────────┤
│ Turn 1: Model makes a minor syntax or logic error.                         │
│         Broken state remains on disk.                                      │
│                                                                            │
│ Turn 2: Model reads traceback and patches the broken implementation.       │
│                                                                            │
│ Turn 3: Context contains multiple failed implementations and diagnostics.  │
│         Model makes increasingly local modifications.                      │
│                                                                            │
│ Turn 4: Workspace and context are polluted. Model exhausts its budget.     │
│                                                                            │
│                                                         [FAIL]             │
└────────────────────────────────────────────────────────────────────────────┘
```

For larger frontier models, multi-turn feedback can work well because the model has sufficient capacity to reason over partially broken state.

For smaller models, however, additional context can become an **agent tax**: failed implementations and diagnostics consume context without increasing the model's underlying reasoning capacity.

AVO changes this state transition:

```text
Conventional:

task → attempt → failure → accumulated history → patch → failure → patch ...


AVO:

task → candidate → verify
             │
             └── failure → rollback → diagnostic → fresh candidate
```

The failed implementation is not treated as conversational state that must be reasoned about indefinitely. It becomes a failed search trajectory.

---

## Verification Asymmetry

AVO relies on a useful asymmetry in software engineering:

* **Generating a correct implementation is difficult.**
* **Verifying many properties of an implementation is comparatively cheap.**

The verifier does not need to know the optimal implementation. It only needs to determine whether a candidate satisfies the constraints.

| Domain | Generation | Verification |
| :--- | :--- | :--- |
| **CUDA optimization** | Generate optimized kernel | Correctness + benchmark |
| **Financial ledger** | Generate concurrent transaction logic | `sum(debits) == sum(credits)` |
| **Compiler optimization** | Generate AST transformation | Type checking + tests + fuzzing |
| **Local coding task** | Generate implementation | Automated test suite |

This distinction is important because an AVO supervisor does **not** need access to the ground-truth solution. The test suite provides the objective signal.

### The Supervisor

The supervisor also does not need domain knowledge.

In our implementation, `AVOSupervisor` observes only:

* verification failures,
* failure streaks,
* similarity between successive candidates.

If a model repeatedly produces nearly identical failing candidates, the supervisor forces a strategy change.

Conceptually:

```text
candidate 1 ──FAIL──┐
                    │
candidate 2 ──FAIL──┼──> high similarity
                    │
                    └──> abandon local search
                         and re-architect
```

This is analogous to a senior engineer recognizing that repeated micro-edits are not converging and resetting the approach.

---

## Implementing AVO in `agent-platform`

NVIDIA's architecture can be mapped onto four components:

| AVO Level | `agent-platform` Component | Role |
| :--- | :--- | :--- |
| **Level 1: Sandbox** | `GitSandbox` | Checkpoint and rollback filesystem state |
| **Level 2: Generator** | `AgenticTDDAgent` | Generate candidate implementations |
| **Level 3: Verifier** | `SubprocessBox` | Execute deterministic tests |
| **Level 4: Supervisor** | `AVOSupervisor` | Detect stagnation and force strategy changes |
| **Lifecycle** | `AVOPlugin` | Connect components to the agent loop |

The resulting system is intentionally lightweight. There is no additional model and no domain-specific planning component.

---

## Level 1: Git as a Transaction Boundary

The first principle is:

> **Do not make a small model reason about its own dirty workspace.**

Instead, successful state is checkpointed and failed state is discarded.

Conceptually:

```python
def on_test_result(iteration, passed):
    if passed:
        git.add_and_commit(f"AVO Checkpoint Step {iteration}")
    else:
        git.reset_hard()
        git.clean_untracked()
```

On the test system, the equivalent of:

```bash
git reset --hard HEAD
git clean -fd
```

completed in approximately **0.8 ms**.

The important property is not Git specifically. It is the existence of a cheap, deterministic transaction boundary between candidate evaluations.

---

## Level 2: Stateless Candidate Generation

Each candidate is generated from the task specification plus compact feedback from the previous evaluation.

Rather than passing the complete conversational history forward:

```text
task
+ previous implementation
+ previous traceback
+ previous discussion
+ previous attempted fix
+ ...
```

the generator receives:

```text
task specification
+ relevant test failure
+ supervisor directive
```

This keeps the model's effective search context small.

---

## Level 3: Deterministic Verification

Candidates are executed in an isolated subprocess and evaluated using deterministic tests.

```python
candidate_code = llm.generate(prompt)
result = run_isolated_tests(candidate_code)

if result.passed:
    git_sandbox.checkpoint()
else:
    git_sandbox.rollback_hard()
```

The verifier is external to the model and therefore does not depend on the model's self-assessment.

---

## Level 4: Meta-Controller Supervisor

Small models often respond to repeated failure with increasingly small edits to the same underlying approach.

`AVOSupervisor` detects this using candidate similarity and failure streaks:

```python
def detect_loop_or_stagnation(history, failure_streak):
    if failure_streak >= 2:
        similarity = diff_similarity(history[-1], history[-2])

        if similarity > 0.85:
            return (
                "High similarity across failing iterations. "
                "Do NOT tweak small details. "
                "Re-architect the approach from scratch."
            )

    return None
```

The supervisor is intentionally **domain agnostic**.

It does not know:

* which algorithm is being implemented,
* what the correct data structure is,
* what the expected output should be,
* which algorithm the model should try next.

It only detects that the current search trajectory is not changing.

---

## The Iterative Refinement Loop

The complete loop is:

```python
for turn in range(1, max_turns):
    prompt = build_prompt(
        task_spec,
        last_test_failure,
        supervisor_directive
    )

    candidate_code = llm.generate(prompt)

    test_result = run_isolated_tests(candidate_code)

    if test_result.passed:
        git_sandbox.checkpoint()
        return Success(candidate_code)

    git_sandbox.rollback_hard()

    supervisor_directive = (
        supervisor.detect_loop_or_stagnation()
    )
```

The important distinction from conventional agents is that **iteration does not imply conversational accumulation**.

Each iteration is an independent candidate in a verified search process.

---

## Empirical Benchmark 1: Algorithmic Optimization

As an initial experiment, we ran `phi4:latest` (14B) on an O(N²) pairwise-distance calculation.

```text
=================================================================
AVO LOCAL PROTOTYPE
Model: phi4:latest
=================================================================

Baseline Version (v0)
Runtime: 22.12 ms
Score:   46.4

--- Iteration 1/4 ---
[FAIL] Incorrect math
       Git rollback: 0.8 ms

--- Iteration 2/4 ---
[FAIL] Incorrect math
       Git rollback: 0.8 ms

--- Iteration 3/4 ---
[FAIL] Off-by-one error
       Git rollback: 0.8 ms

--- Iteration 4/4 ---
[PASS] 100% correct
       Runtime: 1.48 ms
       Score:   646.6

Speedup: 15.0x
```

The final implementation discovered a sorted prefix-sum identity that reduced runtime from **22.12 ms to 1.48 ms**.

The point of the experiment is not the particular optimization. It demonstrates that the model can explore materially different implementations when failed candidates do not remain in the workspace and conversational history.

---

## Empirical Evaluation: AVO-Hard10

To evaluate the architecture more systematically, we constructed **AVO-Hard10**, a suite of 10 algorithmic, concurrency, data-structure, parsing, and mathematical programming tasks.

### Tasks

| # | Task | Category |
| -: | :--- | :--- |
| 1 | `lb_code_interval_merge_k` | Scheduling |
| 2 | `lb_code_regex_validator` | Parsing |
| 3 | `lb_reasoning_longest_path_dag` | Graph DP |
| 4 | `lb_math_modular_inverse_matrix` | Mathematics |
| 5 | `lb_data_log_anomaly_detector` | Data stream |
| 6 | `lb_concurrency_bounded_priority_queue_ttl` | Concurrency |
| 7 | `lb_algorithms_lru_cache_ttl` | Data structure |
| 8 | `lb_graph_tarjan_strongly_connected` | Graph algorithms |
| 9 | `lb_math_convex_hull_monotone_chain` | Geometry |
| 10 | `lb_parsers_json_ast_schema_validator` | Parsing |

### Protocol

| Parameter | Configuration |
| :--- | :--- |
| **Model** | `phi4:latest` |
| **Parameters** | 14B |
| **Quantization** | Q4_K_M |
| **Tasks** | 10 |
| **Trials** | 5 / task |
| **Evaluations / configuration** | 50 |
| **Baseline** | Multi-turn TDD agent |
| **AVO** | TDD + Git sandbox + supervisor |
| **Verification** | Isolated Python `unittest` |

The baseline retained workspace state and accumulated multi-turn context. AVO used the Level 1 Git sandbox and Level 4 supervisor.

### Preventing Oracle Leakage

A key concern in agent evaluation is **oracle leakage**: the harness inadvertently provides the model with information about the solution.

We explicitly excluded this.

The supervisor has no domain awareness. It does not know the task semantics, expected output, or solution algorithm. Its only inputs are candidate history and verification outcomes.

Its intervention is limited to a directive such as:

```text
High similarity across failing iterations.
Do NOT tweak small details.
Re-architect the approach from scratch.
```

The test harness also provides no ground-truth implementation or algorithmic hints.

---

## Results

| Metric | Baseline | AVO | Δ |
| :--- | ---: | ---: | ---: |
| **Pass rate** | 44.0% (22/50) | **100.0% (50/50)** | **+56 pp** |
| **Mean iterations** | 3.12 | **2.40** | −23.1% |
| **Mean tokens/task** | 3,806 | **2,736** | −28.1% |
| **Supervisor interventions** | 0 | **30** | — |

On this benchmark, AVO increased the observed pass rate from 44% to 100%.

**Scope:** this 100% result is specific to the 10-task, 50-trial evaluation using `phi4:latest` (14B Q4_K_M). It should not be interpreted as evidence that AVO generally produces 100% reliability for small language models.

The largest gains occurred on tasks where the baseline repeatedly modified an incorrect implementation. Tasks that were already solved within one or two iterations showed little benefit.

---

## Per-Task Results

| # | Task | Baseline | AVO | Interventions |
| -: | :--- | ---: | ---: | ---: |
| 1 | Interval merge | 0/5 | **5/5** | 5 |
| 2 | Regex validation | 5/5 | **5/5** | 0 |
| 3 | Longest path DAG | 0/5 | **5/5** | 5 |
| 4 | Modular inverse | 5/5 | **5/5** | 0 |
| 5 | Anomaly detection | 0/5 | **5/5** | 5 |
| 6 | Bounded priority queue + TTL | 0/5 | **5/5** | 5 |
| 7 | LRU cache + TTL | 0/5 | **5/5** | 5 |
| 8 | Tarjan SCC | 5/5 | **5/5** | 0 |
| 9 | Convex hull | 2/5 | **5/5** | 5 |
| 10 | JSON schema validator | 5/5 | **5/5** | 0 |

The pattern is consistent: AVO provides the most benefit when the model enters a **stagnant local search trajectory**.

---

## Forensic Trace: Loop Recovery

The bounded-priority-queue task provides a representative failure trace.

### Baseline

The model implemented `size()` using destructive `heapq.heappop()` operations to remove expired entries.

```text
Turn 1
  Generate implementation
       ↓
  Test failure:
  AssertionError: 'persistent' != 'exp_soon'
       ↓
  Keep broken workspace
       ↓
Turn 2
  Local patch
       ↓
  Same underlying heap mutation
       ↓
Turn 3
  Another local patch
       ↓
  Context contains multiple failed implementations
       ↓
Turn 4
  Failure budget exhausted

Result: FAIL
```

Across five baseline trials, none passed.

### AVO

With the AVO architecture:

```text
Turn 1
  Generate implementation
       ↓
  Test failure
       ↓
  Git rollback (0.8 ms)
       ↓
Turn 2
  Generate variation
       ↓
  Test failure
       ↓
  91.4% candidate similarity
       ↓
  Supervisor intervention
       ↓
Turn 3
  Fresh prompt + strategy-change directive
       ↓
  New implementation
       ↓
  PASS
```

Representative trace:

```json
{
  "task_id": "lb_concurrency_bounded_priority_queue_ttl",
  "trial": 1,
  "iterations": 3,
  "status": "PASSED",
  "supervisor_interventions": 1,
  "step_trace": [
    {
      "turn": 1,
      "outcome": "FAILED",
      "error": "heap mutated during size()",
      "action": "git_sandbox.rollback_hard() [0.8ms]"
    },
    {
      "turn": 2,
      "outcome": "FAILED",
      "error": "heap mutated during peek()",
      "action": "git_sandbox.rollback_hard() [0.8ms]",
      "supervisor_event": "STAGNATION_DETECTED"
    },
    {
      "turn": 3,
      "supervisor_directive_injected":
        "High similarity across failing iterations. Re-architect.",
      "outcome": "PASSED",
      "action": "git_sandbox.checkpoint()"
    }
  ]
}
```

The supervisor did not tell the model to use a non-destructive generator. It only prevented another local modification of the same failed design.

---

## Chat History vs. Externalized Search State

The model's raw reasoning capacity does not increase under AVO.

What changes is the representation of search state.

### Conventional Agent

```text
Conversation
├── Task
├── Candidate 1
├── Error 1
├── Candidate 2
├── Error 2
├── Candidate 3
├── Error 3
└── ...
```

### AVO

```text
External Search State
├── Candidate 1 → FAIL → discard
├── Candidate 2 → FAIL → discard
├── Candidate 3 → PASS → checkpoint
└── ...
```

This separates **search exploration from conversational memory**.

For small models, that distinction appears important. Failed candidates do not consume future context, and the model is not required to reason about increasingly obsolete workspace state.

The hypothesis is therefore not that AVO makes a 14B model intrinsically more capable. Rather, it reduces the amount of irrelevant state the model must process while exploring the solution space.

---

## The "Agentic Prompting Trap"

Prompt structure also had a measurable effect.

An initial implementation used explicit agent-role framing:

```text
You are an expert autonomous software engineer
operating inside an AVO container sandbox.

TASK INSTRUCTION:
{instruction}

SUPERVISOR DIRECTIVE:
Try a radically different strategy.
```

For small models, this often caused unnecessary orchestration behavior. The model generated shell wrappers, logging code, signal handling, and other scaffolding rather than directly solving the task.

A simpler terminal-oriented prompt performed better:

```text
You are in a Linux terminal.

{instruction}

Output ONLY the executable shell command or Python script
inside a ```bash or ```python block.
```

The simpler framing reduced syntax errors and roughly doubled execution throughput in our initial testing.

The implication is straightforward:

> **For small local models, operational constraints appear more useful than elaborate agent personas.**

---

## Beyond Unit Tests: Long-Horizon Workflows

The same architecture can extend beyond code generation.

The critical abstraction is not the unit test. It is the **verifiable state transition**.

For example, consider an enterprise research workflow:

```text
Retrieve records
      ↓
Checkpoint 1: Valid entity records?
      ↓
Parse financial data
      ↓
Checkpoint 2: Schema-valid intermediate state?
      ↓
Generate report
      ↓
Checkpoint 3: Required tables and invariants satisfied?
```

A failed checkpoint can prevent downstream stages from operating on invalid state.

For example:

* A failed API request should not cause the agent to fabricate retrieved data.
* A malformed `corporate_tree.json` should not become input to subsequent analysis.
* An inconsistent financial reconciliation should not propagate into the final report.

The general pattern becomes:

```text
state → action → verify → checkpoint
                  │
                  └── failure → rollback
```

This turns the AVO mechanism into a potential **guardrail for long-horizon autonomous workflows**, not just iterative code generation.

---

## Practical Takeaways for Agent Architects

1. **Do not accumulate failed implementations in conversational context.** Re-synthesize from the original specification and compact diagnostics.
2. **Make workspace state transactional.** Successful candidates become checkpoints; failed candidates are discarded.
3. **Detect stagnation explicitly.** Repeatedly similar failures should trigger a strategy change rather than another local edit.
4. **Keep generator prompts operational.** Small models appear to benefit from direct execution constraints rather than elaborate agent personas.
5. **Treat intermediate workflow state as verifiable.** Long-horizon agents can use checkpoints to prevent invalid state from propagating.

---

## Limitations

These results are preliminary.

The evaluation uses a single 14B model, a 10-task benchmark, five trials per task, and deterministic Python tests. The benchmark is intentionally small and does not establish generalization across:

* model families,
* parameter scales,
* quantization schemes,
* programming languages,
* verifier types,
* larger task distributions,
* longer-horizon workflows.

The 100% AVO pass rate should therefore be interpreted as a **benchmark result**, not a general reliability guarantee.

An important follow-up is to determine whether the observed improvement comes primarily from:

1. workspace rollback,
2. context truncation,
3. stagnation detection,
4. prompt simplification,

or the interaction among these components.

A larger factorial evaluation should isolate those effects.

---

## Conclusion

AVO does not increase the underlying reasoning capacity of a small local model. It changes the search process around the model.

The combination of:

* deterministic verification,
* transactional workspace state,
* fresh candidate generation,
* and domain-agnostic stagnation detection

allows failed trajectories to be discarded rather than accumulated in conversational and filesystem state.

On AVO-Hard10, this increased the observed pass rate from **44% to 100%**, while reducing mean iterations by 23.1% and token consumption by 28.1%. These results are specific to the evaluated benchmark and model, but they support the narrower hypothesis that **externalized search state can materially improve iterative coding performance for resource-constrained agents**.

Overall, this is a promising direction we are continuing to pursue in harness development, with further evaluation across models, task distributions, and longer-horizon workflows.

The full AVO plugin, Git sandbox implementation, and benchmark adapters are available in the `agent-platform` codebase.

---

▲ **Chris Borkert** · [github.com/digplan](https://github.com/digplan) · [chris@borkert.dev](mailto:chris@borkert.dev)
