"""Download City of Houston keyword-superset permit rows and layer totals.

Uses the ArcGIS REST query API. Saves JSON under Alex_private.
The LIKE filter is a superset of the locked regex. Exact matching is local.

Run:
  ~/miniforge3/envs/opera/bin/python -I feasibility/candidates/scripts/houston_keyword_download.py
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


def get(url, params):
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(url + "?" + q, headers={"User-Agent": "readiness-check/1.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.load(resp)


def like_where(fields):
    return " OR ".join(f"UPPER({field}) LIKE '%{token}%'" for field in fields for token in LIKES)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = {
        "sf": {
            "url": SF,
            "fields": ["F_PROJ_NAME", "PRMT_DESC", "FCC__Desc"],
            "out": "OBJECTID_1,F_ORG_GROUP,F_PERMIT_TY,F_FCC_CODE,FCC__Desc,F_SOLD_DATE,ADDRESS,CITY,STATE,F_PROJ_NAME,F_DWELLINGS,F_BUILDING_,PRMT_DESC,MERGE_SRC,Sold_Date,Sold_Date_YR",
            "year": "Sold_Date_YR",
            "date": "Sold_Date",
            "oid": "OBJECTID_1",
        },
        "mf": {
            "url": MF,
            "fields": ["F_PROJ_NAME", "USER_PRMT_DESC", "FCC__Desc"],
            "out": "OBJECTID,F_ORG_GROUP,F_PERMIT_TY,F_FCC_CODE,FCC__Desc,F_SOLD_DATE,ADDRESS,F_PROJ_NAME,F_ESTIMATED,F_DWELLINGS,F_BUILDING_,USER_PRMT_DESC,MERGE_SRC,Sold_Date_SZ,Sold_Date_SZ_YR",
            "year": "Sold_Date_SZ_YR",
            "date": "Sold_Date_SZ",
            "oid": "OBJECTID",
        },
    }
    summary = {}
    for label, job in jobs.items():
        where = like_where(job["fields"])
        count = get(job["url"], {"where": "1=1", "returnCountOnly": "true", "f": "json"})
        stats = get(job["url"], {
            "where": "1=1",
            "outStatistics": json.dumps([
                {"statisticType": "min", "onStatisticField": job["year"], "outStatisticFieldName": "min_yr"},
                {"statisticType": "max", "onStatisticField": job["year"], "outStatisticFieldName": "max_yr"},
                {"statisticType": "min", "onStatisticField": job["date"], "outStatisticFieldName": "min_dt"},
                {"statisticType": "max", "onStatisticField": job["date"], "outStatisticFieldName": "max_dt"},
            ]),
            "f": "json",
        })
        kw = get(job["url"], {"where": where, "returnCountOnly": "true", "f": "json"})
        fcc = get(job["url"], {
            "where": "1=1",
            "groupByFieldsForStatistics": "FCC__Desc",
            "outStatistics": json.dumps([
                {"statisticType": "count", "onStatisticField": job["oid"], "outStatisticFieldName": "n"}
            ]),
            "orderByFields": "n DESC",
            "f": "json",
        })
        feats = get(job["url"], {
            "where": where,
            "outFields": job["out"],
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "json",
        })
        (OUT / f"{label}_keyword_superset.geojson").write_text(json.dumps(feats))
        summary[label] = {
            "count": count,
            "stats": stats,
            "keyword_superset_count": kw,
            "fcc_groupby": fcc,
            "n_features_downloaded": len(feats.get("features") or []),
            "where": where,
        }
        print(label, count, kw, "downloaded", summary[label]["n_features_downloaded"], flush=True)
        (OUT / "query_summary.json").write_text(json.dumps(summary))
    print("wrote", OUT / "query_summary.json")


if __name__ == "__main__":
    main()
