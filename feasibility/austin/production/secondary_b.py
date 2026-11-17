"""Test B secondary analyses (AUSTIN_PLAN.md §12 items 15-19 and the slip-rule sensitivity of §14; how each is computed is
fixed in §15, "Secondary analyses: how each is computed", 2026-11-15, before any secondary outcome is joined). Each
changes one thing in Test B (§8B-§10) and carries no decision.

Reuse (unchanged): run_tests.py (world, cases_of, LABEL), run_report.py (testb_panel, check_primary_b), frozen test_b.py
(fit_panel, null_test), testa_core.py (at_risk, window_of, MONTHS).
  field swap (15, 16, 17, slip sensitivity): the primary panel with the cell field replaced. run_report.testb_panel reads
             the field "v" of a cells file, so the variant field is written as "v" of a cells file in the output folder
             (cells, quarters, block unchanged; its SHA-256 is recorded), and the panel, fit and null are the primary's
             calls. The null is the Test B null of the same field (make_testb_surrogates.py, seed 2034, 999 draws); the
             surrogate file's field name and the SHA-256 of its null field are checked against the cells file.
  18         negative binomial (NB2, statsmodels NegativeBinomial, maximum likelihood) with log n as offset, quarter fixed
             effects and, instead of cell fixed effects, the cell means of the Baseline 1 features over the cell's
             eligible houses with complete inputs: age at 2018-08-01, log living area, log lot area, soil linear
             extensibility, slope, elevation, log income, slab-foundation share, x/y (§12.18 lists the Baseline 1
             features; the slab share is a Baseline 1 feature, as in the §10 null covariates). The features are
             centred and scaled over the rows used; velocity stays in mm/yr. Rows: the primary panel's rows (value and
             n > 0) whose cell has such houses. Errors clustered by 2 km block (statsmodels cluster, its default
             small-sample correction); rate ratio per IQR of velocity over the rows used with a normal 95% interval.
             Fit (nb_fit): Newton from the Poisson fit with alpha 0.1, accepted at max |score| <= 1e-6; otherwise
             Newton from the BFGS solution; a fit that reaches the optimum by neither stops the run. Statistic |beta|
             with the primary Test B surrogates (seed 2034), p as §10.
  19         monthly counts: rows (cell, month) for the 88 study months, y = the counted events of the month (run_tests
             cases_of, as the quarterly panel), n = the houses of the cell at risk on the day before the month starts
             (testa_core.at_risk, as the quarterly panel), v = the cell's 12-month velocity before the month (v_monthly);
             rows used: v has a value and n > 0. Fitted by the frozen test_b.fit_panel with the month label in its
             "quarter" column (month fixed effects) and null_test on the monthly Test B surrogates
             (make_testb_monthly_surrogates.py, seed 2034).
The command `anchor` runs the field-swap path with the primary field and checks it against run_tests.py's test_b.json
and test_b_panel.csv.

Usage
  python -I secondary_b.py run    --secondary NAME --mode decoy|real COMMON --events EV --cells CELLS --surrogates SB
         --out DIR [--workers N] [--draws n]
  python -I secondary_b.py anchor --mode decoy|real COMMON --events EV --cells CELLS --surrogates SB_V_2034
         --primary TEST_B_JSON --primary-panel TEST_B_PANEL_CSV --out DIR [--draws n]
  COMMON = --features --grid --episodes --censoring (checkpoint-1 tables, hash-checked)
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import platform  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import run_report as RR  # noqa: E402  (unchanged)
import statsmodels.api as sm  # noqa: E402
from scipy.stats import norm  # noqa: E402

RT, C, PS, TB = RR.RT, RR.C, RR.PS, RR.TB
SEED = 2034
SPECS = {
    "15_lag_1": dict(field="v_lag1", model="ppml"),
    "15_lag_3": dict(field="v_lag3", model="ppml"),
    "15_lag_6": dict(field="v_lag6", model="ppml"),
    "15_lag_12": dict(field="v_lag12", model="ppml"),
    "16_window_24": dict(field="v24", model="ppml"),
    "17_amplitude": dict(field="amp", model="ppml"),
    "17_local_relative_motion": dict(field="lrm", model="ppml"),
    "17_acceleration": dict(field="acc", model="ppml"),
    "slip_first_run_b": dict(field="v_run1", model="ppml"),
    "18_negative_binomial": dict(field="v", model="nb"),
    "19_monthly": dict(field="v_monthly", model="monthly"),
}
NB_FEATURES = ["age_at_start"] + C.STATIC + ["x_km", "y_km"]


def source_hashes():
    out = RR.source_hashes()
    out["secondary_b.py"] = C.sha256(HERE / "secondary_b.py")
    return out


def check_surrogates(S, run_json, field, field_name):
    """The Test B surrogate file was made from this field (make_testb_surrogates.py's field_sha256)."""
    assert str(S["field_name"]) == field_name and int(S["seed"]) == SEED, "surrogate file of another field or seed"
    use = np.isfinite(field).any(0)
    fsha = hashlib.sha256(np.ascontiguousarray(field[:, use].astype(np.float64)).tobytes()).hexdigest()
    info = json.loads(Path(run_json).read_text())
    assert info["field_sha256"] == fsha and info["field"] == field_name, "surrogate file not made from this field"
    return dict(field_sha256=fsha, surrogates_sha256=info["surrogates_sha256"], draws=info["draws"])


def variant_cells(cells, field_name, out):
    """A cells file whose "v" is the variant field (cells, quarters and block unchanged)."""
    with np.load(cells, allow_pickle=False) as z:
        d = dict(cells=z["cells"], quarters=z["quarters"], block=z["block"], v=z[field_name])
    path = out / f"cells_{field_name}_as_v.npz"
    with open(path, "wb") as fh:
        np.savez(fh, **d)
    return path, d["v"]


# ---------------------------------------------------------------- 18: negative binomial with area characteristics
def cell_features(h, grid, labels):
    g = pd.read_parquet(grid, columns=["prop_id", "cell250"])
    assert (g.prop_id.to_numpy() == h.prop_id.to_numpy()).all()
    hc = pd.Index(labels).get_indexer(g.cell250.to_numpy())
    assert (hc >= 0).all()
    c = h.complete_b1.to_numpy(bool)
    X = np.column_stack([C.decimal_year(C.START)[0] - h.loc[c, "year_built"].to_numpy(float),
                         h.loc[c, C.STATIC + ["x_km", "y_km"]].to_numpy(float)])
    n = np.bincount(hc[c], minlength=len(labels))
    with np.errstate(invalid="ignore", divide="ignore"):
        M = np.column_stack([np.bincount(hc[c], weights=X[:, k], minlength=len(labels)) for k in range(X.shape[1])]) / n[:, None]
    return pd.DataFrame(M, columns=NB_FEATURES, index=labels), n


def nb_design(panel, feats):
    Z = feats.loc[panel.cell.to_numpy()].to_numpy(float)
    Z = (Z - Z.mean(0)) / Z.std(0)
    Q = pd.get_dummies(panel.quarter.astype(str), drop_first=True, dtype=float).to_numpy()
    return np.column_stack([np.ones(len(panel)), panel.v.to_numpy(float), Z, Q])


SCORE_TOL = 1e-6


def nb_fit(y, X, log_n, groups):
    """Returns (beta, clustered se, route, alpha) of the velocity column (index 1); alpha is NB2's last parameter.
    Newton (100 iterations) from the Poisson fit of the same design and offset with alpha 0.1; if that does not reach a
    finite optimum with max |score| <= SCORE_TOL, Newton from the BFGS (2,000) solution; otherwise the fit fails.
    (statsmodels' default start diverges to NaN on these panels, and BFGS alone stops before the optimum.)"""
    mod = sm.NegativeBinomial(y, X, loglike_method="nb2", offset=log_n)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pois = sm.Poisson(y, X, offset=log_n).fit(method="newton", maxiter=100, disp=0)
        starts = [("newton from Poisson", np.r_[pois.params, 0.1])]
        for route, start in starts:
            try:
                res = mod.fit(method="newton", maxiter=100, disp=0, start_params=start, cov_type="cluster",
                              cov_kwds={"groups": groups})
                ok = bool(res.mle_retvals.get("converged", False) and np.isfinite(res.params).all()
                          and np.abs(mod.score(res.params)).max() <= SCORE_TOL)
            except (np.linalg.LinAlgError, ValueError, FloatingPointError):
                ok = False
            if ok:
                beta, se = float(res.params[1]), float(res.bse[1])
                if np.isfinite(se) and se > 0:
                    return beta, se, route, float(res.params[-1])
            if len(starts) == 1:
                b = mod.fit(method="bfgs", maxiter=2000, disp=0)
                starts.append(("newton from BFGS", b.params))
    raise RuntimeError("negative binomial fit did not reach the optimum")


_G = {}


def _nb_draw(d):
    P = _G
    field = np.asarray(P["S"][d])
    X = P["X"].copy()
    X[:, 1] = field[P["qi"], P["ci"]]
    assert np.isfinite(X[:, 1]).all()
    beta, se, route, _ = nb_fit(P["y"], X, P["log_n"], P["groups"])
    return d, abs(beta), route


def run_nb(panel, h, a, S, draws, workers):
    labels = np.load(a.cells, allow_pickle=False)["cells"]
    feats, n_complete = cell_features(h, a.grid, labels)
    ok = feats.loc[panel.cell.to_numpy()].notna().all(axis=1).to_numpy()
    p = panel[ok].reset_index(drop=True)
    X = nb_design(p, feats)
    groups = pd.Index(np.unique(p.block.astype(str))).get_indexer(p.block.astype(str))
    y, log_n = p.y.to_numpy(float), np.log(p.n.to_numpy(float))
    beta, se, route, alpha = nb_fit(y, X, log_n, groups)
    iqr = float(np.subtract(*np.percentile(p.v, [75, 25])))
    z = float(norm.ppf(0.975))
    observed = dict(beta=beta, clustered_se=se, velocity_iqr=iqr, rate_ratio_iqr=float(np.exp(beta * iqr)),
                    rate_ratio_ci95=[float(np.exp((beta - z * se) * iqr)), float(np.exp((beta + z * se) * iqr))],
                    null_statistic=abs(beta), fit_route=route, alpha=alpha, rows_input=int(len(panel)),
                    rows_used=int(len(p)), rows_dropped_cell_without_complete_house=int((~ok).sum()),
                    cells_used=int(p.cell.nunique()), blocks_used=int(len(np.unique(groups))), features=NB_FEATURES)
    qi = pd.Index(S["quarters"]).get_indexer(p.quarter)
    ci = pd.Index(S["cells"]).get_indexer(p.cell)
    assert (qi >= 0).all() and (ci >= 0).all()
    _G.update(S=S["fields"], X=X, qi=qi, ci=ci, y=y, log_n=log_n, groups=groups)
    stats, methods = np.full(draws, np.nan), [None] * draws
    with mp.get_context("fork").Pool(workers) as pool:
        for d, s, m in pool.imap_unordered(_nb_draw, range(draws), chunksize=2):
            stats[d], methods[d] = s, m
    _G.clear()
    assert np.isfinite(stats).all()
    exceed = int(np.sum(stats >= observed["null_statistic"]))
    return dict(observed=observed, statistics=stats.tolist(), exceedances=exceed, p_B=(1 + exceed) / (1 + draws),
                draws_fitted_from_bfgs_start=int(sum(m == "newton from BFGS" for m in methods)))


# ---------------------------------------------------------------- 19: monthly panel
def monthly_panel(h, world, grid, cells):
    """run_report.testb_panel's lines with calendar months in place of quarters (module docstring)."""
    house, date, key, t_ep, holds = world
    g = pd.read_parquet(grid, columns=["prop_id", "cell250"])
    assert (g.prop_id.to_numpy() == h.prop_id.to_numpy()).all()
    c = np.load(cells, allow_pickle=False)
    labels, months, block, v = c["cells"], c["months"], c["block"], c["v_monthly"]
    assert list(months) == C.MONTHS and v.shape == (len(months), len(labels))
    house_cell = pd.Index(labels).get_indexer(g.cell250.to_numpy())
    assert (house_cell >= 0).all()
    HV = np.ones((len(C.MONTHS), len(h)), bool)
    _, _, counted = RT.cases_of(house, date, key, h, t_ep, HV)
    mi = C.window_of(counted["date"])
    inm = mi >= 0
    M, NC = len(months), len(labels)
    y = np.zeros((M, NC), np.int64)
    np.add.at(y, (mi[inm], house_cell[counted["house"][inm]]), 1)
    t_dem = h.t_demolition.to_numpy("datetime64[ns]")
    n = np.zeros((M, NC), np.int64)
    for k, m in enumerate(pd.PeriodIndex(list(months), freq="M")):
        ar = C.at_risk(m.start_time - pd.Timedelta(days=1), t_ep, t_dem)
        n[k] = np.bincount(house_cell[ar], minlength=NC)
        sel = inm & (mi == k)
        assert ar[counted["house"][sel]].all(), "a counted event's house is not in n"
    used = np.isfinite(v) & (n > 0)
    mm, cc = np.nonzero(used)
    panel = pd.DataFrame({"cell": labels[cc], "quarter": months[mm], "y": y[mm, cc], "n": n[mm, cc], "v": v[mm, cc],
                          "block": block[cc]})
    info = dict(time_unit="calendar month (in test_b's 'quarter' column)", events_counted=int(len(counted["house"])),
                events_counted_in_months=int(inm.sum()), events_in_rows_used=int(panel.y.sum()),
                events_in_rows_without_value=int(y[~np.isfinite(v)].sum()), rows_possible=int(M * NC),
                rows_with_value=int(np.isfinite(v).sum()), rows_used=int(len(panel)),
                cells_with_an_event_in_used_rows=int(panel.groupby("cell").y.sum().gt(0).sum()))
    return panel, info


# ---------------------------------------------------------------- commands
def stamp():
    return dict(sources=source_hashes(), host=platform.node(), python=platform.python_version(),
                finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))


