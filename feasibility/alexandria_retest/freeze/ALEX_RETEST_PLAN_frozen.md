# Alexandria: registered stricter retest of the LiCSAR association (plan)

**Status: FROZEN 2026-11-18 (draft 4, approved by the user: "Freeze + qualifier"). Written by Claude; asked by the user
with "ok go ahead", targeting a Q1/Q2 contribution.
The user approved D1–D4 as recommended on 2026-11-17 (§16). After the planted check ended in branch 3 of §9, the
user chose on 2026-11-18 the conditional null (c2) as primary, with a flexible-baseline secondary (14) checked on
planted data before freezing (§9, §10, §16). After that check, the user chose on 2026-11-18 to freeze with a
qualifier rule ("Freeze + qualifier", §7).**
Draft 1 was reviewed the same day by an independent referee-style read (Sonnet subagent); draft 2 answers it
(changes listed in §16). Nothing in this plan has been computed on real outcomes. It was frozen after the user
approved it and step 0 (§9) was complete. After freezing, the frozen copy is never edited; changes go to §14 and
records to §15, as in the Austin plan.

**What this is.** A reanalysis of a result that has already been seen: the LiCSAR test of 2026-09-30
(`data/pilot/LICSAR_TEST.md`: PR AUC 0.328 → 0.413, +0.085, largest p 0.005 over six unconditional nulls; 241
cells, 32 collapse cells, 63 events). The data, cells, events, features and model stay as they were. Only the
inference changes, to a stricter form. **The statistic and the null were chosen after the Alexandria result and
after the Austin statistic comparison were known;** the plan fixes every remaining choice before the new statistic
or the new null touches the real outcomes, and the result is reported as a registered robustness analysis of a
known result, not as a confirmation.

