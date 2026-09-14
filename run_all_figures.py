#!/usr/bin/env python3
"""Reproduce all five main manuscript figures from data/*.nc."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SCRIPTS = [
    "plot_fig01_heatwave_days.py",
    "plot_fig02_duration_threshold_exceedance.py",
    "plot_fig03_sm_temperature.py",
    "plot_fig04_termination_wetdry.py",
    "plot_fig05_block_heat_cooccurrence.py",
]


def main():
    for name in SCRIPTS:
        path = ROOT / "plotting" / name
        print(f"\n=== {name} ===", flush=True)
        subprocess.run([sys.executable, str(path)], cwd=ROOT, check=True)
    print(f"\nAll figures written to {ROOT / 'figures'}")


if __name__ == "__main__":
    main()
