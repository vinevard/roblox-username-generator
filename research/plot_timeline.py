"""Plot how often selected prefixes occur over time, against a typical suggestion word.

Reads the JSON written by profile_all.py and the word list written by derive_list.py.
Writes a PNG chart and a CSV file of the plotted values.

Usage: python research/plot_timeline.py <profile json> <derived word list> <output png> <output csv>
"""
import csv
import json
import statistics
import sys

from datetime import datetime, timedelta

from chart_style import AXIS, INK, MUTED, SECONDARY, SERIES, SURFACE, plt, style_axis, ticker
from dates import account_to_time

profile_path, words_path, png_path, csv_path = sys.argv[1:5]

ERAS = range(0, 48)
TICK_YEARS = [2010, 2012, 2014, 2016, 2018]
ERA_MILLIONS = 10
PANELS = [
    ("Glorious", "A typical suggestion word"),
    ("Awesome", "Rejected by the rule; common in ordinary names"),
    ("Roblox", "Rejected by the rule; common in ordinary names"),
    ("Powerful", "A suggestion word at launch, gone by July 2015"),
    ("BadUsername", "Almost all on accounts from July 2015 to January 2017"),
    ("Mystical", "An ordinary word, for contrast"),
]
EVENTS = [(datetime(2009, 11, 24), "Nov 2009"), (datetime(2015, 7, 13), "Jul 2015"), (datetime(2017, 3, 8), "Mar 2017")]
LAST_SHOWN = datetime(2019, 1, 1)

with open(profile_path, encoding="utf-8") as handle:
    profiles = json.load(handle)["profiles"]
with open(words_path, encoding="utf-8") as handle:
    words = [word for word in handle.read().split() if word != "BadUsername"]


def series(prefix):
    return [profiles[prefix].get(str(era), 0) for era in ERAS]


typical = [statistics.median(profiles[word].get(str(era), 0) for word in words) for era in ERAS]
midpoints = [account_to_time((era + 0.5) * ERA_MILLIONS * 1_000_000).replace(tzinfo=None) for era in ERAS]
year_ticks = [datetime(year, 1, 1) for year in TICK_YEARS]

figure, axes = plt.subplots(2, 3, figsize=(13, 7.4), facecolor=SURFACE)
for axis, (prefix, note) in zip(axes.flat, PANELS):
    values = series(prefix)
    style_axis(axis)
    axis.plot(midpoints, typical, color=MUTED, linewidth=2, solid_capstyle="round")
    axis.plot(midpoints, values, color=SERIES, linewidth=2, solid_capstyle="round")
    top = max(max(values), max(typical)) * 1.18
    axis.set_ylim(0, top)
    axis.set_xlim(datetime(2009, 1, 1), LAST_SHOWN)
    for position, label in EVENTS:
        axis.axvline(position, color=AXIS, linewidth=1)
        axis.text(position + timedelta(days=30), top * 0.985, label, color=MUTED, fontsize=8, va="top")
    axis.set_title(prefix, loc="left", color=INK, fontsize=12, fontweight="bold", pad=22)
    axis.text(0, 1.035, note, transform=axis.transAxes, color=SECONDARY, fontsize=9)
    axis.set_xticks(year_ticks)
    axis.set_xticklabels([str(year) for year in TICK_YEARS])
    axis.yaxis.set_major_locator(ticker.MaxNLocator(4, integer=True))

figure.suptitle("Usernames that start with each prefix, 2009 to 2018", x=0.045, y=0.985, ha="left",
                color=INK, fontsize=14, fontweight="bold")
figure.text(0.045, 0.935, "Count for each 10 million new accounts. Only names where the remaining part is one of the 2.5 million "
            "earliest usernames. Each panel has its own vertical scale.", color=SECONDARY, fontsize=9.5)
handles = [plt.Line2D([], [], color=SERIES, linewidth=2, label="The prefix in the chart title"),
           plt.Line2D([], [], color=MUTED, linewidth=2, label="A typical suggestion word (median of 485 words)")]
figure.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.04, 0.925), ncol=2, frameon=False,
              fontsize=9.5, labelcolor=SECONDARY)
figure.text(0.5, 0.012, "Each point is 10 million accounts, placed at the date they were created. Points are closer together in busy years.",
            ha="center", color=SECONDARY, fontsize=9.5)
figure.subplots_adjust(left=0.055, right=0.985, top=0.80, bottom=0.085, hspace=0.50, wspace=0.20)
figure.savefig(png_path, dpi=150, facecolor=SURFACE)

with open(csv_path, "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["first_account_id", "created_about", "typical_suggestion_word"] + [prefix for prefix, _ in PANELS])
    columns = [series(prefix) for prefix, _ in PANELS]
    for index, era in enumerate(ERAS):
        writer.writerow([era * ERA_MILLIONS * 1_000_000, midpoints[index].strftime("%Y-%m"), typical[index]]
                        + [column[index] for column in columns])
print("wrote", png_path, csv_path)
