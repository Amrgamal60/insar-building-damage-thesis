# Reference data for the Austin population and baseline: options for approval

**Status:** APPROVED by the user on 2026-10-31: order A, then C. Written by Claude on 2026-10-30.
- **Amended the same day at the user's direction:**
  - C is registered as the fallback, with eligibility from 2019-10-01;
  - 2026 living area and foundation type are exploratory only;
  - demolition is examined as a competing outcome;
  - the sale analysis needs yearly deed records;
  - an identifier crosswalk is built.
- The earlier choice to keep 2018-08-01 under C is withdrawn.

**Evidence:** `refdata_checks.json`, from `scripts_refdata/refdata_checks.py`. The check is outcome-blind: it reads no permit, InSAR or outcome data. Only aggregate counts are reported.

**Principle:** historical TCAD rolls are preferred but are not a condition for going ahead. The records request to TCAD stays active.

## 1. The two risks

**Survivor bias.** A population taken from the 2026 roll contains only the houses that still stood in 2026. Houses demolished or rebuilt during the study are missing, and so are their repairs. A house with foundation trouble is also a likely teardown, so these losses need not be random.
- **Measured on the public 2019 parcel layer:** 151,944 Austin houses were A1 and built by 2015 in 2019. Of these:
  - **144,041 (94.8%)** are in the 2026 detached population;
  - **2,477 (1.6%)** were rebuilt, with the new year built mostly 2019–2025;
  - **3,274 (2.2%)** are no longer A1, or their property ID changed (replat, reclassification, demolition to vacant land);
  - 2,152 (1.4%) have a main improvement that is not type 01. These are mostly townhouses, which A1 includes in both years, so they are not a survivorship loss.
- **Result:** a 2026 population loses about 2–4% of the houses that existed in 2019, and more of those that existed when the study starts in 2018.

**Temporal leakage.** A characteristic recorded after an event can reflect the event or what followed it. Examples are a living area enlarged by a later addition, or a foundation code updated after a repair.

## 2. What is verified stable (same houses, 2019 vs 2026)

| Characteristic | Agreement 2019 vs 2026 | Treatment |
|---|---|---|
| Year built | identical for 143,780 of 144,233 (99.7%) | stable |
| Lot area (parcel polygon) | within 1% for 139,208 of 144,322 (96.5%); within 5% for 98.6% | stable |
| Living area | cannot be checked: no public pre-2026 source with this field has been opened | not treated as stable |
| Foundation type | cannot be checked, as above | not treated as stable |

Soil (SSURGO), terrain (3DEP), neighbourhood income (ACS 2011–2015), canopy (closest to 2016) and parcel coordinates are pre-event by source.

## 3. Sources

| | Source | Describes | Official | Fields | Status |
|---|---|---|---|---|---|
| **A** | TCAD certified roll, tax year 2018 (or the latest year up to 2018 received) | 1 January 2018, before the study starts | yes | all, including living area, foundation and deed date; the yearly rolls 2016–2025 add sale histories | requested 2026-10-30; not in hand |
| **B** | TCAD 2018 *preliminary* export, a research mirror (TXHousing project) | 1 January 2018 (run 2018-04-10) | non-official copy of a public export; licence unverified | the same tables as A, for one year | header file only; bodies not opened |
| **C** | TxGIO StratMap 2019 parcel layer for Travis County | tax year 2019, extracted September 2019 | official state programme, CC0 (catalogue metadata) | state code, year built, polygon. It has no improvement type, living area, foundation or deed date, and its `DATE_ACQ` is the extraction month | in hand: a public ArcGIS mirror. The official file returned CloudFront 403 to scripts; the user can download it in a browser to confirm the mirror |
| **D** | TCAD 2026 certified roll | 1 January 2026, after every event | yes | all | in hand |

## 4. Rules common to every option

1. **Pre-event or stable data only:** the population and the baseline features come only from a record dated before the study start, or from characteristics verified stable (year built, lot area).
2. **Demolished houses stay at risk until demolished:** a house that is demolished during the study remains in the population until then. It stops being at risk (in the Test A control pool and the Test B exposure *n*) on the date of its first Demolition BP after the study start. This needs only the permit table.
3. **Sale histories:** analyses that need yearly sale histories (secondary 14, the sale-triggered split) run only with option A's yearly rolls. Otherwise they are removed, not replaced by a partial substitute.
4. **Fixing the source:**
   - The source is fixed when checkpoint 1 starts, from what is in hand then, in the approved order.
   - Rolls that arrive later are not used in any prespecified analysis. Anything done with them is labelled exploratory.
   - The draft-5 "reference-roll sensitivity analysis" is removed.
5. **Survivorship check, reported under every option:**
   - events (rules 1–3) at reference-population houses that are no longer in the 2026 detached population;
   - the number of houses censored by demolition.

## 5. What each option gives

