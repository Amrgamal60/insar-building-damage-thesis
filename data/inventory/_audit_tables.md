## 1. Sample size at each stage

| Stage | Count |
|---|---|
| Workbook data rows (all Egypt) | 661 |
| Rows whose governorate is Alexandria | 184 |
| Unique events (multi-building incidents merged) | 173 |
|   of which flagged as possible duplicates of another event | 11 |
| Events located at street/intersection level, exact (A) | 91 |
| Events located at street level incl. flagged matches (A+B) | 107 |
|   of which the street comes from Overture place addresses, not OSM | 2 |
| Events located only to landmark/neighbourhood (C) | 25 |
| Events with street name matching several separate streets (B ambiguous, no coordinates) | 11 |
| Events with district only / no location (D, E) | 30 |

Record-level location categories: A_street 90, C_neighbourhood 28, D_district_only 24, B_street_review 16, B_street_ambiguous 11, E_unlocated 7, A_intersection 5, B_street_overture 2, C_landmark 1.

## 2. Positive cells at candidate grid resolutions

A cell is positive if an event's assigned point falls in it. *Shifted* uses a grid offset by half a cell in x and y. *Events in one cell* is the share of events whose whole matched OSM geometry (street segment, intersection, polygon) lies inside a single cell, i.e. the cell assignment does not depend on where along the street the building is.

| Location set | Cell (m) | Events | Positive cells | Positive cells (shifted) | Events in one cell (%) | Median cells touched | Events touching >4 cells (%) |
|---|---|---|---|---|---|---|---|
| A (street/intersection, exact) | 100 | 91 | 80 | 81 | 9.9 | 4 | 44 |
| A (street/intersection, exact) | 200 | 91 | 72 | 72 | 18.7 | 2 | 20.9 |
| A (street/intersection, exact) | 250 | 91 | 70 | 65 | 17.6 | 2 | 17.6 |
| A+B (adds flagged street matches) | 100 | 107 | 91 | 93 | 10.3 | 4 | 45.8 |
| A+B (adds flagged street matches) | 200 | 107 | 80 | 80 | 17.8 | 3 | 21.5 |
| A+B (adds flagged street matches) | 250 | 107 | 77 | 72 | 16.8 | 2 | 16.8 |
| A+B+C (adds landmark/neighbourhood; reference only) | 100 | 132 | 110 | 112 | 11.4 | 5 | 51.5 |
| A+B+C (adds landmark/neighbourhood; reference only) | 200 | 132 | 96 | 99 | 17.4 | 3 | 31.1 |
| A+B+C (adds landmark/neighbourhood; reference only) | 250 | 132 | 94 | 87 | 16.7 | 3 | 27.3 |

### 2b. Effect of the event definition (location set A+B)

| Event definition | Events | Positive cells @100 m | Positive cells @200 m | Positive cells @250 m |
|---|---|---|---|---|
| all events | 107 | 91 | 80 | 77 |
| excl. external accidents (gas, fire, vehicle, factory) | 105 | 90 | 79 | 76 |
| excl. accidents and building/demolition works | 94 | 79 | 69 | 66 |
| structural only (total + partial_structural) | 74 | 68 | 60 | 56 |
| structural, excl. external accidents (≈ Mohamadi et al. 2020) | 72 | 67 | 59 | 55 |
| total collapse only | 25 | 22 | 22 | 21 |

## 3. Distribution across police districts (qism)

| qism | district | records | events | located_AB | located % | pos_cells_200m |
|---|---|---|---|---|---|---|
| كرموز | Karmouz | 32 | 29 | 26 | 90 | 16 |
| محرم بك | Moharam Bek | 20 | 19 | 13 | 68 | 12 |
| الجمرك | El Gomrok | 16 | 16 | 13 | 81 | 9 |
| سيدي جابر | Sidi Gaber | 13 | 13 | 8 | 62 | 8 |
| اللبان | El Labban | 12 | 12 | 8 | 67 | 6 |
| الدخيلة | El Dekheila | 14 | 11 | 1 | 9 | 1 |
| أول المنتزة | Awal El Montaza | 11 | 11 | 4 | 36 | 4 |
| أول الرمل | Awal El Raml | 10 | 10 | 5 | 50 | 4 |
| مينا البصل | Mina El-Basal | 12 | 10 | 4 | 40 | 2 |
| ثان الرمل | Thani El Raml | 9 | 9 | 6 | 67 | 4 |
| العطارين | Al Attarin | 8 | 8 | 6 | 75 | 5 |
| المنشية | El Manshiya | 8 | 8 | 6 | 75 | 5 |
| باب شرقي | Bab Sharqi | 9 | 8 | 6 | 75 | 5 |
| غير محدد | unspecified | 7 | 6 | 0 | 0 | 0 |
| أول العامرية | Awal El Amreya | 2 | 2 | 0 | 0 | 0 |
| ثان المنتزة | Thani El Montaza | 1 | 1 | 1 | 100 | 1 |

