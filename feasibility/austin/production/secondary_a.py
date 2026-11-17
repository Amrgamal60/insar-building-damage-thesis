"""Test A secondary analyses at house level (AUSTIN_PLAN.md §12 items 2-7, 9-13, D1, D2 and the slip-rule sensitivity of
§14; how each is computed is fixed in §15, "Secondary analyses: how each is computed", 2026-11-15, before any secondary
outcome is joined). Each changes one step of the Test A primary analysis and carries no decision.

Reuse (unchanged): run_tests.py (world, cases_of, LABEL), run_report.py (metric_set, the null and block-bootstrap
arithmetic, METRICS, BOOT_METRICS), testa_core.py (load_houses, Geometry, fields, surrogate store, standardise, risk_sets,
drop_incomplete, design, fold_of_houses, p_value), frozen nyc_lib.py (oof, model, metrics) through them.
The command `anchor` runs the generic path below with the primary settings and checks that it rebuilds the primary
analysis (run_tests.py test_a.json; real mode also run_report.py report_a.json) and that its bootstrap equals
run_report.joint_bootstrap on the same rows.

Steps, with the primary setting and what a secondary changes (SPECS):
  world      events of checkpoint 1 (run_tests.world). 10: issue-dated episodes and events (§15). D1: first total
             demolitions; D2: the first of foundation event and demolition.
  validity   a row needs a value of every field of the analysis in the case's window (the field's own missing pattern;
             7: all four indicators). 12: the primary velocity's validity, because availability has a value everywhere.
  cases      run_tests.cases_of (§8A). D1, D2: their own rule (below).
  folds      the checkpoint-1 fold map (§9) in the real world; decoy: testa_core.fold_of_houses on the decoy houses, as
             run_tests. 11: testa_core.fold_of_houses with seeds 0..9.
  controls   testa_core.risk_sets (50, seed 2029). 2: up to 50 drawn from the houses within 1 km of the case house.
  rows       testa_core.drop_incomplete (Baseline 1). 5 (B2): rows missing a Baseline 2 input are left out (a case's
             whole risk set if the case misses one).
  design     Baseline 1 + x/y (testa_core.design). 5: Baseline 2 = B1 + count of the house's non-foundation building
             permits in [t - 5 years, t) + canopy share; or B1 without log income (same rows).
  indicator  the field standardised per window as §7 (observed: all eligible houses with a value; draw d: its stored
             quantiles), the field changed in 3, 6, 9, 12, 13 and the slip sensitivity; 7: four columns.
  model      logistic regression (nyc_lib). 4: random forest (nyc_lib). 7: HistGradientBoostingClassifier (defaults,
             random_state 0), out of fold with nyc_lib.oof's fold rule.
  null       the conditional null of the field (999 draws; trees: draws 0-499), per-draw change in each metric
             (PR AUC, ROC AUC, top-10% capture, top-10% within the risk set), p = (1 + #null >= observed) / (1 + draws).
  bootstrap  refit block bootstrap over the analysis's 2 km blocks (run_report: default_rng(s), s = 0..n-1; LR 2,000,
             trees 500; 11: none), 95% percentile intervals of the change in PR AUC, ROC AUC and top-10% capture.
D1 (demolition as outcome): cases are first total demolitions (checkpoint-1 censoring table) in the study months, in
  date then prop_id order, dropped for: missing Baseline 1 input; a matched foundation episode on or before the
  demolition date; no value in the window. Controls: 50 at risk at the demolition date (shared rule), as §8A.
D2 (composite): per house the earlier of its foundation event (checkpoint-1 events) and its demolition in the study
  months; dropped for: missing Baseline 1 input; a matched foundation episode before that date that is not the event
  itself; no value in the window. Controls as D1.
Decoy worlds (code checks, not results): foundation events as run_tests (seed 99). D1/D2: the demolition dates at
  default_rng(98) houses, real demolitions ignored, real foundation episodes replaced by run_tests' decoy episodes.

Usage
  python -I secondary_a.py run    --secondary NAME --mode decoy|real COMMON --events EV --field NAME=PATH ...
         --surrogates NAME=PATH ... --quantiles NAME=PATH ... [--mask-field PATH] [--issue-events P --issue-episodes P]
         [--other-bp P] --out DIR --workers N [--draws n] [--boot n]
  python -I secondary_a.py anchor --mode decoy|real COMMON --events EV --field v=P --surrogates v=P --quantiles v=P
         --primary TEST_A_JSON [--report REPORT_A_JSON] --out DIR --workers N [--draws n] [--boot n]
  COMMON = --features --grid --episodes --censoring (checkpoint-1 tables, hash-checked)
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
from scipy.spatial import cKDTree  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.metrics import average_precision_score, roc_auc_score  # noqa: E402

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import run_report as RR  # noqa: E402  (unchanged; imports run_tests, testa_core, planted_signal, nyc_lib, test_b)

RT, C, PS, N = RR.RT, RR.C, RR.PS, RR.N
METRICS, BOOT_METRICS = RR.METRICS, RR.BOOT_METRICS
NAT = RT.NAT
LR, RF, HGB = N.LR, N.RF, "boosted trees"
DEMOLITION_DECOY_SEED = 98
LOCAL_RADIUS_KM = 1.0
INCOME = 1 + C.STATIC.index("log_income")  # column of log income in testa_core.design


def spec(fields, **kw):
    s = dict(fields=list(fields), mask=None, world="foundation", dating="application", controls="primary",
             baseline="b1", kind=LR, fold_seed=None, draws=999, boot=2000)
    s.update(kw)
    if s["kind"] != LR:
        s.update(draws=500, boot=500)
    return s


SPECS = {
    "anchor": spec(["v"]),
    "2_local_controls": spec(["v"], controls="local"),
    "3_window_12": spec(["v12"]),
    "3_window_36": spec(["v36"]),
    "4_random_forest": spec(["v"], kind=RF),
    "5_baseline_2": spec(["v"], baseline="b2"),
    "5_baseline_1_no_income": spec(["v"], baseline="b1_no_income"),
    "6_amplitude": spec(["amp"]),
    "6_local_relative_motion": spec(["lrm"]),
    "6_acceleration": spec(["acc"]),
    "7_boosted_trees": spec(["v", "amp", "lrm", "acc"], kind=HGB),
    "9_lag_1": spec(["v_lag1"]),
    "9_lag_3": spec(["v_lag3"]),
    "9_lag_6": spec(["v_lag6"]),
    "9_lag_12": spec(["v_lag12"]),
    "10_issue_date": spec(["v"], dating="issue"),
    **{f"11_fold_seed_{k}": spec(["v"], fold_seed=k, boot=0) for k in range(10)},
    "12_availability": spec(["avail"], mask="v"),
    "13_no_construction_mask": spec(["v_nomask"]),
    "D1_demolition": spec(["v"], world="demolition"),
    "D2_composite": spec(["v"], world="composite"),
    "slip_first_run": spec(["v_firstrun"]),
}
# the month of the first window with values in the wrapper's surrogate files (make_surrogates_windows.py; §12.3, §12.9)
FIRST_WINDOW = {"v36": "2019-08", "v_lag1": "2018-09", "v_lag3": "2018-11", "v_lag6": "2019-02", "v_lag12": "2019-08"}


def source_hashes():
    out = RR.source_hashes()
    out["secondary_a.py"] = C.sha256(HERE / "secondary_a.py")
    return out


# ---------------------------------------------------------------- worlds
def load(a, mode, sp):
    """run_tests.load with the world of the secondary. Returns inputs, h, foundation world, analysis world, notes."""
    inputs = PS.checkpoint1_inputs(a)
    h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
    notes = {}
    events = a.events
    if sp["dating"] == "issue":
        ep = pd.read_parquet(a.issue_episodes, columns=["prop_id", "t_first", "t_application"])
        assert ep.prop_id.is_unique and set(ep.prop_id) == set(h.prop_id[h.t_episode.notna()]), "issue episodes differ"
        app = h.prop_id.map(ep.set_index("prop_id").t_application).astype("datetime64[ns]")
        m = h.t_episode.notna().to_numpy()
        assert (app.to_numpy()[m] == h.t_episode.to_numpy()[m]).all(), "application dates differ from checkpoint 1"
        h["t_episode"] = h.prop_id.map(ep.set_index("prop_id").t_first).astype("datetime64[ns]")
        events = a.issue_events
        notes["dating"] = "issue date of the episode's first permit (§12.10); episodes and events of §4 re-dated, not re-derived"
    fw = RT.world(mode, h, events)
    if mode == "decoy":  # nothing about the real events stays in reach, as run_tests.load
        h = h.drop(columns=["holds_event", "fold", "t_episode"])
    house, date, key, t_ep, holds = fw
    win = C.window_of(date)
    out_of_study = win < 0
    if out_of_study.any():  # only issue dating can move an event outside the study months
        assert sp["dating"] == "issue"
        notes["events_outside_the_study_months"] = int(out_of_study.sum())
        notes["events_outside_the_study_months_by_month"] = {
            str(k): int(v) for k, v in pd.Series(pd.DatetimeIndex(date[out_of_study]).strftime("%Y-%m")).value_counts().sort_index().items()}
    keep = ~out_of_study
    fw_cases = (house[keep], date[keep], key[keep], t_ep, holds)
    if sp["world"] == "foundation":
        return inputs, h, fw, fw_cases, notes
    t_dem_real = h.t_demolition.to_numpy("datetime64[ns]")
    cens = pd.read_parquet(a.censoring, columns=["prop_id", "t_demolition"])
    if mode == "real":
        pos = pd.Series(np.arange(len(h)), index=h.prop_id)
        d_house = cens.prop_id.map(pos).to_numpy(np.int64)
        d_date = cens.t_demolition.to_numpy("datetime64[ns]")
        t_dem = t_dem_real
    else:
        d_date = cens.t_demolition.to_numpy("datetime64[ns]")
        d_house = np.random.default_rng(DEMOLITION_DECOY_SEED).integers(0, len(h), len(d_date))
        t_dem = np.full(len(h), NAT)
        for k in np.argsort(d_date, kind="stable"):
            if np.isnat(t_dem[d_house[k]]) or d_date[k] < t_dem[d_house[k]]:
                t_dem[d_house[k]] = d_date[k]
        notes["demolition_decoy_seed"] = DEMOLITION_DECOY_SEED
    in_study = C.window_of(d_date) >= 0
    notes["demolitions_in_file"] = int(len(d_date))
    notes["demolitions_outside_the_study_months"] = int((~in_study).sum())
    world = dict(kind=sp["world"], d_house=d_house[in_study], d_date=d_date[in_study], t_dem=t_dem,
                 f_house=house[keep], f_date=date[keep])
    return inputs, h, fw, world, notes


def outcome_cases(world, h, t_ep, HV):
    """D1 and D2 cases (module docstring). Returns cases (house, date, window), drops and notes."""
    t_dem = world["t_dem"]
    if world["kind"] == "demolition":
        house, date = world["d_house"], world["d_date"]
        first = t_dem[house] == date  # the house's first total demolition (decoys drawn twice keep the earliest)
        ep_rule = ~np.isnat(t_ep[house]) & (t_ep[house] <= date)
        ep_reason = "matched foundation episode on or before the demolition date"
    else:
        assert (world["f_house"] >= 0).all(), "a foundation event is not at an eligible house"
        ev = pd.DataFrame({"house": world["f_house"], "date": world["f_date"]}).groupby("house").date.min()
        dm = pd.DataFrame({"house": world["d_house"], "date": world["d_date"]}).groupby("house").date.min()
        comp = pd.concat([ev, dm], axis=1, keys=["event", "demolition"])
        comp["date"] = comp.min(axis=1)
        house = comp.index.to_numpy(np.int64)
        date = comp.date.to_numpy("datetime64[ns]")
        is_event = comp.event.to_numpy("datetime64[ns]") == date
        first = np.ones(len(house), bool)
        te = t_ep[house]
        ep_rule = ~np.isnat(te) & ((te < date) | ((te == date) & ~is_event))
        ep_reason = "matched foundation episode before the date that is not the event itself"
    key = h.prop_id.to_numpy(np.int64)[house]
    order = np.lexsort((key, date))
    house, date, first, ep_rule = house[order], date[order], first[order], ep_rule[order]
    first &= ~pd.Series(house).duplicated().to_numpy()  # one case per house (decoys drawn twice on one date)
    win = C.window_of(date)
    assert (win >= 0).all()
    reason = np.full(len(house), "", dtype=object)
    reason[~first] = "not the house's first demolition"
    reason[~h.complete_b1.to_numpy(bool)[house] & (reason == "")] = "missing Baseline 1 input"
    reason[ep_rule & (reason == "")] = ep_reason
    reason[~HV[win, house] & (reason == "")] = "no value in the window"
    ok = reason == ""
    cases = pd.DataFrame({"house": house[ok], "date": date[ok], "window": win[ok]})
    drops = {str(k): int(v) for k, v in pd.Series(reason[~ok]).value_counts().items()}
    notes = dict(candidates=int(len(house)))
    if world["kind"] == "composite":
        notes["cases_that_are_foundation_events"] = int(is_event[order][ok].sum())
        notes["cases_that_are_demolitions"] = int((~is_event[order][ok]).sum())
    return cases, drops, notes


# ---------------------------------------------------------------- controls, baselines, models
def local_risk_sets(case_house, case_date, case_window, t_episode, t_demolition, HV, xy_km, rng, n_controls=C.CONTROLS):
    """§12.2: per case, min(50, pool) controls drawn without replacement (one generator, case order) from the houses
    whose parcel point lies within 1 km (inclusive) of the case's, with a value in the case's window, at risk at the case
    date (shared rule), the case excluded. A case with an empty pool is left out. Returns rows as testa_core.risk_sets
    and the pool sizes."""
    tree = cKDTree(xy_km)
    houses, sets, ys, keep, pools = [], [], [], [], []
    k = 0
    for c, t, w in zip(case_house, case_date, case_window):
        near = np.sort(np.asarray(tree.query_ball_point(xy_km[c], r=LOCAL_RADIUS_KM), dtype=np.int64))
        ok = HV[w, near] & C.at_risk(t, t_episode[near], t_demolition[near]) & (near != c)
        pool = near[ok]
        pools.append(len(pool))
        if len(pool) == 0:
            keep.append(False)
            continue
        controls = rng.choice(pool, min(n_controls, len(pool)), replace=False)
        houses.append(np.r_[c, controls])
        sets.append(np.full(len(controls) + 1, k))
        ys.append(np.r_[1, np.zeros(len(controls), dtype=np.int64)])
        keep.append(True)
        k += 1
    keep = np.asarray(keep)
    house, rs = np.concatenate(houses), np.concatenate(sets)
    cw, cd = np.asarray(case_window)[keep], np.asarray(case_date)[keep]
    rows = dict(house=house, set=rs, y=np.concatenate(ys), window=cw[rs], date=cd[rs])
    return rows, keep, np.asarray(pools)


def other_bp_counts(path, h, house, date):
    """Count of the house's non-foundation building permits dated in [date - 5 years, date) (§9 Baseline 2)."""
    bp = pd.read_parquet(path, columns=["prop_id", "date"])
    pos = pd.Series(np.arange(len(h)), index=h.prop_id)
    bh = bp.prop_id.map(pos)
    assert bh.notna().all() and bp.date.notna().all(), "a permit is not at an eligible house or has no date"
    K = 100_000
    day = lambda t: (np.asarray(t, dtype="datetime64[D]") - np.datetime64("1970-01-01", "D")).astype(np.int64)  # noqa: E731
    keys = np.sort(bh.to_numpy(np.int64) * K + day(bp.date.to_numpy("datetime64[ns]")))
    lo_date = (pd.DatetimeIndex(date) - pd.DateOffset(years=5)).to_numpy("datetime64[ns]")
    hi = np.searchsorted(keys, house * K + day(date), side="left")
    lo = np.searchsorted(keys, house * K + day(lo_date), side="left")
    return (hi - lo).astype(float)


