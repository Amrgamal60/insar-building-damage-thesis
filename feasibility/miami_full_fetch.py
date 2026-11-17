"""Miami-Dade full case collection (NYC plan §17). Started after the validation batch passed rules R, D and Y
(miami/audit/label_validation/VALIDATION_REPORT.md). Blind to InSAR: no OPERA file is opened.

Population: every Unsafe Structure case opened 2017-01-01 or later in the bulk data, including the 100 label-audit and
250 validation cases. The same four viewer pages per case as miami_validation_sample.py, raw pages only to --raw
(outside the project: they hold names). Pages already fetched are copied from the --reuse folders instead of being
fetched again. A case with all four pages in --raw is skipped, so the run can be stopped and restarted. Pacing as in the
batch: one session per case, --workers sessions side by side, request starts at least 1.5 s apart across all of them.
Cases are fetched in a seeded random order, so a partial run is a random subset. A case that still fails after 8 tries
is logged and left for a later run.

The project keeps miami/full/cases.csv and violations.csv (the batch's columns: codes, standard descriptions and dates,
no names) and fetch_status.json, rebuilt from the raw pages at the end of a run or with --build.
Run from Alex/:  python3 -I feasibility/miami_full_fetch.py --raw <dir outside the project> [--reuse <dir> ...]
                 [--workers 5] [--build]
"""
import argparse
import csv
import glob
import http.cookiejar
import json
import random
import shutil
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from miami_case_sample import BASE, KEEP, ROOT, details, group, table  # noqa: E402  (also applies the IPv4 patch)
from miami_validation_sample import get, pace  # noqa: E402

OUT = ROOT / "full"
SEED = 20261019
TABS = ("USCaseDetails?CaseNum=", "ViolationsUS", "ActivitiesUS", "StructuresInfo")


def population():
    rows = []
    for f in sorted(glob.glob(str(ROOT / "downloads" / "building_violations" / "pages" / "*.geojson"))):
        rows += [x["properties"] for x in json.load(open(f))["features"]]
    us = {}
    for r in rows:
        if r["CASE_TYPE"] == "Unsafe Structure" and r["OPEN_DATE"]:
            year = datetime.fromtimestamp(r["OPEN_DATE"] / 1000, timezone.utc).year
            if year >= 2017:
                us[r["CASE_NUM"]] = dict(r, year=year, group=group(r["CASE_NUM"]))
    return us


def path(raw, cn, tab):
    return raw / f"{cn}_{tab.split('?')[0]}.html"


def fetch(raw, reuse, cn):
    """Returns None when all four pages are in place, else the error text."""
    for tab in TABS:
        f = path(raw, cn, tab)
        if not f.exists():
            for d in reuse:
                if (d / f.name).exists():
                    shutil.copy2(d / f.name, f)
                    break
    if all(path(raw, cn, t).exists() for t in TABS):
        return None
    # The three tabs depend on the session opened by the details page, so a case is fetched whole.
    err = None
    for attempt in range(8):
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        opener.addheaders = [("User-Agent", "Mozilla/5.0 (research label audit; low rate)")]
        try:
            pages = {}
            for tab in TABS:
                pace()
                pages[tab] = get(opener, BASE + (tab + cn if tab.endswith("=") else tab))
            assert details(pages[TABS[0]].decode("utf-8", "replace"))["Case Number"] == cn, "wrong case in session"
            for tab, data in pages.items():
                part = path(raw, cn, tab).with_suffix(".part")
                part.write_bytes(data)
                part.rename(path(raw, cn, tab))
            return None
        except Exception as e:  # any network, page or parse error: log and retry; a long run must not stop on one case
            err = f"{type(e).__name__}: {e}"
            print(f"{cn}: {err}; retry", flush=True)
            time.sleep(10 * (attempt + 1))
    return err


def build(raw, us):
    cases, viols, missing, mismatch = [], [], [], []
    for cn in sorted(us):
        if not all(path(raw, cn, t).exists() for t in TABS):
            missing.append(cn)
            continue
        pg = {t: path(raw, cn, t).read_text(encoding="utf-8", errors="replace") for t in TABS}
        d = details(pg[TABS[0]])
        if d.get("Case Number") != cn:
            mismatch.append(cn)
            continue
        r = us[cn]
        v = table(pg["ViolationsUS"])
        viols += [{"case": cn, "code": row[1].split(" ")[0], "description": row[1], "date": row[2]} for row in v]
        cases.append({"case": cn, "year": r["year"], "prefix_group": r["group"], "folio": r["FOLIO"],
                      "address": (r.get("PROP_ADDR") or "").strip(),
                      **{k.lower().replace(" ", "_"): d[k] for k in KEEP if k != "Case Number"},
                      "violation_codes": ";".join(row[1].split(" ")[0] for row in v),
                      "activities": len(table(pg["ActivitiesUS"]))})
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in (("cases", cases), ("violations", viols)):
        if rows:
            with open(OUT / f"{name}.csv", "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
    status = {"built": datetime.now(timezone.utc).isoformat(timespec="seconds"), "population": len(us),
              "complete": len(cases), "missing": len(missing), "wrong_case_in_page": mismatch}
    (OUT / "fetch_status.json").write_text(json.dumps(status, indent=1) + "\n")
    print(json.dumps(status), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="directory OUTSIDE the project for the raw pages (they hold names)")
    ap.add_argument("--reuse", nargs="*", default=[], help="folders with pages already fetched")
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--build", action="store_true", help="only rebuild the project tables from the raw pages")
    a = ap.parse_args()
    raw = Path(a.raw).resolve()
    assert ROOT.parent.parent not in raw.parents, "raw pages must stay outside the project"
    raw.mkdir(parents=True, exist_ok=True)
    us = population()
    if not a.build:
        reuse = [Path(d).resolve() for d in a.reuse]
        order = sorted(us)
        random.Random(SEED).shuffle(order)
        todo = [cn for cn in order if not all(path(raw, cn, t).exists() for t in TABS)]
        print(f"{len(us)} cases, {len(todo)} to fetch or copy", flush=True)
        done, failed = [0], {}

        def one(cn):
            err = fetch(raw, reuse, cn)
            done[0] += 1
            if err:
                failed[cn] = err
            print(f"{done[0]}/{len(todo)} {cn}{' FAILED' if err else ''}", flush=True)

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(a.workers) as ex:
            list(ex.map(one, todo))
        print(f"failed: {len(failed)} {sorted(failed)}", flush=True)
    build(raw, us)


if __name__ == "__main__":
    main()
