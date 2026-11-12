"""Plot suggested names around the start of the feature.

Reads the JSON written by launch_detail.py.

Usage: python research/plot_launch.py <launch detail json> <output png> <output csv>
"""
import csv
import json
import sys

from chart_style import AXIS, INK, MUTED, SECONDARY, SERIES, SURFACE, plt, style_axis

detail_path, png_path, csv_path = sys.argv[1:4]

FIRST_ACCOUNT = 3_000_000
LAST_ACCOUNT = 8_000_000
PLOT_BIN = 25_000
LAUNCH_ACCOUNT = 5_334_300
LAUNCH_LABEL = "24 Nov 2009"

with open(detail_path, encoding="utf-8") as handle:
    detail = json.load(handle)

source_bin = detail["bin"]
starts = list(range(FIRST_ACCOUNT, LAST_ACCOUNT, PLOT_BIN))
counts = [sum(detail["counts"].get(str(index), 0)
              for index in range(start // source_bin, (start + PLOT_BIN) // source_bin))
          for start in starts]
edges = [start / 1e6 for start in starts] + [LAST_ACCOUNT / 1e6]
millions = range(FIRST_ACCOUNT // 1_000_000, LAST_ACCOUNT // 1_000_000 + 1)

figure, axis = plt.subplots(figsize=(11, 4.6), facecolor=SURFACE)
style_axis(axis)
axis.stairs(counts, edges, baseline=None, color=SERIES, linewidth=2)
axis.set_ylim(0, max(counts) * 1.18)
axis.set_xlim(FIRST_ACCOUNT / 1e6, LAST_ACCOUNT / 1e6)
axis.axvline(LAUNCH_ACCOUNT / 1e6, color=AXIS, linewidth=1)
axis.text(LAUNCH_ACCOUNT / 1e6 - 0.04, max(counts) * 1.15, LAUNCH_LABEL, color=MUTED, fontsize=9,
          va="top", ha="right")
axis.set_xticks(list(millions))
axis.set_xticklabels([f"{value}M" for value in millions])
axis.set_xlabel("Account ID", color=SECONDARY, fontsize=9.5)
axis.set_ylabel(f"Names per {PLOT_BIN:,} accounts", color=SECONDARY, fontsize=9.5)
figure.suptitle("Suggested names appear on 24 November 2009", x=0.06, y=0.97, ha="left",
                color=INK, fontsize=14, fontweight="bold")
figure.text(0.06, 0.875, "Usernames that start with a suggestion word and end with one of the 2.5 million "
            "earliest usernames.", color=SECONDARY, fontsize=9.5)
figure.subplots_adjust(left=0.07, right=0.98, top=0.83, bottom=0.13)
figure.savefig(png_path, dpi=150, facecolor=SURFACE)

with open(csv_path, "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["first_account_id", "names"])
    for start, count in zip(starts, counts):
        writer.writerow([start, count])
print("wrote", png_path)
