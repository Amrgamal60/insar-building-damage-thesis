"""Statistics for the historic-core velocity result: baseline + x/y (B) vs baseline + x/y + Shirzaei velocity (D).
No new features and no tuning. The same 63 events, the same Shirzaei-covered core cells and the same primary
folds (seed 42) as 07/08; the cells come from 07's saved grids.

Primary test, fixed before this run: logistic regression, 250 m, change in PR AUC. Everything else is secondary.
1. Refit block bootstrap: 2 km blocks are resampled with replacement, and copies keep their block's fold, so no
   cell is in its own training set. Both models are refitted, and the out-of-fold change is recomputed. Reports
   2.5-97.5 percentiles.
2. Permutation tests: velocity is shuffled and model D refitted, while B is unchanged. There are two versions:
   (a) free = among all core cells; (b) within-block = only inside each 2 km block. The within-block version keeps
   the ~2 km velocity pattern, so it asks whether finer-scale alignment adds anything.
   One-sided p = (1 + number of null changes >= observed) / (1 + permutations).
Outputs: data/pilot/core_statistics.csv and data/pilot/CORE_STATISTICS.md."""
import importlib.util
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from joblib import Parallel, delayed
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pilot", ROOT / "scripts/07_pilot_models.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
spec8 = importlib.util.spec_from_file_location("checks", ROOT / "scripts/08_location_checks.py")
C8 = importlib.util.module_from_spec(spec8)
spec8.loader.exec_module(C8)

SET_B = P.BASELINE + ["x_km", "y_km"]
N = {"logistic regression": 2000, "random forest": 500}  # resamples and permutations per test
METRICS = [("pr", "PR AUC"), ("roc", "ROC AUC"), ("top10", "Collapse cells in top 10%")]
READING = [  # written after the 2026-09-29 run
    "## Result",
    "",
    "- **Primary test: the association passes both permutation tests, but the size of the gain is uncertain.** "
    "Logistic regression at 250 m: PR AUC 0.328 → 0.372 (+0.044). Free permutation p = 0.011, within-block p = 0.018. "
    "The refit-bootstrap interval for the change, −0.014 to +0.130, includes zero.",
    "- **Same picture at 200 m:** PR AUC +0.093 (p < 0.001 in both permutation tests; interval −0.034 to +0.159). ROC AUC "
    "and top-10% capture give p = 0.003–0.051 across both sizes, with every interval including zero.",
    "- **Random forest: not significant.** At 250 m p = 0.05–0.11 for all three metrics; at 200 m there is no clear gain.",
    "- **Reading:** on these 32 core collapse cells, velocity's link to collapse cells beyond baseline + x/y is unlikely to "
    "be chance. The within-block null gives similar p-values, so it is not only a ~2 km pattern. How much it improves the "
    "ranking in another sample of blocks is not pinned down.",
    "- **Limits:** the permutations break velocity's spatial smoothness below 2 km, so a smooth-field null could be "
    "stricter. Only the primary test was fixed in advance; there is no multiple-test correction. The Shirzaei period is "
    "unknown, so this is a retrospective association.",
    "",
]


def model(kind):  # same settings as 07; one core per forest, the resamples run in parallel instead
    if kind == "logistic regression":
        return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))
    return RandomForestClassifier(n_estimators=500, min_samples_leaf=5, max_features="sqrt",
                                  class_weight="balanced_subsample", n_jobs=1, random_state=0)


def oof(X, y, fold, kind):
    s = np.full(len(y), np.nan)
    for k in range(P.N_FOLDS):
        tr, te = fold != k, fold == k
        if te.any() and y[tr].sum() > 0:
            s[te] = model(kind).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return s


def metrics(y, s):
    return {"pr": average_precision_score(y, s), "roc": roc_auc_score(y, s), "top10": P.recall_top(y, s)}


def core_cells(res, adm):
    c = pd.read_csv(P.PILOT / f"cells_{res}m.csv")
    core = adm[adm.shapeName.isin(C8.CORE)].union_all()
    c = c[shapely.contains_xy(core, c.x.values, c.y.values) & (c.shz_n > 0)]
    c = c[np.isfinite(c[P.BASELINE + ["shz_vlm"]]).all(axis=1)].reset_index(drop=True)
    c["x_km"], c["y_km"] = c.x / 1000, c.y / 1000
    return c


def boot_rep(seed, c, kind):
    rng = np.random.default_rng(seed)
    blocks = c.block.unique()
    idx = np.concatenate([np.flatnonzero(c.block.values == b) for b in rng.choice(blocks, len(blocks), replace=True)])
    d = c.iloc[idx]
    y, fold = d.positive.values.astype(int), d.fold.values
    sb, sd = oof(d[SET_B].values, y, fold, kind), oof(np.c_[d[SET_B].values, d.shz_vlm.values], y, fold, kind)
    ok = np.isfinite(sb) & np.isfinite(sd)
    if not 0 < y[ok].sum() < ok.sum():
        return None
    mb, md = metrics(y[ok], sb[ok]), metrics(y[ok], sd[ok])
    return {m: md[m] - mb[m] for m in md}


