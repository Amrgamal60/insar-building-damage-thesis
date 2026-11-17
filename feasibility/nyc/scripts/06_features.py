"""Checkpoint 2, second part (NYC_REPLICATION_PLAN.md §5, §9, §13 step 2). Builds, for every eligible cell at 250 m and
200 m, the static Baseline 1 features and the fold map, and, for every PLUTO release, the two time-varying features
(building count and median year built). Assigns each event its event PLUTO. No InSAR is read.

Static features follow the Alexandria pilot (scripts/07_pilot_models.py, build_cells):
- built_share_2015: GHS-BUILT-S 2015 (m² per 100 m pixel) averaged onto the cell grid, / 100 (%).
- old_share_1975: GHS-BUILT-S 1975 / 2015 cell means, clipped to 0-1 (no value where 2015 is 0).
- height_m: GHS-BUILT-H ANBH 2018 averaged with 0 as nodata, so the mean of non-zero pixels.
- elevation_m: FABDEM v1-2 cell mean; dist_coast_km: cell centre to the OSM coastline; x_km, y_km: cell centre.
Rasters are averaged onto the grid with rasterio's reproject (Resampling.average), as in Alexandria.
Time-varying features (§5, §9), per release and cell, from the lots whose release XCoord/YCoord point lies in the
study area: n_bldgs = sum of NumBldgs (the model uses log(1 + n_bldgs)); median_yearbuilt over lots with year built
> 0 (Baseline 2's age = event year - median_yearbuilt). A release's date is the newest date of the CSV data files in
its archive; each event's event PLUTO is the latest release dated strictly before the event date.
Event sample (§6, §8): event_sample_<res>m.csv adds to 04's event flags the event PLUTO and the case flags for the
domain and for the whole of NYC (dated on or after 2017-07-16, eligible cell, no earlier event in the cell).
Fold map (§9): 2 km blocks (floor of the cell-centre x and y over 2,000 m), StratifiedGroupKFold(5, shuffle, seed 42)
over all eligible cells in row-major order, label = the cell holds one of the 185 events; as Alexandria's fold_map.
Usage (from feasibility/nyc): ../../.venv/bin/python -I scripts/06_features.py raw out"""
import math
import re
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from sklearn.model_selection import StratifiedGroupKFold

RAW, OUT = Path(sys.argv[1]), Path(sys.argv[2]) / "checkpoint2"
CRS = "EPSG:32618"
RESOLUTIONS = [250, 200]
BLOCK_M, N_FOLDS, SEED, START = 2000, 5, 42, "2017-07-16"
GHSL = "GHS_{}_GLOBE_R2023A_54009_100_V1_0_R5_C12"
STATIC = ["built_share_2015", "old_share_1975", "height_m", "elevation_m", "dist_coast_km"]
COLS = {"bbl": "bbl", "numbldgs": "NumBldgs", "yearbuilt": "YearBuilt", "xcoord": "XCoord", "ycoord": "YCoord"}


def grid(area, res):  # as scripts/04_grid_domain.py
    minx, miny, maxx, maxy = area.bounds
    x0, y0 = math.floor(minx / res) * res, math.ceil(maxy / res) * res
    return from_origin(x0, y0, res, res), (math.ceil((y0 - miny) / res), math.ceil((maxx - x0) / res))


def rowcol(tr, res, x, y):
    return np.floor((tr.f - y) / res).astype(int), np.floor((x - tr.c) / res).astype(int)


def resample(paths, tr, shape, rs, src_nodata=None):  # as Alexandria's resample
    dst = np.full(shape, np.nan, "float32")
    for p in paths:
        with rasterio.open(p) as s:
            tmp = np.full(shape, np.nan, "float32")
            nd = s.nodata if src_nodata is None else src_nodata
            reproject(s.read(1).astype("float32"), tmp, src_transform=s.transform, src_crs=s.crs, src_nodata=nd,
                      dst_transform=tr, dst_crs=CRS, dst_nodata=np.nan, resampling=rs)
        dst = np.where(np.isnan(dst), tmp, dst)
    return dst


def ghsl(name):
    z = RAW / "ghsl" / f"{GHSL.format(name)}.zip"
    return f"/vsizip/{z.resolve()}/{GHSL.format(name)}.tif"


