"""Check of production/parallel_draws.py and make_surrogates.py on a synthetic field only (no InSAR file).

Uses the synthetic velocity field of the planted-signal check (planted_signal/check, step 3) on the real
pixel grid, with the real checkpoint-1 houses and features for the conditional fit.

 1. Cross-machine and parallel equality at the planted-signal check's setting (neighbour cap 200): the first
    draws, made in parallel on this machine, against the same draws made sequentially on the project PC and
    stored by the planted-signal check (--reference).
 2. Parallel equality at the frozen setting (cap 1,000): the same draws made sequentially and in parallel on
    this machine, through testa_core.write_surrogates, must give byte-identical files and the same k.
 3. Throughput at the frozen setting with --workers parallel draws, and the projection for 999 draws.
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import platform  # noqa: E402
import resource  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I leaves the script's folder out
import make_surrogates as M  # noqa: E402  (sets the other import paths)
from make_surrogates import C, PS, ParallelDraws  # noqa: E402

p = argparse.ArgumentParser()
for k in ("features", "grid", "episodes", "censoring", "field", "reference", "work", "out"):
    p.add_argument(f"--{k}", type=Path, required=True)
p.add_argument("--equal-draws", type=int, default=3)
p.add_argument("--workers", type=int, default=32)
p.add_argument("--throughput-draws", type=int, default=64)
a = p.parse_args()
a.work.mkdir(parents=True, exist_ok=True)
a.out.parent.mkdir(parents=True, exist_ok=True)
T0 = time.perf_counter()
R = dict(sources=M.source_hashes(), check_sha256=C.sha256(Path(__file__)), host=platform.node(),
         cpus=os.cpu_count(), field_sha256=C.sha256(a.field))


def note(msg):
    print(f"[{time.perf_counter() - T0:8.1f} s] {msg}", flush=True)


def save():
    a.out.write_text(json.dumps(R, indent=1, default=float) + "\n")


def same_bytes(x, y):
    """Byte equality of two stored draws. np.array_equal would call two NaN cells unequal, and the null field has
    NaN pixels (no value), so it cannot show byte identity here."""
    return np.ascontiguousarray(x).tobytes() == np.ascontiguousarray(y).tobytes()


inputs = PS.checkpoint1_inputs(a)
h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
geo = C.Geometry(h)
v_null = C.load_field(a.field, geo)[:, geo.null_pixels]
fp = C.null_fingerprint(v_null, geo)
cov = C.null_covariates(h, geo)
D = a.equal_draws

# ---------------------------------------------------------------- 1. against the PC's sequential draws (cap 200)
ref = C.SurrogateStore(a.reference, fp, check_hash=True)
t = time.perf_counter()
engine = M.build_engine(v_null, geo, cov, "cpu", dict(C.NULL_SETTINGS, kmax=200))
setup = time.perf_counter() - t
t = time.perf_counter()
meta = C.write_surrogates(a.work / "cap200_parallel.npy", ParallelDraws(engine, D), D, C.NULL_SEED, fp, v_null.shape)
S = np.load(a.work / "cap200_parallel.npy", mmap_mode="r")
diff = max(float(np.nanmax(np.abs(S[d].astype(np.float64) - ref.S[d].astype(np.float64)))) for d in range(D))
R["1_cap200_vs_pc"] = dict(draws=D, reference_sha256=ref.meta["sha256"], setup_seconds=setup,
                           parallel_seconds=time.perf_counter() - t,
                           bytes_identical=bool(all(same_bytes(S[d], ref.S[d]) for d in range(D))),
                           nan_identical=bool(all(np.array_equal(np.isnan(S[d]), np.isnan(ref.S[d])) for d in range(D))),
                           max_abs_diff_mm_yr=diff, k_identical=meta["chosen_k"] == ref.meta["chosen_k"][:D])
del S, engine
save()
assert R["1_cap200_vs_pc"]["nan_identical"] and R["1_cap200_vs_pc"]["k_identical"]
assert R["1_cap200_vs_pc"]["max_abs_diff_mm_yr"] < 1e-5  # float32 storage: at most a last-digit difference
note(f"1 cap 200, parallel here vs sequential on the PC: {R['1_cap200_vs_pc']}")
save()

# ---------------------------------------------------------------- 2. sequential vs parallel here (frozen cap 1,000)
t = time.perf_counter()
engine = M.build_engine(v_null, geo, cov, "cpu", C.NULL_SETTINGS)
setup = time.perf_counter() - t
t = time.perf_counter()
m_seq = C.write_surrogates(a.work / "cap1000_sequential.npy", engine, D, C.NULL_SEED, fp, v_null.shape)
seq_seconds = time.perf_counter() - t
t = time.perf_counter()
m_par = C.write_surrogates(a.work / "cap1000_parallel.npy", ParallelDraws(engine, D), D, C.NULL_SEED, fp, v_null.shape)
R["2_cap1000_equal"] = dict(draws=D, setup_seconds=setup, sequential_seconds_per_draw=seq_seconds / D,
                            parallel_seconds=time.perf_counter() - t,
                            sequential_sha256=m_seq["sha256"], parallel_sha256=m_par["sha256"],
                            files_identical=m_seq["sha256"] == m_par["sha256"],
                            k_identical=m_seq["chosen_k"] == m_par["chosen_k"], chosen_k=m_seq["chosen_k"],
                            explained_variance_mean=float(np.mean(engine.explained_variance)))
save()
assert R["2_cap1000_equal"]["files_identical"] and R["2_cap1000_equal"]["k_identical"]
note(f"2 cap 1,000, sequential vs parallel here: {R['2_cap1000_equal']}")
save()

# ---------------------------------------------------------------- 3. throughput at the frozen setting
n = a.throughput_draws
t = time.perf_counter()
m_thr = C.write_surrogates(a.work / "cap1000_throughput.npy", ParallelDraws(engine, a.workers), n, C.NULL_SEED, fp, v_null.shape)
wall = time.perf_counter() - t
S = np.load(a.work / "cap1000_throughput.npy", mmap_mode="r")
seq = np.load(a.work / "cap1000_sequential.npy", mmap_mode="r")
prefix_equal = bool(all(same_bytes(S[d], seq[d]) for d in range(D)))
R["3_throughput"] = dict(workers=a.workers, draws=n, wall_seconds=wall, seconds_per_draw_effective=wall / n,
                         projected_hours_999=wall / n * C.NULL_DRAWS / 3600,
                         projected_hours_999_by_rounds=math.ceil(C.NULL_DRAWS / a.workers) * wall / math.ceil(n / a.workers) / 3600,
                         first_draws_equal_sequential=prefix_equal,
                         peak_rss_gb_parent=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6,
                         peak_rss_gb_largest_worker=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1e6)
save()
assert prefix_equal
note(f"3 throughput: {R['3_throughput']}")
R["all_passed"] = True
R["seconds"] = time.perf_counter() - T0
save()
for f in ("cap200_parallel.npy", "cap1000_throughput.npy"):
    (a.work / f).unlink()
