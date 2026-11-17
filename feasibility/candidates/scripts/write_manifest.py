"""Write MANIFEST.json for files under the two candidate folders.

The manifest file itself is not included.

Run:
  ~/miniforge3/envs/opera/bin/python -I feasibility/candidates/scripts/write_manifest.py
"""

import hashlib
import json
from pathlib import Path

ROOTS = [
    Path("/mnt/data/Master-projects/Alex/feasibility/candidates"),
    Path("/mnt/data/Master-projects/Alex_private/candidates"),
]
OUT = Path("/mnt/data/Master-projects/Alex_private/candidates/MANIFEST.json")

# source URL is recorded only when this script knows it. Other files are local products.
URLS = {
    "austin_3syk-w9eu_view.json": "https://data.austintexas.gov/api/views/3syk-w9eu.json",
    "austin_kadb-t938_view.json": "https://data.austintexas.gov/api/views/kadb-t938.json",
    "austin_totals.json": "https://data.austintexas.gov/resource/3syk-w9eu.json",
    "austin_terms.html": "https://data.austintexas.gov/stories/s/ranj-cccq",
    "austin_keyword_superset.json": "https://data.austintexas.gov/resource/3syk-w9eu.json",
    "austin_keyword_superset_count.json": "https://data.austintexas.gov/resource/3syk-w9eu.json",
    "Noto_Peninsula_Damage_2_5.gpkg": "https://zenodo.org/api/records/15192949/files/Noto_Peninsula_Damage_2_5.gpkg/content",
    "zenodo_11055711.json": "https://zenodo.org/api/records/11055711",
    "zenodo_allversions.json": "https://zenodo.org/api/records?q=conceptrecid:11055711&allversions=true",
    "sentinel1_noto_asf.csv": "https://api.daac.asf.alaska.edu/services/search/param",
    "cmr_opera_disp_s1_collection.json": "https://cmr.earthdata.nasa.gov/search/collections.json?short_name=OPERA_L3_DISP-S1_V1",
    "opera_noto_count.json": "https://cmr.earthdata.nasa.gov/search/granules.json",
    "hcad_pdata.html": "https://hcad.org/hcad-online-services/pdata/",
    "hcad_downloads.html": "https://hcad.org/pdata/pdata-property-downloads.html",
    "hcad_disclaimer.html": "https://hcad.org/hcad-help/hcad-disclaimer/",
}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    rows = []
    for root in ROOTS:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.name == "MANIFEST.json":
                continue
            rows.append({
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "source_url": URLS.get(path.name),
                "access_date": "2026-10-26",
            })
    OUT.write_text(json.dumps(rows, indent=2))
    print("files", len(rows), "wrote", OUT)


if __name__ == "__main__":
    main()
