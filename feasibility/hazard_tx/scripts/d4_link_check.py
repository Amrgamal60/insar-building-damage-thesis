"""Step 0, Dallas (HAZARD_TX draft): address linkage of permits to the 2022 roll, and the link check.
No map value is read: this links permits to accounts only, and reports match rates.

Normalisation (fixed here, before any outcome is linked to the map):
- Upper case; '.', ',', ':' and '#' become spaces; whitespace collapsed.
- Permit street_address: text after the first comma is dropped (", Dallas, TX"). A trailing unit designator
  (APT, UNIT, STE, SUITE, BLDG, LOT, SP, TRLR, # followed by a token) is dropped.
- House number: the leading integer; a half ("1/2") after it is dropped and flagged. Roll: STREET_NUM.
- Street name: the rest. The FIRST and LAST words only (a directional prefix, a suffix or a directional suffix) are
  replaced by USPS abbreviations for directionals (NORTH->N, SOUTH->S, EAST->E, WEST->W, NORTHEAST->NE, ...) and
  common suffixes (STREET->ST, AVENUE->AVE, DRIVE->DR, ROAD->RD, LANE->LN,
  BOULEVARD->BLVD, CIRCLE->CIR, COURT->CT, PLACE->PL, TERRACE->TER, PARKWAY->PKWY, TRAIL->TRL, HIGHWAY->HWY,
  FREEWAY->FWY, EXPRESSWAY->EXPY, SQUARE->SQ, CROSSING->XING, POINT->PT, HOLLOW->HOLW, RIDGE->RDG, CREEK->CRK,
  VIEW->VW, WAY->WAY). Roll: FULL_STREET_NAME, normalised the same way.
- Key: number + ' ' + street name, over all roll accounts with property city DALLAS or city jurisdiction DALLAS.
  A key held by exactly one account matches it. A key held by several accounts is resolved by the 5-digit ZIP if the
  permit has one and exactly one of them shares it; otherwise the permit is ambiguous and is not allocated.
Outputs: per-permit link table (private) and match rates (overall, by year, by permit type), by account class
(population house / other roll account) and for unmatched and ambiguous permits.

Usage: python -I scripts/d4_link_check.py --permits CSV --dcad-zip Z --population F --out-private DIR --out-json F
"""
import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--permits", type=Path, required=True)
p.add_argument("--dcad-zip", type=Path, required=True)
p.add_argument("--population", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)

ABBR = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W", "NORTHEAST": "NE", "NORTHWEST": "NW", "SOUTHEAST": "SE",
        "SOUTHWEST": "SW", "STREET": "ST", "AVENUE": "AVE", "AV": "AVE", "DRIVE": "DR", "ROAD": "RD", "LANE": "LN",
        "BOULEVARD": "BLVD", "CIRCLE": "CIR", "COURT": "CT", "PLACE": "PL", "TERRACE": "TER", "PARKWAY": "PKWY",
        "TRAIL": "TRL", "HIGHWAY": "HWY", "FREEWAY": "FWY", "EXPRESSWAY": "EXPY", "SQUARE": "SQ", "CROSSING": "XING",
        "POINT": "PT", "HOLLOW": "HOLW", "RIDGE": "RDG", "CREEK": "CRK", "VIEW": "VW"}
UNIT = re.compile(r"\s+(?:APT|UNIT|STE|SUITE|BLDG|LOT|SP|TRLR)\s+\S+$|\s+#\s*\S+$")


