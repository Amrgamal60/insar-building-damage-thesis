"""Austin Test B: PPML area-quarter panel (AUSTIN_PLAN §§8B, 9, 10).

Input rows have cell, quarter, y (nonnegative integer count), n (>0 exposure),
v (raw mm/year), block (2 km identifier); eligibility is established upstream.
Model: y ~ v | cell + quarter, offset log(n), pyfixest fepois, CRV1 by block.
Authors' choice, proposed by the script author: CRV1 includes full FE parameter
count, (N-1)/(N-K) * G/(G-1); normal 1.95996398454 Wald intervals. IWLS tol
1e-10, cap 100; FE tol 1e-10; singleton and FE-separated rows removed/reported.
Null refits must retain observed used rows; any additional separation fails the
run rather than silently changing the statistic's population or denominator.
No real data are accessed by importing this module or by its synthetic checks.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyfixest as pf
from scipy.stats import norm

COLUMNS = ['cell', 'quarter', 'y', 'n', 'v', 'block']


def fit_panel(panel: pd.DataFrame):
    """Return (JSON-safe report, used row positions, fitted pyfixest model)."""
    d = panel.loc[:, COLUMNS].copy().reset_index(drop=True)
    if d.isna().any().any():
        raise ValueError('Missing panel inputs: restrict rows per §8B before fitting')
    for c in ['y', 'n', 'v']:
        if not np.isfinite(d[c].to_numpy(dtype=float)).all():
            raise ValueError(f'Non-finite {c}')
    if (d.n <= 0).any() or (d.y < 0).any() or (d.y != np.floor(d.y)).any():
        raise ValueError('Exposure must be positive; counts must be nonnegative integers')
    if d.duplicated(['cell', 'quarter']).any():
        raise ValueError('Duplicate cell-quarter row')
    if d.groupby('cell').block.nunique().max() != 1:
        raise ValueError('A 250 m cell must belong to one 2 km block')
    d['_row_position'] = np.arange(len(d))
    d['_log_n'] = np.log(d.n)
    model = pf.fepois('y ~ v | cell + quarter', d, offset='_log_n',
                       vcov={'CRV1': 'block'},
                       ssc=pf.ssc(k_adj=True, k_fixef='full', G_adj=True, G_df='conventional'),
                       fixef_rm='singleton', separation_check=['fe'],
                       iwls_tol=1e-10, iwls_maxiter=100, fixef_tol=1e-10)
    if not model.convergence:
        raise RuntimeError('PPML did not converge')
    # Pinned pyfixest retains post-separation/singleton rows in _data.
    used = model._data['_row_position'].to_numpy(dtype=int)
    if len(used) != model._N:
        raise RuntimeError('Cannot identify exact estimation sample')
    u = d.iloc[used]
    beta, se = float(model.coef()['v']), float(model.se()['v'])
    if not np.isfinite([beta, se]).all() or se <= 0:
        raise RuntimeError('Unidentified or invalid velocity estimate')
    iqr = float(np.subtract(*np.percentile(u.v, [75, 25])))
    z = float(norm.ppf(.975))
    G = int(u.block.nunique())
    if G < 2:
        raise ValueError('At least two retained blocks required for CRV1')
    report = dict(beta=beta, clustered_se=se, velocity_iqr=iqr,
                  rate_ratio_iqr=float(np.exp(beta * iqr)),
                  rate_ratio_ci95=[float(np.exp((beta-z*se)*iqr)),
                                   float(np.exp((beta+z*se)*iqr))],
                  null_statistic=abs(beta), rows_input=len(d), rows_used=len(u),
                  rows_dropped=len(d)-len(u), cells_input=int(d.cell.nunique()),
                  cells_used=int(u.cell.nunique()),
                  cells_dropped=int(d.cell.nunique()-u.cell.nunique()),
                  quarters_input=int(d.quarter.nunique()), quarters_used=int(u.quarter.nunique()),
                  quarters_dropped=int(d.quarter.nunique()-u.quarter.nunique()), blocks_used=G,
                  all_zero_cells_input=int((d.groupby('cell').y.sum() == 0).sum()),
                  all_zero_quarters_input=int((d.groupby('quarter').y.sum() == 0).sum()),
                  correction='CRV1 full FE: G/(G-1) * (N-1)/(N-K)',
                  interval='normal Wald 1.959963984540054')
    return report, used, model


def null_test(panel, surrogate_fields, quarters, cells, expected_draws=999):
    """Refit for each (quarter, cell) field from NYC VariogramNull.draws.

    surrogate_fields is an iterable of arrays (or NYC (array, k) tuples).
    quarters and cells explicitly label its axes; no sorting is assumed.
    Nonfinite surrogate values on the observed estimation sample are errors.
    Failed fits are errors: no unsuccessful draws are removed or replaced.
    """
    observed, used, _ = fit_panel(panel)
    u = panel.iloc[used].reset_index(drop=True)
    qi = pd.Index(quarters).get_indexer(u.quarter)
    ci = pd.Index(cells).get_indexer(u.cell)
    if not pd.Index(quarters).is_unique or not pd.Index(cells).is_unique or (qi < 0).any() or (ci < 0).any():
        raise ValueError('Field axes must uniquely cover all used panel rows')
    draws = []
    for draw in surrogate_fields:
        field = draw[0] if isinstance(draw, tuple) else draw
        field = np.asarray(field)
        if field.shape != (len(quarters), len(cells)):
            raise ValueError('Surrogate field shape does not match labelled axes')
        s = u.copy()
        s['v'] = field[qi, ci]
        fit, ix, _ = fit_panel(s)
        if len(ix) != len(u):
            raise RuntimeError('Surrogate changed the estimation sample')
        draws.append(fit)
    if len(draws) != expected_draws or expected_draws < 1:
        raise ValueError(f'Expected {expected_draws} successful draws, got {len(draws)}')
    exceed = sum(d['null_statistic'] >= observed['null_statistic'] for d in draws)
    return dict(observed=observed, draws=draws, exceedances=exceed,
                p_B=(1+exceed)/(1+len(draws)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('panel', type=Path, help='Prepared, restricted panel CSV')
    ap.add_argument('output', type=Path)
    ap.add_argument('--surrogates', type=Path, help='NPZ: fields[draw,quarter,cell], quarters, cells')
    args = ap.parse_args()
    d = pd.read_csv(args.panel)
    if args.surrogates:
        with np.load(args.surrogates, allow_pickle=False) as f:
            result = null_test(d, f['fields'], f['quarters'], f['cells'])
    else:
        result, used, _ = fit_panel(d)
        result['used_row_positions'] = used.tolist()
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
