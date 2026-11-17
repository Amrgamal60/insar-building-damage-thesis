# Label-source readiness facts

Access date for every source below: 2026-10-26.

Keyword list and exclusion rules were written to `keyword_protocol.md` before any filtered counts were retrieved. They were not edited after the counts.

Locked regex:

`foundation|underpin(?:ning)?|slab repair|levell?ing|house level|mudjack|re-level|\bshim\b|helical|(?:push )?pier(?:s|ing)?`

Exclusion rules, in order, from that file: new-construction foundation-only (`foundation only`, `new foundation`, `pour foundation`, and only when the text also indicates new construction and has no repair, pier, underpin, level, mudjack, or shim language); pool or spa without that repair language; sign without that repair language; retaining wall, screen wall, or fence footing without that repair language; waterfront, dock, boat, fishing, or bridge pier without other foundation language. Rule 6 (unrelated trade use of "pier") excluded nothing.

## 1. Sources and access dates

| Source | URL | Accessed |
| --- | --- | --- |
| Austin permit view metadata | https://data.austintexas.gov/api/views/3syk-w9eu.json | 2026-10-26 |
| Austin story-board view | https://data.austintexas.gov/api/views/kadb-t938.json | 2026-10-26 |
| Austin row count and date range | https://data.austintexas.gov/resource/3syk-w9eu.json | 2026-10-26 |
| Austin terms of use | https://data.austintexas.gov/stories/s/ranj-cccq | 2026-10-26 |
| Houston GIS hub | https://houston-mycity.opendata.arcgis.com/api/search/v1 | 2026-10-26 |
| Houston single-family permits | https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/SF_2015_to_2021/FeatureServer/1 | 2026-10-26 |
| Houston multi-family permits | https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/MF_2015_to_2021/FeatureServer/0 | 2026-10-26 |
| Houston CKAN permit search | https://data.houstontx.gov/api/3/action/package_search?q=permit&rows=20 | 2026-10-26 |
| Houston planning reports page | https://www.houstontx.gov/planning/DevelopRegs/dev_reports.html | 2026-10-26 |
| Noto Zenodo concept | https://zenodo.org/api/records/11055711 | 2026-10-26 |
| Noto GeoPackage | https://zenodo.org/api/records/15192949/files/Noto_Peninsula_Damage_2_5.gpkg/content | 2026-10-26 |
| ESSD paper | https://essd.copernicus.org/articles/17/5259/2025/ | 2026-10-26 |
| OPERA collection | https://cmr.earthdata.nasa.gov/search/collections.json?short_name=OPERA_L3_DISP-S1_V1 | 2026-10-26 |
| OPERA granules | CMR `granules.json` and ASF search CSV, same date | 2026-10-26 |
| Sentinel-1 search | https://api.daac.asf.alaska.edu/services/search/param | 2026-10-26 |
| GSI Noto page | https://www.gsi.go.jp/BOUSAI/20240101_noto_earthquake.html | 2026-10-26 |
| G-Portal terms | https://www.gportal.jaxa.jp/gpr/index/eula?lang=en | 2026-10-26 |
| TCAD public information | https://traviscad.org/publicinformation/ | 2026-10-26 |
| HCAD public data | https://hcad.org/hcad-online-services/pdata/ | 2026-10-26 |

## 2. Austin

The current table is Issued Construction Permits, id `3syk-w9eu`, on data.austintexas.gov. `kadb-t938` is a story board named "Issued Construction Permits Story Board", with no columns. The view metadata `rowsUpdatedAt` converts to 2026-10-25T12:18:49Z. The catalog `updatedAt` for `3syk-w9eu` is the same timestamp. Category: Building and Development. The view licence field is "Public Domain U.S. Government" with terms link https://www.usa.gov/government-works. The dataset description links to the City of Austin Open Data Terms of Use. That page says datasets on the portal are in the public domain unless otherwise noted, and it disclaims warranties of completeness, accuracy, and fitness.

