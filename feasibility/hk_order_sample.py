"""Hong Kong order sample: can each building's S26 / S26A order be dated? (NYC plan §17; agreed 2026-10-17 after the GPT
review; the user accepted the Buildings Department's legal notices for this on 2026-10-17.)

Sample: 30 buildings from BDS26.csv and 15 from BDS26A.csv (seed 20261017), by BLOCK_ID_EN. Each block is looked up
once in the BD Orders Search (the request its web page makes: search1.bd.gov.hk ... WS_SEARCH_ORDER_BY_BLK), one request
every 3 s. No InSAR value is read.

Licence: BD's Important Notices allow download for personal, non-commercial internal use only, and forbid
reproducing, distributing or transferring the materials. So the raw results go only to --raw (outside the project), and
the project keeps aggregate counts (hongkong/audit/order_sample_summary.json) and the sampled block IDs (from the open
CSDI data). The "issue_to" fields are dropped on reading.

Checks per building, for the order type of its list (S26 or S26A):
  - the search returns an order of that type issued 2023-05-01 or later (the open data counts orders from 1 May 2023);
  - that number equals the open data's cumulative count;
  - issue dates by year, common parts vs units, status (outstanding / complied / cancelled), and older orders still listed.
Run from Alex/:  python3 -I feasibility/hk_order_sample.py --raw <dir outside the project>
"""
import argparse
import csv
import json
import random
import socket
import time
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

_gai = socket.getaddrinfo  # IPv4 only, as in miami_case_sample.py
socket.getaddrinfo = lambda *a, **k: [x for x in _gai(*a, **k) if x[0] == socket.AF_INET] or _gai(*a, **k)

ROOT = Path(__file__).resolve().parent / "hongkong"
API = "https://search1.bd.gov.hk/api.rsc/bd_dbo_WS_SEARCH_ORDER_BY_BLK"
TOKEN = "0r1Q6z7a3C5d3g2S1k3i"  # public token in the page's own script (js/search/common.js)
PAGE = "https://www.bd.gov.hk/en/resources/online-tools/orders-search/ordersearch.html"
SEED, N = 20261017, {"S26": 30, "S26A": 15}
WINDOW_START = datetime(2023, 5, 1)
DROP = ("issue_to", "issue_to_uc", "doc_id", "file_name", "batch_id")


def lookup(block, raw):
    f = raw / f"{block}.json"
    if not f.exists():
        req = urllib.request.Request(API, data=json.dumps({"blockId": block}).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "x-cdata-authtoken": TOKEN,
                                              "Origin": "https://www.bd.gov.hk", "Referer": PAGE,
                                              "Cookie": "visited=1",
                                              "User-Agent": "Mozilla/5.0 (research label audit; low rate)"})
        for attempt in range(6):
            try:
                body = urllib.request.urlopen(req, timeout=90).read()
                v = json.loads(body).get("value", [])
                recs = json.loads(v[0]["data"]) if v and v[0].get("data") else []
                f.write_text(json.dumps([{k: r[k] for k in r if k not in DROP} for r in recs]))
                break
            except (OSError, ValueError, KeyError) as e:
                print(f"{block}: {e}; retry", flush=True)
                time.sleep(15 * (attempt + 1))
        time.sleep(3)
    return json.loads(f.read_text())


def dt(s):
    return None if not s or s == "NULL" else datetime.strptime(s.split(" ")[0], "%Y/%m/%d")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="directory OUTSIDE the project for the raw results (BD licence)")
    a = ap.parse_args()
    raw = Path(a.raw).resolve()
    assert ROOT.parent.parent not in raw.parents, "raw results must stay outside the project"
    raw.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    out = {"seed": SEED, "window_start": "2023-05-01", "lists": {}}
    for typ, n in N.items():
        with open(ROOT / "downloads" / f"{typ.lower()}_orders" / f"BD{typ}.csv", encoding="utf-8-sig") as fh:
            rows = sorted(csv.DictReader(fh), key=lambda r: r["BLOCK_ID_EN"])
        count_col = next(k for k in rows[0] if k.startswith("Cum_") and k.endswith("_EN"))
        last = max(r["LastUpdate"] for r in rows)
        sample = rng.sample(rows, n)
        res = Counter()
        years, status, older = Counter(), Counter(), Counter()
        for r in sample:
            recs = [x for x in lookup(r["BLOCK_ID_EN"], raw) if x.get("so_type") == typ]
            inwin = [x for x in recs if dt(x["ord_dt"]) and dt(x["ord_dt"]) >= WINDOW_START]
            res["buildings"] += 1
            res["with_any_order_of_type_listed"] += bool(recs)
            res["with_order_issued_in_window"] += bool(inwin)
            res["count_in_window_equals_open_data_count"] += len(inwin) == int(r[count_col] or 0)
            res["count_in_window_more_than_open_data"] += len(inwin) > int(r[count_col] or 0)
            res["with_older_order_still_listed"] += any(dt(x["ord_dt"]) and dt(x["ord_dt"]) < WINDOW_START for x in recs)
            res["orders_in_window"] += len(inwin)
            res["orders_in_window_common_parts"] += sum(str(x.get("iscommon")) == "1" for x in inwin)
            for x in inwin:
                years[dt(x["ord_dt"]).year] += 1
                status[{"1": "outstanding", "2": "complied"}.get(str(x["notice_status"]), "other")
                       + ("_cancelled" if dt(x.get("cancel_dt")) else "")] += 1
            for x in recs:
                if dt(x["ord_dt"]) and dt(x["ord_dt"]) < WINDOW_START:
                    older[dt(x["ord_dt"]).year] += 1
            print(f"{typ} {r['BLOCK_ID_EN']}: {len(recs)} listed, {len(inwin)} in window, open data {r[count_col]}", flush=True)
        out["lists"][typ] = {"open_data_buildings": len(rows), "open_data_last_update": last, "count_column": count_col,
                             "sampled_block_ids": [r["BLOCK_ID_EN"] for r in sample], **res,
                             "issue_year_of_orders_in_window": dict(sorted(years.items())),
                             "status_of_orders_in_window": dict(status),
                             "issue_year_of_older_orders_listed": dict(sorted(older.items()))}
    (ROOT / "audit").mkdir(exist_ok=True)
    (ROOT / "audit" / "order_sample_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({t: {k: v for k, v in d.items() if k != "sampled_block_ids"} for t, d in out["lists"].items()}, indent=1))


if __name__ == "__main__":
    main()
