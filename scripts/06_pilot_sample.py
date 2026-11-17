"""Pilot target sample (no model): the event rule, review decisions for the records inside it, and the final
located events. Outputs go to data/pilot/.

Rule: most severe part total or partial_structural, and the recorded cause is not an external accident (gas,
fire, vehicle, factory) or active demolition/construction work on or next to the building (cause groups
external_accident, works_on_building, works_adjacent). Every other recorded cause is kept. The event's cause
is its first building's cause (events_table in 03).

Located = street level (A or B). Review-queue records inside this sample are settled from the source text
where it is clear; unresolved ones are excluded, never given forced coordinates. The one relocation (DA-R559)
is computed from the two OSM streets its article names, not typed in."""
import importlib.util
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import wkt
from shapely.geometry import Point
from shapely.ops import nearest_points

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "data/inventory"
OUT = ROOT / "data/pilot"
OUT.mkdir(parents=True, exist_ok=True)
CRS = 32636
STREET_LEVEL = ["A_intersection", "A_street", "B_street_review", "B_street_overture"]
CAT_RANK = {"A_intersection": 7, "A_street": 6, "B_street_review": 5, "B_street_overture": 4}
SEVERITY_KEEP = ["total", "partial_structural"]
CAUSE_DROP = ["external_accident", "works_on_building", "works_adjacent"]

HONORIFIC = "honorific variant; article names the street as the address does; one street of that name in the district"
DECISIONS = {  # record_id: (decision, reason). keep | exclude | relocate
    "DA-R049": ("keep", f"{HONORIFIC} (شارع سيدى على البدوى, next to Kom El Dikka)"),
    "DA-R059": ("keep", f"{HONORIFIC} (شارع مرتضى باشا, next to Gianaclis); only source is retrospective, date from the workbook"),
    "DA-R067": ("keep", f"{HONORIFIC} (شارع عرفان باشا)"),
    "DA-R103": ("keep", f"{HONORIFIC} (شارع الشيخ سيد درويش, Kom El Dikka)"),
    "DA-R283": ("keep", f"{HONORIFIC} (شارع نصر الدين)"),
    "DA-R494": ("keep", f"{HONORIFIC} (شارع الشيخ الجارحى)"),
    "DA-R495": ("keep", f"{HONORIFIC} (شارع الشيخ الجارحى)"),
    "DA-R496": ("keep", f"{HONORIFIC} (شارع الشيخ الجارحى)"),
    "DA-R559": ("relocate", "article: building 5 حارة خورشيد, opposite building 5 حارة بن الميسر; OSM شارع خورشيد باشا "
                            "and شارع ابن ميسر meet, so the point moves to their junction"),
    "DA-R570": ("exclude", "fuzzy match only: article شارع ابن العفيفى vs OSM حارة ابن العفيف (different name and street type)"),
    "DA-R616": ("exclude", "the only OSM شارع فرنسا lies 1.0 km outside El Manshiya next to El Labban; the article puts the "
                           "building in El Manshiya"),
    "DA-R318": ("exclude", "street missing from OSM; placed from one Overture place (a church), street extent unknown"),
    "DA-R192": ("keep", "not a duplicate: the article reports two buildings, on شارع الغابة and شارع الفواكه"),
    "DA-R193": ("keep", "not a duplicate: the article reports two buildings, on شارع الغابة and شارع الفواكه"),
    "DA-R391": ("keep", "not a duplicate: own article, building 43 شارع الكسائي, rear part, no injuries"),
    "DA-R392": ("keep", "not a duplicate: own article, building 10 شارع أبو فراس, staircase, 5 injured"),
    "DA-R312": ("keep", "not a duplicate: different street and date from EV075"),
}


def load_geocoder():
    spec = importlib.util.spec_from_file_location("geocode", ROOT / "scripts/02_geocode_osm.py")
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return g


