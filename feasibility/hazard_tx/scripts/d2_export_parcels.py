"""Step 0, Dallas (HAZARD_TX draft): name-free parcel polygons of the reference houses, for the server terrain step
(Austin's checkpoint1/scripts/server/s1_dem.py, used unchanged). Columns: prop_id (= DCAD GIS_PARCEL_ID) and the 2022
polygon in EPSG:32614, repaired and dissolved exactly as in d0_population.py. Outcome-blind.

Usage: python -I scripts/d2_export_parcels.py --parcel-zip P --population F --out F --out-json F
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--parcel-zip", type=Path, required=True)
p.add_argument("--population", type=Path, required=True)
p.add_argument("--out", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
assert not a.out.exists()
h = pd.read_parquet(a.population, columns=["GIS_PARCEL_ID"])
with zipfile.ZipFile(a.parcel_zip) as pz:
    shp = [n for n in pz.namelist() if n.lower().endswith(".shp")]
parc = gpd.read_file(f"zip://{a.parcel_zip}!{shp[0]}", engine="pyogrio", columns=["Acct"])
parc["Acct"] = parc.Acct.astype(str).str.strip()
parc = parc[parc.geometry.notna() & ~parc.geometry.is_empty & parc.Acct.isin(set(h.GIS_PARCEL_ID))].copy()
parc["geometry"] = parc.geometry.make_valid()
if parc.Acct.duplicated().any():
    parc = parc.dissolve(by="Acct", as_index=False)
parc = parc.to_crs(32614).rename(columns={"Acct": "prop_id"})[["prop_id", "geometry"]]
parc = parc.set_index("prop_id").loc[h.GIS_PARCEL_ID].reset_index()
assert len(parc) == len(h) and parc.prop_id.is_unique
parc.to_parquet(a.out, index=False)
b = parc.total_bounds
S = dict(parcels=len(parc), bounds=[float(v) for v in b], crs="EPSG:32614",
         out_sha256=hashlib.sha256(a.out.read_bytes()).hexdigest(),
         population_sha256=hashlib.sha256(a.population.read_bytes()).hexdigest())
a.out_json.write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps(S, indent=1))
