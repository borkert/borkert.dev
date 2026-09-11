/**
 * reporter.js — Formats the Daily Editorial Report and historical log
 */

import fs from 'node:fs';
import { PATHS } from './config.js';

export function generateDailyReport({
  scannedRepos,
  siteAudit,
  styleInbox,
  queueData,
  pitches,
  executionTimeMs
}) {
  const dateStr = new Date().toISOString().split('T')[0];
  const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false });
  const needsReview = queueData.drafts.filter(d => d.stage === 'NEEDS_AUTHOR_REVIEW');
  const readyToPublish = queueData.drafts.filter(d => d.stage === 'READY_TO_PUBLISH');

  let out = `# 🌅 borkert.dev Daily Editorial & Development Digest\n\n`;
  out += `*Run Date: ${dateStr} at ${timeStr} · Execution time: ${executionTimeMs}ms*\n\n`;

  // 1. Executive Summary
  out += `## 1. Executive Summary & Action Items for Chris\n\n`;
  if (needsReview.length > 0 || siteAudit.issues.length > 0 || pitches.length > 0 || readyToPublish.length > 0) {
    if (readyToPublish.length > 0) {
      out += `### 🚀 Ready to Release (${readyToPublish.length})\n`;
      for (const p of readyToPublish) {
        out += `- **${p.title}** is compiled in \`posts/${p.slug}.html\` but not yet linked on \`index.html\`.\n`;
      }
      out += `\n`;
    }

    if (siteAudit.issues.length > 0) {
      out += `### 🛠️ Site Maintenance Alerts (${siteAudit.issues.length})\n`;
      for (const issue of siteAudit.issues) {
        out += `- **[${issue.category}]**: ${issue.message}\n  *Action*: ${issue.action}\n`;
      }
      out += `\n`;
    }

    if (needsReview.length > 0) {
      out += `### 📝 Drafts Needing Author Answers (${needsReview.length})\n`;
      for (const d of needsReview) {
        out += `- **${d.title}**: ${d.challenges.length} skeptic review challenge questions pending.\n`;
      }
      out += `\n`;
    }

    if (pitches.length > 0) {
      out += `### 💡 High-Signal Post Candidates from Recent Commits (${pitches.length})\n`;
      for (const p of pitches) {
        out += `- **${p.title}** (from \`${p.repo}\`)\n`;
      }
      out += `\n`;
    }
  } else {
    out += `*All drafts, site parity checks, and repositories are up to date!*\n\n`;
  }

  // 2. Repository Development Review
  out += `## 2. Multi-Repo Development Review (${scannedRepos.length} active repos)\n\n`;
  for (const repo of scannedRepos) {
    out += `### \`${repo.name}\` (${repo.commitCount} new commit${repo.commitCount === 1 ? '' : 's'}, ${repo.uncommittedCount} uncommitted)\n`;
    out += `- **Branch**: \`${repo.branch}\`\n`;
    if (repo.commits.length > 0) {
      out += `- **Recent Commits**:\n`;
      for (const c of repo.commits.slice(0, 5)) {
        out += `  - \`${c.hash}\` ${c.subject} *(${c.signals.join(', ')})*\n`;
      }
    }
    if (repo.diffStatSummary) {
      const statLine = repo.diffStatSummary.split('\n').filter(Boolean).pop();
      if (statLine) {
        out += `- **Diff Summary**: \`${statLine.trim()}\`\n`;
      }
    }
    out += `\n`;
  }

  // 3. New Post Candidates & Pitches
  out += `## 3. Blog Post Pitches & Mechanical Dilemmas\n\n`;
  if (pitches.length === 0) {
    out += `*No new pitches generated for this cycle.*\n\n`;
  } else {
    for (const p of pitches) {
      out += `### 💡 ${p.title}\n`;
      out += `- **Origin**: Repository \`${p.repo}\` (${p.sourceCommits})\n`;
      out += `- **The Mechanical Dilemma**: ${p.dilemma}\n`;
      out += `- **The Defensible Thesis**: ${p.thesis}\n`;
      out += `- **Required Empirical Data**: ${p.evidenceRequired}\n`;
      out += `- **Adversarial Skeptic Questions for Chris**:\n`;
      for (const q of (p.skepticChallenges || [])) {
        out += `  - [ ] ${q}\n`;
      }
      out += `\n`;
    }
  }

  // 4. Site Improvements & Documentation Parity
  out += `## 4. Site Improvements & Machine Parity\n\n`;
  out += `- **Published Posts**: ${siteAudit.totalPosts}\n`;
  out += `- **Total Drafts**: ${siteAudit.totalDrafts}\n`;
  if (siteAudit.suggestions.length > 0) {
    out += `- **Recommended Documentation Updates**:\n`;
    for (const sug of siteAudit.suggestions) {
      out += `  - **[${sug.category}]**: ${sug.message}\n    *Recommended Fix*: ${sug.action}\n`;
    }
  } else {
    out += `- **Documentation Status**: Fully synchronized with current ecosystem.\n`;
  }
  out += `\n`;

  // 5. Style & Visual Design Inbox
  out += `## 5. Style & Design Inbox\n\n`;
  if (styleInbox.pendingCount === 0) {
    out += `*Inbox empty.* (To test design changes from Claude/Gemini/GPT, drop Markdown or CSS specs into \`style-inbox/\`).\n\n`;
  } else {
    out += `**${styleInbox.pendingCount} Pending Proposal(s)**:\n`;
    for (const prop of styleInbox.proposals) {
      out += `### \`${prop.filename}\` (${prop.sizeBytes} bytes, ${prop.cssVariableCount} CSS vars)\n`;
      out += `- **Zero-Build Vanilla Compliance**: ${prop.isValidVanilla ? '✅ Fully compliant' : '⚠️ Warnings flagged'}\n`;
      if (prop.warnings.length > 0) {
        for (const w of prop.warnings) {
          out += `  - ⚠️ ${w}\n`;
        }
      }
      if (prop.sampleTokens.length > 0) {
        out += `- **Sample CSS Tokens**: \`${prop.sampleTokens.join(' ')}\`\n`;
      }
    }
    out += `\n`;
  }

  // 6. Draft Queue Summary
  out += `## 6. Draft Queue Overview\n\n`;
  out += `See [drafts/QUEUE.md](file://${PATHS.queueFile}) for full checklist and author review gates.\n`;

  return out;
}

/**
 * Writes the daily report, updates state, and appends to the log
 */
export function saveReportAndLog(reportMarkdown, state) {
  // 1. Write current daily report
  fs.writeFileSync(PATHS.reportFile, reportMarkdown, 'utf-8');

  // 2. Update state file
  fs.writeFileSync(PATHS.stateFile, JSON.stringify(state, null, 2), 'utf-8');

  // 3. Append to historical log
  const logEntry = `\n---\n### Run ${state.lastRunTimestamp} · ${state.activeRepoCount} repos active · ${state.pitchesCount} pitches · ${state.issuesCount} site issues\n`;
  fs.appendFileSync(PATHS.logFile, logEntry, 'utf-8');

  return PATHS.reportFile;
}