def model(kind):
    if kind == HGB:
        return HistGradientBoostingClassifier(random_state=0)
    return N.model(kind)


def oof(X, y, fold, kind):
    """nyc_lib.oof for its models; the same fold rule for boosted trees."""
    if kind in (LR, RF):
        return N.oof(X, y, fold, kind)
    s = np.full(len(y), np.nan)
    for k in range(N.N_FOLDS):
        tr, te = fold != k, fold == k
        if te.any() and y[tr].sum() > 0:
            s[te] = model(kind).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return s


def scores(X, y, fold, kind):
    s = oof(X, y, fold, kind)
    assert np.isfinite(s).all()
    return s


def observed_quantiles(v_all, geo):
    """testa_core.observed_quantiles, with no quantile (NaN) in windows where the field has no value."""
    vals = v_all[:, geo.house_pixel]
    q = np.full((len(C.QS), vals.shape[0]), np.nan)
    ok = np.isfinite(vals).any(axis=1)
    q[:, ok] = C.window_quantiles(vals[ok])
    return q


# ---------------------------------------------------------------- the analysis
class Fields:
    """The analysis's fields: observed standardised values, raw values, validity, stores and quantile files."""

    def __init__(self, a, sp, geo):
        self.names = sp["fields"]
        self.v, self.U, self.stores, self.qS, self.meta = {}, {}, {}, {}, {}
        W = len(C.MONTHS)
        for name in self.names:
            v = C.load_field(a.field[name], geo)
            fp = C.null_fingerprint(v[:, geo.null_pixels], geo)
            self.v[name] = v
            self.U[name] = C.standardise(v[:, geo.house_pixel], np.arange(W)[:, None], observed_quantiles(v, geo))
            store = C.SurrogateStore(a.surrogates[name], fp, check_hash=True)
            qmeta = json.loads(Path(str(a.quantiles[name]) + ".json").read_text())
            assert qmeta["surrogates_sha256"] == store.meta["sha256"] and qmeta["sha256"] == C.sha256(a.quantiles[name])
            qS = np.load(a.quantiles[name])
            assert qS.shape == (store.draws, len(C.QS), W)
            run = Path(str(a.surrogates[name]) + ".run.json")
            first = json.loads(run.read_text()).get("first_window_with_values") if run.exists() else None
            if name in FIRST_WINDOW:
                assert first == FIRST_WINDOW[name], f"{name}: surrogate file starts at {first}"
            self.stores[name], self.qS[name] = store, qS
            self.meta[name] = dict(field=C.sha256(a.field[name]), null_fingerprint=fp, surrogates=store.meta["sha256"],
                                   quantiles=qmeta["sha256"], first_window_with_values=first)
        if sp["mask"] is None:
            HV = np.ones((W, len(geo.house_pixel)), bool)
            for v in self.v.values():
                HV &= C.has_value_matrix(v, geo)
        else:
            m = C.load_field(a.mask_field, geo)
            HV = C.has_value_matrix(m, geo)
            self.meta["mask"] = dict(field=C.sha256(a.mask_field), name=sp["mask"])
        self.HV = HV


