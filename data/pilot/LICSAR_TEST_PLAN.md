# Test plan for the LiCSAR velocity check (fixed before any LiCSAR velocity was computed)

**Written:** 2026-09-30, while the interferograms were still downloading (`scripts/14_licsar_download.py`). No LiCSAR velocity has been computed or looked at. Anything changed after this date is listed at the end with its reason.

**Question:** does an independent InSAR velocity with a known observation period repeat the historic-core result that Shirzaei velocity gave (`CORE_STATISTICS.md`, `VARIOGRAM_NULL.md`)?

## Velocity product

- **Input:** LiCSAR interferograms of the descending frame 065D_05935_131108 (1,153 pairs) and the ascending frame 131A_05957_110910 (2,199 pairs), October 2014 to September 2023. They are clipped to the project box (29.75–30.15 E, 31.05–31.38 N) at the native 0.001° grid.
- **Processing:** LiCSBAS (comet-licsar/LiCSBAS, the commit recorded in `data/README.md`), steps 02 and 11–16 with default settings. Steps 01, 03, 04 and 05 are skipped: the data are already downloaded and clipped, and there is no GACOS/ERA5 correction and no extra masking. There is no multilooking (`-n 1`). The full network of each frame is inverted.
- **Periods:**
  - **P1 (primary):** from the first epoch to 2016-12-31, which is the period of the collapses. This is a linear fit to LiCSBAS's cumulative displacement over those epochs (`LiCSBAS_cum2vel.py`).
  - **P2 (secondary):** the full period (LiCSBAS step 14 velocity).
- **Vertical velocity:** the two frames' line-of-sight velocities are decomposed into vertical and east–west components with their E/N/U unit vectors, assuming no north–south motion (`LiCSBAS_decomposeLOS.py`). Units are mm/yr, positive up. Only pixels valid after step 15 in both frames are used.
- **Cell value:** the mean of the valid pixels whose centres fall in the cell. Cells with no valid pixel are excluded and counted.

## Primary test (unchanged from the Shirzaei primary test)

- **Cells:** the 241 historic-core cells at 250 m used in `CORE_STATISTICS.md`. Any of them without a LiCSAR value is dropped and reported.
- **Comparison:** baseline + x/y vs baseline + x/y + LiCSAR vertical velocity (P1). The model is logistic regression with the same settings, the same 63 events, the same folds (seed 42, 2 km blocks) and the same features.
- **Statistic:** the change in out-of-fold PR AUC.
- **Null models:** all six from `VARIOGRAM_NULL.md`, fitted to the LiCSAR field:
  - free permutation and within-block permutation, 2,000 draws each;
  - MSR and amplitude-adjusted MSR, 999 each, with the same weights rule;
  - variogram-matching, plain and rank-remapped, 999 each.

  Each null's variogram is re-checked on the LiCSAR field as in `MSR_VARIOGRAM_CHECK.md` before its p-value is read.
- **Decision rule:** the core result *replicates* only if all three hold:
  1. the PR AUC change is positive;
  2. collapse cells have more negative vertical velocity than background cells in the core (the Shirzaei direction);
  3. the largest p across the six nulls is below 0.05.

  Otherwise it is reported as *not replicated*. No other outcome is claimed.

## Secondary (reported, no decision attached)

1. All historic-core cells with a LiCSAR value (about 351 of 416 in the feasibility check), same test.
2. 200 m cells.
3. Random forest.
4. P2, the full-period velocity.
5. Each frame's line-of-sight velocity on its own, instead of the vertical component.
6. The city-wide location checks (feature sets A–D of `LOCATION_CHECKS.md`) with LiCSAR velocity.
7. Agreement with Shirzaei velocity on shared cells (Spearman correlation, descriptive).

## Changes after 2026-09-30

Made on 2026-09-30 after the user approved the run and before any LiCSAR velocity existed (items 1–3 before LiCSBAS was started, items 4–5 while its first step was running):

1. **"Default settings" made exact.** LiCSBAS is run through its own `batch_LiCSBAS.sh`, as shipped at the recorded commit. Three lines are changed: the start step (02, because the data are already downloaded) and the input and output folder paths; `scripts/15_licsbas_run.sh` prints the diff into the log. The shipped batch script turns on three options that the individual scripts leave off: `--multi_prime` in step 12, `--n_gap_use_merged` in step 15 and `--interpolate_nans` in step 16. The thresholds actually applied are saved in each frame's `TS_GEOCml1/info/*parameters.txt`.
2. **P2 named correctly.** Step 14 computes the velocity's standard deviation, not the velocity. P2 is the linear fit over the full period to the same cumulative displacement as P1: `cum_filt.h5` from step 16, masked with step 15's mask, fitted with `LiCSBAS_cum2vel.py` without an end date. This is the quantity step 16 saves as `vel.filt.mskd`.
3. **Software compatibility.** `LiCSBAS_decomposeLOS.py` uses `np.bool8`, which NumPy 2 removed. The tool is run unedited, with `np.bool8` set to `np.bool_` before it starts; the calculation is unchanged. For the same reason numpy in the `licsbas` env was downgraded to 2.3.5 (`data/README.md`).
4. **Criterion 2 made exact.** "More negative" is read the way `LOCATION_CHECKS.md` reported the Shirzaei direction: the median vertical velocity of the collapse cells is below the median of the background cells, on the primary test's cells.
5. **Secondary tests made exact.** Tests 1–5 each change one thing in the primary test and use the same six nulls; test 5 is run once per frame. Test 3 (random forest) uses 500 draws per null, 09's budget for the random forest. The variogram check covers the four surrogate nulls, as in `MSR_VARIOGRAM_CHECK.md`; the two permutation nulls keep no spatial structure by design. The check is a separate stage (`scripts/17_licsar_test.py --check`, no model fits) that is run and read before any p-value is computed.

## Run notes (no change to the method)

- The first run stopped in step 02 on a software error (numpy 2.4 vs astropy 6.1.7; item 3) and was restarted from scratch.
- 131A's run was killed in step 13 when the working session ended; it was restarted from step 13 (steps 02–12 unchanged, and step 13 restarts its inversion from scratch). Logs: `data/licsbas/run.log` and `run_resume_131A.log`.
- The variogram check (`LICSAR_VARIOGRAM_CHECK.md`) and its reading were written before the test was run.
