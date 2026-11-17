"""Feasibility audit of the Alexandria collapse inventory: sample sizes at each stage, positive cells at
candidate grid resolutions (with a half-cell shifted grid), distribution across districts, and the
observation dates / coverage of the available InSAR data. No model training happens here."""
import json
import math
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import xy as pixel_xy
from shapely.geometry import Polygon, box

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "data/inventory"
CRS = 32636
RESOLUTIONS = [100, 200, 250]
SEV_RANK = {"total": 3, "partial_structural": 2, "partial_element": 1}
CAT_RANK = {"A_intersection": 7, "A_street": 6, "B_street_review": 5, "B_street_overture": 4, "C_landmark": 3,
            "C_neighbourhood": 2, "B_street_ambiguous": 1, "D_district_only": 0, "E_unlocated": -1}
LOCATION_SETS = {
    "A (street/intersection, exact)": ["A_intersection", "A_street"],
    "A+B (adds flagged street matches)": ["A_intersection", "A_street", "B_street_review", "B_street_overture"],
    "A+B+C (adds landmark/neighbourhood; reference only)": ["A_intersection", "A_street", "B_street_review", "B_street_overture",
                                                            "C_landmark", "C_neighbourhood"],
}
WSF = ROOT / "data/interim/layers/wsf_evolution_year.tif"  # DLR WSF Evolution, first year detected as settled (1985-2015)
INCLUSION = {
    "all events": lambda e: np.ones(len(e), bool),
    "excl. external accidents (gas, fire, vehicle, factory)": lambda e: e.cause_group != "external_accident",
    "excl. accidents and building/demolition works": lambda e: ~e.cause_group.isin(["external_accident", "works_on_building", "works_adjacent"]),
    "structural only (total + partial_structural)": lambda e: e.severity_class.isin(["total", "partial_structural"]),
    "structural, excl. external accidents (≈ Mohamadi et al. 2020)": lambda e: e.severity_class.isin(["total", "partial_structural"])
                                                                            & (e.cause_group != "external_accident"),
    "total collapse only": lambda e: e.severity_class == "total",
}
QISM_EN = {"العطارين": "Al Attarin", "مينا البصل": "Mina El-Basal", "محرم بك": "Moharam Bek", "سيدي جابر": "Sidi Gaber",
           "الدخيلة": "El Dekheila", "أول المنتزة": "Awal El Montaza", "ثان المنتزة": "Thani El Montaza",
           "أول الرمل": "Awal El Raml", "ثان الرمل": "Thani El Raml", "الجمرك": "El Gomrok", "اللبان": "El Labban",
           "كرموز": "Karmouz", "باب شرقي": "Bab Sharqi", "المنشية": "El Manshiya", "أول العامرية": "Awal El Amreya",
           "غير محدد": "unspecified"}


def cell(x, y, res, off=0.0):
    return (math.floor((x - off) / res), math.floor((y - off) / res))


def cells_touched(geom, res, off=0.0):
    if geom is None or geom.is_empty:
        return set()
    if geom.geom_type == "Point":
        return {cell(geom.x, geom.y, res, off)}
    minx, miny, maxx, maxy = geom.bounds
    out = set()
    for i in range(math.floor((minx - off) / res), math.floor((maxx - off) / res) + 1):
        for j in range(math.floor((miny - off) / res), math.floor((maxy - off) / res) + 1):
            if geom.intersects(box(i * res + off, j * res + off, (i + 1) * res + off, (j + 1) * res + off)):
                out.add((i, j))
    return out


def md_table(df, floatfmt="{:.0f}"):
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(floatfmt.format(v) if isinstance(v, float) and not pd.isna(v) else ("" if pd.isna(v) else str(v)) for v in r) + " |")
    return "\n".join(lines)


def load():
    rec = pd.read_csv(INV / "inventory_records.csv")
    geo = pd.read_csv(INV / "geocode_auto.csv")
    feats = gpd.read_file(INV / "geocode_auto_matched_features.gpkg").set_index("record_id").geometry
    df = rec.merge(geo, on="record_id", how="left")
    df["matched_geom"] = df.record_id.map(feats)
    return df


