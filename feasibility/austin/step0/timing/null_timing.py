"""Austin plan step 0 (§10 gate): timing test of the NYC variogram-matching null on a synthetic field.

No InSAR value and no outcome is read. Inputs: unique 30 m cell centres (EPSG:32614) of the diagnostic parcel
population, as an .npy (n, 2) array. Fields are synthetic: one smooth random field plus per-window noise, with a
random 10% of cells missing per window. The null's cost does not depend on the values (every draw evaluates all
15 neighbour counts), so only n, the cell layout, the window count and the neighbour cap matter.

  --plan   CPU only: pair and neighbour counts and the GPU memory they imply. No GPU needed.
  default  build nyc_lib.VariogramNull on the GPU, time construction and --draws draws, project 999 draws.
"""
import argparse
import json
import sys
import time

import numpy as np
from scipy.spatial import cKDTree

ap = argparse.ArgumentParser()
ap.add_argument("xy")
ap.add_argument("--windows", type=int, default=88)
ap.add_argument("--kmax", type=int, default=1000)
ap.add_argument("--draws", type=int, default=5)
ap.add_argument("--res", type=float, default=30.0)
ap.add_argument("--plan", action="store_true")
ap.add_argument("--nyc-lib", default="/mnt/data/Master-projects/Alex/feasibility/nyc/scripts")
ap.add_argument("--out", default=None)
ap.add_argument("--lowmem", type=int, default=0, help="window chunk for LowMemVariogramNull; 0 = NYC class")
a = ap.parse_args()

xy = np.load(a.xy).astype(float)
n, W = len(xy), a.windows
ks = np.unique(np.geomspace(2, min(0.9 * n, a.kmax), 15).astype(int))
rep = {"n_cells": n, "windows": W, "kmax": a.kmax, "ks": ks.tolist()}

t = time.time()
tree = cKDTree(xy)
pairs = tree.query_pairs(r=(16 + 0.5) * a.res, output_type="ndarray")
lag = np.rint(np.hypot(*(xy[pairs[:, 0]] - xy[pairs[:, 1]]).T) / a.res).astype(int)
P = int(((lag >= 1) & (lag <= 16)).sum())
del pairs, lag
nnz = int(n * (ks + 1).sum())
rep.update(variogram_pairs=P, smoothing_nnz=nnz, pair_seconds=round(time.time() - t, 1))
gb = 1e9
rep["gpu_gb_estimate"] = {
    "W_k (csr float64 + int32 idx)": round(nnz * 12 / gb, 2),
    "vp (W x P float64, as nyc_lib)": round(W * P * 8 / gb, 2),
    "pair index gi, gj, H (int64/float64)": round(P * (8 + 8 + 20) / gb, 2),
    "z, x0, xs (W x n float64, x3)": round(3 * W * n * 8 / gb, 2),
    "vario chunk d (16 x P float64, x3 temporaries)": round(3 * 16 * P * 8 / gb, 2),
}
rep["gpu_gb_estimate_total"] = round(sum(rep["gpu_gb_estimate"].values()), 2)
rep["surrogate_file_gb (999 x W x n float32)"] = round(999 * W * n * 4 / gb, 1)
print(json.dumps(rep, indent=1), flush=True)
if a.plan:
    sys.exit(0)

# synthetic fields: smooth base (mean of 60 nearest cells of white noise) + per-window noise; 10% missing
rng = np.random.default_rng(1)
_, nb = tree.query(xy, k=60)
base = rng.standard_normal(n)[nb].mean(1)
F = base[None, :] + 0.3 * rng.standard_normal((W, n))
F[rng.random((W, n)) < 0.10] = np.nan

sys.path.insert(0, a.nyc_lib)
import cupy as cp  # noqa: E402
import nyc_lib as N  # noqa: E402

pool = cp.get_default_memory_pool()
t = time.time()
if a.lowmem:
    sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
    from lowmem_null import LowMemVariogramNull
    null = LowMemVariogramNull(F, xy, a.res, kmax=a.kmax, chunk=a.lowmem)
else:
    null = N.VariogramNull(F, xy, a.res, kmax=a.kmax)
rep["implementation"] = f"LowMemVariogramNull(chunk={a.lowmem})" if a.lowmem else "nyc_lib.VariogramNull"
cp.cuda.Device().synchronize()
rep["init_seconds"] = round(time.time() - t, 1)
rep["gpu_gb_after_init"] = round(pool.total_bytes() / gb, 2)
print("init", rep["init_seconds"], "s; pool", rep["gpu_gb_after_init"], "GB", flush=True)

times, kk = [], []
t = time.time()
for d, (s, k) in enumerate(null.draws(a.draws, np.random.default_rng(2027))):
    cp.cuda.Device().synchronize()
    times.append(time.time() - t)
    kk.append(int(k))
    print(f"draw {d}: {times[-1]:.1f} s (k = {k}); pool {pool.total_bytes() / gb:.2f} GB", flush=True)
    t = time.time()
steady = float(np.median(times[1:])) if len(times) > 1 else times[0]
rep.update(draw_seconds=[round(x, 1) for x in times], ks_chosen=kk, steady_draw_seconds=round(steady, 1),
           peak_gpu_gb=round(pool.total_bytes() / gb, 2),
           projected_999_hours=round((rep["init_seconds"] + 999 * steady) / 3600, 1),
           projected_499_hours=round((rep["init_seconds"] + 499 * steady) / 3600, 1))
print(json.dumps(rep, indent=1), flush=True)
if a.out:
    json.dump(rep, open(a.out, "w"), indent=1)
