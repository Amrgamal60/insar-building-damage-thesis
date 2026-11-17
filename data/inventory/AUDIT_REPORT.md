# Alexandria collapse inventory: feasibility audit

**Date:** 2026-09-29 (first version 2026-09-28) · **Scope:** audit only. The inventory was not expanded and no model was trained.
**Source:** OSF 98pyu (Fouad et al. 2025), `Figure 2/Recorded Incidents of Building Collapses in Egypt Over Three Years 2014-2015-2016 from Daftar Ahwal.xlsx`.
**Reproduce:** run `.venv/bin/python scripts/<name>.py` for `00_clip_layers`, `01_build_inventory`, `02_geocode_osm`, `03_audit_report`, `04_layer_check` and `05_map_events`, in that order.

**Changes on 2026-09-29:**
- **Overture places as a second gazetteer.** They are used only for records that OSM could not place, and they add 2 street-level events. Positive cells are unchanged at 200 and 250 m.
- **A background restricted to cells identified as settled by 2015** (WSF Evolution), in §4b.
- **An event definition close to Mohamadi et al. (2020)**, in §2b.
- **A descriptive check of candidate predictor layers**, in the appendix.
- **A restricted pilot** (target rule, 250 m cells, baseline with and without velocity) in `data/pilot/PILOT_REPORT.md`.

## Headline findings

1. **The row count is reconciled.** 184 Alexandria rows = 182 with a full date + 1 dated only by month ("شهر يناير 2014") + 1 dated by a range ("01-05/06/2014"). Both are 2014 events, so the years are 2014: 31, 2015: 95, 2016: 58. The earlier "29 + 95 + 58 = 182" came from my first quick look, which dropped the two non-standard dates.
2. **Rows → events → located events → positive cells** (using the location set A+B):
   - 184 rows become 173 events. Nine incidents involved 2–3 buildings; 11 events are flagged as possible duplicates.
   - 107 events can be placed at street level. 91 of them have no flag, and 2 are placed from Overture place addresses.
   - That gives **91 / 80 / 77 positive cells at 100 / 200 / 250 m**.
   - Keeping only structural collapses (dropping balconies and single-room ceilings) leaves 74 events and 60 cells at 200 m.
   - Also dropping external accidents leaves 72 events and 59 cells. This is the closest match to Mohamadi et al. (2020).
   - Total collapses alone: 25 events.
3. **Street-level location does not pin an event to a single 100 m cell.**
   - The matched street is usually longer than a cell: the median matched extent is 127 m, and 11% of matches exceed 500 m.
   - Only 10–19% of located events fall entirely inside one cell. At 200 m, the median event touches 2–3 cells.
   - The half-cell shifted grid gives similar positive-cell counts (A+B: 93 / 80 / 72 against 91 / 80 / 77), but each individual event's cell is not stable.
   - 79 located records name a building number in the article. OSM Alexandria has almost no house numbers, so those numbers can't narrow the location without another source. The Bibliotheca Alexandrina *Atlas of Alexandria* has been requested.
4. **Events are spatially concentrated.**
   - 76 of the 107 located events are in 7 central districts: Karmouz, Moharam Bek, El Gomrok, El Labban, Attarin, Manshiya and Mina El-Basal.
   - Location success is poor in El Dekheila (1 of 11 events) and Awal El Montaza (4 of 11), where OSM street names are sparse or repeat many times.
   - The comparison class is large at 200 m: about 1 positive per 78 built-up background cells, or 1 per 58 once cells not identified as settled by the historical filter are dropped (§4b).
5. **A quarter of the built-up cells are not identified as settled by the historical filter.**
   - The built-up mask comes from Google Open Buildings v3, which is mapped from recent imagery.
   - 25% of built-up 200 m cells hold no WSF Evolution pixel first mapped as settlement in 1985–2015 (21% at 100 m, 24% at 250 m). That does not establish they were developed after 2015; WSF can miss sparse settlement.
   - Every built-up positive cell passes the filter. The proposed comparison set is therefore built-up **and** settled: 4,745 cells at 200 m, 4,665 of them background.
6. **InSAR: what exists and when.**
   - **Shirzaei et al. VLM** (the only deformation product in hand) gives one mean velocity per point, not a time series, and **the observation period is not documented**.
   - It covers 40% of built-up 200 m cells (51% of the settled set), but 89% of positive cells. Having InSAR points is itself a marker of the dense core.
   - **Sentinel-1 via LiCSAR:** the two frames fully cover the city from Oct/Nov 2014 to Aug/Sep 2023. Relative to the descending frame, 24 events happened before the first acquisition and only 11 events have 2 or more years of earlier data.
   - A **time-split validation with InSAR data from before each event is therefore not possible on the 2014–2016 inventory**. It would need later events (2017+) and a LiCSBAS time series, neither of which exists yet.

