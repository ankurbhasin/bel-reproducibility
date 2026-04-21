#!/usr/bin/env bash
# BEL Minimal Reproducibility Bundle v0.1

set -euo pipefail

python scripts/00_check_inputs.py --results-dir results

mkdir -p release_outputs/nulls release_outputs/figures release_outputs/summary

python scripts/10_independent_shuffle_null.py \
  --in-csv results/gw_event_centered_local_metrics_10x10.csv \
  --group-cols event_id detector \
  --time-col t_center_rel \
  --h-col entropy_rate \
  --c-col attractor_strength \
  --out-json release_outputs/nulls/gw_independent_shuffle_null.json \
  --out-null-csv release_outputs/nulls/gw_independent_shuffle_null_reps.csv \
  --out-groupwise-csv release_outputs/nulls/gw_independent_shuffle_groupwise.csv \
  --n-perm 2000 \
  --seed 42

python scripts/10_independent_shuffle_null.py \
  --in-csv results/eeg_dynamical_bel_windows.csv \
  --group-cols subject_id acq \
  --time-col t_center_rel \
  --h-col entropy_rate \
  --c-col attractor_strength \
  --out-json release_outputs/nulls/eeg_independent_shuffle_null.json \
  --out-null-csv release_outputs/nulls/eeg_independent_shuffle_null_reps.csv \
  --out-groupwise-csv release_outputs/nulls/eeg_independent_shuffle_groupwise.csv \
  --n-perm 2000 \
  --seed 42

python scripts/20_make_figures.py \
  --results-dir results \
  --gw-null-json release_outputs/nulls/gw_independent_shuffle_null.json \
  --gw-null-reps release_outputs/nulls/gw_independent_shuffle_null_reps.csv \
  --eeg-null-json release_outputs/nulls/eeg_independent_shuffle_null.json \
  --eeg-null-reps release_outputs/nulls/eeg_independent_shuffle_null_reps.csv \
  --out-dir release_outputs/figures

python scripts/30_build_release_summary.py \
  --results-dir results \
  --gw-null-json release_outputs/nulls/gw_independent_shuffle_null.json \
  --eeg-null-json release_outputs/nulls/eeg_independent_shuffle_null.json \
  --out-json release_outputs/summary/bel_release_summary.json \
  --out-md release_outputs/summary/bel_release_summary.md

echo "[OK] Release pipeline completed. See release_outputs/."
