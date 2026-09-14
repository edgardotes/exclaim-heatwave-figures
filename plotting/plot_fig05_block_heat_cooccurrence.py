#!/usr/bin/env python3
"""Reproduce Block_heat_cooccurrence_local_summer_global.jpg from compact NetCDF."""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib as mpl
import cartopy.crs as ccrs
import cmocean

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "fig05_block_heat_cooccurrence.nc"
DEFAULT_OUTPUT = ROOT / "figures" / "Block_heat_cooccurrence_local_summer_global.jpg"


def plot_stipple(ax, sig_da):
    sig = sig_da.fillna(0).astype(np.int8)
    cs = ax.contourf(sig.lon, sig.lat, sig, transform=ccrs.PlateCarree(),
                     colors="none", levels=[0.5, 1.5], hatches=["xxxx"])
    if hasattr(cs, "collections"):
        for coll in cs.collections:
            coll.set_edgecolor("black")
            coll.set_linewidth(0.0)
    return cs


def add_blocking_contours(ax, da):
    da.plot.contour(ax=ax, colors="grey", linewidths=0.8,
                    levels=[2, 4, 6, 8, 10, 12], transform=ccrs.PlateCarree())


def format_map(ax, title):
    ax.coastlines(color="0.35", linewidth=0.7)
    ax.set_title(title, loc="center")
    ax.set_title("", loc="left")
    ax.set_title("", loc="right")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(args.input)

    levels = np.arange(0, 100, 10)
    alevels = np.arange(-40, 50, 10)
    proj = ccrs.Robinson(central_longitude=0)
    mpl.rcParams["hatch.linewidth"] = 1.5
    newcmap = cmocean.tools.crop_by_percent(cmocean.cm.balance, 30, which="both", N=None)

    fig, axes = plt.subplots(3, 2, figsize=(12, 9), dpi=300,
                             subplot_kw={"projection": proj})
    panels = [
        (ds["p_block_given_heatwave_era5"], None, axes[0, 0], "a) ERA5", "Spectral_r", levels, "max"),
        (ds["bias_icon25"], ds["significant_icon25"], axes[0, 1], "b) ICON 2.5 km - ERA5", newcmap, alevels, "both"),
        (ds["bias_icon10"], ds["significant_icon10"], axes[1, 0], "c) ICON 10 km - ERA5", newcmap, alevels, "both"),
        (ds["bias_icon10_on"], ds["significant_icon10_on"], axes[1, 1], "d) ICON 10 km ON - ERA5", newcmap, alevels, "both"),
        (ds["bias_icon40_on"], ds["significant_icon40_on"], axes[2, 0], "e) ICON 40 km ON - ERA5", newcmap, alevels, "both"),
    ]

    p_abs = p_bias = None
    for i, (da, sig, ax, title, cmap, lev, extend) in enumerate(panels):
        pmap = da.plot(ax=ax, cmap=cmap, levels=lev, transform=ccrs.PlateCarree(),
                       extend=extend, add_colorbar=False, add_labels=False)
        if sig is not None:
            plot_stipple(ax, sig)
        add_blocking_contours(ax, ds["era5_blocking_frequency"])
        format_map(ax, title)
        if i == 0:
            p_abs = pmap
        elif p_bias is None:
            p_bias = pmap

    axes[2, 1].set_visible(False)
    fig.subplots_adjust(left=0.04, right=0.98, top=0.95, bottom=0.06, wspace=0.02, hspace=0.20)
    box = axes[2, 1].get_position()
    cax_abs = fig.add_axes([box.x0 - 0.3 * box.width, box.y0 + 0.70 * box.height,
                            1.8 * box.width, 0.08 * box.height])
    cax_bias = fig.add_axes([box.x0 - 0.3 * box.width, box.y0 + 0.30 * box.height,
                             1.8 * box.width, 0.08 * box.height])
    fig.colorbar(p_abs, cax=cax_abs, orientation="horizontal").set_label(
        r"$P(\mathrm{block} \mid \mathrm{heatwave})$ [%]"
    )
    fig.colorbar(p_bias, cax=cax_bias, orientation="horizontal").set_label(
        r"Difference in $P(\mathrm{block} \mid \mathrm{heatwave})$ [percentage points]"
    )
    fig.savefig(args.output, dpi=300, facecolor="white", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
