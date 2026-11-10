---
title: "Google Antigravity: 26%–58% Token Savings on Gemini 4 Carbon using Neural Log Filtering"
description: "A lightweight Antigravity (agy) plugin powered by two tiny CPU L2-cache neural models cuts Gemini 4 Carbon billed tokens by 26%–58% and context size by 35% on Terminal-Bench 2.1-modeled tasks while preserving 100% of passing tasks with zero regressions."
author: Chris Borkert
---

*November 2026*

Coding agents waste a huge share of their token budget reading hundreds of repetitive build, test, and server log lines after every shell command, and then re-reading that noise on every turn that follows. Worse, accidentally opening an interactive prompt (`python3`, `sqlite3`, `vim`, or a git pager) stalls automated runs and sends the agent into recovery loops.

To solve both without calling a second LLM or touching the GPU, I built `minimodels-pe`, a lightweight plugin for Google Antigravity (`agy`) powered by two tiny [`minimodels`](/posts/minimodels-rust-metal.html) neural networks compressed to `~2–7 MB`. Because they are that small, both models stay permanently inside the Mac's fast `16 MiB` CPU L2 cache, with zero GPU usage and **`0.68 ms` median hook latency** via tiny compiled C wrappers (`~50 µs` passthrough on short outputs).

Before command output ever reaches **Gemini 4 Carbon**, the first model strips routine log boilerplate while keeping every error, warning, stack trace, and distinct log pattern intact, so **passed tasks keep their passing status (`0` regressions)**. When a command fails or gets stuck, the second model adds a one-line recovery hint and updates its own weights in `32–59 ms` whenever exit codes disagree with its prediction.

---

## Live Benchmark on Gemini 4 Carbon (`gemini-4-carbon-low`)

<figure class="figure-box">
  <img src="/assets/charts/agy_l2_pe_tokens_context.png?v=2" alt="Figure 1: Antigravity (agy) + Gemini 4 Carbon Head-to-Head Token and Context Reductions">
  <figcaption class="figcaption"><strong>Figure 1. Live Head-to-Head Benchmark on Antigravity (<code>agy</code>) with Gemini 4 Carbon (<code>gemini-4-carbon-low</code>).</strong> Across 4 engineering scenarios modeled on <strong>Terminal-Bench 2.1</strong> (<code>4/4</code> pass rate preserved, <code>0</code> regressions), <code>minimodels-pe</code> cuts billed tokens by <code>26.4%</code> (<code>103,545</code> &rarr; <code>76,254</code>, up to <code>-57.8%</code> on incident log triage) and shrinks cumulative prompt context by <code>35.4%</code> (<code>345,001</code> &rarr; <code>222,908</code>).</figcaption>
</figure>

