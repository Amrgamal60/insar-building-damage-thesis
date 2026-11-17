# Austin study: result

**Plan:** `AUSTIN_PLAN.md`, frozen copy `freeze/AUSTIN_PLAN_frozen.md` (SHA-256 `18627d8275d7859b…`; draft 10, approved and frozen 2026-11-07). Reference data option A (TCAD certified 2018 roll and parcel layer); study period 2018-08-01 to 2025-11-30. Primary Test A null: the conditional variogram null (b).

**How this document is made:** `python3 -I production/result_report.py` writes it from the records of the real run, the checks and the secondary report. Every result number is read from those records by that code, and every record's hash is checked against §15 or the hash list written with it (section 11). The §11 readings are quoted from the frozen plan. Nothing here is a new analysis, and nothing in §4–§12 changed after the results were seen (§13 point 7).

**What the outcome is:** the first recorded qualifying foundation-repair permit in the City's issued-permit records, dated by application date. All readings concern *recorded* repair permits, not independently validated physical damage, and not cause (§4, §11).

## Summary

- **Test A (primary, decision): added held-out value of InSAR is NOT demonstrated in Austin.** Change in PR AUC −0.00058 (95% interval −0.00197 to +0.00034), p_A = 0.931 with the conditional null (999 draws).
- **Test B (key secondary, no decision): association not detected.** Rate ratio per IQR 1.006 (95% interval 0.867 to 1.168), p_B = 0.967.
- **Clay contrast: demonstrated**, so the §11 reading is the row "clay contrast demonstrated" for both tests, and "Neither" together.
- **Beside the decision:** largest p across the nulls of §12.8 1.000; directional concordance opposite; remodel negative control: negative-control gain not detected (Test A) and negative-control association not detected (Test B).
- **Sign check: not below** in the first run (+0.84 mm/yr) and **not below** on the corrected values (+0.73). Outcome-blind diagnostics logged three findings; one of them, lasting cycle slips, was corrected before any outcome was compared. The sign was confirmed another way, by the clay seasonal curve (section 6).
- **Secondary analyses:** no Test A secondary has a positive change in PR AUC with a 95% interval excluding 0, and no Test B secondary has p_B < 0.05 (section 8).

## 1. Variogram checks (reported first, §10)

As NYC: the observed semivariance in each lag bin against the 2.5–97.5% range of the surrogates. Whatever they show, no null is changed (§10). Full tables by distance: appendix A.

- **Test A, conditional null:** the 999 surrogates of the null file (`07bf0d54…`; neighbour count 18 in 2, 28 in 997 draws), 20 windows (seed 7): 2018-08, 2018-12, 2019-06, 2019-07, 2020-01, 2020-06, 2020-07, 2022-01, 2022-02, 2022-03, 2022-08, 2023-05, 2023-10, 2023-12, 2024-01, 2024-04, 2024-05, 2024-09, 2025-09, 2025-11.
  - **Lags 1–16 (30–480 m):** observed semivariance inside the surrogates' 95% range at 43 of 320 window-lags. Median surrogate / observed: 1.38× at lag 1, 1.07–1.14× at lags 2–16.
  - **1 km bins from 0.495 to 20 km:** inside at 15 of 400. Median surrogate / observed 1.11× in the first bin, 0.72–0.74× at 15–20 km.
  - **All 720 window-bins:** 58 inside, 322 below and 340 above the range.
- **Test B null (seed 2034):** the 999 surrogates of the null file (`0bc1305e…`; neighbour count 169 in 743, 264 in 185, 411 in 3, 641 in 14, 1000 in 54 draws), 5 quarters (seed 8): 2019Q4, 2020Q2, 2020Q4, 2023Q1, 2025Q2.
  - **Lags 1–16 (250 m to 4 km):** observed semivariance inside the surrogates' 95% range at 51 of 80 quarter-lags. Median surrogate / observed: 1.51× at lag 1, 0.91–1.10× at lags 2–16.
  - **1 km bins from 4.125 to 20 km:** inside at 37 of 80. Median surrogate / observed 0.91× in the first bin, 0.24–0.28× at 15–20 km.
  - **All 160 quarter-bins:** 88 inside, 11 below and 61 above the range.
