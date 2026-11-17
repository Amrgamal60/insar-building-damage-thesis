# Checkpoint 1: the 2018 reference data (option A)

**Date:** 2026-11-09. **By:** Claude, at the user's request. Checkpoint 1 started on this date, when the 2018 files were in hand (AUSTIN_PLAN design summary point 9).

**Not done here:** no InSAR, OPERA or Sentinel file was opened. No event was built: §4 rules 4–8 were not applied, and the §6 event count is the next step. No rule of the frozen plan (`freeze/AUSTIN_PLAN_frozen.md`, SHA-256 `18627d82…`) was changed.

**Privacy:** row-level outputs, raw files and the permit copy are in `Alex_private/austin/`. The parcel layer's situs-address field was never read into any output. The roll header's operator field names a TCAD employee and is not recorded. The permit copy excludes all contractor, applicant, address, legal-description and location columns. This directory holds counts and hashes only.

## Decision under the frozen plan

| Question | Frozen rule | Result |
|---|---|---|
| Reference data | §5: fixed when checkpoint 1 starts, from what is in hand then: A, the TCAD certified 2018 roll with its parcel layer; otherwise C | **Option A.** Both 2018 files were in hand when checkpoint 1 started. Study period from **2018-08-01** (§4). |
| Foundation type in Baseline 1 | §9: added if the reference roll records it for at least 90% of eligible parcels | **Added.** 94.6% have a recorded code; 94.5% have slab and/or pier-and-beam only. Every reading is above 90%. |
| Living area in Baseline 1 | §9: reference roll, option A only | **In.** 100% of eligible parcels. |
| Sale analysis (secondary 14) | §4: needs yearly rolls with deed dates; a single 2018 roll does not qualify | **Removed.** |
| Sensitivities P0–P1 | §12: option C only | **Not applicable.** |
| Primary population | §5 | **149,316 houses** in 114,058 unique 30 m cells |

## 1. Files received (facts)

Released by TCAD for public-information request R010955-110226 on 2026-11-09. Downloaded by Claude on 2026-11-09 from the user's request page, with the user's permission, using the user's login (`Alex_private/austin/tcad/download_2018_R010955-110226.json`). Every archive member is hashed in `inventory_2018_files.json`.

| Archive (private folder) | Bytes | SHA-256 | Contents |
|---|---:|---|---|
| `2018_Certified_Appraisal_Export_Supp_0.zip` (`raw/traviscad.govqa.us_R010955-110226_roll2018/`) | 327,702,589 | `500f594c05f748aad600edbb5a56612b71ada690ecaffa017292de80d9e20c8d` | 20 fixed-width tables (15.2 GB uncompressed: PROP, PROP_ENT, IMP_INFO, IMP_DET, IMP_ATR, LAND_DET, STATE_CD, APPR_HDR, ABS_SUBD, AGENT, ARB, ARBITRATION, COUNTRY, ENTITY, LAWSUIT, MOBILE_HOME_INFO, SKETCH_INFO, TOTALS, and empty SB12 and TAX_DEFERRAL_INFO) and one totals PDF. All members are dated 2026-07-29. |
| `2018_Shapefiles.zip` (`raw/traviscad.govqa.us_R010955-110226_gis2018/`) | 178,134,562 | `64e1a626bd09ad2aad4d0800543e67c162b66b99982a37364c65c95632886c06` | Shapefiles `Parcel_poly` (used) and `_parcel_poly_bak` (not used), with empty ArcGIS `.sr.lock` files. The main files are dated 2019-04-15. |

## 2. Facts verified from the 2018 files

### Appraisal roll

- **Header (APPR_HDR, export layout 8.0.33):**
  - "Appraisal Export - 2018", appraisal year **2018**, supplement number **0000**;
  - run 07/28/2026 19:56, TP version 8.1.33.23, export version 8.0.0.33.
- **Every PROP row:** `prop_val_yr` 2018 and `sup_num` 0 (438,173 rows, 438,173 unique property IDs).
- **Totals PDF:** "Year: 2018", "As of Roll Corr: 0", generated July 28, 2026.
- **Layout:** the record lengths of PROP (9,922), IMP_INFO (114), IMP_DET (622), IMP_ATR (87), LAND_DET (199) and STATE_CD (125) equal the 8.0.33 layout's. Tables were read with the unchanged step-0 reader and that layout.
- **The A1 code exists in 2018:** 252,090 real-property A1 parcels.
- **Fields relevant to the plan:**