Row count from the SODA aggregate: 2,381,895. Issue dates in that aggregate: 1921-09-20 through 2026-10-24. Applied dates: 1921-09-20 through 2026-10-23. Publishing metadata says update frequency Daily and time range 1980-Present. The aggregate min date is earlier than that stated range.

78 fields. Types are the Socrata `dataTypeName` values:

permittype (text), permit_type_desc (text), permit_number (text), permit_class_mapped (text), permit_class (text), work_class (text), condominium (text), permit_location (text), description (text), tcad_id (text), legal_description (text), applieddate (calendar_date), issue_date (calendar_date), day_issued (text), calendar_year_issued (number), fiscal_year_issued (number), issued_in_last_30_days (text), issue_method (text), status_current (text), statusdate (calendar_date), expiresdate (calendar_date), completed_date (calendar_date), total_existing_bldg_sqft (number), remodel_repair_sqft (number), total_new_add_sqft (number), total_valuation_remodel (number), total_job_valuation (number), number_of_floors (number), housing_units (number), building_valuation (number), building_valuation_remodel (number), electrical_valuation (number), electrical_valuation_remodel (number), mechanical_valuation (number), mechanical_valuation_remodel (number), plumbing_valuation (number), plumbing_valuation_remodel (number), medgas_valuation (number), medgas_valuation_remodel (number), original_address1 (text), original_city (text), original_state (text), original_zip (number), council_district (number), jurisdiction (text), link (url), project_id (number), masterpermitnum (number), latitude (number), longitude (number), location (location), contractor_trade (text), contractor_company_name (text), contractor_full_name (text), contractor_phone (text), contractor_address1 (text), contractor_address2 (text), contractor_city (text), contractor_zip (text), applicant_full_name (text), applicant_org (text), applicant_phone (text), applicant_address1 (text), applicant_address2 (text), applicant_city (text), applicantzip (text), certificate_of_occupancy (text), total_lot_sq_ft (number), plus ten `:@computed_region_*` number fields.

The field `permit_class_mapped` is described in the view as residential if `permit_class` starts with "R", otherwise commercial. Latitude is described as a north-south Earth coordinate and longitude as an east-west Earth coordinate. The view metadata does not name an EPSG code.

Keyword search fields: `description`, `work_class`, `permit_class`, `permittype`, `permit_type_desc`. The SODA LIKE superset had 27,007 rows. 6 of those did not match the locked regex. Exclusions: new_construction_foundation_only 59, pier_not_foundation 56, pool 50, sign 31, retaining_wall 8. Matched permits: 26,797.

Issued-date counts:

| Year | Matched permits |
| --- | ---: |
| before 2010 | 7,101 |
| 2010 | 1,040 |
| 2011 | 1,177 |
| 2012 | 1,268 |
| 2013 | 1,286 |
| 2014 | 1,398 |
| 2015 | 1,151 |
| 2016 | 1,188 |
| 2017 | 990 |
| 2018 | 929 |
| 2019 | 889 |
| 2020 | 891 |
| 2021 | 1,022 |
| 2022 | 1,080 |
| 2023 | 1,192 |
| 2024 | 1,159 |
| 2025 | 1,411 |
| 2026 | 1,625 |

Issued on or after 2016-07-01: 11,734. Issued on or after 2018-07-01: 9,701. No matched permit had a missing issue date.

Unique non-blank `original_address1` values, after uppercasing and collapsing whitespace: 17,621. Of those, 4,601 have more than one matched permit. 4 matched permits have a blank address. Unique non-blank `tcad_id`: 16,805. Of those, 4,615 have more than one matched permit. 105 matched permits have a blank `tcad_id`.

`permit_class_mapped`: Residential 24,339, Commercial 2,458. `permittype`: BP 16,557, PP 6,556, EP 1,950, MP 1,423, DS 311.

Usable coordinates means both latitude and longitude are finite, inside the geographic ranges, and not the pair (0, 0). 24,334 of 26,797 matched permits meet that test. 2,459 have a non-blank street address and do not have usable coordinates. No geocoder was run.

