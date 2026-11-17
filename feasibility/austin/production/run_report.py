"""Items reported beside the Test A decision, and the remodel specificity checks (AUSTIN_PLAN.md §9 secondary metrics;
§11 "Reported beside the Test A decision" and the specificity checks of Tests A and B; §12 item 8 permutation nulls).
How each item is computed is fixed in §15 ("Items reported beside the decision (§9, §11, §12.8): how they are computed,
fixed before the real run", 2026-11-12). Written and hashed before the real run.

run_tests.py (the decision path, decoy-tested) is imported unchanged. Its world, cases_of and Test B panel lines are
reused, and this script asserts that it rebuilds the same foundation analysis: Test A cases, rows, baseline and
observed change in average precision and the null statistics equal run_tests.py's test_a.json; the Test B panel
equals its test_b_panel.csv and the observed fit its test_b.json.

Commands
  testa  foundation (controls seed 2029) and remodel (seed 2030) Test A:
         - observed changes in average precision, ROC AUC, pooled top-10% capture and top-10% capture within the risk
           set (frozen nyc_lib.metrics on the same out-of-fold scores), each with p from the conditional null;
         - directional concordance of the foundation analysis (standardised and raw mm/yr), as NYC's 11_models.py;
         - joint refit block bootstrap (2,000; universe = 2 km blocks holding rows of either analysis; one block
           draw per resample applied to both; NYC boot_rep per analysis); foundation, remodel and difference;
         - free and within-block permutation nulls of the foundation analysis (2,000 each, NYC perm_fields).
  testb  remodel Test B (null seed 2035) and the joint 2 km block bootstrap of the foundation-minus-remodel log rate
         ratio per IQR (2,000; copies of a block drawn twice are distinct cells and clusters; frozen fit_panel).
         Remodel Test B keeps the foundation panel's rows, n (foundation at-risk rule), v and blocks; only y changes
         to the remodel control events (§11 "with remodel control events as the counts"; user's choice of 2026-11-12).
Worlds (§15)
  real   foundation: run_tests.world("real"). Remodel: the 1,491 remodel control events at their houses; at-risk
         dates (§8 item 3) from the first remodel episodes of all 9,235 houses (Test A risk sets; Test B counts only);
         folds from "holds a remodel event".
  decoy  foundation: run_tests.world("decoy") (seed 99). Remodel: the 1,491 dates at default_rng(199) houses, remodel
         episodes before 2018-08-01 kept, those inside the study ignored, as run_tests' decoy world. No real remodel
         event's house is read.
Usage
  python -I run_report.py testa COMMON --mode M --events EV --remodel-events REV --remodel-episodes REP --field F
      --surrogates S --quantiles Q --primary TEST_A_JSON --out DIR --workers N [--draws n] [--boot n] [--perm n]
  python -I run_report.py testb COMMON --mode M --events EV --remodel-events REV --remodel-episodes REP --cells CELLS
      --surrogates SB_SEED2035 --primary TEST_B_JSON --primary-panel TEST_B_PANEL_CSV --out DIR --workers N
      [--draws n] [--boot n]
  COMMON = --features --grid --episodes --censoring (checkpoint-1 tables, hash-checked). --draws/--boot/--perm below
  the plan's counts are for smoke tests only (decoy mode).
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
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import run_tests as RT  # noqa: E402  (unchanged; puts planted_signal and the frozen scripts on the path)
from sklearn.metrics import average_precision_score, roc_auc_score  # noqa: E402

C, PS, TB = RT.C, RT.PS, RT.TB
N = C.N
FOUNDATION_SEED, REMODEL_SEED, REMODEL_DECOY_SEED = C.CONTROL_SEED, 2030, 199
REMODEL_EVENTS, REMODEL_EPISODES = 1_491, 9_235
N_BOOT, N_PERM, PERM_BASE = 2_000, 2_000, 10_000
METRICS = ["pr", "roc", "top10", "top10_rs"]
BOOT_METRICS = ["pr", "roc", "top10"]
NAT = RT.NAT


def source_hashes():
    out = RT.source_hashes()
    out["run_report.py"] = C.sha256(HERE / "run_report.py")
    return out


def stamp():
    return dict(sources=source_hashes(), host=platform.node(), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))


# ---------------------------------------------------------------- remodel world (§15)
def remodel_world(mode, h, events_path, episodes_path):
    """(event house, event date, sort key, remodel episode date per house, holds per house)."""
    pos = pd.Series(np.arange(len(h)), index=h.prop_id)
    rep = pd.read_parquet(episodes_path, columns=["prop_id", "t_first"])
    assert len(rep) == REMODEL_EPISODES and rep.prop_id.is_unique
    hp = rep.prop_id.map(pos)
    assert hp.notna().all(), "a remodel episode is not at an eligible house"
    t_real = np.full(len(h), NAT)
    t_real[hp.to_numpy(np.int64)] = rep.t_first.to_numpy("datetime64[ns]")
    if mode == "real":
        ev = pd.read_parquet(events_path, columns=["prop_id", "t_first"])
        assert len(ev) == REMODEL_EVENTS and ev.prop_id.is_unique
        house = ev.prop_id.map(pos)
        assert house.notna().all(), "a remodel control event is not at an eligible house"
        house = house.to_numpy(np.int64)
        date = ev.t_first.to_numpy("datetime64[ns]")
        assert (t_real[house] == date).all(), "a remodel control event is not its house's first remodel episode"
        t_ep = t_real
    else:
        ev = pd.read_parquet(events_path, columns=["t_first"])
        assert len(ev) == REMODEL_EVENTS
        date = ev.t_first.to_numpy("datetime64[ns]")
        house = np.random.default_rng(REMODEL_DECOY_SEED).integers(0, len(h), len(date))
        t_ep = np.where(t_real < np.datetime64(C.START.to_datetime64(), "ns"), t_real, NAT)
        for k in np.argsort(date, kind="stable"):
            hk = house[k]
            if np.isnat(t_ep[hk]) or date[k] < t_ep[hk]:
                t_ep[hk] = date[k]
    key = h.prop_id.to_numpy(np.int64)[house]
    holds = np.zeros(len(h), bool)
    holds[house] = True
    return house, date, key, t_ep, holds


# ---------------------------------------------------------------- Test A analysis (same calls as run_tests.cmd_testa)
class Analysis:
    def __init__(self, name, h, geo, world, HV, seed, U, raw):
        house, date, key, t_ep, holds = world
        self.name = name
        self.events_in_file = len(date)
        self.cases, self.dropped, _ = RT.cases_of(house, date, key, h, t_ep, HV)
        self.fold_h = C.fold_of_houses(h, holds)
        rows = C.risk_sets(self.cases.house.to_numpy(), self.cases.date.to_numpy("datetime64[ns]"),
                           self.cases.window.to_numpy(), t_ep, h.t_demolition.to_numpy("datetime64[ns]"), HV,
                           np.random.default_rng(seed))
        rows, self.lost = C.drop_incomplete(rows, h)
        self.rows = rows
        self.X = C.design(h, rows["house"], rows["date"])
        self.y, self.fold, self.win, self.rs = rows["y"], self.fold_h[rows["house"]], rows["window"], rows["set"]
        self.pix = geo.house_null[rows["house"]]
        assert (self.pix >= 0).all()
        self.u = U[self.win, rows["house"]]
        self.raw = raw[self.win, rows["house"]]
        assert np.isfinite(self.u).all() and np.isfinite(self.raw).all()
        self.block = h.block.to_numpy().astype(str)[rows["house"]]
        self.mb = metric_set(self.y, scores(self.X, self.y, self.fold), self.rs)
        self.mv = metric_set(self.y, scores(np.column_stack([self.X, self.u]), self.y, self.fold), self.rs)
        self.observed = {k: self.mv[k] - self.mb[k] for k in METRICS}

    def describe(self):
        years = pd.DatetimeIndex(self.cases.date).year
        return dict(events_in_file=int(self.events_in_file), cases=int(len(self.cases)), dropped=self.dropped,
                    rows=int(len(self.y)), control_rows_dropped_missing_inputs=self.lost,
                    cases_by_year={str(k): int(v) for k, v in pd.Series(years).value_counts().sort_index().items()},
                    cases_per_fold=[int(self.y[self.fold == k].sum()) for k in range(5)],
                    blocks_with_rows=int(len(np.unique(self.block))), baseline=self.mb, velocity=self.mv,
                    observed=self.observed)


def scores(X, y, fold):
    s = N.oof(X, y, fold, N.LR)
    assert np.isfinite(s).all()
    return s


def metric_set(y, s, rs):
    return {k: float(v) for k, v in N.metrics(y, s, rs).items()}


_G = {}


def _null(d):
    A = _G["A"]
    raw = np.asarray(_G["store"].S[d][A.win, A.pix], dtype=np.float64)
    u = C.standardise(raw, A.win, _G["qS"][d])
    m = metric_set(A.y, scores(np.column_stack([A.X, u]), A.y, A.fold), A.rs)
    return d, {k: m[k] - A.mb[k] for k in METRICS}


def null_metrics(A, store, qS, draws, workers):
    _G.update(A=A, store=store, qS=qS)
    out = [None] * draws
    with mp.get_context("fork").Pool(workers) as pool:
        for d, r in pool.imap_unordered(_null, range(draws), chunksize=2):
            out[d] = r
    _G.clear()
    stats = {k: np.array([r[k] for r in out]) for k in METRICS}
    assert all(np.isfinite(v).all() for v in stats.values())
    return stats


def concordance(A):
    """§11 directional concordance as NYC's 11_models.py (direction_* fields)."""
    df = pd.DataFrame({"rs": A.rs, "y": A.y, "u": A.u, "raw": A.raw})
    case = df[df.y == 1].set_index("rs")[["u", "raw"]]
    ctrl = df[df.y == 0].groupby("rs")[["u", "raw"]].median()
    d = (case - ctrl.reindex(case.index)).dropna()
    med = float(np.median(d.u))
    coef = N.model(N.LR).fit(np.column_stack([A.X, A.u]), A.y)[-1].coef_[0, -1]
    return dict(risk_sets=int(len(case)), risk_sets_without_controls=int(len(case) - len(d)),
                direction_median=med,
                direction_label="concordant" if med < 0 else "opposite" if med > 0 else "none",
                direction_share_below_0=float((d.u < 0).mean()),
                direction_raw_mm_yr_median=float(np.median(d.raw)),
                direction_raw_share_below_0=float((d.raw < 0).mean()),
                event_raw_mm_yr_median=float(np.median(A.raw[A.y == 1])),
                control_raw_mm_yr_median=float(np.median(A.raw[A.y == 0])),
                coef_field_all_rows=float(coef))


