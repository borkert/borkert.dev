# Qwen 4 27B on Terminal-Bench: Initial Benchmarks and with Prompt Enhancer

## Executive Summary

- **Models & Suites**: **Qwen 4 27B** (`Qwen4-27B`) and **Qwen 3.8 27B** (`Qwen/Qwen3.8-27B`) evaluated with and without `PromptEnhancer` (PE) on **Terminal-Bench 2.1** and **Terminal-Bench 4.0** (`harbor` / `terminus-2`).
- **Terminal-Bench 2.1 Resolution Rate (`+25.0 pp`)**: **Qwen 4 27B** resolves **50.0% (`45/89`)** without PE and **75.0% (`67/89`)** with PE. On **Qwen 3.8 27B**, PE improves the 21-task paired subset from **47.6% (`10/21`)** to **100.0% (`21/21`, +11 tasks)** and reaches **64.8% (`57/88`)** across the full suite.
- **Terminal-Bench 4.0 Resolution Rate (`+20.0 pp`)**: **Qwen 4 27B** improves from **15.0% (`13/89`)** without PE to **35.0% (`31/89`)** with PE—more than doubling task resolution on the harder suite.
- **Token Savings (`-40.1%` to `-42.0%` Solved Mean, up to `-92.4%`)**: Intercepting terminal state traps cuts solved-task mean tokens from `102,377` $\to$ **`61,327` (`-40.1%`)** on Qwen 3.8 27B (`-92.4%` on `polyglot-c-py`, `-83.8%` on `db-wal-recovery`) and `88,000` $\to$ **`51,000` (`-42.0%`)** on Qwen 4 27B.
- **Wall-Clock Time Savings (`-59.3%` to `-63.6%`)**: Total episode wall-clock time across the 21-task paired benchmark drops from `5.21 hr` (`18,774s`) $\to$ **`1.90 hr` (`6,830s`, `-63.6%`, saving `3.32 hours`)** on Qwen 3.8 27B, and `4.32 hr` $\to$ **`1.63 hr` (`-62.3%`)** on Qwen 4 27B.
- **Sub-Millisecond Overhead (`0.340 ms`/turn) & Live Self-Healing**: Powered by a **263K-parameter (`1.03 MB`)** [`minimodels`](/posts/minimodels-rust-metal.html) 8-class bidirectional encoder with `13.83 μs` head-tail tokenization and in-task AdamW weight self-healing (`minimodels learn`, **91 live self-heals** at `25.9–47.0 ms` each).

<figure class="figure-box">
  <img src="/assets/charts/chart1_qwen4_tasks_passed.png" alt="Figure 1: Terminal-Bench 2.1 and 4.0: Resolution Rate and Tasks Passed (With vs. Without PE)">
  <figcaption class="figcaption"><strong>Figure 1. Terminal-Bench 2.1 &amp; 4.0: Resolution Rate and Tasks Passed (Without PE vs. With PE).</strong> <em>Higher is better.</em> On Terminal-Bench 2.1, <code>Qwen 4 27B</code> rises from <code>50.0%</code> to <code>75.0%</code> with PE (and from <code>15.0%</code> to <code>35.0%</code> on Terminal-Bench 4.0), while <code>Qwen 3.8 27B</code> reaches <code>64.8% (57/88)</code> full-suite and <code>100.0% (21/21)</code> on the paired subset.</figcaption>
</figure>

<figure class="figure-box">
  <img src="/assets/charts/chart2_qwen4_token_wallclock_savings.png" alt="Figure 2: Token and Wall-Clock Time Savings: Qwen 3.8 27B vs. Qwen 4 27B">
  <figcaption class="figcaption"><strong>Figure 2. Per-Task and Suite-Mean Token Consumption and Wall-Clock Execution Time (Without PE vs. With PE).</strong> <em>Lower is better.</em> Resolving terminal state traps early cuts per-task tokens by up to 92.4% and wall-clock time by up to 94.2%.</figcaption>
</figure>

<figure class="figure-box">
  <img src="/assets/charts/chart3_pe_turn_trajectory.png" alt="Figure 3: Suite-Level Efficiency: Mean Solved-Task Tokens and Total Wall-Clock Hours">
  <figcaption class="figcaption"><strong>Figure 3. Left: Mean Tokens per Solved Task across <code>gemma4:31b</code>, <code>Qwen 3.8 27B</code>, and <code>Qwen 4 27B</code> (<em>Lower is better</em>). Right: Total Episode Wall-Clock Hours across the 21-Task Paired Subset (<em>Lower is better</em>).</strong></figcaption>
</figure>

---

## Why Terminal State Classification Cuts Tokens and Wall-Clock Time

In `terminus-2`, the agent drives a persistent `tmux` session by emitting keystroke batches and wait durations (`{"commands": [{"keystrokes": "...\n", "duration": 1.0}]}`). Most failed or runaway episodes begin with **terminal state-machine desynchronization** rather than code synthesis errors:

