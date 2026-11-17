"""Connected-component label at the frame's reference point (AUSTIN_PLAN.md §7: "as NYC §7, steps 1-3": a pixel is
invalid for a window if its label at any epoch is 0 or differs from the label at the frame's reference point).

Each DISP-S1 granule records its reference point (corrections/reference_point: full-frame row and column). Each
reference date has its own point, and some lie outside the downloaded study-area subset. For every downloaded
granule whose reference point lies outside the subset, this saves an 11 x 11 pixel window around the point with
opera-utils' own subsetting (process_file), as NYC (scripts/08_download_refpoint.py), into OUT/refpoint/, and
writes OUT/refpoint/MANIFEST.sha256 and OUT/reference_points.csv (one row per granule: reference date, point row,
column, latitude, longitude, inside the subset or not, and the label at the point). No displacement is read.

Runs on the project PC (Earthdata login). Subset rows and columns come from the granules' x/y and the frame's grid
(frame_grid in checkpoint1/frame_grid_folds.json: xmin 448080, ymax 3409770, 30 m).
Usage: ~/miniforge3/envs/opera/bin/python -I feasibility/austin/production/i03_download_refpoint.py OPERA_DIR
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

import h5py
from opera_utils.disp import search
from opera_utils.disp._download import process_file

FRAME, HALF = 28482, 5
OUT = Path(sys.argv[1])
DISP, REF = OUT / "disp", OUT / "refpoint"
grid = json.loads((Path(__file__).resolve().parents[1] / "checkpoint1" / "frame_grid_folds.json").read_text())["frame_grid"]
assert grid["epsg"] == 32614 and grid["snap_m"] == 30.0
XMIN, YMAX = grid["xmin"], grid["ymax"]

files = sorted(DISP.glob("*.nc"))
with h5py.File(files[0], "r") as h:
    x, y = h["x"][()], h["y"][()]
r0, c0 = int(round((YMAX - y[0] - 15) / 30)), int(round((x[0] - XMIN - 15) / 30))
r1, c1 = r0 + len(y), c0 + len(x)
assert (YMAX - 15 - 30 * r0, XMIN + 15 + 30 * c0) == (y[0], x[0])
print(f"subset rows {r0}-{r1 - 1}, cols {c0}-{c1 - 1}", flush=True)

rows = []
for f in files:
    with h5py.File(f, "r") as h:
        rp = h["corrections/reference_point"].attrs
        row, col = int(rp["rows"][0]), int(rp["cols"][0])
        lat, lon = float(rp["latitudes"][0]), float(rp["longitudes"][0])
        ref = h["identification/reference_datetime"][()].decode()[:10]
        sec = h["identification/secondary_datetime"][()].decode()[:10]
        inside = r0 <= row < r1 and c0 <= col < c1
        label = int(h["connected_component_labels"][row - r0, col - c0]) if inside else None
    rows.append(dict(file=f.name, reference_date=ref, secondary_date=sec, ref_row=row, ref_col=col,
                     ref_lat=lat, ref_lon=lon, inside_subset=inside, label_at_reference_point=label, source="subset"))

need = {r["file"] for r in rows if not r["inside_subset"]}
REF.mkdir(exist_ok=True)
urls = {Path(str(p.filename)).name: str(p.filename) for p in search(frame_id=FRAME, product_version="1.0")}
by_file = {r["file"]: r for r in rows}
for name in sorted(need):
    r = by_file[name]
    dst = REF / name
    if not dst.exists():
        process_file(urls[name], slice(r["ref_row"] - HALF, r["ref_row"] + HALF + 1),
                     slice(r["ref_col"] - HALF, r["ref_col"] + HALF + 1), REF)
    with h5py.File(dst, "r") as h:
        rp = h["corrections/reference_point"].attrs
        assert (int(rp["rows"][0]), int(rp["cols"][0])) == (r["ref_row"], r["ref_col"]), name
        r["label_at_reference_point"] = int(h["connected_component_labels"][HALF, HALF])
        r["source"] = "refpoint window"
    print(name[30:75], "label", r["label_at_reference_point"], flush=True)

lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}" for p in sorted(REF.glob("*.nc"))]
(REF / "MANIFEST.sha256").write_text("\n".join(lines) + ("\n" if lines else ""))
with open(OUT / "reference_points.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
labels = [r["label_at_reference_point"] for r in rows]
print(json.dumps(dict(granules=len(rows), outside_subset=len(need), label_zero=sum(v == 0 for v in labels),
                      reference_dates=sorted({r["reference_date"] for r in rows})), indent=1))
print("ALLDONE")