# ---------------------------------------------------------------- joint refit block bootstrap (§9, §11)
def members_of(blocks, universe):
    code = pd.Index(universe).get_indexer(blocks)
    assert (code >= 0).all()
    order = np.argsort(code, kind="stable")
    return np.split(order, np.cumsum(np.bincount(code, minlength=len(universe)))[:-1])


def boot_rows(A, idx):
    """NYC 11_models.boot_rep after its block draw: both models refitted out of fold on the resampled rows."""
    yy, ff = A.y[idx], A.fold[idx]
    sb, sv = N.oof(A.X[idx], yy, ff, N.LR), N.oof(np.column_stack([A.X[idx], A.u[idx]]), yy, ff, N.LR)
    ok = np.isfinite(sb) & np.isfinite(sv)
    if not 0 < yy[ok].sum() < ok.sum():
        return None
    return {"pr": average_precision_score(yy[ok], sv[ok]) - average_precision_score(yy[ok], sb[ok]),
            "roc": roc_auc_score(yy[ok], sv[ok]) - roc_auc_score(yy[ok], sb[ok]),
            "top10": N.recall_top(yy[ok], sv[ok]) - N.recall_top(yy[ok], sb[ok])}


def _boot(s):
    rng = np.random.default_rng(s)
    draw = rng.choice(_G["n_universe"], _G["n_universe"], replace=True)
    return s, {A.name: boot_rows(A, np.concatenate([members[i] for i in draw])) for A, members in _G["analyses"]}


