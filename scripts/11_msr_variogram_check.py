"""Why the MSR surrogates of 10 miss the observed variogram at short lags, and whether a variogram-matching null
does better. Diagnostics only: no model is fitted and no p-value is computed, so the choice of any further null is
made blind to its result.

Same core cells, velocity and MSR surrogates as 10 (same seed and order, so the envelopes are 10's).
1. Per-lag table: cell pairs, observed semivariance, the exact mean of the MSR surrogates' semivariance (random
   sign flips cancel the cross terms between Moran eigenvector maps) and the surrogates' 95% range.
2. Lag-1 decomposition: gamma(1) = degree-weighted variance - Moran's I (queen) x variance, where the
   degree-weighted variance weights each cell's squared deviation by its number of queen neighbours. MSR keeps the
   variance and (up to sampling) Moran's I, so a gap has to come from where the variance sits.
3. Where the variance sits: velocity spread by number of queen neighbours and by InSAR points per cell.
4. Weights check: MSR on queen contiguity plus minimum-spanning-tree links (so every cell is connected) instead of
   10's distance-based weights.
5. Variogram-matching surrogates (Burt et al. 2020, after Viladomat et al. 2014): permute velocity, smooth it over
   each cell and its k nearest cells with an exponential kernel, choose k and a rescaling plus white noise so the
   surrogate's variogram best fits the observed one (lags 1-16), and optionally rank-remap to the observed values.
   k is chosen per surrogate from 2 up to 0.9 x cells (Burt et al.'s default range is 0.1-0.9 x cells).
Outputs: data/pilot/msr_variogram_check.csv, msr_variogram_check.png and MSR_VARIOGRAM_CHECK.md."""
import importlib.util
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import shapely
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.spatial.distance import cdist
from scipy.stats import rankdata, skew

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("msr10", ROOT / "scripts/10_msr_null.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
S, P = M.S, M.P

BURT_SEED = M.SEED + 1
NAMES = dict(zip(S.C8.CORE, ["Karmouz", "Moharam Bek", "El Gomrok", "El Labban", "Attarin", "Manshiya", "Mina El-Basal"]))
NULLS = ["MSR", "MSR, amplitude-adjusted", "Variogram-matching", "Variogram-matching, observed values"]
READING = [  # written after the 2026-09-29 run
    "## Result",
    "",
    "- **The gap is short-range only.** At 250 m the MSR surrogates' median semivariance is 38–85% above the observed at "
    "0.25–1 km (all four lags outside the 95% range) and within 13% from 1.5 km on; at 200 m it is 24–192% above up to "
    "1.4 km and within 11% beyond. The surrogates are rougher than the real field at short range; the long-range "
    "structure (sill, range about 1.75 km) is reproduced.",
    "- **Cause: where the variance sits, not the weights.** MSR keeps the variance and Moran's I (queen: I × variance "
    "2.12 observed vs 2.16), so the whole lag-1 gap at 250 m (1.06 vs 1.97) comes from the degree-weighted variance "
    "(3.19 vs 4.14). The largest deviations sit in cells with few neighbours and few InSAR points: at 250 m, cells "
    "with 0–2 queen neighbours are 8% of cells and carry 19% of the variance, and single-point cells are 14% and carry "
    "35% (200 m: 32% and 46%). Such cells have few short-lag pairs, so they add variance but little short-lag "
    "semivariance; MSR's sign flips spread that variance over all cells. MSR on queen contiguity is no better (exact "
    "surrogate mean at lags 1–4: 2.06 · 2.29 · 1.99 · 1.60 × observed, vs 1.85 · 1.53 · 1.42 · 1.37 with 10's weights).",
    "- **The extremes are not collapse cells.** The 10 most negative cells at 250 m (−8.2 to −14.3 mm/yr, 6 of them in "
    "Moharam Bek) include no collapse cell, and none of the cells with 0–2 queen neighbours is a collapse cell at either size.",
    "- **A variogram-matching null reproduces the variogram.** Plain: 16 of 16 lags inside the 95% range at both sizes, "
    "with the median within 18% of the observed at lag 1 and within 10% elsewhere at 250 m (200 m: 35% at lag 1, 8% "
    "elsewhere). But its values are near-Gaussian (skewness −0.13 vs −1.83), and at 200 m its Moran's I is above the "
    "observed, so it is smoother than the real field there. Rank-remapped to the observed values, it keeps the "
    "distribution exactly and has 16 of 16 lags inside a wider range, but its median is still 18–53% above the observed "
    "at lags 1–4 at 250 m (MSR: 38–85%).",
    "- **Reading:** no stationary null reproduces both the skewed values and the short-lag variogram, because the "
    "field's short-range smoothness partly reflects where its extremes sit. The direction of any bias in the MSR "
    "p-values (0.009; 0.020 amplitude-adjusted) is not obvious: rougher surrogates line up with the clustered collapse "
    "cells less often, which makes p too small, but they also move variance from the edges into the well-connected "
    "cells where the collapse cells are, which makes p too large. The two variogram-matching nulls would test this "
    "from the smooth side; they were chosen on this check, before any of their p-values.",
    "",
]


class Lags:
    """Cell pairs at lags 1..MAX_LAG cell widths (lag = distance / cell size, rounded), as in 10's semivariogram."""

    def __init__(self, xy, res):
        lag = np.rint(cdist(xy, xy) / res).astype(int)
        i, j = np.triu_indices(len(xy), 1)
        keep = (lag[i, j] >= 1) & (lag[i, j] <= M.MAX_LAG)
        self.i, self.j, self.k = i[keep], j[keep], lag[i, j][keep]
        self.pairs = np.bincount(self.k, minlength=M.MAX_LAG + 1)[1:]
        self.lap = [np.diag((lag == h).sum(1)) - (lag == h) for h in range(1, M.MAX_LAG + 1)]

    def vario(self, s):
        return np.bincount(self.k, 0.5 * (s[self.i] - s[self.j]) ** 2, minlength=M.MAX_LAG + 1)[1:] / self.pairs

    def msr_mean(self, v, basis):
        c2 = (basis.T @ (v - v.mean())) ** 2
        return np.array([0.5 * c2 @ np.sum(basis * (L @ basis), axis=0) for L in self.lap]) / self.pairs


def burt_surrogates(v, d, lags, rng):
    """Returns (plain surrogates, surrogates rank-remapped to the observed values, chosen k)."""
    n, target, z = len(v), lags.vario(v), v - v.mean()
    ks = np.unique(np.geomspace(2, 0.9 * n, 15).astype(int))
    order = np.argsort(d, axis=1)
    nbr, wgt = {}, {}
    for k in ks:
        nbr[k] = order[:, :k + 1]  # the cell itself and its k nearest cells
        dk = np.take_along_axis(d, nbr[k], 1)
        w = np.exp(-dk / dk.max(1, keepdims=True))
        wgt[k] = w / w.sum(1, keepdims=True)
    plain, chosen = [], []
    for _ in range(M.N_SURR):
        x0 = rng.permutation(z)
        best = None
        for k in ks:
            xs = (wgt[k] * x0[nbr[k]]).sum(1)
            g = lags.vario(xs)
            beta, alpha = np.polyfit(g, target, 1)
            sse = np.sum((target - alpha - beta * g) ** 2)
            if best is None or sse < best[0]:
                best = (sse, k, alpha, beta, xs)
        _, k, alpha, beta, xs = best
        plain.append(v.mean() + np.sqrt(abs(beta)) * xs + np.sqrt(abs(alpha)) * rng.standard_normal(n))
        chosen.append(k)
    plain = np.array(plain)
    remapped = np.sort(v)[rankdata(plain, method="ordinal", axis=1).astype(int) - 1]
    return plain, remapped, np.array(chosen)


def district(adm, xy):
    core = adm[adm.shapeName.isin(S.C8.CORE)].reset_index(drop=True)
    out = np.full(len(xy), "?", dtype=object)
    for _, r in core.iterrows():
        out[shapely.contains_xy(r.geometry, xy[:, 0], xy[:, 1])] = NAMES[r.shapeName]
    return out


def main():
    adm = gpd.read_file(P.RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(P.CRS)
    rng_msr, rng_burt = np.random.default_rng(M.SEED), np.random.default_rng(BURT_SEED)
    R = {}
    for res in (250, 200):  # same order as 10, so the MSR signs are 10's
        c = S.core_cells(res, adm)
        xy, v, y, npts = c[["x", "y"]].values, c.shz_vlm.values, c.positive.values.astype(bool), c.shz_n.values
        d = cdist(xy, xy)
        lags = Lags(xy, res)
        w, t = M.dbmem_weights(xy)
        basis, _ = M.mem_basis(w)
        q = M.queen_weights(xy, res)
        mst = minimum_spanning_tree(d).toarray()
        basis_q, _ = M.mem_basis(np.maximum(q, ((mst + mst.T) > 0).astype(float)))
        surr = {"MSR": M.surrogates(v, basis, rng_msr), "MSR, amplitude-adjusted": M.surrogates(v, basis, rng_msr, amplitude_adjusted=True)}
        surr["Variogram-matching"], surr["Variogram-matching, observed values"], chosen = burt_surrogates(v, d, lags, rng_burt)
        R[res] = dict(c=c, xy=xy, v=v, y=y, npts=npts, deg=q.sum(1), lags=lags, w=w, q=q, t=t, surr=surr, chosen=chosen,
                      obs=lags.vario(v), msr_mean=lags.msr_mean(v, basis), msr_queen_mean=lags.msr_mean(v, basis_q),
                      vario={k: np.array([lags.vario(s) for s in sv]) for k, sv in surr.items()},
                      district=district(adm, xy))
        print(res, "done", flush=True)

    # per-lag table
    rows = []
    for res, r in R.items():
        for h in range(M.MAX_LAG):
            row = {"res": res, "lag": h + 1, "km": (h + 1) * res / 1000, "pairs": int(r["lags"].pairs[h]), "observed": r["obs"][h],
                   "MSR exact mean": r["msr_mean"][h], "MSR exact mean, queen weights": r["msr_queen_mean"][h]}
            for k in NULLS:
                vs = r["vario"][k][:, h]
                row[f"{k}: median"], row[f"{k}: 2.5%"], row[f"{k}: 97.5%"] = np.median(vs), np.percentile(vs, 2.5), np.percentile(vs, 97.5)
            rows.append(row)
    lag_df = pd.DataFrame(rows)
    lag_df.to_csv(P.PILOT / "msr_variogram_check.csv", index=False)

    def lag_table(res):
        d = lag_df[lag_df.res == res].reset_index(drop=True)
        out = {"Lag (km)": d.km.map(lambda x: f"{x:.2f}"), "Cell pairs": d.pairs.map(lambda x: f"{x:,}"),
               "Observed": d.observed.map(lambda x: f"{x:.2f}")}
        for k in NULLS:
            lo, hi, med = d[f"{k}: 2.5%"], d[f"{k}: 97.5%"], d[f"{k}: median"]
            flag = np.where((d.observed < lo) | (d.observed > hi), " ✗", "")
            out[k] = [f"{m:.2f} ({a:.2f}–{b:.2f}){f}" for m, a, b, f in zip(med, lo, hi, flag)]
        return pd.DataFrame(out)

    # summary of each null
    srows = []
    for res, r in R.items():
        for k in NULLS:
            sv, vs = r["surr"][k], r["vario"][k]
            lo, hi, med = np.percentile(vs, 2.5, 0), np.percentile(vs, 97.5, 0), np.median(vs, 0)
            inside = (r["obs"] >= lo) & (r["obs"] <= hi)
            ratio = med / r["obs"]
            mw, mq = np.array([M.morans_i(s, r["w"]) for s in sv]), np.array([M.morans_i(s, r["q"]) for s in sv])
            srows.append({
                "Cell size": f"{res} m", "Null": k, "Lags inside the 95% range": f"{int(inside.sum())} of {M.MAX_LAG}",
                "Median / observed, lags 1–4": " · ".join(f"{x:.2f}" for x in ratio[:4]),
                "Median / observed, lags 5–16 (range)": f"{ratio[4:].min():.2f}–{ratio[4:].max():.2f}",
                "Moran's I, MEM weights: observed / 95% range": f"{M.morans_i(r['v'], r['w']):.3f} / {np.percentile(mw, 2.5):.3f}–{np.percentile(mw, 97.5):.3f}",
                "Moran's I, queen: observed / 95% range": f"{M.morans_i(r['v'], r['q']):.3f} / {np.percentile(mq, 2.5):.3f}–{np.percentile(mq, 97.5):.3f}",
                "Skewness: observed / median": f"{skew(r['v']):.2f} / {np.median(skew(sv, axis=1)):.2f}",
                "Variance: median / observed": f"{np.median(sv.var(1)) / r['v'].var():.2f}"})
    summ = pd.DataFrame(srows)

    # lag-1 decomposition and where the variance sits
    drows, vrows = [], []
    for res, r in R.items():
        v, deg, z = r["v"], r["deg"], r["v"] - r["v"].mean()
        n1 = r["q"].sum() / 2
        sig2 = np.mean(z ** 2)
        dv_obs = np.sum(deg * z ** 2) / (2 * n1)
        sv = r["surr"]["MSR"] - r["surr"]["MSR"].mean(1, keepdims=True)
        dv_msr = np.median((deg * sv ** 2).sum(1) / (2 * n1))
        i_obs = M.morans_i(v, r["q"])
        i_msr = np.median([M.morans_i(s, r["q"]) for s in r["surr"]["MSR"]])
        drows.append({"Cell size": f"{res} m", "Variance": f"{sig2:.2f}",
                      "Degree-weighted variance: observed / MSR median": f"{dv_obs:.2f} ({dv_obs / sig2:.0%} of the variance) / {dv_msr:.2f}",
                      "Moran's I (queen) × variance: observed / MSR median": f"{i_obs * sig2:.2f} / {i_msr * sig2:.2f}",
                      "Lag-1 semivariance: observed / MSR median": f"{r['obs'][0]:.2f} / {np.median(r['vario']['MSR'][:, 0]):.2f}"})
        tot = np.sum(z ** 2)
        for label, m in (("0–2 queen neighbours", deg <= 2), ("3–5 queen neighbours", (deg >= 3) & (deg <= 5)),
                         ("6–8 queen neighbours", deg >= 6), ("1 InSAR point", r["npts"] == 1),
                         ("2–3 InSAR points", (r["npts"] >= 2) & (r["npts"] <= 3)), ("4 or more InSAR points", r["npts"] >= 4)):
            vrows.append({"Cell size": f"{res} m", "Cells": label, "Cells (collapse cells)": f"{m.sum()} ({int(r['y'][m].sum())})",
                          "Share of cells": f"{m.mean():.0%}", "Share of the variance": f"{np.sum(z[m] ** 2) / tot:.0%}",
                          "Velocity SD (mm/yr)": f"{v[m].std():.2f}"})
    dec, var_df = pd.DataFrame(drows), pd.DataFrame(vrows)

    notes = []
    for res, r in R.items():
        ext = np.argsort(r["v"])[:10]
        top = pd.Series(r["district"][ext]).value_counts()
        notes.append(f"{res} m: the 10 most negative cells ({r['v'][ext].max():.1f} to {r['v'][ext].min():.1f} mm/yr) include "
                     f"{int(r['y'][ext].sum())} collapse cells; median {np.median(r['deg'][ext]):.0f} queen neighbours (all cells: "
                     f"{np.median(r['deg']):.0f}) and {np.median(r['npts'][ext]):.0f} InSAR points (all cells: {np.median(r['npts']):.0f}); "
                     + ", ".join(f"{n} {k}" for k, n in top.items()) + ".")
        notes.append(f"{res} m, weights check: exact MSR mean / observed at lags 1–4 = "
                     + " · ".join(f"{x:.2f}" for x in r["msr_queen_mean"][:4] / r["obs"][:4])
                     + " with queen contiguity + spanning-tree links, vs "
                     + " · ".join(f"{x:.2f}" for x in r["msr_mean"][:4] / r["obs"][:4]) + f" with 10's weights (t = {r['t']:.0f} m).")
        ks = pd.Series(r["chosen"])
        notes.append(f"{res} m, variogram-matching: chosen neighbourhood k median {ks.median():.0f} cells "
                     f"(2.5–97.5%: {ks.quantile(0.025):.0f}–{ks.quantile(0.975):.0f}; the largest k offered, "
                     f"{int(0.9 * len(r['v']))}, chosen {int((ks == int(0.9 * len(r['v']))).sum())} times).")
    for s in notes:
        print(s)
    print(summ.to_string(index=False))
    print(dec.to_string(index=False))
    print(var_df.to_string(index=False))

    # figure
    fig, ax = plt.subplots(1, 3, figsize=(17, 4.8), gridspec_kw={"width_ratios": [1, 1, 0.9]})
    for a, res in zip(ax[:2], (250, 200)):
        r = R[res]
        km = np.arange(1, M.MAX_LAG + 1) * res / 1000
        for k, col in (("MSR", "0.55"), ("Variogram-matching, observed values", "tab:orange")):
            vs = r["vario"][k]
            a.fill_between(km, np.percentile(vs, 2.5, 0), np.percentile(vs, 97.5, 0), color=col, alpha=0.25, label=f"{k}: 95% range")
            a.plot(km, np.median(vs, 0), color=col, lw=1.5, label=f"{k}: median")
        a.plot(km, np.median(r["vario"]["Variogram-matching"], 0), color="tab:orange", ls="--", lw=1.2, label="Variogram-matching (plain): median")
        a.plot(km, r["obs"], "o-", color="tab:blue", ms=4, label="observed velocity")
        a.set(xlabel="Lag (km)", ylabel="Semivariance (mm/yr)²", title=f"Core, {res} m: semivariogram")
        a.legend(fontsize=7)
    r = R[250]
    x0, y0 = r["xy"].min(0)
    cells = [Rectangle(((x - x0 - 125) / 1000, (yy - y0 - 125) / 1000), 0.25, 0.25) for x, yy in r["xy"]]
    pc = PatchCollection(cells, cmap="magma", edgecolor=np.where(r["y"], "k", "none").tolist(), linewidth=1.3)
    pc.set_array(r["v"])
    pc.set_clim(-8, r["v"].max())
    ax[2].add_collection(pc)
    lo = r["deg"] <= 2
    ax[2].plot((r["xy"][lo, 0] - x0) / 1000, (r["xy"][lo, 1] - y0) / 1000, "x", color="tab:cyan", ms=6, mew=1.5)
    ax[2].autoscale_view()
    ax[2].set_aspect("equal")
    ax[2].set(xlabel="km east", ylabel="km north", title="Core velocity, 250 m (black edge = collapse cell,\ncyan × = 0–2 queen neighbours)")
    fig.colorbar(pc, ax=ax[2], extend="min", label="Shirzaei VLM (mm/yr), clipped at −8")
    fig.tight_layout()
    fig.savefig(P.PILOT / "msr_variogram_check.png", dpi=130)
    plt.close(fig)

    lines = [
        "# Why the MSR surrogates miss the short-lag variogram",
        "",
        "**Follows:** `MSR_NULL.md`, whose check found the observed semivariogram outside the MSR surrogates' 95% range at "
        "4 of 16 lags at 250 m and 7 of 16 at 200 m.",
        "**Reproduce:** `.venv/bin/python scripts/11_msr_variogram_check.py` (after 10; no model fits, about 20 s).",
        "**Blind:** diagnostics only. No model is fitted and no p-value is computed here, so any further null can be chosen "
        "on how well it reproduces the velocity field, not on its result.",
        "",
        "- **Per-lag check:** the same core cells, velocity and MSR surrogates as `MSR_NULL.md` (same seed and order). ✗ = the "
        "observed value is outside the surrogates' 95% range.",
        "- **Lag-1 decomposition:** lag-1 semivariance = degree-weighted variance − Moran's I (queen) × variance, where the "
        "degree-weighted variance weights each cell's squared deviation by its number of queen neighbours. MSR keeps the "
        "variance and, up to sampling, Moran's I, so any gap has to come from where the variance sits.",
        "- **Variogram-matching null** (Burt et al. 2020, after Viladomat et al. 2014): velocity is permuted, smoothed over "
        "each cell and its k nearest cells with an exponential kernel, then rescaled and given white noise so that its "
        f"variogram (lags 1–{M.MAX_LAG}) best fits the observed one; k is chosen per surrogate from 2 to 0.9 × cells. "
        "\"Observed values\" = the same surrogates rank-remapped to the observed velocities, so the value distribution is "
        f"exact. {M.N_SURR} surrogates each.",
        "",
        *READING,
        "## Semivariogram by lag, 250 m (median and 95% range of 999 surrogates)",
        "",
        P.md_table(lag_table(250)),
        "",
        "## Semivariogram by lag, 200 m",
        "",
        P.md_table(lag_table(200)),
        "",
        "## Each null against the observed field",
        "",
        P.md_table(summ),
        "",
        "## Lag-1 decomposition",
        "",
        P.md_table(dec),
        "",
        "## Where the velocity variance sits",
        "",
        P.md_table(var_df),
        "",
        *[f"- {s}" for s in notes],
        "",
        "Figure: `msr_variogram_check.png` (semivariograms at 250 m and 200 m; map of core velocity at 250 m).",
        "",
    ]
    (P.PILOT / "MSR_VARIOGRAM_CHECK.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
