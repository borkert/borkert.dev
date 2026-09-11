#!/usr/bin/env node

/**
 * runner.js — CLI Entrypoint for borkert.dev Daily Editorial Agent
 *
 * Usage:
 *   node scripts/editorial-agent/runner.js [options]
 *
 * Options:
 *   --since <string>    Override git scan start time (e.g. '24 hours ago', '2026-09-10')
 *   --queue             Refresh queue without scanning repos
 *   --audit             Run site audit only
 *   --dry-run           Print report to stdout without writing files
 *   --help, -h          Show help message
 */

import fs from 'node:fs';
import { PATHS } from './config.js';
import { scanAllRepositories } from './git-scanner.js';
import { auditSite } from './site-auditor.js';
import { inspectStyleInbox } from './style-inbox-watcher.js';
import { getDraftQueue, saveQueue } from './queue-manager.js';
import { synthesizePitches } from './llm-synthesizer.js';
import { generateDailyReport, saveReportAndLog } from './reporter.js';

async function run() {
  const startTime = Date.now();
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
borkert.dev Daily Editorial Agent

Usage:
  node scripts/editorial-agent/runner.js [options]

Options:
  --since <string>    Git lookback window (default: since last run or 48h)
  --queue             Refresh and print draft queue only
  --audit             Run site audit only
  --dry-run           Simulate run without writing files
  --help, -h          Show help
    `);
    process.exit(0);
  }

  const isDryRun = args.includes('--dry-run');
  const queueOnly = args.includes('--queue');
  const auditOnly = args.includes('--audit');

  // Parse --since arg
  let sinceArg = null;
  const sinceIdx = args.indexOf('--since');
  if (sinceIdx !== -1 && args[sinceIdx + 1]) {
    sinceArg = args[sinceIdx + 1];
  }

  // Load prior state
  let lastRunTimestamp = null;
  if (fs.existsSync(PATHS.stateFile)) {
    try {
      const state = JSON.parse(fs.readFileSync(PATHS.stateFile, 'utf-8'));
      lastRunTimestamp = state.lastRunTimestamp;
    } catch {
      lastRunTimestamp = null;
    }
  }

  const effectiveSince = sinceArg || lastRunTimestamp || '48 hours ago';

  console.log(`[borkert.dev Editorial Agent] Initializing run...`);
  console.log(`  Lookback window: ${effectiveSince}`);

  // 1. Site Audit
  console.log(`  → Auditing site health & document parity...`);
  const siteAudit = auditSite();
  if (auditOnly) {
    console.log(JSON.stringify(siteAudit, null, 2));
    process.exit(0);
  }

  // 2. Draft Queue reconciliation
  console.log(`  → Reconciling draft queue & evaluating rubric scores...`);
  const queueData = getDraftQueue(siteAudit);
  if (queueOnly) {
    saveQueue(queueData);
    console.log(`  ✓ Saved queue to ${PATHS.queueFile}`);
    console.log(fs.readFileSync(PATHS.queueFile, 'utf-8'));
    process.exit(0);
  }

  // 3. Scan Git Repositories
  console.log(`  → Scanning developer repositories for recent activity...`);
  const scannedRepos = scanAllRepositories(effectiveSince);
  console.log(`  ✓ Found ${scannedRepos.length} repo(s) with active development`);

  // 4. Style Inbox
  console.log(`  → Inspecting style-inbox for design proposals...`);
  const styleInbox = inspectStyleInbox();

  // 5. Synthesize Pitches
  console.log(`  → Synthesizing high-signal post pitches via editorial engine...`);
  const newPitches = await synthesizePitches(scannedRepos);
  console.log(`  ✓ Generated ${newPitches.length} post candidate(s)`);

  // Update pitches in queue
  queueData.pitches = newPitches;
  if (!isDryRun) {
    saveQueue(queueData);
  }

  // 6. Generate Daily Report
  const executionTimeMs = Date.now() - startTime;
  const reportMarkdown = generateDailyReport({
    scannedRepos,
    siteAudit,
    styleInbox,
    queueData,
    pitches: newPitches,
    executionTimeMs
  });

  const runState = {
    lastRunTimestamp: new Date().toISOString(),
    executionTimeMs,
    activeRepoCount: scannedRepos.length,
    pitchesCount: newPitches.length,
    issuesCount: siteAudit.issues.length,
    draftsNeedingReviewCount: queueData.drafts.filter(d => d.stage === 'NEEDS_AUTHOR_REVIEW').length
  };

  if (!isDryRun) {
    saveReportAndLog(reportMarkdown, runState);
    console.log(`  ✓ Written Daily Report: ${PATHS.reportFile}`);
    console.log(`  ✓ Updated State File: ${PATHS.stateFile}`);
    console.log(`  ✓ Updated Queue File: ${PATHS.queueFile}`);
  } else {
    console.log(`\n=== DRY RUN REPORT ===\n`);
    console.log(reportMarkdown);
  }

  console.log(`\n[borkert.dev Editorial Agent] Run completed successfully in ${executionTimeMs}ms.\n`);
}

run().catch(err => {
  console.error(`[borkert.dev Editorial Agent Error]:`, err);
  process.exit(1);
});
