/**
 * llm-synthesizer.js — Synthesizes git activity into empirical blog pitches & skeptic reviews
 */

import { LLM_CONFIG } from './config.js';

/**
 * System prompt embedding blog-post-writer and blog-post-phd principles
 */
const SYSTEM_PROMPT = `
You are the Senior Editorial Director and Systems Reviewer for borkert.dev (Chris Borkert's research blog).
Target Audience: Graduate-level CS practitioners, systems researchers, principal engineers.
Voice: First person, direct, grounded, zero fluff, mechanistic prose.
Epistemic Invariants:
1. No presumed consensus ("as everyone knows", "the well-known problem").
2. No unquantified prevalence claims ("a frequent pitfall", "most engineers").
3. Concrete grounding in hardware, latencies (ms), sample sizes (N=20), tokens.
4. Banned AI tropes: delve, tapestry, pivotal, crucial, foster, intricate, showcase, navigate, holistic, bespoke, seamlessly, game-changer, revolutionize, landscape.
5. Invariant pseudocode (<25 lines) and Markdown tables for data.

Your job:
Evaluate the user's recent git commits across their repositories.
For any repository with meaningful technical development, generate:
1. A mechanism-oriented blog post title.
2. The mechanical dilemma (what was expected vs what actually happened in production/code).
3. The empirical thesis.
4. Required benchmark or trace measurements (hardware, sample sizes, latencies).
5. 2-3 adversarial skeptic challenge questions that ONLY the human engineer (Chris) can answer based on running the actual system.

Format output as valid JSON.
`;

/**
 * Calls OpenRouter or OpenAI-compatible endpoint
 */
