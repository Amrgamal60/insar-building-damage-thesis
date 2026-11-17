"""Server GPU environment check (scratch, not a project script): frozen GPU LowMemVariogramNull (CuPy) against
CPULowMemVariogramNull on small synthetic masked fields, at the production settings (kmax 1000, max lag 16, chunk 8)
and through the ConditionalVariogramNull wrapper used by make_surrogates.py. Bounded GPU pool.
Usage: python -I check_gpu_small.py CODE_AUSTIN_DIR OUT_JSON
"""
import os
for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[name] = "1"
import json
import sys
from pathlib import Path

import numpy as np

code, out = Path(sys.argv[1]), Path(sys.argv[2])
sys.path[:0] = [str(code / "freeze" / "scripts"), str(code / "freeze" / "scripts" / "calibration")]
import cupy as cp  # noqa: E402
from conditional_null import ConditionalVariogramNull  # noqa: E402
from cpu_null import CPULowMemVariogramNull  # noqa: E402
from lowmem_null import LowMemVariogramNull  # noqa: E402

cp.get_default_memory_pool().set_limit(size=1024 ** 3)
R = dict(cupy=cp.__version__, numpy=np.__version__, device=cp.cuda.runtime.getDeviceProperties(0)["name"].decode(),
         driver=cp.cuda.runtime.driverGetVersion(), cases=[])


def compare(gen_g, gen_c, label):
    errs, f32_same, ks = [], [], []
    for (fg, kg), (fc, kc) in zip(gen_g, gen_c):
        assert kg == kc, (label, kg, kc)
        assert np.array_equal(np.isnan(fg), np.isnan(fc)), label
        errs.append(float(np.nanmax(np.abs(fg - fc))))
        f32_same.append(float(np.mean(fg.astype(np.float32).view(np.uint32) == fc.astype(np.float32).view(np.uint32))))
        ks.append(int(kg))
    R["cases"].append(dict(label=label, draws=len(errs), max_abs_diff=max(errs), k=ks,
                           float32_bytes_identical_fraction_min=min(f32_same)))
    return max(errs)


rng = np.random.default_rng(20261111)
# 1) engines directly, production settings, ~3,000 pixels on a 30 m grid, 8 windows with masks
xy = np.unique(rng.integers(0, 70, (3600, 2)), axis=0).astype(float) * 30 + 15
n = len(xy)
base = np.sin(xy[:, 0] / 400) + np.cos(xy[:, 1] / 300)
fields = np.array([base + 0.4 * rng.standard_normal(n) for _ in range(8)])
fields[rng.random(fields.shape) < 0.05] = np.nan
g = LowMemVariogramNull(fields, xy, 30., kmax=1000, max_lag=16, chunk=8)
c = CPULowMemVariogramNull(fields, xy, 30., kmax=1000, max_lag=16, chunk=8)
e1 = compare(g.draws(4, np.random.default_rng(2027)), c.draws(4, np.random.default_rng(2027)), "engine_kmax1000")
# 2) conditional wrapper (as make_surrogates.py: factory None = frozen GPU class; CPU factory)
X = np.column_stack([base, rng.standard_normal(n), xy[:, 0] / 1e3])
a = ConditionalVariogramNull(fields, xy, 30., X, null_factory=None, kmax=1000, max_lag=16, chunk=8)
b = ConditionalVariogramNull(fields, xy, 30., X, null_factory=CPULowMemVariogramNull, kmax=1000, max_lag=16, chunk=8)
e2 = compare(a.draws(3, np.random.default_rng(2027)), b.draws(3, np.random.default_rng(2027)), "conditional_kmax1000")
R["gpu_pool_peak_mib"] = cp.get_default_memory_pool().total_bytes() / 1024 ** 2
R["pass"] = bool(max(e1, e2) < 1e-11)
out.write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps(R, indent=1))
