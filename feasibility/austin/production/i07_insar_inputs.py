"""Inputs of the InSAR window computation (AUSTIN_PLAN.md §7), as one .npz that the OPERA environment can read
(it has no parquet reader). Outcome-blind: no event, outcome, fold or block column is read or written.

From checkpoint 1 (eligible_grid_folds.parquet, columns prop_id, pix_i, pix_j, cell250_x, cell250_y only):
  - pixels: the unique pixels holding an eligible house, in testa_core.Geometry order (sorted key
    pix_i * 1,000,000 + pix_j), with their subset row r and column c (pix_i = floor(x / 30), pix_j = floor(y / 30));
  - houses (prop_id order): prop_id and the index of the house's pixel;
  - cells: the 250 m cells holding an eligible parcel point (§7, Test B), sorted by (cell250_x, cell250_y), and
    each house's cell.
From the DISP subset grid (production/check/grid_check.json): x0, y0 (centres of column 0 and row 0), rows, cols.
From the full-purpose boundary (vnwj-xmz9, checkpoint 1): inside_city, a rows x cols boolean of pixel centres
inside the boundary (the §14 connected-component rule of 2026-11-11).

Usage: .venv/bin/python -I feasibility/austin/production/i07_insar_inputs.py GRID_FOLDS_PARQUET BOUNDARY_GEOJSON \
         GRID_CHECK_JSON OUT_NPZ
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import shape

KEY = 1_000_000  # as testa_core.KEY
BOUNDARY_SHA256 = "9656bd73a7a7989ef41fd0610f716a8078d0fe843d0466b21e9acef9f93ede47"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


grid_folds, boundary, grid_json, out = map(Path, sys.argv[1:5])
assert sha256(boundary) == BOUNDARY_SHA256
G = json.loads(grid_json.read_text())
assert G["grid_as_assumed"] and G["dx"] == [30.0] and G["dy"] == [-30.0]
x0, y0 = G["x_range"][0], G["y_range"][1]
NR, NC = G["shape"]

g = pd.read_parquet(grid_folds, columns=["prop_id", "pix_i", "pix_j", "cell250_x", "cell250_y"])
assert g.prop_id.is_unique and g.prop_id.is_monotonic_increasing
pi, pj = g.pix_i.to_numpy(np.int64), g.pix_j.to_numpy(np.int64)
ukey, house_pixel = np.unique(pi * KEY + pj, return_inverse=True)
pix_i, pix_j = ukey // KEY, ukey % KEY
c = pix_i - int(round((x0 - 15) / 30))
r = int(round((y0 - 15) / 30)) - pix_j
assert (c >= 0).all() and (c < NC).all() and (r >= 0).all() and (r < NR).all()
assert np.allclose(x0 + 30 * c, pix_i * 30 + 15) and np.allclose(y0 - 30 * r, pix_j * 30 + 15)
ckey = g.cell250_x.to_numpy(np.int64) * KEY + g.cell250_y.to_numpy(np.int64)
cell_key, house_cell = np.unique(ckey, return_inverse=True)

geo = json.loads(boundary.read_text())
tr = Transformer.from_crs("EPSG:4326", "EPSG:32614", always_xy=True)
city = shapely.union_all([shapely.transform(shape(f["geometry"]), lambda a: np.c_[tr.transform(a[:, 0], a[:, 1])])
                          for f in geo["features"]])
XX, YY = np.meshgrid(x0 + 30.0 * np.arange(NC), y0 - 30.0 * np.arange(NR))
inside_city = shapely.contains_xy(city, XX.ravel(), YY.ravel()).reshape(NR, NC)

np.savez(out, prop_id=g.prop_id.to_numpy().astype("U12"), house_pixel=house_pixel.astype(np.int64),
         pix_i=pix_i, pix_j=pix_j, r=r.astype(np.int64), c=c.astype(np.int64),
         cell_x=cell_key // KEY, cell_y=cell_key % KEY, house_cell=house_cell.astype(np.int64),
         inside_city=inside_city, grid=np.array([x0, y0, NR, NC], dtype=np.float64))
info = dict(houses=len(g), pixels=len(ukey), cells=len(cell_key), inside_city_pixels=int(inside_city.sum()),
            grid=dict(x0=x0, y0=y0, rows=NR, cols=NC),
            inputs={p.name: sha256(p) for p in (grid_folds, boundary, grid_json)}, npz_sha256=sha256(out))
Path(str(out) + ".json").write_text(json.dumps(info, indent=1) + "\n")
print(json.dumps(info, indent=1))
