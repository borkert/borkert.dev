# Style & Design Inbox — borkert.dev

This directory is the designated inbox for design explorations, styling updates, and visual system proposals for [borkert.dev](https://borkert.dev).

## How to Use

When experimenting with an external or more powerful model (e.g. Claude 3.5 Sonnet / Opus, Gemini 2.5 Pro, or GPT-4o) to design layout improvements or visual refreshes:

1. **Drop your design output here**:
   - As a Markdown document: e.g. `style-inbox/2026-09-header-redesign.md`
   - Or as CSS/HTML snippets: e.g. `style-inbox/typography-tokens.css`
2. **What the Nightly Editorial Agent Does**:
   - Scans this directory on every run.
   - Parses the proposal, checks compatibility with the site's zero-build vanilla standards (`assets/vercel-brand.css`, `styles.css`), and checks for broken classes or missing tokens.
   - Summarizes the proposal and provides non-destructive integration diffs or testing steps directly in `drafts/DAILY-REPORT.md`.
3. **Template**:
   - See `template-proposal.md` for recommended structure (objective, target elements, CSS variables, typography, and preview instructions).