def joint_bootstrap(analyses, n_boot, workers):
    universe = np.unique(np.concatenate([A.block for A in analyses]))
    _G.update(n_universe=len(universe), analyses=[(A, members_of(A.block, universe)) for A in analyses])
    res = [None] * n_boot
    with mp.get_context("fork").Pool(workers) as pool:
        for s, r in pool.imap_unordered(_boot, range(n_boot), chunksize=4):
            res[s] = r
    _G.clear()
    out = dict(resamples=n_boot, seeds="default_rng(s), s = 0 .. resamples - 1", universe_blocks=int(len(universe)),
               per_analysis={}, per_resample=res)
    for A in analyses:
        ok = [r[A.name] for r in res if r[A.name] is not None]
        out["per_analysis"][A.name] = dict(
            blocks_with_rows=int(len(np.unique(A.block))), universe_is_own_blocks=bool(len(np.unique(A.block)) == len(universe)),
            resamples_with_value=len(ok), resamples_without_value=n_boot - len(ok),
            **{f"{k}_ci95": [float(np.percentile([b[k] for b in ok], q)) for q in (2.5, 97.5)] for k in BOOT_METRICS})
    if len(analyses) == 2:
        a, b = (A.name for A in analyses)
        both = [r[a]["pr"] - r[b]["pr"] for r in res if r[a] is not None and r[b] is not None]
        out["difference_pr"] = dict(definition=f"{a} change in PR AUC minus {b} change, same resampled blocks",
                                    observed=analyses[0].observed["pr"] - analyses[1].observed["pr"],
                                    resamples_used=len(both), ci95=[float(np.percentile(both, q)) for q in (2.5, 97.5)])
    return out