async function callLlm(prompt) {
  const apiKey = LLM_CONFIG.openrouterApiKey || LLM_CONFIG.openaiCompatibleApiKey;
  if (!apiKey) {
    return null; // Fallback to deterministic synthesis
  }

  const endpoint = LLM_CONFIG.openrouterApiKey
    ? 'https://openrouter.ai/api/v1/chat/completions'
    : `${LLM_CONFIG.openaiCompatibleBaseUrl.replace(/\/+$/, '')}/chat/completions`;

  const model = LLM_CONFIG.openrouterApiKey
    ? LLM_CONFIG.openrouterModel
    : LLM_CONFIG.openaiCompatibleModel;

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${apiKey}`
  };

  if (LLM_CONFIG.openrouterApiKey) {
    headers['HTTP-Referer'] = 'https://borkert.dev';
    headers['X-Title'] = 'borkert.dev Editorial Agent';
  }

  const body = JSON.stringify({
    model,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: prompt }
    ],
    temperature: 0.3,
    max_tokens: 1800,
    response_format: { type: 'json_object' }
  });

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), LLM_CONFIG.timeoutMs);

    const res = await fetch(endpoint, {
      method: 'POST',
      headers,
      body,
      signal: controller.signal
    });
    clearTimeout(timeout);

    if (!res.ok) {
      console.warn(`LLM request failed with status ${res.status}: ${await res.text()}`);
      return null;
    }

    const data = await res.json();
    const content = data.choices?.[0]?.message?.content;
    return content ? JSON.parse(content) : null;
  } catch (err) {
    console.warn(`LLM call error: ${err.message}. Falling back to deterministic synthesis.`);
    return null;
  }
}

/**
 * Deterministic synthesis when offline or no API key available
 */
function deterministicSynthesis(activeRepos) {
  const pitches = [];

  for (const repo of activeRepos) {
    if (repo.commitCount === 0 && repo.uncommittedCount === 0) continue;

    const commitSubjects = repo.commits.map(c => c.subject).join('; ');
    const isBenchmark = repo.commits.some(c => c.signals.includes('EMPIRICAL_BENCHMARK'));
    const isNewSystem = repo.commits.some(c => c.signals.includes('NEW_SYSTEM_OR_FEATURE'));
    const isBug = repo.commits.some(c => c.signals.includes('FORENSIC_FAILURE_OR_BUG'));

    let title = '';
    let dilemma = '';
    let thesis = '';
    let evidence = '';

    if (repo.name === 'gateway-agent' || commitSubjects.includes('gateway-agent')) {
      title = 'Bridging Personal Assistants to Unix Pipes via iMessage and Discord';
      dilemma = 'Commercial agent frameworks require heavy cloud microservices, but a local personal assistant only needs a 120-line bash socket loop and SQLite polling.';
      thesis = 'Running Antigravity CLI directly against macOS system internals (~/Library/Messages/chat.db) delivers sub-second mobile agent responses without external cloud dependencies.';
      evidence = 'Measure latency from phone tap to agy invocation (<800ms) and disk usage (<50MB).';
    } else if (repo.name === 'agent-platform' || isBenchmark) {
      title = 'The Multi-Model Sweep: Why Scaffolding Outweighs Parameter Count on Local Models';
      dilemma = 'Larger models are assumed to outperform smaller models on agentic tasks, but prompt format and execution feedback loops introduce higher variance than model weights.';
      thesis = 'Empirical evaluation across 7 Ollama models reveals that deterministic verification loops (compiler exit codes) improve 7B model task completion rates more than switching to a 70B model with static prompts.';
      evidence = 'Pass@k accuracy matrix, token consumption per task, and timeout frequencies across all 7 evaluated models.';
    } else if (isNewSystem) {
      title = `Deconstructing ${repo.name}: Design Invariants and Production Lessons`;
      dilemma = `Standard industry patterns for ${repo.name} introduce unnecessary abstraction layers that degrade observability and latency.`;
      thesis = `A minimal, declarative implementation with inspectable intermediate states achieves deterministic execution with zero framework overhead.`;
      evidence = `Memory footprint, lines of code vs standard alternatives, and error recovery traces.`;
    } else {
      title = `Engineering Notes: Recent Architectural Iterations in ${repo.name}`;
      dilemma = `Iterating on ${repo.name} revealed unexpected edge cases during local execution.`;
      thesis = `Focusing on deterministic rollback and state isolation simplifies maintenance and eliminates cascading failures.`;
      evidence = `Diff statistics (${repo.diffStatSummary ? repo.diffStatSummary.split('\n')[0] : 'recent commits'}).`;
    }

    pitches.push({
      repo: repo.name,
      title,
      sourceCommits: `${repo.commitCount} commit(s) on branch ${repo.branch}`,
      dilemma,
      thesis,
      evidenceRequired: evidence,
      skepticChallenges: [
        `What unexpected failure or runtime exception occurred during this commit sequence?`,
        `What exact hardware/benchmark configuration was used, and can the results be reproduced?`
      ]
    });
  }

  return { pitches };
}

/**
 * Synthesizes pitches from active repos using LLM with deterministic fallback
 */
export async function synthesizePitches(activeRepos) {
  if (!activeRepos || activeRepos.length === 0) {
    return [];
  }

  // Filter repos that have meaningful changes
  const candidateRepos = activeRepos.filter(r => r.commitCount > 0 || r.uncommittedCount > 3);
  if (candidateRepos.length === 0) {
    return [];
  }

  // Construct prompt summary
  const summary = candidateRepos.map(r => {
    const commits = r.commits.slice(0, 5).map(c => `  - [${c.hash}] ${c.subject} (${c.signals.join(', ')})`).join('\n');
    return `Repository: ${r.name} (${r.commitCount} commits)\n${commits}\nWorking Tree: ${r.uncommittedCount} uncommitted files`;
  }).join('\n\n');

  const prompt = `
Recent Git Development Activity across Repositories:
${summary}

Analyze this activity. Generate 1 to 3 compelling, empirical blog post pitches conforming strictly to the borkert.dev systems research guidelines. Return a JSON object with key "pitches", containing an array of:
{
  "repo": "repo-name",
  "title": "Mechanism-Oriented Post Title",
  "sourceCommits": "Summary of relevant commits",
  "dilemma": "The core mechanical dilemma (expected vs reality)",
  "thesis": "The defensible empirical thesis",
  "evidenceRequired": "Exact numbers, hardware, sample sizes N needed",
  "skepticChallenges": ["Challenging question 1", "Challenging question 2"]
}
`;

  const llmResult = await callLlm(prompt);
  if (llmResult && Array.isArray(llmResult.pitches) && llmResult.pitches.length > 0) {
    return llmResult.pitches;
  }

  // Deterministic fallback
  const fallback = deterministicSynthesis(candidateRepos);
  return fallback.pitches;
}
