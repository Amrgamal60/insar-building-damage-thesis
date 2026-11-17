"""Checkpoint 1, processing server (AUSTIN_PLAN §9 Baseline 2; §14 canopy entry of 2026-11-10):
tree canopy share within the parcel, from the City of Austin 2018 canopy layer.

Source: the City's Tree_canopy_2018 feature service (polygons, EPSG:26914, derived by the
City from 2018 NAIP imagery), exported by the service itself as a file geodatabase for the
envelope of the eligible parcels (602200, 3333100, 635400, 3370200) on 2026-11-10. The zip
is hashed on the project PC.

Method (authors' choices, fixed before any InSAR file is opened):
- Parcels are transformed to EPSG:26914.
- Some canopy polygons have thousands of holes, which the standard reader takes hours to
  sort. The layer is therefore read ring by ring (OGR_ORGANIZE_POLYGONS=SKIP): every ring
  becomes one simple polygon. A point is canopy if an odd number of rings contain it
  (even-odd rule), which is the same area as outer rings minus holes and does not depend on
  the direction in which a ring is stored. The reading is checked against the layer's own
  SHAPE_Area field, which is the signed sum of the ring areas (clockwise rings positive).
  Some features are stored with all their rings reversed and so carry a negative area; the
  even-odd rule reads them correctly.
- Canopy and parcels are rasterised on a 0.5 m grid (a pixel belongs to a polygon if its
  centre is inside). Canopy share = canopy pixels in the parcel / pixels in the parcel.
- A random 300 parcels (seed 2038) are also computed without a raster: the rings that touch
  the parcel are combined by symmetric difference (the even-odd rule for polygons) and
  intersected with the parcel. The largest difference from the raster value is reported.
No outcome and no InSAR value is read.
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
import time
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from affine import Affine
from rasterio import features
from rasterio.enums import MergeAlg

p = argparse.ArgumentParser()
p.add_argument("--parcels", type=Path, required=True)
p.add_argument("--canopy-zip", type=Path, required=True)
p.add_argument("--out", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
p.add_argument("--workers", type=int, default=24)
a = p.parse_args()
RES = 0.5
t0 = time.time()
assert os.environ.get("OGR_ORGANIZE_POLYGONS") == "SKIP"
# The geodatabase is read from an unzipped copy (reading it inside the zip is very slow).
gdb = zipfile.ZipFile(a.canopy_zip).namelist()[0].split("/")[0]
unz = a.canopy_zip.parent / "canopy_fgdb_unzipped"
if not (unz / gdb).exists():
    zipfile.ZipFile(a.canopy_zip).extractall(unz)
src = str(unz / gdb)
info = pyogrio.read_info(src, layer="Tree_canopy_2018")
assert info["crs"] == "EPSG:26914"
can = pyogrio.read_dataframe(src, layer="Tree_canopy_2018", columns=["gridcode", "SHAPE_Area"])
assert set(can.gridcode) == {1}
print(f"read {len(can)} features, {time.time() - t0:.0f} s", flush=True)
rings, owner = shapely.get_parts(can.geometry.to_numpy(), return_index=True)
n_inner = int(shapely.get_num_interior_rings(rings).sum())
sign = np.where(shapely.is_ccw(shapely.get_exterior_ring(rings)), -1.0, 1.0)
ring_area = shapely.area(rings)
area_read = np.bincount(owner, weights=sign * ring_area, minlength=len(can))
area_field = can.SHAPE_Area.to_numpy()
dif = np.abs(area_read - area_field)
area_check = dict(features=int(len(can)), rings=int(len(rings)), rings_read_with_their_own_holes=n_inner, anticlockwise_rings=int((sign < 0).sum()),
                  features_with_negative_stored_area=int((area_field < 0).sum()),
                  sum_read_m2=float(area_read.sum()), sum_field_m2=float(area_field.sum()),
                  features_differing_by_more_than_1_m2_and_1_percent=int(((dif > 1) & (dif > 0.01 * area_field)).sum()),
                  max_abs_difference_m2=float(dif.max()))
print(area_check, flush=True)
del can
tree = shapely.STRtree(rings)
par = gpd.read_parquet(a.parcels).to_crs(26914)
geom = par.geometry.to_numpy()
area = shapely.area(geom)
c = shapely.centroid(geom)
b = shapely.bounds(geom)
tiles = {}
for i, key in enumerate(zip(np.floor(shapely.get_x(c) / 1000).astype(int).tolist(), np.floor(shapely.get_y(c) / 1000).astype(int).tolist())):
    tiles.setdefault(key, []).append(i)
keys = sorted(tiles)
cb = np.array(info["total_bounds"])
print(f"{len(rings)} rings, {len(geom)} parcels, {len(keys)} tiles, {time.time() - t0:.0f} s", flush=True)


def one(key):
    idx = np.array(tiles[key])
    x0 = np.floor((b[idx, 0].min() - 1) / RES) * RES
    y0 = np.floor((b[idx, 1].min() - 1) / RES) * RES
    x1 = np.ceil((b[idx, 2].max() + 1) / RES) * RES
    y1 = np.ceil((b[idx, 3].max() + 1) / RES) * RES
    w, h = int(round((x1 - x0) / RES)), int(round((y1 - y0) / RES))
    tr = Affine(RES, 0, x0, 0, -RES, y1)
    hits = tree.query(shapely.box(x0, y0, x1, y1), predicate="intersects")
    lab = features.rasterize(((g, k + 1) for k, g in enumerate(geom[idx])), out_shape=(h, w), transform=tr, fill=0,
                             all_touched=False, dtype="int32")
    n = len(idx) + 1
    npix = np.bincount(lab.ravel(), minlength=n)[1:]
    ncan = np.zeros(len(idx), dtype="int64")
    if len(hits):
        cnt = features.rasterize(((g, 1) for g in rings[hits]), out_shape=(h, w), transform=tr, fill=0, all_touched=False,
                                 merge_alg=MergeAlg.add, dtype="int32")
        ncan = np.bincount(lab.ravel()[(cnt.ravel() % 2) == 1], minlength=n)[1:]
    return idx, npix, ncan


def exact(i):
    hits = tree.query(geom[i], predicate="intersects")
    if not len(hits):
        return 0.0
    box = shapely.bounds(geom[i])
    r = shapely.make_valid(shapely.clip_by_rect(shapely.make_valid(rings[hits]), box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1))
    acc = r[0]
    for g in r[1:]:
        acc = shapely.symmetric_difference(acc, g)
    return float(shapely.area(shapely.intersection(geom[i], acc)))


if __name__ == "__main__":
    npix = np.zeros(len(geom), dtype="int64")
    ncan = np.zeros(len(geom), dtype="int64")
    with mp.Pool(a.workers) as pool:
        for k, (idx, n1, n2) in enumerate(pool.imap_unordered(one, keys, chunksize=4)):
            npix[idx], ncan[idx] = n1, n2
            if k % 100 == 0:
                print(f"{k}/{len(keys)} tiles, {time.time() - t0:.0f} s", flush=True)
        sample = np.sort(np.random.default_rng(2038).choice(len(geom), size=300, replace=False))
        ex = np.array(pool.map(exact, sample.tolist(), chunksize=5))
    share = np.where(npix > 0, ncan / np.maximum(npix, 1), np.nan)
    out = pd.DataFrame(dict(prop_id=par.prop_id.to_numpy(), parcel_area_m2=area, n_pix=npix, n_canopy_pix=ncan, canopy_share=share))
    out.to_parquet(a.out, index=False)
    diff = share[sample] - ex / area[sample]
    inside = (b[:, 0] >= cb[0]) & (b[:, 1] >= cb[1]) & (b[:, 2] <= cb[2]) & (b[:, 3] <= cb[3])
    S = dict(canopy_zip=a.canopy_zip.name, canopy_zip_sha256=hashlib.sha256(a.canopy_zip.read_bytes()).hexdigest(),
             ring_reading_area_check=area_check, canopy_bounds=[round(float(v), 1) for v in cb],
             parcels=len(out), parcels_inside_canopy_layer_bounds=int(inside.sum()), parcels_without_pixels=int((npix == 0).sum()),
             pixel_m=RES, pixel_area_over_polygon_area_median=float(np.median(npix * RES * RES / area)),
             canopy_share=out.canopy_share.describe().round(4).to_dict(), share_zero=int((out.canopy_share == 0).sum()),
             exact_check=dict(parcels=len(sample), seed=2038, max_abs_difference=float(np.abs(diff).max()),
                              mean_difference=float(diff.mean()), p95_abs_difference=float(np.quantile(np.abs(diff), 0.95))),
             seconds=round(time.time() - t0, 1), out_sha256=hashlib.sha256(a.out.read_bytes()).hexdigest())
    a.out_json.write_text(json.dumps(S, indent=1, default=float) + "\n")
    print(json.dumps(S, indent=1, default=float))
