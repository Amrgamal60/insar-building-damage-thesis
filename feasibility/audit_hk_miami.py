"""Audit numbers for Hong Kong and Miami-Dade (NYC plan §17 step 2). Reads only feasibility/<city>/downloads.

For each city: labels (count, dates, coordinates), building layers and how labels link to them, InSAR type,
years of InSAR before the labels, and label-InSAR overlap. Miami also gets the §17 go/no-go check:
at least 100 unsafe-structure cases opened since 2017 inside InSAR coverage.
Writes <city>/audit/audit_numbers.json. No model, no outcome-InSAR association is computed here.

Run from Alex/:  OMP_NUM_THREADS=1 .venv/bin/python -I feasibility/audit_hk_miami.py [hongkong|miami]
"""
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parent
WINDOW_START = "2023-05-01"  # HK order datasets cover orders issued after 1 May 2023


def pages(folder):
    """Rows of a paged ArcGIS download as a DataFrame with lon/lat (point) or centroid lon/lat (polygon)."""
    rows = []
    for p in sorted((folder / "pages").glob("p[0-9]*.geojson")):
        for f in json.loads(p.read_text(encoding="utf-8"))["features"]:
            r = dict(f["properties"])
            g = f.get("geometry")
            if g and g["type"] == "Point":
                r["lon"], r["lat"] = g["coordinates"][:2]
            elif g and g["type"] in ("Polygon", "MultiPolygon"):
                ring = np.array(g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0])
                r["lon"], r["lat"] = ring[:, 0].mean(), ring[:, 1].mean()
            rows.append(r)
    return pd.DataFrame(rows)


def raster_valid(tif, lon, lat, k=0):
    """Share of points with a finite pixel within k pixels (NaN marks no data in these MATLAB GeoTIFFs)."""
    with rasterio.open(tif) as r:
        a = r.read(1)
        ok = []
        for x, y in zip(lon, lat):
            i, j = r.index(x, y)
            if not (0 <= i < a.shape[0] and 0 <= j < a.shape[1]):
                ok.append(False)
                continue
            w = a[max(i - k, 0):i + k + 1, max(j - k, 0):j + k + 1]
            ok.append(bool(np.isfinite(w).any()))
        info = {"crs": str(r.crs), "pixel_deg": r.res[0], "bounds": list(r.bounds),
                "valid_pixels": int(np.isfinite(a).sum()), "pixels": int(a.size)}
    return np.array(ok), info


def ntu_tif(zpath, member, scratch):
    out = scratch / member
    if not out.exists():
        scratch.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zpath) as z:
            out.write_bytes(z.read(member))
    return out


