"""Austin plan step 0 (§10): CPU timing of what the conditional null adds, at full size.

No InSAR value and no outcome is read. Inputs: the step-0 pixel centres, as for null_timing.py.
Velocity fields are synthetic as in null_timing.py (smooth base + per-window noise, 10% missing);
pixel covariates are synthetic smooth fields. The production class ConditionalVariogramNull
(scripts/conditional_null.py) is run unchanged, with a stub in place of the variogram generator:
  - construction = one HistGradientBoostingRegressor fit and prediction per window (timed);
  - each draw = generator draw on the residual field + adding the fitted field back (the
    addition is timed with stub residuals).
The generator's own construction and draw cost are those of the registered null, timed on the
GPU at the same size (timing_k1000_lowmem.json); the projection adds the two.
"""
import argparse
import json
import os
import resource
import sys
import time

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
from conditional_null import ConditionalVariogramNull, HGB_SETTINGS  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("xy")
ap.add_argument("--windows", type=int, default=88)
ap.add_argument("--features", type=int, default=7, help="Baseline 1 without x/y: 7 under A, 6 under C")
ap.add_argument("--add-reps", type=int, default=5)
ap.add_argument("--registered", default=os.path.join(HERE, "timing_k1000_lowmem.json"))
ap.add_argument("--out", default=None)
a = ap.parse_args()

xy = np.load(a.xy).astype(float)
n, W = len(xy), a.windows
rng = np.random.default_rng(1)
tree = cKDTree(xy)
_, nb = tree.query(xy, k=60)
base = rng.standard_normal(n)[nb].mean(1)
cov = np.column_stack([rng.standard_normal(n)[nb].mean(1) + 0.1 * rng.standard_normal(n)
                       for _ in range(a.features)])
F = base[None, :] + 0.5 * cov[:, 0][None, :] + 0.3 * rng.standard_normal((W, n))
F[rng.random((W, n)) < 0.10] = np.nan
names = [f"feature_{i}" for i in range(a.features)]
rep = dict(n_pixels=n, windows=W, features=a.features, cpu_count=os.cpu_count(),
           omp_num_threads=os.environ.get("OMP_NUM_THREADS"), hgb_settings=HGB_SETTINGS)


class StubGenerator:
    """Stands in for LowMemVariogramNull: no variogram work, random residual fields."""

    def __init__(self, fields, xy, res, **kwargs):
        self.shape = np.asarray(fields).shape

    def draws(self, n_draws, rng):
        for _ in range(n_draws):
            yield rng.standard_normal(self.shape), 0


t = time.time()
null = ConditionalVariogramNull(F, xy, 30., cov, feature_names=names, null_factory=StubGenerator)
rep["construction_seconds"] = round(time.time() - t, 1)
rep["per_window_fit_seconds"] = round(rep["construction_seconds"] / W, 2)
rep["explained_variance_mean"] = round(float(np.mean(null.explained_variance)), 3)

# Time only the addition: pre-generate stub residuals, then time the class's own expression.
residuals = [r for r, _ in StubGenerator(F, xy, 30.).draws(a.add_reps, np.random.default_rng(2))]
add = []
for r in residuals:
    t = time.time()
    out = np.where(null.valid, null.fitted + r, np.nan)
    add.append(time.time() - t)
assert out.shape == F.shape and np.array_equal(np.isnan(out), np.isnan(F))
rep["add_seconds_per_draw"] = round(float(np.median(add)), 3)
rep["host_arrays_gb (fitted + residuals + valid)"] = round(
    (null.fitted.nbytes + null.residuals.nbytes + null.valid.nbytes) / 1e9, 3)
rep["peak_rss_gb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2)

reg = json.load(open(a.registered))
init, draw = reg["init_seconds"], reg["steady_draw_seconds"]
rep["registered_gpu_timing"] = dict(source=os.path.basename(a.registered), init_seconds=init,
                                    steady_draw_seconds=draw, n_cells=reg["n_cells"])
rep["projected_999_hours"] = round((init + rep["construction_seconds"]
                                    + 999 * (draw + rep["add_seconds_per_draw"])) / 3600, 2)
print(json.dumps(rep, indent=1), flush=True)
if a.out:
    json.dump(rep, open(a.out, "w"), indent=1)