# ---------------------------------------------------------------- permutation nulls (§12 item 8)
def perm_fields(F, keys, blocks=None):
    """NYC 11_models.perm_fields, unchanged: per window, its valid cells ordered by key (within block) receive its
    values in index order."""
    out = np.full_like(F, np.nan)
    for w in range(len(F)):
        v = np.flatnonzero(np.isfinite(F[w]))
        if blocks is None:
            dst = v[np.argsort(keys[v], kind="stable")]
        else:
            src = v[np.lexsort((v, blocks[v]))]
            dst = v[np.lexsort((keys[v], blocks[v]))]
            out[w, dst] = F[w, src]
            continue
        out[w, dst] = F[w, v]
    return out


def _perm(task):
    kind, d = task
    A, F = _G["A"], _G["F"]
    keys = np.random.default_rng(PERM_BASE + d).random(F.shape[1])
    Fp = perm_fields(F, keys, _G["pix_block"] if kind == "within-block" else None)
    u = C.standardise(Fp[A.win, A.pix], A.win, C.surrogate_quantiles(Fp, _G["geo"]))
    m = metric_set(A.y, scores(np.column_stack([A.X, u]), A.y, A.fold), A.rs)
    return kind, d, {k: m[k] - A.mb[k] for k in METRICS}


def pixel_blocks(h, geo):
    """2 km block code of each null-field pixel (a pixel's houses share its block, §9)."""
    hb = pd.Index(np.unique(h.block.to_numpy().astype(str))).get_indexer(h.block.to_numpy().astype(str))
    hi = np.full(len(geo.null_pixels), -1, dtype=np.int64)
    lo = np.full(len(geo.null_pixels), np.iinfo(np.int64).max, dtype=np.int64)
    np.maximum.at(hi, geo.house_null[geo.null_houses], hb[geo.null_houses])
    np.minimum.at(lo, geo.house_null[geo.null_houses], hb[geo.null_houses])
    assert (hi >= 0).all() and (hi == lo).all(), "houses on one pixel in different blocks"
    return hi


def permutation_nulls(A, F, h, geo, n_perm, workers):
    _G.update(A=A, F=F, geo=geo, pix_block=pixel_blocks(h, geo))
    tasks = [(kind, d) for kind in ("free", "within-block") for d in range(n_perm)]
    res = {kind: [None] * n_perm for kind in ("free", "within-block")}
    with mp.get_context("fork").Pool(workers) as pool:
        for kind, d, r in pool.imap_unordered(_perm, tasks, chunksize=2):
            res[kind][d] = r
    _G.clear()
    out = {}
    for kind, rr in res.items():
        stats = {k: np.array([r[k] for r in rr]) for k in METRICS}
        out[kind] = dict(draws=n_perm, seeds=f"default_rng({PERM_BASE} + d)",
                         **{f"{k}_p": C.p_value(A.observed[k], stats[k]) for k in METRICS},
                         pr_null_median=float(np.median(stats["pr"])), statistics={k: v.tolist() for k, v in stats.items()})
    return out


# ---------------------------------------------------------------- commands
def check_primary_a(A, prim, stats_pr, draws):
    """The foundation analysis rebuilt here equals run_tests.py's test_a.json."""
    checks = dict(cases=A.describe()["cases"] == prim["cases"], rows=len(A.y) == prim["rows"],
                  dropped=A.dropped == {str(k): int(v) for k, v in prim["dropped"].items()},
                  control_rows_dropped=A.lost == prim["control_rows_dropped_missing_inputs"],
                  baseline_ap_diff=abs(A.mb["pr"] - prim["baseline_average_precision"]),
                  observed_diff=abs(A.observed["pr"] - prim["observed"]),
                  null_max_abs_diff=float(np.max(np.abs(stats_pr - np.asarray(prim["statistics"][:draws])))))
    checks["pass"] = bool(checks["cases"] and checks["rows"] and checks["dropped"] and checks["control_rows_dropped"]
                          and checks["baseline_ap_diff"] <= 1e-12 and checks["observed_diff"] <= 1e-12
                          and checks["null_max_abs_diff"] <= 1e-12)
    assert checks["pass"], f"the foundation analysis differs from run_tests.py: {checks}"
    return checks


