"""Pre-registered LiCSAR test (data/pilot/LICSAR_TEST_PLAN.md): does LiCSAR vertical velocity, with a known observation
period, repeat the historic-core result of Shirzaei velocity?

Primary, as fixed in the plan: the 241 historic-core cells at 250 m of CORE_STATISTICS.md that have a LiCSAR value;
logistic regression; baseline + x/y vs baseline + x/y + LiCSAR vertical velocity P1 (first epoch to 2016-12-31);
statistic = change in out-of-fold PR AUC. Same 63 events, folds (seed 42), features and settings as 09-12.
Six nulls on the LiCSAR field, as in VARIOGRAM_NULL.md: free and within-block permutation (2,000 each, 09's seeds),
MSR and amplitude-adjusted MSR (999 each, 10's weights rule and seed) and variogram-matching, plain and rank-remapped
(999 each, 11's method and seed). p = (1 + draws with a change >= observed) / (1 + draws).
Replicates only if (1) the change is positive, (2) the collapse cells' median vertical velocity is below the
background cells' and (3) the largest p of the six nulls is below 0.05. Otherwise: not replicated.
Secondary (reported, no decision): 1 all core cells with a LiCSAR value; 2 200 m; 3 random forest (500 draws per null,
09's budget); 4 P2, the full period; 5 each frame's line-of-sight velocity.
Stages: --check builds the surrogates and checks their variograms against each LiCSAR field, with no model fits
(licsar_variogram_check.csv, LICSAR_VARIOGRAM_CHECK.md); it is read before the default stage computes any p-value
(licsar_test_nulls.csv, licsar_test.csv, licsar_test.png, LICSAR_TEST.md); --report-only rebuilds these from the saved
null draws. --validate runs the same code on the Shirzaei field and checks that it reproduces the null draws of 09, 10
and 12. --jobs N limits the parallel workers."""
import importlib.util
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import shapely
from joblib import Parallel, delayed
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from scipy.spatial.distance import cdist
from scipy.stats import skew
from sklearn.metrics import roc_auc_score

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check11", ROOT / "scripts/11_msr_variogram_check.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)
M, S, P = V.M, V.S, V.P