| Need | Table and field | Fill among the 252,090 A1 parcels |
|---|---|---|
| Property ID | PROP `prop_id` | 100% |
| Geographic ID (the permit key) | PROP `geo_id` | 100% |
| State code | PROP `imprv_state_cd` | 100% (A1 by definition) |
| Improvement type (main dwelling) | IMP_INFO `imprv_type_cd` | main dwelling found for 251,599: type 01 248,133; type 16 3,466; none 491 |
| Year built | IMP_DET `yr_built`, first floor (`1ST`) of the main dwelling | 99.7% nonblank |
| Living area | IMP_DET area, floor codes 1/2, 1ST–5TH, ADDL, main dwelling | 100% of age-eligible parcels |
| Foundation | IMP_ATR attribute "Foundation", first floor of the main dwelling | codes SLAB, PIER AND B, OTHER, BLOCKS, WOOD POST, FLOATING S |
| Lot area | 2018 parcel polygon (§9); LAND_DET size for comparison only | see §4 below |
| Deed date | PROP `deed_dt` (latest transfer only) | 99.5% (not used: secondary 14 is removed) |

- **Other improvement attributes on file:** floor, shape, grade and ceiling factors, roof style and roof covering. They are not in the plan.
- **Main-dwelling rule:** as in step 0, the largest living-floor area among types 01 and 16, ties broken by improvement ID. No parcel's main dwelling is a type 16 while it also has a type 01 improvement, so the two readings of §5 give the same population. No main dwelling has a year built after 2018.

### Parcel layer

- **`Parcel_poly`:** 352,856 polygons in **EPSG:2277**, NAD83 Texas Central State Plane, US feet. It was reprojected to EPSG:32614 for parcel points and areas.
- **Fields:** PID_10, PROP_ID, LOTS, SITUS, BLOCKS, CONDOID, PARCEL_BLO, GRID, Multi_PID, Survey_Dat, area, length. Only PROP_ID, PID_10 and the geometry were read.
- **Metadata:** "gis_data.SDE.Parcel_poly", created 2011-11-01, **last modified 2019-04-06**.
- **Identifiers:**
  - 351,989 unique PROP_IDs; 118 rows have PROP_ID 0 or null; 577 PROP_IDs span several rows.
  - 339,465 PROP_IDs are in the 2018 roll.
  - **PID_10 equals the roll's `geo_id` for 99.93%** of them (339,210). Linkage uses the roll's `geo_id`.
- **Geometry:** 4 null or empty and 36 invalid polygons in the whole layer.
  - Among A1 parcels: 11 were invalid and were repaired with `make_valid`, and 103 extra rows were dissolved by property ID, as in step 0.
  - No A1 parcel point is invalid, and none lies on the boundary line.
- **Exact link to the roll:** 251,326 of 252,090 A1 parcels (99.7%) have a polygon; 764 have none.
- **The backup layer `_parcel_poly_bak`** has the same feature count but is not identical in IDs and geometry. It is not used.

### Study area

- **Source:** the full-purpose boundary (dataset vnwj-xmz9), downloaded at checkpoint 1 (2026-11-09T16:04:12Z) with the step-0 query.
- **File:** 26 features, SHA-256 `9656bd73a7a7989ef41fd0610f716a8078d0fe843d0466b21e9acef9f93ede47`.
- **Comparison with step 0:** its bytes differ from the step-0 copy, but the geometry is identical (755.728 km² both; symmetric difference 0).

## 3. Primary population, 2018 data only (frozen §5)

| Step | Houses remaining |
|---|---:|
| A1 real-property parcels in the 2018 roll | 252,090 |
| main improvement type 01 (1 FAM DWELLING) | 248,133 |
| year built 1–2015 (first floor of the main dwelling; zero is missing) | 238,456 |
| polygon in the 2018 parcel layer | 237,995 |
| valid parcel point (centroid, EPSG:32614) | 237,995 |
| point inside the full-purpose boundary | 149,320 |
| minus the houses on 2 `geo_id`s shared by two houses each (§5 rule 3) | **149,316** |

