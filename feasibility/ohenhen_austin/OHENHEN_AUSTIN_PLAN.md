# External validation of a published InSAR building-risk map against recorded foundation repairs (Austin, 2022–2025)

**Status: FROZEN 2026-11-18 (draft 3, approved by the user: "Freeze and run").**
- **User decisions (2026-11-17, §16):**
  - D1–D4 approved as recommended: risk high or very high as the predictor; δ = IRR 1.5; mapped houses only.
  - After the planted check: inference r3 (wild cluster score bootstrap by 6 km block), and **V and U co-primary with Holm** (this replaces "V primary, U key secondary").
- **Independent review:** draft 1 was reviewed by an independent referee; the changes are listed in §16.
- **Outcomes:** no house was linked to an outcome under this plan before freezing.

Freezing creates `freeze/OHENHEN_AUSTIN_PLAN_frozen.md` (never edited) with its SHA-256 in §15. After freezing, changes go to §14 (deviations) only.

## Design summary

1. **The map is someone else's and is fixed.** Ohenhen et al. (2025, *Nature Cities* 2, 543–554) mapped vertical land motion (VLM) for 28 US cities from Sentinel-1 data of 2015–2021. They turned it into an angular-distortion hazard class and a building-risk class, and published the layers (CC0; data DOI 10.7294/27606942). We test those published files as they are. We do not refit, recalibrate, resample or tune them.
2. **The outcomes come after the map's data.** The map uses InSAR data up to 2021. The outcome is a first recorded foundation-repair permit from 2022-01-01 to 2025-11-30, among houses still at risk at the end of 2021-12-31. No outcome used here could have informed the map.
3. **The authors name the gap.** They write that the lack of documented damage "limits our ability to cross validate or directly correlate identified high-hazard/high-risk zones with documented structural damage. Future studies should address this gap." This study does that for one of their cities.
4. **Inherited from the frozen Austin study** (`feasibility/austin/freeze/`, plan hash 18627d8275d7859b), unchanged:
   - the reference population (option A, TCAD 2018);
   - the event rule;
   - demolition censoring;
   - the shared at-risk rule;
   - the Baseline 1 features;
   - the 2 km blocks and the seed-42 fold map;
   - the frozen logistic model.
   
   **Changed for this design, and only these** (each stated where it applies):
   - a cohort with a fixed start instead of risk sets;
   - building age taken at 2022-01-01;
   - ten further fold assignments made with the cohort's label.
5. **Austin's outcomes are not new to us.** The Austin study tested OPERA line-of-sight velocity against the same permit outcomes from 2018 to 2025 (Test A not demonstrated). This study tests a different, external predictor on the 2022–2025 part of those outcomes (§3).
6. **Prior expectation, stated before linkage** (revised after the planted check, §15):
   - **Unadjusted:** a clearly positive association. In the planted cells built on the Austin generating model, flagged houses had about 2.3 times the event rate from their baseline features alone (high-swelling clay, the east and south of the city).
   - **Beyond Baseline 1:** given Austin's Test A, little or no information.

## 1. Questions

- **V. Validation of the published claim (co-primary).** The paper states that buildings in high and very-high damage-risk areas have "a greater likelihood of infrastructure damage". Do Austin houses that the published risk layer places in a high or very-high class record a first foundation-repair permit at a higher rate in 2022–2025 than the other mapped houses?
  - Estimand: the incidence rate ratio (IRR), flagged against other mapped houses, **unadjusted**.
  - It is unadjusted because the claim is about the map as published. A map user does not adjust for building age or soil.
  - The age-stratified and adjusted IRRs are reported beside it in the headline table (§7).
- **U. Added information beyond the baseline (co-primary).** Does the flag add held-out information about which houses record a permit, beyond Baseline 1 + x/y? This is the thesis question (as in Austin, NYC and Alexandria), applied to an external, physics-based InSAR product.
  - Two estimands, kept separate as recommended in the research-directions report:
    - the held-out log-likelihood gain *T* (usefulness, reported with an interval);
    - the adjusted IRR (association given the baseline, tested).
- **Why both are primary** (draft 3): the planted check showed that, under the Austin generating model with no effect of the flag, V rejects in 93–100% of datasets (§15). A "validated" V alone would therefore say little about the map. The two decisions are made together under Holm's procedure (§10), so the chance of any false claim stays at 5%.

All readings concern **recorded** repair permits, as in Austin §1. None is a claim about physical damage that has been independently validated, or about cause.

## 2. Why this study

- **Gap:** published InSAR building-risk maps are not checked against damage records. The authors of the two largest (Ohenhen 2025; Sadhasivam 2025, *Nature Sustainability*) say so (`feasibility/literature_methods/SYNTHESIS.md` §2). The checks that do exist are fitted and checked on the same buildings (Ezquerro 2020; Peduto 2017, 2019).
- **What is new here:**
  - a published, fixed InSAR product;
  - an outcome period that starts after the product's data end;
  - a complete at-risk population in which every house is a control;
  - spatially separated validation;
  - a prespecified rule, frozen before any house is linked.
