"""Miami version of nyc/scripts/08_download_refpoint.py. Each OPERA DISP-S1 reference date has its own reference point;
for frame 12638 only the 2017-11-21 one (full-frame row 2784, col 6546) lies outside the downloaded subset
(rows 2917-5382, cols 5476-6993). For each of its granules this saves an 11 x 11 pixel window around the reference point,
with opera-utils' own subsetting (process_file), into miami/downloads/opera_refpoint/, and writes MANIFEST.sha256.
Only granules already in miami/downloads/opera_disp are fetched; existing windows are kept, so it can be rerun.
Usage (from Alex/): ~/miniforge3/envs/opera/bin/python -I feasibility/download_miami_refpoint.py
"""
import hashlib
from pathlib import Path

import h5py
from opera_utils.disp import search
from opera_utils.disp._download import process_file

RAW = Path(__file__).resolve().parent / "miami" / "downloads"
OUT = RAW / "opera_refpoint"
REF_DATE, ROW, COL, HALF = "2017-11-21", 2784, 6546, 5

local = {p.name for p in (RAW / "opera_disp").glob("*.nc")}
OUT.mkdir(exist_ok=True)
urls = [p.filename for p in search(frame_id=12638, product_version="1.0")
        if str(p.reference_datetime)[:10] == REF_DATE and Path(str(p.filename)).name in local]
print(len(urls), "granules", flush=True)
for u in sorted(urls, key=str):
    if (OUT / Path(str(u)).name).exists():
        continue
    out = process_file(str(u), slice(ROW - HALF, ROW + HALF + 1), slice(COL - HALF, COL + HALF + 1), OUT)
    with h5py.File(out) as h:
        rp = h["corrections/reference_point"].attrs
        assert (int(rp["rows"][0]), int(rp["cols"][0])) == (ROW, COL), out
        print(out.name, "label at reference point:", h["connected_component_labels"][HALF, HALF], flush=True)
lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}" for p in sorted(OUT.glob("*.nc"))]
(OUT / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")
print("ALLDONE", len(lines))
