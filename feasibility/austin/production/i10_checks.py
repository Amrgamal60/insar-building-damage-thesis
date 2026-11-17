"""Checks before outcomes are joined (AUSTIN_PLAN.md §7): sign check, clay contrast check, coverage report.
Outcome-blind: only prop_id and lep_0_150 (features) and prop_id, pix_i, pix_j (grid) are read; no event, outcome,
fold or block column.

Sign check (§7; §14 entry of 2026-11-10, landfill footprints):
  - footprints: the City of Austin's Landfill Perimeters that intersect the full-purpose boundary (39 expected:
    35 inactive, 4 active); a pixel belongs to a footprint if its centre lies inside a perimeter;
  - landfill value: the median full-period velocity of the valid footprint pixels (each pixel once);
  - compared with the median full-period velocity of all valid pixels of the subset;
  - "below" if the landfill value is lower (away from the satellite). If not, work stops until the cause is found.
  Per perimeter: its ID, operating status, active years, type, pixels and median velocity. No name or owner field
  is written.
Clay contrast check (§7):
  - each eligible parcel takes the full-period seasonal amplitude sqrt(b^2 + c^2) of its pixel (valid pixels only);
  - classes of SSURGO linear extensibility lep_0_150 (%): low < 3, moderate 3-6, high 6-9, very high >= 9;
  - statistic: median amplitude of the high and very high parcels minus that of the low parcels (each parcel once);
  - 95% percentile interval from a bootstrap over 2 km blocks (the block of the pixel centre, edges at multiples of
    2,000 m, as checkpoint 1): 2,000 draws, seed 2026 (authors' choice: NYC's bootstrap size);
  - "demonstrated" if the statistic is above zero and the interval's lower end is above zero.
Coverage report (§7): valid house pixels and valid houses per window, from i08's coverage.csv, by family; and the
pixels with a full-period value (subset, inside the city, house pixels).
Usage: .venv/bin/python -I i10_checks.py FULL_NPZ COVERAGE_CSV INSAR_INPUTS_NPZ PERIMETERS_GEOJSON BOUNDARY_GEOJSON \
         FEATURES_PARQUET GRID_PARQUET OUT
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import shape

SHA = {"perimeters": "9d9e98944eeca842b2bd51bc1f16e2416a5b0e4dfb9a33c09cffd77f9c66f14b",
       "boundary": "9656bd73a7a7989ef41fd0610f716a8078d0fe843d0466b21e9acef9f93ede47"}
CLASSES = [("low", -np.inf, 3.0), ("moderate", 3.0, 6.0), ("high", 6.0, 9.0), ("very high", 9.0, np.inf)]
B, SEED, BLOCK_M = 2000, 2026, 2000.0


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


full, coverage, inputs, perim, boundary, features, grid, out = map(Path, sys.argv[1:9])
assert sha256(perim) == SHA["perimeters"] and sha256(boundary) == SHA["boundary"]
rec = Path(__file__).resolve().parents[1] / "checkpoint1"
want = {"features": json.loads((rec / "features_2018.json").read_text())["private_outputs_sha256"]["features_2018.parquet"],
        "grid": json.loads((rec / "frame_grid_folds.json").read_text())["private_outputs_sha256"]["eligible_grid_folds.parquet"]}
assert sha256(features) == want["features"] and sha256(grid) == want["grid"]
out.mkdir(parents=True, exist_ok=False)
R = dict(inputs={p.name: sha256(p) for p in (full, coverage, inputs, perim, boundary, features, grid)})

Z = np.load(full)
v, amp, good, xs, ys = Z["v"], Z["amp"], Z["good"], Z["x"], Z["y"]
ok = good & np.isfinite(v)
XX, YY = np.meshgrid(xs, ys)
tr = Transformer.from_crs("EPSG:4326", "EPSG:32614", always_xy=True)
to_utm = lambda g: shapely.transform(g, lambda a: np.c_[tr.transform(a[:, 0], a[:, 1])])  # noqa: E731

# ---- sign check
city = shapely.union_all([to_utm(shape(f["geometry"])) for f in json.loads(boundary.read_text())["features"]])
P = json.loads(perim.read_text())["features"]
rows, foot = [], np.zeros(v.shape, bool)
for f in P:
    g = shapely.make_valid(to_utm(shape(f["geometry"])))
    if not g.intersects(city):
        continue
    inside = shapely.contains_xy(g, XX, YY)
    foot |= inside
    p = f["properties"]
    rows.append(dict(perimeter_id=p["LANDFILLS_PERIMETER_ID"], status=p["OPERATING_STATUS"], active_years=p["ACTIVE_YEARS"],
                     type=p["TYPE_OF_LANDFILL"], area_ha=round(g.area / 1e4, 2), pixels=int(inside.sum()),
                     valid_pixels=int((inside & ok).sum()),
                     median_v=float(np.median(v[inside & ok])) if (inside & ok).any() else None))
lf = pd.DataFrame(rows).sort_values("perimeter_id")
lf.to_csv(out / "sign_check_perimeters.csv", index=False)
land, area = float(np.median(v[foot & ok])), float(np.median(v[ok]))
R["sign_check"] = dict(perimeters_used=len(lf), by_status=lf.status.value_counts().to_dict(),
                       footprint_pixels=int(foot.sum()), valid_footprint_pixels=int((foot & ok).sum()),
                       perimeters_with_valid_pixels=int((lf.valid_pixels > 0).sum()),
                       landfill_median_mm_yr=land, subset_median_mm_yr=area, valid_subset_pixels=int(ok.sum()),
                       city_median_mm_yr=float(np.median(v[ok & Z["inside_city"]])),
                       difference_mm_yr=land - area, result="below" if land < area else "not below")
assert len(lf) == 39 and R["sign_check"]["by_status"] == {"INACTIVE": 35, "ACTIVE": 4}, R["sign_check"]

# ---- clay contrast
f = pd.read_parquet(features, columns=["prop_id", "lep_0_150"])
g = pd.read_parquet(grid, columns=["prop_id", "pix_i", "pix_j"])
z = np.load(inputs)
assert (f.prop_id.to_numpy() == g.prop_id.to_numpy()).all() and (z["prop_id"] == g.prop_id.to_numpy().astype("U12")).all()
hp = z["house_pixel"]
r, c = z["r"][hp], z["c"][hp]
a = np.where(good[r, c], amp[r, c], np.nan)
lep = f.lep_0_150.to_numpy(float)
cls = np.full(len(lep), -1)
for k, (_, lo, hi) in enumerate(CLASSES):
    cls[(lep >= lo) & (lep < hi)] = k
pi, pj = z["pix_i"][hp], z["pix_j"][hp]
bx, by = np.floor((pi * 30 + 15) / BLOCK_M).astype(np.int64), np.floor((pj * 30 + 15) / BLOCK_M).astype(np.int64)
block = np.unique(bx * 1_000_000 + by, return_inverse=True)[1]
use = np.isfinite(a) & (cls >= 0)
hi_grp, lo_grp = use & (cls >= 2), use & (cls == 0)


def stat(idx):
    h, l_ = idx[hi_grp[idx]], idx[lo_grp[idx]]
    return float(np.median(a[h]) - np.median(a[l_])) if len(h) and len(l_) else np.nan


obs = stat(np.arange(len(a)))
members = pd.Series(np.arange(len(a))).groupby(block).apply(np.asarray).to_list()
nb = len(members)
rng = np.random.default_rng(SEED)
draws = np.array([stat(np.concatenate([members[k] for k in rng.integers(0, nb, nb)])) for _ in range(B)])
lo_ci, hi_ci = np.nanpercentile(draws, [2.5, 97.5])
R["clay_contrast"] = dict(
    parcels=len(a), parcels_with_lep=int((cls >= 0).sum()), parcels_with_amplitude=int(np.isfinite(a).sum()), used=int(use.sum()),
    by_class={name: dict(parcels=int((cls == k).sum()), used=int((use & (cls == k)).sum()),
                         median_amplitude_mm=float(np.median(a[use & (cls == k)]))) for k, (name, _, _) in enumerate(CLASSES)},
    statistic_mm=obs, interval_95=[float(lo_ci), float(hi_ci)], blocks=nb, draws=B, seed=SEED,
    draws_undefined=int(np.isnan(draws).sum()),
    label="demonstrated" if obs > 0 and lo_ci > 0 else "not demonstrated")
np.save(out / "clay_contrast_draws.npy", draws)
c1 = json.loads((rec / "soil_lep.json").read_text())["shrink_swell_class"]
assert {k: v["count"] for k, v in c1.items()} == {k: v["parcels"] for k, v in R["clay_contrast"]["by_class"].items()}, c1

# ---- coverage
cov = pd.read_csv(coverage)
R["coverage"] = {fam: {k: dict(min=int(s[k].min()), median=float(s[k].median()), max=int(s[k].max()))
                       for k in ("valid", "houses_valid", "construction_mask", "valid_before_construction_mask")}
                 for fam, s in cov.groupby("family")}
R["full_period_pixels"] = dict(subset=int(v.size), valid_subset=int(ok.sum()), inside_city=int(Z["inside_city"].sum()),
                               valid_inside_city=int((ok & Z["inside_city"]).sum()),
                               house_pixels=int(len(z["r"])), valid_house_pixels=int(good[z["r"], z["c"]].sum()))
R["outputs"] = {p.name: sha256(p) for p in sorted(out.iterdir())}
(out / "checks.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
print(json.dumps({k: R[k] for k in ("sign_check", "clay_contrast", "full_period_pixels")}, indent=1, default=str))