LR, RF = "logistic regression", "random forest"
PERM = {LR: 2000, RF: 500}  # draws per permutation null, as in 09
SURR = {LR: M.N_SURR, RF: 500}  # draws per surrogate null
PERMS = ["Free permutation", "Within-block permutation"]
SURRS = ["MSR", "MSR, amplitude-adjusted", "Variogram-matching", "Variogram-matching, observed values"]
NULLS = PERMS + SURRS
TESTS = [  # key, label, cell size, cells, velocity column, model
    ("primary", "Primary: vertical P1, Shirzaei-test cells, 250 m, logistic regression", 250, "shirzaei", "lic_ud_p1", LR),
    ("s1", "1. All core cells with a LiCSAR value", 250, "all", "lic_ud_p1", LR),
    ("s2", "2. 200 m cells", 200, "shirzaei", "lic_ud_p1", LR),
    ("s3", "3. Random forest", 250, "shirzaei", "lic_ud_p1", RF),
    ("s4", "4. P2, full period", 250, "shirzaei", "lic_ud_p2", LR),
    ("s5a", "5. 065D line of sight, P1", 250, "shirzaei", "lic_los_065D_p1", LR),
    ("s5b", "5. 131A line of sight, P1", 250, "shirzaei", "lic_los_131A_p1", LR),
]
CHECKED = [t for t in TESTS if t[0] != "s3"]  # s3 uses the primary field and the first 500 of its surrogates
READING = [  # written after the 2026-09-30 run
    "## Result",
    "",
    "- **Decision: replicated.** Primary test on 241 core cells (32 collapse cells, none dropped): PR AUC 0.328 → 0.413 "
    "(+0.085). The collapse cells' median vertical velocity is 0.06 mm/yr against 0.64 for background cells "
    "(single-layer ROC AUC 0.44). p = 0.001–0.005 under the six nulls; the largest, 0.005, comes from the within-block "
    "permutation and both variogram-matching nulls. All three criteria hold.",
    "- **Larger than with Shirzaei** on the same cells, events, folds and model: Shirzaei gave +0.044 (largest p 0.023, "
    "`VARIOGRAM_NULL.md`).",
    "- **Secondary tests all point the same way.** The change is +0.069 to +0.085 in every test, and the collapse cells' "
    "median is lower in every test. The largest p is below 0.05 in five of six: all 341 core cells with a LiCSAR value "
    "(0.007), random forest (0.038; with Shirzaei it was not significant, p = 0.05–0.11), P2 (0.008) and each frame's "
    "line of sight alone (0.009 and 0.005). On the 341 cells velocity alone does not separate the collapse cells "
    "(single-layer ROC AUC 0.50), so the gain there comes only together with the baseline and location. At 200 m the "
    "permutation and MSR nulls give p ≤ 0.015, but the variogram-matching nulls give 0.102 and 0.090, so the 200 m "
    "result does not pass them.",
    "- **Reading:** an independent InSAR processing with a known observation period (October/November 2014 to December "
    "2016, the collapse period) repeats the core association. Beyond the baseline and location, velocity helps rank the "
    "core cells with a collapse, and those cells move down relative to the background cells (median 0.6 mm/yr lower). "
    "It holds with a random forest, over the full period and in each viewing geometry alone.",
    "- **Limits:** (1) The variogram check found every null rougher than the LiCSAR field at the shortest lag, which "
    "tends to make p too small; the closest null, plain variogram-matching, gives 0.005 at 250 m but 0.102 at 200 m, "
    "where the field is smoothest. (2) The events, cells and baseline are the Shirzaei test's, so this replicates the "
    "velocity product, not the sample. (3) The size of the gain is not re-estimated here; with Shirzaei its refit-"
    "bootstrap interval included zero. (4) P1 rests mainly on November 2015 to December 2016 because of network gaps "
    "(`LICSAR_CELLS.md`). (5) The velocity overlaps the collapse period, so this is a retrospective association, not a "
    "precursor.",
    "",
]
CHECK_READING = [  # written on 2026-09-30 after the check and before the test, so before any LiCSAR p-value
    "## Reading (written after this check, before any p-value)",
    "",
    "- **The LiCSAR field is smoother at short range than the Shirzaei field.** At 250 m its lag-1 semivariance is 0.37 "
    "(mm/yr)², 11% of its value at 1.5 km; Shirzaei's was 1.06, 26% (`MSR_VARIOGRAM_CHECK.md`). LiCSAR pixels are about "
    "100 m and were multilooked and filtered before unwrapping, so neighbouring cells share signal and noise.",
    "- **No null reproduces this at the shortest lags.** On the primary field the surrogates are rougher than the observed "
    "field: MSR at lags 1–3 (median 2.6×, 1.7× and 1.4× the observed), amplitude-adjusted MSR at lags 1–2, "
    "variogram-matching with the observed values at lags 1–2, and plain variogram-matching only at lag 1 (median 1.9×; "
    "the observed value is just below the 95% range). From 1 km on, every null is inside its range. The secondary fields "
    "show the same pattern, most strongly at 200 m, where MSR is outside at 9 of 16 lags.",
    "- **What this means for the p-values:** a null that is rougher than the real field tends to produce fewer large chance "
    "gains, so its p-value tends to be too small. Plain variogram-matching is the closest match, so its p-value should be "
    "weighed most; the permutation nulls keep no spatial structure at all. The decision rule already uses the largest p of "
    "the six, so nothing in the plan changes.",
    "",
]


def test_cells(res, which, col, adm):
    """The test's cells and the number before cells without a velocity value are dropped."""
    if which == "shirzaei":
        c = S.core_cells(res, adm)  # 09's cells: core, Shirzaei-covered, all baseline inputs
    else:
        c = pd.read_csv(P.PILOT / f"cells_{res}m.csv")
        core = adm[adm.shapeName.isin(S.C8.CORE)].union_all()
        c = c[shapely.contains_xy(core, c.x.values, c.y.values) & np.isfinite(c[P.BASELINE]).all(axis=1)].reset_index(drop=True)
        c["x_km"], c["y_km"] = c.x / 1000, c.y / 1000
    n0 = len(c)
    if col not in c:
        c = c.merge(pd.read_csv(P.PILOT / f"licsar_cells_{res}m.csv")[["row", "col", col]], on=["row", "col"], how="left")
    return c[np.isfinite(c[col])].reset_index(drop=True), n0


