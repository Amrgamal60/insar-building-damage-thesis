"""Austin step 0: outcome-blind checks of reference-data options (no permit, InSAR or outcome data are read).

Compares the public September 2019 TxGIO/TNRIS StratMap parcel layer for Travis County (tax year 2019; ArcGIS
mirror downloaded in step 0) with the 2026 certified-roll diagnostic population:
  1. what the 2019 layer holds (tax year, A1 count, year-built fill, whether DATE_ACQ is a deed date);
  2. year-built agreement 2019 vs 2026 for the same detached houses (is year built stable?);
  3. survivorship: 2019 A1 houses built <= 2015 inside the Austin full-purpose boundary, by 2026 status;
  4. lot-area agreement 2019 vs 2026 polygons.
Writes aggregate counts only.

usage: python -I refdata_checks.py <Alex_private/austin> <out.json>
"""
import json
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

R, out = sys.argv[1], sys.argv[2]
SHP = ("/vsizip/{" + f"{R}/tcad/raw/www.arcgis.com_e41c24899f71/data" + "}"
       "/stratmap19-landparcels_48453_vector_shp/stratmap19-landparcels_48453_travis_201909.shp")
BOUNDARY = f"{R}/tcad/raw/data.austintexas.gov_27339cbf4a36/vnwj-xmz9.geojson"
POP = f"{R}/tcad/final_population_2026/eligible_2026_diagnostic.parquet"
A1_2026 = f"{R}/tcad/population_checks_2026/a1_parcel_polygons.parquet"
rep = {"source_2019": "stratmap19-landparcels_48453_travis_201909 (TxGIO/TNRIS StratMap, ArcGIS mirror, step 0)"}

g = pyogrio.read_dataframe(SHP, columns=["PROP_ID", "STAT_LAND_", "TAX_YEAR", "YEAR_BUILT", "DATE_ACQ"]).to_crs(32614)
g["pid"] = pd.to_numeric(g.PROP_ID, errors="coerce")
a1 = g.STAT_LAND_.astype(str).str.strip().str.upper().str.startswith("A1")
rep["layer_2019"] = {
    "rows": len(g),
    "tax_year_counts": {str(k): int(v) for k, v in g.TAX_YEAR.value_counts().items()},
    "a1_rows": int(a1.sum()),
    "a1_year_built_positive": int((g.YEAR_BUILT[a1] > 0).sum()),
    "date_acq_distinct_values": sorted({str(v) for v in g.DATE_ACQ.unique()})[:5],
    "note": "DATE_ACQ is the data acquisition month, not a deed date; the layer has no improvement type, living area or foundation",
}

# 2 and 4: same houses, 2019 vs 2026
pop = pd.read_parquet(POP, columns=["prop_id_numeric", "imprv_type_cd", "year_built", "polygon_area_m2"])
pop = pop[pop.imprv_type_cd == "01"]
k = g.assign(area19=g.geometry.area).dropna(subset=["pid"])
yb19 = k.drop_duplicates("pid").set_index("pid").YEAR_BUILT
area19 = k.groupby("pid").area19.sum()
m = pop.set_index("prop_id_numeric")
y19 = yb19.reindex(m.index)
y26 = pd.to_numeric(m.year_built, errors="coerce")
both = y19 > 0
r = m.polygon_area_m2.values / area19.reindex(m.index).values
ok = np.isfinite(r)
rep["same_houses_2019_vs_2026"] = {
    "detached_2026": len(m),
    "found_in_2019_by_prop_id": int(y19.notna().sum()),
    "year_built_compared": int(both.sum()),
    "year_built_identical": int((y19[both] == y26[both]).sum()),
    "lot_area_compared": int(ok.sum()),
    "lot_area_within_1pct": int((np.abs(r[ok] - 1) <= 0.01).sum()),
    "lot_area_within_5pct": int((np.abs(r[ok] - 1) <= 0.05).sum()),
}

# 3: survivorship of 2019 houses
h = g[a1 & g.YEAR_BUILT.between(1, 2015) & g.geometry.notna() & ~g.geometry.is_empty]
b = gpd.read_file(BOUNDARY).to_crs(32614)
c = gpd.GeoDataFrame({"pid": h.pid.values}, geometry=h.geometry.centroid.values, crs=32614)
c = c[c.within(b.union_all())].dropna(subset=["pid"]).drop_duplicates("pid")
s26 = pd.read_parquet(A1_2026, columns=["prop_id_numeric", "imprv_type_cd", "year_built"]).drop_duplicates("prop_id_numeric")
mm = c.merge(s26, left_on="pid", right_on="prop_id_numeric", how="left")
yb = pd.to_numeric(mm.year_built, errors="coerce")
cat = pd.Series("not A1 in 2026, or property ID changed", index=mm.index)
cat[mm.prop_id_numeric.notna() & (yb > 2015)] = "A1 in 2026, rebuilt (year built after 2015)"
cat[mm.prop_id_numeric.notna() & (yb <= 2015) & (mm.imprv_type_cd != "01")] = "A1 in 2026, main improvement not type 01"
cat[mm.pid.isin(set(pop.prop_id_numeric))] = "in the 2026 detached population"
rep["survivorship_2019_to_2026"] = {
    "boundary": "vnwj-xmz9 version of 2026-10-27 (same as step 0), used for both years",
    "a1_built_by_2015_inside_2019": len(c),
    "by_2026_status": {k2: int(v) for k2, v in cat.value_counts().items()},
    "rebuilt_year_built_counts": {str(int(k2)): int(v) for k2, v in yb[cat.str.contains("rebuilt")].value_counts().sort_index().items()},
}
json.dump(rep, open(out, "w"), indent=1)
print(json.dumps(rep, indent=1))
