#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")/data/raw"
B=https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL
wget -q -c -P wsf_evolution https://download.geoservice.dlr.de/WSF_EVO/files/WSFevolution_v1_28_30.tif https://download.geoservice.dlr.de/WSF_EVO/files/WSFevolution_v1_30_30.tif
for t in N30E027 N30E030; do wget -q -c -P worldcover https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_${t}_Map.tif; done
wget -q -c -P ghsl_age $B/GHS_AGE_GLOBE_R2025A/V1-0/GHS_AGE_1975052020_GLOBE_R2025A_54009_100_V1_0.zip
wget -q -c -P ghsl_obat $B/GHS_OBAT_GLOBE_R2024A/GHS_OBAT_GPKG_GLOBE_R2024A/V1-0/GHS_OBAT_GPKG_EGY_E2020_R2024A_V1_0.zip
wget -q -c -P osm https://download.geofabrik.de/africa/egypt-latest.osm.pbf
echo ALLDONE
