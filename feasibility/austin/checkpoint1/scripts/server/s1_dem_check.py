"""Independent check of s1_dem.py on 60 random parcels (seed 2039), by a second code path:
a window read straight from the tile, pixel centres tested against the polygon with shapely,
and slope by scipy.ndimage correlation with Horn's kernels."""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from rasterio.windows import from_bounds
from scipy import ndimage

parcels, tiles_dir, result, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
par = gpd.read_parquet(parcels).to_crs(26914)
res = pd.read_parquet(result).set_index("prop_id")
pick = np.sort(np.random.default_rng(2039).choice(len(par), size=60, replace=False))
srcs = [rasterio.open(f) for f in sorted(tiles_dir.glob("*.tif"))]
KX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]) / 8.0
KY = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]) / 8.0
rows, skipped = [], 0
for i in pick:
    g = par.geometry.iloc[i]
    x0, y0, x1, y1 = g.bounds
    b = (np.floor(x0) - 3, np.floor(y0) - 3, np.ceil(x1) + 3, np.ceil(y1) + 3)
    use = [s for s in srcs if s.bounds.left <= b[0] and s.bounds.right >= b[2] and s.bounds.bottom <= b[1] and s.bounds.top >= b[3]]
    if not use:
        skipped += 1
        continue
    s = use[0]
    win = from_bounds(*b, s.transform).round_offsets().round_lengths()
    z = s.read(1, window=win).astype("float64")
    tr = s.window_transform(win)
    sl = np.degrees(np.arctan(np.hypot(ndimage.correlate(z, KX, mode="nearest"), ndimage.correlate(z, KY, mode="nearest"))))
    cols, rws = np.meshgrid(np.arange(z.shape[1]), np.arange(z.shape[0]))
    X, Y = tr.c + (cols + 0.5) * tr.a, tr.f + (rws + 0.5) * tr.e
    inside = shapely.contains_xy(g, X, Y)
    pid = par.prop_id.iloc[i]
    rows.append(dict(prop_id=pid, elev=float(z[inside].mean()), slope=float(sl[inside].mean()), n=int(inside.sum()),
                     elev_main=float(res.elevation_m[pid]), slope_main=float(res.slope_deg[pid]), n_main=int(res.n_pix[pid])))
d = pd.DataFrame(rows)
S = dict(parcels_drawn=len(pick), parcels_checked=len(d), skipped_window_crosses_a_tile_edge=skipped, seed=2039,
         max_abs_elevation_difference_m=float((d.elev - d.elev_main).abs().max()),
         max_abs_slope_difference_deg=float((d.slope - d.slope_main).abs().max()),
         pixel_counts_equal=int((d.n == d.n_main).sum()), max_abs_pixel_count_difference=int((d.n - d.n_main).abs().max()))
out.write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps(S, indent=1))