def cmd_testa(a):
    t0 = time.perf_counter()
    inputs, h, house, date, key, t_ep, holds = RT.load(a, a.mode)
    geo = C.Geometry(h)
    v_all = C.load_field(a.field, geo)
    fp = C.null_fingerprint(v_all[:, geo.null_pixels], geo)
    HV = C.has_value_matrix(v_all, geo)
    W = len(C.MONTHS)
    raw = v_all[:, geo.house_pixel]
    U = C.standardise(raw, np.arange(W)[:, None], C.observed_quantiles(v_all, geo))
    world_r = remodel_world(a.mode, h, a.remodel_events, a.remodel_episodes)
    A_f = Analysis("foundation", h, geo, (house, date, key, t_ep, holds), HV, FOUNDATION_SEED, U, raw)
    if a.mode == "real":
        assert (A_f.fold_h == h.fold.to_numpy()).all(), "fold map differs from checkpoint 1"
    A_r = Analysis("remodel", h, geo, world_r, HV, REMODEL_SEED, U, raw)
    store = C.SurrogateStore(a.surrogates, fp, check_hash=True)
    qmeta = json.loads(Path(str(a.quantiles) + ".json").read_text())
    assert qmeta["surrogates_sha256"] == store.meta["sha256"] and qmeta["sha256"] == C.sha256(a.quantiles)
    qS = np.load(a.quantiles)
    assert qS.shape == (store.draws, len(C.QS), W)
    draws = store.draws if a.draws is None else a.draws
    prim = json.loads(Path(a.primary).read_text())
    assert prim["mode"] == a.mode and prim["inputs"]["surrogates"] == store.meta["sha256"]
    R = dict(label=RT.LABEL[a.mode], test="A report", mode=a.mode, remodel_decoy_seed=REMODEL_DECOY_SEED if a.mode == "decoy" else None)
    t = time.perf_counter()
    null = {}
    for A in (A_f, A_r):
        null[A.name] = null_metrics(A, store, qS, draws, a.workers)
    R["primary_check"] = check_primary_a(A_f, prim, null["foundation"]["pr"], draws)
    R["null_seconds"] = time.perf_counter() - t
    for A in (A_f, A_r):
        d = A.describe()
        d["null"] = dict(draws=int(draws), **{f"{k}_p": C.p_value(A.observed[k], null[A.name][k]) for k in METRICS},
                         **{f"{k}_null_median": float(np.median(null[A.name][k])) for k in METRICS},
                         statistics={k: v.tolist() for k, v in null[A.name].items()})
        R[A.name] = d
    R["foundation"]["concordance"] = concordance(A_f)
    t = time.perf_counter()
    boot = joint_bootstrap([A_f, A_r], a.boot, a.workers)
    R["bootstrap_seconds"] = time.perf_counter() - t
    R["bootstrap"] = boot
    pr_p = R["remodel"]["null"]["pr_p"]
    R["remodel"]["specificity"] = dict(
        change_pr=A_r.observed["pr"], ci95=boot["per_analysis"]["remodel"]["pr_ci95"], p=pr_p,
        share_of_foundation_change=(A_r.observed["pr"] / A_f.observed["pr"]) if A_f.observed["pr"] != 0 else None,
        foundation_change_positive=bool(A_f.observed["pr"] > 0),
        label="Negative-control gain detected" if C.demonstrated(A_r.observed["pr"], pr_p) else "Negative-control gain not detected")
    t = time.perf_counter()
    if a.perm:
        R["permutation_nulls"] = permutation_nulls(A_f, v_all[:, geo.null_pixels], h, geo, a.perm, a.workers)
    R["permutation_seconds"] = time.perf_counter() - t
    R["inputs"] = dict(checkpoint1=inputs, events=C.sha256(a.events), remodel_events=C.sha256(a.remodel_events),
                       remodel_episodes=C.sha256(a.remodel_episodes), field=C.sha256(a.field), null_fingerprint=fp,
                       surrogates=store.meta["sha256"], quantiles=qmeta["sha256"], primary=C.sha256(a.primary))
    R.update(workers=a.workers, elapsed_seconds=time.perf_counter() - t0, **stamp())
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "report_a.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
    print(json.dumps(summary_a(R), indent=1, default=str))


