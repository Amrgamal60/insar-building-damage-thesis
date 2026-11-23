"""Core of HAZARD_TX (feasibility/hazard_tx/HAZARD_TX_PLAN.md, draft).

Reused unchanged (hash asserted): feasibility/ohenhen_austin/scripts/oa_core.py (frozen copy identical), which itself
asserts the frozen Austin nyc_lib: Poisson fits with offset, the inference candidates r1-r4 (CR1 Wald; wild cluster
score bootstrap by 2, 6, 12 km blocks with test inversion), the held-out statistic T (nyc_lib LR, out-of-fold) and
Wilson intervals.
New here: the city feature tables (Baseline 1 at 2022-01-01 from the step-0 outputs), blocks on the house point,
the fold assignments computed from the label (seed 42 then 0-9, nyc_lib.fold_map) and the pooled design.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[1]
PRIV = Path("/mnt/data/Master-projects/Alex_private")
OA = ROOT / "feasibility/ohenhen_austin/scripts"
OA_CORE_SHA256 = "509e3f27af49aceda2c511aed29307a980ec2b3a060b3f82998cbb47af80c076"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


assert sha256(OA / "oa_core.py") == OA_CORE_SHA256, "oa_core changed"
sys.path.insert(0, str(OA))
import oa_core as C  # noqa: E402

N = C.N
START, END = pd.Timestamp("2022-01-01"), pd.Timestamp("2025-12-31")  # follow-up, END inclusive
FU_DAYS = (END - START).days + 1  # 1,461
FU_YEARS = FU_DAYS / 365.25
AGE_DATE = 2022.0
B1 = list(C.B1)  # building_age, log_living_area, log_lot_area, lep_0_150, slope_deg, elevation_m, log_income, foundation_slab, x_km, y_km
FOLD_SEEDS = [42] + list(range(10))
METHODS, BLOCK_OF = C.METHODS, C.BLOCK_OF
SEED_WILD, SEED_BOOT_T = 2071, 2072  # plan §7 (new seeds; Ohenhen-Austin used 2061 and 2052)

D = PRIV / "hazard_tx/dallas"
CITIES = {
    "dallas": dict(population=D / "population_20261119/dallas_population_2022.parquet",
                   income=D / "income_20261119/dallas_income_2021.parquet",
                   terrain=D / "terrain_20261119/terrain_dallas.parquet",
                   soil=D / "soil_20261119/soil_lep.parquet"),
}
# outcome-only tables (permits linked to roll accounts; no map value): read by the planted check's planning figures
LINKS = {"dallas": D / "links_20261119/dallas_permit_links.parquet"}
EVENT_TYPE = {"dallas": "Residential Foundation Repair", "sanantonio": "Foundation Repair Permit"}
ID_COL = {"dallas": "ACCOUNT_NUM", "sanantonio": "PropID"}
# Baseline 1 per city (§7): the slab indicator only where the roll records foundation type for >= 90% of houses
B1_BY_CITY = {"dallas": B1, "sanantonio": [c for c in B1 if c != "foundation_slab"]}


def register_sanantonio(folder, links=None):
    """San Antonio step-0 outputs (current Bexar layer, D7) once built: folder holds population/, income/, terrain/,
    soil/ subfolders as written by s0_population.py, d1_income.py, s1_dem.py and d3_soil.py."""
    f = Path(folder)
    CITIES["sanantonio"] = dict(population=f / "population/sanantonio_population.parquet",
                                income=f / "income/sanantonio_income_2021.parquet",
                                terrain=f / "terrain/terrain_sanantonio.parquet",
                                soil=f / "soil/soil_lep.parquet")
    if links:
        LINKS["sanantonio"] = Path(links)


SA = PRIV / "hazard_tx/sanantonio_20261122"  # built 2026-11-22 from the complete current Bexar layer (SHA256SUMS there)
register_sanantonio(SA, links=SA / "links/sanantonio_permit_links.parquet")


def input_hashes(city):
    return {k: sha256(p) for k, p in CITIES[city].items()}


def source_hashes():
    return {p.name: sha256(p) for p in sorted(HERE.glob("*.py"))} | {"oa_core.py": OA_CORE_SHA256}


def load_city(city):
    """All eligible houses of the city (population order) with Baseline 1 at 2022-01-01, blocks of 2, 6 and 12 km on
    the house point, and the published hazard and risk classes. No outcome is read."""
    P, idc = CITIES[city], ID_COL[city]
    h = pd.read_parquet(P["population"])
    inc = pd.read_parquet(P["income"], columns=[idc, "log_income"])
    soil = pd.read_parquet(P["soil"], columns=[idc, "lep_0_150"])
    ter = pd.read_parquet(P["terrain"], columns=["prop_id", "slope_deg", "elevation_m"])
    n = len(h)
    h = h.merge(inc, on=idc, how="left", validate="one_to_one").merge(soil, on=idc, how="left", validate="one_to_one")
    tkey = "GIS_PARCEL_ID" if city == "dallas" else idc  # terrain is keyed by the parcel the polygon came from
    h = h.merge(ter, left_on=tkey, right_on="prop_id", how="left", validate="one_to_one").drop(columns="prop_id")
    assert len(h) == n
    if city != "dallas":
        h["ACCOUNT_NUM"] = h[idc]  # one id name downstream (outcome_only, links)
    h["hid"] = city + ":" + h[idc].astype(str)
    h["city"] = city
    h["building_age"] = AGE_DATE - h.year_built
    la = pd.to_numeric(h.TOT_LIVING_AREA_SF if city == "dallas" else h.building_area_sf, errors="coerce")
    h["log_living_area"] = np.log(la.where(la > 0))
    h["log_lot_area"] = np.log(h.lot_area_m2.where(h.lot_area_m2 > 0))
    if city == "dallas":
        f = h.FOUNDATION_TYP_DESC.fillna("UNASSIGNED")
        h["foundation_slab"] = np.where(f.eq("UNASSIGNED"), np.nan, f.eq("SLAB").astype(float))
    else:
        h["foundation_slab"] = np.nan  # not recorded (not in this city's Baseline 1)
    h["x_km"], h["y_km"] = h.x / 1000, h.y / 1000
    bx, by = np.floor(h.x / 2000).astype("int64"), np.floor(h.y / 2000).astype("int64")
    h["b2"] = city + ":" + bx.astype(str) + "_" + by.astype(str)
    h["b6"] = city + ":" + (bx // 3).astype(str) + "_" + (by // 3).astype(str)
    h["b12"] = city + ":" + (bx // 6).astype(str) + "_" + (by // 6).astype(str)
    h["complete_b1"] = h[B1_BY_CITY[city]].notna().all(1)
    h["mapped"] = h.beta_class.notna()
    h["flag"] = (h.beta_class >= 2).astype(float)
    return h


def fold_assignments(blocks, y, seeds=FOLD_SEEDS):
    """(len(seeds), n): nyc_lib.fold_map (StratifiedGroupKFold, 5 folds, 2 km blocks) with label = y, per seed."""
    cells = pd.DataFrame(dict(block=np.asarray(blocks), holds_event=np.asarray(y, int)))
    return np.array([cells.block.map(N.fold_map(cells, s)).to_numpy(np.int64) for s in seeds])


def pooled_design(frame, cities, x, cols=None, names=None):
    """[intercept per city, city x standardised Baseline 1 columns (standardised within city), flag last].
    cols=None: each city's own Baseline 1 (B1_BY_CITY), the city found by its name (cities hold names, or integer codes
    with names={code: name}); cols=list: the same columns for every city ([] = city intercepts only)."""
    parts = []
    cities = np.asarray(cities)
    for c in sorted(set(cities.tolist())):
        m = (cities == c).astype(float)
        parts.append(m)
        cc = B1_BY_CITY[names[c] if names else c] if cols is None else cols
        Z = frame.loc[:, cc].to_numpy(float)
        sel = m == 1
        mu, sd = Z[sel].mean(0), Z[sel].std(0)
        sd[sd == 0] = 1.0
        parts += list((((Z - mu) / sd) * m[:, None]).T)
    return np.column_stack(parts + [np.asarray(x, float)])


def t_statistic(XB, x, y, folds):
    return C.t_statistic(XB, x, y, folds)
