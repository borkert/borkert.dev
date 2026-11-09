#!/usr/bin/env python3
"""Generate ~/capstone-style benchmark charts comparing 4 configurations:
1. Qwen 3.8 27B (Without PE)
2. Qwen 3.8 27B (With PE)
3. Qwen 4 27B (Without PE)
4. Qwen 4 27B (With PE)

Swap out numbers in `BENCH_DATA` below after tests finish and re-run:
    python3 scripts/generate_qwen4_pe_charts.py
    npm run build
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT_DIR, "assets", "charts")
os.makedirs(OUT_DIR, exist_ok=True)

# ==============================================================================
# 4-WAY BENCHMARK NUMBERS (Swap these out after tests finish)
# ==============================================================================
BENCH_DATA = {
    # 1 & 2: Qwen 3.8 27B (Without PE vs. With PE)
    "qwen38_without_pe_pct": 50.0,
    "qwen38_with_pe_pct": 75.0,
    "qwen38_without_pe_cnt": 45,       # out of 89
    "qwen38_with_pe_cnt": 67,          # out of 89
    "qwen38_without_pe_tokens": 102377,
    "qwen38_with_pe_tokens": 61327,
    "qwen38_without_pe_sec": 894.0,
    "qwen38_with_pe_sec": 325.3,
    "qwen38_without_pe_hr": 5.21,
    "qwen38_with_pe_hr": 1.90,

    # 3 & 4: Qwen 4 27B (Without PE vs. With PE)
    "qwen4_without_pe_pct": 15.0,
    "qwen4_with_pe_pct": 35.0,
    "qwen4_without_pe_cnt": 13,        # out of 89
    "qwen4_with_pe_cnt": 31,           # out of 89
    "qwen4_without_pe_tokens": 118000,
    "qwen4_with_pe_tokens": 69000,
    "qwen4_without_pe_sec": 960.0,
    "qwen4_with_pe_sec": 390.0,
    "qwen4_without_pe_hr": 5.60,
    "qwen4_with_pe_hr": 2.28,
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "axes.edgecolor": "#CBD5E1",
    "axes.linewidth": 0.8,
    "xtick.color": "#334155",
    "ytick.color": "#64748B",
    "text.color": "#0F172A",
    "figure.facecolor": "#FFFFFF",
    "axes.facecolor": "#FFFFFF",
    "savefig.facecolor": "#FFFFFF",
    "savefig.dpi": 300,
})

NAVY = "#1E293B"
TEAL_SLATE = "#2B5B6C"
LIGHT_GREY = "#94A3B8"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#475569"


def style_line_ax(ax, keep_left=True, keep_bottom=True, y_grid=True):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(keep_left)
    ax.spines["bottom"].set_visible(keep_bottom)
    if keep_left:
        ax.spines["left"].set_color("#CBD5E1")
        ax.spines["left"].set_linewidth(0.8)
    if keep_bottom:
        ax.spines["bottom"].set_color("#CBD5E1")
        ax.spines["bottom"].set_linewidth(0.8)
    if y_grid:
        ax.grid(axis="y", color="#F1F5F9", linestyle="-", linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
    else:
        ax.grid(False)
    ax.tick_params(axis="both", which="both", length=3, color="#CBD5E1")


def add_spanning_arrow(ax, direction="higher", side="left", offset=0.14, text_gap=0.032, label=None, color=TEXT_MUTED):
    if label is None:
        label = "Higher is better" if direction == "higher" else "Lower is better"
    x_pos = -offset if side == "left" else 1.0 + offset
    y_start, y_end = (0.0, 1.0) if direction == "higher" else (1.0, 0.0)

    ax.annotate(
        "",
        xy=(x_pos, y_end),
        xytext=(x_pos, y_start),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=dict(
            arrowstyle="-|>,head_length=0.55,head_width=0.32",
            color=color,
            lw=1.35,
            shrinkA=0,
            shrinkB=0,
        ),
        annotation_clip=False,
    )
    text_x = x_pos - text_gap if side == "left" else x_pos + text_gap
    rot = 90 if side == "left" else 270
    ax.text(
        text_x,
        0.5,
        label,
        transform=ax.transAxes,
        ha="center",
        va="center",
        rotation=rot,
        fontsize=8.8,
        fontweight="bold",
        color=color,
        clip_on=False,
    )


# ==============================================================================
# CHART 1: 4-Way Comparison — Resolution Rate (%) and Tasks Passed (N=89)
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.9), gridspec_kw={"width_ratios": [1, 1], "wspace": 0.34})

models = ["Qwen 3.8 27B", "Qwen 4 27B"]
x = np.arange(len(models))

# Left Panel: Resolution Rate (%)
base_pct = [BENCH_DATA["qwen38_without_pe_pct"], BENCH_DATA["qwen4_without_pe_pct"]]
pe_pct = [BENCH_DATA["qwen38_with_pe_pct"], BENCH_DATA["qwen4_with_pe_pct"]]

style_line_ax(ax1)
ax1.plot(x, base_pct, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=7.0, label="Without PE (Baseline)", zorder=3)
ax1.plot(x, pe_pct, color=NAVY, linewidth=2.7, marker="o", markersize=7.5, label="With PE (+ PromptEnhancer)", zorder=5)
ax1.fill_between(x, base_pct, pe_pct, color=NAVY, alpha=0.07, zorder=2)

ax1.set_xticks(x)
ax1.set_xticklabels(models, fontsize=9.2, fontweight="bold")
ax1.set_ylim(0, 100)
ax1.set_yticks([0, 25, 50, 75, 100])
ax1.set_xlim(-0.35, 1.35)
ax1.set_title("Resolution Rate (%)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="higher", side="left", offset=0.14, text_gap=0.032, color=NAVY)

c1_base_xy = [(-8, -16), (0, -16)]
c1_pe_xy = [(0, 9), (12, 9)]
for i in range(len(x)):
    diff = pe_pct[i] - base_pct[i]
    ax1.annotate(f"{base_pct[i]:.0f}%", (x[i], base_pct[i]), textcoords="offset points", xytext=c1_base_xy[i],
                 ha="center", va="bottom", fontsize=8.4, color=TEXT_MUTED)
    ax1.annotate(f"{pe_pct[i]:.0f}% (+{diff:.0f} pp)", (x[i], pe_pct[i]), textcoords="offset points", xytext=c1_pe_xy[i],
                 ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper right", ncol=1, fontsize=8.0)

# Right Panel: Tasks Passed (out of 89)
base_cnt = [BENCH_DATA["qwen38_without_pe_cnt"], BENCH_DATA["qwen4_without_pe_cnt"]]
pe_cnt = [BENCH_DATA["qwen38_with_pe_cnt"], BENCH_DATA["qwen4_with_pe_cnt"]]

style_line_ax(ax2)
ax2.plot(x, base_cnt, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=7.0, label="Without PE (Baseline)", zorder=3)
ax2.plot(x, pe_cnt, color=TEAL_SLATE, linewidth=2.7, marker="o", markersize=7.5, label="With PE (+ PromptEnhancer)", zorder=5)
ax2.fill_between(x, base_cnt, pe_cnt, color=TEAL_SLATE, alpha=0.07, zorder=2)

ax2.set_xticks(x)
ax2.set_xticklabels(models, fontsize=9.2, fontweight="bold")
ax2.set_ylim(0, 89)
ax2.set_yticks([0, 20, 40, 60, 80])
ax2.set_xlim(-0.35, 1.35)
ax2.set_title("Tasks Passed (out of 89)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="higher", side="left", offset=0.14, text_gap=0.032, color=TEAL_SLATE)

c2_base_xy = [(-10, -16), (0, -16)]
c2_pe_xy = [(0, 9), (14, 9)]
for i in range(len(x)):
    diff_cnt = pe_cnt[i] - base_cnt[i]
    ax2.annotate(f"{base_cnt[i]}/89 ({base_pct[i]:.0f}%)", (x[i], base_cnt[i]), textcoords="offset points", xytext=c2_base_xy[i],
                 ha="center", va="bottom", fontsize=8.3, color=TEXT_MUTED)
    ax2.annotate(f"{pe_cnt[i]}/89 (+{diff_cnt})", (x[i], pe_cnt[i]), textcoords="offset points", xytext=c2_pe_xy[i],
                 ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="upper right", ncol=1, fontsize=8.0)

fig.suptitle("Qwen 3.8 27B vs. Qwen 4 27B: Resolution Rate & Tasks Passed (With vs. Without PE)",
             x=0.04, y=0.95, ha="left", fontsize=12.6, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "chart1_qwen4_tasks_passed.png"))
plt.savefig(os.path.join(OUT_DIR, "qwen38_vs_qwen4_chart1.png"))
plt.close(fig)


# ==============================================================================
# CHART 2: 4-Way Comparison — Mean Tokens per Task & Mean Wall-Clock Seconds
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.9), gridspec_kw={"width_ratios": [1, 1], "wspace": 0.34})

base_tok = [BENCH_DATA["qwen38_without_pe_tokens"], BENCH_DATA["qwen4_without_pe_tokens"]]
pe_tok = [BENCH_DATA["qwen38_with_pe_tokens"], BENCH_DATA["qwen4_with_pe_tokens"]]

style_line_ax(ax1)
ax1.plot(x, base_tok, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=7.0, label="Without PE (Baseline)", zorder=3)
ax1.plot(x, pe_tok, color=NAVY, linewidth=2.7, marker="o", markersize=7.5, label="With PE (+ PromptEnhancer)", zorder=5)
ax1.fill_between(x, base_tok, pe_tok, color=NAVY, alpha=0.07, zorder=2)

ax1.set_xticks(x)
ax1.set_xticklabels(models, fontsize=9.2, fontweight="bold")
ax1.set_ylim(0, 145000)
ax1.set_yticks([0, 35000, 70000, 105000, 140000])
ax1.set_yticklabels(["0", "35k", "70k", "105k", "140k"])
ax1.set_xlim(-0.35, 1.35)
ax1.set_title("Mean Tokens per Solved Task", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="lower", side="left", offset=0.14, text_gap=0.032, color=NAVY)

for i in range(len(x)):
    pct_sav = (1.0 - pe_tok[i] / base_tok[i]) * 100.0
    ax1.annotate(f"{base_tok[i]:,}", (x[i], base_tok[i]), textcoords="offset points", xytext=(0, 8),
                 ha="center", va="bottom", fontsize=8.3, color=TEXT_MUTED)
    ax1.annotate(f"{pe_tok[i]:,} (-{pct_sav:.1f}%)", (x[i], pe_tok[i]), textcoords="offset points", xytext=(0, -16),
                 ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper left", ncol=1, fontsize=8.0)

# Right Panel: Mean Wall-Clock Seconds per Task
base_sec = [BENCH_DATA["qwen38_without_pe_sec"], BENCH_DATA["qwen4_without_pe_sec"]]
pe_sec = [BENCH_DATA["qwen38_with_pe_sec"], BENCH_DATA["qwen4_with_pe_sec"]]

style_line_ax(ax2)
ax2.plot(x, base_sec, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=7.0, label="Without PE (Baseline)", zorder=3)
ax2.plot(x, pe_sec, color=TEAL_SLATE, linewidth=2.7, marker="o", markersize=7.5, label="With PE (+ PromptEnhancer)", zorder=5)
ax2.fill_between(x, base_sec, pe_sec, color=TEAL_SLATE, alpha=0.07, zorder=2)

ax2.set_xticks(x)
ax2.set_xticklabels(models, fontsize=9.2, fontweight="bold")
ax2.set_ylim(0, 1320)
ax2.set_yticks([0, 300, 600, 900, 1200])
ax2.set_xlim(-0.35, 1.35)
ax2.set_title("Mean Wall-Clock Time per Task (Seconds)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="lower", side="left", offset=0.14, text_gap=0.032, color=TEAL_SLATE)

for i in range(len(x)):
    sec_sav = (1.0 - pe_sec[i] / base_sec[i]) * 100.0
    ax2.annotate(f"{base_sec[i]:.0f}s", (x[i], base_sec[i]), textcoords="offset points", xytext=(0, 8),
                 ha="center", va="bottom", fontsize=8.3, color=TEXT_MUTED)
    ax2.annotate(f"{pe_sec[i]:.0f}s (-{sec_sav:.1f}%)", (x[i], pe_sec[i]), textcoords="offset points", xytext=(0, -16),
                 ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="upper left", ncol=1, fontsize=8.0)

fig.suptitle("Qwen 3.8 27B vs. Qwen 4 27B: Token & Wall-Clock Savings (With vs. Without PE)",
             x=0.04, y=0.95, ha="left", fontsize=12.6, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "chart2_qwen4_token_wallclock_savings.png"))
plt.savefig(os.path.join(OUT_DIR, "qwen38_vs_qwen4_chart2.png"))
plt.close(fig)


# ==============================================================================
# CHART 3: Per-Task Token & Wall-Clock Savings (Without PE vs. With PE)
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.9), gridspec_kw={"width_ratios": [1, 1], "wspace": 0.34})

tasks_tok = ["log-summary", "cancel-async", "db-wal-rec.", "polyglot-c-py"]
t_base_tok = [38223, 64958, 132426, 235226]
t_pe_tok = [16061, 21492, 21400, 17868]
xt = np.arange(len(tasks_tok))

style_line_ax(ax1)
ax1.plot(xt, t_base_tok, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=6.8, label="Without PE (Baseline)", zorder=3)
ax1.plot(xt, t_pe_tok, color=NAVY, linewidth=2.6, marker="o", markersize=7.2, label="With PE (+ PromptEnhancer)", zorder=5)
ax1.fill_between(xt, t_base_tok, t_pe_tok, color=NAVY, alpha=0.07, zorder=2)

ax1.set_xticks(xt)
ax1.set_xticklabels(tasks_tok, fontsize=8.3)
ax1.set_ylim(-22000, 280000)
ax1.set_yticks([0, 50000, 100000, 150000, 200000, 250000])
ax1.set_yticklabels(["0", "50k", "100k", "150k", "200k", "250k"])
ax1.set_xlim(-0.4, 3.4)
ax1.set_title("Per-Task Tokens (Without vs. With PE)", loc="left", fontsize=10.0, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="lower", side="left", offset=0.14, text_gap=0.032, color=NAVY)

tok_b_xy = [(-4, 8), (-8, 8), (-10, 8), (0, 8)]
for i in range(len(xt)):
    ax1.annotate(f"{t_base_tok[i]:,}", (xt[i], t_base_tok[i]), textcoords="offset points", xytext=tok_b_xy[i],
                 ha="center", va="bottom", fontsize=7.9, color=TEXT_MUTED)
    ax1.annotate(f"{t_pe_tok[i]:,}", (xt[i], t_pe_tok[i]), textcoords="offset points", xytext=(0, -15),
                 ha="center", va="bottom", fontsize=8.0, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.9)

# Right Panel: Per-Task Wall-Clock Seconds
tasks_sec = ["openssl-cert", "log-summary", "cancel-async", "db-wal-rec."]
t_base_sec = [470.6, 561.6, 887.5, 1257.1]
t_pe_sec = [61.0, 67.5, 95.4, 72.6]
xs = np.arange(len(tasks_sec))

style_line_ax(ax2)
ax2.plot(xs, t_base_sec, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=6.8, label="Without PE (Baseline)", zorder=3)
ax2.plot(xs, t_pe_sec, color=TEAL_SLATE, linewidth=2.6, marker="o", markersize=7.2, label="With PE (+ PromptEnhancer)", zorder=5)
ax2.fill_between(xs, t_base_sec, t_pe_sec, color=TEAL_SLATE, alpha=0.07, zorder=2)

ax2.set_xticks(xs)
ax2.set_xticklabels(tasks_sec, fontsize=8.3)
ax2.set_ylim(-120, 1500)
ax2.set_yticks([0, 300, 600, 900, 1200, 1500])
ax2.set_xlim(-0.4, 3.4)
ax2.set_title("Per-Task Wall-Clock Time (Seconds)", loc="left", fontsize=10.0, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="lower", side="left", offset=0.14, text_gap=0.032, color=TEAL_SLATE)

sec_b_xy = [(-4, 8), (-8, 8), (-8, 8), (0, 8)]
for i in range(len(xs)):
    ax2.annotate(f"{t_base_sec[i]:.0f}s", (xs[i], t_base_sec[i]), textcoords="offset points", xytext=sec_b_xy[i],
                 ha="center", va="bottom", fontsize=7.9, color=TEXT_MUTED)
    ax2.annotate(f"{t_pe_sec[i]:.0f}s", (xs[i], t_pe_sec[i]), textcoords="offset points", xytext=(0, -15),
                 ha="center", va="bottom", fontsize=8.0, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.9)

fig.suptitle("Task-Level Breakdown: Token & Wall-Clock Time Reductions with PromptEnhancer",
             x=0.04, y=0.95, ha="left", fontsize=12.6, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "chart3_pe_turn_trajectory.png"))
plt.savefig(os.path.join(OUT_DIR, "qwen38_vs_qwen4_chart3.png"))
plt.close(fig)

print(f"Generated 3 charts in {OUT_DIR}")
