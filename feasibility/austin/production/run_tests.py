"""Test A and Test B on the decoy outcome and on the real outcome (AUSTIN_PLAN.md §13 steps 4 and 5; §8 shared at-risk
rule, §8A risk sets, §8B panel, §9 models, §10 nulls, §11 rule). The primary analyses only.

testa_core.py (Test A core, hashed at checkpoint 1) and the frozen test_b.py are imported unchanged.

Worlds
  real   the events of checkpoint 1 (foundation_events.parquet: prop_id, t_first) at their houses; each house's
         episode date is its first matched foundation episode (testa_core.load_houses); folds from the houses that
         hold an event (checked equal to the checkpoint-1 fold column).
  decoy  (§13 step 4, as NYC: "each event moved to a random eligible parcel (seed 99), keeping its date")
         - only the t_first column of the events file is read; no real event's house, and no holds_event or fold
           column, enters the decoy world;
         - decoy houses: numpy default_rng(99).integers(0, 149_316, 2_846) over the eligible houses in prop_id order,
           one per event in the file's row order (uniform, with replacement, no redraws), as NYC's decoy_events;
         - episode dates (the shared at-risk rule): a house's real first matched episode is kept if it is before
           2018-08-01, real episodes inside the study period are ignored, and a decoy sets its house's episode date
           (the earliest decoy if the house is drawn more than once), as the planted-signal check's synthetic world;
           real demolition dates are kept;
         - folds: testa_core.fold_of_houses with "the house holds a decoy" (before the case rules).
Cases (§8A), the same function in both worlds: events in order of date, then prop_id, each dropped for the first
  reason that applies: house not eligible; missing Baseline 1 input; demolition-censored on or before the event date;
  not at risk at the event date (the house has an earlier matched episode, or an earlier event or decoy on the same
  date); no value in the window. On real events the fourth reason cannot apply (each event is its house's first
  matched episode), and the function equals testa_core.real_cases (command selfcheck).
Test A: risk sets with numpy default_rng(2029) in case order (§8A), rows missing inputs dropped, Baseline 1 + x/y,
  testa_core.TestA; the observed statistic with the observed standardised field; null draw d with stored surrogate d
  standardised by its own quantiles (planted_signal.py quantiles); p and the §11 rule (testa_core).
Test B panel (§8B):
  - rows: the 250 m cells of i12_testb_cells.py by the 28 quarters 2018-Q4 .. 2025-Q3;
  - y: the events of the world whose house is eligible and at risk at the event date (not demolition-censored on or
    before it; the first matched episode, or the first decoy, at the house), counted in the cell of the house's
    parcel point and the quarter of the event date. Baseline 1 completeness and the house's own pixel value do not
    enter (§8B counts events by cell);
  - n: the houses of the cell at risk at the start of the quarter, evaluated with testa_core.at_risk on the day
    before the quarter's first day. Authors' choice: at_risk counts an episode or demolition "on or before t" as
    ended, so evaluating on the first day itself would drop from n a house whose event falls on that day while the
    event counts in y, and would remove a house demolished on that day from its own quarter, where §5 removes it
    "from the next quarter". Every counted event's house is checked to be in n of its row;
  - v: the cell's 12-month velocity for the quarter (i12 field v); block: the cell's 2 km block (i12);
  - rows used: v has a value and n > 0. Fitted by test_b.fit_panel; null by test_b.null_test on the Test B null.
Outputs: OUT/test_a.json, OUT/test_b.json (the decoy run's records carry "DECOY" in their label).
Usage:
  python -I run_tests.py selfcheck  COMMON --events EV --field F --out OUT.json
  python -I run_tests.py testa      COMMON --mode decoy|real --events EV --field F --surrogates S --quantiles Q --out DIR --workers N
  python -I run_tests.py testb      COMMON --mode decoy|real --events EV --cells CELLS --surrogates SB --out DIR [--expected-draws 999]
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

HERE = Path(__file__).resolve().parent
PS_DIR = HERE.parent / "planted_signal"
sys.path[:0] = [str(HERE), str(PS_DIR)]
import testa_core as C  # noqa: E402
import planted_signal as PS  # noqa: E402  (checkpoint-1 input hash check only)
import test_b as TB  # noqa: E402  (frozen, on the path through testa_core)

DECOY_SEED, ELIGIBLE, EVENTS = 99, 149_316, 2_846
NAT = np.datetime64("NaT", "ns")
LABEL = {"decoy": "DECOY RUN (code check, not a result)", "real": "REAL RUN"}


def source_hashes():
    return {p.name: C.sha256(p) for p in (HERE / "run_tests.py", PS_DIR / "testa_core.py", PS_DIR / "planted_signal.py",
                                          C.FROZEN / "nyc_lib.py", C.FROZEN / "test_b.py")}


def world(mode, h, events_path):
    """(event house or -1, event date, sort key, episode date per house, holds per house) of the run's world."""
    if mode == "real":
        ev = pd.read_parquet(events_path, columns=["prop_id", "t_first"])
        pos = pd.Series(np.arange(len(h)), index=h.prop_id)
        house = ev.prop_id.map(pos).fillna(-1).to_numpy(np.int64)
        date = ev.t_first.to_numpy("datetime64[ns]")
        key = ev.prop_id.to_numpy(np.int64)
        t_ep = h.t_episode.to_numpy("datetime64[ns]")
        holds = h.holds_event.to_numpy(bool)
        assert (np.isin(np.arange(len(h)), house[house >= 0]) == holds).all(), "holds_event differs from the events"
        return house, date, key, t_ep, holds
    ev = pd.read_parquet(events_path, columns=["t_first"])
    assert len(h) == ELIGIBLE and len(ev) == EVENTS
    date = ev.t_first.to_numpy("datetime64[ns]")
    house = np.random.default_rng(DECOY_SEED).integers(0, len(h), len(date))
    key = h.prop_id.to_numpy(np.int64)[house]
    t_real = h.t_episode.to_numpy("datetime64[ns]")
    t_ep = np.where(t_real < np.datetime64(C.START.to_datetime64(), "ns"), t_real, NAT)
    for k in np.argsort(date, kind="stable"):
        hk = house[k]
        if np.isnat(t_ep[hk]) or date[k] < t_ep[hk]:
            t_ep[hk] = date[k]
    holds = np.zeros(len(h), bool)
    holds[house] = True
    return house, date, key, t_ep, holds