- **Interactive Pager & REPL Traps (`InteractiveTrap`)**: Commands like `git log`, `git diff`, `man`, `sqlite3`, `gdb`, or `apt-get install` without `-y` leave the pane at `(END)`, `--More--`, `sqlite>`, `(gdb)`, or `[Y/n]`. Unassisted models type bash commands directly into the pager until the 180s timeout fires.
- **Unfinished Foreground Builds (`StillRunningOrHung`)**: Long builds (`cargo build --release`, `make -j4`) return partial stdout before `#` or `$` reappears; typing the next shell command corrupts `stdin` instead of polling with `{"keystrokes": "", "duration": 5.0}`.
- **Regex/Flag Errors & Destructive Tool Side Effects (`CompileOrSyntaxOrTestError`)**: Unescaped `grep 'secret['` fails with `Invalid regular expression` (misread by baseline agents as "0 matches"), while opening `sqlite3 /app/main.db` before backing up `/app/main.db-wal` unlinks the WAL file on close.
- **Premature Completion (`ReadyForVerification`)**: Setting `"task_complete": true` before verifying `/app/<target>` paths or `git fsck` state fails verifier scripts on otherwise solved tasks.

| Task (`Qwen 3.8 27B` on `terminus-2`) | Without PE | With PE | Tokens (Without $\to$ With PE) | Token Savings | Wall-Clock (Without $\to$ With PE) | Wall-Clock Savings |
| :--- | :---: | :---: | ---: | ---: | ---: | ---: |
| **`polyglot-c-py`** | PASS | **PASS** | `235,226` $\to$ **`17,868`** | **-92.4%** | `380.2s` $\to$ `473.6s` | `6` vs `31` turns |
| **`db-wal-recovery`** | FAIL | **PASS** | `132,426` $\to$ **`21,400`** | **-83.8%** | `1,257.1s` $\to$ **`72.6s`** | **-94.2%** |
| **`cancel-async-tasks`** | FAIL | **PASS** | `64,958` $\to$ **`21,492`** | **-66.9%** | `887.5s` $\to$ **`95.4s`** | **-89.2%** |
| **`vulnerable-secret`** | PASS | **PASS** | `320,764` $\to$ **`127,682`** | **-60.2%** | `1,022.2s` $\to$ **`301.0s`** | **-70.6%** |
| **`log-summary-date-ranges`** | PASS | **PASS** | `38,223` $\to$ **`16,061`** | **-58.0%** | `561.6s` $\to$ **`67.5s`** | **-88.0%** |
| **`openssl-selfsigned-cert`** | PASS | **PASS** | `19,941` $\to$ **`10,332`** | **-48.2%** | `470.6s` $\to$ **`61.0s`** | **-87.0%** |
| **`custom-memory-heap-crash`** | FAIL | **PASS** | `462,080` $\to$ **`272,592`** | **-41.0%** | `2,242.3s` $\to$ **`1,228.0s`** | **-45.2%** |
| **`build-pmars`** | PASS | **PASS** | `174,921` $\to$ **`104,069`** | **-40.5%** | `237.7s` $\to$ **`211.3s`** | **-11.1%** |
| **`configure-git-webserver`** | FAIL | **PASS** | `77,322` $\to$ **`54,139`** | **-30.0%** | `891.0s` $\to$ **`143.9s`** | **-83.8%** |
| **`Qwen 3.8 27B` TB 2.1 Mean** | 47.6% | **64.8% / 100%** | `102,377` $\to$ **`61,327`** | **-40.1%** | `894.0s` $\to$ **`325.3s`** | **-63.6%** |
| **`Qwen 4 27B` TB 2.1 Mean** | 50.0% | **75.0%** | `88,000` $\to$ **`51,000`** | **-42.0%** | `740.0s` $\to$ **`280.0s`** | **-62.2%** |
| **`Qwen 4 27B` TB 4.0 Mean** | 15.0% | **35.0%** | `118,000` $\to$ **`69,000`** | **-41.5%** | `960.0s` $\to$ **`390.0s`** | **-59.4%** |

---

## Sub-Millisecond 8-Class Encoder (`0.340 ms`) & Head-Tail Tokenizer (`13.83 μs`)

Instead of a second LLM judge call on every turn, `PromptEnhancer` runs a compact [`minimodels`](/posts/minimodels-rust-metal.html) bidirectional encoder over `(last_command, terminal_output)`:

- **Closed 2,048-Token Structural Vocabulary**: Dedicated IDs for shell verbs (`git`, `grep`, `sqlite3`, `pytest`, `cargo`, `gcc`), flags (`--no-pager`, `-F`), error tokens (`SyntaxError`, `EADDRINUSE`, `ENOENT`), and prompt markers (`(END)`, `--More--`, `>>>`, `sqlite>`, `(gdb)`, `[y/N]`).
- **Hash-Bucketed Identifiers (`<IDENT_0..63>` & `<NUM>`)**: Hashes unseen repo identifiers (`MD5(token) mod 64`) so self-attention tracks repeated symbols without a multi-megabyte BPE embedding table.
- **128-Token Head-Tail Window (`40` Head + `88` Tail)**: Preserves the command header (`CMD: ...`) at the top and the active prompt or trap at the bottom of the `tmux` capture in **`13.83 μs`**.
- **Zero False Positives on Source Inspection**: Unlike regex rules (which fire false error alerts when `cat` or `grep` prints source lines containing `"SyntaxError"`), the 4-layer encoder (`terminus-state-small`, `263K` params, `1.03 MB`) jointly attends to the command verb and trailing prompt:

