"""Final part of Miami's go/no-go check (NYC plan §17 step 2): OPERA DISP-S1 pixel validity at the unsafe-structure cases.

For each case opened since 2017, the 30 m pixel holding its point is read in every downloaded granule (frame 12638).
A pixel counts as valid in a granule when displacement is finite and recommended_mask is 1. The script reports how many
cases are valid in at least 50%, 80% and 100% of granules, and the median temporal coherence at the cases.
No displacement value is related to the outcome here. Writes miami/audit/opera_coverage.json.
Run from Alex/:  OMP_NUM_THREADS=1 ~/miniforge3/envs/opera/bin/python -I feasibility/audit_miami_opera.py
"""
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from pyproj import Transformer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_hk_miami import ROOT, pages  # noqa: E402

D = ROOT / "miami" / "downloads"
v = pages(D / "building_violations")
u = v[(v.CASE_TYPE == "Unsafe Structure") & v.lon.notna()].copy()
u = u[pd.to_datetime(u.OPEN_DATE, unit="ms").dt.year >= 2017]
files = sorted((D / "opera_disp").glob("*.nc"))
with h5py.File(files[0]) as h:
    x, y = h["x"][:], h["y"][:]
X, Y = Transformer.from_crs("EPSG:4326", "EPSG:32617", always_xy=True).transform(u.lon.values, u.lat.values)
col = np.rint((X - x[0]) / (x[1] - x[0])).astype(int)
row = np.rint((Y - y[0]) / (y[1] - y[0])).astype(int)
inside = (row >= 0) & (row < len(y)) & (col >= 0) & (col < len(x))
r, c = row[inside], col[inside]
valid = np.zeros((len(files), inside.sum()), bool)
tcoh = np.full((len(files), inside.sum()), np.nan, np.float32)
for k, f in enumerate(files):
    with h5py.File(f) as h:
        d = h["displacement"][:][r, c]
        m = h["recommended_mask"][:][r, c]
        tcoh[k] = h["temporal_coherence"][:][r, c]
    valid[k] = np.isfinite(d) & (m == 1)
share = valid.mean(axis=0)
out = {"cases_since_2017": int(len(u)), "inside_subset": int(inside.sum()), "granules": len(files),
       "valid_in_at_least_50pct": int((share >= 0.5).sum()), "valid_in_at_least_80pct": int((share >= 0.8).sum()),
       "valid_in_all": int((share == 1).sum()), "folios_valid_80pct": int(u.FOLIO.values[inside][share >= 0.8].size and
                                                                          pd.Series(u.FOLIO.values[inside][share >= 0.8]).nunique()),
       "median_temporal_coherence_at_cases": float(np.nanmedian(tcoh)),
       "rule": "valid = finite displacement and recommended_mask == 1, per granule"}
(ROOT / "miami" / "audit" / "opera_coverage.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=1))
