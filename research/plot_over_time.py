"""Plot suggested names per calendar month over the whole life of the feature.

Reads the JSON written by count_suggested.py and dates each bin with account-dates.csv.

Usage: python research/plot_over_time.py <suggested counts json> <output png> <output csv>
"""
import csv
import json
import sys
from datetime import datetime, timezone

import matplotlib.dates as mdates

from chart_style import AXIS, INK, MUTED, SECONDARY, SERIES, SURFACE, plt, style_axis
from dates import account_to_time

counts_path, png_path, csv_path = sys.argv[1:4]

FIRST_YEAR = 2009
LAST_YEAR = 2017
EVENTS = [
    (datetime(2009, 11, 24, tzinfo=timezone.utc), "24 Nov 2009\nfirst suggested names", "left"),
    (datetime(2015, 7, 13, tzinfo=timezone.utc), "13 Jul 2015", "right"),
    (datetime(2015, 11, 18, tzinfo=timezone.utc), "18 Nov 2015", "left"),
    (datetime(2017, 3, 8, tzinfo=timezone.utc), "8 Mar 2017", "left"),
]

with open(counts_path, encoding="utf-8") as handle:
    detail = json.load(handle)

bin_size = detail["bin"]
monthly = {(year, month): 0 for year in range(FIRST_YEAR, LAST_YEAR + 1) for month in range(1, 13)}
for index, count in detail["counts"].items():
    moment = account_to_time((int(index) + 0.5) * bin_size)
    key = (moment.year, moment.month)
    if key in monthly:
        monthly[key] += count

months = sorted(monthly)
starts = [datetime(year, month, 1) for year, month in months]
values = [monthly[key] for key in months]

figure, axis = plt.subplots(figsize=(11, 5), facecolor=SURFACE)
style_axis(axis)
axis.bar(starts, values, width=25, align="edge", color=SERIES)
top = max(values) * 1.2
axis.set_ylim(0, top)
axis.set_xlim(datetime(FIRST_YEAR, 1, 1), datetime(LAST_YEAR + 1, 1, 1))
for moment, label, side in EVENTS:
    axis.axvline(moment.replace(tzinfo=None), color=AXIS, linewidth=1)
    offset = 20 if side == "left" else -20
    axis.text(mdates.date2num(moment.replace(tzinfo=None)) + offset, top * 0.97, label, color=MUTED, fontsize=9,
              va="top", ha=side)
axis.xaxis.set_major_locator(mdates.YearLocator())
axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
axis.set_ylabel("Suggested names per month", color=SECONDARY, fontsize=9.5)
figure.suptitle("Suggested names per month, 2009 to 2017", x=0.06, y=0.97, ha="left",
                color=INK, fontsize=14, fontweight="bold")
figure.text(0.06, 0.865, "Each bar counts the accounts created that month whose username is a suggestion word in "
            "front of one of the 2.5 million earliest usernames.\nBefore November 2009 these are ordinary names "
            "that happen to fit.", color=SECONDARY, fontsize=9.5, va="center")
figure.subplots_adjust(left=0.08, right=0.98, top=0.80, bottom=0.08)
figure.savefig(png_path, dpi=150, facecolor=SURFACE)

with open(csv_path, "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["month", "names"])
    for (year, month), value in zip(months, values):
        writer.writerow([f"{year}-{month:02d}", value])
print("wrote", png_path, "| total", sum(values), "| peak", max(values))
