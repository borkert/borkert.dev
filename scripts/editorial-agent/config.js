/**
 * config.js — Configuration for borkert.dev Daily Editorial Agent
 */

import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const HOME_DIR = process.env.HOME || os.homedir() || '/Users/chris';
export const ROOT_DIR = path.resolve(__dirname, '../..');

export const PATHS = {
  root: ROOT_DIR,
  draftsDir: path.join(ROOT_DIR, 'drafts'),
  postsDir: path.join(ROOT_DIR, 'posts'),
  styleInboxDir: path.join(ROOT_DIR, 'style-inbox'),
  queueFile: path.join(ROOT_DIR, 'drafts/QUEUE.md'),
  queueJson: path.join(ROOT_DIR, 'drafts/queue.json'),
  reportFile: path.join(ROOT_DIR, 'drafts/DAILY-REPORT.md'),
  logFile: path.join(ROOT_DIR, 'drafts/EDITORIAL-LOG.md'),
  stateFile: path.join(ROOT_DIR, 'drafts/.editorial-state.json'),
  indexHtml: path.join(ROOT_DIR, 'index.html'),
  sitemapXml: path.join(ROOT_DIR, 'sitemap.xml'),
  llmsTxt: path.join(ROOT_DIR, 'llms.txt'),
  llmsFullTxt: path.join(ROOT_DIR, 'llms-full.txt'),
  agentInstructions: path.join(ROOT_DIR, 'agent-instructions.md'),
  skillsDir: path.join(ROOT_DIR, '.agents/skills'),
  stylesCss: path.join(ROOT_DIR, 'styles.css'),
  brandCss: path.join(ROOT_DIR, 'assets/vercel-brand.css'),
};

// Priority repositories to scan for new development
export const PRIORITY_REPOS = [
  'borkert.dev',
  'gateway-agent',
  'agent-platform',
  'prolific',
  'apicat',
  'avo',
  'capstone',
  'workflow',
  'mitm-llm',
  'gemma4.c',
  'Classes',
  'football-data',
  'infer-engine',
  'housekeeper',
  'indxr'
];

// Repos to ignore during auto-discovery
export const IGNORED_REPOS = [
  'Library',
  '.Trash',
  'Applications',
  '.gemini',
  '.local',
  'daytona-test'
];

// LLM settings
export const LLM_CONFIG = {
  // Check available providers in order of preference
  openrouterApiKey: process.env.OPENROUTER_API_KEY || '',
  openrouterModel: process.env.EDITORIAL_MODEL || 'anthropic/claude-sonnet-5',
  
  openaiCompatibleBaseUrl: process.env.OPENAI_COMPATIBLE_BASE_URL || '',
  openaiCompatibleApiKey: process.env.OPENAI_COMPATIBLE_API_KEY || '',
  openaiCompatibleModel: process.env.OPENAI_COMPATIBLE_MODEL || 'gpt-oss-120b',

  anthropicApiKey: process.env.ANTHROPIC_API_KEY || '',
  geminiApiKey: process.env.GEMINI_API_KEY || '',
  timeoutMs: 60000,
};

// Editorial rules & banned AI clichés (from blog-post-writer & blog-post-phd)
export const BANNED_PATTERNS = [
  /\bdelve\b/i,
  /\btapestry\b/i,
  /\btestament\b/i,
  /\bvibrant\b/i,
  /\bpivotal\b/i,
  /\bcrucial\b/i,
  /\bfoster\b/i,
  /\bintricate\b/i,
  /\bshowcase\b/i,
  /\bnavigate\b/i,
  /\bholistic\b/i,
  /\bbespoke\b/i,
  /\bseamlessly\b/i,
  /\bgame-changer\b/i,
  /\brevolutionize\b/i,
  /\blandscape\b/i,
  /\bin today's rapidly evolving\b/i,
  /\bat its core\b/i,
  /\bin conclusion\b/i,
  /\blet's dive in\b/i,
  /\bnot only .* but also\b/i,
  /\bit's not .* it's\b/i,
  /\bas everyone knows\b/i,
  /\bthe well-known problem of\b/i,
  /\bit is widely understood\b/i,
  /\ba frequent pitfall\b/i,
  /\bmost engineers do\b/i,
  /\bcommonly seen\b/i
];

export const PIPELINE_STAGES = [
  'PITCH',
  'OUTLINE',
  'DRAFT',
  'NEEDS_AUTHOR_REVIEW',
  'PHD_RUBRIC_AUDIT',
  'READY_TO_PUBLISH',
  'PUBLISHED'
];