class Analysis:
    def __init__(self, sp, a, mode, h, geo, F, fw, world, notes):
        self.sp, self.kind, self.notes = sp, sp["kind"], dict(notes)
        house, date, key, t_ep, holds = fw
        t_dem = h.t_demolition.to_numpy("datetime64[ns]")
        if sp["world"] == "foundation":
            self.events_in_file = len(date)
            self.cases, self.dropped, _ = RT.cases_of(*world[:3], h, t_ep, F.HV)
        else:
            t_dem = world["t_dem"]
            self.cases, self.dropped, extra = outcome_cases(world, h, t_ep, F.HV)
            self.events_in_file = extra["candidates"]
            self.notes.update({f"{sp['world']}_{k}": v for k, v in extra.items()})
        if mode == "real" and sp["fold_seed"] is None:
            self.fold_h = h.fold.to_numpy(np.int64)
            if sp["world"] == "foundation":
                assert (C.fold_of_houses(h, holds) == self.fold_h).all(), "fold map differs from checkpoint 1"
        else:
            seed = C.FOLD_SEED if sp["fold_seed"] is None else sp["fold_seed"]
            self.fold_h = C.fold_of_houses(h, holds, seed=seed)
        ch, cd, cw = self.cases.house.to_numpy(), self.cases.date.to_numpy("datetime64[ns]"), self.cases.window.to_numpy()
        rng = np.random.default_rng(C.CONTROL_SEED)
        if sp["controls"] == "local":
            rows, kept, pools = local_risk_sets(ch, cd, cw, t_ep, t_dem, F.HV, h[["x_km", "y_km"]].to_numpy(float), rng)
            self.notes["local_controls"] = dict(
                radius_km=LOCAL_RADIUS_KM, cases_with_empty_pool=int((~kept).sum()),
                sets_with_fewer_than_50=int(((pools > 0) & (pools < C.CONTROLS)).sum()),
                pool_size_quantiles={str(q): float(np.percentile(pools, q)) for q in (0, 5, 25, 50, 75, 95, 100)})
            self.cases = self.cases[kept].reset_index(drop=True)
        else:
            rows = C.risk_sets(ch, cd, cw, t_ep, t_dem, F.HV, rng)
        rows, self.lost = C.drop_incomplete(rows, h)
        X = C.design(h, rows["house"], rows["date"])
        if sp["baseline"] == "b1_no_income":
            X = np.delete(X, INCOME, axis=1)
        elif sp["baseline"] == "b2":
            bp = other_bp_counts(a.other_bp, h, rows["house"], rows["date"])
            canopy = pd.read_parquet(a.features, columns=["prop_id", "canopy_share"])
            assert (canopy.prop_id.to_numpy() == h.prop_id.to_numpy()).all()
            cs = canopy.canopy_share.to_numpy(float)[rows["house"]]
            X = np.column_stack([X, bp, cs])
            bad = ~np.isfinite(X).all(axis=1)
            bad_sets = np.unique(rows["set"][bad & (rows["y"] == 1)])
            drop = bad | np.isin(rows["set"], bad_sets)
            self.notes["baseline_2"] = dict(
                rows_missing_an_input=int(bad.sum()), risk_sets_left_out_case_missing=int(len(bad_sets)),
                control_rows_left_out=int((drop & (rows["y"] == 0)).sum()),
                cases_dated_before_2018_11_04=int(((rows["y"] == 1) & ~drop & (rows["date"] < np.datetime64("2018-11-04"))).sum()),
                other_bp_count_case_rows_mean=float(bp[(rows["y"] == 1) & ~drop].mean()),
                other_bp_count_control_rows_mean=float(bp[(rows["y"] == 0) & ~drop].mean()))
            rows = {k: v[~drop] for k, v in rows.items()}
            X = X[~drop]
            keep_cases = np.isin(np.arange(len(self.cases)), np.unique(rows["set"]))
            self.cases = self.cases[keep_cases].reset_index(drop=True)
        self.rows, self.X = rows, X
        self.y, self.win, self.rs = rows["y"], rows["window"], rows["set"]
        self.fold = self.fold_h[rows["house"]]
        self.pix = geo.house_null[rows["house"]]
        assert (self.pix >= 0).all()
        self.notes["risk_sets_without_a_control_row"] = int((np.bincount(self.rs)[np.unique(self.rs)] < 2).sum())
        cases_per_set = np.bincount(self.rs, weights=self.y)
        assert (cases_per_set[np.unique(self.rs)] == 1).all(), "every risk set must keep exactly one case row"
        self.u = np.column_stack([F.U[n][self.win, rows["house"]] for n in F.names])
        assert np.isfinite(self.u).all() and np.isfinite(self.X).all()
        self.block = h.block.to_numpy().astype(str)[rows["house"]]
        self.name = "analysis"
        self.mb = RR.metric_set(self.y, scores(self.X, self.y, self.fold, self.kind), self.rs)
        self.mv = RR.metric_set(self.y, scores(np.column_stack([self.X, self.u]), self.y, self.fold, self.kind), self.rs)
        self.observed = {k: self.mv[k] - self.mb[k] for k in METRICS}

    def describe(self):
        years = pd.DatetimeIndex(self.cases.date).year
        return dict(events_in_file=self.events_in_file, cases=int(len(self.cases)), dropped=self.dropped,
                    rows=int(len(self.y)), control_rows_dropped_missing_inputs=self.lost, notes=self.notes,
                    cases_by_year={str(k): int(v) for k, v in pd.Series(years).value_counts().sort_index().items()},
                    cases_per_fold=[int(self.y[self.fold == k].sum()) for k in range(5)],
                    controls_per_set_median=float(np.median(np.bincount(self.rs) - 1)),
                    blocks_with_rows=int(len(np.unique(self.block))), baseline=self.mb, with_indicator=self.mv,
                    observed=self.observed)


