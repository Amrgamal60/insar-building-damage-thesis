"""List OPERA DISP-S1 frames from CMR granule metadata. No granules are opened.

Bounding boxes are passed as min_lon,min_lat,max_lon,max_lat.
CMR polygons are latitude longitude pairs.

Run:
  ~/miniforge3/envs/opera/bin/python -I feasibility/candidates/scripts/opera_frame_metadata.py CITY MINLON MINLAT MAXLON MAXLAT
"""

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("/mnt/data/Master-projects/Alex_private/candidates/raw")
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"


def fetch(params):
    url = CMR + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "readiness-check/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        body = json.load(resp)
    return body, headers


def main():
    city, minlon, minlat, maxlon, maxlat = sys.argv[1:6]
    bbox = f"{minlon},{minlat},{maxlon},{maxlat}"
    page = 1
    entries = []
    hits = None
    while True:
        body, headers = fetch({
            "short_name": "OPERA_L3_DISP-S1_V1",
            "bounding_box": bbox,
            "page_size": "500",
            "page_num": str(page),
        })
        hits = int(headers.get("cmr-hits", body.get("feed", {}).get("hits", 0) or 0))
        batch = body["feed"]["entry"]
        print(f"page {page} got {len(batch)} hits {hits}", flush=True)
        entries.extend(batch)
        if not batch or len(entries) >= hits:
            break
        page += 1
    # drop links to keep the raw file smaller, keep polygons and times
    slim = []
    for e in entries:
        slim.append({
            "id": e.get("id"),
            "title": e.get("title"),
            "producer_granule_id": e.get("producer_granule_id"),
            "time_start": e.get("time_start"),
            "time_end": e.get("time_end"),
            "polygons": e.get("polygons"),
        })
    path = OUT / f"opera_{city}_granules.json"
    path.write_text(json.dumps({
        "bbox": bbox,
        "cmr_hits": hits,
        "n_downloaded": len(slim),
        "granules": slim,
    }))
    print("wrote", path, "bytes", path.stat().st_size)


if __name__ == "__main__":
    main()