def cases_of(house, date, key, h, t_ep, HV):
    """§8A cases and, for Test B, the events counted (eligible and at risk at the event date)."""
    order = np.lexsort((key, date))  # by date, then prop_id (stable)
    house, date = house[order], date[order]
    win = C.window_of(date)
    assert (win >= 0).all(), "event outside the study months"
    ok = house >= 0
    hh = np.where(ok, house, 0)
    t_dem = h.t_demolition.to_numpy("datetime64[ns]")
    first = np.zeros(len(house), bool)
    seen = set()
    for k in range(len(house)):
        if ok[k] and t_ep[hh[k]] == date[k] and hh[k] not in seen:
            first[k] = True
            seen.add(hh[k])
    reason = np.full(len(house), "", dtype=object)
    reason[~ok] = "house not eligible"
    m = ok & ~h.complete_b1.to_numpy(bool)[hh]
    reason[m & (reason == "")] = "missing Baseline 1 input"
    demolished = ok & (t_dem[hh] <= date)
    reason[demolished & (reason == "")] = "demolition-censored on or before the event date"
    reason[ok & ~first & (reason == "")] = "not at risk at the event date"
    m = ok & ~HV[win, hh]
    reason[m & (reason == "")] = "no value in the window"
    keep = reason == ""
    cases = pd.DataFrame({"house": house[keep], "date": date[keep], "window": win[keep]})
    counted = ok & ~demolished & first
    drops = {str(k): int(v) for k, v in pd.Series(reason[~keep]).value_counts().items()}
    return cases, drops, dict(house=house[counted], date=date[counted])


def load(a, mode):
    inputs = PS.checkpoint1_inputs(a)
    h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
    house, date, key, t_ep, holds = world(mode, h, a.events)
    if mode == "decoy":  # nothing about the real events stays in reach
        h = h.drop(columns=["holds_event", "fold", "t_episode"])
    return inputs, h, house, date, key, t_ep, holds