# ---------------------------------------------------------------- null and bootstrap
_G = {}


def _null(d):
    A, F = _G["A"], _G["F"]
    cols = []
    for n in F.names:
        raw = np.asarray(F.stores[n].S[d][A.win, A.pix], dtype=np.float64)
        cols.append(C.standardise(raw, A.win, F.qS[n][d]))
    m = RR.metric_set(A.y, scores(np.column_stack([A.X] + cols), A.y, A.fold, A.kind), A.rs)
    return d, {k: m[k] - A.mb[k] for k in METRICS}


def null_metrics(A, F, draws, workers):
    _G.update(A=A, F=F)
    out = [None] * draws
    with mp.get_context("fork").Pool(workers) as pool:
        for d, r in pool.imap_unordered(_null, range(draws), chunksize=1 if A.kind != LR else 2):
            out[d] = r
    _G.clear()
    stats = {k: np.array([r[k] for r in out]) for k in METRICS}
    assert all(np.isfinite(v).all() for v in stats.values())
    return stats


def boot_rows(A, idx):
    """run_report.boot_rows with the analysis's model."""
    yy, ff = A.y[idx], A.fold[idx]
    sb, sv = oof(A.X[idx], yy, ff, A.kind), oof(np.column_stack([A.X[idx], A.u[idx]]), yy, ff, A.kind)
    ok = np.isfinite(sb) & np.isfinite(sv)
    if not 0 < yy[ok].sum() < ok.sum():
        return None
    return {"pr": average_precision_score(yy[ok], sv[ok]) - average_precision_score(yy[ok], sb[ok]),
            "roc": roc_auc_score(yy[ok], sv[ok]) - roc_auc_score(yy[ok], sb[ok]),
            "top10": N.recall_top(yy[ok], sv[ok]) - N.recall_top(yy[ok], sb[ok])}


