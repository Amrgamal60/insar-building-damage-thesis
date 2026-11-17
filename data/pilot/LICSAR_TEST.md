# LiCSAR test of the historic-core result

**Plan, fixed before any LiCSAR velocity existed:** `LICSAR_TEST_PLAN.md`. **Velocity:** `LICSAR_CELLS.md`. **Null check, read before this run:** `LICSAR_VARIOGRAM_CHECK.md`.
**Reproduce:** `.venv/bin/python scripts/17_licsar_test.py` (after 15, 16 and `17_licsar_test.py --check`).

- **Primary test:** the historic-core cells at 250 m of `CORE_STATISTICS.md` that have a LiCSAR value; logistic regression; baseline + x/y vs baseline + x/y + LiCSAR vertical velocity P1 (first epoch to 2016-12-31); statistic = change in out-of-fold PR AUC. Same 63 events, folds (seed 42), features and settings as the Shirzaei test.
- **Nulls:** the six of `VARIOGRAM_NULL.md`, fitted to the LiCSAR field: free and within-block permutation (2,000 draws each), MSR and amplitude-adjusted MSR (999 each) and variogram-matching, plain and with the observed values (999 each). p = (1 + draws with a change ≥ observed) / (1 + draws).
- **Decision rule:** replicated only if all three criteria hold; otherwise not replicated. Secondary tests carry no decision.

## Decision: Replicated

| Criterion | Value | Met |
|---|---|---|
| 1. PR AUC change is positive | +0.085 | yes |
| 2. Collapse cells' median vertical velocity is below the background cells' | 0.06 vs 0.64 mm/yr | yes |
| 3. Largest p of the six nulls is below 0.05 | 0.005 | yes |

## Result

- **Decision: replicated.** Primary test on 241 core cells (32 collapse cells, none dropped): PR AUC 0.328 → 0.413 (+0.085). The collapse cells' median vertical velocity is 0.06 mm/yr against 0.64 for background cells (single-layer ROC AUC 0.44). p = 0.001–0.005 under the six nulls; the largest, 0.005, comes from the within-block permutation and both variogram-matching nulls. All three criteria hold.
- **Larger than with Shirzaei** on the same cells, events, folds and model: Shirzaei gave +0.044 (largest p 0.023, `VARIOGRAM_NULL.md`).
- **Secondary tests all point the same way.** The change is +0.069 to +0.085 in every test, and the collapse cells' median is lower in every test. The largest p is below 0.05 in five of six: all 341 core cells with a LiCSAR value (0.007), random forest (0.038; with Shirzaei it was not significant, p = 0.05–0.11), P2 (0.008) and each frame's line of sight alone (0.009 and 0.005). On the 341 cells velocity alone does not separate the collapse cells (single-layer ROC AUC 0.50), so the gain there comes only together with the baseline and location. At 200 m the permutation and MSR nulls give p ≤ 0.015, but the variogram-matching nulls give 0.102 and 0.090, so the 200 m result does not pass them.
- **Reading:** an independent InSAR processing with a known observation period (October/November 2014 to December 2016, the collapse period) repeats the core association. Beyond the baseline and location, velocity helps rank the core cells with a collapse, and those cells move down relative to the background cells (median 0.6 mm/yr lower). It holds with a random forest, over the full period and in each viewing geometry alone.
- **Limits:** (1) The variogram check found every null rougher than the LiCSAR field at the shortest lag, which tends to make p too small; the closest null, plain variogram-matching, gives 0.005 at 250 m but 0.102 at 200 m, where the field is smoothest. (2) The events, cells and baseline are the Shirzaei test's, so this replicates the velocity product, not the sample. (3) The size of the gain is not re-estimated here; with Shirzaei its refit-bootstrap interval included zero. (4) P1 rests mainly on November 2015 to December 2016 because of network gaps (`LICSAR_CELLS.md`). (5) The velocity overlaps the collapse period, so this is a retrospective association, not a precursor.

## Primary test: the six nulls

| Null | Draws | Null median | Null 95th / 99th percentile | Draws ≥ observed | p |
|---|---|---|---|---|---|
| Free permutation | 2,000 | -0.017 | +0.016 / +0.045 | 2 | 0.001 |
| Within-block permutation | 2,000 | -0.026 | +0.031 / +0.064 | 9 | 0.005 |
| MSR | 999 | -0.012 | +0.031 / +0.052 | 0 | 0.001 |
| MSR, amplitude-adjusted | 999 | -0.012 | +0.030 / +0.053 | 1 | 0.002 |
| Variogram-matching | 999 | -0.020 | +0.034 / +0.062 | 4 | 0.005 |
| Variogram-matching, observed values | 999 | -0.019 | +0.032 / +0.063 | 4 | 0.005 |

## All tests (secondary tests change one thing each; random forest: 500 draws per null)

| Test | Cells kept / before (collapse cells) | PR AUC: baseline + x/y → + velocity | Change | Median velocity, collapse / background (mm/yr) | Single-layer ROC AUC | p, Free permutation | p, Within-block permutation | p, MSR | p, MSR, amplitude-adjusted | p, Variogram-matching | p, Variogram-matching, observed values | Largest p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Primary: vertical P1, Shirzaei-test cells, 250 m, logistic regression | 241 / 241 (32) | 0.328 → 0.413 | +0.085 | 0.06 / 0.64 | 0.44 | 0.001 | 0.005 | 0.001 | 0.002 | 0.005 | 0.005 | 0.005 |
| 1. All core cells with a LiCSAR value | 341 / 416 (34) | 0.326 → 0.409 | +0.082 | 0.06 / 0.35 | 0.50 | < 0.001 | 0.006 | 0.002 | 0.001 | 0.007 | 0.004 | 0.007 |
| 2. 200 m cells | 345 / 347 (36) | 0.197 → 0.269 | +0.072 | 0.09 / 0.73 | 0.37 | < 0.001 | < 0.001 | 0.013 | 0.015 | 0.102 | 0.090 | 0.102 |
| 3. Random forest | 241 / 241 (32) | 0.249 → 0.318 | +0.069 | 0.06 / 0.64 | 0.44 | 0.004 | 0.022 | 0.018 | 0.024 | 0.038 | 0.038 | 0.038 |
| 4. P2, full period | 241 / 241 (32) | 0.328 → 0.408 | +0.080 | 2.18 / 2.73 | 0.43 | 0.002 | 0.004 | 0.002 | 0.002 | 0.008 | 0.005 | 0.008 |
| 5. 065D line of sight, P1 | 241 / 241 (32) | 0.328 → 0.399 | +0.071 | 0.93 / 1.33 | 0.44 | 0.002 | 0.009 | 0.003 | 0.003 | 0.009 | 0.008 | 0.009 |
| 5. 131A line of sight, P1 | 241 / 241 (32) | 0.328 → 0.408 | +0.080 | -0.81 / -0.51 | 0.44 | 0.002 | 0.005 | 0.002 | 0.002 | 0.002 | 0.003 | 0.005 |

Figure: `licsar_test.png` (a: LiCSAR vertical velocity in the primary cells; b: the six null distributions).
