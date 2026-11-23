"""Core of the Alexandria stricter retest (feasibility/alexandria_retest/ALEX_RETEST_PLAN.md).

Everything that the original LiCSAR test fixed is taken from its own code, imported unchanged:
scripts/17_licsar_test.py (cells, nulls), 09_core_statistics.py (model, oof, metrics), 07_pilot_models.py
(fold_map, grid), 16_licsar_cells.py (pixels). The null generator is the frozen Austin copy
(feasibility/austin/freeze/scripts: nyc_lib, lowmem_null, calibration/cpu_null), imported unchanged. New here:
the statistic T (§5), the fold-assignment matrix, the pixel field and the linear conditional fits (§6, draft 3)
and averaging pixel surrogates into cells.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RETEST = HERE.parent
ROOT = RETEST.parents[1]
AUSTIN_FROZEN = ROOT / "feasibility/austin/freeze/scripts"
sys.path[:0] = [str(AUSTIN_FROZEN), str(AUSTIN_FROZEN / "calibration")]
import nyc_lib as N  # noqa: E402
from cpu_null import CPULowMemVariogramNull  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T17 = _load("licsar_test17", ROOT / "scripts/17_licsar_test.py")
L16 = _load("licsar_cells16", ROOT / "scripts/16_licsar_cells.py")
P, S = T17.P, T17.S
LR = T17.LR
COL = "lic_ud_p1"
RES = 250
FOLD_SEEDS = [42] + list(range(10))
PIXEL_LAG_M, MAX_LAG, KMAX = 100.0, 16, 1000
CELL_CHECK_LAGS = 6
SEED_NULL, SEED_BOOT, SEED_LOC = 2043, 2042, 2044
P1_TIF = ROOT / "data/licsbas/decomposed/P1_UD.geo.tif"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


SOURCES = {p.relative_to(ROOT).as_posix(): p for p in [
    ROOT / "scripts/07_pilot_models.py", ROOT / "scripts/09_core_statistics.py", ROOT / "scripts/10_msr_null.py",
    ROOT / "scripts/11_msr_variogram_check.py", ROOT / "scripts/16_licsar_cells.py", ROOT / "scripts/17_licsar_test.py",
    AUSTIN_FROZEN / "nyc_lib.py", AUSTIN_FROZEN / "lowmem_null.py",
    AUSTIN_FROZEN / "calibration/cpu_null.py", HERE / "retest_core.py"]}
INPUTS = {p.relative_to(ROOT).as_posix(): p for p in [
    P.PILOT / "cells_250m.csv", P.PILOT / "licsar_cells_250m.csv", P.PILOT / "target_events.csv", P1_TIF,
    P.RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson"]}


def hashes():
    return dict(sources={k: sha256(v) for k, v in SOURCES.items()}, inputs={k: sha256(v) for k, v in INPUTS.items()})


# ---------------------------------------------------------------- cells, labels, folds
def load_cells():
    """c: the 241 primary cells (original test); f: the 341 field cells; allc: the 3,300 eligible cells."""
    import geopandas as gpd
    adm = gpd.read_file(P.RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(P.CRS)
    c, n0 = T17.test_cells(RES, "shirzaei", COL, adm)
    f, _ = T17.test_cells(RES, "all", COL, adm)
    allc = pd.read_csv(P.PILOT / f"cells_{RES}m.csv")
    assert (n0, len(c), int(c.positive.sum())) == (241, 241, 32), (n0, len(c), c.positive.sum())
    assert (len(f), int(f.positive.sum())) == (341, 34), (len(f), f.positive.sum())
    kc, kf = c.row * 100_000 + c.col, f.row * 100_000 + f.col
    assert kc.isin(kf).all(), "primary cells must lie in the field"
    c = c.reset_index(drop=True)
    c["field_index"] = pd.Index(kf).get_indexer(kc)
    return c, f.reset_index(drop=True), allc


def fold_matrix(allc, c, labels=None):
    """(11, n) folds of the primary cells: original fold_map (seed 42, then 0-9) on all eligible cells, with the
    primary cells' labels replaced by `labels` when given (planted datasets)."""
    a = allc.copy()
    if labels is not None:
        idx = pd.Index(a.row * 100_000 + a.col).get_indexer(c.row * 100_000 + c.col)
        assert (idx >= 0).all()
        pos = a.positive.to_numpy().copy()
        pos[idx] = np.asarray(labels, dtype=bool)
        a["positive"] = pos
    return np.array([c.block.map(P.fold_map(a, seed=s)).to_numpy(np.int64) for s in FOLD_SEEDS])


def design(c):
    return c[S.SET_B].to_numpy(float)


# ---------------------------------------------------------------- statistic (§5)
def loglik(y, p):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return float(np.sum(y * np.log(p) + (1 - y) * np.log1p(-p)))


class Stat:
    """T = mean over the 11 fold assignments of the out-of-fold log-likelihood gain of M1 over M0; also the
    seed-42 change in PR AUC (the original statistic) from the same fits."""

    def __init__(self, XB, y, folds, kind=LR):
        self.XB, self.y, self.folds, self.kind = XB, np.asarray(y, int), folds, kind
        s0 = [S.oof(XB, self.y, f, kind) for f in folds]
        assert all(np.isfinite(s).all() for s in s0), "a fold had no positive in training"
        self.ll0 = [loglik(self.y, s) for s in s0]
        self.pr0 = [S.metrics(self.y, s)["pr"] for s in s0]

    def of(self, v):
        X1 = np.c_[self.XB, np.asarray(v, float)]
        dl, dpr = [], []
        for f, ll0, pr0 in zip(self.folds, self.ll0, self.pr0):
            s1 = S.oof(X1, self.y, f, self.kind)
            assert np.isfinite(s1).all()
            dl.append(loglik(self.y, s1) - ll0)
            dpr.append(S.metrics(self.y, s1)["pr"] - pr0)
        return dict(T=float(np.mean(dl)), dl=dl, dpr42=float(dpr[0]), dpr_mean=float(np.mean(dpr)))


