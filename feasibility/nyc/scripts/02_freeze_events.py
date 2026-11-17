"""Freeze the NYC event file: apply the audit's final rule (01_audit_events.py funnel) to out/events_clean.csv and
write out/events_final.csv, one row per event with a stable ID. No new rule is introduced here.
Kept: geocoded to an address-level lot in the stated borough; within 150 m of the OEM point (or no usable OEM point);
lot has a PLUTO record; no major works permitted on the lot, and no new-building, demolition or excavation permit
within 50 m on the block, in the 365 days before the event.
Usage: python -I scripts/02_freeze_events.py out"""
import sys
from pathlib import Path

import pandas as pd

OUT = Path(sys.argv[1])
e = pd.read_csv(OUT / "events_clean.csv", dtype={"bbl": str, "bin": str})
d = pd.to_numeric(e.dist_geo_oem_m, errors="coerce")
keep = (e.geo_addr_level & e.geo_boro_ok & (d.isna() | (d <= 150)) & e.bldgclass.notna()
        & e.works_before.isna() & e.adjacent_works_before.isna())
f = e[keep].copy()
f.insert(0, "event_id", [f"NYC{i:03d}" for i in range(1, len(f) + 1)])
f = f[["event_id", "date", "address", "boro", "types", "n_reports", "bbl", "bin", "geo_label", "geo_lat", "geo_lon",
       "yearbuilt", "bldgclass", "insar_years_before"]]
f.to_csv(OUT / "events_final.csv", index=False)
print(f"{len(f)} events, {f.date.min()} to {f.date.max()}; on or after 2017-07-16: {(f.date >= '2017-07-16').sum()}")