Thirty most frequent description strings, with counts:

1. 1348 — Foundation repair on the existing single family residence.
2. 1046 — Express: Foundation repair
3. 684 — Express: Foundation Repair
4. 401 — Repair/stabilize foundation on existing structure. Changes/increases to the footprint of the structure are not permitted. Foundation must remain of the same type as the original (i.e. pier-and-beam cannot be switched to a slab or vice-versa). The stored string continues past this point; the full string is in `readiness.json`.
5. 397 — Express: foundation repair
6. 281 — foundation repair
7. 281 — Repair existing foundation.
8. 211 — existing foundation repair
9. 200 — Foundation Repair
10. 199 — Repair/stabilize foundation on existing structure. Changes/increases to the footprint of the structure are not permitted.
11. 199 — tunnel below the foundation to repair drain lines
12. 172 — Repair existing foundation on sf res.
13. 169 — Foundation repair
14. 167 — Repair existing foundation on single family res.
15. 164 — Repair the foundation on the existing single family residence.
16. 160 — Foundation repair to existing single family res.
17. 137 — Repair Foundation
18. 130 — foundation repair to existing sfr
19. 117 — Express: foundation repair.
20. 103 — Repair/stabilize foundation on existing structure. Foundation must remain of the same type as the original (i.e. pier-and-beam cannot be switched to a slab or vice-versa). The stored string continues; the full string is in `readiness.json`.
21. 100 — Foundation repair.
22. 97 — existing foundation repair.
23. 88 — tunnel below foundation to repair drain lines
24. 85 — Foundation Repair To Existing Residence
25. 81 — Express: Existing foundation repair as per scope of work attached.
26. 77 — Repair existing foundation
27. 76 — Foundation repair at existing SFR.
28. 73 — express foundation repair
29. 66 — Foundation repair to existing sfr
30. 66 — Express - Foundation Repair

Precision sample: seed 20261026, 60 of 26,797. Classes, read from each description: REPAIR_EXISTING_FOUNDATION 42, NOT_FOUNDATION 11, NEW_CONSTRUCTION 4, UNCLEAR 3. REPAIR share 42/60. 95% Clopper-Pearson interval from the binomial tail definition: 0.5679168661239764 to 0.8115485545802781. Permit ids, classes, and reasons are in `austin_a4_classes.json`. Descriptions are in the private sample file.

OPERA DISP-S1 frames whose footprints intersect the bounding box of the 24,334 matched points with coordinates (longitude -97.99673564 to -97.55066125, latitude 30.12239891 to 30.50919223). CMR hits: 523 granules. An official city-limit polygon was not used.

| Frame | Path | Direction | Granules | Earliest granule time_start | Latest granule time_end | Points inside every granule polygon | Points inside the union |
| --- | --- | --- | --- | ---: | --- | --- | ---: | ---: |
| 28482 | 107 | ASCENDING | 254 | 2016-07-10 | 2025-11-20 | 24,334 | 24,334 |
| 28483 | 107 | ASCENDING | 269 | 2016-07-10 | 2026-03-20 | 1,188 | 1,191 |

Granule polygons inside one frame are not identical. Direction and path come from one UMM record per frame. 2,463 matched permits have no usable coordinates and were not tested. No granule file was opened.

## 3. Houston

Direct requests from this machine to data.houstontx.gov returned HTTP 403, Cloudflare error 1009. A CKAN `package_search` for "permit" returned 9 packages. The only building-permit package is "City of Houston Residential Building Permits by Month and Year", id `525772a1-0b4b-4d55-9b43-4d3b589fe1b7`, resource `c9cef716-4d81-4dac-9b05-d19acddf159f`, licence Open Data Commons Attribution License, metadata modified 2026-05-01. It is a monthly summary of single-family and multi-family permits, not permit-level rows with work descriptions. The other eight packages are vehicle, parking, dumpster, alcohol, or fee-schedule records.

