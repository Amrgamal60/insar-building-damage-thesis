"""Checkpoint 1 (AUSTIN_PLAN §5, option A): the 2018 reference population and its feature completeness.

Inputs (all private): the step-0 reader's tables for the 2018 roll (derived_2018, from
step0/scripts/inspect_roll.py, unchanged) and its field table (static_checks_2018, from
step0/scripts/static_checks.py, unchanged: main dwelling = largest living-floor area among
types 01/16, tie by imprv_id; year built = first-floor year, zero missing); the TCAD 2018
parcel layer (zip); the checkpoint-1 full-purpose boundary; the step-0 2026 roll, 2026
diagnostic population and 2019 crosswalk, for comparison only.

Only PROP_ID, PID_10 and geometry are read from the parcel layer (no situs address).
Row-level output goes to OUT_PRIVATE; the project JSON holds counts only.
No permit, outcome or InSAR data is read.
"""
import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely

p = argparse.ArgumentParser()
p.add_argument("--derived", type=Path, required=True)
p.add_argument("--fields", type=Path, required=True)
p.add_argument("--parcels-zip", type=Path, required=True)
p.add_argument("--boundary", type=Path, required=True)
p.add_argument("--roll-2026", type=Path, required=True)
p.add_argument("--diag-2026", type=Path, required=True)
p.add_argument("--crosswalk-2019", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)
S = {}


def norm(s):
    # As step0/scripts_refdata/id_crosswalk.py norm_geo: strip, blank -> missing, leading zeros dropped.
    s = s.astype("string").str.strip()
    return s.mask(s.eq("")).str.lstrip("0").mask(lambda v: v.eq(""))


def pct(k, n):
    return dict(count=int(k), denominator=int(n), percent=round(100 * k / n, 3) if n else None)


# ---- roll ----
prop = pd.read_parquet(a.derived / "PROP.TXT.parquet")
fields = pd.read_parquet(a.fields)
S["roll"] = dict(properties=len(prop), prop_val_yr=prop.prop_val_yr.value_counts().to_dict(),
                 sup_num=prop.sup_num.value_counts().to_dict(), a1_real_parcels=len(fields),
                 main_dwelling_type=fields.imprv_type_cd.fillna("MISSING").value_counts().to_dict())
info = pd.read_parquet(a.derived / "IMP_INFO.TXT.parquet")
has01 = set(info.loc[info.imprv_type_cd.eq("01"), "prop_id"])
S["roll"]["main_16_but_has_a_type01_improvement"] = int((fields.imprv_type_cd.eq("16") & fields.prop_id.isin(has01)).sum())
S["roll"]["year_built_after_2018_on_main"] = int(fields.year_built.gt(2018).sum())

# ---- parcel layer ----
src = f"/vsizip/{a.parcels_zip}/2018_Shapefiles/Parcel_poly.shp"
poly = pyogrio.read_dataframe(src, columns=["PROP_ID", "PID_10"])
bak = pyogrio.read_dataframe(f"/vsizip/{a.parcels_zip}/2018_Shapefiles/_parcel_poly_bak.shp", columns=["PROP_ID"])
key = lambda g: set(zip(g.PROP_ID.astype("int64"), [hashlib.sha1(w or b"").hexdigest() for w in shapely.to_wkb(g.geometry.to_numpy())]))
S["layer"] = dict(file="2018_Shapefiles/Parcel_poly.shp", crs=str(poly.crs), features=len(poly),
                  prop_id_zero_or_null=int(poly.PROP_ID.isna().sum() + poly.PROP_ID.eq(0).sum()),
                  unique_prop_ids=int(poly.PROP_ID.nunique()),
                  prop_ids_with_several_rows=int(poly.PROP_ID.value_counts().gt(1).sum()),
                  null_or_empty_geometry=int((poly.geometry.isna() | poly.geometry.is_empty).sum()),
                  invalid_geometry=int((~poly.geometry.is_valid).sum()),
                  backup_layer_identical_prop_id_and_geometry=key(poly) == key(bak))