def beta_hat(XB, y, v):
    """M1 fitted on all cells: velocity coefficient per SD (StandardScaler, population SD) and per mm/yr."""
    m = S.model(LR).fit(np.c_[XB, v], np.asarray(y, int))
    b = float(m[-1].coef_[0, -1])
    return dict(per_sd=b, per_mm_yr=b / float(m[0].scale_[-1]), odds_ratio_per_sd=float(np.exp(b)))


def p_upper(observed, null):
    null = np.asarray(null, float)
    return (1 + int(np.sum(null >= observed))) / (1 + len(null))


# ---------------------------------------------------------------- pixel field (§6)
class PixelField:
    """Valid P1 vertical pixels whose centres fall in the given cells (the 241 primary cells, §6 as revised in
    draft 3); cell index of each pixel."""

    def __init__(self, f):
        x, y, v = L16.pixels(P1_TIF)
        x0 = np.unique(np.round(f.x - (f.col + 0.5) * RES, 3))
        y0 = np.unique(np.round(f.y + (f.row + 0.5) * RES, 3))
        assert len(x0) == len(y0) == 1
        from rasterio.transform import from_origin
        r, cc = P.rowcol(from_origin(x0[0], y0[0], RES, RES), RES, x, y)
        cell = pd.Index(f.row * 100_000 + f.col).get_indexer(r * 100_000 + cc)
        keep = cell >= 0
        self.xy = np.c_[x[keep], y[keep]]
        self.v = v[keep]
        self.cell = cell[keep]
        self.n_cells = len(f)
        self.count = np.bincount(self.cell, minlength=self.n_cells)
        assert (self.count > 0).all(), "every field cell must hold a pixel"
        self.cells = f.reset_index(drop=True)
        means = self.to_cells(self.v[None, :])[0]
        assert np.allclose(means, f[COL].to_numpy(float), rtol=0, atol=1e-9), "pixel means differ from the cell values"
        lc = pd.read_csv(P.PILOT / f"licsar_cells_{RES}m.csv")[["row", "col", f"{COL}_n"]]
        n_saved = f[["row", "col"]].merge(lc, on=["row", "col"], how="left")[f"{COL}_n"].to_numpy(int)
        assert np.array_equal(self.count, n_saved), "pixel counts differ from the cell counts"

    def to_cells(self, S_pix):
        """(draws, pixels) -> (draws, field cells): mean of each cell's pixels."""
        S_pix = np.atleast_2d(S_pix)
        out = np.empty((len(S_pix), self.n_cells))
        for d, s in enumerate(S_pix):
            out[d] = np.bincount(self.cell, weights=s, minlength=self.n_cells) / self.count
        return out


class LinearConditionalNull:
    """Conditional null with a linear in-sample fit: pixel velocity regressed (ordinary least squares) on its cell's
    design; the residual is randomised by the unchanged generator and the fitted part added back.
    (c1) design = the six baseline features (Austin's rule: no coordinates);
    (c2) design = M0's full design, baseline + x/y (the spatial analogue of Freedman & Lane 1983)."""

    def __init__(self, field, xy, design, res=PIXEL_LAG_M, kmax=KMAX, max_lag=MAX_LAG):
        from sklearn.linear_model import LinearRegression
        field = np.asarray(field, float)
        self.fitted = LinearRegression().fit(design, field).predict(design)
        resid = field - self.fitted
        self.explained = float(1 - np.var(resid) / np.var(field))
        self.residual_null = CPULowMemVariogramNull(resid[None, :], xy, res, kmax=kmax, max_lag=max_lag)

    def draws(self, n_draws, rng):
        for r, k in self.residual_null.draws(n_draws, rng):
            yield self.fitted[None, :] + r, k


def make_null(kind, px):
    """kind in {'c1', 'c2', 'a'}: linear conditional on baseline (c1) or on baseline + x/y (c2); a unconditional."""
    if kind == "c1":
        return LinearConditionalNull(px.v, px.xy, px.cells[P.BASELINE].to_numpy(float)[px.cell])
    if kind == "c2":
        return LinearConditionalNull(px.v, px.xy, px.cells[S.SET_B].to_numpy(float)[px.cell])
    if kind == "a":
        nl = CPULowMemVariogramNull(px.v[None, :], px.xy, PIXEL_LAG_M, kmax=KMAX, max_lag=MAX_LAG)
        nl.explained = 0.0
        return nl
    raise ValueError(kind)


def pixel_surrogates(kind, px, n_draws, seed=SEED_NULL):
    """(n_draws, pixels) surrogate fields and the neighbour count of each draw."""
    nl = make_null(kind, px)
    out, ks = np.empty((n_draws, len(px.v))), []
    for d, (s, k) in enumerate(nl.draws(n_draws, np.random.default_rng(seed))):
        out[d] = np.asarray(s)[0] if np.ndim(s) == 2 else s
        ks.append(int(k) if np.ndim(k) == 0 else int(np.asarray(k).ravel()[0]))
    return out, ks, nl.explained


def cell_variogram(values, xy, max_lag=CELL_CHECK_LAGS):
    lags = N.Lags(xy, RES, max_lag)
    return lags, lags.vario(np.atleast_2d(values), np.isfinite(np.atleast_2d(values)))
