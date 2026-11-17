"""Checkpoint 1 (AUSTIN_PLAN §4 rules 1-8, §5 demolition censoring and survivorship counts, §6), option A.

Foundation events, the remodel negative-control events (seed 2031) and the demolition
censoring dates are built from the checkpoint-1 permit copy and the 2018 population.
Rules 1-3 are applied exactly as in c1_04_link_check.py (the locked regex and exclusions,
imported unchanged). No InSAR value is read. No description is written to the project.

How the frozen wording is applied (each choice is reported in the JSON):
- Rule 5: the date is applieddate; issue_date where applieddate is blank.
- Rule 6: a matched permit within 365 days of the first permit of an episode belongs to
  that episode. The event (rule 7) is the parcel's first episode, dated by its first
  permit, so it is the same under the chained reading (within 365 days of the previous
  permit); both episode counts are reported.
- Rule 7: "from 1980" = dates on or after 1980-01-01. Earlier matched permits are counted
  and ignored.
- Rule 8: a construction BP on the same parcel dated in [t_e - 3 years, t_e).
- §5 demolition: the first total-demolition permit dated on or after 2018-08-01.

Row-level output goes to OUT_PRIVATE; the project JSON holds counts only.
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
from filter_keyword_matches import RX, blob_austin, exclusion  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--permits", type=Path, required=True)
p.add_argument("--reference", type=Path, required=True)
p.add_argument("--diag-2026", type=Path, required=True)
p.add_argument("--out-private", type=Path, required=True)
p.add_argument("--out-json", type=Path, required=True)
a = p.parse_args()
a.out_private.mkdir(parents=True, exist_ok=False)

START, END, FROM = pd.Timestamp("2018-08-01"), pd.Timestamp("2025-11-30"), pd.Timestamp("1980-01-01")
CONSTRUCTION = ["New", "Demolition", "Addition", "Addition and Remodel", "Shell", "Relocation"]
REMODEL_RX = re.compile(r"kitchen|bath(?:room)?|cabinet|counter ?top|interior remodel", re.I)
PARTIAL_RX = re.compile(r"\bpartial\b", re.I)
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


S = dict(inputs=dict(permits=a.permits.name, permits_sha256=sha(a.permits),
                     population_sha256=sha(a.reference / "population_2018.parquet")),
         study_period=[str(START.date()), str(END.date())])

d = pd.read_csv(a.permits, dtype=str, keep_default_na=False)
d["date"] = pd.to_datetime(d.applieddate.where(d.applieddate.ne(""), d.issue_date), errors="coerce")
d["issue_used"] = d.applieddate.eq("")
d["geo"] = norm(d.tcad_id)
pop = pd.read_parquet(a.reference / "population_2018.parquet")
assert pop.geo.is_unique and pop.geo.notna().all()
pop_geo = set(pop.geo)
S["permit_rows"] = len(d)
S["population_houses"] = len(pop)
bp = d[d.permittype.eq("BP")]

# ---------------- rules 1-3 (as c1_04) and rule 4 ----------------
sub = bp[bp.work_class.isin(["Repair", "Remodel"])].copy()
text = sub.apply(lambda r: blob_austin(r.to_dict()), axis=1)
kw = text.map(lambda t: bool(RX.search(t)))
excl = pd.Series([exclusion(t, w) if k else None for t, w, k in zip(text, sub.work_class, kw)], index=sub.index)
q = sub[kw & excl.isna() & sub.permit_class_mapped.eq("Residential")].copy()
S["foundation"] = dict(rules_1_to_3=len(q))
m_all = q[q.geo.isin(pop_geo)].copy()
S["foundation"]["rule4_on_population_houses"] = len(m_all)
S["foundation"]["undated"] = int(m_all.date.isna().sum())
S["foundation"]["dated_before_1980_ignored"] = int((m_all.date < FROM).sum())


def first_episodes(m, label):
    """Per parcel: the first matched permit from 1980, and episode counts under both readings."""
    m = m[m.date.notna() & (m.date >= FROM)].sort_values(["geo", "date", "permit_number"]).copy()
    out = dict(permits_from_1980=len(m), houses=int(m.geo.nunique()))
    gap_prev = m.groupby("geo").date.diff().dt.days
    out["episodes_chained_reading"] = int((gap_prev.isna() | (gap_prev > 365)).sum())
    n_anchor = 0
    for _, days in m.assign(t=(m.date - FROM).dt.days).groupby("geo").t:
        start = None
        for t in days.to_numpy():
            if start is None or t - start > 365:
                start, n_anchor = t, n_anchor + 1
    out["episodes_anchored_reading"] = n_anchor
    first = m.groupby("geo", as_index=False).first()[["geo", "date", "permit_number", "issue_used", "work_class"]]
    first = first.rename(columns={"date": "t_first", "permit_number": "first_permit_number"})
    first["n_matched_permits"] = first.geo.map(m.geo.value_counts())
    S[label].update(out)
    return first


con = bp[bp.work_class.isin(CONSTRUCTION) & bp.geo.isin(pop_geo) & bp.date.notna()][["geo", "date"]]


def apply_rules_7_8(first, label):
    first["status"] = "event"
    first.loc[first.t_first < START, "status"] = "first episode before the study period"
    first.loc[first.t_first > END, "status"] = "first episode after the study period"
    cand = first[first.status.eq("event")]
    j = cand[["geo", "t_first"]].merge(con, on="geo")
    recent = j[(j.date < j.t_first) & (j.date >= j.t_first - pd.DateOffset(years=3))]
    first.loc[first.geo.isin(set(recent.geo)) & first.status.eq("event"), "status"] = "excluded: construction BP in the 3 years before"
    S[label]["first_episode_status"] = first.status.value_counts().to_dict()
    ev = first[first.status.eq("event")]
    # §4: the 24-month window before the event month must lie inside the granule series.
    w_end = ev.t_first.dt.to_period("M").dt.to_timestamp()
    assert ((w_end - pd.DateOffset(months=24)) >= FIRST_GRANULE).all()
    assert ((w_end - pd.Timedelta(days=1)) < LAST_GRANULE + pd.Timedelta(days=12)).all()
    S[label]["events"] = len(ev)
    S[label]["events_dated_by_issue_date"] = int(ev.issue_used.sum())
    S[label]["events_by_year"] = ev.t_first.dt.year.value_counts().sort_index().to_dict()
    return first


first = first_episodes(m_all, "foundation")
first = apply_rules_7_8(first, "foundation")
ev = first[first.status.eq("event")].copy()
ev["month"] = ev.t_first.dt.strftime("%Y-%m")
months = [str(x) for x in pd.period_range(START, END, freq="M")]
by_month = ev.month.value_counts().reindex(months, fill_value=0)
S["foundation"]["events_by_month"] = by_month.to_dict()
S["foundation"]["events_by_work_class"] = ev.work_class.value_counts().to_dict()
S["foundation"]["events_by_matched_permits_on_house"] = ev.n_matched_permits.clip(upper=4).value_counts().sort_index().to_dict()
S["section6"] = dict(events_in_primary_population=len(ev), threshold=300, passes=bool(len(ev) >= 300))

# ---------------- demolition censoring (§5) ----------------
dem = bp[bp.work_class.eq("Demolition") & bp.permit_class_mapped.eq("Residential") & bp.geo.isin(pop_geo) & bp.date.notna()].copy()
total = ~dem.description.map(lambda s: bool(PARTIAL_RX.search(s)))
S["demolition"] = dict(residential_demolition_bp_on_population_houses=len(dem), partial_by_description=int((~total).sum()))
dem_t = dem[total & (dem.date >= START)].sort_values(["geo", "date", "permit_number"])
cens = dem_t.groupby("geo", as_index=False).first()[["geo", "date", "permit_number", "issue_used"]].rename(columns={"date": "t_demolition"})
S["demolition"]["total_demolition_permits_from_study_start"] = len(dem_t)
S["demolition"]["houses_censored_from_study_start"] = len(cens)
S["demolition"]["houses_censored_within_study_period"] = int((cens.t_demolition <= END).sum())
S["demolition"]["houses_censored_by_year"] = cens.t_demolition.dt.year.value_counts().sort_index().to_dict()
ev = ev.merge(cens[["geo", "t_demolition"]], on="geo", how="left")
ev["censored_on_or_before_event"] = ev.t_demolition.notna() & (ev.t_demolition <= ev.t_first)
S["demolition"]["events_on_houses_censored_on_or_before_the_event"] = int(ev.censored_on_or_before_event.sum())
S["demolition"]["events_on_houses_demolished_later_in_the_study_period"] = int((ev.t_demolition.notna() & (ev.t_demolition > ev.t_first) & (ev.t_demolition <= END)).sum())

# ---------------- survivorship counts (§5) ----------------
d26 = pd.read_parquet(a.diag_2026, columns=["prop_id", "imprv_type_cd"])
det26 = set(d26.loc[d26.imprv_type_cd.eq("01"), "prop_id"])
pop["in_2026_detached"] = pop.prop_id.isin(det26)
g26 = pop.set_index("geo").in_2026_detached
in_period = m_all[m_all.date.between(START, END)]
k = int((~in_period.geo.map(g26)).sum())
S["survivorship"] = dict(
    population_houses_not_in_2026_detached_population=int((~pop.in_2026_detached).sum()),
    rule_1_to_3_permits_in_study_period_on_population_houses=len(in_period),
    of_which_at_houses_not_in_2026_detached_population=k,
    percent=round(100 * k / len(in_period), 3),
    events=len(ev), events_at_houses_not_in_2026_detached_population=int((~ev.geo.map(g26)).sum()),
    events_percent=round(100 * float((~ev.geo.map(g26)).mean()), 3))
shared = pd.read_parquet(a.reference / "roll_keys_2018.parquet")
shared = set(shared.loc[~shared.in_population & shared.geo.notna(), "geo"]) & pop_geo
S["foundation"]["events_on_keys_shared_with_a_non_population_roll_parcel"] = int(ev.geo.isin(shared).sum())

# ---------------- remodel negative-control events (§4, seed 2031) ----------------
rem = bp[bp.work_class.eq("Remodel") & bp.permit_class_mapped.eq("Residential")].copy()
hit = rem.description.map(lambda s: bool(REMODEL_RX.search(s)))
fnd = rem.description.map(lambda s: bool(RX.search(s)))
S["remodel"] = dict(residential_remodel_bp=len(rem), description_matches_remodel_regex=int(hit.sum()),
                    of_which_also_match_foundation_regex_dropped=int((hit & fnd).sum()))
r_all = rem[hit & ~fnd & rem.geo.isin(pop_geo)].copy()
S["remodel"]["rule4_on_population_houses"] = len(r_all)
S["remodel"]["undated"] = int(r_all.date.isna().sum())
S["remodel"]["dated_before_1980_ignored"] = int((r_all.date < FROM).sum())
rfirst = first_episodes(r_all, "remodel")
rfirst = apply_rules_7_8(rfirst, "remodel")
rc = rfirst[rfirst.status.eq("event")].copy()
rc["month"] = rc.t_first.dt.strftime("%Y-%m")
rng = np.random.default_rng(2031)
picked, short = [], {}
for mth in months:
    need = int(by_month[mth])
    c = rc[rc.month.eq(mth)].sort_values(["t_first", "geo"])
    if len(c) < need:
        short[mth] = dict(needed=need, available=len(c))
        picked.append(c)
    else:
        picked.append(c.iloc[np.sort(rng.choice(len(c), size=need, replace=False))])
ctrl = pd.concat(picked, ignore_index=True)
S["remodel"]["candidate_control_events"] = len(rc)
S["remodel"]["sampled_control_events"] = len(ctrl)
S["remodel"]["months_with_too_few_candidates"] = short
S["remodel"]["sampled_at_houses_holding_a_foundation_event"] = int(ctrl.geo.isin(set(ev.geo)).sum())
S["remodel"]["sampled_at_houses_with_any_foundation_episode"] = int(ctrl.geo.isin(set(first.geo)).sum())
S["remodel"]["sampled_by_year"] = ctrl.t_first.dt.year.value_counts().sort_index().to_dict()

# ---------------- output ----------------
key = pop.set_index("geo").prop_id
for frame in (first, ev, cens, rfirst, ctrl):
    frame.insert(0, "prop_id", frame.geo.map(key))
first.to_parquet(a.out_private / "foundation_first_episodes.parquet", index=False)
ev.to_parquet(a.out_private / "foundation_events.parquet", index=False)
cens.to_parquet(a.out_private / "demolition_censoring.parquet", index=False)
rfirst.to_parquet(a.out_private / "remodel_first_episodes.parquet", index=False)
ctrl.to_parquet(a.out_private / "remodel_control_events.parquet", index=False)
S["private_outputs_sha256"] = {f.name: sha(f) for f in sorted(a.out_private.glob("*.parquet"))}
a.out_json.write_text(json.dumps(S, indent=1, default=int) + "\n")
print(json.dumps(S, indent=1, default=int))
