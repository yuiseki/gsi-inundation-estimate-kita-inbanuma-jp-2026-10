#!/usr/bin/env python3
"""docs/inundation_kita_inbanuma_4versions.png: the four versions side by side on a common extent (transparent background)."""

from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import ScalarFormatter

ROOT = Path(__file__).resolve().parent.parent
g = gpd.read_parquet(ROOT / "data" / "parquet" / "inundation_kita_inbanuma.parquet").sort_values("version_time")
minx, miny, maxx, maxy = g.total_bounds
pad = 0.003
fig, axes = plt.subplots(1, 4, figsize=(16, 5.2), sharex=True, sharey=True)
colors = ["#0b3c5d", "#1d6fa5", "#2a9d8f", "#e76f51"]
for ax, (_, r), c in zip(axes, g.iterrows(), colors):
    gpd.GeoSeries([r.geometry], crs=4326).plot(ax=ax, facecolor=c, edgecolor=c, alpha=0.75, linewidth=0.3)
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)
    ax.set_aspect(1 / 0.8137)  # 1 / cos(35.8 deg): equal ground scale in x and y
    ax.set_title(f"{r.version_time:%Y-%m-%d %H:%M} +09:00\n(published {r.published})", fontsize=10)
    ax.tick_params(labelsize=7)
    ax.xaxis.set_major_formatter(ScalarFormatter(useOffset=False))
    ax.set_xticks([140.23, 140.25, 140.27])
    ax.set_xlabel("")
    ax.patch.set_alpha(0)
axes[0].set_ylabel("latitude (EPSG:4326)")
for ax in axes[1:]:
    ax.set_ylabel("")
fig.supxlabel("longitude (EPSG:4326)", fontsize=9, y=0.03)
fig.legend(handles=[Patch(facecolor=c, alpha=0.75, label=f"{r.version_time:%Y-%m-%d %H:%M} (+09:00)") for c, (_, r) in zip(colors, g.iterrows())],
           title="basis time", loc="lower center", ncol=4, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.07))
fig.suptitle("GSI inundation estimate, Kita-Inbanuma (Typhoon No. 25, Reiwa 8): outline of each version", fontsize=11)
fig.text(0.5, -0.14, "Source: Geospatial Information Authority of Japan (GSI). Plotted from data processed by yuiseki; not a GSI publication.", ha="center", fontsize=8)
fig.patch.set_alpha(0)
(ROOT / "docs").mkdir(exist_ok=True)
fig.savefig(ROOT / "docs" / "inundation_kita_inbanuma_4versions.png", dpi=130, transparent=True, bbox_inches="tight")
