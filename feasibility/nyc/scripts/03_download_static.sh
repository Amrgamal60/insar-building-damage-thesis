#!/bin/bash
# Download the open (no-account) NYC layers named in NYC_REPLICATION_PLAN.md §5, §7 and §9 into raw/<layer>/.
# Static products are fixed releases; the permit extract, borough boundaries and OSM are snapshots, so their
# source metadata and download time are saved beside them. Ends by writing raw/STATIC_MANIFEST.sha256.
# Usage (from feasibility/nyc): bash scripts/03_download_static.sh raw
set -euo pipefail
R=$(realpath "$1"); PY=~/miniforge3/envs/opera/bin/python
GHSL=https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL
SODA=https://data.cityofnewyork.us
# Files already present are kept, so an interrupted run can be resumed.
get() { [ -s "$1" ] && return 0; curl -sSfL --retry 5 --retry-delay 10 -A "Mozilla/5.0" -o "$1.dl" "$2" && mv "$1.dl" "$1"; }

# Reference PLUTO: 15v1, the only (so final) release labelled 2015 in DCP's archive (14v1, 14v2, 15v1, 16v1, 16v2).
mkdir -p "$R/pluto_15v1"
get "$R/pluto_15v1/nyc_pluto_15v1.zip" https://www.nyc.gov/assets/planning/download/zip/data-maps/open-data/nyc_pluto_15v1.zip

# Study area: DCP Borough Boundaries, clipped to shoreline.
mkdir -p "$R/boroughs"
get "$R/boroughs/borough_boundaries.geojson" "$SODA/resource/gthc-hcne.geojson"
get "$R/boroughs/meta_gthc-hcne.json" "$SODA/api/views/gthc-hcne.json"

# Settled filter: WSF Evolution v1, 2-degree tiles covering lon -76..-72, lat 40..42.
mkdir -p "$R/wsf_evolution"
for t in -76_40 -74_40; do get "$R/wsf_evolution/WSFevolution_v1_$t.tif" "https://download.geoservice.dlr.de/WSF_EVO/files/WSFevolution_v1_$t.tif"; done

# Baseline features: GHS-BUILT-S 1975 and 2015, GHS-BUILT-H ANBH 2018 (R2023A, 100 m, Mollweide tile R5_C12 holds NYC).
mkdir -p "$R/ghsl"
for p in BUILT_S/GHS_BUILT_S_E1975 BUILT_S/GHS_BUILT_S_E2015 BUILT_H/GHS_BUILT_H_ANBH_E2018; do
  c=${p%%/*}; n=${p#*/}
  get "$R/ghsl/${n}_GLOBE_R2023A_54009_100_V1_0_R5_C12.zip" \
      "$GHSL/GHS_${c}_GLOBE_R2023A/${n}_GLOBE_R2023A_54009_100/V1-0/tiles/${n}_GLOBE_R2023A_54009_100_V1_0_R5_C12.zip"
done

# Ground elevation: FABDEM v1-2 tiles N40W075 and N40W074, copied byte for byte out of the 10-degree zip.
mkdir -p "$R/fabdem"
"$PY" -I - "$R/fabdem" <<'EOF'
import os, sys
from osgeo import gdal
gdal.UseExceptions()
z = "/vsizip//vsicurl/https://data.bris.ac.uk/datasets/s5hqmjcdj8yo2ibzi9b4ew3sn/N40W080-N50W070_FABDEM_V1-2.zip"
for t in ["N40W075", "N40W074"]:
    dst = f"{sys.argv[1]}/{t}_FABDEM_V1-2.tif"
    if os.path.exists(dst):
        continue
    f = gdal.VSIFOpenL(f"{z}/{t}_FABDEM_V1-2.tif", "rb")
    with open(dst + ".part", "wb") as o:
        while b := gdal.VSIFReadL(1, 1 << 22, f):
            o.write(b)
    gdal.VSIFCloseL(f)
    os.replace(dst + ".part", dst)
