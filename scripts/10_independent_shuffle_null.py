#!/usr/bin/env python3
# BEL Minimal Reproducibility Bundle v0.1

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def compute_deltas(df: pd.DataFrame, group_cols, time_col, h_col, c_col) -> pd.DataFrame:
    df = df.sort_values(group_cols + [time_col], kind='stable').copy()
    df['dH_dt'] = df.groupby(group_cols)[h_col].diff()
    df['dC_dt'] = df.groupby(group_cols)[c_col].diff()
    return df.dropna(subset=['dH_dt', 'dC_dt']).copy()


def fit_line(x: np.ndarray, y: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    n = len(x)
    if n < 3:
        return {'n': int(n), 'pearson_r': np.nan, 'slope': np.nan, 'intercept': np.nan, 'r_squared': np.nan}
    x_std = float(np.std(x))
    y_std = float(np.std(y))
    if x_std < 1e-12 or y_std < 1e-12:
        return {'n': int(n), 'pearson_r': np.nan, 'slope': np.nan, 'intercept': float(np.mean(y)), 'r_squared': np.nan}
    try:
        r = float(np.corrcoef(x, y)[0, 1])
    except Exception:
        r = np.nan
    try:
        slope, intercept = np.polyfit(x, y, 1)
        yhat = slope * x + intercept
        ss_res = float(np.sum((y - yhat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = np.nan if ss_tot <= 1e-12 else 1.0 - ss_res / ss_tot
    except Exception:
        slope = np.nan
        intercept = float(np.mean(y))
        r2 = np.nan
    return {
        'n': int(n),
        'pearson_r': float(r) if np.isfinite(r) else np.nan,
        'slope': float(slope) if np.isfinite(slope) else np.nan,
        'intercept': float(intercept) if np.isfinite(intercept) else np.nan,
        'r_squared': float(r2) if np.isfinite(r2) else np.nan,
    }


def independently_shuffled_copy(df: pd.DataFrame, group_cols, time_col, h_col, c_col, rng) -> pd.DataFrame:
    pieces = []
    for _, sub in df.groupby(group_cols, sort=False):
        sub = sub.sort_values(time_col, kind='stable').copy()
        idx_h = np.arange(len(sub))
        idx_c = np.arange(len(sub))
        rng.shuffle(idx_h)
        rng.shuffle(idx_c)
        shuffled = sub.copy()
        shuffled[h_col] = sub[h_col].to_numpy()[idx_h]
        shuffled[c_col] = sub[c_col].to_numpy()[idx_c]
        pieces.append(shuffled)
    return pd.concat(pieces, ignore_index=True)


def main(in_csv, group_cols, time_col, h_col, c_col, out_json, out_null_csv, out_groupwise_csv, n_perm, seed):
    df = pd.read_csv(in_csv)
    req = set(group_cols + [time_col, h_col, c_col])
    missing = req - set(df.columns)
    if missing:
        raise ValueError(f'Missing required columns: {sorted(missing)}')

    rng = np.random.default_rng(seed)
    obs = compute_deltas(df, group_cols, time_col, h_col, c_col)
    obs_global = fit_line(obs['dC_dt'].to_numpy(), obs['dH_dt'].to_numpy())

    group_rows = []
    for key, sub in obs.groupby(group_cols, sort=False):
        if not isinstance(key, tuple):
            key = (key,)
        row = {col: val for col, val in zip(group_cols, key)}
        row.update(fit_line(sub['dC_dt'].to_numpy(), sub['dH_dt'].to_numpy()))
        group_rows.append(row)
    obs_groupwise = pd.DataFrame(group_rows)

    null_rows = []
    for rep in range(n_perm):
        shuf = independently_shuffled_copy(df, group_cols, time_col, h_col, c_col, rng)
        work = compute_deltas(shuf, group_cols, time_col, h_col, c_col)
        fit = fit_line(work['dC_dt'].to_numpy(), work['dH_dt'].to_numpy())
        fit['rep'] = rep
        null_rows.append(fit)
    null_df = pd.DataFrame(null_rows)

    valid_r = null_df['pearson_r'].dropna()
    valid_s = null_df['slope'].dropna()

    summary = {
        'observed_global': obs_global,
        'null_global': {
            'pearson_r_mean': float(null_df['pearson_r'].mean(skipna=True)),
            'pearson_r_std': float(null_df['pearson_r'].std(ddof=1, skipna=True)),
            'slope_mean': float(null_df['slope'].mean(skipna=True)),
            'slope_std': float(null_df['slope'].std(ddof=1, skipna=True)),
            'r_squared_mean': float(null_df['r_squared'].mean(skipna=True)),
            'r_squared_std': float(null_df['r_squared'].std(ddof=1, skipna=True)),
        },
        'p_values': {
            'pearson_r_more_negative_than_null': float((valid_r <= obs_global['pearson_r']).mean()) if len(valid_r) else np.nan,
            'slope_more_negative_than_null': float((valid_s <= obs_global['slope']).mean()) if len(valid_s) else np.nan,
        },
        'n_perm': int(n_perm),
        'seed': int(seed),
        'group_cols': group_cols,
        'time_col': time_col,
        'h_col': h_col,
        'c_col': c_col,
        'null_type': 'independent_shuffle_within_group',
    }

    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    obs_groupwise.to_csv(out_groupwise_csv, index=False)
    null_df.to_csv(out_null_csv, index=False)
    with open(out_json, 'w') as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--in-csv', required=True)
    p.add_argument('--group-cols', nargs='+', required=True)
    p.add_argument('--time-col', required=True)
    p.add_argument('--h-col', required=True)
    p.add_argument('--c-col', required=True)
    p.add_argument('--out-json', required=True)
    p.add_argument('--out-null-csv', required=True)
    p.add_argument('--out-groupwise-csv', required=True)
    p.add_argument('--n-perm', type=int, default=2000)
    p.add_argument('--seed', type=int, default=42)
    a = p.parse_args()
    main(a.in_csv, a.group_cols, a.time_col, a.h_col, a.c_col, a.out_json, a.out_null_csv, a.out_groupwise_csv, a.n_perm, a.seed)
