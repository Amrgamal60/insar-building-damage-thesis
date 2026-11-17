"""Checkpoint 1 (AUSTIN_PLAN §9 Baseline 2): the dates of non-foundation building permits on
the eligible houses, from which "the parcel's count of non-foundation BPs in the 5 years
before t_e" is taken for every risk-set row at the analysis step.

How the wording is applied (authors' choices, fixed before any InSAR file is opened):
- A BP is any row with permittype = BP, of any work class and permit class, linked to the
  house by tcad_id as in §4 rule 4.
- Non-foundation: the permit does not meet §4 rule 2 (the locked keyword regex after its
  exclusions, on the same five fields).
- Date: the application date, or the issue date if missing (as §4 rule 5).
- The count for a row is the number of such permits dated in [t_e - 5 years, t_e).
The table holds the house key and the date only. No InSAR value is read.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "candidates" / "scripts"))
from filter_keyword_matches import RX, blob_austin, exclusion  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--permits", type=Path, required=True)
p.add_argument("--grid", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)


def norm(s):
    s = s.astype("string").str.strip()
    return s.mask(s.eq("")).str.lstrip("0").mask(lambda v: v.eq(""))


g = pd.read_parquet(a.grid, columns=["prop_id", "geo"])
d = pd.read_csv(a.permits, dtype=str, keep_default_na=False)
d = d[d.permittype.eq("BP")].copy()
d["geo"] = norm(d.tcad_id)
d = d[d.geo.isin(set(g.geo))].copy()
d["date"] = pd.to_datetime(d.applieddate.where(d.applieddate.ne(""), d.issue_date), errors="coerce")
text = d.apply(lambda r: blob_austin(r.to_dict()), axis=1)
kw = text.map(lambda t: bool(RX.search(t)))
excl = pd.Series([exclusion(t, w) if k else None for t, w, k in zip(text, d.work_class, kw)], index=d.index)
d["foundation_match"] = kw & excl.isna()
o = d[~d.foundation_match & d.date.notna()][["geo", "date", "work_class"]].sort_values(["geo", "date"]).reset_index(drop=True)
o.insert(0, "prop_id", o.geo.map(g.set_index("geo").prop_id))
o[["prop_id", "geo", "date"]].to_parquet(a.out_private / "other_bp_dates.parquet", index=False)
ref = pd.Timestamp("2018-08-01")
c5 = o[(o.date < ref) & (o.date >= ref - pd.DateOffset(years=5))].groupby("geo").size().reindex(g.geo, fill_value=0)
S = dict(permits_sha256=hashlib.sha256(a.permits.read_bytes()).hexdigest(), eligible_houses=len(g),
         bp_on_eligible_houses=len(d), foundation_matches_left_out=int(d.foundation_match.sum()),
         undated_left_out=int((~d.foundation_match & d.date.isna()).sum()), non_foundation_bp=len(o),
         by_work_class=o.work_class.value_counts().head(10).to_dict(),
         date_range=[str(o.date.min().date()), str(o.date.max().date())],
         illustration_count_in_5_years_before_2018_08_01=dict(
             houses_with_none=int((c5 == 0).sum()), houses_with_one=int((c5 == 1).sum()), houses_with_two_or_more=int((c5 >= 2).sum()),
             mean=round(float(c5.mean()), 4), max=int(c5.max())),
         private_outputs_sha256={"other_bp_dates.parquet": hashlib.sha256((a.out_private / "other_bp_dates.parquet").read_bytes()).hexdigest()})
a.out_json.write_text(json.dumps(S, indent=1, default=int) + "\n")
print(json.dumps(S, indent=1, default=int))