def summary_a(R):
    s = {k: R[k] for k in ("label", "mode", "primary_check", "null_seconds", "bootstrap_seconds", "permutation_seconds")}
    for name in ("foundation", "remodel"):
        d = R[name]
        s[name] = dict(cases=d["cases"], rows=d["rows"], dropped=d["dropped"], observed=d["observed"],
                       p={k: d["null"][f"{k}_p"] for k in METRICS}, ci95=R["bootstrap"]["per_analysis"][name])
    s["concordance"] = R["foundation"]["concordance"]
    s["specificity"] = R["remodel"]["specificity"]
    s["difference_pr"] = R["bootstrap"].get("difference_pr")
    if "permutation_nulls" in R:
        s["permutation_p"] = {k: {m: v[f"{m}_p"] for m in METRICS} for k, v in R["permutation_nulls"].items()}
    return s


# ---------------------------------------------------------------- Test B
def testb_panel(h, world, grid, cells, exposure_t_ep=None):
    """run_tests.cmd_testb's panel for a world (its lines, unchanged). exposure_t_ep: the at-risk episode dates for n
    (default: the world's own). The remodel panel passes the foundation world's, because remodel Test B keeps the
    foundation exposure and only its counts change (§15, the user's choice of 2026-11-12); a counted remodel event at a
    house not in n is then counted and reported instead of asserted away."""
    house, date, key, t_ep, holds = world
    t_n = t_ep if exposure_t_ep is None else exposure_t_ep
    not_in_n = 0
    g = pd.read_parquet(grid, columns=["prop_id", "cell250"])
    assert (g.prop_id.to_numpy() == h.prop_id.to_numpy()).all()
    c = np.load(cells, allow_pickle=False)
    labels, quarters, block, v = c["cells"], c["quarters"], c["block"], c["v"]
    house_cell = pd.Index(labels).get_indexer(g.cell250.to_numpy())
    assert (house_cell >= 0).all()
    HV = np.ones((len(C.MONTHS), len(h)), bool)  # Test B counts do not use the house's own pixel value
    _, _, counted = RT.cases_of(house, date, key, h, t_ep, HV)
    qp = pd.PeriodIndex([str(q) for q in quarters], freq="Q")
    eq = pd.PeriodIndex(pd.DatetimeIndex(counted["date"]), freq="Q")
    qi = qp.get_indexer(eq)
    inq = qi >= 0
    Q, NC = len(quarters), len(labels)
    y = np.zeros((Q, NC), np.int64)
    np.add.at(y, (qi[inq], house_cell[counted["house"][inq]]), 1)
    t_dem = h.t_demolition.to_numpy("datetime64[ns]")
    n = np.zeros((Q, NC), np.int64)
    for k, q in enumerate(qp):
        day_before = q.start_time - pd.Timedelta(days=1)
        ar = C.at_risk(day_before, t_n, t_dem)
        n[k] = np.bincount(house_cell[ar], minlength=NC)
        sel = inq & (qi == k)
        if exposure_t_ep is None:
            assert ar[counted["house"][sel]].all(), "a counted event's house is not in n"
        else:
            not_in_n += int((~ar[counted["house"][sel]]).sum())
    used = np.isfinite(v) & (n > 0)
    qq, cc = np.nonzero(used)
    panel = pd.DataFrame({"cell": labels[cc], "quarter": quarters[qq], "y": y[qq, cc], "n": n[qq, cc], "v": v[qq, cc],
                          "block": block[cc]})
    info = dict(events_counted=int(len(counted["house"])), events_counted_in_quarters=int(inq.sum()),
                events_outside_the_28_quarters=int((~inq).sum()), events_in_rows_used=int(panel.y.sum()),
                events_in_rows_without_value=int(y[~np.isfinite(v)].sum()), rows_possible=int(Q * NC),
                rows_with_value=int(np.isfinite(v).sum()), rows_used=int(len(panel)),
                cells_with_an_event_in_used_rows=int(panel.groupby("cell").y.sum().gt(0).sum()))
    if exposure_t_ep is not None:
        info["exposure"] = "foundation at-risk rule (§8), as the foundation panel"
        info["events_counted_in_quarters_at_houses_not_in_n"] = not_in_n
    return panel, info


