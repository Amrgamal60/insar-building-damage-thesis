"""Secondary 20: the temporal deep model (AUSTIN_PLAN.md §12 item 20; §15 "Item 20 (deep model): how it is run").

Rows   the primary Test A rows by run_tests.py's own path (cases, risk sets with default_rng(2029), rows missing inputs
       dropped), the Test A design (testa_core.design: Baseline 1 + x/y, unchanged), the checkpoint fold map and the
       2 km blocks. Cases, rows, drops and cases per fold are asserted equal to the primary record of the same world.
Series deep_field.build_field (acquisition-date field from i08's house_series.npz) and the frozen
       deep_model.series_from_fields: the §7 24-month window of the case's month, shared by every row of a risk set.
       Checked: every row's pixel has a Test A value in that window, every in-window acquisition passes the
       connected-component rule there (so the step masks do not depend on it), and every row has an unmasked step.
       No additional row/step mask: the construction and slip rules are window-level and every row already passes them.
Model  frozen deep_model.oof_scores (both networks) and temporal_null_test (registered null: LowMemVariogramNull on
       the GPU, seed 2037; only the series network refitted per draw), called unchanged. Its observed scores are
       asserted equal to the standalone oof_scores call.
Boot   refit block bootstrap as run_report.joint_bootstrap (frozen README item 9): universe = the 2 km blocks holding
       rows, resample s draws them with default_rng(s), both networks refitted out of fold by oof_scores on the
       resampled rows. A resample for which oof_scores rejects its input because a fold has no rows or an inner split
       lacks a class has no value (as run_report's single-class resamples); any other error fails the run. The worker
       pool is forked before the first torch operation and runs the resamples while the parent runs the null (which
       is serial in the frozen code); resamples 0 and 1 are recomputed in the parent and must be identical.
Null engines: gpu (the registered default generator; the only one allowed in a real run) or shuffle (decoy code
       checks only: each draw permutes the pixels with default_rng(2037), median-filled, the real mask kept).
Usage: python -I secondary_deep.py --mode decoy|real COMMON --field FIELD_V --house-series HS --primary TEST_A_JSON
         --out DIR --workers N [--draws N] [--boot N] [--null gpu|shuffle]
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import platform  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import average_precision_score, roc_auc_score  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
import run_tests as RT  # noqa: E402  (unchanged; puts testa_core and the frozen scripts on the path)
import run_report as RR  # noqa: E402  (unchanged; members_of)
import deep_field as DF  # noqa: E402

C, N = RT.C, RT.C.N
import deep_model as DM  # noqa: E402  (frozen copy, freeze/scripts)

NAME, DRAWS, BOOT, NULL_SEED = "20_deep_model", 99, 2000, 2037
LABEL = {"decoy": "DECOY RUN (code check, not a result)", "real": "REAL RUN"}
NO_VALUE = ("Inner training and validation must each contain both classes", "Expected input fold labels 0..4")
_G = {}


def source_hashes():
    return {p.name: C.sha256(p) for p in (HERE / "secondary_deep.py", HERE / "deep_field.py", HERE / "run_tests.py",
                                          HERE / "run_report.py", C.FROZEN / "deep_model.py", C.FROZEN / "lowmem_null.py",
                                          C.FROZEN / "nyc_lib.py", Path(C.__file__))}


def stamp():
    return time.strftime("%Y-%m-%d %H:%M:%S %Z")


def metric_set(y, s_series, s_comparison):
    return {"pr": float(average_precision_score(y, s_series) - average_precision_score(y, s_comparison)),
            "roc": float(roc_auc_score(y, s_series) - roc_auc_score(y, s_comparison)),
            "top10": float(N.recall_top(y, s_series) - N.recall_top(y, s_comparison))}


def rows_of(a):
    inputs, h, house, date, key, t_ep, holds = RT.load(a, a.mode)
    geo = C.Geometry(h)
    v_all = C.load_field(a.field, geo)
    HV = C.has_value_matrix(v_all, geo)
    cases, dropped, _ = RT.cases_of(house, date, key, h, t_ep, HV)
    fold_h = C.fold_of_houses(h, holds)
    if a.mode == "real":
        assert (fold_h == h.fold.to_numpy()).all(), "fold map differs from checkpoint 1"
    rows = C.risk_sets(cases.house.to_numpy(), cases.date.to_numpy("datetime64[ns]"), cases.window.to_numpy(), t_ep,
                       h.t_demolition.to_numpy("datetime64[ns]"), HV, np.random.default_rng(C.CONTROL_SEED))
    rows, lost = C.drop_incomplete(rows, h)
    X = C.design(h, rows["house"], rows["date"])
    y, fold = rows["y"], fold_h[rows["house"]]
    block = h.block.to_numpy()[rows["house"]]
    prim = json.loads(Path(a.primary).read_text())
    assert prim["mode"] == a.mode, "primary record of another world"
    check = dict(cases=len(cases) == prim["cases"], rows=len(y) == prim["rows"],
                 dropped={str(k): int(v) for k, v in dropped.items()} == {str(k): int(v) for k, v in prim["dropped"].items()},
                 control_rows_dropped=lost == prim["control_rows_dropped_missing_inputs"],
                 cases_per_fold=[int(y[fold == k].sum()) for k in range(5)] == prim["cases_per_fold"])
    assert all(check.values()), f"rows differ from the primary Test A rows: {check}"
    info = dict(inputs=inputs, events_in_file=int(len(date)), cases=int(len(cases)), rows=int(len(y)),
                dropped={str(k): int(v) for k, v in dropped.items()}, control_rows_dropped_missing_inputs=lost,
                cases_per_fold=[int(y[fold == k].sum()) for k in range(5)], primary_record=str(a.primary),
                primary_record_sha256=C.sha256(a.primary), equal_to_primary=check)
    return h, geo, HV, rows, X, y, fold, block, info


def series_of(a, geo, HV, rows):
    dates, field, finfo = DF.build_field(a.house_series, geo.pix_i, geo.pix_j)
    pix, when, win = geo.house_pixel[rows["house"]], rows["date"].astype("datetime64[ns]"), rows["window"]
    assert (C.window_of(when) == win).all(), "a row's window is not its case's month"
    assert HV[win, rows["house"]].all(), "a row has no Test A value in its window"
    with np.load(a.house_series, allow_pickle=False) as z:
        L = z["label_ok"].astype(bool)
    for w in np.unique(win):
        te = pd.Timestamp(C.MONTHS[w] + "-01")
        d = (dates >= np.datetime64(te - pd.DateOffset(months=24))) & (dates < np.datetime64(te))
        assert L[d][:, np.unique(pix[win == w])].all(), "an in-window acquisition fails the component rule"
    del L
    series, mask = DM.series_from_fields(dates, field, np.isfinite(field), pix, when)
    assert mask.any(1).all(), "a row has no unmasked step"
    finfo.update(rows_steps_valid_share=float(mask.mean()), rows_min_valid_steps=int(mask.sum(1).min()),
                 row_series=DM.series_diagnostics(series, mask))
    return dates, field, pix, when, series, mask, finfo


# ---------------------------------------------------------------- refit block bootstrap
def boot_one(s):
    g = _G
    rng = np.random.default_rng(s)
    draw = rng.choice(g["n_universe"], g["n_universe"], replace=True)
    idx = np.concatenate([g["members"][i] for i in draw])
    yy = g["y"][idx]
    if not 0 < yy.sum() < len(yy):
        return s, None
    try:
        sc, _ = DM.oof_scores(g["X"][idx], g["series"][idx], g["mask"][idx], yy, g["block"][idx], g["fold"][idx])
    except ValueError as e:
        if str(e) in NO_VALUE:
            return s, None
        raise
    return s, metric_set(yy, sc["series"], sc["comparison"])


def shuffle_draws(field, n, seed):
    """Decoy code checks only: per draw one pixel permutation for every date, median-filled, real mask kept."""
    valid = np.isfinite(field)
    med = np.array([np.median(f[v]) for f, v in zip(field, valid)])
    filled = np.where(valid, field, med[:, None])
    rng = np.random.default_rng(seed)
    for _ in range(n):
        perm = rng.permutation(field.shape[1])
        yield np.where(valid, filled[:, perm], np.nan), None


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in ("features", "grid", "episodes", "censoring", "events", "field", "house_series", "primary", "out"):
        p.add_argument("--" + k.replace("_", "-"), type=Path, required=True)
    p.add_argument("--mode", choices=("decoy", "real"), required=True)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--draws", type=int, default=None, help="default 99; fewer only for decoy checks")
    p.add_argument("--boot", type=int, default=None, help="default 2,000; fewer only for decoy checks")
    p.add_argument("--null", choices=("gpu", "shuffle"), default="gpu")
    a = p.parse_args(argv)
    if a.mode == "real":
        assert a.draws is None and a.boot is None and a.null == "gpu", "the real run uses the plan's counts and null"
    draws, n_boot = a.draws or DRAWS, a.boot or BOOT
    t0, started = time.perf_counter(), stamp()
    a.out.mkdir(parents=True, exist_ok=True)

    h, geo, HV, rows, X, y, fold, block, rinfo = rows_of(a)
    dates, field, pix, when, series, mask, finfo = series_of(a, geo, HV, rows)
    print(json.dumps(dict(rows=rinfo["rows"], cases=rinfo["cases"], field=finfo["valid_share"]), default=str), flush=True)

    universe = np.unique(block)
    _G.update(X=X, series=series, mask=mask, y=y, block=block, fold=fold, n_universe=len(universe),
              members=RR.members_of(block, universe))
    pool = mp.get_context("fork").Pool(a.workers)  # forked before the parent's first torch operation

    t1 = time.perf_counter()
    scores, audit = DM.oof_scores(X, series, mask, y, block, fold, progress=True)
    observed = metric_set(y, scores["series"], scores["comparison"])
    fit_seconds = time.perf_counter() - t1
    np.savez_compressed(a.out / "oof_scores.npz", comparison=scores["comparison"], series=scores["series"], y=y,
                        block=block, fold=fold, house=rows["house"], set=rows["set"])

    tb = time.perf_counter()  # the bootstrap runs in the pool while the parent runs the null
    pending = pool.map_async(boot_one, range(n_boot), chunksize=1)
    t1 = time.perf_counter()
    xy = np.column_stack([geo.pix_i * C.PIXEL_M + C.PIXEL_M / 2, geo.pix_j * C.PIXEL_M + C.PIXEL_M / 2])
    sf = None if a.null == "gpu" else shuffle_draws(field, draws, NULL_SEED)
    res, obs2 = DM.temporal_null_test(X, dates, field, pix, when, y, block, fold, expected_draws=draws, xy=xy,
                                      res=C.PIXEL_M, surrogate_fields=sf, diagnostics=True)
    assert all(np.array_equal(obs2[k], scores[k]) for k in ("comparison", "series")), "observed scores differ"
    assert res["observed_delta_pr_auc"] == observed["pr"]
    null_seconds = time.perf_counter() - t1

    out = pending.get()
    pool.close()
    pool.join()
    assert [s for s, _ in out] == list(range(n_boot))
    boot = [r for _, r in out]
    boot_seconds = time.perf_counter() - tb
    serial = [boot_one(s)[1] for s in range(min(2, n_boot))]
    assert serial == boot[:len(serial)], "pooled bootstrap resamples differ from serial ones"
    ok = [b for b in boot if b is not None]
    bootstrap = dict(resamples=n_boot, seeds="default_rng(s), s = 0 .. resamples - 1", universe_blocks=int(len(universe)),
                     resamples_with_value=len(ok), resamples_without_value=n_boot - len(ok),
                     serial_check_resamples=len(serial),
                     **{f"{k}_ci95": [float(np.percentile([b[k] for b in ok], q)) for q in (2.5, 97.5)]
                        for k in ("pr", "roc", "top10")}, per_resample=boot)

    stats = [r["delta_pr_auc"] for r in res["draws"]]
    R = dict(label=LABEL[a.mode], secondary=NAME, mode=a.mode, null_engine=a.null, **rinfo, field=finfo,
             comparison_pr_auc=res["comparison_pr_auc"], series_pr_auc=res["observed_series_pr_auc"], observed=observed,
             null=dict(draws=len(stats), seed=NULL_SEED, statistics=stats, exceedances=res["exceedances"], p=res["p"],
                       k=[r["k"] for r in res["draws"]],
                       variogram_relative_rmse_median=[r.get("variogram_relative_rmse_median") for r in res["draws"]],
                       setup_seconds=res["null_setup_seconds"]),
             bootstrap=bootstrap, fit_seconds=fit_seconds, null_seconds=null_seconds, boot_seconds=boot_seconds,
             workers=a.workers, started=started, elapsed_seconds=time.perf_counter() - t0, sources=source_hashes(),
             inputs_deep=dict(field=str(a.field), field_sha256=C.sha256(a.field), house_series=str(a.house_series)),
             host=platform.node(), python=platform.python_version(), finished=stamp())
    (a.out / "null_draws.json").write_text(json.dumps(dict(draws=res["draws"], observed_fold_audit=res["observed_fold_audit"],
                                                           observed_series_diagnostics=res.get("observed_series_diagnostics")),
                                                      default=str) + "\n")
    (a.out / "fold_audit.json").write_text(json.dumps(audit, default=str) + "\n")
    (a.out / "result.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in R.items() if k not in ("bootstrap", "null", "field")}, indent=1, default=str))
    print(json.dumps(dict(p=res["p"], boot={k: v for k, v in bootstrap.items() if k != "per_resample"}), indent=1))


if __name__ == "__main__":
    main()
