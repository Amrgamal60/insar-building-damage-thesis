"""Test B null surrogates for secondary 19, monthly counts (AUSTIN_PLAN.md §12 item 19; §10 Test B null; §15, 2026-11-15).

As make_testb_surrogates.py (unchanged engine, settings and seed), with the monthly field in place of a quarterly one:
  - field: v_monthly of i12_testb_cells.py, the cell's velocity for the 12 months before each study month
    (88 months, 2018-08 .. 2025-11), on the cells with a value in at least one month;
  - engine: calibration/cpu_null.CPULowMemVariogramNull at 250 m, neighbour cap 1,000, max lag 16, chunk 8; all months
    share one permutation, one neighbour count and one noise vector per draw, as the quarters do in the Test B null;
  - seed 2034 (the Test B null of §10), default_rng, 999 draws; parallel draws by production/parallel_draws.py.
Outcome-blind: reads only the cell field.
Writes OUT (.npz in the format test_b.null_test reads: fields[draw, month, cell], quarters = the month labels, which are
the labelled time axis, cells; plus months, k, seed, field_name) and OUT.run.json.
Usage: python -I make_testb_monthly_surrogates.py CELLS_NPZ OUT [--workers N] [--draws 999]
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_testb_surrogates as MT  # noqa: E402  (unchanged: engine, settings, paths)
from make_testb_surrogates import C, ParallelDraws, CPULowMemVariogramNull  # noqa: E402

FIELD, SEED = "v_monthly", 2034


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cells", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--draws", type=int, default=MT.DRAWS, help="999 (frozen); fewer only for checks")
    a = p.parse_args(argv)
    assert not a.out.exists()
    t0 = time.perf_counter()
    with np.load(a.cells, allow_pickle=False) as z:
        field, cells, xy, months = z[FIELD].astype(np.float64), z["cells"], z["xy"], z["months"]
    assert list(months) == C.MONTHS and field.shape == (len(C.MONTHS), len(cells))
    use = np.isfinite(field).any(0)
    f_null, c_null, xy_null = field[:, use], cells[use], xy[use]
    windows_with_values = np.isfinite(f_null).any(1)
    engine = CPULowMemVariogramNull(f_null, xy_null, MT.RES, **MT.SETTINGS)
    setup = time.perf_counter() - t0
    runner = ParallelDraws(engine, a.workers) if a.workers > 1 else engine
    t1 = time.perf_counter()
    S = np.empty((a.draws,) + f_null.shape, np.float64)
    ks = np.empty(a.draws, np.int64)
    for d, (s, k) in enumerate(runner.draws(a.draws, np.random.default_rng(SEED))):
        assert s.shape == f_null.shape
        S[d], ks[d] = s, k
    assert d == a.draws - 1
    assert np.array_equal(np.isfinite(S), np.broadcast_to(np.isfinite(f_null), S.shape))  # missing pattern kept
    with open(a.out, "wb") as fh:
        np.savez(fh, fields=S, quarters=months, months=months, cells=c_null, k=ks, seed=np.int64(SEED),
                 field_name=np.array(FIELD))
    info = dict(field=FIELD, seed=SEED, draws=a.draws, workers=a.workers, res=MT.RES, settings=MT.SETTINGS,
                cells_npz_sha256=MT.sha256(a.cells), cells_in_null=int(use.sum()), cells_total=int(len(cells)),
                months=len(months), months_with_values=int(windows_with_values.sum()),
                first_month_with_values=str(months[int(np.argmax(windows_with_values))]),
                field_sha256=hashlib.sha256(np.ascontiguousarray(f_null).tobytes()).hexdigest(),
                surrogates_sha256=MT.sha256(a.out), k_median=float(np.median(ks)), k_offered=[int(x) for x in engine.ks],
                setup_seconds=setup, draw_seconds=time.perf_counter() - t1, host=platform.node(),
                python=platform.python_version(), numpy=np.__version__,
                sources={str(q.relative_to(HERE.parent)): MT.sha256(q) for q in
                         (HERE / "make_testb_monthly_surrogates.py", HERE / "make_testb_surrogates.py",
                          HERE / "parallel_draws.py", C.FROZEN / "nyc_lib.py", C.FROZEN / "lowmem_null.py",
                          C.FROZEN / "calibration" / "cpu_null.py")},
                finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    Path(str(a.out) + ".run.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
