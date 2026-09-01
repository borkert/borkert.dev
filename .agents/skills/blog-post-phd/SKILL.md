---
name: blog-post-phd
description: >-
  A PhD-level rubric grader for borkert.dev blog posts. Independently scores a draft against objective criteria (epistemic grounding, quantified claims, concrete measurements, AI-tell purge, citation coverage, structure, site formatting, forensic treatment, audience calibration) with evidence quotes and blocking gates. Produces a scored report and blocks publication on any blocking failure. Use as the final independent gate before a borkert.dev post is published.
---

# borkert.dev Blog Post PhD Rubric Grader

Grade a draft the way a rigorous PhD thesis committee would: every claim must be grounded, every prevalence statement quantified, every mechanism concrete, and every AI-sounding shortcut struck. Run this as an **independent final gate**, after the writer's own drafting and skeptic review.

## How to grade

- Score each criterion **0–5**. 0 = absent/wrong, 3 = adequate but needs work, 5 = excellent.
- For every score below 4, quote the exact offending passage and say what must change.
- **Blocking criteria** marked 🔒 must score ≥ 4 or the post cannot be published.
- Output a report in the format below. Do not edit the draft's prose — only diagnose, score, and list required fixes.

## Rubric

### 🔒 1. Epistemic grounding (no presumed consensus)
Every concept is cited (numbered footnote), derived from first principles, or coined and operationally defined with the author's own data. Penalize: "as everyone knows", "the well-known problem of X", ungrounded consensus.
- 0–5 ___

### 🔒 2. No unquantified prevalence claims
No "a frequent pitfall", "most engineers do X", "commonly seen". Prevalence statements are replaced with structural failure modes and measured data.
- 0–5 ___

### 🔒 3. No invented results
Every benchmark result, quote, latency, and experience is traceable to the draft's source material or the author's stated work. Flag anything that reads like a plausible-but-unfabricated number with no source.
- 0–5 ___

### 4. Concrete empirical grounding
Claims are anchored in exact numbers where they depend on them: latencies (ms), hardware/RAM, model sizes (`phi4:14b`), tokens, costs, task counts, N sample sizes.
- 0–5 ___

### 5. Calibrated systems tone
Active, concise, mechanistic prose. Penalize passive academic sludge ("effectuation of…") and melodrama ("destroys execution", "code vanishes into thin air") equally.
- 0–5 ___

### 6. AI-tell purge
No stock AI words (delve, tapestry, pivotal, seamless, etc.), theatrical announcements, trailing participle clauses, fake objections, forced triplets, or cheerful generic endings.
- 0–5 ___

### 7. Citation coverage
External sources and papers carry numbered footnotes `[^n]` and appear in a terminal References section with complete citations/links.
- 0–5 ___

### 8. Structure & navigation
Mechanism-oriented, tradeoff-focused headings; the sectioning serves the material. Penalize clickbait headings and template padding.
- 0–5 ___

### 9. Site formatting compliance
Data/metrics in Markdown tables; architecture/flow in Mermaid; algorithms as invariant pseudocode (<25 lines, no runtime boilerplate); LaTeX `$…$` for measurements/complexity where appropriate.
- 0–5 ___

### 10. Negative results & forensics
Failures, regressions, and anomalies are first-class findings with exact trace detail (turn numbers, failed assertions, rollbacks), not footnotes.
- 0–5 ___

### 11. Audience calibration
Written for graduate-level systems researchers: high density, no fluff, no definitions of obvious concepts, no over-explaining.
- 0–5 ___

## Report format

```
# PhD Rubric Report — <draft title>
Criteria scores:
  1. Epistemic grounding .... 5  |  7. Citations ............ 3
  2. No prevalence claims ... 4  |  8. Structure ............. 4
  3. No invented results .... 5  |  9. Site formatting ....... 4
  4. Empirical grounding .... 4  | 10. Negative results ...... 3
  5. Calibrated tone ........ 4  | 11. Audience .............. 4
  6. AI-tell purge .......... 3  |

Blocking failures (must fix before publishing):
- [criterion] <quoted passage> → <required fix>
Required improvements (non-blocking):
- [criterion] <quoted passage> → <suggested fix>

VERDICT: PUBLISH / REVISE / BLOCK
```

- **BLOCK**: any 🔒 criterion < 4, or fabricated data.
- **REVISE**: no blocking failures but ≥ 2 criteria below 4, or any score below 3.
- **PUBLISH**: all 🔒 ≥ 4, no score below 3.

## Independence rule

Do not grade your own draft, and do not overlap with the writer's skeptic-review gate. The PhD rubric is the *objective* scoring layer; the skeptic gate is the *qualitative* adversarial pass. If the report is being produced by the same agent that wrote the draft, state that as a caveat and prefer re-running after a fresh read.