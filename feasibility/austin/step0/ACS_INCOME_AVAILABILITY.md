# ACS 2011–2015 median household income availability, Travis County

Pre-freeze check for block-group median household income (ACS table B19013) on the Austin detached-house population. Aggregate counts only.

## Source

The Census Data API was not usable anonymously. A request for Travis County block groups returned a redirect to `https://api.census.gov/data/missing_key.html` (final HTTP 200, body title Missing Key). A tract request timed out (curl exit 28, no body). No API key was used.

Estimates are from the 2015 ACS 5-year Summary File, Texas tracts and block groups archive `Texas_Tracts_Block_Groups_Only.zip`. Table B19013 is sequence `0059`, start position 177, in `ACS_5yr_Seq_Table_Number_Lookup.txt`. That position is the estimate `e20155tx0059000.txt` and the margin `m20155tx0059000.txt`, joined to `g20155tx.csv` on `LOGRECNO`. The table title in the lookup is median household income in the past 12 months in 2015 inflation-adjusted dollars. Block-group polygons are the 2015 TIGER/Line file `tl_2015_48_bg.zip`, restricted to county 453.

Geography checks while reading the summary file: GEOID suffix matched state+county+tract+block group on every Travis tract and block group; names begin with `Census Tract` or `Block Group` as expected for summary levels 140 and 150. Summary level 140/150 is identified from those names in `g20155tx.csv`. The technical documentation states that 5-year estimates are published for census tracts and block groups; the numeric summary-level list is Appendix B, which was not transcribed here.

## What was counted as a valid median

A valid median is an integer dollar amount that is not a jam value. Empty cells and `.` are missing. Section 4.2 of the 2015 ACS Summary File Technical Documentation (`2015_SummaryFile_Tech_Doc.pdf`) defines these summary-file annotations:

- Empty cell: the estimate is unavailable (geographic filtering, coefficient-of-variation filtering, or Disclosure Review Board removal).
- `.`: no sample observations, or too few sample observations. In the margin-of-error file, `.` can also mean the margin is unavailable because the median was replaced by a jam value.
- Margin of error `0`: the estimate is controlled (the summary-file equivalent of the American FactFinder `*****` symbol). It is not treated as a sampling margin of zero, so it is left out of the relative-margin distribution.
- Jam values for income: `2499` means 2,500 or less; `200001` means 200,000 or more; `250001` means 250,000 or more. These are not calculated dollar medians.

Data API numeric codes in the summary-file cells: -666666666 block groups 0, tracts 0; -999999999 block groups 0, tracts 0; -222222222 block groups 0, tracts 0; -333333333 block groups 0, tracts 0; -555555555 block groups 0, tracts 0. The retrieved 2015 summary-file technical documentation does not define these codes. Their meanings are **UNVERIFIED**.

Relative margin of error is the published margin divided by the estimate. It is computed only where the estimate is a valid median greater than zero and the margin is a positive integer. Percentiles use the linear sample quantile.

## Block groups

ACS summary-file block groups in Travis County (summary level 150): **580**.
TIGER/Line 2015 block groups in Travis County: **580**. GEOID overlap with the summary file: 580. TIGER only: 0. Summary file only: 0.
Valid median: **568** (97.93% coverage).

| Estimate cell | Count | Meaning |
|---|---:|---|
| valid median | 568 | Integer dollar amount, not a jam value |
| `blank` | 8 | Missing value (empty cell): estimate unavailable because of geographic filtering, coefficient-of-variation filtering, or Disclosure Review Board removal (tech doc section 4.2). |
| `dot` | 4 | Dot '.': no sample observations or too few sample observations. In a margin-of-error file, also used when the margin is unavailable because the median was replaced by a jam value (tech doc section 4.2). |

Relative margin of error on 568 block groups with a defined ratio: median **0.2637**, 75th percentile **0.3600**, 90th percentile **0.5350**.
Block groups with relative margin of error above 0.5: **67**.

## Tracts

ACS summary-file census tracts in Travis County (summary level 140): **218**.
Valid median: **215** (98.62% coverage).

| Estimate cell | Count | Meaning |
|---|---:|---|
| valid median | 215 | Integer dollar amount, not a jam value |
| `dot` | 3 | Dot '.': no sample observations or too few sample observations. In a margin-of-error file, also used when the margin is unavailable because the median was replaced by a jam value (tech doc section 4.2). |

Relative margin of error on 215 tracts with a defined ratio: median **0.1527**, 75th percentile **0.1987**, 90th percentile **0.2652**.
Tracts with relative margin of error above 0.5: **1**.

## Detached houses

Parcel file geometry is Arrow extension `geoarrow.wkb` with geo-metadata encoding `WKB` and CRS EPSG:32614 (`EPSG:32614`), which matches the step-0 statement of EPSG:32614. Rows in the diagnostic file: 146857. `imprv_type_cd` value `01`: **144458**.

Each type `01` polygon centroid was formed in EPSG:32614. 2015 TIGER block groups were transformed from their native CRS to EPSG:32614 and the centroid was assigned with a within test. Centroids on a boundary that meet exactly one block group were assigned to that block group. The tract is the first 11 digits of the block-group GEOID.

Empty parcel geometries: 0. Invalid parcel geometries: 0. Centroids assigned to a block group: 144428, of which 0 were boundary assignments.

Of the 144458 detached houses:

- Valid block-group median: **143613** (99.42%).
- Block-group median missing (empty, `.`, or no summary-file value) and tract median valid: **806** (0.56%).
- Neither: **39** (0.03%).

The neither count splits into exclusive parts: unassigned 30, bg_jam 0, bg_missing_tract_not_valid 9, bg_other 0, boundary_ambiguous 0, within_multiple_block_groups 0.

Restricted to the 10969 detached houses in block groups whose relative margin of error is above 0.5 (7.59% of 144458): valid block-group median **10969**, tract fallback **0**, neither **0**. A relative margin above 0.5 is defined only when the block-group median is a valid positive dollar amount, so this subset sits inside the valid-median group.

## Read checks

GEOID mismatches: 0. Unexpected geography names: 0. Estimate rows with a sequence other than 0059: 0. Margin rows with a sequence other than 0059: 0.
Median of the valid block-group dollar estimates: 61433.5. Median of the valid tract dollar estimates: 60125.0. These are a column check, not a published county median.

