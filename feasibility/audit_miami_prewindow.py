"""Miami-Dade: OPERA DISP-S1 coverage in each case's own pre-case window (NYC plan §17; asked for in the 2026-10-17 GPT
review). Outcome-blind: only pixel validity is read (finite displacement and recommended_mask == 1, as in
audit_miami_opera.py); no displacement value is used or related to the cases.

For each unsafe-structure case opened since 2017, the granules whose secondary (observation) date falls in
[open date - W, open date) are taken, W = 1, 2 or 3 years. A case's window qualifies when
  (a) it starts inside the series (open date - W >= 2016-07-05, the first date),
  (b) the case opened no later than 90 days after the last granule (2026-02-07), so the window is mostly observed, and
  (c) the case pixel is valid in >= 80% of the granules in the window.
W = 2 years and the 80% / 90-day settings are provisional and outcome-blind (GPT review); they are to be fixed in the
deep-learning plan before any InSAR value is linked to a case. Counts are given per case, per folio (any qualifying
case) and per folio's first case since 2017; folios with an unsafe case before 2017 are counted too.
Writes miami/audit/opera_prewindow.json.
Run from Alex/:  OMP_NUM_THREADS=1 ~/miniforge3/envs/opera/bin/python -I feasibility/audit_miami_prewindow.py
"""
import json
import re
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from pyproj import Transformer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_hk_miami import ROOT, pages  # noqa: E402

D = ROOT / "miami" / "downloads"
SHARE, LATE_DAYS = 0.8, 90


def main():
    v = pages(D / "building_violations")
    us = v[(v.CASE_TYPE == "Unsafe Structure")].copy()
    us["open"] = pd.to_datetime(us.OPEN_DATE, unit="ms")
    earlier = set(us.FOLIO[us.open.dt.year < 2017].dropna())
    u = us[(us.open.dt.year >= 2017) & us.lon.notna()].copy()
    files = sorted((D / "opera_disp").glob("*.nc"))
    obs = pd.to_datetime([re.search(r"_VV_\d{8}T\d{6}Z_(\d{8})T", f.name).group(1) for f in files])
    first = pd.Timestamp(re.search(r"_VV_(\d{8})T", files[0].name).group(1))
    with h5py.File(files[0]) as h:
        x, y = h["x"][:], h["y"][:]
    X, Y = Transformer.from_crs("EPSG:4326", "EPSG:32617", always_xy=True).transform(u.lon.values, u.lat.values)
    col = np.rint((X - x[0]) / (x[1] - x[0])).astype(int)
    row = np.rint((Y - y[0]) / (y[1] - y[0])).astype(int)
    inside = (row >= 0) & (row < len(y)) & (col >= 0) & (col < len(x))
    u = u[inside].copy()
    r, c = row[inside], col[inside]
    valid = np.zeros((len(files), len(u)), bool)
    for k, f in enumerate(files):
        with h5py.File(f) as h:
            valid[k] = np.isfinite(h["displacement"][:][r, c]) & (h["recommended_mask"][:][r, c] == 1)
    out = {"cases_since_2017_inside": int(len(u)), "folios": int(u.FOLIO.nunique()), "granules": len(files),
           "series": [str(first.date()), str(obs.max().date())],
           "folios_with_unsafe_case_before_2017": int(len(set(u.FOLIO) & earlier)), "rule": __doc__.split("\n\n")[1]}
    u = u.sort_values("open")
    firsts = ~u.FOLIO.duplicated()
    for W in (1, 2, 3):
        start = u.open - pd.DateOffset(years=W)
        a = (start >= first).values
        b = (u.open <= obs.max() + pd.Timedelta(days=LATE_DAYS)).values
        inwin = (obs.values[:, None] >= start.values[None, :]) & (obs.values[:, None] < u.open.values[None, :])
        n = inwin.sum(0)
        share = np.where(n > 0, (valid & inwin).sum(0) / np.maximum(n, 1), 0.0)
        q = a & b & (n > 0) & (share >= SHARE)
        out[f"window_{W}y"] = {
            "starts_inside_series": int(a.sum()), "opened_within_90d_of_last_granule": int(b.sum()),
            "median_granules_in_window": float(np.median(n[a & b])) if (a & b).any() else None,
            "qualifying_cases": int(q.sum()), "qualifying_folios_any_case": int(u.FOLIO[q].nunique()),
            "qualifying_folios_first_case_since_2017": int(u.FOLIO[q & firsts.values].nunique()),
            "qualifying_cases_by_open_year": {int(k): int(n_) for k, n_ in u.open.dt.year[q].value_counts().sort_index().items()},
            "qualifying_cases_F_prefix": int(u.CASE_NUM[q].str.startswith("F").sum())}
    (ROOT / "miami" / "audit" / "opera_prewindow.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rule"}, indent=1))


if __name__ == "__main__":
    main()
