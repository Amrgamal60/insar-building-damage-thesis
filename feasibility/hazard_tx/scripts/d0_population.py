"""Step 0, Dallas (HAZARD_TX draft): the reference population of houses on 2022-01-01 and the published
Ohenhen (2025) classes at each house. Outcome-blind: no permit file is opened.

Reference data: the DCAD 2022 certified roll (certified 2022-07-25; it describes each property on 2022-01-01)
and the DCAD 2022 parcel layer. Rules (authors' choices, mirroring the frozen Austin plan §5; draft):
- Single-family residential: state property code A11 (SPTD_CODE; A12 townhouses and A13 condominiums are out),
  division RES, and city jurisdiction DALLAS (the roll's taxing-jurisdiction field, i.e. city limits).
- Main improvement: the residential-detail row with the largest total living area (ties: smallest TAX_OBJ_ID).
  Year built is that row's YR_BUILT (0 or blank is missing). Eligible if built in 2019 or earlier.
- House point: the centroid of the 2022 parcel polygon whose Acct equals the account's GIS_PARCEL_ID, in EPSG:32614.
  A GIS_PARCEL_ID held by more than one A11 account is ambiguous: those accounts are left out and counted.
- Study area: the point lies inside the City of Dallas (TIGER/Line 2021 place 4819000).
- Map classes: risk_dallas.tif and beta_dallas.tif (figshare 27606942), the class of the map cell that contains the
  point (transformed to EPSG:4326); no data gives no class. Hazard flag = beta class 2-3; risk flag = risk class 3-4.

Usage: python -I scripts/d0_population.py --dcad-zip Z --parcel-zip P --place-zip T --ohenhen-dir D
                                          --out-private DIR --out-json FILE
"""
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

