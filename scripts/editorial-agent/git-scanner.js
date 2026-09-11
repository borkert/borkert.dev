/**
 * git-scanner.js — Scans developer repositories for recent git activity & changes
 */

import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { HOME_DIR, PRIORITY_REPOS, IGNORED_REPOS } from './config.js';

/**
 * Discovers git repositories under the user's home directory
 */
export function discoverRepositories(baseDir = HOME_DIR) {
  const repos = new Map();

  // 1. Add priority repos first if they exist
  for (const name of PRIORITY_REPOS) {
    const repoPath = path.join(baseDir, name);
    if (fs.existsSync(path.join(repoPath, '.git'))) {
      repos.set(name, repoPath);
    }
  }

  // 2. Discover additional top-level directories containing .git
  try {
    const entries = fs.readdirSync(baseDir, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory() || entry.name.startsWith('.')) continue;
      if (IGNORED_REPOS.includes(entry.name)) continue;

      const repoPath = path.join(baseDir, entry.name);
      if (fs.existsSync(path.join(repoPath, '.git')) && !repos.has(entry.name)) {
        repos.set(entry.name, repoPath);
      }
    }
  } catch (err) {
    console.warn(`Warning: Could not list directory ${baseDir}: ${err.message}`);
  }

  return repos;
}

/**
 * Executes a git command safely in a repository directory
 */
function runGit(repoPath, args) {
  try {
    return execSync(`git ${args}`, {
      cwd: repoPath,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 10000
    }).trim();
  } catch {
    return '';
  }
}

/**
 * Categorizes a commit or change based on technical signal
 */
function evaluateSignal(subject, files) {
  const lowerSub = subject.toLowerCase();
  const lowerFiles = files.join(' ').toLowerCase();

  const signals = [];
  if (/\b(bench|benchmark|eval|accuracy|latency|pass@k|metrics)\b/i.test(lowerSub + lowerFiles)) {
    signals.push('EMPIRICAL_BENCHMARK');
  }
  if (/\b(feat|release|initial|launch|v\d+\.)\b/i.test(lowerSub)) {
    signals.push('NEW_SYSTEM_OR_FEATURE');
  }
  if (/\b(fix|bug|crash|race|deadlock|leak|timeout|fallback)\b/i.test(lowerSub)) {
    signals.push('FORENSIC_FAILURE_OR_BUG');
  }
  if (/\b(refactor|protocol|schema|sandbox|runtime|engine)\b/i.test(lowerSub)) {
    signals.push('ARCHITECTURAL_INSIGHT');
  }
  if (/\b(zero-build|vanilla|css|component|dom)\b/i.test(lowerSub + lowerFiles)) {
    signals.push('FRONTEND_STANDARDS');
  }

  return signals.length > 0 ? signals : ['GENERAL_DEV'];
}

/**
 * Scans a single repository for commits, diff stats, and working tree changes
 */
export function scanRepository(name, repoPath, sinceIso) {
  const sinceArg = sinceIso ? `--since="${sinceIso}"` : '--since="48 hours ago"';

  // 1. Fetch recent commits
  const logOutput = runGit(repoPath, `log ${sinceArg} --pretty=format:"%H|%an|%ad|%s" --date=iso`);
  const commits = [];

  if (logOutput) {
    const lines = logOutput.split('\n').filter(Boolean);
    for (const line of lines) {
      const [hash, author, date, ...subjectParts] = line.split('|');
      const subject = subjectParts.join('|');
      
      // Get changed files for this commit
      const numstat = runGit(repoPath, `show --numstat --pretty="" ${hash}`);
      const filesChanged = [];
      if (numstat) {
        for (const statLine of numstat.split('\n')) {
          const parts = statLine.split('\t');
          if (parts.length >= 3) {
            filesChanged.push(parts[2]);
          }
        }
      }

      commits.push({
        hash: hash ? hash.substring(0, 8) : '',
        author,
        date,
        subject,
        signals: evaluateSignal(subject, filesChanged),
        filesChanged
      });
    }
  }

  // 2. Check uncommitted changes in working tree
  const statusOutput = runGit(repoPath, 'status --porcelain');
  const uncommittedFiles = statusOutput
    ? statusOutput.split('\n').map(l => l.trim()).filter(Boolean)
    : [];

  // 3. Get overall diff stat if there are commits
  let diffStatSummary = '';
  if (commits.length > 0) {
    const oldestCommit = commits[commits.length - 1].hash;
    diffStatSummary = runGit(repoPath, `diff --stat ${oldestCommit}^..HEAD`);
  }

  // Get current active branch
  const branch = runGit(repoPath, 'rev-parse --abbrev-ref HEAD') || 'unknown';

  const hasActivity = commits.length > 0 || uncommittedFiles.length > 0;

  return {
    name,
    path: repoPath,
    branch,
    hasActivity,
    commitCount: commits.length,
    commits,
    uncommittedCount: uncommittedFiles.length,
    uncommittedFiles,
    diffStatSummary
  };
}

/**
 * Scans all discovered repositories for activity since a given timestamp
 */
export function scanAllRepositories(sinceIso = null) {
  const repos = discoverRepositories();
  const results = [];

  for (const [name, repoPath] of repos.entries()) {
    const scan = scanRepository(name, repoPath, sinceIso);
    if (scan.hasActivity) {
      results.push(scan);
    }
  }

  return results;
}
