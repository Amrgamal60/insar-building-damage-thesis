"""Download the brief's Hong Kong and Miami-Dade datasets (NYC plan §17 step 2). Standard library only.

Each source goes into its own folder, <city>/downloads/<key>/. Every attempt is appended to
<city>/audit/download_log.csv with URL, HTTP headers, size, SHA-256 and MD5 checks. A source whose
folder holds a COMPLETE.json is skipped, so the script can be rerun after a network failure.
ArcGIS layers are paged by object ID and resume from the last saved page.

OPERA DISP-S1 (Miami) and Sentinel-1 via HyP3 (Hong Kong) need an Earthdata login and are not here.

Run from Alex/:  python3 -I feasibility/download_hk_miami.py [--only KEY ...] [--list]
"""
import argparse
import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (academic feasibility study; research data download)"
CKAN = "https://data.gov.hk/en-data/api/3/action/package_show?id="
MDC = "https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/"
NTU = "https://researchdata.ntu.edu.sg/api/access/datafile/"
# Owner, mailing and violator-name fields name private people and are not needed for the study.
PRIVATE = {"TRUE_MAILING_ADDR1", "TRUE_MAILING_ADDR2", "TRUE_MAILING_ADDR3", "TRUE_MAILING_CITY",
           "TRUE_MAILING_STATE", "TRUE_MAILING_ZIP_CODE", "TRUE_MAILING_COUNTRY", "TRUE_OWNER1",
           "TRUE_OWNER2", "TRUE_OWNER3", "OWNER", "OWNER_ADDRESS", "OWNER_CITY", "VIOL_NAME"}

SOURCES = [
    # Hong Kong: outcomes, buildings and public InSAR named in the brief
    dict(city="hongkong", key="s26_orders", kind="ckan", id="hk-bd-opendata-s26-order-1",
         what="Buildings with Section 26 dangerous-building Repair Orders issued after 1 May 2023 (cumulative counts, monthly)"),
    dict(city="hongkong", key="s26a_orders", kind="ckan", id="hk-bd-opendata-s26a-order-1",
         what="Buildings with Section 26A building-defect Investigation Orders issued after 1 May 2023"),
    dict(city="hongkong", key="s26_cws", kind="ckan", id="hk-bd-opendata-s26-order-2",
         what="Section 26 orders complied with, withdrawn or superseded after 1 May 2024 (companion dataset)"),
    dict(city="hongkong", key="s26a_cws", kind="ckan", id="hk-bd-opendata-s26a-order-2",
         what="Section 26A orders complied with, withdrawn or superseded (companion dataset)"),
    dict(city="hongkong", key="building_info", kind="ckan", id="hk-bd-opendata-building-information",
         what="Building information and age records: block ID, address, type, use, occupation-permit date and number, lat/lon"),
    dict(city="hongkong", key="monthly_digests", kind="files",
         files=[("Md22.csv", "https://static.data.gov.hk/bd/opendata/monthlydigests/Md22.csv", None),
                ("Md24.csv", "https://static.data.gov.hk/bd/opendata/monthlydigests/Md24.csv", None)],
         what="BD Monthly Digest tables 2.2 (orders issued) and 2.4 (orders complied with), monthly counts used by the order datasets"),
    dict(city="hongkong", key="ntu_insar", kind="files",
         files=[("HongKong_TA011.zip", NTU + "87438", "e7cd472f3c3bcae661b3cf707ecd696f"),
                ("README.txt", NTU + "97893", None)],
         what="Tay et al. 2022 48-coastal-city InSAR (doi 10.21979/N9/GPVX0F), Hong Kong track 11 velocity; CC BY-NC 4.0"),
    dict(city="hongkong", key="s1_listing", kind="files",
         files=[("asf_s1_iw_slc_kowloon.csv", "https://api.daac.asf.alaska.edu/services/search/param?platform="
                 "SENTINEL-1&processingLevel=SLC&beamMode=IW&intersectsWith=POINT(114.17%2022.32)&output=csv", None)],
         what="ASF listing of Sentinel-1 IW SLC scenes over Kowloon (dates, tracks), for planning the HyP3 time series"),
    # Miami-Dade: outcomes, property layers and public InSAR named in the brief
    dict(city="miami", key="building_violations", kind="arcgis", service="BuildingViolation_gdb",
         what="County building-violation cases incl. Unsafe Structure: case, type, folio, address, open/closed dates, point (violator name left out)"),
    dict(city="miami", key="opera_cmr_listing", kind="files",
         files=[("granules_F12638_bbox.json", "https://cmr.earthdata.nasa.gov/search/granules.json?short_name="
                 "OPERA_L3_DISP-S1_V1&bounding_box=-80.45,25.55,-80.12,25.98&page_size=2000", None)],
         what="NASA CMR listing of OPERA DISP-S1 granules over Miami (frame 12638): dates and footprints; the data need an Earthdata login"),
    dict(city="miami", key="zenodo_barrier_insar", kind="zenodo", record="12699617",
         what="Aziz Zanjani et al. 2024 barrier-island Sentinel-1 time series (Sunny Isles, Surfside, Miami Beach), 2016-2023 and 2019-2023; CC BY 4.0"),
    dict(city="miami", key="ntu_insar", kind="files",
         files=[("Miami_TA048.zip", NTU + "87469", "9d7cb263a5d1bf413301ac16fb5decf8"),
                ("README.txt", NTU + "97893", None)],
         what="Tay et al. 2022 48-coastal-city InSAR, Miami track 48 velocity; CC BY-NC 4.0"),
    dict(city="miami", key="parcels", kind="arcgis", service="PaParcelView_gdb", geometry=False,
         what="Property Appraiser parcels: folio, site address/city, land use, year built, floors, units, areas, X/Y (owner and mailing fields left out)"),
    dict(city="miami", key="footprints_folio", kind="arcgis", service="BuildingFootprintUBIDFolio_gdb",
         what="Building footprints with folio, year built, floors, height, municipality (owner fields left out)"),
    dict(city="miami", key="municipalities", kind="arcgis", service="Municipalitypoly_gdb",
         what="Municipal boundaries (cases outside unincorporated Miami-Dade are handled by city building departments)"),
]


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def say(*a):
    print(now(), *a, flush=True)


