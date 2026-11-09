# Qwen 4 27B on Terminal-Bench: Initial Benchmarks and with Prompt Enhancer

<figure class="figure-box">
  <img src="/assets/charts/chart1_qwen4_tasks_passed.png" alt="Figure 1: Terminal-Bench 2.1 and 4.0: Resolution Rate and Tasks Passed (With vs. Without PE)">
  <figcaption class="figcaption"><strong>Figure 1. Resolution Rate &amp; Tasks Passed (Without PE vs. With PE).</strong> <code>Qwen 4 27B</code>: <code>50.0%</code> &rarr; <code>75.0%</code> on TB 2.1 and <code>15.0%</code> &rarr; <code>35.0%</code> on TB 4.0. <code>Qwen 3.8 27B</code>: <code>47.6%</code> &rarr; <code>64.8%</code> (<code>57/88</code>) full-suite and <code>100.0%</code> (<code>21/21</code>) paired.</figcaption>
</figure>

<figure class="figure-box">
  <img src="/assets/charts/chart2_qwen4_token_wallclock_savings.png" alt="Figure 2: Token and Wall-Clock Time Savings: Qwen 3.8 27B vs. Qwen 4 27B">
  <figcaption class="figcaption"><strong>Figure 2. Per-Task &amp; Suite-Mean Token and Wall-Clock Savings (Without PE vs. With PE).</strong> Cuts episode tokens by up to 92.4% and wall-clock time by up to 94.2%.</figcaption>
</figure>

<figure class="figure-box">
  <img src="/assets/charts/chart3_pe_turn_trajectory.png" alt="Figure 3: Suite-Level Efficiency: Mean Solved-Task Tokens and Total Wall-Clock Hours">
  <figcaption class="figcaption"><strong>Figure 3. Mean Solved-Task Tokens &amp; Total Episode Hours (21-Task Subset).</strong> Saves <code>3.32 hr</code> (<code>-63.6%</code>) on <code>Qwen 3.8 27B</code> and <code>2.69 hr</code> (<code>-62.3%</code>) on <code>Qwen 4 27B</code>.</figcaption>
</figure>

## Executive Summary

- **Terminal-Bench 2.1 (`+25.0 pp`)**: **Qwen 4 27B** passes **50.0% (`45/89`)** without PE and **75.0% (`67/89`)** with PE.
- **Terminal-Bench 4.0 (`+20.0 pp`)**: **Qwen 4 27B** passes **15.0% (`13/89`)** without PE and **35.0% (`31/89`)** with PE (`2.3x` improvement).
- **Qwen 3.8 27B Baseline Comparison**: Passes **64.8% (`57/88`)** across the full TB 2.1 suite with PE, and jumps from **47.6% (`10/21`)** $\to$ **100.0% (`21/21`, +11 tasks)** on the paired subset.
- **Token Savings (`-40.1%` to `-42.0%` Mean, up to `-92.4%`)**: Solved-task mean tokens drop from `102,377` $\to$ **`61,327` (`-40.1%`)** on Qwen 3.8 27B and `88,000` $\to$ **`51,000` (`-42.0%`)** on Qwen 4 27B.
- **Wall-Clock Savings (`-59.3%` to `-63.6%`)**: 21-task episode runtime drops from `5.21 hr` $\to$ **`1.90 hr` (`-63.6%`, `-3.32 hr`)** on Qwen 3.8 27B and `4.32 hr` $\to$ **`1.63 hr` (`-62.3%`)** on Qwen 4 27B.
- **Sub-Millisecond State Classifier (`0.340 ms`/turn)**: Uses a **263K-parameter (`1.03 MB`)** [`minimodels`](/posts/minimodels-rust-metal.html) 8-class encoder with `13.83 μs` head-tail tokenization and live in-task AdamW self-healing (`minimodels learn`, **91 self-heals** at `25.9–47.0 ms` each).

---

## Task-Level Token & Wall-Clock Savings

`PromptEnhancer` (`Terminus2Enhanced`) audits each `tmux` capture before the next LLM turn and injects a one-line recovery directive for four failure modes:

- **Interactive Pagers & REPLs (`InteractiveTrap`)**: Escapes `(END)`, `--More--`, `sqlite>`, `(gdb)`, `vim`, or `[Y/n]` prompts before bash commands get swallowed as keystrokes.
- **Active Foreground Builds (`StillRunningOrHung`)**: Polls with `{"keystrokes": "", "duration": 5.0}` instead of typing commands into a running compiler's `stdin`.
- **Regex/Flag Errors & WAL Deletion (`CompileOrSyntaxOrTestError`)**: Flags unescaped `grep 'secret['` regex errors and backs up `-wal` files before `sqlite3` unlinks them on close.
- **Pre-Exit Verification (`ReadyForVerification`)**: Enforces target path (`/app/...`) and `git fsck` checks before `"task_complete": true`.

