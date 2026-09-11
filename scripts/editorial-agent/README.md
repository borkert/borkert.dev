# borkert.dev Daily Editorial Agent

An autonomous daily editorial and development review agent for [borkert.dev](https://borkert.dev).

Designed to run overnight on your always-on Mac mini, the agent inspects your local repositories for new commits, synthesizes high-signal blog post candidates following systems research invariants, audits site health, manages the draft queue, and screens visual design proposals.

---

## Architecture Overview

```
[MacBook Air]                                       [Mac mini (Always-On)]
      │                                                       │
      │ ◄────────── Mutagen Two-Way Safe Sync ──────────────► │
      │                                                       │
  Local Coding                                       Nightly 3:00 AM launchd
  git commits                                        dev.borkert.daily-agent
                                                              │
                                                     ┌────────┴────────┐
                                                     │ Git Repo Scan   │
                                                     │ Site Audit      │
                                                     │ Style Inbox     │
                                                     │ Draft Queue     │
                                                     │ LLM Synthesizer │
                                                     └────────┬────────┘
                                                              │
                                                     drafts/DAILY-REPORT.md
                                                     drafts/QUEUE.md
                                                     drafts/.editorial-state.json
```

---

## Core Capabilities

### 1. Multi-Repo Development Scanner (`git-scanner.js`)
- Scans priority projects (`borkert.dev`, `gateway-agent`, `agent-platform`, `prolific`, `apicat`, `avo`, `capstone`, `workflow`, `mitm-llm`, etc.) plus any other git repo in `~`.
- Extracts commit messages, diff statistics, author dates, and branch states since the last run.
- Categorizes signals: `EMPIRICAL_BENCHMARK`, `NEW_SYSTEM_OR_FEATURE`, `FORENSIC_FAILURE_OR_BUG`, `ARCHITECTURAL_INSIGHT`.

### 2. Research-Grade Post Pitching (`llm-synthesizer.js`)
- Strictly enforces the `blog-post-writer` voice:
  - **Mechanical Dilemma**: What counterintuitive problem occurred? (e.g. expected X, but Y happened).
  - **Empirical Grounding**: Exact measurements ($N$ sample size, latencies, tokens, hardware).
  - **No AI Tropes**: Purges banned words (*delve*, *tapestry*, *pivotal*, *seamlessly*, etc.).
  - **Negative Results**: Treats rollbacks and edge-case crashes as first-class findings.
- Works via OpenRouter, Cerebras OpenAI-compatible endpoint, or deterministic heuristics if offline.

### 3. Human-in-the-Loop Draft Queue (`queue-manager.js`)
- Maintains `drafts/QUEUE.md` and `drafts/queue.json`.
- Automatically evaluates drafts against the 11-point PhD Rubric (`blog-post-phd/SKILL.md`).
- Generates **Adversarial Skeptic Review Challenge Questions** specifically for Chris to answer before any draft can ship.
- Pipeline stages:
  1. `[PITCH]` — Proposed concept from commits.
  2. `[OUTLINE]` — Structured thesis, expected vs actual, benchmark targets.
  3. `[DRAFT]` — Active markdown in `drafts/draft-<slug>.md`.
  4. `[NEEDS_AUTHOR_REVIEW]` — Blocked on author's answers to skeptic challenges or missing data.
  5. `[READY_TO_PUBLISH]` — Rubric passed, compiled to `posts/<slug>.html`.
  6. `[PUBLISHED]` — Live and linked on `index.html`.

### 4. Site Health & Parity Auditor (`site-auditor.js`)
- Detects orphaned compiled posts in `posts/` not linked on `index.html`.
- Verifies sitemap parity in `sitemap.xml`.
- Audits machine endpoints (`agent-instructions.md`, `llms.txt`) for missing new tools.

### 5. Style & Design Inbox (`style-inbox-watcher.js`)
- Monitors `style-inbox/` for design specifications, CSS snippets, or layout mockups pasted from external models (Claude 3.5 Sonnet / Opus, Gemini 2.5 Pro, GPT-4o).
- Verifies compliance with zero-build vanilla standards (flags accidental Tailwind/Sass syntax).
- Summarizes proposed CSS custom properties in the daily report.

---

## CLI Usage

Run anytime on either machine:

```bash
# Run full daily cycle
npm run editorial
# or: node scripts/editorial-agent/runner.js

# View / refresh draft queue only
npm run editorial:queue

# Run site audit only
npm run editorial:audit

# Custom lookback window (e.g. 7 days)
node scripts/editorial-agent/runner.js --since "7 days ago"

# Dry run (print report to stdout without writing files)
node scripts/editorial-agent/runner.js --dry-run
```

---

## Overnight Setup on Mac mini

### Step 1: Install LaunchAgent on Mac mini
Run via SSH:
```bash
ssh mac "cd /Users/chris/borkert.dev && ./scripts/editorial-agent/install-service.sh"
```

### Step 2: Verify Status
```bash
ssh mac "launchctl list | grep dev.borkert.daily-agent"
```

### Step 3: View Overnight Logs
```bash
ssh mac "tail -n 50 ~/Library/Logs/borkert-editorial-agent.log"
```

---

## File Synchronization via Mutagen

The repository `borkert.dev` is configured for continuous two-way sync between your MacBook Air and Mac mini:

```bash
# Check sync status
mutagen sync list borkert

# Check all project syncs
cd /Users/chris/gateway-agent && mutagen project list
```
All outputs created on the Mac mini (`drafts/DAILY-REPORT.md`, `drafts/QUEUE.md`, `.editorial-state.json`) automatically sync to your laptop in real time.
