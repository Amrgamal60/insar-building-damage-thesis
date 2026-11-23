"""Step 0, San Antonio (HAZARD_TX draft): the reference population of houses and the published Ohenhen (2025)
classes at each house. Outcome-blind: no permit file is opened.

Reference data (D7, user 2026-11-19): the CURRENT Bexar County parcel layer (maps.bexar.org Parcels MapServer layer 0,
downloaded page by page as Esri JSON, EPSG:2278). Its values are current (year built up to 2025), not as of
2022-01-01; this is a stated limit of the plan (§5, §11, secondary 15). Rules (authors' choices; draft):
- Single-family residential: state code A1. Property-use codes inside A1 are tabulated (with median lot and building
  area); an exclusion, if any, is passed as --exclude-use and recorded before any linkage.
- Year built: YrBlt (0 or blank is missing); eligible if 2019 or earlier.
- Building area: GBA (gross building area; 0 is missing).
- House point: the centroid of the account's polygon in EPSG:32614 (repaired with make_valid). A polygon geometry
  shared by more than one A1 account is ambiguous: those accounts are left out and counted. A property ID or account
  that appears twice is left out and counted.
- Study area: the point lies inside the City of San Antonio (TIGER/Line 2021 place 4865000).
- Map classes: beta_sanAntonio.tif and risk_sanAntonio.tif (figshare 27606942), the class of the map cell that
  contains the point (EPSG:4326); no data gives no class. Hazard flag = beta class 2-3; risk flag = risk class 3-4.
Outputs (private): sanantonio_population.parquet (attributes, point, classes) and sanantonio_parcels.parquet
(prop_id + polygon in EPSG:32614, for the server terrain step); a JSON summary in the project.

Usage: python -I scripts/s0_population.py --pages DIR --place-zip T --ohenhen-dir D --out-private DIR --out-json F
                                          [--exclude-use CODE ...] [--allow-partial]
"""
import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

