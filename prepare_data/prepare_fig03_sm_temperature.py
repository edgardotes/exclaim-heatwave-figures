#!/usr/bin/env python3
"""Standardize the existing SM-Tmax coupling NetCDF for Figure 3."""
from __future__ import annotations

import argparse
from pathlib import Path
import xarray as xr

from _common import require_vars, write_netcdf, copy_global_attrs, release_attrs

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "fig03_sm_temperature.nc"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True, help="Existing derived SM-Tmax coupling NetCDF")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = p.parse_args()

    src = xr.open_dataset(args.input)
    require_vars(
        src,
        [
            "r_era5",
            "bias_icon25",
            "bias_icon10",
            "bias_icon10_on",
            "bias_icon40_on",
            "p_icon25",
            "p_icon10",
            "p_icon10_on",
            "p_icon40_on",
        ],
        args.input,
    )

    sig_source = {}
    for short in ["icon25", "icon10", "icon10_on", "icon40_on"]:
        for candidate in [f"sig_{short}_plot", f"sig_{short}_raw", f"sig_{short}"]:
            if candidate in src:
                sig_source[short] = candidate
                break
        else:
            raise KeyError(f"No significance variable found for {short} in {args.input}")

    out = xr.Dataset(
        {
            "correlation_era5": src["r_era5"],
            "bias_icon25": src["bias_icon25"],
            "bias_icon10": src["bias_icon10"],
            "bias_icon10_on": src["bias_icon10_on"],
            "bias_icon40_on": src["bias_icon40_on"],
            "pvalue_icon25": src["p_icon25"],
            "pvalue_icon10": src["p_icon10"],
            "pvalue_icon10_on": src["p_icon10_on"],
            "pvalue_icon40_on": src["p_icon40_on"],
            "significant_icon25": src[sig_source["icon25"]].fillna(False).astype("int8"),
            "significant_icon10": src[sig_source["icon10"]].fillna(False).astype("int8"),
            "significant_icon10_on": src[sig_source["icon10_on"]].fillna(False).astype("int8"),
            "significant_icon40_on": src[sig_source["icon40_on"]].fillna(False).astype("int8"),
        }
    )
    for old, new in [
        ("r_icon25", "correlation_icon25"),
        ("r_icon10", "correlation_icon10"),
        ("r_icon10_on", "correlation_icon10_on"),
        ("r_icon40_on", "correlation_icon40_on"),
    ]:
        if old in src:
            out[new] = src[old]

    # Keep raw/FDR masks when available because they are tiny and scientifically useful.
    for short in ["icon25", "icon10", "icon10_on", "icon40_on"]:
        for suffix in ["raw", "fdr"]:
            name = f"sig_{short}_{suffix}"
            if name in src:
                out[f"significant_{short}_{suffix}"] = src[name].fillna(False).astype("int8")

    copy_global_attrs(
        src,
        out,
        figure="corr_SoilTemp_LocalSummer_Global.jpg",
        archive_role="Processed data required to reproduce the main soil-moisture/Tmax coupling figure.",
        **release_attrs(preparation_script=Path(__file__).name, source_files=[args.input]),
    )
    write_netcdf(out, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
