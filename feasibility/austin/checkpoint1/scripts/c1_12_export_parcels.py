"""Checkpoint 1: name-free parcel polygons of the eligible houses, for the terrain and canopy
features (AUSTIN_PLAN §9), which are computed on the processing server.

The polygons are built exactly as in c1_03_population_2018.py (2018 parcel layer, made valid,
rows of one property dissolved, EPSG:32614). Only PROP_ID and geometry are read from the
layer. The output holds prop_id and geometry: no owner, no address.
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
p.add_argument("--parcels-zip", type=Path, required=True)
p.add_argument("--grid", type=Path, required=True)
p.add_argument("--reference", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)

g = pd.read_parquet(a.grid, columns=["prop_id", "x", "y"])
pop = pd.read_parquet(a.reference / "population_2018.parquet", columns=["prop_id", "lot_area_m2"])
poly = pyogrio.read_dataframe(f"/vsizip/{a.parcels_zip}/2018_Shapefiles/Parcel_poly.shp", columns=["PROP_ID"]).to_crs(32614)
poly["prop_id"] = poly.PROP_ID.astype("int64").astype(str).str.zfill(12)
poly = poly[poly.prop_id.isin(set(g.prop_id)) & poly.geometry.notna() & ~poly.geometry.is_empty].copy()
poly["geometry"] = shapely.make_valid(poly.geometry.to_numpy())
poly = poly.dissolve(by="prop_id", as_index=False, aggfunc="first")[["prop_id", "geometry"]]
poly = poly.sort_values("prop_id").reset_index(drop=True)
m = poly.merge(g, on="prop_id", validate="one_to_one").merge(pop, on="prop_id", validate="one_to_one")
assert len(m) == len(g) == len(poly)
c = m.geometry.centroid
assert np.allclose(c.x, m.x, atol=1e-6) and np.allclose(c.y, m.y, atol=1e-6)
assert np.allclose(m.geometry.area, m.lot_area_m2, rtol=1e-9)
out = a.out_private / "parcels_eligible_32614.parquet"
gpd.GeoDataFrame(poly, geometry="geometry", crs=32614).to_parquet(out, index=False)
b = poly.total_bounds
S = dict(file=out.name, sha256=hashlib.sha256(out.read_bytes()).hexdigest(), bytes=out.stat().st_size, parcels=len(poly),
         columns=["prop_id", "geometry"], crs="EPSG:32614", bounds=[round(float(v), 1) for v in b],
         geometry_types=poly.geometry.geom_type.value_counts().to_dict(),
         centroid_and_area_equal_to_population_table=True)
a.out_json.write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps(S, indent=1))
