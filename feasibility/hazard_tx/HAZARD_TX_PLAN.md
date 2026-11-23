# Confirmatory external test of a published InSAR differential-settlement hazard layer against recorded foundation repairs in San Antonio and Dallas (2022–2025)

**Status: FROZEN 2026-11-22 (draft 2, approved by the user: "Freeze and run (Recommended)"). Decisions D1–D7 made. After freezing, changes go to §14 (deviations) only.**
- **Outcomes:** no house has been linked to an outcome under this plan. Step 0 so far read the map layers, the 2022 appraisal roll, parcels, terrain and income only (§3).
- **Decisions for the user** are marked **D1–D7** (§16). All are now made.
- **Planted check (Dallas) done 2026-11-19** (§9.1). r3 was acceptable and was chosen then (user, D2; revised on 2026-11-22, see below).
- **Pooled planted check done 2026-11-22** (§9.2): no inference acceptable in all null cells (15 km field), and nonlinear soil gives 23% false demonstrations. The user chose a **flexible Baseline 1, checked first** (§9.3).
- **Flexible planted check done 2026-11-22** (§9.3.1): it fixes both failures. Under the §9 rule the inference becomes **r4** (wild, 12 km), because r3 misses one null cell narrowly.
- **User decisions:**
  - 2026-11-19: D2 r3, δ 1.5.
  - 2026-11-22: **flexible Baseline 1 + r4** (revising D2's r3); **D1 pooled test**; **D3–D6 as drafted**.
  - D7 (2026-11-19, revised the same day): **no BCAD request.** San Antonio enters with house data from the **current** Bexar County parcel layer, and its limits are stated (§5, §11). San Antonio's step 0 and the pooled planted check are done.
- **Before freezing:** the event-construction and real-run scripts were written and checked on synthetic outcomes (§15, 2026-11-22); the user approved the freeze on 2026-11-22.
- **Freezing:** freezing creates `freeze/HAZARD_TX_PLAN_frozen.md` (never edited) and `freeze/HAZARD_TX_PLAN_frozen.sha256` (its SHA-256, read by the gate in `run_ht.py`), and records the hash in §15. No script is edited at freezing. After freezing, changes go to §14 (deviations) only.

## Design summary

1. **The lead being tested.** In the frozen Ohenhen–Austin study (`feasibility/ohenhen_austin/`, plan 60aac893…), secondary 2 used the published **hazard** layer (angular distortion class 2–3). Beyond Baseline 1 + x/y it gave an adjusted IRR of **1.74 [1.11, 2.77]** (nominal, not multiplicity-corrected) and a held-out gain of **T = +20.8**.
   - The study's co-primary U, which used the **risk** layer, was not demonstrated.
   - VLM itself pointed the wrong way (IRR 0.79 per mm/yr of subsidence).
   - The hazard result is therefore a **lead from one secondary in one city, not a finding**: it was one of 13 secondaries, chosen for follow-up after it was seen.
2. **What this study does.** It tests that lead with a plan frozen before any linkage, in two new cities that sit on expansive clay. Both are among the 28 cities Ohenhen et al. (2025) mapped, and their layers (CC0, DOI 10.7294/27606942) are used as published: no refitting, resampling or tuning.
3. **The outcomes come after the map's data.** The map uses Sentinel-1 data from 2015–2021. The outcome is a first recorded foundation-repair permit issued from 2022-01-01 to 2025-12-31, among houses at risk at the end of 2021.
4. **Design carried over from Ohenhen–Austin** (each change is stated where it applies):
   - a cohort with a fixed start;
   - Baseline 1 + location (here in flexible form: splines and an x/y surface, §7);
   - the adjusted Poisson IRR with wild cluster score bootstrap inference (here 12 km blocks, §7);
   - the held-out log-likelihood gain T over 11 fold assignments;
   - Holm's procedure where two tests share one family;
   - a planted check on synthetic outcomes before freezing.
5. **Why these two cities** (`feasibility/second_clay_city/FEASIBILITY.md`):
   - **Both:** a separate foundation-repair permit type in open data, an appraisal roll describing houses on 2022-01-01, and expansive clay.
   - **San Antonio:** about 5.5% of mapped pixels are hazard class 2–3 (Austin 2.4%), and there are about 3,000 foundation-repair permits a year.
   - **Dallas:** 1.2% of mapped houses are flagged, so on its own it is weak.
   - NYC was ruled out: its outcome data end in August 2022, and its hazard flag covers 0.46% of the map.

## 1. Questions

- **Primary (confirmatory), Q-H: added information.** Does the published hazard flag add information about which houses record a first foundation-repair permit in 2022–2025, beyond Baseline 1 and location? Baseline 1 enters in flexible form: splines and a smooth x/y surface (§7).
  - **Estimand (D1, decided by the user on 2026-11-22):** the **pooled adjusted IRR** of the flag, from one Poisson model fitted on both cities. Each city keeps its own intercept and its own Baseline 1 coefficients; the flag has one common coefficient. Its one-sided test (IRR > 1) is the decision test.
  - **Held-out gain:** the pooled T, the sum of the two cities' T values. Each city's T is computed within that city, on its own folds, as in Austin.
  - **"Added information demonstrated"** requires both a rejection and a pooled T > 0.
- **Key secondaries (not decision tests):**
  - the city-specific adjusted IRRs and T values;
  - **V:** the unadjusted IRR (does the map flag houses with more repairs at all?);
  - the same analyses for the risk layer.

All readings concern **recorded** repair permits, not independently validated physical damage or its cause.

## 2. Why this study

- **The thesis question:** does InSAR ground motion add held-out information about building damage?
- **Where the evidence stands:**
  - Alexandria: robust, but concurrent and site-specific.
  - NYC: not replicated.
  - Austin, OPERA velocity: not demonstrated.
  - Austin, Ohenhen risk map: V validated; U not demonstrated.
- **The open lead:** differential settlement (angular distortion), the quantity that structural engineering ties to damage, in the hazard layer.
- **What a confirmatory test adds:**
  - new places, with no outcome seen;
  - a published, fixed product;
  - a complete at-risk population in which every house is a control;
  - spatially separated validation.
  
  This is the evidence standard the research-directions report asks for (`deep-research-report.md`).

## 3. What is already known (disclosure; step 0, outcome-blind)

- **Map layers:** downloaded 2026-11-18 into `Alex_private/ohenhen2025_tx_20261118/` (SHA256SUMS there). The grids are EPSG:4326, 0.0015°.

  | | Hazard class 2–3, share of mapped pixels |
  |---|---|
  | San Antonio | 5.50% |
  | Austin | 2.39% |
  | Fort Worth | 2.20% |
  | Dallas | 1.04% |

- **Dallas reference population** (`step0/dallas_population.json`, `scripts/d0_population.py`; DCAD 2022 certified roll and 2022 parcels):
  - **Flow:** 210,914 accounts with code A11, division RES and city jurisdiction DALLAS → built 2019 or earlier: 207,647 → ambiguous parcel IDs out (117) → points outside the city (27) → **207,503 eligible**.
  - **Hazard layer:** 101,173 houses mapped (48.8%). **Flagged 1,200** (1.19% of mapped), in 162 map cells, with no class 3.
  - **Risk layer:** 98,575 mapped, 2,093 flagged.
  - **Foundation recorded for 99.99%:** pier and beam 100,311; slab 89,513; post 16,539.
  - **Mapped share by year built:** 34–45% for 1900–1959, 68–72% for 1980 and later.
  - **Medians:** year built 1975 flagged vs 1968 other mapped; slab share 0.61 vs 0.54.
- **Dallas features so far:**
  - **Income** (`step0/dallas_income.json`): ACS 2017–2021 B19013. Block group for 196,305 houses, tract fallback for 8,193, missing for 3,005 (1.45%).
  - **Terrain** (`step0/dallas_terrain.json`): Austin's `s1_dem.py` run unchanged on 30 USGS 1 m tiles (project TX_Pecos_Dallas_2018_D19). All 207,503 houses have a value.
  - **Soil** (`step0/dallas_soil.json`, `scripts/d3_soil.py`): Austin's method unchanged, read from the NRCS gSSURGO Texas geodatabase (survey version 2026-09-03 for TX113, the same date as Austin's TX453 file). Missing for 1,098 houses (0.53%, mostly 'Urban land').
    - Shrink–swell classes: low 15%, moderate 40%, high 19%, very high 25%.
    - **Reader check** (`step0/soil_reader_check.json`): rerun on Austin's 149,316 houses, the gSSURGO reader reproduces the frozen Austin values exactly wherever the map unit is the same (99.6% of houses; largest difference 1e-6).
    - The other 0.4% take a neighbouring map unit because the polygon boundaries differ between the two packagings.
