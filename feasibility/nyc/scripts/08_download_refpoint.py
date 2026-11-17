"""Read the connected-component label at the reference point for the granules whose reference point lies outside the
NYC subset (NYC_REPLICATION_PLAN.md §7, rule 3). Found on 2026-10-08 from the granules' metadata: each reference date has
its own reference point, and only the 2021-10-30 one (full-frame row 4250, col 5254; Long Island, 40.7304 N 73.5591 W)
falls outside the downloaded subset (rows 3573-5145, cols 3276-4898). For each granule of that reference date, this
saves an 11 x 11 pixel window around the reference point with opera-utils' own subsetting (process_file), into
raw/opera/refpoint/, and writes raw/opera/refpoint/MANIFEST.sha256. Only the granules already in raw/opera/disp are fetched.
Usage (from feasibility/nyc): ~/miniforge3/envs/opera/bin/python -I scripts/08_download_refpoint.py raw"""
import hashlib
import sys
from pathlib import Path

import h5py
from opera_utils.disp import search
from opera_utils.disp._download import process_file

RAW = Path(sys.argv[1]) / "opera"
OUT = RAW / "refpoint"
REF_DATE, ROW, COL, HALF = "2021-10-30", 4250, 5254, 5

local = {p.name for p in (RAW / "disp").glob("*.nc")}
OUT.mkdir(exist_ok=True)
urls = [p.filename for p in search(frame_id=8622, product_version="1.0")
        if str(p.reference_datetime)[:10] == REF_DATE and Path(str(p.filename)).name in local]
print(len(urls), "granules")
for u in sorted(urls, key=str):
    out = process_file(str(u), slice(ROW - HALF, ROW + HALF + 1), slice(COL - HALF, COL + HALF + 1), OUT)
    with h5py.File(out) as h:
        rp = h["corrections/reference_point"].attrs
        assert (int(rp["rows"][0]), int(rp["cols"][0])) == (ROW, COL), out
        print(out.name, "label at reference point:", h["connected_component_labels"][HALF, HALF], flush=True)
lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}" for p in sorted(OUT.glob("*.nc"))]
(OUT / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")
print("ALLDONE", len(lines))