def perm_rep(seed, c, kind, mode, mb):
    rng = np.random.default_rng(10_000 + seed)
    v = c.shz_vlm.values.copy()
    if mode == "free":
        v = rng.permutation(v)
    else:
        for b in np.unique(c.block.values):
            i = np.flatnonzero(c.block.values == b)
            v[i] = rng.permutation(v[i])
    y, fold = c.positive.values.astype(int), c.fold.values
    md = metrics(y, oof(np.c_[c[SET_B].values, v], y, fold, kind))
    return {m: md[m] - mb[m] for m in md}


def test(res, kind, c):
    y, fold = c.positive.values.astype(int), c.fold.values
    mb = metrics(y, oof(c[SET_B].values, y, fold, kind))
    md = metrics(y, oof(np.c_[c[SET_B].values, c.shz_vlm.values], y, fold, kind))
    obs = {m: md[m] - mb[m] for m in md}
    n = N[kind]
    boots = [b for b in Parallel(n_jobs=-1)(delayed(boot_rep)(s, c, kind) for s in range(n)) if b is not None]
    nulls = {mode: Parallel(n_jobs=-1)(delayed(perm_rep)(s, c, kind, mode, mb) for s in range(n))
             for mode in ("free", "within-block")}
    rows = []
    for m, label in METRICS:
        bt = np.array([b[m] for b in boots])
        row = {"Cell size": f"{res} m", "Model": kind, "Metric": label, "Cells (collapse cells)": f"{len(c)} ({int(y.sum())})",
               "baseline + x/y": mb[m], "+ velocity": md[m], "observed change": obs[m],
               "bootstrap 2.5%": np.percentile(bt, 2.5), "bootstrap 97.5%": np.percentile(bt, 97.5),
               "bootstrap resamples": len(bt)}
        for mode in ("free", "within-block"):
            nv = np.array([r[m] for r in nulls[mode]])
            row[f"p, {mode}"] = (1 + (nv >= obs[m] - 1e-12).sum()) / (1 + len(nv))
            row[f"null median, {mode}"] = np.median(nv)
        row["permutations"] = n
        rows.append(row)
    return rows


def fmt_p(v):
    return "< 0.001" if v < 0.001 else f"{v:.3f}"


def fmt_change(m, v):
    return f"{100 * v:+.0f} pts" if m == "Collapse cells in top 10%" else f"{v:+.3f}"


def fmt_level(m, v):
    return f"{v:.0%}" if m == "Collapse cells in top 10%" else f"{v:.3f}"


def main():
    adm = gpd.read_file(P.RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(P.CRS)
    if "--report-only" in sys.argv:  # rebuild the report from the saved run
        rows = pd.read_csv(P.PILOT / "core_statistics.csv").to_dict("records")
    else:
        rows = []
        for res in P.RESOLUTIONS:
            c = core_cells(res, adm)
            for kind in ("logistic regression", "random forest"):
                rows += test(res, kind, c)
                print(res, kind, "done", flush=True)
        pd.DataFrame(rows).to_csv(P.PILOT / "core_statistics.csv", index=False)
    show = pd.DataFrame([{
        "Cell size": r["Cell size"], "Model": r["Model"], "Metric": r["Metric"], "Cells (collapse cells)": r["Cells (collapse cells)"],
        "Baseline + x/y → + velocity": f"{fmt_level(r['Metric'], r['baseline + x/y'])} → {fmt_level(r['Metric'], r['+ velocity'])}",
        "Change": fmt_change(r["Metric"], r["observed change"]),
        "95% refit-bootstrap interval": f"{fmt_change(r['Metric'], r['bootstrap 2.5%'])} to {fmt_change(r['Metric'], r['bootstrap 97.5%'])}",
        "p, free permutation": fmt_p(r["p, free"]), "p, within-block permutation": fmt_p(r["p, within-block"]),
    } for r in rows])
    print(show.to_string(index=False))
    lines = [
        "# Statistics for the historic-core velocity result",
        "",
        "**Comparison:** baseline + x/y vs baseline + x/y + Shirzaei velocity, on the Shirzaei-covered cells of the historic core "
        "(the 7 central districts named in the audit). Same 63 events, same primary spatial folds (seed 42), no new features, "
        "no tuning.",
        "**Reproduce:** `.venv/bin/python scripts/09_core_statistics.py` (after 07 and 08).",
        "**Primary test, fixed before this run:** logistic regression, 250 m, change in PR AUC. Everything else is secondary, "
        "with no correction for multiple tests.",
        "",
        f"- **Refit block bootstrap** ({N['logistic regression']:,} resamples for logistic regression, {N['random forest']} for the "
        "random forest): 2 km blocks are resampled with replacement, and copies keep their block's fold. Both models are refitted "
        "and the out-of-fold change is recomputed; the interval is the 2.5–97.5 percentiles.",
        "- **Free permutation:** velocity is shuffled among all core cells and the velocity model refitted; this tests any "
        "association beyond baseline + x/y.",
        "- **Within-block permutation:** velocity is shuffled only inside each 2 km block. The null keeps the ~2 km velocity "
        "pattern, so this asks whether finer-scale alignment with collapse cells adds anything.",
        "- **p-values** are one-sided: (1 + null changes ≥ observed) / (1 + permutations); < 0.001 = no permutation reached "
        "the observed change.",
        "",
        *READING,
        P.md_table(show),
        "",
    ]
    (P.PILOT / "CORE_STATISTICS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
