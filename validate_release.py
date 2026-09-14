#!/usr/bin/env python3
"""Validate the expected v1.0.0 repository contents and compact NetCDF metadata."""
from __future__ import annotations

from pathlib import Path
import sys

import xarray as xr

ROOT = Path(__file__).resolve().parent
VERSION = "1.0.0"
DATA_FILES = {
    "fig01_heatwave_days.nc": "Heatwave_days_global_local_summer_MOV.jpg",
    "fig02_duration_threshold_exceedance.nc": "Duration_PerGrid_byGroup_summer.jpg",
    "fig03_sm_temperature.nc": "corr_SoilTemp_LocalSummer_Global.jpg",
    "fig04_termination_wetdry.nc": "heatwave_termination_wetdry_summer_lag1_regional_relative.png",
    "fig05_block_heat_cooccurrence.nc": "Block_heat_cooccurrence_local_summer_global.jpg",
}
FIGURE_FILES = list(DATA_FILES.values())
REPOSITORY_FILES = [
    "README.md", "LICENSE", "CITATION.cff", "environment.yml", "VERSION",
    "CHANGELOG.md", ".gitignore", ".gitattributes", ".zenodo.json",
]


def main() -> int:
    failures: list[str] = []

    for name in REPOSITORY_FILES:
        if not (ROOT / name).exists():
            failures.append(f"missing repository file: {name}")

    version_path = ROOT / "VERSION"
    if version_path.exists() and version_path.read_text().strip() != VERSION:
        failures.append(f"VERSION is not {VERSION}")

    for filename, figure in DATA_FILES.items():
        path = ROOT / "data" / filename
        if not path.exists():
            failures.append(f"missing data file: data/{filename}")
            continue
        try:
            with xr.open_dataset(path, decode_timedelta=False) as ds:
                if ds.attrs.get("figure") != figure:
                    failures.append(
                        f"data/{filename}: figure attribute is {ds.attrs.get('figure')!r}, expected {figure!r}"
                    )
                version = ds.attrs.get("reproduction_package_version")
                if version not in (None, VERSION):
                    failures.append(
                        f"data/{filename}: unexpected reproduction_package_version={version!r}"
                    )
                for key, value in ds.attrs.items():
                    if isinstance(value, str) and any(
                        marker in value for marker in ("/users/", "/capstor/", "/scratch/")
                    ):
                        failures.append(
                            f"data/{filename}: machine-specific path remains in attribute {key!r}"
                        )
        except Exception as exc:
            failures.append(f"could not open data/{filename}: {exc}")

    missing_figures = [name for name in FIGURE_FILES if not (ROOT / "figures" / name).exists()]
    if missing_figures:
        print("Reference figures not all present yet:")
        for name in missing_figures:
            print(f"  - figures/{name}")
        print("This is not fatal before running `python run_all_figures.py`.\n")

    if failures:
        print("Release validation FAILED:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("Release validation passed for v1.0.0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
