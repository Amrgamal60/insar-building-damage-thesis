"""Download the Austin keyword superset from Socrata, without name fields.

The superset is a SQL LIKE filter that contains the locked regex matches.
Exact regex and exclusion rules are applied later by austin_filter_and_stats.py.

Run:
  ~/miniforge3/envs/opera/bin/python -I feasibility/candidates/scripts/austin_download_superset.py
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("/mnt/data/Master-projects/Alex_private/candidates/raw/austin_keyword_superset.json")
BASE = "https://data.austintexas.gov/resource/3syk-w9eu.json"
SELECT = ",".join([
    "permit_number",
    "permittype",
    "permit_type_desc",
    "permit_class",
    "permit_class_mapped",
    "work_class",
    "description",
    "tcad_id",
    "issue_date",
    "applieddate",
    "calendar_year_issued",
    "original_address1",
    "original_city",
    "original_state",
    "original_zip",
    "latitude",
    "longitude",
    "housing_units",
    "status_current",
])
# Superset of the locked regex. Exact matching is local.
LIKE_BITS = [
    "%foundation%",
    "%underpin%",
    "%slab repair%",
    "%leveling%",
    "%levelling%",
    "%house level%",
    "%mudjack%",
    "%re-level%",
    "%helical%",
    "%pier%",
    "%shim%",
]
FIELDS = ["description", "work_class", "permit_class", "permittype", "permit_type_desc"]
WHERE = " OR ".join(
    f"lower({field}) like '{bit}'" for field in FIELDS for bit in LIKE_BITS
)


def fetch(offset, limit=10000):
    params = {
        "$select": SELECT,
        "$where": WHERE,
        "$order": "permit_number",
        "$limit": str(limit),
        "$offset": str(offset),
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "readiness-check/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


def main():
    rows = []
    offset = 0
    while True:
        page = fetch(offset)
        print(f"offset {offset} got {len(page)}", flush=True)
        rows.extend(page)
        if len(page) < 10000:
            break
        offset += 10000
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows))
    print(f"wrote {OUT} n={len(rows)} bytes={OUT.stat().st_size}")


if __name__ == "__main__":
    main()
