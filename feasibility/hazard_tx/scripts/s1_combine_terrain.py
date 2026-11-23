"""Step 0, San Antonio (HAZARD_TX draft, §4): one terrain value per house from three overlapping 3DEP 1 m projects.
Outcome-blind.

Austin's s1_dem.py is run unchanged once per project (each project's tiles are distinct 10 km cells, so no pixel is
counted twice within a run). This script combines the runs:
- full pixel count of a parcel = the largest n_pix over the projects (the projects share the USGS 10 km tile grid);
- a project is COMPLETE for a parcel if its elevation and slope are present and n_valid equals that full count
  (for a parcel with no pixel centre inside, n_pix = 0 in every run: complete if its centroid values are present);
- the house takes the first complete project in ORDER (largest coverage of the city first); if none is complete,
  the project with the most valid pixels (ties: ORDER); if none has a value, it is missing.
Reported: houses per project and rule, and the agreement of elevation and slope where two projects are complete.

Usage: python -I s1_combine_terrain.py --runs P1.parquet P2.parquet P3.parquet --names N1 N2 N3 --out F --out-json F
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--runs", type=Path, nargs="+", required=True)
p.add_argument("--names", nargs="+", required=True)
p.add_argument("--out", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
assert len(a.runs) == len(a.names) and not a.out.exists()
R = [pd.read_parquet(f) for f in a.runs]
ids = R[0].prop_id.to_numpy()
for r in R:
    assert (r.prop_id.to_numpy() == ids).all()
n_full = np.max([r.n_pix.to_numpy() for r in R], axis=0)
ok = []
for r in R:
    present = r.elevation_m.notna().to_numpy() & r.slope_deg.notna().to_numpy()
    ok.append(present & np.where(n_full > 0, r.n_valid.to_numpy() == n_full, True))
ok = np.array(ok)
first = np.where(ok.any(0), ok.argmax(0), -1)
nv = np.array([np.where(r.elevation_m.notna(), r.n_valid, -1) for r in R])
best = np.where((nv >= 0).any(0), nv.argmax(0), -1)
pick = np.where(first >= 0, first, best)
rule = np.where(first >= 0, "complete", np.where(best >= 0, "most valid pixels", "missing"))
out = pd.DataFrame(dict(prop_id=ids, project=np.where(pick >= 0, np.array(a.names, dtype=object)[np.clip(pick, 0, None)], None),
                        rule=rule, n_full=n_full))
for c in ("elevation_m", "slope_deg", "n_pix", "n_valid"):
    v = np.array([r[c].to_numpy(float) for r in R])
    out[c] = np.where(pick >= 0, v[np.clip(pick, 0, None), np.arange(len(ids))], np.nan)
out.to_parquet(a.out, index=False)
agree = {}
for i in range(len(R)):
    for j in range(i + 1, len(R)):
        both = ok[i] & ok[j]
        if both.sum() < 10:
            continue
        de = R[i].elevation_m.to_numpy()[both] - R[j].elevation_m.to_numpy()[both]
        si, sj = R[i].slope_deg.to_numpy()[both], R[j].slope_deg.to_numpy()[both]
        agree[f"{a.names[i]} vs {a.names[j]}"] = dict(houses=int(both.sum()), elevation_diff_median=float(np.median(de)),
                                                      elevation_abs_diff_p95=float(np.quantile(np.abs(de), 0.95)),
                                                      slope_pearson=float(np.corrcoef(si, sj)[0, 1]),
                                                      slope_ratio_median=float(np.median(si / sj)))
S = dict(order=a.names, houses=len(out), by_project_and_rule={f"{k[0]} / {k[1]}": int(v) for k, v in out.groupby(["project", "rule"], dropna=False).size().items()},
         missing=int(out.elevation_m.isna().sum()), complete_in={a.names[i]: int(ok[i].sum()) for i in range(len(R))},
         agreement_where_both_complete=agree,
         runs_sha256={a.names[i]: hashlib.sha256(a.runs[i].read_bytes()).hexdigest() for i in range(len(R))},
         out_sha256=hashlib.sha256(a.out.read_bytes()).hexdigest(), note="Outcome-blind: no permit or outcome file was opened.")
a.out_json.write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps(S, indent=1))