- **Reading** (as recorded in §15 before the real run):
  - The pattern is NYC's: surrogates rougher than the field at the first lags, and too little long-range semivariance beyond a few km. The §10 null matches the residual's short-lag variogram only, so long-range structure in velocity that the baseline features do not explain is under-represented in the surrogates. The frozen plan does not name this as a limitation; it is reported here with Test A.
  - Test A's counts inside are low because its 95% ranges are very narrow with this many pixels; the ratios carry more information than the counts.
  - What this means for Test A is read with the planted-signal check (section 5), not by changing the null.

## 2. Decision (§11)

**Rule:** Only Test A, the primary analysis, carries the study's decision (design summary, point 2).
Added value is demonstrated if and only if, in the primary analysis (single-family parcels, logistic regression, Baseline 1 + x/y, 24-month window), the change in PR AUC is positive **and** p_A < 0.05.

- **Test A: added held-out value of InSAR is NOT demonstrated in Austin.** The change in PR AUC is not positive (−0.00058), and p_A = 0.931 (930 of 999 draws at or above the observed change; seed 2027).
- Otherwise added value is **not demonstrated** in the primary analysis. That is not evidence that ground motion carries no information. The conclusion concerns 24-month trend velocity in this logistic model; other indicators, windows and models are secondary analyses. The change in PR AUC and its interval show whether a useful gain is excluded or the result is inconclusive.

| Metric | Baseline 1 + x/y | + velocity | Change | p (conditional null) | Null median | 95% refit-bootstrap interval |
|---|---|---|---|---|---|---|
| PR AUC (primary) | 0.04599 | 0.04542 | −0.00058 | 0.931 | −0.00042 | −0.00197 to +0.00034 |
| ROC AUC | 0.7242 | 0.7227 | −0.0015 | 0.287 | −0.0017 | −0.0044 to +0.0020 |
| Top-10% capture, pooled | 0.2685 | 0.2680 | −0.0006 | 0.501 | −0.0006 | −0.0203 to +0.0079 |
| Top-10% capture within the risk set | 0.2811 | 0.2702 | −0.0108 | 0.962 | −0.0063 | not bootstrapped (as fixed) |

- **Null draws** (PR AUC change): median −0.00042, maximum +0.00002. 930 of 999 draws lie at or above the observed change.
- **Interval:** refit block bootstrap, 2,000 resamples over the 201 blocks of 2 km holding rows of either analysis; 0 resamples lacked a value. It excludes changes above +0.00034, which is 0.7% of the baseline's PR AUC (0.046). §11 set no number for a "useful" gain, so this upper limit is reported as it is. PR AUC here is average precision on the sampled risk sets (1 case and on average 46.6 controls each, after controls missing an input were dropped), not city-wide precision.

**Directional concordance** (§11; 1,754 risk sets, 0 without controls; below 0 is concordant):
- Standardised: median of (case − median of its controls) +0.0092, so the label is **opposite**; 49.6% of risk sets lie below 0.
- Raw: median +0.025 mm/yr (49.6% below 0). Median velocity of cases 8.30 mm/yr, of controls 7.91 mm/yr.
- Coefficient of the standardised velocity, logistic model on all rows: +0.0085.
- Both medians are close to zero: case and control velocities barely differ.

**Largest p across the nulls of §12.8:** 1.000 (section 4).

## 3. Test B (key secondary, prespecified reading, no decision)

- **Association not detected:** rate ratio per IQR (27.0 mm/yr) **1.006**, 95% interval 0.867 to 1.168 (Wald, errors clustered by 2 km block); β = +0.00022 per mm/yr (clustered SE 0.00283).
- **p_B = 0.967** (966 of 999 draws with |β| at or above the observed; seed 2034). p_B is nominal secondary evidence.
- **Direction:** opposite (rate ratio above 1); the estimate is close to 1.
- **Block bootstrap** (2,000 resamples over 192 blocks, 0 failed fits): log rate ratio per IQR −0.138 to +0.161, i.e. a rate ratio of 0.871–1.175.
- **Panel:** 129,682 cell-quarter rows; the model keeps 38,047 rows in 1,397 cells, 28 quarters and 145 blocks (3,583 cells with no event in any quarter drop out under the cell fixed effects).

