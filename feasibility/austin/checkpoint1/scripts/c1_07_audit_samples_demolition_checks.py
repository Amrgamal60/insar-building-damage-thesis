"""Checkpoint 1 (AUSTIN_PLAN §4 label audit sample; §5 demolition audit sample and checks (a)-(b)).

Permits only. No InSAR value is read. Descriptions go to OUT_PRIVATE only.

- Label audit sample (§4): 100 events, seed 2028, from the events sorted by date and key.
  The row read by hand is the first permit of the event's episode (it dates the event).
- Demolition audit sample (§5): 50 permits, seed 2036, from the censoring permits (each
  house's first total-demolition permit dated on or after 2018-08-01), sorted by date and key.
- Check (a): the share of total-demolition permits whose description matches the locked
  foundation regex. The other four fields of the keyword protocol hold no free text for a
  Demolition BP, so the description alone is tested.
- Check (b): demolition rate per house-year after a matched foundation episode against
  houses without one. Follow-up runs from 2018-08-01 to the house's first total-demolition
  permit or 2025-11-30. Person-time is split at the date of the house's first matched permit
  (§4 rules 1-4, any date from 1980); a house whose episode is before 2018-08-01 is exposed
  throughout. A demolition dated on the episode date itself is counted as unexposed.
  Mantel-Haenszel rate ratio over deciles of year built, Greenland-Robins variance.
  Eligibility here is the primary population; the frame clip (§5) is not yet applied.
"""
import argparse
import hashlib
import json
import math
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

START, END = pd.Timestamp("2018-08-01"), pd.Timestamp("2025-11-30")
Z = 1.959963984540054


def norm(s):
    s = s.astype("string").str.strip()
    return s.mask(s.eq("")).str.lstrip("0").mask(lambda v: v.eq(""))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def wilson(k, n):
    ph = k / n
    c = (ph + Z * Z / (2 * n)) / (1 + Z * Z / n)
    h = Z * math.sqrt(ph * (1 - ph) / n + Z * Z / (4 * n * n)) / (1 + Z * Z / n)
    return dict(count=int(k), denominator=int(n), percent=round(100 * ph, 3),
                wilson95=[round(100 * (c - h), 3), round(100 * (c + h), 3)])


E = json.loads(a.events_json.read_text())
for name in ("foundation_events.parquet", "foundation_first_episodes.parquet", "demolition_censoring.parquet"):
    assert sha(a.events_private / name) == E["private_outputs_sha256"][name], name
assert sha(a.permits) == E["inputs"]["permits_sha256"]
ev = pd.read_parquet(a.events_private / "foundation_events.parquet")
fe = pd.read_parquet(a.events_private / "foundation_first_episodes.parquet")
cens = pd.read_parquet(a.events_private / "demolition_censoring.parquet")
pop = pd.read_parquet(a.reference / "population_2018.parquet")
S = dict(inputs=dict(permits_sha256=E["inputs"]["permits_sha256"], population_sha256=E["inputs"]["population_sha256"]))

d = pd.read_csv(a.permits, dtype=str, keep_default_na=False)
d["date"] = pd.to_datetime(d.applieddate.where(d.applieddate.ne(""), d.issue_date), errors="coerce")
d["geo"] = norm(d.tcad_id)
bp = d[d.permittype.eq("BP")]
SHOW = ["permit_number", "work_class", "permit_class", "permit_class_mapped", "permit_type_desc", "applieddate", "issue_date", "description"]

# ---------------- label audit sample (§4, seed 2028) ----------------
ev = ev.sort_values(["t_first", "geo"]).reset_index(drop=True)
pick = np.sort(np.random.default_rng(2028).choice(len(ev), size=100, replace=False))
lab = ev.iloc[pick][["prop_id", "geo", "t_first", "first_permit_number", "n_matched_permits"]]
rows = bp[bp.work_class.isin(["Repair", "Remodel"])].merge(
    lab.rename(columns={"first_permit_number": "permit_number"}), on=["permit_number", "geo"])
rows = rows[rows.date.eq(rows.t_first)]
assert len(rows) == 100 and rows.permit_number.is_unique
rows = rows.sort_values(["t_first", "geo"]).reset_index(drop=True)
rows.insert(0, "audit_id", [f"L{i + 1:03d}" for i in range(len(rows))])
rows[["audit_id", "prop_id", "geo", "n_matched_permits"] + SHOW].to_csv(a.out_private / "label_audit_sample.csv", index=False)
S["label_audit_sample"] = dict(events=len(ev), drawn=len(rows), seed=2028,
                               by_year=rows.t_first.dt.year.value_counts().sort_index().to_dict())

