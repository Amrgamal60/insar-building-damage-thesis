"""Checkpoint 1 (AUSTIN_PLAN §4 parcel link check; §5 survivorship link check), option A, 2018 keys.

Permits meeting §4 rules 1-3 (BP with work class Repair or Remodel; the locked keyword regex
and exclusions of feasibility/candidates/keyword_protocol.md on the same five fields, imported
unchanged from feasibility/candidates/scripts/filter_keyword_matches.py; permit_class_mapped
Residential) are matched on tcad_id to the 2018 roll geo_id (§5 rule 2), with leading zeros
dropped on both sides as in step0/scripts_refdata/id_crosswalk.py. No event is built (rules
4-8 are not applied), no description is written out, no InSAR value is read.

Counts only go to OUT_JSON. No row-level output.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "candidates" / "scripts"))
from filter_keyword_matches import RX, blob_austin, exclusion  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--permits", type=Path, required=True)
p.add_argument("--reference", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()


def norm(s):
    s = s.astype("string").str.strip()
    return s.mask(s.eq("")).str.lstrip("0").mask(lambda v: v.eq(""))


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return None
    ph = k / n
    c = (ph + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return dict(count=int(k), denominator=int(n), percent=round(100 * ph, 3),
                wilson95=[round(100 * (c - h), 3), round(100 * (c + h), 3)])


d = pd.read_csv(a.permits, dtype=str, keep_default_na=False)
S = dict(permit_rows=len(d))
d["date"] = pd.to_datetime(d.applieddate.where(d.applieddate.ne(""), d.issue_date), errors="coerce")
r1 = d.permittype.eq("BP") & d.work_class.isin(["Repair", "Remodel"])
sub = d[r1].copy()
text = sub.apply(lambda r: blob_austin(r.to_dict()), axis=1)
kw = text.map(lambda t: bool(RX.search(t)))
excl = pd.Series([exclusion(t, w) if k else None for t, w, k in zip(text, sub.work_class, kw)], index=sub.index)
r2 = kw & excl.isna()
r3 = sub.permit_class_mapped.eq("Residential")
q = sub[r2 & r3].copy()
S["rules"] = dict(rule1_bp_repair_or_remodel=int(r1.sum()), rule2_keyword_match=int(kw.sum()),
                  rule2_excluded=excl.value_counts().to_dict(), rules_1_to_3=len(q))

ref = pd.read_parquet(a.reference / "roll_keys_2018.parquet")
pop = pd.read_parquet(a.reference / "population_2018.parquet", columns=["prop_id", "geo", "prop_id_in_2026_roll"])
pop_geo = set(pop.geo)
other = ref[~ref.in_population & ref.geo.notna()]
other_kind = other.assign(kind=other.prop_type_cd.where(~other.a1_real, "R, A1 not in population")).groupby("geo").kind.first()
q["geo"] = norm(q.tcad_id)
q["status"] = "unmatched"
q.loc[q.geo.isin(set(other.geo)), "status"] = "matched to another reference-roll parcel"
q.loc[q.geo.isin(pop_geo), "status"] = "matched to the primary population"
exact = q.tcad_id.str.strip().ne("") & q.tcad_id.str.strip().isin(set(ref.geo_id.str.strip()) - {""})


def link(frame):
    n = len(frame)
    out = dict(permits=n, blank_tcad_id=int(frame.geo.isna().sum()))
    out["matched_any_reference_parcel"] = wilson(frame.status.ne("unmatched").sum(), n)
    for st in ["matched to the primary population", "matched to another reference-roll parcel", "unmatched"]:
        out[st] = wilson(frame.status.eq(st).sum(), n)
    o = frame[frame.status.eq("matched to another reference-roll parcel")]
    out["other_parcel_by_kind"] = o.geo.map(other_kind).value_counts().to_dict()
    return out


S["link_check_all_dates"] = link(q)
S["link_check_all_dates"]["exact_string_match_without_zero_normalisation"] = int(exact.sum())
in_period = q.date.between("2018-08-01", "2025-11-30")
S["link_check_study_period_A"] = link(q[in_period])
S["link_check_study_period_A"]["note"] = "application date (issue date if missing) 2018-08-01..2025-11-30; reported only, not an event count"
S["pop_geo_also_on_other_parcel_permits"] = int(q.geo.isin(pop_geo & set(other.geo)).sum())
S["population_geo_ids_with_any_rule_1_3_permit_all_dates"] = int(q.loc[q.status.eq("matched to the primary population"), "geo"].nunique())

# §5 survivorship link check: permits of all types per house-year through 2018 keys, by year and
# by whether the 2018 property ID is present in the 2026 roll. House-years count every house in
# the category for the whole year (no demolition censoring); this is a diagnostic rate.
d["geo"] = norm(d.tcad_id)
g = pop.groupby("geo").prop_id_in_2026_roll.first()
linked = d[d.geo.isin(pop_geo)].copy()
linked["in_2026"] = linked.geo.map(g)
linked["year"] = linked.date.dt.year
houses = pop.prop_id_in_2026_roll.value_counts()
rows = []
for y in range(2016, 2026):
    for flag in [True, False]:
        k = int(((linked.year == y) & (linked.in_2026 == flag)).sum())
        rows.append(dict(year=y, prop_id_2018_in_2026_roll=flag, houses=int(houses[flag]), permits=k,
                         permits_per_100_house_years=round(100 * k / houses[flag], 3)))
S["survivorship_link_check"] = rows
a.out_json.write_text(json.dumps(S, indent=1, default=int) + "\n")
print(json.dumps(S, indent=1, default=int))
