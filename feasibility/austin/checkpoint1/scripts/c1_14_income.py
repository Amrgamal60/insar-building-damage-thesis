"""Checkpoint 1 (AUSTIN_PLAN §9): neighbourhood income for the eligible houses, and the
income safeguard.

Median household income (ACS 2011-2015 five-year, table B19013, 2015 dollars) of the 2015
block group that contains the parcel point; the tract median where the block-group median is
not published; missing otherwise. The summary-file reading and the definition of a valid
median are the step-0 functions (step0/scripts_acs/build_acs_income_availability.py),
imported unchanged. A point on a boundary that meets exactly one block group takes it.
Safeguard (§9): income stays in Baseline 1 unless it is missing for more than 10% of
eligible parcels. No outcome and no InSAR value is read.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "step0" / "scripts_acs"))
import build_acs_income_availability as acs  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--acs-dir", type=Path, required=True)
p.add_argument("--grid", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)
sf = a.acs_dir / "summary_file_2015_5yr"
tiger = a.acs_dir / "tiger2015_bg" / "tl_2015_48_bg.zip"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


seq, start = acs.lookup_b19013(sf / "ACS_5yr_Seq_Table_Number_Lookup.txt")
assert seq == "0059"
field_index = start - 1  # as step 0
records, checks = acs.load_geographies(sf / "extracted" / "g20155tx.csv", sf / "extracted" / "e20155tx0059000.txt",
                                       sf / "extracted" / "m20155tx0059000.txt", field_index)
assert checks["geoid_constructed_mismatches"] == 0 and checks["unexpected_name"] == 0
bg = {r["geoid"]: r for r in records if r["sumlevel"] == "150"}
tr = {r["geoid"]: r for r in records if r["sumlevel"] == "140"}
S = dict(inputs={f.name: sha(f) for f in (sf / "extracted" / "e20155tx0059000.txt", sf / "extracted" / "m20155tx0059000.txt",
                                           sf / "extracted" / "g20155tx.csv", tiger)},
         table="B19013 (sequence 0059)", block_groups=len(bg), block_groups_valid=sum(r["estimate_label"] == "valid" for r in bg.values()),
         tracts=len(tr), tracts_valid=sum(r["estimate_label"] == "valid" for r in tr.values()))
assert (S["block_groups"], S["block_groups_valid"], S["tracts"], S["tracts_valid"]) == (580, 568, 218, 215)

g = pd.read_parquet(a.grid, columns=["prop_id", "x", "y"])
pts = gpd.GeoDataFrame(g[["prop_id"]], geometry=gpd.points_from_xy(g.x, g.y), crs=32614)
t = gpd.read_file(tiger)
t = t.loc[t.COUNTYFP.eq("453"), ["GEOID", "geometry"]].to_crs(32614)
assert set(t.GEOID) == set(bg)
j = gpd.sjoin(pts, t, how="left", predicate="within")
assert not j.prop_id.duplicated().any()
j["GEOID"] = j.GEOID.astype(object)
miss = j.GEOID.isna()
if miss.any():
    j2 = gpd.sjoin(pts[miss.to_numpy()], t, how="left", predicate="intersects")
    one = j2.groupby("prop_id").GEOID.agg(lambda s: s.dropna().unique().tolist())
    fix = {k: v[0] for k, v in one.items() if len(v) == 1}
    j.loc[miss, "GEOID"] = j.loc[miss, "prop_id"].map(fix)
    S["boundary_assignments"] = len(fix)
out = pd.DataFrame(dict(prop_id=j.prop_id.to_numpy(), bg_geoid=j.GEOID.to_numpy()))
val = lambda d, k: d[k]["estimate_value"] if k in d and d[k]["estimate_label"] == "valid" else np.nan
moe = lambda d, k: d[k]["moe_value"] if k in d and d[k]["estimate_label"] == "valid" and d[k]["moe_label"] == "usable" else np.nan
b_inc = out.bg_geoid.map(lambda k: val(bg, k) if isinstance(k, str) else np.nan)
t_inc = out.bg_geoid.map(lambda k: val(tr, k[:11]) if isinstance(k, str) else np.nan)
out["income_source"] = np.where(b_inc.notna(), "block group", np.where(t_inc.notna(), "tract", "none"))
out["income_usd_2015"] = b_inc.where(b_inc.notna(), t_inc)
b_moe = out.bg_geoid.map(lambda k: moe(bg, k) if isinstance(k, str) else np.nan)
t_moe = out.bg_geoid.map(lambda k: moe(tr, k[:11]) if isinstance(k, str) else np.nan)
out["income_moe"] = np.where(out.income_source.eq("block group"), b_moe, np.where(out.income_source.eq("tract"), t_moe, np.nan))
assert (out.income_usd_2015.dropna() > 0).all()
out["log_income"] = np.log(out.income_usd_2015)
out.to_parquet(a.out_private / "income_2015.parquet", index=False)
n = len(out)
missing = int(out.income_usd_2015.isna().sum())
rm = (out.income_moe / out.income_usd_2015).dropna()
S.update(eligible_houses=n, no_block_group=int(out.bg_geoid.isna().sum()),
         by_source={k: dict(count=int(v), percent=round(100 * v / n, 3)) for k, v in out.income_source.value_counts().items()},
         missing=dict(count=missing, percent=round(100 * missing / n, 3)),
         safeguard=dict(threshold_percent=10, income_in_baseline_1=bool(missing / n <= 0.10)),
         income_usd_2015=out.income_usd_2015.describe().round(0).to_dict(),
         relative_margin_of_error=dict(houses_with_a_margin=int(len(rm)), median=round(float(rm.median()), 3), p90=round(float(rm.quantile(0.9)), 3),
                                       houses_above_half=int((rm > 0.5).sum()), percent_above_half=round(100 * float((rm > 0.5).sum()) / n, 2)),
         block_groups_used=int(out.bg_geoid.nunique()),
         private_outputs_sha256={"income_2015.parquet": sha(a.out_private / "income_2015.parquet")})
a.out_json.write_text(json.dumps(S, indent=1, default=float) + "\n")
print(json.dumps(S, indent=1, default=float))
