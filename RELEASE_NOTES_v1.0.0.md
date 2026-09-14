# v1.0.0 — Initial figure-reproduction release

This release contains the plotting code and processed figure-ready data needed to reproduce the five main manuscript figures.

The public plotting workflow is intentionally independent of the original HPC directory structure and does not require access to daily ERA5 or ICON fields.

## Main outputs

1. `Heatwave_days_global_local_summer_MOV.jpg`
2. `Duration_PerGrid_byGroup_summer.jpg`
3. `corr_SoilTemp_LocalSummer_Global.jpg`
4. `heatwave_termination_wetdry_summer_lag1_regional_relative.png`
5. `Block_heat_cooccurrence_local_summer_global.jpg`

## Important scope note

The archive provides figure-level reproducibility from compact processed NetCDF files. The full upstream raw-data preprocessing, heatwave detection, blocking detection, and HPC workflow are outside the scope of this release.
