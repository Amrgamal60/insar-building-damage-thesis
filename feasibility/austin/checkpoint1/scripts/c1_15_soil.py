"""Checkpoint 1 (AUSTIN_PLAN §9): soil shrink-swell for the eligible houses, and how many
houses have no value.

Source: NRCS SSURGO for Travis County (survey area TX453), the Web Soil Survey download.
Table columns are located by name through the survey's own layout table (mstabcol).

Method (authors' choices, fixed before any InSAR file is opened):
- Component value: the mean of the representative linear extensibility (lep_r, percent)
  over 0-150 cm, weighted by horizon thickness inside that depth range, over the horizons
  that have a value.
- Map-unit value: the mean of its components' values weighted by the representative
  component percentage (comppct_r), over the components that have a value. A map unit whose
  components have no value (for example urban land, water, pits) is missing.
- Parcel value: the value of the map unit polygon that contains the parcel point (§5).
The NRCS shrink-swell classes of §7 are also given: low (< 3), moderate (3-6), high (6-9),
very high (>= 9). No outcome and no InSAR value is read.
"""
import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--ssurgo-zip", type=Path, required=True)
p.add_argument("--grid", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)
z = zipfile.ZipFile(a.ssurgo_zip)
TOP, BOTTOM = 0.0, 150.0


def table(name):
    return list(csv.reader(io.TextIOWrapper(z.open(f"TX453/tabular/{name}.txt"), encoding="latin-1"), delimiter="|"))


layout = defaultdict(list)
for r in table("mstabcol"):
    layout[r[0]].append((int(r[1]), r[2]))
files = {r[0]: r[4] for r in table("mstab")}


def frame(logical, cols):
    names = [c for _, c in sorted(layout[logical])]
    rows = table(files[logical])
    assert all(len(r) == len(names) for r in rows), logical
    return pd.DataFrame([[r[names.index(c)] for c in cols] for r in rows], columns=cols)


num = lambda s: pd.to_numeric(s.replace("", np.nan))
hz = frame("chorizon", ["cokey", "chkey", "hzdept_r", "hzdepb_r", "lep_r"])
co = frame("component", ["mukey", "cokey", "comppct_r", "compname", "compkind", "majcompflag"])
mu = frame("mapunit", ["mukey", "musym", "muname", "mukind"])
for c in ("hzdept_r", "hzdepb_r", "lep_r"):
    hz[c] = num(hz[c])
co["comppct_r"] = num(co.comppct_r)
hz["thick"] = (hz.hzdepb_r.clip(upper=BOTTOM) - hz.hzdept_r.clip(lower=TOP)).clip(lower=0)
h = hz[hz.lep_r.notna() & hz.thick.gt(0)]
cv = h.assign(w=h.lep_r * h.thick).groupby("cokey").agg(w=("w", "sum"), t=("thick", "sum"))
co["lep"] = co.cokey.map(cv.w / cv.t)
co["depth_with_value_cm"] = co.cokey.map(cv.t)
c = co[co.lep.notna() & co.comppct_r.gt(0)]
mv = c.assign(w=c.lep * c.comppct_r).groupby("mukey").agg(w=("w", "sum"), pct=("comppct_r", "sum"))
mu["lep"] = mu.mukey.map(mv.w / mv.pct)
mu["comppct_with_value"] = mu.mukey.map(mv.pct).fillna(0)
mu["comppct_total"] = mu.mukey.map(co.groupby("mukey").comppct_r.sum())

soil = gpd.read_file(f"/vsizip/{a.ssurgo_zip}/TX453/spatial/soilmu_a_tx453.shp")
assert soil.crs.to_epsg() == 4326
soil = soil[["MUKEY", "MUSYM", "geometry"]].to_crs(32614)
g = pd.read_parquet(a.grid, columns=["prop_id", "x", "y"])
pts = gpd.GeoDataFrame(g[["prop_id"]], geometry=gpd.points_from_xy(g.x, g.y), crs=32614)
j = gpd.sjoin(pts, soil, how="left", predicate="within")
dup = j.prop_id.duplicated(keep=False)
n_dup = int(j.loc[dup, "prop_id"].nunique())
j = j.sort_values(["prop_id", "MUKEY"]).drop_duplicates("prop_id")
out = pd.DataFrame(dict(prop_id=j.prop_id.to_numpy(), mukey=j.MUKEY.astype(object).to_numpy()))
out = out.merge(mu[["mukey", "musym", "muname", "lep", "comppct_with_value"]], on="mukey", how="left").sort_values("prop_id").reset_index(drop=True)
out = out.rename(columns={"lep": "lep_0_150"})
out["shrink_swell_class"] = pd.cut(out.lep_0_150, [-np.inf, 3, 6, 9, np.inf], right=False, labels=["low", "moderate", "high", "very high"]).astype(object)
out.to_parquet(a.out_private / "soil_lep.parquet", index=False)
n = len(out)
miss = out.lep_0_150.isna()
top_missing = out[miss].groupby("muname", dropna=False).size().sort_values(ascending=False).head(8)
S = dict(source=a.ssurgo_zip.name, sha256=hashlib.sha256(a.ssurgo_zip.read_bytes()).hexdigest(),
         survey_area=table("sacatlog")[0][:4], map_units=len(mu), map_units_with_value=int(mu.lep.notna().sum()),
         components=len(co), components_with_value=int(co.lep.notna().sum()), horizons=len(hz), horizons_with_lep=int(hz.lep_r.notna().sum()),
         eligible_houses=n, houses_outside_any_map_unit=int(out.mukey.isna().sum()), houses_in_two_polygons_first_mukey_taken=n_dup,
         missing=dict(count=int(miss.sum()), percent=round(100 * float(miss.mean()), 3)),
         missing_by_map_unit_name={str(k): int(v) for k, v in top_missing.items()},
         houses_whose_value_rests_on_under_half_of_the_map_unit=int((out.comppct_with_value[~miss] < 50).sum()),
         lep_0_150=out.lep_0_150.describe().round(3).to_dict(),
         shrink_swell_class={k: dict(count=int(v), percent=round(100 * v / n, 2)) for k, v in out.shrink_swell_class.value_counts().items()},
         distinct_values=int(out.lep_0_150.nunique()),
         private_outputs_sha256={"soil_lep.parquet": hashlib.sha256((a.out_private / "soil_lep.parquet").read_bytes()).hexdigest()})
a.out_json.write_text(json.dumps(S, indent=1, default=float) + "\n")
print(json.dumps(S, indent=1, default=float))
