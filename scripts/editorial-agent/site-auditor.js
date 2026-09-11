/**
 * site-auditor.js — Audits borkert.dev for content parity, sitemap sync, and documentation freshness
 */

import fs from 'node:fs';
import path from 'node:path';
import { PATHS } from './config.js';

export function auditSite() {
  const issues = [];
  const suggestions = [];

  // 1. Audit Drafts vs Posts
  const drafts = fs.readdirSync(PATHS.draftsDir)
    .filter(f => f.startsWith('draft-') && f.endsWith('.md'));
  
  const posts = fs.existsSync(PATHS.postsDir)
    ? fs.readdirSync(PATHS.postsDir).filter(f => f.endsWith('.html') && !f.startsWith('.'))
    : [];

  const draftSlugs = drafts.map(d => d.replace(/^draft-/, '').replace(/\.md$/, ''));
  const postSlugs = posts.map(p => p.replace(/\.html$/, ''));

  // Drafts not yet compiled
  const uncompiledDrafts = draftSlugs.filter(slug => !postSlugs.includes(slug));
  if (uncompiledDrafts.length > 0) {
    suggestions.push({
      category: 'DRAFT_BUILD',
      message: `${uncompiledDrafts.length} draft(s) not yet built to HTML: ${uncompiledDrafts.join(', ')}`,
      action: `Run 'npm run build' or 'node scripts/build-posts.js --file drafts/draft-<slug>.md'`
    });
  }

  // 2. Audit Posts vs index.html
  const indexHtml = fs.existsSync(PATHS.indexHtml) ? fs.readFileSync(PATHS.indexHtml, 'utf-8') : '';
  const unlinkedPosts = [];

  for (const postSlug of postSlugs) {
    const postLink = `/posts/${postSlug}.html`;
    if (!indexHtml.includes(postLink) && !indexHtml.includes(`href="posts/${postSlug}.html"`)) {
      unlinkedPosts.push(postSlug);
    }
  }

  if (unlinkedPosts.length > 0) {
    issues.push({
      severity: 'WARNING',
      category: 'UNLINKED_POST',
      message: `${unlinkedPosts.length} compiled post(s) are NOT linked on index.html: ${unlinkedPosts.map(p => `posts/${p}.html`).join(', ')}`,
      action: `Add an article entry to Section 01 (Writing & Research) in index.html`
    });
  }

  // 3. Audit Posts vs sitemap.xml
  const sitemapXml = fs.existsSync(PATHS.sitemapXml) ? fs.readFileSync(PATHS.sitemapXml, 'utf-8') : '';
  const missingFromSitemap = [];

  for (const postSlug of postSlugs) {
    const canonical = `https://borkert.dev/posts/${postSlug}.html`;
    if (!sitemapXml.includes(canonical)) {
      missingFromSitemap.push(postSlug);
    }
  }

  if (missingFromSitemap.length > 0) {
    issues.push({
      severity: 'WARNING',
      category: 'SITEMAP_PARITY',
      message: `${missingFromSitemap.length} post(s) missing from sitemap.xml: ${missingFromSitemap.join(', ')}`,
      action: `Run 'node scripts/build-posts.js --sync-sitemap'`
    });
  }

  // 4. Audit Machine Endpoints (agent-instructions.md & llms.txt)
  const agentInstructions = fs.existsSync(PATHS.agentInstructions)
    ? fs.readFileSync(PATHS.agentInstructions, 'utf-8')
    : '';
  const llmsTxt = fs.existsSync(PATHS.llmsTxt)
    ? fs.readFileSync(PATHS.llmsTxt, 'utf-8')
    : '';

  // Check if gateway-agent is mentioned
  if (!agentInstructions.includes('gateway-agent')) {
    suggestions.push({
      category: 'MACHINE_ENDPOINTS',
      message: `'gateway-agent' is not documented in agent-instructions.md or llms.txt`,
      action: `Add gateway-agent (iMessage & Discord daemon for Antigravity) to Section 2 of agent-instructions.md and llms.txt`
    });
  }

  // Check if avo is mentioned
  if (!agentInstructions.includes('avo') && fs.existsSync(path.join(PATHS.root, 'posts/avo-local-harness.html'))) {
    suggestions.push({
      category: 'MACHINE_ENDPOINTS',
      message: `'avo' (Agentic Variation Operators) is published as a post but missing from agent-instructions.md decision matrix`,
      action: `Add avo to agent-instructions.md decision table`
    });
  }

  return {
    totalDrafts: drafts.length,
    totalPosts: posts.length,
    uncompiledDrafts,
    unlinkedPosts,
    missingFromSitemap,
    issues,
    suggestions
  };
}
