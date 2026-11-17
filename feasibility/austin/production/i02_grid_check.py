"""Pixel-grid check (AUSTIN_PLAN.md §15, checkpoint 1: "checked against the coordinates of the first granule at
the InSAR step"). Checkpoint 1 assumed pixel edges at multiples of 30 m in EPSG:32614 (pixel centres at
30 k + 15 m), from the frame's snapped bounding box. This reads only the coordinate vectors and the grid metadata
of every downloaded granule (x, y, spatial_ref), no displacement or mask value, and checks:
  - CRS EPSG:32614, spacing +30 m in x and -30 m in y;
  - every x and y pixel centre equals 30 k + 15;
  - all granules share the first granule's x and y vectors;
  - every eligible house's pixel centre (checkpoint-1 pix_cx, pix_cy) lies on the subset's grid.
The OPERA environment has no parquet reader, so the pixel centres come from an .npz with arrays pix_cx and
pix_cy (written from checkpoint1 eligible_grid_folds.parquet by i00_house_pixels.py).
Usage: OPERA_PYTHON -I feasibility/austin/production/i02_grid_check.py DISP_DIR HOUSE_PIXELS_NPZ OUT_JSON
"""
import json
import sys
from pathlib import Path

import h5py
import numpy as np

disp, grid, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
files = sorted(disp.glob("*.nc"))
assert files, "no granule"


def coords(p):
    with h5py.File(p, "r") as h:
        x, y = h["x"][()], h["y"][()]
        sr = dict(h["spatial_ref"].attrs) if "spatial_ref" in h else {}
    return x, y, sr


x0, y0, sr = coords(files[0])
wkt = str(sr.get("crs_wkt", sr.get("spatial_ref", b"")))
epsg_ok = 'ID["EPSG",32614]' in wkt or "32614" in wkt
same = all(np.array_equal(x0, x) and np.array_equal(y0, y) for x, y, _ in (coords(p) for p in files[1:]))
dx, dy = np.unique(np.diff(x0)), np.unique(np.diff(y0))
centres_ok = bool(np.all((x0 - 15) % 30 == 0) and np.all((y0 - 15) % 30 == 0))
with np.load(grid) as z:
    cx, cy = z["pix_cx"], z["pix_cy"]
inside = bool(np.isin(cx, x0).all() and np.isin(cy, y0).all())
R = dict(granules=len(files), first=files[0].name, crs_epsg_32614=epsg_ok, dx=dx.tolist(), dy=dy.tolist(),
         x_range=[float(x0.min()), float(x0.max())], y_range=[float(y0.min()), float(y0.max())],
         shape=[len(y0), len(x0)], centres_at_30k_plus_15=centres_ok, all_granules_same_grid=same,
         all_house_pixels_inside_subset=inside, houses=len(cx),
         grid_as_assumed=bool(epsg_ok and dx.tolist() == [30.0] and dy.tolist() == [-30.0] and centres_ok and same and inside))
out.write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps(R, indent=1))