- **Role in the thesis:**
  - The earlier studies: Alexandria (discovery and stricter retest), NYC (frozen replication, not replicated) and Austin (preregistered, not demonstrated).
  - This is the forward-looking, external test. It uses the differential-settlement feature that the research-directions report recommends, without our own feature engineering.

## 3. What is already known (disclosure)

- **Austin outcomes:** the 2,846 events of 2018-08-01 to 2025-11-30 (`feasibility/austin/checkpoint1/events_2018.json`) were used by the Austin study with OPERA velocity.
  - By year: 2022 386, 2023 397, 2024 369, 2025 471. That is **1,623 events in 2022–2025** over all eligible houses.
  - Austin's Test A found no added held-out value of 24-month OPERA velocity (change in PR AUC −0.00058, p 0.931; `feasibility/austin/AUSTIN_RESULT.md`).
- **The map's layers,** read in step 0 (`step0/coverage.json`, script `step0/scripts/s0_coverage.py`). No outcome was read: the outcome column of the feature table was never loaded, and only the published yearly event counts were used.
  - **Published grids:** both class layers are EPSG:4326 grids of 0.0015° (about 144 m east–west × 166 m north–south, 2.4 ha), 279 × 245 cells. The paper's text describes an 80 m building-density grid; the files are used as published.
  - **Classes:**
    - Hazard (angular distortion): 0 low (below 1/3,000), 1 medium, 2 high (1/1,500 to 1/500), 3 very high (above 1/500).
    - Risk: 0 very low to 4 very high, combining hazard with building density (paper, Methods).
  - **VLM points:** 232,466 points about 21 m apart, with a standard deviation per point (median 0.29 mm/yr). VLM median −0.82 mm/yr; 5th to 95th percentile −2.13 to +0.46.
- **Coverage of the 149,316 eligible houses** (Austin option A):
  - **Risk layer:** 51.6% have a class. Very low 1,941; low 39,249; medium 31,821; high 3,258; very high 704. The paper reports 706 very-high-risk buildings in Austin.
  - **Hazard layer:** 52.7% have a class. Low 68,859; medium 7,204; high 2,628; very high 9.
    - The hazard layer covers about 1,600 houses that have no risk class.
    - Among houses with a risk class, 2,591 are hazard high or very high (60 blocks). In the hazard layer's own domain the figure is 2,637.
  - **Flagged (risk high or very high):** 3,962 houses, 5.1% of risk-mapped houses, in 212 map cells and 65 of the 213 two-kilometre blocks. The flag is constant within a map cell, so the exposed units are about 212 cells.
  - **VLM points:** the nearest point is a median 80 m from a house. 26% of houses have a point within 30 m, 37% within 50 m and 58% within 100 m.
- **Coverage is selective:**
  - **By building age:** mapped share 70% for houses built 1900–19, 37% for 1940–59, 25% for 1960–79, 59% for 1980–99 and 82% for 2000 and later.
  - **Mapped vs unmapped houses** (medians): built 1993 vs 1974; canopy share 0.32 vs 0.36.
  
  Dense canopy and older neighbourhoods are likely where InSAR coherence is lost.
- **Flagged houses differ from other mapped houses** (medians):

  | | Flagged | Other mapped |
  |---|---|---|
  | Year built | 2006 | 1993 |
  | Soil linear extensibility | 12.0 | 4.8 |
  | Canopy share | 0.06 | 0.34 |
  | Log lot area | 6.34 | 6.61 |
  | Log income | 10.94 | 11.22 |

  Among mapped houses, the risk class has these Spearman correlations: lot area −0.48 (risk includes building density), canopy −0.31, elevation −0.26, year built +0.23, soil +0.23.
- **Expected numbers if the flag were unrelated to repairs:** about 837 events among mapped houses and about 43 among flagged houses in 2022–2025. These are 1,623 × the mapped share × the flagged share.
  - The at-risk rule removes only houses whose first episode came earlier, so it changes the denominators, not these event counts.
  - The figures assume events are spread like houses. They are planning numbers, not results.

## 4. Fixed inputs

- **Map files:**
  - `risk_austin.tif`, `beta_austin.tif`, `austin_VLM.csv`, `README.rtf`, `suppTables.xlsx`.
  - Downloaded 2026-11-17 from figshare article 27606942, each checked against the repository MD5.
  - Stored in `Alex_private/ohenhen2025_raw/` with `SHA256SUMS` and the article metadata.
- **From the frozen Austin study** (unchanged; the scripts assert their hashes):
  - population and features: `population_2018.parquet`, `features_2018.parquet`;
  - blocks and fold map: `eligible_grid_folds.parquet`;
  - first episodes, events and demolition: `foundation_first_episodes.parquet`, `foundation_events.parquet`, `demolition_censoring.parquet`;
  - remodel controls: `remodel_controls_amended/`;
  - the permit download `permits_3syk-w9eu_20261109`, used in secondary 7;
  - code: `testa_core.at_risk` and `nyc_lib.model`;
  - `planted_signal/generating_coefficients.json`.
