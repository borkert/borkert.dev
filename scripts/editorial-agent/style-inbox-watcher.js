/**
 * style-inbox-watcher.js — Monitors style-inbox/ for design explorations & style updates
 */

import fs from 'node:fs';
import path from 'node:path';
import { PATHS } from './config.js';

export function inspectStyleInbox() {
  if (!fs.existsSync(PATHS.styleInboxDir)) {
    return { pendingCount: 0, proposals: [] };
  }

  const files = fs.readdirSync(PATHS.styleInboxDir)
    .filter(f => !f.startsWith('.') && f !== 'README.md' && f !== 'template-proposal.md');

  if (files.length === 0) {
    return {
      pendingCount: 0,
      proposals: [],
      note: 'Style inbox is clean. Drop design specs or CSS snippets from powerful models into style-inbox/ to generate review reports.'
    };
  }

  const proposals = [];

  for (const filename of files) {
    const filePath = path.join(PATHS.styleInboxDir, filename);
    const content = fs.readFileSync(filePath, 'utf-8');
    const ext = path.extname(filename).toLowerCase();

    // Check for build-tool anti-patterns in vanilla context
    const hasTailwindDirectives = /@tailwind|@apply/i.test(content);
    const hasSassVariables = /\$[a-zA-Z0-9_-]+:/i.test(content);
    const hasNpmImports = /@import\s+['"](?!https?:\/\/|\/|\.)/i.test(content);

    const warnings = [];
    if (hasTailwindDirectives) {
      warnings.push('Contains Tailwind directives (@tailwind/@apply). borkert.dev requires zero-build vanilla CSS.');
    }
    if (hasSassVariables) {
      warnings.push('Contains Sass variables ($var). Convert to standard CSS custom properties (--var).');
    }
    if (hasNpmImports) {
      warnings.push('Contains bare npm module imports. Use native CSS imports or bundle-free CDN.');
    }

    // Extract proposed CSS variables
    const cssVarMatches = content.match(/--[a-zA-Z0-9_-]+:\s*[^;]+;/g) || [];

    proposals.push({
      filename,
      filePath,
      ext,
      sizeBytes: Buffer.byteLength(content, 'utf-8'),
      cssVariableCount: cssVarMatches.length,
      sampleTokens: cssVarMatches.slice(0, 5),
      warnings,
      isValidVanilla: warnings.length === 0
    });
  }

  return {
    pendingCount: proposals.length,
    proposals
  };
}
