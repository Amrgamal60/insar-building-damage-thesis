"""Secondary 1, NYC design: the cell data and the cell-level conditional null (AUSTIN_PLAN.md §12 item 1; §10 Test A null;
§15, 2026-11-15). Outcome-blind: no event, holds_event, fold or episode date is read here (load_houses reads the
checkpoint-1 episode and demolition tables only because its signature needs them; nothing here uses those columns).

Cells (§12.1 "250 m cells"): the 5,645 UTM 14N 250 m cells holding an eligible parcel point (i12_testb_cells.py, its
order). A house's cell is cell250 of the checkpoint-1 grid table.
Cell value (§12.1 "the mean of valid pixels"): i08's NYC-design cell mean of the 24-month window of each study month
(nyc_cells_L24.npz of the corrected run: the mean velocity of the valid pixels whose centre lies in the cell), and no
value where the cell has no valid pixel.
Cell baseline (Baseline 1 at cell level, as NYC's cell rows carry cell means of building features), authors' choice:
  - means over the cell's eligible houses with complete Baseline 1 inputs of year built (building age at a row's date =
    decimal year of the date minus the mean year built, i.e. the mean age) and of the seven static features of
    testa_core.STATIC, plus the cell centre x/y in km (NYC's cell coordinates);
  - a cell with no such house has no baseline (NYC's base_ok) and enters no risk set.
Null field (§10 as for the primary): the cells with a baseline. Covariates: the cell means above, with age at
2018-08-01 (testa_core.NULL_COVARIATES order), no coordinates.
Null: ConditionalVariogramNull (frozen conditional_null.py) at 250 m with the §10 settings (neighbour cap 1,000, max lag
16, chunk 8), CPU engine of §14 (calibration/cpu_null.CPULowMemVariogramNull) through production/parallel_draws.py,
seed 2027, 999 draws. Written with testa_core.write_surrogates under the fingerprint of the cell null field.
Quantiles per draw (§7 as the primary): testa_core.window_quantiles over the null cells with a value in the window, each
cell once; the observed field is standardised over all cells with a value (secondary_cells.py).

Usage: python -I secondary_cells_null.py COMMON --cells CELLS_NPZ --nyc-cells NYC_CELLS_NPZ --out DIR --workers N [--draws n]
  COMMON = --features --grid --episodes --censoring (checkpoint-1 tables, hash-checked)
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
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
import planted_signal as PS  # noqa: E402  (checkpoint-1 input hash check)
from parallel_draws import ParallelDraws  # noqa: E402

sys.path.insert(0, str(C.FROZEN / "calibration"))
from conditional_null import ConditionalVariogramNull  # noqa: E402
from cpu_null import CPULowMemVariogramNull  # noqa: E402

RES = 250.0


class Cells:
    """The cell design's outcome-free data. Arrays over cells are in i12 order."""

    def __init__(self, h, grid, cells_npz, nyc_cells_npz):
        g = pd.read_parquet(grid, columns=["prop_id", "cell250"])
        assert (g.prop_id.to_numpy() == h.prop_id.to_numpy()).all()
        with np.load(cells_npz, allow_pickle=False) as z:
            self.labels, self.xy, self.block = z["cells"], z["xy"].astype(np.float64), z["block"].astype(str)
            cell_x, cell_y = z["cell_x"], z["cell_y"]
        with np.load(nyc_cells_npz, allow_pickle=False) as z:
            assert list(z["months"]) == C.MONTHS
            assert np.array_equal(z["cell_x"], cell_x) and np.array_equal(z["cell_y"], cell_y), "cell order differs"
            mean, count = z["mean"].astype(np.float64), z["count"]
        self.house_cell = pd.Index(self.labels).get_indexer(g.cell250.to_numpy())
        assert (self.house_cell >= 0).all()
        NC = len(self.labels)
        assert mean.shape == count.shape == (len(C.MONTHS), NC)
        self.value = np.where(count > 0, mean, np.nan)
        assert np.isfinite(self.value[count > 0]).all()
        self.HV = np.isfinite(self.value)
        c = h.complete_b1.to_numpy(bool)
        hc = self.house_cell[c]
        self.n_complete = np.bincount(hc, minlength=NC)
        self.base_ok = self.n_complete > 0
        cols = ["year_built"] + C.STATIC
        X = h.loc[c, cols].to_numpy(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            M = np.column_stack([np.bincount(hc, weights=X[:, k], minlength=NC) for k in range(X.shape[1])]) / self.n_complete[:, None]
        self.mean_year_built = M[:, 0]
        self.static = M[:, 1:]
        self.x_km, self.y_km = self.xy[:, 0] / 1000.0, self.xy[:, 1] / 1000.0
        assert np.isfinite(M[self.base_ok]).all() and not np.isfinite(M[~self.base_ok]).any()
        self.null_cells = np.flatnonzero(self.base_ok)

    def design(self, cell, date):
        """Cell Baseline 1 + x/y at rows (cell, risk-set date), in testa_core.B1 order."""
        age = C.decimal_year(date) - self.mean_year_built[cell]
        X = np.column_stack([age, self.static[cell], self.x_km[cell], self.y_km[cell]])
        assert np.isfinite(X).all()
        return X

    def null_covariates(self):
        n = self.null_cells
        return np.column_stack([C.decimal_year(C.START)[0] - self.mean_year_built[n], self.static[n]])

    def fingerprint(self, v_null):
        f = hashlib.sha256(np.ascontiguousarray(v_null, np.float64).tobytes())
        f.update("|".join(C.MONTHS).encode())
        f.update("|".join(self.labels[self.null_cells].astype(str)).encode())
        return f.hexdigest()


def source_hashes():
    files = [HERE / "secondary_cells_null.py", HERE / "parallel_draws.py", PS_DIR / "testa_core.py", PS_DIR / "planted_signal.py",
             C.FROZEN / "nyc_lib.py", C.FROZEN / "lowmem_null.py", C.FROZEN / "conditional_null.py",
             C.FROZEN / "calibration" / "cpu_null.py"]
    return {str(p.relative_to(HERE.parent)): C.sha256(p) for p in files}


def load(a):
    inputs = PS.checkpoint1_inputs(a)
    h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
    return inputs, h, Cells(h, a.grid, a.cells, a.nyc_cells)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in ("features", "grid", "episodes", "censoring", "cells", "nyc-cells", "out"):
        p.add_argument(f"--{k}", dest=k.replace("-", "_"), type=Path, required=True)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--draws", type=int, default=C.NULL_DRAWS, help="999 (frozen); fewer only for checks")
    a = p.parse_args(argv)
    t0 = time.perf_counter()
    inputs, h, cells = load(a)
    v_null = cells.value[:, cells.null_cells]
    fp = cells.fingerprint(v_null)
    cov = cells.null_covariates()
    engine = ConditionalVariogramNull(v_null, cells.xy[cells.null_cells], RES, cov, feature_names=C.NULL_COVARIATES,
                                      null_factory=CPULowMemVariogramNull, **C.NULL_SETTINGS)
    setup = time.perf_counter() - t0
    runner = ParallelDraws(engine, a.workers) if a.workers > 1 else engine
    a.out.mkdir(parents=True, exist_ok=False)
    t1 = time.perf_counter()
    meta = C.write_surrogates(a.out / "surrogates_cells.npy", runner, a.draws, C.NULL_SEED, fp, v_null.shape)
    draw_seconds = time.perf_counter() - t1
    S = np.load(a.out / "surrogates_cells.npy", mmap_mode="r")
    q = np.stack([C.window_quantiles(np.asarray(S[d], dtype=np.float64)) for d in range(S.shape[0])])
    np.save(a.out / "quantiles_cells.npy", q)
    qmeta = dict(sha256=C.sha256(a.out / "quantiles_cells.npy"), surrogates_sha256=meta["sha256"], fingerprint=fp,
                 shape=list(q.shape), percentiles=C.QS, standardisation_set="null cells with a value, each once")
    (a.out / "quantiles_cells.npy.json").write_text(json.dumps(qmeta, indent=1) + "\n")
    info = dict(draws=a.draws, workers=a.workers, seed=C.NULL_SEED, res=RES, settings=C.NULL_SETTINGS, fingerprint=fp,
                inputs=dict(checkpoint1=inputs, cells=C.sha256(a.cells), nyc_cells=C.sha256(a.nyc_cells)),
                cells=int(len(cells.labels)), cells_with_baseline=int(cells.base_ok.sum()),
                cells_with_a_value_by_window=[int(x) for x in cells.HV.sum(1)],
                null_cells_with_a_value_by_window=[int(x) for x in np.isfinite(v_null).sum(1)],
                surrogates_sha256=meta["sha256"], quantiles_sha256=qmeta["sha256"], chosen_k=meta["chosen_k"],
                explained_variance=[float(x) for x in engine.explained_variance],
                setup_seconds=setup, draw_seconds=draw_seconds, host=platform.node(), python=platform.python_version(),
                numpy=np.__version__, sources=source_hashes(), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    (a.out / "surrogates_cells.npy.run.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps({k: v for k, v in info.items() if k not in ("chosen_k", "cells_with_a_value_by_window",
                                                                  "null_cells_with_a_value_by_window")}, indent=1))


if __name__ == "__main__":
    main()