def analyse(a, name, sp):
    t0 = time.perf_counter()
    started = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    inputs, h, house, date, key, t_ep, holds = RT.load(a, a.mode)
    world = (house, date, key, t_ep, holds)
    a.out.mkdir(parents=True, exist_ok=True)
    S = np.load(a.surrogates, allow_pickle=False)
    run_json = Path(str(a.surrogates) + ".run.json")
    with np.load(a.cells, allow_pickle=False) as z:
        sinfo = check_surrogates(S, run_json, z[sp["field"]].astype(np.float64), sp["field"])
    assert sinfo["surrogates_sha256"] == C.sha256(a.surrogates)
    draws = sinfo["draws"] if a.draws is None else a.draws
    R = dict(label=RT.LABEL[a.mode], secondary=name, mode=a.mode, spec=sp, field=sp["field"], surrogate_seed=SEED)
    t = time.perf_counter()
    if sp["model"] == "monthly":
        panel, info = monthly_panel(h, world, a.grid, a.cells)
        res = TB.null_test(panel, S["fields"][:draws], S["quarters"], S["cells"], expected_draws=draws)
        cells_used = None
    else:
        cells_path, _ = variant_cells(a.cells, sp["field"], a.out)
        panel, info = RR.testb_panel(h, world, a.grid, cells_path)
        cells_used = C.sha256(cells_path)
        if sp["model"] == "ppml":
            res = TB.null_test(panel, S["fields"][:draws], S["quarters"], S["cells"], expected_draws=draws)
        else:
            res = run_nb(panel, h, a, S, draws, a.workers)
    if "draws" in res:
        res["statistics"] = [d["null_statistic"] for d in res.pop("draws")]
    R.update(panel=info, observed=res["observed"], draws=int(draws), statistics=res["statistics"],
             exceedances=int(res["exceedances"]), p_B=res["p_B"], null_seconds=time.perf_counter() - t)
    if "draws_fitted_from_bfgs_start" in res:
        R["draws_fitted_from_bfgs_start"] = res["draws_fitted_from_bfgs_start"]
    R["inputs"] = dict(checkpoint1=inputs, events=C.sha256(a.events), cells=C.sha256(a.cells),
                       cells_with_field_as_v=cells_used, surrogates=sinfo)
    R.update(started=started, elapsed_seconds=time.perf_counter() - t0, **stamp())
    panel.to_csv(a.out / "panel.csv", index=False)
    return R, panel