def _boot(s):
    rng = np.random.default_rng(s)
    draw = rng.choice(_G["n_universe"], _G["n_universe"], replace=True)
    return s, boot_rows(_G["A"], np.concatenate([_G["members"][i] for i in draw]))


def bootstrap(A, n_boot, workers):
    """run_report.joint_bootstrap for one analysis (universe = its own blocks), with its model."""
    universe = np.unique(A.block)
    _G.update(A=A, n_universe=len(universe), members=RR.members_of(A.block, universe))
    res = [None] * n_boot
    with mp.get_context("fork").Pool(workers) as pool:
        for s, r in pool.imap_unordered(_boot, range(n_boot), chunksize=1 if A.kind != LR else 4):
            res[s] = r
    _G.clear()
    ok = [r for r in res if r is not None]
    return dict(resamples=n_boot, seeds="default_rng(s), s = 0 .. resamples - 1", universe_blocks=int(len(universe)),
                resamples_with_value=len(ok), resamples_without_value=n_boot - len(ok),
                **{f"{k}_ci95": [float(np.percentile([b[k] for b in ok], q)) for q in (2.5, 97.5)] for k in BOOT_METRICS},
                per_resample=res)


# ---------------------------------------------------------------- commands
def pairs(items):
    out = {}
    for it in items or []:
        k, _, v = it.partition("=")
        assert k and v and k not in out, f"bad NAME=PATH: {it}"
        out[k] = Path(v)
    return out


