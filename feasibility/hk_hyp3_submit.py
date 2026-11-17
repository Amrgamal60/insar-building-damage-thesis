"""Hong Kong Sentinel-1 interferograms via ASF HyP3 (NYC plan §17 step 4). Approved by the user on 2026-10-16:
option 1, "pre-2023 core" (~870 credits of the 8,000 monthly allowance).

Track 11 ascending, bursts 011_021605/06/07_IW3 (VV), which cover all of urban Hong Kong. Dates 2015-06-01 to
2023-04-30 (all InSAR before the order window). Each date is paired with its 3 nearest later dates plus the date nearest
to +1 year (within 24 days). Job type INSAR_ISCE_MULTI_BURST, 10x2 looks (~40 m), water mask on: 1 credit per pair.

Default is a dry run that writes the pair list. --submit sends only pairs not already submitted under JOB_NAME, and only
if the account is approved and has enough credits. With --resubmit-failed, a pair whose only jobs FAILED counts as not
submitted (used 2026-10-16 for 2 jobs that failed on ASF's side, with the user's approval). Needs ~/.netrc for urs.earthdata.nasa.gov.
Run from Alex/:  .venv-hyp3/bin/python -I feasibility/hk_hyp3_submit.py [--submit]   (uv venv: hyp3_sdk 7.7.8, asf_search 14.1.0)
"""
import argparse
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import asf_search as asf
import hyp3_sdk

OUT = Path(__file__).resolve().parent / "hongkong" / "hyp3"
BURSTS = ["011_021605_IW3", "011_021606_IW3", "011_021607_IW3"]
START, END = "2015-06-01T00:00:00Z", "2023-04-30T23:59:59Z"
JOB_NAME = "HK_T011_core_2015_2023"
NEAREST, YEAR_TOL = 3, 24


def burst_table():
    """Burst granule names per acquisition date; only dates with all three bursts are kept."""
    by_date = defaultdict(dict)
    for b in BURSTS:
        for r in asf.search(dataset=asf.DATASET.SLC_BURST, fullBurstID=b, polarization="VV", start=START, end=END):
            p = r.properties
            by_date[p["startTime"][:10]][b] = p["fileID"]
    full = {d: g for d, g in by_date.items() if len(g) == len(BURSTS)}
    return dict(sorted(full.items())), sorted(set(by_date) - set(full))


def pairs(dates):
    ds = [date.fromisoformat(d) for d in dates]
    out = set()
    for i, d in enumerate(ds):
        for j in range(i + 1, min(i + 1 + NEAREST, len(ds))):
            out.add((i, j))
        later = [(abs((e - d).days - 365), j) for j, e in enumerate(ds) if j > i]
        if later:
            gap, j = min(later)
            if gap <= YEAR_TOL:
                out.add((i, j))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--limit", type=int, help="submit at most this many pairs (e.g. 1 for a test job)")
    ap.add_argument("--resubmit-failed", action="store_true", help="treat pairs whose jobs all FAILED as not submitted")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    table, partial = burst_table()
    dates = list(table)
    pl = pairs(dates)
    rows = [{"reference_date": dates[i], "secondary_date": dates[j], "days": (date.fromisoformat(dates[j])
             - date.fromisoformat(dates[i])).days, "reference": [table[dates[i]][b] for b in BURSTS],
             "secondary": [table[dates[j]][b] for b in BURSTS]} for i, j in pl]
    (OUT / "burst_granules.json").write_text(json.dumps({"bursts": BURSTS, "dates_with_all_bursts": table,
                                                          "dates_missing_a_burst": partial}, indent=1))
    (OUT / "pairs.json").write_text(json.dumps(rows, indent=1))
    print(f"{len(dates)} dates with all 3 bursts ({dates[0]} to {dates[-1]}); {len(partial)} dates missing a burst; "
          f"{len(rows)} pairs (credits at 1 each)")
    hyp3 = hyp3_sdk.HyP3(prompt=False)
    info = hyp3.my_info()
    status = info.get("application_status")
    credits = hyp3.check_credits()
    print(f"HyP3 user {info.get('user_id')}: application_status {status}, remaining credits {credits}, "
          f"credits per month {info.get('credits_per_month')}")
    done = {(tuple(j.job_parameters["reference"]), tuple(j.job_parameters["secondary"]))
            for j in hyp3.find_jobs(name=JOB_NAME) if not (a.resubmit_failed and j.status_code == "FAILED")}
    todo = [r for r in rows if (tuple(r["reference"]), tuple(r["secondary"])) not in done]
    print(f"already submitted under {JOB_NAME}: {len(done)}; still to submit: {len(todo)}")
    if not a.submit:
        return
    if status != "APPROVED":
        raise SystemExit(f"account not approved for processing (status {status}); not submitting")
    if credits is not None and credits < len(todo):
        todo = todo[: int(credits)]  # nearest-date pairs come first in date order; the rest waits for the reset
        print(f"only {credits} credits left: submitting the first {len(todo)} pairs")
    if a.limit is not None:
        todo = todo[: a.limit]
    prepared = [hyp3_sdk.HyP3.prepare_insar_isce_multi_burst_job(
        reference=r["reference"], secondary=r["secondary"], name=JOB_NAME, apply_water_mask=True, looks="10x2")
        for r in todo]
    log = OUT / "submitted_jobs.jsonl"
    for k in range(0, len(prepared), 200):  # the API accepts at most 200 jobs per request
        ids = [j.job_id for j in hyp3.submit_prepared_jobs(prepared[k:k + 200])]
        with log.open("a") as f:
            f.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "job_name": JOB_NAME,
                                "n": len(ids), "job_ids": ids}) + "\n")
        print(f"submitted {len(ids)} jobs", flush=True)
    print(f"remaining credits {hyp3.check_credits()}")


if __name__ == "__main__":
    main()
