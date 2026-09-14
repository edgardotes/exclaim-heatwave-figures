#!/usr/bin/env python3
"""Reproduce Heatwave_days_global_local_summer_MOV.jpg from compact NetCDF."""
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
DEFAULT_INPUT = ROOT / "data" / "fig01_heatwave_days.nc"
DEFAULT_OUTPUT = ROOT / "figures" / "Heatwave_days_global_local_summer_MOV.jpg"

MODELS = [
    ("ICON 2.5 km", "bias_icon25", "significant_icon25"),
    ("ICON 10 km", "bias_icon10", "significant_icon10"),
    ("ICON 10 km ON", "bias_icon10_on", "significant_icon10_on"),
    ("ICON 40 km ON", "bias_icon40_on", "significant_icon40_on"),
]


def plot_stipple(ax, sig_da):
    sig = sig_da.fillna(0).astype(np.int8)
    cs = ax.contourf(
        sig.lon, sig.lat, sig,
        transform=ccrs.PlateCarree(),
        colors="none", levels=[0.5, 1.5], hatches=["xxxx"],
    )
    if hasattr(cs, "collections"):
        for coll in cs.collections:
            coll.set_edgecolor("black")
            coll.set_linewidth(0.0)
    return cs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    ds = xr.open_dataset(args.input)
    levels = np.arange(0, 9, 1)
    alevels = np.arange(-4, 5, 1)
    proj = ccrs.Robinson(central_longitude=0)

    mpl.rcParams["hatch.linewidth"] = 1.5
    cmap = cmocean.cm.balance
    newcmap = cmocean.tools.crop_by_percent(cmap, 30, which="both", N=None)

    fig, axes = plt.subplots(3, 2, figsize=(12, 9), dpi=300,
                             subplot_kw={"projection": proj})

    p_abs = ds["heatwave_days_era5"].plot(
        ax=axes[0, 0], cmap=cmocean.cm.matter, levels=levels,
        transform=ccrs.PlateCarree(), extend="max", add_colorbar=False,
    )
    axes[0, 0].coastlines(color="grey")
    axes[0, 0].set_title("a) ERA5")

    panel_axes = [axes[0, 1], axes[1, 0], axes[1, 1], axes[2, 0]]
    p_bias = None
    for letter, ax, (label, bias_name, sig_name) in zip("bcde", panel_axes, MODELS):
        p_bias = ds[bias_name].plot(
            ax=ax, cmap=newcmap, levels=alevels,
            transform=ccrs.PlateCarree(), extend="both", add_colorbar=False,
        )
        plot_stipple(ax, ds[sig_name])
        ax.coastlines(color="grey")
        ax.set_title(f"{letter}) {label} - ERA5")

    axes[2, 1].set_visible(False)
    fig.subplots_adjust(left=0.04, right=0.98, top=0.95, bottom=0.06,
                        wspace=0.02, hspace=0.20)

    box = axes[2, 1].get_position()
    cax_abs = fig.add_axes([box.x0 - 0.3 * box.width, box.y0 + 0.70 * box.height,
                            1.8 * box.width, 0.08 * box.height])
    cax_bias = fig.add_axes([box.x0 - 0.3 * box.width, box.y0 + 0.30 * box.height,
                             1.8 * box.width, 0.08 * box.height])

    fig.colorbar(p_abs, cax=cax_abs, orientation="horizontal").set_label(
        "[Local summer] Mean number of heatwave days"
    )
    fig.colorbar(p_bias, cax=cax_bias, orientation="horizontal").set_label(
        "Difference in [Local summer] mean heatwave days"
    )

    fig.savefig(args.output, dpi=300, facecolor="white", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