def cmd_selfcheck(a):
    """cases_of on the real events in the real world equals testa_core.real_cases (validity of the given field only)."""
    inputs, h, house, date, key, t_ep, holds = load(a, "real")
    geo = C.Geometry(h)
    HV = C.has_value_matrix(C.load_field(a.field, geo), geo)
    ours, d_ours, counted = cases_of(house, date, key, h, t_ep, HV)
    ref, d_ref = C.real_cases(pd.read_parquet(a.events), h, HV)
    d_ref = {str(k): int(v) for k, v in d_ref.items()}
    fold_h = C.fold_of_houses(h, holds)
    R = dict(field_sha256=C.sha256(a.field), cases=len(ours), cases_equal=bool(ours.equals(ref)), drops=d_ours,
             drops_equal=d_ours == d_ref, counted_for_test_b=int(len(counted["house"])),
             folds_equal_checkpoint1=bool((fold_h == h.fold.to_numpy()).all()), sources=source_hashes())
    R["pass"] = bool(R["cases_equal"] and R["drops_equal"] and R["folds_equal_checkpoint1"])
    Path(a.out).write_text(json.dumps(R, indent=1, default=str) + "\n")
    print(json.dumps(R, indent=1, default=str))


# ---------------------------------------------------------------- Test A
_A = {}


def _null_a(d):
    raw = np.asarray(_A["store"].S[d][_A["win"], _A["pix"]], dtype=np.float64)
    return d, _A["A"].delta(C.standardise(raw, _A["win"], _A["qS"][d]))


