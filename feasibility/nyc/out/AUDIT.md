# NYC feasibility audit: structural collapses × InSAR

**Date:** 2026-10-07. **Reproduce:** `Alex/.venv/bin/python -I scripts/01_audit_events.py raw out`, run from `feasibility/nyc/`. API answers are cached in `raw/`.

**Verdict:** feasible as an external validation city. 185 clean, lot-located collapse events from 2011 to 2022. Of these, 82 have at least 1 year of OPERA InSAR history before the event, and 45 have at least 3 years. For comparison, the Alexandria pilot has 63 events.

## Event funnel

| Stage | Events |
|---|---|
| Records (OEM `Structural-Collapse` + `Structural-Partial Collapse`) | 459 |
| Events after merging duplicate reports (same address, within 3 days) | 279 |
| … geocoded to an address-level tax lot in the right borough (NYC Geosearch) | 247 |
| … and within 150 m of the OEM point (or no usable OEM point) | 243 |
| … and the lot has a PLUTO record | 243 |
| … and no major works (BIS NB/DM/A1; DOB NOW demolition/foundation/earthwork/excavation) permitted on the lot in the 365 days before | 205 |
| … and no new-building, demolition or excavation permit within 50 m on the same block in the 365 days before | **185** |
| ≥ 1 year of OPERA DISP-S1 history before the event | **82** |
| ≥ 2 years | 63 |
| ≥ 3 years | 45 |

- **By borough (185):** Brooklyn 64, Bronx 44, Queens 33, Manhattan 30, Staten Island 14.
- **By year:** 15–21 a year, except 10 in 2017 and 6 in 2022 (a partial year).
- **Partial collapses only:** 73 of 185 events.
- **Location quality:** the geocoded lot is a median 24 m from the OEM point (90th percentile 59 m). In Alexandria the median matched street was 127 m long, so NYC events are placed at building level.
- **Building age at the event (PLUTO):** median 91 years; 76% are at least 80 years old (n = 145). Age will be a strong baseline feature.

## InSAR available

| Product | Coverage | Form | Notes |
|---|---|---|---|
| [OPERA DISP-S1](https://www.earthdata.nasa.gov/data/catalog/asf-opera-l3-disp-s1-v1-1), frame F08622 | 2016-07-16 to 2025-11, 269 granules over all five boroughs | 30 m displacement time series, line of sight | One geometry only (track 33, ascending), so no vertical/east-west split. Free Earthdata login needed. |
| [Ohenhen et al. 2025 US metropolises](https://doi.org/10.7294/27606942) (`newYork_VLM.csv`, 54 MB) | 2015–2021 | Mean vertical velocity points | CC0. The NYC analogue of the Shirzaei product in Alexandria. |
| LiCSAR | Frame 033A_08614_131313 only | — | One epoch on CEDA, so not usable. |
| Descending tracks 113 and 11 | ~10 acquisitions each | — | Too sparse. |

## Limits found

- **No cause field.** OEM keeps fire collapses (`Fire-Collapse`), construction accidents and demolition as separate types, but the cause of a `Structural-Collapse` is not recorded. The permit filters are a proxy and miss some cases. Example: 331 Madison Ave (2015 partial collapse) was demolished for a tower whose lot was merged later, so its permits sit under another BBL.
- **PLUTO is the current release.** For 39 events the building has since been replaced, or the lot is now vacant (22 class-V lots). Their baseline attributes need an archived PLUTO from before the event.
- **The dataset is frozen.** It stops in August 2022; no newer OEM incidents are published.
- **Single viewing geometry.** The Alexandria LiCSAR test found the same result with each line of sight alone, so a line-of-sight test is defensible, but it must be pre-registered.

## Files

- `raw/incidents.csv`: OEM Emergency Response Incidents (NYC Open Data `pasr-j7fb`).
- `raw/geosearch.json`, `raw/pluto.json`, `raw/permits_blocks.json`: cached API answers.
- `out/events_clean.csv`: one row per merged event, with every flag used above.
