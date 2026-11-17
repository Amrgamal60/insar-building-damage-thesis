#!/bin/bash
# Download the PLUTO releases labelled 2016-2022 from NYC DCP's archive into raw/pluto_archive/ (NYC_REPLICATION_PLAN.md §5,
# §13 step 2). These are the candidate "event PLUTO" releases. Release names were found by probing DCP's archive on
# 2026-10-08: 16v1 to 18v1 are plain zips, 18v1.1 onwards are "_csv" zips; no other name (e.g. 18v2 plain, 22v3) exists.
# Ends by writing raw/pluto_archive/MANIFEST.sha256. Usage (from feasibility/nyc): bash scripts/05_download_pluto.sh raw
set -euo pipefail
R=$(realpath "$1")/pluto_archive
B=https://www.nyc.gov/assets/planning/download/zip/data-maps/open-data
mkdir -p "$R"
get() { [ -s "$1" ] && return 0; curl -sSfL --retry 5 --retry-delay 10 -A "Mozilla/5.0" -o "$1.dl" "$2" && mv "$1.dl" "$1"; }
for v in 16v1 16v2 17v1 17v1_1 18v1; do get "$R/nyc_pluto_$v.zip" "$B/nyc_pluto_$v.zip"; done
for v in 18v1_1 18v2 18v2_1 19v1 19v2 20v1 20v2 20v3 20v4 20v5 20v6 20v7 20v8 21v1 21v2 21v3 21v4 22v1 22v2; do
  get "$R/nyc_pluto_${v}_csv.zip" "$B/nyc_pluto_${v}_csv.zip"
done
date -u +%Y-%m-%dT%H:%M:%SZ > "$R/DOWNLOADED_AT.txt"
cd "$R" && sha256sum *.zip DOWNLOADED_AT.txt > MANIFEST.sha256
echo ALLDONE