del bak
poly = poly.to_crs(32614)
poly["prop_id"] = poly.PROP_ID.astype("int64").astype(str).str.zfill(12)
roll_keys = prop[["prop_id", "geo_id", "prop_type_cd", "imprv_state_cd"]].copy()
roll_keys["geo"] = norm(roll_keys.geo_id)
S["layer"]["prop_ids_in_roll"] = int(poly.drop_duplicates("prop_id").prop_id.isin(set(prop.prop_id)).sum())
pid10 = poly.drop_duplicates("prop_id").merge(roll_keys[["prop_id", "geo"]], on="prop_id", how="inner")
pid10["pid10"] = norm(pid10.PID_10)
S["layer"]["pid10_equals_roll_geo_id"] = pct(pid10.pid10.eq(pid10.geo).sum(), len(pid10))

# ---- A1 parcels with polygons (as step0/scripts/population_checks.py) ----
a1 = poly[poly.prop_id.isin(set(fields.prop_id)) & poly.geometry.notna() & ~poly.geometry.is_empty].copy()
invalid_before = int((~a1.geometry.is_valid).sum())
a1["geometry"] = shapely.make_valid(a1.geometry.to_numpy())
dup = int(a1.prop_id.duplicated().sum())
a1 = a1.dissolve(by="prop_id", as_index=False, aggfunc="first")[["prop_id", "geometry"]]
a1["lot_area_m2"] = a1.geometry.area
pt = a1.geometry.centroid
a1["x"], a1["y"] = pt.x, pt.y
a1["valid_point"] = ~pt.is_empty & np.isfinite(a1.x) & np.isfinite(a1.y)
S["a1_polygons"] = dict(a1_parcels_with_polygon=len(a1), a1_parcels_without_polygon=int((~fields.prop_id.isin(set(a1.prop_id))).sum()),
                        invalid_before_make_valid=invalid_before, duplicate_rows_dissolved=dup,
                        invalid_point=int((~a1.valid_point).sum()))

# ---- study area ----
b = gpd.read_file(a.boundary)
assert set(b.jurisdiction_type) == {"FULL"} and set(b.city_name) == {"CITY OF AUSTIN"}
city = shapely.union_all(b.to_crs(32614).geometry.to_numpy())
if not shapely.is_valid(city):
    city = shapely.make_valid(city)
shapely.prepare(city)
pts = shapely.points(a1.x.to_numpy(), a1.y.to_numpy())
a1["inside"] = a1.valid_point & shapely.within(pts, city)
S["boundary"] = dict(file=a.boundary.name, sha256=hashlib.sha256(a.boundary.read_bytes()).hexdigest(),
                     features=len(b), area_km2=round(city.area / 1e6, 3),
                     a1_points_on_boundary_line=int(shapely.touches(pts, city).sum()))

# ---- population (§5) ----
f = fields.merge(a1, on="prop_id", how="left", validate="one_to_one")
f = f.merge(roll_keys[["prop_id", "geo_id", "geo"]].rename(columns={"geo_id": "geo_id_roll"}), on="prop_id", how="left", validate="one_to_one")
steps = [("A1 real-property parcels in the 2018 roll", pd.Series(True, index=f.index)),
         ("main improvement type 01 (1 FAM DWELLING)", f.imprv_type_cd.eq("01")),
         ("year built 1..2015 (first floor of main dwelling)", f.year_built.between(1, 2015)),
         ("polygon in the 2018 parcel layer", f.prop_id.isin(set(a1.prop_id))),
         ("valid parcel point", f.valid_point.fillna(False).astype(bool)),
         ("point inside the full-purpose boundary", f.inside.fillna(False).astype(bool))]
mask = pd.Series(True, index=f.index)
S["flow"] = []
for label, m in steps:
    mask &= m
    S["flow"].append(dict(step=label, remaining=int(mask.sum())))
pre = f[mask].copy()
mult = pre.groupby("geo").prop_id.transform("nunique")
amb = pre.geo.isna() | mult.gt(1)
S["flow"].append(dict(step="minus houses whose 2018 geo_id is shared by another house (rule 3) or blank",
                      removed=int(amb.sum()), ambiguous_geo_ids=int(pre.loc[mult.gt(1), "geo"].nunique()),
                      remaining=int((~amb).sum())))
pop = pre[~amb].copy()
S["excluded_for_information"] = dict(
    townhouse_main_type16_built_by_2015_inside=int((f.imprv_type_cd.eq("16") & f.year_built.between(1, 2015) & f.inside.fillna(False).astype(bool)).sum()),
    main_dwelling_missing=int(f.imprv_type_cd.isna().sum()))
