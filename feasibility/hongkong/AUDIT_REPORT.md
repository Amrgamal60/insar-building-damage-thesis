# Hong Kong: data audit (NYC plan §17, steps 2–3)

Audited 2026-10-15 from files downloaded the same day. The numbers come from `feasibility/audit_hk_miami.py` and are saved in `audit/audit_numbers.json`. Each file's URL, size and SHA-256 are in `audit/download_log.csv`. No outcome–InSAR association has been computed.

## Sources (the supervisor's brief, plus companions)

| Folder in `downloads/` | What it is | Source |
|---|---|---|
| `s26_orders` | Buildings with Section 26 dangerous-building Repair Orders issued after 1 May 2023 | data.gov.hk `hk-bd-opendata-s26-order-1` (CSDI WFS) |
| `s26a_orders` | Buildings with Section 26A building-defect Investigation Orders issued after 1 May 2023 | `hk-bd-opendata-s26a-order-1` |
| `s26_cws`, `s26a_cws` | The same orders complied with, withdrawn or superseded (companion datasets, not in the brief) | `-s26-order-2`, `-s26a-order-2` |
| `building_info` | Building information and age records (private buildings), a ZIP holding one CSV | `hk-bd-opendata-building-information` |
| `monthly_digests` | Buildings Department Monthly Digest tables 2.2 (orders issued) and 2.4 (compliance), as monthly counts | static.data.gov.hk |
| `ntu_insar` | Tay et al. 2022, 48 coastal cities: Hong Kong velocity map from ascending track 11 (CC BY-NC 4.0) | doi 10.21979/N9/GPVX0F |
| `s1_listing` | ASF list of Sentinel-1 IW SLC scenes over Kowloon, for planning the time series | ASF search API |

The brief's two papers (Zhang et al. 2025; the Tay et al. paper behind the NTU data) are references, not datasets.

## Audit table

| Item | Finding |
|---|---|
| **Labels** | **S26 Repair Orders:** 1,319 buildings, 1,787 orders. **S26A Investigation Orders:** 80 buildings, 153 orders. 10 buildings have both. **Complied, withdrawn or superseded:** S26, 727 buildings (953 orders); S26A, 63 buildings (68 orders). |
| **Dates** | **No issue date for any order or building.** Each file gives cumulative counts from 1 May 2023 to its last update, 2026-09-07. |
| **Monthly copies (step 3)** | **None found.** The data.gov.hk historical archive keeps other Buildings Department files but no S26 or S26A files, because these are served live from CSDI. The Wayback Machine has no copies either. → §17's fallback applies: "orders by 2026" against InSAR from before 1 May 2023. All InSAR from before the window still precedes every order, so the design remains prospective at the level of the window. |
| **Coordinates** | All 1,319 + 80 order buildings have latitude and longitude (a point per building block). All of them link by block ID to the building records. |
| **Building layer** | 51,354 private building blocks: 45,028 towers and 6,326 podiums. 50,575 (98.5%) have an occupation-permit date (1947 to 2025). Use: residential/composite 40,722, others 4,269, office/commercial 4,072, industrial 2,291. District is given. 2.6% of blocks have an S26 order. |
| **Labels vs buildings** | Order buildings are older: median occupation-permit year 1972, against 1988 for all buildings. Building age will be a strong baseline predictor. Most orders are in the old urban core: Yau Tsim Mong 269, Central & Western 148, Eastern 136, Sham Shui Po 132, Kowloon City 119. |
| **InSAR type** | (a) **Tay et al. 2022:** a static vertical velocity map (~90 m pixels, relative to one reference point), with no time series. Only 32,218 of its 333,304 pixels are valid. (b) **Sentinel-1 for our own time series (§17 step 4):** ascending track 11 has 314 scenes, 225 of them before May 2023; ascending track 113 has 610, 416 before May 2023. Both start in June 2015. Descending coverage is a single scene. |
| **Years of InSAR before labels** | Sentinel-1 gives about 7.9 years (June 2015 to April 2023) before the order window. The Tay et al. map's observation period is given in the paper, not in the files. |
| **Label–InSAR overlap** | Tay et al. map: a valid pixel at 790 of 1,319 S26 buildings (60%), 1,115 within one pixel (85%) and 1,227 within two (93%). For S26A: 41, 68 and 72 of 80. For all buildings: 63%, 83% and 90%. A HyP3 + MintPy time series would need its own coherence check. |
| **Count check** | Monthly Digest table 2.2, May 2023 to July 2026: 1,592 building-repair orders, 212 + 1 + 56 demolition orders and 139 investigation orders. The S26 file's 1,787 orders lie between repair-only and repair + demolition. The exact mapping is unclear, and this does not affect building-level labels. |

## Assessment

- **Hong Kong passes as the main case.** It has about 1,320 labelled buildings out of 51,354, with exact locations, building age, type and use, and Sentinel-1 since 2015.
- **Main weakness: no order dates.** The design is "orders issued May 2023 to Sep 2026" against InSAR up to April 2023. Monthly snapshots from now on (starting with this download) would date future orders. That only helps a later extension.
- **Labels are proxies.** S26 and S26A orders mark buildings judged dangerous or defective, not collapses. The plan must state this (supervisor's clarification, §17).
- **Confounding to plan for:** orders cluster in old dense districts and older buildings. Building age and location must be in the baseline, as in NYC.

## Still to do (needs the user's Earthdata login in `~/.netrc`)

- Submit Sentinel-1 interferograms to ASF HyP3 (track 11 and/or 113, 2015 to April 2023), then build a MintPy time series. This is §17 step 4. Choose the track and the number of jobs before submitting, because jobs use the account's HyP3 credits.
