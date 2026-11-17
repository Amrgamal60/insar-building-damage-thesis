"""Spatially constrained null for the primary core test: Moran spectral randomization (MSR).

Primary analysis, fixed before this run: historic core, 250 m, logistic regression, baseline + x/y vs baseline +
x/y + Shirzaei velocity, statistic = change in out-of-fold PR AUC. The cells, labels, baseline features, folds
(seed 42), preprocessing and model settings are the same as in 09. 200 m is a robustness check only.

Surrogates (Wagner & Dray 2015, singleton method):
1. W = distance-based weights among the core cells: w = 1 - (d / 4t)^2 for d <= t, where t is the longest edge of
   the minimum spanning tree, so every cell is connected.
2. The Moran eigenvector maps (MEMs) are the eigenvectors of the doubly centred W, restricted to the space
   orthogonal to the constant.
3. Velocity is written as mean + sum of c_k * MEM_k. Each surrogate flips the sign of every c_k at random. That
   keeps the variance carried by every spatial scale, so Moran's I under W is reproduced exactly, and the
   multiscale structure (correlogram / variogram) approximately.
Check (secondary): an amplitude-adjusted MSR that also keeps the observed value distribution exactly. It
alternates rank remapping with restoring |c_k|, like IAAFT for time series.
Verification: Moran's I under W and under an independent queen-neighbour W, and the empirical semivariogram by
lag, compared between observed and surrogates.
Test: velocity is replaced by each surrogate and the velocity model refitted on the same folds. The null is the
surrogate changes in PR AUC. p = (1 + null changes >= observed) / (1 + surrogates).
Outputs: data/pilot/msr_*.csv, msr_*.png and MSR_NULL.md."""
import importlib.util
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
from scipy.linalg import null_space
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.spatial.distance import cdist
from scipy.stats import rankdata, skew

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("stats09", ROOT / "scripts/09_core_statistics.py")
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
P = S.P

N_SURR, SEED, AA_ITERS, MAX_LAG = 999, 2026, 50, 16  # MAX_LAG in cell widths
KIND = "logistic regression"


def dbmem_weights(xy):
    d = cdist(xy, xy)
    t = minimum_spanning_tree(d).toarray().max()
    w = np.where((d > 0) & (d <= t), 1 - (d / (4 * t)) ** 2, 0.0)
    return w, t


def queen_weights(xy, res):
    d = cdist(xy, xy)
    return ((d > 0) & (d <= 1.5 * res)).astype(float)


def morans_i(v, w):
    z = v - v.mean()
    return len(v) / w.sum() * (z @ w @ z) / (z @ z)


def mem_basis(w):
    q = null_space(np.ones((1, len(w))))  # orthonormal basis orthogonal to the constant
    lam, u = np.linalg.eigh(q.T @ w @ q)
    return q @ u, lam


def surrogates(v, basis, rng, amplitude_adjusted=False):
    mean, c = v.mean(), basis.T @ (v - v.mean())
    ordered = np.sort(v)
    out = []
    for _ in range(N_SURR):
        s = mean + basis @ (rng.choice([-1.0, 1.0], len(c)) * c)
        if amplitude_adjusted:
            for _ in range(AA_ITERS):
                s = ordered[rankdata(s, method="ordinal").astype(int) - 1]
                cs = basis.T @ (s - mean)
                s = mean + basis @ (np.sign(cs) * np.abs(c))
            s = ordered[rankdata(s, method="ordinal").astype(int) - 1]
        out.append(s)
    return np.array(out)


def semivariogram(v, lag, max_lag):
    iu = np.triu_indices(len(v), 1)
    sq, lg = 0.5 * (v[:, None] - v[None, :])[iu] ** 2, lag[iu]
    return np.array([sq[lg == k].mean() for k in range(1, max_lag + 1)])