def events_table(df):
    """One row per event: best location, most severe part, cause of the primary building."""
    rows = []
    for eid, g in df.groupby("event_id", sort=False):
        g = g.assign(_cat=g.loc_category.map(CAT_RANK), _sev=g.severity_class.map(SEV_RANK))
        best = g.sort_values("_cat", ascending=False).iloc[0]
        primary = g[g.building_ordinal.isin(["أول", "اول"])]
        primary = primary.iloc[0] if len(primary) else g.iloc[0]
        rows.append({"event_id": eid, "record_ids": ";".join(g.record_id), "n_buildings": len(g),
                     "event_date_start": best.event_date_start, "year": best.year, "qism": best.qism,
                     "address_base": best.address_base, "loc_category": best.loc_category,
                     "x_utm36": best.x_utm36, "y_utm36": best.y_utm36, "matched_extent_m": best.matched_extent_m,
                     "matched_geom": best.matched_geom,
                     "severity_class": g.sort_values("_sev", ascending=False).severity_class.iloc[0],
                     "cause_group": primary.cause_group,
                     "possible_duplicate": "; ".join(g.possible_duplicate.dropna().unique()) or None})
    return pd.DataFrame(rows)


def study_area():
    g = gpd.read_file(ROOT / "data/raw/admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(CRS)
    names = ["Al Attarin", "Mina Al-Basal", "Muharam Bik", "Sidi Gabir", "Al Dikhila", "Muntazah", "Al Raml",
             "Kesm than Al Raml", "Al Gumruk", "A L Labban", "Karmuz", "Bab Sharqi", "Al Manshiyya", "Al Amreia"]
    return g[g.shapeName.isin(names)].union_all()


def grid_counts(xy, res, area, off=0.0):
    """Count points per cell -> Series indexed by (i, j), restricted to points inside `area`."""
    pts = gpd.GeoSeries(gpd.points_from_xy(xy[:, 0], xy[:, 1]), crs=CRS)
    inside = pts.within(area).values
    ij = np.floor((xy[inside] - off) / res).astype(np.int64)
    return pd.Series(1, index=pd.MultiIndex.from_arrays([ij[:, 0], ij[:, 1]])).groupby(level=[0, 1]).sum()


def main():
    df = load()
    ev = events_table(df)
    area = study_area()
    report = []
    W = report.append

    # ---------------------------------------------------------------- 1. counts along the pipeline
    n_rows = len(df)
    n_events = ev.event_id.nunique()
    n_dup_flag = ev.possible_duplicate.notna().sum()
    loc = ev.loc_category.value_counts()
    W("## 1. Sample size at each stage\n")
    stage = pd.DataFrame([
        ("Workbook data rows (all Egypt)", 661),
        ("Rows whose governorate is Alexandria", n_rows),
        ("Unique events (multi-building incidents merged)", n_events),
        ("  of which flagged as possible duplicates of another event", n_dup_flag),
        ("Events located at street/intersection level, exact (A)", int(ev.loc_category.isin(LOCATION_SETS["A (street/intersection, exact)"]).sum())),
        ("Events located at street level incl. flagged matches (A+B)", int(ev.loc_category.isin(LOCATION_SETS["A+B (adds flagged street matches)"]).sum())),
        ("  of which the street comes from Overture place addresses, not OSM", int((ev.loc_category == "B_street_overture").sum())),
        ("Events located only to landmark/neighbourhood (C)", int(ev.loc_category.isin(["C_landmark", "C_neighbourhood"]).sum())),
        ("Events with street name matching several separate streets (B ambiguous, no coordinates)", int(loc.get("B_street_ambiguous", 0))),
        ("Events with district only / no location (D, E)", int(loc.get("D_district_only", 0) + loc.get("E_unlocated", 0))),
    ], columns=["Stage", "Count"])
    W(md_table(stage))
    W("\nRecord-level location categories: " + ", ".join(f"{k} {v}" for k, v in df.loc_category.value_counts().items()) + ".\n")

    # ---------------------------------------------------------------- 2. positive cells per resolution
    W("## 2. Positive cells at candidate grid resolutions\n")
    W("A cell is positive if an event's assigned point falls in it. *Shifted* uses a grid offset by half a cell in x and y. "
      "*Events in one cell* is the share of events whose whole matched OSM geometry (street segment, intersection, polygon) "
      "lies inside a single cell, i.e. the cell assignment does not depend on where along the street the building is.\n")
    rows = []
    for name, cats in LOCATION_SETS.items():
        e = ev[ev.loc_category.isin(cats)]
        for res in RESOLUTIONS:
            pos = {cell(x, y, res) for x, y in zip(e.x_utm36, e.y_utm36)}
            pos_s = {cell(x, y, res, res / 2) for x, y in zip(e.x_utm36, e.y_utm36)}
            touched = e.matched_geom.map(lambda g: len(cells_touched(g, res)))
            rows.append({"Location set": name, "Cell (m)": res, "Events": len(e), "Positive cells": len(pos),
                         "Positive cells (shifted)": len(pos_s),
                         "Events in one cell (%)": round(100 * (touched == 1).mean(), 1),
                         "Median cells touched": float(touched.median()),
                         "Events touching >4 cells (%)": round(100 * (touched > 4).mean(), 1)})
    W(md_table(pd.DataFrame(rows), floatfmt="{:g}"))

    W("\n### 2b. Effect of the event definition (location set A+B)\n")
    e_ab = ev[ev.loc_category.isin(LOCATION_SETS["A+B (adds flagged street matches)"])]
    rows = []
    for name, f in INCLUSION.items():
        e = e_ab[f(e_ab)]
        r = {"Event definition": name, "Events": len(e)}
        for res in RESOLUTIONS:
            r[f"Positive cells @{res} m"] = len({cell(x, y, res) for x, y in zip(e.x_utm36, e.y_utm36)})
        rows.append(r)
    W(md_table(pd.DataFrame(rows)))

    # ---------------------------------------------------------------- 3. distribution across districts and years
    W("\n## 3. Distribution across police districts (qism)\n")
    ev["located_AB"] = ev.loc_category.isin(LOCATION_SETS["A+B (adds flagged street matches)"])
    d = ev.groupby("qism").agg(events=("event_id", "count"), located_AB=("located_AB", "sum"))
    d["records"] = df.groupby("qism").record_id.count()
    d["pos_cells_200m"] = ev[ev.located_AB].groupby("qism").apply(
        lambda e: len({cell(x, y, 200) for x, y in zip(e.x_utm36, e.y_utm36)}), include_groups=False)
    d = d.fillna(0).astype(int).sort_values("events", ascending=False).reset_index()
    d.insert(1, "district", d.qism.map(QISM_EN))
    d["located %"] = (100 * d.located_AB / d.events).round(0).astype(int)
    W(md_table(d[["qism", "district", "records", "events", "located_AB", "located %", "pos_cells_200m"]]))
    y = pd.crosstab(ev.year, ev.located_AB.map({True: "located A+B", False: "not located"}))
    y["total"] = y.sum(axis=1)
    W("\nEvents by year:\n")
    W(md_table(y.reset_index()))

    # ---------------------------------------------------------------- 4. built-up background cells
    W("\n## 4. Built-up background (comparison cells)\n")
    b = duckdb.sql("select longitude, latitude from read_csv_auto('" + str(ROOT / "data/interim/google_buildings_v3_alex.csv") +
                   "') where confidence >= 0.70").df()
    bxy = np.c_[gpd.GeoSeries(gpd.points_from_xy(b.longitude, b.latitude), crs=4326).to_crs(CRS).x,
                gpd.GeoSeries(gpd.points_from_xy(b.longitude, b.latitude), crs=4326).to_crs(CRS).y]
    W(f"Study area = union of the 14 CAPMAS/geoBoundaries ADM2 polygons that match the inventory's districts "
      f"({area.area / 1e6:.0f} km²). Built-up = cell containing ≥1 Google Open Buildings v3 footprint centroid with confidence ≥ 0.70 "
      f"({len(b):,} footprints in the AOI bbox).\n")
    rows = []
    shz = pd.read_csv(ROOT / "data/raw/insar_vlm_shirzaei/LLIVS_IGS14_Alexandria.csv", header=None,
                      names=["lon", "lat", "incidence_deg", "vlm_cm_yr", "vlm_std_cm_yr"])
    sp = gpd.GeoSeries(gpd.points_from_xy(shz.lon, shz.lat), crs=4326).to_crs(CRS)
    sxy = np.c_[sp.x, sp.y]
    for res in RESOLUTIONS:
        bc = grid_counts(bxy, res, area)
        sc = grid_counts(sxy, res, area)
        built = set(bc.index)
        e = e_ab
        pos = {cell(x, y, res) for x, y in zip(e.x_utm36, e.y_utm36)}
        rows.append({"Cell (m)": res, "Built-up cells": len(built), "Positive cells (A+B)": len(pos),
                     "Positive cells that are built-up": len(pos & built),
                     "Positive : background ratio": f"1 : {round((len(built) - len(pos & built)) / max(len(pos & built), 1))}",
                     "Built-up cells with ≥1 InSAR point (%)": round(100 * len(built & set(sc.index)) / len(built), 1),
                     "Positive cells with ≥1 InSAR point (%)": round(100 * len(pos & set(sc.index)) / max(len(pos), 1), 1),
                     "Median InSAR points per covered built-up cell": float(sc.reindex(list(built & set(sc.index))).median())})
    W(md_table(pd.DataFrame(rows), floatfmt="{:g}"))

    W("\n### 4b. Background restricted to areas already settled by 2015\n")
    W("Google Open Buildings v3 is mapped from recent imagery, so the built-up mask may include cells developed after the "
      "2014–2016 inventory. *Settled* = the cell contains the centre of at least one 30 m WSF Evolution pixel first detected as "
      "settlement in 1985–2015 (DLR; input-data consistency score 6 of 6 across the city). Built-up cells without one are *not "
      "identified as settled by the historical filter*; that does not establish they were developed after 2015. The proposed "
      "comparison set is built-up **and** settled.\n")
    with rasterio.open(WSF) as s:
        yr = s.read(1)
        r_, c_ = np.nonzero((yr >= 1985) & (yr <= 2015))
        wx, wy = pixel_xy(s.transform, r_, c_)
        wp = gpd.GeoSeries(gpd.points_from_xy(wx, wy), crs=s.crs).to_crs(CRS)
    wxy = np.c_[wp.x, wp.y]
    rows = []
    for res in RESOLUTIONS:
        built = set(grid_counts(bxy, res, area).index)
        settled = set(map(tuple, np.unique(np.floor(wxy / res).astype(np.int64), axis=0)))
        sc = set(grid_counts(sxy, res, area).index)
        bs = built & settled
        pos = {cell(x, y, res) for x, y in zip(e_ab.x_utm36, e_ab.y_utm36)}
        rows.append({"Cell (m)": res, "Built-up cells": len(built), "Built-up and settled by 2015": len(bs),
                     "Built-up cells not identified as settled (%)": round(100 * (1 - len(bs) / len(built)), 1),
                     "Positive cells (A+B) in the set": len(pos & bs),
                     "Positive : background ratio": f"1 : {round((len(bs) - len(pos & bs)) / max(len(pos & bs), 1))}",
                     "Set cells with ≥1 InSAR point (%)": round(100 * len(bs & sc) / len(bs), 1)})
    W(md_table(pd.DataFrame(rows), floatfmt="{:g}"))

    # ---------------------------------------------------------------- 5. InSAR observation dates and coverage
    W("\n## 5. InSAR data available: dates and coverage\n")
    inside = sp.within(area).values
    v = shz[inside]
    W("**Shirzaei et al. vertical land motion (VT Figshare 10.7294/25864435, CC0).** "
      f"{len(shz):,} points in the file, {inside.sum():,} inside the study area. "
      f"VLM (IGS14) inside the study area: median {v.vlm_cm_yr.median() * 10:.1f} mm/yr, "
      f"5th–95th percentile {v.vlm_cm_yr.quantile(.05) * 10:.1f} to {v.vlm_cm_yr.quantile(.95) * 10:.1f} mm/yr; "
      f"median reported standard deviation {v.vlm_std_cm_yr.median() * 10:.1f} mm/yr. "
      f"Distinct coordinate pairs: {shz[['lon', 'lat']].drop_duplicates().shape[0]:,} (the file repeats some points). "
      "**The observation period is not stated in the dataset metadata or README**; it is a single mean velocity per point, "
      "not a time series. Until the period is confirmed (associated paper or corresponding author), it cannot be claimed "
      "to precede the 2014–2016 events.\n")
    rows = []
    ev_dates = pd.to_datetime(ev.event_date_start)
    for fid in ["065D_05935_131108", "131A_05957_110910"]:
        ep = pd.to_datetime(pd.read_csv(ROOT / f"data/raw/insar_licsar/{fid}/epochs.txt", header=None, dtype=str)[0])
        poly = np.loadtxt(ROOT / f"data/raw/insar_licsar/{fid}/metadata/{fid}-poly.txt")
        fp = gpd.GeoSeries([Polygon(poly)], crs=4326).to_crs(CRS).iloc[0]
        nifg = sum(1 for _ in open(ROOT / f"data/raw/insar_licsar/{fid}/interferograms.txt"))
        pre = ev_dates.map(lambda d: int((ep < d).sum()) if pd.notna(d) else 0)
        yrs = ev_dates.map(lambda d: (d - ep.min()).days / 365.25 if pd.notna(d) else np.nan)
        rows.append({"Frame": fid, "Pass": "descending" if "D_" in fid else "ascending",
                     "Epochs": len(ep), "First": ep.min().date(), "Last": ep.max().date(), "Interferograms": nifg,
                     "Study area covered (%)": round(100 * area.intersection(fp).area / area.area, 1),
                     "Events with 0 prior epochs": int((pre == 0).sum()),
                     "Events with ≥1 yr prior data": int((yrs >= 1).sum()),
                     "Events with ≥2 yr prior data": int((yrs >= 2).sum()),
                     "Median prior epochs per event": float(pre.median())})
    W(md_table(pd.DataFrame(rows), floatfmt="{:g}"))
    W("\nOnly the LiCSAR frame metadata was downloaded (E/N/U unit vectors, DEM heights, land mask, baselines, "
      "`vlos_eur`). `vlos_eur` is nearly constant over the city (≈ +14 mm/yr descending, ≈ −19 mm/yr ascending, "
      "σ ≈ 0.2 mm/yr): it is the plate-motion reference layer, not measured deformation. "
      "A deformation time series requires downloading the interferograms and running LiCSBAS (or HyP3/MintPy); "
      "none has been produced.\n")

    # ---------------------------------------------------------------- outputs
    ev.drop(columns=["matched_geom"]).to_csv(INV / "events.csv", index=False, encoding="utf-8-sig")
    gdf = gpd.GeoDataFrame(df.drop(columns=["matched_geom"]),
                           geometry=gpd.points_from_xy(df.x_utm36, df.y_utm36), crs=CRS)
    gdf[gdf.x_utm36.notna()].to_file(INV / "inventory_geocoded.gpkg", layer="records", driver="GPKG")
    df.drop(columns=["matched_geom"]).to_csv(INV / "inventory_geocoded.csv", index=False, encoding="utf-8-sig")

    q = []
    for r in df.itertuples():
        ev_ = json.loads(r.evidence) if isinstance(r.evidence, str) else {}
        sm = ev_.get("street_match", {})
        reasons = []
        if r.loc_category == "B_street_review":
            reasons.append(f"street match needs confirmation ({sm.get('how')}: {', '.join(sm.get('osm_names', []))})")
        if r.loc_category == "B_street_ambiguous":
            reasons.append(f"street name matches {sm.get('n_clusters')} separate streets in the district")
        if r.loc_category == "B_street_overture":
            os_ = ev_["overture_street"]
            reasons.append(f"street not in OSM, placed from {os_['n_places']} Overture place(s) ({os_['rule']}): "
                           + "; ".join(x["address"] for x in os_["places"][:3]))
        if ev_.get("overture_resolved"):
            reasons.append(ev_["overture_resolved"])
        if ev_.get("area_match", {}).get("kind") == "Overture address cluster":
            a = ev_["area_match"]
            reasons.append(f"neighbourhood '{a['name']}' not in OSM, placed from {a['n_places_main_cluster']} Overture addresses")
        for c in ev_.get("overture_street_candidates", []):
            if c.get("longer_names"):
                reasons.append(f"Overture has {c['n_places_longer_name']} place(s) on a longer name ({', '.join(c['longer_names'][:2])}): same street?")
            if c.get("n_places"):
                reasons.append(f"Overture has {c['n_places']} place(s) on '{c['street']}', not enough to place it")
        for c in ev_.get("overture_landmark_candidates", []):
            if c.get("distance_to_neighbourhood_m"):
                reasons.append(f"Overture landmark '{c['name']}' is {c['distance_to_neighbourhood_m'][0]} m from the named neighbourhood (not used)")
        if sm.get("conflict_article_never_mentions_address_street"):
            reasons.append("article text names a different street: " + ", ".join(sm.get("article_also_mentions", [])))
        if ev_.get("area_outside_reported_district"):
            a = ev_["area_outside_reported_district"][0]
            reasons.append(f"neighbourhood '{a['name']}' lies {a['distance_to_district_m']} m outside the reported district")
        if r.loc_category in ("C_landmark", "C_neighbourhood", "D_district_only") and ev_.get("unmatched_streets"):
            reasons.append("street not in OSM: " + ", ".join(u["name"] for u in ev_["unmatched_streets"]))
        if isinstance(r.possible_duplicate, str):
            reasons.append("possible duplicate: " + r.possible_duplicate)
        if isinstance(r.severity_flag, str):
            reasons.append(r.severity_flag)
        if r.source_is_retrospective:
            reasons.append(f"only source is a retrospective article ({int(r.pub_minus_event_days)} d after the event)")
        if reasons:
            q.append({"record_id": r.record_id, "event_id": r.event_id, "event_date": r.event_date_start, "qism": r.qism,
                      "address": r.address, "loc_category": r.loc_category, "lon": r.lon, "lat": r.lat,
                      "reasons": " | ".join(reasons), "links": r.links})
    pd.DataFrame(q).to_csv(INV / "review_queue.csv", index=False, encoding="utf-8-sig")
    W(f"\n_Review queue: {len(q)} records need a human decision → `review_queue.csv`._\n")

    (INV / "_audit_tables.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