def cmd_testa(a):
    t0 = time.perf_counter()
    inputs, h, house, date, key, t_ep, holds = load(a, a.mode)
    geo = C.Geometry(h)
    v_all = C.load_field(a.field, geo)
    fp = C.null_fingerprint(v_all[:, geo.null_pixels], geo)
    HV = C.has_value_matrix(v_all, geo)
    W = len(C.MONTHS)
    U = C.standardise(v_all[:, geo.house_pixel], np.arange(W)[:, None], C.observed_quantiles(v_all, geo))
    cases, dropped, _ = cases_of(house, date, key, h, t_ep, HV)
    fold_h = C.fold_of_houses(h, holds)
    if a.mode == "real":
        assert (fold_h == h.fold.to_numpy()).all(), "fold map differs from checkpoint 1"
    rows = C.risk_sets(cases.house.to_numpy(), cases.date.to_numpy("datetime64[ns]"), cases.window.to_numpy(), t_ep,
                       h.t_demolition.to_numpy("datetime64[ns]"), HV, np.random.default_rng(C.CONTROL_SEED))
    rows, lost = C.drop_incomplete(rows, h)
    X = C.design(h, rows["house"], rows["date"])
    y, fold, win = rows["y"], fold_h[rows["house"]], rows["window"]
    pix = geo.house_null[rows["house"]]
    assert (pix >= 0).all()
    A = C.TestA(X, y, fold)
    observed = A.delta(U[win, rows["house"]])
    store = C.SurrogateStore(a.surrogates, fp, check_hash=True)
    qmeta = json.loads(Path(str(a.quantiles) + ".json").read_text())
    assert qmeta["surrogates_sha256"] == store.meta["sha256"] and qmeta["sha256"] == C.sha256(a.quantiles)
    qS = np.load(a.quantiles)
    assert qS.shape == (store.draws, len(C.QS), W)
    draws = store.draws if a.draws is None else a.draws
    _A.update(store=store, win=win, pix=pix, qS=qS, A=A)
    stats = np.full(draws, np.nan)
    t1 = time.perf_counter()
    with mp.get_context("fork").Pool(a.workers) as pool:
        for d, s in pool.imap_unordered(_null_a, range(draws), chunksize=2):
            stats[d] = s
    assert np.isfinite(stats).all()
    p = C.p_value(observed, stats)
    years = pd.DatetimeIndex(cases.date).year
    R = dict(label=LABEL[a.mode], test="A", mode=a.mode, events_in_file=int(len(date)),
             decoy_seed=DECOY_SEED if a.mode == "decoy" else None,
             decoy_houses_drawn_twice_or_more=int((np.bincount(house[house >= 0]) > 1).sum()) if a.mode == "decoy" else None,
             cases=int(len(cases)), dropped=dropped, rows=int(len(y)), control_rows_dropped_missing_inputs=lost,
             cases_by_year={str(k): int(v) for k, v in pd.Series(years).value_counts().sort_index().items()},
             cases_per_fold=[int(y[fold == k].sum()) for k in range(5)], houses_per_fold=[int((fold_h == k).sum()) for k in range(5)],
             baseline_average_precision=A.baseline, observed=observed, draws=int(draws), statistics=stats.tolist(),
             exceedances=int(np.sum(stats >= observed)), p=p, meets_rule=C.demonstrated(observed, p),
             null_seconds=time.perf_counter() - t1, elapsed_seconds=time.perf_counter() - t0, workers=a.workers,
             inputs=dict(checkpoint1=inputs, events=C.sha256(a.events), field=C.sha256(a.field), null_fingerprint=fp,
                         surrogates=store.meta["sha256"], quantiles=qmeta["sha256"]),
             sources=source_hashes(), host=platform.node(), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "test_a.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in R.items() if k != "statistics"}, indent=1, default=str))


# ---------------------------------------------------------------- Test B
def cmd_testb(a):
    t0 = time.perf_counter()
    inputs, h, house, date, key, t_ep, holds = load(a, a.mode)
    g = pd.read_parquet(a.grid, columns=["prop_id", "cell250"])
    assert (g.prop_id.to_numpy() == h.prop_id.to_numpy()).all()
    c = np.load(a.cells, allow_pickle=False)
    labels, quarters, block, v = c["cells"], c["quarters"], c["block"], c["v"]
    house_cell = pd.Index(labels).get_indexer(g.cell250.to_numpy())
    assert (house_cell >= 0).all()
    HV = np.ones((len(C.MONTHS), len(h)), bool)  # Test B counts do not use the house's own pixel value
    _, _, counted = cases_of(house, date, key, h, t_ep, HV)
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
        ar = C.at_risk(day_before, t_ep, t_dem)
        n[k] = np.bincount(house_cell[ar], minlength=NC)
        sel = inq & (qi == k)
        assert ar[counted["house"][sel]].all(), "a counted event's house is not in n"
    used = np.isfinite(v) & (n > 0)
    qq, cc = np.nonzero(used)
    panel = pd.DataFrame({"cell": labels[cc], "quarter": quarters[qq], "y": y[qq, cc], "n": n[qq, cc], "v": v[qq, cc],
                          "block": block[cc]})
    info = dict(events_counted=int(len(counted["house"])), events_counted_in_quarters=int(inq.sum()),
                events_outside_the_28_quarters=int((~inq).sum()), events_in_rows_used=int(panel.y.sum()),
                events_in_rows_without_value=int(y[~np.isfinite(v)].sum()), rows_possible=int(Q * NC),
                rows_with_value=int(np.isfinite(v).sum()), rows_used=int(len(panel)),
                cells_with_an_event_in_used_rows=int(panel.groupby("cell").y.sum().gt(0).sum()))
    S = np.load(a.surrogates, allow_pickle=False)
    assert np.array_equal(S["quarters"], quarters)
    res = TB.null_test(panel, S["fields"], S["quarters"], S["cells"], expected_draws=a.expected_draws)
    R = dict(label=LABEL[a.mode], test="B", mode=a.mode, panel=info, observed=res["observed"],
             statistics=[d["null_statistic"] for d in res["draws"]], exceedances=res["exceedances"], p_B=res["p_B"],
             detected=bool(res["p_B"] < 0.05), elapsed_seconds=time.perf_counter() - t0,
             inputs=dict(checkpoint1=inputs, events=C.sha256(a.events), cells=C.sha256(a.cells), surrogates=C.sha256(a.surrogates),
                         surrogate_seed=int(S["seed"])),
             sources=source_hashes(), host=platform.node(), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    a.out.mkdir(parents=True, exist_ok=True)
    panel.to_csv(a.out / "test_b_panel.csv", index=False)
    (a.out / "test_b.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in R.items() if k != "statistics"}, indent=1, default=str))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("selfcheck", "testa", "testb"):
        s = sub.add_parser(name)
        for k in ("features", "grid", "episodes", "censoring", "events", "out"):
            s.add_argument(f"--{k}", type=Path, required=True)
        if name != "selfcheck":
            s.add_argument("--mode", choices=("decoy", "real"), required=True)
            s.add_argument("--surrogates", type=Path, required=True)
        if name in ("selfcheck", "testa"):
            s.add_argument("--field", type=Path, required=True)
        if name == "testa":
            s.add_argument("--quantiles", type=Path, required=True)
            s.add_argument("--workers", type=int, required=True)
            s.add_argument("--draws", type=int, default=None, help="default: all stored draws; fewer only for checks")
        if name == "testb":
            s.add_argument("--cells", type=Path, required=True)
            s.add_argument("--expected-draws", type=int, default=999)
    a = p.parse_args(argv)
    {"selfcheck": cmd_selfcheck, "testa": cmd_testa, "testb": cmd_testb}[a.cmd](a)


if __name__ == "__main__":
    main()
