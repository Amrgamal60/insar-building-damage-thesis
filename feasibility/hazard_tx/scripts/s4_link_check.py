"""Step 0, San Antonio (HAZARD_TX draft): linkage of permits to parcels of the current Bexar County layer, and the
link check. No map value is read: this links permits to parcel accounts only, and reports match rates.

Rules (D6; fixed here, before any outcome is linked to the map):
- Permits: the two City of San Antonio files (issued 2020-07-20 to 2024-12-31, and 2025 onward), one row per
  PERMIT # (the first row kept; the files repeat rows per contact).
- Issue date: DATE ISSUED (M/D/YYYY in the first file, ISO in the second).
- Point: X_COORD/Y_COORD; values with |x| < 200 are longitude/latitude (EPSG:4326), others Texas South Central
  state-plane feet (EPSG:2278); transformed to EPSG:32614.
- Step 1, point in parcel: the point lies within exactly one parcel polygon of the layer (all state codes) -> that
  account. Within several polygons -> ambiguous (not allocated).
- Step 2, address fallback, for permits without a point or whose point lies in no polygon: the d4 (Dallas)
  normalisation (upper case; '.', ',', ':', '#' to spaces; text after the first comma dropped; a trailing 5-digit ZIP
  dropped and kept as the ZIP; a trailing unit designator dropped; leading house number; USPS abbreviation of the
  first and last words). Situs: the first line of Situs, normalised the same way; ZIP = its last 5 digits.
  A key held by exactly one parcel matches it; by several, resolved by ZIP if exactly one shares it; else ambiguous.
- Step 3, suffix-free address, for permits still unmatched: the same keys with a trailing street-type word (SUFFIX
  list below) removed on both sides (permits often omit it); same uniqueness and ZIP rule.
- Quality check: for permits linked by point to a population house, the share whose address house number equals the
  parcel's situs house number.
Outputs: per-permit link table (private) and match rates (overall, by year, by permit type), by target class
(population house / other parcel / unmatched / ambiguous) and by link step.

Usage: python -I scripts/s4_link_check.py --permits CSV CSV --pages DIR --population F --out-private DIR --out-json F
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer

p = argparse.ArgumentParser()
p.add_argument("--permits", type=Path, nargs="+", required=True)
p.add_argument("--pages", type=Path, required=True)
p.add_argument("--population", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
p.add_argument("--max-oid", type=int, default=729183)
p.add_argument("--allow-partial", action="store_true", help="development only")
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)

ABBR = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W", "NORTHEAST": "NE", "NORTHWEST": "NW", "SOUTHEAST": "SE",
        "SOUTHWEST": "SW", "STREET": "ST", "AVENUE": "AVE", "AV": "AVE", "DRIVE": "DR", "ROAD": "RD", "LANE": "LN",
        "BOULEVARD": "BLVD", "CIRCLE": "CIR", "COURT": "CT", "PLACE": "PL", "TERRACE": "TER", "PARKWAY": "PKWY",
        "TRAIL": "TRL", "HIGHWAY": "HWY", "FREEWAY": "FWY", "EXPRESSWAY": "EXPY", "SQUARE": "SQ", "CROSSING": "XING",
        "POINT": "PT", "HOLLOW": "HOLW", "RIDGE": "RDG", "CREEK": "CRK", "VIEW": "VW"}
UNIT = re.compile(r"\s+(?:APT|UNIT|STE|SUITE|BLDG|LOT|SP|TRLR)\s+\S+$|\s+#\s*\S+$")
SUFFIX = {"ST", "AVE", "DR", "RD", "LN", "BLVD", "CIR", "CT", "PL", "TER", "PKWY", "TRL", "HWY", "FWY", "EXPY", "SQ",
          "XING", "PT", "HOLW", "RDG", "CRK", "VW", "WAY", "LOOP", "PATH", "RUN", "PASS", "GLN", "CV", "BND", "CYN", "HL",
          "HLS", "PARK", "PLZ", "RDG", "ROW", "SPGS", "VLY", "WALK", "XRD", "TRCE", "MDW", "MDWS", "OVAL", "GRV", "BLF"}
RESIDENTIAL = ["Foundation Repair Permit", "Res Foundation Permit", "Residential Repair Permit", "Res New Building Permit",
               "Re-Roof Permit", "Home Addition Permit", "Res Accessory-Addition Permit", "Res Accessory Dwelling Permit",
               "Residential Fence Permit", "Swimming Pool or Spa Permit"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def clean(s):
    return s.fillna("").str.upper().str.replace(r"[.,:#]", " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()


def street(s):
    def one(v):
        w = v.split()
        if w:
            w[0], w[-1] = ABBR.get(w[0], w[0]), ABBR.get(w[-1], w[-1])
        return " ".join(w)
    return s.map(one)


def key_of(first_part):
    """(key, zip5) from the street part of an address (text before the first comma or line break)."""
    raw = clean(first_part)
    zp = raw.str.extract(r"\s(\d{5})(?:-\d{4})?$")[0].fillna("")
    raw = raw.str.replace(r"\s\d{5}(?:-\d{4})?$", "", regex=True).str.replace(UNIT, "", regex=True).str.strip()
    m = raw.str.extract(r"^(\d+)(?:\s+1/2)?\s+(.*)$")
    key = pd.Series(np.where(m[0].notna(), m[0].str.lstrip("0") + " " + street(m[1].fillna("")), None), index=raw.index)
    return key, zp


# ---- parcels (all state codes)
pages = sorted(a.pages.glob("oid_*_*.json"), key=lambda f: int(f.stem.split("_")[1]))
spans = [tuple(int(v) for v in f.stem.split("_")[1:]) for f in pages]
complete = spans == [(s, min(s + 999, a.max_oid)) for s in range(1, a.max_oid + 1, 1000)]
if not complete and not a.allow_partial:
    raise SystemExit("pages incomplete")
g = pd.concat([gpd.read_file(f, engine="pyogrio", columns=["OBJECTID", "PropID", "Situs", "State_cd"]) for f in pages], ignore_index=True)
g = gpd.GeoDataFrame(g, geometry="geometry", crs=2278).drop_duplicates("OBJECTID")
g = g[g.geometry.notna() & ~g.geometry.is_empty].copy()
g["PropID"] = g.PropID.astype(str).str.strip()
g["geometry"] = g.geometry.make_valid()
g = g.to_crs(32614)
pop = set(pd.read_parquet(a.population, columns=["PropID"]).PropID)
situs1 = g.Situs.fillna("").str.split(r"[\r\n]", regex=True).str[0]
g["key"], _ = key_of(situs1)
g["zip5"] = g.Situs.fillna("").str.extract(r"(\d{5})(?:-\d{4})?\s*$")[0].fillna("")
keys = g[g.key.notna()].groupby("key").PropID.agg(lambda s: sorted(set(s)))


def drop_suffix(k):
    if not isinstance(k, str):
        return None
    w = k.split()
    return " ".join(w[:-1]) if len(w) > 2 and w[-1] in SUFFIX else k


g["key3"] = g.key.map(drop_suffix)
keys3 = g[g.key3.notna()].groupby("key3").PropID.agg(lambda s: sorted(set(s)))
zipmap = g.drop_duplicates("PropID").set_index("PropID").zip5

# ---- permits
pm = pd.concat([pd.read_csv(f, dtype=str) for f in a.permits], ignore_index=True)
n_rows = len(pm)
pm = pm.drop_duplicates("PERMIT #").reset_index(drop=True)
d1 = pd.to_datetime(pm["DATE ISSUED"], format="%m/%d/%Y", errors="coerce")
d2 = pd.to_datetime(pm["DATE ISSUED"], format="%Y-%m-%d", errors="coerce")
pm["issue_date"] = d1.fillna(d2)
pm["year"] = pm.issue_date.dt.year
x, y = pd.to_numeric(pm.X_COORD, errors="coerce"), pd.to_numeric(pm.Y_COORD, errors="coerce")
ll = x.abs() < 200
sp = x.notna() & y.notna() & ~ll & (x.abs() > 1e5)
X, Y = np.full(len(pm), np.nan), np.full(len(pm), np.nan)
t1 = Transformer.from_crs(4326, 32614, always_xy=True)
t2 = Transformer.from_crs(2278, 32614, always_xy=True)
X[ll], Y[ll] = t1.transform(x[ll].to_numpy(), y[ll].to_numpy())
X[sp], Y[sp] = t2.transform(x[sp].to_numpy(), y[sp].to_numpy())
pm["has_point"] = np.isfinite(X)
pts = gpd.GeoDataFrame(dict(i=np.flatnonzero(pm.has_point)), geometry=gpd.points_from_xy(X[pm.has_point], Y[pm.has_point]), crs=32614)
j = gpd.sjoin(pts, g[["PropID", "geometry"]], how="inner", predicate="within")
hits = j.groupby("i").PropID.agg(lambda s: sorted(set(s)))
pm["PropID"], pm["link"] = None, "unmatched"
one = hits[hits.map(len) == 1]
pm.loc[one.index, "PropID"] = one.map(lambda v: v[0])
pm.loc[one.index, "link"] = "point in parcel"
many = hits[hits.map(len) > 1].index
pm.loc[many, "link"] = "ambiguous (point in several parcels)"
pm["key"], pm["zip5"] = key_of(pm.ADDRESS.fillna("").str.split(",").str[0])
zp_full = pm.ADDRESS.fillna("").str.extract(r"(\d{5})(?:-\d{4})?\s*$")[0].fillna("")
pm["zip5"] = pm.zip5.where(pm.zip5 != "", zp_full)


def resolve(k, zp, tab, name):
    if k is None or k not in tab.index:
        return None, "unmatched"
    acc = tab[k]
    if len(acc) == 1:
        return acc[0], name
    if zp:
        hit = [v for v in acc if zipmap.get(v) == zp]
        if len(hit) == 1:
            return hit[0], name + " + zip"
    return None, f"ambiguous ({name})"


todo = pm.link.eq("unmatched")
res = [resolve(k, zp, keys, "address") for k, zp in zip(pm.key[todo], pm.zip5[todo])]
pm.loc[todo, "PropID"] = [r[0] for r in res]
pm.loc[todo, "link"] = [r[1] for r in res]
todo = pm.link.eq("unmatched")
res = [resolve(drop_suffix(k), zp, keys3, "suffix-free address") for k, zp in zip(pm.key[todo], pm.zip5[todo])]
pm.loc[todo, "PropID"] = [r[0] for r in res]
pm.loc[todo, "link"] = [r[1] for r in res]
pm["target"] = np.where(pm.PropID.isin(pop), "population house",
                        np.where(pm.PropID.notna(), "other parcel", np.where(pm.link.str.startswith("ambiguous"), "ambiguous", "unmatched")))
keep = ["PERMIT #", "PERMIT TYPE", "WORK TYPE", "issue_date", "year", "has_point", "key", "zip5", "PropID", "link", "target"]
pm[keep].rename(columns={"PERMIT #": "permit_number", "PERMIT TYPE": "permit_type", "WORK TYPE": "work_type"}).to_parquet(
    a.out_private / "sanantonio_permit_links.parquet", index=False)


def rates(d):
    n = len(d)
    return dict(n=n, **{k: dict(count=int(v), percent=round(100 * v / n, 2)) for k, v in d.target.value_counts().items()},
                by_step={k: int(v) for k, v in d.link.value_counts().items()})


res_like = pm["PERMIT TYPE"].isin(RESIDENTIAL)
pp = pm[pm.link.eq("point in parcel") & pm.target.eq("population house")]
situs_num = g.drop_duplicates("PropID").set_index("PropID").key.str.split().str[0]
agree = pp.key.str.split().str[0] == pp.PropID.map(situs_num)
S = dict(
    inputs=dict(permits={f.name: sha(f) for f in a.permits}, pages=len(pages), pages_complete=complete, population=sha(a.population)),
    parcels=len(g), parcel_keys=len(keys), parcel_keys_shared=int((keys.map(len) > 1).sum()),
    permit_rows=n_rows, permits=len(pm), issue_date_unparsed=int(pm.issue_date.isna().sum()),
    with_point=int(pm.has_point.sum()), point_lonlat=int(ll.sum()), point_state_plane=int(sp.sum()),
    residential_types_used=RESIDENTIAL,
    point_links_house_number_agrees=dict(n=len(pp), share=round(float(agree.mean()), 4) if len(pp) else None),
    residential_types=rates(pm[res_like]),
    residential_types_by_year={str(int(yy)): rates(gg) for yy, gg in pm[res_like].groupby("year")},
    by_permit_type={t: rates(gg) for t, gg in pm[res_like].groupby("PERMIT TYPE")},
    demolition=rates(pm[pm["PERMIT TYPE"].eq("Demolition Permit")]),
    private_outputs_sha256={"sanantonio_permit_links.parquet": sha(a.out_private / "sanantonio_permit_links.parquet")},
    note="No map value was read. Permits are linked to parcel accounts only.")
a.out_json.write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps({k: S[k] for k in S if k not in ("by_permit_type", "inputs", "residential_types_by_year")}, indent=1))