def check_primary_b(panel, csv_path, prim):
    p = pd.read_csv(csv_path, float_precision="round_trip", dtype={"cell": str, "quarter": str, "block": str})
    checks = dict(rows=len(p) == len(panel))
    if checks["rows"]:
        for col in ("cell", "quarter", "block"):
            checks[col] = bool((p[col].to_numpy() == panel[col].astype(str).to_numpy()).all())
        for col in ("y", "n"):
            checks[col] = bool((p[col].to_numpy() == panel[col].to_numpy()).all())
        checks["v_max_abs_diff"] = float(np.max(np.abs(p.v.to_numpy() - panel.v.to_numpy())))
    rep, _, _ = TB.fit_panel(panel)
    checks["beta_diff"] = abs(rep["beta"] - prim["observed"]["beta"])
    checks["pass"] = bool(all(v for k, v in checks.items() if k in ("rows", "cell", "quarter", "block", "y", "n"))
                          and checks.get("v_max_abs_diff", 1) == 0 and checks["beta_diff"] <= 1e-10)
    assert checks["pass"], f"the foundation Test B panel differs from run_tests.py: {checks}"
    return checks, rep


def _tb_init(n_universe, prepared):
    _G.update(n_universe=n_universe, panels=prepared)


def _tb_boot(s):
    rng = np.random.default_rng(s)
    nU = _G["n_universe"]
    draw = rng.choice(nU, nU, replace=True)
    out = {}
    for name, P, members in _G["panels"]:
        parts = [members[i] for i in draw]
        idx = np.concatenate(parts)
        pos = np.repeat(np.arange(nU), [len(x) for x in parts])  # draw position: distinct copies of a block
        d = pd.DataFrame({"cell": P["cell_code"][idx] * nU + pos, "quarter": P["quarter"][idx], "y": P["y"][idx],
                          "n": P["n"][idx], "v": P["v"][idx], "block": P["block_code"][idx] * nU + pos})
        try:
            rep, _, _ = TB.fit_panel(d)
            out[name] = dict(beta=rep["beta"], velocity_iqr=rep["velocity_iqr"],
                             log_rr_iqr=rep["beta"] * rep["velocity_iqr"], rows_used=rep["rows_used"])
        except Exception as e:  # counted and reported, never dropped silently
            out[name] = dict(error=f"{type(e).__name__}: {e}")
    return s, out


def testb_bootstrap(panels, n_boot, workers):
    universe = np.unique(np.concatenate([P.block.astype(str).to_numpy() for _, P in panels]))
    prepared = []
    for name, P in panels:
        cells = np.unique(P.cell.astype(str).to_numpy())
        prepared.append((name, dict(cell_code=pd.Index(cells).get_indexer(P.cell.astype(str)).astype(np.int64),
                                    block_code=pd.Index(universe).get_indexer(P.block.astype(str)).astype(np.int64),
                                    quarter=P.quarter.astype(str).to_numpy(), y=P.y.to_numpy(), n=P.n.to_numpy(),
                                    v=P.v.to_numpy(float)),
                         members_of(P.block.astype(str).to_numpy(), universe)))
    # spawn, not fork: pyfixest's thread pools deadlock in forked children (seen in the synthetic check)
    res = [None] * n_boot
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), initializer=_tb_init,
                             initargs=(len(universe), prepared)) as ex:
        for s, r in ex.map(_tb_boot, range(n_boot), chunksize=2):
            res[s] = r
    names = [name for name, _ in panels]
    failed = {name: [s for s, r in enumerate(res) if "error" in r[name]] for name in names}
    both = [r[names[0]]["log_rr_iqr"] - r[names[1]]["log_rr_iqr"] for r in res
            if "error" not in r[names[0]] and "error" not in r[names[1]]]
    return dict(resamples=n_boot, seeds="default_rng(s), s = 0 .. resamples - 1", universe_blocks=int(len(universe)),
                failed_fits={k: dict(count=len(v), seeds=v) for k, v in failed.items()},
                resamples_used=len(both), difference_log_rr_iqr_ci95=[float(np.percentile(both, q)) for q in (2.5, 97.5)],
                per_analysis={name: dict(log_rr_iqr_ci95=[float(np.percentile([r[name]["log_rr_iqr"] for r in res if "error" not in r[name]], q)) for q in (2.5, 97.5)])
                              for name in names},
                per_resample=res)