The City of Houston GIS open-data hub (104 datasets on this date) has no building-permit feature layer. It does have "Houston Sidewalk Permits Range 2020 Through 2023". The Planning and Development page https://www.houstontx.gov/planning/DevelopRegs/dev_reports.html says permit activity reports were neighborhood ZIP-code reports, that the department stopped supplying those links on 2025-12-01, and that current permit lookup is the Houston Permitting Center sold-permits search. That search is not a bulk download.

Permit-level layers with a work-description field are on the City of Houston ArcGIS org `NummVBqZSIJKUeVR`, owner `COH_PDMAPPING`, and are the layers in the public web map "Building Permits" (item `fb02e32d3c9c4fd5941907d3fa080dee`):

- Single family: `SF_2015_to_2021`, item `7c791aadaa6c44f095529e84b7dc8325`, layer 1. Item snippet "BP 2015 to 2021". Item description "Updated Jan 2024". Item `modified` 1706730063000, which is 2024-01-31T19:41:03Z. `licenseInfo` is empty.
- Multi family: `MF_2015_to_2021`, item `ff12e2bc84644db8aa6a6d6582d6d151`, layer 0. Item snippet "2015 - 2021 MF Building permits". Item description "Updated Jan 2024." Layer `dataLastEditDate` 1747678356101, which is 2025-05-19T18:12:36Z. `licenseInfo` is empty.

These are not the Seattle layer that shares a similar display name on a different ArcGIS org.

SF layer count: 57,166. Statistics: `Sold_Date_YR` 2015 to 2024; `Sold_Date` 2015-01-02 to 2024-12-31. Native spatial reference in the statistics response: wkid 102740, latestWkid 2278. Queried point coordinates were requested with `outSR=4326`.

SF fields from a one-record query: OBJECTID_1 (OID), Loc_name, Status, Score, Match_type, F_ORG_GROUP, F_PERMIT_TY, F_FCC_CODE, FCC__Desc, F_SOLD_DATE, ADDRESS, CITY, STATE, F_PROJ_NAME, F_DWELLINGS, F_BUILDING_, PRMT_DESC, ObjectID, MERGE_SRC, Sold_Date, Sold_Date_MO, Sold_Date_DM, Sold_Date_YR, Sold_Month, MERGE_SRC_1. There is no permit-number field and no parcel-id field. `F_PROJ_NAME` holds the work text. `FCC__Desc` holds a type string such as "New Single Family Dwelling".

MF layer count: 4,389. A statistics request for min and max `Sold_Date_SZ` timed out. The layer metadata lists USER_PRMT_DESC (alias PRMT_DESC), F_PROJ_NAME, FCC__Desc, ADDRESS, Sold_Date_SZ, Sold_Date_SZ_YR, and related fields. There is no parcel-id field in that field list.

Keyword superset counts: SF 12, MF 9. None of those 21 were removed by the locked exclusion rules. The three exclusion phrases (`foundation only`, `new foundation`, `pour foundation`) occur in two MF texts, but those texts say "future" rather than the new-construction patterns used for rule 1, so they stayed in the matched set and were classified in the sample.

Matched permits by the year field: 2015: 6, 2016: 0, 2017: 7, 2018: 3, 2019: 0, 2020: 1, 2021: 1, 2022: 1, 2023: 1, 2024: 1. Years 2010-2014 and 2025-2026: 0. Sold date on or after 2016-07-01: 15. Sold date on or after 2018-07-01: 6. Two MF rows have a null sold timestamp and year values 2022 and 2023; those two are included in both cut totals because the year is after 2018.

18 non-blank addresses. One address has three matched permits. One matched permit has a blank address. All 21 have point coordinates in the 4326 download. No geocoder was run.

The SF layer is single-family permits and the MF layer is multi-family permits. Of the 21, 12 are on the SF layer and 9 are on the MF layer. No commercial building-permit layer with work text was found. FCC values on the 21 rows are New Single Family Dwelling, Apartments, Duplex, or null.

