"""Outcome-blind exploration: variogram match of candidate conditional nulls (no label read)."""
import sys, numpy as np
sys.path.insert(0, '/mnt/data/Master-projects/Alex/feasibility/alexandria_retest/scripts')
import retest_core as R
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from cpu_null import CPULowMemVariogramNull
c, f, _ = R.load_cells()
px = R.PixelField(f)
in241 = np.isin(px.cell, c.field_index.to_numpy())
xy241 = c[['x','y']].to_numpy(float); v241 = c[R.COL].to_numpy(float)
cl, obs = R.cell_variogram(v241, xy241); obs = obs[0]
fxy = f[['x_km','y_km']].to_numpy(float)
def run(name, mask, design, model, n=199):
    pv, pxy, pc = px.v[mask], px.xy[mask], px.cell[mask]
    X = design[pc]
    if model is None: fit = np.full(len(pv), pv.mean())
    else: fit = model.fit(X, pv).predict(X)
    res = pv - fit
    nl = CPULowMemVariogramNull(res[None,:], pxy, 100.0, kmax=1000, max_lag=16)
    rng = np.random.default_rng(2043)
    cells = []
    cnt = np.bincount(pc, minlength=len(f))
    for s, k in nl.draws(n, rng):
        full = fit + s[0]
        m = np.bincount(pc, weights=full, minlength=len(f)) / np.maximum(cnt, 1)
        cells.append(m[c.field_index.to_numpy()])
    cells = np.array(cells)
    g = cl.vario(cells); lo, med, hi = np.percentile(g, [2.5, 50, 97.5], 0)
    ev = 1 - res.var()/pv.var()
    cv = np.mean([np.corrcoef(x, v241)[0,1] for x in cells])
    print(f"{name:42s} EV {ev:.2f} corr {cv:+.2f} ratio " + " ".join(f"{r:.2f}{'' if l<=o<=h else '*'}" for r,l,o,h in zip(med/obs, lo, obs, hi)))
B = f[R.P.BASELINE].to_numpy(float); BXY = np.c_[B, fxy]
run('A 241 pixels, OLS baseline', in241, B, LinearRegression())
run('B 241 pixels, OLS baseline+x/y', in241, BXY, LinearRegression())
run('C 341 pixels, OLS baseline+x/y', np.ones_like(in241), BXY, LinearRegression())
run('D 241 pixels, unconditional', in241, B, None)
run('F 241 pixels, HGB leaf200 baseline', in241, B, HistGradientBoostingRegressor(**dict(R.HGB_SETTINGS, min_samples_leaf=200)))
run('G 241 pixels, HGB leaf200 baseline+x/y', in241, BXY, HistGradientBoostingRegressor(**dict(R.HGB_SETTINGS, min_samples_leaf=200)))
print('in241 pixels', int(in241.sum()))
