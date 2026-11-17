# Primary core test under a variogram-matching null

**Primary analysis, unchanged:** historic core, 250 m, logistic regression, baseline + x/y vs baseline + x/y + Shirzaei velocity, statistic = change in out-of-fold PR AUC (0.328 → 0.372, +0.044). Same cells, folds (seed 42) and settings as `CORE_STATISTICS.md` and `MSR_NULL.md`; 200 m is robustness only.
**Reproduce:** `.venv/bin/python scripts/12_variogram_null.py` (after 09–11).

- **New nulls:** the two variogram-matching nulls of `MSR_VARIOGRAM_CHECK.md` (Burt et al. 2020), plain and rank-remapped to the observed values, with the same 999 surrogates per null. They were chosen there on how well they reproduce the velocity variogram, before any of their p-values.
- **Test:** velocity is replaced by each surrogate and the velocity model refitted on the same folds. p = (1 + draws with a change ≥ observed) / (1 + draws).
- **Earlier nulls** are copied from their reports, so every null of the primary test is in one table.

## Result

- **Primary test: p = 0.009–0.023 under every null.** At 250 m the variogram-matching nulls give p = 0.023 (plain) and 0.017 (observed values), next to 0.009 (MSR), 0.020 (amplitude-adjusted MSR), 0.011 (free permutation) and 0.018 (within-block). The null that reproduces the variogram best, the plain one, gives the largest p; 0.023 is the conservative summary.
- **200 m (robustness): still below 0.05, but less clear-cut.** p rises from 0.006 or less under MSR and the permutations to 0.037 (plain) and 0.030 (observed values). Smooth surrogate fields produce large chance gains at 200 m more often (99th percentile +0.149 and +0.127, vs +0.070 under MSR), so the 200 m result depends more on short-range smoothness. The plain null is smoother than the real field at 200 m (`MSR_VARIOGRAM_CHECK.md`), so 0.037 is on the strict side.
- **Reading:** velocity's link to core collapse cells beyond baseline + x/y is unlikely to be chance under nulls that keep the value distribution, Moran's I or the full variogram. This settles significance, not size: the refit-bootstrap interval for the gain (−0.014 to +0.130, `CORE_STATISTICS.md`) still includes zero.
- **Limits:** every null is stationary, while the real field's variance is concentrated in poorly covered edge cells (none of them collapse cells). The Shirzaei observation period is unknown, so this is a retrospective association, not a precursor.

## All nulls, 250 m (primary)

| Null | What it reproduces | Draws | Null median | Null 95th / 99th percentile | Draws ≥ observed | p | Source |
|---|---|---|---|---|---|---|---|
| Free permutation | the values only; no spatial structure | 2,000 | -0.017 | – | – | 0.011 | `CORE_STATISTICS.md` |
| Within-block permutation | the values within each 2 km block; no structure below 2 km | 2,000 | -0.020 | – | – | 0.018 | `CORE_STATISTICS.md` |
| MSR | Moran's I exactly; the variogram from about 1.5 km (rougher below) | 999 | -0.013 | +0.024 / +0.038 | 8 | 0.009 | `MSR_NULL.md` |
| MSR, amplitude-adjusted | the values; the variogram from about 1.5 km (rougher below) | 999 | -0.013 | +0.028 / +0.053 | 19 | 0.020 | `MSR_NULL.md` |
| Variogram-matching | the variogram at all lags; near-Gaussian values; smoother than the real field at 200 m | 999 | -0.018 | +0.027 / +0.059 | 22 | 0.023 | this run |
| Variogram-matching, observed values | the values; the variogram inside its 95% range at all lags (median still high below 1 km) | 999 | -0.016 | +0.027 / +0.057 | 16 | 0.017 | this run |

## All nulls, 200 m (robustness; observed change +0.093)

| Null | What it reproduces | Draws | Null median | Null 95th / 99th percentile | Draws ≥ observed | p | Source |
|---|---|---|---|---|---|---|---|
| Free permutation | the values only; no spatial structure | 2,000 | -0.002 | – | – | < 0.001 | `CORE_STATISTICS.md` |
| Within-block permutation | the values within each 2 km block; no structure below 2 km | 2,000 | -0.003 | – | – | < 0.001 | `CORE_STATISTICS.md` |
| MSR | Moran's I exactly; the variogram from about 1.5 km (rougher below) | 999 | -0.002 | +0.027 / +0.070 | 5 | 0.006 | `MSR_NULL.md` |
| MSR, amplitude-adjusted | the values; the variogram from about 1.5 km (rougher below) | 999 | -0.001 | +0.031 / +0.067 | 1 | 0.002 | `MSR_NULL.md` |
| Variogram-matching | the variogram at all lags; near-Gaussian values; smoother than the real field at 200 m | 999 | -0.001 | +0.079 / +0.149 | 36 | 0.037 | this run |
| Variogram-matching, observed values | the values; the variogram inside its 95% range at all lags (median still high below 1 km) | 999 | -0.001 | +0.068 / +0.127 | 29 | 0.030 | this run |

Figure: `variogram_null.png` (null distributions of the four surrogate nulls with the observed change).
