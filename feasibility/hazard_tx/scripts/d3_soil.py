"""Step 0 (HAZARD_TX draft): soil shrink-swell for the reference houses of one city. Outcome-blind.

Source: the NRCS gSSURGO Texas file geodatabase (gSSURGO_TX.gdb, from the NRCS Box share; survey versions in the
sacatalog table). Method: the Austin rule (feasibility/austin/checkpoint1/scripts/c1_15_soil.py), unchanged:
- Component value: the mean of the representative linear extensibility (lep_r, percent) over 0-150 cm, weighted by
  horizon thickness inside that depth range, over the horizons that have a value.
- Map-unit value: the mean of its components' values weighted by comppct_r, over the components that have a value.
  A map unit whose components have no value (urban land, water, pits) is missing.
- House value: the value of the map-unit polygon that contains the house point; if two polygons contain it, the
  smaller MUKEY is taken (Austin's sort), and this is counted.
NRCS shrink-swell classes: low (< 3), moderate (3-6), high (6-9), very high (>= 9).
Only reading differs from Austin: tables come from the geodatabase instead of the WSS text files, and polygons are
read for the houses' bounding box (+1 km) from the seamless MUPOLYGON layer instead of one survey's shapefile.

Usage: python -I scripts/d3_soil.py --gdb G --population F --id-col ACCOUNT_NUM --out-private DIR --out-json F
"""
import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

p = argparse.ArgumentParser()
p.add_argument("--gdb", type=Path, required=True)
p.add_argument("--archive", type=Path, help="the downloaded .7z, hashed into the record")
p.add_argument("--population", type=Path, required=True)
p.add_argument("--id-col", default="ACCOUNT_NUM")
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)
TOP, BOTTOM = 0.0, 150.0


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def tab(name, cols, where=None):
    d = pyogrio.read_dataframe(a.gdb, layer=name, columns=cols, read_geometry=False, where=where)
    return pd.DataFrame(d)


g = pd.read_parquet(a.population, columns=[a.id_col, "x", "y"]).rename(columns={a.id_col: "hid"})
pts = gpd.GeoDataFrame(g[["hid"]], geometry=gpd.points_from_xy(g.x, g.y), crs=32614)
info = pyogrio.read_info(a.gdb, layer="MUPOLYGON")
bb = gpd.GeoSeries(gpd.points_from_xy([g.x.min() - 1000, g.x.max() + 1000], [g.y.min() - 1000, g.y.max() + 1000]),
                   crs=32614).to_crs(info["crs"]).total_bounds
soil = pyogrio.read_dataframe(a.gdb, layer="MUPOLYGON", columns=["AREASYMBOL", "MUSYM", "MUKEY"], bbox=tuple(bb))
soil = soil.to_crs(32614)
j = gpd.sjoin(pts, soil[["MUKEY", "AREASYMBOL", "geometry"]], how="left", predicate="within")
dup = j.hid.duplicated(keep=False)
n_dup = int(j.loc[dup, "hid"].nunique())
j = j.sort_values(["hid", "MUKEY"]).drop_duplicates("hid")
mukeys = sorted(set(j.MUKEY.dropna().astype(str)))
quoted = ",".join(f"'{k}'" for k in mukeys)
mu = tab("mapunit", ["mukey", "musym", "muname", "mukind"], where=f"mukey IN ({quoted})")
co = tab("component", ["mukey", "cokey", "comppct_r", "compname", "compkind", "majcompflag"], where=f"mukey IN ({quoted})")
ck = ",".join(f"'{k}'" for k in co.cokey.astype(str))
hz = tab("chorizon", ["cokey", "chkey", "hzdept_r", "hzdepb_r", "lep_r"], where=f"cokey IN ({ck})")
for c in ("hzdept_r", "hzdepb_r", "lep_r"):
    hz[c] = pd.to_numeric(hz[c])
co["comppct_r"] = pd.to_numeric(co.comppct_r)
hz["thick"] = (hz.hzdepb_r.clip(upper=BOTTOM) - hz.hzdept_r.clip(lower=TOP)).clip(lower=0)
h = hz[hz.lep_r.notna() & hz.thick.gt(0)]
cv = h.assign(w=h.lep_r * h.thick).groupby("cokey").agg(w=("w", "sum"), t=("thick", "sum"))
co["lep"] = co.cokey.map(cv.w / cv.t)
c = co[co.lep.notna() & co.comppct_r.gt(0)]
mv = c.assign(w=c.lep * c.comppct_r).groupby("mukey").agg(w=("w", "sum"), pct=("comppct_r", "sum"))
mu["lep"] = mu.mukey.map(mv.w / mv.pct)
mu["comppct_with_value"] = mu.mukey.map(mv.pct).fillna(0)

out = pd.DataFrame(dict(hid=j.hid.to_numpy(), mukey=j.MUKEY.astype(object).to_numpy(), areasymbol=j.AREASYMBOL.to_numpy()))
out = out.merge(mu[["mukey", "musym", "muname", "lep", "comppct_with_value"]], on="mukey", how="left")
out = out.set_index("hid").loc[g.hid].reset_index().rename(columns={"hid": a.id_col, "lep": "lep_0_150"})
out["shrink_swell_class"] = pd.cut(out.lep_0_150, [-np.inf, 3, 6, 9, np.inf], right=False,
                                   labels=["low", "moderate", "high", "very high"]).astype(object)
out.to_parquet(a.out_private / "soil_lep.parquet", index=False)
n = len(out)
miss = out.lep_0_150.isna()
sac = tab("sacatalog", ["areasymbol", "areaname", "saverest"])
areas = sorted(set(out.areasymbol.dropna()))
S = dict(source="gSSURGO_TX.gdb (NRCS Box share)", archive_sha256=sha(a.archive) if a.archive else None,
         survey_areas={r.areasymbol: dict(name=r.areaname, saverest=str(r.saverest)) for r in sac.itertuples() if r.areasymbol in areas},
         houses_by_survey_area={str(k): int(v) for k, v in out.areasymbol.value_counts(dropna=False).items()},
         map_units=len(mu), map_units_with_value=int(mu.lep.notna().sum()),
         components=len(co), components_with_value=int(co.lep.notna().sum()), horizons=len(hz), horizons_with_lep=int(hz.lep_r.notna().sum()),
         houses=n, houses_outside_any_map_unit=int(out.mukey.isna().sum()), houses_in_two_polygons_first_mukey_taken=n_dup,
         missing=dict(count=int(miss.sum()), percent=round(100 * float(miss.mean()), 3)),
         missing_by_map_unit_name={str(k): int(v) for k, v in out[miss].groupby("muname", dropna=False).size().sort_values(ascending=False).head(8).items()},
         houses_whose_value_rests_on_under_half_of_the_map_unit=int((out.comppct_with_value[~miss] < 50).sum()),
         lep_0_150=out.lep_0_150.describe().round(3).to_dict(),
         shrink_swell_class={k: dict(count=int(v), percent=round(100 * v / n, 2)) for k, v in out.shrink_swell_class.value_counts().items()},
         population_sha256=sha(a.population),
         private_outputs_sha256={"soil_lep.parquet": sha(a.out_private / "soil_lep.parquet")},
         note="Outcome-blind: no permit or outcome file was opened.")
a.out_json.write_text(json.dumps(S, indent=1, default=float) + "\n")
print(json.dumps(S, indent=1, default=float))
