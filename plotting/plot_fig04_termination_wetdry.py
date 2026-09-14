#!/usr/bin/env python3
"""Reproduce the regional post-heatwave wet/dry figure from compact NetCDF."""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Rectangle
import cartopy.crs as ccrs

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "fig04_termination_wetdry.nc"
DEFAULT_OUTPUT = ROOT / "figures" / "heatwave_termination_wetdry_summer_lag1_regional_relative.png"

SHORT_LABELS = {
    "ICON-2.5 km": "2.5 km",
    "ICON-10 km": "10 km",
    "ICON-10 km ON": "10 km ON",
    "ICON-40 km ON": "40 km ON",
}


def lon_to_180(da):
    if "longitude" in da.coords or "longitude" in da.dims:
        da = da.rename({"longitude": "lon"})
    if "latitude" in da.coords or "latitude" in da.dims:
        da = da.rename({"latitude": "lat"})
    da = da.assign_coords(lon=((da.lon + 180.0) % 360.0) - 180.0).sortby("lon").sortby("lat")
    _, ilon = np.unique(da.lon.values, return_index=True)
    _, ilat = np.unique(da.lat.values, return_index=True)
    return da.isel(lon=np.sort(ilon), lat=np.sort(ilat))


def domain_bounds(ds, domain):
    return tuple(float(ds[v].sel(domain=domain)) for v in [
        "domain_lon_min", "domain_lon_max", "domain_lat_min", "domain_lat_max"
    ])


def regional_extent(ds, domain):
    lon_min, lon_max, lat_min, lat_max = domain_bounds(ds, domain)
    pad_lon = float(ds.attrs.get("context_map_padding_lon_degrees", 10.0))
    pad_lat = float(ds.attrs.get("context_map_padding_lat_degrees", 8.0))
    return (
        max(-180.0, lon_min - pad_lon), min(180.0, lon_max + pad_lon),
        max(-90.0, lat_min - pad_lat), min(90.0, lat_max + pad_lat),
    )


def subset_extent(da, extent):
    west, east, south, north = extent
    return da.where(
        (da.lon >= west) & (da.lon <= east) & (da.lat >= south) & (da.lat <= north),
        drop=True,
    )


def context_vmax(ds, bias, domains):
    vals = []
    for domain in domains:
        x = np.abs(subset_extent(bias, regional_extent(ds, domain)).values.astype(float))
        x = x[np.isfinite(x)]
        if x.size:
            vals.append(x)
    if not vals:
        raise ValueError("No finite context-map data found")
    vmax = float(np.nanpercentile(np.concatenate(vals), 98.0))
    return max(2.0, 2.0 * np.ceil(vmax / 2.0))


def draw_context_map(ax, ds, bias, domain, norm, letter):
    extent = regional_extent(ds, domain)
    field = subset_extent(bias, extent)
    mesh = ax.pcolormesh(field.lon, field.lat, field, transform=ccrs.PlateCarree(),
                         cmap="RdBu_r", norm=norm, shading="auto", rasterized=True)
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.coastlines(linewidth=0.6)
    lon_min, lon_max, lat_min, lat_max = domain_bounds(ds, domain)
    ax.add_patch(Rectangle((lon_min, lat_min), lon_max - lon_min, lat_max - lat_min,
                           fill=False, edgecolor="black", linewidth=2.0,
                           transform=ccrs.PlateCarree(), zorder=8))
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=0.35,
                      linestyle=":", alpha=0.55, x_inline=False, y_inline=False)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 8}
    gl.ylabel_style = {"size": 8}
    title = str(ds["domain_title"].sel(domain=domain).item())
    ax.set_title(f"({letter}) {title}: ICON-2.5 km heatwave-frequency bias", fontsize=10)
    return mesh


