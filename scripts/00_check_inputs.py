#!/usr/bin/env python3
# BEL Minimal Reproducibility Bundle v0.1

import argparse
from pathlib import Path

REQUIRED = [
    Path('matched_10x10/event_metrics_matched_with_residual.csv'),
    Path('gw_event_centered_local_metrics_10x10.csv'),
    Path('eeg_dynamical_bel_windows.csv'),
]
OPTIONAL = [
    Path('cross_resolution/gw_cross_resolution_dynamical_bel_summary.csv'),
]


def main(results_dir: str):
    root = Path(results_dir)
    missing = []
    for rel in REQUIRED:
        p = root / rel
        if not p.exists():
            missing.append(str(p))
    if missing:
        print('[ERROR] Missing required inputs:')
        for m in missing:
            print(' -', m)
        raise SystemExit(1)

    print('[OK] All required inputs found.')
    for rel in OPTIONAL:
        p = root / rel
        print(f"[INFO] Optional {'present' if p.exists() else 'missing'}: {p}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-dir', default='results')
    args = parser.parse_args()
    main(args.results_dir)
