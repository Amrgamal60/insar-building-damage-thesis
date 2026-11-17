"""Is the NYC class itself bit-reproducible on the GPU? Run it twice on the small field of check_equal.py."""
import sys

import numpy as np

sys.path.insert(0, "/mnt/data/Master-projects/Alex/feasibility/nyc/scripts")
import nyc_lib as N  # noqa: E402

rng = np.random.default_rng(5)
n, W = 4000, 11
xy = rng.uniform(0, 3000, (n, 2))
xy = np.unique(np.floor(xy / 30), axis=0) * 30 + 15
n = len(xy)
F = rng.standard_normal(n)[None, :] + 0.3 * rng.standard_normal((W, n))
F[rng.random((W, n)) < 0.1] = np.nan
a = N.VariogramNull(F, xy, 30.0, kmax=200)
b = N.VariogramNull(F, xy, 30.0, kmax=200)
for (sa, ka), (sb, kb) in zip(a.draws(4, np.random.default_rng(2027)), b.draws(4, np.random.default_rng(2027))):
    same = np.array_equal(np.nan_to_num(sa, nan=-9e9), np.nan_to_num(sb, nan=-9e9))
    print(f"NYC vs NYC: k {ka} vs {kb}; identical: {same}; max abs diff {np.nanmax(np.abs(sa - sb)):.3g}")
