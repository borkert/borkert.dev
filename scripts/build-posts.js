#!/usr/bin/env node

/**
 * build-posts.js — Automated, zero-dependency Markdown to HTML build pipeline
 * Transforms blog post drafts in drafts/ into production-ready HTML posts in posts/
 * Conforms strictly to borkert.dev's Vercel Brand Visual System and Web Standards.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseMarkdown, escapeHtml } from './md-parser.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');
const DRAFTS_DIR = path.join(ROOT_DIR, 'drafts');
const POSTS_DIR = path.join(ROOT_DIR, 'posts');

/**
 * Derives output HTML slug from a markdown filename
 * e.g., 'draft-benchmarks-without-harness.md' -> 'benchmarks-without-harness'
 * e.g., 'zero-build-frontend.md' -> 'zero-build-frontend'
 */
export function deriveSlug(filename) {
  const base = path.basename(filename, path.extname(filename));
  return base.replace(/^draft-/, '');
}

/**
 * Generates full post HTML page adhering to the Vercel Brand Visual System
 */
export function renderPostTemplate({
  title,
  meta,
  description,
  contentHtml,
  slug,
  author = 'Chris Borkert',
  domain = 'https://borkert.dev'
}) {
  const canonicalUrl = `${domain}/posts/${slug}.html`;
  const safeTitle = escapeHtml(title);
  const safeDescription = escapeHtml(description);
  const safeAuthor = escapeHtml(author);

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${safeTitle} — ${safeAuthor}</title>
  <meta name="description" content="${safeDescription}">
  <meta name="author" content="${safeAuthor}">
  <link rel="canonical" href="${canonicalUrl}">

  <!-- Open Graph -->
  <meta property="og:title" content="${safeTitle}">
  <meta property="og:description" content="${safeDescription}">
  <meta property="og:url" content="${canonicalUrl}">
  <meta property="og:type" content="article">

  <!-- Theme Color -->
  <meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">

  <!-- Geist Typography (Vercel Brand Guideline) -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400..600&family=Geist+Mono:wght@400..600&display=swap" rel="stylesheet" referrerpolicy="no-referrer">

  <!-- Vercel Brand Stylesheet -->
  <link rel="stylesheet" href="/assets/vercel-brand.css?v=2">
  <link rel="stylesheet" href="/styles.css?v=2">
</head>
<body class="vbg-report">
  <div class="vbg-shell">
    <a class="vbg-skip-link" href="#main">Skip to main content</a>

    <header class="vbg-header">
      <div class="vbg-masthead">
        <div class="vbg-identity">
          <a href="/" class="site-link-mono">← borkert.dev</a>
        </div>
      </div>
    </header>

    <main id="main">
      <article class="post-content">
        <header class="post-header">
          <h1 class="vbg-title">${safeTitle}</h1>
          ${meta ? `<div class="post-meta">${escapeHtml(meta)}</div>` : ''}
        </header>

        ${contentHtml}

      </article>
    </main>

    <footer class="vbg-footer">
      <div class="site-footer-brand">
        <span class="site-logo-mark" aria-hidden="true">▲</span>
        <span>${safeAuthor} · <a href="https://github.com/digplan">github.com/digplan</a> · <a href="mailto:chris@borkert.dev">chris@borkert.dev</a></span>
      </div>
      <div>
        <a href="/" class="site-link-mono">borkert.dev</a>
      </div>
    </footer>
  </div>

  <script src="/main.js?v=2"></script>
</body>
</html>
`;
}

/**
 * Transforms a single Markdown file to HTML and writes to destination
 */
export function buildPost(inputPath, options = {}) {
  const outDir = options.outDir || POSTS_DIR;
  if (!fs.existsSync(inputPath)) {
    throw new Error(`Input file not found: ${inputPath}`);
  }

  const rawMarkdown = fs.readFileSync(inputPath, 'utf-8');
  const parsed = parseMarkdown(rawMarkdown, options);
  const slug = options.slug || deriveSlug(inputPath);
  const outFilename = `${slug}.html`;
  const outPath = path.join(outDir, outFilename);

  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  const html = renderPostTemplate({
    title: parsed.title,
    meta: parsed.meta,
    description: parsed.description,
    contentHtml: parsed.contentHtml,
    slug,
    author: parsed.frontmatter.author || 'Chris Borkert',
    domain: options.domain || 'https://borkert.dev'
  });

  fs.writeFileSync(outPath, html, 'utf-8');
  return { inputPath, outPath, slug, parsed };
}

/**
 * Builds all drafts in drafts/ into posts/
 */
export function buildAllPosts(options = {}) {
  const draftsDir = options.draftsDir || DRAFTS_DIR;
  const outDir = options.outDir || POSTS_DIR;

  if (!fs.existsSync(draftsDir)) {
    console.warn(`Drafts directory does not exist: ${draftsDir}`);
    return [];
  }

  const files = fs.readdirSync(draftsDir)
    .filter(file => file.endsWith('.md') && !file.startsWith('.'));

  const results = [];
  for (const file of files) {
    const inputPath = path.join(draftsDir, file);
    try {
      const res = buildPost(inputPath, { ...options, outDir });
      results.push(res);
      console.log(`  ✓ Built post: ${path.relative(ROOT_DIR, inputPath)} → ${path.relative(ROOT_DIR, res.outPath)}`);
    } catch (err) {
      console.error(`  ✗ Error building ${file}: ${err.message}`);
    }
  }

  return results;
}

/**
 * Synchronizes posts with sitemap.xml
 */
export function syncSitemap(builtPosts, options = {}) {
  const sitemapPath = path.join(ROOT_DIR, 'sitemap.xml');
  if (!fs.existsSync(sitemapPath)) return;

  const today = new Date().toISOString().split('T')[0];
  const postUrls = builtPosts.map(p => `https://borkert.dev/posts/${p.slug}.html`);

  let currentSitemap = fs.readFileSync(sitemapPath, 'utf-8');

  for (const post of builtPosts) {
    const loc = `https://borkert.dev/posts/${post.slug}.html`;
    if (!currentSitemap.includes(loc)) {
      const entry = `  <url>\n    <loc>${loc}</loc>\n    <lastmod>${today}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>\n</urlset>`;
      currentSitemap = currentSitemap.replace('</urlset>', entry);
    }
  }

  fs.writeFileSync(sitemapPath, currentSitemap, 'utf-8');
  console.log(`  ✓ Synced sitemap.xml with ${builtPosts.length} posts`);
}

