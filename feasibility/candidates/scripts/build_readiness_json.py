"""Assemble readiness.json from files already downloaded. Does not query the network.

Run:
  ~/miniforge3/envs/opera/bin/python -I feasibility/candidates/scripts/build_readiness_json.py
"""

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import Polygon

RAW = Path("/mnt/data/Master-projects/Alex_private/candidates/raw")
OUT = Path("/mnt/data/Master-projects/Alex/feasibility/candidates/readiness.json")


def load(path):
    return json.loads(Path(path).read_text())


def epoch(ms):
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, timezone.utc).date().isoformat()


def main():
    austin_stats = load(RAW / "austin_match_stats.json")
    austin_totals = load(RAW / "austin_totals.json")[0]
    view = load(RAW / "austin_3syk-w9eu_view.json")
    fields = [
        {"name": c.get("fieldName"), "type": c.get("dataTypeName"), "label": c.get("name")}
        for c in view["columns"]
    ]
    noto = load(RAW / "noto_gpkg_facts.json")
    shares = load(RAW / "opera_point_shares.json")
    sf = load(RAW / "houston" / "sf_keyword_superset.geojson")
    mf = load(RAW / "houston" / "mf_keyword_superset.geojson")
    sf_stats = load(RAW / "houston" / "sf_stats.json")["features"][0]["attributes"]
    sf_count = load(RAW / "houston" / "sf_kw_count.json")
    # layer totals were printed and the count file is the keyword count.
    # Total row counts are stored beside this script's inputs if present.
    sample_rows = []
    for layer, gj, datek, yeark, proj, desc in [
        ("SF", sf, "Sold_Date", "Sold_Date_YR", "F_PROJ_NAME", "PRMT_DESC"),
        ("MF", mf, "Sold_Date_SZ", "Sold_Date_SZ_YR", "F_PROJ_NAME", "USER_PRMT_DESC"),
    ]:
        for feat in gj["features"]:
            a = feat["attributes"]
            g = feat.get("geometry") or {}
            oid = a.get("OBJECTID_1") if layer == "SF" else a.get("OBJECTID")
            sample_rows.append({
                "permit_id": f"{layer}:{oid}",
                "layer": layer,
                "object_id": oid,
                "year": a.get(yeark),
                "sold_date": epoch(a.get(datek)),
                "fcc_desc": a.get("FCC__Desc"),
                "project_text": a.get(proj),
                "permit_desc": a.get(desc),
                "address": a.get("ADDRESS"),
                "longitude": g.get("x"),
                "latitude": g.get("y"),
            })
    Path("/mnt/data/Master-projects/Alex_private/candidates/samples/houston_a4_sample.json").write_text(
        json.dumps(sample_rows, indent=2)
    )
    years = Counter()
    for row in sample_rows:
        years[str(row["year"])] += 1
    after_2016 = 0
    after_2018 = 0
    for row in sample_rows:
        if row["sold_date"]:
            if row["sold_date"] >= "2016-07-01":
                after_2016 += 1
            if row["sold_date"] >= "2018-07-01":
                after_2018 += 1
        elif row["year"] and int(row["year"]) >= 2017:
            # Sold timestamp is null. The year field is 2022 or 2023 for these rows.
            after_2016 += 1
            if int(row["year"]) >= 2019:
                after_2018 += 1
    addrs = [(r["address"] or "").strip().upper() for r in sample_rows]
    nonempty = [a for a in addrs if a]
    addr_counts = Counter(nonempty)
    desc_counts = Counter((r["project_text"] or "").strip() for r in sample_rows)

    # Sentinel-1 SLC dates intersecting the inventory extent
    bbox_poly = Polygon([
        (136.670683417, 37.000347909),
        (137.360662401, 37.000347909),
        (137.360662401, 37.529975389),
        (136.670683417, 37.529975389),
    ])
    s1 = list(csv.DictReader(open(RAW / "sentinel1_noto_asf.csv")))
    passes = defaultdict(set)
    level_counts = Counter()
    n_intersect = 0
    for r in s1:
        level_counts[r["Processing Level"]] += 1
        if r["Processing Level"] != "SLC":
            continue
        try:
            poly = Polygon([
                (float(r["Near Start Lon"]), float(r["Near Start Lat"])),
                (float(r["Far Start Lon"]), float(r["Far Start Lat"])),
                (float(r["Far End Lon"]), float(r["Far End Lat"])),
                (float(r["Near End Lon"]), float(r["Near End Lat"])),
            ])
        except Exception:
            continue
        if not poly.intersects(bbox_poly):
            continue
        n_intersect += 1
        passes[(r["Path Number"], r["Ascending or Descending?"])].add(r["Start Time"][:10])
    s1_out = []
    for (path, direction), days in sorted(passes.items(), key=lambda kv: (kv[0][1], int(kv[0][0]))):
        s1_out.append({
            "relative_orbit": int(path),
            "direction": direction,
            "n_slc_scenes": None,
            "n_dates": len(days),
            "dates": sorted(days),
        })
    # fill scene counts
    scene_n = Counter()
    for r in s1:
        if r["Processing Level"] != "SLC":
            continue
        try:
            poly = Polygon([
                (float(r["Near Start Lon"]), float(r["Near Start Lat"])),
                (float(r["Far Start Lon"]), float(r["Far Start Lat"])),
                (float(r["Far End Lon"]), float(r["Far End Lat"])),
                (float(r["Near End Lon"]), float(r["Near End Lat"])),
            ])
        except Exception:
            continue
        if poly.intersects(bbox_poly):
            scene_n[(r["Path Number"], r["Ascending or Descending?"])] += 1
    for row in s1_out:
        row["n_slc_scenes"] = scene_n[(str(row["relative_orbit"]), row["direction"])]

    doc = {
        "access_date": "2026-10-26",
        "austin": {
            "dataset_id": "3syk-w9eu",
            "total_rows": int(austin_totals["n"]),
            "min_issue_date": austin_totals["min_issue"],
            "max_issue_date": austin_totals["max_issue"],
            "n_fields": len(fields),
            "fields": fields,
            "keyword_superset_n": austin_stats["superset_n"],
            "superset_failed_locked_regex": austin_stats["superset_failed_locked_regex"],
            "excluded": austin_stats["excluded"],
            "matched_n": austin_stats["matched_n"],
            "by_year": austin_stats["by_year"],
            "issued_on_or_after_2016_07_01": austin_stats["issued_on_or_after_2016_07_01"],
            "issued_on_or_after_2018_07_01": austin_stats["issued_on_or_after_2018_07_01"],
            "unique_addresses": austin_stats["unique_addresses"],
            "addresses_with_more_than_one_matched_permit": austin_stats["addresses_with_more_than_one_matched_permit"],
            "permits_with_blank_address": austin_stats["permits_with_blank_address"],
            "unique_tcad_id": austin_stats["unique_tcad_id"],
            "tcad_id_with_more_than_one_matched_permit": austin_stats["tcad_id_with_more_than_one_matched_permit"],
            "permits_with_blank_tcad_id": austin_stats["permits_with_blank_tcad_id"],
            "usable_coordinates": austin_stats["usable_coordinates"],
            "address_present_without_usable_coordinates": austin_stats["address_present_without_usable_coordinates"],
            "permit_class_mapped_counts": austin_stats["permit_class_mapped_counts"],
            "permittype_counts": austin_stats["permittype_counts"],
            "top30_descriptions": austin_stats["top30_descriptions"],
            "a4": load("/mnt/data/Master-projects/Alex/feasibility/candidates/austin_a4_classes.json"),
            "opera_point_shares": shares["austin"],
        },
        "houston": {
            "sf_layer_count": 57166,
            "mf_layer_count": 4389,
            "sf_keyword_superset_count": sf_count["count"],
            "mf_keyword_superset_count": 9,
            "sf_year_min": sf_stats["min_yr"],
            "sf_year_max": sf_stats["max_yr"],
            "sf_date_min": epoch(sf_stats["min_dt"]),
            "sf_date_max": epoch(sf_stats["max_dt"]),
            "matched_n": len(sample_rows),
            "by_year": dict(years),
            "issued_on_or_after_2016_07_01": after_2016,
            "issued_on_or_after_2018_07_01": after_2018,
            "unique_nonblank_addresses": len(addr_counts),
            "addresses_with_more_than_one_matched_permit": sum(1 for c in addr_counts.values() if c > 1),
            "blank_address": sum(1 for a in addrs if not a),
            "with_coordinates": sum(1 for r in sample_rows if r["longitude"] is not None),
            "description_counts": [{"description": d, "n": c} for d, c in desc_counts.most_common()],
            "a4": load("/mnt/data/Master-projects/Alex/feasibility/candidates/houston_a4_classes.json"),
            "opera_points_inside_one_granule_polygon": shares["houston_points_in_one_polygon"],
        },
        "noto": {
            "n_features": noto["n_features"],
            "n_invalid_geometries": noto["n_invalid_geometries"],
            "overall": noto["overall"],
            "by_municipality": noto["by_municipality_parsed_from_field"],
        },
        "sentinel1_slc": {
            "asf_rows_including_header_products": len(s1),
            "processing_level_counts_in_bbox_search": dict(level_counts),
            "slc_scenes_intersecting_inventory_extent": n_intersect,
            "passes": s1_out,
        },
    }
    # The two null-date Houston rows are years 2022 and 2023. Count them on both cut dates.
    # The loop above adds them to after_2016 when year>=2017, and to after_2018 only when year>=2019.
    # 2022 and 2023 are >= 2019, so both cuts include them. Check:
    null_years = [r["year"] for r in sample_rows if not r["sold_date"]]
    doc["houston"]["null_sold_date_years"] = null_years
    OUT.write_text(json.dumps(doc, indent=2))
    print("wrote", OUT)
    print("houston matched", doc["houston"]["matched_n"], "after2016", doc["houston"]["issued_on_or_after_2016_07_01"], "after2018", doc["houston"]["issued_on_or_after_2018_07_01"])
    print("null years", null_years)
    print("s1", json.dumps(s1_out))


if __name__ == "__main__":
    main()
