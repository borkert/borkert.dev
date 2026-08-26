#!/usr/bin/env python3
"""
parse-results.py — Aggregates raw benchmark metrics, token telemetry (in/out/cached), and cost into Markdown tables.
"""

import os
import json
import glob
import argparse
from pathlib import Path
from token_accountant import calculate_cost, parse_aider_tokens, parse_evalplus_tokens, parse_log_tokens, PRICING_TABLE

def parse_args():
    parser = argparse.ArgumentParser(description="Parse benchmark results into markdown tables.")
    parser.add_argument("--results-dir", default="results", help="Directory containing benchmark results")
    parser.add_argument("--traces-dir", default="traces", help="Directory containing execution traces")
    parser.add_argument("--timestamp", default=None, help="Timestamp of the specific run")
    return parser.parse_args()

def main():
    args = parse_args()
    results_dir = Path(args.results_dir)
    traces_dir = Path(args.traces_dir)

    print(f"[Results Parser] Scanning results: {results_dir.resolve()}")
    print(f"[Results Parser] Scanning traces: {traces_dir.resolve()}")

    models = ["z-ai/glm-5.2", "google/gemini-3.7-flash", "deepseek/deepseek-v4-flash-0731"]
    
    scores = {m: {"evalplus": "Pending", "aider": "Pending", "bigcodebench": "Pending", "livebench": "Pending"} for m in models}
    tokens = {m: {"prompt": 0, "cached": 0, "completion": 0, "cost": 0.0} for m in models}

    # 1. EvalPlus Results
    for eval_file in results_dir.glob("evalplus/**/evalplus_results.json"):
        try:
            with open(eval_file) as f:
                data = json.load(f)
                model = data.get("model", "")
                pass_at_1 = data.get("pass@1", "N/A")
                if model in scores:
                    scores[model]["evalplus"] = f"{pass_at_1:.1%}" if isinstance(pass_at_1, float) else str(pass_at_1)
        except Exception:
            pass

    # 2. Aider Bench Results
    for aider_file in results_dir.glob("aider/**/*.json"):
        try:
            with open(aider_file) as f:
                data = json.load(f)
                model = data.get("model", "")
                pass_rate = data.get("pass_rate", "N/A")
                if model in scores:
                    scores[model]["aider"] = f"{pass_rate:.1%}" if isinstance(pass_rate, float) else str(pass_rate)
        except Exception:
            pass

    # 3. BigCodeBench Results
    for bcb_file in results_dir.glob("bigcodebench/**/*.json"):
        try:
            with open(bcb_file) as f:
                data = json.load(f)
                model = data.get("model", "")
                score = data.get("pass@1", "N/A")
                if model in scores:
                    scores[model]["bigcodebench"] = f"{score:.1%}" if isinstance(score, float) else str(score)
        except Exception:
            pass

    # 4. LiveBench Results
    for lb_file in results_dir.glob("livebench/**/judgment.json"):
        try:
            with open(lb_file) as f:
                data = json.load(f)
                model = data.get("model", "")
                avg_score = data.get("average", "N/A")
                if model in scores:
                    scores[model]["livebench"] = f"{avg_score:.1f}" if isinstance(avg_score, float) else str(avg_score)
        except Exception:
            pass

    # 5. Aggregate Token Telemetry & Cost per Model
    for m in models:
        safe_m = m.replace("/", "_")
        # Check trace logs
        t_prompt, t_cached, t_comp = 0, 0, 0
        for log_file in traces_dir.glob(f"**/*{safe_m}*.log"):
            log_stats = parse_log_tokens(log_file)
            t_prompt += log_stats["prompt"]
            t_cached += log_stats["cached"]
            t_comp += log_stats["completion"]

        tokens[m]["prompt"] = t_prompt
        tokens[m]["cached"] = t_cached
        tokens[m]["completion"] = t_comp
        tokens[m]["cost"] = calculate_cost(m, t_prompt, t_cached, t_comp)

    # Output Markdown Tables
    md_output = []
    md_output.append("## 1. Empirical Multi-Benchmark Evaluation Results\n")
    md_output.append("| Model | EvalPlus (Pass@1) | Aider Bench (Diff Edit %) | BigCodeBench Lite (%) | LiveBench (Overall) |")
    md_output.append("| :--- | :--- | :--- | :--- | :--- |")
    for m in models:
        md_output.append(f"| **`{m}`** | {scores[m]['evalplus']} | {scores[m]['aider']} | {scores[m]['bigcodebench']} | {scores[m]['livebench']} |")

    md_output.append("\n## 2. Token Telemetry & Empirical Cost Breakdown\n")
    md_output.append("| Model | Input Tokens | Cached Tokens | Output Tokens | Total Tokens | Live Cost (USD) |")
    md_output.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    total_cost_cohort = 0.0
    for m in models:
        p = tokens[m]["prompt"]
        c = tokens[m]["cached"]
        o = tokens[m]["completion"]
        tot = p + o
        cost = tokens[m]["cost"]
        total_cost_cohort += cost
        md_output.append(f"| **`{m}`** | {p:,} | {c:,} | {o:,} | {tot:,} | **${cost:.4f}** |")

    md_output.append(f"| **COHORT TOTAL** | — | — | — | — | **${total_cost_cohort:.4f}** |")

    table_str = "\n".join(md_output)
    print("\n" + table_str + "\n")

    out_file = results_dir / "summary_table.md"
    with open(out_file, "w") as f:
        f.write(table_str)
    print(f"[Results Parser] Saved markdown summary and token ledger to {out_file.resolve()}")

if __name__ == "__main__":
    main()