def log(city, row):
    path = ROOT / city / "audit" / "download_log.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = ["utc", "key", "file", "url", "status", "bytes", "sha256", "md5_expected", "md5_ok",
            "last_modified", "etag", "note"]
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, cols)
        if new:
            w.writeheader()
        w.writerow({c: row.get(c, "") for c in cols})


def fetch(url, dest, tries=30, timeout=180):  # some Azure-hosted servers drop this network for minutes at a time
    """GET url into dest atomically; returns (status, headers). Retries on network errors and 5xx."""
    part = dest.with_name(dest.name + ".part")
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r, part.open("wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
                part.replace(dest)
                return r.status, dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code < 500 and e.code != 429:
                raise
            err = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            err = repr(e)
        wait = min(300, 15 * 2 ** k)
        say(f"  retry {k + 1}/{tries} in {wait}s: {err[:160]}")
        time.sleep(wait)
    raise RuntimeError(f"gave up after {tries} tries: {url}")


def fetch_json(url, dest=None):
    tmp = dest or (ROOT / ".tmp_download.json")
    fetch(url, tmp)
    data = json.loads(tmp.read_text(encoding="utf-8"))
    if dest is None:
        tmp.unlink()
    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"service error {data['error']} for {url}")
    return data


def digest(path, algo):
    h = hashlib.new(algo)
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def check_file(path):
    """Reject HTML error pages and broken archives; returns a note."""
    head = path.read_bytes()[:512].lstrip()
    if path.stat().st_size == 0:
        raise RuntimeError(f"{path.name}: empty")
    if head[:1] == b"<" and path.suffix.lower() in {".csv", ".json", ".txt"}:
        raise RuntimeError(f"{path.name}: looks like HTML/XML, not data")
    if path.suffix.lower() in {".zip", ".xlsx"}:
        with zipfile.ZipFile(path) as z:
            bad = z.testzip()
            if bad:
                raise RuntimeError(f"{path.name}: bad CRC in {bad}")
            return f"zip ok, {len(z.namelist())} members"
    return "ok"


def get_file(src, out, name, url, md5=None):
    dest = out / name
    status, hdr = fetch(url, dest)
    with dest.open("rb") as f:
        if f.read(4) == b"PK\x03\x04" and dest.suffix.lower() not in {".zip", ".xlsx"}:  # e.g. CSDI "csv" is a zip
            dest = dest.replace(dest.with_name(dest.name + ".zip"))
            name = dest.name
    note = check_file(dest)
    got_md5 = digest(dest, "md5")
    ok = "" if md5 is None else str(got_md5 == md5)
    log(src["city"], dict(utc=now(), key=src["key"], file=f"{out.name}/{name}", url=url, status=status,
                          bytes=dest.stat().st_size, sha256=digest(dest, "sha256"), md5_expected=md5 or "",
                          md5_ok=ok, last_modified=hdr.get("Last-Modified", ""), etag=hdr.get("ETag", ""), note=note))
    if md5 is not None and got_md5 != md5:
        raise RuntimeError(f"{name}: MD5 mismatch")
    say(f"  {name}: {dest.stat().st_size:,} bytes, {note}")
    return {"file": name, "url": url, "bytes": dest.stat().st_size}