- **Left out for information:**
  - 2,544 townhouses (main type 16, built by 2015, inside the boundary);
  - 491 A1 parcels with no main dwelling.
- **Cells:** 114,058 unique 30 m cells.

## 4. Completeness of the Baseline 1 inputs from the 2018 reference data (149,316 houses)

| Input | Complete | Note |
|---|---:|---|
| Year built (building age at *t_e*) | 100% | range 201–2015; see unresolved items |
| Living area | 100% (positive) | quartiles 1,308 / 1,708 / 2,331 sq ft |
| Lot area (2018 polygon) | 100% (positive) | quartiles 623 / 766 / 992 m²; median ratio to the 2018 land-table area 0.9997 |
| Foundation, any recorded code | 94.63% (141,294) | SLAB 118,970; PIER AND B 21,886; both 262; OTHER 166; BLOCKS 7; other 3; blank 8,022 |
| Foundation, slab and/or pier-and-beam only | 94.51% (141,118) | the frozen threshold is 90% |

Soil, terrain and income come from other sources and are built later in checkpoint 1. The income safeguard (§9, at most 10% missing) is checked then, on this population.

## 5. Permit linkage through 2018 keys (§4 parcel link check; §5 link check)

- **Permit copy:** 3syk-w9eu, downloaded at checkpoint 1.
  - Download finished at 2026-11-09T16:09:21Z. The dataset was last updated at 13:13:18Z and was unchanged during the download.
  - 2,384,452 rows. 13 columns: ID, permit type and description, permit number, class, mapped class, work class, description, `tcad_id`, application and issue dates, status, issue year.
  - SHA-256 `0e6f003f286473512cc4cb59765df9ddd4a834b70256f788269e0a3b76f28146`.
- **Permits meeting §4 rules 1–3:** 13,881.
  - Rule 1 kept 239,103 BP repair or remodel permits.
  - The locked regex matched 15,011 of them, and 19 were excluded.
- **Matching:** `tcad_id` against the 2018 `geo_id` (§5 rule 2). Exact matching and leading-zero-normalised matching agree (13,037 each).

| Permits meeting rules 1–3 | All dates (n = 13,881) | Study period A, 2018-08-01 to 2025-11-30 (n = 4,221) |
|---|---|---|
| Match any 2018 reference-roll parcel | **93.92%** (93.51–94.31) | 93.01% (92.20–93.74) |
| Matched to the primary population | **84.33%** (83.72–84.93) | 83.25% (82.09–84.35) |
| Matched to another roll parcel | 9.59% (9.11–10.09) | 9.76% (8.90–10.69) |
| Unmatched | 6.08% (5.70–6.49) | 6.99% (6.26–7.80) |

- **Intervals and dates:** intervals are 95% Wilson intervals. The study-period column uses the application date (issue date if missing) and is reported only. It is not an event count.
- **"Another roll parcel" breakdown:** 1,107 other real-property accounts and 224 A1 parcels outside the population.
- **Shared keys:** 61 population `geo_id`s also belong to a non-population roll account. Five rule 1–3 permits carry such a key and link to the house (rule 2).
- **Repairs:** unmatched permits are not repaired (§4).
- **Survivorship link check** (§5, option A categories): permits of all types per 100 house-years, through 2018 keys, by application year (`link_check_2018.json`). House-years count every house for the whole year, without demolition censoring.

| 2018 property ID in the 2026 roll? | 2016 | 2018 | 2020 | 2022 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| yes (147,670 houses) | 13.6 | 14.9 | 15.3 | 18.0 | 14.5 | 14.5 |
| no (1,646 houses) | 3.0 | 13.9 | 2.2 | 27.3 | 61.3 | 19.6 |

## 6. Comparisons with earlier diagnostics (reported only; no rule changed)

