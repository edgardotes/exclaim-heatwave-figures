# Changelog

All notable changes to this figure-reproduction package are documented here.

## [1.0.0] - 2026-09-09

Initial archival release.

### Included

- Five lightweight plotting scripts that reproduce the main manuscript figures from compact processed NetCDF files.
- Five preparation/export scripts that standardize previously computed analysis outputs into figure-ready NetCDF files.
- Correct conditional heatwave-duration threshold-exceedance diagnostic for Figure 2.
- Robust normalization of legacy duration-threshold values stored as nanoseconds back to discrete day counts.
- Reproduction environment, citation metadata, repository metadata, and release documentation.

### Reproducibility boundary

This release reproduces the manuscript figures from processed data. It does not distribute the complete raw ERA5/ICON analysis pipeline or the original multi-year model and reanalysis fields.
