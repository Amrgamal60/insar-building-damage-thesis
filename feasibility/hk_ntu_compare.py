"""Matched comparison of our Hong Kong velocities with the Tay et al. 2022 (NTU) map (NYC plan §17; asked for in the
2026-10-17 GPT review). No order data are read. The settings of both products are listed in hongkong/NTU_COMPARISON.md.

Made comparable as far as the files allow:
  - period: ours refitted over June 2015 to April 2020 (timeseries2velocity --end-date 20200430; NTU: Oct 2014 to Apr 2020),
    beside our full 2015-2023 fit;
  - direction and units: ours converted from line of sight to vertical as NTU did (v / cos(incidence), per pixel,
    inputs/geometryGeo.h5), both in mm/yr, negative = away from the satellite / down;
  - support and grid: our 40 m pixels with temporal coherence >= 0.7 (land) averaged into each ~90 m NTU pixel
    (pixel centres binned); only NTU pixels that are finite and hold >= 1 valid pixel of ours are used (the intersection);
  - local reference: where used, the same operation on the same grid and mask for both (value minus the mean of the
    intersection pixels within 12 x 12 NTU pixels, ~1 km).
NTU's map is itself interpolated (kriging-type with per-pixel uncertainty, Tay et al. Methods), so its pixels are not
independent measurements. Also with a plane (lon, lat) removed from both over the intersection (NTU deramped
linearly; we did not), and, as an artefact check, the correlation of each map's 1 km local values with the local
terrain height (DEM height averaged the same way). Scale check: both maps averaged into square blocks of 0.5, 1, 2 and 4 km (blocks with
>= 5 intersection pixels) and correlated.
Writes hongkong/mintpy/NTU_COMPARISON.json.
Run from Alex/:  PROJ_DATA=~/miniforge3/envs/insar/share/proj ~/miniforge3/envs/insar/bin/python -I feasibility/hk_ntu_compare.py
"""
import json
from pathlib import Path

import h5py
import numpy as np
from osgeo import gdal
from pyproj import Transformer
from scipy.ndimage import uniform_filter
from scipy.stats import spearmanr

gdal.UseExceptions()
ROOT = Path(__file__).resolve().parent / "hongkong"
MP = ROOT / "mintpy"
PRODUCTS = {"run2_2015_2023": ("velocity.h5", "temporalCoherence.h5"),
            "run2_2015_2020": ("velocity_2015_2020.h5", "temporalCoherence.h5"),
            "local_2015_2023": ("velocity_local.h5", "temporalCoherence_local.h5"),
            "local_2015_2020": ("velocity_local_2015_2020.h5", "temporalCoherence_local.h5")}


def rd(name, key):
    with h5py.File(MP / name) as h:
        return h[key][:], dict(h.attrs)


def locref(v, m, w=12):
    n = uniform_filter(m.astype(float), w, mode="constant")
    s = uniform_filter(np.where(m, v, 0.0), w, mode="constant")
    return np.where(m & (n > 0), v - s / np.where(n > 0, n, 1), np.nan)


def deramp(v, m, lon, lat):
    """Minus the least-squares plane in lon/lat fitted over mask m (NTU's step 3 was a linear deramp)."""
    G = np.c_[np.ones(m.sum()), lon[m], lat[m]]
    coef = np.linalg.lstsq(G, v[m], rcond=None)[0]
    return np.where(m, v - (coef[0] + coef[1] * lon + coef[2] * lat), np.nan)


