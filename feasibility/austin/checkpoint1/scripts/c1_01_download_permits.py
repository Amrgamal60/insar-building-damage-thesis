"""Checkpoint 1 (AUSTIN_PLAN §4, §13 step 2): download and hash the issued-permit table 3syk-w9eu.

Only the columns the frozen rules use are requested. Contractor, applicant, address,
legal-description and location columns are not downloaded. Rows are paged in :id order.
The dataset's rowsUpdatedAt is read before and after; a change means the pages may mix
two versions, and the script refuses to finish.

Run: .venv/bin/python -I feasibility/austin/checkpoint1/scripts/c1_01_download_permits.py OUT_DIR
OUT_DIR must not exist (private area). Writes the CSV and download.json there.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import sys
import urllib.parse
from pathlib import Path

import requests

BASE = "https://data.austintexas.gov/resource/3syk-w9eu.csv"
VIEW = "https://data.austintexas.gov/api/views/3syk-w9eu.json"
COLUMNS = [":id", "permittype", "permit_type_desc", "permit_number", "permit_class_mapped",
           "permit_class", "work_class", "description", "tcad_id", "applieddate", "issue_date",
           "status_current", "calendar_year_issued"]
PAGE = 400_000
UA = {"User-Agent": "austin-checkpoint1/1.0"}

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=False)


def updated():
    v = requests.get(VIEW, headers=UA, timeout=120).json()
    return v["rowsUpdatedAt"]


before = updated()
target = out / "3syk-w9eu_checkpoint1.csv"
sha, rows, pages = hashlib.sha256(), 0, []
with open(target, "wb") as fh:
    offset = 0
    while True:
        params = {"$select": ",".join(COLUMNS), "$order": ":id", "$limit": PAGE, "$offset": offset}
        url = BASE + "?" + urllib.parse.urlencode(params)
        r = requests.get(url, headers=UA, timeout=900)
        r.raise_for_status()
        body = r.content
        header, _, data = body.partition(b"\n")
        n = sum(1 for _ in csv.reader(io.StringIO(data.decode("utf-8"), newline="")))
        if offset == 0:
            fh.write(header + b"\n")
            sha.update(header + b"\n")
        fh.write(data)
        sha.update(data)
        rows += n
        pages.append(dict(offset=offset, rows=n, bytes=len(body)))
        print(json.dumps(pages[-1]), flush=True)
        if n < PAGE:
            break
        offset += PAGE
after = updated()
if after != before:
    sys.exit(f"dataset updated during download ({before} -> {after}); rerun")
record = dict(dataset="3syk-w9eu (Issued Construction Permits, City of Austin)", endpoint=BASE,
              columns=COLUMNS, order=":id", page_size=PAGE, pages=pages, data_rows=rows,
              rows_updated_at_utc=dt.datetime.fromtimestamp(before, dt.timezone.utc).isoformat(),
              downloaded_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              file=target.name, bytes=target.stat().st_size, sha256=sha.hexdigest())
(out / "download.json").write_text(json.dumps(record, indent=1) + "\n")
print(json.dumps({k: record[k] for k in ("data_rows", "bytes", "sha256", "rows_updated_at_utc")}))
