"""The 999 conditional-null surrogate fields of Test A (AUSTIN_PLAN.md §10), written in the format of
planted_signal/testa_core.py (write_surrogates; read by SurrogateStore).

Frozen settings: ConditionalVariogramNull (conditional_null.py) on the null field, neighbour cap 1,000,
max lag 16, chunk 8, 999 draws, seed 2027 (default_rng, as NYC). Nothing here changes them.

Backends (§14, 2026-11-10: all heavy runs on the processing server):
  cpu  calibration/cpu_null.CPULowMemVariogramNull (NumPy/SciPy allocation of the unchanged LowMemVariogramNull;
       equal to the GPU class within 2.4e-14 with identical k in the calibration's unit check), draws run in
       parallel by production/parallel_draws.py, which yields them in draw order with identical arithmetic.
  gpu  the frozen default, LowMemVariogramNull on CuPy, sequential.
Thread counts are fixed at 1 (OMP, OpenBLAS, MKL), so the per-window gradient-boosting fits and every draw
use the same arithmetic on every run.

Usage (from the repository root):
  python -I feasibility/austin/production/make_surrogates.py --features ... --grid ... --episodes ...
      --censoring ... --field FIELD.npz --out surrogates_conditional.npy --backend cpu --workers 32
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
from conditional_null import ConditionalVariogramNull  # noqa: E402
from cpu_null import CPULowMemVariogramNull  # noqa: E402


def source_hashes():
    files = [HERE / "make_surrogates.py", HERE / "parallel_draws.py", PS_DIR / "testa_core.py",
             PS_DIR / "planted_signal.py", C.FROZEN / "nyc_lib.py", C.FROZEN / "lowmem_null.py",
             C.FROZEN / "conditional_null.py", C.FROZEN / "calibration" / "cpu_null.py"]
    return {str(p.relative_to(HERE.parent)): C.sha256(p) for p in files}


def build_engine(v_null, geo, cov, backend, settings):
    factory = CPULowMemVariogramNull if backend == "cpu" else None
    return ConditionalVariogramNull(v_null, geo.null_xy(), C.PIXEL_M, cov, feature_names=C.NULL_COVARIATES,
                                    null_factory=factory, **settings)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in ("features", "grid", "episodes", "censoring", "field", "out"):
        p.add_argument(f"--{k}", type=Path, required=True)
    p.add_argument("--backend", choices=("cpu", "gpu"), required=True)
    p.add_argument("--workers", type=int, default=1, help="parallel draws (cpu backend)")
    p.add_argument("--draws", type=int, default=C.NULL_DRAWS, help="999 (frozen); fewer only for checks")
    a = p.parse_args(argv)
    t0 = time.perf_counter()
    inputs = PS.checkpoint1_inputs(a)
    h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
    geo = C.Geometry(h)
    v_null = C.load_field(a.field, geo)[:, geo.null_pixels]
    fp = C.null_fingerprint(v_null, geo)
    cov = C.null_covariates(h, geo)
    engine = build_engine(v_null, geo, cov, a.backend, C.NULL_SETTINGS)
    setup = time.perf_counter() - t0
    runner = ParallelDraws(engine, a.workers) if a.backend == "cpu" and a.workers > 1 else engine
    t1 = time.perf_counter()
    meta = C.write_surrogates(a.out, runner, a.draws, C.NULL_SEED, fp, v_null.shape)
    info = dict(backend=a.backend, workers=a.workers, draws=a.draws, seed=C.NULL_SEED, settings=C.NULL_SETTINGS,
                field_sha256=C.sha256(a.field), fingerprint=fp, inputs=inputs, surrogates_sha256=meta["sha256"],
                chosen_k=meta["chosen_k"], explained_variance=[float(x) for x in engine.explained_variance],
                setup_seconds=setup, draw_seconds=time.perf_counter() - t1,
                peak_rss_gb_parent=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6,
                peak_rss_gb_largest_worker=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1e6,
                host=platform.node(), python=platform.python_version(), numpy=np.__version__,
                sources=source_hashes(), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    Path(str(a.out) + ".run.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps({k: v for k, v in info.items() if k != "chosen_k"}, indent=1))


if __name__ == "__main__":
    main()