**Decisions for the user before freezing** (Claude's recommendation first):
- **D1. Primary statistic:** the change in out-of-fold log-likelihood, averaged over the 11 fold assignments the
  original study already used (§5). Alternatives: the change in PR AUC; or one fold assignment (seed 42) only.
- **D2. Primary null:** a covariate-conditional variogram null on the radar-pixel field, averaged into cells
  (§6), with the conditional fit chosen in step 0 between two registered candidates (§9). Alternative: the
  cell-level variogram-matching null of the original test.
- **D3. Three outcomes, not two:** robust / not robust / inconclusive, where "inconclusive" means the test had
  less than 80% power at the observed effect (§7). Alternative: robust / not robust.
- **D4. Population:** the original 241 cells (32 collapse cells); the 341 core cells are secondary.

## 1. Role in the paper (Q1/Q2 target)

The thesis paper is planned as one study across three cities: a discovery in Alexandria, a frozen replication in
New York (not replicated) and a frozen test in Austin (not demonstrated, 2,719 events). This retest answers the
question a Q1/Q2 reviewer asks first about the discovery: *does it survive the inference the later studies used?*
All three outcomes are informative and their readings are fixed in advance (§7).

**Contributions the paper can claim** (positioning from `feasibility/literature_methods/SYNTHESIS.md`; journal
quartiles still to be verified against Scimago):
1. No published study found applies a held-out, baseline-compared test of whether InSAR adds information about
   where buildings are damaged. This study applies it in three cities, two of them preregistered.
2. A method for this test under spatial autocorrelation: a covariate-conditional surrogate null at the radar-pixel
   scale, a held-out likelihood statistic, and a planted-signal check that measures size and power on the real
   field. On the Austin design and under Austin's conditional null, the held-out log-likelihood gain doubled power
   at β = −0.1 (34% → 66%) with no rise in false positives (7.0% → 4.7% pooled over three no-effect cells, 300
   datasets; 2026-11-17). Whether that transfers to 32 positives is measured only by step 0 here.
3. A substantive answer on what 30–100 m InSAR velocity can and cannot locate, with effect sizes and intervals.

**Candidate venues** (to verify): Remote Sensing of Environment; ISPRS Journal of Photogrammetry and Remote
Sensing; IEEE Transactions on Geoscience and Remote Sensing; IEEE JSTARS; International Journal of Applied Earth
Observation and Geoinformation; Natural Hazards and Earth System Sciences; International Journal of Disaster Risk
Reduction.

## 2. Question and hypothesis

**Question.** In the historic core of Alexandria, does LiCSAR vertical velocity over the collapse period add
held-out information about which 250 m cells contain a structural collapse (2014–2016), beyond the urban/coastal
baseline and location, under a null that keeps velocity's dependence on the baseline features and its spatial
structure?

**Null hypothesis (primary).** Given the baseline features and linear x/y, the cell's velocity carries no further
information about whether it contains a collapse. The null keeps velocity's fitted dependence on the baseline
features and the spatial structure of the remainder.

**What the primary test does not exclude, and where it is checked.** A smooth, nonlinear location effect that
velocity tracks is neither in M0 (linear x/y only) nor in the part every surrogate keeps (the conditional fit
excludes coordinates). It is checked by planted cell 4 (§9) and by secondary 2 (smooth location in the baseline,
§10). Nor does it exclude a **nonlinear effect of a baseline feature** that velocity partly carries: velocity
correlates with elevation (|ρ| 0.58), and in planted cell 2 (a nonlinear elevation effect, no velocity effect)
every null, including the original one, rejected in 8–10% of datasets (§15). It is checked by secondary 14
(flexible baseline, §10), which rejected in 3.0% of that cell's datasets (§15). A robust decision is qualified
when secondary 14 does not reject (§7).

**Scope.** The velocity overlaps the collapses (P1 ends 2016-12-31; events 2014–2016), so this is a concurrent
association, not a precursor test. A precursor test needs events from 2017 on (synthesis, section 3).

## 3. Fixed from the original test (unchanged)

Hashes of every input file are recorded in §15 at freezing and asserted by the code.
- **Events:** the 63 target events of `data/pilot/target_events.csv` (rule in `data/pilot/PILOT_REPORT.md` §1),
  at the assigned points used in the original test.
- **Cells:** 250 m grid of `data/pilot/cells_250m.csv`. **Primary population:** the 241 cells of the original
  primary test (`scripts/17_licsar_test.py`, `test_cells(250, "shirzaei", "lic_ud_p1")`: historic-core cells,
  Shirzaei-covered, all baseline inputs; all have a LiCSAR value), 32 collapse cells (prevalence 13.3%). A cell is
  positive if a target event's point falls in it.
- **Baseline:** built-up share 2015, share built by 1975, net building height 2018, log building count, ground
  elevation, distance to the 2021 shoreline (`scripts/07_pilot_models.py` BASELINE), plus x/y in km.
- **Velocity:** LiCSAR vertical velocity P1 (`data/licsbas/decomposed/P1_UD.geo.tif`, mm/yr, positive up), cell
  value = mean of the valid pixels whose centres fall in the cell (`scripts/16_licsar_cells.py`). It enters the
  models raw (mm/yr); the model pipeline's StandardScaler, fitted within each training fold, scales it, as in the
  original test. Surrogate cell values enter the same way. There is no other standardisation.
- **Model:** logistic regression, StandardScaler + C = 1 (`scripts/07_pilot_models.py` `model`).
- **Folds:** the original fold map (`scripts/07_pilot_models.py` `fold_map`): 2 km blocks dealt into 5 folds by
  StratifiedGroupKFold, built once on all 3,300 eligible city cells and stratified on all 50 of their positive
  cells, then read at the 241 cells. At seed 42 the 241 cells span 16 blocks; the folds hold 51, 56, 38, 23 and 73
  cells with 7, 7, 1, 5 and 12 collapse cells. Seeds 0–9 are the original fold check's alternatives.
- **Anchor:** before anything new is computed, the code reproduces the original primary result (seed 42: PR AUC
  0.328 → 0.413, +0.085) from these inputs. If it does not, nothing proceeds until the difference is explained in
  §14.

## 4. What changes, and why

| Change | Original test | This retest | Why |
|---|---|---|---|
| Statistic | change in out-of-fold PR AUC, one fold assignment | change in out-of-fold log-likelihood, mean over 11 fold assignments (D1) | More power at the same false-positive rate on the Austin design; uses every predicted probability, not only the ranking; tests the same hypothesis (Pepe et al. 2013, *Statistics in Medicine*, 10.1002/sim.5727). With 16 blocks and one fold holding a single collapse cell, one split can sway the result; averaging over the original study's 11 splits removes that dependence. |
| Null | six unconditional nulls at cell level; decision on the largest p | conditional variogram null on the pixel field, averaged into cells (D2) | The original variogram check found every null rougher than the field at the shortest lag, which tends to make p too small; generating at the pixel scale and averaging reproduces how cell values are made. Conditioning removes gains that velocity gets by standing in for the baseline features (Austin calibration: the unconditional null rejected up to 30% of datasets under a misspecified covariate effect). |
| Size and power | not measured | planted-signal check at Alexandria's size before the real run (§9) | A reader must know what the test could detect with 32 collapse cells. |
| Outcomes | replicated / not replicated | robust / not robust / inconclusive (D3) | A non-significant result at low power is not evidence against the association. |

## 5. Primary analysis

- **Rows:** the 241 cells. **Label:** collapse cell or not.
- **Models:** M0 = baseline + x/y; M1 = M0 + P1 velocity. For each fold assignment f (seed 42 and seeds 0–9),
  each model is fitted on four folds and predicts the fifth.
- **Statistic:** for each f, Δℓ_f = ℓ_f(M1) − ℓ_f(M0), where ℓ_f is the Bernoulli log-likelihood summed over all
  241 cells' out-of-fold probabilities, Σ [y log p + (1 − y) log(1 − p)], p clipped to [1e-15, 1 − 1e-15].
  **T = the mean of Δℓ_f over the 11 assignments.** Positive = velocity improves held-out prediction.
- **Direction:** the velocity coefficient of M1 fitted on all 241 cells, in mm/yr⁻¹ and per SD of cell velocity
  (β̂). Negative = collapse cells sink relative to others (the original direction).
- **Effect sizes, always reported:** T and T per collapse cell (T/32); Δℓ_42 alone; Δℓ per fold of seed 42; the
  change in PR AUC (seed 42 must be +0.085; also the mean over 11 assignments), against the prevalence 0.133;
  the change in ROC AUC; collapse cells in the top 10%; β̂ and its odds ratio per SD; the collapse and background
  medians of P1 velocity (the original criterion 2); the change in Brier score (seed 42 and mean of 11); the
  calibration of M0's and M1's seed-42 out-of-fold predictions: the slope b of y ~ a + b·logit(p) and the intercept
  in the large a of y ~ a + offset(logit p). Intervals: refit block bootstrap over the 16 blocks (2,000
  resamples, seed 2042; copies keep their block's fold, both models refitted, as `scripts/09_core_statistics.py`).
  Leave-one-block-out T (16 values) is reported to show whether a few blocks dominate.

## 6. Primary null: conditional variogram null on the pixel field

- **Field (draft 3):** all valid pixels of `P1_UD.geo.tif` whose centres fall in the 241 primary cells (1,357
  pixels; every cell holds at least one). Pixel centres in UTM 36N. Draft 2 used the 341 core cells; the
  outcome-blind variogram check showed that field to be rougher than the 241 cells' (the velocity field is not
  stationary across the core), so surrogates matched to it had 1.4–1.9 times the observed semivariance at the
  241 cells (`step0/VARIOGRAM_CHECK_v1.md`, `step0/null_variants_exploration.txt`).
- **Conditioning (draft 3):** each pixel carries its own cell's design; pixels in one cell share it. Pixel velocity
  is regressed by ordinary least squares, in-sample and outcome-blind, on one of two designs, chosen in step 0
  (§9):
  - **(c1)** the six baseline features (Austin's rule: no coordinates);
  - **(c2)** M0's full design, the six baseline features and x/y in km: the spatial analogue of Freedman–Lane
    residual randomisation (Freedman and Lane 1983), in which the nuisance covariates of the tested model are
    regressed out, the residual is randomised, and the fitted part is added back. It keeps velocity's planar
    trend in every surrogate, which M0 already uses. **Chosen by the user on 2026-11-18 after the planted check
    (§9, branch 3).**
  The fitted part is kept in every surrogate. Draft 2's HistGradientBoosting fits were dropped after the
  outcome-blind check: with cell-level covariates, Austin's settings explained 96% of pixel velocity (they
  reproduce the cell means, so every surrogate would be almost the observed field), and the cross-fitted variant
  was 2–5 times rougher than the field at short lags.
- **Surrogates:** the residual field is replaced by variogram-matched surrogates with the unchanged NYC/Austin
  generator (`lowmem_null.py`, or its CPU adapter `CPULowMemVariogramNull` in `cpu_null.py`, as used for Austin's server
  runs; the CPU path must agree with the GPU path within 1e-12 on a test field, as Austin's check). Lags are pixel-pair distances in metres divided by 100 and
  rounded (as `nyc_lib.Lags`), lags 1–16; neighbour cap 1,000. The fitted part is added back. 999 draws, seed
  2043.
- **Cell values:** each surrogate is averaged over the valid pixels of each cell, exactly as the observed cell
  value, and enters the models raw.
- **p-value:** p = (1 + draws with T ≥ observed T) / (1 + 999), each draw's T computed over the same 11 fold
  assignments.
- **Variogram check, read first; after freezing it is never used to change the null** (before freezing it was used,
  outcome-blind, to correct the field and the fit; draft 3): pixel level, lags 1–16 × 100 m; cell level,
  lags 1–6 × 250 m (the generator matches only to 1.6 km, so longer cell lags are not expected to match). Median
  and 95% range of the surrogates against the observed field, with pair counts per lag, as
  `data/pilot/LICSAR_VARIOGRAM_CHECK.md`. The conditional fit's explained variance is reported.
- **Draws are shared:** the same 999 surrogates serve every analysis and every planted dataset, so planted
  rejection rates are correlated across datasets (as in Austin). This is stated with the results.

## 7. Decision rule (fixed now)

Let p be the primary null's p-value for T, and β̂ the direction of §5.

1. **Robust to the stricter test** if T > 0, p < 0.05 and β̂ < 0.
2. Otherwise, **inconclusive** if the planted power at the observed effect (§9, cell 7) is below 80%.
3. Otherwise, **not robust to the stricter test.**

The original criterion 2 (collapse cells' median P1 velocity strictly below the background cells') is reported
beside the decision. If it disagrees with the sign of β̂, the disagreement is reported and the decision stands.

**Readings (fixed now):**

| Outcome | Reading |
|---|---|
| Robust | The concurrent association between LiCSAR velocity and collapse cells holds under a calibrated conditional null and a held-out likelihood statistic averaged over fold assignments, at the size and power stated by the planted check. The NYC and Austin non-replications are then not explained by a lenient test in Alexandria. It remains a concurrent association in one historic core with news-derived labels; secondaries 9 and 10 bound how much of it could be a post-collapse radar artefact. |
| Inconclusive | The stricter test could not have detected an effect of the size observed with adequate power. The original result is neither confirmed nor refuted by it; the paper reports the effect size with its interval and the power. |
| Not robust, T > 0 and β̂ < 0 | The test had adequate power at the observed effect, yet a field with velocity's structure and its dependence on the baseline produces gains this large in at least 5% of draws. The original p-values were too small. |
| Not robust, T ≤ 0 or β̂ ≥ 0 | Under held-out likelihood the velocity model does not predict better than the baseline, or not in the original direction. The original gain was specific to PR AUC's ranking of a few cells or to one fold assignment. |
| Robust with a linear baseline only (qualifier below) | The association holds under the stricter null with the original test's linear baseline, but not when the baseline features enter flexibly. Part of the gain may be a nonlinear effect of a baseline feature that velocity carries (the pattern of planted cell 2). |

**Qualifier (draft 4; the user's decision of 2026-11-18, §16). It does not change the decision.**
- Secondary 14 (flexible baseline, §10) is computed with the primary, under the primary null with the same 999
  draws.
- If the decision is robust and secondary 14 does not reject (T > 0, p < 0.05 and β̂ < 0 are not all met), the
  decision is stated everywhere as **"robust to the stricter test with a linear baseline only: not robust to a
  flexible baseline (secondary 14)"**.
- On the planted data (§15), an unqualified robust reading occurred in 1.8% of cell 1, 2.6% of cell 2 and 71.6% of
  cell 7 datasets. A robust decision, qualified or not, occurred in 4.4%, 10.0% and 86.0%.

Reported beside the decision, without changing it: the effect sizes and intervals of §5; the full 2 × 2 of
statistic × null (§10.1), presented next to the decision in every summary; the planted power curve.

## 8. Synthetic data rule

No real outcome is joined to any new statistic or new null until the plan is frozen. Before freezing, real
outcomes are used only:
- (a) to reproduce the anchor (seed 42, Δ PR AUC +0.085);
- (b) to fit the generating baseline model of the planted check (§9), whose coefficients are hashed and recorded
  in §15 before any planted dataset is drawn;
- (c) to compute β̂ of §5 (the original M1 refitted on all cells; this is an effect size of the already-seen
  model, not the new statistic), which sets planted cell 7.

## 9. Step 0 before freezing: planted-signal check at Alexandria's size

Synthetic outcomes on the real 241 cells, the real baseline features, the real velocity field and the real
surrogates. Code adapted from `feasibility/austin/planted_signal/planted_signal.py`.
- **Generating model:** M0 (baseline + x/y, logistic, StandardScaler + C = 1) fitted on all 241 cells with the
  real labels; scaler, coefficients and intercept are saved, hashed and recorded first. Its in-sample and
  out-of-fold (seed 42) ROC AUC are reported, and so is the mean ROC AUC of M0 on the cell-1 datasets, to show
  whether synthetic data are easier than the real data (real out-of-fold M0 ROC AUC: 0.746).
- **Datasets:** 32 positive cells per dataset (the real count), drawn sequentially without replacement with
  probability ∝ exp(η), where η is the generating model's linear predictor plus the cell's term. Seeds:
  SeedSequence([20261118, cell, dataset]).
- **Folds in planted datasets:** the fold map is rebuilt for each dataset by the original rule (`fold_map`,
  StratifiedGroupKFold on all 3,300 eligible cells, seeds 42 and 0–9), with the dataset's synthetic labels in the
  241 cells and the real labels elsewhere. The positives per fold are recorded.
- **Cells, 500 datasets each:**
  1. nothing added;
  2. nonlinear covariate effect: 0.65 · t, where s = z(the baseline feature with the largest |Spearman ρ| with
     cell P1 velocity over the 241 cells; ties broken by BASELINE order; outcome-blind; the feature is recorded)
     and t = z(max(s − 0.7, 0)²) (Austin cell 2);
  3. hidden spatial field independent of velocity: 0.7 · H, white noise on a 50 m grid over the cells' extent
     padded by 2.4 km, Gaussian filter σ = 600 m (12 px), mode "reflect", truncate 4, read at the cell centres,
     z-scored over the 241 cells (Austin cell 3);
  4. **smooth location effect that velocity tracks:** 0.7 · L, where L = z(the cell P1 velocity field smoothed
     by a Gaussian kernel of σ = 1 km over the centres of the 341 core cells with a LiCSAR value, read at the 241
     cells). The outcome
     depends on the large-scale pattern of velocity (a location effect), not on the cell's own deviation from it.
     A test that is not fooled by location should rarely reject here;
  5.–6. velocity effect β · u, u = z(cell P1 velocity over the 241 cells), β = −0.25 and −0.5 (odds ratio per SD
     1.28 and 1.65). The effect is on the total cell velocity, which is what M1 uses (Austin's power cells did
     the same);
  7. **observed effect:** β = β̂ per SD from §8(c) (if β̂ ≥ 0, β = −|β̂| is used and noted);
  8. location noise: as cell 6 (β = −0.5), then each positive is moved, with probability 0.2, to a random one
     of its eight neighbouring cells among the 241 (if none is free, it stays).
- **Tested in each dataset:** T and the seed-42 change in PR AUC, each under the primary conditional null with
  (c1) and with (c2) (999 draws each), and under the original plain variogram-matching null at cell level (999
  draws, seed `M.SEED + 1` = 2027 as `scripts/11_msr_variogram_check.py` BURT_SEED). This gives the primary test's
  size and power for each candidate fit, and shows whether the original null was lenient at Alexandria's size.
- **Acceptable** in a no-effect cell (1–4), for a statistic–null pair: the rejection rate's lower 95% Wilson bound
  ≤ 0.05; its point estimate ≤ 0.075; and the paired bias (observed T minus the mean of its null draws, per
  dataset, in units of T) has a Student-t 95% interval over datasets whose lower bound ≤ 0. Rejection means p <
  0.05 with T > 0 and β̂ < 0 (the rule of §7, item 1). With 500 datasets, a true rate of 7.5% has a lower Wilson
  bound of about 5.5%.
- **Rule (registered before any planted result):**
  1. If T under (c1) and under (c2) are both acceptable in cells 1–4, the primary null uses the one with the
     higher rejection rate in cell 6 (ties: c2).
  2. If only one is acceptable in cells 1–4, it is used.
  3. If neither is, nothing is frozen, and the user decides with the planted results in hand. The statistic is not
     switched to Δ PR AUC by rule.
  Power in cells 5–8 is reported. Cell 6 enters only to choose between two acceptable nulls. Cell 7 sets the
  "inconclusive" branch of §7.
- **Result (2026-11-18, §15): branch 3.** Neither c1 nor c2 was acceptable in all of cells 1–4. c2 was the only
  candidate acceptable in cell 1 (4.4%); it failed cell 2 (10.0%; every null failed, the original 8.2%) and, on the
  paired-bias criterion only, cells 3 and 4 (rates 3.4% and 1.6%). **The user chose c2 as the primary null**
  (`step0/null_choice.json`, which records the planted summary's hash) and asked for a flexible-baseline secondary
  (14) whose false-positive rate in cells 1–2 and power in cell 7 are measured on the same synthetic datasets
  before freezing (`scripts/planted_spline.py`; §15). **Power at the observed effect under c2: 86.0%** (cell 7), so
  §7's "inconclusive" branch does not apply.
- **Flexible secondary (2026-11-18, §15):** it rejected in 2.4% and 3.0% of cells 1–2 and had 73.0% power in cell
  7. The user then chose to freeze with the qualifier of §7.
- **Also in step 0, outcome-blind:** the variogram check of §6 for both fits; explained variance of both fits;
  timing.

## 10. Secondary analyses (exploratory; nominal p; no multiplicity correction; no decision)

Each changes one thing in the primary analysis and uses the primary null unless stated.
1. **2 × 2 of statistic × null:** T and the change in PR AUC (seed 42 and mean of 11), each under the primary null
   and under the original six cell-level nulls (largest p). Presented beside the decision.
2. **Smooth location in the baseline:** M0 and M1 add a smooth of x/y: cubic B-spline bases of x and of y
   (scikit-learn `SplineTransformer`, 5 knots at quantiles of the 241 cells, degree 3; additive in x and y) and
   the product x·y, in the same logistic model, where the L2 penalty of C = 1 applies to them too.
3. **All 341 core cells with a LiCSAR value** (34 collapse cells; original secondary 1).
4. **Location uncertainty carried through:** 100 redraws of each event's point along its matched street geometry
   (the method of `scripts/07_pilot_models.py`, `PILOT_REPORT.md` §8, which used 20 draws; intersections and the
   one junction fixed; seed 2044). The statistic is the mean T over the 100 labelings; each of 999 null draws is
   scored on the same 100 labelings (about 100 × the primary cost; server).
5. **200 m cells** (original secondary 2).
6. **Random forest** (original settings; 500 draws).
7. **P2, the full period** (original secondary 4).
8. **Each frame's line of sight, P1** (original secondary 5).
9. **Timing of collapse relative to the velocity window.** P1 rests mainly on November 2015 – December 2016, so a
   2014–2015 collapse was usually observed afterwards, over rubble or rebuilding. Two analyses with the same
   background cells: positives = cells whose target events are all in 2014–2015; positives = cells with a 2016
   target event. If the association is a post-collapse radar artefact, it should be stronger in the first.
10. **Radar coverage:** (a) the number of valid pixels per cell as the only added predictor; (b) the primary
    analysis with the pixel count added to M0 and M1. Rubble and rebuilding lower coherence, so coverage could
    carry the signal instead of motion.
11. **Persistence: P3**, a linear fit from 2019-01-01 to the last epoch on the same LiCSBAS cumulative displacement
    and mask (`LiCSBAS_cum2vel.py`), decomposed as P1. Descriptive comparison with P1.
12. **Unconditional pixel null:** T under the unconditional variogram null on the same pixel field (Austin's null
    (a) generator), to separate the effect of conditioning from the effect of the pixel scale.
13. **Lesser damage as an outcome:** cells with a located partial-element event (falls of balconies or façade
    elements) and no target event, as the label instead of collapse; same analysis. There is no clean
    negative-control outcome: only 2 located external-accident events exist.
14. **Flexible baseline** (draft 4): each of the six baseline features is replaced in M0 and M1 by its cubic
    B-spline basis (scikit-learn `SplineTransformer`, degree 3, 5 knots at the quantiles 0, 0.25, 0.5, 0.75 and 1 of
    the 241 cells, `include_bias=False`, 6 columns per feature; a feature whose five quantile knots are not distinct
    gets 5 uniform knots over its range instead: share built by 1975); x/y stay linear (secondary 2 treats
    location); the same logistic pipeline (StandardScaler, C = 1); T, β̂ and the change in PR AUC under the primary
    null (c2). It targets the weakness found in planted cell 2: a nonlinear effect of a baseline feature that
    velocity partly carries. Its false-positive rate in cells 1–2 and power in cell 7 were measured before
    freezing on the same synthetic datasets (§15: 2.4% and 3.0%, against 4.4% and 10.0% for the primary; power
    73.0% against 86.0%) and are reported with it. It is computed by `run_primary.py` together with the primary
    (same draws), because the qualifier of §7 depends on it; the script asserts that its design is byte-identical
    to the one checked on planted data.

## 11. Known limits (stated now)

- The result has been seen, and the statistic and null were chosen knowing it and the Austin comparison. The plan
  protects only against choices made after seeing the new statistic or null on the real outcomes.
- Concurrent, not precursor. Collapses and demolition change radar scatterers; secondaries 9 and 10 bound the
  effect, they do not exclude it.
- 32 collapse cells in 16 blocks: power is limited, and the planted check states it.
- Labels come from news reports; background cells may hold unrecorded collapses.
- P1 rests mainly on November 2015 – December 2016 (network gaps in 2015). LiCSBAS's default thresholds kept 38–39%
  of pixels; masking is not random. The vertical decomposition assumes no north–south motion. Each frame's
  reference point fixes an arbitrary offset; the models use differences between cells only, and a constant offset
  cannot change any statistic here. The collapse and background medians (0.06 and 0.64 mm/yr) differ by less than
  the usual uncertainty of a one-to-two-year LiCSAR velocity at a single pixel; the analysis rests on the pattern
  over cells, and the per-pixel velocity uncertainty (LiCSBAS step 14 standard deviation) is reported for the
  collapse and background cells.
- Pixels are 0.001° (about 95 × 111 m): a cell value averages about six pixels and cannot resolve a building.
- 2 km blocks are comparable to the 1.6 km over which the generator matches the field, so some spatial leakage
  across folds remains; larger blocks are not feasible with 16 blocks.
- **The primary null is not calibrated against every alternative** (planted check, §15): under a nonlinear
  elevation effect it rejected in 10.0% of datasets (every null did, 8–10%), and under a hidden field and a smooth
  location effect the null mean of T sat below the observed mean even though the rejection rates were 3.4% and
  1.6%. A robust result carries the qualifier of §7 when secondary 14 (flexible baseline) does not reject, and is
  read together with secondary 2 (smooth location).

## 12. Order of work and safeguards

0. User approves D1–D4 and this draft.
1. Code written and checked on synthetic fields; anchor reproduced; generating coefficients and β̂ recorded (§15).
2. Step 0: variogram check, planted-signal check, rule of §9 applied and recorded (§15).
3. Plan frozen: copy in `freeze/`, hash recorded, all input and code hashes asserted.
4. Real run: primary (with secondary 14 and the qualifier of §7), then the other secondaries in the order of §10.
5. Result document, generated from the records by code, as Austin's.

Compute: the pixel field has 1,357 pixels and the models 241 rows; one model fit takes about 2.4 ms (PC,
193 rows, 2026-11-17). The planted check (8 cells × 500 datasets × 3 nulls × 999 draws × 11 fold assignments × 5
folds of M1 fits) was projected at about 7 hours from the PC's fit time; the server smoke test (2026-11-17, 703 s
per dataset with 2 workers) projects about 12 hours on 64 workers; secondary 4 at minutes. Both run on the
server, by the standing rule for heavy runs; the machine of each run is recorded in §15.
- **Timing gate (planted check):** after the first 64 datasets, the projected time is written down before any
  further dataset runs. If it exceeds 24 hours, every cell runs 300 datasets instead of 500.

## 13. Authors' choices made in this draft (not user decisions)

Seeds 2042–2044 and 20261118; 500 datasets per planted cell; 100 location draws; the 241-cell pixel field; lag unit
100 m; β = −0.25 and −0.5; the σ of the hidden field (600 m) and of the location field (1 km); 20% location
noise; the two linear designs (c1) and (c2); the spline basis for secondary 2; the spline basis of secondary 14 and its knot rule; the 24-hour timing gate; the choice of the nonlinear covariate
by |Spearman ρ|.

## 14. Deviations log

(empty)

## 15. Freeze record

Records written before freezing (step 1 and step 0). The plan is not yet frozen.

- **2026-11-17. Step 1: anchor, generating model, beta-hat** (Claude; PC; `scripts/step1_anchor.py`
  `c0a97733…`, run with `retest_core.py` `ca0a3bd5…`, the version before the draft-3 null change, which touched
  only the null classes). Record `step1/step1.json` (`be581ffc…`).
  - **Inputs (SHA-256 prefixes):** `data/pilot/cells_250m.csv` b0a66785, `licsar_cells_250m.csv` 4096b774,
    `target_events.csv` 88319996, `P1_UD.geo.tif` 61ca6ba5, ADM2 boundaries d5a319ad.
  - **Anchor:** seed-42 PR AUC 0.32812 → 0.41313, change +0.08501 (rounds to the original 0.328 → 0.413, +0.085);
    the original plain variogram-matching null's 999 draws reproduced within 1.0e-16, p 0.005. The seed-42 fold
    map rebuilt by `fold_map` equals the saved folds.
  - **Generating model** `step1/generating_model.json` (`f6098458…`): M0 on all 241 cells with the real labels;
    in-sample ROC AUC 0.825, seed-42 out-of-fold 0.746 (the original's).
  - **beta-hat** (original M1 refitted on all 241 cells; §8 c): −1.156 per SD of cell velocity (odds ratio 0.315
    per SD), −0.652 per mm/yr. Collapse and background medians 0.059 and 0.642 mm/yr. Planted cell 7 uses
    β = −1.156.
  - **Folds:** the 241 cells span 16 blocks; at seed 42 the folds hold 7, 7, 1, 5 and 12 collapse cells; over the
    11 assignments the smallest test fold has 1 collapse cell and the smallest training set 20.
  - The new statistic T was not computed on real outcomes.
- **2026-11-17. Step 0: variogram check, first version (draft 2's null)** (PC; outcome-blind). `step0/surrogates_v1.npz`
  (`9a28673c…`), `variogram_check_v1.json` (`d82cedb4…`), `VARIOGRAM_CHECK_v1.md` (`07eb2837…`). Findings and the
  resulting change: §16, draft 3. Exploration: `scripts/explore_null_variants.py` (`5ab094b1…`),
  `step0/null_variants_exploration.txt` (`5d1ddbd6…`).
- **2026-11-17. Step 0: variogram check of the draft-3 nulls** (PC; outcome-blind; `scripts/make_surrogates.py`
  `4f8f9f54…`, `retest_core.py` `299076d8…`). 999 draws each, seed 2043, 1,357 pixels of the 241 cells.
  `step0/surrogates.npz` (`31312c48…`), `variogram_check.json` (`5a1c2c54…`), `VARIOGRAM_CHECK.md` (`ae7c718c…`).
  - Explained variance: c1 0.485, c2 0.629.
  - Cell level, surrogates' median / observed at lags 1–6 × 250 m: c1 0.95, 0.85, 0.76, 0.72, 0.71, 0.69 (all inside
    the 95% range); c2 0.77*, 0.77, 0.76, 0.76, 0.76, 0.75 (lag 1 just outside, smoother); unconditional pixel null
    0.76, 0.84, 0.84, 0.87, 0.89*, 0.89*; original plain cell-level null 1.93*, 1.43, 1.22, 1.11, 1.04, 0.97.
  - Pixel level: c1 and c2 are rougher than the field at lags 1–2 (c1 2.98, 1.71; c2 2.30, 1.34), because the fitted
    part is constant within cells; at the cell level, which enters the models, this averages out.
- **2026-11-17. Step 0: planted-signal inputs** (PC; `scripts/planted.py prepare`, `planted.py` `e818fb50…`).
  `step0/planted_inputs.npz` (`03c0b825…`), `planted_inputs.json` (`d8baabec…`). No real label of the 241 cells is
  stored (blanked in the city-wide label column; the fold rule receives synthetic labels there). Cell-2 feature:
  elevation (|Spearman ρ| with P1 velocity 0.580; height 0.562, distance to shore 0.451, others ≤ 0.249).
  - Re-prepared after a fix to the summary step (it failed on one dataset per cell in the smoke test): the inputs file
    is byte-identical (`03c0b825…`); `planted_inputs.json` is now `2ea2558a…` (it records `planted.py` `3528f3d7…`).
- **2026-11-17. Step 0: planted-signal smoke test and launch** (server, `~/AmrGamal/work/run_alex_planted.sh`). Smoke:
  cells 1 and 7, dataset 0, 2 workers, 15:28–15:39; 703 s per dataset. Cell 7 dataset 0: T +6.882, seed-42 PR AUC
  change +0.0629, beta-hat −1.33, p 0.007 (c1), 0.016 (c2), 0.005 (plain). Full run (cells 1–8 × 500 datasets,
  64 workers) started 15:43:23 into `~/AmrGamal/work/alex_planted_20261117`; server load from other users was about 27.
- **2026-11-17. Real-run script written and checked on synthetic labels** (`scripts/run_primary.py` `e040a767…`). It
  refuses real outcomes until `FROZEN_SHA256` is set to the frozen plan's hash. On planted cell 7, dataset 0 (40
  draws, 30 resamples, PC) it reproduced the smoke record's T (+6.882) and PR AUC change (+0.0629) exactly.

- **2026-11-18. Step 0: planted-signal check complete** (server, 64 workers, 2026-11-17 15:43 – 2026-11-18 06:00;
  4,000 datasets, 0 errors in `run.log`/`stdout.log`). Copied to `step0/planted_20261117/` (records, logs,
  `planted_summary.json` `6f785363…`, `PLANTED.md` `a01e6ee2…`). **The summary was rebuilt on the PC from the copied
  records (`planted.py summarise`) and is byte-identical**; the records' source hashes equal the PC's `planted.py`
  (`3528f3d7…`), `retest_core.py` (`299076d8…`) and inputs (`03c0b825…`).
  - **T in the no-effect cells** (rejection = p < 0.05, T > 0, β̂ < 0; Wilson 95%; paired bias = mean of observed T
    minus null mean, 95% t interval):

    | Cell | c1 | c2 | original plain null |
    |---|---|---|---|
    | 1. nothing added | 5.6% [3.9, 8.0], bias +0.40 [+0.20, +0.59] ✗ | **4.4% [2.9, 6.6], bias +0.13 [−0.06, +0.33] ✓** | 6.4% [4.6, 8.9], bias +0.78 ✗ |
    | 2. nonlinear elevation | 8.8% [6.6, 11.6] ✗ | 10.0% [7.7, 12.9] ✗ | 8.2% [6.1, 10.9] ✗ |
    | 3. hidden field | 4.6%, bias +0.43 [+0.11, +0.75] ✗ | 3.4%, bias +0.41 [+0.10, +0.73] ✗ | 5.4%, bias +0.93 ✗ |
    | 4. smooth location | 0.8%, bias +0.23 [+0.08, +0.37] ✗ | 1.6%, bias +0.25 [+0.09, +0.40] ✗ | 0.8%, bias +0.63 ✗ |

  - **Rule of §9: branch 3** (neither c1 nor c2 acceptable in cells 1–4). Nothing is frozen; the user decides.
  - **Power of T** (same rejection rule): cell 5 (β −0.25) c1 18.4%, c2 15.0%; cell 6 (β −0.5) 38.0%, 29.2%;
    **cell 7 (observed β −1.156) 93.0%, 86.0%**; cell 8 (β −0.5, 20% location noise) 38.6%, 30.6%. Plain null:
    21.0%, 41.2%, 95.4%, 43.4%.
  - **Diagnosis** (descriptive, computed from the records after the summary):
    - The raw p-values of c2 are near nominal in cells 1, 3 and 4 (p < 0.05 in 5.2%, 4.6%, 6.0%; p < 0.10 in
      9.2%, 12.4%, 10.2%). Its failures there are on the paired-bias criterion only: the null mean of T sits
      0.13–0.41 below the mean observed T (cells 1, 3, 4), and the null SD (2.1, 3.1, 2.0) is close to the SD of
      observed T over datasets (2.3, 3.9, 1.8), so the shift moves few p-values below 0.05.
    - Cell 2 fails for every null, including the original one: velocity correlates with elevation (|ρ| 0.58), so
      when the outcome depends on elevation nonlinearly, velocity carries part of that effect beyond the linear
      baseline and T gains under any null that keeps the linear baseline. This is a property of the linear
      baseline model, not of the null.
    - The original plain null is the most lenient: positive bias in all four cells (+0.63 to +0.93) and 6.4% in
      cell 1.
    - Mean β̂ in cell 1 is −0.21 per SD although the generator has no velocity term (sequential draws without
      replacement are not exactly logistic); in cell 4 it is +0.13.
- **2026-11-18. User decision after branch 3:** c2 as the primary null, with the flexible-baseline secondary checked
  on planted data ("c2 + spline check"). Recorded in `step0/null_choice.json` (`c93fe768…`; planted summary `6f785363…`,
  power at the observed effect 0.86).
- **2026-11-18. Real-run script updated for draft 4** (`scripts/run_primary.py` `db7e3047…`): `--null-choice` (asserts
  the planted summary's hash), the change in Brier score and the calibration of M0 and M1. Checked on planted
  cell 7, dataset 0 (20 draws, 10 resamples, PC): T +6.882 and PR AUC change +0.0629 as in the smoke record;
  Brier change −0.0028 (seed 42); calibration slope M0 0.34, M1 0.47.
- **2026-11-18. Planted check of secondary 14 launched** (server, `~/AmrGamal/work/run_alex_planted_spline.sh`,
  `scripts/planted_spline.py` `2149637c…`, 64 workers, 09:31) into `~/AmrGamal/work/alex_planted_spline_20261118`:
  cells 1, 2 and 7 × 500 datasets, null c2, the same synthetic datasets as the main check (`planted.draw_labels`, same
  seeds; with the linear baseline, `run_primary.py` on cell 7, dataset 0 gives the main record's T +6.882). Spline knots: quantile for five features, uniform
  for the share built by 1975 (tied quantiles).
- **2026-11-18. Planted check of secondary 14 complete** (server run 09:31–11:50; copied to
  `step0/planted_spline_20261118/`, 1,500 records; summarised on the PC with `planted_spline.py summarise`, which pairs
  each dataset with its main-check record: `planted_spline_summary.json` `a81a41f8…`, `PLANTED_SPLINE.md` `7b0c0a2b…`).
  Rejection (p < 0.05, T > 0, β̂ < 0) under c2, 500 datasets per cell:

  | Cell | Flexible baseline (secondary 14) | Paired bias of T (flexible) | Linear baseline (main check) | Both reject |
  |---|---|---|---|---|
  | 1. nothing added | 2.4% [1.4, 4.1] | +0.13 [−0.11, +0.37] | 4.4% | 1.8% |
  | 2. nonlinear covariate | 3.0% [1.8, 4.9] | +0.34 [+0.12, +0.56] ✗ | 10.0% | 2.6% |
  | 7. β = observed | 73.0% [68.9, 76.7] | — | 86.0% | 71.6% |

  - The flexible baseline removes the excess rejections of cell 2 (10.0% → 3.0%). It fails cell 2 on the paired-bias
    criterion only, as c2 did in cells 3–4 of the main check.
  - The cost is power at the observed effect: 73.0% against 86.0%.
  - Raw p < 0.05 (any sign): 3.8% and 4.4% in cells 1–2. Mean β̂ (flexible): −0.14, −0.10, −1.35.
- **2026-11-18. User decision after the spline check: "Freeze + qualifier"** (§7, §16). `scripts/run_primary.py`
  (`69406f49…` before `FROZEN_SHA256` was set) now:
  - computes secondary 14 with the primary, under the primary null with the same draws;
  - applies the qualifier of §7;
  - asserts the flexible design's SHA-256 (`a9fa9565…`, the planted check's) and the surrogates' SHA-256
    (`31312c48…`, from `step0/planted_inputs.json`).
  
  **Checked on the PC** with 999 draws (20 resamples and 50 permutations only), about 5 minutes per dataset on 16 jobs:
  - **Planted cell 2, dataset 19:** robust (p 0.015). Secondary 14: T −4.848, p 0.896, so the **qualifier is applied**.
  - **Cell 7, dataset 0:** robust (p 0.016). Secondary 14: T +16.151, p 0.001, so there is no qualifier.
  - Every T, p and β̂ equals the planted records, both the main check and the spline check.

## 16. Revisions before freezing

- **Draft 2 (2026-11-17), after the referee-style review of draft 1:**
  - Statistic averaged over the original 11 fold assignments (the 241 cells span 16 blocks; one fold at seed 42
    holds one collapse cell). Sign condition β̂ < 0 added to the rule. "Inconclusive" outcome added (power below
    80% at the observed effect). The 2 × 2 is presented beside the decision.
  - Conditional fit chosen in step 0 between Austin's fit (c1) and a cross-fitted, more regularised fit (c2); the
    rule no longer switches the statistic to PR AUC.
  - Planted check: 500 datasets per cell (was 100); new cells for a smooth location effect that velocity tracks
    (4), the observed effect (7) and location noise (8); folds rebuilt per dataset by the original rule; the
    generator's ease reported.
  - New secondaries: smooth location in the baseline (2), collapse timing relative to the velocity window (9),
    radar coverage as a covariate (10b).
  - Ambiguities fixed: velocity enters raw and is scaled inside the pipeline; ℓ is a sum over all cells; the
    pixel field and cell-level covariates defined; the original null's seed named; cell-level variogram check
    limited to lags 1–6; the CPU tolerance stated; D3's comparison strict.
  - **2026-11-17: the user approved D1–D4 as recommended** (statistic averaged over 11 fold assignments; conditional
    pixel null; three outcomes; the original 241 cells), by answering the four questions. Step 1 (code, anchor,
    generating model) starts; the plan is not frozen before step 0 is complete.
- **Draft 3 (2026-11-17), after the outcome-blind variogram check of step 0** (no label read; the user had approved
  D2 as "the conditional pixel null"; this revision keeps it and changes its field and fit):
  - **What the check found** (`step0/VARIOGRAM_CHECK_v1.md`): on the draft-2 field (1,821 pixels of 341 cells),
    Austin's HistGradientBoosting fit explained 95.7% of pixel velocity, because pixels in a cell share the cell's
    covariates and the fit reproduces the cell means; its surrogates correlate 0.99 with the observed cell values,
    so the null would have almost no power. The cross-fitted fit explained 43.7% but its surrogates were 2.75 times
    the observed semivariance at the first cell lag. Even the unconditional pixel null averaged into the 241 cells
    had 1.7–1.9 times the observed semivariance at every cell lag: the 100 extra cells are rougher than the 241.
  - **Exploration** (`scripts/explore_null_variants.py`, 199 draws, `step0/null_variants_exploration.txt`):
    restricting the field to the 241 cells' pixels and fitting linearly brought the cell-level ratios to
    0.68–0.94 (baseline only, all inside the 95% range) and 0.75–0.77 (baseline + x/y, first lag just outside).
    Flexible fits on the restricted field explained 80–89% and kept most of the observed field.
  - **Change:** field = the 241 cells' pixels; candidates (c1) OLS on the baseline and (c2) OLS on baseline + x/y,
    chosen by the unchanged rule of §9. The full check on 999 draws is `step0/VARIOGRAM_CHECK.md`: at cell level
    c1 is inside the 95% range at all six lags (ratios 0.69–0.95) and c2 at five (0.75–0.77; lag 1 just smoother);
    the original plain null is 1.93 times rougher at lag 1.
  - **Direction of the remaining mismatch:** both new nulls are somewhat smoother than the field at cell level, which
    tends to make p larger (conservative); the planted check measures the result.
  - The review's point that the Austin statistic comparison was run under Austin's null (a) was checked and is
    not correct: `run_planted.sh` used `surrogates_conditional.npy`, the conditional null (b). The plan says so.
- **Draft 4 (2026-11-18), after the planted check** (synthetic outcomes only; the new statistic and nulls have not
  touched the real outcomes):
  - **Planted check: branch 3 of §9** (§15). The user chose **c2** as the primary null ("c2 + spline check"):
    c2 was the only candidate acceptable in the clean no-effect cell; its failures were shared by every null (cell
    2) or on the paired-bias criterion with rejection rates at or below 6% (cells 3–4). c1 had more power at the
    observed effect (93.0% against 86.0%) but failed cell 1 on bias and cell 2 at 8.8%.
  - **New secondary 14 (flexible baseline)** with its own planted check on cells 1, 2 and 7 before freezing
    (`scripts/planted_spline.py`, server).
  - **Effect sizes added (§5):** the change in Brier score and the calibration intercept and slope of M0 and M1
    (authors' choice, planned since draft 3 for the paper's effect-size table; no separate Spatial+ analysis).
  - **§2 and §11** state the nonlinear-covariate weakness and how it is read.
  - **2026-11-18, after the spline check: the user chose "Freeze + qualifier"** (alternatives offered: require both
    baselines, which would have left "not robust" unreachable at a joint power of 71.6%; or freeze as is). Added:
    the qualifier and its reading in §7, secondary 14 computed with the primary (§10), and the matching lines in §2,
    §9, §11 and §12. The user approved draft 4 for freezing with this change.