def surrogates(v, xy, res, n):
    """The four surrogate nulls for field v, each from a fresh generator with 10's or 11's seed."""
    w, t = M.dbmem_weights(xy)
    basis, _ = M.mem_basis(w)
    rng = np.random.default_rng(M.SEED)
    out = {"MSR": M.surrogates(v, basis, rng), "MSR, amplitude-adjusted": M.surrogates(v, basis, rng, amplitude_adjusted=True)}
    lags = V.Lags(xy, res)
    out[SURRS[2]], out[SURRS[3]], _ = V.burt_surrogates(v, cdist(xy, xy), lags, np.random.default_rng(V.BURT_SEED))
    return {k: s[:n] for k, s in out.items()}, dict(w=w, t=t, lags=lags, q=M.queen_weights(xy, res))


def permutations(v, blocks, mode, n):
    """09's permutations: seed 10,000 + draw; free, or within each 2 km block."""
    out = []
    for seed in range(n):
        rng = np.random.default_rng(10_000 + seed)
        p = v.copy()
        if mode == "free":
            p = rng.permutation(p)
        else:
            for b in np.unique(blocks):
                i = np.flatnonzero(blocks == b)
                p[i] = rng.permutation(p[i])
        out.append(p)
    return np.array(out)


def delta(s, xb, y, fold, kind, mb):
    return S.metrics(y, S.oof(np.c_[xb, s], y, fold, kind))["pr"] - mb


def check_rows(key, res, v, surr, aux):
    lags, obs = aux["lags"], aux["lags"].vario(v)
    summ, per_lag = [], []
    for k in SURRS:
        vs = np.array([lags.vario(s) for s in surr[k]])
        lo, hi, med = np.percentile(vs, 2.5, 0), np.percentile(vs, 97.5, 0), np.median(vs, 0)
        inside, ratio = (obs >= lo) & (obs <= hi), med / obs
        mw = np.array([M.morans_i(s, aux["w"]) for s in surr[k]])
        mq = np.array([M.morans_i(s, aux["q"]) for s in surr[k]])
        summ.append({"test": key, "Null": k, "Lags inside the 95% range": f"{int(inside.sum())} of {M.MAX_LAG}",
                     "Median / observed, lags 1–4": " · ".join(f"{x:.2f}" for x in ratio[:4]),
                     "Median / observed, lags 5–16 (range)": f"{ratio[4:].min():.2f}–{ratio[4:].max():.2f}",
                     "Moran's I, MEM weights: observed / 95% range": f"{M.morans_i(v, aux['w']):.3f} / {np.percentile(mw, 2.5):.3f}–{np.percentile(mw, 97.5):.3f}",
                     "Moran's I, queen: observed / 95% range": f"{M.morans_i(v, aux['q']):.3f} / {np.percentile(mq, 2.5):.3f}–{np.percentile(mq, 97.5):.3f}",
                     "Skewness: observed / median": f"{skew(v):.2f} / {np.median(skew(surr[k], axis=1)):.2f}",
                     "Variance: median / observed": f"{np.median(surr[k].var(1)) / v.var():.2f}"})
        for h in range(M.MAX_LAG):
            per_lag.append({"test": key, "null": k, "lag": h + 1, "km": (h + 1) * res / 1000, "pairs": int(lags.pairs[h]),
                            "observed": obs[h], "median": med[h], "2.5%": lo[h], "97.5%": hi[h]})
    return summ, per_lag


