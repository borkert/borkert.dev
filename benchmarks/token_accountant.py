#!/usr/bin/env python3
"""
token_accountant.py — Extracts exact token usage (in/out/cached) and computes live costs from benchmark traces.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any

# Current OpenRouter pricing per 1M tokens ($)
PRICING_TABLE = {
    "z-ai/glm-5.2": {
        "prompt": 1.19,
        "cached": 0.119,
        "completion": 3.74,
        "name": "GLM-5.2 (Zhipu AI)"
    },
    "google/gemini-3.7-flash": {
        "prompt": 0.375,
        "cached": 0.0375,
        "completion": 1.875,
        "name": "Gemini 3.7 Flash"
    },
    "deepseek/deepseek-v4-flash-0731": {
        "prompt": 0.07,
        "cached": 0.014,
        "completion": 0.14,
        "name": "DeepSeek Flash 0731"
    }
}

def calculate_cost(model_id: str, prompt_tokens: int, cached_tokens: int, completion_tokens: int) -> float:
    prices = PRICING_TABLE.get(model_id, {"prompt": 0.20, "cached": 0.05, "completion": 0.80})
    uncached_prompt = max(0, prompt_tokens - cached_tokens)
    cost = (
        (uncached_prompt / 1_000_000.0) * prices["prompt"] +
        (cached_tokens / 1_000_000.0) * prices["cached"] +
        (completion_tokens / 1_000_000.0) * prices["completion"]
    )
    return round(cost, 5)

def parse_aider_tokens(aider_dir: Path, model_id: str) -> Dict[str, int]:
    """Extracts tokens from Aider results and markdown logs."""
    stats = {"prompt": 0, "cached": 0, "completion": 0}
    # Check .aider.results.json or raw logs
    for json_file in aider_dir.glob("**/*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        stats["prompt"] += item.get("prompt_tokens", 0)
                        stats["cached"] += item.get("cached_tokens", 0)
                        stats["completion"] += item.get("completion_tokens", 0)
        except Exception:
            pass
    return stats

def parse_evalplus_tokens(evalplus_dir: Path, model_id: str) -> Dict[str, int]:
    """Extracts tokens from EvalPlus sample outputs."""
    stats = {"prompt": 0, "cached": 0, "completion": 0}
    for jsonl_file in evalplus_dir.glob("**/*.jsonl"):
        try:
            with open(jsonl_file) as f:
                for line in f:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    usage = item.get("usage", {})
                    stats["prompt"] += usage.get("prompt_tokens", 0)
                    stats["cached"] += usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
                    stats["completion"] += usage.get("completion_tokens", 0)
        except Exception:
            pass
    return stats

def parse_log_tokens(log_file: Path) -> Dict[str, int]:
    """Regex fallback scanner on raw run stdout/stderr logs."""
    stats = {"prompt": 0, "cached": 0, "completion": 0}
    if not log_file.exists():
        return stats
    try:
        with open(log_file) as f:
            content = f.read()
            # Match standard OpenAI/OpenRouter token reporting
            prompts = re.findall(r'"prompt_tokens":\s*(\d+)', content)
            completions = re.findall(r'"completion_tokens":\s*(\d+)', content)
            cached = re.findall(r'"cached_tokens":\s*(\d+)', content)
            stats["prompt"] = sum(int(x) for x in prompts)
            stats["completion"] = sum(int(x) for x in completions)
            stats["cached"] = sum(int(x) for x in cached)
    except Exception:
        pass
    return stats
