"""Construction-mask permits and the pixels each one masks (AUSTIN_PLAN.md §7, construction mask; §14 entry
"Construction mask: parcel polygon and location order", decided by the user on 2026-11-11).

Frozen rule: "for each window, pixels within 50 m of a parcel with a BP of work class New, Demolition, Addition,
Addition and Remodel, Shell or Relocation are dropped. This applies to permits issued from 365 days before the
window start to the window end."

As decided (§14):
  - Distance: from the pixel centre to the parcel polygon (zero inside it), at most 50 m.
  - Location of a permit's parcel, in this order:
      1. its 2018 TCAD parcel polygon (2018_Shapefiles.zip, Parcel_poly), matched on tcad_id = the 2018 roll's
         geo_id (§5 rule 2), or else on the layer's own PID_10; several polygons with one key are united;
      2. only where no 2018 parcel has that key: the parcel of the TCAD "Parcels Dec 2025" layer (step 0 copy,
         dissolved by property ID), matched on geo_id;
      3. otherwise the permit's own coordinates in 3syk-w9eu (production/i04_permit_points.py), distance to that
         point;
      4. otherwise the permit is unplaced: it masks nothing and is counted.
  - Keys are normalised as checkpoint 1 (strip, blank -> missing, leading zeros dropped).
  - Permits: the checkpoint-1 permit table, permittype BP, the six work classes, issued 2015-01-01 to 2025-11-30
    (the earliest window of §7 starts at the first granule, 2016-07-10, so 365 days earlier is 2015-07-11).
    The window selection by issue date is done by the processing script.

Pixels are those of the DISP subset grid (production/check/grid_check.json: centres x0 + 30 c, y0 - 30 r).
No InSAR value is read.

Writes OUT/mask_permits.npz:
  issue_day (int32, days since 1970-01-01), work_class (int8, index into CLASSES), source (int8: 1-3 as above,
  0 unplaced), ptr (int64 CSR offsets, length permits + 1), pixel (int32 flat index r * ncols + c);
and OUT/mask_permits.json (inputs and their hashes, counts by source, year and work class, pixel counts).
Usage: .venv/bin/python -I feasibility/austin/production/i06_mask_permits.py \
         PERMITS_CSV ROLL_KEYS_2018 PARCELS_2018_ZIP PARCELS_DEC2025 PERMIT_POINTS GRID_CHECK_JSON OUT
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyogrio
import shapely
from pyproj import Transformer

CLASSES = ["New", "Demolition", "Addition", "Addition and Remodel", "Shell", "Relocation"]
DIST, FIRST, LAST = 50.0, "2015-01-01", "2025-11-30"
SHA = {"permits": "0e6f003f286473512cc4cb59765df9ddd4a834b70256f788269e0a3b76f28146",
       "parcels_2018": "64e1a626bd09ad2aad4d0800543e67c162b66b99982a37364c65c95632886c06"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def norm(s):
    s = s.astype("string").str.strip()
    return s.mask(s.eq("")).str.lstrip("0").mask(lambda v: v.eq(""))


permits_csv, roll_keys, zip18, dec25, points, grid_json, out = map(Path, sys.argv[1:8])
assert sha256(permits_csv) == SHA["permits"] and sha256(zip18) == SHA["parcels_2018"]
out.mkdir(parents=True, exist_ok=False)
R = dict(inputs={k: dict(file=p.name, sha256=sha256(p)) for k, p in
                 dict(permits=permits_csv, roll_keys_2018=roll_keys, parcels_2018=zip18, parcels_dec2025=dec25,
                      permit_points=points, grid_check=grid_json).items()},
         distance_m=DIST, issue_dates=[FIRST, LAST], classes=CLASSES)

# ---- permits
d = pd.read_csv(permits_csv, usecols=["permit_number", "permittype", "work_class", "tcad_id", "issue_date"], dtype=str)
d = d[d.permittype.eq("BP") & d.work_class.isin(CLASSES)].copy()
d["date"] = pd.to_datetime(d.issue_date.str[:10], format="%Y-%m-%d", errors="coerce")
R["mask_class_permits_all_dates"] = len(d)
R["mask_class_permits_without_issue_date"] = int(d.date.isna().sum())
d = d[(d.date >= FIRST) & (d.date <= LAST)].sort_values(["date", "permit_number"]).reset_index(drop=True)
assert d.permit_number.is_unique
d["geo"] = norm(d.tcad_id)

# ---- 2018 polygons by key (roll geo_id first, then the layer's PID_10)
lay = pyogrio.read_dataframe(f"/vsizip/{zip18}/2018_Shapefiles/Parcel_poly.shp", columns=["PROP_ID", "PID_10"]).to_crs(32614)
lay = lay[lay.geometry.notna() & ~lay.geometry.is_empty].copy()
lay["geometry"] = shapely.make_valid(lay.geometry.to_numpy())
lay["pid"] = lay.PROP_ID.astype("int64").astype(str)
rk = pd.read_parquet(roll_keys, columns=["prop_id", "geo"])
rk["pid"] = rk.prop_id.str.lstrip("0")
lay = lay.merge(rk[["pid", "geo"]], on="pid", how="left", validate="many_to_one")
lay["pid10"] = norm(lay.PID_10)
by_roll = lay.dropna(subset=["geo"]).dissolve(by="geo").geometry
by_pid10 = lay.dropna(subset=["pid10"]).dissolve(by="pid10").geometry
p25 = pd.read_parquet(dec25, columns=["geo26", "geometry"])
import geopandas as gpd  # noqa: E402
p25 = gpd.GeoDataFrame(p25, geometry=gpd.GeoSeries.from_wkb(p25.geometry, crs=32614))
p25 = p25[p25.geo26.notna() & p25.geometry.notna() & ~p25.geometry.is_empty]
p25["geometry"] = shapely.make_valid(p25.geometry.to_numpy())
by_25 = p25.dissolve(by="geo26").geometry

pts = pd.read_parquet(points)
d = d.merge(pts, on="permit_number", how="left", validate="one_to_one")
x, y = Transformer.from_crs("EPSG:4326", "EPSG:32614", always_xy=True).transform(d.longitude.to_numpy(), d.latitude.to_numpy())
geoms, source = [], np.zeros(len(d), np.int8)
for i, g in enumerate(d.geo.to_numpy()):
    if isinstance(g, str) and g in by_roll.index:
        geoms.append(by_roll[g]); source[i] = 1
    elif isinstance(g, str) and g in by_pid10.index:
        geoms.append(by_pid10[g]); source[i] = 1
    elif isinstance(g, str) and g in by_25.index:
        geoms.append(by_25[g]); source[i] = 2
    elif np.isfinite(x[i]) and np.isfinite(y[i]):
        geoms.append(shapely.Point(x[i], y[i])); source[i] = 3
    else:
        geoms.append(None)

# ---- pixels within 50 m
G = json.loads(grid_json.read_text())
assert G["grid_as_assumed"] and G["dx"] == [30.0] and G["dy"] == [-30.0]
X0, Y0 = G["x_range"][0], G["y_range"][1]  # centre of column 0, centre of row 0
NR, NC = G["shape"]
ptr, pix = [0], []
for g in geoms:
    if g is None:
        ptr.append(ptr[-1]); continue
    xmin, ymin, xmax, ymax = g.bounds
    c0, c1 = max(int(np.floor((xmin - DIST - X0) / 30)), 0), min(int(np.ceil((xmax + DIST - X0) / 30)), NC - 1)
    r0, r1 = max(int(np.floor((Y0 - ymax - DIST) / 30)), 0), min(int(np.ceil((Y0 - ymin + DIST) / 30)), NR - 1)
    if c0 > c1 or r0 > r1:
        ptr.append(ptr[-1]); continue
    rr, cc = np.meshgrid(np.arange(r0, r1 + 1), np.arange(c0, c1 + 1), indexing="ij")
    rr, cc = rr.ravel(), cc.ravel()
    ok = shapely.dwithin(g, shapely.points(X0 + 30.0 * cc, Y0 - 30.0 * rr), DIST)
    sel = (rr[ok] * NC + cc[ok]).astype(np.int32)
    pix.append(sel)
    ptr.append(ptr[-1] + len(sel))
pixel = np.concatenate(pix) if pix else np.zeros(0, np.int32)
np.savez(out / "mask_permits.npz", issue_day=(d.date.to_numpy().astype("datetime64[D]").astype(np.int64)).astype(np.int32),
         work_class=d.work_class.map({c: i for i, c in enumerate(CLASSES)}).to_numpy(np.int8), source=source,
         ptr=np.asarray(ptr, np.int64), pixel=pixel)

# ---- summary
names = {0: "unplaced", 1: "2018 parcel polygon", 2: "Dec-2025 parcel polygon", 3: "permit coordinates"}
d["source"] = pd.Series(source).map(names)
d["year"] = d.date.dt.year
d["pixels"] = np.diff(ptr)
R["permits"] = len(d)
R["by_source"] = d.source.value_counts().to_dict()
R["by_source_from_2015_07_11"] = d[d.date >= "2015-07-11"].source.value_counts().to_dict()
R["by_year_and_source"] = {str(k): v for k, v in pd.crosstab(d.year, d.source).to_dict("index").items()}
R["by_work_class_and_source"] = pd.crosstab(d.work_class, d.source).to_dict("index")
R["placed_permits_masking_no_subset_pixel"] = int(((source > 0) & (d.pixels.to_numpy() == 0)).sum())
R["pixels_per_permit_quantiles"] = {str(q): float(v) for q, v in d.loc[source > 0, "pixels"].quantile([.5, .9, .99, 1]).items()}
R["subset_pixels_ever_masked"] = int(np.unique(pixel).size)
R["subset_pixels"] = int(NR * NC)
R["npz_sha256"] = sha256(out / "mask_permits.npz")
(out / "mask_permits.json").write_text(json.dumps(R, indent=1, default=int) + "\n")
print(json.dumps({k: v for k, v in R.items() if k not in ("by_year_and_source", "by_work_class_and_source")}, indent=1, default=int))
