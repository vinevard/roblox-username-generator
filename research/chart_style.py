"""Colours and axis styling shared by the plotting scripts."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import ticker

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SERIES = "#2a78d6"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def style_axis(axis):
    axis.set_facecolor(SURFACE)
    axis.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
    axis.grid(axis="y", color=GRID, linewidth=1)
    axis.set_axisbelow(True)
    axis.tick_params(colors=MUTED, length=0, labelsize=9)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(AXIS)