def hongkong():
    D = ROOT / "hongkong" / "downloads"
    s26 = pd.read_csv(D / "s26_orders" / "BDS26.csv")
    s26a = pd.read_csv(D / "s26a_orders" / "BDS26A.csv")
    cws = pd.read_csv(D / "s26_cws" / "BDS26_CWS.csv")
    cwsa = pd.read_csv(D / "s26a_cws" / "BDS26A_CWS.csv")
    with zipfile.ZipFile(D / "building_info" / "building_info.csv.zip") as z:
        bi = pd.read_csv(z.open(z.namelist()[0]), encoding="utf-8-sig")
    bi = bi.rename(columns={"NSEARCH1_E": "block", "NSEARCH3_E": "op_date", "NSEARCH4_E": "type",
                            "NSEARCH5_E": "use", "SEARCH1_E": "district"})
    md = pd.read_csv(D / "monthly_digests" / "Md22.csv", encoding="utf-8-sig")
    md["ym"] = md.Year.astype(int).astype(str) + "-" + md.Month.astype(int).map("{:02d}".format)
    since = md[md.ym >= WINDOW_START[:7]]
    n = {}
    for name, df, col in [("s26", s26, "Cum_s26Orders_Issued_EN"), ("s26a", s26a, "Cum_s26AOrders_Issued_EN"),
                          ("s26_cws", cws, "Cum_s26Orders_CW_WD_SS_EN"), ("s26a_cws", cwsa, "Cum_s26AOrders_CW_WD_SS_EN")]:
        n[name] = {"buildings": len(df), "unique_blocks": int(df.BLOCK_ID_EN.nunique()), "orders": int(df[col].sum()),
                   "with_lat_lon": int(df[["Latitude", "Longitude"]].notna().all(axis=1).sum()),
                   "last_update": sorted(df.LastUpdate.str[:10].unique().tolist()),
                   "block_types": df.Block_TypeEN.value_counts().to_dict(),
                   "blocks_in_building_info": int(df.BLOCK_ID_EN.astype(str).isin(bi.block.astype(str)).sum())}
    n["s26_and_s26a_buildings"] = int(len(set(s26.BLOCK_ID_EN) & set(s26a.BLOCK_ID_EN)))
    n["monthly_digest_since_2023_05"] = {"months": [since.ym.min(), since.ym.max()],
                                         "building_repair_orders": int(since["Building repair"].sum()),
                                         "investigation_orders": int(since["Investigation on buildings Defects"].sum())}
    op = pd.to_datetime(bi.op_date, errors="coerce")
    bi["op_year"] = op.dt.year
    lab = bi.block.astype(str).isin(s26.BLOCK_ID_EN.astype(str))
    n["building_info"] = {"rows": len(bi), "unique_blocks": int(bi.block.nunique()),
                          "with_op_date": int(op.notna().sum()), "op_date_range": [str(op.min().date()), str(op.max().date())],
                          "types": bi.type.value_counts().to_dict(), "uses": bi.use.value_counts().to_dict(),
                          "median_op_year_all": float(bi.op_year.median()),
                          "median_op_year_s26": float(bi.op_year[lab].median()),
                          "s26_share_of_buildings": float(lab.mean()),
                          "built_after_2015": int((bi.op_year >= 2016).sum())}
    n["s26_by_district"] = bi[lab].district.value_counts().to_dict()
    tif = ntu_tif(D / "ntu_insar" / "HongKong_TA011.zip", "HongKong_TA011_velocity_InSAR.tif",
                  ROOT / "hongkong" / "work" / "ntu")
    ins = {}
    for k in (0, 1, 2):
        ok26, info = raster_valid(tif, s26.Longitude, s26.Latitude, k)
        ok26a, _ = raster_valid(tif, s26a.Longitude, s26a.Latitude, k)
        okbi, _ = raster_valid(tif, bi.LONGITUDE, bi.LATITUDE, k)
        ins[f"within_{k}_px"] = {"s26": int(ok26.sum()), "s26a": int(ok26a.sum()), "all_buildings": int(okbi.sum())}
    s1 = pd.read_csv(D / "s1_listing" / "asf_s1_iw_slc_kowloon.csv")
    s1["date"] = s1["Acquisition Date"].str[:10]
    tracks = {f"{int(p)}{d[0]}": {"scenes": int(len(g)), "first": g.date.min(), "last": g.date.max(),
                                  "before_window": int((g.date < WINDOW_START).sum())}
              for (p, d), g in s1.groupby(["Path Number", "Ascending or Descending?"])}
    n["insar"] = {"ntu_tay2022": {"type": "static velocity map (no time series), ~90 m, vertical, relative to a reference point",
                                  **info, **ins},
                  "sentinel1_scenes_kowloon": tracks}
    n["dates"] = ("No issue date per order or building: counts are cumulative from 1 May 2023 to LastUpdate. "
                  "No monthly back copies found (data.gov.hk historical archive lists no S26/S26A files; Wayback has none).")
    return n


