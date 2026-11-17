"""Test A surrogates: GPU-path file against the CPU-path file, draw by draw (AUSTIN_PLAN.md §15 part 3, file-choice rule).
Both are float32 .npy (draws, W, P_null); either may still be the .tmp.npy being written. Only draws below --upto
(default: the draws both files are known to hold, from allocated blocks minus one) are read, read-only.
Agreement: same missing values; each value identical as float32 or at most one float32 rounding step apart.
Usage: python -I check_gpu_cpu_draws.py GPU_NPY CPU_NPY OUT_JSON [--upto N]
"""
import argparse
import json
import os
from pathlib import Path

import numpy as np

p = argparse.ArgumentParser()
p.add_argument("gpu", type=Path)
p.add_argument("cpu", type=Path)
p.add_argument("out", type=Path)
p.add_argument("--upto", type=int, default=None)
a = p.parse_args()
G, C = np.load(a.gpu, mmap_mode="r"), np.load(a.cpu, mmap_mode="r")
assert G.shape[1:] == C.shape[1:] and G.dtype == C.dtype == np.float32
per = int(np.prod(G.shape[1:])) * 4


def held(path, arr):
    if not path.name.endswith(".tmp.npy"):
        return arr.shape[0]
    return max(0, os.stat(path).st_blocks * 512 // per - 1)  # sequential writes; last one may be partial


n = min(held(a.gpu, G), held(a.cpu, C)) if a.upto is None else a.upto
rows, worst_steps, nonid = [], 0, 0
for d in range(n):
    g, c = np.asarray(G[d]), np.asarray(C[d])
    same_nan = bool(np.array_equal(np.isnan(g), np.isnan(c)))
    ok = ~np.isnan(g) & ~np.isnan(c)
    gi, ci = g[ok].view(np.int32).astype(np.int64), c[ok].view(np.int32).astype(np.int64)
    # ULP distance for same-sign floats (sign flips counted as large)
    same_sign = (gi >= 0) == (ci >= 0)
    steps = np.where(same_sign, np.abs(gi - ci), np.iinfo(np.int64).max)
    m = int(steps.max()) if steps.size else 0
    k = int((steps != 0).sum())
    rows.append(dict(draw=d, nan_identical=same_nan, max_float32_steps=m, values_not_identical=k,
                     max_abs_diff=float(np.abs(g[ok].astype(np.float64) - c[ok]).max()) if ok.any() else 0.0,
                     all_zero=bool(not g.any() or not c.any())))
    worst_steps, nonid = max(worst_steps, m), nonid + k
values = sum(int((~np.isnan(np.asarray(G[d]))).sum()) for d in range(n))
R = dict(gpu=str(a.gpu.name), cpu=str(a.cpu.name), draws_compared=n,
         all_nan_identical=all(r["nan_identical"] for r in rows), max_float32_steps=worst_steps,
         values_not_identical=nonid, values_compared=values,
         share_not_identical=nonid / values if values else None,
         max_abs_diff=max((r["max_abs_diff"] for r in rows), default=0.0),
         any_unwritten_draw=any(r["all_zero"] for r in rows), per_draw=rows)
R["pass"] = bool(n > 0 and R["all_nan_identical"] and worst_steps <= 1 and not R["any_unwritten_draw"])
a.out.write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps({k: v for k, v in R.items() if k != "per_draw"}, indent=1))
