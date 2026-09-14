#!/usr/bin/env python3
"""Standardize the existing heatwave-frequency output for Figure 1.

This script does NOT recompute heatwaves. It reads the compact derived NetCDF
already produced by plot_hw_frequency_global.py and writes the publication
input used by plotting/plot_fig01_heatwave_days.py.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import xarray as xr

from _common import require_vars, write_netcdf, copy_global_attrs, release_attrs

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "fig01_heatwave_days.nc"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True, help="Existing derived heatwave-frequency NetCDF")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = p.parse_args()

    src = xr.open_dataset(args.input)
    require_vars(
        src,
        [
            "hw_era5",
            "hw_bias_icon25",
            "hw_bias_icon10",
            "hw_bias_icon10_on",
            "hw_bias_icon40_on",
            "sig_icon25",
            "sig_icon10",
            "sig_icon10_on",
            "sig_icon40_on",
            "p_icon25",
            "p_icon10",
            "p_icon10_on",
            "p_icon40_on",
        ],
        args.input,
    )

    out = xr.Dataset(
        {
            "heatwave_days_era5": src["hw_era5"],
            "bias_icon25": src["hw_bias_icon25"],
            "bias_icon10": src["hw_bias_icon10"],
            "bias_icon10_on": src["hw_bias_icon10_on"],
            "bias_icon40_on": src["hw_bias_icon40_on"],
            "significant_icon25": src["sig_icon25"].fillna(False).astype("int8"),
            "significant_icon10": src["sig_icon10"].fillna(False).astype("int8"),
            "significant_icon10_on": src["sig_icon10_on"].fillna(False).astype("int8"),
            "significant_icon40_on": src["sig_icon40_on"].fillna(False).astype("int8"),
            "pvalue_icon25": src["p_icon25"],
            "pvalue_icon10": src["p_icon10"],
            "pvalue_icon10_on": src["p_icon10_on"],
            "pvalue_icon40_on": src["p_icon40_on"],
        }
    )
    if "hw_icon25" in src:
        out["heatwave_days_icon25"] = src["hw_icon25"]

    copy_global_attrs(
        src,
        out,
        figure="Heatwave_days_global_local_summer_MOV.jpg",
        archive_role="Processed data required to reproduce the main heatwave-day figure.",
        **release_attrs(preparation_script=Path(__file__).name, source_files=[args.input]),
    )
    out["heatwave_days_era5"].attrs.setdefault("units", "days per local summer")
    for name in ["bias_icon25", "bias_icon10", "bias_icon10_on", "bias_icon40_on"]:
        out[name].attrs.setdefault("units", "days per local summer")
        out[name].attrs.setdefault("long_name", "ICON minus ERA5 heatwave-day difference")

    write_netcdf(out, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
