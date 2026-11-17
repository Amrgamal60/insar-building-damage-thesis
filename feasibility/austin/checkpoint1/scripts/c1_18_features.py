"""Checkpoint 1 (AUSTIN_PLAN §9): the static feature table of the eligible houses, the
completeness of Baseline 1, and the generating coefficients of the planted-signal check
(§14, 2026-11-10). No InSAR value is read.

Baseline 1 columns (§9): building age (from year built, at the row's date), log living
area, log lot area, soil linear extensibility, slope, elevation, log neighbourhood income,
foundation type, and x/y in km.

How the wording is applied (authors' choices, fixed before any InSAR file is opened):
- Building age at a date = the decimal year of the date minus the year built.
- Foundation type: 1 for a house whose only recorded code is SLAB, 0 for one whose only
  recorded code is PIER AND B. Blank, mixed and other codes have no value. By the
  missing-input rule of §9, a house without a value is left out of every comparison that
  uses Baseline 1, and is counted.
- Logs are natural logs of living area (square feet), lot area (m2) and income (dollars).
Generating coefficients (§14): the frozen logistic model (nyc_lib.model) fitted once to
"house holds an event" on Baseline 1 + x/y over the eligible houses with complete inputs,
with building age taken at 2018-08-01.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--private", type=Path, required=True)
p.add_argument("--frozen-scripts", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
p.add_argument("--out-coefficients", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(a.frozen_scripts))
import nyc_lib  # noqa: E402  (frozen copy)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


src = dict(grid=a.private / "grid_folds" / "eligible_grid_folds.parquet", population=a.private / "reference_2018" / "population_2018.parquet",
           soil=a.private / "soil" / "soil_lep.parquet", terrain=a.private / "terrain" / "terrain_parcels.parquet",
           income=a.private / "income" / "income_2015.parquet", canopy=a.private / "canopy" / "canopy_parcels.parquet")
g = pd.read_parquet(src["grid"])
pop = pd.read_parquet(src["population"], columns=["prop_id", "year_built", "living_area", "lot_area_m2", "foundation"])
f = g[["prop_id", "geo", "x", "y", "block", "fold", "holds_event"]].merge(pop, on="prop_id", validate="one_to_one")
for name, cols in (("soil", ["prop_id", "lep_0_150"]), ("terrain", ["prop_id", "elevation_m", "slope_deg"]),
                   ("income", ["prop_id", "income_usd_2015"]), ("canopy", ["prop_id", "canopy_share"])):
    f = f.merge(pd.read_parquet(src[name], columns=cols), on="prop_id", how="left", validate="one_to_one")
assert len(f) == len(g)
code = f.foundation.fillna("").str.strip()
f["foundation_slab"] = np.where(code.eq("SLAB"), 1.0, np.where(code.eq("PIER AND B"), 0.0, np.nan))
f["log_living_area"] = np.log(f.living_area)
f["log_lot_area"] = np.log(f.lot_area_m2)
f["log_income"] = np.log(f.income_usd_2015)
f["x_km"], f["y_km"] = f.x / 1000, f.y / 1000
STATIC = ["log_living_area", "log_lot_area", "lep_0_150", "slope_deg", "elevation_m", "log_income", "foundation_slab"]
B1 = ["building_age"] + STATIC + ["x_km", "y_km"]
f["complete_b1"] = f[["year_built"] + STATIC + ["x_km", "y_km"]].notna().all(axis=1)
keep = ["prop_id", "geo", "block", "fold", "holds_event", "year_built"] + STATIC + ["x_km", "y_km", "canopy_share", "complete_b1"]
f = f.sort_values("prop_id").reset_index(drop=True)
f[keep].to_parquet(a.out_private / "features_2018.parquet", index=False)

n = len(f)
miss = {c: dict(count=int(f[c].isna().sum()), percent=round(100 * float(f[c].isna().mean()), 3)) for c in ["year_built"] + STATIC + ["canopy_share"]}
ev, inc = f.holds_event, ~f.complete_b1
S = dict(inputs={k: sha(v) for k, v in src.items()}, eligible_houses=n, baseline_1_columns=B1, baseline_2_extra=["other_bp_5y (at the row date)", "canopy_share"],
         missing=miss,
         complete_baseline_1=dict(houses=int(f.complete_b1.sum()), percent=round(100 * float(f.complete_b1.mean()), 3),
                                  events=int((ev & f.complete_b1).sum()), events_percent=round(100 * float((ev & f.complete_b1).sum()) / int(ev.sum()), 3)),
         incomplete_baseline_1=dict(houses=int(inc.sum()), events=int((ev & inc).sum()),
                                    only_foundation_missing=int((inc & f[[c for c in STATIC if c != "foundation_slab"]].notna().all(axis=1)).sum())),
         event_share_by_foundation={k: dict(houses=int(m.sum()), events=int((ev & m).sum()), events_per_1000=round(1000 * float((ev & m).sum()) / int(m.sum()), 2))
                                    for k, m in (("slab", f.foundation_slab.eq(1)), ("pier and beam", f.foundation_slab.eq(0)), ("no value", f.foundation_slab.isna()))},
         summary={c: f[c].describe().round(4).to_dict() for c in ["year_built"] + STATIC + ["canopy_share"]},
         year_built_before_1800=int((f.year_built < 1800).sum()))

# ---- generating coefficients of the planted-signal check (§14) ----
REF = 2018 + (pd.Timestamp("2018-08-01").dayofyear - 1) / 365.25
d = f[f.complete_b1].copy()
d["building_age"] = REF - d.year_built
X, y = d[B1].to_numpy(dtype="float64"), d.holds_event.to_numpy().astype(int)
m = nyc_lib.model(nyc_lib.LR).fit(X, y)
sc, lr = m.named_steps["standardscaler"], m.named_steps["logisticregression"]
C = dict(model="nyc_lib.model('logistic regression'): StandardScaler + LogisticRegression(C=1.0, max_iter=5000)",
         nyc_lib_sha256=sha(a.frozen_scripts / "nyc_lib.py"), label="house holds an event (§4)", age_reference_date="2018-08-01",
         age_reference_decimal_year=REF, features_sha256=sha(a.out_private / "features_2018.parquet"),
         rows=int(len(d)), events=int(y.sum()), columns=B1, scaler_mean=sc.mean_.tolist(), scaler_scale=sc.scale_.tolist(),
         coefficients_on_standardised_columns=lr.coef_[0].tolist(), intercept=float(lr.intercept_[0]), iterations=int(lr.n_iter_[0]))
a.out_coefficients.write_text(json.dumps(C, indent=1) + "\n")
S["generating_coefficients"] = dict(file=a.out_coefficients.name, sha256=sha(a.out_coefficients), rows=C["rows"], events=C["events"],
                                    coefficients={k: round(v, 4) for k, v in zip(B1, C["coefficients_on_standardised_columns"])})
S["private_outputs_sha256"] = {"features_2018.parquet": C["features_sha256"]}
a.out_json.write_text(json.dumps(S, indent=1, default=float) + "\n")
print(json.dumps(S, indent=1, default=float))
