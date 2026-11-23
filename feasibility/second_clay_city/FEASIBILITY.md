# Second clay city: feasibility of a confirmatory test of the Ohenhen hazard layer (2026-11-18)

Question: can the Austin hazard-layer lead (Ohenhen 2025 beta layer, class 2-3; Austin adjusted IRR 1.74 [1.11, 2.77],
a secondary, not a finding) be tested in a second expansive-clay city with a frozen plan, 2022-2025 outcomes and Austin's design?
All checks below are outcome-blind: no permit was linked to any hazard value.

## Ohenhen layers (figshare 27606942)
All three cities have risk, beta and VLM files. Raw copies: Alex_private/ohenhen2025_tx_20261118 (SHA256SUMS there).
Hazard class 2-3 share of mapped pixels: San Antonio 5.50% (1,598 px), Austin 2.39%, Fort Worth 2.20%, Dallas 1.04%.

## Dallas: all data available and free
- Outcome: Dallas OpenData "Building Permits" (e7gq-4sah, 2018-01-01 to 2025-12-31, updated 2026-11-18) has a distinct
  permit type "Residential Foundation Repair" (from 2021): 2022 428, 2023 583, 2024 955, 2025 1,165 (3,131).
  Address + zip only (no parcel ID): match to DCAD addresses. Caveat: total permit volume about doubles from mid-2024
  (system change); foundation share 1.5% -> 1.9%. A citywide time trend does not bias a hazard IRR unless it differs by place.
- Baseline: DCAD 2022 certified roll (07/25/2022; status as of 2022-01-01, i.e. end of 2021, matching a cohort at risk
  at the end of 2021): YR_BUILT, EFF_YR_BUILT, TOT_LIVING_AREA_SF, NUM_STORIES_DESC, FOUNDATION_TYP_DESC, BLDG_CLASS_DESC,
  DESIRABILITY_RATING. Dallas (property city) residential detail: 281,885 accounts; foundation slab 130k, pier and beam 110k.
  Raw: Alex_private/dcad_20261118 (owner fields stay there).
- Parcels: DCAD PARCEL2022 (682,875 polygons, EPSG:2276); 100% of Dallas residential accounts match by GIS_PARCEL_ID.
- Hazard coverage: 281,883 houses located; 154,858 inside the mapped beta extent; flagged (class 2-3) 1,386 (0.9%).
  Austin had 3,709 flagged houses and 127 flagged events; the Austin CI implies SE(log IRR) about 0.23. Scaling to
  Dallas (about 1,400 flagged houses, roughly 70 flagged events if rates are Austin-like) gives SE about 0.3 and power
  about 45% for IRR 1.74. Rough; a planted-signal check would replace it before any freeze.

## Fort Worth: outcome available, appraisal data not reachable from here
- Outcome: ArcGIS feature service CFW_Open_Data_Development_Permits_View (2001 to today). "Residential Building Permit"
  with work description containing "FOUNDATION REPAIR": 2022 260, 2023 144, 2024 250, 2025 290 (containing
  "FOUNDATION": 529, 360, 526, 540). File date, not issue date; status fields present.
- Baseline: TAD (tad.org) returns 403 to automated access; needs a manual browser download. Not checked.
- Coverage: 2.2% of pixels flagged; fewer events per house than Dallas. Alone, power would be similar to or lower than Dallas.

## San Antonio: strongest coverage, data blocked from this network
- Outcome: a permit is required for residential foundation repair (sa.gov DSD: "Foundation Repairs", over the counter,
  IB 172). The open data portal (data.sanantonio.gov, permits from 2020) returns Cloudflare error 1009 (country banned)
  from the PC and the server, and 403 to the web fetcher. Needs a download from a US connection (VPN) by the user.
- Baseline: BCAD appraisal export by written request (PIA / FTP), as with TCAD.
- Coverage: 5.5% of pixels flagged, about 2.3 times Austin's share; likely several thousand flagged houses: the only
  city with clearly adequate power on its own.

## Reading
Dallas alone is likely underpowered (about 45%). Dallas + Fort Worth pooled is still modest. San Antonio is the only
well-powered single city, but it needs two user actions (VPN download of permits; BCAD request).

## Update 2026-11-19: San Antonio permits obtained (Grok 4.7 worker, OpenVPN to a US exit in a network namespace)
- Files: Alex_private/sanantonio_permits_20261118/ (SHA256SUMS verified; MANIFEST.md). Two issued-permit files:
  permits_issued_ending_12312024.csv (issued 2020-07-20 to 2024-12-31) and permits_issued.csv (2025-01-01 to 2026-11-13);
  data dictionary datadictionary-permits.xlsx; applications file.
- Outcome: PERMIT TYPE "Foundation Repair Permit". Unique permits by issue year: 2021 3,230; 2022 3,177; 2023 3,153;
  2024 2,927; 2025 2,976 (2022-2025: 12,233, about 4 times Dallas). Rows repeat per permit (deduplicate on PERMIT #).
- Location: X/Y on 99% of permits: State Plane TX South Central (ft) in the pre-2025 file, lon/lat in the 2025+ file.
  No BCAD property ID; houses are matched by point-in-parcel or address.
- Look-back for the at-risk rule: only from 2020-07-20 (older permits are in the legacy web app only). Dallas: from 2018.
- Still needed: house features as of 2022-01-01 (BCAD request, user; Bexar County GIS parcels being checked by Grok).

## Update 2026-11-19: Dallas reference population built (outcome-blind; feasibility/hazard_tx/scripts/d0_population.py -> step0/dallas_population.json)
- DCAD 2022 roll: A11 + RES + city jurisdiction DALLAS 210,914 -> built 2019 or earlier 207,647 -> 117 ambiguous parcel IDs
  out -> 27 points outside the TIGER 2021 city boundary -> eligible 207,503 houses.
- Ohenhen hazard layer: 101,173 mapped (48.8%); flagged (class 2-3) 1,200 (1.19% of mapped) in 162 map cells; no class 3.
  Risk layer: 98,575 mapped, flagged (3-4) 2,093.
- Foundation recorded for 99.99% (pier and beam 100,311; slab 89,513; post 16,539) -> foundation in Baseline 1.
- Mapped share is lower for houses built 1900-1959 (34-45%) than 1980+ (68-72%), as in Austin.
- Reading: Dallas alone has about a third of Austin's flagged houses; a Dallas-only test would be underpowered.
- DEM: 30 USGS 1 m tiles (TX_Pecos_Dallas_2018_D19, EPSG:26914) on the server, all verified readable. SSURGO: NRCS
  servers returned 502/504; Grok retrying. Bexar County's own parcel service is current-year only (no 2022) and very
  slow; Grok is fetching TxGIO StratMap 2022 Bexar parcels (year built) instead.
