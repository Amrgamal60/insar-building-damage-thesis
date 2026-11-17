"""Test B variogram-null surrogates (AUSTIN_PLAN.md §10 Test B; §4 remodel specificity check; §14 compute location).

Field: a quarters x cells field of i12_testb_cells.py (primary: v), on the cells with a value in at least one quarter.
That is the field of all cells used in Test B, as NYC's null field (cells with a value in any window). No outcome
or exposure enters: cells are not filtered by n > 0 or by events.
Engine: the NYC implementation as the frozen GPU class's CPU equivalent, calibration/cpu_null.CPULowMemVariogramNull
(§14 2026-11-10 surrogate backend), at 250 m: neighbour cap 1,000, max lag 16, chunk 8. The calibration checked it
against the NYC GPU class on Test B panels (gpu_execution.run_b_gpu: same k, difference at most 1e-11). All quarters
share one permutation, one neighbour count and one noise vector per draw.
Seeds (§10, §14): 2034 for Test B, 2035 for the remodel Test B; default_rng(seed), as NYC. 999 draws.
Draws in parallel with production/parallel_draws.py when --workers > 1 (identical arithmetic, draw order kept).
Thread counts are fixed at 1.
Writes OUT (.npz, the format test_b.py --surrogates reads: fields[draw, quarter, cell], quarters, cells; plus k, seed)
and OUT.run.json.
Usage: .venv/bin/python -I make_testb_surrogates.py CELLS_NPZ OUT --field v --seed 2034 [--workers N] [--draws 999]
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
PS_DIR = HERE.parent / "planted_signal"
sys.path[:0] = [str(HERE), str(PS_DIR)]
import testa_core as C  # noqa: E402  (puts the frozen scripts on the path)
from parallel_draws import ParallelDraws  # noqa: E402

sys.path.insert(0, str(C.FROZEN / "calibration"))
from cpu_null import CPULowMemVariogramNull  # noqa: E402

RES, SETTINGS, DRAWS = 250.0, dict(kmax=1000, max_lag=16, chunk=8), 999


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cells", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--field", default="v")
    p.add_argument("--seed", type=int, required=True, choices=(2034, 2035))
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--draws", type=int, default=DRAWS, help="999 (frozen); fewer only for checks")
    a = p.parse_args(argv)
    assert not a.out.exists()
    t0 = time.perf_counter()
    with np.load(a.cells, allow_pickle=False) as z:
        field, cells, xy, quarters = z[a.field].astype(np.float64), z["cells"], z["xy"], z["quarters"]
    assert field.shape == (len(quarters), len(cells)) == (28, len(cells))
    use = np.isfinite(field).any(0)
    f_null, c_null, xy_null = field[:, use], cells[use], xy[use]
    engine = CPULowMemVariogramNull(f_null, xy_null, RES, **SETTINGS)
    setup = time.perf_counter() - t0
    runner = ParallelDraws(engine, a.workers) if a.workers > 1 else engine
    t1 = time.perf_counter()
    S = np.empty((a.draws,) + f_null.shape, np.float64)
    ks = np.empty(a.draws, np.int64)
    for d, (s, k) in enumerate(runner.draws(a.draws, np.random.default_rng(a.seed))):
        assert s.shape == f_null.shape
        S[d], ks[d] = s, k
    assert d == a.draws - 1
    assert np.array_equal(np.isfinite(S), np.broadcast_to(np.isfinite(f_null), S.shape))  # missing pattern kept
    with open(a.out, "wb") as fh:
        np.savez(fh, fields=S, quarters=quarters, cells=c_null, k=ks, seed=np.int64(a.seed), field_name=np.array(a.field))
    info = dict(field=a.field, seed=a.seed, draws=a.draws, workers=a.workers, res=RES, settings=SETTINGS,
                cells_npz_sha256=sha256(a.cells), cells_in_null=int(use.sum()), cells_total=int(len(cells)),
                field_sha256=hashlib.sha256(np.ascontiguousarray(f_null).tobytes()).hexdigest(),
                surrogates_sha256=sha256(a.out), k_median=float(np.median(ks)), k_offered=[int(x) for x in engine.ks],
                setup_seconds=setup, draw_seconds=time.perf_counter() - t1, host=platform.node(),
                python=platform.python_version(), numpy=np.__version__,
                sources={str(q.relative_to(HERE.parent)): sha256(q) for q in
                         (HERE / "make_testb_surrogates.py", HERE / "parallel_draws.py", C.FROZEN / "nyc_lib.py",
                          C.FROZEN / "lowmem_null.py", C.FROZEN / "calibration" / "cpu_null.py")},
                finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    Path(str(a.out) + ".run.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