def run(res, adm, rng):
    c = S.core_cells(res, adm)
    y, fold = c.positive.values.astype(int), c.fold.values
    xb = c[S.SET_B].values
    v = c.shz_vlm.values
    mb = S.metrics(y, S.oof(xb, y, fold, KIND))["pr"]
    obs = S.metrics(y, S.oof(np.c_[xb, v], y, fold, KIND))["pr"] - mb

    xy = c[["x", "y"]].values
    w, t = dbmem_weights(xy)
    wq = queen_weights(xy, res)
    basis, _ = mem_basis(w)
    lag = np.rint(cdist(xy, xy) / res).astype(int)
    out = {"res": res, "cells": len(c), "positives": int(y.sum()), "baseline_pr": mb, "observed_delta": obs, "mst_t": t,
           "moran_obs_w": morans_i(v, w), "moran_obs_queen": morans_i(v, wq), "skew_obs": skew(v),
           "vario_obs": semivariogram(v, lag, MAX_LAG)}
    for name, aa in (("MSR", False), ("MSR, amplitude-adjusted", True)):
        surr = surrogates(v, basis, rng, amplitude_adjusted=aa)
        null = np.array([S.metrics(y, S.oof(np.c_[xb, s], y, fold, KIND))["pr"] - mb for s in surr])
        out[name] = {"null": null, "p": (1 + (null >= obs - 1e-12).sum()) / (1 + len(null)),
                     "moran_w": np.array([morans_i(s, w) for s in surr]),
                     "moran_queen": np.array([morans_i(s, wq) for s in surr]),
                     "skew": np.array([skew(s) for s in surr]),
                     "vario": np.array([semivariogram(s, lag, MAX_LAG) for s in surr])}
    return out


def figures(r):
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    for name, col in (("MSR", "0.45"), ("MSR, amplitude-adjusted", "tab:orange")):
        ax[0].hist(r[name]["null"], bins=40, color=col, alpha=0.6, label=f"{name} null (p = {r[name]['p']:.3f})")
    ax[0].axvline(r["observed_delta"], color="tab:blue", lw=2, label=f"observed +{r['observed_delta']:.3f}")
    ax[0].set_xlabel("Change in out-of-fold PR AUC when velocity is added")
    ax[0].set_ylabel("Surrogate fields")
    ax[0].set_title(f"Core, {r['res']} m, logistic regression: {N_SURR} MSR surrogates")
    ax[0].legend(fontsize=8)
    lags = np.arange(1, MAX_LAG + 1) * r["res"] / 1000
    vs = r["MSR"]["vario"]
    ax[1].fill_between(lags, np.percentile(vs, 2.5, axis=0), np.percentile(vs, 97.5, axis=0), color="0.8", label="MSR 95% envelope")
    ax[1].plot(lags, np.median(vs, axis=0), color="0.4", label="MSR median")
    ax[1].plot(lags, r["vario_obs"], "o-", color="tab:blue", ms=4, label="observed velocity")
    ax[1].set_xlabel("Lag (km)")
    ax[1].set_ylabel("Semivariance (mm/yr)²")
    ax[1].set_title("Semivariogram: observed vs surrogates")
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(P.PILOT / f"msr_null_{r['res']}m.png", dpi=130)
    plt.close(fig)


def pct(a, q):
    return float(np.percentile(a, q))