All 17 distinct `F_PROJ_NAME` strings and their counts are in `readiness.json`. The most common is "RESIDENTIAL FOUNDATION FOR HOUSE MOVE IN" (3). There are fewer than 30 distinct strings.

Precision check: the matched set has 21 rows, so all 21 were read. Seed 20261026 was not used to draw a subset. Classes: NEW_CONSTRUCTION 21, REPAIR_EXISTING_FOUNDATION 0, NOT_FOUNDATION 0, UNCLEAR 0. REPAIR share 0/21. 95% Clopper-Pearson interval: 0.0 to 0.16109761521907956.

OPERA DISP-S1 frames intersecting the SF layer extent from the item metadata (longitude -95.69165277710096 to -94.98429597637958, latitude 29.550178090981742 to 30.10653268116034). CMR downloaded 1,645 of 1,645 granule records. The ASF metadata CSV has the same 1,645 rows. An official city-limit polygon was not used. Granule polygons inside a frame are not identical. For these 21 points, the count inside the union equals the count inside the intersection of every granule polygon in the frame.

| Frame | Path | Direction | Granules | Earliest start | Latest end | Points inside union and intersection |
| --- | --- | --- | ---: | --- | --- | ---: |
| 38238 | 143 | DESCENDING | 449 | 2016-07-12 | 2026-03-22 | 21 |
| 38239 | 143 | DESCENDING | 449 | 2016-07-12 | 2026-02-14 | 4 |
| 8882 | 34 | ASCENDING | 269 | 2016-09-27 | 2026-02-19 | 21 |
| 36269 | 136 | ASCENDING | 239 | 2016-10-04 | 2025-10-17 | 1 |
| 36268 | 136 | ASCENDING | 239 | 2016-10-04 | 2025-10-17 | 0 |

No granule file was opened.

## 4. Noto

Zenodo concept DOI 10.5281/zenodo.11055711. The concept has 4 version records. The newest file record is id 15192949, version 2.5, publication date 2025-04, created 2025-04-11. Licence id `cc-by-4.0`. The record's `doi` field is `10.5194/essd-2024-363`. The concept DOI is the one above. An earlier file version is 2.4 (record 14650106, publication date 2025-01). File downloaded: `Noto_Peninsula_Damage_2_5.gpkg`, 47,853,568 bytes. sha256 `1adf3ff883951db42728448e6f338f93c9d0343d11de11fd8274dabfc27aaf9d`. Zenodo also reports md5 `280e9c53cb45086786c20ed0b2c21ffb`.

GeoPackage layer `v2.5`. Geometry column `geom`, MultiPolygon, SRS EPSG:4326. Extent in `gpkg_contents`: longitude 136.670683417 to 137.360662401, latitude 37.000347909 to 37.529975389. Content timestamp 2025-04-11T04:49:47.741Z. Features: 140,208. Null geometries: 0. Invalid geometries under Shapely `is_valid` after reading the GeoPackage WKB: 0.

Columns in the file: fid (INTEGER), geom (MULTIPOLYGON), s_fid (TEXT), source (TEXT), damage_val (MEDIUMINT), municipality (TEXT), conf (TEXT), damage_2 (MEDIUMINT), GSI_fire (INTEGER), GSI_tsunami (INTEGER), GSI_slope_failure (INTEGER), USGS_MMI (REAL).

The Zenodo description table names `damage` and `damage_val`. The file has `damage_val` and `damage_2`, and no column named `damage`. The description defines `damage_val` as the damage class after technical validation and `municipality` as the municipality name from e-Stat (Ministry of Internal Affairs and Communications, 2024). The ESSD paper page defines class 0 as survived, 1 as destroyed, 9 as obstructed, and 99 as missing or inconsistent. The fetched paper HTML did not include the cells of Table 5, so which of `damage_val` and `damage_2` is the validated column is not taken from that table. Counts for both columns are below.