/**
 * Watches drafts directory for changes and triggers buildPost
 */
export function watchDrafts(options = {}) {
  const draftsDir = options.draftsDir || DRAFTS_DIR;
  console.log(`Watching for Markdown changes in ${path.relative(ROOT_DIR, draftsDir)}...`);

  // Initial build
  buildAllPosts(options);

  fs.watch(draftsDir, (eventType, filename) => {
    if (filename && filename.endsWith('.md') && !filename.startsWith('.')) {
      const inputPath = path.join(draftsDir, filename);
      if (fs.existsSync(inputPath)) {
        console.log(`[${new Date().toLocaleTimeString()}] Change detected in ${filename}. Rebuilding...`);
        try {
          const res = buildPost(inputPath, options);
          console.log(`  ✓ Updated: ${path.relative(ROOT_DIR, res.outPath)}`);
        } catch (err) {
          console.error(`  ✗ Failed to rebuild ${filename}: ${err.message}`);
        }
      }
    }
  });
}

/**
 * CLI Runner
 */
function runCli() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
borkert.dev — Markdown to HTML Post Builder

Usage:
  node scripts/build-posts.js [options] [file]

Options:
  --all               Build all Markdown files in drafts/ to posts/ (default if no file given)
  --file <path>       Build a specific markdown file
  --watch, -w         Watch drafts/ for changes and recompile automatically
  --sync-sitemap      Update sitemap.xml with all compiled posts
  --out-dir <dir>     Specify custom output directory (default: posts/)
  --help, -h          Show this help message

Examples:
  node scripts/build-posts.js --all
  node scripts/build-posts.js drafts/draft-benchmarks-without-harness.md
  node scripts/build-posts.js --watch
    `);
    process.exit(0);
  }

  const isWatch = args.includes('--watch') || args.includes('-w');
  const doSyncSitemap = args.includes('--sync-sitemap');
  const outDirIdx = args.indexOf('--out-dir');
  const customOutDir = outDirIdx !== -1 && args[outDirIdx + 1] ? path.resolve(args[outDirIdx + 1]) : POSTS_DIR;

  const fileArgIdx = args.indexOf('--file');
  let singleFile = null;
  if (fileArgIdx !== -1 && args[fileArgIdx + 1]) {
    singleFile = path.resolve(args[fileArgIdx + 1]);
  } else {
    const nonFlagArgs = args.filter(a => !a.startsWith('-'));
    if (nonFlagArgs.length > 0) {
      singleFile = path.resolve(nonFlagArgs[0]);
    }
  }

  if (isWatch) {
    watchDrafts({ outDir: customOutDir });
    return;
  }

  if (singleFile) {
    console.log(`Building post: ${path.relative(ROOT_DIR, singleFile)}...`);
    const res = buildPost(singleFile, { outDir: customOutDir });
    console.log(`✓ Successfully compiled to ${path.relative(ROOT_DIR, res.outPath)}`);
    if (doSyncSitemap) {
      syncSitemap([res]);
    }
    return;
  }

  // Default: build all
  console.log(`Building all blog posts from ${path.relative(ROOT_DIR, DRAFTS_DIR)} → ${path.relative(ROOT_DIR, customOutDir)}...`);
  const results = buildAllPosts({ outDir: customOutDir });
  if (doSyncSitemap) {
    syncSitemap(results);
  }
  console.log(`\nCompleted. Built ${results.length} posts.\n`);
}

// Only execute CLI when invoked directly
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(__filename)) {
  runCli();
}
