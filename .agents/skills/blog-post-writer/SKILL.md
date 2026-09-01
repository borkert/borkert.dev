---
name: blog-post-writer
description: >-
  Voice, rigor, and site conventions for writing borkert.dev blog posts — deep empirical systems essays for graduate-level CS researchers and principal engineers. Merges a human engineering voice with epistemic rigor (no presumed consensus, no unquantified prevalence claims, concrete measured grounding) and the site's formatting conventions (tables, Mermaid, LaTeX math, invariant pseudocode, numbered citations). Includes a mandatory adversarial skeptic review gate before publishing.
---

# borkert.dev Blog Post Writer

Write technical blog posts for [borkert.dev](https://borkert.dev) as if an experienced systems engineer wrote them after actually doing the work. The target reader is a graduate-level CS practitioner, systems researcher, or principal engineer — high conceptual density, no fluff, no marketing.

## Voice

- First person, direct, conversational. "I expected X, but Y happened."
- State real uncertainty when something isn't known. Never fabricate results, quotes, benchmarks, or experiences.
- Prefer concrete examples, measurements, and mechanism over abstraction.
- Vary sentence and paragraph length. Short sentences for emphasis. Don't make every paragraph equally polished.
- Strong but defensible opinions. Say what surprised you and what you'd do differently.

### Banned AI patterns

- "In today's rapidly evolving…", "At its core…", "In conclusion…", "Let's dive in…", "Not only X, but also Y", "It's not X, it's Y" as a repeated device.
- Stock AI words: *delve, tapestry, testament, vibrant, pivotal, crucial, foster, intricate, showcase, navigate, holistic, bespoke, seamlessly, game-changer, revolutionize, landscape* (abstract).
- Theatrical announcements ("Here's what you need to know"), trailing participle clauses ("…highlighting the importance of caching"), answering objections no one raised ("This isn't to say X doesn't matter"), forced triplets, generic optimistic endings.
- Excessive em dashes, semicolons, and perfectly symmetrical paragraphs.

## Epistemic invariants (non-negotiable)

1. **No presumed consensus.** Never "as everyone knows", "the well-known problem of X", "it is widely understood". Every concept must be (a) cited from literature/specs with a numbered footnote, (b) derived from first principles, or (c) coined and operationally defined with your data.
2. **No unquantified prevalence claims.** Never "a frequent pitfall", "most engineers do X", "commonly seen in the industry". Shift to structural failure modes, formal invariants, and your own measurements.
3. **Calibrated systems tone.** Active, concise, mechanistic prose. Avoid both passive academic sludge ("effectuation of…") and melodrama ("destroys execution", "code vanishes").
4. **Concrete grounding.** Anchor claims in exact numbers: latencies (e.g. `0.8 ms git reset`), hardware (e.g. `16 GB RAM`, `phi4:14b`), tokens/costs, task counts. Use LaTeX (`$N=20$`, `$\mathcal{O}(N \log N)$`) for measurements and complexity.

## Structure

Don't force a template. A natural arc is: problem → what I expected → what actually happened → the interesting technical detail → implementation → tradeoffs → what I'd do differently.

Headings: mechanism-oriented, descriptive, tradeoff-focused.
- *Reject:* "Why Small Models Fail" / "Our Benchmarking Rig"
- *Adopt:* "The 'Agent Tax': Multi-Turn Context Rot on Quantized Models" / "Level 1: Git as a Transaction Boundary"

## borkert.dev site conventions (verified against the repo)

- **Drafts live in `drafts/` as `draft-<slug>.md`; `node scripts/build-posts.js --all --sync-sitemap` builds them to `posts/<slug>.html`.** Slug = filename minus `draft-`.
- **Title = first H1.** There is no YAML frontmatter requirement; keep the H1 as the post title.
- **Byline below the H1**, e.g. `*By Chris Borkert · Draft · September 2026*` (or `- Draft -`). Update for final posts.
- **Markdown tables** for structured/measured data: tiers, metrics, comparison vectors, state machines.
- **Mermaid** is allowed and used on this site for architecture/flow diagrams (e.g. the AVO harness post). Use it for flow; use tables for data.
- **Invariant pseudocode** (<25 lines) for algorithms — no language runtime boilerplate, focus on state transitions and invariants.
- **Citations**: numbered footnotes `[^1]` in prose, plus a References section at the end with complete citations/links.
- **Negative results and forensic trace logs are first-class findings**, not caveats. Log exact turn numbers, failed assertions, rollbacks.
- A brief italic **note** block after the byline is fine for in-progress/draft status.

## Workflow

1. **Align** — state the core mechanical dilemma and thesis; outline sections before drafting.
2. **Draft** — write in the voice and invariants above, embedding pseudocode, tables, trace logs, measurements.
3. **Skeptic review gate (mandatory, blocking)** — assume the persona of a skeptical senior systems reviewer who despises AI-sounding filler. Audit for: derivative observations any LLM would emit without running code; missing empirical edge cases (race conditions, benchmark anomalies, kernel/runtime surprises); synthetic analogies; hollow textbook takeaways. Produce an adversarial report listing flagged tropes plus specific challenge questions for the author. **Block completion until the human author resolves every challenge.**
4. **Pre-publication audit** — run the checklist below; fix all failures before the post ships.

## Pre-publication checklist

- [ ] No presumed-consensus phrasing ("known as", "as we know").
- [ ] No unquantified prevalence claims; structural framing instead.
- [ ] Active, calibrated prose — no melodrama, no nominalization sludge.
- [ ] Exact hardware/latency/token/cost numbers where claims depend on them.
- [ ] Pseudocode is invariant-focused and under 25 lines; data in tables, flow in Mermaid.
- [ ] External sources cited with numbered footnotes + References section.
- [ ] No stock AI vocabulary; no fake objections or cheerleading ending.
- [ ] All skeptic-gate challenge questions resolved by the author.
- [ ] Byline and H1 correct; builds cleanly via `build-posts.js`.