- **Dallas link check** (`step0/dallas_link_check.json`, `scripts/d4_link_check.py`; permits linked to roll accounts only, no map value read):
  - **All residential permit types (255,988):** 70.5% to a population house, 13.7% to another roll account, 13.9% unmatched, 1.9% ambiguous.
  - **"Residential Foundation Repair" (4,589, 2021–2026):** 77.5% to a population house, 6.0% to another account, 14.8% unmatched, 1.7% ambiguous.
  - **Unmatched foundation permits (679):** 358 are on streets that do not exist on the Dallas County roll, probably the parts of the city in Collin, Denton, Kaufman or Rockwall County, which are outside the population. The other 321 (7%) are address errors or numbers missing from the 2022 roll.
  - These losses are not expected to depend on the map, so they bias toward the null.
  - The full permit file (`Alex_private/dallas_permits_20261119/`, 397,306 rows, SHA256SUMS) runs to 2026-11-18. The SoQL text maximum "12/31/25" was a text-sort artefact.
- **Dallas outcomes, counts only, not linked to any house:** Dallas OpenData `e7gq-4sah`, permit type "Residential Foundation Repair": 2022 428, 2023 583, 2024 955, 2025 1,165, citywide over all property types.
  - Total permit volume about doubles from mid-2024 (a system change); the foundation share goes from 1.5% to 1.9%.
  - For 2018–2020 the same work appears as "Building (BU) Single Family" permits whose description contains FOUNDATION (about 1,000 a year).
- **San Antonio outcomes, counts only** (`Alex_private/sanantonio_permits_20261118/`): permit type "Foundation Repair Permit". Unique permits by issue year: 2021 3,230; 2022 3,177; 2023 3,153; 2024 2,927; 2025 2,976. 99% carry coordinates. Issued permits are online from 2020-07-20 only.
- **San Antonio houses: the current Bexar County parcel layer (D7).**
  - **Why this source:**
    - a 2022 certified BCAD roll would need a Public Information Act request, which the user chose not to send;
    - TxGIO StratMap 2021/2022 Bexar parcels are blocked by the host (HTTP 403, including from US VPN exits).
  - **The source:** the Bexar County Parcels MapServer layer 0 (maps.bexar.org), downloaded in full by a Grok worker over a US VPN into `Alex_private/bexar_parcels_current_20261119/` (729,183 object IDs, in progress).
  - **What it holds:** current values, with year built up to 2025.
    - Fields: property ID, account, situs, state code, property use, year built, gross building area (GBA), land and improvement values, and the polygon (EPSG:2278).
    - Stories, rooms and the house/detached counts are empty. There is **no foundation type**.
  - **Complete:** 730 pages, 729,183 records, SHA256SUMS verified. Two pages too large to fetch whole were fetched in blocks of 100 IDs and merged; the parts are kept in `pages_split/` and listed in `MANIFEST.md`.
