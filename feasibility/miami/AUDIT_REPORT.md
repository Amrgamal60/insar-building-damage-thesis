# Miami-Dade: data audit (NYC plan §17, step 2)

Audited 2026-10-16 from files downloaded on 2026-10-15/16. The numbers come from `feasibility/audit_hk_miami.py`, saved in `audit/audit_numbers.json`, plus a property-type breakdown (below). Each file's URL, size and SHA-256 are in `audit/download_log.csv`. No outcome–InSAR association has been computed.

## Sources (the supervisor's brief, plus what the check needs)

| Folder in `downloads/` | What it is | Source |
|---|---|---|
| `building_violations` | County building-violation cases: case number, type, folio, address, open and closed dates, point. 77,299 rows, all downloaded. The violator's name is left out. | Miami-Dade Open Data Hub, `BuildingViolation_gdb` (the bulk form of the brief's per-case search viewer) |
| `parcels` | Property Appraiser parcels: folio, site address and city, land use, year built, floors, units, areas, X/Y. 596,677 rows. Owner and mailing fields are left out. | `PaParcelView_gdb` |
| `footprints_folio` | Building footprints with folio, year built, floors, height and municipality. 605,762 polygons. Owner fields are left out. | `BuildingFootprintUBIDFolio_gdb` |
| `municipalities` | Municipal boundaries | `Municipalitypoly_gdb` |
| `zenodo_barrier_insar` | Aziz Zanjani et al. 2024 barrier-island Sentinel-1 point time series (4 XLSX files, MD5 verified, CC BY 4.0) | doi 10.5281/zenodo.12699617 |
| `ntu_insar` | Tay et al. 2022 Miami static velocity map (track 48, CC BY-NC 4.0) | doi 10.21979/N9/GPVX0F |
| `opera_cmr_listing` | NASA CMR list of OPERA DISP-S1 granules over Miami: dates and footprints. The data themselves need an Earthdata login. | CMR |

The brief's papers (Aziz Zanjani et al. 2024; Bardet 2025) are references, not datasets.

## Audit table

| Item | Finding |
|---|---|
| **Labels** | 7,366 "Unsafe Structure" cases from 1993 to 2026 on 4,439 folios; 3,091 are still open. **Since 2017: 6,667 cases on 4,096 folios.** 3,799 folios have their first unsafe case in 2018 or later, which leaves at least 1.5 years of OPERA data before the case. |
| **Dates** | Every case has an open date, so the labels can be dated to the day, unlike Hong Kong. |
| **Coordinates** | Every case has a point. The folio links 6,512 of the 6,667 cases (98%) to a parcel and 5,858 (88%) to a footprint. |
| **Where** | 98% of cases since 2017 are in unincorporated Miami-Dade (folio prefix 30). There are 77 in the City of Miami and almost none elsewhere. **Miami Beach, Surfside, Bal Harbour and Sunny Isles are missing**, because their own building departments handle their unsafe structures. |
| **What kind of property** (cases since 2017, by parcel land use) | Condominium reference folios 2,144; single-family homes 1,247; county-owned 1,039; multifamily 10+ units 369; warehouses 363; retail 211. Median year built is 1967, against 1973 for all parcels. |
| **Timing** | Cases per year: 150 (2017), 201, 417, 368, **1,275 (2021), 1,410 (2022)**, 490, 504, **1,267 (2025)**, 585 (2026 so far). The 2021–22 jump follows the Surfside collapse (June 2021) and the recertification enforcement after it. The many condo reference folios fit that. The data have no case subtype, so how many cases are administrative (for example, an overdue 40-year recertification) and how many are physical defects is **unknown**. |
| **InSAR type** | (a) **OPERA DISP-S1 frame 12638:** a displacement time series of 254 granules with 255 dates, July 2016 to February 2026. Its footprint covers the whole county. (b) **Zenodo barrier-island series:** points with full time series, 2016–2023 (2,618 north + 16,401 south points) and 2019–2023 (3,473 + 20,277). (c) **Tay et al.:** a static map of central Miami only. |
| **Years of InSAR before labels** | OPERA: 0.5 to 9.5 years, depending on the case date (it starts July 2016). For cases from 2021 on, 4.5 years or more. |
| **Label–InSAR overlap** | **OPERA: all 6,667 cases since 2017 lie inside the frame footprint.** Whether each case has coherent pixels can only be checked once the data are downloaded. **Zenodo barrier-island series: 3 cases**, because the cases are not on the barrier islands. **Tay et al. map:** 53 cases on a valid pixel (146 within one pixel). |
| **Building layers** | Parcels: 517,516 of 596,677 have a year built (87%). Footprints: 593,590 have a folio. Land use, floors, units and areas come from the parcels; height comes from the footprints. |

## Go/no-go check (§17 step 2)

**Passes.**
- **Footprint:** all 6,667 unsafe-structure cases since 2017 (4,096 folios) lie inside OPERA DISP-S1 coverage, far above 100.
- **Valid pixels (2026-10-16):** after the OPERA download (254 granules, `audit/opera_coverage.json`, `feasibility/audit_miami_opera.py`), **6,527 cases on 4,034 folios** have a valid 30 m pixel in at least 80% of granules. Valid means finite displacement with recommended_mask = 1. 6,266 cases are valid in every granule. Median temporal coherence at the cases is 0.98.

## Assessment

- **Miami-Dade stays as the second case, but its InSAR source changes.** The brief's barrier-island series does not overlap the outcome data (3 cases). The study must use OPERA DISP-S1 over mainland unincorporated Miami-Dade, the same product and code path as NYC.
- **Strengths:** many dated labels, exact folio linkage, building age and use, and an InSAR time series of up to 9.5 years before each case.
- **Main risk: what the label means.** "Unsafe Structure" here mixes condominium recertification enforcement after Surfside, abandoned or fire-damaged houses and county-owned property. Much of this has nothing to do with ground motion. Two things are needed before freezing a plan:
  - a manual check of a random sample of cases in the county's per-case viewer, to see which are physical defects and which are administrative;
  - possibly limiting the analysis to case years, or folio types, less driven by the post-2021 recertification wave.
- **Confounding:** building age drives both recertification (at 40 years) and these cases, so it must be in the baseline, as in NYC.

## OPERA download (done 2026-10-16)

- **Files:** `downloads/opera_disp/` holds 254 granules of frame 12638 (2016-07 to 2026-02), clipped to lon −80.56 to −80.11 and lat 25.32 to 25.99, which is 2,466 × 1,518 pixels at 30 m. Total 11 GB. Hashes are in `MANIFEST.sha256`.
- **How:** `feasibility/download_miami_opera.sh`, using opera-utils 0.25.8 in conda env `opera`, rebuilt from `nyc/out/checkpoint2/LOCK_opera.txt`.
- **Reference points:** each reference date has its own. Only the 2017-11-21 one (full-frame row 2784, col 6546) lies outside the subset. Its 15 granules get 11 × 11 windows in `downloads/opera_refpoint/` (`feasibility/download_miami_refpoint.py`), as in NYC. All 15 were fetched on 2026-10-16 (hashes in `MANIFEST.sha256`). As in NYC, the reference pixel itself has label 0, no displacement and recommended_mask 0 in every granule. The other 120 pixels of each window are all valid and all carry label 1, so the reference point sits inside one uniform component. Any rule that compares labels with "the label at the reference point" must therefore be written as in NYC deviation 1 (the component around it), not read literally.
