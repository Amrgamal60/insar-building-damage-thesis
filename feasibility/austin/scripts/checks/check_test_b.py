"""Synthetic-only independent PPML/CRV1 checks and realistic timing."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
import importlib.util
import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.sandwich_covariance import cov_cluster

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from test_b import fit_panel, null_test


def panel(cells, quarters, seed, beta=-.35, overdispersed=False, sparse=False):
    rng = np.random.default_rng(seed)
    c, q = np.indices((cells, quarters))
    v = rng.normal(size=(cells, quarters)) + .7*rng.normal(size=(cells, 1)) + .4*np.sin(q/3)
    n = rng.integers(15, 60, (cells, quarters))
    alpha = rng.normal(0, .45, (cells, 1))
    lograte = (-4.5 if sparse else -2.4) + beta*v + alpha + .25*np.cos(q/2)
    mu = n*np.exp(lograte)
    rate = mu*rng.gamma(2, .5, mu.shape) if overdispersed else mu
    y = rng.poisson(rate)
    return pd.DataFrame(dict(cell=c.ravel(), quarter=q.ravel(), v=v.ravel(),
                             n=n.ravel(), y=y.ravel(), block=(c//8).ravel()))


def compare(d):
    a, ix, model = fit_panel(d)
    u = d.iloc[ix]
    b = smf.glm('y ~ v + C(cell) + C(quarter)', data=u,
                offset=np.log(u.n), family=sm.families.Poisson()).fit(maxiter=100, tol=1e-12)
    cov = cov_cluster(b, u.block, use_correction=True)
    j = b.model.exog_names.index('v')
    beta, se = float(b.params['v']), float(np.sqrt(cov[j, j]))
    db, ds = abs(a['beta']-beta), abs(a['clustered_se']-se)
    K, N, G = b.model.exog.shape[1], len(u), u.block.nunique()
    result = dict(pyfixest=a, statsmodels_beta=beta, statsmodels_clustered_se=se,
                  abs_coefficient_difference=db, abs_se_difference=ds,
                  coefficient_tolerance=1e-7, se_tolerance=1e-7,
                  N=N, K=K, G=int(G), correction_factor=float(G/(G-1)*(N-1)/(N-K)))
    assert db <= 1e-7 and ds <= 1e-7, result
    return result


def main():
    result = {'synthetic_only': True, 'beta_true': -.35, 'agreement': []}
    for seed in [431, 432]:
        d = panel(80, 12, seed, overdispersed=seed==432)
        # Exercise separation counts, including an all-zero quarter.
        if seed == 432:
            d.loc[d.cell < 3, 'y'] = 0
            d.loc[d.quarter == 11, 'y'] = 0
        result['agreement'].append(compare(d))
    d = panel(3000, 28, 433, overdispersed=True, sparse=True)
    t0 = time.perf_counter()
    fit, _, _ = fit_panel(d)
    elapsed = time.perf_counter()-t0
    recovery = abs(fit['beta']+.35)
    assert recovery < .05 and recovery < 4*fit['clustered_se'], fit
    result['realistic'] = dict(fit=fit, elapsed_seconds=elapsed,
                               projected_999_refits_seconds=999*elapsed,
                               beta_absolute_error=recovery,
                               synthetic_distribution='Gamma-Poisson, shape=2, mean exposure*exp(FEs+beta*v)')
    small = panel(48, 8, 434)
    axesq, axesc = np.arange(8), np.arange(48)
    original = small.pivot(index='quarter', columns='cell', values='v').to_numpy()
    fields = [original, original[:, np.random.default_rng(435).permutation(48)]]
    out = null_test(small, fields, axesq, axesc, expected_draws=2)
    assert out['draws'][0]['beta'] == out['observed']['beta']
    assert out['p_B'] == (1+out['exceedances'])/3
    result['null_smoke'] = dict(draws=2, p_B=out['p_B'], identity_draw_exact=True)
    path = Path(__file__).with_name('test_b_results.json')
    path.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
