"""Download the OPERA DISP-S1 STATIC layers of frame 28482 (AUSTIN_PLAN.md §7 "plus its STATIC layers", §13 step 3).

Collection OPERA_L3_DISP-S1-STATIC_V1 (CMR C3959290248-ASF); one granule per frame. Files: the DEM, the layover and
shadow mask, the line-of-sight east/north/up unit vectors and the ISO metadata, each checked against the MD5 that
ASF publishes beside it. Full-frame files (the STATIC product has no subsetting). No rule of §4–§12 uses these
layers; they are kept with the displacement files for reference.

Runs on the project PC (Earthdata login in ~/.netrc). Writes OUT/static/*, OUT/static/MANIFEST.sha256 and
OUT/static.json.
Usage: ~/miniforge3/envs/opera/bin/python -I feasibility/austin/production/i05_download_static.py OPERA_DIR
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import requests

COLLECTION, FRAME = "C3959290248-ASF", 28482
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
SUFFIXES = ("_dem.tif", "_layover_shadow_mask.tif", "_line_of_sight_enu.tif", ".iso.xml")


def digest(p, algo):
    h = hashlib.new(algo)
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


out = Path(sys.argv[1]) / "static"
out.mkdir(parents=True, exist_ok=False)
r = requests.get(CMR, params={"collection_concept_id": COLLECTION, "readable_granule_name": f"*F{FRAME}*",
                              "options[readable_granule_name][pattern]": "true", "page_size": 50}, timeout=120)
r.raise_for_status()
entries = r.json()["feed"]["entry"]
assert len(entries) == 1, f"expected one STATIC granule for frame {FRAME}, found {len(entries)}"
g = entries[0]
urls = sorted({l["href"] for l in g["links"] if l["href"].startswith("https://") and "/BROWSE/" not in l["href"]
               and l["href"].endswith(SUFFIXES)})
assert len(urls) == len(SUFFIXES), urls
files = []
with requests.Session() as s:  # ~/.netrc supplies the Earthdata login on the redirect
    for url in urls:
        dst = out / url.rsplit("/", 1)[1]
        for attempt in range(4):
            try:
                with s.get(url, stream=True, timeout=600) as resp:
                    resp.raise_for_status()
                    with open(dst, "wb") as f:
                        for chunk in resp.iter_content(1 << 22):
                            f.write(chunk)
                md5 = s.get(url + ".md5", timeout=120)
                md5.raise_for_status()
                expected = md5.text.split()[0].strip().lower()
                break
            except requests.RequestException as e:
                if attempt == 3:
                    raise
                print("retry", dst.name, type(e).__name__, flush=True)
                time.sleep(30)
        ok = digest(dst, "md5") == expected
        assert ok, f"MD5 mismatch {dst.name}"
        files.append(dict(file=dst.name, bytes=dst.stat().st_size, md5_matches_asf=ok, sha256=digest(dst, "sha256")))
        print(files[-1], flush=True)
(out / "MANIFEST.sha256").write_text("".join(f"{f['sha256']}  {f['file']}\n" for f in files))
info = dict(collection=COLLECTION, granule=g["title"], cmr_updated=g.get("updated"), frame=FRAME, files=files,
            manifest_sha256=digest(out / "MANIFEST.sha256", "sha256"), finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
(out.parent / "static.json").write_text(json.dumps(info, indent=1) + "\n")
print(json.dumps(info, indent=1))
