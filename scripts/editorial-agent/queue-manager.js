/**
 * queue-manager.js — Manages the draft pipeline, rubric evaluation, and author review gates
 */

import fs from 'node:fs';
import path from 'node:path';
import { PATHS, BANNED_PATTERNS } from './config.js';

/**
 * Extracts metadata and title from a Markdown draft
 */
export function parseDraftMetadata(content, filename) {
  const lines = content.split('\n');
  let title = '';
  let byline = '';
  let slug = filename.replace(/^draft-/, '').replace(/\.md$/, '');

  for (const line of lines) {
    if (!title && line.startsWith('# ')) {
      title = line.replace(/^#\s+/, '').trim();
    } else if (title && !byline && line.trim().startsWith('*By Chris Borkert')) {
      byline = line.trim();
    }
  }

  if (!title) {
    title = slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  // Count words
  const words = content.replace(/[#*`_\[\]()]/g, ' ').split(/\s+/).filter(Boolean).length;

  return { title, byline, slug, words };
}

/**
 * Evaluates a draft against the PhD rubric and editorial invariants
 */
export function evaluateDraft(content) {
  const flaggedBannedWords = [];
  for (const pattern of BANNED_PATTERNS) {
    const match = content.match(pattern);
    if (match) {
      flaggedBannedWords.push(match[0]);
    }
  }

  const hasTables = /\|[^\n]+\|\n\|[-:\s|]+\|\n\|/.test(content);
  const hasMermaid = /```mermaid/i.test(content);
  const hasCodeBlocks = /```[a-z0-9_-]+/i.test(content);
  const hasCitations = /\[\^\d+\]/.test(content);
  const hasReferences = /##\s+References/i.test(content);
  const hasLatexMath = /\$[^$\n]+\$/.test(content);
  const hasExactNumbers = /\b\d+(\.\d+)?\s*(ms|s|%|MB|GB|tokens|N=)/i.test(content);

  // Heuristic rubric scores (0-5)
  const scores = {
    epistemicGrounding: 5,
    noPrevalenceClaims: 5,
    noInventedResults: 4,
    empiricalGrounding: hasExactNumbers ? 4 : 2,
    calibratedTone: flaggedBannedWords.length === 0 ? 5 : Math.max(1, 5 - flaggedBannedWords.length),
    aiTellPurge: flaggedBannedWords.length === 0 ? 5 : Math.max(1, 5 - flaggedBannedWords.length),
    citations: hasCitations && hasReferences ? 5 : (hasCitations || hasReferences ? 3 : 2),
    structure: hasCodeBlocks ? 4 : 3,
    siteFormatting: (hasTables || hasMermaid) ? 5 : 3,
    negativeResults: /fail|rollback|stagnat|surpris|crash|bug|regress/i.test(content) ? 4 : 2,
    audienceCalibration: 4
  };

  const blockingFailures = [];
  if (flaggedBannedWords.length > 0) {
    blockingFailures.push(`Found banned AI terms: ${[...new Set(flaggedBannedWords)].join(', ')}`);
  }
  if (!hasExactNumbers) {
    blockingFailures.push(`Lacks concrete empirical grounding (latencies, token counts, N sample sizes)`);
  }

  const verdict = blockingFailures.length > 0 ? 'BLOCK' : 'PUBLISH_CANDIDATE';

  return {
    scores,
    flaggedBannedWords: [...new Set(flaggedBannedWords)],
    hasTables,
    hasMermaid,
    hasCodeBlocks,
    hasCitations,
    hasLatexMath,
    hasExactNumbers,
    blockingFailures,
    verdict
  };
}

/**
 * Generates adversarial skeptic challenge questions for the author
 */
export function generateSkepticChallenges(metadata, evaluation, content) {
  const challenges = [];

  if (!evaluation.hasExactNumbers) {
    challenges.push({
      question: `What was the exact hardware setup, latency (ms), or sample size N measured during this work?`,
      rationale: `Grounded systems posts require empirical verification before claims can stand.`
    });
  }

  if (!evaluation.hasCitations) {
    challenges.push({
      question: `Which literature, specs, or benchmark standards (e.g. Pass@k, POSIX, RFCs) establish the baseline here?`,
      rationale: `Prevents presumed-consensus fallacies.`
    });
  }

  if (!/what I would do differently|trade-off|limitation/i.test(content)) {
    challenges.push({
      question: `What broke unexpectedly, and what would you design differently in retrospect?`,
      rationale: `Forensic failure modes and candid regrets are essential to an authentic systems engineering voice.`
    });
  }

  challenges.push({
    question: `Author Voice Check: Does any section sound like an LLM summarizing documentation rather than a battle-tested post-mortem?`,
    rationale: `Mandatory human-in-the-loop review pass.`
  });

  return challenges;
}

/**
 * Loads the current draft queue state, scans drafts directory, and returns reconciled queue
 */
export function getDraftQueue(siteAudit) {
  let queueState = { drafts: [], pitches: [] };

  if (fs.existsSync(PATHS.queueJson)) {
    try {
      queueState = JSON.parse(fs.readFileSync(PATHS.queueJson, 'utf-8'));
    } catch {
      queueState = { drafts: [], pitches: [] };
    }
  }

  const existingDraftFiles = fs.existsSync(PATHS.draftsDir)
    ? fs.readdirSync(PATHS.draftsDir).filter(f => f.startsWith('draft-') && f.endsWith('.md'))
    : [];

  const reconciledDrafts = [];

  for (const filename of existingDraftFiles) {
    const fullPath = path.join(PATHS.draftsDir, filename);
    const content = fs.readFileSync(fullPath, 'utf-8');
    const metadata = parseDraftMetadata(content, filename);
    const evaluation = evaluateDraft(content);
    const challenges = generateSkepticChallenges(metadata, evaluation, content);

    // Determine current pipeline stage
    let stage = 'DRAFT';
    const isCompiled = fs.existsSync(path.join(PATHS.postsDir, `${metadata.slug}.html`));
    const isLinkedOnHome = siteAudit && !siteAudit.unlinkedPosts.includes(metadata.slug) && isCompiled;

    if (isLinkedOnHome) {
      stage = 'PUBLISHED';
    } else if (isCompiled && evaluation.verdict === 'PUBLISH_CANDIDATE') {
      stage = 'READY_TO_PUBLISH';
    } else if (challenges.length > 0 || evaluation.blockingFailures.length > 0) {
      stage = 'NEEDS_AUTHOR_REVIEW';
    }

    reconciledDrafts.push({
      filename,
      slug: metadata.slug,
      title: metadata.title,
      byline: metadata.byline,
      words: metadata.words,
      stage,
      evaluation,
      challenges,
      isCompiled,
      isLinkedOnHome,
      lastModified: fs.statSync(fullPath).mtime.toISOString()
    });
  }

  // Preserve proposed pitches that haven't become drafts yet
  const activePitches = queueState.pitches || [];

  return {
    drafts: reconciledDrafts,
    pitches: activePitches
  };
}

/**
 * Saves queue state to drafts/queue.json and renders drafts/QUEUE.md
 */
export function saveQueue(queueData) {
  fs.writeFileSync(PATHS.queueJson, JSON.stringify(queueData, null, 2), 'utf-8');

  // Render markdown queue dashboard
  const md = renderQueueDashboard(queueData);
  fs.writeFileSync(PATHS.queueFile, md, 'utf-8');
  return PATHS.queueFile;
}

/**
 * Generates the human-facing QUEUE.md markdown dashboard
 */
function renderQueueDashboard(queueData) {
  const needsReview = queueData.drafts.filter(d => d.stage === 'NEEDS_AUTHOR_REVIEW');
  const readyToPublish = queueData.drafts.filter(d => d.stage === 'READY_TO_PUBLISH');
  const published = queueData.drafts.filter(d => d.stage === 'PUBLISHED');
  const pitches = queueData.pitches || [];

  let out = `# 📋 borkert.dev Editorial Draft Queue & Pipeline\n\n`;
  out += `*Last Updated: ${new Date().toISOString()} · Managed by Daily Editorial Agent*\n\n`;

  out += `> [!IMPORTANT]\n`;
  out += `> **Human-in-the-Loop Review Policy**: AI drafts are structured starting points. No draft moves to production without Chris verifying empirical claims, answering skeptic challenges, and approving publication.\n\n`;

  // Section 1: Immediate Action Items for Chris
  out += `## ⚡ Immediate Action Items for Chris (${needsReview.length})\n\n`;
  if (needsReview.length === 0) {
    out += `*No drafts currently blocked on author review. All caught up!*\n\n`;
  } else {
    for (const draft of needsReview) {
      out += `### [${draft.title}](file://${path.join(PATHS.draftsDir, draft.filename)})\n`;
      out += `- **File**: \`drafts/${draft.filename}\` (${draft.words} words)\n`;
      out += `- **PhD Rubric Verdict**: \`${draft.evaluation.verdict}\`\n`;
      if (draft.evaluation.blockingFailures.length > 0) {
        out += `- **Blocking Rubric Failures**:\n`;
        for (const failure of draft.evaluation.blockingFailures) {
          out += `  - ❌ ${failure}\n`;
        }
      }
      out += `- **Skeptic Review Challenge Questions (Answer these before shipping)**:\n`;
      for (const ch of draft.challenges) {
        out += `  - [ ] **${ch.question}**\n    *Rationale: ${ch.rationale}*\n`;
      }
      out += `\n`;
    }
  }

  // Section 2: Ready to Publish
  out += `## 🚀 Ready to Publish (${readyToPublish.length})\n\n`;
  if (readyToPublish.length === 0) {
    out += `*None currently staged for release.*\n\n`;
  } else {
    for (const draft of readyToPublish) {
      out += `- **${draft.title}** (\`drafts/${draft.filename}\`)\n`;
      out += `  - Status: Rubric passed, compiled to \`posts/${draft.slug}.html\`\n`;
      out += `  - Action: Add entry to Section 01 in \`index.html\` and sync sitemap\n`;
    }
    out += `\n`;
  }

  // Section 3: Ideas & Proposed Pitches from Git Scanner
  out += `## 💡 Proposed Post Ideas & Pitches (${pitches.length})\n\n`;
  if (pitches.length === 0) {
    out += `*No pending pitches. Development scans will populate candidates here.*\n\n`;
  } else {
    for (const pitch of pitches) {
      out += `### ${pitch.title}\n`;
      out += `- **Source Repo**: \`${pitch.repo}\` (${pitch.sourceCommits || 'Recent commits'})\n`;
      out += `- **Mechanical Dilemma**: ${pitch.dilemma}\n`;
      out += `- **Proposed Thesis**: ${pitch.thesis}\n`;
      out += `- **Required Empirical Data**: ${pitch.evidenceRequired}\n`;
      out += `- **Status**: *Awaiting Chris's approval to outline*\n\n`;
    }
  }

  // Section 4: Live / Published Posts
  out += `## 🌐 Published on Site (${published.length})\n\n`;
  for (const post of published) {
    out += `- [${post.title}](https://borkert.dev/posts/${post.slug}.html) · \`${post.words} words\`\n`;
  }
  out += `\n`;

  return out;
}