- **House point:** the parcel centroid of the 2018 polygon (EPSG:32614), as in Austin.
  - A house takes the class of the map cell that contains its point (transformed to EPSG:4326).
  - A cell with no data gives no class.

## 5. Cohort, follow-up and outcome

- **Cohort:** eligible houses (Austin §5, option A) with a risk class (§4; D4), at risk at the end of 2021-12-31 under the Austin shared at-risk rule. In `at_risk(2021-12-31, …)`, at risk means no matched foundation episode and no demolition censoring on or before that date. The rule reads episodes from 1980 on.
- **Follow-up** runs from 2022-01-01 to the earliest of:
  - the house's first matched foundation episode;
  - its demolition date;
  - 2025-11-30, the Austin study end, inclusive.
- **Event:** an Austin event (Austin §4, rules 1–8) dated within follow-up.
  - A first episode that is not an event (Austin rule 8, recent construction) ends follow-up without an event. Such cases are counted.
- **Person-time:** in days from 2022-01-01 to the exit, converted to years of 365.25 days.
  - A house followed to the end gets all 1,430 days (3.915 years).
  - An exit by episode or demolition counts its day as half a day.
- **Flow diagram (RECORD/STROBE):** 149,316 eligible houses → with a risk class → at risk at the end of 2021 → with complete Baseline 1 (U). The losses at each step are given by flag.
- **Depletion before follow-up (descriptive, no decision):** by flag, the share of mapped eligible houses that leave before 2022 through an episode dated 2018-08-01 to 2021-12-31.
  - If the map also flags houses that recorded repairs in 2018–2021, those houses have left the cohort. The 2022–2025 contrast is then biased toward the null.
  - This table reads pre-2022 outcomes by flag, so it is computed with the real run, not before freezing.

## 6. Predictor

- **Primary (D2):** flagged = the published risk class is high or very high (3–4), against the mapped classes 0–2. This is the paper's own wording of the claim.
- **Other codings** (secondaries, §11):
  - the five risk classes;
  - the hazard layer;
  - VLM at the house.
- No threshold, class merger or smoothing is chosen from the data.

## 7. Co-primary analysis (V)

- **Model:** Poisson regression of the event indicator with log person-years as offset and the flag as the only covariate. IRR = exp(coefficient), the ratio of the two incidence rates.
- **Inference:** **r3**, chosen by the user after the planted check (§9, branch 2; §15), from these candidates:
  - **r1:** cluster-robust (CR1) Wald with errors clustered by the Austin 2 km block;
  - **r2:** wild cluster score bootstrap (Kline and Santos 2012) by 2 km block;
  - **r3:** wild cluster score bootstrap by 6 km block (3 × 3 Austin blocks on the same grid);
  - **r4:** wild cluster score bootstrap by 12 km block.
  
  The bootstraps use Webb six-point weights (Webb 2023), 9,999 draws, seed 2061. The bootstrap is used because few clusters hold flagged houses (MacKinnon and Webb 2017).
- **What the chosen inference gives:**
  - a one-sided p for IRR > 1;
  - **two-sided 90% and 95% intervals**, from inverting the test over a grid of 801 log-IRR values from log 0.2 to log 5. Their bounds are one-sided 95% and 97.5% bounds, so they agree with p < 0.05 and p < 0.025.
  
  The reading uses the interval that matches the test's Holm level (§10). Both are reported.