<figure class="figure-box">
  <img src="/assets/charts/agy_l2_cache_footprint.png?v=2" alt="Figure 2: Fitting Neural Salience and Execution-State Models Inside Apple Silicon CPU L2 Cache">
  <figcaption class="figcaption"><strong>Figure 2. CPU L2 Cache Footprint &amp; Per-Call Latency.</strong> 4-bit compression shrinks checkpoints by <code>7&times;</code> with zero accuracy loss, fitting both the <code>6.52 MiB</code> general+CLI filter and a <code>1.90 MiB</code> CLI-only filter (under <code>12%</code> of Apple Silicon's <code>16 MiB</code> L2 cache) alongside the <code>1.00 MB</code> state model.</figcaption>
</figure>

We ran eight automated `agy` sessions in isolated sandboxes comparing stock `agy` (`baseline`) against `agy` + `minimodels-pe` (`pe-hook`) across four realistic debugging and triage tasks modeled on **Terminal-Bench 2.1** (`noisy-c-build-fix`, `sqlite-lock-wal-recovery`, `noisy-microservice-log-triage`, and `python-pipeline-env-and-bug`), each graded by deterministic exit-code and output checks.

Every passing task kept its passing status (**`4 / 4` = `100%` pass rate preserved, zero regressions from filtering**), even with up to **`76.1%`** of tool output text stripped. On full Docker **Terminal-Bench 2.1** tasks (`db-wal-recovery`, `sanitize-git-repo`, and `fix-code-vulnerability`), the same CPU L2 filter likewise preserved passing status on every solved task while cutting token usage by **`43%–68%`**.

### Suite Summary (`4 / 4` Verified Pass Preserved)

| Metric | Stock `agy` (`baseline`) | `agy` + `minimodels-pe` (`pe-hook`) | Delta |
| :--- | ---: | ---: | ---: |
| **Verified Task Pass Rate** | **4 / 4 (100%)** | **4 / 4 (100%)** | **0 regressions (all passed tasks stay PASS)** |
| **Billed Total Tokens** | `103,545` | **`76,254`** | **`-26.4%` (`-27,291` tok)** |
| **Effective Context Tokens (`input + cached`)** | `345,001` | **`222,908`** | **`-35.4%` (`-122,093` tok)** |
| **LLM Planner Turns** | `24` | **`19`** | **`-20.8%` (`-5` turns)** |
| **Tool Output Chars Stored in Transcript** | `91,983` | **`29,013`** | **`-68.5%` (`281,214` raw log chars stripped)** |
| **Median Hook Overhead / Total Plugin Time** | N/A | **`0.68 ms` / `0.40 s` total** | `< 0.2%` of total runtime |

### Per-Scenario Breakdown

| Scenario | Arm | Pass | Turns | Billed Tokens | Effective Context | Stored Tool Chars | Wall Time (s) | L2 Chars Stripped |
| :--- | :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **1. `noisy-c-build-fix`** | `baseline` | PASS | `8` | `30,371` | `117,024` | `29,199` | `88.55` | `0` |
| **1. `noisy-c-build-fix`** | **`pe-hook`** | **PASS** | **`6`** | **`24,579` (`-19.1%`)** | **`75,966` (`-35.1%`)** | **`11,537` (`-60.5%`)** | **`60.21` (`-32.0%`)** | **`76,723`** |
| **2. `sqlite-lock-wal-recovery`** | `baseline` | PASS | `7` | `28,279` | `101,902` | `26,524` | `63.37` | `0` |
| **2. `sqlite-lock-wal-recovery`** | **`pe-hook`** | **PASS** | **`5`** | **`20,177` (`-28.7%`)** | **`57,959` (`-43.1%`)** | **`7,297` (`-72.5%`)** | **`63.32` (`-0.1%`)** | **`28,762`** |
| **3. `noisy-microservice-log-triage`** | `baseline` | PASS | `4` | `19,937` | `53,719` | `11,376` | `38.29` | `0` |
| **3. `noisy-microservice-log-triage`** | **`pe-hook`** | **PASS** | **`3`** | **`8,407` (`-57.8%`)** | **`30,468` (`-43.3%`)** | **`2,715` (`-76.1%`)** | `47.25` | **`138,403`** |
| **4. `python-pipeline-env-and-bug`** | `baseline` | PASS | `5` | `24,958` | `72,356` | `24,884` | `51.15` | `0` |
| **4. `python-pipeline-env-and-bug`** | **`pe-hook`** | **PASS** | **`5`** | **`23,091` (`-7.5%`)** | **`58,515` (`-19.1%`)** | **`7,464` (`-70.0%`)** | `65.95` | **`37,326`** |

- **57.8% fewer billed tokens on 1,200-line log triage (Scenario 3)**: Filtering `138,403` characters of compressed `.log.gz` output in `11.9 ms` left a `2,715`-character summary with all three root-cause IDs (`19,937` &rarr; **`8,407` tokens**).
- **32.0% faster C build debugging (Scenario 1)**: Surfacing the exact compiler and unit-test failures helped the agent patch both C bugs in one pass, finishing in `6` turns instead of `8` (**`60.21s` vs. `88.55s`**).
- **Half as many shell calls on SQLite recovery (Scenario 2)**: A single lock-and-permission hint prompted the agent to clear the stale `.lock` file and fix read-only database permissions in one command instead of six (`-28.7%` tokens, `-43.1%` context).

---

## Takeaways

- **Passed tasks stay passed (`0` regressions)**: Because the filter achieves `100%` critical-error recall (`99.75%` log accuracy) and always keeps errors, stack traces, and command head/tail lines, stripping `60%–76%` of noisy output preserved `100%` of passing runs across both our `agy` suite (`4/4`) and full Docker **Terminal-Bench 2.1** tasks.
- **Filter once on the way in to keep cloud prefix caches intact**: Stripping log noise before command output is saved leaves earlier turns untouched, preserving Gemini 4 Carbon's cloud prefix cache (`67.2%`–`74.1%` cache hit rate) instead of invalidating cached history on every step.
- **Cloud TPUs vs. local GPUs**: On Cloud TPUs, prompt prefill takes ~`100 ms` so filtering immediately cuts token spend (`26%–58%`) while saved turns cut runtime (`-32%`); on a local Mac Studio GPU (`Qwen3.8-27B` via `vllm-mlx`) running Docker **Terminal-Bench 2.1**, the exact same CPU L2 filter cuts both tokens (`43%–68%`) and wall-clock time (`31%–40%`).
- **Small enough to live in CPU L2**: Training specifically on CLI and DevOps output shrinks the log filter to **`1.90 MiB`** (under `12%` of Apple Silicon's `16 MiB` P-core L2 cache).
