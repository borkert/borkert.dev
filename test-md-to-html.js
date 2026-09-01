/**
 * test-md-to-html.js — Automated test suite for Markdown to HTML transformation pipeline.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseMarkdown, parseInline, escapeHtml, slugify, extractFrontmatter } from './scripts/md-parser.js';
import { buildPost, buildAllPosts, deriveSlug, renderPostTemplate } from './scripts/build-posts.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname);

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

function assert(condition, message) {
  totalTests++;
  if (condition) {
    console.log(`  ✓ PASS: ${message}`);
    passedTests++;
  } else {
    console.error(`  ✗ FAIL: ${message}`);
    failedTests++;
  }
}

function testSection(title, fn) {
  console.log(`\n--- ${title} ---`);
  fn();
}

console.log('Running Markdown to HTML Transformation Test Suite...');

// 1. Test Inline Parser
testSection('1. Inline Formatting, Code, Links & Math', () => {
  assert(parseInline('**bold**') === '<strong>bold</strong>', 'Parses bold asterisks');
  assert(parseInline('*italic*') === '<em>italic</em>', 'Parses italic asterisks');
  assert(parseInline('***bold italic***') === '<strong><em>bold italic</em></strong>', 'Parses bold italic');
  assert(parseInline('~~deleted~~') === '<del>deleted</del>', 'Parses strikethrough');
  assert(parseInline('`const x = 10;`') === '<code>const x = 10;</code>', 'Parses inline code');
  assert(parseInline('`<Tag attr="val">`') === '<code>&lt;Tag attr=&quot;val&quot;&gt;</code>', 'Escapes HTML inside inline code');
  assert(parseInline('[Link](https://borkert.dev)') === '<a href="https://borkert.dev">Link</a>', 'Parses standard link');
  assert(parseInline('![Alt](image.png "Title")') === '<img src="image.png" alt="Alt" title="Title">', 'Parses image with title');
  assert(parseInline('$pass@1$') === '<span class="vbg-formula">pass@1</span>', 'Parses simple inline math');
  assert(parseInline('$\\text{Model} \\times \\text{Harness}$') === '<span class="vbg-formula">Model &times; Harness</span>', 'Parses and cleans LaTeX inline formula');
  assert(parseInline('variable_name_with_underscores') === 'variable_name_with_underscores', 'Preserves snake_case variables without italic corruption');
});

// 2. Test Headings & Anchor Slugs
testSection('2. Headings & Slug Generation', () => {
  assert(slugify('Model Leaderboards Mean Nothing Without the Harness') === 'model-leaderboards-mean-nothing-without-the-harness', 'Slugifies standard heading');
  assert(slugify('1. The Output Contract & Edit Syntax') === '1-the-output-contract-edit-syntax', 'Slugifies numbered heading with ampersand');
  assert(slugify('EvalPlus ($pass@1$)') === 'evalplus-pass1', 'Slugifies heading with math');

  const md = `
# Main Post Title

## Section A
Paragraph in A.

## Section B
Paragraph in B.

### Subsection B.1
Deep details.
`;
  const parsed = parseMarkdown(md);
  assert(parsed.title === 'Main Post Title', 'Extracts H1 as post title');
  assert(parsed.contentHtml.includes('<h2 id="section-a">Section A</h2>'), 'Generates H2 with anchor ID');
  assert(parsed.contentHtml.includes('<h2 id="section-b">Section B</h2>'), 'Generates H2 with anchor ID');
  assert(parsed.contentHtml.includes('<h3 id="subsection-b1">Subsection B.1</h3>'), 'Generates H3 with anchor ID');
});

// 3. Test GFM Tables
testSection('3. GFM Tables & Alignment', () => {
  const tableMd = `
| Model | Tasks Solved | Mean Pass Rate |
| :--- | :---: | ---: |
| **Ox Alpha** | 8 / 10 | 80% |
| Claude Fable 5 | ~6.5 / 10 | 65% |
`;
  const parsed = parseMarkdown(tableMd);
  assert(parsed.contentHtml.includes('<div class="vbg-table-wrap">'), 'Wraps table in .vbg-table-wrap container');
  assert(parsed.contentHtml.includes('<table class="vbg-table">'), 'Uses .vbg-table class');
  assert(parsed.contentHtml.includes('<th scope="col">Model</th>'), 'Left aligned header');
  assert(parsed.contentHtml.includes('<th scope="col" data-align="center">Tasks Solved</th>'), 'Center aligned header');
  assert(parsed.contentHtml.includes('<th scope="col" class="vbg-numeric">Mean Pass Rate</th>'), 'Right / numeric aligned header');
  assert(parsed.contentHtml.includes('<th scope="row"><strong>Ox Alpha</strong></th>'), 'Row header first column with bold inline');
  assert(parsed.contentHtml.includes('<td class="vbg-numeric">80%</td>'), 'Numeric cell formatting');
});

// 4. Test Code Blocks & Escaping
testSection('4. Fenced Code Blocks & Mermaid Support', () => {
  const codeMd = `
\`\`\`python
def test_calc():
    assert 2 < 3 and 4 > 1
    return "<ok>"
\`\`\`

\`\`\`mermaid
flowchart LR
    A --> B
\`\`\`
`;
  const parsed = parseMarkdown(codeMd);
  assert(parsed.contentHtml.includes('<pre class="code-block"><code class="language-python">'), 'Adds language class to code block');
  assert(parsed.contentHtml.includes('assert 2 &lt; 3 and 4 &gt; 1'), 'Escapes HTML entities < and > inside code block');
  assert(parsed.contentHtml.includes('return &quot;&lt;ok&gt;&quot;'), 'Escapes quotes and tags in code');
  assert(parsed.contentHtml.includes('<pre class="code-block mermaid"><code class="language-mermaid">'), 'Handles Mermaid diagram code block');
  assert(parsed.hasMermaid === true, 'Sets hasMermaid flag when mermaid diagrams exist');
});

// 5. Test Blockquotes & GitHub Callouts
testSection('5. Blockquotes & Callouts', () => {
  const quoteMd = `
> Standard single-paragraph quote.

> [!NOTE]
> This is a crucial note about system architecture.

> [!WARNING]
> Breaking changes ahead.
`;
  const parsed = parseMarkdown(quoteMd);
  assert(parsed.contentHtml.includes('<blockquote>'), 'Renders standard blockquote');
  assert(parsed.contentHtml.includes('<div class="vbg-callout" data-variant="note"><h4>NOTE</h4><p>This is a crucial note about system architecture.</p></div>'), 'Renders NOTE callout');
  assert(parsed.contentHtml.includes('<div class="vbg-callout" data-variant="warning"><h4>WARNING</h4><p>Breaking changes ahead.</p></div>'), 'Renders WARNING callout');
});

// 6. Test Nested Lists
testSection('6. Nested Lists (Ordered & Unordered)', () => {
  const listMd = `
1. Step 1
   * Sub-item A
   * Sub-item B
2. Step 2
   1. Sub-step 2.1
   2. Sub-step 2.2
`;
  const parsed = parseMarkdown(listMd);
  assert(parsed.contentHtml.includes('<ol>'), 'Renders ordered list');
  assert(parsed.contentHtml.includes('<ul>'), 'Renders nested unordered list');
  assert(parsed.contentHtml.includes('<li>Step 1'), 'Renders parent list item');
  assert(parsed.contentHtml.includes('<li>Sub-item A</li>'), 'Renders nested list item');
});

// 7. Test Frontmatter & Full Post Generation
testSection('7. Frontmatter & Vercel Brand Template Rendering', () => {
  const postMd = `---
title: "Custom Post Title"
description: "Custom post description for meta tags"
author: "Chris Borkert"
---

*By Chris Borkert · August 2026 · AI Systems*

Paragraph content here.
`;
  const parsed = parseMarkdown(postMd);
  assert(parsed.title === 'Custom Post Title', 'Extracts frontmatter title');
  assert(parsed.description === 'Custom post description for meta tags', 'Extracts frontmatter description');
  assert(parsed.meta === 'By Chris Borkert · August 2026 · AI Systems', 'Extracts post-meta subtitle');

  const html = renderPostTemplate({
    title: parsed.title,
    meta: parsed.meta,
    description: parsed.description,
    contentHtml: parsed.contentHtml,
    slug: 'custom-post-slug',
    hasMermaid: false
  });

  assert(html.includes('<!doctype html>'), 'Outputs valid HTML5 doctype');
  assert(html.includes('<body class="vbg-report">'), 'Includes .vbg-report body class');
  assert(html.includes('<div class="vbg-shell">'), 'Includes .vbg-shell container');
  assert(html.includes('<link rel="canonical" href="https://borkert.dev/posts/custom-post-slug.html">'), 'Includes canonical link');
  assert(html.includes('<h1 class="vbg-title">Custom Post Title</h1>'), 'Includes .vbg-title heading');
  assert(html.includes('<div class="post-meta">By Chris Borkert · August 2026 · AI Systems</div>'), 'Includes .post-meta');
  assert(html.includes('<link rel="stylesheet" href="/assets/vercel-brand.css?v=2">'), 'Links vercel-brand.css');
  assert(html.includes('<link rel="stylesheet" href="/styles.css?v=2">'), 'Links styles.css');
});

// 8. End-to-End Build All Drafts
testSection('8. End-to-End Compilation of Real Drafts in drafts/', () => {
  const results = buildAllPosts();
  assert(results.length >= 4, `Compiled ${results.length} draft files from drafts/`);

  for (const res of results) {
    assert(fs.existsSync(res.outPath), `Generated HTML file exists: ${path.basename(res.outPath)}`);
    const content = fs.readFileSync(res.outPath, 'utf-8');
    assert(content.includes('<article class="post-content">'), `${res.slug}.html contains article.post-content`);
    assert(content.includes('class="vbg-title"'), `${res.slug}.html contains .vbg-title`);
    assert(content.includes('class="vbg-report"'), `${res.slug}.html conforms to vbg-report`);
    assert(!content.includes('\x1A_MD_TOKEN_'), `${res.slug}.html contains zero unreplaced placeholder tokens`);
    assert(!content.includes('___PLCHLDR_'), `${res.slug}.html contains zero unreplaced legacy placeholders`);
  }
});

console.log(`\n========================================`);
console.log(`Test Results: ${passedTests}/${totalTests} passed (${failedTests} failures)`);
console.log(`========================================\n`);

if (failedTests > 0) {
  process.exit(1);
}
