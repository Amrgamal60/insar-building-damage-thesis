"""Synthetic-only checks of the frozen architecture; never hyperparameter search."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from deep_model import oof_scores, resample_series


def make_synthetic(n, signal, seed):
    rng = np.random.default_rng(seed)
    y = np.zeros(n, np.int64)
    y[np.arange(0, n, 51)] = 1
    # Independent synthetic parcels/blocks; no real geometry or features.
    block = np.arange(n)//510
    baseline = rng.normal(size=(n, 9)).astype(np.float32)
    baseline[:, 0] += .7*y
    latent = rng.normal(size=n).astype(np.float32) + (3*y if signal else 0)
    t = np.linspace(0, 1, 61, dtype=np.float32)
    series = latent[:, None]*t[None, :] + .2*rng.normal(size=(n,61)).astype(np.float32)
    series += .3*rng.normal(size=(n,1))*np.sin(4*np.pi*t)
    mask = rng.random((n,61)) >= .1
    mask[:, 0] = False  # left edge of the approved grid crosses the calendar window
    first = np.argmax(mask, axis=1)
    series -= series[np.arange(n), first, None]
    series[~mask] = 0.
    fold = np.full(n, -1)
    for k, (_, test) in enumerate(StratifiedGroupKFold(5, shuffle=True, random_state=42).split(baseline, y, block)):
        fold[test] = k
    return baseline, series, mask, y, block, fold


def metrics(scores, y, blocks):
    a = average_precision_score(y, scores['comparison'])
    b = average_precision_score(y, scores['series'])
    # Paired fixed-score block bootstrap diagnoses noise in the synthetic check;
    # this is NOT the plan's production refit bootstrap.
    rng = np.random.default_rng(909)
    members = [np.flatnonzero(blocks==v) for v in np.unique(blocks)]
    diffs = []
    for _ in range(300):
        ix = np.concatenate([members[j] for j in rng.integers(0, len(members), len(members))])
        diffs.append(average_precision_score(y[ix], scores['series'][ix])-
                     average_precision_score(y[ix], scores['comparison'][ix]))
    return dict(comparison_pr_auc=float(a), series_pr_auc=float(b), delta_pr_auc=float(b-a),
                paired_fixed_score_bootstrap_ci95=np.percentile(diffs,[2.5,97.5]).tolist(),
                paired_fixed_score_bootstrap_sd=float(np.std(diffs, ddof=1)))


def digest(scores):
    return {k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in scores.items()}


def check_resampler():
    # T=2025-01-01, a step at T-12d has two equidistant acquisitions.
    dates = np.array(['2022-01-01','2024-12-18','2024-12-22','2025-01-01'], dtype='datetime64[D]')
    s,m = resample_series(dates, [999,10,30,999], '2025-01-17')
    assert m.sum() == 1 and m[-1] and s[-1] == 0 and not m[0]
    # Add an earlier valid grid step: reference is 4; tie must choose 10, giving 6.
    dates = np.array(['2024-12-08','2024-12-18','2024-12-22','2025-01-01'], dtype='datetime64[D]')
    s,m = resample_series(dates, [4,10,30,999], '2025-01-17')
    assert m.sum() == 2 and s[-2] == 0 and s[-1] == 6
    # Nearest acquisition is missing: do not fill from a farther valid one.
    s,m = resample_series(np.array(['2024-12-19','2024-12-22'], dtype='datetime64[D]'),
                          [np.nan, 30], '2025-01-17')
    assert not m[-1] and s[-1] == 0
    return {'nearest_missing_masked':True, 'event_month_boundary_excluded':True, 'tie_earlier':True,
            'first_valid_reference':True, 'left_grid_boundary_masked':True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--realistic', action='store_true')
    args = ap.parse_args()
    if args.realistic:
        data = make_synthetic(300000, True, 608)
        t = time.perf_counter()
        scores, audit = oof_scores(*data, progress=True)
        elapsed = time.perf_counter()-t
        result = dict(synthetic_only=True, rows=300000, steps=61, baseline_features=9,
                      elapsed_seconds=elapsed, projected_99_full_paired_refits_seconds=99*elapsed,
                      score_sha256=digest(scores), folds=audit,
                      comparison_pr_auc=float(average_precision_score(data[3], scores['comparison'])),
                      series_pr_auc=float(average_precision_score(data[3], scores['series'])))
        label = 'deep_realistic'
    else:
        result = dict(synthetic_only=True, rows=30600, resampler=check_resampler())
        signal = make_synthetic(30600, True, 606)
        t = time.perf_counter()
        s1, audit = oof_scores(*signal, progress=True)
        result['planted_signal'] = metrics(s1, signal[3], signal[4])
        result['planted_signal']['elapsed_seconds'] = time.perf_counter()-t
        assert result['planted_signal']['paired_fixed_score_bootstrap_ci95'][0] > 0
        s2, _ = oof_scores(*signal, progress=True)
        same = {k:bool(np.array_equal(s1[k],s2[k])) for k in s1}
        assert all(same.values()), same
        result['reproducibility'] = dict(exact_array_equality=same, score_sha256=digest(s1))
        no_signal = make_synthetic(30600, False, 607)
        s3, _ = oof_scores(*no_signal, progress=True)
        result['no_signal'] = metrics(s3, no_signal[3], no_signal[4])
        r = result['no_signal']
        # Explicit predeclared pass: any positive gain is at most 3 paired block SE.
        assert r['delta_pr_auc'] <= 3*r['paired_fixed_score_bootstrap_sd'], r
        result['no_signal']['pass_rule'] = 'delta <= 3 paired fixed-score block bootstrap SD'
        result['folds_planted_signal'] = audit
        label = 'deep_behavior'
    (Path(__file__).parent/(label+'_results.json')).write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if not k.startswith('folds')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