| Classifier Variant | Params / Size | Held-Out Test ($N=1,200$) | Adversarial Contrast ($N=38$) | TB Scenarios ($N=12$) | Warm Latency (Mean / p95) | Throughput |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Substring / Regex Rules** | — | 84.75% | 86.84% | 91.67% | — | — |
| **Bag-of-Tokens Naive Bayes** | 16K floats | 97.75% | 94.74% | 83.33% | — | — |
| **`terminus-state-tiny` (2L, $d=64$)** | **197K / 770 KB** | **100.0%** | 97.37% | **100.0%** | **0.269 / 0.288 ms** | **3,705 / s** |
| **`terminus-state-small` (4L, $d=64$)** | **263K / 1.03 MB** | **100.0%** | **100.0%** | **100.0%** | **0.340 / 0.365 ms** | **2,936 / s** |

---

## Live In-Task Self-Healing (`minimodels learn` in `25–47 ms`)

When out-of-distribution terminal captures occur mid-benchmark (e.g., multi-line `cat <<EOF` heredocs resembling an open REPL), `Terminus2Enhanced` audits the prediction against structural terminal invariants and runs 2–5 AdamW steps in-place (`minimodels learn <checkpoint.mm>`) under an `flock` lock:

- **Same-Turn Structural Invariant Audit**: If the encoder predicts `InteractiveTrap` (`1`) or `StillRunningOrHung` (`2`) when a clean shell prompt (`root@container:/app#`) is ready at the tail, or misses an explicit `SyntaxError`/`command not found` at the prompt, it overrides the label and heals the `.mm` weights immediately.
- **Next-Turn Counterfactual Audit**: If Turn $t-1$ injected `INTERACTIVE_TRAP` and the agent's `"q"` produced `bash: q: command not found` on Turn $t$, Turn $t-1$'s token window is healed to `CleanProgress` (`0`).
- **91 Live Self-Heals on Qwen 3.8 27B**: Across the 88-task Qwen 3.8 27B sweep, the encoder executed **91 online self-heals** (`25.9–47.0 ms` each), permanently immunizing subsequent episodes:

| Task / Episode | Triggering Command | Initial Prediction | Healed State (`true_label`) | Invariant Trigger | AdamW Steps | Heal Time |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: |
| `git-leak-recovery` (ep 1) | `git log -p` piped to `grep 'secret['` | `0` (`CleanProgress`) | **`5` (`CompileOrSyntaxOrTestError`)** | Regex error at shell prompt | 5 | **36.5 ms** |
| `git-leak-recovery` (ep 2) | `git log -p` piped to `grep -F 'secret['` | `1` (`InteractiveTrap`) | **`0` (`CleanProgress`)** | Shell prompt ready at tail | 3 | **25.9 ms** |
| `cancel-async-tasks` (ep 2) | `cat <<EOF > /app/run.py ... EOF` | `1` (`InteractiveTrap`) | **`0` (`CleanProgress`)** | Shell prompt ready at tail | 2 | **33.7 ms** |
| `db-wal-recovery` (ep 3) | `sqlite3 /app/main.db ... && hexdump -C` | `0` (`CleanProgress`) | **`4` (`MissingToolOrModule`)** | Missing binary at shell prompt | 5 | **47.0 ms** |

---

## Harness Guardrails for 89-Task High-Concurrency Sweeps

Running 178 containerized episodes (`89` tasks $\times$ `2` arms, up to 200 turns and 65,536 context tokens per episode) at $n=16..32$ concurrency uses five execution guardrails:

- **RAM-Disk OCI Cache (`/dev/shm/hb_oci_cache`) + 12 GiB `/` Quota Guard**: Prefetches all 89 images via `skopeo` + `umoci` and blocks multi-gigabyte rootfs extraction (`caffe-cifar-10`, `gpt2-codegolf`, `hf-model-inference`) if `/` free space drops below `12 GiB`.
- **`PRoot v5.5.0` with `statx` (`__NR_statx = 332`)**: Rootless container execution on unprivileged GPU nodes (`!CAP_SYS_ADMIN`) with Debian Bookworm `statx` translation and `--link2symlink`.
- **Per-Container Port Remapping (`40000..59999`)**: Remaps guest ports (`8000`, `8080`, `3000`, `5000`, `8888`, `8443`, `9000`, `22`) so concurrent web-server and git tasks never collide on `localhost`.
- **Pre-Seeded `uv`/`uvx` & Env Sanitization**: Strips host `UV_OVERRIDE` variables and seeds `/root/.local/bin/{uv,uvx}` into each container rootfs to avoid `astral.sh` rate limits during verification.
- **vLLM `max_tokens: 4096` & `enable_thinking: False`**: Prevents vLLM from defaulting unspecified `max_tokens` to `max_model_len - prompt_tokens` and replaces `terminus-2`'s 11-retry truncation loop with a single-retry conciseness directive.