## How the inventory was built

- **Row IDs:** each preserved row has `record_id = DA-R<Excel row>`. All 36 original columns are kept verbatim in `daftar_ahwal_alexandria_original.csv`.
- **Excluded rows:** 6 rows mention Alexandria only as a road name in another governorate and are excluded, listed in `excluded_non_alexandria_mentions.csv`.
- **Event vs publication date:** the event date comes from the workbook's own date column. `pub_date_from_url` is taken from source links where the URL carries a date (113 records; youm7 and masrawy URLs).
  - The median gap between event and publication is 0 days.
  - For 9 records the only dated source is a retrospective article published 1–12 months later (e.g. youm7's year-end summary), flagged as `source_is_retrospective`.
  - 36 records share their article text with other records (summary articles). Those texts are not used for geocoding.
- **Severity** (`severity_class`, mapping in `severity_mapping.csv`, editable):
  - `total` = whole building
  - `partial_structural` = parts of the building, a staircase, roof or facade, or multiple elements
  - `partial_element` = a balcony, a single room ceiling, a floor or a single wall
  - One record (DA-R138) says the collapse was total ("كلي") while its collapsed part is a room ceiling ("سقف غرفة"). It is flagged.
- **Cause** (`cause_group`, mapping in `cause_mapping.csv`): kept as inventory metadata only, not as a predictor. It is used below only to show how the sample size changes under different event definitions.
- **Event grouping and duplicates:**
  - Rows with the same date, district and address (ignoring the "first/second/third building" suffix) form one event.
  - Flags, which never delete anything:
    - **STRONG:** same street within 3 days.
    - **MEDIUM:** same date with an identical injury count at a different address (DA-R188 / DA-R189), or a source article dated on another event's date in the same area (the three Gleem total collapses DA-R189 / R229 / R245).
    - **WEAK:** same date or neighbourhood with a different street.
    - **Ordinal:** DA-R590 / R591 are both labelled "second building".

## How geocoding works

- **Data sources:**
  - **OSM:** the local extract is Geofabrik `egypt-latest.osm.pbf`, dated 2026-09-28, with 43,666 road segments in the city area, 14,857 of them named.
  - **Overture Maps places** (release 2026-09-23.0, CDLA-Permissive-2.0): 31,797 places in the city window, 19,118 of them with an Arabic free-form address. Used only as a fallback (see below).
  - **District polygons** are geoBoundaries EGY ADM2 (CAPMAS / OCHA 2020), used buffered by 300 m.
  - OSM has no police-district boundaries for Alexandria.
- **No coordinates are typed by hand.** Every point comes from a matched OSM feature or Overture place. The evidence is stored as JSON in `inventory_geocoded.csv`: parsed address, matched names, OSM or Overture ids, number of separate matches, fuzzy suggestions, and streets named in the article.
- **Name matching:** Arabic spellings are normalized (hamza/alef, ya/alef maqsura, ta marbuta, "ال", ابن/بن), and the street-type word (شارع, حارة …) is set aside.
- **Order of attempts:**
  1. an intersection of two streets;
  2. an exact street match near the named neighbourhood, else inside the district;
  3. the article's spelling of the same street;
  4. the same name with an honorific added or removed (الشيخ, الدكتور, سيدي, باشا …), flagged as B;
  5. a fuzzy match (≥ 90), flagged as B;
  6. a landmark;
  7. a neighbourhood;
  8. otherwise the district only, with no coordinates;
  9. only if steps 1–8 give no street-level result, Overture places (rules below). OSM results are never changed by Overture.
- **Wrong same-name matches are rejected.** A street with the same name elsewhere in the city (e.g. matches 16–23 km away for "ش الطيار" and "ش الكورنيش") only counts if it is a single street within 1.5 km of the reported district.
- **Repeated names get no coordinates.** A name that matches several separate streets in the district, with nothing to choose between them, is `B_street_ambiguous`.
- **`matched_extent_m`** is the largest distance from the assigned point to the matched OSM geometry. It is a property of the matched street or polygon, not a geocoder accuracy score. It is left empty where no extent is known: station, square and place *points*, and Overture places.
- **Overture fallback rules.** Overture addresses are free text entered by businesses and users, so the rules are strict:
  - **Street missing from OSM:** at least 2 places in the district whose address names the street and that form one cluster (gaps ≤ 300 m), or 1 place whose address also names the record's neighbourhood. The assigned point is an actual place location. A longer name that only starts with the record's street (e.g. "ش الطيار" vs "ش الطيار أحمد سعود") is a review candidate, not a match.
  - **Neighbourhood missing from OSM:** at least 3 places whose address names it, at least two-thirds of them in one cluster. It may also pick one of several same-named OSM streets, flagged B.
  - **Landmark:** the place name must match, within 300 m of the named neighbourhood.
  - **Result:**
    - 2 records (DA-R251 and DA-R318, two separate events) moved from C to `B_street_overture`. Both rest on a single place, a church at "154 شارع الرند - غيط العنب".
    - 2 district-only records gained a neighbourhood: Wingate and Smouha.
    - The landmarks مسجد القويري (Hanoville) and شركة الشمعدان (Um Zeghiw) were found 1.7 km and 4.8 km from their named neighbourhoods, so they were not used.
    - 22 of the 24 streets missing from OSM are missing from Overture too. For 5 records, Overture has partial candidates, listed in the review queue.

| Category | Meaning | Coordinates | Records |
|---|---|---|---|
| A_intersection | two named streets meet (≤ 25 m) in the district or neighbourhood | yes | 5 |
| A_street | one exact street name, one spatial cluster, in the district or next to the named neighbourhood | yes | 90 |
| B_street_review | one cluster, but an honorific / fuzzy / article-only match, outside the district polygon, or the article names a different street | yes, flagged | 16 |
| B_street_overture | street not in OSM, placed from Overture places whose address names it | yes, flagged | 2 |
| B_street_ambiguous | the name matches several separate streets | no | 11 |
| C_landmark / C_neighbourhood | only a landmark or neighbourhood matched | yes (coarse) | 1 / 28 |
| D_district_only / E_unlocated | district only / nothing | no | 24 / 7 |

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

## Decisions needed before any modelling

1. **Event definition.** Which severities and causes count as a positive? §2b shows how the sample changes. Mohamadi et al. (2020) dropped fire, explosion and car accidents, as well as their smallest collapse level (a room ceiling, balcony or wall). The closest row here is "structural, excl. external accidents": 72 events and 59 cells at 200 m.
2. **Primary resolution.** At 100 m most events touch several cells, so a 100 m cell label mostly reflects which point along the street was assigned. The location audit supports **200–250 m as primary**, with 100 m only as a sensitivity check. Alternatively, label a cell by the fraction of the matched street segment that falls in it.
3. **Comparison set.** Use built-up cells identified as settled by the historical filter (§4b) as the background, and keep all built-up cells as a sensitivity check.
4. **Review queue** (`review_queue.csv`, 73 records):
   - 16 B matches and 2 Overture-placed streets to confirm, and 11 ambiguous streets.
   - 22 streets missing from both OSM and Overture. Overture has partial candidates for 5 of these records.
   - 12 duplicate flags and 9 retrospective-only sources.
   - 3 Overture landmarks rejected for distance.
   - The individual flags DA-R138, DA-R136 and DA-R571.

   The missing streets need the Bibliotheca Alexandrina atlas or a manual lookup (Google Maps / Wikimapia); otherwise they are dropped.
5. **InSAR product and period.** The Shirzaei group was asked on 2026-09-29 for the VLM observation window. If it starts after 2016, it can only support a retrospective susceptibility map, not a claim that the deformation came first.
6. **InSAR coverage.** At 200 m, InSAR points exist in 89% of positive cells but only 51% of the settled background. Compare InSAR features only among cells that have InSAR points. Otherwise a model can learn that "has InSAR data" means "dense core".
7. **Temporal validation.** It needs events after 2016 *and* a LiCSBAS time series. Mohamadi et al.'s GPS-located inventory (255 collapses, January 2001 – May 2019, from district offices) was requested from the authors on 2026-09-29. If they share it, its 2017–2019 events have Sentinel-1 data from before each collapse.

## Limitations

- **News-derived:** collapses with casualties and in the historic core are likely over-reported, and Dekheila, Amreya and Montaza are under-located.
- **Possible missing events.** Mohamadi et al.'s official district records list 17 whole-building collapses in 2015–16 (their Tables 2–3).
  - Only 2 of these fall on a date that also has a Daftar Ahwal event. By contrast, all 24 of their listed partial collapses (levels 2–3) do.
  - So some whole-building collapses may be missing from the Daftar Ahwal. This date-only comparison does not establish how many, or that most are missing.
  - Confirming this needs their addresses.
- **District polygons** (CAPMAS 2020) may not match 2014–2016 police districts exactly. Three records are 0.3–1 km outside the reported district, and DA-R136 (Azarita) is 6.9 km away.
- **Name checks, not ground checks.** OSM names were checked against the reported district and neighbourhood, not against the ground. All A and B points should be spot-checked on imagery before use.
- **Overture addresses** are entered by businesses and users. The two Overture-placed events rest on one place and must be checked.
- "No recorded collapse" in a background cell does not mean the cell is safe.

## Files (`data/inventory/`)

| File | Content |
|---|---|
| `daftar_ahwal_alexandria_original.csv` | the 184 source rows, all original columns, plus `record_id` |
| `excluded_non_alexandria_mentions.csv` | 6 non-Alexandria rows that mention the name |
| `inventory_records.csv` | derived fields: dates, severity, cause group, event_id, duplicate flags, article address snippets |
| `inventory_geocoded.csv` / `.gpkg` | records + location category, coordinates (UTM 36N and WGS84), extent, evidence JSON |
| `geocode_auto_matched_features.gpkg` | the matched OSM geometry or Overture places behind each located record |
| `events.csv` | one row per event (best location, most severe part, primary cause) |
| `review_queue.csv` | records needing a human decision, with reasons and source links |
| `severity_mapping.csv`, `cause_mapping.csv` | editable class definitions |
| `geocoded_events_map.png` | sanity-check map (`scripts/05_map_events.py`) |

The layer check in the appendix is `data/interim/layer_check_200m.csv` (`scripts/04_layer_check.py`).

## Appendix: candidate predictor layers (descriptive only, no model)

Each layer is compared between the 80 positive 200 m cells (all A+B events) and the background using a univariate AUC (Mann-Whitney). The final pilot target has its own table in `data/pilot/PILOT_REPORT.md`. 0.5 means no difference. Below 0.5 means lower values in collapse cells, so 0.24 separates as well as 0.76. **This is not a model score.** Positives cluster in the historic core, so any layer that tracks "old dense core vs the rest" separates well here without adding information beyond location.

| Layer | Built-up cells covered (%) | Median, collapse cells | Median, all built-up background | AUC | Median, settled background | AUC, settled background |
|---|---|---|---|---|---|---|
| WSF first settled year (min) | 77.2 | 1985 | 1985 | 0.42 | 1985 | 0.42 |
| WSF median settled year | 77.2 | 1985 | 1985 | 0.29 | 1985 | 0.29 |
| WSF IDC score (mode) | 100 | 6 | 6 | 0.50 | 6 | 0.50 |
| GHS-BUILT-S 1975 (m² per 100 m px) | 99.8 | 4,351 | 281 | 0.88 | 1,131 | 0.84 |
| GHS-BUILT-S 2015 (m² per 100 m px) | 99.8 | 4,356 | 2,052 | 0.84 | 3,044 | 0.79 |
| GHS-BUILT-S growth 1975-2015 (m²) | 99.8 | 0 | 412 | 0.18 | 726 | 0.15 |
| GHS-BUILT-H ANBH 2018 (m) | 98.3 | 19.14 | 8.82 | 0.85 | 11.29 | 0.80 |
| GHS-AGE epoch class (mode, 1 = <1975) | 98.3 | 1 | 4 | 0.24 | 1 | 0.27 |
| GSW ever water 1984-2021 (share of cell) | 100 | 0 | 0 | 0.39 | 0 | 0.39 |
| GSW water lost 1984-2021 (share of cell) | 100 | 0 | 0 | 0.46 | 0 | 0.45 |
| Nile delta VLM 2014-2023 (cm/yr) | 96.5 | -0.51 | -0.70 | 0.75 | -0.63 | 0.69 |
| Shirzaei VLM mean (cm/yr) | 40.8 | -0.34 | -0.31 | 0.45 | -0.31 | 0.44 |

- **Old-core markers separate best.** These are built-up surface in 1975 and 2015, building height, and GHS-AGE. The settled background lowers their AUCs by 0.03–0.05.
- **WSF years cannot separate cells inside the core.** Every positive cell was already settled in 1985, WSF's first year.
- **The Nile-delta VLM separates in the unexpected direction.** Collapse cells subside *less* than the background (−5.1 vs −7.0 mm/yr).
- **Shirzaei VLM shows no difference.**
- **Surface water shows almost no signal.** Almost no positive cell was ever water.
- **GHS-OBAT is not listed**, because its height and age attributes are zonal statistics of GHS-BUILT-H and GHS-AGE.
