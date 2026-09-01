/**
 * md-parser.js — Zero-dependency, deterministic GitHub-Flavored Markdown (GFM) parser.
 * Designed specifically for borkert.dev blog posts and Vercel Brand Visual System.
 */

// HTML Entity Escaper
export function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Clean LaTeX math symbols for browser presentation
export function formatMathFormula(raw) {
  let cleaned = raw.trim();
  // Normalize \text{...} -> ...
  cleaned = cleaned.replace(/\\text\{([^}]+)\}/g, '$1');
  cleaned = cleaned.replace(/\\%/g, '%');
  cleaned = cleaned.replace(/\\times/g, '&times;');
  cleaned = cleaned.replace(/\\le(q)?/g, '&le;');
  cleaned = cleaned.replace(/\\ge(q)?/g, '&ge;');
  cleaned = cleaned.replace(/\\pm/g, '&plusmn;');
  cleaned = cleaned.replace(/\\approx/g, '&asymp;');
  cleaned = cleaned.replace(/\\neq/g, '&ne;');
  cleaned = cleaned.replace(/\\cdot/g, '&middot;');
  cleaned = cleaned.replace(/\\to|\\rightarrow/g, '&rarr;');
  return escapeHtml(cleaned).replace(/&amp;(times|le|ge|plusmn|asymp|ne|middot|rarr);/g, '&$1;');
}

// Slugify string for accessible heading anchor IDs
export function slugify(str) {
  return str
    .toLowerCase()
    .replace(/<[^>]+>/g, '') // Strip HTML tags
    .replace(/\$/g, '') // Strip math dollar signs
    .replace(/[^\w\s-]/g, '') // Remove non-word chars except hyphens and spaces
    .replace(/\s+/g, '-') // Replace spaces with hyphens
    .replace(/-+/g, '-') // Replace multiple hyphens with single hyphen
    .replace(/^-+|-+$/g, ''); // Trim leading and trailing hyphens
}

/**
 * Extract YAML frontmatter and markdown body from markdown text
 */
export function extractFrontmatter(rawMarkdown) {
  const normalized = rawMarkdown.replace(/\r\n/g, '\n');
  const frontmatterRegex = /^---\n([\s\S]*?)\n---\n/;
  const match = normalized.match(frontmatterRegex);

  if (!match) {
    return { frontmatter: {}, body: normalized };
  }

  const yamlBlock = match[1];
  const body = normalized.slice(match[0].length);
  const frontmatter = {};

  for (const line of yamlBlock.split('\n')) {
    const colonIdx = line.indexOf(':');
    if (colonIdx === -1) continue;
    const key = line.slice(0, colonIdx).trim();
    let val = line.slice(colonIdx + 1).trim();

    // Strip surrounding quotes
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    frontmatter[key] = val;
  }

  return { frontmatter, body };
}