def clean(s):
    s = s.fillna("").str.upper().str.replace(r"[.,:#]", " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    return s


def street(s):
    def one(v):
        w = v.split()
        if w:
            w[0], w[-1] = ABBR.get(w[0], w[0]), ABBR.get(w[-1], w[-1])
        return " ".join(w)
    return s.map(one)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


# roll keys
z = zipfile.ZipFile(a.dcad_zip)
with z.open("account_info.csv") as f:
    ai = pd.read_csv(io.TextIOWrapper(f, encoding="latin-1"), dtype=str,
                     usecols=["ACCOUNT_NUM", "STREET_NUM", "FULL_STREET_NAME", "PROPERTY_CITY", "PROPERTY_ZIPCODE"])
with z.open("account_apprl_year.csv") as f:
    ay = pd.read_csv(io.TextIOWrapper(f, encoding="latin-1"), dtype=str, usecols=["ACCOUNT_NUM", "CITY_JURIS_DESC", "SPTD_CODE"])
ai = ai.apply(lambda s: s.str.strip()).merge(ay.apply(lambda s: s.str.strip()), on="ACCOUNT_NUM", how="left")
ai = ai[(ai.PROPERTY_CITY.str.upper() == "DALLAS") | (ai.CITY_JURIS_DESC == "DALLAS")].copy()
num = pd.to_numeric(ai.STREET_NUM, errors="coerce")
ai = ai[num.notna() & (num > 0)].copy()
ai["key"] = num[num.notna() & (num > 0)].astype("int64").astype(str) + " " + street(clean(ai.FULL_STREET_NAME))
ai["zip5"] = ai.PROPERTY_ZIPCODE.fillna("").str[:5]
pop = set(pd.read_parquet(a.population, columns=["ACCOUNT_NUM"]).ACCOUNT_NUM)
ai["in_population"] = ai.ACCOUNT_NUM.isin(pop)
keys = ai.groupby("key").ACCOUNT_NUM.agg(list)

# permits
pm = pd.read_csv(a.permits, dtype=str)
pm.columns = [c.strip().lower().replace(" ", "_") for c in pm.columns]
raw = clean(pm.street_address.str.split(",").str[0])
raw = raw.str.replace(UNIT, "", regex=True).str.strip()
m = raw.str.extract(r"^(\d+)(?:\s+1/2)?\s+(.*)$")
pm["half"] = raw.str.match(r"^\d+\s+1/2\s")
pm["key"] = np.where(m[0].notna(), m[0].str.lstrip("0") + " " + street(m[1].fillna("")), None)
pm["zip5"] = pm.get("zip_code", pd.Series("", index=pm.index)).fillna("").str[:5]
zipmap = ai.set_index("ACCOUNT_NUM").zip5


def resolve(key, zp):
    if key is None or key not in keys.index:
        return None, "unmatched"
    acc = keys[key]
    if len(acc) == 1:
        return acc[0], "matched"
    if zp:
        hit = [x for x in acc if zipmap.get(x) == zp]
        if len(hit) == 1:
            return hit[0], "matched by zip"
    return None, "ambiguous"


res = [resolve(k, zp) for k, zp in zip(pm.key, pm.zip5)]
pm["ACCOUNT_NUM"] = [r[0] for r in res]
pm["link"] = [r[1] for r in res]
pm["target"] = np.where(pm.ACCOUNT_NUM.isin(pop), "population house", np.where(pm.ACCOUNT_NUM.notna(), "other roll account", pm.link))
pm["issue_date"] = pd.to_datetime(pm.issued_date, format="%m/%d/%y", errors="coerce")
pm["year"] = pm.issue_date.dt.year
keep = ["permit_number", "permit_type", "issue_date", "year", "land_use", "key", "zip5", "half", "ACCOUNT_NUM", "link", "target"]
pm[keep].to_parquet(a.out_private / "dallas_permit_links.parquet", index=False)

res_like = pm.permit_type.str.startswith("Residential", na=False) | pm.permit_type.str.contains("Single Family", na=False)


def rates(d):
    n = len(d)
    return dict(n=n, **{k: dict(count=int(v), percent=round(100 * v / n, 2)) for k, v in d.target.value_counts().items()})


S = dict(
    inputs=dict(permits=sha(a.permits), dcad_zip=sha(a.dcad_zip), population=sha(a.population)),
    roll_accounts_keyed=len(ai), roll_keys=len(keys), roll_keys_shared=int((keys.map(len) > 1).sum()),
    permits=len(pm), permits_unparsed_address=int(pm.key.isna().sum()), permits_with_half_number=int(pm.half.sum()),
    issue_date_unparsed=int(pm.issue_date.isna().sum()),
    residential_types=rates(pm[res_like]),
    residential_types_by_year={str(int(y)): rates(g) for y, g in pm[res_like].groupby("year")},
    by_permit_type={t: rates(g) for t, g in pm[res_like].groupby("permit_type") if len(g) >= 500},
    single_family_land_use=rates(pm[pm.land_use.fillna("").str.contains("SINGLE FAMILY")]),
    private_outputs_sha256={"dallas_permit_links.parquet": sha(a.out_private / "dallas_permit_links.parquet")},
    note="No map value was read. Permits are linked to roll accounts only.")
a.out_json.write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps({k: S[k] for k in S if k not in ("by_permit_type", "inputs")}, indent=1))
