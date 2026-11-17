"""Miami-Dade label audit, step 1: draw a seeded sample of unsafe-structure cases and fetch their public case pages
(NYC plan §17; agreed 2026-10-17 after the GPT review). Blind to InSAR: no OPERA file is opened.

Sample: cases with CASE_TYPE "Unsafe Structure" opened 2017-01-01 or later (feasibility/miami/downloads/building_violations),
10 per open year 2017-2026. Within a year the 10 are split across case-number prefix groups (F, CF, G, digits, other: the
only case-type information in the bulk data) in proportion to their counts, with at least 1 for any group holding 5 or
more cases that year. Seed 20261017.

Fetch: for each case, the county's Regulation Cases viewer (wwwx.miamidade.gov/Apps/RER/RegulationSupportWebViewer):
case details, violation codes, activity history and structures, one request every 1.5 s. The raw pages hold owner,
violator, inspector and other personal names, so they are written only to --raw (outside the project; never copied in).
The project files keep codes, standard descriptions and dates; all free text (case comments, alleged violation,
activity comments, structure descriptions) stays in --raw.

Writes feasibility/miami/audit/label_sample/: sample.json, cases.csv, violations.csv, activities.csv.
Run from Alex/:  python3 -I feasibility/miami_case_sample.py --raw <dir outside the project>
"""
import argparse
import csv
import glob
import html
import http.cookiejar
import json
import random
import re
import socket
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_gai = socket.getaddrinfo  # IPv4 only: on this network IPv6 connects hang until the timeout
socket.getaddrinfo = lambda *a, **k: [x for x in _gai(*a, **k) if x[0] == socket.AF_INET] or _gai(*a, **k)
ROOT = Path(__file__).resolve().parent / "miami"
OUT = ROOT / "audit" / "label_sample"
BASE = "https://wwwx.miamidade.gov/Apps/RER/RegulationSupportWebViewer/USCase/"
SEED, PER_YEAR, YEARS = 20261017, 10, range(2017, 2027)
KEEP = ["Case Number", "Case Type", "Open Date", "Date Closed", "Folio Number", "Permit Number", "Building Code"]
# Left out: Inspector, Violator, Owner Name, Owner Address, and the free-text Alleged Violation and Comments (they can
# hold personal names). Free text is read only from --raw; the audit file carries name-free summaries instead.


def group(case):
    for p in ("CF", "F", "G"):
        if case.startswith(p):
            return p
    return "digits" if case[:1].isdigit() else "other"


def draw():
    rows = []
    for f in sorted(glob.glob(str(ROOT / "downloads" / "building_violations" / "pages" / "*.geojson"))):
        rows += [x["properties"] for x in json.load(open(f))["features"]]
    us = [r for r in rows if r["CASE_TYPE"] == "Unsafe Structure" and r["OPEN_DATE"]]
    for r in us:
        r["year"] = datetime.fromtimestamp(r["OPEN_DATE"] / 1000, timezone.utc).year
        r["group"] = group(r["CASE_NUM"])
    rng = random.Random(SEED)
    sample, design = [], {}
    for y in YEARS:
        pool = sorted((r for r in us if r["year"] == y), key=lambda r: r["CASE_NUM"])
        cnt = Counter(r["group"] for r in pool)
        quota = {g: PER_YEAR * n / len(pool) for g, n in cnt.items()}
        alloc = {g: int(q) for g, q in quota.items()}
        for g in sorted(quota, key=lambda g: quota[g] - alloc[g], reverse=True)[:PER_YEAR - sum(alloc.values())]:
            alloc[g] += 1
        for g, n in cnt.items():  # at least 1 for a group with >= 5 cases, taken from the largest allocation
            if n >= 5 and alloc[g] == 0:
                alloc[max(alloc, key=alloc.get)] -= 1
                alloc[g] = 1
        for g in sorted(alloc):
            sample += rng.sample([r for r in pool if r["group"] == g], alloc[g])
        design[y] = {"cases": len(pool), "by_group": dict(cnt), "drawn": alloc}
    return sample, design


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def table(page):
    body = re.search(r"<tbody>(.*?)</tbody>", page, re.S)
    if not body:
        return []
    return [[text(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)] for tr in re.findall(r"<tr>(.*?)</tr>", body.group(1), re.S)]


def details(page):
    out = {}
    for k in KEEP:
        m = re.search(r"<strong>\s*" + re.escape(k) + r"\s*</strong>\s*(?:</p>)?\s*<p>(.*?)</p>", page, re.S)
        out[k] = text(m.group(1)) if m else ""
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="directory OUTSIDE the project for the raw pages (they hold names)")
    a = ap.parse_args()
    raw = Path(a.raw).resolve()
    assert ROOT.parent.parent not in raw.parents, "raw pages must stay outside the project"
    raw.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    sample, design = draw()
    (OUT / "sample.json").write_text(json.dumps({"seed": SEED, "per_year": PER_YEAR, "design": design,
                                                 "cases": [r["CASE_NUM"] for r in sample]}, indent=1) + "\n")
    cases, viols, acts = [], [], []
    for i, r in enumerate(sample):
        cn = r["CASE_NUM"]
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        opener.addheaders = [("User-Agent", "Mozilla/5.0 (research label audit; low rate)")]
        pages = {}
        for tab in ("USCaseDetails?CaseNum=" + cn, "ViolationsUS", "ActivitiesUS", "StructuresInfo"):
            f = raw / f"{cn}_{tab.split('?')[0]}.html"
            if not f.exists():
                for attempt in range(5):
                    try:
                        f.write_bytes(opener.open(BASE + tab, timeout=60).read())
                        break
                    except OSError as e:
                        print(f"{cn} {tab}: {e}; retry", flush=True)
                        time.sleep(10 * (attempt + 1))
                time.sleep(1.5)
            pages[tab.split("?")[0]] = f.read_text(encoding="utf-8", errors="replace")
        d = details(pages["USCaseDetails"])
        assert d["Case Number"] == cn, (cn, d["Case Number"])
        v = table(pages["ViolationsUS"])
        ac = table(pages["ActivitiesUS"])
        for row in v:
            viols.append({"case": cn, "code": row[1].split(" ")[0], "description": row[1], "date": row[2]})
        for row in ac:  # COUNT, CODE, DESCRIPTION, STRUCTURE ID, ISSUE, ENTRY, FOLLOW UP, PRICE, COMMENTS (comments left out)
            acts.append({"case": cn, "n": row[0], "code": row[1], "description": row[2], "issue_date": row[4],
                         "entry_date": row[5], "follow_up_date": row[6]})
        cases.append({"case": cn, "year": r["year"], "prefix_group": r["group"], "folio": r["FOLIO"],
                      **{k.lower().replace(" ", "_"): d[k] for k in KEEP if k not in ("Case Number",)},
                      "violation_codes": ";".join(row[1].split(" ")[0] for row in v), "activities": len(ac),
                      "structures_page_empty": "no structures information" in pages["StructuresInfo"]})
        print(f"{i + 1}/{len(sample)} {cn}: {cases[-1]['violation_codes']}", flush=True)
    for name, rows in (("cases", cases), ("violations", viols), ("activities", acts)):
        with open(OUT / f"{name}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    print(Counter(c for x in cases for c in x["violation_codes"].split(";")).most_common(30))


if __name__ == "__main__":
    main()