def coastline():
    import json
    els = json.loads((RAW / "osm/coastline.json").read_text())["elements"]
    lines = [shapely.LineString([(p["lon"], p["lat"]) for p in e["geometry"]]) for e in els if e["type"] == "way"]
    return gpd.GeoSeries(lines, crs=4326).to_crs(CRS).union_all()


def releases():
    """(name, zip path, CSV members, date) for PLUTO 15v1 and every archive release, oldest first."""
    zips = [RAW / "pluto_15v1/nyc_pluto_15v1.zip"] + sorted((RAW / "pluto_archive").glob("nyc_pluto_*.zip"))
    out = []
    for z in zips:
        name = re.sub(r"_csv$", "", z.stem.removeprefix("nyc_pluto_")).replace("_", ".")
        with zipfile.ZipFile(z) as f:
            members = [i for i in f.infolist() if i.filename.lower().endswith(".csv")]
        date = max(pd.Timestamp(*i.date_time) for i in members).normalize()
        out.append((name, z, [m.filename for m in members], date))
    return sorted(out, key=lambda r: r[3])


def load_release(z, members, area):
    """Lots with a release lot point inside the study area, in UTM 18N, and a load summary."""
    parts = []
    with zipfile.ZipFile(z) as f:
        for m in members:
            head = pd.read_csv(f.open(m), nrows=0, encoding="latin-1").columns
            use = {c: COLS[c.strip().lower()] for c in head if c.strip().lower() in COLS}
            parts.append(pd.read_csv(f.open(m), usecols=list(use), dtype=str, encoding="latin-1").rename(columns=use))
    lots = pd.concat(parts, ignore_index=True)
    missing = [c for c in COLS.values() if c not in lots]
    num = ["NumBldgs", "YearBuilt", "XCoord", "YCoord"]
    for c in num:
        lots[c] = pd.to_numeric(lots[c].str.strip(), errors="coerce") if c in lots else np.nan
    n_all = len(lots)
    lots = lots[(lots.XCoord > 0) & (lots.YCoord > 0)]
    x, y = Transformer.from_crs("EPSG:2263", CRS, always_xy=True).transform(lots.XCoord.values, lots.YCoord.values)
    lots = lots.assign(x=x, y=y)
    inside = shapely.contains_xy(area, lots.x.values, lots.y.values)
    info = {"lots": n_all, "with_point": len(lots), "in_area": int(inside.sum()), "missing_columns": ",".join(missing),
            "numbldgs_recorded": int(lots.NumBldgs[inside].notna().sum()),
            "yearbuilt_gt0": int((lots.YearBuilt[inside] > 0).sum())}
    return lots[inside].reset_index(drop=True), info


def release_cells(lots, cells, tr, res):
    r, c = rowcol(tr, res, lots.x.values, lots.y.values)
    d = pd.DataFrame({"row": r, "col": c, "nb": lots.NumBldgs.fillna(0).values, "yb": lots.YearBuilt.values})
    g = d.groupby(["row", "col"])
    agg = pd.DataFrame({"n_bldgs": g.nb.sum(), "n_lots": g.size(),
                        "median_yearbuilt": d[d.yb > 0].groupby(["row", "col"]).yb.median(),
                        "n_lots_yearbuilt": d[d.yb > 0].groupby(["row", "col"]).size()}).reset_index()
    out = cells[["row", "col"]].merge(agg, on=["row", "col"], how="left")
    out[["n_bldgs", "n_lots", "n_lots_yearbuilt"]] = out[["n_bldgs", "n_lots", "n_lots_yearbuilt"]].fillna(0)
    return out


def fold_map(cells, label, seed=SEED):  # as Alexandria's fold_map
    fold = np.full(len(cells), -1)
    for k, (_, te) in enumerate(StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
                                .split(cells, label.astype(int), cells.block)):
        fold[te] = k
    return dict(zip(cells.block, fold))