def run_check(adm):
    summ, per_lag, cells = [], [], []
    for key, label, res, which, col, kind in CHECKED:
        c, n0 = test_cells(res, which, col, adm)
        v, xy = c[col].values, c[["x", "y"]].values
        surr, aux = surrogates(v, xy, res, SURR[kind])
        s, pl = check_rows(key, res, v, surr, aux)
        summ += s
        per_lag += pl
        cells.append({"Test": label, "Cells kept / before (collapse cells)": f"{len(c)} / {n0} ({int(c.positive.sum())})",
                      "MST threshold t (m)": f"{aux['t']:.0f}"})
        print(key, "checked", flush=True)
    pd.DataFrame(per_lag).to_csv(P.PILOT / "licsar_variogram_check.csv", index=False)
    summ, cells = pd.DataFrame(summ), pd.DataFrame(cells)
    print(cells.to_string(index=False))
    print(summ.to_string(index=False))
    names = {t[0]: t[1] for t in TESTS}
    lines = ["# Variogram check of the six nulls on the LiCSAR fields",
             "",
             "**Plan:** `LICSAR_TEST_PLAN.md` (each null's variogram is re-checked on the LiCSAR field before its p-value is read). "
             "**Reproduce:** `.venv/bin/python scripts/17_licsar_test.py --check` (after 16). No model is fitted here.",
             "",
             "- Same checks as `MSR_VARIOGRAM_CHECK.md`, on each test's LiCSAR field: semivariogram at lags 1–16 cell widths, "
             "Moran's I, skewness and variance of the surrogates against the observed field. The two permutation nulls keep "
             "no spatial structure by design and are not checked. Test 3 (random forest) uses the primary field and the "
             "first 500 of its surrogates.",
             "",
             *CHECK_READING,
             "## Cells",
             "",
             P.md_table(cells),
             ""]
    for key, _, res, *_ in CHECKED:
        d = pd.DataFrame(per_lag).query("test == @key")
        lag_t = {"Lag (km)": [f"{x:.2f}" for x in d[d.null == "MSR"].km], "Cell pairs": [f"{x:,}" for x in d[d.null == "MSR"].pairs],
                 "Observed": [f"{x:.2f}" for x in d[d.null == "MSR"].observed]}
        for k in SURRS:
            e = d[d.null == k]
            lag_t[k] = [f"{m:.2f} ({a:.2f}–{b:.2f}){' ✗' if not a <= o <= b else ''}"
                        for m, a, b, o in zip(e["median"], e["2.5%"], e["97.5%"], e.observed)]
        lines += [f"## {names[key]}", "", P.md_table(summ.query("test == @key").drop(columns="test")), "",
                  "Semivariogram by lag (median and 95% range of the surrogates; ✗ = observed outside):", "",
                  P.md_table(pd.DataFrame(lag_t)), ""]
    (P.PILOT / "LICSAR_VARIOGRAM_CHECK.md").write_text("\n".join(lines), encoding="utf-8")


def run_test(res, which, col, kind, adm, jobs, check=None, saved=None):
    """Observed change, direction and the six null distributions for one test (saved = null draws from a finished run)."""
    c, n0 = test_cells(res, which, col, adm)
    y, fold, xb, v = c.positive.values.astype(int), c.fold.values, c[S.SET_B].values, c[col].values
    mb = S.metrics(y, S.oof(xb, y, fold, kind))["pr"]
    md = S.metrics(y, S.oof(np.c_[xb, v], y, fold, kind))["pr"]
    if saved is not None:
        null = saved
    else:
        surr, aux = surrogates(v, c[["x", "y"]].values, res, SURR[kind])
        if check is not None:  # the surrogates must be the ones the check looked at
            for k in SURRS:
                med = np.median([aux["lags"].vario(s) for s in surr[k]], 0)
                assert np.allclose(med, check.query("null == @k")["median"].values), f"{k} differs from the check"
        fields = {PERMS[0]: permutations(v, c.block.values, "free", PERM[kind]),
                  PERMS[1]: permutations(v, c.block.values, "within-block", PERM[kind]), **surr}
        null = {k: np.array(Parallel(n_jobs=jobs)(delayed(delta)(s, xb, y, fold, kind, mb) for s in f)) for k, f in fields.items()}
    return dict(c=c, n0=n0, y=y, v=v, mb=mb, md=md, obs=md - mb, null=null,
                p={k: (1 + (nv >= md - mb - 1e-12).sum()) / (1 + len(nv)) for k, nv in null.items()},
                med_pos=np.median(v[y == 1]), med_bg=np.median(v[y == 0]), auc=roc_auc_score(y, v))


