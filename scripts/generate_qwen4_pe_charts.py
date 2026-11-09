#!/usr/bin/env python3
"""Generate ~/capstone-style benchmark charts for the Qwen 4 27B + PromptEnhancer blog post.

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
# CONFIG: Fill in Qwen 4 27B numbers here as soon as the benchmark run finishes
# ==============================================================================
QWEN4_27B_PRELIM = {
    # Set is_pending=False once live Qwen 4 27B benchmark numbers are plugged in
    "is_pending": True,
    "subset_label": "Qwen 4 27B\n(Prelim)",
    # Pass rate (%) on Terminal-Bench 2.1 preliminary evaluation
    "baseline_pass_pct": 60.0,
    "enhanced_pass_pct": 80.0,
    "baseline_tasks_passed": 6,
    "enhanced_tasks_passed": 8,
    "total_tasks_in_subset": 10,
    # Mean tokens per resolved task
    "baseline_mean_tokens": 68400,
    "enhanced_mean_tokens": 33200,
    # Mean wall-clock seconds per resolved task
    "baseline_mean_seconds": 245.0,
    "enhanced_mean_seconds": 122.0,
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
# CHART 1: Tasks Passed & Pass Rate Across Models (Baseline vs. + PromptEnhancer)
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.9), gridspec_kw={"width_ratios": [1, 1], "wspace": 0.34})

models_c1 = [
    "nemotron-3-\nnano:4b",
    "gemma4:31b",
    QWEN4_27B_PRELIM["subset_label"],
]
base_tasks = [0, 5, QWEN4_27B_PRELIM["baseline_tasks_passed"]]
enh_tasks = [1, 6, QWEN4_27B_PRELIM["enhanced_tasks_passed"]]
x1 = np.arange(len(models_c1))

style_line_ax(ax1)
ax1.plot(x1, base_tasks, color=LIGHT_GREY, linewidth=2.2, linestyle="--", marker="s", markersize=6.5, label="Baseline (terminus-2)", zorder=3)
ax1.plot(x1, enh_tasks, color=NAVY, linewidth=2.6, marker="o", markersize=7.0, label="+ PromptEnhancer (PE)", zorder=5)
ax1.fill_between(x1, base_tasks, enh_tasks, color=NAVY, alpha=0.07, zorder=2)

if QWEN4_27B_PRELIM["is_pending"]:
    ax1.scatter([x1[-1]], [enh_tasks[-1]], facecolors="#FFFFFF", edgecolors=NAVY, s=65, linewidth=2.2, zorder=6)
    ax1.scatter([x1[-1]], [base_tasks[-1]], facecolors="#FFFFFF", edgecolors=LIGHT_GREY, s=55, linewidth=2.0, zorder=6)

ax1.set_xticks(x1)
ax1.set_xticklabels(models_c1, fontsize=8.6)
ax1.set_ylim(-1.0, 10.6)
ax1.set_yticks([0, 2, 4, 6, 8, 10])
ax1.set_xlim(-0.35, 2.35)
ax1.set_title("Tasks Passed (10-Task Calibration)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="higher", side="left", offset=0.14, text_gap=0.032, color=NAVY)

for i in range(len(x1)):
    is_qwen_pending = (i == 2 and QWEN4_27B_PRELIM["is_pending"])
    b_lbl = f"TBD ({base_tasks[i]}/10 est.)" if is_qwen_pending else f"{base_tasks[i]}/10"
    e_lbl = f"TBD ({enh_tasks[i]}/10 est.)" if is_qwen_pending else f"{enh_tasks[i]}/10"
    ax1.annotate(b_lbl, (x1[i], base_tasks[i]), textcoords="offset points", xytext=(0, -15),
                 ha="center", va="bottom", fontsize=8.1, color=TEXT_MUTED)
    ax1.annotate(e_lbl, (x1[i], enh_tasks[i]), textcoords="offset points", xytext=(0, 8),
                 ha="center", va="bottom", fontsize=8.4, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper left", ncol=1, fontsize=8.0)

# Right panel: Pass Rate (%)
base_pct = [0.0, 50.0, QWEN4_27B_PRELIM["baseline_pass_pct"]]
enh_pct = [10.0, 60.0, QWEN4_27B_PRELIM["enhanced_pass_pct"]]

style_line_ax(ax2)
ax2.plot(x1, base_pct, color=LIGHT_GREY, linewidth=2.2, linestyle="--", marker="s", markersize=6.5, label="Baseline (terminus-2)", zorder=3)
ax2.plot(x1, enh_pct, color=TEAL_SLATE, linewidth=2.6, marker="o", markersize=7.0, label="+ PromptEnhancer (PE)", zorder=5)
ax2.fill_between(x1, base_pct, enh_pct, color=TEAL_SLATE, alpha=0.07, zorder=2)

if QWEN4_27B_PRELIM["is_pending"]:
    ax2.scatter([x1[-1]], [enh_pct[-1]], facecolors="#FFFFFF", edgecolors=TEAL_SLATE, s=65, linewidth=2.2, zorder=6)
    ax2.scatter([x1[-1]], [base_pct[-1]], facecolors="#FFFFFF", edgecolors=LIGHT_GREY, s=55, linewidth=2.0, zorder=6)

ax2.set_xticks(x1)
ax2.set_xticklabels(models_c1, fontsize=8.6)
ax2.set_ylim(-10, 106)
ax2.set_yticks([0, 20, 40, 60, 80, 100])
ax2.set_xlim(-0.35, 2.35)
ax2.set_title("Resolution Rate (%)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="higher", side="left", offset=0.14, text_gap=0.032, color=TEAL_SLATE)

for i in range(len(x1)):
    is_qwen_pending = (i == 2 and QWEN4_27B_PRELIM["is_pending"])
    b_lbl = f"TBD (~{base_pct[i]:.0f}%)" if is_qwen_pending else f"{base_pct[i]:.0f}%"
    e_lbl = f"TBD (~{enh_pct[i]:.0f}%)" if is_qwen_pending else f"{enh_pct[i]:.0f}%"
    ax2.annotate(b_lbl, (x1[i], base_pct[i]), textcoords="offset points", xytext=(0, -15),
                 ha="center", va="bottom", fontsize=8.1, color=TEXT_MUTED)
    ax2.annotate(e_lbl, (x1[i], enh_pct[i]), textcoords="offset points", xytext=(0, 8),
                 ha="center", va="bottom", fontsize=8.4, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="upper left", ncol=1, fontsize=8.0)

fig.suptitle("Terminal-Bench 2.1 Preliminary Benchmark: Tasks Passed & Resolution Rate",
             x=0.04, y=0.95, ha="left", fontsize=12.8, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "chart1_qwen4_tasks_passed.png"))
plt.close(fig)


# ==============================================================================
# CHART 2: Token Savings & Wall-Clock Time Savings (Ordered Low -> High like ~/capstone Chart 7)
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.9), gridspec_kw={"width_ratios": [1.05, 1], "wspace": 0.34})

tasks_tok = [
    "cancel-async-\ntasks",
    "git-leak-\nrecovery",
    "db-wal-\nrecovery",
    "nginx-request-\nlogging",
    QWEN4_27B_PRELIM["subset_label"],
]
baseline_tokens = [5276, 53532, 73336, 80102, QWEN4_27B_PRELIM["baseline_mean_tokens"]]
enhanced_tokens = [3568, 18988, 32779, 50608, QWEN4_27B_PRELIM["enhanced_mean_tokens"]]
xt = np.arange(len(tasks_tok))

style_line_ax(ax1)
ax1.plot(xt, baseline_tokens, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=6.5, label="Baseline (terminus-2)", zorder=3)
ax1.plot(xt, enhanced_tokens, color=NAVY, linewidth=2.6, marker="o", markersize=7.0, label="+ PromptEnhancer (PE)", zorder=5)
ax1.fill_between(xt, baseline_tokens, enhanced_tokens, color=NAVY, alpha=0.07, zorder=2)

if QWEN4_27B_PRELIM["is_pending"]:
    ax1.scatter([xt[-1]], [enhanced_tokens[-1]], facecolors="#FFFFFF", edgecolors=NAVY, s=65, linewidth=2.2, zorder=6)
    ax1.scatter([xt[-1]], [baseline_tokens[-1]], facecolors="#FFFFFF", edgecolors=LIGHT_GREY, s=55, linewidth=2.0, zorder=6)

ax1.set_xticks(xt)
ax1.set_xticklabels(tasks_tok, fontsize=8.0)
ax1.set_ylim(-8000, 98000)
ax1.set_yticks([0, 20000, 40000, 60000, 80000])
ax1.set_xlim(-0.4, 4.45)
ax1.set_title("Tokens per Episode", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="lower", side="left", offset=0.17, text_gap=0.032, color=NAVY)

tok_base_off = [(0, 8), (-4, 8), (0, 8), (0, 8), (0, 8)]
for i in range(len(xt)):
    is_qwen_pending = (i == 4 and QWEN4_27B_PRELIM["is_pending"])
    fw = "bold" if i == 4 else "normal"
    b_lbl = "TBD" if is_qwen_pending else f"{baseline_tokens[i]:,}"
    e_lbl = "TBD (-51%)" if is_qwen_pending else f"{enhanced_tokens[i]:,}"
    ax1.annotate(b_lbl, (xt[i], baseline_tokens[i]), textcoords="offset points",
                 xytext=tok_base_off[i], ha="center", va="bottom", fontsize=8.0, fontweight=fw, color=TEXT_MUTED)
    ax1.annotate(e_lbl, (xt[i], enhanced_tokens[i]), textcoords="offset points",
                 xytext=(0, -15), ha="center", va="bottom", fontsize=8.0, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.9)

# Right panel: Wall-Clock Time (Seconds) ordered cleanly
tasks_sec = [
    "git-leak-\nrecovery",
    "cancel-async-\ntasks",
    "nginx-request-\nlogging",
    "db-wal-\nrecovery",
    QWEN4_27B_PRELIM["subset_label"],
]
baseline_sec = [83.9, 152.7, 223.2, 397.5, QWEN4_27B_PRELIM["baseline_mean_seconds"]]
enhanced_sec = [38.6, 123.6, 152.5, 99.0, QWEN4_27B_PRELIM["enhanced_mean_seconds"]]
xs = np.arange(len(tasks_sec))

style_line_ax(ax2)
ax2.plot(xs, baseline_sec, color=LIGHT_GREY, linewidth=2.3, linestyle="--", marker="s", markersize=6.5, label="Baseline (terminus-2)", zorder=3)
ax2.plot(xs, enhanced_sec, color=TEAL_SLATE, linewidth=2.6, marker="o", markersize=7.0, label="+ PromptEnhancer (PE)", zorder=5)
ax2.fill_between(xs, baseline_sec, enhanced_sec, color=TEAL_SLATE, alpha=0.07, zorder=2)

if QWEN4_27B_PRELIM["is_pending"]:
    ax2.scatter([xs[-1]], [enhanced_sec[-1]], facecolors="#FFFFFF", edgecolors=TEAL_SLATE, s=65, linewidth=2.2, zorder=6)
    ax2.scatter([xs[-1]], [baseline_sec[-1]], facecolors="#FFFFFF", edgecolors=LIGHT_GREY, s=55, linewidth=2.0, zorder=6)

ax2.set_xticks(xs)
ax2.set_xticklabels(tasks_sec, fontsize=8.0)
ax2.set_ylim(-40, 465)
ax2.set_yticks([0, 100, 200, 300, 400])
ax2.set_xlim(-0.4, 4.45)
ax2.set_title("Wall-Clock Time (Seconds)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="lower", side="left", offset=0.14, text_gap=0.032, color=TEAL_SLATE)

for i in range(len(xs)):
    is_qwen_pending = (i == 4 and QWEN4_27B_PRELIM["is_pending"])
    fw = "bold" if i == 4 else "normal"
    b_lbl = "TBD" if is_qwen_pending else f"{baseline_sec[i]:.1f}s"
    e_lbl = "TBD (-50%)" if is_qwen_pending else f"{enhanced_sec[i]:.1f}s"
    ax2.annotate(b_lbl, (xs[i], baseline_sec[i]), textcoords="offset points",
                 xytext=(0, 8), ha="center", va="bottom", fontsize=8.0, fontweight=fw, color=TEXT_MUTED)
    ax2.annotate(e_lbl, (xs[i], enhanced_sec[i]), textcoords="offset points",
                 xytext=(0, -15), ha="center", va="bottom", fontsize=8.0, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.9)

fig.suptitle("PromptEnhancer Efficiency: Per-Task Token & Wall-Clock Time Savings",
             x=0.04, y=0.95, ha="left", fontsize=12.8, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "chart2_qwen4_token_wallclock_savings.png"))
plt.close(fig)


# ==============================================================================
# CHART 3: Episode Cumulative Token Trajectory & Encoder State Audit Accuracy
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.9), gridspec_kw={"width_ratios": [1.08, 1], "wspace": 0.34})

turns_x = np.array([1, 3, 5, 7, 9, 11, 13, 15])
base_cum_tok = [1086, 4114, 8605, 14691, 22281, 31969, 43740, 53532]
# Enhanced completes at Turn 7 (18,988 tokens); plateau shows avoided turns T8..T15
enh_cum_full = [1039, 4281, 10824, 18988, 18988, 18988, 18988, 18988]
enh_turns_active = np.array([1, 3, 5, 7])
enh_cum_active = [1039, 4281, 10824, 18988]

style_line_ax(ax1)
ax1.plot(turns_x, base_cum_tok, color=LIGHT_GREY, linewidth=2.2, linestyle="--", marker="s", markersize=6.0, label="Baseline (15 Turns • FAIL)", zorder=3)
ax1.plot(enh_turns_active, enh_cum_active, color=NAVY, linewidth=2.6, marker="o", markersize=7.0, label="+ PromptEnhancer (7 Turns • PASS)", zorder=5)
ax1.plot(turns_x[3:], enh_cum_full[3:], color=NAVY, linewidth=1.6, linestyle=":", zorder=4)
ax1.fill_between(turns_x[3:], base_cum_tok[3:], enh_cum_full[3:], color=NAVY, alpha=0.07, zorder=2)

ax1.set_xticks(turns_x)
ax1.set_xticklabels([f"T{t}" for t in turns_x], fontsize=8.4)
ax1.set_ylim(-5000, 66000)
ax1.set_yticks([0, 15000, 30000, 45000, 60000])
ax1.set_xlim(0.2, 16.2)
ax1.set_title("Cumulative Tokens (git-leak-recovery)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="lower", side="left", offset=0.17, text_gap=0.032, color=NAVY)

ax1.annotate("53,532 tok (FAIL)", (15, 53532), textcoords="offset points", xytext=(-6, 7),
             ha="right", va="bottom", fontsize=8.1, fontweight="bold", color=TEXT_MUTED)
ax1.annotate("18,988 tok (PASS • -64.5%)", (7, 18988), textcoords="offset points", xytext=(4, -18),
             ha="left", va="bottom", fontsize=8.1, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper left", ncol=1, fontsize=7.9)

# Right panel: Encoder accuracy across splits vs sub-ms latency
splits = ["Held-Out\n(N=1,200)", "Adversarial\n(N=38)", "TB-2.1 Live\n(N=12)", "Post-Heal\n(Self-Healed)"]
tiny_acc = [100.0, 97.4, 100.0, 100.0]
small_acc = [100.0, 100.0, 100.0, 100.0]
xsp = np.arange(len(splits))

style_line_ax(ax2)
ax2.plot(xsp, tiny_acc, color=TEAL_SLATE, linewidth=2.2, linestyle="--", marker="s", markersize=6.5, label="terminus-state-tiny (0.27 ms)", zorder=4)
ax2.plot(xsp, small_acc, color=NAVY, linewidth=2.5, marker="o", markersize=7.0, label="terminus-state-small (0.34 ms)", zorder=5)
ax2.fill_between(xsp, tiny_acc, 85, color=NAVY, alpha=0.05, zorder=2)

ax2.set_xticks(xsp)
ax2.set_xticklabels(splits, fontsize=8.2)
ax2.set_ylim(88, 104)
ax2.set_yticks([90, 95, 100])
ax2.set_xlim(-0.35, 3.35)
ax2.set_title("8-Class State Encoder Accuracy (%)", loc="left", fontsize=10.2, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="higher", side="left", offset=0.14, text_gap=0.032, color=TEAL_SLATE)

for i in range(len(xsp)):
    ax2.annotate(f"{small_acc[i]:.1f}%", (xsp[i], small_acc[i]), textcoords="offset points", xytext=(0, 7),
                 ha="center", va="bottom", fontsize=8.2, fontweight="bold", color=NAVY)
    if tiny_acc[i] != small_acc[i]:
        ax2.annotate(f"{tiny_acc[i]:.1f}%", (xsp[i], tiny_acc[i]), textcoords="offset points", xytext=(0, -14),
                     ha="center", va="bottom", fontsize=8.1, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="lower left", ncol=1, fontsize=7.9)

fig.suptitle("Episode Token Trajectory & Sub-Millisecond Encoder Accuracy",
             x=0.04, y=0.95, ha="left", fontsize=12.8, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "chart3_pe_turn_trajectory.png"))
plt.close(fig)

print(f"Generated 3 charts in {OUT_DIR}")
