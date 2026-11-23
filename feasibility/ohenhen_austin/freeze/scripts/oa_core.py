"""Core of the Ohenhen-map validation (feasibility/ohenhen_austin/OHENHEN_AUSTIN_PLAN.md).

New here: reading the published classes at the house points (§4), the Poisson rate-ratio fits with offset (§7), the
four inference candidates r1-r4 (§7: cluster-robust Wald; wild cluster score bootstrap by 2, 6 and 12 km blocks with
test inversion), the Mantel-Haenszel rate ratio, the E-value and U's statistic T (§8).
Taken unchanged from the frozen Austin study: nyc_lib (model, oof, fold_map; hash asserted).

Wild cluster score bootstrap (Kline and Santos 2012), as implemented here for H0: beta_flag = b0:
- restricted Poisson fit with offset log(person-years) + b0 * flag and the other covariates free;
- efficient score of each house s_i = (x_i - Z (Z'WZ)^-1 Z'W x)_i (y_i - mu_i), W = diag(mu), summed by cluster -> S_g;
- studentised score t = sum S_g / sqrt(sum S_g^2); draws t* = sum w_g S_g / sqrt(sum w_g^2 S_g^2), Webb six-point
  weights w_g (Webb 2023); one-sided p_up = (1 + #{t* >= t}) / (1 + B) for beta > b0, p_low likewise for beta < b0;
- interval: the b0 on a grid of 801 log-IRR values (log 0.2 to log 5) not rejected one-sidedly at alpha each side,
  with the same weights at every grid point.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[1]
PRIV = Path("/mnt/data/Master-projects/Alex_private")
RAW = PRIV / "ohenhen2025_raw"
CP1 = PRIV / "austin/checkpoint1"
AUSTIN = ROOT / "feasibility/austin"
FROZEN = AUSTIN / "freeze/scripts"
sys.path[:0] = [str(FROZEN)]
import nyc_lib as N  # noqa: E402

NYC_LIB_SHA256 = "619e4de49415bc2f33cc7e54cd91f26740a37de8c0fcd0d990503a93f4546db1"
START, END = pd.Timestamp("2022-01-01"), pd.Timestamp("2025-11-30")  # follow-up, END inclusive
FU_DAYS = (END - START).days + 1  # 1,430
FU_YEARS = FU_DAYS / 365.25
AGE_DATE = 2022.0  # decimal year of 2022-01-01
B1 = ["building_age", "log_living_area", "log_lot_area", "lep_0_150", "slope_deg", "elevation_m", "log_income",
      "foundation_slab", "x_km", "y_km"]
FLAG_CLASSES = (3, 4)  # risk high, very high (D2)
FOLD_SEEDS = [42] + list(range(10))
SEED_BOOT_T, SEED_WILD = 2052, 2061
N_WILD = 9999
GRID = np.linspace(np.log(0.2), np.log(5.0), 801)
WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])
METHODS = ("r1", "r2", "r3", "r4")  # r1 CR1 2 km; r2-r4 wild score bootstrap 2, 6, 12 km
BLOCK_OF = {"r1": "b2", "r2": "b2", "r3": "b6", "r4": "b12"}
INPUTS = {"ohenhen/risk_austin.tif": RAW / "risk_austin.tif", "ohenhen/beta_austin.tif": RAW / "beta_austin.tif",
          "ohenhen/austin_VLM.csv": RAW / "austin_VLM.csv",
          "austin/reference_2018/population_2018.parquet": CP1 / "reference_2018/population_2018.parquet",
          "austin/features/features_2018.parquet": CP1 / "features/features_2018.parquet",
          "austin/grid_folds/eligible_grid_folds.parquet": CP1 / "grid_folds/eligible_grid_folds.parquet",
          "feasibility/austin/planted_signal/generating_coefficients.json": AUSTIN / "planted_signal/generating_coefficients.json"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


assert sha256(FROZEN / "nyc_lib.py") == NYC_LIB_SHA256, "frozen nyc_lib changed"


def source_hashes():
    return {p.name: sha256(p) for p in sorted(HERE.glob("*.py"))} | {"nyc_lib.py": NYC_LIB_SHA256}


def input_hashes():
    return {k: sha256(p) for k, p in INPUTS.items()}


# ---------------------------------------------------------------- houses and the published classes (§4)
def read_class(path, lon, lat):
    import rasterio
    with rasterio.open(path) as r:
        a = r.read(1).astype(float)
        rr, cc = (np.asarray(t) for t in rasterio.transform.rowcol(r.transform, lon, lat))
        inside = (rr >= 0) & (rr < a.shape[0]) & (cc >= 0) & (cc < a.shape[1])
        v = np.full(len(lon), np.nan)
        v[inside] = a[rr[inside], cc[inside]]
        v[~np.isfinite(v) | (v < -1e30)] = np.nan
        return v, np.where(inside, rr * 100_000 + cc, -1)


def load_houses():
    """All 149,316 eligible houses (prop_id order of the feature table) with Baseline 1 at 2022-01-01, blocks of 2, 6
    and 12 km, the seed-42 fold, and the published risk and hazard classes. No outcome column is read."""
    from pyproj import Transformer
    feat_cols = ["prop_id", "block", "fold", "year_built", "log_living_area", "log_lot_area", "lep_0_150", "slope_deg",
                 "elevation_m", "log_income", "foundation_slab", "x_km", "y_km", "canopy_share", "complete_b1"]
    h = pd.read_parquet(INPUTS["austin/features/features_2018.parquet"], columns=feat_cols)
    g = pd.read_parquet(INPUTS["austin/grid_folds/eligible_grid_folds.parquet"], columns=["prop_id", "x", "y", "block_x", "block_y", "block"])
    h = h.merge(g, on="prop_id", suffixes=("", "_g"), validate="one_to_one")
    assert (h.block == h.block_g).all() and len(h) == 149_316
    h = h.drop(columns="block_g").sort_values("prop_id", kind="stable").reset_index(drop=True)
    h["building_age"] = AGE_DATE - h.year_built
    h["b2"] = h.block
    h["b6"] = (h.block_x // 3).astype(str) + "_" + (h.block_y // 3).astype(str)
    h["b12"] = (h.block_x // 6).astype(str) + "_" + (h.block_y // 6).astype(str)
    lon, lat = Transformer.from_crs(32614, 4326, always_xy=True).transform(h.x.to_numpy(), h.y.to_numpy())
    h["risk"], h["risk_cell"] = read_class(INPUTS["ohenhen/risk_austin.tif"], lon, lat)
    h["hazard"], h["hazard_cell"] = read_class(INPUTS["ohenhen/beta_austin.tif"], lon, lat)
    h["mapped"] = h.risk.notna()
    h["flag"] = h.risk.isin(FLAG_CLASSES).astype(float)
    h["hazard_flag"] = (h.hazard >= 2).astype(float)
    h["lon"], h["lat"] = lon, lat
    return h


def group_index(labels):
    codes, uniq = pd.factorize(np.asarray(labels))
    return codes, len(uniq)


# ---------------------------------------------------------------- Poisson fits with offset (§7)
def solve(A, b):
    """np.linalg.solve, with a least-squares fallback when A is singular (extreme restricted fits of the grid)."""
    try:
        return np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return np.linalg.lstsq(A, b, rcond=None)[0]


def poisson_fit(X, y, offset, b_init=None, tol=1e-10, maxit=100):
    """Newton-Raphson for log E[y] = offset + X b, with step-halving whenever a full step would lower the
    log-likelihood or leave it non-finite (a full step is taken whenever it does not). Returns b, mu, Hessian."""
    b = np.zeros(X.shape[1]) if b_init is None else np.array(b_init, float)
    if b_init is None:
        b[0] = np.log(y.sum() / np.exp(offset).sum())

    def ll(bb):
        eta = offset + X @ bb
        return float(np.sum(y * eta - np.exp(eta))) if np.max(eta) < 700 else -np.inf

    cur = ll(b)
    for _ in range(maxit):
        mu = np.exp(offset + X @ b)
        H = (X * mu[:, None]).T @ X
        step = solve(H, X.T @ (y - mu))
        t = 1.0
        new = ll(b + step)
        while not (np.isfinite(new) and new >= cur - 1e-9 * (1 + abs(cur))) and t > 1e-10:
            t /= 2
            new = ll(b + t * step)
        b, cur = b + t * step, new
        if np.max(np.abs(t * step)) < tol:
            break
    mu = np.exp(offset + X @ b)
    return b, mu, (X * mu[:, None]).T @ X


def design(cols=None, frame=None, x=None):
    """[intercept, standardised covariates..., flag last]; covariates standardised for stability only (the flag's
    coefficient does not depend on it)."""
    parts = [np.ones(len(x))]
    if cols:
        Z = frame[cols].to_numpy(float)
        sd = Z.std(0)
        sd[sd == 0] = 1.0
        parts += list(((Z - Z.mean(0)) / sd).T)
    return np.column_stack(parts + [np.asarray(x, float)])


def cr1(X, y, mu, H, gidx, G, j=-1):
    """Cluster-robust (CR1, G/(G-1)) variance of coefficient j."""
    S = np.zeros((G, X.shape[1]))
    np.add.at(S, gidx, X * (y - mu)[:, None])
    Hi = np.linalg.inv(H)
    V = Hi @ (S.T @ S) @ Hi * G / (G - 1)
    return float(V[j, j])


def webb_weights(rng, B, G):
    return WEBB[rng.integers(0, 6, size=(B, G))]


def restricted_scores(X, y, offset, b0, gidx, G):
    """Cluster sums of the efficient score for the last column at beta = b0 (other columns refitted)."""
    Z, x = X[:, :-1], X[:, -1]
    _, mu, Hz = poisson_fit(Z, y, offset + b0 * x)
    xt = x - Z @ solve(Hz, (Z * mu[:, None]).T @ x)
    return np.bincount(gidx, weights=xt * (y - mu), minlength=G)


def wild_p(S, W):
    """One-sided p-values (beta > b0, beta < b0) of the studentised score; W = (B, G) weights."""
    den = np.sqrt((S ** 2).sum())
    t = S.sum() / den if den > 0 else 0.0
    SB = W * S[None, :]
    tb = SB.sum(1) / np.sqrt((SB ** 2).sum(1))
    B = len(W)
    return (1 + np.sum(tb >= t)) / (1 + B), (1 + np.sum(tb <= t)) / (1 + B)


def fit_flag(X, y, offset):
    b, mu, H = poisson_fit(X, y, offset)
    return b, mu, H


def infer(X, y, offset, groups, method, rng_seed, alpha=0.05, interval=True, fit=None):
    """Inference on the last coefficient (log IRR of the flag) by r1-r4.
    Returns dict(log_irr, irr, p_one_sided [beta > 0], lo90, hi90, lo95, hi95 [IRR scale; None if open at the grid edge])."""
    b, mu, H = fit if fit is not None else fit_flag(X, y, offset)
    est = float(b[-1])
    gidx, G = group_index(groups[BLOCK_OF[method]])
    out = dict(method=method, clusters=G, log_irr=est, irr=float(np.exp(est)))
    if method == "r1":
        se = np.sqrt(cr1(X, y, mu, H, gidx, G))
        out.update(se=float(se), p_one_sided=float(1 - norm.cdf(est / se)))
        for lev, z in ((90, norm.ppf(0.95)), (95, norm.ppf(0.975))):
            out[f"lo{lev}"], out[f"hi{lev}"] = float(np.exp(est - z * se)), float(np.exp(est + z * se))
        return out
    W = webb_weights(np.random.default_rng(rng_seed), N_WILD, G)
    p_up, _ = wild_p(restricted_scores(X, y, offset, 0.0, gidx, G), W)
    out["p_one_sided"] = float(p_up)
    if interval:
        pu, pl = np.empty(len(GRID)), np.empty(len(GRID))
        for i, b0 in enumerate(GRID):
            pu[i], pl[i] = wild_p(restricted_scores(X, y, offset, b0, gidx, G), W)
        for lev, a in ((90, alpha), (95, alpha / 2)):
            keep = (pu >= a) & (pl >= a)
            if keep.any():
                i0, i1 = np.flatnonzero(keep)[[0, -1]]
                out[f"lo{lev}"] = None if i0 == 0 else float(np.exp(GRID[i0]))
                out[f"hi{lev}"] = None if i1 == len(GRID) - 1 else float(np.exp(GRID[i1]))
            else:
                out[f"lo{lev}"] = out[f"hi{lev}"] = None
    return out


def unadjusted(y, py, x):
    """Rates per 1,000 house-years, IRR and rate difference (closed form)."""
    x = np.asarray(x, bool)
    e1, e0, t1, t0 = y[x].sum(), y[~x].sum(), py[x].sum(), py[~x].sum()
    return dict(events_flagged=int(e1), events_other=int(e0), py_flagged=float(t1), py_other=float(t0),
                houses_flagged=int(x.sum()), houses_other=int((~x).sum()),
                rate_flagged_per_1000=float(1000 * e1 / t1), rate_other_per_1000=float(1000 * e0 / t0),
                irr=float((e1 / t1) / (e0 / t0)) if e0 > 0 and t1 > 0 else None)


def mantel_haenszel(y, py, x, strata):
    x = np.asarray(x, bool)
    num = den = 0.0
    for s in np.unique(strata):
        m = strata == s
        T = py[m].sum()
        num += y[m & x].sum() * py[m & ~x].sum() / T
        den += y[m & ~x].sum() * py[m & x].sum() / T
    return float(num / den) if den > 0 else None


def e_value(rr):
    if rr is None:
        return None
    rr = 1 / rr if rr < 1 else rr
    return float(rr + np.sqrt(rr * (rr - 1)))


# ---------------------------------------------------------------- U: held-out log-likelihood gain (§8)
def loglik(y, p):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return float(np.sum(y * np.log(p) + (1 - y) * np.log1p(-p)))


def fold_assignments(blocks, fold42, y):
    """(11, n): the Austin seed-42 fold, then nyc_lib.fold_map with seeds 0-9 on these rows, label = y."""
    cells = pd.DataFrame(dict(block=np.asarray(blocks), holds_event=np.asarray(y, int)))
    rows = [np.asarray(fold42, np.int64)]
    for s in FOLD_SEEDS[1:]:
        rows.append(cells.block.map(N.fold_map(cells, s)).to_numpy(np.int64))
    return np.array(rows)


def t_statistic(XB, x, y, folds):
    """T = mean over assignments of the out-of-fold log-likelihood gain of M1 (XB + x) over M0 (XB)."""
    y = np.asarray(y, int)
    X1 = np.c_[XB, x]
    dl = []
    for f in folds:
        s0, s1 = N.oof(XB, y, f, N.LR), N.oof(X1, y, f, N.LR)
        assert np.isfinite(s0).all() and np.isfinite(s1).all()
        dl.append(loglik(y, s1) - loglik(y, s0))
    return float(np.mean(dl)), dl


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return float(c - h), float(c + h)
