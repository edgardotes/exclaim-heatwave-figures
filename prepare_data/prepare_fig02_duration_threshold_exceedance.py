#!/usr/bin/env python3
"""Export compact data for the 3-panel conditional duration-threshold figure.

This is a one-time preparation script for the analysis/HPC environment. It
imports the current full ``plot_hw_duration_distribution_3panel.py`` workflow,
reuses its event-duration, ERA5-threshold, ERA5 N-year envelope and CvM
calculations, and writes only the quantities required to reproduce
``Duration_PerGrid_byGroup_summer.jpg``.

The resulting public plotting script does not read daily heatwave masks and
performs no bootstrap/CvM calculations.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import tempfile

import numpy as np
import xarray as xr

from _common import write_netcdf, release_attrs

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "fig02_duration_threshold_exceedance.nc"
REGIONS = ["Polar", "Extratropics", "Tropics"]


NS_PER_DAY = 86_400_000_000_000.0


def _as_discrete_day_counts(values, *, label: str) -> np.ndarray:
    """Return duration thresholds as integer day counts.

    Accepts normal numeric day counts, numpy/pandas timedelta values, and the
    legacy numeric-nanosecond representation produced by the earlier exporter
    (e.g. 345600000000000 == 4 days).
    """
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
        raise ValueError(f"{label}: non-finite duration thresholds: {days}")
    if not np.allclose(days, np.rint(days), rtol=0, atol=1e-6):
        raise ValueError(f"{label}: duration thresholds are not integer days: {days}")

    counts = np.rint(days).astype(np.int16)
    if np.any(counts < 0):
        raise ValueError(f"{label}: negative duration thresholds: {counts}")
    return counts


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(
        "duration_threshold_analysis_for_export", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _model_names(results, reference_name: str) -> list[str]:
    names = list(results[REGIONS[0]]["regional_probs"].keys())
    if reference_name not in names:
        raise ValueError(f"Reference {reference_name!r} not found in model list: {names}")
    return names


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--analysis-script",
        type=Path,
        default=Path("plot_hw_duration_distribution_3panel.py"),
        help="Path to the current full duration-analysis script on the HPC system.",
    )
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument(
        "--n-bootstrap",
        type=int,
        default=10000,
        help="ERA5 resamples used for the threshold envelope and CvM test.",
    )
    p.add_argument("--ci", type=float, default=95.0)
    args = p.parse_args()

    analysis_script = args.analysis_script.expanduser().resolve()
    if not analysis_script.exists():
        raise FileNotFoundError(analysis_script)

    mod = load_module(analysis_script)

    # Configure the imported workflow for exactly the manuscript diagnostic.
    mod.make_threshold_exceedance_plot = True
    mod.make_absolute_exceedance_plot = False
    mod.save_individual_figures = False
    mod.make_three_panel_figures = False
    mod.n_boot_test = int(args.n_bootstrap)
    mod.n_boot_uncertainty = int(args.n_bootstrap)
    mod.ci = float(args.ci)

    # The manuscript figure uses these three broad latitude-band regions.
    if hasattr(mod, "panel_regions"):
        mod.panel_regions = list(REGIONS)

    results = {}
    with tempfile.TemporaryDirectory(prefix="duration_threshold_export_") as tmp:
        # process_region writes small diagnostic CSV/JSON files; isolate those in
        # a temporary directory because only the compact NetCDF is retained.
        mod.out_dir = tmp
        for region in REGIONS:
            print(f"Processing {region} for compact threshold-exceedance export ...")
            results[region] = mod.process_region(region)

    reference_name = str(mod.reference_name)
    model_names = _model_names(results, reference_name)

    # Use the first region to establish the common quantile dimension. The
    # quantiles should be identical across regions, while the corresponding
    # discrete threshold duration can differ region by region.
    first_exc = results[REGIONS[0]]["conditional_exceedance"]
    if first_exc is None:
        raise RuntimeError(
            "conditional_exceedance is None. Ensure make_threshold_exceedance_plot=True."
        )
    quantiles = first_exc["quantile"].to_numpy(dtype=float)
    nq = len(quantiles)
    nr = len(REGIONS)
    nm = len(model_names)

    relative = np.full((nr, nm, nq), np.nan, dtype=float)
    threshold_days = np.full((nr, nq), -1, dtype=np.int16)
    era5_exceedance = np.full((nr, nq), np.nan, dtype=float)
    era5_cdf_at_threshold = np.full((nr, nq), np.nan, dtype=float)

    env_low = np.full((nr, nq), np.nan, dtype=float)
    env_high = np.full((nr, nq), np.nan, dtype=float)
    env_median = np.full((nr, nq), np.nan, dtype=float)
    env_n_years = np.zeros(nr, dtype=np.int16)

    cvm_pvalue = np.full((nr, nm), np.nan, dtype=float)
    cvm_statistic = np.full((nr, nm), np.nan, dtype=float)
    cvm_significant = np.zeros((nr, nm), dtype=np.int8)
    n_valid_years = np.zeros((nr, nm), dtype=np.int16)

    threshold_labels = np.empty((nr, nq), dtype=object)

    for i, region in enumerate(REGIONS):
        r = results[region]
        exc = r["conditional_exceedance"]
        thresholds = r["thresholds"]
        envelope = r["threshold_envelope"]
        sig_results = r["sig_results"]
        significant_key = r["significant_key"]
        probs = r["regional_probs"]

        if exc is None or thresholds is None or envelope is None:
            raise RuntimeError(
                f"{region}: threshold-exceedance products were not returned by process_region()."
            )

        q_region = exc["quantile"].to_numpy(dtype=float)
        if q_region.shape != quantiles.shape or not np.allclose(q_region, quantiles):
            raise ValueError(
                f"{region}: quantile grid differs from {REGIONS[0]}: {q_region} vs {quantiles}"
            )

        threshold_days[i, :] = _as_discrete_day_counts(
            exc["threshold_days"].to_numpy(),
            label=f"{region} threshold_days",
        )
        era5_exceedance[i, :] = exc["era5_exceedance"].to_numpy(dtype=float)
        threshold_labels[i, :] = exc["threshold_label"].astype(str).to_numpy()

        if "era5_cdf_at_threshold" in thresholds.columns:
            era5_cdf_at_threshold[i, :] = thresholds[
                "era5_cdf_at_threshold"
            ].to_numpy(dtype=float)

        for j, model in enumerate(model_names):
            if model not in exc.columns:
                raise KeyError(
                    f"{region}: {model!r} missing from conditional-exceedance table; "
                    f"available columns={list(exc.columns)}"
                )
            relative[i, j, :] = exc[model].to_numpy(dtype=float)
            n_valid_years[i, j] = int(
                probs[model].dropna(axis=0, how="any").shape[0]
            )

            if model != reference_name:
                s = sig_results[model]
                cvm_pvalue[i, j] = float(s.get("pvalue", np.nan))
                cvm_statistic[i, j] = float(s.get("statistic", np.nan))
                cvm_significant[i, j] = int(
                    bool(s.get(significant_key, s.get("significant", False)))
                )

        env_low[i, :] = np.asarray(envelope["low"], dtype=float)
        env_high[i, :] = np.asarray(envelope["high"], dtype=float)
        env_median[i, :] = np.asarray(envelope["median"], dtype=float)
        env_n_years[i] = int(envelope["n_years"])

    out = xr.Dataset(
        {
            "relative_exceedance": (
                ("region", "model", "threshold"),
                relative,
            ),
            "threshold_days": (("region", "threshold"), threshold_days),
            "threshold_label": (
                ("region", "threshold"),
                threshold_labels.astype(str),
            ),
            "era5_exceedance_probability": (
                ("region", "threshold"),
                era5_exceedance,
            ),
            "era5_cdf_at_threshold": (
                ("region", "threshold"),
                era5_cdf_at_threshold,
            ),
            "era5_envelope_low": (("region", "threshold"), env_low),
            "era5_envelope_high": (("region", "threshold"), env_high),
            "era5_envelope_median": (("region", "threshold"), env_median),
            "era5_envelope_n_years": ("region", env_n_years),
            "cvm_pvalue": (("region", "model"), cvm_pvalue),
            "cvm_statistic": (("region", "model"), cvm_statistic),
            "cvm_significant": (("region", "model"), cvm_significant),
            "n_valid_years": (("region", "model"), n_valid_years),
        },
        coords={
            "region": np.asarray(REGIONS, dtype=str),
            "model": np.asarray(model_names, dtype=str),
            "threshold": np.arange(nq, dtype=np.int16),
            "quantile": ("threshold", quantiles),
        },
    )

    out.attrs.update(
        {
            "description": (
                "Figure-ready conditional exceedance of ERA5-derived heatwave-duration "
                "thresholds for Polar, Extratropical, and Tropical land regions."
            ),
            "figure": "Duration_PerGrid_byGroup_summer.jpg",
            "diagnostic": "conditional heatwave-duration threshold exceedance",
            "relative_difference_definition": (
                "100 * [P_model(D>=d_q) - P_ERA5(D>=d_q)] / P_ERA5(D>=d_q)"
            ),
            "threshold_definition": (
                "d_q is the first discrete duration bin at which the ERA5 mean CDF "
                "reaches or exceeds quantile q"
            ),
            "season_mode": str(mod.season_mode),
            "reference_name": reference_name,
            "minimum_heatwave_duration_days": int(mod.min_duration),
            "quantiles": ",".join(f"{q:g}" for q in quantiles),
            "n_bootstrap": int(args.n_bootstrap),
            "confidence_level": float(args.ci),
            "sample_era5_with_replacement": str(
                bool(mod.sample_era5_with_replacement)
            ),
            "cvm_significance_level": float(mod.alpha_sig),
            "cvm_significant_key": str(results[REGIONS[0]]["significant_key"]),
            **release_attrs(preparation_script=Path(__file__).name, source_files=[analysis_script]),
        }
    )

    out["relative_exceedance"].attrs.update(
        {
            "long_name": "Relative exceedance difference from ERA5",
            "units": "%",
        }
    )
    out["threshold_days"].attrs.update(
        {
            "long_name": "ERA5-derived discrete duration threshold",
            # Deliberately avoid CF ``units=days`` here. Xarray interprets that
            # as a timedelta on read, whereas this variable is a discrete day count.
            "unit_label": "days",
            "description": "Integer number of days in the discrete duration threshold",
        }
    )
    out["era5_exceedance_probability"].attrs.update(
        {
            "long_name": "ERA5 probability of duration at or above threshold",
            "units": "1",
        }
    )
    for name in ["era5_envelope_low", "era5_envelope_high", "era5_envelope_median"]:
        out[name].attrs["units"] = "%"

    write_netcdf(out, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
