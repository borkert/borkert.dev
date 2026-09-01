/**
 * borkert.dev — Vercel Brand Visual Style Script
 * Handles subtle theme toggling with preference persistence and
 * exposes client-side WebMCP agent tools for AI browser agents.
 */

(() => {
  'use strict';

  // --- Theme Management ---
  const themeToggleBtn = document.getElementById('theme-toggle');
  const storedTheme = localStorage.getItem('digplan-theme');
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (document.body) {
      document.body.setAttribute('data-theme', theme);
      if (theme === 'dark') {
        document.body.classList.add('dark-theme');
        document.body.classList.remove('light-theme');
      } else {
        document.body.classList.add('light-theme');
        document.body.classList.remove('dark-theme');
      }
    }
    updateToggleLabel(theme);
  }

  function updateToggleLabel(theme) {
    if (themeToggleBtn) {
      themeToggleBtn.textContent = theme === 'dark' ? 'light mode' : 'dark mode';
    }
  }

  // Initialize theme
  if (storedTheme) {
    applyTheme(storedTheme);
  } else {
    updateToggleLabel(systemPrefersDark ? 'dark' : 'light');
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || (systemPrefersDark ? 'dark' : 'light');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('digplan-theme', newTheme);
      applyTheme(newTheme);
    });
  }

  // Listen for system theme changes if no stored manual preference
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('digplan-theme')) {
      updateToggleLabel(e.matches ? 'dark' : 'light');
    }
  });

  // --- WebMCP (Web Model Context Protocol) Tools ---
  // Expose structured profile and systems data to AI browser agents if supported.
  const modelContext = (typeof document !== 'undefined' && document.modelContext) ||
                       (typeof navigator !== 'undefined' && navigator.modelContext);

  if (modelContext && typeof modelContext.registerTool === 'function') {
    const SYSTEMS_CATALOG = [
      {
        name: 'apicat',
        summary: 'APIs as executable definitions (YAML compiled to CLI and TypeScript library).',
        url: 'https://github.com/digplan/apicat',
        package: 'https://www.npmjs.com/package/apicat',
        whenToUse: 'When building LLM tool calling pipelines and needing compact, token-efficient YAML schemas.'
      },
      {
        name: 'prolific',
        summary: 'Minimal, environment-scoped coding agent in Bun with apicat routing and /bench harness.',
        url: 'https://github.com/digplan/prolific',
        whenToUse: 'When needing reproducible coding agents with scoped memory and deterministic evaluation.'
      },
      {
        name: 'benchforge',
        summary: 'Benchmark infrastructure and repeatable evaluation workflows for AI systems.',
        url: 'https://github.com/digplan/benchforge',
        whenToUse: 'When evaluating LLM coding, reasoning, and tool use with deterministic pass@k exit codes.'
      },
      {
        name: 'llm-scorer',
        summary: 'Primitives for scoring model outputs and validating reasoning steps.',
        url: 'https://github.com/digplan/llm-scorer',
        whenToUse: 'When building LLM-as-a-judge pipelines with bias mitigation.'
      },
      {
        name: 'compare-llms',
        summary: 'Tools for empirical model comparison and reasoning divergence.',
        url: 'https://github.com/digplan/compare-llms',
        whenToUse: 'When analyzing chain-of-thought branch divergence across model architectures.'
      },
      {
        name: 'vanilla-light',
        summary: 'A no-build, dependency-free full-stack web framework on Bun.',
        url: 'https://github.com/digplan/vanilla-light',
        whenToUse: 'When building zero-build web applications with reactive client and Bun server.'
      },
      {
        name: 'workflow',
        summary: 'Tooling for expressing and executing composable workflows via Unix pipes.',
        url: 'https://github.com/digplan/workflow',
        whenToUse: 'When building multi-step automation pipelines with Unix-style streams.'
      }
    ];

    try {
      modelContext.registerTool({
        name: 'get_site_summary',
        description: 'Returns profile metadata, research focus, and core principles for Chris Borkert.',
        inputSchema: { type: 'object', properties: {} },
        execute: () => ({
          author: 'Chris Borkert',
          title: 'Software Engineer & AI Systems Researcher',
          url: 'https://borkert.dev',
          github: 'https://github.com/digplan',
          email: 'chris@borkert.dev',
          llmsIndex: 'https://borkert.dev/llms.txt',
          instructions: 'https://borkert.dev/agent-instructions.md',
          focus: 'AI agent infrastructure, declarative tool protocols, deterministic sandboxes, and empirical evaluation harnesses.'
        }),
        annotations: { readOnlyHint: true }
      });

      modelContext.registerTool({
        name: 'list_systems',
        description: 'Lists all open-source systems, developer tools, and evaluation frameworks by Chris Borkert.',
        inputSchema: { type: 'object', properties: {} },
        execute: () => SYSTEMS_CATALOG,
        annotations: { readOnlyHint: true }
      });

      modelContext.registerTool({
        name: 'get_system_details',
        description: 'Retrieves detailed metadata and when-to-use guidance for a specific system by name.',
        inputSchema: {
          type: 'object',
          properties: {
            name: { type: 'string', description: 'Name of the system (e.g. apicat, prolific, benchforge, llm-scorer)' }
          },
          required: ['name']
        },
        execute: (input) => {
          const match = SYSTEMS_CATALOG.find((s) => s.name.toLowerCase() === (input?.name || '').toLowerCase());
          return match || { error: `System '${input?.name}' not found. Available: ${SYSTEMS_CATALOG.map((s) => s.name).join(', ')}` };
        },
        annotations: { readOnlyHint: true }
      });
    } catch {
      // Gracefully ignore registration failure in non-WebMCP runtime
    }
  }
})();
