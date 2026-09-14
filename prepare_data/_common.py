from __future__ import annotations

from pathlib import Path
import xarray as xr

PACKAGE_NAME = "exclaim-heatwave-figures"
PACKAGE_VERSION = "1.0.0"
PACKAGE_AUTHOR = "Edgar Dolores-Tesillos"
PACKAGE_LICENSE = "MIT (software)"
REPRODUCIBILITY_SCOPE = (
    "Processed figure-ready data; full raw ERA5/ICON preprocessing and HPC "
    "analysis workflow are outside this archive."
)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def release_attrs(*, preparation_script: str, source_files: list[Path] | None = None) -> dict[str, str]:
    attrs = {
        "reproduction_package": PACKAGE_NAME,
        "reproduction_package_version": PACKAGE_VERSION,
        "package_author": PACKAGE_AUTHOR,
        "software_license": PACKAGE_LICENSE,
        "preparation_script": preparation_script,
        "reproducibility_scope": REPRODUCIBILITY_SCOPE,
    }
    if source_files:
        attrs["source_files"] = ", ".join(Path(p).name for p in source_files)
    return attrs


def copy_global_attrs(source: xr.Dataset, target: xr.Dataset, **extra) -> xr.Dataset:
    target.attrs.update(source.attrs)
    target.attrs.update(extra)
    return target


def write_netcdf(ds: xr.Dataset, path: Path) -> None:
    """Write a compact NetCDF with lossless compression when netCDF4 is available."""
    ensure_parent(path)
    encoding = {}
    for name, da in ds.data_vars.items():
        if da.dtype.kind in "biufc":
            encoding[name] = {"zlib": True, "complevel": 4, "shuffle": True}
    try:
        import netCDF4  # noqa: F401
        ds.to_netcdf(path, engine="netcdf4", encoding=encoding)
    except Exception:
        ds.to_netcdf(path)


def require_vars(ds: xr.Dataset, names: list[str], source: Path) -> None:
    missing = [name for name in names if name not in ds]
    if missing:
        raise KeyError(
            f"Missing variables in {source}: {missing}. Available: {list(ds.data_vars)}"
        )
