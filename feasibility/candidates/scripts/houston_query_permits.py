"""Query City of Houston GIS building-permit layers. Metadata and keyword rows only.

Layers (ArcGIS hosted, org NummVBqZSIJKUeVR):
  SF_2015_to_2021 layer 1
  MF_2015_to_2021 layer 0

Writes JSON under Alex_private/candidates/raw/houston/.
Does not download the full tables. Keyword WHERE is a LIKE superset of the
locked regex in keyword_protocol.md. Exact regex is applied in
filter_keyword_matches.py.

Run:
  ~/miniforge3/envs/opera/bin/python -I feasibility/candidates/scripts/houston_query_permits.py
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("/mnt/data/Master-projects/Alex_private/candidates/raw/houston")
SF = "https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/SF_2015_to_2021/FeatureServer/1/query"
MF = "https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/MF_2015_to_2021/FeatureServer/0/query"
LIKES = [
    "FOUNDATION", "UNDERPIN", "SLAB REPAIR", "LEVELING", "LEVELLING",
    "HOUSE LEVEL", "MUDJACK", "RE-LEVEL", "HELICAL", "PIER", "SHIM",
]
SF_FIELDS = ["F_PROJ_NAME", "PRMT_DESC", "FCC__Desc"]
MF_FIELDS = ["F_PROJ_NAME", "USER_PRMT_DESC", "FCC__Desc"]
SF_OUT = [
    "OBJECTID_1", "F_ORG_GROUP", "F_PERMIT_TY", "F_FCC_CODE", "FCC__Desc",
    "F_SOLD_DATE", "ADDRESS", "CITY", "STATE", "F_PROJ_NAME", "F_DWELLINGS",
    "F_BUILDING_", "PRMT_DESC", "MERGE_SRC", "Sold_Date", "Sold_Date_YR",
]
MF_OUT = [
    "OBJECTID", "F_ORG_GROUP", "F_PERMIT_TY", "F_FCC_CODE", "FCC__Desc",
    "F_SOLD_DATE", "ADDRESS", "F_PROJ_NAME", "F_ESTIMATED", "F_DWELLINGS",
    "F_BUILDING_", "USER_PRMT_DESC", "MERGE_SRC", "Sold_Date_SZ", "Sold_Date_SZ_YR",
]


def get(url, params):
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(url + "?" + q, headers={"User-Agent": "readiness-check/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def like_where(fields):
    parts = []
    for field in fields:
        for token in LIKES:
            parts.append(f"UPPER({field}) LIKE '%{token}%'")
    return " OR ".join(parts)


def paged(url, where, out_fields):
    rows = []
    offset = 0
    while True:
        data = get(url, {
            "where": where,
            "outFields": ",".join(out_fields),
            "returnGeometry": "true",
            "outSR": "4326",
            "resultRecordCount": "2000",
            "resultOffset": str(offset),
            "f": "json",
        })
        if data.get("error"):
            raise SystemExit(json.dumps(data["error"]))
        feats = data.get("features") or []
        rows.extend(feats)
        print(f"offset {offset} got {len(feats)}", flush=True)
        if not data.get("exceededTransferLimit") and len(feats) < 2000:
            break
        offset += len(feats)
        if not feats:
            break
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for label, url, fields, out_fields, year_field, date_field in [
        ("sf", SF, SF_FIELDS, SF_OUT, "Sold_Date_YR", "Sold_Date"),
        ("mf", MF, MF_FIELDS, MF_OUT, "Sold_Date_SZ_YR", "Sold_Date_SZ"),
    ]:
        print("====", label, flush=True)
        count = get(url, {"where": "1=1", "returnCountOnly": "true", "f": "json"})
        stats = get(url, {
            "where": "1=1",
            "outStatistics": json.dumps([
                {"statisticType": "min", "onStatisticField": year_field, "outStatisticFieldName": "min_yr"},
                {"statisticType": "max", "onStatisticField": year_field, "outStatisticFieldName": "max_yr"},
                {"statisticType": "min", "onStatisticField": date_field, "outStatisticFieldName": "min_dt"},
                {"statisticType": "max", "onStatisticField": date_field, "outStatisticFieldName": "max_dt"},
            ]),
            "f": "json",
        })
        where = like_where(fields)
        kw = get(url, {"where": where, "returnCountOnly": "true", "f": "json"})
        fcc = get(url, {
            "where": "1=1",
            "groupByFieldsForStatistics": "FCC__Desc",
            "outStatistics": json.dumps([
                {"statisticType": "count", "onStatisticField": "OBJECTID" if label == "mf" else "OBJECTID_1", "outStatisticFieldName": "n"}
            ]),
            "orderByFields": "n DESC",
            "f": "json",
        })
        rows = paged(url, where, out_fields)
        (OUT / f"{label}_keyword_superset.geojson").write_text(json.dumps({
            "type": "FeatureCollection",
            "features": rows,
        }))
        summary[label] = {
            "count": count,
            "stats": stats,
            "keyword_superset_count": kw,
            "fcc_groupby": fcc,
            "n_downloaded": len(rows),
            "where": where,
        }
        print(label, "count", count, "kw", kw, "downloaded", len(rows), flush=True)
    (OUT / "query_summary.json").write_text(json.dumps(summary))
    print("wrote", OUT / "query_summary.json")


if __name__ == "__main__":
    main()