def miami():
    D = ROOT / "miami" / "downloads"
    v = pages(D / "building_violations")
    v["open"] = pd.to_datetime(v.OPEN_DATE, unit="ms", utc=True).dt.tz_convert("America/New_York").dt.date
    v["closed"] = pd.to_datetime(v.CLOSED_DATE, unit="ms", utc=True).dt.tz_convert("America/New_York").dt.date
    v["muni_code"] = v.FOLIO.astype(str).str[:2]
    u = v[v.CASE_TYPE == "Unsafe Structure"].copy()
    u["year"] = pd.to_datetime(u.open).dt.year
    u17 = u[(u.year >= 2017) & u.lon.notna()]
    n = {"violations": {"rows": len(v), "case_types": v.CASE_TYPE.value_counts().to_dict()},
         "unsafe": {"cases": len(u), "unique_folios": int(u.FOLIO.nunique()), "with_point": int(u.lon.notna().sum()),
                    "with_open_date": int(u.open.notna().sum()), "open_date_range": [str(u.open.min()), str(u.open.max())],
                    "still_open": int(u.closed.isna().sum()), "by_year": u.year.value_counts().sort_index().to_dict(),
                    "since_2017_with_point": len(u17),
                    "folio_prefix_since_2017": u17.muni_code.value_counts().head(12).to_dict()}}
    # OPERA DISP-S1 frame footprint from the CMR listing (polygons are "lat lon lat lon ...")
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    cmr = json.loads((D / "opera_cmr_listing" / "granules_F12638_bbox.json").read_text())["feed"]["entry"]
    polys, dates, frames = [], set(), set()
    for g in cmr:
        frames.add(re.search(r"_F(\d+)_", g["title"]).group(1))
        sec = re.findall(r"_(\d{8})T\d{6}Z", g["title"])
        dates.update(sec[:2])
        for ring in g.get("polygons", []):
            c = np.array(ring[0].split(), float).reshape(-1, 2)
            polys.append(Polygon(c[:, ::-1]))
    foot = unary_union(polys)
    inside = np.array([foot.contains(Point(x, y)) for x, y in zip(u17.lon, u17.lat)])
    d = sorted(dates)
    n["insar_opera"] = {"frames": sorted(frames), "granules": len(cmr), "dates": [d[0], d[-1]], "distinct_dates": len(d),
                        "dates_before_2017": sum(x < "20170101" for x in d),
                        "unsafe_since_2017_inside_frame": int(inside.sum()),
                        "note": "footprint only; valid (coherent) pixels at the cases need the data (Earthdata login)"}
    # Barrier-island time series (Zenodo): point locations and epochs
    zen = {}
    zpts = []
    for f in sorted((D / "zenodo_barrier_insar").glob("*.xlsx")):
        x = pd.read_excel(f, nrows=None)
        cols = [str(c) for c in x.columns]
        lonc = next((c for c in x.columns if re.search(r"(?i)^(lon|xcoord)", str(c))), None)
        latc = next((c for c in x.columns if re.search(r"(?i)^(lat|ycoord)", str(c))), None)
        epochs = [c for c in cols if re.fullmatch(r"D\d{8}", c)]
        zen[f.name] = {"rows": len(x), "columns_first": cols[:12], "n_columns": len(cols), "lon_col": str(lonc),
                       "lat_col": str(latc), "epochs": len(epochs), "first_epoch": epochs[0] if epochs else None,
                       "last_epoch": epochs[-1] if epochs else None}
        if lonc is not None and latc is not None:
            zpts.append(x[[lonc, latc]].to_numpy(float))
    if zpts:
        from shapely.geometry import MultiPoint
        pts = np.vstack(zpts)
        hull = MultiPoint(pts[np.isfinite(pts).all(axis=1)]).convex_hull
        zen["unsafe_since_2017_inside_hull"] = int(sum(hull.contains(Point(x, y)) for x, y in zip(u17.lon, u17.lat)))
        zen["unsafe_all_years_inside_hull"] = int(sum(hull.contains(Point(x, y)) for x, y in zip(u.lon.dropna(), u.lat.dropna())))
        from scipy.spatial import cKDTree  # metres via a local equirectangular projection (25.8 N)
        xy = lambda lo, la: np.c_[np.asarray(lo) * 100_300.0, np.asarray(la) * 110_800.0]
        dist, _ = cKDTree(xy(pts[:, 0], pts[:, 1])).query(xy(u17.lon, u17.lat))
        zen["unsafe_since_2017_within_50m_of_point"] = int((dist <= 50).sum())
        zen["unsafe_since_2017_within_100m_of_point"] = int((dist <= 100).sum())
        zen["points_total"] = int(len(pts))
    n["insar_zenodo_barrier"] = zen
    tif = ntu_tif(D / "ntu_insar" / "Miami_TA048.zip", "Miami_TA048_velocity_InSAR.tif", ROOT / "miami" / "work" / "ntu")
    ok0, info = raster_valid(tif, u17.lon, u17.lat, 0)
    ok1, _ = raster_valid(tif, u17.lon, u17.lat, 1)
    n["insar_ntu_tay2022"] = {"type": "static velocity map", **info, "unsafe_since_2017_valid_0px": int(ok0.sum()),
                              "unsafe_since_2017_valid_1px": int(ok1.sum())}
    par = pages(D / "parcels") if (D / "parcels" / "COMPLETE.json").exists() else None
    fp = pages(D / "footprints_folio") if (D / "footprints_folio" / "COMPLETE.json").exists() else None
    if par is not None:
        yb = pd.to_numeric(par.YEAR_BUILT, errors="coerce")
        n["parcels"] = {"rows": len(par), "with_year_built": int((yb > 1800).sum()),
                        "unsafe_since_2017_folio_matched": int(u17.FOLIO.astype(str).isin(par.FOLIO.astype(str)).sum())}
    if fp is not None:
        n["footprints"] = {"rows": len(fp), "with_folio": int(fp.FOLIO.notna().sum()),
                           "unsafe_since_2017_folio_matched": int(u17.FOLIO.astype(str).isin(fp.FOLIO.astype(str)).sum())}
    n["go_no_go"] = {"rule": ">=100 unsafe-structure cases opened since 2017 inside InSAR coverage (plan §17 step 2)",
                     "opera_frame_count": int(inside.sum()), "passes_on_footprint": bool(inside.sum() >= 100)}
    return n


def main():
    for city in sys.argv[1:] or ["hongkong", "miami"]:
        out = {"hongkong": hongkong, "miami": miami}[city]()
        path = ROOT / city / "audit" / "audit_numbers.json"
        path.write_text(json.dumps(out, indent=2, default=str) + "\n")
        print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
