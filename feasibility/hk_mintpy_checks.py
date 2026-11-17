"""Checks of the Hong Kong MintPy time series (NYC plan §17 step 4), before any order data are linked to InSAR values.

1. Run facts: dates, dates left out of the velocity fit, reference date and reference point.
2. Coverage: share of land pixels with temporal coherence >= 0.7 (MintPy's maskTempCoh).
3. Order buildings (S26 and S26A, unique by building block): how many sit on a pixel with temporal coherence >= 0.7, or
   have one within 1 pixel (40 m). Only coherence is read at these points; no velocity or displacement value.
4. Sign check: median line-of-sight velocity on the Chek Lap Kok airport platform (reclaimed 1992-98, known to settle)
   against the median of all valid land. Expected: lower (away from the satellite).
5. Cross-check with the Tay et al. 2022 NTU velocity map of the same track (TA011, ~90 m): Spearman correlation between
   the NTU value and the median MintPy velocity within 1 pixel, over points valid in both. Both maps have their own
   reference point, so only the correlation is reported.
Writes hongkong/mintpy/MINTPY_CHECKS.json.
With --local, checks the locally referenced product of hk_local_reference.py instead (temporalCoherence_local.h5,
velocity_local.h5) and writes MINTPY_CHECKS_local.json. The sign check is skipped there (the 1 km local reference removes
platform-wide settlement), and the NTU map is referenced the same way (minus the mean of its finite pixels within 1 km).
Run from Alex/:  PROJ_DATA=~/miniforge3/envs/insar/share/proj ~/miniforge3/envs/insar/bin/python -I feasibility/hk_mintpy_checks.py [--local]
"""
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from osgeo import gdal
from pyproj import Transformer
from scipy.ndimage import uniform_filter
from scipy.stats import spearmanr

gdal.UseExceptions()
ROOT = Path(__file__).resolve().parent / "hongkong"
MP = ROOT / "mintpy"
D = ROOT / "downloads"
AIRPORT = (113.895, 113.945, 22.295, 22.322)  # lon0 lon1 lat0 lat1: the 1990s platform, south of the 2016-22 reclamation
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32649", always_xy=True)
LOCAL = "--local" in sys.argv[1:]
SUF = "_local" if LOCAL else ""


def h5(name, key):
    with h5py.File(MP / name) as h:
        return h[key][:], dict(h.attrs)


def rowcol(lon, lat, a):
    x, y = TO_UTM.transform(np.asarray(lon, float), np.asarray(lat, float))
    r = np.floor((y - float(a["Y_FIRST"])) / float(a["Y_STEP"])).astype(int)
    c = np.floor((x - float(a["X_FIRST"])) / float(a["X_STEP"])).astype(int)
    inside = (r >= 0) & (r < int(a["LENGTH"])) & (c >= 0) & (c < int(a["WIDTH"]))
    return r, c, inside


def near(arr, r, c, k):
    """Values within k pixels of (r, c), edges clipped."""
    return arr[max(r - k, 0):r + k + 1, max(c - k, 0):c + k + 1]