def show(R):
    s = {k: R[k] for k in ("label", "secondary", "mode", "field", "panel", "draws", "exceedances", "p_B", "null_seconds")}
    s["observed"] = {k: R["observed"][k] for k in ("beta", "rate_ratio_iqr", "rate_ratio_ci95", "rows_used")}
    print(json.dumps(s, indent=1, default=str))


def cmd_run(a):
    sp = SPECS[a.secondary]
    if a.mode == "real":
        assert a.draws is None, "the real run uses the plan's counts"
    R, _ = analyse(a, a.secondary, sp)
    (a.out / "result.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
    show(R)


def cmd_anchor(a):
    R, panel = analyse(a, "anchor", dict(field="v", model="ppml"))
    prim = json.loads(Path(a.primary).read_text())
    assert prim["mode"] == a.mode
    check, rep = RR.check_primary_b(panel, a.primary_panel, prim)
    n = R["draws"]
    check["null_max_abs_diff"] = float(np.max(np.abs(np.asarray(R["statistics"]) - np.asarray(prim["statistics"][:n]))))
    check["observed_beta_diff"] = abs(R["observed"]["beta"] - prim["observed"]["beta"])
    check["pass"] = bool(check["pass"] and check["null_max_abs_diff"] <= 1e-10 and check["observed_beta_diff"] <= 1e-10)
    R["anchor_check"] = check
    (a.out / "anchor.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
    show(R)
    print(json.dumps(check, indent=1, default=str))
    assert check["pass"], "the field-swap path differs from the primary Test B"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("run", "anchor"):
        s = sub.add_parser(name)
        for k in ("features", "grid", "episodes", "censoring", "events", "cells", "surrogates", "out"):
            s.add_argument(f"--{k}", type=Path, required=True)
        s.add_argument("--mode", choices=("decoy", "real"), required=True)
        s.add_argument("--workers", type=int, default=1)
        s.add_argument("--draws", type=int, default=None, help="default: all stored draws; fewer only for checks")
        if name == "run":
            s.add_argument("--secondary", choices=list(SPECS), required=True)
        else:
            s.add_argument("--primary", type=Path, required=True)
            s.add_argument("--primary-panel", type=Path, required=True)
    a = p.parse_args(argv)
    {"run": cmd_run, "anchor": cmd_anchor}[a.cmd](a)


if __name__ == "__main__":
    main()