| | A: certified 2018 | B: 2018 preliminary mirror | C: 2019 public layer | D: 2026 roll only |
|---|---|---|---|---|
| Population fixed | 1 Jan 2018 (before start) | 1 Jan 2018 | September 2019 (before the C start, 2019-10-01) | 2026 |
| Survivor bias | removed | removed | removed (the study starts after the layer date) | **not removable** |
| Baseline 1 | as the plan: age, living area, lot area, foundation type (if ≥ 90%), soil, terrain, income, x/y | as A | age (2019), lot area (2019 polygon), soil, terrain, income, x/y | as A, but every roll feature is post-event |
| Living area, foundation type | pre-event | pre-event, but from a source that cannot be verified | **not in Baseline 1**; any use of the 2026 values is exploratory, not evidence of prospective predictive performance | post-event |
| Sale split (secondary 14) | only if yearly certified deed records for the whole period arrive; the 2018 roll alone does not provide them | removed | removed | removed |
| New work | none | download, verification and your acceptance of its provenance | none | none |

**Details for C:**
- **Population:** A1 in the 2019 layer, built by 2015 (2019 value), inside the full-purpose boundary, fixed from 2019 data alone. The 2,152 houses that keep their property ID and year built and are townhouses in 2026 are left out. Every other house stays in, whatever became of its account, and where its 2019 type cannot be checked it is called unknown, not detached (AUSTIN_PLAN §5).
- **Study start (registered 2026-10-31): 2019-10-01.** Eligibility begins after the September 2019 layer, so every population fact predates every event.
  - About 14 of 88 months of events (about 16%) are lost. That is the price of removing the leftover survivor bias.
  - An earlier choice to keep 2018-08-01 was withdrawn.
- **Identifiers:** the 1.4% of 2019 houses that are not type 01 in 2026 is reconciled. They are 2,152 type 16 townhouses with the same property ID and year built, so they are the same buildings, not lost houses (`ID_CROSSWALK.md`).
  - Houses whose property ID changed were traced by an outcome-blind crosswalk: the same property ID, then the same `geo_id`, then polygon overlap (`ID_CROSSWALK.md`, `id_crosswalk.json`). It recovers 21 renumbered, 126 merged and 49 split lots, and leaves 1,891 unresolved.
  - The registered rule (AUSTIN_PLAN §5): permits link through the 2019 `geo_id`, successor keys are not used, six houses with ambiguous keys are left out, and a house with no 2026 match is not treated as demolished.
- **Demolition:** demolished houses stay at risk until their first total demolition. Whether demolition is an informative competing outcome is examined, not assumed:
  - permit checks at checkpoint 1, before InSAR;
  - analyses D1–D3 with InSAR (AUSTIN_PLAN §5, §12).

**Details for B:** before adoption, its bodies are downloaded and checked outcome-blind:
- the header says the 2018 preliminary roll;
- the fields are filled at the same rates as the 2026 roll;
- year built agrees with the 2019 layer and the 2026 roll for at least 99% of the same houses.

Its added fields, living area and foundation type, cannot be verified against any official pre-event source. That is its main weakness.

**Cost of the request:** the primary analysis needs only *one* certified roll, tax year 2018. If TCAD's estimate for 2016–2025 is high, the request can be narrowed to 2018 alone. This gives option A without the sale split.

## 6. Recommendation

**Order (approved): A, then C.** The TCAD request stays active, with the certified 2018 roll as its priority (`TCAD_PIA_FOLLOWUP_draft.md`). B is not used. D is not used.
- **A** is the official, complete pre-event record, and the only option that supports the sale split.
- **C** uses an official public layer and only characteristics verified to be stable. It removes most of the survivor bias, at the cost of moving living area and foundation type out of the primary baseline. Every claim it rests on is checked in `refdata_checks.json`.
- **B** gives the same fields as A on the same date. However, its distinctive fields cannot be verified, and its provenance and licence are unclear.
- **D** cannot remove survivor bias.

**Effect on step 0 results:** under C the population is about 152,000 houses (less townhouses) instead of 144,458, with 74 monthly windows instead of 88. The timing gate (1.9 h for 999 draws) and the income coverage (99.97%) are expected to change only slightly. Both are recomputed at checkpoint 1.

## Outcome at checkpoint 1 (2026-11-09)

The certified 2018 roll and the 2018 parcel layer were in hand when checkpoint 1 started on 2026-11-09. Under the frozen order (AUSTIN_PLAN §5), **option A applies**: the study period starts on 2018-08-01, and all reference features come from the 2018 files.

- Foundation type was recorded for 94.6% of eligible parcels, so it enters Baseline 1 (§9, threshold 90%). Living area also enters.
- The primary population is 149,316 houses.
- Option C, its townhouse rule and sensitivities P0–P1 are not used.
- The sale analysis (secondary 14) is removed, because a single roll gives no sale history.

Details: `../checkpoint1/REFERENCE_DATA_2018.md`.
