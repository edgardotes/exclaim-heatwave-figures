#!/usr/bin/env python3
"""Reproduce the 3-panel conditional duration-threshold exceedance figure."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "fig02_duration_threshold_exceedance.nc"
DEFAULT_OUTPUT = (
    ROOT / "figures" / "Duration_PerGrid_byGroup_summer.jpg"
)

COLORS = {
    "ERA5": "#000000",
    "ICON 2.5 km": "#448933",
    "ICON 10 km": "#F2AA3C",
    "ICON 10 km ON": "#BD4078",
    "ICON 40 km ON": "#88CCEE",
}
REGIONS = ["Polar", "Extratropics", "Tropics"]


NS_PER_DAY = 86_400_000_000_000.0


def _as_discrete_day_counts(values, *, label: str) -> np.ndarray:
    """Normalize threshold values to integer days, including legacy ns values."""
    raw = np.asarray(values)
    if np.issubdtype(raw.dtype, np.timedelta64):
        days = (raw / np.timedelta64(1, "D")).astype(float)
    else:
        days = np.asarray(raw, dtype=float)
        finite = days[np.isfinite(days)]
        if finite.size and np.nanmax(np.abs(finite)) > 10_000:
            candidate = days / NS_PER_DAY
            candidate_finite = candidate[np.isfinite(candidate)]
            if (
                candidate_finite.size
                and np.nanmax(np.abs(candidate_finite)) < 10_000
                and np.allclose(
                    candidate_finite, np.rint(candidate_finite), rtol=0, atol=1e-6
                )
            ):
                days = candidate

    if not np.all(np.isfinite(days)):
        raise ValueError(f"{label}: non-finite threshold values: {days}")
    if not np.allclose(days, np.rint(days), rtol=0, atol=1e-6):
        raise ValueError(f"{label}: thresholds are not integer day counts: {days}")
    return np.rint(days).astype(int)


def _cvm_annotation(ds: xr.Dataset, region: str, reference_name: str) -> str:
    abbreviations = {
        "ICON 2.5 km": "2.5",
        "ICON 10 km": "10",
        "ICON 10 km ON": "10 ON",
        "ICON 40 km ON": "40 ON",
    }
    parts = []
    for model in ds.model.values.astype(str):
        if model == reference_name:
            continue
        p = float(ds["cvm_pvalue"].sel(region=region, model=model))
        significant = bool(
            ds["cvm_significant"].sel(region=region, model=model).item()
        )
        parts.append(
            f"{abbreviations.get(model, model)}: {p:.3f}{'*' if significant else ''}"
        )

    if not parts:
        return ""
    midpoint = (len(parts) + 1) // 2
    return "CvM p: " + "; ".join(parts[:midpoint]) + "\n" + "; ".join(parts[midpoint:])


def _shared_legend(fig, ax, ncol=3, y=0.02) -> None:
    handles, labels = ax.get_legend_handles_labels()
    unique = {}
    for handle, label in zip(handles, labels):
        if label not in unique:
            unique[label] = handle
    fig.legend(
        list(unique.values()),
        list(unique.keys()),
        loc="lower center",
        bbox_to_anchor=(0.5, y),
        frameon=False,
        fontsize=9,
        ncol=ncol,
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Keep timedelta decoding disabled, then normalize legacy threshold values
    # explicitly below. Earlier compact files may contain nanoseconds rather than
    # integer days (e.g. 345600000000000 == 4 days).
    with xr.open_dataset(args.input, decode_timedelta=False) as src:
        ds = src.load()

    reference_name = str(ds.attrs.get("reference_name", "ERA5"))
    ci = float(ds.attrs.get("confidence_level", 95.0))
    season_mode = str(ds.attrs.get("season_mode", "summer"))

    available_regions = set(ds.region.values.astype(str))
    missing = [r for r in REGIONS if r not in available_regions]
    if missing:
        raise ValueError(f"Missing required regions in {args.input}: {missing}")

    x = ds["quantile"].values.astype(float)
    fig, axes = plt.subplots(
        len(REGIONS),
        1,
        figsize=(8.6, 13.5),
        sharey=True,
    )
    axes = np.atleast_1d(axes)

    for i, (ax, region) in enumerate(zip(axes, REGIONS)):
        n_env = int(ds["era5_envelope_n_years"].sel(region=region))
        ax.fill_between(
            x,
            ds["era5_envelope_low"].sel(region=region).values,
            ds["era5_envelope_high"].sel(region=region).values,
            color="0.75",
            alpha=0.45,
            linewidth=0,
            label=f"ERA5 random {n_env}-yr {ci:g}% range",
            zorder=1,
        )

        for model in ds.model.values.astype(str):
            y = ds["relative_exceedance"].sel(region=region, model=model).values
            if model == reference_name:
                linewidth = 2.4
                zorder = 5
            else:
                significant = bool(
                    ds["cvm_significant"].sel(region=region, model=model).item()
                )
                linewidth = 3.4 if significant else 1.7
                zorder = 6 if significant else 4

            ax.plot(
                x,
                y,
                marker="o",
                linewidth=linewidth,
                color=COLORS.get(model),
                label=model,
                zorder=zorder,
            )

        ax.axhline(0, color="black", linewidth=1.0, zorder=2)

        threshold_days = _as_discrete_day_counts(
            ds["threshold_days"].sel(region=region).values,
            label=f"{region} threshold_days",
        )

        xtick_labels = [
            f"{q:.3g}\n>= {d}"
            for q, d in zip(x, threshold_days)
        ]
        ax.set_xticks(x)
        ax.set_xticklabels(xtick_labels)
        ax.set_title(f"({chr(97 + i)}) {region}", fontsize=12, weight="bold")
        ax.grid(axis="y", alpha=0.25)

        annotation = _cvm_annotation(ds, region, reference_name)
        if annotation:
            ax.text(
                0.98,
                0.97,
                annotation,
                transform=ax.transAxes,
                ha="right",
                va="top",
                fontsize=7.2,
                bbox=dict(
                    facecolor="white",
                    edgecolor="none",
                    alpha=0.72,
                    pad=1.8,
                ),
                zorder=20,
            )

        ax.set_xlabel("")
        ax.set_ylabel("")

    # Deliberately no figure-level title: matches the current manuscript script.
    fig.supxlabel(
        "ERA5 duration quantile threshold",
        fontsize=12,
        weight="bold",
        y=0.065,
    )
    fig.supylabel(
        "Relative exceedance difference [%]",
        fontsize=12,
        weight="bold",
        x=0.02,
    )

    _shared_legend(fig, axes[0], ncol=3, y=0.02)
    fig.subplots_adjust(
        left=0.11,
        right=0.98,
        top=0.94,
        bottom=0.12,
        hspace=0.26,
    )

    fig.savefig(
        args.output,
        dpi=300,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.03,
    )
    plt.close(fig)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