def validate(adm, jobs):
    """The test code on the Shirzaei field must reproduce 09's p-values and 10's and 12's null draws."""
    r = run_test(250, "shirzaei", "shz_vlm", LR, adm, jobs)
    cs = pd.read_csv(P.PILOT / "core_statistics.csv")
    r9 = cs[(cs["Cell size"] == "250 m") & (cs.Model == LR) & (cs.Metric == "PR AUC")].iloc[0]
    msr, vn = pd.read_csv(P.PILOT / "msr_null_250m.csv"), pd.read_csv(P.PILOT / "variogram_null_250m.csv")
    ok = {"observed change (09)": abs(r["obs"] - r9["observed change"]) < 1e-9,
          "free permutation p (09)": abs(r["p"][PERMS[0]] - r9["p, free"]) < 1e-12,
          "within-block permutation p (09)": abs(r["p"][PERMS[1]] - r9["p, within-block"]) < 1e-12,
          **{f"{k} draws (10)": np.allclose(r["null"][k], msr[f"delta_pr_{k}"]) for k in SURRS[:2]},
          **{f"{k} draws (12)": np.allclose(r["null"][k], vn[f"delta_pr_{k}"]) for k in SURRS[2:]}}
    for k, v in ok.items():
        print(f"{'OK ' if v else 'FAIL'} {k}")
    print("p:", {k: round(v, 3) for k, v in r["p"].items()})
    assert all(ok.values()), "the test code does not reproduce the Shirzaei results"


def fmt_p(v):
    return "< 0.001" if v < 0.001 else f"{v:.3f}"


def figure(r, res):
    fig, ax = plt.subplots(2, 1, figsize=(9, 12), gridspec_kw={"height_ratios": [1.1, 1]})
    c, v, y = r["c"], r["v"], r["y"]
    pc = PatchCollection([Rectangle((x - res / 2, yy - res / 2), res, res) for x, yy in c[["x", "y"]].values], cmap="magma",
                         edgecolor=np.where(y == 1, "k", "none").tolist(), linewidth=1.4)
    pc.set_array(v)
    pc.set_clim(np.percentile(v, 2), np.percentile(v, 98))
    ax[0].add_collection(pc)
    ax[0].autoscale_view()
    ax[0].set_aspect("equal")
    ax[0].set_axis_off()
    ax[0].set_title(f"(a) LiCSAR vertical velocity P1, core cells of the primary test ({len(c)})\n"
                    "black outline = cell with a pilot collapse", fontsize=12, loc="left")
    fig.colorbar(pc, ax=ax[0], extend="both", shrink=0.8, label="mm/yr, positive up (2nd–98th percentile)")
    cols = dict(zip(NULLS, ["0.6", "0.3", "tab:green", "tab:purple", "tab:orange", "tab:red"]))
    allv = np.concatenate(list(r["null"].values()))
    bins = np.linspace(min(allv.min(), r["obs"]), max(allv.max(), r["obs"]), 50)
    for k, nv in r["null"].items():
        ax[1].hist(nv, bins=bins, histtype="step", lw=1.4, color=cols[k], label=f"{k} (p = {fmt_p(r['p'][k])})")
    ax[1].axvline(r["obs"], color="tab:blue", lw=2, label=f"observed {r['obs']:+.3f}")
    ax[1].set(xlabel="Change in out-of-fold PR AUC when velocity is added", ylabel="Null draws")
    ax[1].set_title("(b) Primary test: observed change and the six nulls", fontsize=12, loc="left")
    ax[1].legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(P.PILOT / "licsar_test.png", dpi=130)
    plt.close(fig)