EOF

# Distance to coast (OSM coastline) and the LaGuardia runways for the sign check (§7), with OSM's base timestamp.
mkdir -p "$R/osm"
# The main Overpass instance refuses generic user agents; kumi.systems mirrors the same OSM data.
ovp() {  # $1 out json, $2 query
  [ -s "$1" ] && return 0
  for u in https://overpass-api.de/api/interpreter https://overpass.kumi.systems/api/interpreter; do
    curl -sSf --retry 3 --retry-delay 30 -A "Alex-NYC-replication/1.0 (academic research)" -o "$1" --data-urlencode "data=$2" "$u" && return 0
  done; return 1
}
ovp "$R/osm/coastline.json" '[out:json][timeout:300];way["natural"="coastline"](40.40,-74.35,41.00,-73.60);out geom;'
ovp "$R/osm/lga_runways.json" '[out:json][timeout:120];way["aeroway"="runway"](40.76,-73.895,40.79,-73.855);out geom;'

# Construction mask (§7): citywide permits issued 2013-2022 from both DOB systems, the same types as the audit.
mkdir -p "$R/permits"
for id in ipu4-2q9a rbx6-tga4; do get "$R/permits/meta_$id.json" "$SODA/api/views/$id.json"; done
page() {  # $1 out csv, $2 dataset, $3 select, $4 where; pages of 50,000 ordered by row id
  local o=0 n
  : > "$1"
  while :; do
    rm -f "$1.part"; get "$1.part" "$SODA/resource/$2.csv?\$select=$3&\$where=$(printf %s "$4" | jq -sRr @uri)&\$order=:id&\$limit=50000&\$offset=$o"
    n=$(($(wc -l < "$1.part") - 1)); if [ $o -eq 0 ]; then cat "$1.part" > "$1"; else tail -n +2 "$1.part" >> "$1"; fi
    [ $n -lt 50000 ] && break; o=$((o + 50000))
  done; rm "$1.part"
}
BIS_YEARS=$(for y in $(seq 2013 2022); do printf "issuance_date like '%%/%s' or " $y; done)
page "$R/permits/bis_nb_dm_a1_2013_2022.csv" ipu4-2q9a \
  "borough,block,lot,bbl,bin__,job__,job_type,work_type,permit_type,permit_sequence__,permit_status,filing_status,issuance_date,gis_latitude,gis_longitude" \
  "job_type in ('NB','DM','A1') and (${BIS_YEARS% or })"
page "$R/permits/now_excav_demo_2013_2022.csv" rbx6-tga4 \
  "job_filing_number,work_permit,borough,block,lot,bbl,bin,work_type,permit_status,issued_date,latitude,longitude" \
  "work_type in ('Full Demolition','Foundation','Earth Work','Support of Excavation') and issued_date between '2013-01-01T00:00:00' and '2022-12-31T23:59:59'"

# Exploratory analysis 15 only: Ohenhen et al. 2025 NYC VLM (CC0), checked against figshare's MD5s.
mkdir -p "$R/ohenhen2025"
get "$R/ohenhen2025/newYork_VLM.csv" https://ndownloader.figshare.com/files/50326986
get "$R/ohenhen2025/README.rtf" https://ndownloader.figshare.com/files/54378455
echo "89dc0c0608cf9c8919bda7bbfe3b9811  $R/ohenhen2025/newYork_VLM.csv
d52e6237d49e500668b1d6ac4fb36a29  $R/ohenhen2025/README.rtf" | md5sum -c

date -u +%Y-%m-%dT%H:%M:%SZ > "$R/STATIC_DOWNLOADED_AT.txt"
cd "$R" && sha256sum pluto_15v1/* boroughs/* wsf_evolution/* ghsl/* fabdem/* osm/* permits/* ohenhen2025/* STATIC_DOWNLOADED_AT.txt > STATIC_MANIFEST.sha256
echo ALLDONE
