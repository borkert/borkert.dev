#!/usr/bin/env python3
"""Generate borkert.dev benchmark charts for the Apple Silicon CPU L2-cache-resident
neural log filter & execution state plugin (`minimodels-pe`) on Antigravity (`agy`)
with Gemini 4 Carbon (`gemini-4-carbon-low`).

Usage:
    python3 scripts/generate_agy_l2_pe_charts.py
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
TEAL_ACCENT = "#0D9488"
LIGHT_GREY = "#94A3B8"
PALE_GREY = "#CBD5E1"
WARN_RED = "#B91C1C"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#475569"


def style_ax(ax, keep_left=True, keep_bottom=True, y_grid=True):
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


def add_spanning_arrow(ax, direction="lower", side="left", offset=0.14, text_gap=0.032, label=None, color=TEXT_MUTED):
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
        fontsize=8.6,
        fontweight="bold",
        color=color,
        clip_on=False,
    )


# ==============================================================================
# CHART 1: Gemini 4 Carbon (`gemini-4-carbon-low`) on `agy` — Billed & Context Tokens
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.1), gridspec_kw={"width_ratios": [1.22, 0.92], "wspace": 0.34})

scenarios = [
    "c-build-fix\n(8 $\\rightarrow$ 6 turns)",
    "sqlite-wal\n(7 $\\rightarrow$ 5 turns)",
    "log-triage\n(4 $\\rightarrow$ 3 turns)",
    "py-pipeline\n(5 $\\rightarrow$ 5 turns)",
]
base_billed = [30371, 28279, 19937, 24958]
pe_billed = [24579, 20177, 8407, 23091]
pct_deltas = [-19.1, -28.7, -57.8, -7.5]

x = np.arange(len(scenarios))
w = 0.36

style_ax(ax1)
b1 = ax1.bar(x - w / 2, base_billed, width=w, color=PALE_GREY, edgecolor="#94A3B8", linewidth=0.7, label="Stock agy (Baseline)", zorder=3)
b2 = ax1.bar(x + w / 2, pe_billed, width=w, color=NAVY, label="With minimodels-pe (L2 Hook)", zorder=4)

ax1.set_xticks(x)
ax1.set_xticklabels(scenarios, fontsize=8.2, fontweight="bold")
ax1.set_ylim(0, 39000)
ax1.set_yticks([0, 10000, 20000, 30000])
ax1.set_yticklabels(["0", "10k", "20k", "30k"])
ax1.set_title("Billed Tokens per Scenario (4/4 Verified Pass)", loc="left", fontsize=10.0, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="lower", side="left", offset=0.135, text_gap=0.030, color=NAVY)

base_dx = [0.0, 0.0, 0.0, -0.05]
pe_dx = [0.04, 0.04, 0.02, 0.07]
for i in range(len(x)):
    ax1.text(x[i] - w / 2 + base_dx[i], base_billed[i] + 750, f"{base_billed[i]:,}", ha="center", va="bottom", fontsize=7.6, color=TEXT_MUTED)
    ax1.text(x[i] + w / 2 + pe_dx[i], pe_billed[i] + 750, f"{pe_billed[i]:,}\n({pct_deltas[i]:.1f}%)", ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper right", fontsize=8.0)

# Right panel: Suite-wide Billed vs Effective Context Tokens
agg_labels = ["Billed Total\nTokens", "Effective Context\n(in + cache_read)"]
agg_base = [103545, 345001]
agg_pe = [76254, 222908]
agg_pct = [-26.4, -35.4]
xa = np.arange(len(agg_labels))
wa = 0.32

style_ax(ax2)
ax2.bar(xa - wa / 2, agg_base, width=wa, color=PALE_GREY, edgecolor="#94A3B8", linewidth=0.7, label="Stock agy", zorder=3)
ax2.bar(xa + wa / 2, agg_pe, width=wa, color=TEAL_SLATE, label="With minimodels-pe", zorder=4)

ax2.set_xticks(xa)
ax2.set_xticklabels(agg_labels, fontsize=8.6, fontweight="bold")
ax2.set_ylim(0, 425000)
ax2.set_yticks([0, 100000, 200000, 300000, 400000])
ax2.set_yticklabels(["0", "100k", "200k", "300k", "400k"])
ax2.set_title("4-Scenario Suite Totals (Gemini 4 Carbon)", loc="left", fontsize=10.0, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax2, direction="lower", side="left", offset=0.16, text_gap=0.036, color=TEAL_SLATE)

for i in range(len(xa)):
    ax2.text(xa[i] - wa / 2, agg_base[i] + 8000, f"{agg_base[i]:,}", ha="center", va="bottom", fontsize=7.9, color=TEXT_MUTED)
    ax2.text(xa[i] + wa / 2, agg_pe[i] + 8000, f"{agg_pe[i]:,}\n({agg_pct[i]:.1f}%)", ha="center", va="bottom", fontsize=8.0, fontweight="bold", color=TEAL_SLATE)

ax2.legend(frameon=False, loc="upper left", fontsize=8.0)

fig.suptitle("Antigravity (agy) + Gemini 4 Carbon: Head-to-Head Token & Context Reductions",
             x=0.04, y=0.96, ha="left", fontsize=12.4, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.98, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "agy_l2_pe_tokens_context.png"))
plt.close(fig)


# ==============================================================================
# CHART 2: Apple Silicon 16 MiB P-Core L2 Cache Residency via SPECTRA Q4
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.0), gridspec_kw={"width_ratios": [1.18, 0.96], "wspace": 0.34})

models = [
    "summarizer-l2-pro\n(12.03M, General+CLI)",
    "summarizer-cli-l2\n(3.50M, Pure CLI)",
    "pe-state-encoder\n(263K, 8-Class State)",
]
fp32_mib = [45.91, 13.33, 0.96]
q4_mib = [6.52, 1.90, 0.96]  # state encoder kept in FP32 SIMD (0.96 MiB / 1.00 MB)

xm = np.arange(len(models))
wm = 0.33

style_ax(ax1)
ax1.axhspan(0, 16.0, color=TEAL_ACCENT, alpha=0.08, zorder=1)
ax1.axhline(16.0, color=TEAL_ACCENT, linestyle="--", linewidth=1.3, zorder=4)
ax1.text(2.40, 17.3, "16.0 MiB Apple Silicon P-Core Shared L2 Limit", ha="right", va="bottom",
         fontsize=8.0, fontweight="bold", color="#0F766E")

ax1.bar(xm[0] - wm / 2, fp32_mib[0], width=wm, color="#FCA5A5", edgecolor=WARN_RED, linewidth=0.8, label="FP32 Checkpoint", zorder=3)
ax1.bar(xm[1] - wm / 2, fp32_mib[1], width=wm, color=PALE_GREY, edgecolor="#94A3B8", linewidth=0.7, zorder=3)
ax1.bar(xm[2] - wm / 2, fp32_mib[2], width=wm, color=PALE_GREY, edgecolor="#94A3B8", linewidth=0.7, zorder=3)

ax1.bar(xm + wm / 2, q4_mib, width=wm, color=NAVY, label="Deployed in L2 Cache (4-Bit / Native)", zorder=5)

ax1.set_xticks(xm)
ax1.set_xticklabels(models, fontsize=8.1, fontweight="bold")
ax1.set_xlim(-0.52, 2.52)
ax1.set_ylim(0, 55.0)
ax1.set_yticks([0, 16, 32, 48])
ax1.set_yticklabels(["0 MiB", "16 MiB", "32 MiB", "48 MiB"])
ax1.set_title("Checkpoint Size vs. 16 MiB P-Core L2 Cache", loc="left", fontsize=10.0, fontweight="bold", color=TEXT_MUTED, pad=10)
add_spanning_arrow(ax1, direction="lower", side="left", offset=0.145, text_gap=0.032, color=NAVY)

ax1.text(xm[0] - wm / 2, fp32_mib[0] + 1.0, "45.91 MiB\n(Spills L2)", ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=WARN_RED)
ax1.text(xm[0] + wm / 2 + 0.08, q4_mib[0] + 1.0, "6.52 MiB Q4\n(7.0x smaller)", ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=NAVY)

ax1.text(xm[1] - wm / 2, fp32_mib[1] - 3.6, "13.33\nMiB", ha="center", va="center", fontsize=7.3, fontweight="bold", color="#334155", zorder=6)
ax1.text(xm[1] + wm / 2 + 0.08, q4_mib[1] + 1.0, "1.90 MiB Q4\n(<12% of L2)", ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=NAVY)

ax1.text(xm[2] + 0.04, q4_mib[2] + 1.2, "1.00 MB FP32\n(Live Self-Heal)", ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=NAVY)

ax1.legend(frameon=False, loc="upper right", fontsize=7.7)

# Right panel: Latency breakdown (sub-millisecond hook & L2 execution)
stages = [
    "Short output\n(<36 lines)",
    "Hook call\n(median)",
    "8-Class State\n(mean)",
    "Log Filter\n(mean)",
    "Python CLI\n(cold start)",
]
lat_ms = [0.050, 0.676, 4.266, 6.251, 45.0]
colors = [TEAL_ACCENT, NAVY, TEAL_SLATE, TEAL_SLATE, PALE_GREY]

yl = np.arange(len(stages))
style_ax(ax2, y_grid=False)
ax2.grid(axis="x", color="#F1F5F9", linestyle="-", linewidth=0.8, zorder=0)
ax2.set_axisbelow(True)

bars = ax2.barh(yl, lat_ms, height=0.52, color=colors, zorder=3)
ax2.axvline(1.0, color="#94A3B8", linestyle=":", linewidth=1.0, zorder=2)
ax2.set_yticks(yl)
ax2.set_yticklabels(stages, fontsize=8.1, fontweight="bold")
ax2.invert_yaxis()
ax2.set_xlim(0, 58)
ax2.set_xticks([0, 10, 20, 30, 40, 50])
ax2.set_xticklabels(["0 ms", "10 ms", "20 ms", "30 ms", "40 ms", "50 ms"], fontsize=8.0)
ax2.set_title("Per-Invocation Overhead (ms, Lower is Better)", loc="left", fontsize=9.8, fontweight="bold", color=TEXT_MUTED, pad=10)

labels_txt = ["0.05 ms (~50 µs)", "0.68 ms median", "4.27 ms in L2", "6.25 ms in L2", "~30–60 ms avoided"]
for i, v in enumerate(lat_ms):
    c = TEXT_MUTED if i == 4 else NAVY
    fw = "normal" if i == 4 else "bold"
    ax2.text(v + 1.0, yl[i], labels_txt[i], va="center", ha="left", fontsize=7.8, fontweight=fw, color=c)

fig.suptitle("Fitting Neural Salience & Execution-State Models Inside Apple Silicon CPU L2 Cache",
             x=0.04, y=0.96, ha="left", fontsize=12.4, fontweight="bold", color=TEXT_DARK)

plt.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.16)
plt.savefig(os.path.join(OUT_DIR, "agy_l2_cache_footprint.png"))
plt.close(fig)

print(f"Generated 2 charts in {OUT_DIR}")