def run_files(src, out):
    return [get_file(src, out, n, u, m) for n, u, m in src["files"]]


def run_ckan(src, out):
    pkg = fetch_json(CKAN + src["id"], out / "package.json")["result"]
    got = []
    for r in pkg["resources"]:
        url = r["url"]
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        stem = q.get("typename", [None])[0] or src["key"]
        got.append(get_file(src, out, f"{stem}.{r.get('format', 'dat').lower()}", url))
    return got


def run_zenodo(src, out):
    rec = fetch_json(f"https://zenodo.org/api/records/{src['record']}", out / "record.json")
    return [get_file(src, out, f["key"], f["links"]["self"], f["checksum"].split(":", 1)[1])
            for f in rec["files"]]


def run_arcgis(src, out):
    base = MDC + src["service"] + "/FeatureServer/0"
    info = fetch_json(base + "?f=json", out / "layer_info.json")
    oid = info.get("objectIdField") or "OBJECTID"
    fields = [f["name"] for f in info["fields"] if f["name"] not in PRIVATE]
    geometry = src.get("geometry", True)
    expected = fetch_json(base + "/query?where=1%3D1&returnCountOnly=true&f=json")["count"]
    pages = out / "pages"
    pages.mkdir(exist_ok=True)
    done = sorted(pages.glob("p[0-9]*.geojson"))
    last = int(done[-1].stem.split("_")[1]) if done else -1
    n, rows = len(done), sum(int(p.stem.split("_")[2]) for p in done)
    say(f"  {src['service']}: {expected:,} features expected; resuming after {oid} {last} ({n} pages)")
    while True:
        params = {"where": f"{oid}>{last}", "orderByFields": f"{oid} ASC", "outFields": ",".join(fields),
                  "returnGeometry": str(geometry).lower(), "outSR": "4326", "resultRecordCount": "2000",
                  "f": "geojson"}
        if geometry:
            params["geometryPrecision"] = "7"
        url = base + "/query?" + urllib.parse.urlencode(params)
        tmp = pages / "next.part.geojson"
        fetch(url, tmp)
        feats = json.loads(tmp.read_text(encoding="utf-8")).get("features")
        if feats is None:
            raise RuntimeError(f"no features key in page after {oid} {last}")
        if not feats:
            tmp.unlink()
            break
        ids = [f["properties"][oid] for f in feats]
        assert ids == sorted(ids) and ids[0] > last, "page not ordered by object ID"
        tmp.replace(pages / f"p{n:05d}_{ids[-1]}_{len(feats)}.geojson")  # page, last object ID, count
        last, n, rows = ids[-1], n + 1, rows + len(feats)
        if n % 25 == 0:
            say(f"  {n} pages, {rows:,} features")
    log(src["city"], dict(utc=now(), key=src["key"], file=f"{out.name}/pages", url=base, status=200, bytes=sum(
        p.stat().st_size for p in pages.glob("*.geojson")), note=f"{n} pages, {rows:,} features; {expected:,} expected"
        + ("" if rows == expected else " (count changed during download or differs)") + f"; fields left out: "
        + ",".join(sorted(PRIVATE & {f['name'] for f in info['fields']}))))
    say(f"  {rows:,} features in {n} pages ({expected:,} expected)")
    return [{"pages": n, "features": rows, "expected": expected, "fields": fields, "geometry": geometry}]


RUN = {"files": run_files, "ckan": run_ckan, "zenodo": run_zenodo, "arcgis": run_arcgis}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="city/key or key")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    failed = []
    for city in sorted({s["city"] for s in SOURCES}):
        meta = ROOT / city / "metadata" / "sources.json"
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text(json.dumps([{k: v for k, v in s.items()} for s in SOURCES if s["city"] == city], indent=2))
    for src in SOURCES:
        tag = f"{src['city']}/{src['key']}"
        if a.list:
            print(tag, "-", src["what"])
            continue
        if a.only and tag not in a.only and src["key"] not in a.only:
            continue
        out = ROOT / src["city"] / "downloads" / src["key"]
        if (out / "COMPLETE.json").exists():
            say(f"{tag}: already complete, skipped")
            continue
        out.mkdir(parents=True, exist_ok=True)
        say(f"{tag}: {src['what']}")
        try:
            got = RUN[src["kind"]](src, out)
        except Exception as e:  # keep going; the source stays incomplete and is retried next run
            say(f"{tag}: FAILED {e!r}")
            log(src["city"], dict(utc=now(), key=src["key"], status="failed", note=repr(e)[:500]))
            failed.append(tag)
            continue
        (out / "COMPLETE.json").write_text(json.dumps({"completed_utc": now(), "source": src, "result": got},
                                                      indent=2) + "\n")
    say("done" + (f"; FAILED: {', '.join(failed)}" if failed else "; all sources complete"))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
