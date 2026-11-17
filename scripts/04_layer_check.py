"""Descriptive check of candidate predictor layers on the 200 m study grid (no model training).

For each layer: coverage of built-up cells, median value in positive vs background built-up cells, and the
univariate rank separation (Mann-Whitney AUC; 0.5 = no difference). The AUC is a descriptive statistic on
the whole city, not a validated model score: positives cluster in the historic core, so any layer that
tracks "old core vs rest" will separate well here without adding information beyond location.
Two backgrounds: all built-up cells, and built-up cells already settled by 2015 (WSF Evolution, as in
03_audit_report.py section 4b)."""
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.transform import xy as pixel_xy
from rasterio.warp import reproject
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parents[1]
L = ROOT / "data/interim/layers"
CRS, RES = "EPSG:32636", 200
DISTRICTS = ["Al Attarin", "Mina Al-Basal", "Muharam Bik", "Sidi Gabir", "Al Dikhila", "Muntazah", "Al Raml",
             "Kesm than Al Raml", "Al Gumruk", "A L Labban", "Karmuz", "Bab Sharqi", "Al Manshiyya", "Al Amreia"]

# name -> (file, resampling, src_nodata, transform-before, description)
LAYERS = {
    "WSF first settled year (min)": ("wsf_evolution_year", Resampling.min, 0, None, "WSF Evolution 1985-2015, 30 m"),
    "WSF median settled year": ("wsf_evolution_year", Resampling.med, 0, None, "WSF Evolution 1985-2015, 30 m"),
    "WSF IDC score (mode)": ("wsf_idc_score", Resampling.mode, 0, None, "Landsat input quality 1-6"),
    "GHS-BUILT-S 1975 (m² per 100 m px)": ("ghs_built_s_1975", Resampling.average, None, None, "GHSL R2023A"),
    "GHS-BUILT-S 2015 (m² per 100 m px)": ("ghs_built_s_2015", Resampling.average, None, None, "GHSL R2023A"),
    "GHS-BUILT-S growth 1975-2015 (m²)": ("growth", Resampling.average, None, None, "2015 minus 1975"),
    "GHS-BUILT-H ANBH 2018 (m)": ("ghs_built_h_anbh_2018", Resampling.average, 0, None, "net building height"),
    "GHS-AGE epoch class (mode, 1 = <1975)": ("ghs_age_1975_2020", Resampling.mode, 0, None, "GHSL R2025A, 1-10"),
    "GSW ever water 1984-2021 (share of cell)": ("gsw_occurrence", Resampling.average, None, "binary_pos", "JRC GSW v1.4"),
    "GSW water lost 1984-2021 (share of cell)": ("gsw_transitions", Resampling.average, None, "lost", "classes 3, 6"),
    "Nile delta VLM 2014-2023 (cm/yr)": ("nile_vlm_ohenhen2025", Resampling.bilinear, None, None, "Ohenhen 2025, ~900 m"),
}


def grid(area):
    minx, miny, maxx, maxy = area.bounds
    x0, y0 = np.floor(minx / RES) * RES, np.ceil(maxy / RES) * RES
    w, h = int(np.ceil((maxx - x0) / RES)), int(np.ceil((y0 - miny) / RES))
    return from_origin(x0, y0, RES, RES), (h, w)


def to_grid(name, rs, nd, pre, tr, shape):
    if name == "growth":
        a = to_grid("ghs_built_s_2015", rs, nd, None, tr, shape)
        b = to_grid("ghs_built_s_1975", rs, nd, None, tr, shape)
        return a - b
    with rasterio.open(L / f"{name}.tif") as s:
        src = s.read(1).astype("float32")
        if pre == "binary_pos":
            src = (src > 0).astype("float32")
        elif pre == "lost":
            src = np.isin(src, [3, 6]).astype("float32")
        dst = np.full(shape, np.nan, "float32")
        reproject(src, dst, src_transform=s.transform, src_crs=s.crs, src_nodata=nd if nd is not None else s.nodata,
                  dst_transform=tr, dst_crs=CRS, dst_nodata=np.nan, resampling=rs)
    return dst


