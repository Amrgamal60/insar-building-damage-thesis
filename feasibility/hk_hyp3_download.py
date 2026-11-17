"""Download finished Hong Kong HyP3 products (job name from hk_hyp3_submit.py) into hongkong/hyp3/products/.

HyP3 keeps products for 14 days, so run this until every job is fetched. Each zip is checked against the size HyP3
reports and its CRCs; its SHA-256 goes into hongkong/hyp3/products/MANIFEST.sha256. Existing good files are skipped.
Run from Alex/:  .venv-hyp3/bin/python -I feasibility/hk_hyp3_download.py [--wait]
--wait polls every 10 minutes until no job is pending or running, downloading as jobs finish.
"""
import argparse
import hashlib
import sys
import time
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

import hyp3_sdk

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I leaves the script's folder off sys.path
from hk_hyp3_submit import JOB_NAME, OUT  # noqa: E402

PROD = OUT / "products"


def fetch(url, dest, size, tries=20):
    part = dest.with_name(dest.name + ".part")
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url), timeout=300) as r, part.open("wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            if part.stat().st_size != size:
                raise OSError(f"size {part.stat().st_size} != {size}")
            with zipfile.ZipFile(part) as z:
                if z.testzip() is not None:
                    raise OSError("bad CRC")
            part.replace(dest)
            return True
        except Exception as e:  # network drops are common here; retry with backoff
            print(f"  retry {k + 1} {dest.name[:60]}: {repr(e)[:100]}", flush=True)
            time.sleep(min(300, 15 * 2 ** k))
    return False


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        while b := f.read(1 << 20):
            h.update(b)
    return h.hexdigest()


def once(hyp3):
    jobs = hyp3.find_jobs(name=JOB_NAME)
    status = Counter(j.status_code for j in jobs)
    got = 0
    man = PROD / "MANIFEST.sha256"
    listed = {line.split()[1] for line in man.read_text().splitlines()} if man.exists() else set()
    for j in jobs:
        if j.status_code != "SUCCEEDED":
            continue
        for f in j.files:
            dest = PROD / f["filename"]
            if not (dest.exists() and dest.stat().st_size == f["size"]):
                if not fetch(f["url"], dest, f["size"]):
                    continue
                got += 1
            if dest.name not in listed:
                with man.open("a") as m:
                    m.write(f"{sha256(dest)}  {dest.name}\n")
                listed.add(dest.name)
    have = len(list(PROD.glob("*.zip")))
    print(time.strftime("%Y-%m-%d %H:%M:%S"), dict(status), f"downloaded now {got}, zips on disk {have}", flush=True)
    return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait", action="store_true")
    a = ap.parse_args()
    PROD.mkdir(parents=True, exist_ok=True)
    hyp3 = None
    while True:
        try:
            hyp3 = hyp3 or hyp3_sdk.HyP3(prompt=False)
            status = once(hyp3)
        except Exception as e:
            print("error, will retry:", repr(e)[:160], flush=True)
            hyp3, status = None, {"PENDING": 1}
        if not a.wait or not (status.get("PENDING", 0) + status.get("RUNNING", 0)):
            break
        time.sleep(600)
    if status.get("FAILED"):
        print(f"{status['FAILED']} jobs FAILED; resubmit them or log them as missing pairs", flush=True)


if __name__ == "__main__":
    main()