# ---------------- demolition audit sample (§5, seed 2036) ----------------
cens = cens.sort_values(["t_demolition", "geo"]).reset_index(drop=True)
pick = np.sort(np.random.default_rng(2036).choice(len(cens), size=50, replace=False))
dm = cens.iloc[pick][["prop_id", "geo", "t_demolition", "permit_number"]]
drows = bp[bp.work_class.eq("Demolition")].merge(dm, on=["permit_number", "geo"])
drows = drows[drows.date.eq(drows.t_demolition)]
assert len(drows) == 50 and drows.permit_number.is_unique
drows = drows.merge(pop[["geo", "year_built", "living_area"]], on="geo").sort_values(["t_demolition", "geo"]).reset_index(drop=True)
drows.insert(0, "audit_id", [f"D{i + 1:03d}" for i in range(len(drows))])
drows[["audit_id", "prop_id", "geo", "year_built", "living_area"] + SHOW].to_csv(a.out_private / "demolition_audit_sample.csv", index=False)
S["demolition_audit_sample"] = dict(censoring_permits=len(cens), drawn=len(drows), seed=2036,
                                    by_year=drows.t_demolition.dt.year.value_counts().sort_index().to_dict())

# ---------------- check (a): foundation mentions in total-demolition permits ----------------
cp = bp[bp.work_class.eq("Demolition")].merge(cens[["geo", "permit_number", "t_demolition"]], on=["geo", "permit_number"])
cp = cp[cp.date.eq(cp.t_demolition)]
assert len(cp) == len(cens)
hit = cp.description.map(lambda s: bool(RX.search(s)))
inp = cp.t_demolition <= END
S["check_a"] = dict(
    censoring_permits_from_study_start=wilson(hit.sum(), len(cp)),
    censoring_permits_within_study_period=wilson((hit & inp).sum(), inp.sum()),
    matched_terms=cp.description[hit].map(lambda s: RX.search(s).group(0).lower()).value_counts().to_dict())
cp.loc[hit, ["geo"] + SHOW].to_csv(a.out_private / "check_a_foundation_mentions.csv", index=False)

# ---------------- check (b): demolition rate after a foundation episode ----------------
h = pop[["geo", "year_built"]].copy()
h["t_ep"] = h.geo.map(fe.set_index("geo").t_first)
h["t_dem"] = h.geo.map(cens.set_index("geo").t_demolition)
h["dem"] = h.t_dem.notna() & (h.t_dem <= END)
h["stop"] = h.t_dem.where(h.dem, END)
ep = h.t_ep.clip(lower=START).where(h.t_ep.notna(), pd.Timestamp.max.normalize())
split = np.minimum(ep, h.stop)
h["py0"] = (split - START).dt.days / 365.25
h["py1"] = (h.stop - split).dt.days / 365.25
h["d1"] = h.dem & h.t_ep.notna() & (h.t_ep < h.stop)
h["d0"] = h.dem & ~h.d1
assert (h.py0 >= 0).all() and (h.py1 >= 0).all()
h["stratum"] = pd.qcut(h.year_built, 10, duplicates="drop")
g = h.groupby("stratum", observed=True).agg(houses=("geo", "size"), a=("d1", "sum"), b=("d0", "sum"), T1=("py1", "sum"), T0=("py0", "sum"))
g["T"] = g.T1 + g.T0
num, den = (g.a * g.T0 / g["T"]).sum(), (g.b * g.T1 / g["T"]).sum()
rr = num / den
se = math.sqrt(((g.a + g.b) * g.T1 * g.T0 / g["T"] ** 2).sum() / (num * den))
a1, b0, T1, T0 = int(h.d1.sum()), int(h.d0.sum()), float(h.py1.sum()), float(h.py0.sum())
crude = (a1 / T1) / (b0 / T0)
se_c = math.sqrt(1 / a1 + 1 / b0)
S["check_b"] = dict(
    houses=len(h), houses_with_a_matched_episode_by_study_end=int((h.t_ep <= END).sum()),
    houses_with_episode_before_study_start=int((h.t_ep < START).sum()),
    demolitions_in_study_period=int(h.dem.sum()),
    demolitions_dated_on_the_episode_date_counted_unexposed=int((h.dem & (h.t_ep == h.t_dem)).sum()),
    exposed=dict(demolitions=a1, house_years=round(T1, 1), rate_per_1000_house_years=round(1000 * a1 / T1, 3)),
    unexposed=dict(demolitions=b0, house_years=round(T0, 1), rate_per_1000_house_years=round(1000 * b0 / T0, 3)),
    crude_rate_ratio=round(crude, 4),
    crude_95=[round(crude * math.exp(-Z * se_c), 4), round(crude * math.exp(Z * se_c), 4)],
    mantel_haenszel_rate_ratio=round(rr, 4),
    mantel_haenszel_95=[round(rr * math.exp(-Z * se), 4), round(rr * math.exp(Z * se), 4)],
    strata=[dict(year_built=str(i), houses=int(r.houses), exposed_demolitions=int(r.a), unexposed_demolitions=int(r.b),
                 exposed_house_years=round(r.T1, 1), unexposed_house_years=round(r.T0, 1),
                 rate_ratio=(round((r.a / r.T1) / (r.b / r.T0), 3) if r.a and r.b else None)) for i, r in g.iterrows()])
S["private_outputs_sha256"] = {f.name: sha(f) for f in sorted(a.out_private.glob("*.csv"))}
a.out_json.write_text(json.dumps(S, indent=1, default=int) + "\n")
print(json.dumps(S, indent=1, default=int))
