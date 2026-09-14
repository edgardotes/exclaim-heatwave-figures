# v1.0.0 release checklist

Use this checklist in the working repository that already contains the five real `data/*.nc` files and five reference figures.

## 1. Apply the cleaned repository files

Copy the v1.0.0 release files over the working repository. Do not delete the existing scientific files in `data/` or `figures/`.

## 2. Add release metadata to the existing compact NetCDFs

```bash
python prepare_data/add_release_metadata.py
```

This changes metadata only; it does not recompute any scientific quantity. It also removes legacy machine-specific source paths from known provenance attributes.

## 3. Reproduce the reference figures

```bash
conda env create -f environment.yml
conda activate exclaim-heatwave-figures
python run_all_figures.py
```

## 4. Validate v1.0.0

```bash
python validate_release.py
```

The validator checks the expected repository files, five compact NetCDF filenames, manuscript figure associations, release version metadata, and known machine-specific path leakage.

## 5. Remove transient Python files

```bash
find . -type d -name '__pycache__' -prune -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
```

## 6. Commit and tag

```bash
git add .
git commit -m "Release v1.0.0"
git tag -a v1.0.0 -m "Initial figure-reproduction release"
git push origin main
git push origin v1.0.0
```

Create a GitHub Release from tag `v1.0.0` and paste the contents of `RELEASE_NOTES_v1.0.0.md` into the release notes.

## 7. Zenodo

After the GitHub release is archived by Zenodo, use the **version-specific DOI** for v1.0.0 in the manuscript/code-availability statement. Do not modify the archived v1.0.0 tag merely to add the DOI; the DOI can be added to the development branch or a later release if desired.
