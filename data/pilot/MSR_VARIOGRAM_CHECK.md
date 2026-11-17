# Why the MSR surrogates miss the short-lag variogram

**Follows:** `MSR_NULL.md`, whose check found the observed semivariogram outside the MSR surrogates' 95% range at 4 of 16 lags at 250 m and 7 of 16 at 200 m.
**Reproduce:** `.venv/bin/python scripts/11_msr_variogram_check.py` (after 10; no model fits, about 20 s).
**Blind:** diagnostics only. No model is fitted and no p-value is computed here, so any further null can be chosen on how well it reproduces the velocity field, not on its result.

- **Per-lag check:** the same core cells, velocity and MSR surrogates as `MSR_NULL.md` (same seed and order). ✗ = the observed value is outside the surrogates' 95% range.
- **Lag-1 decomposition:** lag-1 semivariance = degree-weighted variance − Moran's I (queen) × variance, where the degree-weighted variance weights each cell's squared deviation by its number of queen neighbours. MSR keeps the variance and, up to sampling, Moran's I, so any gap has to come from where the variance sits.
- **Variogram-matching null** (Burt et al. 2020, after Viladomat et al. 2014): velocity is permuted, smoothed over each cell and its k nearest cells with an exponential kernel, then rescaled and given white noise so that its variogram (lags 1–16) best fits the observed one; k is chosen per surrogate from 2 to 0.9 × cells. "Observed values" = the same surrogates rank-remapped to the observed velocities, so the value distribution is exact. 999 surrogates each.

## Result

