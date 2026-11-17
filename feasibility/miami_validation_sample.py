"""Miami-Dade label validation batch (NYC plan §17; the user's instruction of 2026-10-17: an independent batch of
200-300 cases before any full download). Blind to InSAR: no OPERA file is opened.

Sample: 250 Unsafe Structure cases opened 2017-01-01 or later, leaving out the 100 cases of the first audit
(miami/audit/label_sample/sample.json). Allocation is proportional to the number of cases in each open year x
case-number prefix group (largest remainder), so the batch is close to self-weighting; the exact weights (pool size /
cases drawn per stratum) are saved. Seed 20261018 (the first audit used 20261017).

Fetch: the same four viewer pages per case as miami_case_sample.py, raw pages only to --raw (outside the project: they
hold names). Each case uses its own session; --workers sessions run side by side, but request starts are at least 1.5 s
apart across all of them (the viewer often holds a session for about 90 s after sending a page, so one session alone
spends most of its time waiting). The project keeps sample.json, cases.csv and violations.csv (codes, standard
descriptions and dates only) in miami/audit/label_validation/.
Run from Alex/:  python3 -I feasibility/miami_validation_sample.py --raw <dir outside the project> [--workers 5]
"""
import argparse
import csv
import glob
import http.cookiejar
import json
import random
import sys
import threading
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from miami_case_sample import BASE, KEEP, ROOT, details, group, table  # noqa: E402  (also applies the IPv4 patch)

OUT = ROOT / "audit" / "label_validation"
SEED, N = 20261018, 250
GAP = 1.5  # seconds between request starts, all workers together
_lock, _last = threading.Lock(), [0.0]


def pace():
    with _lock:
        wait = _last[0] + GAP - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()


def get(opener, url, timeout=90):
    """Read until the closing </html> tag: some viewer pages send the whole page and then hold the connection open for
    about two minutes, which a plain read() waits out."""
    with opener.open(url, timeout=timeout) as resp:
        data = b""
        while True:
            chunk = resp.read1(65536)
            if not chunk:
                break
            data += chunk
            if b"</html>" in data[-4096:].lower():
                break
    assert b"</html>" in data[-4096:].lower(), f"incomplete page {url}"
    return data


def draw():
    rows = []
    for f in sorted(glob.glob(str(ROOT / "downloads" / "building_violations" / "pages" / "*.geojson"))):
        rows += [x["properties"] for x in json.load(open(f))["features"]]
    us = [r for r in rows if r["CASE_TYPE"] == "Unsafe Structure" and r["OPEN_DATE"]]
    for r in us:
        r["year"] = datetime.fromtimestamp(r["OPEN_DATE"] / 1000, timezone.utc).year
        r["group"] = group(r["CASE_NUM"])
    first = set(json.loads((ROOT / "audit" / "label_sample" / "sample.json").read_text())["cases"])
    pool = sorted((r for r in us if r["year"] >= 2017 and r["CASE_NUM"] not in first), key=lambda r: r["CASE_NUM"])
    size = Counter((r["year"], r["group"]) for r in pool)
    quota = {k: N * n / len(pool) for k, n in size.items()}
    alloc = {k: int(q) for k, q in quota.items()}
    for k in sorted(quota, key=lambda k: (quota[k] - alloc[k], k), reverse=True)[:N - sum(alloc.values())]:
        alloc[k] += 1
    rng = random.Random(SEED)
    sample = []
    for k in sorted(alloc):
        sample += rng.sample([r for r in pool if (r["year"], r["group"]) == k], alloc[k])
    strata = {f"{y}|{g}": {"pool": size[(y, g)], "drawn": alloc[(y, g)]} for (y, g) in sorted(size)}
    return sample, strata, len(pool)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="directory OUTSIDE the project for the raw pages (they hold names)")
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()
    raw = Path(a.raw).resolve()
    assert ROOT.parent.parent not in raw.parents, "raw pages must stay outside the project"
    raw.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    sample, strata, pool = draw()
    (OUT / "sample.json").write_text(json.dumps({"seed": SEED, "n": N, "pool": pool, "excluded": "label_sample (100)",
                                                 "strata": strata, "cases": [r["CASE_NUM"] for r in sample]},
                                                indent=1) + "\n")

    def fetch(r):
        cn = r["CASE_NUM"]
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        opener.addheaders = [("User-Agent", "Mozilla/5.0 (research label audit; low rate)")]
        pages = {}
        for tab in ("USCaseDetails?CaseNum=" + cn, "ViolationsUS", "ActivitiesUS", "StructuresInfo"):
            f = raw / f"{cn}_{tab.split('?')[0]}.html"
            if not f.exists():
                for attempt in range(8):
                    pace()
                    try:
                        part = f.with_suffix(".part")
                        part.write_bytes(get(opener, BASE + tab))
                        part.rename(f)
                        break
                    except (OSError, AssertionError) as e:
                        print(f"{cn} {tab}: {e}; retry", flush=True)
                        time.sleep(10 * (attempt + 1))
            pages[tab.split("?")[0]] = f.read_text(encoding="utf-8", errors="replace")
        d = details(pages["USCaseDetails"])
        assert d["Case Number"] == cn, (cn, d["Case Number"])
        v = table(pages["ViolationsUS"])
        viol = [{"case": cn, "code": row[1].split(" ")[0], "description": row[1], "date": row[2]} for row in v]
        case = {"case": cn, "year": r["year"], "prefix_group": r["group"], "folio": r["FOLIO"],
                "address": (r.get("PROP_ADDR") or "").strip(),
                **{k.lower().replace(" ", "_"): d[k] for k in KEEP if k != "Case Number"},
                "violation_codes": ";".join(row[1].split(" ")[0] for row in v),
                "activities": len(table(pages["ActivitiesUS"]))}
        done.append(cn)
        print(f"{len(done)}/{len(sample)} {cn}", flush=True)
        return case, viol

    done = []
    with ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(fetch, sample))  # sample order
    cases = [c for c, _ in res]
    viols = [v for _, vs in res for v in vs]
    for name, rows in (("cases", cases), ("violations", viols)):
        with open(OUT / f"{name}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


if __name__ == "__main__":
    main()
