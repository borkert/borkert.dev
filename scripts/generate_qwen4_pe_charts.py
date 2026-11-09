#!/usr/bin/env python3
"""Generate ~/capstone-style benchmark charts for Qwen 3.8 27B and Qwen 4 27B (with and without PE).

Update the numbers in `BENCH_DATA` below after running tests and re-run:
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
# BENCHMARK NUMBERS (Swap these out after tests finish)
# ==============================================================================
BENCH_DATA = {
    # Pass rate (%) with and without PromptEnhancer (PE)
    "qwen38_tb21_paired_base_pct": 47.6,   # 10 / 21
    "qwen38_tb21_paired_pe_pct": 100.0,    # 21 / 21
    "qwen38_tb21_full_base_pct": 47.6,     # baseline rate
    "qwen38_tb21_full_pe_pct": 64.8,       # 57 / 88

    # Terminal-Bench 2.1 (Qwen 4 27B): without PE 50%, with PE 75%
    "qwen4_tb21_base_pct": 50.0,
    "qwen4_tb21_pe_pct": 75.0,

    # Terminal-Bench 4.0 (Qwen 4 27B): without PE 15%, with PE 35%
    "qwen4_tb40_base_pct": 15.0,
    "qwen4_tb40_pe_pct": 35.0,

    # Tasks passed counts (out of 89 for full suites, 21 for paired)
    "qwen38_paired_base_cnt": 10,
    "qwen38_paired_pe_cnt": 21,
    "qwen38_full_base_cnt": 42,
    "qwen38_full_pe_cnt": 57,
    "qwen4_tb21_base_cnt": 45,   # 50% of 89
    "qwen4_tb21_pe_cnt": 67,     # 75% of 89
    "qwen4_tb40_base_cnt": 13,   # 15% of 89
    "qwen4_tb40_pe_cnt": 31,     # 35% of 89

    # Mean tokens per solved task
    "qwen38_solved_base_tokens": 102377,
    "qwen38_solved_pe_tokens": 61327,
    "qwen4_tb21_base_tokens": 88000,
    "qwen4_tb21_pe_tokens": 51000,
    "qwen4_tb40_base_tokens": 118000,
    "qwen4_tb40_pe_tokens": 69000,

    # Mean wall-clock seconds per task
    "qwen38_base_sec": 894.0,
    "qwen38_pe_sec": 325.3,
    "qwen4_tb21_base_sec": 740.0,
    "qwen4_tb21_pe_sec": 280.0,
    "qwen4_tb40_base_sec": 960.0,
    "qwen4_tb40_pe_sec": 390.0,

    # Total episode hours (21-task paired comparison)
    "qwen38_base_hr": 5.21,
    "qwen38_pe_hr": 1.90,
    "qwen4_tb21_base_hr": 4.32,
    "qwen4_tb21_pe_hr": 1.63,
    "qwen4_tb40_base_hr": 5.60,
    "qwen4_tb40_pe_hr": 2.28,
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


def add_spanning_arrow(ax, direction="higher", side="left", offset=0.13, text_gap=0.032, label=None, color=TEXT_MUTED):
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
# CHART 1: Terminal-Bench 2.1 & 4.0 — Resolution Rate (%) and Tasks Passed
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.9), gridspec_kw={"width_ratios": [1, 1], "wspace": 0.34})

# Left Panel: Resolution Rate (%) across Qwen 3.8 27B and Qwen 4 27B (TB 2.1 & TB 4.0)
c1_labels = [
    "Qwen 3.8 27B\nTB 2.1 (N=88)",
    "Qwen 3.8 27B\nTB 2.1 (N=21)",
    "Qwen 4 27B\nTB 2.1",
    "Qwen 4 27B\nTB 4.0",
]
c1_base_pct = [
    BENCH_DATA["qwen38_tb21_full_base_pct"],
    BENCH_DATA["qwen38_tb21_paired_base_pct"],
    BENCH_DATA["qwen4_tb21_base_pct"],
    BENCH_DATA["qwen4_tb40_base_pct"],
]
c1_pe_pct = [
    BENCH_DATA["qwen38_tb21_full_pe_pct"],
    BENCH_DATA["qwen38_tb21_paired_pe_pct"],
    BENCH_DATA["qwen4_tb21_pe_pct"],
    BENCH_DATA["qwen4_tb40_pe_pct"],
]
x1 = np.arange(len(c1_labels))

style_line_ax(ax1)
ax1.plot(x1, c1_base_pct, color=LIGHT_GREY, linewidth=2.2, linestyle="--", marker="s", markersize=6.5, label="Without PE (Baseline)", zorder=3)
ax1.plot(x1, c1_pe_pct, color=NAVY, linewidth=2.6, marker="o", markersize=7.0, label="With PE (+ PromptEnhancer)", zorder=5)
ax1.fill_between(x1, c1_base_pct, c1_pe_pct, color=NAVY, alpha=0.07, zorder=2)

ax1.set_xticks(x1)
ax1.set_xticklabels(c1_labels, fontsize=8.1)
ax1.set_ylim(-5, 122)
ax1.set_yticks([0, 25, 50, 75, 100])
ax1.set_xlim(-0.4, 3.4)
ax1.set_title("Resolution Rate (%)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="higher", side="left", offset=0.14, text_gap=0.032, color=NAVY)

c1_base_xy = [(0, -15), (0, -15), (-8, -15), (0, -15)]
c1_pe_xy = [(-8, 8), (0, 7), (10, 7), (8, 8)]
for i in range(len(x1)):
    ax1.annotate(f"{c1_base_pct[i]:.1f}%", (x1[i], c1_base_pct[i]), textcoords="offset points", xytext=c1_base_xy[i],
                 ha="center", va="bottom", fontsize=8.0, color=TEXT_MUTED)
    ax1.annotate(f"{c1_pe_pct[i]:.1f}%", (x1[i], c1_pe_pct[i]), textcoords="offset points", xytext=c1_pe_xy[i],
                 ha="center", va="bottom", fontsize=8.2, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper right", ncol=1, fontsize=7.8)

# Right Panel: Tasks Passed (Count)
c2_labels = [
    "Qwen 3.8 27B\nTB 2.1 (N=21)",
    "Qwen 3.8 27B\nTB 2.1 (N=88)",
    "Qwen 4 27B\nTB 2.1 (N=89)",
    "Qwen 4 27B\nTB 4.0 (N=89)",
]
c2_base_cnt = [
    BENCH_DATA["qwen38_paired_base_cnt"],
    BENCH_DATA["qwen38_full_base_cnt"],
    BENCH_DATA["qwen4_tb21_base_cnt"],
    BENCH_DATA["qwen4_tb40_base_cnt"],
]
c2_pe_cnt = [
    BENCH_DATA["qwen38_paired_pe_cnt"],
    BENCH_DATA["qwen38_full_pe_cnt"],
    BENCH_DATA["qwen4_tb21_pe_cnt"],
    BENCH_DATA["qwen4_tb40_pe_cnt"],
]
x2 = np.arange(len(c2_labels))

style_line_ax(ax2)
ax2.plot(x2, c2_base_cnt, color=LIGHT_GREY, linewidth=2.2, linestyle="--", marker="s", markersize=6.5, label="Without PE (Baseline)", zorder=3)
ax2.plot(x2, c2_pe_cnt, color=TEAL_SLATE, linewidth=2.6, marker="o", markersize=7.0, label="With PE (+ PromptEnhancer)", zorder=5)
ax2.fill_between(x2, c2_base_cnt, c2_pe_cnt, color=TEAL_SLATE, alpha=0.07, zorder=2)

ax2.set_xticks(x2)
ax2.set_xticklabels(c2_labels, fontsize=8.1)
ax2.set_ylim(-4, 88)
ax2.set_yticks([0, 20, 40, 60, 80])
ax2.set_xlim(-0.45, 3.45)
ax2.set_title("Tasks Passed (Count)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="higher", side="left", offset=0.14, text_gap=0.032, color=TEAL_SLATE)

c2_base_txt = ["10/21", "42/88", "45/89 (50%)", "13/89 (15%)"]
c2_pe_txt = ["21/21", "57/88 (+15)", "67/89 (75%)", "31/89 (35%)"]
c2_base_xy = [(0, -15), (10, -15), (-14, -15), (0, -15)]
c2_pe_xy = [(-12, 8), (-8, 8), (0, 8), (14, 10)]
for i in range(len(x2)):
    ax2.annotate(c2_base_txt[i], (x2[i], c2_base_cnt[i]), textcoords="offset points", xytext=c2_base_xy[i],
                 ha="center", va="bottom", fontsize=7.9, color=TEXT_MUTED)
    ax2.annotate(c2_pe_txt[i], (x2[i], c2_pe_cnt[i]), textcoords="offset points", xytext=c2_pe_xy[i],
                 ha="center", va="bottom", fontsize=8.1, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.8)

fig.suptitle("Terminal-Bench 2.1 & 4.0: Resolution Rate & Tasks Passed (With vs. Without PE)",
             x=0.04, y=0.95, ha="left", fontsize=12.6, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "chart1_qwen4_tasks_passed.png"))
plt.close(fig)


# ==============================================================================
# CHART 2: Per-Task & Suite Token Savings and Wall-Clock Savings
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.9), gridspec_kw={"width_ratios": [1.05, 1], "wspace": 0.34})

tasks_tok = [
    "cancel-async\n(Qwen 3.8)",
    "db-wal-rec.\n(Qwen 3.8)",
    "polyglot-c-py\n(Qwen 3.8)",
    "Qwen 3.8 27B\nTB 2.1 Mean",
    "Qwen 4 27B\nTB 2.1 Mean",
    "Qwen 4 27B\nTB 4.0 Mean",
]
baseline_tokens = [
    64958,
    132426,
    235226,
    BENCH_DATA["qwen38_solved_base_tokens"],
    BENCH_DATA["qwen4_tb21_base_tokens"],
    BENCH_DATA["qwen4_tb40_base_tokens"],
]
enhanced_tokens = [
    21492,
    21400,
    17868,
    BENCH_DATA["qwen38_solved_pe_tokens"],
    BENCH_DATA["qwen4_tb21_pe_tokens"],
    BENCH_DATA["qwen4_tb40_pe_tokens"],
]
xt = np.arange(len(tasks_tok))

style_line_ax(ax1)
ax1.plot(xt, baseline_tokens, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=6.5, label="Without PE (Baseline)", zorder=3)
ax1.plot(xt, enhanced_tokens, color=NAVY, linewidth=2.6, marker="o", markersize=7.0, label="With PE (+ PromptEnhancer)", zorder=5)
ax1.fill_between(xt, baseline_tokens, enhanced_tokens, color=NAVY, alpha=0.07, zorder=2)

ax1.set_xticks(xt)
ax1.set_xticklabels(tasks_tok, fontsize=7.5)
ax1.set_ylim(-24000, 285000)
ax1.set_yticks([0, 50000, 100000, 150000, 200000, 250000])
ax1.set_yticklabels(["0", "50k", "100k", "150k", "200k", "250k"])
ax1.set_xlim(-0.45, 5.45)
ax1.set_title("Tokens per Episode", loc="left", fontsize=10.0, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="lower", side="left", offset=0.14, text_gap=0.032, color=NAVY)

tok_base_xy = [(-6, 8), (-10, 8), (0, 8), (10, 8), (0, 8), (0, 8)]
tok_enh_xy = [(0, -15), (0, -15), (4, -15), (-4, -16), (0, -15), (0, -15)]
for i in range(len(xt)):
    fw = "bold" if i >= 3 else "normal"
    ax1.annotate(f"{baseline_tokens[i]:,}", (xt[i], baseline_tokens[i]), textcoords="offset points",
                 xytext=tok_base_xy[i], ha="center", va="bottom", fontsize=7.6, fontweight=fw, color=TEXT_MUTED)
    ax1.annotate(f"{enhanced_tokens[i]:,}", (xt[i], enhanced_tokens[i]), textcoords="offset points",
                 xytext=tok_enh_xy[i], ha="center", va="bottom", fontsize=7.7, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper right", ncol=1, fontsize=7.8)

# Right Panel: Wall-Clock Time (Seconds)
tasks_sec = [
    "log-summary\n(Qwen 3.8)",
    "cancel-async\n(Qwen 3.8)",
    "db-wal-rec.\n(Qwen 3.8)",
    "Qwen 3.8 27B\nTB 2.1 Mean",
    "Qwen 4 27B\nTB 2.1 Mean",
    "Qwen 4 27B\nTB 4.0 Mean",
]
baseline_sec = [
    561.6,
    887.5,
    1257.1,
    BENCH_DATA["qwen38_base_sec"],
    BENCH_DATA["qwen4_tb21_base_sec"],
    BENCH_DATA["qwen4_tb40_base_sec"],
]
enhanced_sec = [
    67.5,
    95.4,
    72.6,
    BENCH_DATA["qwen38_pe_sec"],
    BENCH_DATA["qwen4_tb21_pe_sec"],
    BENCH_DATA["qwen4_tb40_pe_sec"],
]
xs = np.arange(len(tasks_sec))

style_line_ax(ax2)
ax2.plot(xs, baseline_sec, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=6.5, label="Without PE (Baseline)", zorder=3)
ax2.plot(xs, enhanced_sec, color=TEAL_SLATE, linewidth=2.6, marker="o", markersize=7.0, label="With PE (+ PromptEnhancer)", zorder=5)
ax2.fill_between(xs, baseline_sec, enhanced_sec, color=TEAL_SLATE, alpha=0.07, zorder=2)

ax2.set_xticks(xs)
ax2.set_xticklabels(tasks_sec, fontsize=7.5)
ax2.set_ylim(-130, 1520)
ax2.set_yticks([0, 300, 600, 900, 1200, 1500])
ax2.set_xlim(-0.45, 5.45)
ax2.set_title("Wall-Clock Time (Seconds)", loc="left", fontsize=10.0, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="lower", side="left", offset=0.14, text_gap=0.032, color=TEAL_SLATE)

sec_base_xy = [(-6, 8), (-9, 8), (0, 8), (8, 8), (-6, 8), (0, 8)]
sec_enh_xy = [(0, -15), (0, -15), (4, -15), (-4, -16), (0, -15), (0, -15)]
for i in range(len(xs)):
    fw = "bold" if i >= 3 else "normal"
    ax2.annotate(f"{baseline_sec[i]:.0f}s", (xs[i], baseline_sec[i]), textcoords="offset points",
                 xytext=sec_base_xy[i], ha="center", va="bottom", fontsize=7.6, fontweight=fw, color=TEXT_MUTED)
    ax2.annotate(f"{enhanced_sec[i]:.0f}s", (xs[i], enhanced_sec[i]), textcoords="offset points",
                 xytext=sec_enh_xy[i], ha="center", va="bottom", fontsize=7.7, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="upper right", ncol=1, fontsize=7.8)

fig.suptitle("Token & Wall-Clock Time Savings: Qwen 3.8 27B vs. Qwen 4 27B (TB 2.1 & TB 4.0)",
             x=0.04, y=0.95, ha="left", fontsize=12.6, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "chart2_qwen4_token_wallclock_savings.png"))
plt.close(fig)


# ==============================================================================
# CHART 3: Suite-Level Mean Tokens & Total Wall-Clock Hours
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.9), gridspec_kw={"width_ratios": [1, 1], "wspace": 0.34})

suite_tok_labels = [
    "gemma4:31b\nTB 2.1",
    "Qwen 3.8 27B\nTB 2.1",
    "Qwen 4 27B\nTB 2.1",
    "Qwen 4 27B\nTB 4.0",
]
suite_base_tok = [
    68990,
    BENCH_DATA["qwen38_solved_base_tokens"],
    BENCH_DATA["qwen4_tb21_base_tokens"],
    BENCH_DATA["qwen4_tb40_base_tokens"],
]
suite_enh_tok = [
    34125,
    BENCH_DATA["qwen38_solved_pe_tokens"],
    BENCH_DATA["qwen4_tb21_pe_tokens"],
    BENCH_DATA["qwen4_tb40_pe_tokens"],
]
xst = np.arange(len(suite_tok_labels))

style_line_ax(ax1)
ax1.plot(xst, suite_base_tok, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=6.5, label="Without PE (Baseline)", zorder=3)
ax1.plot(xst, suite_enh_tok, color=NAVY, linewidth=2.6, marker="o", markersize=7.0, label="With PE (+ PromptEnhancer)", zorder=5)
ax1.fill_between(xst, suite_base_tok, suite_enh_tok, color=NAVY, alpha=0.07, zorder=2)

ax1.set_xticks(xst)
ax1.set_xticklabels(suite_tok_labels, fontsize=8.2)
ax1.set_ylim(0, 142000)
ax1.set_yticks([0, 35000, 70000, 105000, 140000])
ax1.set_yticklabels(["0", "35k", "70k", "105k", "140k"])
ax1.set_xlim(-0.4, 3.4)
ax1.set_title("Mean Tokens per Solved Task", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="lower", side="left", offset=0.14, text_gap=0.032, color=NAVY)

tok_base_xy3 = [(-6, 8), (0, 8), (-6, 8), (0, 8)]
tok_enh_xy3 = [(6, -16), (0, 8), (0, -16), (-4, 9)]
tok_enh_notes = ["34,125 (-50.5%)", "61,327 (-40.1%)", "51,000 (-42.0%)", "69,000 (-41.5%)"]
for i in range(len(xst)):
    ax1.annotate(f"{suite_base_tok[i]:,}", (xst[i], suite_base_tok[i]), textcoords="offset points", xytext=tok_base_xy3[i],
                 ha="center", va="bottom", fontsize=7.9, color=TEXT_MUTED)
    ax1.annotate(tok_enh_notes[i], (xst[i], suite_enh_tok[i]), textcoords="offset points", xytext=tok_enh_xy3[i],
                 ha="center", va="bottom", fontsize=8.0, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.9)

# Right panel: Total Wall-Clock Hours (N=21 Paired Benchmark Equivalent)
hr_labels = [
    "Qwen 3.8 27B\nTB 2.1",
    "Qwen 4 27B\nTB 2.1",
    "Qwen 4 27B\nTB 4.0",
]
base_hrs = [
    BENCH_DATA["qwen38_base_hr"],
    BENCH_DATA["qwen4_tb21_base_hr"],
    BENCH_DATA["qwen4_tb40_base_hr"],
]
enh_hrs = [
    BENCH_DATA["qwen38_pe_hr"],
    BENCH_DATA["qwen4_tb21_pe_hr"],
    BENCH_DATA["qwen4_tb40_pe_hr"],
]
xh = np.arange(len(hr_labels))

style_line_ax(ax2)
ax2.plot(xh, base_hrs, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=6.8, label="Without PE (Baseline)", zorder=3)
ax2.plot(xh, enh_hrs, color=TEAL_SLATE, linewidth=2.6, marker="o", markersize=7.2, label="With PE (+ PromptEnhancer)", zorder=5)
ax2.fill_between(xh, base_hrs, enh_hrs, color=TEAL_SLATE, alpha=0.07, zorder=2)

ax2.set_xticks(xh)
ax2.set_xticklabels(hr_labels, fontsize=8.4)
ax2.set_ylim(0, 7.5)
ax2.set_yticks([0, 1.5, 3.0, 4.5, 6.0, 7.5])
ax2.set_xlim(-0.35, 2.35)
ax2.set_title("Total Episode Time (Hours, 21-Task Subset)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="lower", side="left", offset=0.14, text_gap=0.032, color=TEAL_SLATE)

hr_base_txt = ["5.21 hr", "4.32 hr", "5.60 hr"]
hr_enh_txt = ["1.90 hr (-63.6%)", "1.63 hr (-62.3%)", "2.28 hr (-59.3%)"]
hr_base_xy = [(0, 8), (0, 8), (0, 8)]
hr_enh_xy = [(6, -16), (0, -16), (-4, -16)]
for i in range(len(xh)):
    ax2.annotate(hr_base_txt[i], (xh[i], base_hrs[i]), textcoords="offset points", xytext=hr_base_xy[i],
                 ha="center", va="bottom", fontsize=8.1, fontweight="bold", color=TEXT_MUTED)
    ax2.annotate(hr_enh_txt[i], (xh[i], enh_hrs[i]), textcoords="offset points", xytext=hr_enh_xy[i],
                 ha="center", va="bottom", fontsize=8.1, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.9)

fig.suptitle("Suite-Level Efficiency: Mean Solved-Task Tokens & Total Wall-Clock Hours",
             x=0.04, y=0.95, ha="left", fontsize=12.6, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "chart3_pe_turn_trajectory.png"))
plt.close(fig)

print(f"Generated 3 charts in {OUT_DIR}")
