"""Checkpoint 1 (AUSTIN_PLAN §9 terrain): list the USGS 3DEP 1 m DEM tiles that cover the
eligible parcels (their bounding box plus 500 m), from The National Map catalogue.

Run: .venv/bin/python -I feasibility/austin/checkpoint1/scripts/c1_13_dem_tile_list.py PARCELS_JSON OUT_JSON
"""
import datetime as dt
import json
import sys
from pathlib import Path

import pyproj
import requests

b = json.loads(Path(sys.argv[1]).read_text())["bounds"]
t = pyproj.Transformer.from_crs(32614, 4326, always_xy=True)
w, s = t.transform(b[0] - 500, b[1] - 500)
e, n = t.transform(b[2] + 500, b[3] + 500)
API = "https://tnmaccess.nationalmap.gov/api/v1/products"
items, off = [], 0
while True:
    r = requests.get(API, params={"datasets": "Digital Elevation Model (DEM) 1 meter", "bbox": f"{w},{s},{e},{n}",
                                  "prodFormats": "GeoTIFF", "max": 200, "offset": off, "outputFormat": "JSON"},
                     headers={"User-Agent": "research-client"}, timeout=300)
    r.raise_for_status()
    j = r.json()
    items += j.get("items", [])
    if len(items) >= j.get("total", 0) or not j.get("items"):
        break
    off += 200
tiles = sorted((dict(title=i["title"], url=i["downloadURL"], bytes=i.get("sizeInBytes"), publication_date=i["publicationDate"],
                     project=i["downloadURL"].split("/Projects/")[1].split("/")[0]) for i in items), key=lambda x: x["url"])
out = dict(api=API, bbox_lonlat=[round(v, 6) for v in (w, s, e, n)], queried_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           tiles=len(tiles), projects=sorted({x["project"] for x in tiles}), items=tiles)
Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps({k: v for k, v in out.items() if k != "items"}, indent=1))
