"""Step 0, Dallas (HAZARD_TX draft): neighbourhood income for the reference houses. Outcome-blind.

Austin's rule (frozen Austin plan §9; checkpoint1/scripts/c1_14_income.py), moved to the cohort start of 2022-01-01:
median household income (ACS 2017-2021 five-year, table B19013, 2021 dollars) of the 2020-vintage block group
(TIGER/Line 2021) that contains the house point; the tract median where the block-group median is not a valid
median; missing otherwise. A valid median is a positive integer that is not a jam value (2499 = 2,500 or less,
250001 = 250,000 or more) and not a negative annotation code (e.g. -666666666). A margin is usable if it is a positive
integer. A point on a boundary that meets exactly one block group takes it.

Usage: python -I scripts/d1_income.py --acs-dat F --bg-zip F --population F --out-private DIR --out-json FILE
       [--county 029 --id-col PropID --out-name sanantonio_income_2021.parquet]   (San Antonio, Bexar County)
"""
import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--acs-dat", type=Path, required=True)
p.add_argument("--bg-zip", type=Path, required=True)
p.add_argument("--population", type=Path, required=True)
p.add_argument("--county", default="113")
p.add_argument("--id-col", default="ACCOUNT_NUM", help="house id column of the population (San Antonio: PropID)")
p.add_argument("--out-name", default="dallas_income_2021.parquet")
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)
JAM = {2499, 250001}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


d = pd.read_csv(a.acs_dat, sep="|", dtype=str)
assert list(d.columns) == ["GEO_ID", "B19013_E001", "B19013_M001"]
est = pd.to_numeric(d.B19013_E001, errors="coerce")
moe = pd.to_numeric(d.B19013_M001, errors="coerce")
d["valid"] = est.notna() & (est > 0) & ~est.isin(JAM) & (est == est.round())
d["est"], d["moe"] = est, moe.where(moe > 0)
pre = {"150": "1500000US48" + a.county, "140": "1400000US48" + a.county}
bg = d[d.GEO_ID.str.startswith(pre["150"])].assign(geoid=lambda x: x.GEO_ID.str[9:]).set_index("geoid")
tr = d[d.GEO_ID.str.startswith(pre["140"])].assign(geoid=lambda x: x.GEO_ID.str[9:]).set_index("geoid")
S = dict(table="B19013, ACS 2017-2021 five-year, table-based summary file", county_fips="48" + a.county,
         block_groups=len(bg), block_groups_valid=int(bg.valid.sum()),
         block_group_invalid_codes={str(k): int(v) for k, v in bg.loc[~bg.valid, "B19013_E001"].value_counts(dropna=False).items()},
         tracts=len(tr), tracts_valid=int(tr.valid.sum()))

h = pd.read_parquet(a.population, columns=[a.id_col, "x", "y"]).rename(columns={a.id_col: "ACCOUNT_NUM"})
pts = gpd.GeoDataFrame(h[["ACCOUNT_NUM"]], geometry=gpd.points_from_xy(h.x, h.y), crs=32614)
t = gpd.read_file(f"zip://{a.bg_zip}", engine="pyogrio")
t = t.loc[t.COUNTYFP.eq(a.county), ["GEOID", "geometry"]].to_crs(32614)
S["tiger_block_groups"] = len(t)
S["tiger_not_in_acs"] = int((~t.GEOID.isin(bg.index)).sum())
S["acs_not_in_tiger"] = int((~bg.index.isin(t.GEOID)).sum())
j = gpd.sjoin(pts, t, how="left", predicate="within")
assert not j.ACCOUNT_NUM.duplicated().any()
j["GEOID"] = j.GEOID.astype(object)
miss = j.GEOID.isna()
S["boundary_assignments"] = 0
if miss.any():
    j2 = gpd.sjoin(pts[miss.to_numpy()], t, how="left", predicate="intersects")
    one = j2.groupby("ACCOUNT_NUM").GEOID.agg(lambda s: s.dropna().unique().tolist())
    fix = {k: v[0] for k, v in one.items() if len(v) == 1}
    j.loc[miss, "GEOID"] = j.loc[miss, "ACCOUNT_NUM"].map(fix)
    S["boundary_assignments"] = len(fix)
out = pd.DataFrame(dict(ACCOUNT_NUM=j.ACCOUNT_NUM.to_numpy(), bg_geoid=j.GEOID.to_numpy()))


def look(tab, key, col):
    if not isinstance(key, str) or key not in tab.index or not tab.at[key, "valid"]:
        return np.nan
    return tab.at[key, col]


b_inc = out.bg_geoid.map(lambda k: look(bg, k, "est"))
t_inc = out.bg_geoid.map(lambda k: look(tr, k[:11] if isinstance(k, str) else k, "est"))
out["income_source"] = np.where(b_inc.notna(), "block group", np.where(t_inc.notna(), "tract", "none"))
out["income_usd_2021"] = b_inc.where(b_inc.notna(), t_inc)
b_moe = out.bg_geoid.map(lambda k: look(bg, k, "moe"))
t_moe = out.bg_geoid.map(lambda k: look(tr, k[:11] if isinstance(k, str) else k, "moe"))
out["income_moe"] = np.where(out.income_source.eq("block group"), b_moe, np.where(out.income_source.eq("tract"), t_moe, np.nan))
assert (out.income_usd_2021.dropna() > 0).all()
out["log_income"] = np.log(out.income_usd_2021)
out = out.rename(columns={"ACCOUNT_NUM": a.id_col})
out.to_parquet(a.out_private / a.out_name, index=False)
n = len(out)
S.update(houses=n, by_source={k: int(v) for k, v in out.income_source.value_counts().items()},
         missing_percent=round(100 * float((out.income_source == "none").mean()), 3),
         relative_moe_median=round(float((out.income_moe / out.income_usd_2021).median()), 3),
         inputs={a.acs_dat.name: sha(a.acs_dat), a.bg_zip.name: sha(a.bg_zip), "population": sha(a.population)},
         private_output_sha256=sha(a.out_private / a.out_name),
         safeguard="income stays in Baseline 1 unless missing for more than 10% of houses (Austin §9)",
         note="Outcome-blind: no permit or outcome file was opened.")
a.out_json.write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps({k: v for k, v in S.items() if k != "inputs"}, indent=1))