def prepare(a, sp):
    for k in ("field", "surrogates", "quantiles"):
        assert set(getattr(a, k)) == set(sp["fields"]), f"--{k} must name exactly {sp['fields']}"
    assert (sp["mask"] is None) == (a.mask_field is None), "--mask-field is required exactly for secondary 12"
    if sp["dating"] == "issue":
        assert a.issue_events and a.issue_episodes
    if sp["baseline"] == "b2":
        assert a.other_bp
    inputs, h, fw, world, notes = load(a, a.mode, sp)
    geo = C.Geometry(h)
    F = Fields(a, sp, geo)
    A = Analysis(sp, a, a.mode, h, geo, F, fw, world, notes)
    return inputs, h, geo, F, A


def stamp():
    return dict(sources=source_hashes(), host=platform.node(), python=platform.python_version(),
                finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))


def run_analysis(a, name, sp):
    t0 = time.perf_counter()
    started = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    inputs, h, geo, F, A = prepare(a, sp)
    draws = sp["draws"] if a.draws is None else a.draws
    boot = sp["boot"] if a.boot is None else a.boot
    R = dict(label=RT.LABEL[a.mode], secondary=name, mode=a.mode, spec=sp, **A.describe())
    t = time.perf_counter()
    null = null_metrics(A, F, draws, a.workers)
    R["null"] = dict(draws=int(draws), draw_indices=f"0 .. {draws - 1} of the stored draws",
                     **{f"{k}_p": C.p_value(A.observed[k], null[k]) for k in METRICS},
                     **{f"{k}_null_median": float(np.median(null[k])) for k in METRICS},
                     statistics={k: v.tolist() for k, v in null.items()}, seconds=time.perf_counter() - t)
    t = time.perf_counter()
    R["bootstrap"] = bootstrap(A, boot, a.workers) if boot else None
    R["bootstrap_seconds"] = time.perf_counter() - t
    R["inputs"] = dict(checkpoint1=inputs, events=C.sha256(a.events), fields=F.meta,
                       issue_events=C.sha256(a.issue_events) if a.issue_events else None,
                       issue_episodes=C.sha256(a.issue_episodes) if a.issue_episodes else None,
                       other_bp=C.sha256(a.other_bp) if a.other_bp else None)
    R.update(workers=a.workers, started=started, elapsed_seconds=time.perf_counter() - t0, **stamp())
    return R, A, F