Events by year:

| year | located A+B | not located | total |
|---|---|---|---|
| 2014 | 14 | 16 | 30 |
| 2015 | 58 | 34 | 92 |
| 2016 | 35 | 16 | 51 |

## 4. Built-up background (comparison cells)

Study area = union of the 14 CAPMAS/geoBoundaries ADM2 polygons that match the inventory's districts (1138 km²). Built-up = cell containing ≥1 Google Open Buildings v3 footprint centroid with confidence ≥ 0.70 (446,895 footprints in the AOI bbox).

| Cell (m) | Built-up cells | Positive cells (A+B) | Positive cells that are built-up | Positive : background ratio | Built-up cells with ≥1 InSAR point (%) | Positive cells with ≥1 InSAR point (%) | Median InSAR points per covered built-up cell |
|---|---|---|---|---|---|---|---|
| 100 | 19464 | 91 | 89 | 1 : 218 | 31.5 | 69.2 | 1 |
| 200 | 6295 | 80 | 80 | 1 : 78 | 40.3 | 88.8 | 4 |
| 250 | 4327 | 77 | 76 | 1 : 56 | 42.5 | 85.7 | 5 |

### 4b. Background restricted to areas already settled by 2015

Google Open Buildings v3 is mapped from recent imagery, so the built-up mask may include cells developed after the 2014–2016 inventory. *Settled* = the cell contains the centre of at least one 30 m WSF Evolution pixel first detected as settlement in 1985–2015 (DLR; input-data consistency score 6 of 6 across the city). Built-up cells without one are *not identified as settled by the historical filter*; that does not establish they were developed after 2015. The proposed comparison set is built-up **and** settled.

| Cell (m) | Built-up cells | Built-up and settled by 2015 | Built-up cells not identified as settled (%) | Positive cells (A+B) in the set | Positive : background ratio | Set cells with ≥1 InSAR point (%) |
|---|---|---|---|---|---|---|
| 100 | 19464 | 15428 | 20.7 | 89 | 1 : 172 | 38.2 |
| 200 | 6295 | 4745 | 24.6 | 80 | 1 : 58 | 51.4 |
| 250 | 4327 | 3300 | 23.7 | 76 | 1 : 42 | 53.7 |

## 5. InSAR data available: dates and coverage

**Shirzaei et al. vertical land motion (VT Figshare 10.7294/25864435, CC0).** 75,931 points in the file, 28,841 inside the study area. VLM (IGS14) inside the study area: median -3.6 mm/yr, 5th–95th percentile -7.1 to -1.9 mm/yr; median reported standard deviation 0.1 mm/yr. Distinct coordinate pairs: 58,182 (the file repeats some points). **The observation period is not stated in the dataset metadata or README**; it is a single mean velocity per point, not a time series. Until the period is confirmed (associated paper or corresponding author), it cannot be claimed to precede the 2014–2016 events.

| Frame | Pass | Epochs | First | Last | Interferograms | Study area covered (%) | Events with 0 prior epochs | Events with ≥1 yr prior data | Events with ≥2 yr prior data | Median prior epochs per event |
|---|---|---|---|---|---|---|---|---|---|---|
| 065D_05935_131108 | descending | 228 | 2014-10-10 | 2023-08-24 | 1153 | 100 | 24 | 110 | 11 | 31 |
| 131A_05957_110910 | ascending | 411 | 2014-11-07 | 2023-09-09 | 2199 | 100 | 28 | 72 | 8 | 21 |

Only the LiCSAR frame metadata was downloaded (E/N/U unit vectors, DEM heights, land mask, baselines, `vlos_eur`). `vlos_eur` is nearly constant over the city (≈ +14 mm/yr descending, ≈ −19 mm/yr ascending, σ ≈ 0.2 mm/yr): it is the plate-motion reference layer, not measured deformation. A deformation time series requires downloading the interferograms and running LiCSBAS (or HyP3/MintPy); none has been produced.


_Review queue: 73 records need a human decision → `review_queue.csv`._
