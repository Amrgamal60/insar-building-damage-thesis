"""Checkpoint 1, processing server (AUSTIN_PLAN §9): terrain elevation and slope, mean within
the parcel, from the USGS 3DEP 1 m DEM.

Inputs: the name-free parcel polygons (prop_id, geometry, EPSG:32614) and the tile list from
c1_13_dem_tile_list.py. Each tile is downloaded and hashed.

Method (authors' choices, fixed before any InSAR file is opened):
- Parcels are transformed to the DEM's CRS (NAD83 / UTM 14N).
- Slope is computed on the 1 m grid by Horn's 3x3 method, in degrees, on the whole tile
  including its overlap margin, so there is no edge effect between tiles.
- Each tile is then cut to its nominal 10 km square, so no pixel is counted twice.
- A pixel belongs to a parcel if its centre lies inside the polygon. Elevation and slope are
  the means over the parcel's valid pixels. A parcel with no pixel centre inside takes the
  pixel under its centroid (counted).
No outcome and no InSAR value is read.
"""
import argparse
import hashlib
import json
import multiprocessing as mp
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
import shapely
from rasterio import features
from rasterio.windows import Window, from_bounds

p = argparse.ArgumentParser()
p.add_argument("--parcels", type=Path, required=True)
p.add_argument("--tiles", type=Path, required=True)
p.add_argument("--work", type=Path, required=True)
p.add_argument("--out", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
p.add_argument("--workers", type=int, default=6)
a = p.parse_args()
(a.work / "tiles").mkdir(parents=True, exist_ok=True)
TILES = json.loads(a.tiles.read_text())["items"]


def fetch(item):
    f = a.work / "tiles" / item["url"].rsplit("/", 1)[1]
    if not (f.exists() and f.stat().st_size == item["bytes"]):
        with requests.get(item["url"], stream=True, timeout=600, headers={"User-Agent": "research-client"}) as r:
            r.raise_for_status()
            with open(f, "wb") as o:
                for chunk in r.iter_content(1 << 22):
                    o.write(chunk)
    h = hashlib.sha256()
    with open(f, "rb") as o:
        for b in iter(lambda: o.read(1 << 24), b""):
            h.update(b)
    return dict(file=f.name, bytes=f.stat().st_size, sha256=h.hexdigest())


def horn_slope_deg(z, res):
    s = np.full(z.shape, np.nan, dtype="float32")
    a_, b_, c_ = z[:-2, :-2], z[:-2, 1:-1], z[:-2, 2:]
    d_, f_ = z[1:-1, :-2], z[1:-1, 2:]
    g_, h_, i_ = z[2:, :-2], z[2:, 1:-1], z[2:, 2:]
    dzdx = ((c_ + 2 * f_ + i_) - (a_ + 2 * d_ + g_)) / (8 * res)
    dzdy = ((g_ + 2 * h_ + i_) - (a_ + 2 * b_ + c_)) / (8 * res)
    s[1:-1, 1:-1] = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    return s


def one_tile(item):
    f = a.work / "tiles" / item["url"].rsplit("/", 1)[1]
    par = gpd.read_parquet(a.parcels)
    with rasterio.open(f) as src:
        assert src.crs.to_epsg() == 26914, src.crs
        res = src.res[0]
        assert abs(res - 1.0) < 1e-9 and abs(src.res[1] - 1.0) < 1e-9
        z = src.read(1).astype("float32")
        if src.nodata is not None:
            z[z == src.nodata] = np.nan
        z[z < -1000] = np.nan
        b = src.bounds
        left, top = round(b.left / 10000) * 10000, round(b.top / 10000) * 10000
        win = from_bounds(left, top - 10000, left + 10000, top, src.transform).round_offsets().round_lengths()
        win = win.intersection(Window(0, 0, src.width, src.height))
        tr = src.window_transform(win)
    slope = horn_slope_deg(z, res)
    r0, c0, h, w = int(win.row_off), int(win.col_off), int(win.height), int(win.width)
    z, slope = z[r0:r0 + h, c0:c0 + w], slope[r0:r0 + h, c0:c0 + w]
    par = par.to_crs(26914)
    x0, y1 = tr.c, tr.f
    x1, y0 = x0 + w * res, y1 - h * res
    bb = par.geometry.bounds
    sel = np.flatnonzero((bb.maxx > x0) & (bb.minx < x1) & (bb.maxy > y0) & (bb.miny < y1))
    out = dict(tile=f.name, nominal=[x0, y0, x1, y1], valid_share=float(np.isfinite(z).mean()), parcels_touching=int(len(sel)))
    if len(sel) == 0:
        return out, None
    lab = features.rasterize(((g, k + 1) for k, g in enumerate(par.geometry.iloc[sel])), out_shape=(h, w), transform=tr,
                             fill=0, all_touched=False, dtype="int32")
    n = len(sel) + 1
    flat = lab.ravel()
    ok = np.isfinite(z).ravel()
    oks = ok & np.isfinite(slope).ravel()
    df = pd.DataFrame(dict(
        idx=sel,
        n_pix=np.bincount(flat, minlength=n)[1:],
        n_valid=np.bincount(flat[ok], minlength=n)[1:],
        sum_elev=np.bincount(flat[ok], weights=z.ravel()[ok].astype("float64"), minlength=n)[1:],
        n_slope=np.bincount(flat[oks], minlength=n)[1:],
        sum_slope=np.bincount(flat[oks], weights=slope.ravel()[oks].astype("float64"), minlength=n)[1:]))
    c = par.geometry.iloc[sel].centroid
    col = np.floor((c.x.to_numpy() - x0) / res).astype(int)
    row = np.floor((y1 - c.y.to_numpy()) / res).astype(int)
    inside = (col >= 0) & (col < w) & (row >= 0) & (row < h)
    df["elev_centroid"], df["slope_centroid"] = np.nan, np.nan
    df.loc[inside, "elev_centroid"] = z[row[inside], col[inside]]
    df.loc[inside, "slope_centroid"] = slope[row[inside], col[inside]]
    return out, df


if __name__ == "__main__":
    with mp.Pool(min(a.workers, len(TILES))) as pool:
        files = pool.map(fetch, TILES)
        res = pool.map(one_tile, TILES)
    par = gpd.read_parquet(a.parcels)
    parts = pd.concat([d for _, d in res if d is not None], ignore_index=True)
    agg = parts.groupby("idx").agg(n_pix=("n_pix", "sum"), n_valid=("n_valid", "sum"), sum_elev=("sum_elev", "sum"),
                                   n_slope=("n_slope", "sum"), sum_slope=("sum_slope", "sum"),
                                   elev_centroid=("elev_centroid", "max"), slope_centroid=("slope_centroid", "max"))
    agg = agg.reindex(range(len(par)))
    out = pd.DataFrame(dict(prop_id=par.prop_id.to_numpy()))
    for k in ("n_pix", "n_valid", "n_slope"):
        out[k] = agg[k].fillna(0).astype("int64").to_numpy()
    out["elev_mean_m"] = (agg.sum_elev / agg.n_valid.where(agg.n_valid > 0)).to_numpy()
    out["slope_mean_deg"] = (agg.sum_slope / agg.n_slope.where(agg.n_slope > 0)).to_numpy()
    out["elev_centroid_m"], out["slope_centroid_deg"] = agg.elev_centroid.to_numpy(), agg.slope_centroid.to_numpy()
    out["source"] = np.where(out.n_pix > 0, "parcel mean", "centroid pixel")
    nopix = out.n_pix.eq(0)
    out["elevation_m"] = out.elev_mean_m.where(~nopix, out.elev_centroid_m)
    out["slope_deg"] = out.slope_mean_deg.where(~nopix, out.slope_centroid_deg)
    out.to_parquet(a.out, index=False)
    S = dict(tiles=files, per_tile=[o for o, _ in res], parcels=len(out),
             parcels_with_no_pixel_centre_inside=int(nopix.sum()),
             elevation_missing=int(out.elevation_m.isna().sum()), slope_missing=int(out.slope_deg.isna().sum()),
             parcels_with_some_invalid_pixels=int((out.n_valid < out.n_pix).sum()),
             pixel_area_over_polygon_area_median=float((out.n_pix / par.to_crs(26914).geometry.area.to_numpy()).median()),
             elevation_m=out.elevation_m.describe().round(3).to_dict(), slope_deg=out.slope_deg.describe().round(3).to_dict(),
             out_sha256=hashlib.sha256(a.out.read_bytes()).hexdigest())
    a.out_json.write_text(json.dumps(S, indent=1, default=float) + "\n")
    print(json.dumps({k: v for k, v in S.items() if k not in ("tiles", "per_tile")}, indent=1, default=float))
