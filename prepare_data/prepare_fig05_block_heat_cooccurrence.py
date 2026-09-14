#!/usr/bin/env python3
"""Standardize the existing block-heatwave co-occurrence NetCDF for Figure 5."""
from __future__ import annotations

import argparse
from pathlib import Path
import xarray as xr

from _common import require_vars, write_netcdf, copy_global_attrs, release_attrs

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "fig05_block_heat_cooccurrence.nc"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True, help="Existing derived blocking-heatwave NetCDF")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = p.parse_args()

    src = xr.open_dataset(args.input)
    require_vars(
        src,
        [
            "p_block_given_heatwave_era5",
            "bias_icon25",
            "bias_icon10",
            "bias_icon10_on",
            "bias_icon40_on",
            "sig_icon25",
            "sig_icon10",
            "sig_icon10_on",
            "sig_icon40_on",
            "pvalue_icon25",
            "pvalue_icon10",
            "pvalue_icon10_on",
            "pvalue_icon40_on",
            "era5_blocking_frequency",
        ],
        args.input,
    )

    out = xr.Dataset(
        {
            "p_block_given_heatwave_era5": src["p_block_given_heatwave_era5"],
            "bias_icon25": src["bias_icon25"],
            "bias_icon10": src["bias_icon10"],
            "bias_icon10_on": src["bias_icon10_on"],
            "bias_icon40_on": src["bias_icon40_on"],
            "significant_icon25": src["sig_icon25"].fillna(False).astype("int8"),
            "significant_icon10": src["sig_icon10"].fillna(False).astype("int8"),
            "significant_icon10_on": src["sig_icon10_on"].fillna(False).astype("int8"),
            "significant_icon40_on": src["sig_icon40_on"].fillna(False).astype("int8"),
            "pvalue_icon25": src["pvalue_icon25"],
            "pvalue_icon10": src["pvalue_icon10"],
            "pvalue_icon10_on": src["pvalue_icon10_on"],
            "pvalue_icon40_on": src["pvalue_icon40_on"],
            "era5_blocking_frequency": src["era5_blocking_frequency"],
        }
    )
    copy_global_attrs(
        src,
        out,
        figure="Block_heat_cooccurrence_local_summer_global.jpg",
        archive_role="Processed data required to reproduce the main blocking-heatwave co-occurrence figure.",
        **release_attrs(preparation_script=Path(__file__).name, source_files=[args.input]),
    )
    write_netcdf(out, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