def junction(g, name_a, name_b, qism):
    """Meeting point of two OSM streets in the district (midpoint of their nearest points)."""
    streets, _ = g.load_osm()
    district = g.load_districts()[qism].buffer(g.DISTRICT_BUFFER_M)
    a = streets[(streets.key == g.street_key(name_a)) & streets.intersects(district)].geometry.union_all()
    b = streets[(streets.key == g.street_key(name_b)) & streets.intersects(district)].geometry.union_all()
    pa, pb = nearest_points(a, b)
    return Point((pa.x + pb.x) / 2, (pa.y + pb.y) / 2), round(pa.distance(pb), 1)


def main():
    ev = pd.read_csv(INV / "events.csv")
    rec = pd.read_csv(INV / "inventory_geocoded.csv").set_index("record_id")
    feats = gpd.read_file(INV / "geocode_auto_matched_features.gpkg").set_index("record_id").geometry
    rule = ev.severity_class.isin(SEVERITY_KEEP) & ~ev.cause_group.isin(CAUSE_DROP)
    tgt = ev[rule].copy()
    queue = pd.read_csv(INV / "review_queue.csv").set_index("record_id")

    g = load_geocoder()
    rows, dec_rows = [], []
    for e in tgt.itertuples():
        ids = e.record_ids.split(";")
        cands = []
        for rid in ids:
            d, why = DECISIONS.get(rid, ("keep", None))
            if rid in queue.index and rid not in DECISIONS and rec.loc_category[rid] in STREET_LEVEL:
                raise SystemExit(f"{rid} is in the review queue but has no decision")
            if rid in DECISIONS:
                dec_rows.append({"record_id": rid, "event_id": e.event_id, "loc_category": rec.loc_category[rid],
                                 "queue_reasons": queue.reasons.get(rid), "decision": d, "reason": why})
            if rec.loc_category[rid] not in STREET_LEVEL or d == "exclude":
                continue
            if d == "relocate":
                p, gap = junction(g, "ش خورشيد باشا", "ش ابن ميسر", rec.qism[rid])
                cands.append((8, rid, p.x, p.y, p, f"relocated to OSM junction (gap {gap} m)"))
            else:
                geom = feats.get(rid)
                cands.append((CAT_RANK[rec.loc_category[rid]], rid, rec.x_utm36[rid], rec.y_utm36[rid], geom, d))
        if not cands:
            continue
        _, rid, x, y, geom, how = max(cands, key=lambda c: c[0])
        rows.append({"event_id": e.event_id, "record_ids": e.record_ids, "record_used": rid,
                     "event_date_start": e.event_date_start, "qism": e.qism, "severity_class": e.severity_class,
                     "cause_group": e.cause_group, "loc_category": rec.loc_category[rid], "location_note": how,
                     "x_utm36": round(x, 1), "y_utm36": round(y, 1),
                     "geometry_wkt": geom.wkt if geom is not None else Point(x, y).wkt})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "target_events.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(dec_rows).drop_duplicates("record_id").to_csv(OUT / "review_decisions.csv", index=False, encoding="utf-8-sig")

    located = tgt[tgt.loc_category.isin(STREET_LEVEL)]
    counts = pd.DataFrame([
        ("Events in the inventory", len(ev)),
        ("Most severe part total or partial structural", int(ev.severity_class.isin(SEVERITY_KEEP).sum())),
        ("… and cause not an external accident or active works (the target rule)", len(tgt)),
        ("… located at street level (A or B)", len(located)),
        ("… after the review decisions (final sample)", len(out)),
    ], columns=["Stage", "Events"])
    counts.to_csv(OUT / "sample_counts.csv", index=False)
    print(counts.to_string(index=False))
    print("dropped by cause:", ev[ev.severity_class.isin(SEVERITY_KEEP)].cause_group.value_counts().reindex(CAUSE_DROP).to_dict())
    print("target not located:", tgt.loc_category[~tgt.loc_category.isin(STREET_LEVEL)].value_counts().to_dict())
    print("final by category:", out.loc_category.value_counts().to_dict(), "| severity:", out.severity_class.value_counts().to_dict())
    print(json.dumps(pd.DataFrame(dec_rows).drop_duplicates("record_id").decision.value_counts().to_dict()))


if __name__ == "__main__":
    main()
