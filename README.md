# EXCLAIM heatwave figures

**Version 1.0.0**

Figure-reproduction code and compact processed data for five main manuscript figures comparing heatwave characteristics and their dynamical and land-atmosphere relationships in ERA5 and four ICON configurations.

This repository is intentionally a **figure-level reproducibility archive**. The plotting scripts operate only on the processed NetCDF files in `data/`; they do not require the original daily ERA5/ICON fields, the event-detection pipeline, or access to the HPC analysis environment.

## Quick start

Create the environment from the repository root:

```bash
conda env create -f environment.yml
conda activate exclaim-heatwave-figures
```

Reproduce all five figures:

```bash
python run_all_figures.py
```

Outputs are written to `figures/` using the manuscript-facing filenames.

To validate the release contents and NetCDF metadata:

```bash
python validate_release.py
```

## Main figures

| Figure | Reproduction script | Processed input |
|---|---|---|
| `Heatwave_days_global_local_summer_MOV.jpg` | `plotting/plot_fig01_heatwave_days.py` | `data/fig01_heatwave_days.nc` |
| `Duration_PerGrid_byGroup_summer.jpg` | `plotting/plot_fig02_duration_threshold_exceedance.py` | `data/fig02_duration_threshold_exceedance.nc` |
| `corr_SoilTemp_LocalSummer_Global.jpg` | `plotting/plot_fig03_sm_temperature.py` | `data/fig03_sm_temperature.nc` |
| `heatwave_termination_wetdry_summer_lag1_regional_relative.png` | `plotting/plot_fig04_termination_wetdry.py` | `data/fig04_termination_wetdry.nc` |
| `Block_heat_cooccurrence_local_summer_global.jpg` | `plotting/plot_fig05_block_heat_cooccurrence.py` | `data/fig05_block_heat_cooccurrence.nc` |

### Figure 1 — heatwave days

The ERA5 panel shows mean local-summer heatwave days. The four ICON panels show ICON minus ERA5 differences, with the archived significance masks reproduced as stippling.

### Figure 2 — duration-threshold exceedance

The three panels show Polar, Extratropical, and Tropical land regions. For each ERA5-derived duration quantile threshold \(d_q\), the plotted quantity is

\[
100\,\frac{P_{\mathrm{model}}(D\ge d_q)-P_{\mathrm{ERA5}}(D\ge d_q)}
{P_{\mathrm{ERA5}}(D\ge d_q)}.
\]

The grey envelope represents the range expected from random ERA5 samples with the same record length as the ICON simulations. CvM results are retained in the compact NetCDF and used for the line-weight/annotation logic. `threshold_days` is treated explicitly as a discrete number of days; the plotting script also normalizes legacy nanosecond-encoded thresholds.

### Figure 3 — soil-moisture / temperature coupling

The ERA5 panel shows the local-summer soil-moisture/temperature correlation. The ICON panels show correlation differences relative to ERA5 with the archived significance masks.

### Figure 4 — post-heatwave wet/dry conditions

The top panels provide regional heatwave-frequency-bias context for Tropical Americas and East Asia. The lower panels show relative differences from ERA5 in dry- and wet-day occurrence one day after heatwave termination, together with ERA5 short-record uncertainty.

### Figure 5 — blocking–heatwave co-occurrence

The ERA5 panel shows \(P(\mathrm{blocking}\mid\mathrm{heatwave})\). The ICON panels show differences from ERA5 with archived significance masks; ERA5 blocking-frequency contours provide circulation context.

## Repository layout

```text
exclaim-heatwave-figures/
├── README.md
├── LICENSE
├── CITATION.cff
├── CHANGELOG.md
├── RELEASE_NOTES_v1.0.0.md
├── RELEASE_CHECKLIST.md
├── VERSION
├── environment.yml
├── run_all_figures.py
├── validate_release.py
├── data/
│   ├── README.md
│   ├── fig01_heatwave_days.nc
│   ├── fig02_duration_threshold_exceedance.nc
│   ├── fig03_sm_temperature.nc
│   ├── fig04_termination_wetdry.nc
│   └── fig05_block_heat_cooccurrence.nc
├── plotting/
│   ├── plot_fig01_heatwave_days.py
│   ├── plot_fig02_duration_threshold_exceedance.py
│   ├── plot_fig03_sm_temperature.py
│   ├── plot_fig04_termination_wetdry.py
│   └── plot_fig05_block_heat_cooccurrence.py
├── prepare_data/
│   ├── _common.py
│   ├── add_release_metadata.py
│   ├── prepare_fig01_heatwave_days.py
│   ├── prepare_fig02_duration_threshold_exceedance.py
│   ├── prepare_fig03_sm_temperature.py
│   ├── prepare_fig04_termination_wetdry.py
│   └── prepare_fig05_block_heat_cooccurrence.py
└── figures/
    ├── README.md
    └── <five reference figure files>
```