def main():
    adm = gpd.read_file(P.RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(P.CRS)
    rng = np.random.default_rng(SEED)
    R = {res: run(res, adm, rng) for res in (250, 200)}
    rows, vrows = [], []
    for res, r in R.items():
        figures(r)
        for name in ("MSR", "MSR, amplitude-adjusted"):
            n = r[name]
            rows.append({"Cell size": f"{res} m", "Null": name, "Cells (collapse cells)": f"{r['cells']} ({r['positives']})",
                         "Observed ΔPR AUC": f"{r['observed_delta']:+.3f}",
                         "Null median": f"{np.median(n['null']):+.3f}",
                         "Null 95th / 99th percentile": f"{pct(n['null'], 95):+.3f} / {pct(n['null'], 99):+.3f}",
                         "Surrogates ≥ observed": f"{int((n['null'] >= r['observed_delta'] - 1e-12).sum())} of {N_SURR}",
                         "Monte Carlo p": f"{n['p']:.3f}",
                         "Moran's I, MEM weights: observed / surrogates (2.5–97.5%)":
                             f"{r['moran_obs_w']:.3f} / {pct(n['moran_w'], 2.5):.3f}–{pct(n['moran_w'], 97.5):.3f}",
                         "Moran's I, queen neighbours: observed / surrogates (2.5–97.5%)":
                             f"{r['moran_obs_queen']:.3f} / {pct(n['moran_queen'], 2.5):.3f}–{pct(n['moran_queen'], 97.5):.3f}",
                         "Skewness: observed / surrogates (median)": f"{r['skew_obs']:.2f} / {np.median(n['skew']):.2f}"})
            lo, hi = np.percentile(n["vario"], 2.5, axis=0), np.percentile(n["vario"], 97.5, axis=0)
            inside = (r["vario_obs"] >= lo) & (r["vario_obs"] <= hi)
            vrows.append({"Cell size": f"{res} m", "Null": name, "Lags inside the 95% envelope": f"{int(inside.sum())} of {MAX_LAG}",
                          "Largest |observed − median| / observed": f"{np.max(np.abs(r['vario_obs'] - np.median(n['vario'], axis=0)) / r['vario_obs']):.1%}"})
        pd.DataFrame({"surrogate": np.arange(N_SURR), **{f"delta_pr_{k}": R[res][k]["null"] for k in ("MSR", "MSR, amplitude-adjusted")},
                      **{f"moran_w_{k}": R[res][k]["moran_w"] for k in ("MSR", "MSR, amplitude-adjusted")}}).to_csv(
            P.PILOT / f"msr_null_{res}m.csv", index=False)
    t, vt = pd.DataFrame(rows), pd.DataFrame(vrows)
    print(t.to_string(index=False))
    print(vt.to_string(index=False))
    r = R[250]
    lines = [
        "# Spatially constrained null (Moran spectral randomization) for the primary core test",
        "",
        "**Primary analysis, fixed before this run:** historic core, 250 m, logistic regression, baseline + x/y vs baseline + x/y + "
        "Shirzaei velocity, statistic = change in out-of-fold PR AUC. Same cells, labels, baseline features, folds (seed 42), "
        "preprocessing and model settings as `CORE_STATISTICS.md`. 200 m is robustness only; nothing was tuned on the result.",
        "**Reproduce:** `.venv/bin/python scripts/10_msr_null.py` (after 09).",
        "",
        f"- **Surrogates:** {N_SURR} velocity fields per null, by Moran spectral randomization (Wagner & Dray 2015, singleton method). "
        f"Velocity is decomposed on the Moran eigenvector maps of distance-based weights among the core cells "
        f"(w = 1 − (d/4t)² for d ≤ t, t = {r['mst_t']:.0f} m, the longest minimum-spanning-tree edge), and the sign of every "
        "coefficient is flipped at random. This keeps the variance carried by each spatial scale, so Moran's I under those weights is "
        "reproduced exactly, and the correlogram and variogram approximately.",
        f"- **Check null:** an amplitude-adjusted MSR that also keeps the observed value distribution exactly ({AA_ITERS} rounds "
        "alternating rank remapping and restoring each coefficient's size, like IAAFT for time series).",
        "- **Test:** velocity is replaced by each surrogate and the velocity model refitted on the same folds. "
        "p = (1 + surrogates with a change ≥ observed) / (1 + surrogates).",
        "",
        "## Result",
        "",
        P.md_table(t),
        "",
        "## Does the null reproduce the velocity field's spatial structure?",
        "",
        f"Semivariogram of velocity by lag (1–{MAX_LAG} cell widths), observed vs the surrogates' 95% envelope:",
        "",
        P.md_table(vt),
        "",
        "Figures: `msr_null_250m.png` and `msr_null_200m.png` (left: null distribution with the observed change; right: variogram check).",
        "",
    ]
    (P.PILOT / "MSR_NULL.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