def main():
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else -1
    adm = gpd.read_file(P.RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(P.CRS)
    if "--validate" in sys.argv:
        return validate(adm, jobs)
    if "--check" in sys.argv:
        return run_check(adm)
    chk = pd.read_csv(P.PILOT / "licsar_variogram_check.csv")
    report_only = "--report-only" in sys.argv  # rebuild the report from the saved null draws
    saved = pd.read_csv(P.PILOT / "licsar_test_nulls.csv") if report_only else None
    R, rows, long = {}, [], []
    for key, label, res, which, col, kind in TESTS:
        sv = {k: saved[(saved.test == key) & (saved.null == k)].sort_values("draw").delta_pr.values for k in NULLS} if report_only else None
        r = R[key] = run_test(res, which, col, kind, adm, jobs, check=None if key == "s3" else chk[chk.test == key], saved=sv)
        for k, nv in r["null"].items():
            long.append(pd.DataFrame({"test": key, "null": k, "draw": np.arange(len(nv)), "delta_pr": nv}))
        rows.append({"test": key, "Test": label, "Cells kept / before (collapse cells)": f"{len(r['c'])} / {r['n0']} ({int(r['y'].sum())})",
                     "PR AUC: baseline + x/y → + velocity": f"{r['mb']:.3f} → {r['md']:.3f}", "Change": f"{r['obs']:+.3f}",
                     "Median velocity, collapse / background (mm/yr)": f"{r['med_pos']:.2f} / {r['med_bg']:.2f}",
                     "Single-layer ROC AUC": f"{r['auc']:.2f}",
                     **{f"p, {k}": fmt_p(r["p"][k]) for k in NULLS}, "Largest p": fmt_p(max(r["p"].values()))})
        print(key, rows[-1], flush=True)
    if not report_only:
        pd.concat(long).to_csv(P.PILOT / "licsar_test_nulls.csv", index=False)
    table = pd.DataFrame(rows)
    table.to_csv(P.PILOT / "licsar_test.csv", index=False)
    r = R["primary"]
    crit = [("1. PR AUC change is positive", f"{r['obs']:+.3f}", r["obs"] > 0),
            ("2. Collapse cells' median vertical velocity is below the background cells'",
             f"{r['med_pos']:.2f} vs {r['med_bg']:.2f} mm/yr", r["med_pos"] < r["med_bg"]),
            ("3. Largest p of the six nulls is below 0.05", fmt_p(max(r["p"].values())), max(r["p"].values()) < 0.05)]
    verdict = "Replicated" if all(m for *_, m in crit) else "Not replicated"
    dec = pd.DataFrame([{"Criterion": a, "Value": b, "Met": "yes" if m else "no"} for a, b, m in crit])
    nt = pd.DataFrame([{"Null": k, "Draws": f"{len(nv):,}", "Null median": f"{np.median(nv):+.3f}",
                        "Null 95th / 99th percentile": f"{np.percentile(nv, 95):+.3f} / {np.percentile(nv, 99):+.3f}",
                        "Draws ≥ observed": f"{int((nv >= r['obs'] - 1e-12).sum())}", "p": fmt_p(r["p"][k])}
                       for k, nv in r["null"].items()])
    figure(r, 250)
    print(dec.to_string(index=False), "\n", verdict)
    print(nt.to_string(index=False))
    lines = [
        "# LiCSAR test of the historic-core result",
        "",
        "**Plan, fixed before any LiCSAR velocity existed:** `LICSAR_TEST_PLAN.md`. **Velocity:** `LICSAR_CELLS.md`. "
        "**Null check, read before this run:** `LICSAR_VARIOGRAM_CHECK.md`.",
        "**Reproduce:** `.venv/bin/python scripts/17_licsar_test.py` (after 15, 16 and `17_licsar_test.py --check`).",
        "",
        "- **Primary test:** the historic-core cells at 250 m of `CORE_STATISTICS.md` that have a LiCSAR value; logistic "
        "regression; baseline + x/y vs baseline + x/y + LiCSAR vertical velocity P1 (first epoch to 2016-12-31); statistic = "
        "change in out-of-fold PR AUC. Same 63 events, folds (seed 42), features and settings as the Shirzaei test.",
        "- **Nulls:** the six of `VARIOGRAM_NULL.md`, fitted to the LiCSAR field: free and within-block permutation (2,000 draws "
        "each), MSR and amplitude-adjusted MSR (999 each) and variogram-matching, plain and with the observed values (999 each). "
        "p = (1 + draws with a change ≥ observed) / (1 + draws).",
        "- **Decision rule:** replicated only if all three criteria hold; otherwise not replicated. Secondary tests carry no decision.",
        "",
        f"## Decision: {verdict}",
        "",
        P.md_table(dec),
        "",
        *READING,
        "## Primary test: the six nulls",
        "",
        P.md_table(nt),
        "",
        "## All tests (secondary tests change one thing each; random forest: 500 draws per null)",
        "",
        P.md_table(table.drop(columns="test")),
        "",
        "Figure: `licsar_test.png` (a: LiCSAR vertical velocity in the primary cells; b: the six null distributions).",
        "",
    ]
    (P.PILOT / "LICSAR_TEST.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