## 4. Reported beside the decision (§11, §12.8)

### Nulls of §12.8 (change in PR AUC; same analysis and observed change)

| Null | Draws | p, PR AUC | p, ROC AUC | p, Top-10% pooled | p, Top-10% own set | Null median, PR AUC |
|---|---|---|---|---|---|---|
| Conditional variogram null (primary, §10) | 999 | 0.931 | 0.287 | 0.501 | 0.962 | −0.00042 |
| Null (a): NYC variogram null, unconditional (the calibration found it too lenient, §10) | 999 | 1.000 | – | – | – | −0.00005 |
| Free permutation | 2,000 | 1.000 | 1.000 | 0.840 | 1.000 | −0.00004 |
| Within-block permutation | 2,000 | 0.995 | 0.658 | 0.775 | 0.995 | −0.00020 |
| MSR | 999 | 1.000 | – | – | – | −0.00006 |

Largest p: **1.000**. Null (a) and MSR were run for PR AUC only (§15). Their p's are secondary 8 only.

### Specificity check, Test A: remodel negative control

- The primary analysis repeated unchanged on 1,491 remodel control events (§14 rule, controls seed 2030, the same 999 surrogates): 866 cases, 41,248 rows. Dropped: 515 no value in the window; 108 missing Baseline 1 input; 2 demolition-censored on or before the event date.
- Baseline PR AUC 0.0274. **Change +0.00011, 95% interval −0.00066 to +0.00098, p = 0.341. Label: Negative-control gain not detected.**
- Share of the foundation change: −0.19. The foundation change is negative, so this share has no useful reading; it is reported as computed.
- Its other metrics (nominal): ROC AUC −0.0014 (p 0.713); pooled top-10% +0.0046 (p 0.135); top-10% within the risk set +0.0150 (p 0.022).
  The last p is below 0.05, on one of four uncorrected metrics of the negative control. §11 labels the negative control by PR AUC only, so it carries no label.
- **Direct comparison:** foundation change minus remodel change, on the same 2,000 resampled blocks: −0.00069, 95% interval −0.00225 to +0.00049. No difference is claimed.
- "Not detected" does not show that remodel permits have no gain, and does not prove the foundation result free of owner, income or reporting bias (§11).

### Specificity check, Test B: remodel counts

- Remodel events: 1,489 counted, 1,411 inside the 28 quarters, 1,376 in rows used. Exposure: foundation at-risk rule (§8), as the foundation panel.
- The model keeps 30,182 rows in 1,099 cells, 28 quarters and 152 blocks.
- **Rate ratio per IQR 1.084, 95% interval 0.899 to 1.308**; bootstrap interval of the log rate ratio −0.104 to +0.274. **p = 0.706** (705 of 999, seed 2035). **Label: Negative-control association not detected.**
- **Direct comparison:** foundation minus remodel log rate ratio per IQR, on the same 2,000 resampled blocks: −0.075, 95% interval −0.321 to +0.164. No difference is claimed.

### Reading, as fixed in §11

The clay contrast was demonstrated (section 6), so the rows read:

| Test | Decision | Label | Reading |
|---|---|---|---|
| A | Not demonstrated | Clay contrast demonstrated | The seasonal signal separates the soil classes as expected, yet a gain from 24-month velocity in locating recorded repairs was not demonstrated. The interval of the change shows whether a useful gain is excluded or the result is inconclusive. |
| B | Not detected | Clay contrast demonstrated | An association between within-area motion and later recorded permits was not detected at quarterly resolution. The rate-ratio interval shows how large an association remains compatible with the data. |

Together (Test B never changes the decision): **Neither:** read through the clay-contrast label, as in the table, with the effect sizes and intervals.

## 5. Sensitivity of Test A at Austin's size (planted-signal check)

