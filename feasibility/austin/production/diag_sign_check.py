"""Diagnostics after the sign check came out "not below" (AUSTIN_PLAN.md §7: "work stops until the cause is found and
logged"). Outcome-blind: reads only the full-period velocity field (i08 full.npz), the landfill perimeters and the
full-purpose boundary. Changes nothing; it describes.

1. Status: landfill median of valid footprint pixels for inactive and active perimeters separately.
2. Local contrast: for each perimeter, the median velocity of its valid footprint pixels minus the median of the valid
   pixels whose centre lies 100-500 m outside it (and inside no perimeter). This removes signal that varies over
   kilometres (for example a gradient across the subset from the reference far away).
3. Regional pattern: median velocity of valid pixels inside the city by 5 km band of x and of y; a plane
   v = a + b x + c y fitted by least squares over the valid subset pixels; the sign check repeated on residuals.
Usage: .venv/bin/python -I diag_sign_check.py FULL_NPZ PERIMETERS_GEOJSON BOUNDARY_GEOJSON OUT_JSON
"""
import json
import sys
from pathlib import Path

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import shape

full, perim, boundary, out = map(Path, sys.argv[1:5])
Z = np.load(full)
v, good, xs, ys, inside_city = Z["v"], Z["good"], Z["x"], Z["y"], Z["inside_city"]
ok = good & np.isfinite(v)
XX, YY = np.meshgrid(xs, ys)
tr = Transformer.from_crs("EPSG:4326", "EPSG:32614", always_xy=True)
to_utm = lambda g: shapely.transform(g, lambda a: np.c_[tr.transform(a[:, 0], a[:, 1])])  # noqa: E731
city = shapely.union_all([to_utm(shape(f["geometry"])) for f in json.loads(boundary.read_text())["features"]])
polys = []
for f in json.loads(perim.read_text())["features"]:
    g = shapely.make_valid(to_utm(shape(f["geometry"])))
    if g.intersects(city):
        p = f["properties"]
        polys.append((p["LANDFILLS_PERIMETER_ID"], p["OPERATING_STATUS"], p["ACTIVE_YEARS"], g))
anyfoot = np.zeros(v.shape, bool)
foot = {}
for pid, st, yrs, g in polys:
    foot[pid] = shapely.contains_xy(g, XX, YY)
    anyfoot |= foot[pid]
R = {}
for st in ("INACTIVE", "ACTIVE"):
    m = np.zeros(v.shape, bool)
    for pid, s, _, _ in polys:
        if s == st:
            m |= foot[pid]
    R[f"median_{st.lower()}"] = dict(valid_pixels=int((m & ok).sum()), median=float(np.median(v[m & ok])) if (m & ok).any() else None)
R["median_subset"] = float(np.median(v[ok]))
R["median_city"] = float(np.median(v[ok & inside_city]))

rows = []
pts = None
for pid, st, yrs, g in polys:
    x0, y0, x1, y1 = g.bounds
    sel = (XX >= x0 - 520) & (XX <= x1 + 520) & (YY >= y0 - 520) & (YY <= y1 + 520)
    d = np.full(v.shape, np.inf)
    d[sel] = shapely.distance(g, shapely.points(XX[sel], YY[sel]))
    ring = (d > 100) & (d <= 500) & ~anyfoot & ok
    fm = foot[pid] & ok
    fv, rv = (float(np.median(v[fm])) if fm.any() else None), (float(np.median(v[ring])) if ring.any() else None)
    rows.append(dict(perimeter_id=pid, status=st, active_years=yrs, valid_footprint=int(fm.sum()), footprint_median=fv,
                     valid_ring=int(ring.sum()), ring_median=rv,
                     contrast=None if fv is None or rv is None else fv - rv))
R["perimeters"] = rows
c_in = [r["contrast"] for r in rows if r["status"] == "INACTIVE" and r["contrast"] is not None]
c_in_w = [(r["contrast"], r["valid_footprint"]) for r in rows if r["status"] == "INACTIVE" and r["contrast"] is not None]
R["local_contrast_inactive"] = dict(perimeters=len(c_in), median=float(np.median(c_in)), below_zero=int(sum(c < 0 for c in c_in)),
                                    pixel_weighted_mean=float(sum(c * n for c, n in c_in_w) / sum(n for _, n in c_in_w)))
c_ac = [r for r in rows if r["status"] == "ACTIVE"]
R["local_contrast_active"] = [dict(perimeter_id=r["perimeter_id"], contrast=r["contrast"], valid_footprint=r["valid_footprint"]) for r in c_ac]

# pooled local contrast: every valid footprint pixel minus its own perimeter's ring median, inactive only
pooled = []
for pid, st, _, _ in polys:
    r = next(q for q in rows if q["perimeter_id"] == pid)
    if st == "INACTIVE" and r["ring_median"] is not None:
        pooled.append(v[foot[pid] & ok] - r["ring_median"])
pooled = np.concatenate(pooled)
R["pooled_inactive_pixel_contrast"] = dict(pixels=len(pooled), median=float(np.median(pooled)), share_below_zero=float((pooled < 0).mean()))

bands = {}
for name, A in (("x", XX), ("y", YY)):
    b = np.floor(A / 5000).astype(int)
    m = ok & inside_city
    bands[name] = {f"{k * 5}-{k * 5 + 5} km": dict(pixels=int((m & (b == k)).sum()), median=float(np.median(v[m & (b == k)])))
                   for k in np.unique(b[m]) if (m & (b == k)).sum() > 1000}
R["city_bands"] = bands
X = np.c_[np.ones(ok.sum()), (XX[ok] - XX.mean()) / 1000, (YY[ok] - YY.mean()) / 1000]
coef = np.linalg.lstsq(X, v[ok], rcond=None)[0]
res = np.full(v.shape, np.nan)
res[ok] = v[ok] - X @ coef
R["plane"] = dict(intercept=float(coef[0]), per_km_east=float(coef[1]), per_km_north=float(coef[2]))
inact = np.zeros(v.shape, bool)
for pid, st, _, _ in polys:
    if st == "INACTIVE":
        inact |= foot[pid]
R["residual_sign_check"] = dict(all_landfills=float(np.nanmedian(res[anyfoot & ok])), inactive=float(np.nanmedian(res[inact & ok])),
                                subset=float(np.nanmedian(res[ok])))
out.write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps({k: v_ for k, v_ in R.items() if k != "perimeters"}, indent=1))
for r in rows:
    print(r["perimeter_id"], r["status"], r["active_years"], r["valid_footprint"], r["valid_ring"],
          None if r["contrast"] is None else round(r["contrast"], 2))