## Processed-data files

The five NetCDF files are deliberately compact. They contain only figure-ready derived quantities and closely related uncertainty/significance information needed to reproduce and interpret the manuscript figures.

The archive does **not** include the original daily ERA5 or ICON fields.

Each v1.0.0 NetCDF may include release-level provenance attributes such as:

```text
reproduction_package = "exclaim-heatwave-figures"
reproduction_package_version = "1.0.0"
package_author = "Edgar Dolores-Tesillos"
software_license = "MIT (software)"
figure = "<manuscript figure filename>"
preparation_script = "<preparation script>"
```

If the compact NetCDFs were produced before these release attributes were added, they can be updated **without recomputing the scientific analysis**:

```bash
python prepare_data/add_release_metadata.py
```

## Preparing the compact files from existing analysis outputs

The `prepare_data/` directory documents how existing derived analysis products were converted into the standardized public NetCDFs. These scripts are not required by readers who use the archived `data/*.nc` files.

The public release does not hard-code user- or HPC-specific paths. Source files are supplied explicitly.

### Figure 1

```bash
python prepare_data/prepare_fig01_heatwave_days.py \
  --input /path/to/hw_frequency_bias_Global_LocalSummer.nc
```

### Figure 2

```bash
python prepare_data/prepare_fig02_duration_threshold_exceedance.py \
  --analysis-script /path/to/plot_hw_duration_distribution_3panel.py
```

This is the only preparation step that reuses the full duration-analysis workflow because the ERA5-derived thresholds, short-record envelope, and CvM results are calculated there.

### Figure 3

```bash
python prepare_data/prepare_fig03_sm_temperature.py \
  --input /path/to/t_sm_coupling_bias_Global_LocalSummer_significance.nc
```

### Figure 4

```bash
python prepare_data/prepare_fig04_termination_wetdry.py \
  --csv-dir /path/to/derived/csvs \
  --context-nc /path/to/hw_frequency_bias_Global_LocalSummer.nc
```

The expected CSV basenames are:

```text
heatwave_termination_wetdry_summer_lag1_MAIN_TropicalAmericas_EastAsia_relative_to_ERA5.csv
heatwave_termination_wetdry_summer_lag1_MAIN_TropicalAmericas_EastAsia_ERA5_short_record_uncertainty.csv
```

The analysis boxes stored in the compact file are:

- Tropical Americas: 83°W–45°W, 15°S–10°N
- East Asia: 110°E–141°E, 35°N–55°N

### Figure 5

```bash
python prepare_data/prepare_fig05_block_heat_cooccurrence.py \
  --input /path/to/block_heat_cooccurrence_local_summer_global.nc
```

## Reproducibility boundary

The processed NetCDF files in `data/` are the public reproducibility boundary of this repository. They contain plotted climatologies and biases, threshold diagnostics, uncertainty intervals, significance masks and p-values, and figure-context fields.

The following are outside this archive:

- original multi-year daily ERA5 and ICON files;
- complete heatwave-detection and blocking-detection workflows;
- remapping and other HPC preprocessing;
- intermediate diagnostics that are not required for the five main figures.

Accordingly, the appropriate availability statement is that this archive provides **the plotting scripts and processed data required to reproduce the main manuscript figures**, not the complete raw-data processing chain.

## Citation

Citation metadata are provided in `CITATION.cff`. For reproducibility, cite the **version-specific Zenodo DOI for v1.0.0** once the GitHub release has been archived by Zenodo, together with the associated manuscript.

The DOI is intentionally not hard-coded in this release candidate because it does not exist until Zenodo archives the GitHub release.

## License

The software in this repository is released under the MIT License; see `LICENSE`.

The repository does not redistribute the original third-party ERA5 or ICON source datasets. The software license does not alter or supersede any terms applying to those upstream data/model products.

## Release

This repository is prepared as **v1.0.0**, released on 2026-09-09. See `CHANGELOG.md` and `RELEASE_NOTES_v1.0.0.md`.