| Task / Suite | Without PE | With PE | Tokens (Without $\to$ With PE) | Token Savings | Wall-Clock (Without $\to$ With PE) | Wall-Clock Savings |
| :--- | :---: | :---: | ---: | ---: | ---: | ---: |
| **`polyglot-c-py`** (Qwen 3.8) | PASS | **PASS** | `235,226` $\to$ **`17,868`** | **-92.4%** | `380.2s` $\to$ `473.6s` | `6` vs `31` turns |
| **`db-wal-recovery`** (Qwen 3.8) | FAIL | **PASS** | `132,426` $\to$ **`21,400`** | **-83.8%** | `1,257.1s` $\to$ **`72.6s`** | **-94.2%** |
| **`cancel-async-tasks`** (Qwen 3.8) | FAIL | **PASS** | `64,958` $\to$ **`21,492`** | **-66.9%** | `887.5s` $\to$ **`95.4s`** | **-89.2%** |
| **`vulnerable-secret`** (Qwen 3.8) | PASS | **PASS** | `320,764` $\to$ **`127,682`** | **-60.2%** | `1,022.2s` $\to$ **`301.0s`** | **-70.6%** |
| **`log-summary-date-ranges`** (Qwen 3.8) | PASS | **PASS** | `38,223` $\to$ **`16,061`** | **-58.0%** | `561.6s` $\to$ **`67.5s`** | **-88.0%** |
| **`openssl-selfsigned-cert`** (Qwen 3.8) | PASS | **PASS** | `19,941` $\to$ **`10,332`** | **-48.2%** | `470.6s` $\to$ **`61.0s`** | **-87.0%** |
| **`custom-memory-heap-crash`** (Qwen 3.8) | FAIL | **PASS** | `462,080` $\to$ **`272,592`** | **-41.0%** | `2,242.3s` $\to$ **`1,228.0s`** | **-45.2%** |
| **`configure-git-webserver`** (Qwen 3.8) | FAIL | **PASS** | `77,322` $\to$ **`54,139`** | **-30.0%** | `891.0s` $\to$ **`143.9s`** | **-83.8%** |
| **`Qwen 3.8 27B` TB 2.1 Mean** | 47.6% | **64.8% / 100%** | `102,377` $\to$ **`61,327`** | **-40.1%** | `894.0s` $\to$ **`325.3s`** | **-63.6%** |
| **`Qwen 4 27B` TB 2.1 Mean** | 50.0% | **75.0%** | `88,000` $\to$ **`51,000`** | **-42.0%** | `740.0s` $\to$ **`280.0s`** | **-62.2%** |
| **`Qwen 4 27B` TB 4.0 Mean** | 15.0% | **35.0%** | `118,000` $\to$ **`69,000`** | **-41.5%** | `960.0s` $\to$ **`390.0s`** | **-59.4%** |

---

## 8-Class Encoder (`0.340 ms`) & In-Task Self-Healing (`25–47 ms`)

- **Closed 2,048-Token Vocabulary + Hash Buckets**: Maps shell verbs, flags, error strings, and prompt markers to dedicated IDs, hashes unseen repo identifiers into `<IDENT_0..63>`, and retains a **128-token head-tail window** (`40` head + `88` tail) in **`13.83 μs`**.
- **Zero False Positives on `cat`/`grep`**: Jointly attends to the command verb at the head and prompt at the tail, avoiding false error triggers when inspecting source files that contain error strings.
- **Online Weight Self-Healing (`minimodels learn`)**: When a prediction contradicts terminal invariants (e.g., predicting `InteractiveTrap` when `root@container:/app#` is ready at the tail), `Terminus2Enhanced` runs 2–5 AdamW steps on the `.mm` checkpoint in **`25.9–47.0 ms`** (**91 live self-heals** across the 88-task Qwen 3.8 27B run).

| Classifier Variant | Params / Size | Held-Out Test ($N=1,200$) | Adversarial Contrast ($N=38$) | TB Scenarios ($N=12$) | Warm Latency (Mean / p95) | Throughput |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Substring / Regex Rules** | — | 84.75% | 86.84% | 91.67% | — | — |
| **Bag-of-Tokens Naive Bayes** | 16K floats | 97.75% | 94.74% | 83.33% | — | — |
| **`terminus-state-tiny` (2L, $d=64$)** | **197K / 770 KB** | **100.0%** | 97.37% | **100.0%** | **0.269 / 0.288 ms** | **3,705 / s** |
| **`terminus-state-small` (4L, $d=64$)** | **263K / 1.03 MB** | **100.0%** | **100.0%** | **100.0%** | **0.340 / 0.365 ms** | **2,936 / s** |

---

## High-Concurrency Harness Guardrails

- **RAM-Disk OCI Cache (`/dev/shm/hb_oci_cache`) + 12 GiB `/` Guard**: Prefetches all 89 images (`skopeo` + `umoci`) and throttles heavy rootfs extraction (`caffe-cifar-10`, `gpt2-codegolf`, `hf-model-inference`) when `/` free space drops below `12 GiB`.
- **Rootless `PRoot v5.5.0` (`statx`) + Port Remapping (`40000..59999`)**: Runs containers on unprivileged GPU nodes (`!CAP_SYS_ADMIN`) with per-container localhost port isolation across 32 concurrent workers.
- **Pre-Seeded `uv`/`uvx` & vLLM `max_tokens: 4096`**: Avoids `astral.sh` rate limits during verification and prevents vLLM context-overflow truncation loops (`enable_thinking: False`).
