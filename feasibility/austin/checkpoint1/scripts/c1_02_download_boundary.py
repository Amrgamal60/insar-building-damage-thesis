"""Checkpoint 1 (AUSTIN_PLAN §5 study area): download and hash the City of Austin full-purpose
boundary (dataset vnwj-xmz9), with the same query as step 0, and compare with the step-0 copy.

Run: .venv/bin/python -I feasibility/austin/checkpoint1/scripts/c1_02_download_boundary.py OUT_DIR STEP0_COPY
"""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import requests

URL = ("https://data.austintexas.gov/resource/vnwj-xmz9.geojson?$where=jurisdiction_type=%27FULL%27"
       "%20AND%20city_name=%27CITY%20OF%20AUSTIN%27&$limit=50000")
VIEW = "https://data.austintexas.gov/api/views/vnwj-xmz9.json"
out, step0 = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=False)
view = requests.get(VIEW, timeout=120).json()
r = requests.get(URL, timeout=300)
r.raise_for_status()
(out / "vnwj-xmz9.geojson").write_bytes(r.content)
sha = hashlib.sha256(r.content).hexdigest()
old = hashlib.sha256(step0.read_bytes()).hexdigest()
record = dict(dataset="vnwj-xmz9 (City of Austin jurisdictions)", url=URL, file="vnwj-xmz9.geojson",
              bytes=len(r.content), sha256=sha,
              rows_updated_at_utc=dt.datetime.fromtimestamp(view["rowsUpdatedAt"], dt.timezone.utc).isoformat(),
              downloaded_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              step0_copy_sha256=old, identical_to_step0=sha == old,
              features=len(r.json()["features"]))
(out / "download.json").write_text(json.dumps(record, indent=1) + "\n")
print(json.dumps(record, indent=1))
