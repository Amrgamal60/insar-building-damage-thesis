# Spatially constrained null (Moran spectral randomization) for the primary core test

**Primary analysis, fixed before this run:** historic core, 250 m, logistic regression, baseline + x/y vs baseline + x/y + Shirzaei velocity, statistic = change in out-of-fold PR AUC. Same cells, labels, baseline features, folds (seed 42), preprocessing and model settings as `CORE_STATISTICS.md`. 200 m is robustness only; nothing was tuned on the result.
**Reproduce:** `.venv/bin/python scripts/10_msr_null.py` (after 09).

- **Surrogates:** 999 velocity fields per null, by Moran spectral randomization (Wagner & Dray 2015, singleton method). Velocity is decomposed on the Moran eigenvector maps of distance-based weights among the core cells (w = 1 − (d/4t)² for d ≤ t, t = 791 m, the longest minimum-spanning-tree edge), and the sign of every coefficient is flipped at random. This keeps the variance carried by each spatial scale, so Moran's I under those weights is reproduced exactly, and the correlogram and variogram approximately.
- **Check null:** an amplitude-adjusted MSR that also keeps the observed value distribution exactly (50 rounds alternating rank remapping and restoring each coefficient's size, like IAAFT for time series).
- **Test:** velocity is replaced by each surrogate and the velocity model refitted on the same folds. p = (1 + surrogates with a change ≥ observed) / (1 + surrogates).

## Result

| Cell size | Null | Cells (collapse cells) | Observed ΔPR AUC | Null median | Null 95th / 99th percentile | Surrogates ≥ observed | Monte Carlo p | Moran's I, MEM weights: observed / surrogates (2.5–97.5%) | Moran's I, queen neighbours: observed / surrogates (2.5–97.5%) | Skewness: observed / surrogates (median) |
|---|---|---|---|---|---|---|---|---|---|---|
| 250 m | MSR | 241 (32) | +0.044 | -0.013 | +0.024 / +0.038 | 8 of 999 | 0.009 | 0.377 / 0.377–0.377 | 0.511 / 0.465–0.574 | -1.83 / 0.00 |
| 250 m | MSR, amplitude-adjusted | 241 (32) | +0.044 | -0.013 | +0.028 / +0.053 | 19 of 999 | 0.020 | 0.377 / 0.241–0.373 | 0.511 / 0.329–0.546 | -1.83 / -1.83 |
| 200 m | MSR | 347 (36) | +0.093 | -0.002 | +0.027 / +0.070 | 5 of 999 | 0.006 | 0.366 / 0.366–0.366 | 0.484 / 0.437–0.515 | -2.28 / -0.01 |
| 200 m | MSR, amplitude-adjusted | 347 (36) | +0.093 | -0.001 | +0.031 / +0.067 | 1 of 999 | 0.002 | 0.366 / 0.231–0.362 | 0.484 / 0.292–0.501 | -2.28 / -2.28 |

## Does the null reproduce the velocity field's spatial structure?

Semivariogram of velocity by lag (1–16 cell widths), observed vs the surrogates' 95% envelope:

| Cell size | Null | Lags inside the 95% envelope | Largest |observed − median| / observed |
|---|---|---|---|
| 250 m | MSR | 12 of 16 | 85.5% |
| 250 m | MSR, amplitude-adjusted | 13 of 16 | 116.9% |
| 200 m | MSR | 9 of 16 | 191.5% |
| 200 m | MSR, amplitude-adjusted | 10 of 16 | 241.0% |

Figures: `msr_null_250m.png` and `msr_null_200m.png` (left: null distribution with the observed change; right: variogram check).
