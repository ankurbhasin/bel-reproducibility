#!/usr/bin/env python3
# BEL Minimal Reproducibility Bundle v0.1

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _require_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")


def _compute_deltas(df, group_cols, time_col='t_center_rel'):
    required = set(group_cols + [time_col, 'entropy_rate', 'attractor_strength'])
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df.sort_values(group_cols + [time_col], kind='stable').copy()
    df['dH_dt'] = df.groupby(group_cols)['entropy_rate'].diff()
    df['dC_dt'] = df.groupby(group_cols)['attractor_strength'].diff()
    return df.dropna(subset=['dH_dt', 'dC_dt']).copy()


def _safe_fit_line(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]

    if len(x) < 2:
        return None

    if np.std(x) < 1e-12 or np.std(y) < 1e-12:
        return None

    try:
        slope, intercept = np.polyfit(x, y, 1)
    except Exception:
        return None

    return float(slope), float(intercept)


def save_gw_static(results_dir, out_dir):
    path = results_dir / 'matched_10x10' / 'event_metrics_matched_with_residual.csv'
    _require_file(path)

    df = pd.read_csv(path)

    required = {'regime', 'attractor_strength', 'entropy_rate'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {path}: {sorted(missing)}")

    fig, ax = plt.subplots(figsize=(7, 5))

    for regime, sub in df.groupby('regime'):
        sub = sub.dropna(subset=['attractor_strength', 'entropy_rate']).copy()
        if sub.empty:
            continue

        ax.scatter(
            sub['attractor_strength'],
            sub['entropy_rate'],
            alpha=0.6,
            s=18,
            label=regime
        )

        x = sub['attractor_strength'].to_numpy()
        y = sub['entropy_rate'].to_numpy()
        fit = _safe_fit_line(x, y)
        if fit is not None:
            slope, intercept = fit
            xx = np.linspace(x.min(), x.max(), 100)
            ax.plot(xx, slope * xx + intercept, linewidth=1.8)

    ax.set_xlabel(r'Attractor strength $\mathcal{C}$')
    ax.set_ylabel(r'Entropy rate $h$')
    ax.set_title('GW static entropy–confinement relation')
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out_dir / 'gw_static_bel_scatter.png', dpi=220)
    plt.close(fig)


def save_dynamic(results_dir, csv_name, group_cols, title, out_png, out_dir, null_json=None):
    csv_path = results_dir / csv_name
    _require_file(csv_path)

    df = pd.read_csv(csv_path)
    work = _compute_deltas(df, group_cols)

    if work.empty:
        raise ValueError(f"No valid delta rows available after processing {csv_path}")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(work['dC_dt'], work['dH_dt'], alpha=0.14, s=8)

    x = work['dC_dt'].to_numpy()
    y = work['dH_dt'].to_numpy()
    fit = _safe_fit_line(x, y)
    if fit is not None:
        slope, intercept = fit
        xx = np.linspace(x.min(), x.max(), 200)
        ax.plot(xx, slope * xx + intercept, linewidth=2.0)

    full_title = title
    if null_json:
        null_json = Path(null_json)
        _require_file(null_json)
        d = json.loads(null_json.read_text())
        obs_r = d.get('observed_global', {}).get('pearson_r', np.nan)
        null_r_mean = d.get('null_global', {}).get('pearson_r_mean', np.nan)
        if np.isfinite(obs_r) and np.isfinite(null_r_mean):
            full_title += f"\nobs r={obs_r:.3f}, null mean={null_r_mean:.3f}"

    ax.set_title(full_title)
    ax.set_xlabel(r'$d\mathcal{C}/dt$')
    ax.set_ylabel(r'$dh/dt$')
    fig.tight_layout()
    fig.savefig(out_dir / out_png, dpi=220)
    plt.close(fig)


def save_null_hist(reps_csv, summary_json, title, out_png, out_dir):
    reps_csv = Path(reps_csv)
    summary_json = Path(summary_json)

    _require_file(reps_csv)
    _require_file(summary_json)

    df = pd.read_csv(reps_csv)
    d = json.loads(summary_json.read_text())

    if 'pearson_r' not in df.columns:
        raise ValueError(f"Missing 'pearson_r' column in {reps_csv}")

    obs_r = d.get('observed_global', {}).get('pearson_r', np.nan)
    vals = pd.to_numeric(df['pearson_r'], errors='coerce').dropna()

    if vals.empty:
        raise ValueError(f"No valid pearson_r values found in {reps_csv}")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(vals, bins=40, label='null')

    if np.isfinite(obs_r):
        ax.axvline(
            obs_r,
            linestyle='--',
            linewidth=2.0,
            label=f'observed = {obs_r:.3f}'
        )

    ax.set_xlabel('Null Pearson r')
    ax.set_ylabel('Count')
    ax.set_title(title)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out_dir / out_png, dpi=220)
    plt.close(fig)


def main(results_dir, gw_null_json, gw_null_reps, eeg_null_json, eeg_null_reps, out_dir):
    results_dir = Path(results_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    save_gw_static(results_dir, out_dir)

    save_dynamic(
        results_dir,
        'gw_event_centered_local_metrics_10x10.csv',
        ['event_id', 'detector'],
        'GW dynamical BEL',
        'gw_dynamical_bel_scatter.png',
        out_dir,
        gw_null_json
    )

    save_null_hist(
        gw_null_reps,
        gw_null_json,
        'GW dynamical BEL independent-shuffle null',
        'gw_dynamical_bel_null_hist.png',
        out_dir
    )

    save_dynamic(
        results_dir,
        'eeg_dynamical_bel_windows.csv',
        ['subject_id', 'acq'],
        'EEG dynamical BEL',
        'eeg_dynamical_bel_scatter.png',
        out_dir,
        eeg_null_json
    )

    save_null_hist(
        eeg_null_reps,
        eeg_null_json,
        'EEG dynamical BEL independent-shuffle null',
        'eeg_dynamical_bel_null_hist.png',
        out_dir
    )

    print(f'[OK] Wrote figures to {out_dir}')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--results-dir', default='results')
    p.add_argument('--gw-null-json', required=True)
    p.add_argument('--gw-null-reps', required=True)
    p.add_argument('--eeg-null-json', required=True)
    p.add_argument('--eeg-null-reps', required=True)
    p.add_argument('--out-dir', required=True)
    a = p.parse_args()

    main(
        a.results_dir,
        a.gw_null_json,
        a.gw_null_reps,
        a.eeg_null_json,
        a.eeg_null_reps,
        a.out_dir
    )