def draw_bars(ax, ds, domain, letter):
    models = ds.model.values.astype(str).tolist()
    x = np.arange(len(models))
    width = 0.36
    dry = ds["dryday_relative_pct"].sel(domain=domain).values.astype(float)
    wet = ds["wetday_relative_pct"].sel(domain=domain).values.astype(float)
    ax.bar(x - width / 2, dry, width, label="Dry", color="tab:grey")
    ax.bar(x + width / 2, wet, width, label="Wet", color="tab:blue")
    ax.axhline(0.0, linewidth=0.8)

    for j, model in enumerate(models):
        d_lo = float(ds["dry_ci_low_pct"].sel(domain=domain, model=model))
        d_hi = float(ds["dry_ci_high_pct"].sel(domain=domain, model=model))
        w_lo = float(ds["wet_ci_low_pct"].sel(domain=domain, model=model))
        w_hi = float(ds["wet_ci_high_pct"].sel(domain=domain, model=model))
        for xpos, lo, hi in [(x[j] - width / 2, d_lo, d_hi), (x[j] + width / 2, w_lo, w_hi)]:
            cap = 0.045
            ax.vlines(xpos, lo, hi, color="0.35", linewidth=1.2, zorder=5)
            ax.hlines([lo, hi], xpos - cap, xpos + cap, color="0.35", linewidth=1.2, zorder=5)

        if bool(ds["significant"].sel(domain=domain, model=model).item()):
            pair_vals = [dry[j], wet[j], d_lo, d_hi, w_lo, w_hi]
            ymax, ymin = max(pair_vals), min(pair_vals)
            span = max(10.0, abs(ymax - ymin))
            if wet[j] >= 0:
                ystar, va = max(dry[j], wet[j]) + 0.05 * span, "bottom"
            else:
                ystar, va = min(dry[j], wet[j]) - 0.05 * span, "top"
            ax.text(x[j], ystar, "*", ha="center", va=va, fontsize=12)

    title = str(ds["domain_title"].sel(domain=domain).item())
    ax.set_title(f"({letter}) {title}")
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT_LABELS.get(m, m) for m in models], rotation=25, ha="right")
    era5_dry = 100.0 * float(ds["era5_dryday_fraction"].sel(domain=domain))
    era5_wet = 100.0 * float(ds["era5_wetday_fraction"].sel(domain=domain))
    ax.text(0.02, 0.98, f"ERA5: dry {era5_dry:.1f}%, wet {era5_wet:.1f}%",
            transform=ax.transAxes, ha="left", va="top", fontsize=8)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(args.input)
    domains = ds.domain.values.astype(str).tolist()
    if len(domains) != 2:
        raise ValueError("This main-text layout expects exactly two domains")

    bias = lon_to_180(ds["context_heatwave_frequency_bias_icon25"])
    vmax = context_vmax(ds, bias, domains)
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)

    fig = plt.figure(figsize=(11.8, 8.8), layout="constrained")
    gs = fig.add_gridspec(2, 2, height_ratios=[0.92, 1.08])
    map_axes = [
        fig.add_subplot(gs[0, 0], projection=ccrs.PlateCarree()),
        fig.add_subplot(gs[0, 1], projection=ccrs.PlateCarree()),
    ]
    bar_axes = [fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])]
    bar_axes[1].sharey(bar_axes[0])

    meshes = [draw_context_map(ax, ds, bias, domain, norm, chr(97 + i))
              for i, (ax, domain) in enumerate(zip(map_axes, domains))]
    cbar = fig.colorbar(meshes[0], ax=map_axes, orientation="horizontal",
                        pad=0.035, fraction=0.06, shrink=0.86)
    cbar.set_label("Heatwave-frequency bias [days per local summer]")

    for i, (ax, domain) in enumerate(zip(bar_axes, domains)):
        draw_bars(ax, ds, domain, chr(99 + i))
    bar_axes[0].set_ylabel("Relative difference from ERA5 [%]")
    bar_axes[0].legend(frameon=False)
    bar_axes[1].tick_params(labelleft=False)

    fig.savefig(args.output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