p = argparse.ArgumentParser()
p.add_argument("--pages", type=Path, required=True)
p.add_argument("--place-zip", type=Path, required=True)
p.add_argument("--ohenhen-dir", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
p.add_argument("--exclude-use", nargs="*", default=[])
p.add_argument("--max-oid", type=int, default=729183)
p.add_argument("--allow-partial", action="store_true", help="development only: run on the pages present")
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# pages: oid_<start>_<end>.json must tile 1..max_oid
pages = sorted(a.pages.glob("oid_*_*.json"), key=lambda f: int(f.stem.split("_")[1]))
spans = [tuple(int(v) for v in f.stem.split("_")[1:]) for f in pages]
expected = [(s, min(s + 999, a.max_oid)) for s in range(1, a.max_oid + 1, 1000)]
complete = spans == expected
if not complete and not a.allow_partial:
    raise SystemExit(f"pages incomplete: {len(spans)} of {len(expected)}")
inputs = dict(pages=len(pages), pages_expected=len(expected), complete=complete,
              pages_sha256=hashlib.sha256("".join(sha256(f) for f in pages).encode()).hexdigest(),
              place_zip=sha256(a.place_zip), beta=sha256(a.ohenhen_dir / "beta_sanAntonio.tif"),
              risk=sha256(a.ohenhen_dir / "risk_sanAntonio.tif"))
cols = ["OBJECTID", "PropID", "AcctNumb", "Situs", "State_cd", "PropUse", "YrBlt", "GBA", "LandVal", "ImprVal", "Nbhd",
        "IS_UDI", "UDIPARNT"]
g = pd.concat([gpd.read_file(f, engine="pyogrio", columns=cols) for f in pages], ignore_index=True)
g = gpd.GeoDataFrame(g, geometry="geometry", crs=2278)
flow = dict(records=len(g), objectid_duplicates=int(g.OBJECTID.duplicated().sum()))
g = g.drop_duplicates("OBJECTID")
flow["state_code_counts_top"] = {str(k): int(v) for k, v in g.State_cd.value_counts(dropna=False).head(12).items()}
h = g[g.State_cd.eq("A1")].copy()
flow["state_code_A1"] = len(h)
for c in ("YrBlt", "GBA", "LandVal", "ImprVal"):
    h[c] = pd.to_numeric(h[c], errors="coerce")
h["year_built"] = h.YrBlt.where(h.YrBlt > 0)
h["building_area_sf"] = h.GBA.where(h.GBA > 0)
h["PropID"] = h.PropID.astype(str).str.strip()
h["geometry"] = h.geometry.make_valid()
h = h.to_crs(32614)
h["lot_area_m2"] = h.geometry.area
use = h.groupby(h.PropUse.fillna("NA")).agg(n=("PropID", "size"), median_lot_m2=("lot_area_m2", "median"),
                                             median_building_sf=("building_area_sf", "median"),
                                             median_year_built=("year_built", "median"))
flow["a1_property_use"] = {str(k): {kk: (None if pd.isna(vv) else round(float(vv), 1)) for kk, vv in r.items()}
                           for k, r in use.sort_values("n", ascending=False).head(15).iterrows()}
if a.exclude_use:
    flow["excluded_property_use"] = int(h.PropUse.isin(a.exclude_use).sum())
    h = h[~h.PropUse.isin(a.exclude_use)]
flow["year_built_missing"] = int(h.year_built.isna().sum())
flow["year_built_after_2019"] = int((h.year_built > 2019).sum())
h = h[h.year_built.notna() & (h.year_built <= 2019)].copy()
flow["built_2019_or_earlier"] = len(h)
flow["no_polygon"] = int((h.geometry.isna() | h.geometry.is_empty).sum())
h = h[h.geometry.notna() & ~h.geometry.is_empty].copy()
dup_id = h.PropID.duplicated(keep=False) | h.AcctNumb.duplicated(keep=False)
flow["duplicate_property_id_or_account"] = int(dup_id.sum())
h = h[~dup_id].copy()
key = h.geometry.normalize().to_wkb()
shared = key.duplicated(keep=False)
flow["ambiguous_shared_polygon"] = int(shared.sum())
h = h[~shared].copy()
c = h.geometry.centroid
h["x"], h["y"] = c.x, c.y
place = gpd.read_file(f"zip://{a.place_zip}", engine="pyogrio")
city = place[place.GEOID == "4865000"].to_crs(32614)
assert len(city) == 1
inside = gpd.GeoSeries(gpd.points_from_xy(h.x, h.y), crs=32614).within(city.geometry.iloc[0]).to_numpy()
flow["point_outside_city"] = int((~inside).sum())
h = h[inside].copy()
flow["eligible"] = len(h)
flow["building_area_missing"] = int(h.building_area_sf.isna().sum())
flow["undivided_interest_records"] = int(h.IS_UDI.notna().sum())

lon, lat = Transformer.from_crs(32614, 4326, always_xy=True).transform(h.x.to_numpy(), h.y.to_numpy())
for lay in ("beta", "risk"):
    with rasterio.open(a.ohenhen_dir / f"{lay}_sanAntonio.tif") as r:
        v = np.array([s[0] for s in r.sample(zip(lon, lat))], dtype=float)
        nd = r.nodata
    v[(~np.isfinite(v)) | ((v == nd) if nd is not None else False)] = np.nan
    h[f"{lay}_class"] = v
h["hazard_flag"] = np.where(h.beta_class.notna(), (h.beta_class >= 2).astype(float), np.nan)
h["risk_flag"] = np.where(h.risk_class.notna(), (h.risk_class >= 3).astype(float), np.nan)

keep = ["PropID", "AcctNumb", "Situs", "PropUse", "Nbhd", "x", "y", "lot_area_m2", "year_built", "building_area_sf",
        "LandVal", "ImprVal", "beta_class", "risk_class", "hazard_flag", "risk_flag"]
out = pd.DataFrame(h[keep]).reset_index(drop=True)
out.to_parquet(a.out_private / "sanantonio_population.parquet", index=False)
parc = gpd.GeoDataFrame(dict(prop_id=h.PropID.to_numpy()), geometry=h.geometry.to_numpy(), crs=32614)
parc.to_parquet(a.out_private / "sanantonio_parcels.parquet", index=False)


def vc(s):
    return {str(k): int(v) for k, v in s.value_counts(dropna=False).sort_index().items()}


mapped = out.beta_class.notna()
summary = dict(
    source="Bexar County Parcels MapServer layer 0 (maps.bexar.org), CURRENT values (D7)",
    flow=flow,
    beta_classes=vc(out.beta_class), risk_classes=vc(out.risk_class),
    hazard_mapped=int(mapped.sum()), hazard_flagged=int((out.hazard_flag == 1).sum()),
    hazard_flagged_share_of_mapped=round(float(out.hazard_flag[mapped].mean()), 5) if mapped.any() else None,
    risk_mapped=int(out.risk_class.notna().sum()), risk_flagged=int((out.risk_flag == 1).sum()),
    flagged_map_cells=int(len(set(zip(np.floor(np.asarray(lon)[(out.hazard_flag == 1).to_numpy()] / 0.0015),
                                      np.floor(np.asarray(lat)[(out.hazard_flag == 1).to_numpy()] / 0.0015))))),
    year_built_quantiles={str(q): float(out.year_built.quantile(q)) for q in (0.05, 0.25, 0.5, 0.75, 0.95)},
    medians_by_hazard_flag={str(k): dict(year_built=float(gg.year_built.median()),
                                         log_lot_area=float(np.log(gg.lot_area_m2).median()),
                                         building_area_sf=float(gg.building_area_sf.median()))
                            for k, gg in out[mapped].groupby("hazard_flag")},
    mapped_share_by_20_years={str(int(k)): round(float(v), 3) for k, v in mapped.groupby((out.year_built // 20) * 20).mean().items()},
    bounds_32614=[float(v) for v in parc.total_bounds],
    inputs=inputs,
    private_outputs_sha256={f: sha256(a.out_private / f) for f in ("sanantonio_population.parquet", "sanantonio_parcels.parquet")},
    note="Outcome-blind: no permit or outcome file was opened.",
)
a.out_json.parent.mkdir(parents=True, exist_ok=True)
a.out_json.write_text(json.dumps(summary, indent=1) + "\n")
print(json.dumps({k: summary[k] for k in summary if k not in ("inputs",)}, indent=1))