def main():
    adm = gpd.read_file(ROOT / "data/raw/admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(CRS)
    area = adm[adm.shapeName.isin(DISTRICTS)].union_all()
    tr, shape = grid(area)
    ij = lambda x, y: (np.floor((tr.f - y) / RES).astype(int), np.floor((x - tr.c) / RES).astype(int))

    b = duckdb.sql("select longitude, latitude from read_csv_auto('" + str(ROOT / "data/interim/google_buildings_v3_alex.csv") +
                   "') where confidence >= 0.70").df()
    bp = gpd.GeoSeries(gpd.points_from_xy(b.longitude, b.latitude), crs=4326).to_crs(CRS)
    inside = bp.within(area).values
    r, c = ij(bp.x.values[inside], bp.y.values[inside])
    ok = (r >= 0) & (r < shape[0]) & (c >= 0) & (c < shape[1])
    built = np.zeros(shape, bool)
    built[r[ok], c[ok]] = True

    ev = pd.read_csv(ROOT / "data/inventory/events.csv")
    ev = ev[ev.loc_category.isin(["A_intersection", "A_street", "B_street_review", "B_street_overture"])]
    pr, pc = ij(ev.x_utm36.values, ev.y_utm36.values)
    pos = np.zeros(shape, bool)
    pos[pr, pc] = True
    bg = built & ~pos
    with rasterio.open(L / "wsf_evolution_year.tif") as s:
        yr = s.read(1)
        r_, c_ = np.nonzero((yr >= 1985) & (yr <= 2015))
        wx, wy = pixel_xy(s.transform, r_, c_)
        wp = gpd.GeoSeries(gpd.points_from_xy(wx, wy), crs=s.crs).to_crs(CRS)
    wr, wc = ij(wp.x.values, wp.y.values)
    ok = (wr >= 0) & (wr < shape[0]) & (wc >= 0) & (wc < shape[1])
    settled = np.zeros(shape, bool)
    settled[wr[ok], wc[ok]] = True
    bg_s = bg & settled
    print(f"200 m grid {shape}, built-up cells {built.sum()}, positive {pos.sum()} (built-up {(pos & built).sum()}, "
          f"settled {(pos & built & settled).sum()}), background {bg.sum()}, settled background {bg_s.sum()}")

    shz = pd.read_csv(ROOT / "data/raw/insar_vlm_shirzaei/LLIVS_IGS14_Alexandria.csv", header=None,
                      names=["lon", "lat", "inc", "vlm", "std"]).drop_duplicates(["lon", "lat"])
    sp = gpd.GeoSeries(gpd.points_from_xy(shz.lon, shz.lat), crs=4326).to_crs(CRS)
    sr, sc = ij(sp.x.values, sp.y.values)
    ok = (sr >= 0) & (sr < shape[0]) & (sc >= 0) & (sc < shape[1])
    sm = pd.DataFrame({"r": sr[ok], "c": sc[ok], "v": shz.vlm.values[ok]}).groupby(["r", "c"]).v.mean()
    shz_grid = np.full(shape, np.nan, "float32")
    shz_grid[sm.index.get_level_values(0), sm.index.get_level_values(1)] = sm.values

    rows = []
    layers = dict(LAYERS)
    layers["Shirzaei VLM mean (cm/yr)"] = (None, None, None, None, "period undocumented")
    for label, (name, rs, nd, pre, desc) in layers.items():
        g = shz_grid if name is None else to_grid(name, rs, nd, pre, tr, shape)
        vp, vb, vs = g[pos & built], g[bg], g[bg_s]
        vp, vb, vs = vp[np.isfinite(vp)], vb[np.isfinite(vb)], vs[np.isfinite(vs)]
        cov = np.isfinite(g[built]).mean() * 100
        auc = lambda a, b: round(float(mannwhitneyu(a, b).statistic / (len(a) * len(b))), 2) if len(a) and len(b) else np.nan
        med = lambda a: round(float(np.median(a)), 2) if len(a) else None
        rows.append({"Layer": label, "Source": desc, "Built-up cells covered (%)": round(cov, 1),
                     "Positive cells with value": len(vp), "Median, positive": med(vp), "Median, background": med(vb),
                     "Univariate AUC": auc(vp, vb), "Median, settled background": med(vs),
                     "AUC, settled background": auc(vp, vs)})
    t = pd.DataFrame(rows)
    t.to_csv(ROOT / "data/interim/layer_check_200m.csv", index=False)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
