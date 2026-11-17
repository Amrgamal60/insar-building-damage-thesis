"""Primary core test under the variogram-matching nulls chosen in 11, set next to the earlier nulls.

Primary analysis, unchanged: historic core, 250 m, logistic regression, baseline + x/y vs baseline + x/y + Shirzaei
velocity, statistic = change in out-of-fold PR AUC. Same cells, folds (seed 42) and settings as 09 and 10; 200 m is
robustness only.
Nulls: the two variogram-matching nulls of 11 (Burt et al. 2020), plain and rank-remapped to the observed values.
They were chosen in 11 on how well they reproduce the velocity variogram, before any of their p-values. The
surrogates are 11's (same seed and order), 999 per null. Velocity is replaced by each surrogate and the velocity
model refitted on the same folds; p = (1 + null changes >= observed) / (1 + surrogates).
The report puts them next to 09's permutation tests and 10's MSR nulls, read from their saved outputs.
Outputs: data/pilot/variogram_null_<res>m.csv, variogram_null.png and VARIOGRAM_NULL.md.
`--report-only` rebuilds the report from the saved CSVs."""
import importlib.util
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check11", ROOT / "scripts/11_msr_variogram_check.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)
M, S, P = V.M, V.S, V.P

NEW = ["Variogram-matching", "Variogram-matching, observed values"]
KEEPS = {  # what each null reproduces, from CORE_STATISTICS.md, MSR_NULL.md and MSR_VARIOGRAM_CHECK.md
    "Free permutation": "the values only; no spatial structure",
    "Within-block permutation": "the values within each 2 km block; no structure below 2 km",
    "MSR": "Moran's I exactly; the variogram from about 1.5 km (rougher below)",
    "MSR, amplitude-adjusted": "the values; the variogram from about 1.5 km (rougher below)",
    "Variogram-matching": "the variogram at all lags; near-Gaussian values; smoother than the real field at 200 m",
    "Variogram-matching, observed values": "the values; the variogram inside its 95% range at all lags (median still high below 1 km)",
}
READING = [  # written after the 2026-09-29 run
    "## Result",
    "",
    "- **Primary test: p = 0.009–0.023 under every null.** At 250 m the variogram-matching nulls give p = 0.023 (plain) "
    "and 0.017 (observed values), next to 0.009 (MSR), 0.020 (amplitude-adjusted MSR), 0.011 (free permutation) and "
    "0.018 (within-block). The null that reproduces the variogram best, the plain one, gives the largest p; 0.023 is the "
    "conservative summary.",
    "- **200 m (robustness): still below 0.05, but less clear-cut.** p rises from 0.006 or less under MSR and the "
    "permutations to 0.037 (plain) and 0.030 (observed values). Smooth surrogate fields produce large chance gains at "
    "200 m more often (99th percentile +0.149 and +0.127, vs +0.070 under MSR), so the 200 m result depends more on "
    "short-range smoothness. The plain null is smoother than the real field at 200 m (`MSR_VARIOGRAM_CHECK.md`), so "
    "0.037 is on the strict side.",
    "- **Reading:** velocity's link to core collapse cells beyond baseline + x/y is unlikely to be chance under nulls "
    "that keep the value distribution, Moran's I or the full variogram. This settles significance, not size: the "
    "refit-bootstrap interval for the gain (−0.014 to +0.130, `CORE_STATISTICS.md`) still includes zero.",
    "- **Limits:** every null is stationary, while the real field's variance is concentrated in poorly covered edge "
    "cells (none of them collapse cells). The Shirzaei observation period is unknown, so this is a retrospective "
    "association, not a precursor.",
    "",
]


def run(adm):
    rng = np.random.default_rng(V.BURT_SEED)
    for res in (250, 200):  # same order as 11, so the surrogates are 11's
        c = S.core_cells(res, adm)
        y, fold, xb, v = c.positive.values.astype(int), c.fold.values, c[S.SET_B].values, c.shz_vlm.values
        xy = c[["x", "y"]].values
        lags = V.Lags(xy, res)
        plain, remapped, _ = V.burt_surrogates(v, cdist(xy, xy), lags, rng)
        chk = pd.read_csv(P.PILOT / "msr_variogram_check.csv").query("res == @res")
        for k, sv in zip(NEW, (plain, remapped)):  # the surrogates must be the ones 11 checked
            assert np.allclose(np.median([lags.vario(s) for s in sv], 0), chk[f"{k}: median"].values), f"{k} differs from 11"
        mb =S.metrics(y, S.oof(xb, y, fold, M.KIND))["pr"]
        obs = S.metrics(y, S.oof(np.c_[xb, v], y, fold, M.KIND))["pr"] - mb
        null = {k: np.array([S.metrics(y, S.oof(np.c_[xb, s], y, fold, M.KIND))["pr"] - mb for s in sv])
                for k, sv in zip(NEW, (plain, remapped))}
        pd.DataFrame({"surrogate": np.arange(M.N_SURR), "baseline_pr": mb, "observed_delta": obs,
                      **{f"delta_pr_{k}": null[k] for k in NEW}}).to_csv(P.PILOT / f"variogram_null_{res}m.csv", index=False)
        print(res, "done", flush=True)


def fmt_p(v):
    return "< 0.001" if v < 0.001 else f"{v:.3f}"