def main():
    vel, a = h5(f"velocity{SUF}.h5", "velocity")
    vel = vel * 1000  # mm/yr, positive toward the satellite
    tc, _ = h5(f"temporalCoherence{SUF}.h5", "temporalCoherence")
    land = h5("waterMask.h5", "waterMask")[0].astype(bool)
    ok = (np.nan_to_num(tc) >= 0.7) & land  # MintPy's maskTempCoh rule
    if LOCAL:
        a = {**h5("velocity.h5", "velocity")[1], **{k: v for k, v in a.items() if k not in ("REF_Y", "REF_X", "REF_LAT", "REF_LON")}}
    with h5py.File(MP / "timeseries.h5") as h:
        dates = [d.decode() for d in h["date"][:]]
    lon, lat = Transformer.from_crs("EPSG:32649", "EPSG:4326", always_xy=True).transform(float(a["REF_LON"]), float(a["REF_LAT"]))
    out = {"run": {"dates": len(dates), "first": dates[0], "last": dates[-1],
                   "excluded_from_velocity": (MP / "exclude_date.txt").read_text().split(),
                   "reference_date": a.get("REF_DATE"), "reference_pixel_row_col": [int(a["REF_Y"]), int(a["REF_X"])],
                   "reference_lon_lat": [round(lon, 5), round(lat, 5)]},
           "coverage": {"land_pixels": int(land.sum()), "land_share_tcoh_ge_0.7": round(float(ok.sum() / land.sum()), 4),
                        "median_tcoh_land": round(float(np.nanmedian(tc[land])), 3)}}
    # 3. order buildings: coherence only
    orders = pd.concat([pd.read_csv(D / "s26_orders" / "BDS26.csv"), pd.read_csv(D / "s26a_orders" / "BDS26A.csv")])
    orders = orders.drop_duplicates("BLOCK_ID_EN")
    r, c, inside = rowcol(orders.Longitude, orders.Latitude, a)
    at = np.array([ok[i, j] if s else False for i, j, s in zip(r, c, inside)])
    w1 = np.array([near(ok, i, j, 1).any() if s else False for i, j, s in zip(r, c, inside)])
    out["order_buildings"] = {"unique_buildings": int(len(orders)), "inside_grid": int(inside.sum()),
                              "on_pixel_tcoh_ge_0.7": int(at.sum()), "within_1px_tcoh_ge_0.7": int(w1.sum()),
                              "median_tcoh_at_pixel": round(float(np.nanmedian([tc[i, j] for i, j, s in zip(r, c, inside) if s])), 3)}
    # 4. sign check
    if LOCAL:
        out["sign_check_airport"] = "skipped: the 1 km local reference removes platform-wide settlement"
    yy, xx = np.mgrid[0:int(a["LENGTH"]), 0:int(a["WIDTH"])]
    x = float(a["X_FIRST"]) + (xx + 0.5) * float(a["X_STEP"])
    y = float(a["Y_FIRST"]) + (yy + 0.5) * float(a["Y_STEP"])
    plon, plat = Transformer.from_crs("EPSG:32649", "EPSG:4326", always_xy=True).transform(x, y)
    box = np.zeros_like(ok) if LOCAL else (plon >= AIRPORT[0]) & (plon <= AIRPORT[1]) & (plat >= AIRPORT[2]) & (plat <= AIRPORT[3]) & ok
    out["sign_check_airport"] = out.get("sign_check_airport") or {"valid_pixels": int(box.sum()), "median_mm_yr": round(float(np.median(vel[box])), 2),
                                 "land_median_mm_yr": round(float(np.median(vel[ok])), 2),
                                 "pass": bool(np.median(vel[box]) < np.median(vel[ok]))}
    # 5. NTU cross-check
    ds = gdal.Open(str(ROOT / "work" / "ntu" / "HongKong_TA011_velocity_InSAR.tif"))
    g, nv = ds.GetGeoTransform(), ds.GetRasterBand(1).ReadAsArray().astype(float)
    nd = ds.GetRasterBand(1).GetNoDataValue()
    if nd is not None:
        nv[nv == nd] = np.nan
    if LOCAL:  # same local reference as hk_local_reference.py: minus the mean of finite pixels within ~1 km (12 px of ~90 m)
        fin = np.isfinite(nv)
        n_ = uniform_filter(fin.astype(float), 12, mode="constant")
        s_ = uniform_filter(np.where(fin, nv, 0.0), 12, mode="constant")
        nv = np.where(fin & (n_ > 0), nv - s_ / np.where(n_ > 0, n_, 1), np.nan)
    ii, jj = np.nonzero(np.isfinite(nv))
    nlon, nlat = g[0] + (jj + 0.5) * g[1], g[3] + (ii + 0.5) * g[5]
    r, c, inside = rowcol(nlon, nlat, a)
    pairs = []
    for k in np.nonzero(inside)[0]:
        m = near(ok, r[k], c[k], 1)
        if m.any():
            pairs.append((nv[ii[k], jj[k]], float(np.median(near(vel, r[k], c[k], 1)[m]))))
    p = np.array(pairs)
    rho = spearmanr(p[:, 0], p[:, 1])
    out["ntu_crosscheck"] = {"ntu_crs_wkt_head": ds.GetProjection()[:60], "points_valid_in_both": int(len(p)),
                             "spearman_rho": round(float(rho.statistic), 3)}
    (MP / f"MINTPY_CHECKS{SUF}.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
