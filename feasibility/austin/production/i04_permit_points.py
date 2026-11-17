"""Point coordinates of the construction-mask permits (AUSTIN_PLAN.md §7, construction mask), for permits whose
parcel is in no TCAD parcel layer we hold.

The checkpoint-1 permit table (3syk-w9eu, downloaded 2026-11-09) was taken without location columns. The
construction mask needs a location for every BP of work class New, Demolition, Addition, Addition and Remodel,
Shell or Relocation. This fetches only three columns of the same public dataset, for those permits:
  permit_number, latitude, longitude.
No address, applicant, contractor or description column is requested. The rows are joined to the checkpoint-1
table by permit_number (unique in both). The row identifier :id cannot be used: the City replaced the dataset on
2026-11-10 (16:53 UTC), after the checkpoint-1 download, and every :id changed. Rows not in the checkpoint-1
table are counted and dropped.

Writes OUT/permit_points.parquet (permit_number, latitude, longitude), OUT/pages/*.json (raw pages) and OUT/fetch.json
(query, row counts, dataset update time, hashes).
Usage: .venv/bin/python -I feasibility/austin/production/i04_permit_points.py CHECKPOINT1_PERMITS_CSV OUT
"""
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

URL = "https://data.austintexas.gov/resource/3syk-w9eu.json"
META = "https://data.austintexas.gov/api/views/3syk-w9eu.json"
CLASSES = ["New", "Demolition", "Addition", "Addition and Remodel", "Shell", "Relocation"]
PAGE = 50000
SNAPSHOT_SHA256 = "0e6f003f286473512cc4cb59765df9ddd4a834b70256f788269e0a3b76f28146"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-client", "Accept": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except Exception as e:  # network errors: retry
            if attempt == 4:
                raise
            print("retry", attempt + 1, type(e).__name__, flush=True)
            time.sleep(30)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


snap, out = Path(sys.argv[1]), Path(sys.argv[2])
assert sha256(snap) == SNAPSHOT_SHA256, "not the checkpoint-1 permit table"
(out / "pages").mkdir(parents=True, exist_ok=False)
meta = json.loads(get(META))
where = "permittype='BP' AND work_class in(" + ",".join(f"'{c}'" for c in CLASSES) + ")"
rows, offset, pages = [], 0, []
while True:
    q = urllib.parse.urlencode({"$select": "permit_number,latitude,longitude", "$where": where, "$order": "permit_number",
                                "$limit": PAGE, "$offset": offset})
    raw = get(f"{URL}?{q}")
    page = out / "pages" / f"{offset:08d}.json"
    page.write_bytes(raw)
    got = json.loads(raw)
    pages.append(dict(offset=offset, rows=len(got), sha256=sha256(page)))
    print(pages[-1], flush=True)
    rows += got
    if len(got) < PAGE:
        break
    offset += PAGE
pts = pd.DataFrame(rows)
for c in ("latitude", "longitude"):
    pts[c] = pd.to_numeric(pts.get(c), errors="coerce")
s = pd.read_csv(snap, usecols=["permit_number", "permittype", "work_class"], dtype=str)
s = s[s.permittype.eq("BP") & s.work_class.isin(CLASSES)]
assert pts.permit_number.is_unique and s.permit_number.is_unique
fetched_not_in_snapshot = int((~pts.permit_number.isin(set(s.permit_number))).sum())
pts = pts[pts.permit_number.isin(set(s.permit_number))]
pts[["permit_number", "latitude", "longitude"]].to_parquet(out / "permit_points.parquet", index=False)
info = dict(dataset="3syk-w9eu", rows_updated_at=meta.get("rowsUpdatedAt"), where=where, columns=["permit_number", "latitude", "longitude"],
            fetched=time.strftime("%Y-%m-%d %H:%M:%S %Z"), pages=pages, rows_fetched=len(rows),
            snapshot_mask_permits=len(s), joined=len(pts), fetched_not_in_snapshot=fetched_not_in_snapshot,
            snapshot_permits_not_fetched=int((~s.permit_number.isin(set(pts.permit_number))).sum()),
            with_coordinates=int(pts.latitude.notna().sum()), permit_points_sha256=sha256(out / "permit_points.parquet"))
(out / "fetch.json").write_text(json.dumps(info, indent=1) + "\n")
print(json.dumps({k: v for k, v in info.items() if k != "pages"}, indent=1))
