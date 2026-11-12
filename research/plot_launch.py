"""Plot suggested names around the start of the feature.

Reads the JSON written by count_suggested.py. Steps are equal numbers of accounts, and one
step begins exactly at the first suggested name, so no step mixes accounts from before and
after the start. The axis is labelled with dates from account-dates.csv.

Usage: python research/plot_launch.py <suggested counts json> <output png> <output csv>
"""
import csv
import json
import sys
from datetime import datetime, timezone

from chart_style import AXIS, INK, MUTED, SECONDARY, SERIES, SURFACE, plt, style_axis
from dates import time_to_account

counts_path, png_path, csv_path = sys.argv[1:4]

STEP = 25_000
LAUNCH_ACCOUNT = 5_334_300
LAUNCH_LABEL = "24 Nov 2009"
TICK_MONTHS = [(2009, 5), (2009, 7), (2009, 9), (2009, 11), (2010, 1), (2010, 3), (2010, 5)]

with open(counts_path, encoding="utf-8") as handle:
    detail = json.load(handle)

fine_bin = detail["fine_bin"]
steps_before = (LAUNCH_ACCOUNT - detail["fine_from"]) // STEP
steps_after = (detail["fine_to"] - LAUNCH_ACCOUNT) // STEP
starts = [LAUNCH_ACCOUNT + STEP * index for index in range(-steps_before, steps_after)]
counts = [sum(detail["fine_counts"].get(str(index), 0)
              for index in range(start // fine_bin, (start + STEP) // fine_bin))
          for start in starts]
edges = starts + [starts[-1] + STEP]
ticks = [time_to_account(datetime(year, month, 1, tzinfo=timezone.utc)) for year, month in TICK_MONTHS]
tick_labels = [datetime(year, month, 1).strftime("%b %Y") for year, month in TICK_MONTHS]

figure, axis = plt.subplots(figsize=(11, 4.6), facecolor=SURFACE)
style_axis(axis)
axis.stairs(counts, edges, baseline=None, color=SERIES, linewidth=2)
axis.set_ylim(0, max(counts) * 1.18)
axis.set_xlim(edges[0], edges[-1])
axis.axvline(LAUNCH_ACCOUNT, color=AXIS, linewidth=1)
axis.text(LAUNCH_ACCOUNT - 40_000, max(counts) * 1.15, LAUNCH_LABEL, color=MUTED, fontsize=9, va="top", ha="right")
axis.set_xticks(ticks)
axis.set_xticklabels(tick_labels)
axis.set_ylabel(f"Names per {STEP:,} accounts", color=SECONDARY, fontsize=9.5)
figure.suptitle("Suggested names appear on 24 November 2009", x=0.06, y=0.97, ha="left",
                color=INK, fontsize=14, fontweight="bold")
figure.text(0.06, 0.875, f"Each step is {STEP:,} new accounts. It counts the usernames that are a suggestion word "
            "in front of one of the 2.5 million earliest usernames.", color=SECONDARY, fontsize=9.5)
figure.subplots_adjust(left=0.07, right=0.98, top=0.83, bottom=0.09)
figure.savefig(png_path, dpi=150, facecolor=SURFACE)

with open(csv_path, "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["first_account_id", "names"])
    for start, count in zip(starts, counts):
        writer.writerow([start, count])
before = counts[steps_before - 1]
print("wrote", png_path, "| step before the start:", before, "| first step after:", counts[steps_before])
