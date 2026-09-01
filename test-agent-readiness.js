/**
 * Automated Test Suite: borkert.dev Agent Readiness & Modern Web Standards Verification
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)));

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

console.log('Running Agent Readiness & Modern Web Verification Suite...');

// 1. Test Content Without JavaScript (Fix 1)
testSection('1. Content Without JavaScript & Semantic HTML', () => {
  const indexPath = path.join(ROOT_DIR, 'index.html');
  assert(fs.existsSync(indexPath), 'index.html exists');

  const html = fs.readFileSync(indexPath, 'utf-8');
  assert(/Chris Borkert/i.test(html), 'index.html contains Chris Borkert');

  // Strip tags and comments to measure raw text content length
  const textOnly = html
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  assert(textOnly.length >= 500, `Raw HTML text content is ${textOnly.length} chars (must be >= 500)`);
  assert(/<header[\s>]/i.test(html) && html.includes('</header>'), 'Uses semantic <header>');
  assert(/<main[\s>]/i.test(html) && html.includes('</main>'), 'Uses semantic <main>');
  assert(html.includes('<section') && html.includes('</section>'), 'Uses semantic <section>');
  assert(html.includes('<article') && html.includes('</article>'), 'Uses semantic <article>');
  assert(/<footer[\s>]/i.test(html) && html.includes('</footer>'), 'Uses semantic <footer>');
  assert(html.includes('<link rel="canonical" href="https://borkert.dev/">'), 'Contains canonical link');
  assert(/skip-link/i.test(html) && html.includes('href="#main"'), 'Contains accessible skip link pointing to #main');
});

// 2. Test Agent-Friendly 404s (Fix 2)
testSection('2. Agent-Friendly 404 Page', () => {
  const notFoundPath = path.join(ROOT_DIR, '404.html');
  assert(fs.existsSync(notFoundPath), '404.html exists in root for GitHub Pages / Cloudflare');

  const notFoundHtml = fs.readFileSync(notFoundPath, 'utf-8');
  assert(/<h1[^>]*>[\s\S]*?404[\s\S]*?<\/h1>/i.test(notFoundHtml), '404.html has an <h1> containing 404');
  assert(/<meta\s+name=["']robots["']\s+content=["']noindex,\s*follow["']/i.test(notFoundHtml), '404.html has noindex, follow robots meta');
  assert(notFoundHtml.includes('Recovery Guide') || notFoundHtml.includes('404 Recovery'), '404.html contains recovery guide');
  assert(notFoundHtml.includes('https://borkert.dev/llms.txt') || notFoundHtml.includes('/llms.txt'), '404.html points agents to llms.txt');
  assert(notFoundHtml.includes('https://borkert.dev/sitemap.xml') || notFoundHtml.includes('/sitemap.xml'), '404.html points agents to sitemap.xml');
  assert(notFoundHtml.includes('https://borkert.dev/index.md') || notFoundHtml.includes('/index.md'), '404.html points agents to index.md');
});

// 3. Test Markdown Content Negotiation & Discoverability (Fix 3)
testSection('3. Markdown Content Negotiation (acceptmarkdown.com)', () => {
  const indexMdPath = path.join(ROOT_DIR, 'index.md');
  assert(fs.existsSync(indexMdPath), 'index.md exists as markdown representation');

  const mdContent = fs.readFileSync(indexMdPath, 'utf-8');
  assert(mdContent.startsWith('# Chris Borkert'), 'index.md has valid H1 title');
  assert(mdContent.includes('apicat') && mdContent.includes('prolific') && mdContent.includes('benchforge'), 'index.md includes all major systems');

  const indexHtml = fs.readFileSync(path.join(ROOT_DIR, 'index.html'), 'utf-8');
  assert(/<link[^>]+rel=["']alternate["'][^>]+type=["']text\/markdown["'][^>]+href=["']\/index\.md["']/i.test(indexHtml), 'index.html advertises /index.md via link rel="alternate"');

  const workerPath = path.join(ROOT_DIR, 'cloudflare-worker.js');
  assert(fs.existsSync(workerPath), 'cloudflare-worker.js recipe exists for edge Accept negotiation');
  const workerContent = fs.readFileSync(workerPath, 'utf-8');
  assert(workerContent.includes('text/markdown') && workerContent.includes('Vary') && workerContent.includes('Accept'), 'Worker enforces Vary: Accept, Accept-Encoding on markdown negotiation');
});

// 4. Test JSON-LD Structured Data (Fix 4)
testSection('4. JSON-LD Structured Data Graph', () => {
  const indexHtml = fs.readFileSync(path.join(ROOT_DIR, 'index.html'), 'utf-8');
  const jsonLdMatch = indexHtml.match(/<script type=["']application\/ld\+json["']>([\s\S]*?)<\/script>/i);
  assert(jsonLdMatch !== null, 'Found <script type="application/ld+json"> tag in index.html');

  let jsonLdData;
  try {
    jsonLdData = JSON.parse(jsonLdMatch[1]);
    assert(true, 'JSON-LD is valid, parsable JSON');
  } catch (err) {
    assert(false, `JSON-LD failed to parse: ${err.message}`);
    return;
  }

  assert(jsonLdData['@context'] === 'https://schema.org', '@context is https://schema.org');
  assert(jsonLdData['@type'] === 'Person', '@type is Person');
  assert(jsonLdData.name === 'Chris Borkert', 'Person entity name is Chris Borkert');
  assert(jsonLdData.url === 'https://borkert.dev', 'Person entity url is https://borkert.dev');
  assert(jsonLdData.email === 'mailto:chris@borkert.dev', 'Person entity email is present');
  assert(Array.isArray(jsonLdData.sameAs) && jsonLdData.sameAs.includes('https://github.com/digplan'), 'Person entity sameAs contains GitHub');
});

// 5. Test Agent Instruction & When-to-Use Guidance (Fix 5)
testSection('5. Agent Instruction & When-to-Use Guidance', () => {
  const llmsPath = path.join(ROOT_DIR, 'llms.txt');
  assert(fs.existsSync(llmsPath), 'llms.txt exists');

  const llmsContent = fs.readFileSync(llmsPath, 'utf-8');
  assert(llmsContent.startsWith('# Chris Borkert'), 'llms.txt has H1 header per llmstxt.org specification');
  assert(llmsContent.includes('> '), 'llms.txt has blockquote summary per llmstxt.org specification');
  assert(llmsContent.toLowerCase().includes('when to use'), 'llms.txt includes explicit "When to Use" guidance');
  assert(llmsContent.includes('apicat') && llmsContent.includes('prolific') && llmsContent.includes('benchforge'), 'llms.txt mentions key systems and their jobs');

  const llmsFullPath = path.join(ROOT_DIR, 'llms-full.txt');
  assert(fs.existsSync(llmsFullPath), 'llms-full.txt exists for full context ingestion');

  const agentInstructionsPath = path.join(ROOT_DIR, 'agent-instructions.md');
  assert(fs.existsSync(agentInstructionsPath), 'agent-instructions.md exists');
  const agentInstructions = fs.readFileSync(agentInstructionsPath, 'utf-8');
  assert(agentInstructions.includes('Decision Matrix') || agentInstructions.includes('When to Use'), 'agent-instructions.md has decision matrix');
});

// 6. Test Sitemaps & Robots Discovery
testSection('6. Sitemaps & Robots Discovery', () => {
  const sitemapPath = path.join(ROOT_DIR, 'sitemap.xml');
  assert(fs.existsSync(sitemapPath), 'sitemap.xml exists');
  const sitemapContent = fs.readFileSync(sitemapPath, 'utf-8');
  assert(sitemapContent.includes('<urlset') && sitemapContent.includes('</urlset>'), 'sitemap.xml is valid XML urlset');
  assert(sitemapContent.includes('https://borkert.dev/'), 'sitemap.xml contains homepage');
  assert(sitemapContent.includes('https://borkert.dev/llms.txt'), 'sitemap.xml contains llms.txt');
  assert(sitemapContent.includes('https://borkert.dev/index.md'), 'sitemap.xml contains index.md');

  const robotsPath = path.join(ROOT_DIR, 'robots.txt');
  assert(fs.existsSync(robotsPath), 'robots.txt exists');
  const robotsContent = fs.readFileSync(robotsPath, 'utf-8');
  assert(robotsContent.includes('User-agent: *') && robotsContent.includes('Allow: /'), 'robots.txt allows crawlers');
  assert(robotsContent.includes('Sitemap: https://borkert.dev/sitemap.xml'), 'robots.txt points to sitemap.xml');
});

// 7. Test WebMCP & Theme Logic in main.js
testSection('7. WebMCP Tools & Theme Management (main.js)', () => {
  const mainJsPath = path.join(ROOT_DIR, 'main.js');
  assert(fs.existsSync(mainJsPath), 'main.js exists');

  const mainJs = fs.readFileSync(mainJsPath, 'utf-8');
  assert(mainJs.includes('digplan-theme'), 'Theme preference persistence preserved');
  assert(mainJs.includes('modelContext'), 'WebMCP modelContext referenced');
  assert(mainJs.includes('get_site_summary') && mainJs.includes('list_systems') && mainJs.includes('get_system_details'), 'WebMCP tools registered for AI agents');
});

console.log(`\n========================================`);
console.log(`Test Results: ${passedTests}/${totalTests} passed (${failedTests} failures)`);
console.log(`========================================\n`);

if (failedTests > 0) {
  process.exit(1);
}