other = roll_keys[~roll_keys.prop_id.isin(set(pop.prop_id))]
S["population_geo_ids_shared_with_a_non_population_roll_parcel"] = int(pop.geo.isin(set(other.geo.dropna())).sum())
pop["cell_x"] = np.floor(pop.x / 30).astype("int64")
pop["cell_y"] = np.floor(pop.y / 30).astype("int64")
S["population"] = dict(houses=len(pop), unique_30m_cells=int(len(pop[["cell_x", "cell_y"]].drop_duplicates())))

# ---- completeness of Baseline 1 inputs from the 2018 reference data (§9) ----
n = len(pop)
fd = pop.foundation.fillna("")
only_sp = fd.ne("") & fd.map(lambda s: set(s.split(" | ")) <= {"SLAB", "PIER AND B"})
dates = pd.to_datetime(pop.deed_dt, format="mixed", errors="coerce")
S["completeness"] = dict(
    year_built_positive=pct(pop.year_built.gt(0).sum(), n),
    living_area_positive=pct(pop.living_area.gt(0).sum(), n),
    lot_area_polygon_positive=pct(pop.lot_area_m2.gt(0).sum(), n),
    foundation_any_code=pct(fd.ne("").sum(), n),
    foundation_slab_or_pier_and_beam_only=pct(only_sp.sum(), n),
    foundation_single_slab_or_single_pier_and_beam=pct(fd.isin(["SLAB", "PIER AND B"]).sum(), n),
    foundation_categories=fd.replace("", "(blank)").value_counts().to_dict(),
    deed_date_parseable_not_in_baseline=pct(dates.notna().sum(), n),
    land_table_square_feet_positive_comparison_only=pct(pop.size_square_feet.gt(0).sum(), n),
    year_built_range=[int(pop.year_built.min()), int(pop.year_built.max())],
    living_area_sqft_quartiles=[float(q) for q in pop.living_area.quantile([.25, .5, .75])],
    lot_area_m2_quartiles=[round(float(q), 1) for q in pop.lot_area_m2.quantile([.25, .5, .75])],
    polygon_vs_land_table_area_ratio_median=round(float((pop.lot_area_m2 / (pop.size_square_feet * 0.09290304)).median()), 4))

# ---- comparisons (reported only; no rule depends on them) ----
p26 = set(pd.read_parquet(a.roll_2026, columns=["prop_id"]).prop_id)
d26 = pd.read_parquet(a.diag_2026, columns=["prop_id", "imprv_type_cd"])
xw = pd.read_parquet(a.crosswalk_2019, columns=["pid19"])
pid19 = set(xw.pid19.astype("int64").astype(str).str.zfill(12))
pop["prop_id_in_2026_roll"] = pop.prop_id.isin(p26)
S["comparison"] = dict(
    population_2018=len(pop),
    diagnostic_2026_type01=int(d26.imprv_type_cd.eq("01").sum()),
    option_c_2019_before_exclusions=len(xw), option_c_2019_primary_step0=149786,
    population_2018_prop_id_in_2026_roll=pct(pop.prop_id_in_2026_roll.sum(), n),
    population_2018_in_2026_type01_diagnostic=pct(pop.prop_id.isin(set(d26.loc[d26.imprv_type_cd.eq("01"), "prop_id"])).sum(), n),
    population_2018_in_2019_option_c_set=pct(pop.prop_id.isin(pid19).sum(), n),
    option_c_2019_set_in_population_2018=pct(len(pid19 & set(pop.prop_id)), len(pid19)))

cols = ["prop_id", "geo_id_roll", "geo", "imprv_id", "year_built", "living_area", "foundation", "lot_area_m2",
        "size_square_feet", "x", "y", "cell_x", "cell_y", "prop_id_in_2026_roll"]
pop[cols].to_parquet(a.out_private / "population_2018.parquet", index=False)
roll_keys["in_population"] = roll_keys.prop_id.isin(set(pop.prop_id))
roll_keys["a1_real"] = roll_keys.prop_id.isin(set(fields.prop_id))
roll_keys.to_parquet(a.out_private / "roll_keys_2018.parquet", index=False)
a.out_json.write_text(json.dumps(S, indent=1, default=int) + "\n")
print(json.dumps(S, indent=1, default=int))
