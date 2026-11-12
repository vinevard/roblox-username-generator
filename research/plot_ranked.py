"""Plot every prefix in rank order by its extra names in 2016.

Uses the three numbers defined in derive_list.py. Writes a PNG chart and a CSV file with
the numbers for every prefix shown.

Usage: python research/plot_ranked.py <profile json> <output png> <output csv>
"""
import csv
import sys

from chart_style import AXIS, INK, MUTED, SECONDARY, SERIES, SURFACE, plt, style_axis
from derive_list import THRESHOLD, load_measures

profile_path, png_path, csv_path = sys.argv[1:4]

SHOWN = 700
NOT_A_WORD = "BadUsername"

measures = load_measures(profile_path)
ranked = sorted(measures.items(), key=lambda item: -item[1][2])[:SHOWN]
kept = [(rank, prefix, extra) for rank, (prefix, (_, _, extra)) in enumerate(ranked, 1) if extra >= THRESHOLD]
rejected = [(rank, prefix, extra) for rank, (prefix, (_, _, extra)) in enumerate(ranked, 1) if extra < THRESHOLD]
words = [entry for entry in kept if entry[1] != NOT_A_WORD]
lowest_word = words[-1]
not_a_word = next(entry for entry in kept if entry[1] == NOT_A_WORD)
nearest_miss = rejected[0]

figure, axis = plt.subplots(figsize=(11, 5), facecolor=SURFACE)
style_axis(axis)
axis.scatter([rank for rank, _, _ in kept], [extra for _, _, extra in kept], s=9, color=SERIES,
             label=f"Kept by the rule ({len(kept)})")
axis.scatter([rank for rank, _, _ in rejected], [extra for _, _, extra in rejected], s=9, color=MUTED,
             label="Rejected")
axis.axhline(THRESHOLD, color=AXIS, linewidth=1)
axis.text(8, THRESHOLD + 18, f"cut-off {THRESHOLD}", color=MUTED, fontsize=9)
labels = [(lowest_word, f"{lowest_word[1]}, the lowest word", (-190, 170)),
          (not_a_word, f"{not_a_word[1]}, not a word", (-190, -160)),
          (nearest_miss, f"{nearest_miss[1]}, the nearest miss", (40, 30))]
for (rank, _, extra), text, (dx, dy) in labels:
    axis.annotate(f"{text} ({extra:.0f})", xy=(rank, extra), xytext=(rank + dx, extra + dy), color=SECONDARY,
                  fontsize=9, arrowprops={"arrowstyle": "-", "color": AXIS, "linewidth": 1})
axis.set_xlim(0, SHOWN + 10)
axis.set_ylim(0, ranked[0][1][2] * 1.08)
axis.set_xlabel("Prefixes in order, from most extra names to fewest", color=SECONDARY, fontsize=9.5)
axis.set_ylabel("Extra names in 2016", color=SECONDARY, fontsize=9.5)
axis.legend(loc="upper right", frameon=False, fontsize=9.5, labelcolor=SECONDARY)
figure.suptitle(f"{len(kept)} prefixes stand apart from the rest", x=0.06, y=0.97, ha="left",
                color=INK, fontsize=14, fontweight="bold")
figure.text(0.06, 0.885, "Extra names in 2016 = a prefix's lowest count that year minus its usual level, "
            f"per 10 million accounts. The top {SHOWN} prefixes are shown.", color=SECONDARY, fontsize=9.5)
figure.subplots_adjust(left=0.08, right=0.98, top=0.84, bottom=0.12)
figure.savefig(png_path, dpi=150, facecolor=SURFACE)

with open(csv_path, "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["rank", "prefix", "usual", "lowest_in_2016", "extra", "kept"])
    for rank, (prefix, (usual, lowest, extra)) in enumerate(ranked, 1):
        writer.writerow([rank, prefix, round(usual, 1), lowest, round(extra, 1), int(extra >= THRESHOLD)])
print("wrote", png_path, "| kept", len(kept), "| lowest word", lowest_word, "| nearest miss", nearest_miss)
