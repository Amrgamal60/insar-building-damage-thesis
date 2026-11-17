"""The 999 surrogate fields of null (a), the NYC variogram null, for secondary 8 of Test A (AUSTIN_PLAN.md §10
"Secondary: the NYC null itself (variogram surrogates of the whole velocity field) is reported beside it with the
same draws and seed (§12 item 8)"; §12 item 8; §15 timing-gate setting: "neighbour cap 1,000 and 999 draws for both
Test A nulls ... with seed 2027").

Same as make_surrogates.py except for the engine: the variogram-matching generator is applied to the whole velocity
field on the null field's pixels, with no conditional fit (ConditionalVariogramNull is the primary null (b); this
is null (a) of the §10 calibration). Engine: calibration/cpu_null.CPULowMemVariogramNull, the class that
ConditionalVariogramNull wraps on the cpu backend, with the frozen settings (cap 1,000, max lag 16, chunk 8), seed
2027 (default_rng), 999 draws; draws in parallel by production/parallel_draws.py in draw order (identical
arithmetic). Output in the format of testa_core.write_surrogates, so SurrogateStore and the quantiles command read it
unchanged. Written on 2026-11-12, after the decoy run and before the real run; it reads no outcome.

Usage: python -I make_surrogates_nulla.py --features ... --grid ... --episodes ... --censoring ... --field FIELD.npz
           --out surrogates_nulla.npy --workers 64 [--draws N (checks only)]
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import resource  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
PS_DIR = HERE.parent / "planted_signal"
sys.path[:0] = [str(HERE), str(PS_DIR)]
import testa_core as C  # noqa: E402
import planted_signal as PS  # noqa: E402  (checkpoint-1 input hash check)
from parallel_draws import ParallelDraws  # noqa: E402

sys.path.insert(0, str(C.FROZEN / "calibration"))
from cpu_null import CPULowMemVariogramNull  # noqa: E402


def source_hashes():
    files = [HERE / "make_surrogates_nulla.py", HERE / "parallel_draws.py", PS_DIR / "testa_core.py",
             PS_DIR / "planted_signal.py", C.FROZEN / "nyc_lib.py", C.FROZEN / "lowmem_null.py",
             C.FROZEN / "calibration" / "cpu_null.py"]
    return {str(p.relative_to(HERE.parent)): C.sha256(p) for p in files}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in ("features", "grid", "episodes", "censoring", "field", "out"):
        p.add_argument(f"--{k}", type=Path, required=True)
    p.add_argument("--workers", type=int, required=True)
    p.add_argument("--draws", type=int, default=C.NULL_DRAWS, help="999 (frozen); fewer only for checks")
    a = p.parse_args(argv)
    t0 = time.perf_counter()
    inputs = PS.checkpoint1_inputs(a)
    h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
    geo = C.Geometry(h)
    v_null = C.load_field(a.field, geo)[:, geo.null_pixels]
    fp = C.null_fingerprint(v_null, geo)
    engine = CPULowMemVariogramNull(v_null, geo.null_xy(), C.PIXEL_M, **C.NULL_SETTINGS)
    setup = time.perf_counter() - t0
    runner = ParallelDraws(engine, a.workers) if a.workers > 1 else engine
    t1 = time.perf_counter()
    meta = C.write_surrogates(a.out, runner, a.draws, C.NULL_SEED, fp, v_null.shape)
    info = dict(null="(a) NYC variogram null, whole field (secondary 8)", backend="cpu", workers=a.workers,
                draws=a.draws, seed=C.NULL_SEED, settings=C.NULL_SETTINGS, field_sha256=C.sha256(a.field),
                fingerprint=fp, inputs=inputs, surrogates_sha256=meta["sha256"], chosen_k=meta["chosen_k"],
                setup_seconds=setup, draw_seconds=time.perf_counter() - t1,
                peak_rss_gb_parent=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6,
                peak_rss_gb_largest_worker=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1e6,
                host=platform.node(), python=platform.python_version(), numpy=np.__version__,
                sources=source_hashes(), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    Path(str(a.out) + ".run.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps({k: v for k, v in info.items() if k != "chosen_k"}, indent=1))


if __name__ == "__main__":
    main()
