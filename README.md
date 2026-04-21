# BEL Minimal Reproducibility Pipeline

This repository reproduces the **empirical results** for the Bhasin Entropy–Confinement Law (BEL) from precomputed coarse-grained dynamical metrics.

It is designed as a **clean, minimal, audit-friendly reproducibility layer** for the published results.

---

## Data (Required)

Download the dataset from Zenodo:

https://doi.org/10.5281/zenodo.19686843

Place files under:

results/
  matched_10x10/
    event_metrics_matched_with_residual.csv
  gw_event_centered_local_metrics_10x10.csv
  eeg_dynamical_bel_windows.csv

Optional:

results/
  cross_resolution/
    gw_cross_resolution_dynamical_bel_summary.csv

---

## Setup

pip install -r requirements.txt

---

## Run Pipeline

bash run_release_pipeline.sh

Outputs will be generated in:

release_outputs/

---

## What This Reproduces

- Gravitational-wave (GW) dynamical BEL
- EEG dynamical BEL
- Independent-shuffle null tests
- Publication figures
- Summary statistics
- Cross-resolution robustness (if data provided)

---

## Interpretation

- Static BEL is partly structural (occupancy-driven)
- Dynamical BEL is nontrivial and survives strong null tests
- Cross-resolution results show robustness across coarse-graining scales

---

## Design Philosophy

This repository:
- DOES reproduce all paper-level results
- DOES NOT include raw signal processing pipelines
- DOES NOT include raw GW or EEG data

This keeps the release:
- Small
- Transparent
- Easy to audit
- IP-safe

---

## License

Code: MIT License  
Data: CC BY 4.0 (via Zenodo)

---

## Citation

If you use this work:

Bhasin, A. (2026).  
Data for: The Bhasin Entropy–Confinement Law (BEL).  
Zenodo. https://doi.org/10.5281/zenodo.19686843