| Population | Houses | Note |
|---|---:|---|
| **2018, option A (this check)** | **149,316** | type 01, built by 2015, 2018 keys, ambiguous keys out |
| 2019, option C before exclusions (step 0) | 151,944 | A1 houses in the 2019 layer, no type information |
| 2019, option C primary (step 0) | 149,786 | minus 2,152 townhouses and 6 ambiguous keys |
| 2026 diagnostic, type 01 (step 0) | 144,458 | the 2026 roll with 2026 polygons |

- 99.53% of the 2018 houses are in the 2019 option C set. 97.81% of that set is in the 2018 population.
- 98.90% of the 2018 houses' property IDs are in the 2026 roll, and 96.23% are in the 2026 type-01 diagnostic.
- Step 0's figures from the 2026 roll were close to these 2018 figures: foundation 94.6%, deed date 99.5%.

## 7. Assumptions

- **Certification status.** The roll is TCAD's "2018_Certified_Appraisal_Export_Supp_0", with year 2018 and supplement 0 in the header and every row, and roll correction 0 in the totals.
  - TCAD produced it on 2026-07-28 from its current system. The values are taken to be the 2018 supplement-0 values.
  - The file was not compared with TCAD's 2018 certification letter or published 2018 totals.
- **Parcel-layer vintage.** TCAD released the layer as the 2018 layer, and §5 uses "its parcel layer".
  - It was last modified on 2019-04-06, so geometry edits made between 2018-01-01 and that date cannot be dated.
  - The polygon areas agree closely with the 2018 roll's land sizes (median ratio 0.9997).
- **Shared keys.** A rule 1–3 permit whose key belongs to both a population house and another roll account links to the house (rule 2). This affects 5 permits.
- **Link-check rates** use whole-year denominators without demolition censoring. They are a diagnostic, not a rate model.

## 8. Unresolved

- **One house records year built 201,** an evident data error. The plan has no rule for it, so it stays and is reported.
- **No polygon for 764 A1 parcels,** of which 461 are type 01 built by 2015, so they have no parcel point and are not eligible (§5). Account changes between the roll date and the layer's last edit are a plausible cause; it is not verified.
- **Changed accounts.** Houses whose 2018 property ID is not in the 2026 roll have permit rates that swing from year to year, high in 2022–2024. A plausible reading is redevelopment, where the house is demolished and rebuilt under the same key; it is not verified. The rate is not falling, so there is no sign of permits lost to key changes for these houses.
- **Frame clip not yet applied.** §5 also requires the study area to lie within frame 28482. That clip needs the frame footprint, which was not opened here. Step 0 found every geocoded matched permit inside the frame (CMR metadata only).
- **Not yet done at checkpoint 1:**
  - events and the §6 count;
  - label audit, demolition audit and checks (a)–(b), and the survivorship event counts;
  - permits and drought, and the remodel controls;
  - SSURGO, DEM and ACS features, and the income safeguard;
  - folds.

## 9. Scripts, outputs and hashes

All scripts run from `/mnt/data/Master-projects/Alex` with `.venv/bin/python -I`.

| Step | Script | Output (private unless stated) |
|---|---|---|
| Read the roll (unchanged step-0 code) | `step0/scripts/inspect_roll.py` with the 8.0.33 layout | `tcad/derived_2018/` |
| Main dwelling and fields (unchanged step-0 code) | `step0/scripts/static_checks.py` | `tcad/static_checks_2018/parcel_fields.parquet` (`4e1a8073…`) |
| Inventory and hashes | `checkpoint1/scripts/c1_00_inventory_2018.py` | `inventory_2018_files.json` (project) |
| Permit copy | `checkpoint1/scripts/c1_01_download_permits.py` | `checkpoint1/permits_3syk-w9eu_20261109/` |
| Boundary | `checkpoint1/scripts/c1_02_download_boundary.py` | `checkpoint1/boundary_vnwj-xmz9_20261109/` |
| Population and completeness | `checkpoint1/scripts/c1_03_population_2018.py` | `checkpoint1/reference_2018/population_2018.parquet` (`8a418a3b…`), `roll_keys_2018.parquet` (`c8c715d9…`); `reference_2018_population.json` (project) |
| Link checks | `checkpoint1/scripts/c1_04_link_check.py` | `link_check_2018.json` (project) |

`SHA256SUMS` in this directory covers every project file here.