export function normalizeUrl(url) {
  if (!url) return '';
  if (url.startsWith('file:///Users/chris/')) {
    const sub = url.replace(/^file:\/\/\/Users\/chris\//, '');
    return `https://github.com/digplan/${sub}`;
  }
  return url;
}

/**
 * Parses inline markdown: bold, italic, code, links, images, math, del
 */
export function parseInline(text) {
  if (!text) return '';

  const placeholders = [];
  function addPlaceholder(replacement) {
    // Use control character \x1A to prevent placeholder collisions with any markdown syntax
    const id = `\x1A_MD_TOKEN_${placeholders.length}_\x1A`;
    placeholders.push({ id, replacement });
    return id;
  }

  // 1. Protect inline code `...`
  let processed = text.replace(/(`+)((?:(?!\1)[^\n])+?)\1/g, (match, fence, code) => {
    return addPlaceholder(`<code>${escapeHtml(code)}</code>`);
  });

  // 2. Protect inline math $...$
  processed = processed.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
    return addPlaceholder(`<span class="vbg-formula">${formatMathFormula(formula)}</span>`);
  });

  // 3. Images: ![alt](url "title")
  processed = processed.replace(/!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g, (match, alt, url, title) => {
    const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
    const safeUrl = normalizeUrl(url);
    return addPlaceholder(`<img src="${escapeHtml(safeUrl)}" alt="${escapeHtml(alt)}"${titleAttr}>`);
  });

  // 4. Links: [text](url "title")
  processed = processed.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g, (match, label, url, title) => {
    const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
    const parsedLabel = parseInline(label);
    const safeUrl = normalizeUrl(url);
    return addPlaceholder(`<a href="${escapeHtml(safeUrl)}"${titleAttr}>${parsedLabel}</a>`);
  });

  // 5. Autolinks: <https://...> or <email@domain.com>
  processed = processed.replace(/<(https?:\/\/[^\s>]+)>/g, (match, url) => {
    return addPlaceholder(`<a href="${escapeHtml(url)}">${escapeHtml(url)}</a>`);
  });
  processed = processed.replace(/<([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>/g, (match, email) => {
    return addPlaceholder(`<a href="mailto:${escapeHtml(email)}">${escapeHtml(email)}</a>`);
  });

  // 6. Strikethrough (~~text~~)
  processed = processed.replace(/~~([^~]+)~~/g, '<del>$1</del>');

  // 7. Bold & Italic (***text***)
  processed = processed.replace(/\*\*\*([^\*\n]+)\*\*\*/g, '<strong><em>$1</em></strong>');

  // 8. Bold (**text** or __text__)
  processed = processed.replace(/\*\*([^\*\n]+)\*\*/g, '<strong>$1</strong>');
  processed = processed.replace(/(?:^|\s)__([^_\n]+)__(?:\s|$)/g, (m, p1) => m.replace(`__${p1}__`, `<strong>${p1}</strong>`));

  // 9. Italic (*text* or bounded _text_)
  processed = processed.replace(/\*([^\*\n]+)\*/g, '<em>$1</em>');
  // Avoid converting snake_case_variable names to italics by requiring non-word or space boundaries
  processed = processed.replace(/(^|[^\w])_([^_\n]+)_([^\w]|$)/g, '$1<em>$2</em>$3');

  // 10. Restore placeholders in reverse order
  for (let i = placeholders.length - 1; i >= 0; i--) {
    const { id, replacement } = placeholders[i];
    processed = processed.replaceAll(id, replacement);
  }

  return processed;
}

/**
 * Checks if a line is a table delimiter/separator row: e.g. | :--- | :---: | ---: |
 */
function isTableDelimiter(line) {
  if (!line) return false;
  const trimmed = line.trim();
  if (!trimmed.includes('|') && !trimmed.includes('-')) return false;
  const cells = trimmed.replace(/^\||\|$/g, '').split('|');
  if (cells.length === 0) return false;
  return cells.every(cell => /^[\s:]*-{3,}[\s:]*$/.test(cell));
}

/**
 * Parse alignment from delimiter row
 */
function parseAlignments(delimiterLine) {
  const cells = delimiterLine.trim().replace(/^\||\|$/g, '').split('|');
  return cells.map(cell => {
    const trimmed = cell.trim();
    const startColon = trimmed.startsWith(':');
    const endColon = trimmed.endsWith(':');
    if (startColon && endColon) return 'center';
    if (endColon) return 'right';
    return 'left';
  });
}

/**
 * Parse table block into HTML
 */
function parseTableBlock(lines) {
  if (lines.length < 2) return '';
  const headerLine = lines[0];
  const delimiterLine = lines[1];
  const dataLines = lines.slice(2);

  const alignments = parseAlignments(delimiterLine);
  const headerCells = headerLine.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());

  let html = '<div class="vbg-table-wrap">\n  <table class="vbg-table">\n    <thead>\n      <tr>\n';

  for (let i = 0; i < headerCells.length; i++) {
    const text = parseInline(headerCells[i]);
    const align = alignments[i] || 'left';
    const alignClass = align === 'right' ? ' class="vbg-numeric"' : '';
    const alignAttr = align === 'center' ? ' data-align="center"' : '';
    html += `        <th scope="col"${alignClass}${alignAttr}>${text}</th>\n`;
  }

  html += '      </tr>\n    </thead>\n    <tbody>\n';

  for (const rowLine of dataLines) {
    if (!rowLine.trim()) continue;
    const rowCells = rowLine.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());
    html += '      <tr>\n';

    for (let i = 0; i < headerCells.length; i++) {
      const cellText = rowCells[i] !== undefined ? parseInline(rowCells[i]) : '';
      const align = alignments[i] || 'left';
      const alignClass = align === 'right' ? ' class="vbg-numeric"' : '';
      const alignAttr = align === 'center' ? ' data-align="center"' : '';

      if (i === 0) {
        html += `        <th scope="row"${alignClass}${alignAttr}>${cellText}</th>\n`;
      } else {
        html += `        <td${alignClass}${alignAttr}>${cellText}</td>\n`;
      }
    }

    html += '      </tr>\n';
  }

  html += '    </tbody>\n  </table>\n</div>';
  return html;
}

/**
 * Parses markdown body into clean HTML elements
 */
export function parseMarkdown(markdownText, options = {}) {
  const { frontmatter, body } = extractFrontmatter(markdownText);
  const lines = body.replace(/\r\n/g, '\n').split('\n');

  const outputBlocks = [];
  const usedSlugs = new Set();

  function getUniqueSlug(text) {
    let slug = slugify(text);
    if (!slug) slug = 'section';
    if (!usedSlugs.has(slug)) {
      usedSlugs.add(slug);
      return slug;
    }
    let count = 1;
    while (usedSlugs.has(`${slug}-${count}`)) {
      count++;
    }
    const uniqueSlug = `${slug}-${count}`;
    usedSlugs.add(uniqueSlug);
    return uniqueSlug;
  }

  let i = 0;
  let hasExtractedMeta = false;
  let postTitle = frontmatter.title || '';
  let postMeta = '';
  let postDescription = frontmatter.description || '';

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // Skip empty lines
    if (trimmed === '') {
      i++;
      continue;
    }

    // 1. Fenced Code Blocks (``` or ~~~)
    const codeFenceMatch = line.match(/^(\s*)(`{3,}|~{3,})(.*)$/);
    if (codeFenceMatch) {
      const fenceChar = codeFenceMatch[2][0];
      const fenceLen = codeFenceMatch[2].length;
      const lang = codeFenceMatch[3].trim().toLowerCase();
      const codeLines = [];
      i++;

      while (i < lines.length) {
        const currentLine = lines[i];
        const closeMatch = currentLine.match(/^(\s*)(`{3,}|~{3,})\s*$/);
        if (closeMatch && closeMatch[2][0] === fenceChar && closeMatch[2].length >= fenceLen) {
          i++;
          break;
        }
        codeLines.push(currentLine);
        i++;
      }

      const escapedCode = escapeHtml(codeLines.join('\n'));
      if (lang === 'mermaid') {
        outputBlocks.push(`<div class="diagram-block">
  <div class="diagram-caption">Diagram</div>
  <pre class="code-block mermaid-source"><code class="language-mermaid">${escapedCode}</code></pre>
</div>`);
      } else if (lang) {
        outputBlocks.push(`<pre class="code-block"><code class="language-${lang}">${escapedCode}</code></pre>`);
      } else {
        outputBlocks.push(`<pre class="code-block"><code>${escapedCode}</code></pre>`);
      }
      continue;
    }

    // 2. Display Math Blocks ($$...$$)
    if (trimmed === '$$') {
      const mathLines = [];
      i++;
      while (i < lines.length && lines[i].trim() !== '$$') {
        mathLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) i++; // Consume closing $$
      const formula = formatMathFormula(mathLines.join('\n'));
      outputBlocks.push(`<div class="vbg-formula">${formula}</div>`);
      continue;
    }

    // 3. Horizontal Rules (---, ***, ___)
    if (/^(?:---|\*\*\*|___)\s*$/.test(trimmed)) {
      outputBlocks.push('<hr>');
      i++;
      continue;
    }

    // 4. Headings (# H1, ## H2, ### H3, #### H4)
    const headingMatch = line.match(/^(#{1,6})\s+(.+?)(?:\s+#+)?$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const headingText = headingMatch[2].trim();
      const inlineHeading = parseInline(headingText);

      // If this is the first H1 in the document and title is not explicitly in frontmatter
      if (level === 1 && !postTitle) {
        postTitle = headingText.replace(/<[^>]+>/g, '').trim();
        // Do not add the top H1 to the body output since post-header renders it
        i++;
        continue;
      }

      const slug = getUniqueSlug(headingText);
      outputBlocks.push(`<h${level} id="${slug}">${inlineHeading}</h${level}>`);
      i++;
      continue;
    }

    // 5. Post Metadata line (e.g. *By Chris Borkert · August 2026 · Category* or *Chris Borkert · ...*)
    // If we haven't found post-meta yet and this is an italic-wrapped line near the start
    if (!hasExtractedMeta && outputBlocks.length === 0 && /^(\*|_)(By\s+)?Chris Borkert[\s\S]*?\1$/.test(trimmed)) {
      postMeta = trimmed.slice(1, -1).trim();
      hasExtractedMeta = true;
      i++;
      continue;
    }

    // 6. GFM Tables
    if (trimmed.startsWith('|') || (trimmed.includes('|') && i + 1 < lines.length && isTableDelimiter(lines[i + 1]))) {
      const tableLines = [line];
      i++;
      while (i < lines.length && (lines[i].trim().startsWith('|') || lines[i].includes('|'))) {
        if (lines[i].trim() === '') break;
        tableLines.push(lines[i]);
        i++;
      }
      const tableHtml = parseTableBlock(tableLines);
      if (tableHtml) {
        outputBlocks.push(tableHtml);
        continue;
      }
    }

    // 7. Blockquotes and GitHub Alerts (> ...)
    if (trimmed.startsWith('>')) {
      const quoteLines = [];
      while (i < lines.length) {
        const curTrim = lines[i].trim();
        if (curTrim.startsWith('>')) {
          quoteLines.push(curTrim.replace(/^>\s?/, ''));
          i++;
        } else if (curTrim === '' || curTrim.startsWith('#') || curTrim.startsWith('```') || /^([*+-]|\d+\.)\s+/.test(curTrim)) {
          break;
        } else {
          quoteLines.push(lines[i]);
          i++;
        }
      }

      const quoteText = quoteLines.join('\n').trim();

      // Check for GitHub Alerts: [!NOTE], [!TIP], [!IMPORTANT], [!WARNING], [!CAUTION]
      const alertMatch = quoteText.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\](?:\s*\n)?([\s\S]*)$/i);
      if (alertMatch) {
        const alertType = alertMatch[1].toUpperCase();
        const alertContent = alertMatch[2].trim();
        const parsedAlertContent = parseInline(alertContent);
        outputBlocks.push(`<div class="vbg-callout" data-variant="${alertType.toLowerCase()}"><h4>${alertType}</h4><p>${parsedAlertContent}</p></div>`);
      } else {
        const paragraphs = quoteText.split(/\n\s*\n/).map(p => `<p>${parseInline(p.trim())}</p>`).join('\n');
        outputBlocks.push(`<blockquote>\n  ${paragraphs}\n</blockquote>`);
      }
      continue;
    }

    // 8. Lists (Unordered and Ordered)
    const isUnordered = /^(\s*)([*+-])\s+(.+)$/.test(line);
    const isOrdered = /^(\s*)(\d+)\.\s+(.+)$/.test(line);

    if (isUnordered || isOrdered) {
      const listLines = [];
      let inListCode = false;
      while (i < lines.length) {
        const curLine = lines[i];
        const isCurUnordered = /^(\s*)([*+-])\s+(.+)$/.test(curLine);
        const isCurOrdered = /^(\s*)(\d+)\.\s+(.+)$/.test(curLine);
        const isCurIndented = /^(\s+|\t+)\S/.test(curLine);
        const isCurFence = /^(\s*)(`{3,}|~{3,})/.test(curLine);

        if (isCurFence) {
          inListCode = !inListCode;
          listLines.push(curLine);
          i++;
          continue;
        }

        if (inListCode || isCurUnordered || isCurOrdered || (curLine.trim() !== '' && isCurIndented)) {
          listLines.push(curLine);
          i++;
        } else {
          break;
        }
      }

      const listHtml = parseListHierarchy(listLines);
      outputBlocks.push(listHtml);
      continue;
    }

    // 9. Passthrough HTML elements (like <div ...>, <table ...>, <details ...>)
    if (/^<([a-zA-Z0-9_-]+)[\s>]/.test(trimmed)) {
      const tagMatch = trimmed.match(/^<([a-zA-Z0-9_-]+)/);
      const tagName = tagMatch[1].toLowerCase();
      // Single line self-closing or inline tag
      if (trimmed.endsWith(`</${tagName}>`) || trimmed.endsWith('/>')) {
        outputBlocks.push(trimmed);
        i++;
        continue;
      }
      // Multiline HTML block
      const htmlLines = [line];
      i++;
      let closed = false;
      while (i < lines.length) {
        htmlLines.push(lines[i]);
        if (lines[i].includes(`</${tagName}>`)) {
          closed = true;
          i++;
          break;
        }
        i++;
      }
      outputBlocks.push(htmlLines.join('\n'));
      continue;
    }

    // 10. Regular Paragraph
    const paraLines = [trimmed];
    i++;
    while (i < lines.length) {
      const nextLine = lines[i];
      const nextTrimmed = nextLine.trim();
      if (nextTrimmed === '') break;
      if (nextLine.startsWith('#') || nextLine.startsWith('>') || nextLine.startsWith('```') ||
          /^(\s*)([*+-]|\d+\.)\s+/.test(nextLine) || /^(?:---|\*\*\*|___)\s*$/.test(nextTrimmed) ||
          (nextTrimmed.startsWith('|') && isTableDelimiter(lines[i + 1] || ''))) {
        break;
      }
      paraLines.push(nextTrimmed);
      i++;
    }

    const paraText = paraLines.join(' ');
    if (paraText) {
      // If we don't have a description yet, derive it from the first paragraph
      if (!postDescription) {
        postDescription = paraText
          .replace(/<[^>]+>/g, '')
          .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
          .replace(/[*_`~]/g, '')
          .slice(0, 160)
          .trim();
        if (paraText.length > 160) postDescription += '...';
      }

      outputBlocks.push(`<p>${parseInline(paraText)}</p>`);
    }
  }

  return {
    title: postTitle || 'Untitled Post',
    meta: postMeta,
    description: postDescription,
    frontmatter,
    contentHtml: outputBlocks.join('\n\n')
  };
}

/**
 * Parses nested list hierarchy into valid HTML (ul / ol)
 */
function parseListHierarchy(lines) {
  if (lines.length === 0) return '';

  const rootItems = [];
  const stack = [{ indent: -1, items: rootItems, isOrdered: false }];
  let insideCodeFence = false;
  let codeFenceChar = '';
  let codeFenceLen = 0;
  let codeFenceLang = '';
  let codeFenceLines = [];

  for (let idx = 0; idx < lines.length; idx++) {
    const line = lines[idx];

    // Check if we are currently inside an indented code fence
    if (insideCodeFence) {
      const closeMatch = line.match(/^(\s*)(`{3,}|~{3,})\s*$/);
      if (closeMatch && closeMatch[2][0] === codeFenceChar && closeMatch[2].length >= codeFenceLen) {
        insideCodeFence = false;
        const lastItem = findDeepestLastItem(rootItems);
        if (lastItem) {
          const escaped = escapeHtml(codeFenceLines.join('\n'));
          const langClass = codeFenceLang ? ` class="language-${codeFenceLang}"` : '';
          lastItem.content += `\n<pre class="code-block"><code${langClass}>${escaped}</code></pre>`;
        }
        codeFenceLines = [];
        continue;
      }
      codeFenceLines.push(line);
      continue;
    }

    // Check for start of an indented code fence inside a list
    const fenceMatch = line.match(/^(\s*)(`{3,}|~{3,})(.*)$/);
    if (fenceMatch && !/^(\s*)([*+-]|\d+\.)\s+/.test(line)) {
      insideCodeFence = true;
      codeFenceChar = fenceMatch[2][0];
      codeFenceLen = fenceMatch[2].length;
      codeFenceLang = fenceMatch[3].trim().toLowerCase();
      codeFenceLines = [];
      continue;
    }

    const uMatch = line.match(/^(\s*)([*+-])\s+(.*)$/);
    const oMatch = line.match(/^(\s*)(\d+)\.\s+(.*)$/);

    if (uMatch || oMatch) {
      const match = uMatch || oMatch;
      const indent = match[1].replace(/\t/g, '  ').length;
      const isOrdered = Boolean(oMatch);
      const content = match[3];

      while (stack.length > 1 && indent <= stack[stack.length - 1].indent) {
        stack.pop();
      }

      const currentParent = stack[stack.length - 1];
      const newItem = {
        content: parseInline(content),
        children: [],
        isOrdered
      };

      currentParent.items.push(newItem);
      stack.push({ indent, items: newItem.children, isOrdered });
    } else {
      // Continuation of previous item (e.g. blockquote or text)
      const lastItem = findDeepestLastItem(rootItems);
      if (lastItem) {
        const trimmed = line.trim();
        if (trimmed.startsWith('>')) {
          const quoteContent = parseInline(trimmed.replace(/^>\s?/, ''));
          lastItem.content += `\n<blockquote><p>${quoteContent}</p></blockquote>`;
        } else {
          lastItem.content += ' ' + parseInline(trimmed);
        }
      }
    }
  }

  return renderListHtml(rootItems);
}

function findDeepestLastItem(items) {
  if (!items || items.length === 0) return null;
  const last = items[items.length - 1];
  if (last.children && last.children.length > 0) {
    return findDeepestLastItem(last.children) || last;
  }
  return last;
}

function renderListHtml(items) {
  if (!items || items.length === 0) return '';
  const isOrdered = items[0].isOrdered;
  const tag = isOrdered ? 'ol' : 'ul';

  let html = `<${tag}>\n`;
  for (const item of items) {
    html += `  <li>${item.content}`;
    if (item.children && item.children.length > 0) {
      html += '\n' + renderListHtml(item.children).split('\n').map(l => '  ' + l).join('\n') + '\n';
    }
    html += '</li>\n';
  }
  html += `</${tag}>`;
  return html;
}
