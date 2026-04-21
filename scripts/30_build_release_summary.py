#!/usr/bin/env python3
# BEL Minimal Reproducibility Bundle v0.1

import argparse
import json
from pathlib import Path

import pandas as pd


def main(results_dir, gw_null_json, eeg_null_json, out_json, out_md):
    results_dir = Path(results_dir)
    gw_null = json.loads(Path(gw_null_json).read_text())
    eeg_null = json.loads(Path(eeg_null_json).read_text())

    out = {
        'gw_dynamical': gw_null,
        'eeg_dynamical': eeg_null,
    }

    cross_path = results_dir / 'cross_resolution' / 'gw_cross_resolution_dynamical_bel_summary.csv'
    if cross_path.exists():
        out['gw_cross_resolution'] = pd.read_csv(cross_path).to_dict(orient='records')

    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, 'w') as f:
        json.dump(out, f, indent=2)

    lines = []
    lines.append('# BEL release summary')
    lines.append('')
    lines.append('## GW dynamical BEL')
    lines.append(f"- observed r: {gw_null['observed_global']['pearson_r']:.6f}")
    lines.append(f"- observed slope: {gw_null['observed_global']['slope']:.6f}")
    lines.append(f"- null mean r: {gw_null['null_global']['pearson_r_mean']:.6f}")
    lines.append(f"- p(r more negative than null): {gw_null['p_values']['pearson_r_more_negative_than_null']}")
    lines.append('')
    lines.append('## EEG dynamical BEL')
    lines.append(f"- observed r: {eeg_null['observed_global']['pearson_r']:.6f}")
    lines.append(f"- observed slope: {eeg_null['observed_global']['slope']:.6f}")
    lines.append(f"- null mean r: {eeg_null['null_global']['pearson_r_mean']:.6f}")
    lines.append(f"- p(r more negative than null): {eeg_null['p_values']['pearson_r_more_negative_than_null']}")
    lines.append('')
    if cross_path.exists():
        df = pd.read_csv(cross_path)
        lines.append('## GW cross-resolution')
        lines.append('')
        lines.append(df.to_markdown(index=False))
        lines.append('')
    Path(out_md).write_text('\n'.join(lines))
    print(f'[OK] Wrote {out_json}')
    print(f'[OK] Wrote {out_md}')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--results-dir', default='results')
    p.add_argument('--gw-null-json', required=True)
    p.add_argument('--eeg-null-json', required=True)
    p.add_argument('--out-json', required=True)
    p.add_argument('--out-md', required=True)
    a = p.parse_args()
    main(a.results_dir, a.gw_null_json, a.eeg_null_json, a.out_json, a.out_md)