`damage_val`: 0 = 112,275; 1 = 3,461; 9 = 9,437; 99 = 15,035.
`damage_2`: 0 = 112,320; 1 = 3,361; 9 = 9,460; 99 = 15,067.

Municipality was assigned from the dataset field `municipality`. Each value is a comma-separated string beginning with the prefecture. The second token was used. No boundary file was joined.

`damage_val` counts:

| Municipality | Token | n | 0 | 1 | 9 | 99 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Suzu | 珠洲市 | 23,001 | 17,538 | 1,767 | 884 | 2,812 |
| Wajima | 輪島市 | 26,700 | 19,376 | 1,310 | 921 | 5,093 |
| Noto | 能登町 | 17,177 | 13,302 | 113 | 1,289 | 2,473 |
| Anamizu | 穴水町 | 6,989 | 3,763 | 77 | 2,508 | 641 |
| Nanao | 七尾市 | 43,898 | 40,435 | 116 | 708 | 2,639 |
| Shika | 志賀町 | 20,778 | 16,288 | 76 | 3,125 | 1,289 |
| not in the six | 中能登町 | 1,643 | 1,566 | 0 | 1 | 76 |
| null field |  | 22 | 7 | 2 | 1 | 12 |

`damage_2` for Wajima: 0 = 19,381; 1 = 1,274; 9 = 921; 99 = 5,124. For Suzu: 0 = 17,581; 1 = 1,719; 9 = 888; 99 = 2,813. The other municipalities are in `readiness.json`.

Sentinel-1, ASF search, platform Sentinel-1, bounding box equal to the inventory extent, 2023-10-01 through 2024-03-31. The search returned 548 rows, all Sentinel-1A, beam mode IW. Processing-level counts in that download are in `readiness.json`. SLC scenes whose four-corner footprint intersects the inventory extent: 47. Unique start dates:

- Relative orbit 112, ascending, 2 dates: 2024-01-06, 2024-01-18. 2 SLC scenes.
- Relative orbit 17, descending, 15 dates from 2023-10-07 to 2024-03-23, every 12 days in that list. 15 SLC scenes.
- Relative orbit 119, descending, 15 dates from 2023-10-02 to 2024-03-30. 30 SLC scenes. The date list is in `readiness.json`. It does not include 2023-12-01.

OPERA DISP-S1 over that same extent: CMR `cmr-hits` 0 for short name `OPERA_L3_DISP-S1_V1`. The collection record is `C3294057315-ASF`, version 1, time_start 2016-07-01T00:00:00.000Z, platforms Sentinel-1A, Sentinel-1B, Sentinel-1C, and Sentinel-1D. The collection polygon vertices include longitudes from -180 to 180. None of those vertices fall in latitude 20 to 50 and longitude 120 to 150. A written statement that the product is North America only was not in the collection JSON that was saved.

ALOS-2: a direct fetch of https://www.gportal.jaxa.jp/gpr/index/eula?lang=en returned a maintenance page (HTTP 503). A retrieval of that same URL on this date contained section 5: data provided by G-Portal may be used free of charge, including commercially; use is limited to peaceful purposes; the source must be indicated; commercial use requires prior notice to JAXA; agreements with JAXA take precedence. The appended table row for this sensor is "ALOS-2 (catalog only, PALSAR-2)" with provider JAXA. No ALOS-2 scene was downloaded.

GSI page https://www.gsi.go.jp/BOUSAI/20240101_noto_earthquake.html. The page says the geographic information may be reused, including reproduction, if the source is stated, under the GSI content terms of use. Layers listed on that page, with the formats stated there. Imagery files were not downloaded.

