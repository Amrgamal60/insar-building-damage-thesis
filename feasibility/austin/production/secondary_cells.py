"""Secondary 1, NYC design (AUSTIN_PLAN.md §12 item 1: "250 m cells with risk sets as NYC §8, cell value as the mean of
valid pixels, and the event label as any event in the cell"; how it is computed is fixed in §15, "Secondary analyses: how
each is computed", 2026-11-15, before any secondary outcome is joined). No decision.

Data and null: secondary_cells_null.py (cells, cell value, cell Baseline 1, cell-level conditional null and its
quantiles), imported unchanged.
Risk sets: the frozen nyc_lib.risk_sets, unchanged, with rule "first" (NYC §8, as NYC's primary):
  - events: the world's events (run_tests.load: real events, or the decoys of seed 99), each in the cell of its house,
    in date then prop_id order; length key 730 (NYC's 24-month key; its first usable date, 2018-07-16, precedes every
    Austin event, so no event is skipped there); window of an event = its calendar month (§7);
  - population: every cell; has_value: the cell has a value in the event's window; base_ok: the cell has a baseline;
  - a case is the first event of its cell (later events in the cell and a second event on the same cell and date are
    dropped, NYC's reasons); controls are all population cells with a value and a baseline whose first event is after
    the case date (or never), the case cell excluded. No sampling of controls (NYC).
Rows: the case cell and every control; baseline = the cell Baseline 1 + x/y at the risk set's date
  (secondary_cells_null.Cells.design); indicator = the cell value standardised per window as §7, over all cells with a
  value (observed) or by the draw's stored quantiles (null cells with a value).
Folds: each cell takes the fold of its 2 km block in the house fold map (real: checkpoint 1; decoy: testa_core
  .fold_of_houses on the decoy houses, as run_tests).
Model, metrics, null and bootstrap: logistic regression (nyc_lib) and run_report.null_metrics / joint_bootstrap
  unchanged (999 draws of the cell null, seed 2027; 2,000 block resamples over the analysis's blocks).

Usage: python -I secondary_cells.py --mode decoy|real COMMON --events EV --cells CELLS_NPZ --nyc-cells NYC_CELLS_NPZ
         --surrogates DIR/surrogates_cells.npy --quantiles DIR/quantiles_cells.npy --out DIR --workers N [--draws n] [--boot n]
  COMMON = --features --grid --episodes --censoring (checkpoint-1 tables, hash-checked)
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import run_report as RR  # noqa: E402  (unchanged)
import secondary_cells_null as SC  # noqa: E402  (unchanged since the cell null was made)

RT, C, N = RR.RT, RR.C, RR.N
METRICS, BOOT_METRICS = RR.METRICS, RR.BOOT_METRICS
LENGTH = 730


def source_hashes():
    out = RR.source_hashes()
    for f in ("secondary_cells.py", "secondary_cells_null.py"):
        out[f] = C.sha256(HERE / f)
    return out


class CellAnalysis:
    """Attributes as run_report.Analysis, so that run_report.null_metrics and joint_bootstrap run unchanged."""

    def __init__(self, cells, h, house, date, key, holds, mode):
        self.name = "nyc_design"
        ok = house >= 0
        cell_of = np.where(ok, cells.house_cell[np.where(ok, house, 0)], -1)
        order = np.lexsort((key, date))
        ev = pd.DataFrame({"event_id": key[order], "date": date[order]})
        cell_of = cell_of[order]
        month = {f"{LENGTH}d_{pd.Timestamp(d).date()}": w for d, w in zip(ev.date, C.window_of(ev.date.to_numpy()))}
        assert min(month.values()) >= 0
        HV = cells.HV
        has_value = lambda w: HV[month[w]]  # noqa: E731
        population = np.ones(len(cells.labels), bool)
        sets, log = N.risk_sets(ev, cell_of, population, LENGTH, "first", has_value, cells.base_ok)
        self.events_in_file = int(len(ev))
        self.dropped = {str(k): int(v) for k, v in log.dropped[log.dropped != ""].value_counts().items()}
        self.events_logged = int(len(log))
        n_ctl = np.array([len(s["controls"]) for s in sets])
        cell = np.concatenate([np.r_[s["pos"], s["controls"]] for s in sets])
        rs = np.repeat(np.arange(len(sets)), n_ctl + 1)
        y = np.zeros(len(cell), np.int64)
        y[np.r_[0, np.cumsum(n_ctl + 1)[:-1]]] = 1
        set_date = np.array([s["date"] for s in sets], dtype="datetime64[ns]")
        set_win = C.window_of(set_date)
        self.cases = pd.DataFrame({"cell": [s["pos"] for s in sets], "date": set_date, "window": set_win})
        self.cell, self.rs, self.y = cell, rs, y
        self.win = set_win[rs]
        date_rows = set_date[rs]
        self.X = cells.design(cell, date_rows)
        q = C.window_quantiles(cells.value)
        U = C.standardise(cells.value, np.arange(len(C.MONTHS))[:, None], q)
        self.u = U[self.win, cell]
        self.raw = cells.value[self.win, cell]
        assert np.isfinite(self.u).all() and np.isfinite(self.raw).all()
        pos = np.full(len(cells.labels), -1, np.int64)
        pos[cells.null_cells] = np.arange(len(cells.null_cells))
        self.pix = pos[cell]
        assert (self.pix >= 0).all()
        if mode == "real":
            bf = pd.Series(h.fold.to_numpy(np.int64), index=h.block.to_numpy().astype(str))
        else:
            bf = pd.Series(C.fold_of_houses(h, holds), index=h.block.to_numpy().astype(str))
        bf = bf.groupby(level=0).agg(["min", "max"])
        assert (bf["min"] == bf["max"]).all(), "a block has two folds"
        cell_fold = bf["min"].reindex(cells.block)
        assert cell_fold.notna().all(), "a cell's block holds no eligible house pixel"
        self.fold = cell_fold.to_numpy(np.int64)[cell]
        self.block = cells.block[cell]
        self.mb = RR.metric_set(self.y, RR.scores(self.X, self.y, self.fold), self.rs)
        self.mv = RR.metric_set(self.y, RR.scores(np.column_stack([self.X, self.u]), self.y, self.fold), self.rs)
        self.observed = {k: self.mv[k] - self.mb[k] for k in METRICS}
        self.n_ctl = n_ctl

    def describe(self):
        years = pd.DatetimeIndex(self.cases.date).year
        return dict(events_in_file=self.events_in_file, events_logged=self.events_logged, cases=int(len(self.cases)),
                    dropped=self.dropped, rows=int(len(self.y)),
                    controls_per_set=dict(min=int(self.n_ctl.min()), median=float(np.median(self.n_ctl)),
                                          max=int(self.n_ctl.max())),
                    cases_by_year={str(k): int(v) for k, v in pd.Series(years).value_counts().sort_index().items()},
                    cases_per_fold=[int(self.y[self.fold == k].sum()) for k in range(5)],
                    cells_in_rows=int(len(np.unique(self.cell))), blocks_with_rows=int(len(np.unique(self.block))),
                    baseline=self.mb, with_indicator=self.mv, observed=self.observed)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in ("features", "grid", "episodes", "censoring", "events", "cells", "nyc-cells", "surrogates", "quantiles", "out"):
        p.add_argument(f"--{k}", dest=k.replace("-", "_"), type=Path, required=True)
    p.add_argument("--mode", choices=("decoy", "real"), required=True)
    p.add_argument("--workers", type=int, required=True)
    p.add_argument("--draws", type=int, default=None, help="default: all stored draws; fewer only for checks")
    p.add_argument("--boot", type=int, default=RR.N_BOOT)
    a = p.parse_args(argv)
    if a.mode == "real":
        assert a.draws is None and a.boot == RR.N_BOOT, "the real run uses the plan's counts"
    t0 = time.perf_counter()
    started = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    inputs, h, house, date, key, t_ep, holds = RT.load(a, a.mode)
    cells = SC.Cells(h, a.grid, a.cells, a.nyc_cells)
    fp = cells.fingerprint(cells.value[:, cells.null_cells])
    store = C.SurrogateStore(a.surrogates, fp, check_hash=True)
    qmeta = json.loads(Path(str(a.quantiles) + ".json").read_text())
    assert qmeta["surrogates_sha256"] == store.meta["sha256"] and qmeta["sha256"] == C.sha256(a.quantiles)
    qS = np.load(a.quantiles)
    assert qS.shape == (store.draws, len(C.QS), len(C.MONTHS))
    A = CellAnalysis(cells, h, house, date, key, holds, a.mode)
    draws = store.draws if a.draws is None else a.draws
    R = dict(label=RT.LABEL[a.mode], secondary="1_nyc_design", mode=a.mode, **A.describe())
    t = time.perf_counter()
    null = RR.null_metrics(A, store, qS, draws, a.workers)
    R["null"] = dict(draws=int(draws), **{f"{k}_p": C.p_value(A.observed[k], null[k]) for k in METRICS},
                     **{f"{k}_null_median": float(np.median(null[k])) for k in METRICS},
                     statistics={k: v.tolist() for k, v in null.items()}, seconds=time.perf_counter() - t)
    t = time.perf_counter()
    boot = RR.joint_bootstrap([A], a.boot, a.workers)
    R["bootstrap"] = dict(boot, **boot["per_analysis"][A.name])
    R["bootstrap_seconds"] = time.perf_counter() - t
    R["inputs"] = dict(checkpoint1=inputs, events=C.sha256(a.events), cells=C.sha256(a.cells),
                       nyc_cells=C.sha256(a.nyc_cells), null_fingerprint=fp, surrogates=store.meta["sha256"],
                       quantiles=qmeta["sha256"])
    R.update(workers=a.workers, started=started, elapsed_seconds=time.perf_counter() - t0, sources=source_hashes(),
             host=platform.node(), python=platform.python_version(), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "result.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
    s = {k: R[k] for k in ("label", "secondary", "mode", "cases", "rows", "dropped", "controls_per_set", "observed")}
    s["p"] = {k: R["null"][f"{k}_p"] for k in METRICS}
    s["ci95"] = {k: R["bootstrap"][f"{k}_ci95"] for k in BOOT_METRICS}
    s["seconds"] = dict(null=R["null"]["seconds"], bootstrap=R["bootstrap_seconds"], total=R["elapsed_seconds"])
    print(json.dumps(s, indent=1, default=str))


if __name__ == "__main__":
    main()
