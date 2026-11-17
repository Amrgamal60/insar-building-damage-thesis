"""Inputs of secondaries 5 and 10 for the processing server (AUSTIN_PLAN.md §12 items 5 and 10; §15, 2026-11-15).
Only property IDs and dates leave the private area; no permit number, description or address is written.

  other_bp_dates.parquet               prop_id, date: the non-foundation building permits of checkpoint 1 (Baseline 2,
                                       "count of non-foundation BPs in the 5 years before t_e").
  foundation_first_episodes_issue.parquet  prop_id, t_first (issue date), t_application: the same 10,240 first matched
                                       episodes, dated by the issue date of the episode's first permit.
  foundation_events_issue.parquet      prop_id, t_first (issue date), t_application: the same 2,846 events, re-dated
                                       the same way.
Secondary 10 keeps the episodes and events of §4 and only re-dates them; §4 is not re-derived. Issue dates come from
the checkpoint-1 permit download (3syk-w9eu), by the episode's first permit number.

Usage: python -I export_secondary_server.py PRIVATE_CHECKPOINT1_DIR OUT_DIR
"""
import json
import sys
from pathlib import Path

import pandas as pd


def main(src, out):
    src, out = Path(src), Path(out)
    out.mkdir(parents=True, exist_ok=False)
    bp = pd.read_parquet(src / "other_bp" / "other_bp_dates.parquet", columns=["prop_id", "date"])
    bp["date"] = pd.to_datetime(bp.date).astype("datetime64[ns]")
    bp.sort_values(["prop_id", "date"], kind="stable").reset_index(drop=True).to_parquet(out / "other_bp_dates.parquet", index=False)
    perm = pd.read_csv(src / "permits_3syk-w9eu_20261109" / "3syk-w9eu_checkpoint1.csv",
                       usecols=["permit_number", "applieddate", "issue_date"], dtype=str).drop_duplicates("permit_number")
    perm["t_issue"] = pd.to_datetime(perm.issue_date, errors="coerce", utc=True).dt.tz_localize(None).dt.normalize()
    perm["t_app"] = pd.to_datetime(perm.applieddate, errors="coerce", utc=True).dt.tz_localize(None).dt.normalize()
    info = dict(other_bp_rows=int(len(bp)))
    for name in ("foundation_first_episodes", "foundation_events"):
        e = pd.read_parquet(src / "events" / f"{name}.parquet", columns=["prop_id", "t_first", "first_permit_number"])
        m = e.merge(perm[["permit_number", "t_issue", "t_app"]], left_on="first_permit_number", right_on="permit_number",
                    how="left", validate="many_to_one")
        t_app = pd.to_datetime(m.t_first).dt.normalize()
        assert m.t_issue.notna().all() and (t_app == m.t_app).all(), "issue date missing or application date differs"
        r = pd.DataFrame({"prop_id": m.prop_id.to_numpy(), "t_first": m.t_issue.astype("datetime64[ns]").to_numpy(),
                          "t_application": pd.to_datetime(m.t_first).astype("datetime64[ns]").to_numpy()})
        r = r.sort_values(["prop_id"], kind="stable").reset_index(drop=True)
        r.to_parquet(out / f"{name}_issue.parquet", index=False)
        info[name] = dict(rows=int(len(r)), same_date=int((r.t_first == r.t_application).sum()),
                          issue_before_application=int((r.t_first < r.t_application).sum()),
                          issue_month_after_2025_11=int((r.t_first.dt.to_period("M") > pd.Period("2025-11", "M")).sum()))
    (out / "export.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
