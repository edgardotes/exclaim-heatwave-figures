#!/usr/bin/env python3
"""Add v1.0.0 release metadata to already-generated compact NetCDF files.

This is optional and does not recompute any scientific quantity. It is useful
when the five figure-ready files were created before the release metadata was
added to the preparation scripts.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import tempfile

import xarray as xr

from _common import release_attrs, write_netcdf

FIGURES = {
    "fig01_heatwave_days.nc": "Heatwave_days_global_local_summer_MOV.jpg",
    "fig02_duration_threshold_exceedance.nc": "Duration_PerGrid_byGroup_summer.jpg",
    "fig03_sm_temperature.nc": "corr_SoilTemp_LocalSummer_Global.jpg",
    "fig04_termination_wetdry.nc": "heatwave_termination_wetdry_summer_lag1_regional_relative.png",
    "fig05_block_heat_cooccurrence.nc": "Block_heat_cooccurrence_local_summer_global.jpg",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data",
    )
    args = parser.parse_args()

    for filename, figure in FIGURES.items():
        path = args.data_dir / filename
        if not path.exists():
            raise FileNotFoundError(path)

        with xr.open_dataset(path, decode_timedelta=False) as src:
            ds = src.load()

        # Remove machine-specific absolute paths left by earlier exporters.
        for key in [
            "source_file",
            "source_analysis_script",
            "relative_csv",
            "uncertainty_csv",
            "context_source",
        ]:
            value = ds.attrs.get(key)
            if isinstance(value, str) and value:
                ds.attrs[key] = Path(value).name

        ds.attrs.update(
            release_attrs(preparation_script="release metadata update")
        )
        ds.attrs["figure"] = figure

        with tempfile.TemporaryDirectory(dir=path.parent) as tmpdir:
            tmp = Path(tmpdir) / filename
            write_netcdf(ds, tmp)
            tmp.replace(path)
        print(f"Updated metadata: {path}")


if __name__ == "__main__":
    main()