def main():
    boros = gpd.read_file(RAW / "boroughs/borough_boundaries.geojson").to_crs(CRS)
    area = boros.union_all()
    shore = coastline()
    ev = pd.read_csv(OUT.parent / "events_final.csv", dtype={"bbl": str, "bin": str})
    ex, ey = Transformer.from_crs("EPSG:4326", CRS, always_xy=True).transform(ev.geo_lon.values, ev.geo_lat.values)
    rel = releases()
    lots = {}
    rel_rows = []
    for name, z, members, date in rel:
        lots[name], info = load_release(z, members, area)
        rel_rows.append({"release": name, "file": str(z.relative_to(RAW)), "date": date.date(), "csv_files": len(members), **info})
        print(name, date.date(), info, flush=True)
    rel_df = pd.DataFrame(rel_rows)
    rel_df["usable"] = rel_df.missing_columns.eq("") & (rel_df.numbldgs_recorded > 0) & (rel_df.yearbuilt_gt0 > 0)
    rel_df.to_csv(OUT / "pluto_releases.csv", index=False)

    usable = rel_df[rel_df.usable].sort_values("date")
    dates = pd.to_datetime(usable.date).values
    t = pd.to_datetime(ev.date).values
    k = np.searchsorted(dates, t, side="left") - 1  # latest release dated strictly before the event
    ev_pluto = pd.DataFrame({"event_id": ev.event_id, "date": ev.date,
                             "event_pluto": np.where(k >= 0, usable.release.values[np.maximum(k, 0)], ""),
                             "event_pluto_date": np.where(k >= 0, usable.date.astype(str).values[np.maximum(k, 0)], "")})
    ev_pluto.to_csv(OUT / "event_pluto.csv", index=False)

    for res in RESOLUTIONS:
        tr, shape = grid(area, res)
        cells = pd.read_csv(OUT / f"cells_{res}m.csv")
        cells = cells[cells.eligible].reset_index(drop=True)
        r, c = cells.row.values, cells.col.values
        b15 = resample([ghsl("BUILT_S_E2015")], tr, shape, Resampling.average)[r, c]
        b75 = resample([ghsl("BUILT_S_E1975")], tr, shape, Resampling.average)[r, c]
        anbh = resample([ghsl("BUILT_H_ANBH_E2018")], tr, shape, Resampling.average, src_nodata=0)[r, c]
        dem = resample(sorted((RAW / "fabdem").glob("*_FABDEM_V1-2.tif")), tr, shape, Resampling.average)[r, c]
        f = cells[["row", "col", "x", "y", "borough", "landmass", "centre_on_land", "domain"]].copy()
        f["built_share_2015"] = b15 / 100.0
        f["old_share_1975"] = np.clip(b75 / np.where(b15 > 0, b15, np.nan), 0, 1)
        f["height_m"] = anbh
        f["elevation_m"] = dem
        f["dist_coast_km"] = shapely.distance(shapely.points(f.x.values, f.y.values), shore) / 1000.0
        f["x_km"], f["y_km"] = f.x / 1000.0, f.y / 1000.0
        f["block"] = (np.floor(f.x / BLOCK_M).astype(int).astype(str) + "_" + np.floor(f.y / BLOCK_M).astype(int).astype(str))
        er, ec = rowcol(tr, res, ex, ey)
        f["holds_event"] = pd.Series(list(zip(f.row, f.col))).isin(set(zip(er, ec))).values
        folds = fold_map(f, f.holds_event.values)
        f["fold"] = f.block.map(folds)
        f.to_csv(OUT / f"features_{res}m.csv", index=False)
        pd.DataFrame({"block": list(folds), "fold": list(folds.values())}).to_csv(OUT / f"folds_{res}m.csv", index=False)
        pc = pd.concat([release_cells(lots[name], f, tr, res).assign(release=name) for name in rel_df.release], ignore_index=True)
        pc[["release", "row", "col", "n_bldgs", "n_lots", "n_lots_yearbuilt", "median_yearbuilt"]].to_csv(
            OUT / f"pluto_cells_{res}m.csv", index=False)
        es = pd.read_csv(OUT / f"event_cells_{res}m.csv").merge(ev_pluto[["event_id", "event_pluto", "event_pluto_date"]], on="event_id")
        es["from_start"] = es.date >= START
        es["case_whole_nyc"] = es.from_start & es.eligible & es.no_earlier_event
        es["case_domain"] = es.case_whole_nyc & es.domain
        es.to_csv(OUT / f"event_sample_{res}m.csv", index=False)
        miss = f[STATIC].isna().sum()
        print(res, len(f), "eligible cells;", "missing:", miss.to_dict(), "| cells holding an event:", int(f.holds_event.sum()),
              "| blocks:", f.block.nunique(), "| cells per fold:", f.fold.value_counts().sort_index().tolist(),
              "| event cells per fold:", f[f.holds_event].fold.value_counts().sort_index().tolist(), flush=True)


if __name__ == "__main__":
    main()
