"""Checkpoint 1: remodel negative-control events under the amended rule (AUSTIN_PLAN §14, 2026-11-10).

The frozen rule (§4: residential BPs of work class Remodel) gives 16 control events
(c1_05_events.py). The amended rule, logged in §14 before this script was run:

- Matching permits: residential BPs with work class Repair or Remodel whose description matches
  the remodel regex and does not match the foundation regex.
- The episode, first-event, recent-construction and study-period rules (§4 rules 4-8) as in
  c1_05_events.py, unchanged.
- Sample: months in calendar order with one generator (seed 2031). A month with more candidate
  control events than foundation events gives the foundation count, drawn without replacement.
  Any other month gives all its candidates.

The foundation events are read from the c1_05 output (hash checked against events_2018.json).
The frozen-rule count is recomputed with the same code as a check. No InSAR value is read. No
description is written to the project. Row-level output goes to OUT_PRIVATE.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "candidates" / "scripts"))
from filter_keyword_matches import RX  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--permits", type=Path, required=True)
p.add_argument("--reference", type=Path, required=True)
p.add_argument("--events-private", type=Path, required=True)
p.add_argument("--events-json", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)

START, END, FROM = pd.Timestamp("2018-08-01"), pd.Timestamp("2025-11-30"), pd.Timestamp("1980-01-01")
CONSTRUCTION = ["New", "Demolition", "Addition", "Addition and Remodel", "Shell", "Relocation"]
REMODEL_RX = re.compile(r"kitchen|bath(?:room)?|cabinet|counter ?top|interior remodel", re.I)
FIRST_GRANULE, LAST_GRANULE = pd.Timestamp("2016-07-10"), pd.Timestamp("2025-11-20")


def norm(s):
    s = s.astype("string").str.strip()
    return s.mask(s.eq("")).str.lstrip("0").mask(lambda v: v.eq(""))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


E = json.loads(a.events_json.read_text())
S = dict(inputs=dict(permits=a.permits.name, permits_sha256=sha(a.permits),
                     population_sha256=sha(a.reference / "population_2018.parquet")),
         study_period=[str(START.date()), str(END.date())])
assert S["inputs"]["permits_sha256"] == E["inputs"]["permits_sha256"]
assert S["inputs"]["population_sha256"] == E["inputs"]["population_sha256"]
for name in ("foundation_events.parquet", "foundation_first_episodes.parquet", "demolition_censoring.parquet"):
    assert sha(a.events_private / name) == E["private_outputs_sha256"][name], name
ev = pd.read_parquet(a.events_private / "foundation_events.parquet")
fe = pd.read_parquet(a.events_private / "foundation_first_episodes.parquet")
cens = pd.read_parquet(a.events_private / "demolition_censoring.parquet")
assert len(ev) == E["foundation"]["events"]
months = [str(x) for x in pd.period_range(START, END, freq="M")]
by_month = ev.t_first.dt.strftime("%Y-%m").value_counts().reindex(months, fill_value=0)
assert by_month.to_dict() == E["foundation"]["events_by_month"]
S["foundation_events"] = len(ev)

d = pd.read_csv(a.permits, dtype=str, keep_default_na=False)
d["date"] = pd.to_datetime(d.applieddate.where(d.applieddate.ne(""), d.issue_date), errors="coerce")
d["issue_used"] = d.applieddate.eq("")
d["geo"] = norm(d.tcad_id)
pop = pd.read_parquet(a.reference / "population_2018.parquet")
assert pop.geo.is_unique and pop.geo.notna().all()
pop_geo = set(pop.geo)
bp = d[d.permittype.eq("BP")]
con = bp[bp.work_class.isin(CONSTRUCTION) & bp.geo.isin(pop_geo) & bp.date.notna()][["geo", "date"]]


def build(work_classes):
    """Candidate control events for the given work classes: §4 rules 4-8 as in c1_05_events.py."""
    out = {}
    rem = bp[bp.work_class.isin(work_classes) & bp.permit_class_mapped.eq("Residential")]
    hit = rem.description.map(lambda s: bool(REMODEL_RX.search(s)))
    fnd = rem.description.map(lambda s: bool(RX.search(s)))
    out["residential_bp_of_these_work_classes"] = len(rem)
    out["description_matches_remodel_regex"] = int(hit.sum())
    out["of_which_also_match_foundation_regex_dropped"] = int((hit & fnd).sum())
    m = rem[hit & ~fnd & rem.geo.isin(pop_geo)]
    out["rule4_on_population_houses"] = len(m)
    out["undated"] = int(m.date.isna().sum())
    out["dated_before_1980_ignored"] = int((m.date < FROM).sum())
    m = m[m.date.notna() & (m.date >= FROM)].sort_values(["geo", "date", "permit_number"])
    out["permits_from_1980"] = len(m)
    out["houses"] = int(m.geo.nunique())
    gap_prev = m.groupby("geo").date.diff().dt.days
    out["episodes_chained_reading"] = int((gap_prev.isna() | (gap_prev > 365)).sum())
    first = m.groupby("geo", as_index=False).first()[["geo", "date", "permit_number", "issue_used", "work_class"]]
    first = first.rename(columns={"date": "t_first", "permit_number": "first_permit_number"})
    first["n_matched_permits"] = first.geo.map(m.geo.value_counts())
    first["status"] = "event"
    first.loc[first.t_first < START, "status"] = "first episode before the study period"
    first.loc[first.t_first > END, "status"] = "first episode after the study period"
    cand = first[first.status.eq("event")]
    j = cand[["geo", "t_first"]].merge(con, on="geo")
    recent = j[(j.date < j.t_first) & (j.date >= j.t_first - pd.DateOffset(years=3))]
    first.loc[first.geo.isin(set(recent.geo)) & first.status.eq("event"), "status"] = "excluded: construction BP in the 3 years before"
    out["first_episode_status"] = first.status.value_counts().to_dict()
    rc = first[first.status.eq("event")].copy()
    w_end = rc.t_first.dt.to_period("M").dt.to_timestamp()
    assert ((w_end - pd.DateOffset(months=24)) >= FIRST_GRANULE).all()
    assert ((w_end - pd.Timedelta(days=1)) < LAST_GRANULE + pd.Timedelta(days=12)).all()
    rc["month"] = rc.t_first.dt.strftime("%Y-%m")
    out["candidate_control_events"] = len(rc)
    return first, rc, out


_, rc_frozen, frozen = build(["Remodel"])
S["frozen_rule_check"] = dict(candidate_control_events=len(rc_frozen),
                              matches_c1_05=bool(len(rc_frozen) == E["remodel"]["candidate_control_events"]))
assert S["frozen_rule_check"]["matches_c1_05"]

rfirst, rc, S["amended"] = build(["Repair", "Remodel"])
A = S["amended"]
A["candidates_by_work_class"] = rc.work_class.value_counts().to_dict()
A["candidates_by_year"] = rc.t_first.dt.year.value_counts().sort_index().to_dict()
A["candidates_dated_by_issue_date"] = int(rc.issue_used.sum())

rng = np.random.default_rng(2031)
picked, short, drawn_months = [], {}, 0
for mth in months:
    need = int(by_month[mth])
    c = rc[rc.month.eq(mth)].sort_values(["t_first", "geo"])
    if len(c) > need:
        picked.append(c.iloc[np.sort(rng.choice(len(c), size=need, replace=False))])
        drawn_months += 1
    else:
        picked.append(c)
        if len(c) < need:
            short[mth] = dict(needed=need, available=len(c))
ctrl = pd.concat(picked, ignore_index=True)
assert ctrl.geo.is_unique
ctrl = ctrl.merge(cens[["geo", "t_demolition"]], on="geo", how="left")
ctrl["censored_on_or_before_event"] = ctrl.t_demolition.notna() & (ctrl.t_demolition <= ctrl.t_first)
A["sampled_control_events"] = len(ctrl)
A["sampled_share_of_foundation_events"] = round(len(ctrl) / len(ev), 4)
A["months"] = dict(total=len(months), drawn_to_the_foundation_count=drawn_months,
                   equal_all_taken=len(months) - drawn_months - len(short), too_few_all_taken=len(short))
A["months_with_too_few_candidates"] = short
A["sampled_by_year"] = ctrl.t_first.dt.year.value_counts().sort_index().to_dict()
A["foundation_events_by_year"] = ev.t_first.dt.year.value_counts().sort_index().to_dict()
A["sampled_by_month"] = ctrl.month.value_counts().reindex(months, fill_value=0).to_dict()
A["sampled_by_work_class"] = ctrl.work_class.value_counts().to_dict()
A["sampled_by_matched_permits_on_house"] = ctrl.n_matched_permits.clip(upper=4).value_counts().sort_index().to_dict()
A["sampled_at_houses_holding_a_foundation_event"] = int(ctrl.geo.isin(set(ev.geo)).sum())
A["sampled_at_houses_with_any_foundation_episode"] = int(ctrl.geo.isin(set(fe.geo)).sum())
A["sampled_on_houses_censored_on_or_before_the_event"] = int(ctrl.censored_on_or_before_event.sum())

key = pop.set_index("geo").prop_id
for frame in (rfirst, ctrl):
    frame.insert(0, "prop_id", frame.geo.map(key))
rfirst.to_parquet(a.out_private / "remodel_first_episodes_amended.parquet", index=False)
ctrl.to_parquet(a.out_private / "remodel_control_events_amended.parquet", index=False)
S["private_outputs_sha256"] = {f.name: sha(f) for f in sorted(a.out_private.glob("*.parquet"))}
a.out_json.write_text(json.dumps(S, indent=1, default=int) + "\n")
print(json.dumps(S, indent=1, default=int))
