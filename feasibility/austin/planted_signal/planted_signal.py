"""Planted-signal check of Test A at Austin's size (AUSTIN_PLAN.md §14, entry of 2026-11-10).

Written on 2026-11-10 at checkpoint 1, before any InSAR file was opened, and checked on synthetic
velocity fields only (check_planted_signal.py). It runs after the decoy run (§13 step 4) and before the
real run (step 5), on the real houses, Baseline 1 features and standardised window velocities and on the
999 stored conditional-null surrogate fields (seed 2027) of the real run. No real event is joined to a
velocity value: the real events enter only as a file of dates (command `event-dates`, which uses the
events and the field's validity, never its values).

Commands
  event-dates  dates of the real events usable in the primary comparison (testa_core.real_cases).
  quantiles    per-draw window quantiles of the stored surrogates (they do not depend on events).
  run          cells 1-6 x datasets 0-99, one resume-safe record per (cell, dataset).
  summarise    planted_signal_summary.json and PLANTED_SIGNAL.md.

Fixed details (§14 leaves them to the script):
- Synthetic world. A house's episode date is its real first matched foundation episode if that is before
  2018-08-01, otherwise none (real episodes inside the study period are ignored). A synthetic event sets
  its house's episode date to the event date. The shared at-risk rule (testa_core.at_risk) is then
  applied unchanged, with the real demolition censoring dates.
- Synthetic events: one per date of the dates file, in its order (sorted by date; events sharing a date
  are exchangeable). Candidates at date t in window w: complete Baseline 1 inputs, a value in w, at risk
  at t. One is drawn by rng.choice(candidates in prop_id order, p = exp(eta - max eta) / sum).
- eta: the generating coefficients (planted_signal/generating_coefficients.json: scaler mean and scale,
  coefficients on the standardised columns, intercept) applied to Baseline 1 + x/y with building age at
  t, plus the cell's term:
    cell 1  nothing;
    cell 2  0.65 * t_soil, s = z(lep_0_150) and t_soil = z(max(s - 0.7, 0)^2), both over the houses with
            complete inputs, z with the population SD (as the calibration's z);
    cell 3  0.7 * H. White noise on the 30 m pixel grid over the bounding box of the eligible houses'
            pixels, padded by 80 pixels (2.4 km, 4 sigma) on every side, drawn first from the dataset's
            generator as standard normals of shape (rows = j, columns = i); scipy gaussian_filter, sigma
            20 pixels (600 m), mode "reflect", truncate 4; read at each house's pixel and z-scored over
            the houses with complete inputs;
    cells 4-6  beta * u, beta = -0.1, -0.2, -0.4; u = the house's standardised observed velocity in w
            (testa_core.standardise with the observed field's quantiles), the model's own input.
- Generators: numpy SeedSequence([20261110, cell, dataset]) for H (first) and the event draws;
  SeedSequence([20261110, cell, dataset, 2029]) for the controls (testa_core.risk_sets).
- Fold map: testa_core.fold_of_houses with "house holds a synthetic event" (seed 42).
- Analysis: testa_core unchanged: risk sets, rows missing inputs dropped, Baseline 1 + x/y at the case
  date, TestA (logistic regression, pooled out-of-fold average precision), the observed statistic with the
  observed field, null draw d with stored surrogate d standardised by its own quantiles, p_value and the
  §11 rule.
- Time and fallback: jobs run dataset-major (dataset 0 of cells 1-6, then dataset 1, ...). The first round
  is the first `workers` jobs. When it is complete, projected hours = mean job seconds x all jobs /
  workers / 3600. If that exceeds 72, every cell runs datasets 0-49 only. The projection and the decision
  are written to projection.json before any further job starts, and reused on resume.
- Every record is kept. None is rerun except for a logged code error.
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import multiprocessing as mp  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor, as_completed  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.ndimage import gaussian_filter  # noqa: E402
from scipy.stats import norm, t as student_t  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
import testa_core as C  # noqa: E402

AUSTIN = HERE.parent
COEFFICIENTS_SHA256 = "2f67ed802968a6992101894724fdfb09489bb3fb2e8054ef277e37a1c98a9c8b"
MASTER = 20261110
CELLS = {1: dict(label="1. nothing added", kind="none"),
         2: dict(label="2. 0.65 t (nonlinear soil)", kind="soil", coef=0.65),
         3: dict(label="3. 0.7 H (hidden spatial field)", kind="hidden", coef=0.7),
         4: dict(label="4. beta = -0.1", kind="velocity", coef=-0.1),
         5: dict(label="5. beta = -0.2", kind="velocity", coef=-0.2),
         6: dict(label="6. beta = -0.4", kind="velocity", coef=-0.4)}
H_SIGMA_PX, H_PAD_PX = 20.0, 80
PROJECTION_HOURS, FALLBACK_DATASETS = 72.0, 50


def zscore(a):
    a = np.asarray(a, dtype=float)
    return (a - a.mean()) / a.std()


def atomic_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(obj, indent=1, allow_nan=False) + "\n")
    tmp.replace(path)


def source_hashes():
    return {p.name: C.sha256(p) for p in (HERE / "planted_signal.py", HERE / "testa_core.py", C.FROZEN / "nyc_lib.py")}


def checkpoint1_inputs(a):
    """Private checkpoint-1 tables, hash-checked against the checkpoint-1 records."""
    rec = AUSTIN / "checkpoint1"
    want = {"features": json.loads((rec / "features_2018.json").read_text())["private_outputs_sha256"]["features_2018.parquet"],
            "grid": json.loads((rec / "frame_grid_folds.json").read_text())["private_outputs_sha256"]["eligible_grid_folds.parquet"]}
    ev = json.loads((rec / "events_2018.json").read_text())["private_outputs_sha256"]
    want["episodes"], want["censoring"] = ev["foundation_first_episodes.parquet"], ev["demolition_censoring.parquet"]
    got = {k: C.sha256(getattr(a, k)) for k in want}
    assert got == want, f"checkpoint-1 input hash mismatch: {got} vs {want}"
    return got


# ---------------------------------------------------------------- context shared by the workers (fork)
CTX = {}


def build_context(a, need_null=True):
    t0 = time.perf_counter()
    inputs = checkpoint1_inputs(a)
    h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
    geo = C.Geometry(h)
    v_all = C.load_field(a.field, geo)
    v_null = v_all[:, geo.null_pixels]
    fp = C.null_fingerprint(v_null, geo)
    HV = C.has_value_matrix(v_all, geo)
    q_obs = C.observed_quantiles(v_all, geo)
    W, H = len(C.MONTHS), len(h)
    U = C.standardise(v_all[:, geo.house_pixel], np.arange(W)[:, None], q_obs)  # NaN where no value
    complete = h.complete_b1.to_numpy(bool)
    # generating model
    assert C.sha256(a.coefficients) == COEFFICIENTS_SHA256
    G = json.loads(a.coefficients.read_text())
    assert G["columns"] == C.B1
    mean, scale = np.asarray(G["scaler_mean"]), np.asarray(G["scaler_scale"])
    coef = np.asarray(G["coefficients_on_standardised_columns"])
    Xs = h[C.STATIC + ["x_km", "y_km"]].to_numpy(float)  # B1 without age, in B1 order
    eta_static = G["intercept"] + ((Xs - mean[1:]) / scale[1:]) @ coef[1:]
    # cell 2 term
    s = np.full(H, np.nan)
    s[complete] = zscore(h.lep_0_150.to_numpy(float)[complete])
    t_soil = np.full(H, np.nan)
    t_soil[complete] = zscore(np.maximum(s[complete] - 0.7, 0) ** 2)
    # cell 3 grid
    i0, j0 = geo.pix_i.min() - H_PAD_PX, geo.pix_j.min() - H_PAD_PX
    shape = (int(geo.pix_j.max() + H_PAD_PX - j0 + 1), int(geo.pix_i.max() + H_PAD_PX - i0 + 1))
    hj = h.pix_j.to_numpy(np.int64) - j0
    hi = h.pix_i.to_numpy(np.int64) - i0
    dates = pd.read_csv(a.event_dates, dtype=str).t_e
    dates = pd.to_datetime(dates, format="%Y-%m-%d").to_numpy("datetime64[ns]")
    assert len(dates) > 0 and (np.diff(dates.astype(np.int64)) >= 0).all()
    windows = C.window_of(dates)
    assert (windows >= 0).all()
    t_ep = h.t_episode.to_numpy("datetime64[ns]")
    t_ep_pre = np.where(t_ep < C.START.to_datetime64().astype("datetime64[ns]"), t_ep, np.datetime64("NaT", "ns"))
    CTX.update(h=h, geo=geo, HV=HV, U=U, complete=complete, eta_static=eta_static,
               age_mean=mean[0], age_scale=scale[0], age_coef=coef[0], year_built=h.year_built.to_numpy(float),
               t_soil=t_soil, grid_shape=shape, hi=hi, hj=hj, dates=dates, windows=windows,
               dec_dates=C.decimal_year(dates), t_ep_pre=t_ep_pre, t_dem=h.t_demolition.to_numpy("datetime64[ns]"),
               fingerprint=fp, q_obs=q_obs)
    fingerprints = dict(checkpoint1_inputs=inputs, field_npz=C.sha256(a.field), null_field=fp,
                        coefficients=COEFFICIENTS_SHA256, event_dates=C.sha256(a.event_dates))
    if need_null:
        store = C.SurrogateStore(a.surrogates, fp, check_hash=True)
        qmeta = json.loads(Path(str(a.quantiles) + ".json").read_text())
        assert qmeta["surrogates_sha256"] == store.meta["sha256"] and qmeta["sha256"] == C.sha256(a.quantiles)
        qS = np.load(a.quantiles)
        assert qS.shape == (store.draws, len(C.QS), W)
        CTX.update(store=store, qS=qS)
        fingerprints.update(surrogates=store.meta["sha256"], quantiles=qmeta["sha256"])
    CTX["fingerprints"] = fingerprints
    CTX["sources"] = source_hashes()
    CTX["setup_seconds"] = time.perf_counter() - t0
    return CTX


# ---------------------------------------------------------------- one dataset
def cell_term(cell, rng):
    kind = CELLS[cell]["kind"]
    if kind == "none":
        return lambda idx, w: 0.0
    if kind == "soil":
        return lambda idx, w: CELLS[cell]["coef"] * CTX["t_soil"][idx]
    if kind == "hidden":
        noise = rng.standard_normal(CTX["grid_shape"])
        field = gaussian_filter(noise, sigma=H_SIGMA_PX, mode="reflect", truncate=4.0)
        at = field[CTX["hj"], CTX["hi"]]
        Hh = np.full(len(at), np.nan)
        c = CTX["complete"]
        Hh[c] = zscore(at[c])
        return lambda idx, w: CELLS[cell]["coef"] * Hh[idx]
    return lambda idx, w: CELLS[cell]["coef"] * CTX["U"][w, idx]


def synthetic_events(cell, dataset):
    rng = np.random.default_rng(np.random.SeedSequence([MASTER, cell, dataset]))
    term = cell_term(cell, rng)
    t_ep = CTX["t_ep_pre"].copy()
    n = len(CTX["dates"])
    house = np.empty(n, dtype=np.int64)
    diag = dict(case_term=0.0, candidate_term=0.0, case_u=0.0, candidate_u=0.0, candidates_min=None)
    for e, (t, w, dy) in enumerate(zip(CTX["dates"], CTX["windows"], CTX["dec_dates"])):
        cand = CTX["complete"] & CTX["HV"][w] & C.at_risk(t, t_ep, CTX["t_dem"])
        idx = np.flatnonzero(cand)
        age = dy - CTX["year_built"][idx]
        extra = term(idx, w)
        eta = CTX["eta_static"][idx] + CTX["age_coef"] * (age - CTX["age_mean"]) / CTX["age_scale"] + extra
        assert np.isfinite(eta).all()
        wts = np.exp(eta - eta.max())
        k = rng.choice(len(idx), p=wts / wts.sum())
        house[e] = idx[k]
        t_ep[idx[k]] = t
        ex = np.broadcast_to(extra, idx.shape)
        u = CTX["U"][w, idx]
        diag["case_term"] += float(ex[k]) / n
        diag["candidate_term"] += float(ex.mean()) / n
        diag["case_u"] += float(u[k]) / n
        diag["candidate_u"] += float(u.mean()) / n
        diag["candidates_min"] = len(idx) if diag["candidates_min"] is None else min(diag["candidates_min"], len(idx))
    assert len(np.unique(house)) == n
    return house, t_ep, diag


def analyse(cell, dataset, draws):
    t0 = time.perf_counter()
    h, geo = CTX["h"], CTX["geo"]
    house, t_ep, diag = synthetic_events(cell, dataset)
    holds = np.zeros(len(h), dtype=bool)
    holds[house] = True
    fold_h = C.fold_of_houses(h, holds)
    crng = np.random.default_rng(np.random.SeedSequence([MASTER, cell, dataset, C.CONTROL_SEED]))
    rows = C.risk_sets(house, CTX["dates"], CTX["windows"], t_ep, CTX["t_dem"], CTX["HV"], crng)
    rows, lost = C.drop_incomplete(rows, h)
    X = C.design(h, rows["house"], rows["date"])
    y, fold, win = rows["y"], fold_h[rows["house"]], rows["window"]
    pix = geo.house_null[rows["house"]]
    assert (pix >= 0).all()
    A = C.TestA(X, y, fold)
    observed = A.delta(CTX["U"][win, rows["house"]])
    stats = []
    t1 = time.perf_counter()
    for d in range(draws):
        raw = np.asarray(CTX["store"].S[d][win, pix], dtype=np.float64)
        stats.append(A.delta(C.standardise(raw, win, CTX["qS"][d])))
    p = C.p_value(observed, stats)
    years = pd.DatetimeIndex(CTX["dates"]).year
    return dict(
        cell=cell, dataset=dataset, label=CELLS[cell]["label"],
        seeds=dict(events=[MASTER, cell, dataset], controls=[MASTER, cell, dataset, C.CONTROL_SEED]),
        synthetic_events=int(len(house)), rows=int(len(y)), control_rows_dropped_missing_inputs=lost,
        events_by_year={str(k): int(v) for k, v in pd.Series(years).value_counts().sort_index().items()},
        events_per_fold=[int(y[fold == k].sum()) for k in range(5)],
        houses_per_fold=[int((fold_h == k).sum()) for k in range(5)],
        diagnostics=diag, baseline_average_precision=A.baseline, observed=observed,
        draws=draws, statistics=stats, exceedances=int(np.sum(np.asarray(stats) >= observed)), p=p,
        meets_rule=C.demonstrated(observed, p),
        null_seconds=time.perf_counter() - t1, elapsed_seconds=time.perf_counter() - t0)


def run_job(spec):
    cell, dataset, draws, folder = spec
    path = Path(folder) / f"cell{cell}_ds{dataset:03d}.json"
    if path.exists():
        rec = json.loads(path.read_text())
        assert rec["sources"] == CTX["sources"] and rec["fingerprints"] == CTX["fingerprints"] and rec["draws"] == draws, \
            f"{path}: sources, inputs or draws differ; refusing a mixed run"
        return rec, True
    rec = analyse(cell, dataset, draws)
    rec.update(sources=CTX["sources"], fingerprints=CTX["fingerprints"], status="complete")
    atomic_json(path, rec)
    return rec, False


# ---------------------------------------------------------------- commands
def cmd_event_dates(a):
    """InSAR step: dates of the real cases of the primary comparison; uses the field's validity only."""
    checkpoint1_inputs(a)
    h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
    geo = C.Geometry(h)
    HV = C.has_value_matrix(C.load_field(a.field, geo), geo)
    ev = pd.read_parquet(a.events)
    cases, dropped = C.real_cases(ev, h, HV)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"t_e": pd.DatetimeIndex(cases.date).strftime("%Y-%m-%d")}).to_csv(a.out, index=False)
    info = dict(events=len(ev), cases=len(cases), dropped=dropped, sha256=C.sha256(a.out),
                events_sha256=C.sha256(a.events), field_sha256=C.sha256(a.field), sources=source_hashes())
    Path(str(a.out) + ".json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info, indent=1))


def _quantiles_of(d):
    return d, C.surrogate_quantiles(CTX["store"].draw(d), CTX["geo"])


def cmd_quantiles(a):
    checkpoint1_inputs(a)
    h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
    geo = C.Geometry(h)
    v_null = C.load_field(a.field, geo)[:, geo.null_pixels]
    store = C.SurrogateStore(a.surrogates, C.null_fingerprint(v_null, geo), check_hash=True)
    CTX.update(store=store, geo=geo)
    q = np.empty((store.draws, len(C.QS), len(C.MONTHS)))
    with ProcessPoolExecutor(a.workers, mp_context=mp.get_context("fork")) as ex:
        for d, qd in ex.map(_quantiles_of, range(store.draws), chunksize=4):
            q[d] = qd
    np.save(a.out, q)
    meta = dict(sha256=C.sha256(a.out), surrogates_sha256=store.meta["sha256"], fingerprint=store.meta["fingerprint"],
                shape=list(q.shape), percentiles=C.QS, sources=source_hashes())
    Path(str(a.out) + ".json").write_text(json.dumps(meta, indent=1) + "\n")
    print(json.dumps(meta, indent=1))


def cmd_run(a):
    build_context(a)
    draws = a.draws if a.draws is not None else CTX["store"].draws
    assert draws <= CTX["store"].draws
    records = a.out / "records"
    records.mkdir(parents=True, exist_ok=True)
    jobs = [(c, d, draws, str(records)) for d in range(a.datasets) for c in a.cells]
    log = open(a.out / "run.log", "a")

    def say(msg):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    say(f"setup {CTX['setup_seconds']:.1f} s; {len(jobs)} jobs; {a.workers} workers; draws {draws}; "
        f"synthetic events per dataset {len(CTX['dates'])}")
    proj_path = a.out / "projection.json"
    with ProcessPoolExecutor(a.workers, mp_context=mp.get_context("fork")) as ex:
        def run(batch):
            out = []
            for fut in as_completed([ex.submit(run_job, j) for j in batch]):
                rec, cached = fut.result()
                out.append(rec)
                took = "cached" if cached else "%.0f s" % rec["elapsed_seconds"]
                say(f"cell {rec['cell']} dataset {rec['dataset']}: observed {rec['observed']:+.5f}, p {rec['p']:.4f}, {took}")
            return out
        done = 0
        if proj_path.exists():
            proj = json.loads(proj_path.read_text())
            assert proj["workers"] == a.workers and proj["jobs"] == len(jobs) and proj["draws"] == draws
        else:
            done = a.workers
            first = run(jobs[:a.workers])
            secs = float(np.mean([r["elapsed_seconds"] for r in first]))
            hours = secs * len(jobs) / a.workers / 3600
            limit = a.datasets if hours <= a.projection_hours else min(a.datasets, FALLBACK_DATASETS)
            proj = dict(first_round_jobs=len(first), mean_job_seconds=secs, workers=a.workers, jobs=len(jobs), draws=draws,
                        projected_hours=hours, threshold_hours=a.projection_hours, datasets_per_cell=limit,
                        fallback_applied=limit < a.datasets, written=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
            atomic_json(proj_path, proj)
            say(f"projection: {hours:.1f} h for {len(jobs)} jobs -> datasets per cell {limit}")
        rest = [j for j in jobs[done:] if j[1] < proj["datasets_per_cell"]]
        run(rest)
    say("run complete")


def wilson(k, n):
    z = norm.ppf(.975)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [centre - half, centre + half]


def mean_interval(values):
    x = np.asarray(values, dtype=float)
    m, sd, n = float(x.mean()), float(x.std(ddof=1)), int(x.size)
    half = float(student_t.ppf(.975, n - 1) * sd / math.sqrt(n))
    return dict(mean=m, sd=sd, n=n, ci95=[m - half, m + half])


def deciles(p):
    """Right-closed deciles (0,.1], ..., (.9,1], as the calibration."""
    return np.bincount(np.clip(np.ceil(np.asarray(p) * 10).astype(int) - 1, 0, 9), minlength=10).tolist()


def cmd_summarise(a):
    proj = json.loads((a.out / "projection.json").read_text())
    recs = [json.loads(p.read_text()) for p in sorted((a.out / "records").glob("cell*_ds*.json"))]
    recs = [r for r in recs if r["dataset"] < proj["datasets_per_cell"]]
    assert len({json.dumps([r["sources"], r["fingerprints"], r["draws"]]) for r in recs}) == 1, "mixed records"
    cells = {}
    for c in sorted({r["cell"] for r in recs}):
        rs = sorted([r for r in recs if r["cell"] == c], key=lambda r: r["dataset"])
        assert [r["dataset"] for r in rs] == list(range(proj["datasets_per_cell"])), f"cell {c} incomplete"
        k, n = sum(r["meets_rule"] for r in rs), len(rs)
        cells[c] = dict(label=CELLS[c]["label"], datasets=n, meets_rule=k, share=k / n, wilson95=wilson(k, n),
                        p_below_005=sum(r["p"] < .05 for r in rs),
                        observed=mean_interval([r["observed"] for r in rs]),
                        null_dataset_means=mean_interval([np.mean(r["statistics"]) for r in rs]),
                        paired_bias=mean_interval([r["observed"] - np.mean(r["statistics"]) for r in rs]),
                        p_deciles=deciles([r["p"] for r in rs]),
                        synthetic_events=sorted({r["synthetic_events"] for r in rs}),
                        rows_mean=float(np.mean([r["rows"] for r in rs])),
                        control_rows_dropped_mean=float(np.mean([r["control_rows_dropped_missing_inputs"] for r in rs])),
                        case_term_minus_candidate_mean=float(np.mean([r["diagnostics"]["case_term"] - r["diagnostics"]["candidate_term"] for r in rs])),
                        case_u_minus_candidate_mean=float(np.mean([r["diagnostics"]["case_u"] - r["diagnostics"]["candidate_u"] for r in rs])))
    S = dict(projection=proj, draws=recs[0]["draws"], sources=recs[0]["sources"], fingerprints=recs[0]["fingerprints"], cells=cells)
    atomic_json(a.out / "planted_signal_summary.json", S)
    f6 = lambda x: f"{x:+.5f}"  # noqa: E731
    lines = ["# Planted-signal check of Test A (AUSTIN_PLAN.md §14)", "",
             f"Datasets per cell: {proj['datasets_per_cell']} (projection {proj['projected_hours']:.1f} h on {proj['workers']} workers; "
             f"fallback {'applied' if proj['fallback_applied'] else 'not applied'}). Null draws per dataset: {S['draws']}. "
             f"Synthetic events per dataset: {', '.join(str(v) for v in sorted({e for c in cells.values() for e in c['synthetic_events']}))}.", "",
             "A dataset meets the §11 rule if its change in PR AUC is positive and p < 0.05. Paired bias is the observed change minus the mean of that dataset's null draws; intervals are Student t over datasets. p deciles count (0,.1], ..., (.9,1].", "",
             "| Cell | Meets §11 rule [95% Wilson] | Mean observed change [95% t] | Mean null change | Paired bias [95% t] | p deciles |",
             "|---|---|---|---|---|---|"]
    for c in cells.values():
        lines.append(f"| {c['label']} | {c['meets_rule']}/{c['datasets']} = {100 * c['share']:.1f}% [{100 * c['wilson95'][0]:.1f}, {100 * c['wilson95'][1]:.1f}] | "
                     f"{f6(c['observed']['mean'])} [{f6(c['observed']['ci95'][0])}, {f6(c['observed']['ci95'][1])}] | {f6(c['null_dataset_means']['mean'])} | "
                     f"{f6(c['paired_bias']['mean'])} [{f6(c['paired_bias']['ci95'][0])}, {f6(c['paired_bias']['ci95'][1])}] | {c['p_deciles']} |")
    lines += ["", "Source hashes: " + ", ".join(f"`{k}` {v}" for k, v in S["sources"].items()) + ".",
              "Input fingerprints: " + json.dumps(S["fingerprints"]) + "."]
    (a.out / "PLANTED_SIGNAL.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("event-dates", "quantiles", "run", "summarise"):
        s = sub.add_parser(name)
        if name != "summarise":
            for k in ("features", "grid", "episodes", "censoring", "field"):
                s.add_argument(f"--{k}", type=Path, required=True)
        if name == "event-dates":
            s.add_argument("--events", type=Path, required=True)
            s.add_argument("--out", type=Path, required=True)
        if name == "quantiles":
            s.add_argument("--surrogates", type=Path, required=True)
            s.add_argument("--out", type=Path, required=True)
            s.add_argument("--workers", type=int, default=8)
        if name == "run":
            s.add_argument("--surrogates", type=Path, required=True)
            s.add_argument("--quantiles", type=Path, required=True)
            s.add_argument("--event-dates", type=Path, required=True)
            s.add_argument("--coefficients", type=Path, default=HERE / "generating_coefficients.json")
            s.add_argument("--out", type=Path, required=True)
            s.add_argument("--workers", type=int, required=True)
            s.add_argument("--cells", type=int, nargs="+", default=list(CELLS))
            s.add_argument("--datasets", type=int, default=100)
            s.add_argument("--draws", type=int, default=None, help="default: all stored draws (999); fewer only for checks")
            s.add_argument("--projection-hours", type=float, default=PROJECTION_HOURS)
        if name == "summarise":
            s.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    {"event-dates": cmd_event_dates, "quantiles": cmd_quantiles, "run": cmd_run, "summarise": cmd_summarise}[a.command](a)


if __name__ == "__main__":
    main()
