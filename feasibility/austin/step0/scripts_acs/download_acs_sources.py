"""Download ACS 2015 5-year summary-file inputs and 2015 TIGER block groups.

Anonymous curl only. The Census Data API was already observed to redirect to a
missing-key page; this script does not send an API key. Each HTTP attempt is
appended to the attempt log passed on the command line.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument("--private-root", type=pathlib.Path, required=True)
p.add_argument("--attempt-log", type=pathlib.Path, required=True)
args = p.parse_args()

ROOT = args.private_root
LOG = args.attempt_log
LOG.parent.mkdir(parents=True, exist_ok=True)

DOWNLOADS = [
    {
        "source": "summary_file_2015_5yr",
        "url": "https://www2.census.gov/programs-surveys/acs/summary_file/2015/documentation/user_tools/ACS_5yr_Seq_Table_Number_Lookup.txt",
        "dest": ROOT / "summary_file_2015_5yr" / "ACS_5yr_Seq_Table_Number_Lookup.txt",
        "connect_timeout": 20,
        "max_time": 120,
        "attempts": 4,
    },
    {
        "source": "summary_file_2015_5yr",
        "url": "https://www2.census.gov/programs-surveys/acs/summary_file/2015/documentation/tech_docs/2015_SummaryFile_Tech_Doc.pdf",
        "dest": ROOT / "summary_file_2015_5yr" / "documentation" / "2015_SummaryFile_Tech_Doc.pdf",
        "connect_timeout": 20,
        "max_time": 180,
        "attempts": 4,
    },
    {
        "source": "summary_file_2015_5yr",
        "url": "https://www2.census.gov/programs-surveys/acs/summary_file/2015/documentation/tech_docs/ACS_2015_SF_5YR_Appendices.xls",
        "dest": ROOT / "summary_file_2015_5yr" / "documentation" / "ACS_2015_SF_5YR_Appendices.xls",
        "connect_timeout": 20,
        "max_time": 180,
        "attempts": 4,
    },
    {
        "source": "summary_file_2015_5yr",
        "url": "https://www2.census.gov/programs-surveys/acs/summary_file/2015/data/5_year_by_state/Texas_Tracts_Block_Groups_Only.zip",
        "dest": ROOT / "summary_file_2015_5yr" / "Texas_Tracts_Block_Groups_Only.zip",
        "connect_timeout": 30,
        "max_time": 900,
        "attempts": 4,
    },
    {
        "source": "tiger2015_bg",
        "url": "https://www2.census.gov/geo/tiger/TIGER2015/BG/tl_2015_48_bg.zip",
        "dest": ROOT / "tiger2015_bg" / "tl_2015_48_bg.zip",
        "connect_timeout": 30,
        "max_time": 600,
        "attempts": 4,
    },
]


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append(entry):
    rows = json.loads(LOG.read_text()) if LOG.exists() else []
    rows.append(entry)
    LOG.write_text(json.dumps(rows, indent=2) + "\n")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def curl_once(url, dest, connect_timeout, max_time):
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".partial")
    if partial.exists():
        partial.unlink()
    started = now()
    command = [
        "curl", "-L", "-sS",
        "--connect-timeout", str(connect_timeout),
        "--max-time", str(max_time),
        "--retry", "0",
        "--user-agent", "Austin-acs-availability/1.0 (anonymous research)",
        "--output", str(partial),
        "--write-out", "%{json}",
        url,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    meta = {}
    if result.stdout.strip():
        try:
            meta = json.loads(result.stdout)
        except json.JSONDecodeError:
            meta = {"write_out_raw": result.stdout[:500]}
    status = meta.get("response_code")
    size = partial.stat().st_size if partial.exists() else 0
    entry = {
        "url": url,
        "access_time_utc": started,
        "method": "GET",
        "http_status": status,
        "bytes": size,
        "num_redirects": meta.get("num_redirects"),
        "final_url": meta.get("url_effective"),
        "content_type": meta.get("content_type"),
        "curl_exit": result.returncode,
        "sha256": None,
        "private_path": None,
    }
    if result.returncode != 0:
        entry["error"] = (result.stderr or "").strip()[:500]
        if partial.exists():
            partial.unlink()
        return entry
    if status != 200 or size == 0:
        entry["error"] = f"not saved (http_status={status}, bytes={size})"
        if partial.exists():
            partial.unlink()
        return entry
    if dest.exists():
        dest.unlink()
    partial.rename(dest)
    entry["bytes"] = dest.stat().st_size
    entry["sha256"] = sha256(dest)
    entry["private_path"] = str(dest)
    return entry


def already_saved(spec):
    dest = spec["dest"]
    if not dest.exists() or dest.stat().st_size == 0:
        return False
    if not LOG.exists():
        return False
    digest = sha256(dest)
    for row in json.loads(LOG.read_text()):
        if row.get("url") == spec["url"] and row.get("sha256") == digest and row.get("private_path") == str(dest):
            print(json.dumps({"url": spec["url"], "skipped": True, "bytes": dest.stat().st_size}), flush=True)
            return True
    return False


def download(spec):
    if already_saved(spec):
        return {"sha256": "present", "url": spec["url"]}
    delays = [0, 15, 30, 60]
    last = None
    for i in range(spec["attempts"]):
        if i:
            time.sleep(delays[i])
        last = curl_once(spec["url"], spec["dest"], spec["connect_timeout"], spec["max_time"])
        last["source"] = spec["source"]
        last["attempt"] = i + 1
        append(last)
        summary = {k: last.get(k) for k in ("url", "http_status", "bytes", "curl_exit", "attempt", "error")}
        print(json.dumps(summary), flush=True)
        if last.get("sha256"):
            return last
    return last


def main():
    failed = []
    for spec in DOWNLOADS:
        entry = download(spec)
        if not entry or not entry.get("sha256"):
            failed.append(spec["url"])
    if failed:
        raise SystemExit("download failed: " + " | ".join(failed))


if __name__ == "__main__":
    main()