p = argparse.ArgumentParser()
p.add_argument("--dcad-zip", type=Path, required=True)
p.add_argument("--parcel-zip", type=Path, required=True)
p.add_argument("--place-zip", type=Path, required=True)
p.add_argument("--ohenhen-dir", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_csv(z, name, cols):
    with z.open(name) as f:
        d = pd.read_csv(io.TextIOWrapper(f, encoding="latin-1"), usecols=cols, dtype=str)
    return d.apply(lambda s: s.str.strip())


inputs = {k: sha256(v) for k, v in dict(dcad_zip=a.dcad_zip, parcel_zip=a.parcel_zip, place_zip=a.place_zip,
                                         beta=a.ohenhen_dir / "beta_dallas.tif", risk=a.ohenhen_dir / "risk_dallas.tif").items()}
flow = {}
z = zipfile.ZipFile(a.dcad_zip)
ay = read_csv(z, "account_apprl_year.csv", ["ACCOUNT_NUM", "APPRAISAL_YR", "DIVISION_CD", "SPTD_CODE", "CITY_JURIS_DESC", "GIS_PARCEL_ID"])
assert set(ay.APPRAISAL_YR) == {"2022"}
flow["roll_accounts"] = len(ay)
h = ay[(ay.SPTD_CODE == "A11") & (ay.DIVISION_CD == "RES") & (ay.CITY_JURIS_DESC == "DALLAS")].copy()
flow["a11_res_city_dallas"] = len(h)
assert not h.ACCOUNT_NUM.duplicated().any()

rd = read_csv(z, "res_detail.csv", ["ACCOUNT_NUM", "TAX_OBJ_ID", "YR_BUILT", "TOT_LIVING_AREA_SF", "NUM_STORIES_DESC",
                                    "FOUNDATION_TYP_DESC", "BLDG_CLASS_DESC", "DESIRABILITY_RATING", "CONSTR_FRAM_TYP_DESC"])
rd = rd[rd.ACCOUNT_NUM.isin(h.ACCOUNT_NUM)].copy()
rd["living"] = pd.to_numeric(rd.TOT_LIVING_AREA_SF, errors="coerce").fillna(-1)
rd = rd.sort_values(["ACCOUNT_NUM", "living", "TAX_OBJ_ID"], ascending=[True, False, True])
flow["accounts_with_several_detail_rows"] = int(rd.ACCOUNT_NUM.duplicated().groupby(rd.ACCOUNT_NUM).any().sum())
rd = rd.drop_duplicates("ACCOUNT_NUM", keep="first")
h = h.merge(rd, on="ACCOUNT_NUM", how="left")
flow["no_residential_detail"] = int(h.TAX_OBJ_ID.isna().sum())
h = h[h.TAX_OBJ_ID.notna()]
yb = pd.to_numeric(h.YR_BUILT, errors="coerce")
h["year_built"] = yb.where(yb > 0)
flow["year_built_missing"] = int(h.year_built.isna().sum())
flow["year_built_after_2019"] = int((h.year_built > 2019).sum())
h = h[h.year_built.notna() & (h.year_built <= 2019)].copy()
flow["built_2019_or_earlier"] = len(h)

amb = h.GIS_PARCEL_ID.duplicated(keep=False)
flow["ambiguous_parcel_id"] = int(amb.sum())
h = h[~amb]
with zipfile.ZipFile(a.parcel_zip) as pz:
    shp = [n for n in pz.namelist() if n.lower().endswith(".shp")]
    assert len(shp) == 1
parc = gpd.read_file(f"zip://{a.parcel_zip}!{shp[0]}", engine="pyogrio", columns=["Acct"])
parc["Acct"] = parc.Acct.astype(str).str.strip()
parc = parc[parc.geometry.notna() & ~parc.geometry.is_empty]
flow["parcel_polygons"] = len(parc)
parc = parc[parc.Acct.isin(set(h.GIS_PARCEL_ID))].copy()
flow["invalid_polygons_repaired"] = int((~parc.geometry.is_valid).sum())
parc["geometry"] = parc.geometry.make_valid()
dup_poly = parc.Acct.duplicated(keep=False)
flow["house_parcels_with_several_polygons"] = int(parc.loc[dup_poly, "Acct"].nunique())
parc = parc.dissolve(by="Acct", as_index=False) if dup_poly.any() else parc
parc = parc.to_crs(32614)
parc["lot_area_m2"] = parc.geometry.area
c = parc.geometry.centroid
parc["x"], parc["y"] = c.x, c.y
h = h.merge(parc[["Acct", "x", "y", "lot_area_m2"]], left_on="GIS_PARCEL_ID", right_on="Acct", how="left")
flow["no_parcel_polygon"] = int(h.x.isna().sum())
h = h[h.x.notna()].copy()

place = gpd.read_file(f"zip://{a.place_zip}", engine="pyogrio")
city = place[place.GEOID == "4819000"].to_crs(32614)
assert len(city) == 1
pts = gpd.GeoSeries(gpd.points_from_xy(h.x, h.y), crs=32614)
inside = pts.within(city.geometry.iloc[0]).to_numpy()
flow["point_outside_city"] = int((~inside).sum())
h = h[inside].copy()
flow["eligible"] = len(h)

lon, lat = Transformer.from_crs(32614, 4326, always_xy=True).transform(h.x.to_numpy(), h.y.to_numpy())
for lay in ("beta", "risk"):
    with rasterio.open(a.ohenhen_dir / f"{lay}_dallas.tif") as r:
        v = np.array([s[0] for s in r.sample(zip(lon, lat))], dtype=float)
        nd = r.nodata
    v[(~np.isfinite(v)) | ((v == nd) if nd is not None else False)] = np.nan
    h[f"{lay}_class"] = v
h["hazard_flag"] = np.where(h.beta_class.notna(), (h.beta_class >= 2).astype(float), np.nan)
h["risk_flag"] = np.where(h.risk_class.notna(), (h.risk_class >= 3).astype(float), np.nan)

keep = ["ACCOUNT_NUM", "GIS_PARCEL_ID", "x", "y", "lot_area_m2", "year_built", "TOT_LIVING_AREA_SF", "NUM_STORIES_DESC",
        "FOUNDATION_TYP_DESC", "BLDG_CLASS_DESC", "DESIRABILITY_RATING", "CONSTR_FRAM_TYP_DESC", "beta_class", "risk_class",
        "hazard_flag", "risk_flag"]
out = h[keep].reset_index(drop=True)
out.to_parquet(a.out_private / "dallas_population_2022.parquet", index=False)


def vc(s):
    return {str(k): int(v) for k, v in s.value_counts(dropna=False).sort_index().items()}


mapped = out.beta_class.notna()
summary = dict(
    flow=flow,
    beta_classes=vc(out.beta_class), risk_classes=vc(out.risk_class),
    hazard_mapped=int(mapped.sum()), hazard_flagged=int((out.hazard_flag == 1).sum()),
    hazard_flagged_share_of_mapped=round(float(out.hazard_flag[mapped].mean()), 5),
    risk_mapped=int(out.risk_class.notna().sum()), risk_flagged=int((out.risk_flag == 1).sum()),
    flagged_map_cells=int(len(set(zip(np.floor(np.asarray(lon)[(out.hazard_flag == 1).to_numpy()] / 0.0015),
                                      np.floor(np.asarray(lat)[(out.hazard_flag == 1).to_numpy()] / 0.0015))))),
    foundation=vc(out.FOUNDATION_TYP_DESC),
    year_built_quantiles={str(q): float(out.year_built.quantile(q)) for q in (0.05, 0.25, 0.5, 0.75, 0.95)},
    medians_by_hazard_flag={str(k): dict(year_built=float(g.year_built.median()),
                                         log_lot_area=float(np.log(g.lot_area_m2).median()),
                                         slab_share=float((g.FOUNDATION_TYP_DESC == "SLAB").mean()))
                            for k, g in out[mapped].groupby("hazard_flag")},
    mapped_share_by_decade={str(int(k)): round(float(v), 3) for k, v in
                            mapped.groupby((out.year_built // 20) * 20).mean().items()},
    inputs=inputs,
    private_output_sha256=sha256(a.out_private / "dallas_population_2022.parquet"),
    note="Outcome-blind: no permit or outcome file was opened.",
)
a.out_json.parent.mkdir(parents=True, exist_ok=True)
a.out_json.write_text(json.dumps(summary, indent=1) + "\n")
print(json.dumps({k: summary[k] for k in summary if k not in ("inputs",)}, indent=1))