def table(res):
    cs = pd.read_csv(P.PILOT / "core_statistics.csv")
    r9 = cs[(cs["Cell size"] == f"{res} m") & (cs.Model == M.KIND) & (cs.Metric == "PR AUC")].iloc[0]
    msr = pd.read_csv(P.PILOT / f"msr_null_{res}m.csv")
    vn = pd.read_csv(P.PILOT / f"variogram_null_{res}m.csv")
    obs = vn.observed_delta.iloc[0]
    assert abs(obs - r9["observed change"]) < 1e-9, "observed change differs from 09"
    rows = []
    for mode in ("free", "within-block"):
        name = f"{mode.capitalize()} permutation"
        rows.append({"Null": name, "What it reproduces": KEEPS[name], "Draws": f"{int(r9.permutations):,}",
                     "Null median": f"{r9[f'null median, {mode}']:+.3f}", "Null 95th / 99th percentile": "–",
                     "Draws ≥ observed": "–", "p": fmt_p(r9[f"p, {mode}"]), "Source": "`CORE_STATISTICS.md`"})
    nulls = {"MSR": (msr["delta_pr_MSR"], "`MSR_NULL.md`"),
             "MSR, amplitude-adjusted": (msr["delta_pr_MSR, amplitude-adjusted"], "`MSR_NULL.md`"),
             **{k: (vn[f"delta_pr_{k}"], "this run") for k in NEW}}
    for name, (nv, src) in nulls.items():
        nv = nv.values
        hits = int((nv >= obs - 1e-12).sum())
        rows.append({"Null": name, "What it reproduces": KEEPS[name], "Draws": f"{len(nv):,}",
                     "Null median": f"{np.median(nv):+.3f}",
                     "Null 95th / 99th percentile": f"{np.percentile(nv, 95):+.3f} / {np.percentile(nv, 99):+.3f}",
                     "Draws ≥ observed": f"{hits}", "p": fmt_p((1 + hits) / (1 + len(nv))), "Source": src})
    return pd.DataFrame(rows), obs, r9, nulls


def figure(res_tables):
    fig, ax = plt.subplots(2, 1, figsize=(9, 9))
    cols = {"MSR": "0.35", "MSR, amplitude-adjusted": "tab:purple", "Variogram-matching": "tab:orange",
            "Variogram-matching, observed values": "tab:red"}
    for a, (res, (t, obs, _, nulls)) in zip(ax, res_tables.items()):
        allv = np.concatenate([nv.values for nv, _ in nulls.values()])
        bins = np.linspace(allv.min(), max(allv.max(), obs), 50)
        p = dict(zip(t.Null, t.p))
        for name, (nv, _) in nulls.items():
            a.hist(nv, bins=bins, histtype="step", lw=1.5, color=cols[name], label=f"{name} (p = {p[name]})")
        a.axvline(obs, color="tab:blue", lw=2, label=f"observed {obs:+.3f}")
        a.set(xlabel="Change in out-of-fold PR AUC when velocity is added", ylabel="Surrogate fields",
              title=f"Core, {res} m{' (primary)' if res == 250 else ''}, logistic regression: {M.N_SURR} surrogates per null")
        a.legend(fontsize=9.5)
    fig.tight_layout()
    fig.savefig(P.PILOT / "variogram_null.png", dpi=130)
    plt.close(fig)


def main():
    if "--report-only" not in sys.argv:
        run(gpd.read_file(P.RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(P.CRS))
    tabs = {res: table(res) for res in (250, 200)}
    for res, (t, obs, _, _) in tabs.items():
        print(res, f"observed {obs:+.3f}")
        print(t.drop(columns=["What it reproduces", "Source"]).to_string(index=False))
    figure(tabs)
    t250, obs250, r9, _ = tabs[250]
    lines = [
        "# Primary core test under a variogram-matching null",
        "",
        "**Primary analysis, unchanged:** historic core, 250 m, logistic regression, baseline + x/y vs baseline + x/y + Shirzaei "
        f"velocity, statistic = change in out-of-fold PR AUC ({r9['baseline + x/y']:.3f} → {r9['+ velocity']:.3f}, "
        f"{obs250:+.3f}). Same cells, folds (seed 42) and settings as `CORE_STATISTICS.md` and `MSR_NULL.md`; 200 m is "
        "robustness only.",
        "**Reproduce:** `.venv/bin/python scripts/12_variogram_null.py` (after 09–11).",
        "",
        "- **New nulls:** the two variogram-matching nulls of `MSR_VARIOGRAM_CHECK.md` (Burt et al. 2020), plain and "
        "rank-remapped to the observed values, with the same 999 surrogates per null. They were chosen there on how well "
        "they reproduce the velocity variogram, before any of their p-values.",
        "- **Test:** velocity is replaced by each surrogate and the velocity model refitted on the same folds. "
        "p = (1 + draws with a change ≥ observed) / (1 + draws).",
        "- **Earlier nulls** are copied from their reports, so every null of the primary test is in one table.",
        "",
        *READING,
        "## All nulls, 250 m (primary)",
        "",
        P.md_table(t250),
        "",
        f"## All nulls, 200 m (robustness; observed change {tabs[200][1]:+.3f})",
        "",
        P.md_table(tabs[200][0]),
        "",
        "Figure: `variogram_null.png` (null distributions of the four surrogate nulls with the observed change).",
        "",
    ]
    (P.PILOT / "VARIOGRAM_NULL.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
