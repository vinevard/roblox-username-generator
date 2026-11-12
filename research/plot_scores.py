"""Plot how the derivation rule's score separates suggestion words from other prefixes.

Usage: python research/plot_scores.py <profile json> <output png> <output csv>
"""
import csv
import sys

from chart_style import AXIS, INK, MUTED, SECONDARY, SERIES, SURFACE, plt, style_axis
from derive_list import THRESHOLD, load_scores

profile_path, png_path, csv_path = sys.argv[1:4]

SHOW_FROM = 50
BIN_WIDTH = 25
NOT_A_WORD = "BadUsername"

scores = load_scores(profile_path)
shown = {prefix: score for prefix, score in scores.items() if score >= SHOW_FROM}
kept = [score for prefix, score in shown.items() if score >= THRESHOLD and prefix != NOT_A_WORD]
rejected = [score for prefix, score in shown.items() if score < THRESHOLD]
bin_count = int((max(kept) - SHOW_FROM) // BIN_WIDTH) + 2
edges = [SHOW_FROM + BIN_WIDTH * index for index in range(bin_count)]

figure, axis = plt.subplots(figsize=(11, 4.8), facecolor=SURFACE)
style_axis(axis)
axis.hist(rejected, bins=edges, color=MUTED, rwidth=0.86, label=f"Rejected ({len(rejected)} shown)")
axis.hist(kept, bins=edges, color=SERIES, rwidth=0.86, label=f"Suggestion words ({len(kept)})")
height = axis.get_ylim()[1]
axis.axvline(THRESHOLD, color=AXIS, linewidth=1)
axis.text(THRESHOLD + 8, height * 0.97, f"cut-off {THRESHOLD}", color=MUTED, fontsize=9, va="top")
axis.annotate(f"{NOT_A_WORD} ({scores[NOT_A_WORD]:.0f})", xy=(scores[NOT_A_WORD], 1),
              xytext=(scores[NOT_A_WORD] + 10, height * 0.30), color=SECONDARY, fontsize=9,
              arrowprops={"arrowstyle": "-", "color": AXIS, "linewidth": 1})
axis.set_xlim(SHOW_FROM, edges[-1])
axis.set_xlabel("Score: smallest excess over the baseline of the prefix, accounts 110–200 million",
                color=SECONDARY, fontsize=9.5)
axis.set_ylabel("Number of prefixes", color=SECONDARY, fontsize=9.5)
axis.legend(loc="upper right", frameon=False, fontsize=9.5, labelcolor=SECONDARY)
figure.suptitle("The rule separates suggestion words from everything else", x=0.06, y=0.97, ha="left",
                color=INK, fontsize=14, fontweight="bold")
figure.text(0.06, 0.875, f"Prefixes by score. Another {len(scores) - len(shown):,} prefixes score below "
            f"{SHOW_FROM} and are not shown.", color=SECONDARY, fontsize=9.5)
figure.subplots_adjust(left=0.07, right=0.98, top=0.83, bottom=0.13)
figure.savefig(png_path, dpi=150, facecolor=SURFACE)

with open(csv_path, "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["prefix", "score", "kept_by_rule"])
    for prefix, score in sorted(shown.items(), key=lambda item: -item[1]):
        writer.writerow([prefix, round(score, 1), int(score >= THRESHOLD)])
print("wrote", png_path, "| kept", len(kept), "| rejected shown", len(rejected),
      "| max rejected", round(max(rejected), 1), "| min kept", round(min(kept), 1))