- **The gap is short-range only.** At 250 m the MSR surrogates' median semivariance is 38–85% above the observed at 0.25–1 km (all four lags outside the 95% range) and within 13% from 1.5 km on; at 200 m it is 24–192% above up to 1.4 km and within 11% beyond. The surrogates are rougher than the real field at short range; the long-range structure (sill, range about 1.75 km) is reproduced.
- **Cause: where the variance sits, not the weights.** MSR keeps the variance and Moran's I (queen: I × variance 2.12 observed vs 2.16), so the whole lag-1 gap at 250 m (1.06 vs 1.97) comes from the degree-weighted variance (3.19 vs 4.14). The largest deviations sit in cells with few neighbours and few InSAR points: at 250 m, cells with 0–2 queen neighbours are 8% of cells and carry 19% of the variance, and single-point cells are 14% and carry 35% (200 m: 32% and 46%). Such cells have few short-lag pairs, so they add variance but little short-lag semivariance; MSR's sign flips spread that variance over all cells. MSR on queen contiguity is no better (exact surrogate mean at lags 1–4: 2.06 · 2.29 · 1.99 · 1.60 × observed, vs 1.85 · 1.53 · 1.42 · 1.37 with 10's weights).
- **The extremes are not collapse cells.** The 10 most negative cells at 250 m (−8.2 to −14.3 mm/yr, 6 of them in Moharam Bek) include no collapse cell, and none of the cells with 0–2 queen neighbours is a collapse cell at either size.
- **A variogram-matching null reproduces the variogram.** Plain: 16 of 16 lags inside the 95% range at both sizes, with the median within 18% of the observed at lag 1 and within 10% elsewhere at 250 m (200 m: 35% at lag 1, 8% elsewhere). But its values are near-Gaussian (skewness −0.13 vs −1.83), and at 200 m its Moran's I is above the observed, so it is smoother than the real field there. Rank-remapped to the observed values, it keeps the distribution exactly and has 16 of 16 lags inside a wider range, but its median is still 18–53% above the observed at lags 1–4 at 250 m (MSR: 38–85%).
- **Reading:** no stationary null reproduces both the skewed values and the short-lag variogram, because the field's short-range smoothness partly reflects where its extremes sit. The direction of any bias in the MSR p-values (0.009; 0.020 amplitude-adjusted) is not obvious: rougher surrogates line up with the clustered collapse cells less often, which makes p too small, but they also move variance from the edges into the well-connected cells where the collapse cells are, which makes p too large. The two variogram-matching nulls would test this from the smooth side; they were chosen on this check, before any of their p-values.

## Semivariogram by lag, 250 m (median and 95% range of 999 surrogates)

| Lag (km) | Cell pairs | Observed | MSR | MSR, amplitude-adjusted | Variogram-matching | Variogram-matching, observed values |
|---|---|---|---|---|---|---|
| 0.25 | 693 | 1.06 | 1.97 (1.73–2.21) ✗ | 2.31 (1.69–2.95) ✗ | 1.25 (0.85–2.16) | 1.63 (0.93–2.78) |
| 0.50 | 899 | 1.62 | 2.47 (2.09–2.84) ✗ | 2.82 (1.93–3.58) ✗ | 1.76 (1.42–2.71) | 2.20 (1.34–3.23) |
| 0.75 | 1,061 | 2.12 | 3.02 (2.43–3.65) ✗ | 3.34 (2.16–4.18) ✗ | 2.30 (1.88–3.22) | 2.76 (1.63–3.92) |
| 1.00 | 1,843 | 2.84 | 3.93 (3.05–4.84) ✗ | 4.09 (2.56–5.11) | 2.92 (2.35–3.87) | 3.36 (1.88–4.69) |
| 1.25 | 1,403 | 3.49 | 4.36 (3.16–5.40) | 4.41 (2.75–5.51) | 3.47 (2.74–4.27) | 3.88 (2.09–5.35) |
| 1.50 | 1,767 | 4.06 | 4.60 (3.33–5.54) | 4.56 (2.89–5.61) | 3.82 (2.97–4.63) | 4.23 (2.24–5.61) |
| 1.75 | 1,527 | 4.48 | 4.67 (3.42–5.49) | 4.59 (3.02–5.59) | 4.04 (3.16–4.88) | 4.43 (2.39–5.76) |
| 2.00 | 1,613 | 4.48 | 4.56 (3.50–5.31) | 4.52 (3.08–5.46) | 4.20 (3.26–5.06) | 4.50 (2.58–5.78) |
| 2.25 | 1,931 | 4.41 | 4.46 (3.65–5.13) | 4.47 (3.10–5.29) | 4.28 (3.35–5.16) | 4.61 (2.63–5.78) |
| 2.50 | 1,330 | 4.51 | 4.37 (3.72–5.05) | 4.40 (3.21–5.25) | 4.33 (3.44–5.21) | 4.66 (2.67–5.67) |
| 2.75 | 1,471 | 4.35 | 4.26 (3.64–4.93) | 4.23 (3.32–5.25) | 4.32 (3.55–5.17) | 4.61 (2.92–5.69) |
| 3.00 | 1,177 | 4.24 | 4.13 (3.54–4.86) | 4.15 (3.26–5.12) | 4.28 (3.60–5.16) | 4.55 (2.96–5.69) |
| 3.25 | 1,307 | 4.04 | 4.06 (3.46–4.99) | 4.05 (3.34–5.08) | 4.30 (3.64–5.13) | 4.50 (3.27–5.79) |
| 3.50 | 1,145 | 4.02 | 3.97 (3.34–4.93) | 3.97 (3.26–5.02) | 4.31 (3.57–5.24) | 4.47 (3.30–5.77) |
| 3.75 | 925 | 4.34 | 4.00 (3.30–4.97) | 4.04 (3.21–5.02) | 4.29 (3.44–5.41) | 4.46 (3.24–5.80) |
| 4.00 | 1,099 | 4.24 | 4.10 (3.25–5.16) | 4.08 (3.23–5.19) | 4.33 (3.27–5.58) | 4.43 (3.38–5.93) |

## Semivariogram by lag, 200 m

| Lag (km) | Cell pairs | Observed | MSR | MSR, amplitude-adjusted | Variogram-matching | Variogram-matching, observed values |
|---|---|---|---|---|---|---|
| 0.20 | 1,036 | 0.74 | 2.17 (1.99–2.33) ✗ | 2.53 (1.98–2.99) ✗ | 1.00 (0.69–1.57) | 1.44 (0.72–2.39) |
| 0.40 | 1,362 | 1.36 | 2.59 (2.32–2.87) ✗ | 2.96 (2.26–3.52) ✗ | 1.36 (1.15–1.90) | 1.87 (0.93–2.81) |
| 0.60 | 1,655 | 1.90 | 3.04 (2.66–3.48) ✗ | 3.39 (2.54–4.11) ✗ | 1.77 (1.52–2.34) | 2.32 (1.07–3.35) |
| 0.80 | 2,952 | 2.23 | 3.89 (3.35–4.48) ✗ | 4.05 (2.97–5.07) ✗ | 2.28 (1.92–2.93) | 2.80 (1.29–4.08) |
| 1.00 | 2,301 | 2.59 | 4.28 (3.64–4.95) ✗ | 4.37 (3.15–5.62) ✗ | 2.80 (2.33–3.42) | 3.28 (1.54–4.70) |
| 1.20 | 2,996 | 3.19 | 4.45 (3.76–5.10) ✗ | 4.46 (3.25–5.58) ✗ | 3.18 (2.68–3.81) | 3.67 (1.73–5.08) |
| 1.40 | 2,691 | 3.63 | 4.51 (3.86–5.11) ✗ | 4.54 (3.35–5.48) | 3.54 (2.94–4.17) | 3.96 (1.85–5.42) |
| 1.60 | 2,907 | 4.07 | 4.53 (3.89–5.10) | 4.55 (3.45–5.38) | 3.78 (3.11–4.47) | 4.19 (1.99–5.62) |
| 1.80 | 3,652 | 4.23 | 4.46 (3.84–4.99) | 4.43 (3.39–5.22) | 3.98 (3.28–4.67) | 4.35 (2.10–5.69) |
| 2.00 | 2,659 | 4.33 | 4.42 (3.86–5.01) | 4.38 (3.46–5.21) | 4.13 (3.44–4.81) | 4.47 (2.12–5.85) |
| 2.20 | 3,025 | 4.13 | 4.34 (3.79–4.93) | 4.29 (3.51–5.12) | 4.19 (3.59–4.84) | 4.53 (2.24–5.83) |
| 2.40 | 2,473 | 4.17 | 4.27 (3.68–4.85) | 4.22 (3.49–4.96) | 4.25 (3.71–4.87) | 4.64 (2.23–5.74) |
| 2.60 | 2,810 | 4.28 | 4.16 (3.63–4.70) | 4.14 (3.44–4.85) | 4.28 (3.76–4.87) | 4.64 (2.34–5.71) |
| 2.80 | 2,421 | 4.26 | 4.05 (3.50–4.60) | 4.06 (3.32–4.68) | 4.30 (3.74–4.96) | 4.59 (2.60–5.65) |
| 3.00 | 2,014 | 4.28 | 4.02 (3.48–4.54) | 4.02 (3.33–4.72) | 4.32 (3.61–5.11) | 4.52 (2.72–5.69) |
| 3.20 | 2,304 | 4.11 | 4.01 (3.47–4.64) | 4.03 (3.37–4.78) | 4.34 (3.52–5.26) | 4.46 (3.00–5.82) |

## Each null against the observed field

| Cell size | Null | Lags inside the 95% range | Median / observed, lags 1–4 | Median / observed, lags 5–16 (range) | Moran's I, MEM weights: observed / 95% range | Moran's I, queen: observed / 95% range | Skewness: observed / median | Variance: median / observed |
|---|---|---|---|---|---|---|---|---|
| 250 m | MSR | 12 of 16 | 1.85 · 1.53 · 1.42 · 1.38 | 0.92–1.25 | 0.377 / 0.377–0.377 | 0.511 / 0.465–0.574 | -1.83 / 0.00 | 1.00 |
| 250 m | MSR, amplitude-adjusted | 13 of 16 | 2.17 · 1.75 · 1.57 · 1.44 | 0.93–1.26 | 0.377 / 0.241–0.373 | 0.511 / 0.329–0.546 | -1.83 / -1.83 | 1.00 |
| 250 m | Variogram-matching | 16 of 16 | 1.18 · 1.09 · 1.08 · 1.03 | 0.90–1.07 | 0.377 / 0.302–0.653 | 0.511 / 0.407–0.808 | -1.83 / -0.13 | 0.93 |
| 250 m | Variogram-matching, observed values | 16 of 16 | 1.53 · 1.36 · 1.30 · 1.18 | 0.99–1.11 | 0.377 / 0.252–0.628 | 0.511 / 0.330–0.807 | -1.83 / -1.83 | 1.00 |
| 200 m | MSR | 9 of 16 | 2.92 · 1.90 · 1.60 · 1.74 | 0.94–1.65 | 0.366 / 0.366–0.366 | 0.484 / 0.437–0.515 | -2.28 / -0.01 | 1.00 |
| 200 m | MSR, amplitude-adjusted | 10 of 16 | 3.41 · 2.17 · 1.79 · 1.81 | 0.94–1.69 | 0.366 / 0.231–0.362 | 0.484 / 0.292–0.501 | -2.28 / -2.28 | 1.00 |
| 200 m | Variogram-matching | 16 of 16 | 1.35 · 1.00 · 0.93 · 1.02 | 0.93–1.08 | 0.366 / 0.440–0.730 | 0.484 / 0.562–0.847 | -2.28 / -0.13 | 0.92 |
| 200 m | Variogram-matching, observed values | 16 of 16 | 1.94 · 1.38 · 1.23 · 1.25 | 1.03–1.27 | 0.366 / 0.340–0.680 | 0.484 / 0.428–0.805 | -2.28 / -2.28 | 1.00 |

## Lag-1 decomposition

| Cell size | Variance | Degree-weighted variance: observed / MSR median | Moran's I (queen) × variance: observed / MSR median | Lag-1 semivariance: observed / MSR median |
|---|---|---|---|---|
| 250 m | 4.16 | 3.19 (77% of the variance) / 4.14 | 2.12 / 2.16 | 1.06 / 1.97 |
| 200 m | 4.10 | 2.73 (67% of the variance) / 4.12 | 1.98 / 1.96 | 0.74 / 2.17 |

## Where the velocity variance sits

| Cell size | Cells | Cells (collapse cells) | Share of cells | Share of the variance | Velocity SD (mm/yr) |
|---|---|---|---|---|---|
| 250 m | 0–2 queen neighbours | 19 (0) | 8% | 19% | 3.06 |
| 250 m | 3–5 queen neighbours | 84 (8) | 35% | 53% | 2.48 |
| 250 m | 6–8 queen neighbours | 138 (24) | 57% | 28% | 1.36 |
| 250 m | 1 InSAR point | 34 (1) | 14% | 35% | 2.97 |
| 250 m | 2–3 InSAR points | 59 (6) | 24% | 28% | 2.17 |
| 250 m | 4 or more InSAR points | 148 (25) | 61% | 37% | 1.56 |
| 200 m | 0–2 queen neighbours | 27 (0) | 8% | 32% | 3.82 |
| 200 m | 3–5 queen neighbours | 97 (7) | 28% | 37% | 2.28 |
| 200 m | 6–8 queen neighbours | 223 (29) | 64% | 31% | 1.34 |
| 200 m | 1 InSAR point | 76 (5) | 22% | 46% | 2.83 |
| 200 m | 2–3 InSAR points | 150 (17) | 43% | 33% | 1.77 |
| 200 m | 4 or more InSAR points | 121 (14) | 35% | 21% | 1.52 |

- 250 m: the 10 most negative cells (-8.2 to -14.3 mm/yr) include 0 collapse cells; median 4 queen neighbours (all cells: 6) and 2 InSAR points (all cells: 4); 6 Moharam Bek, 2 Mina El-Basal, 2 Karmouz.
- 250 m, weights check: exact MSR mean / observed at lags 1–4 = 2.06 · 2.29 · 1.99 · 1.60 with queen contiguity + spanning-tree links, vs 1.85 · 1.53 · 1.42 · 1.37 with 10's weights (t = 791 m).
- 250 m, variogram-matching: chosen neighbourhood k median 40 cells (2.5–97.5%: 10–158; the largest k offered, 216, chosen 25 times).
- 200 m: the 10 most negative cells (-8.1 to -18.4 mm/yr) include 0 collapse cells; median 2 queen neighbours (all cells: 7) and 2 InSAR points (all cells: 3); 7 Moharam Bek, 2 Mina El-Basal, 1 Karmouz.
- 200 m, weights check: exact MSR mean / observed at lags 1–4 = 2.98 · 2.73 · 2.09 · 1.82 with queen contiguity + spanning-tree links, vs 2.92 · 1.90 · 1.61 · 1.74 with 10's weights (t = 632 m).
- 200 m, variogram-matching: chosen neighbourhood k median 51 cells (2.5–97.5%: 17–217; the largest k offered, 312, chosen 22 times).

Figure: `msr_variogram_check.png` (semivariograms at 250 m and 200 m; map of core velocity at 250 m).