1. Orthophotos. Viewed in GSI Maps. Dates of photography are on the page.
2. Vertical aerial photographs. Viewed in GSI Maps.
3. 3D terrain view from post-earthquake aerial photos.
4. 3D printed terrain models. Not a downloadable file on the page.
5. Before/after aerial-photo comparison in GSI Maps.
6. Ports interpreted as land after uplift. GeoJSON in a ZIP, stated size 6 KB.
7. Tsunami inundation interpreted from aerial photos. GeoJSON ZIPs stated at 50.3 KB, 75.1 KB, 43.6 KB, and 35.0 KB, plus PDFs stated at 18.9 MB, 20.7 MB, 21.4 MB, and 1.3 MB.
8. Slope-failure and deposit polygons. GeoJSON ZIPs stated at 251 KB, 125 KB, 148 KB, 46 KB, and 31 KB.
9. Slope-failure maps as PDF, including A0 sheets stated up to 48.9 MB, and an index PDF stated at 236 KB.
10. Disaster-status map. PDF stated at 27.5 MB.
11. LiDAR terrain-analysis figures. The page points to a company site for detail.
12. Surface-crack map. PDF stated at 2.6 MB. Crack data are named on the page.
13. ALOS-2 crustal-deformation figures on the page.
14. Comparison with past earthquakes. PDF stated at 580 KB.
15. Field survey note for a fishing port, with images on the page.
16. ALOS-2 coastline-change figures on the page.
17. GNSS control-point displacement reports, with a PDF stated at 0.2 MB for the first report.
18. Source-fault model.
19. Emergency field survey results.
20. Digital elevation maps. PDFs stated at 2.6 MB, 2.1 MB, 2.2 MB, 2.7 MB, and 3.1 MB.
21. Fire-burned area in central Wajima. PDF stated at 165 KB and GeoJSON ZIP stated at 0.6 KB.
22. Notes on public surveys and on geodetic control results. These are procedural notices, not spatial layers.
23. 2020 census 250 m mesh for Ishikawa, displayed in GSI Maps.

## 5. What I could not verify

- TCAD residential parcel count, whether year built and building type are in the appraisal extract, and the extract's licence. The public-information page lists certified-totals reports and an export-layout file. Those files were not opened. The full roll was not downloaded. Austin permits do contain a field named `tcad_id`.
- HCAD residential parcel count, year built, building type, and the licence text. The public-data page says real-property text files and GIS files exist and that most files are very large. The disclaimer page's HTML did not include the disclaimer body. The codebook was not downloaded. The full roll was not downloaded.
- A parcel-id join from the Houston SF/MF layers to HCAD. Those layers' field lists have no parcel id.
- A bulk City of Houston commercial-permit table with work descriptions. None was found on the GIS hub or in the CKAN search. The permitting-center search was not used as a bulk source. Whether a login-only export exists was not checked. No credential file was opened.
- Which of `damage_val` and `damage_2` Table 5 of the ESSD paper defines as the validated class.
- A sentence in the OPERA collection record that says the product is limited to North America. The granule search over the Noto extent returned 0 hits.
- The live G-Portal terms page. The direct fetch was a maintenance response.
- Shares against an official city-limit polygon. The search boxes are the ones stated above.
- MF layer-wide minimum and maximum sold dates. The statistics request timed out. Per-record dates for the 9 keyword rows were saved.
- A geocoder success rate. Address-present counts are not geocoder results.
- An EPSG code for the Austin latitude and longitude fields. The view metadata does not name one.
- A licence string for the Houston ArcGIS permit items. `licenseInfo` is empty. The CKAN ODC-BY licence is for the monthly summary package.

## 6. Deviations from these instructions

- `data.houstontx.gov` was not readable with a direct HTTP client from this machine. The CKAN package list was taken from a fetch of the API URL.
- The first draft of the Austin exclusion code treated any new-construction text that contained "foundation" as foundation-only. That was wider than `keyword_protocol.md`. It was corrected before the reported counts. The reported Austin counts and the sample of 60 are from the corrected run.
- Houston has 21 matched permits, so the precision check classified all of them instead of drawing 60.
- OPERA searches used a bounding box of matched Austin coordinates and the Houston SF-layer extent, not a city-limit polygon.
- No InSAR displacement, velocity, or coherence file was opened. No model was fit. No HyP3 job was submitted.