def cmd_testb(a):
    t0 = time.perf_counter()
    inputs, h, house, date, key, t_ep, holds = RT.load(a, a.mode)
    prim = json.loads(Path(a.primary).read_text())
    assert prim["mode"] == a.mode
    panel_f, info_f = testb_panel(h, (house, date, key, t_ep, holds), a.grid, a.cells)
    check, rep_f = check_primary_b(panel_f, a.primary_panel, prim)
    world_r = remodel_world(a.mode, h, a.remodel_events, a.remodel_episodes)
    panel_r, info_r = testb_panel(h, world_r, a.grid, a.cells, exposure_t_ep=t_ep)
    for col in ("cell", "quarter", "n", "v", "block"):  # same rows and exposure as the foundation panel
        assert (panel_r[col].to_numpy() == panel_f[col].to_numpy()).all(), col
    S = np.load(a.surrogates, allow_pickle=False)
    assert int(S["seed"]) == 2035 and np.array_equal(S["quarters"], np.load(a.cells, allow_pickle=False)["quarters"])
    fields = S["fields"] if a.draws is None else S["fields"][:a.draws]
    t = time.perf_counter()
    res = TB.null_test(panel_r, fields, S["quarters"], S["cells"], expected_draws=len(fields))
    null_seconds = time.perf_counter() - t
    t = time.perf_counter()
    boot = testb_bootstrap([("foundation", panel_f), ("remodel", panel_r)], a.boot, a.workers)
    boot["observed_difference_log_rr_iqr"] = (rep_f["beta"] * rep_f["velocity_iqr"]
                                              - res["observed"]["beta"] * res["observed"]["velocity_iqr"])
    R = dict(label=RT.LABEL[a.mode], test="B report", mode=a.mode,
             remodel_decoy_seed=REMODEL_DECOY_SEED if a.mode == "decoy" else None, primary_check=check,
             foundation=dict(panel=info_f, observed=rep_f),
             remodel=dict(panel=info_r, observed=res["observed"], draws=len(fields),
                          statistics=[d["null_statistic"] for d in res["draws"]], exceedances=res["exceedances"],
                          p_B=res["p_B"], detected=bool(res["p_B"] < 0.05),
                          label="Negative-control association detected" if res["p_B"] < 0.05 else "Negative-control association not detected"),
             bootstrap=boot, null_seconds=null_seconds, bootstrap_seconds=time.perf_counter() - t,
             inputs=dict(checkpoint1=inputs, events=C.sha256(a.events), remodel_events=C.sha256(a.remodel_events),
                         remodel_episodes=C.sha256(a.remodel_episodes), cells=C.sha256(a.cells),
                         surrogates=C.sha256(a.surrogates), primary=C.sha256(a.primary),
                         primary_panel=C.sha256(a.primary_panel)),
             workers=a.workers, elapsed_seconds=time.perf_counter() - t0, **stamp())
    a.out.mkdir(parents=True, exist_ok=True)
    panel_r.to_csv(a.out / "test_b_panel_remodel.csv", index=False)
    (a.out / "report_b.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
    short = {k: v for k, v in R.items() if k not in ("bootstrap", "remodel", "sources")}
    short["remodel"] = {k: v for k, v in R["remodel"].items() if k != "statistics"}
    short["bootstrap"] = {k: v for k, v in boot.items() if k != "per_resample"}
    print(json.dumps(short, indent=1, default=str))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("testa", "testb"):
        s = sub.add_parser(name)
        for k in ("features", "grid", "episodes", "censoring", "events", "remodel-events", "remodel-episodes",
                  "surrogates", "primary", "out"):
            s.add_argument(f"--{k}", type=Path, required=True)
        s.add_argument("--mode", choices=("decoy", "real"), required=True)
        s.add_argument("--workers", type=int, required=True)
        s.add_argument("--draws", type=int, default=None, help="default: all stored draws; fewer only for checks")
        s.add_argument("--boot", type=int, default=N_BOOT)
        if name == "testa":
            s.add_argument("--field", type=Path, required=True)
            s.add_argument("--quantiles", type=Path, required=True)
            s.add_argument("--perm", type=int, default=N_PERM, help="0 skips the permutation nulls")
        else:
            s.add_argument("--cells", type=Path, required=True)
            s.add_argument("--primary-panel", type=Path, required=True)
    a = p.parse_args(argv)
    if a.mode == "real":
        assert a.draws is None and a.boot == N_BOOT and getattr(a, "perm", N_PERM) == N_PERM, "the real run uses the plan's counts"
    {"testa": cmd_testa, "testb": cmd_testb}[a.cmd](a)


if __name__ == "__main__":
    main()
