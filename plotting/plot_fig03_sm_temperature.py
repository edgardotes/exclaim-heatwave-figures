#!/usr/bin/env python3
"""Reproduce corr_SoilTemp_LocalSummer_Global.jpg from compact NetCDF."""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "fig03_sm_temperature.nc"
DEFAULT_OUTPUT = ROOT / "figures" / "corr_SoilTemp_LocalSummer_Global.jpg"
HATCH = "...."


def lon_to_180(da):
    if "longitude" in da.dims or "longitude" in da.coords:
        da = da.rename({"longitude": "lon"})
    if "latitude" in da.dims or "latitude" in da.coords:
        da = da.rename({"latitude": "lat"})
    da = da.assign_coords(lon=(((da.lon + 180) % 360) - 180)).sortby("lon")
    _, ilat = np.unique(da.lat.values, return_index=True)
    _, ilon = np.unique(da.lon.values, return_index=True)
    return da.isel(lat=np.sort(ilat), lon=np.sort(ilon)).sortby("lat")


def plot_panel(ax, da, title, vmin, vmax, cmap="RdBu"):
    da = lon_to_180(da)
    data = np.ma.masked_invalid(da.values)
    extent = [float(da.lon.min()), float(da.lon.max()), float(da.lat.min()), float(da.lat.max())]
    pcm = ax.imshow(data, origin="lower", extent=extent, transform=ccrs.PlateCarree(),
                    cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest", rasterized=True)
    ax.set_title(title, fontsize=12)
    ax.set_global()
    ax.coastlines(linewidth=0.6, color="grey")
    return pcm


def plot_stipple(ax, sig_da):
    sig = lon_to_180(sig_da).fillna(0).astype(np.int8)
    cs = ax.contourf(sig.lon, sig.lat, sig, transform=ccrs.PlateCarree(),
                     levels=[0.5, 1.5], colors="none", hatches=[HATCH], zorder=10)
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

    proj = ccrs.Robinson(central_longitude=0)
    fig, axes = plt.subplots(3, 2, figsize=(11, 7.5), dpi=150,
                             subplot_kw={"projection": proj}, constrained_layout=False)

    pcm_abs = plot_panel(axes[0, 0], ds["correlation_era5"], "(a) ERA5", -0.70, 0.70)
    panels = [
        (axes[0, 1], "bias_icon25", "significant_icon25", "(b) ICON-2.5 km - ERA5"),
        (axes[1, 0], "bias_icon10", "significant_icon10", "(c) ICON-10 km - ERA5"),
        (axes[1, 1], "bias_icon10_on", "significant_icon10_on", "(d) ICON-10 km ON - ERA5"),
        (axes[2, 0], "bias_icon40_on", "significant_icon40_on", "(e) ICON-40 km ON - ERA5"),
    ]
    pcm_bias = None
    for ax, bname, sname, title in panels:
        pcm_bias = plot_panel(ax, ds[bname], title, -0.50, 0.50)
        plot_stipple(ax, ds[sname])

    axes[2, 1].set_visible(False)
    fig.subplots_adjust(left=0.04, right=0.98, top=0.93, bottom=0.06, wspace=0.02, hspace=0.20)
    box = axes[2, 1].get_position()
    cax_abs = fig.add_axes([box.x0 - 0.30 * box.width, box.y0 + 0.68 * box.height,
                            1.80 * box.width, 0.08 * box.height])
    cax_bias = fig.add_axes([box.x0 - 0.30 * box.width, box.y0 + 0.28 * box.height,
                             1.80 * box.width, 0.08 * box.height])
    fig.colorbar(pcm_abs, cax=cax_abs, orientation="horizontal").set_label(r"Corr ($SM$,$T_{\max}$)")
    fig.colorbar(pcm_bias, cax=cax_bias, orientation="horizontal").set_label(r"Difference in Corr ($SM$,$T_{\max}$)")

    fig.savefig(args.output, dpi=300, facecolor="white", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