def summary(R):
    s = {k: R[k] for k in ("label", "secondary", "mode", "cases", "rows", "dropped", "observed")}
    s["p"] = {k: R["null"][f"{k}_p"] for k in METRICS}
    if R["bootstrap"]:
        s["ci95"] = {k: R["bootstrap"][f"{k}_ci95"] for k in BOOT_METRICS}
    s["notes"] = R["notes"]
    s["seconds"] = dict(null=R["null"]["seconds"], bootstrap=R["bootstrap_seconds"], total=R["elapsed_seconds"])
    return s


def write(out, R, fname="result.json"):
    out.mkdir(parents=True, exist_ok=True)
    (out / fname).write_text(json.dumps(R, indent=1, default=str) + "\n")
    print(json.dumps(summary(R), indent=1, default=str))


def cmd_run(a):
    sp = SPECS[a.secondary]
    assert a.secondary != "anchor"
    if a.mode == "real":
        assert a.draws is None and a.boot is None, "the real run uses the plan's counts"
    R, _, _ = run_analysis(a, a.secondary, sp)
    write(a.out, R)


def cmd_anchor(a):
    """The generic path with the primary settings equals the primary analysis; its bootstrap equals run_report's."""
    sp = SPECS["anchor"]
    R, A, F = run_analysis(a, "anchor", sp)
    prim = json.loads(Path(a.primary).read_text())
    assert prim["mode"] == a.mode
    n = R["null"]["draws"]
    pr = np.asarray(R["null"]["statistics"]["pr"])
    chk = dict(cases=R["cases"] == prim["cases"], rows=R["rows"] == prim["rows"],
               dropped=R["dropped"] == {str(k): int(v) for k, v in prim["dropped"].items()},
               control_rows_dropped=R["control_rows_dropped_missing_inputs"] == prim["control_rows_dropped_missing_inputs"],
               baseline_ap_diff=abs(A.mb["pr"] - prim["baseline_average_precision"]),
               observed_diff=abs(A.observed["pr"] - prim["observed"]),
               null_pr_max_abs_diff=float(np.max(np.abs(pr - np.asarray(prim["statistics"][:n])))))
    if a.report:
        rep = json.loads(Path(a.report).read_text())["foundation"]
        chk["report_observed_max_abs_diff"] = max(abs(A.observed[k] - rep["observed"][k]) for k in METRICS)
        chk["report_null_max_abs_diff"] = max(float(np.max(np.abs(np.asarray(R["null"]["statistics"][k])
                                                                   - np.asarray(rep["null"]["statistics"][k][:n]))))
                                              for k in METRICS)
    ref = RR.joint_bootstrap([A], a.check_boot, a.workers)
    mine = bootstrap(A, a.check_boot, a.workers)
    chk["bootstrap_resamples_compared"] = a.check_boot
    def same(x, y):
        if x is None or y is None:
            return x is None and y is None
        return all(abs(x[k] - y[k]) <= 1e-12 for k in BOOT_METRICS)

    chk["bootstrap_equal"] = all(same(x["analysis"], y) for x, y in zip(ref["per_resample"], mine["per_resample"]))
    tol = [v for k, v in chk.items() if k.endswith("diff")]
    chk["pass"] = bool(chk["cases"] and chk["rows"] and chk["dropped"] and chk["control_rows_dropped"]
                       and max(tol) <= 1e-12 and chk["bootstrap_equal"])
    R["anchor_check"] = chk
    write(a.out, R, "anchor.json")
    print(json.dumps(chk, indent=1))
    assert chk["pass"], "the generic path differs from the primary analysis"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("run", "anchor"):
        s = sub.add_parser(name)
        for k in ("features", "grid", "episodes", "censoring", "events", "out"):
            s.add_argument(f"--{k}", type=Path, required=True)
        s.add_argument("--mode", choices=("decoy", "real"), required=True)
        for k in ("field", "surrogates", "quantiles"):
            s.add_argument(f"--{k}", action="append", required=True, help="NAME=PATH")
        for k in ("mask-field", "issue-events", "issue-episodes", "other-bp"):
            s.add_argument(f"--{k}", dest=k.replace("-", "_"), type=Path, default=None)
        s.add_argument("--workers", type=int, required=True)
        s.add_argument("--draws", type=int, default=None, help="default: the plan's count; fewer only for checks")
        s.add_argument("--boot", type=int, default=None, help="default: the plan's count; fewer only for checks")
        if name == "run":
            s.add_argument("--secondary", choices=[k for k in SPECS if k != "anchor"], required=True)
        else:
            s.add_argument("--primary", type=Path, required=True, help="run_tests.py test_a.json of the same mode")
            s.add_argument("--report", type=Path, default=None, help="run_report.py report_a.json (real mode)")
            s.add_argument("--check-boot", type=int, default=20)
    a = p.parse_args(argv)
    for k in ("field", "surrogates", "quantiles"):
        setattr(a, k, pairs(getattr(a, k)))
    {"run": cmd_run, "anchor": cmd_anchor}[a.cmd](a)


if __name__ == "__main__":
    main()
