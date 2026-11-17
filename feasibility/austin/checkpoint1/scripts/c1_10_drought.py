"""Checkpoint 1 (AUSTIN_PLAN §4 permits and drought). Labels only; no InSAR value is read.

Spearman correlation between the annual count of matched repair permits (issue year
2008-2025) and the previous year's mean Palmer Drought Severity Index of the NOAA climate
division that contains Austin (Travis County, FIPS 48453, looked up in NOAA's county table).

How the wording is applied:
- "Matched repair permits ... building permits with the work-class rule": §4 rules 1 and 2
  (BP, work class Repair or Remodel, the locked regex and exclusions). This is the stated
  measure. The same count with rule 3 (Residential), and with rules 3 and 4 (population
  houses), is reported beside it.
- Issue year: the year of issue_date.
- Previous year's mean PDSI: the mean of the 12 monthly values of the calendar year before.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "candidates" / "scripts"))
from filter_keyword_matches import RX, blob_austin, exclusion  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--permits", type=Path, required=True)
p.add_argument("--reference", type=Path, required=True)
p.add_argument("--noaa", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def norm(s):
    s = s.astype("string").str.strip()
    return s.mask(s.eq("")).str.lstrip("0").mask(lambda v: v.eq(""))


rec = json.loads((a.noaa / "download.json").read_text())
pdsi_file = a.noaa / rec["pdsi_file"]
assert sha(pdsi_file) == rec["files"][rec["pdsi_file"]]["sha256"]
div = [ln.split() for ln in (a.noaa / "county-to-climdivs.txt").read_text().splitlines() if ln.startswith("48453 ")]
assert len(div) == 1
division = div[0][2]
pdsi = {}
for ln in pdsi_file.read_text().splitlines():
    if ln[:4] == division and ln[4:6] == "05":
        vals = [float(v) for v in ln[10:].split()]
        assert len(vals) == 12
        pdsi[int(ln[6:10])] = vals
YEARS = list(range(2008, 2026))
assert all(min(pdsi[y - 1]) > -99 for y in YEARS)
prev = {y: sum(pdsi[y - 1]) / 12 for y in YEARS}

d = pd.read_csv(a.permits, dtype=str, keep_default_na=False)
sub = d[d.permittype.eq("BP") & d.work_class.isin(["Repair", "Remodel"])].copy()
text = sub.apply(lambda r: blob_austin(r.to_dict()), axis=1)
kw = text.map(lambda t: bool(RX.search(t)))
excl = pd.Series([exclusion(t, w) if k else None for t, w, k in zip(text, sub.work_class, kw)], index=sub.index)
q = sub[kw & excl.isna()].copy()
q["year"] = pd.to_datetime(q.issue_date, errors="coerce").dt.year
pop_geo = set(pd.read_parquet(a.reference / "population_2018.parquet", columns=["geo"]).geo)
res3 = q.permit_class_mapped.eq("Residential")
onpop = norm(q.tcad_id).isin(pop_geo)
series = {
    "rules_1_2": q,
    "rules_1_3_residential": q[res3],
    "rules_1_4_population_houses": q[res3 & onpop],
}
S = dict(inputs=dict(permits_sha256=sha(a.permits), pdsi_file=rec["pdsi_file"], pdsi_sha256=rec["files"][rec["pdsi_file"]]["sha256"]),
         climate_division=division, travis_county_fips="48453", issue_years=[YEARS[0], YEARS[-1]],
         matched_permits_without_issue_date=int(q.year.isna().sum()),
         previous_year_mean_pdsi={y: round(prev[y], 3) for y in YEARS}, results={})
for name, frame in series.items():
    counts = frame.year.value_counts().reindex(YEARS, fill_value=0).astype(int)
    r = spearmanr(counts.to_numpy(), [prev[y] for y in YEARS])
    S["results"][name] = dict(annual_counts=counts.to_dict(), n_years=len(YEARS),
                              spearman_rho=round(float(r.statistic), 4), p_two_sided=round(float(r.pvalue), 4))
a.out_json.write_text(json.dumps(S, indent=1, default=int) + "\n")
print(json.dumps(S, indent=1, default=int))