- **San Antonio reference population** (`step0/sanantonio_population.json`, `scripts/s0_population.py`; built 2026-11-22; private outputs in `Alex_private/hazard_tx/sanantonio_20261122/`, SHA256SUMS):
  - **Flow:**
    - 729,183 records → state code A1: **588,018**;
    - year built missing 2,334; **after 2019: 76,033** (13% of A1, mostly new subdivisions; this share is what secondary 15 must bound) → built 2019 or earlier: 509,651;
    - duplicate property ID or account 18; shared polygons 0;
    - points outside the city 156,058 → **353,575 eligible**.
  - **Property use inside A1:** code 001 for 576,382 of 588,018; 002 (10,508) has larger lots (median 2,310 m²). No code identifies townhouses, so **no property-use exclusion** is made (authors' choice).
  - **Hazard layer:** 215,137 houses mapped (60.8%). **Flagged 14,492** (6.7% of mapped), in 1,980 map cells (class 3: 47).
  - **Risk layer:** 211,457 mapped, 17,519 flagged.
  - **Medians:** year built 1999 flagged vs 1986 other mapped; building area 1,639 vs 1,756 sq ft.
  - **Building area** (GBA) missing for 1,633 houses (0.46%).
- **San Antonio features** (outcome-blind):
  - **Income** (`step0/sanantonio_income.json`): Bexar County block groups for 337,234 houses, tract fallback for 16,341, none missing.
  - **Soil** (`step0/sanantonio_soil.json`): TX029 from the same gSSURGO file; none missing.
    - Shrink–swell classes: low 9%, moderate 32%, high 21%, very high 38%.
  - **Terrain** (`step0/sanantonio_terrain*.json`): Austin's `s1_dem.py` unchanged, once per 3DEP project, then `scripts/s1_combine_terrain.py`. All 353,575 houses have a value.
    - TX_Central_B2_2017: 347,053 houses (77 of them by most valid pixels);
    - TX_Hurricane_2018_D18_SUPPLEMENTAL_DRRA: 6,522;
    - TX_RedRiver_Atacosa_B2_2018: none.
    - Where both projects are complete (1,893 houses): median elevation difference 1.1 cm, slope correlation 0.98.
  - **Primary rows** (mapped, complete Baseline 1 without the slab term): 214,417, of which 14,456 are flagged.
- **San Antonio link check** (`step0/sanantonio_link_check.json`, `scripts/s4_link_check.py`; permits linked to parcel accounts only, no map value read):
  - **Permits:** 457,909 unique; 420,279 with a point (both coordinate systems).
  - **Residential types (117,176):** 68.1% to a population house, 31.2% to another parcel, 0.7% unmatched, 0.02% ambiguous.
  - **"Foundation Repair Permit" (18,495):** 92.1% to a population house, 7.8% to another parcel, 0.14% unmatched.
  - **House-number agreement** for permits linked by point to a population house: 99.3% (268,455 permits).
  - **Demolition permits (2,755):** 19.9% to a population house, 77.3% to another parcel. Demolished houses are often no longer A1, which is the loss secondary 15 bounds.
- **Planning numbers for San Antonio, if the flag were unrelated to repairs** (link table, eligible houses only):
  - **10,544** eligible houses have their first linked foundation permit on record (from 2020-07-20) issued in 2022–2025;
  - scaled to the primary rows (60.6% of eligible), that is **about 6,394 events**, and **about 431 among the 14,456 flagged rows**;
  - between-block SD of the log repair rate (2 km blocks): 0.73 in 2021 and 0.67 in 2022–2025, within the range the planted cells cover.
- **Planning numbers for Dallas, if the flag were unrelated to repairs** (link table, eligible houses only, no map value): **2,266** eligible houses have their first linked "Residential Foundation Repair" permit on record (2021 onward) issued in 2022–2025. Scaled to the primary rows (mapped, complete Baseline 1: 97,764 of 207,503, 47.1%), that is **about 1,068 events**, and **about 12.5 among the 1,145 flagged rows**.
  - The first draft's rough figures (2,500 eligible, 1,220 mapped, 15 flagged) are replaced by these.
  - If flagged houses repaired at Austin's unadjusted hazard ratio (4.7), the flagged count would be about 60.
  - These are planning numbers, not results. Dallas alone cannot carry the test.
- **Dallas planted check (§9; synthetic outcomes only), 2026-11-19:**
  - r1 fails the null cells (rejection up to 7.8%). r2, r3 and r4 are acceptable in all six null cells, at 1.9–3.6% (conservative).
  - Power to demonstrate (rejection with T > 0) at IRR 1.5 / 1.74: r2 **41% / 64%**, r3 **38% / 62%**.
  - Under the U null (the Austin generating model, no flag effect), the unadjusted test rejects 13–29% of the time, because flagged houses differ on Baseline 1. The adjusted test rejects 2–4% under r2–r4. Baseline 1 is needed.
  - Between-block SD of the log repair rate in the real outcomes (2 km blocks, eligible houses, no map value): 0.80 in 2021 and 0.71 in 2022–2025. The SD-1.0 cell covers this.

## 4. Fixed inputs

- **Map files:** `risk_<city>.tif` and `beta_<city>.tif` (and `<city>_VLM.csv` for secondary 5), from figshare 27606942, SHA-256 in `Alex_private/ohenhen2025_tx_20261118/SHA256SUMS`.
- **Dallas:**
  - DCAD `DCAD2022_CERTIFIED_07252022.ZIP` (88d83371…) and `PARCEL2022.zip` (489bfd76…);
  - the permits `e7gq-4sah` as downloaded on 2026-11-19 (`Alex_private/dallas_permits_20261119/e7gq-4sah.csv`, SHA-256 e970c38a…; issue dates 2018-01-01 to 2026-11-18). This file is the one used for the link check, and it is **fixed now** (authors' choice): it is not downloaded again for the real run. Permits issued after 2025-12-31 are not used.
  - TIGER/Line 2021 place and block groups; ACS 2021 B19013;
  - the USGS 1 m DEM tiles (server, SHA256SUMS);
  - SSURGO via `gSSURGO_TX.7z` (NRCS Box share, downloaded 2026-11-19; SHA-256 in `Alex_private/gssurgo_tx_20261119/SHA256SUMS`), survey areas TX113 and TX029.
- **San Antonio:**
  - the current Bexar County parcel layer (D7; `Alex_private/bexar_parcels_current_20261119/`, SHA256SUMS written when the download completes);
  - the permit files `permits_issued_ending_12312024.csv` and `permits_issued.csv` (SHA256SUMS in their folder);
  - TIGER/ACS as for Dallas; soil from the same gSSURGO file (TX029).
  - **The 3DEP 1 m DEM.** Three projects overlap the city (`Alex_private/dem_sanantonio_20261119/summary.txt`), all collected before 2022:

    | Project | Collected | Share of the city's bounding box | Tiles |
    |---|---|---|---|
    | TX_Central_B2_2017 | Jan–Mar 2017 | 86% | 36 |
    | TX_Hurricane_2018_D18_SUPPLEMENTAL_DRRA | Jan–Feb 2019 | 65% | 36 |
    | TX_RedRiver_Atacosa_B2_2018 | Jan 2018 | 12% | 11 |

    - Austin's `s1_dem.py` is run unchanged once per project.
    - Each house takes the first project, in the order above (largest coverage first, so most houses share one survey), in which all of its parcel's pixels are valid. If no project covers the whole parcel, it takes the project with the most valid pixels.
    - The number of houses from each project, and the agreement of elevation and slope where projects overlap, are reported.
- **House point:** the parcel polygon's centroid in EPSG:32614 (Dallas and San Antonio are both in UTM zone 14). A house takes the class of the map cell that contains its point. A cell with no data gives no class.

## 5. Population, cohort, follow-up and outcome

- **Population (D3), per city:** detached single-family houses on the 2022 certified roll.
  - **Dallas:** state code A11 (A12 townhouses and A13 condominiums are out), division RES, city jurisdiction DALLAS.
  - **San Antonio (current layer, D7):** state code A1 (single-family residence), inside the City of San Antonio (TIGER 2021 place 4865000), year built 1–2019.
    - A polygon shared by several A1 accounts is ambiguous: those accounts are left out and counted.
    - The property-use codes inside A1 are tabulated, and any exclusion (for example townhouses) is fixed from that table before any linkage.
    - **The values are current, not as of 2022-01-01.** Three consequences are stated and checked (§11, secondary 15):
      - a house demolished or rebuilt after 2021 drops out or shows its new year built;
      - an addition after 2021 shows in its building area;
      - parcels may have been re-platted.
  - **Main improvement:** the largest living area. Year built is that improvement's (zero is missing). **Built in 2019 or earlier.**
  - **Point:** inside the city (TIGER 2021 place). A parcel ID held by more than one account is ambiguous: those accounts are left out and counted.
- **Mapped houses only:** houses with a hazard class (D4 of Ohenhen–Austin). Secondary 9 covers the map user's view.
- **At risk at 2021-12-31:** no matched foundation-repair episode in the look-back and no demolition censoring on or before that date.
  - **Look-back (D5):** everything the open data hold. Matched foundation permits (authors' choices, fixed 2026-11-22 from the permit-type and description tables; no outcome was linked to a map value):
    - **Dallas:**
      - "Residential Foundation Repair" (first issued 2021-01-31), at any date;
      - any "Building (BU) Single Family …" permit (these end in 2021) whose work description contains FOUNDATION, at any date;
      - **look-back only:** a "Residential Alteration Addition Permit" whose work description contains FOUNDATION, issued before 2022-01-01.
      - **Why the last item:** from mid-2021 to early 2025 the city recorded about 70–180 such permits a quarter, alongside "Residential Foundation Repair". From 2025-Q2 they fall to about 30 a quarter while "Residential Foundation Repair" keeps rising. Part of the city's foundation work was therefore filed under this type. In the look-back these permits remove houses already repaired.
      - In follow-up the event stays the city's own type (D4, as drafted). The broader outcome is secondary 17.
      - "Phase – …" permits (no land use; phases of a main permit) are not used.
    - **San Antonio:** "Foundation Repair Permit", which is first issued on 2020-12-01 in the files (the files start 2020-07-20). "Res Foundation Permit" (11 permits in all) is not used.
  - The look-back is short, so houses repaired earlier stay in the cohort. That biases toward the null and is stated in §12.
- **Follow-up** from 2022-01-01 to the earliest of:
  - the first matched foundation episode;
  - total demolition: the house's first demolition permit at any date in the files (Dallas: "Demolition Permit SFD/Duplex" and "Residential Demolition Permit"; San Antonio: "Demolition Permit"). A permit whose description (Dallas work description; San Antonio project name) contains the word PARTIAL is not a total demolition (Austin's rule; 8 of 8,202 in Dallas, 1 of 2,755 in San Antonio). A demolition on or before 2021-12-31 removes the house from the cohort (at risk, above).
  - **2025-12-31.**
- **Event (D4):** a first foundation-repair episode during follow-up.
  - **Permit types:** Dallas "Residential Foundation Repair"; San Antonio "Foundation Repair Permit". The permit type is the city's own classification, so no keyword rule is needed.
  - **Date:** the **issue date** in both cities (Dallas publishes no application date).
  - **One episode:** permits on the same house within 365 days are one episode, dated by the first.
  - **Recent construction:** a first episode within 3 years after a new-building, addition or demolition permit on the same house (dated in [episode − 3 years, episode)) ends follow-up without an event. This is Austin rule 8, adapted to each city's permit types (authors' choices, fixed 2026-11-22):
    - **Dallas:**
      - "Building (BU) Single Family" New Construction, Addition and Reconstruction;
      - "Residential New Construction Permit";
      - "Residential Alteration Addition Permit" only where the work description contains ADDITION (9,041 of 28,673; the rest are alterations);
      - the two demolition types (total).
    - **San Antonio:** "Res New Building Permit", "Home Addition Permit", "Building Move Permit" and "Demolition Permit" (total). Accessory-structure types are not used.
- **Linkage (D6):**
  - **San Antonio** (`scripts/s4_link_check.py`): the permit point falls within exactly one parcel polygon of the current layer (D7), which may belong to any property type.
    - Permits with no point, or whose point misses every polygon, are matched by normalised address to the situs: first exactly, then with a trailing street-type word removed on both sides, because permits often omit it.
    - A match must be unique, resolved by ZIP if needed.
    - **Quality check (development run on the first third of the layer):** for permits linked by point to a population house, the house number in the permit address equals the parcel's situs number in 99.5% of cases.
  - **Dallas:** normalised address (house number, street name, ZIP) to the 2022 roll's situs. A permit matching more than one house is not allocated and is counted.
  - **Link check before freezing:** the match rate is checked on permits of **all** residential types (not foundation alone) and reported. No permit is linked to any map value before freezing.
- **Person-time:** days from 2022-01-01 to exit, divided by 365.25. An exit by episode or demolition counts its day as half a day.

## 6. Predictor

- **Primary:** hazard flag = published beta class 2–3 (angular distortion 1/1,500 or more), against classes 0–1.
- **Other codings (secondaries, §11):** the four hazard classes; the risk flag (classes 3–4); VLM at the house.
- No threshold, merger or smoothing is chosen from the data.

## 7. Primary analysis

- **Rows:** cohort houses with complete Baseline 1, in both cities.
- **Baseline 1 (per city, as Austin §9):**
  - building age at 2022-01-01;
  - log living area (San Antonio: log gross building area from the current layer); log lot area (the parcel polygon);
  - soil linear extensibility, weighted over 0–150 cm (SSURGO);
  - mean slope and elevation within the parcel (USGS 1 m DEM);
  - log neighbourhood income (ACS 2017–2021 B19013, block group, with tract fallback);
  - a slab-foundation indicator, if the roll records foundation type for at least 90% of houses (Dallas: yes, 99.99%; San Antonio: no field, so the term is absent there);
  - x/y in km (entered through the location surface below).
- **Form of Baseline 1: flexible** (user, 2026-11-22, after the planted checks of §9.2 and §9.3.1). These are the columns of the planted check in §9.3, per city:
  - **Continuous features:** each of building age, log living area, log lot area, soil LEP, slope, elevation and log income enters as a restricted cubic spline (Harrell) with 5 knots, giving 4 columns.
    - The knots are **fixed now** at the values in `step0/planted_flex_20261122/flex_design.json` (SHA-256 2ae6d676…). They are each city's 5%, 27.5%, 50%, 72.5% and 95% quantiles over the mapped houses with complete Baseline 1, computed with no outcome. They are not recomputed in the real run.
  - **Slab indicator:** linear (Dallas).
  - **Location:** a tensor-product surface, RCS(x) ⊗ RCS(y), with the same fixed knots. That is 4 + 4 main-effect columns and 16 products, 24 columns in all, replacing linear x/y.
  - **Columns:** Dallas 53, San Antonio 52.
  - **Orthonormalisation:** within each city, the standardised columns are orthonormalised on that city's primary rows (SVD, columns scaled to mean square 1; `planted_flex.py`'s procedure). This changes no fitted value and no flag estimate; it makes the Newton fits converge.
  - **The linear Baseline 1 + x/y** of draft 1 is secondary 16.