def stats(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    return {"n": int(ok.sum()), "spearman": round(float(spearmanr(a, b).statistic), 3),
            "pearson": round(float(np.corrcoef(a, b)[0, 1]), 3),
            "ours_p5_p50_p95": [round(float(x), 2) for x in np.percentile(a, [5, 50, 95])],
            "ntu_p5_p50_p95": [round(float(x), 2) for x in np.percentile(b, [5, 50, 95])]}


def main():
    ds = gdal.Open(str(ROOT / "work" / "ntu" / "HongKong_TA011_velocity_InSAR.tif"))
    g = ds.GetGeoTransform()
    ntu = ds.GetRasterBand(1).ReadAsArray().astype(float) * 1000  # m/yr -> mm/yr, vertical
    land = rd("waterMask.h5", "waterMask")[0].astype(bool)
    inc = rd("inputs/geometryGeo.h5", "incidenceAngle")[0]
    a = rd("velocity.h5", "velocity")[1]
    yy, xx = np.mgrid[0:land.shape[0], 0:land.shape[1]]
    lon, lat = Transformer.from_crs("EPSG:32649", "EPSG:4326", always_xy=True).transform(
        float(a["X_FIRST"]) + (xx + 0.5) * float(a["X_STEP"]), float(a["Y_FIRST"]) + (yy + 0.5) * float(a["Y_STEP"]))
    nr = np.floor((lat - g[3]) / g[5]).astype(int)
    nc = np.floor((lon - g[0]) / g[1]).astype(int)
    inside = (nr >= 0) & (nr < ntu.shape[0]) & (nc >= 0) & (nc < ntu.shape[1])
    flat = np.where(inside, nr * ntu.shape[1] + nc, -1)
    glon = g[0] + (np.arange(ntu.shape[1])[None, :] + 0.5) * g[1] + 0 * ntu
    glat = g[3] + (np.arange(ntu.shape[0])[:, None] + 0.5) * g[5] + 0 * ntu
    hgt_ = rd("inputs/geometryGeo.h5", "height")[0]
    hm = land & np.isfinite(hgt_) & (flat >= 0)
    hc = np.bincount(flat[hm], minlength=ntu.size).reshape(ntu.shape)
    hgt = np.where(hc > 0, np.bincount(flat[hm], weights=hgt_[hm], minlength=ntu.size).reshape(ntu.shape) / np.maximum(hc, 1), np.nan)
    out = {"ntu_pixel_deg": [g[1], -g[5]], "our_incidence_deg_min_max": [round(float(np.nanmin(inc)), 1), round(float(np.nanmax(inc)), 1)]}
    for name, (vf, tf) in PRODUCTS.items():
        v = rd(vf, "velocity")[0] * 1000 / np.cos(np.deg2rad(inc))  # LOS -> vertical, mm/yr
        ok = land & (np.nan_to_num(rd(tf, "temporalCoherence")[0]) >= 0.7) & np.isfinite(v) & (flat >= 0)
        cnt = np.bincount(flat[ok], minlength=ntu.size).reshape(ntu.shape)
        tot = np.bincount(flat[ok], weights=v[ok], minlength=ntu.size).reshape(ntu.shape)
        ours = np.where(cnt > 0, tot / np.maximum(cnt, 1), np.nan)
        both = np.isfinite(ours) & np.isfinite(ntu)
        o, n = np.where(both, ours, np.nan), np.where(both, ntu, np.nan)
        od, nd = deramp(o, both, glon, glat), deramp(n, both, glon, glat)
        hl = locref(hgt, both)
        res = {"as_is": stats(o, n), "both_deramped": stats(od, nd), "both_local_1km": stats(locref(o, both), locref(n, both)),
               "local_1km_vs_local_height_spearman": {"ours": stats(locref(o, both), hl)["spearman"],
                                                      "ntu": stats(locref(n, both), hl)["spearman"]},
               "blocks": {}, "blocks_deramped": {}}
        for km in (0.5, 1, 2, 4):
            k = max(1, int(round(km * 1000 / 90)))
            R, C = (np.arange(ntu.shape[0]) // k)[:, None], (np.arange(ntu.shape[1]) // k)[None, :]
            bid = (R * (ntu.shape[1] // k + 1) + C)[both]
            m = np.bincount(bid)
            keep = m >= 5
            bo = np.bincount(bid, weights=o[both])[keep] / m[keep]
            bn = np.bincount(bid, weights=n[both])[keep] / m[keep]
            res["blocks"][f"{km}km"] = stats(bo, bn)
            res["blocks_deramped"][f"{km}km"] = stats(np.bincount(bid, weights=od[both])[keep] / m[keep],
                                                     np.bincount(bid, weights=nd[both])[keep] / m[keep])
        out[name] = res
    (MP / "NTU_COMPARISON.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