- **Headline table** (one row each, all with the chosen inference):
  - the unadjusted IRR (V's test);
  - the age-stratified IRR, with strata of year built up to 1989, 1990–2009 and 2010–2015: a Poisson model with stratum indicators, inferred like the others, with the Mantel–Haenszel estimate beside it;
  - the IRR adjusted for Baseline 1 + x/y (U's test, §8);
  - the hazard-flag IRR (secondary 2).
- **Also reported:**
  - the incidence per 1,000 house-years in each group;
  - the rate difference, with the intervals implied by the IRR intervals (the rate among other mapped houses held fixed);
  - the absolute counts;
  - the E-value of the unadjusted IRR and of its bound nearer 1 at V's Holm level (§10; VanderWeele and Ding 2017);
  - **as a screening tool:** the share of events in flagged houses (sensitivity), the share of flagged houses with an event, the excess events in flagged houses, and the number of flagged houses per excess event.

## 8. Co-primary (U)

- **Rows:** cohort houses with complete Baseline 1 (Austin §9).
  - Outcome: an event in follow-up (0/1).
  - Houses censored by demolition count as 0 and are counted.
- **Models:** the frozen Austin logistic model (`nyc_lib.model("LR")`).
  - M0: Baseline 1 + x/y, with building age at 2022-01-01 (Austin took age at each event date; here the cohort has one start).
  - M1: M0 + the flag.
- **Statistic T:** the mean, over 11 fold assignments, of the out-of-fold log-likelihood gain of M1 over M0. The gain is summed over houses, with probabilities clipped at 1e-15.
  - **Fold assignments:** the Austin fold map (seed 42), then the same function with seeds 0–9: StratifiedGroupKFold over 2 km blocks, with the label "house has an event in follow-up".
  - This is the statistic of the Alexandria retest. It was chosen on synthetic data only (`feasibility/austin/planted_signal/statcmp_20261117/`).
- **Interval for T:** refit block bootstrap with 2,000 resamples of the 2 km blocks, seed 2052, for the co-primary U only. Copies keep their block's fold in every assignment, and resamples that leave a fold without a positive are skipped and counted. In the secondaries (2, 3, 8), U reports T and the adjusted IRR without a bootstrap interval. T has no p-value of its own.
- **Association given the baseline:** the adjusted IRR of the flag, from a Poisson model with offset on Baseline 1 + x/y + flag, with the inference chosen for V (r3). Its one-sided p (IRR > 1) is U's test in Holm's procedure (§10).
- **Decision:** see §10. T, its interval and the adjusted IRR are always reported.
- **In the secondaries** (2, 3, 8; descriptive): "added information detected" if T > 0 and the adjusted IRR's one-sided p < 0.05; "not detected" otherwise.
- **Also reported:**
  - the change in PR AUC (seed-42 assignment) and in ROC AUC;
  - the change in Brier score;
  - the calibration intercept and slope of M1's out-of-fold predictions;
  - observed against predicted risk by decile of M1.

## 9. Planted check (before freezing; synthetic outcomes only)

- **Purpose:** choose the inference by its false-positive rate when outcomes and the map are both spatially clustered but unrelated, and measure power.
- **Setting:**
  - the real risk-mapped houses and the real map;
  - the at-risk rule, which reads outcomes, is replaced by a fixed follow-up of 3.915 years (1,430 days, 2022-01-01 to 2025-11-30) for every house;
  - synthetic events are drawn Bernoulli per house, which matches the Poisson model with a common exposure;
  - the intercept is set so that each dataset expects 837 events, the step-0 planning figure (§3).
- **Hidden field:** a stationary Gaussian random field independent of the map, built from 2,000 random Fourier features (squared-exponential covariance), on the logit scale.
- **Reference for the field's size (outcome only, no map):** the between-block standard deviation of the log event rate over 2018-08-01 to 2021-12-31, by method of moments over the 2 km blocks. It is computed when the planted inputs are prepared and recorded in §15. It shows which cells resemble Austin; it does not change the rule.
- **Cells:** null cells have 1,000 datasets and power cells 500. Master seed 20261119.

  | Cell | Linear predictor | Role |
  |---|---|---|
  | 1 | field, range 1 km, SD 0.5 | V null |
  | 2 | field, range 3 km, SD 0.5 | V null |
  | 3 | field, range 8 km, SD 0.5 | V null |
  | 4 | field, range 15 km, SD 0.5 | V null |
  | 5 | field, range 3 km, SD 1.0 | V null (stress) |
  | 6 | field 3 km SD 0.5 + a linear trend in a random direction, changing the logit by 1.0 across 40 km | V null |
  | 7 | Austin generating coefficients (Baseline 1 + x/y) + field 3 km SD 0.5 | U null (500 datasets) |
  | 8 | as 7 with the soil term squared (nonlinear) | U null, reported only (500) |
  | 9 | field 3 km SD 0.5 + log(1.5) × flag | V power at δ |
  | 10 | field 3 km SD 0.5 + log(2.0) × flag | V power at 2.0 |
  | 11 | as 7 + log(1.5) × flag | U power at 1.5 |

- **Acceptable in a null cell:**
  - the rejection rate's lower 95% Wilson bound is at most 0.05;
  - the rejection rate is at most 0.075;
  - no positive bias: the mean estimated log IRR has a 95% interval whose lower bound is at most 0.
  
  Rejection means IRR > 1 and one-sided p < 0.05. With 1,000 datasets, the Monte Carlo SE of a 5% rate is 0.7 percentage points.
- **Rule** (fixed before any result):
  1. The first of r1, r2, r3, r4 that is acceptable in all six V null cells becomes the inference for V and U.
  2. If none is acceptable, the user decides before freezing.
- **Result** (§15): no candidate was acceptable in all six cells; all fail cell 4 (15 km range). Branch 2: the user chose **r3** on 2026-11-17 (`step0/inference_choice.json`, which records the planted summary's hash). r3 fails only cell 4 (7.3%, Wilson 5.8–9.1%). r4 also fails cell 4 (6.4%) and has less power (56.8% against 65.2% at IRR 1.5).
- **Reported** (no switch):
  - the U null cells: the adjusted-IRR test's rejection rate and T's null distribution;
  - V's rejection rate in cell 7. It is not expected to be nominal, because the baseline features are related to the flag and V is unadjusted.
  - power in cells 9–11.

## 10. Decisions (V and U, co-primary, Holm)

- **Tests:** two one-sided tests, both with the chosen inference (r3):
  - **V:** the unadjusted IRR > 1 (§7);
  - **U:** the IRR adjusted for Baseline 1 + x/y > 1 (§8).
- **Holm's procedure** (family-wise error 0.05):
  1. The test with the smaller p is tested at 0.025. (A tie goes to V first.)
  2. If it is rejected, the other is tested at 0.05. If not, neither is rejected, and the other stays at level 0.025.
- **Interval for each reading:** the two-sided interval whose one-sided level matches the test's Holm level: **95%** at level 0.025, **90%** at level 0.05. So a test is rejected exactly when its interval's lower bound is above 1.
- **V readings:**

  | Reading | Condition |
  |---|---|
  | **Validated, enrichment of δ or more not excluded** | rejected and upper bound ≥ 1.5 |
  | **Validated, enrichment below δ** | rejected and upper bound < 1.5 |
  | **Not validated, useful enrichment excluded** | not rejected, 1 ≤ upper bound < 1.5 |
  | **Not validated, inconclusive** | not rejected, upper bound ≥ 1.5 |
  | **Not validated, opposite** | upper bound < 1 |

- **U readings:** the same conditions on the adjusted IRR, with these words:
  - **"Added information demonstrated"** (with "enrichment of δ or more not excluded" or "below δ") requires that Holm rejects U's test **and** T > 0.
  - If Holm rejects but T ≤ 0: **"added information not demonstrated: association beyond the baseline without a held-out gain"**.
  - Otherwise: "added information not demonstrated", with "useful enrichment excluded", "inconclusive" or "opposite" as for V.
- **δ = IRR 1.5 (authors' choice, D3).** It is the smallest enrichment that would make the flag worth acting on as a screen.
  - At the expected 3.9-year risk of about 1.1%, 1.5 means about 1.6% among flagged houses.
  - That is roughly 21 extra recorded repairs among about 4,000 flagged houses over the follow-up.
  - Less than that adds little to triage, given that inspection effort would go to about 190 flagged houses per extra repair.
- **Wording:**
  - V's reading is about the **unadjusted** contrast that the paper claims, for recorded repair permits in the map's own domain.
  - U's reading is about information beyond age, size, soil, terrain, location and income.
  - "Not validated" does not say that the map's 25-year hazard is wrong.
  - A validated V with U not demonstrated is read as follows: the map flags houses that record more repairs, but not beyond what the baseline features already show. The planted check makes this the expected pattern if the map adds nothing (§15).
- **Power and error under Holm** (planted records, r3; §15):
  - **V:** at IRR 1.5 (cell 9), 65.2% at level 0.05 and 51.2% at 0.025; at IRR 2.0 (cell 10), 97.6% and 93.6%.
  - **U:** under the Austin generating model V is almost always rejected first (94–100% of datasets in cells 7, 8 and 11), so U is in practice tested at 0.05. "Added information demonstrated" at IRR 1.5 beyond the baseline (cell 11): 75.8%. With no flag effect (cells 7 and 8): 4.8% and 3.6%.
  - **V's false-positive rate at 0.025** in the null cells 1–6: 1.4%, 1.5%, 2.2%, 4.6%, 0.7%, 2.6%.
  
  Power at δ is below 80% for both, and the summary says so. Power is reported as the design's sensitivity; the interval-based readings are unchanged.
- **E-values** (VanderWeele and Ding 2017): of the unadjusted IRR and of the interval bound nearer 1, at V's Holm level.
- **Beside the decisions (no change to them):** the age-stratified IRR, the E-values and secondaries 5–7.

## 11. Secondary analyses (descriptive; nominal p-values, no multiplicity correction, no claims beyond §10)

1. **Per class:** incidence by risk class (0–4) and a trend IRR per class step.
2. **Hazard layer:** V and U with flagged = hazard high or very high (2–3), in the hazard layer's domain; incidence by hazard class. Also the overlap of the risk and hazard flags.
3. **VLM at the house:**
   - the mean of the VLM points within 50 m of the house point (houses with at least one point);
   - V as the IRR per 1 mm/yr of subsidence (VLM sign reversed), and U with VLM in place of the flag;
   - the overlap of VLM in its lowest decile with the two flags.
4. **The map user's domain:** all eligible houses; those without a class count as not flagged.
5. **Building age:** IRR within each age stratum (§7); IRR adjusted for age at 2022-01-01 only.
6. **Within neighbourhoods:** a conditional Poisson model with 2 km block fixed effects.
7. **Construction nearby:** excluding houses with **at least 10** residential BPs of work class New dated 2015-01-01 to 2021-12-31 within 150 m (Austin permit download; date = application, or issue if missing). Permits are located at the centroid of the 2018 TCAD parcel whose `PID_10` equals their `tcad_id`. Permits on parcels created after the 2018 layer cannot be located and are counted. The threshold of 10 was set from permits alone, before any linkage. A single permit nearby is common across Austin (infill homes, secondary units: 60% of eligible houses have one within 150 m). Ten or more marks a subdivision or a multi-unit development (12% of eligible houses, 29% of flagged houses). Distortion in new subdivisions may record construction and fill settlement rather than movement under existing houses.
8. **Remodel negative control:** V and U with Austin remodel control events (2022–2025) as the outcome, with the same cohort rules.
9. **By year:** IRR for 2022, 2023, 2024 and 2025 separately.
10. **Overlapping period, not prospective:** IRR for 2018-08-01 to 2021-12-31, with houses at risk from 2018-08-01, and a pooled 2018-08-01 to 2025-11-30 estimate. This is retrospective (the InSAR period overlaps), labelled so, and is not a bias correction. The depletion table of §5 goes with it.
11. **Cell edges:** excluding houses within 30 m of an edge of their map cell where the neighbouring cell has a different flag.
12. **Demolition as a competing event:** the demolition IRR by flag (cause-specific Poisson, same cohort). Flagged areas are newer, so fewer demolitions are expected.
13. **Inference not chosen:** V and U under the other candidates of §7.

## 12. Limits

- **The outcome:** a permit records an owner's decision to repair, not when or whether damage happened (Austin §4 limits). Under-recording that follows income and geology is addressed by the age-stratified and adjusted analyses and the remodel control, not removed.
- **Confounding:** flagged houses are newer and on clay. The unadjusted IRR mixes the map's information with these, in opposite directions. The headline table shows how much each moves it.
- **The map's domain:** about half the houses, selected by InSAR coherence (younger, less canopy). Results do not transfer to unmapped areas; secondary 4 shows the map user's view.
- **Resolution:**
  - A class covers about 2.4 ha, with a median of 11 eligible houses per mapped cell. The map describes areas, not buildings, as its authors state.
  - Point-in-cell errors near cell edges are likely non-differential and bias toward 1 (secondary 11).
- **Timing:**
  - The 25-year angular-distortion horizon is longer than the 3.9-year follow-up, so a weak short-term association does not refute the 25-year hazard.
  - Repairs recorded in 2022–2025 can follow damage that began earlier.
  - Depletion of flagged houses by 2018–2021 repairs biases toward the null (§5).
- **Seen outcomes:** the 2022–2025 outcomes were used by the Austin study with a different predictor (§3). The map, the cohort rule and the analysis are fixed here before any linkage.
- **One city:** the other 27 cities' layers are public. Any city with a damage or repair record could repeat this plan.

## 13. Order of work

1. **Step 0** (done 2026-11-17): download, hashes, outcome-blind coverage (§3, §15).
2. **Scripts:**
   - the planted generator and the analysis code, checked on synthetic outcomes;
   - the analysis refuses real outcomes until `FROZEN_SHA256` is set;
   - the field-size reference of §9 is computed when the planted inputs are prepared.
3. **Planted check** (§9; done 2026-11-17), then the inference choice: branch 2, the user chose r3 (§15).
4. **User approval and freeze** (this draft): `freeze/OHENHEN_AUSTIN_PLAN_frozen.md` is created and its SHA-256 is set as `FROZEN_SHA256` in `run_analysis.py` and recorded in §15.
5. **Real run:** `run_analysis.py real` with `step0/planted_20261117/planted_summary.json` and `step0/inference_choice.json`: V, the headline table, U with the Holm decisions (§10), then the secondaries in the order of §11, with start and end times.
6. **Result document,** with a RECORD/STROBE checklist and the flow diagram.

## 14. Deviations log

(Empty until freezing.)

## 15. Records

- **2026-11-17, step 0:**
  - map files downloaded and MD5-checked (`Alex_private/ohenhen2025_raw/SHA256SUMS`; risk 68a6e4a2…, beta 3a742b6a…, VLM 2ab7fc62…);
  - `step0/scripts/s0_coverage.py` → `step0/coverage.json` (fc2a6d70…); the numbers are in §3;
  - New York's three layers were downloaded with Austin's for possible later use. They are not part of this plan.
- **2026-11-17, scripts:** `scripts/oa_core.py`, `scripts/planted.py` and `scripts/run_analysis.py`.
  - `run_analysis.py` refuses real outcomes until `FROZEN_SHA256` is set. Its decoy mode gives every real date to random houses (seed 2071).
  - **Decoy runs on the PC:** a full decoy run with a stand-in inference choice completed all of §7, §8 and secondaries 1–12 (19:17–20:10). It gave an IRR near 1, as expected for randomised outcomes.
  - **Fixes from the decoy runs:**
    - The Poisson fitter now halves a Newton step that would lower the log-likelihood, and falls back to least squares for a singular system. The first decoy failed in secondary 3: a restricted fit at an extreme grid value with a continuous predictor overflowed.
    - Secondary 7 now requires at least 10 new-construction permits within 150 m (§11; set from permits only).
- **2026-11-17, planted inputs** (`planted.py prepare`; `step0/planted_inputs.npz` 4db326cd…, `planted_inputs.json` 04de3508…):
  - 76,973 risk-mapped houses, 3,962 flagged; 73,099 with complete Baseline 1, 3,694 of them flagged.
  - Clusters among mapped houses: 195 two-km blocks (65 with flagged houses), 34 six-km blocks (24), 11 twelve-km blocks (9).
  - **Field-size reference** (outcome only, no map value): 1,223 events of 2018-08-01 to 2021-12-31 over the 213 blocks of all eligible houses. Between-block SD of the log rate: 0.628.
- **2026-11-17, planted check** (`step0/planted_20261117/`; summary ad5d0285…, `PLANTED.md` 327ae22b…):
  - **Run:** 8,500 datasets, 16 workers on the PC, 18:58–20:19 (81 min).
  - **Code check:** the Poisson fitter changed during the run (the step-halving and fallback above). 21 records were recomputed with the final code: 20 are byte-identical; in one, the estimate differs in the 14th significant digit and every p-value is identical.
  - **V false-positive rates** in the null cells (1,000 datasets each):

    | Cell | r1 | r2 | r3 | r4 |
    |---|---|---|---|---|
    | 1 (1 km) | 5.3% | 3.6% | 3.0% | 3.8% |
    | 2 (3 km) | 7.4% ✗ | 3.8% | 3.2% | 5.5% |
    | 3 (8 km) | 10.5% ✗ | 6.0% | 4.6% | 4.4% |
    | 4 (15 km) | 13.0% ✗ | 9.2% ✗ | 7.3% ✗ (Wilson 5.8–9.1%) | 6.4% ✗ (Wilson 5.0–8.1%) |
    | 5 (SD 1.0) | 7.0% ✗ | 4.2% | 2.4% | 2.7% |
    | 6 (trend) | 11.4% ✗ | 7.7% ✗ | 5.4% | 5.9% |

    The bias criterion holds in every cell: the mean log IRR's 95% interval has a lower bound ≤ 0.
  - **Rule:** no candidate is acceptable in all six cells, because all fail cell 4 (a hidden field with a 15 km range, in a city about 40 km across). **Branch 2: the user decides before freezing.**
  - **V power:**
    - at IRR 1.5 (cell 9): r1 78.6%, r2 69.4%, r3 65.2%, r4 56.8%;
    - at IRR 2.0 (cell 10): r1 99.6%, r2 99.0%, r3 97.6%, r4 93.8%.
  - **U null** (cell 7, Austin generating model + field):
    - the adjusted test rejects 8.6% (r1), 5.4% (r2), 5.8% (r3), 5.6% (r4);
    - "added information detected" (T > 0 and p < 0.05): 7.0%, 4.8%, 4.8%, 4.2%;
    - T: mean −1.00, 5–95% −4.44 to 2.53, positive in 24% of datasets.
    
    Cell 8 (nonlinear soil): detected 3.6–5.6%.
  - **U power** (cell 11, IRR 1.5 beyond the baseline): detected 78.6% (r1), 76.8% (r2), 75.8% (r3), 66.6% (r4).
  - **Disclosure (new before freezing).** In cells 7 and 8, outcomes follow the Austin generating model, which was fitted to the real 2018–2025 outcomes, and the flag has no effect of its own. Even so, the unadjusted IRR averaged exp(0.825) = 2.3 (cell 7) and exp(0.742) = 2.1 (cell 8), and V rejected in 93–100% of datasets.
    - Flagged houses carry the baseline features that the Austin model links to repairs: high-swelling clay, and the east and south of the city.
    - V is therefore expected to come out "validated" through those features whether or not the map adds anything. The adjusted contrast (U) is the informative test.
    - This is a planted-cell property of the Austin model, not the real IRR. It replaces the prior expectation of design point 6.
- **2026-11-17, inference choice (branch 2):** the user chose **r3** (wild cluster score bootstrap, 6 km blocks). Recorded in `step0/inference_choice.json` with the planted summary's SHA-256 (ad5d0285…); `run_analysis.py` asserts that hash.
- **2026-11-17, co-primary decision:** after the disclosure above, the user made V and U co-primary under Holm's procedure (§10).
  - `run_analysis.py` now computes both decisions with Holm, the reading interval at each test's Holm level, and the E-value at V's level.
  - A decoy run with r3 and the Holm code (secondaries skipped) gave "V not validated, useful enrichment excluded | U added information not demonstrated, useful enrichment excluded", as expected for randomised outcomes.
  - Added after that decoy: the rate-difference intervals implied by the IRR intervals (§7), checked on a synthetic input.
  - **Holm-level figures** from the planted records (r3; computed after the user's decision, reported in §10, no change to any rule): V rejects at 0.025 in 51.2% of cell 9 and 93.6% of cell 10. In cells 7, 8 and 11, V is rejected first in 95.8%, 94.0% and 100%. U demonstrated (Holm and T > 0): 4.8% (cell 7), 3.6% (cell 8), 75.8% (cell 11). V at 0.025 in null cells 1–6: 1.4%, 1.5%, 2.2%, 4.6%, 0.7%, 2.6%.
- **2026-11-18, FREEZE** (user: "Freeze and run"). `freeze/OHENHEN_AUSTIN_PLAN_frozen.md` SHA-256
  **60aac893384f145d82c9b806ae3711938fc8f6c29264eb40e87f5b27d9358f75**, frozen at 07:27 UTC (`freeze/FROZEN_AT.txt`).
  - Frozen with it (read-only, `freeze/MANIFEST.sha256`): `scripts/oa_core.py` (509e3f27…), `planted.py` (7b065123…),
    `run_analysis.py` (e96c46a0…, with `FROZEN_SHA256` set), and from step 0 `inference_choice.json` (024047a7…),
    `planted_summary.json` (ad5d0285…), `PLANTED.md`, `planted_inputs.json`, `coverage.json`.
  - From here on, this working copy differs from the frozen plan only in §14 and §15.
- **2026-11-18, real run started** 09:28 EET on the PC (16 jobs): `run_analysis.py real` into `real_20261118/`.
- **2026-11-18, real run complete** 10:21:10 EET (V 09:28:28, headline 09:29:27, U 10:05:59). `real_20261118/results.json`
  SHA-256 **57b1d1105a282d40751ced7037fe979eed36f10a3ebca3b9f528ac7f5cd74437**, with the frozen code hashes. No deviation.
  - **Decisions (§10, Holm):**
    - **V: validated, enrichment of δ or more not excluded.** IRR 3.23, 95% interval 1.59 to beyond the grid (> 5),
      p 0.002, tested first at 0.025 and rejected.
    - **U: added information not demonstrated, inconclusive.** Adjusted IRR 1.16, 90% interval 0.69–1.75, p 0.298,
      tested at 0.05 and not rejected. T −4.65, 95% bootstrap interval −30.1 to +28.9 (2,000 of 2,000 resamples kept).
  - **Cohort:** 73,256 houses, 3,709 of them flagged. 127 events in 14,252 person-years among flagged houses; 744 in
    269,633 among the others.
  - **Result document:** `OHENHEN_AUSTIN_RESULT.md`, generated by `scripts/result_report.py` (f11d89c7…), which
    asserts the frozen hashes. It contains the decisions, the headline table, U in detail, the secondaries, the
    interpretation, the limits and the RECORD/STROBE checklist.

## 16. Drafts and decisions

- **Draft 1 (2026-11-17):** questions V and U, flag, Poisson IRR with clustered errors, planted check, readings.
- **User decisions (2026-11-17), all as recommended:**
  - D1: V primary, U key secondary.
  - D2: primary predictor = risk high or very high.
  - D3: δ = IRR 1.5.
  - D4: mapped houses only, with the map user's view as secondary 4.
- **Draft 2 (2026-11-17), after an independent referee review of draft 1.** Adopted:
  - **Interval:** a two-sided 90% interval for the readings, so that bounds and one-sided p agree. Draft 1 mixed a one-sided 0.05 test with 95% bounds.
  - **Readings:**
    - The "validated" reading now separates enrichment of δ or more from enrichment below δ.
    - The power caveat no longer overrides the interval: power is reported as sensitivity.
  - **Headline table:** age-stratified (Mantel–Haenszel) and adjusted IRRs beside the decision; E-values.
  - **Inference candidates:** wild cluster score bootstrap candidates (2, 6 and 12 km) after CR1, chosen in a fixed order.
  - **Planted cells:** range 15 km, a SD 1.0 stress cell, a random linear trend, 1,000 datasets per null cell, and an outcome-only reference for the field's size.
  - **New secondaries:**
    - the depletion table and a pooled retrospective estimate;
    - a cell-edge exclusion;
    - demolition by flag;
    - calibration by decile;
    - overlap of the flags.
  - **Reporting and text:**
    - a RECORD/STROBE flow diagram;
    - the prior expectation stated;
    - the changes from Austin listed (cohort start, age date, fold assignments);
    - the 2,591 vs 2,637 hazard counts explained;
    - the at-risk date harmonised (end of 2021-12-31);
    - the secondaries declared descriptive.
- **Draft 3 (2026-11-17), after the planted check:**
  - **Inference:** r3 (wild cluster score bootstrap by 6 km block), chosen by the user under branch 2 of §9 (no candidate passed cell 4).
  - **V and U co-primary, Holm** (user decision; replaces D1's "V primary, U key secondary"). Reason: under the Austin generating model with no flag effect, V rejected in 93–100% of planted datasets, so V alone cannot show that the map adds anything.
    - Each reading uses the interval at its test's Holm level (95% at 0.025, 90% at 0.05).
    - "Added information demonstrated" requires Holm's rejection of the adjusted IRR and T > 0.
  - **The disclosure** of the planted cells 7–8 and the revised prior expectation (design point 6).
  - **Secondary 7:** at least 10 new-construction permits within 150 m, set from permits only.
  - **Code fixes** from the decoy runs: Poisson step-halving and the least-squares fallback; the rate-difference intervals.
- **2026-11-18: the user approved draft 3 for freezing** ("Freeze and run").
- **Not adopted** (authors' choice):
  - **Translating the map at random as the null.** Each shift moves no-data cells over houses, so the mapped cohort changes in every draw. The wild cluster bootstrap handles few clusters without that.
  - **A placebo map from another city.**
  - **A 6 km fold map for U.** The 11 assignments already vary the folds, and U's test (the adjusted IRR) uses the 6 km inference.
  - **A cell-level analysis.** The clustered inference already treats cells within blocks as dependent.