- **Pooled adjusted IRR (D1, decided by the user on 2026-11-22):** a Poisson model with log person-years as offset. The terms are each city's own intercept, each city's own flexible Baseline 1 coefficients (city × column interactions) and one flag term.
- **Inference (D2, revised 2026-11-22):** wild cluster score bootstrap (Kline and Santos 2012) with Webb six-point weights, 9,999 draws, seed 2071.
  - **Clusters:** the **12 km block** on a grid of 12,000 m edges in EPSG:32614 (the 2 km grid's blocks grouped 6 × 6). Blocks are city-specific and never cross cities. Dallas has 15 blocks and San Antonio 18; 12 and 15 of them, respectively, hold flagged houses.
  - **This is r4.** Under the flexible baseline, the §9 rule (r3 first, then r1, r2, r4) gives r4: r3 misses one null cell narrowly (§9.3.1), and r4 is acceptable in all six. The user confirmed flexible + r4 on 2026-11-22, replacing the earlier D2 choice of r3 (6 km). r3 is reported under secondary 13.
  - **Outputs:** a one-sided p for IRR > 1, and two-sided 90% and 95% intervals from inverting the test over 801 log-IRR values from log 0.2 to log 5.
  - **Computation (authors' choice, fixed before freezing):**
    - **Primary:** the estimate, p and intervals come from `oa_core.infer` (the frozen Ohenhen–Austin code, hash asserted) on the full pooled design.
    - **Secondaries:** every secondary uses `scripts/hx_infer.py`. It gives the same values faster, because with the flag coefficient fixed the model separates by city. Its restricted fits start from the previous grid point, and secondary 6's block fixed effects are concentrated out.
    - **How agreement is checked:**
      - `hx_infer.py`'s self-test compares it with `oa_core.infer` (r1, r3, r4: estimate, p, intervals) and with explicit fixed-effect dummies;
      - every run fits the primary both ways and records whether they agree (`primary_check`).
    - **When a p-value can differ by one draw:** only at an exact tie between a bootstrap statistic and the observed one. That needs a constant weight vector, with probability 6/6^G, which is negligible at r4's 33 blocks.
    - **Person-time:** comes from Ohenhen–Austin's frozen `follow()`.
- **Code:**
  - `scripts/build_events.py` builds the tables of §5 and has a self-test of 22 synthetic houses covering each rule;
  - `scripts/run_ht.py` runs the cohort, primary, decision and secondaries, in synthetic, decoy and real modes; real mode (and `build_events.py` on real permits) is refused until the frozen plan exists and matches `freeze/HAZARD_TX_PLAN_frozen.sha256`, so the scripts keep the hashes recorded in §15. `build_events.py`'s self-test also writes its tables to disk and reads them back through `run_ht.py`'s reader (the hand-off used by the decoy and real runs).
- **Held-out gain T (per city, then summed):**
  - **Models:** the frozen Austin logistic model (`nyc_lib.model("LR")`). M0 = the city's flexible Baseline 1 columns (orthonormalised, as in the planted check); M1 = M0 + flag.
  - **Statistic:** the mean, over 11 fold assignments, of the out-of-fold log-likelihood gain.
  - **Folds:** StratifiedGroupKFold, 5 folds, over 2 km blocks, with label = "house has an event in follow-up". Seed 42, then seeds 0–9.
  - **Pooled T** = T(San Antonio) + T(Dallas).
  - **Interval for pooled T:** a refit block bootstrap, 2,000 resamples of 2 km blocks, stratified by city, seed 2072. It resamples rows of the fixed orthonormalised design; the design is not re-orthonormalised per resample.
    - **What this interval looks like under a true effect (synthetic run, §15):** with the planted IRR 1.5 in the primary rows, T was 42.7. Its bootstrap median was 38.1 and its 95% interval [−7.3, 86.5], with 5.5% of resamples at or below 0.
    - The interval is wide because the flagged houses sit in few 2 km blocks. An interval that includes 0 beside a demonstrated primary is therefore expected. It is descriptive and does not change the §8 reading, which uses the point value of T.
- **Also reported:**
  - the city-specific adjusted IRRs and Ts;
  - the change in PR AUC and ROC AUC;
  - the change in Brier score;
  - calibration of M1;
  - observed against predicted risk by decile.

## 8. Decision (pooled; one test)

- **Test:** the pooled adjusted IRR > 1, one-sided, at α = 0.05 (one family member, so no Holm). The **90%** interval matches the test.
- **δ = IRR 1.5 (D2, as Ohenhen–Austin):** the smallest enrichment worth acting on as a screen.
- **Readings:**

  | Reading | Condition |
  |---|---|
  | **Added information demonstrated, enrichment of δ or more not excluded** | rejected, T > 0, upper bound ≥ 1.5 |
  | **Added information demonstrated, enrichment below δ** | rejected, T > 0, upper bound < 1.5 |
  | **Not demonstrated: association beyond the baseline without a held-out gain** | rejected, T ≤ 0 |
  | **Not demonstrated, useful enrichment excluded** | not rejected, 1 ≤ upper bound < 1.5 |
  | **Not demonstrated, inconclusive** | not rejected, upper bound ≥ 1.5 |
  | **Not demonstrated, opposite** | upper bound < 1 |

- **If only Dallas is in hand at freezing (D7):** the same rules apply to Dallas alone. The plan then states its planted power, and "inconclusive" is the expected reading if power is low.
- **Austin result:** it is not pooled into the decision, because it generated the hypothesis. A descriptive three-city summary is secondary 12.

## 9. Planted check (before freezing; synthetic outcomes only)

- **Setting:**
  - the real mapped houses and the real map of each city;
  - a fixed follow-up of 4.0 years for every house;
  - Bernoulli events;
  - an intercept giving each city its planning event count (Dallas: 1,068 events among the primary rows, from §3; San Antonio: set from the link table once the roll is in hand).
  - **Rows:** the primary rows (mapped, complete Baseline 1); the null cells are judged on the primary adjusted test (city intercepts, city × Baseline 1 terms, flag).
- **Hidden field:** independent of the map, on the logit scale (random Fourier features, squared-exponential covariance), as in Ohenhen–Austin.
- **Null cells** (1,000 datasets each):
  - fields with range 1, 3, 8 and 15 km at SD 0.5;
  - range 3 km at SD 1.0;
  - range 3 km plus a linear trend.
- **U null and power** (500 datasets each):
  - **Generating model:** the Austin generating coefficients (`feasibility/austin/planted_signal/generating_coefficients.json`, standardised features), transported unchanged, plus a 3 km field.
  - **U null:** the generating model with no flag effect.
  - **Power:** the generating model + log(1.5) × flag, and + log(1.74) × flag (the Austin estimate).
- **Acceptability rule (as Ohenhen–Austin):**
  - a null cell is acceptable if the Wilson lower bound of the rejection rate is at most 0.05, the rate is at most 0.075, and there is no positive bias;
  - **r3** (wild, 6 km) is the inference if it is acceptable in all null cells (user, D2, 2026-11-19). If it is not, the first acceptable of r1 (CR1 Wald, 2 km), r2 (wild, 2 km) and r4 (wild, 12 km), in that order, is used.
  - The first draft said "the first acceptable of r1–r4", which conflicted with D2; this wording replaces it.
  - otherwise the user decides before freezing.
  - **Outcome:** the linear baseline gave no acceptable candidate (§9.2). The flexible baseline gives r4 (§9.3.1), which the user confirmed on 2026-11-22.
- **Power** is reported for the pooled test and each city at IRR 1.5 and 1.74.
- **Code:** `scripts/planted_ht.py` with `scripts/ht_core.py` (the Ohenhen–Austin `oa_core.py`, hash asserted). The run is on the server: 64 workers, 8,000 datasets, 23 minutes.

### 9.1 Dallas result (2026-11-19; `step0/planted_dallas_20261119/PLANTED.md`)

- **Inputs:** 97,764 rows, 1,145 flagged, 1,068 target events. The 2 km / 6 km / 12 km blocks number 214 / 41 / 15, and 66 / 29 / 12 of them hold flagged houses.
- **Null cells 1–6, rejection rate of the adjusted test** (1,000 datasets each):

  | Cell | r1 | r2 | r3 | r4 |
  |---|---|---|---|---|
  | 1 km, SD 0.5 | 7.8% **fails** | 3.6% | 3.1% | 3.1% |
  | 3 km, SD 0.5 | 6.4% **fails** | 2.6% | 2.2% | 2.4% |
  | 8 km, SD 0.5 | 6.4% **fails** | 3.4% | 3.6% | 3.6% |
  | 15 km, SD 0.5 | 5.9% | 1.9% | 2.2% | 2.7% |
  | 3 km, SD 1.0 | 7.4% **fails** | 3.2% | 3.0% | 2.6% |
  | 3 km, SD 0.5 + trend | 5.3% | 2.1% | 2.3% | 2.6% |

  - The mean log IRR is slightly negative in every null cell (−0.035 to −0.059). With about 12.6 flagged events this is the expected small-count bias of a log ratio, and it is not a positive bias.
- **U null (cell 7), 500 datasets:**
  - adjusted test: 7.0%, 3.6%, 3.4%, 2.2% (r1–r4);
  - unadjusted test: 28.6%, 15.8%, 16.6%, 13.0%;
  - T > 0 in 17%; demonstrated under r2 3.6%, under r3 3.0%.
- **Soil squared (cell 8, reported):** adjusted 1.4% under r2–r4.
- **Power to demonstrate** (rejected and T > 0):

  | | r1 | r2 | r3 | r4 |
  |---|---|---|---|---|
  | IRR 1.5 | 51% | 41% | 38% | 34% |
  | IRR 1.74 | 75% | 64% | 62% | 58% |

  T > 0 in 55% (IRR 1.5) and 78% (IRR 1.74) of datasets.
- **What the rule gives:** **r3**, which is acceptable in all six null cells. The first draft's §9 wording ("first acceptable") would have picked r2 and disagreed with D2. The user chose r3 (D2, 2026-11-19), and §9 now says so.
- **Mean time per dataset:** 11.1 s.

### 9.2 Pooled result, Dallas + San Antonio (2026-11-22; `step0/planted_pooled_20261122/PLANTED.md`)

- **Inputs:** 312,181 rows. Dallas: 97,764 rows, 1,145 flagged, 1,068 target events (12.5 flagged if unrelated). San Antonio: 214,417 rows, 14,456 flagged, 6,394 target events (431 flagged if unrelated); 2 km / 6 km / 12 km blocks 314 / 51 / 18 (197 / 44 / 15 with flagged houses).
- **Null cells 1–6, rejection rate of the pooled adjusted test** (1,000 datasets each; one-sided α 0.05):

  | Cell | r1 | r2 | r3 | r4 |
  |---|---|---|---|---|
  | 1 km, SD 0.5 | 6.0% | 5.0% | 4.9% | 4.4% |
  | 3 km, SD 0.5 | 8.0% **fails** | 6.5% **fails** | 6.0% | 5.0% |
  | 8 km, SD 0.5 | 8.2% **fails** | 7.3% **fails** | 5.3% | 4.8% |
  | 15 km, SD 0.5 | 9.7% **fails** | 8.6% **fails** | **7.1% fails** (Wilson 5.7–8.9%) | **6.8% fails** (5.4–8.5%) |
  | 3 km, SD 1.0 | 8.6% **fails** | 6.9% **fails** | 5.4% | 4.7% |
  | 3 km, SD 0.5 + trend | 6.3% | 5.2% | 4.8% | 4.0% |

  - No positive bias: the median null IRR is 0.993–1.006 in every cell. The 15 km failure is a too-narrow null distribution, not a shifted estimate.
  - Per city (r3), the 15 km cell rejects 7.4% in San Antonio and 2.2% in Dallas: San Antonio drives it.
  - Pooled r3 in the 15 km cell rejects 4.8% at α 0.025 and 3.0% at α 0.01.
- **U null (cell 7), 500 datasets:** adjusted r3 5.4%; demonstrated (rejected and T > 0) 3.6%; T > 0 in 16%.
- **Soil squared (cell 8, reported):** adjusted r3 rejects 24.4% and demonstrates 23.0%; the median IRR is 1.07 (San Antonio 1.075, Dallas 0.90). With about 430 flagged events, a 7% bias from a nonlinear soil effect left in the residual is detected often. Ohenhen–Austin's cell 8 was 3.6–5.6%; Dallas alone, 1.4%.
- **Power to demonstrate** (pooled; rejected and T > 0): 100% at IRR 1.5 and at IRR 1.74 under r1–r4. The median estimated IRR is 1.45 and 1.65: a small attenuation from the hidden field left out of the model.
- **Per city, Holm over two cities (the D1 alternative), r3:** Dallas 38.8% / 63.8% rejected at IRR 1.5 / 1.74 (demonstrated 38.0% / 61.6%); San Antonio 100% / 100%. In the null cells, Dallas rejects 2.2–3.6% at α 0.05 and San Antonio 4.6–7.4%.
  - Familywise (either city rejected under Holm; computed from the records on the PC): 3.4–3.9% in null cells 1, 2, 3, 5 and 6 and **5.6% in the 15 km cell (Wilson 4.3–7.1%, acceptable)**; U null 3.8% (demonstrated 3.6%); soil squared 16.8%.
- **What the rule gives:** no candidate is acceptable in all six null cells, so **the user decides before freezing** (§9 rule).
- **Mean time per dataset:** 50.7 s (64 workers; 1 h 30 min).
- **User decision (2026-11-22): "Flexible baseline, check first"** (§9.3). The other options offered were:
  - keep r3 with a qualifier;
  - a pooled test at α 0.025 (fixes the 15 km cell, not cell 8);
  - per-city Holm (also leaves cell 8 at 16.8%).

### 9.3 Flexible Baseline 1, checked first (user, 2026-11-22)

- **Why:** the 15 km cell fails because a long-range field survives the linear x/y terms, and cell 8 falsely demonstrates in 23% of datasets because a nonlinear soil effect survives the linear soil term. Pooled power is 100% at IRR 1.5, so the design can spend some of it on a more flexible baseline.
- **Flexible Baseline 1, per city** (authors' choices, fixed before the run; knots from the city's primary rows; no outcome used):
  - each continuous feature (building age, log living area, log lot area, soil LEP, slope, elevation, log income): a restricted cubic spline (Harrell) with knots at the 5%, 27.5%, 50%, 72.5% and 95% quantiles, giving 4 columns;
  - the slab indicator, linear, where the city has it (Dallas);
  - location: a tensor-product surface of restricted cubic splines of x and of y (5 knots each, same quantiles). That is 4 + 4 main-effect columns and their 16 products, 24 columns in all, replacing linear x/y.
  - Columns: Dallas 53, San Antonio 52. Each city's standardised columns are orthonormalised (SVD; nothing fell below the numerical-null threshold of 1e-8). The column space, and with it every fitted value and the flag estimate, stays the same. This makes Newton converge: the products are nearly collinear, with a Hessian condition number of about 1e13 before.
  - The pooled model is otherwise as in §7: city intercepts, city × flexible columns, one flag term. T uses the same columns in M0, with M1 = M0 + flag (nyc_lib LR).
- **Before the run (outcome-blind):** on simulated 15 km fields at the house points, the surface absorbs 92–94% of the field's variance (linear x/y: 17–30%), and 61–71% of an 8 km field.
- **Same datasets:** the synthetic worlds are planted_ht.py's, unchanged (same npz, cells, draws and seeds). Each dataset is therefore the same as in §9.2; only the adjustment differs.
- **Code:** `scripts/planted_flex.py`. It computes the same values as `oa_core.infer`, faster, by using the block structure: with the flag fixed at 0, the restricted fit is the per-city fits.
  - Check 1: with the linear design, it reproduced linear records cells 1, 4 and 9 (dataset 0) exactly (p, T; log IRR within 1e-15).
  - Check 2: on the flexible design, it equalled `oa_core.infer` itself for r1–r4 and per city on cells 4 and 8 (dataset 0).
  - The server run repeats both checks before starting.
- **Acceptance (set before the run):**
  - the §9 rule as before (r3 if acceptable in all six null cells, then r1, r2, r4);
  - cell 8 (reported) is read against Ohenhen–Austin's 3.6–5.6%;
  - if the flexible baseline passes, it becomes the primary baseline (§7), and the linear baseline moves to a secondary;
  - the result goes to the user before freezing.

#### 9.3.1 Result (2026-11-22; `step0/planted_flex_20261122/PLANTED.md`)

- **Null cells 1–6, rejection rate of the pooled adjusted test** (same 1,000 datasets per cell as §9.2; flexible Baseline 1):

  | Cell | r1 | r2 | r3 | r4 | linear r3 (§9.2) |
  |---|---|---|---|---|---|
  | 1 km, SD 0.5 | 6.1% | 5.2% | 5.8% | 5.4% | 4.9% |
  | 3 km, SD 0.5 | 7.6% **fails** | 6.5% **fails** | **6.5% fails** (Wilson 5.13–8.2%) | 5.3% | 6.0% |
  | 8 km, SD 0.5 | 4.4% | 3.5% | 3.4% | 3.9% | 5.3% |
  | 15 km, SD 0.5 | 4.9% | 4.4% | 4.6% | 4.6% | 7.1% fails |
  | 3 km, SD 1.0 | 7.2% **fails** | 6.2% | 5.6% | 4.8% | 5.4% |
  | 3 km, SD 0.5 + trend | 4.4% | 3.8% | 4.7% | 3.9% | 4.8% |

  - **No positive bias:** the median null IRR is 0.996–1.003 in every cell.
  - **r4 is acceptable in all six cells.** Its highest rate is 5.4% (cell 1; Wilson 4.2–7.0%).
  - **The r3 miss is narrow.** It is 65 of 1,000 in cell 2, where at most 63 would be acceptable. Linear r3 had 60 on the same datasets. The paired split, 22 datasets rejected only under the linear baseline and 27 only under the flexible one, fits chance. Under the rule set before the run, this still fails; nothing was rerun or re-read to change it.
  - **The 15 km cell is fixed.** It falls from 7.1% to 4.6% under both r3 and r4. On the same datasets, 50 rejections occur only under the linear baseline and 25 only under the flexible one.
- **U null (cell 7), 500 datasets:** adjusted 6.6%, 5.2%, 6.2%, 4.4% (r1–r4). Demonstrated: r3 4.2%, r4 3.2%. T > 0 in 21%.
- **Soil squared (cell 8, reported):**
  - Under r4, the test rejects 5.0% and demonstrates 2.8%, inside Ohenhen–Austin's 3.6–5.6%.
  - Under r3, it rejects 5.8% (just above that range) and demonstrates 3.6%.
  - The linear baseline gave 24.4% (r3). On the same datasets, 93 rejections occur only under the linear baseline and none only under the flexible one.
  - Median IRR 1.004 (linear 1.07).
- **Power to demonstrate (pooled):** 100% at IRR 1.5 and at IRR 1.74 under r1–r4. The median estimated IRR is 1.45 and 1.65, as with the linear baseline.
- **Per city, Holm over two cities (the D1 alternative):**
  - **Inference:** the records hold r3 only for this design, so per-city r4 figures are not available. A per-city r4 test would have 15 Dallas blocks, which is thin for a wild bootstrap.
  - **Familywise rate** (either city rejected under Holm, from the records): 3.1–4.2% in null cells 1–6. In cell 7 it rejects 5.0% and demonstrates 4.8%; in cell 8 it rejects and demonstrates 5.8%.
  - **Power to demonstrate:** Dallas 38.6% at IRR 1.5 and 63.2% at 1.74 (linear: 38.0% / 61.6%); San Antonio 100% / 100%.
  - **Per city at α 0.05 in null cells:** Dallas 2.5–4.0%, San Antonio 3.2–6.3%.
- **What the rule gives:** r3 is not acceptable in every null cell (cell 2). Of r1, r2 and r4, the first acceptable is **r4**. Its pooled power to demonstrate is 100% / 100%.
  - The flexible baseline therefore **passes**, with r4 as the inference.
  - **Effect on D2:** this changes the user's D2 choice (r3). It was put to the user as the rule's result, and **the user confirmed flexible + r4 on 2026-11-22** (§16).
  - r4 fits D2's own stated reason, that larger clusters are safer against longer-range correlation. Blocks of 12 km number 15 in Dallas and 18 in San Antonio (12 and 15 of them hold flagged houses).
  - **After the confirmation:**
    - §7 now gives the flexible baseline and r4;
    - §10 adds the linear baseline as secondary 16, and r3 is under secondary 13;
    - §16 records the decisions.
- **Mean time per dataset:** 35 s for a null dataset and 208 s with T (64 workers; 2 h 44 min).

## 10. Secondary analyses (descriptive; nominal p-values; no claims beyond §8)

Each reports its estimate with the r4 one-sided p and 90%/95% intervals (`hx_infer`, seed 2071). Secondaries that fit the adjusted model use the flexible Baseline 1 on their own rows: the knots stay fixed, and the columns are orthonormalised again on those rows. Secondaries 4, 10, 15, 16 and 17 also report T.

1. **City-specific:** adjusted IRR and T for San Antonio and for Dallas; heterogeneity (ratio of the two IRRs with its interval).
2. **V, unadjusted:** IRR of the flag, pooled (city-stratified) and per city; age-stratified IRR (built up to 1949, 1950–1979, 1980–2019).
3. **Hazard classes:** incidence by class 0–3 and the trend per class step.
4. **Risk layer:** V and U with the risk flag (classes 3–4).
5. **VLM:** the mean of VLM points within 50 m; IRR per 1 mm/yr of subsidence, adjusted.
6. **Within neighbourhoods:** conditional Poisson with 2 km block fixed effects, plus the flexible feature splines **without** the x/y surface (the surface is nearly collinear with the block effects).
7. **Foundation type:** the flag IRR among slab and among pier-and-beam houses (Dallas has both in large numbers).
8. **By year:** 2022, 2023, 2024 and 2025.
9. **The map user's domain:** all eligible houses, unmapped counted as not flagged.
10. **Cell edges:** excluding houses within 30 m of a map-cell edge where the neighbouring cell has a different flag.
11. **Demolition** as a competing event, by flag.
12. **Three cities, descriptive:** Austin (the hypothesis-generating estimate), San Antonio and Dallas side by side, with a random-effects summary labelled as including the generating data. Austin's 1.74 was adjusted for the **linear** Baseline 1 + x/y, so the summary uses the San Antonio and Dallas estimates from secondary 16 (linear baseline), and the primary estimates are shown beside it.
13. **Inference not chosen:** the primary under the other candidates (r1, r2 and r3; r3 was the earlier D2 choice).
14. **Remodel negative control: removed** (§10's own condition, checked 2026-11-22). San Antonio has no remodel-only permit type: "Residential Repair Permit" covers repairs of every kind, and "Re-Roof Permit" follows hail, which is spatially clustered. Dallas has none from 2022 either, because "Residential Alteration Addition Permit" also covers additions and, until 2025, foundation work.
15. **Current-layer check (San Antonio, D7):** the primary is repeated without San Antonio houses that had a residential new-building, addition or demolition permit issued 2022–2025, since the current layer may describe them after the change. The script also counts permits of those types on parcels whose current year built is after 2019; such houses are missing from the population and may include rebuilds after foundation failure.
16. **Linear Baseline 1 (draft 1's primary):** the pooled adjusted IRR, its r4 test and T, with Baseline 1 linear plus linear x/y. Its planted check (§9.2) failed the 15 km null cell and gave 22–24% rejections under nonlinear soil.
17. **Dallas, broader outcome:** the Dallas event also counts a "Residential Alteration Addition Permit" whose work description contains FOUNDATION, at any date (look-back and follow-up alike). Reported: the pooled primary and the Dallas IRR and T. This checks the primary against the city's filing change (§5).

## 11. Limits

- **The outcome:** a permit records an owner's decision to repair. Under-recording that follows income or geology is addressed by Baseline 1 (income, soil) and block fixed effects (secondary 6), not removed. No negative-control outcome is available (secondary 14).
- **Short look-back:** houses repaired before 2018 (Dallas) or before December 2020 (San Antonio, the first "Foundation Repair Permit") stay in the cohort. Bias toward the null.
- **The map's domain** is selected by InSAR coherence (younger houses, less canopy). Results do not transfer to unmapped areas.
- **Resolution:** a map cell is about 2.4 ha; the map describes areas, not buildings.
- **Timing:** the hazard layer's 25-year angular-distortion horizon is longer than the 4-year follow-up.
- **Dallas power:** on its own, Dallas's planted power to demonstrate is about 39% at IRR 1.5 and about 63% at IRR 1.74 (§9.1; flexible baseline, r3, §9.3.1). San Antonio carries most of the information in the pooled test, so the city-specific results (secondary 1) for Dallas are likely to be inconclusive.
- **San Antonio house data are current, not 2022 (D7):** year built, building area and parcels come from the layer as downloaded in November 2026.
  - A house rebuilt after 2021 drops out; a rebuild after foundation failure would remove an event.
  - Building area includes later additions.
  - There is no foundation type.
  - Secondary 15 checks the size of these effects. The San Antonio features are not claimed to be pre-event.
- **Filing changes in Dallas:**
  - "Residential Foundation Repair" permits roughly double from 2023 to 2025.
  - Until early 2025, part of the foundation work was filed as "Residential Alteration Addition" (§5).
  - A citywide change in recording does not bias the flag contrast unless it differs by place. Secondary 8 (by year) and secondary 17 (broader outcome) show its size.

## 12. Order of work

1. **Step 0:** layers, population, features, outcome-blind coverage (Dallas done except soil; San Antonio pending the roll).
2. **Scripts**, checked on synthetic outcomes. The analysis refuses real outcomes until the frozen plan and its hash file exist.
3. **Link check** on all residential permit types (no map values).
4. **Planted check**, then the inference rule (§9).
5. **User approval and freeze.**
6. **Real run on the server:**
   - build events (`build_events.py`, Dallas, Dallas broad, San Antonio), then a decoy run (real tables given to random houses of the same city), then the real run;
   - cohort and folds;
   - the primary and decision;
   - the secondaries in order, with start and end times.
7. **Result document** (code-generated), with a RECORD/STROBE checklist and flow diagram.

## 13. Data still needed before freezing

- **San Antonio step 0:** done 2026-11-22 (§3).
- **The pooled planted check** (both cities): done 2026-11-22, linear (§9.2) and flexible (§9.3.1). The user confirmed flexible + r4 the same day.
- **D1 and D3–D6:** decided by the user on 2026-11-22 (§16).
- **Scripts:** done 2026-11-22 and checked on synthetic outcomes on the server (§15): `build_events.py`, `hx_infer.py`, `run_ht.py`, with the freeze gate.
- **User approval:** given 2026-11-22 ("Freeze and run (Recommended)").
- **The Dallas permit file:** fixed on 2026-11-22 (the 2026-11-19 download, e970c38a…; §4).

## 14. Deviations log

1. **2026-11-22, where the events are built (procedural; no change to any rule, input or output).**
   - §12 step 6 says the events are built on the server. Instead, `build_events.py` (frozen hash 655fd0e5…) runs on the PC, against `Alex_private`.
   - **Why:** a standing project rule keeps raw permit text (work descriptions, project names, addresses) inside `Alex_private`. Copying the permit files to the shared server would break that rule.
   - **What goes to the server:** only the output tables (house id, dates, status, first permit number and type), hashed. The decoy and real runs stay on the server as planned.

## 15. Records

- 2026-11-18/19, step 0 (outcome-blind):
  - feasibility in `feasibility/second_clay_city/FEASIBILITY.md`;
  - the Dallas population (`step0/dallas_population.json`; private parquet ccb65a2f…);
  - income (`step0/dallas_income.json`; 288c36de…);
  - parcels for terrain (`step0/dallas_parcels_export.json`; cfefebc2…);
  - terrain (`step0/dallas_terrain.json`; 23729904…);
  - soil (`step0/dallas_soil.json`; 2f4dbdd5…) and the soil reader check (`step0/soil_reader_check.json`).
  - The link check (`step0/dallas_link_check.json`; private links 9a97c36d… before the normalisation fix, rerun after it): the address rule abbreviates only the first and last word (a mid-name 'HOLLOW' was wrongly abbreviated in the first run).
- 2026-11-19, Dallas planted check (§9.1; synthetic outcomes only):
  - inputs `step0/planted_inputs.json` (npz 6d135e6b…; links table 58243ac1… read for eligible-house counts only);
  - code `ht_core.py` 2cf88a3d…, `planted_ht.py` 4576090a…, `oa_core.py` 509e3f27…;
  - server run 04:11:47–04:35:04;
  - outputs `step0/planted_dallas_20261119/` (8,000 records). The first summary (cb298af2…, PLANTED.md e8b51872…) used the draft-1 rule "first acceptable" and picked r2; it is kept as `*.first_rule.*`.
  - After D2 (user, r3), the summary code was given the r3-first rule (`planted_ht.py` 74200b84…, summarise step only; the records are unchanged) and rerun on the PC: planted_summary.json f7370e9c…, PLANTED.md 8063b6ba…. It chose r3, with demonstrated power 38.0% / 61.6% at IRR 1.5 / 1.74.
- 2026-11-19 to 2026-11-22, San Antonio step 0 (outcome-blind; D7):
  - Bexar layer `Alex_private/bexar_parcels_current_20261119/` (SHA256SUMS aff2c32d…; pages digest d6c9ff98…);
  - population `step0/sanantonio_population.json` (private b7b0a246…, parcels 61ecd009…);
  - income (`step0/sanantonio_income.json`), soil (`step0/sanantonio_soil.json`);
  - terrain on the server: 3DEP tiles in `Alex_private/dem_sanantonio_20261119/` (per-project SHA256SUMS), combined output 47140de7…;
  - links (`step0/sanantonio_link_check.json`);
  - private folder `Alex_private/hazard_tx/sanantonio_20261122/` with SHA256SUMS.
  - Scripts: `s0_population.py`, `s1_combine_terrain.py`, `s4_link_check.py`; `d1_income.py` gained `--id-col`, `--out-name` and `--county` (Dallas output unchanged).
- 2026-11-22, pooled planted check (§9; synthetic outcomes only):
  - inputs `step0/planted_pooled_20261122/planted_inputs.json` (npz 1c07e371…; 312,181 rows);
  - code `ht_core.py` a9609670…, `planted_ht.py` a9e781da…. Since the Dallas run, the code gained per-city Baseline 1 columns (San Antonio has no slab term), per-city block SD, per-city r3 tests and Holm power. Two Dallas records were re-run and reproduced exactly.
  - server run 07:54:48–09:24:41 (run exit 0, summarise exit 0);
  - outputs `step0/planted_pooled_20261122/` (8,000 records; SHA256SUMS over all files): planted_summary.json d307fc5a…, PLANTED.md 1ba451cf…;
  - result §9.2: no candidate acceptable in all null cells (r3 and r4 fail the 15 km cell); the user decides.
- 2026-11-22, user decision "Flexible baseline, check first"; planted check of the flexible Baseline 1 (§9.3; synthetic outcomes only):
  - code `planted_flex.py` a07981ce… (imports `planted_ht.py` a9e781da… and `ht_core.py` a9609670…, both unchanged); same inputs npz 1c07e371…;
  - PC checks passed (linear reproduction; equality with `oa_core.infer` on the flexible design); PC smoke: 18 s per null dataset, about 95 s with T;
  - server `~/AmrGamal/work/run_ht_planted_flex.sh` (check, run, summarise), 64 workers, started 11:33:04 into `~/AmrGamal/work/hazard_tx/planted_flex_20261122`.
  - Check exit 0 at 11:36:03 (linear reproduction of cells 1, 4 and 9; flexible equal to `oa_core.infer` on cells 4 and 8). Run exit 0 at 14:19:48; summarise exit 0 at 14:19:50.
  - **Outputs** in `step0/planted_flex_20261122/` (8,000 records; SHA256SUMS 1c984798… over all files): planted_summary.json dc5d22e3…, PLANTED.md 71ff3cb7…, flex_design.json 2ae6d676…, check.log 02d88691….
  - Familywise Holm rates and paired linear-against-flexible counts were computed from the records of both runs on the PC.
  - **Result (§9.3.1):** both failures are fixed. r3 misses cell 2 (6.5%, Wilson lower bound 5.13%), so the rule gives r4, which is acceptable in all six null cells; cell 8 under r4 is 5.0%.
- 2026-11-22, user decisions (AskUserQuestion, answers verbatim): "Flexible + r4 (Recommended)", "Pooled test (Recommended)", "Approve as drafted (Recommended)" (D3–D6).
  - The plan became draft 2: §1, the design summary, §7, §10 (secondary 16; secondary 13 now lists r3), §11, §13 and §16.
  - The spline knots are fixed from `flex_design.json` (2ae6d676…), an authors' choice: they are not recomputed in the real run.
- 2026-11-22, pre-freeze code and synthetic check (§12 step 2; synthetic outcomes only, no permit file opened):
  - **Code:**
    - `scripts/build_events.py` 655fd0e5…: self-test of 22 synthetic houses, which writes its tables and reads them back through `run_ht.py`'s reader;
    - `scripts/hx_infer.py` 8e0db959…: its self-test matches `oa_core.infer` for r1, r3 and r4, and the fixed-effects fit matches explicit dummies;
    - `scripts/run_ht.py` 541ca2cb…;
    - `scripts/ht_core.py` a9609670… (unchanged).
  - **Run 1** (code 0228a652… / f1963527…; server, 96 workers, 2,000 T resamples), 17:27:57–19:34:09:
    - both self-tests exit 0, run exit 0, no task errors;
    - outputs `step0/synthetic_run_20261122/` (SHA256SUMS 2903986d…).
  - **Changes after run 1 (advisor review):**
    - the freeze gate reads `freeze/HAZARD_TX_PLAN_frozen.sha256`, so no script is edited at freezing;
    - `world_from_tables` checks that every table names a population house;
    - the `build_events.py` self-test checks the file hand-off;
    - the T bootstrap records its quantiles, its share ≤ 0 and its values;
    - the row description omits flag counts for a continuous predictor (secondary 5).
    - House ids were also checked to be identical between the two scripts: Dallas 207,503 and San Antonio 353,575, both from the same population files.
  - **Run 2** (final code above; same settings), 19:42:32–21:54:17:
    - both self-tests exit 0, run exit 0, no task errors;
    - outputs `step0/synthetic_run2_20261122/` (SHA256SUMS 875fd466…; results.json 63a60b15…);
    - the primary, the flow and all secondaries are identical to run 1.
  - **What the check shows:**
    - `oa_core.infer` and `hx_infer` agree on the primary (`primary_check` equal);
    - planted IRR 1.5 → estimate 1.498, r4 p = 0.0006, 90% [1.385, 1.569], 95% [1.358, 1.582]; T = 42.7 (San Antonio 39.6, Dallas 3.1); reading "Added information demonstrated, enrichment of δ or more not excluded", as §8 gives;
    - T bootstrap median 38.1, 95% [−7.3, 86.5], 5.5% ≤ 0 (§7).
  - **Timing** (expected for the real run, about 2.2 h): `primary_oa` 2.2 h, `s1_ratio` 2.0 h, secondary 8 1.6 h, `primary_block` 1.2 h, T bootstrap chunks of 25 resamples 1.4–1.6 h each, run in parallel.

- 2026-11-22 22:09 EET, user decision (AskUserQuestion, answer verbatim): "Freeze and run (Recommended)". The plan is frozen as this text (draft 2). Then, on the server: `build_events.py` (Dallas, Dallas broad, San Antonio), the decoy run, the real run, and the result document.

- 2026-11-22 22:09:03 EET (20:09:03Z, `FROZEN_AT.txt`), **FROZEN**:
  - `freeze/HAZARD_TX_PLAN_frozen.md` SHA-256 **d6f25de61ac85dd81f6e46f6a66b6ce71901bc741ce0b30156749a31ff570224**, also written to `freeze/HAZARD_TX_PLAN_frozen.sha256`;
  - `freeze/FROZEN_AT.txt`, plus copies of the scripts (`run_ht` 541ca2cb…, `build_events` 655fd0e5…, `hx_infer` 8e0db959…, `ht_core` a9609670…, `planted_flex` a07981ce…, `planted_ht` a9e781da…) and of the flexible planted outputs and synthetic run 2 results;
  - `freeze/MANIFEST.sha256` lists every file; the folder is read-only.
  - The `run_ht.py` gate opens on the PC.

- 2026-11-22, **events built** (§14 deviation 1: on the PC; `build_events.py` 655fd0e5…; 5–61 s per city):
  - private tables in `Alex_private/hazard_tx/events_20261122/` (SHA256SUMS; copied to the server and verified there);
  - counts in `real/events_<city>.json`;
  - Dallas: 2,089 events (2022–2025: 291, 435, 640, 723); 2,734 first episodes before the study period; 45 excluded for recent construction; 3,788 houses with a total demolition;
  - Dallas broad (secondary 17): 2,227 events;
  - San Antonio: 10,380 events (2,763, 2,742, 2,459, 2,416); 3,058 first episodes before the study period; 164 excluded; 312 demolished houses; secondary 15: 2,456 population houses with a construction permit in 2022–2025.
- 2026-11-22 22:11:35, **server decoy → real run** started (`~/AmrGamal/work/run_ht_real.sh`, 96 workers):
  - the freeze manifest and the event tables were verified on the server first;
  - outputs in `~/AmrGamal/work/hazard_tx/real_20261122/{decoy,real}`.
- 2026-11-22 23:55:43, **decoy (code check) passed**, 22:11:36–23:55:42 (1 h 44 min):
  - copied to `real_20261122/decoy/`; `results.json` SHA-256 25c7d7d1…;
  - no errors; the frozen `oa_core` estimate and `hx_infer.BlockModel` give the same values;
  - pooled IRR 0.989 (90% CI 0.879–1.088), p one-sided 0.573; T −2.10 (bootstrap 95% −9.9 to +1.1);
  - 308,610 rows, 7,169 events (random houses, so the counts differ slightly from the real run).
  - The real run started at 23:55:43.
- 2026-11-23 02:25:05, **REAL RUN DONE**, 2026-11-22 23:55:44 to 2026-11-23 02:25:04 (2 h 29 min), no errors, `primary_check` equal:
  - copied to `real_20261122/real/` (`results.json` SHA-256 8444aacf81753c2d…; `real_20261122/SHA256SUMS` covers decoy and real);
  - **§8 reading: "Added information demonstrated, enrichment below δ".** Pooled adjusted IRR **1.25** (90% 1.09–1.47; 95% 1.05–1.53), one-sided p 0.0077; T **+11.93**;
  - T by city: San Antonio +13.48 (11 of 11 assignments positive); Dallas −1.55 (0 of 11); T bootstrap median +14.4, 95% −9.5 to +60.0, 15.0% ≤ 0 (descriptive);
  - primary rows 308,701, 7,080 events; flagged events 863 (San Antonio 850, Dallas 13);
  - key secondaries (descriptive):
    - San Antonio 1.25 (95% 1.05–1.55), Dallas 1.29 (0.48–2.15);
    - 2 km block fixed effects 1.13 (0.97–1.39, p 0.055);
    - linear baseline 1.44;
    - VLM per mm/yr of subsidence 0.94 adjusted;
    - ΔROC AUC San Antonio +0.0001.
- 2026-11-23, **result document** `HAZARD_TX_RESULT.md` (SHA-256 f8dc90ab7128b339…), generated by `scripts/result_report.py` (70b9f342…; not in `freeze/`, written after freezing, changes no number):
  - §6 Interpretation was written after the result was seen;
  - every number in it is read from `results.json`.
  - VLM sign confirmed on the real CSVs: VLM < 0 for 89% of San Antonio points and 99.9% of Dallas points, so −VLM is subsidence, as coded.

## 16. Decisions for the user (all decided by 2026-11-22)

- **D1. Primary estimand — DECIDED (user, 2026-11-22): the pooled adjusted IRR**, with city-specific baselines and one test.
  - The alternative was city-specific tests under Holm, with San Antonio and Dallas co-primary (the option accepted on 2026-11-18 described this).
  - In the flexible planted check (§9.3.1), the pooled test has 100% power to demonstrate at IRR 1.5 and 1.74. Under Holm (r3 figures), Dallas has 38.6% and 63.2%.
- **D2. Inference and δ — REVISED (user, 2026-11-22): r4** (wild cluster score bootstrap, 12 km blocks), with the **flexible Baseline 1** (§7); δ = IRR 1.5 (unchanged).
  - **Why it was revised:**
    - Under the linear baseline, no candidate passed all null cells (§9.2).
    - Under the flexible baseline, the §9 rule gives r4: r3 has 6.5% in the 3 km cell, with a Wilson lower bound of 5.13% (§9.3.1).
    - r4 follows the reason given below for r3: larger clusters are safer against longer-range correlation.
    - The user confirmed flexible + r4 on 2026-11-22.
- **D2 as first decided (user, 2026-11-19): r3** (wild cluster score bootstrap, 6 km), δ = IRR 1.5.
  - In the Dallas planted check, r2, r3 and r4 were all acceptable. Power to demonstrate at IRR 1.5 / 1.74 was r2 41% / 64% and r3 38% / 62%.
  - Reasons for r3:
    - it matches Ohenhen–Austin;
    - its larger clusters are safer against longer-range correlation (the real between-block SD is 0.7–0.8).
  - §7 and §9 were aligned to this choice, and §7 now gives r4.
- **D3–D6 — DECIDED (user, 2026-11-22): as drafted below.**
- **D3. Population:** detached single-family houses on the 2022 certified roll, built 2019 or earlier, inside the city.
- **D4. Event date and window:** issue date; 2022-01-01 to 2025-12-31 in both cities. San Antonio's 2026 permits are not used (one window for both cities).
- **D5. Look-back:** all open-data years (Dallas from 2018, San Antonio from mid-2020).
- **D6. Linkage:** San Antonio by point in parcel, with an address fallback; Dallas by normalised address.
- **D7. San Antonio data — DECIDED (user, 2026-11-19), revised:** no BCAD request. San Antonio uses the current Bexar County parcel layer (§3, §5), and its limits are in §11 and secondary 15. The earlier choice of the same day (wait for the BCAD roll) is withdrawn.
