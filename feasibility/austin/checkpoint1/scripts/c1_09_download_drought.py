"""Checkpoint 1 (AUSTIN_PLAN §4 permits and drought; §13 step 2): download and hash NOAA's
divisional Palmer Drought Severity Index file (nClimDiv), the county-to-division table and
the readme files.

Run: .venv/bin/python -I feasibility/austin/checkpoint1/scripts/c1_09_download_drought.py OUT_DIR
"""
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

import requests

BASE = "https://www.ncei.noaa.gov/pub/data/cirs/climdiv/"
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=False)
H = {"User-Agent": "research-client"}
listing = requests.get(BASE, headers=H, timeout=120)
listing.raise_for_status()
names = sorted(set(re.findall(r'href="(climdiv-pdsidv-v[0-9.]+-\d{8})"', listing.text)))
assert len(names) == 1, names
files = {}
for name in [names[0], "county-to-climdivs.txt", "divisional-readme.txt", "drought-readme.txt", "procdate.txt"]:
    r = requests.get(listing.url + name, headers=H, timeout=300)
    r.raise_for_status()
    (out / name).write_bytes(r.content)
    files[name] = dict(bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest())
record = dict(source=listing.url, files=files, pdsi_file=names[0],
              downloaded_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
(out / "download.json").write_text(json.dumps(record, indent=1) + "\n")
print(json.dumps(record, indent=1))
