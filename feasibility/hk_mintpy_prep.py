"""Prepare the Hong Kong HyP3 interferograms for a MintPy time series (NYC plan §17 step 4).

Every product listed in hongkong/hyp3/products/MANIFEST.sha256 (size- and CRC-checked on download) is clipped, straight
from its zip, to one fixed 40 m grid: the bounding box of Hong Kong's 51,354 private buildings (building_info) plus 1 km,
snapped to the products' grid. No order data are used. The script stops if a product does not cover the whole window.
Per product it writes unw_phase, corr and conncomp (and the metadata .txt that MintPy reads) to
hongkong/mintpy/data/<product>/; the geometry layers (dem, lv_theta, lv_phi, water_mask) come from the first product only,
since all products share bursts and DEM. Existing clips are kept, so it can be rerun as products arrive.
It also reports whether the interferogram network is connected, and writes hongkong/mintpy/hk_T011.cfg.
Run from Alex/:  PROJ_DATA=~/miniforge3/envs/insar/share/proj ~/miniforge3/envs/insar/bin/python -I feasibility/hk_mintpy_prep.py
(PROJ_DATA is what conda activation would set; without it GDAL cannot open proj.db in this env.)
"""
import json
import math
import zipfile
from pathlib import Path

import pandas as pd
from osgeo import gdal
from pyproj import Transformer

gdal.UseExceptions()
ROOT = Path(__file__).resolve().parent / "hongkong"
PROD = ROOT / "hyp3" / "products"
WORK = ROOT / "mintpy"
DATA = WORK / "data"
IFG_LAYERS = ["unw_phase", "corr", "conncomp"]
GEOM_LAYERS = ["dem", "lv_theta", "lv_phi", "water_mask"]
MARGIN, PIX = 1000.0, 40.0
CO = ["COMPRESS=DEFLATE", "PREDICTOR=1", "TILED=YES"]

CFG = """# Hong Kong, Sentinel-1 track 11 ascending, HyP3 INSAR_ISCE_MULTI_BURST (10x2 looks, 40 m), 2015-06 to 2023-04.
# Written by feasibility/hk_mintpy_prep.py. Processing choices are fixed before any order data are linked to InSAR.
mintpy.load.processor        = hyp3
mintpy.load.unwFile          = {d}/*/*_unw_phase_clip.tif
mintpy.load.corFile          = {d}/*/*_corr_clip.tif
mintpy.load.connCompFile     = {d}/*/*_conncomp_clip.tif
mintpy.load.demFile          = {d}/*/*_dem_clip.tif
mintpy.load.incAngleFile     = {d}/*/*_lv_theta_clip.tif
mintpy.load.azAngleFile      = {d}/*/*_lv_phi_clip.tif
mintpy.load.waterMaskFile    = {d}/*/*_water_mask_clip.tif
mintpy.compute.cluster       = local
mintpy.compute.numWorker     = 8
mintpy.reference.yx          = auto
# Bridging, added 2026-10-17 before any order data were linked: in the first run (no correction) a typical pair split
# Hong Kong's land into ~13 unwrapped components (Central in the reference's component in 24% of pairs, the airport in
# 0%), so temporal coherence was high only near the reference. Bridging ties each component to the reference's across water.
mintpy.unwrapError.method    = bridging
mintpy.troposphericDelay.method = height_correlation
mintpy.deramp                = no
mintpy.topographicResidual   = yes
mintpy.save.hdfEos5          = no
mintpy.plot                  = no
"""


def window():
    """Fixed clip window in UTM 49N: private-building bounding box + MARGIN, snapped outward to the 40 m grid."""
    with zipfile.ZipFile(ROOT / "downloads" / "building_info" / "building_info.csv.zip") as z:
        bi = pd.read_csv(z.open(z.namelist()[0]), encoding="utf-8-sig", usecols=["LATITUDE", "LONGITUDE"])
    lon0, lon1, lat0, lat1 = bi.LONGITUDE.min(), bi.LONGITUDE.max(), bi.LATITUDE.min(), bi.LATITUDE.max()
    t = Transformer.from_crs("EPSG:4326", "EPSG:32649", always_xy=True)
    xs, ys = t.transform([lon0, lon1, lon0, lon1], [lat0, lat0, lat1, lat1])
    return (math.floor((min(xs) - MARGIN) / PIX) * PIX, math.ceil((max(ys) + MARGIN) / PIX) * PIX,
            math.ceil((max(xs) + MARGIN) / PIX) * PIX, math.floor((min(ys) - MARGIN) / PIX) * PIX)  # ulx uly lrx lry


def clip(src, dst, win):
    if dst.exists():
        return
    ds = gdal.Open(src)
    gt = ds.GetGeoTransform()
    x1, y1 = gt[0] + gt[1] * ds.RasterXSize, gt[3] + gt[5] * ds.RasterYSize
    assert (gt[1], gt[5]) == (PIX, -PIX) and gt[0] % PIX == 0 and gt[3] % PIX == 0, (src, gt)
    assert gt[0] <= win[0] and gt[3] >= win[1] and x1 >= win[2] and y1 <= win[3], f"window not covered: {src}"
    tmp = dst.with_name(dst.name + ".part.tif")
    gdal.Translate(str(tmp), ds, projWin=list(win), creationOptions=CO)
    tmp.replace(dst)


def main():
    win = window()
    names = sorted(line.split()[1] for line in (PROD / "MANIFEST.sha256").read_text().splitlines())
    DATA.mkdir(parents=True, exist_ok=True)
    edges = []
    for k, n in enumerate(names):
        stem = n[:-4]
        out = DATA / stem
        out.mkdir(exist_ok=True)
        with zipfile.ZipFile(PROD / n) as z:
            (out / f"{stem}.txt").write_bytes(z.read(f"{stem}/{stem}.txt"))
        for layer in IFG_LAYERS + (GEOM_LAYERS if k == 0 else []):
            clip(f"/vsizip/{PROD / n}/{stem}/{stem}_{layer}.tif", out / f"{stem}_{layer}_clip.tif", win)
        edges.append(tuple(stem.split("_")[4:6]))
    # connectivity of the date network (union-find)
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b in edges:
        parent[find(a)] = find(b)
    comps = {find(d) for d in parent}
    pairs = json.loads((ROOT / "hyp3" / "pairs.json").read_text())
    n_planned = len(pairs["pairs"]) if isinstance(pairs, dict) and "pairs" in pairs else len(pairs)
    shape = gdal.Open(str(next(DATA.glob("*/*_unw_phase_clip.tif"))))
    info = {"products": len(names), "planned_pairs": n_planned, "dates": len(parent), "network_components": len(comps),
            "window_utm49n_ulx_uly_lrx_lry": win, "grid_cols_rows": [shape.RasterXSize, shape.RasterYSize]}
    (WORK / "prep_info.json").write_text(json.dumps(info, indent=1) + "\n")
    (WORK / "hk_T011.cfg").write_text(CFG.format(d=DATA))
    print(json.dumps(info), flush=True)


if __name__ == "__main__":
    main()
