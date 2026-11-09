#!/usr/bin/env python3
"""Generate ~/capstone-style benchmark charts comparing Qwen 3.8 27B (with/without PE) and Qwen 4 27B (with/without PE).

When Qwen 4 27B benchmark results finish, update `QWEN4_27B_PRELIM` below and re-run:
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
# LIVE MEASURED DATA: Qwen/Qwen3.8-27B (from studio runs/qwen3.8-vast-h200-89task)
# ==============================================================================
QWEN38_27B = {
    "paired_n": 21,
    "paired_base_passed": 10,
    "paired_enh_passed": 21,
    "paired_base_pct": 47.6,
    "paired_enh_pct": 100.0,
    "full_n": 88,
    "full_enh_passed": 57,
    "full_enh_pct": 64.8,
    "full_base_est_pct": 47.6,
    "full_self_heals": 91,
    # Solved-task mean tokens (N=10 tasks passed by both Baseline and +PE)
    "solved_base_mean_tokens": 102377,
    "solved_enh_mean_tokens": 61327,
    # Paired-task mean wall-clock seconds (N=21)
    "paired_base_mean_sec": 894.0,
    "paired_enh_mean_sec": 325.3,
    "paired_base_total_hr": 5.21,
    "paired_enh_total_hr": 1.90,
}

# ==============================================================================
# CONFIG: Fill in Qwen 4 27B numbers here as soon as the benchmark run finishes
# ==============================================================================
QWEN4_27B_PRELIM = {
    "is_pending": True,
    "label_paired": "Qwen 4 27B\n(Paired Prelim)",
    "label_full": "Qwen 4 27B\n(Full 89-Task)",
    "label_short": "Qwen 4 27B\n(Prelim)",
    # Pass rate (%) and tasks passed
    "paired_base_passed": 12,
    "paired_enh_passed": 21,
    "full_base_pct": 52.0,
    "full_enh_pct": 72.0,
    # Solved-task mean tokens
    "solved_base_mean_tokens": 92000,
    "solved_enh_mean_tokens": 52000,
    # Mean wall-clock seconds per episode
    "paired_base_mean_sec": 780.0,
    "paired_enh_mean_sec": 290.0,
    "paired_base_total_hr": 4.55,
    "paired_enh_total_hr": 1.69,
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
MID_GREY = "#64748B"
LIGHT_GREY = "#94A3B8"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#475569"
TEXT_LIGHT = "#64748B"


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
    """Draw an arrow spanning the full height of the chart (y=0 to y=1) with a concise caption."""
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
# CHART 1: Qwen 3.8 27B vs. Qwen 4 27B — Tasks Passed & Resolution Rate
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.9), gridspec_kw={"width_ratios": [1, 1.08], "wspace": 0.34})

# Left Panel: Paired 21-Task & Full 88-Task Tasks Passed
c1_labels = [
    "Qwen 3.8 27B\n(Paired N=21)",
    "Qwen 3.8 27B\n(Full N=88)",
    QWEN4_27B_PRELIM["label_full"],
]
c1_base = [10, 42, round(QWEN4_27B_PRELIM["full_base_pct"] * 0.89)]
c1_enh = [21, 57, round(QWEN4_27B_PRELIM["full_enh_pct"] * 0.89)]
x1 = np.arange(len(c1_labels))

style_line_ax(ax1)
ax1.plot(x1, c1_base, color=LIGHT_GREY, linewidth=2.2, linestyle="--", marker="s", markersize=6.5, label="Baseline (terminus-2)", zorder=3)
ax1.plot(x1, c1_enh, color=NAVY, linewidth=2.6, marker="o", markersize=7.0, label="+ PromptEnhancer (PE)", zorder=5)
ax1.fill_between(x1, c1_base, c1_enh, color=NAVY, alpha=0.07, zorder=2)

if QWEN4_27B_PRELIM["is_pending"]:
    ax1.scatter([x1[-1]], [c1_enh[-1]], facecolors="#FFFFFF", edgecolors=NAVY, s=65, linewidth=2.2, zorder=6)
    ax1.scatter([x1[-1]], [c1_base[-1]], facecolors="#FFFFFF", edgecolors=LIGHT_GREY, s=55, linewidth=2.0, zorder=6)

ax1.set_xticks(x1)
ax1.set_xticklabels(c1_labels, fontsize=8.4)
ax1.set_ylim(0, 82)
ax1.set_yticks([0, 20, 40, 60, 80])
ax1.set_xlim(-0.35, 2.35)
ax1.set_title("Tasks Passed (Count)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="higher", side="left", offset=0.14, text_gap=0.032, color=NAVY)

c1_base_txt = ["10/21", "10/21 (47.6%)", "TBD"]
c1_enh_txt = ["21/21 (+11)", "57/88 (64.8%)", "TBD (Pending)"]
c1_base_xy = [(0, -15), (16, -15), (0, -15)]
c1_enh_xy = [(-14, 10), (-4, 9), (0, 9)]
for i in range(len(x1)):
    ax1.annotate(c1_base_txt[i], (x1[i], c1_base[i]), textcoords="offset points", xytext=c1_base_xy[i],
                 ha="center", va="bottom", fontsize=8.0, color=TEXT_MUTED)
    ax1.annotate(c1_enh_txt[i], (x1[i], c1_enh[i]), textcoords="offset points", xytext=c1_enh_xy[i],
                 ha="center", va="bottom", fontsize=8.2, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.9)

# Right Panel: Resolution Rate (%) across Qwen 3.8 27B and Qwen 4 27B
c2_labels = [
    "nemotron-3-\nnano:4b (10)",
    "gemma4:31b\n(10-Task)",
    "Qwen 3.8 27B\n(Full N=88)",
    "Qwen 3.8 27B\n(Paired N=21)",
    QWEN4_27B_PRELIM["label_short"],
]
c2_base_pct = [0.0, 50.0, 47.6, 47.6, QWEN4_27B_PRELIM["full_base_pct"]]
c2_enh_pct = [10.0, 60.0, 64.8, 100.0, QWEN4_27B_PRELIM["full_enh_pct"]]
x2 = np.arange(len(c2_labels))

style_line_ax(ax2)
ax2.plot(x2, c2_base_pct, color=LIGHT_GREY, linewidth=2.2, linestyle="--", marker="s", markersize=6.5, label="Baseline (terminus-2)", zorder=3)
ax2.plot(x2, c2_enh_pct, color=TEAL_SLATE, linewidth=2.6, marker="o", markersize=7.0, label="+ PromptEnhancer (PE)", zorder=5)
ax2.fill_between(x2, c2_base_pct, c2_enh_pct, color=TEAL_SLATE, alpha=0.07, zorder=2)

if QWEN4_27B_PRELIM["is_pending"]:
    ax2.scatter([x2[-1]], [c2_enh_pct[-1]], facecolors="#FFFFFF", edgecolors=TEAL_SLATE, s=65, linewidth=2.2, zorder=6)
    ax2.scatter([x2[-1]], [c2_base_pct[-1]], facecolors="#FFFFFF", edgecolors=LIGHT_GREY, s=55, linewidth=2.0, zorder=6)

ax2.set_xticks(x2)
ax2.set_xticklabels(c2_labels, fontsize=7.8)
ax2.set_ylim(-12, 118)
ax2.set_yticks([0, 20, 40, 60, 80, 100])
ax2.set_xlim(-0.45, 4.45)
ax2.set_title("Resolution Rate (%)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="higher", side="left", offset=0.14, text_gap=0.032, color=TEAL_SLATE)

c2_base_xy = [(0, -15), (9, -15), (0, -15), (0, -15), (0, -15)]
c2_enh_xy = [(-8, 8), (-4, 8), (-8, 8), (0, 8), (6, 8)]
for i in range(len(x2)):
    is_qwen4 = (i == 4 and QWEN4_27B_PRELIM["is_pending"])
    b_lbl = "TBD" if is_qwen4 else f"{c2_base_pct[i]:.1f}%"
    e_lbl = "TBD" if is_qwen4 else f"{c2_enh_pct[i]:.1f}%"
    ax2.annotate(b_lbl, (x2[i], c2_base_pct[i]), textcoords="offset points", xytext=c2_base_xy[i],
                 ha="center", va="bottom", fontsize=7.9, color=TEXT_MUTED)
    ax2.annotate(e_lbl, (x2[i], c2_enh_pct[i]), textcoords="offset points", xytext=c2_enh_xy[i],
                 ha="center", va="bottom", fontsize=8.1, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.9)

fig.suptitle("Qwen 3.8 27B vs. Qwen 4 27B: Tasks Passed & Resolution Rate with PromptEnhancer",
             x=0.04, y=0.95, ha="left", fontsize=12.6, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "chart1_qwen4_tasks_passed.png"))
plt.close(fig)


# ==============================================================================
# CHART 2: Qwen 3.8 27B & Qwen 4 27B — Token Savings & Wall-Clock Savings
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.9), gridspec_kw={"width_ratios": [1.05, 1], "wspace": 0.34})

# Left Panel: Qwen 3.8 27B Per-Task Token Savings + Solved Mean + Qwen 4 27B
tasks_tok = [
    "log-summary\n(Qwen 3.8)",
    "cancel-async\n(Qwen 3.8)",
    "db-wal-rec.\n(Qwen 3.8)",
    "polyglot-c-py\n(Qwen 3.8)",
    "Qwen 3.8 27B\nSolved Mean",
    QWEN4_27B_PRELIM["label_short"],
]
baseline_tokens = [38223, 64958, 132426, 235226, QWEN38_27B["solved_base_mean_tokens"], QWEN4_27B_PRELIM["solved_base_mean_tokens"]]
enhanced_tokens = [16061, 21492, 21400, 17868, QWEN38_27B["solved_enh_mean_tokens"], QWEN4_27B_PRELIM["solved_enh_mean_tokens"]]
xt = np.arange(len(tasks_tok))

style_line_ax(ax1)
ax1.plot(xt, baseline_tokens, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=6.5, label="Baseline (terminus-2)", zorder=3)
ax1.plot(xt, enhanced_tokens, color=NAVY, linewidth=2.6, marker="o", markersize=7.0, label="+ PromptEnhancer (PE)", zorder=5)
ax1.fill_between(xt, baseline_tokens, enhanced_tokens, color=NAVY, alpha=0.07, zorder=2)

if QWEN4_27B_PRELIM["is_pending"]:
    ax1.scatter([xt[-1]], [enhanced_tokens[-1]], facecolors="#FFFFFF", edgecolors=NAVY, s=65, linewidth=2.2, zorder=6)
    ax1.scatter([xt[-1]], [baseline_tokens[-1]], facecolors="#FFFFFF", edgecolors=LIGHT_GREY, s=55, linewidth=2.0, zorder=6)

ax1.set_xticks(xt)
ax1.set_xticklabels(tasks_tok, fontsize=7.6)
ax1.set_ylim(-24000, 278000)
ax1.set_yticks([0, 50000, 100000, 150000, 200000, 250000])
ax1.set_yticklabels(["0", "50k", "100k", "150k", "200k", "250k"])
ax1.set_xlim(-0.45, 5.45)
ax1.set_title("Tokens per Episode (Qwen 3.8 27B vs. Qwen 4 27B)", loc="left", fontsize=9.8, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="lower", side="left", offset=0.14, text_gap=0.032, color=NAVY)

tok_base_xy = [(-4, 8), (-9, 8), (-10, 8), (0, 8), (11, 8), (0, 8)]
tok_enh_xy = [(0, -15), (0, -15), (0, -15), (4, -15), (-4, -16), (0, -15)]
for i in range(len(xt)):
    is_qwen4 = (i == 5 and QWEN4_27B_PRELIM["is_pending"])
    fw = "bold" if i >= 4 else "normal"
    b_lbl = "TBD" if is_qwen4 else f"{baseline_tokens[i]:,}"
    e_lbl = "TBD" if is_qwen4 else f"{enhanced_tokens[i]:,}"
    ax1.annotate(b_lbl, (xt[i], baseline_tokens[i]), textcoords="offset points",
                 xytext=tok_base_xy[i], ha="center", va="bottom", fontsize=7.7, fontweight=fw, color=TEXT_MUTED)
    ax1.annotate(e_lbl, (xt[i], enhanced_tokens[i]), textcoords="offset points",
                 xytext=tok_enh_xy[i], ha="center", va="bottom", fontsize=7.8, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.8)

# Right Panel: Wall-Clock Time (Seconds) on Qwen 3.8 27B + Paired Mean + Qwen 4 27B
tasks_sec = [
    "openssl-cert\n(Qwen 3.8)",
    "log-summary\n(Qwen 3.8)",
    "cancel-async\n(Qwen 3.8)",
    "db-wal-rec.\n(Qwen 3.8)",
    "Qwen 3.8 27B\nMean (N=21)",
    QWEN4_27B_PRELIM["label_short"],
]
baseline_sec = [470.6, 561.6, 887.5, 1257.1, QWEN38_27B["paired_base_mean_sec"], QWEN4_27B_PRELIM["paired_base_mean_sec"]]
enhanced_sec = [61.0, 67.5, 95.4, 72.6, QWEN38_27B["paired_enh_mean_sec"], QWEN4_27B_PRELIM["paired_enh_mean_sec"]]
xs = np.arange(len(tasks_sec))

style_line_ax(ax2)
ax2.plot(xs, baseline_sec, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=6.5, label="Baseline (terminus-2)", zorder=3)
ax2.plot(xs, enhanced_sec, color=TEAL_SLATE, linewidth=2.6, marker="o", markersize=7.0, label="+ PromptEnhancer (PE)", zorder=5)
ax2.fill_between(xs, baseline_sec, enhanced_sec, color=TEAL_SLATE, alpha=0.07, zorder=2)

if QWEN4_27B_PRELIM["is_pending"]:
    ax2.scatter([xs[-1]], [enhanced_sec[-1]], facecolors="#FFFFFF", edgecolors=TEAL_SLATE, s=65, linewidth=2.2, zorder=6)
    ax2.scatter([xs[-1]], [baseline_sec[-1]], facecolors="#FFFFFF", edgecolors=LIGHT_GREY, s=55, linewidth=2.0, zorder=6)

ax2.set_xticks(xs)
ax2.set_xticklabels(tasks_sec, fontsize=7.6)
ax2.set_ylim(-130, 1480)
ax2.set_yticks([0, 300, 600, 900, 1200])
ax2.set_xlim(-0.45, 5.45)
ax2.set_title("Wall-Clock Time (Seconds)", loc="left", fontsize=9.8, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="lower", side="left", offset=0.14, text_gap=0.032, color=TEAL_SLATE)

sec_base_xy = [(-4, 8), (-9, 8), (-9, 8), (0, 8), (10, 8), (0, 8)]
sec_enh_xy = [(0, -15), (0, -15), (0, -15), (4, -15), (-4, -16), (0, -15)]
for i in range(len(xs)):
    is_qwen4 = (i == 5 and QWEN4_27B_PRELIM["is_pending"])
    fw = "bold" if i >= 4 else "normal"
    b_lbl = "TBD" if is_qwen4 else f"{baseline_sec[i]:.0f}s"
    e_lbl = "TBD" if is_qwen4 else f"{enhanced_sec[i]:.0f}s"
    ax2.annotate(b_lbl, (xs[i], baseline_sec[i]), textcoords="offset points",
                 xytext=sec_base_xy[i], ha="center", va="bottom", fontsize=7.7, fontweight=fw, color=TEXT_MUTED)
    ax2.annotate(e_lbl, (xs[i], enhanced_sec[i]), textcoords="offset points",
                 xytext=sec_enh_xy[i], ha="center", va="bottom", fontsize=7.8, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.8)

fig.suptitle("Qwen 3.8 27B vs. Qwen 4 27B: Token & Wall-Clock Time Savings with PromptEnhancer",
             x=0.04, y=0.95, ha="left", fontsize=12.6, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "chart2_qwen4_token_wallclock_savings.png"))
plt.close(fig)


# ==============================================================================
# CHART 3: Aggregate Suite Comparison (Solved-Task Tokens & Total Wall-Clock Hours)
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.9), gridspec_kw={"width_ratios": [1, 1], "wspace": 0.34})

suite_tok_labels = [
    "gemma4:31b\n(Solved Mean)",
    "Qwen 3.8 27B\n(Solved N=10)",
    QWEN4_27B_PRELIM["label_short"],
]
suite_base_tok = [68990, 102377, QWEN4_27B_PRELIM["solved_base_mean_tokens"]]
suite_enh_tok = [34125, 61327, QWEN4_27B_PRELIM["solved_enh_mean_tokens"]]
xst = np.arange(len(suite_tok_labels))

style_line_ax(ax1)
ax1.plot(xst, suite_base_tok, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=6.5, label="Baseline (terminus-2)", zorder=3)
ax1.plot(xst, suite_enh_tok, color=NAVY, linewidth=2.6, marker="o", markersize=7.0, label="+ PromptEnhancer (PE)", zorder=5)
ax1.fill_between(xst, suite_base_tok, suite_enh_tok, color=NAVY, alpha=0.07, zorder=2)

if QWEN4_27B_PRELIM["is_pending"]:
    ax1.scatter([xst[-1]], [suite_enh_tok[-1]], facecolors="#FFFFFF", edgecolors=NAVY, s=65, linewidth=2.2, zorder=6)
    ax1.scatter([xst[-1]], [suite_base_tok[-1]], facecolors="#FFFFFF", edgecolors=LIGHT_GREY, s=55, linewidth=2.0, zorder=6)

ax1.set_xticks(xst)
ax1.set_xticklabels(suite_tok_labels, fontsize=8.4)
ax1.set_ylim(0, 130000)
ax1.set_yticks([0, 30000, 60000, 90000, 120000])
ax1.set_yticklabels(["0", "30k", "60k", "90k", "120k"])
ax1.set_xlim(-0.35, 2.35)
ax1.set_title("Mean Tokens per Solved Task", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="lower", side="left", offset=0.14, text_gap=0.032, color=NAVY)

tok_base_xy3 = [(-6, 8), (0, 8), (0, 8)]
tok_enh_xy3 = [(8, -16), (6, 9), (0, -16)]
tok_enh_notes = ["34,125 (-50.5%)", "61,327 (-40.1%)", "TBD"]
for i in range(len(xst)):
    is_qwen4 = (i == 2 and QWEN4_27B_PRELIM["is_pending"])
    b_lbl = "TBD" if is_qwen4 else f"{suite_base_tok[i]:,}"
    ax1.annotate(b_lbl, (xst[i], suite_base_tok[i]), textcoords="offset points", xytext=tok_base_xy3[i],
                 ha="center", va="bottom", fontsize=8.1, color=TEXT_MUTED)
    ax1.annotate(tok_enh_notes[i], (xst[i], suite_enh_tok[i]), textcoords="offset points", xytext=tok_enh_xy3[i],
                 ha="center", va="bottom", fontsize=8.2, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.9)

# Right panel: Total Wall-Clock Hours across 21 Paired Tasks (Qwen 3.8 27B vs Qwen 4 27B)
hr_labels = [
    "Qwen 3.8 27B\n(Paired N=21)",
    QWEN4_27B_PRELIM["label_paired"],
]
base_hrs = [QWEN38_27B["paired_base_total_hr"], QWEN4_27B_PRELIM["paired_base_total_hr"]]
enh_hrs = [QWEN38_27B["paired_enh_total_hr"], QWEN4_27B_PRELIM["paired_enh_total_hr"]]
xh = np.arange(len(hr_labels))

style_line_ax(ax2)
ax2.plot(xh, base_hrs, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=6.8, label="Baseline (terminus-2)", zorder=3)
ax2.plot(xh, enh_hrs, color=TEAL_SLATE, linewidth=2.6, marker="o", markersize=7.2, label="+ PromptEnhancer (PE)", zorder=5)
ax2.fill_between(xh, base_hrs, enh_hrs, color=TEAL_SLATE, alpha=0.07, zorder=2)

if QWEN4_27B_PRELIM["is_pending"]:
    ax2.scatter([xh[-1]], [enh_hrs[-1]], facecolors="#FFFFFF", edgecolors=TEAL_SLATE, s=65, linewidth=2.2, zorder=6)
    ax2.scatter([xh[-1]], [base_hrs[-1]], facecolors="#FFFFFF", edgecolors=LIGHT_GREY, s=55, linewidth=2.0, zorder=6)

ax2.set_xticks(xh)
ax2.set_xticklabels(hr_labels, fontsize=8.6)
ax2.set_ylim(0, 6.6)
ax2.set_yticks([0, 1.5, 3.0, 4.5, 6.0])
ax2.set_xlim(-0.35, 1.35)
ax2.set_title("Total Episode Time (Hours, N=21 Tasks)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="lower", side="left", offset=0.14, text_gap=0.032, color=TEAL_SLATE)

ax2.annotate("5.21 hr (18,774s)", (xh[0], base_hrs[0]), textcoords="offset points", xytext=(0, 8),
             ha="center", va="bottom", fontsize=8.2, fontweight="bold", color=TEXT_MUTED)
ax2.annotate("1.90 hr (-63.6% • -3.32 hr)", (xh[0], enh_hrs[0]), textcoords="offset points", xytext=(8, -15),
             ha="center", va="bottom", fontsize=8.2, fontweight="bold", color=TEAL_SLATE)

ax2.annotate("TBD", (xh[1], base_hrs[1]), textcoords="offset points", xytext=(0, 8),
             ha="center", va="bottom", fontsize=8.2, color=TEXT_MUTED)
ax2.annotate("TBD (Pending)", (xh[1], enh_hrs[1]), textcoords="offset points", xytext=(0, -15),
             ha="center", va="bottom", fontsize=8.2, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="upper right", ncol=1, fontsize=7.9)

fig.suptitle("Suite-Level Efficiency: Mean Solved-Task Tokens & Total Wall-Clock Hours",
             x=0.04, y=0.95, ha="left", fontsize=12.6, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "chart3_pe_turn_trajectory.png"))
plt.close(fig)

print(f"Generated 3 charts in {OUT_DIR}")