Fixed in §14 (2026-11-10) and run before the real run: synthetic outcomes on the real field, 1,754 events per dataset (the real run's case count), 999 null draws, 100 datasets per cell. Test A is not demonstrated, so §14 reports cells 4–6 as the test's sensitivity:

| Cell | Odds ratio per IQR | Meets the §11 rule [95% Wilson] | Mean observed change [95% t] | Paired bias [95% t] |
|---|---|---|---|---|
| 4. beta = −0.1 | 1.11 | 34/100 = 34% [25.5, 43.7] | +0.00070 [+0.00054 to +0.00086] | +0.00037 [+0.00027 to +0.00047] |
| 5. beta = −0.2 | 1.22 | 75/100 = 75% [65.7, 82.5] | +0.00275 [+0.00253 to +0.00298] | +0.00143 [+0.00127 to +0.00159] |
| 6. beta = −0.4 | 1.49 | 100/100 = 100% [96.3, 100.0] | +0.00948 [+0.00907 to +0.00990] | +0.00542 [+0.00513 to +0.00572] |

Cells 1–3 (no velocity effect; rejection rates 5%, 11%, 5%) are in `planted_signal/PLANTED_SIGNAL.md`; §14 reports them beside a demonstrated result only.

## 6. Checks before outcomes (§7, §13 steps 3–4)

- **Sign check (§7): not below.** First run: landfill median +8.87 mm/yr against a subset median of +8.02 (difference +0.84; 1,183 valid footprint pixels at 32 of 39 perimeters). By §7 work stopped until the cause was found and logged.
  - **Diagnostics** (outcome-blind, §15) logged three findings: a west–east regional gradient, with most landfills east of the subset's median; no detectable pooled settlement at the old landfills; and lasting phase-unwrapping cycle slips (steps near one half-wavelength) in a north-east zone holding the active landfills. The slip screen found slips at 2,741 of 114,058 house pixels (2.4%; 4,183 houses).
  - **Correction:** decided by the user on 2026-11-11 (§14, "Lasting cycle slips"), before any outcome was compared: a pixel has no value in a window that contains one of its slips. All analyses use the corrected fields; the first run's fields serve the slip-rule sensitivity analysis (secondary report).
  - **On the corrected values:** landfills +8.77 against +8.04 mm/yr (difference +0.73): still **not below**. The result stands as recorded.
  - **The sign itself is confirmed** another way: the seasonal curve of the high and very high clay classes minus the low class has its trough at day of year 272 (95% interval 260–287), in late September: clay shrinking in the dry season, as expected if positive is toward the satellite.
- **Clay contrast (§7): demonstrated.** High and very high classes minus the low class, median full-period seasonal amplitude: +0.67 mm, 95% block-bootstrap interval 0.38 to 0.98 (213 blocks of 2 km, 2,000 draws, seed 2026). By class: low 2.87 mm (16,024 parcels), moderate 2.61 mm (90,045 parcels), high 3.50 mm (8,521 parcels), very high 3.57 mm (22,941 parcels).
- **Coverage (§7):** in the 24-month windows a median of 70,310 of 114,058 house pixels and 92,950 of 149,316 houses have a value. The construction mask removes a median of 40,003.5 house pixels per window, the largest loss.
- **Decoy run (§13 step 4; a code check, not a result):** each event moved to a random house (seed 99). Test A: 1,568 decoy cases, change −0.00013, p 0.248. Test B: rate ratio per IQR 0.90, p_B 0.460. Both ran end to end with no code error; nothing was changed.
- **Checks at checkpoint 1** (permits only, no InSAR; design summary points 8 and 11): label audit 98/100 foundation repairs (98%, exact 95% CI 93.0–99.8; one AI reader, no engineer); parcel link check: 93.9% of 13,881 qualifying permits match a 2018 parcel and 84.3% the primary population; survivorship: 30 events (1.1%) are at houses no longer in the 2026 detached population; demolition audit: 38/50 censoring permits demolish the main house (76%).
- **Permits and drought (§4, reported only):** Spearman ρ = −0.42 (p = 0.086, 18 years) between repair permits by issue year (rules 1–2, 2008–2025) and the previous year's mean drought index (NOAA division 4107).
- **Survivorship link check (§5; option A: 2018 property ID present or absent in the 2026 roll):** permits of all types per 100 house-years, as recorded; §5 reads a falling rate at absent accounts as permits lost to key changes.

| Year | ID in the 2026 roll (147,670 houses) | ID absent (1,646 houses) |
|---|---|---|
| 2016 | 13.6 | 3.0 |
| 2017 | 13.7 | 10.2 |
| 2018 | 14.9 | 13.9 |
| 2019 | 16.0 | 3.7 |
| 2020 | 15.3 | 2.2 |
| 2021 | 19.5 | 17.4 |
| 2022 | 18.0 | 27.3 |
| 2023 | 15.7 | 36.5 |
| 2024 | 14.5 | 61.3 |
| 2025 | 14.5 | 19.6 |

## 7. Sample and exclusions

- **Events (§4):** 2,846 first qualifying foundation-repair permits on the 149,316 eligible detached houses, one per house, dated by application date. By year: 2018 170, 2019 355, 2020 316, 2021 382, 2022 386, 2023 397, 2024 369, 2025 471.
- **Test A:** 1,754 cases. Dropped: 961 no value in the window; 127 missing Baseline 1 input; 4 demolition-censored on or before the event date. 83,496 case and control rows (5,958 control rows dropped for missing inputs). Cases by fold: 319, 349, 346, 365, 375. By year: 2018 115, 2019 189, 2020 180, 2021 222, 2022 235, 2023 264, 2024 225, 2025 324.
  - 33.8% of events are lost for want of an InSAR value in their 24-month window, mostly to the construction mask (section 6).
- **Test B:** 2,842 events counted (the 4 demolition-censored events are not at risk), 2,655 inside the 28 quarters, 2,553 in rows used and 102 in rows without a value.

## 8. Secondary analyses (§12; reported, no decision attached)

Full report: `secondary_real/AUSTIN_SECONDARY_RESULTS.md` (SHA-256 `4bfb57719af8e986…`), summary `secondary_real/secondary_summary.json`. Every p there is nominal and uncorrected.

- **Test A secondaries** (31 analyses, counting each lag and fold seed; 21 have a bootstrap interval, the fold seeds have none, as fixed in §15): 0 with a positive change in PR AUC whose 95% interval excludes 0.
- **Nominal p < 0.05** on any metric: 14 cases. 6 have a negative change (the null draws were lower still), so they are not gains; the other 8 are positive with intervals that include 0 or no interval.
- **Test B secondaries** (11 analyses): 0 with p_B < 0.05. Wald intervals excluding 1: item 15, lag 12 (rate ratio 1.133, above 1, the opposite direction, p_B 0.327).
- **Deep model (item 20):** change in PR AUC −0.00371 (95% interval −0.00537 to +0.00165), p 0.52.
- **Not run:** item 14 (sale-triggered repairs; removed under §4: it needs yearly deed records, which the single 2018 roll does not provide) and P0–P1 (defined for option C only). No analysis is "not run" for lack of time: the user removed the compute budget on 2026-11-12 (§14).

## 9. Deviations from the frozen plan (§14)

- 2026-11-10: Addition: planted-signal check of Test A at Austin's size.
- 2026-11-10: Canopy layer for Baseline 2 (§9): the 2018 layer.
- 2026-11-10: Landfill footprints for the sign check (§7): the City of Austin's landfill perimeters.
- 2026-11-10: Remodel negative control (§4): work class Repair or Remodel, and fewer control events.
- 2026-11-10: Compute location: all heavy runs on the processing server.
- 2026-11-11: Construction mask (§7): distance to the parcel polygon, and where a permit's parcel is.
- 2026-11-11: Connected-component rule (§7, "as NYC §7, steps 1–3"): the main component inside the city instead of the label at the frame's reference point.
- 2026-11-11: Lasting cycle slips (§7, processing corrected after the checks): a pixel has no value in a window that contains one of its slips.
- 2026-11-12: Compute budget (§13 point 6): no time limit. Every secondary analysis and the deep model run to completion.

Each is logged with its reason and approval in §14. All were decided before any outcome was compared, except the compute budget, which changed no analysis.

§15 also records authors' choices made after the primary result but before the outcome each one concerns, each with its time: the MSR code (secondary 8), the details §12 leaves open for the secondary runners, the deep model's settings, and the move of one secondary surrogate file from the CPU to the GPU engine. None changes a rule of §4–§12.

## 10. Limits of this result

- The outcome is recorded permits. Unpermitted repairs and unrepaired damage are not seen (§4).
- 33.8% of events had no InSAR value in their window; Test A rests on 1,754 cases.
- The conclusion concerns 24-month trend velocity in the logistic model; other indicators, windows and models are the secondary analyses (§11).
- The surrogates under-represent long-range variance (section 1). The planted-signal check measured the test's behaviour on the real field at this size (section 5).
- The calibration (§10) found the conditional null may be conservative at Austin's size and has less power than null (a). The other four nulls of §12.8 are reported in section 4.
- The sign check is "not below" before and after the slip correction. Only the slips were corrected; the other two findings are described, not removed (section 6).
- One ascending track gives line-of-sight motion only (plan, outstanding data limitations).

## 11. Records

Run on the processing server (`run_tests.py` `020c67e0…`, `run_report.py` `ea0315b6…`); records copied to the PC with the same hashes. Every record below was checked by this generator:

| Record | SHA-256 (16) | Checked against |
|---|---|---|
| `real_20261112/test_a.json` | `c50f3da7ff87f6ef` | §15 (full hash) |
| `real_20261112/test_b.json` | `489e822c79226dac` | §15 (full hash) |
| `real_20261112/report_a.json` | `4cf9abe0f9ce1940` | §15 (full hash) |
| `real_20261112/report_b.json` | `1f50166eca6fc8cb` | §15 (full hash) |
| `real_20261112/nulla/test_a.json` | `3aced26fa06cc8c9` | §15 (full hash) |
| `real_20261112/msr/test_a.json` | `c3a6abbc19b281ed` | §15 (full hash) |
| `production/check/variogram_check_a.json` | `0ebbed61ebabb780` | hash list |
| `production/check/variogram_check_b.json` | `bbaa122b4cc4839b` | hash list |
| `production/check/checks_run1_checks.json` | `543eda6e4bcb06af` | hash list |
| `production/check/checks_slips_checks.json` | `479ae8e87e61afb3` | hash list |
| `production/check/checks_run1_sign_series_diagnostics.json` | `0eccf3b485ec029c` | hash list |
| `production/check/slip_screen.json` | `be03647840b08ca9` | hash list |
| `production/check/decoy_test_a.json` | `1a3b40fc8b36ee3d` | hash list |
| `production/check/decoy_test_b.json` | `9d32f091ccc2d8dd` | hash list |
| `planted_signal/run_20261111/planted_signal_summary.json` | `883f7b1e3ba4c2e5` | §15 (prefix) |
| `planted_signal/PLANTED_SIGNAL.md` | `dca7936df8c3f8f7` | §15 (full hash) |
| `checkpoint1/events_2018.json` | `5c732312397796dc` | hash list |
| `checkpoint1/audit_results_2018.json` | `0a2d3248c1a5b2fd` | hash list |
| `checkpoint1/link_check_2018.json` | `6e02306de7ab1d35` | hash list |
| `checkpoint1/drought_check.json` | `f95e470d304626eb` | hash list |
| `secondary_real/AUSTIN_SECONDARY_RESULTS.md` | `4bfb57719af8e986` | §15 (prefix) |
| `secondary_real/secondary_summary.json` | `ba12c39a0585e900` | §15 (prefix) |

| Run | Finished (EET) |
|---|---|
| Test A (decision) | 2026-11-12 09:23:52 |
| Test B | 2026-11-12 09:27:07 |
| Test A report (beside items) | 2026-11-12 09:35:40 |
| Test B report | 2026-11-12 09:40:15 |
| Null (a), secondary 8 | 2026-11-12 12:54:03 |
| MSR, secondary 8 | 2026-11-12 15:35:31 |
| Decoy Test A | 2026-11-11 19:34:13 |
| Decoy Test B | 2026-11-11 19:38:29 |

**Reproduce this document:** `python3 -I production/result_report.py` (two runs give the same bytes).

## Appendix A. Variogram checks by distance

**Test A (conditional null; 30 m pixels):** windows inside the surrogates' 95% range, and the median over windows of surrogate / observed.

| Distance | Windows inside (of 20) | Median surrogate / observed |
|---|---|---|
| 0.03 km (lag 1) | 0 | 1.38 |
| 0.06 km (lag 2) | 0 | 1.14 |
| 0.09 km (lag 3) | 0 | 1.10 |
| 0.12 km (lag 4) | 1 | 1.08 |
| 0.15 km (lag 5) | 2 | 1.09 |
| 0.18 km (lag 6) | 1 | 1.09 |
| 0.21 km (lag 7) | 1 | 1.10 |
| 0.24 km (lag 8) | 0 | 1.11 |
| 0.27 km (lag 9) | 2 | 1.09 |
| 0.3 km (lag 10) | 2 | 1.09 |
| 0.33 km (lag 11) | 4 | 1.08 |
| 0.36 km (lag 12) | 6 | 1.07 |
| 0.39 km (lag 13) | 6 | 1.07 |
| 0.42 km (lag 14) | 6 | 1.07 |
| 0.45 km (lag 15) | 6 | 1.07 |
| 0.48 km (lag 16) | 6 | 1.08 |
| 0.495-1 km | 2 | 1.11 |
| 1-2 km | 2 | 1.03 |
| 2-3 km | 5 | 0.98 |
| 3-4 km | 2 | 0.93 |
| 4-5 km | 1 | 0.89 |
| 5-6 km | 1 | 0.87 |
| 6-7 km | 1 | 0.85 |
| 7-8 km | 0 | 0.83 |
| 8-9 km | 0 | 0.82 |
| 9-10 km | 1 | 0.80 |
| 10-11 km | 0 | 0.79 |
| 11-12 km | 0 | 0.78 |
| 12-13 km | 0 | 0.77 |
| 13-14 km | 0 | 0.75 |
| 14-15 km | 0 | 0.74 |
| 15-16 km | 0 | 0.72 |
| 16-17 km | 0 | 0.73 |
| 17-18 km | 0 | 0.73 |
| 18-19 km | 0 | 0.74 |
| 19-20 km | 0 | 0.74 |

**Test B (250 m cells):** windows inside the surrogates' 95% range, and the median over windows of surrogate / observed.

| Distance | Windows inside (of 5) | Median surrogate / observed |
|---|---|---|
| 0.25 km (lag 1) | 1 | 1.51 |
| 0.5 km (lag 2) | 3 | 1.10 |
| 0.75 km (lag 3) | 4 | 0.97 |
| 1 km (lag 4) | 2 | 0.93 |
| 1.25 km (lag 5) | 0 | 0.91 |
| 1.5 km (lag 6) | 0 | 0.93 |
| 1.75 km (lag 7) | 2 | 0.94 |
| 2 km (lag 8) | 5 | 0.98 |
| 2.25 km (lag 9) | 5 | 1.02 |
| 2.5 km (lag 10) | 4 | 1.04 |
| 2.75 km (lag 11) | 3 | 1.04 |
| 3 km (lag 12) | 4 | 1.03 |
| 3.25 km (lag 13) | 4 | 1.02 |
| 3.5 km (lag 14) | 5 | 1.01 |
| 3.75 km (lag 15) | 5 | 0.99 |
| 4 km (lag 16) | 4 | 0.96 |
| 4.125-5 km | 4 | 0.91 |
| 5-6 km | 4 | 0.81 |
| 6-7 km | 4 | 0.70 |
| 7-8 km | 4 | 0.61 |
| 8-9 km | 4 | 0.55 |
| 9-10 km | 4 | 0.46 |
| 10-11 km | 3 | 0.42 |
| 11-12 km | 2 | 0.39 |
| 12-13 km | 1 | 0.36 |
| 13-14 km | 1 | 0.32 |
| 14-15 km | 1 | 0.30 |
| 15-16 km | 1 | 0.28 |
| 16-17 km | 1 | 0.26 |
| 17-18 km | 1 | 0.25 |
| 18-19 km | 1 | 0.24 |
| 19-20 km | 1 | 0.24 |
