#!/usr/bin/env python3
"""Build one compact NetCDF for the regional heatwave-termination wet/dry figure.

Inputs are the small CSV products already written by
plot_heatwave_termination_wetdry_regions_zooms.py plus the heatwave-frequency
bias NetCDF used by the two context-map panels. No daily precipitation or
heatwave masks are loaded here.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

from _common import write_netcdf, release_attrs

BASE = "heatwave_termination_wetdry_summer_lag1_MAIN_TropicalAmericas_EastAsia"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "fig04_termination_wetdry.nc"

DOMAINS = ["tropical_americas", "east_asia"]
DOMAIN_TITLES = ["Tropical Americas", "East Asia"]
DOMAIN_BOUNDS = {
    "tropical_americas": (-83.0, -45.0, -15.0, 10.0),
    "east_asia": (110.0, 141.0, 35.0, 55.0),
}
MODELS = ["ICON-2.5 km", "ICON-10 km", "ICON-10 km ON", "ICON-40 km ON"]


def as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def norm_model(s: str) -> str:
    return (
        str(s).lower().replace("icon", "").replace("-", "")
        .replace("_", "").replace(" ", "").replace(".", "")
    )


def find_model_row(df: pd.DataFrame, domain: str, model: str) -> pd.Series:
    sub = df[df["domain"].astype(str) == domain]
    target = norm_model(model)
    hit = sub[sub["dataset"].map(norm_model) == target]
    if len(hit) != 1:
        raise ValueError(f"Expected one row for domain={domain!r}, model={model!r}; found {len(hit)}")
    return hit.iloc[0]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--csv-dir", type=Path, default=Path("."), help="Directory containing the two derived CSV files")
    p.add_argument("--relative-csv", type=Path, default=None)
    p.add_argument("--uncertainty-csv", type=Path, default=None)
    p.add_argument("--context-nc", type=Path, required=True, help="Derived heatwave-frequency NetCDF used for the context maps")
    p.add_argument("--context-var", default="hw_bias_icon25")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = p.parse_args()

    relative_path = args.relative_csv or (args.csv_dir / f"{BASE}_relative_to_ERA5.csv")
    uncertainty_path = args.uncertainty_csv or (args.csv_dir / f"{BASE}_ERA5_short_record_uncertainty.csv")

    relative = pd.read_csv(relative_path)
    uncertainty = pd.read_csv(uncertainty_path)

    req_rel = {"domain", "dataset", "dryday_rel_pct", "wetday_rel_pct", "era5_dryday", "era5_wetday"}
    req_unc = {
        "domain", "dataset", "dry_rel_low", "dry_rel_high", "wet_rel_low", "wet_rel_high",
        "outside_era5_range", "empirical_p_two_sided",
    }
    if not req_rel.issubset(relative.columns):
        raise KeyError(f"Missing relative CSV columns: {sorted(req_rel - set(relative.columns))}")
    if not req_unc.issubset(uncertainty.columns):
        raise KeyError(f"Missing uncertainty CSV columns: {sorted(req_unc - set(uncertainty.columns))}")

    nd, nm = len(DOMAINS), len(MODELS)
    arrays = {name: np.full((nd, nm), np.nan, dtype=float) for name in [
        "dryday_relative_pct", "wetday_relative_pct",
        "dry_ci_low_pct", "dry_ci_high_pct", "wet_ci_low_pct", "wet_ci_high_pct",
        "pvalue",
    ]}
    significant = np.zeros((nd, nm), dtype=np.int8)
    era5_dry = np.full(nd, np.nan)
    era5_wet = np.full(nd, np.nan)

    for i, domain in enumerate(DOMAINS):
        # ERA5 reference fractions are repeated in the relative table; use the first valid row.
        sub = relative[relative["domain"].astype(str) == domain]
        if sub.empty:
            raise ValueError(f"No rows found for domain={domain}")
        era5_dry[i] = float(sub["era5_dryday"].dropna().iloc[0])
        era5_wet[i] = float(sub["era5_wetday"].dropna().iloc[0])

        for j, model in enumerate(MODELS):
            r = find_model_row(relative, domain, model)
            u = find_model_row(uncertainty, domain, model)
            arrays["dryday_relative_pct"][i, j] = float(r["dryday_rel_pct"])
            arrays["wetday_relative_pct"][i, j] = float(r["wetday_rel_pct"])
            arrays["dry_ci_low_pct"][i, j] = float(u["dry_rel_low"])
            arrays["dry_ci_high_pct"][i, j] = float(u["dry_rel_high"])
            arrays["wet_ci_low_pct"][i, j] = float(u["wet_rel_low"])
            arrays["wet_ci_high_pct"][i, j] = float(u["wet_rel_high"])
            arrays["pvalue"][i, j] = float(u["empirical_p_two_sided"])
            significant[i, j] = int(as_bool(u["outside_era5_range"]))

    bounds = np.array([DOMAIN_BOUNDS[d] for d in DOMAINS], dtype=float)
    out = xr.Dataset(
        coords={
            "domain": DOMAINS,
            "model": MODELS,
            "domain_title": ("domain", DOMAIN_TITLES),
        }
    )
    for name, values in arrays.items():
        out[name] = (("domain", "model"), values)
    out["significant"] = (("domain", "model"), significant)
    out["era5_dryday_fraction"] = ("domain", era5_dry)
    out["era5_wetday_fraction"] = ("domain", era5_wet)
    out["domain_lon_min"] = ("domain", bounds[:, 0])
    out["domain_lon_max"] = ("domain", bounds[:, 1])
    out["domain_lat_min"] = ("domain", bounds[:, 2])
    out["domain_lat_max"] = ("domain", bounds[:, 3])

    with xr.open_dataset(args.context_nc) as ctx:
        if args.context_var not in ctx:
            raise KeyError(f"{args.context_var!r} not found in {args.context_nc}; available={list(ctx.data_vars)}")
        out["context_heatwave_frequency_bias_icon25"] = ctx[args.context_var].load()

    out.attrs.update(
        {
            "description": "Processed data required to reproduce the regional post-heatwave wet/dry figure.",
            "figure": "heatwave_termination_wetdry_summer_lag1_regional_relative.png",
            "event_subset": "heatwave termination day",
            "lag_days": 1,
            "wet_day_threshold_mm_day": 1.0,
            "local_summer": "NH=JJA, SH=DJF",
            **release_attrs(
                preparation_script=Path(__file__).name,
                source_files=[relative_path, uncertainty_path, args.context_nc],
            ),
            "context_map_padding_lon_degrees": 10.0,
            "context_map_padding_lat_degrees": 8.0,
        }
    )
    for v in ["dryday_relative_pct", "wetday_relative_pct", "dry_ci_low_pct", "dry_ci_high_pct", "wet_ci_low_pct", "wet_ci_high_pct"]:
        out[v].attrs["units"] = "%"
    out["era5_dryday_fraction"].attrs["units"] = "1"
    out["era5_wetday_fraction"].attrs["units"] = "1"
    out["context_heatwave_frequency_bias_icon25"].attrs.setdefault("units", "days per local summer")

    write_netcdf(out, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
