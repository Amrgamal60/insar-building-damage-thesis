"""Download the OPERA L3 DISP-S1 v1 granules of frame 28482 (AUSTIN_PLAN.md §7, §13 step 3), clipped to the
study area plus a 2 km buffer, with opera-utils 0.25.8's disp-s1-download (as NYC).

Runs on the project PC, which holds the Earthdata login (~/.netrc); the processing server cannot reach it. The
files are then copied to the server and their hashes checked there (§14, compute location). This script reads
no displacement value: it downloads, then lists and hashes the files.

Bounding box: the full-purpose boundary (vnwj-xmz9, checkpoint 1, SHA-256 checked) buffered by 2,000 m in
EPSG:32614, transformed to longitude/latitude; its envelope. Acquisitions from the first available product
(2016-07) to 2025-11-30, the end of the study period.

Usage (from the repository root):
  ~/miniforge3/envs/opera/bin/python -I feasibility/austin/production/i01_download_disp.py BOUNDARY.geojson OUTDIR
Writes OUTDIR/disp/*.nc, OUTDIR/disp_download.log, OUTDIR/download.json and OUTDIR/disp/MANIFEST.sha256.
"""
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import time
from pathlib import Path

import shapely
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

BOUNDARY_SHA256 = "9656bd73a7a7989ef41fd0610f716a8078d0fe843d0466b21e9acef9f93ede47"
FRAME, END, BUFFER_M, ATTEMPTS = 28482, "2025-12-01", 2000.0, 4
CLI = Path(sys.executable).parent / "opera-utils"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


boundary, out = Path(sys.argv[1]), Path(sys.argv[2])
assert sha256(boundary) == BOUNDARY_SHA256, "boundary is not the checkpoint-1 copy"
geo = json.loads(boundary.read_text())
area = shapely.union_all([shape(f["geometry"]) for f in geo["features"]])
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32614", always_xy=True).transform
to_ll = Transformer.from_crs("EPSG:32614", "EPSG:4326", always_xy=True).transform
buffered = transform(to_ll, transform(to_utm, area).buffer(BUFFER_M))
west, south, east, north = (round(v, 6) for v in buffered.bounds)
west, south = west - 1e-6, south - 1e-6  # rounding never cuts the buffer
east, north = east + 1e-6, north + 1e-6
disp = out / "disp"
disp.mkdir(parents=True, exist_ok=True)
cmd = [str(CLI), "disp-s1-download", "--frame-id", str(FRAME), "--end-datetime", END,
       "--bbox", *map(str, (west, south, east, north)), "--url-type", "HTTPS", "--num-workers", "4",
       "--product-version", "1.0", "--output-dir", str(disp)]
log = out / "disp_download.log"
t0 = time.time()
for attempt in range(1, ATTEMPTS + 1):
    with open(log, "a") as f:
        f.write(f"attempt {attempt} {time.strftime('%Y-%m-%d %H:%M:%S %Z')}: {' '.join(cmd)}\n")
        f.flush()
        rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT).returncode
        f.write(f"attempt {attempt} exit {rc} files {len(list(disp.glob('*.nc')))}\n")
    if rc == 0:
        break
    time.sleep(60)
files = sorted(disp.glob("*.nc"))
(disp / "MANIFEST.sha256").write_text("".join(f"{sha256(p)}  {p.name}\n" for p in files))
info = dict(frame=FRAME, product="OPERA_L3_DISP-S1 v1.0 (CMR C3294057315-ASF)", end_datetime=END,
            bbox_lonlat=[west, south, east, north], buffer_m=BUFFER_M, boundary_sha256=BOUNDARY_SHA256,
            opera_utils=importlib.metadata.version("opera-utils"),
            exit_code=rc, attempts=attempt, files=len(files), manifest_sha256=sha256(disp / "MANIFEST.sha256"),
            first=files[0].name if files else None, last=files[-1].name if files else None,
            seconds=time.time() - t0, finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
(out / "download.json").write_text(json.dumps(info, indent=1) + "\n")
print(json.dumps(info, indent=1))
sys.exit(rc)
