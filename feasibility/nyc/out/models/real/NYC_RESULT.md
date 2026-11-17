# NYC replication: result

**Plan:** `NYC_REPLICATION_PLAN.md` (frozen copy `freeze/NYC_REPLICATION_PLAN_frozen.md`), §11–§13. **Reproduce:** `../../.venv/bin/python -I scripts/11_models.py raw out --real`, then `scripts/12_report.py out --real`.

## 1. Variogram check (reported first, §10)

**Variogram check of the primary null (999 surrogates, seed 2027; 20 windows, seed 7)**

- **Primary analysis structure:** 60 windows; 4,966 domain cells with a value in any window (the null's union). Event counts and losses are reported with the results, not here.
- **Chosen neighbourhood k:** median 169 (2.5–97.5%: 169–169); offered 2, 3, 4, 7, 11, 18, 28, 44, 69, 108, 169, 264, 411, 641, 1000.
- **Lags 1–16 cell widths:** observed inside the surrogates' 95% range at 194 of 320 window-lags; **1 km bins from 4 to 20 km:** 79 of 320.
- Whatever this shows, the primary null is not changed (§10).

| window | Lags 1–16 inside | 1 km bins 4–20 km inside | Median / observed, lags 1–4 | Median / observed, lags 5–16 (range) | Outside, below the range | Outside, above the range |
|---|---|---|---|---|---|---|
| 365d_2017-08-07 | 8 of 16 | 0 of 16 | 1.59 · 1.08 · 0.94 · 0.90 | 0.91–1.05 | 4 | 20 |
| 365d_2017-09-24 | 11 of 16 | 0 of 16 | 1.27 · 1.02 · 0.94 · 0.91 | 0.91–1.09 | 4 | 17 |
| 365d_2018-02-18 | 12 of 16 | 1 of 16 | 1.62 · 1.13 · 0.97 · 0.94 | 0.92–1.02 | 1 | 18 |
| 365d_2018-05-13 | 7 of 16 | 0 of 16 | 2.03 · 1.17 · 0.96 · 0.89 | 0.88–1.05 | 5 | 20 |
| 365d_2018-08-06 | 12 of 16 | 5 of 16 | 1.83 · 1.27 · 1.10 · 1.03 | 0.93–1.04 | 4 | 11 |
| 365d_2018-08-09 | 12 of 16 | 5 of 16 | 1.83 · 1.27 · 1.10 · 1.03 | 0.93–1.04 | 4 | 11 |
| 365d_2019-05-06 | 8 of 16 | 9 of 16 | 2.27 · 1.29 · 1.03 · 0.92 | 0.88–1.04 | 3 | 12 |
| 365d_2019-07-21 | 13 of 16 | 0 of 16 | 1.68 · 1.15 · 1.00 · 0.95 | 0.93–1.04 | 3 | 16 |
| 365d_2019-10-28 | 10 of 16 | 0 of 16 | 1.20 · 1.01 · 0.95 · 0.93 | 0.92–1.05 | 3 | 19 |
| 365d_2019-10-31 | 10 of 16 | 0 of 16 | 1.12 · 0.98 · 0.94 · 0.94 | 0.92–1.05 | 3 | 19 |
| 365d_2020-07-08 | 6 of 16 | 0 of 16 | 1.71 · 1.07 · 0.92 · 0.88 | 0.89–1.09 | 5 | 21 |
| 365d_2020-07-31 | 9 of 16 | 2 of 16 | 1.50 · 1.03 · 0.93 · 0.90 | 0.92–1.06 | 4 | 17 |
| 365d_2020-08-04 | 8 of 16 | 2 of 16 | 1.91 · 1.15 · 0.96 · 0.89 | 0.88–1.06 | 4 | 18 |
| 365d_2020-12-28 | 13 of 16 | 0 of 16 | 1.47 · 1.10 · 0.97 · 0.93 | 0.93–1.04 | 1 | 18 |
| 365d_2021-02-14 | 7 of 16 | 14 of 16 | 1.87 · 1.27 · 1.07 · 0.96 | 0.88–1.05 | 4 | 7 |
| 365d_2021-03-01 | 4 of 16 | 16 of 16 | 1.86 · 1.29 · 1.08 · 0.95 | 0.87–1.06 | 6 | 6 |
| 365d_2021-06-21 | 2 of 16 | 16 of 16 | 3.77 · 2.43 · 2.05 · 1.82 | 1.00–1.70 | 14 | 0 |
| 365d_2022-03-11 | 16 of 16 | 8 of 16 | 1.31 · 0.98 · 0.93 · 0.93 | 0.96–1.03 | 0 | 8 |
| 365d_2022-04-14 | 14 of 16 | 0 of 16 | 1.41 · 1.02 · 0.94 · 0.93 | 0.94–1.04 | 0 | 18 |
| 365d_2022-04-17 | 12 of 16 | 1 of 16 | 1.77 · 1.13 · 0.97 · 0.92 | 0.91–1.03 | 1 | 18 |

**By lag, over the 20 windows:**

| Lag | Windows inside the 95% range | Surrogate median / observed (median over windows) |
|---|---|---|
| 0.25 km | 6 of 20 | 1.69 |
| 0.50 km | 12 of 20 | 1.13 |
| 0.75 km | 18 of 20 | 0.96 |
| 1.00 km | 6 of 20 | 0.93 |
| 1.25 km | 5 of 20 | 0.93 |
| 1.50 km | 10 of 20 | 0.94 |
| 1.75 km | 14 of 20 | 0.96 |
| 2.00 km | 16 of 20 | 0.99 |
| 2.25 km | 17 of 20 | 1.02 |
| 2.50 km | 17 of 20 | 1.03 |
| 2.75 km | 11 of 20 | 1.04 |
| 3.00 km | 10 of 20 | 1.03 |
| 3.25 km | 7 of 20 | 1.03 |
| 3.50 km | 15 of 20 | 1.01 |
| 3.75 km | 17 of 20 | 0.98 |
| 4.00 km | 13 of 20 | 0.96 |
| 4.125–5 km | 9 of 20 | 0.89 |
| 5–6 km | 4 of 20 | 0.80 |
| 6–7 km | 4 of 20 | 0.70 |
| 7–8 km | 4 of 20 | 0.63 |
| 8–9 km | 5 of 20 | 0.58 |
| 9–10 km | 4 of 20 | 0.54 |
| 10–11 km | 4 of 20 | 0.51 |
| 11–12 km | 3 of 20 | 0.49 |
| 12–13 km | 3 of 20 | 0.48 |
| 13–14 km | 5 of 20 | 0.47 |
| 14–15 km | 4 of 20 | 0.47 |
| 15–16 km | 6 of 20 | 0.47 |
| 16–17 km | 6 of 20 | 0.47 |
| 17–18 km | 6 of 20 | 0.46 |
| 18–19 km | 7 of 20 | 0.45 |
| 19–20 km | 5 of 20 | 0.45 |

Full check and figure: `out/insar/INSAR_CHECKS.md`, `out/insar/insar_checks.png`.

## 2. Decision (§11)

- **Incremental-value replication: not replicated.** Primary analysis (domain, 250 m, logistic regression, Baseline 1 + x/y, 1-year window): out-of-fold PR AUC 0.000231 → 0.000227, change -0.000004; variogram-matching null p = 0.418 (999 draws). Rule: change > 0 and p < 0.05.
- **Directional concordance: opposite.** Line-of-sight velocity is positive toward the satellite. Measure: the median over risk sets of (event cell − median of its controls), standardised velocity: +0.037 (47% of risk sets below 0). Below 0 is concordant with Alexandria: event cells move away from the satellite relative to their controls, as relative subsidence would. Above 0 is opposite.
  - Same measure in raw line of sight: -0.72 mm/yr. Raw values are not standardised, so they keep each window's landmass-group medians and spread. Medians pooled over rows (controls repeat across risk sets, so these need not differ by the value above): event cells -2.85, control rows -1.80 mm/yr.
  - Velocity coefficient in a logistic regression fitted on all rows (standardised, conditional on the baseline features): -0.016, sign concordant (negative = concordant).
- **Together:** no incremental-value replication (opposite deformation direction).
- **Effect size:** -0.000004 (95% refit-bootstrap interval -0.000021 to +0.000023, 2000 of 2000 resamples).
- **Largest p across the six nulls** (Alexandria's LiCSAR standard, reported only): 0.48126 (PR AUC p of each: Variogram-matching (primary) 0.418; Free permutation 0.42229; Within-block permutation 0.48126; MSR 0.371; MSR, amplitude-adjusted 0.380; Variogram-matching, observed values 0.395).

**Sample:** 64 risk sets over 60 windows; 309,972 rows; 4,887 cells; prevalence 0.000206 (one event per risk set, §9). Events from 2017-07-16 not used: 14 cell not in the population; 3 earlier event in the cell; 1 same cell and date as another event (one risk set). Cells without a static input: 0.

| Metric | Baseline 1 + x/y | + velocity | Change | p (variogram-matching) | Null median | 95% refit-bootstrap interval |
|---|---|---|---|---|---|---|
| PR AUC (primary) | 0.000231 | 0.000227 | -0.000004 | 0.418 | -0.000005 | -0.000021 to +0.000023 |
| ROC AUC | 0.5330 | 0.5298 | -0.0032 | 0.450 | -0.0044 | -0.0309 to +0.0446 |
| Top-10% recall, pooled (share of events in the top 10% of all rows) | 0.0469 | 0.0469 | +0.0000 | 0.851 | +0.0156 | -0.0615 to +0.0545 |
| Top 10% of own risk set (share of events) | 0.0469 | 0.0469 | +0.0000 | 0.857 | +0.0156 | – |

The bootstrap interval is not computed for the own-risk-set top-10% share.

## 3. All nulls on the primary analysis (primary and secondary 8)

| Null | Draws | p, PR AUC | p, ROC AUC | p, Top-10% recall, pooled | p, Top 10% of own risk set |
|---|---|---|---|---|---|
| Variogram-matching (primary, §10) | 999 | 0.418 | 0.450 | 0.851 | 0.857 |
| Free permutation | 2000 | 0.42229 | 0.46027 | 0.86257 | 0.87106 |
| Within-block permutation | 2000 | 0.48126 | 0.51324 | 0.90555 | 0.92554 |
| MSR | 999 | 0.371 | 0.392 | 0.862 | 0.857 |
| MSR, amplitude-adjusted | 999 | 0.380 | 0.393 | 0.839 | 0.843 |
| Variogram-matching, observed values | 999 | 0.395 | 0.443 | 0.850 | 0.860 |


## 4. Secondary analyses (no decision attached; primary null unless stated)

| Analysis | Risk sets | PR AUC | Change | p | Draws | Interval | ΔROC AUC (p) | ΔTop-10% pooled (p) | ΔTop-10% own set (p) | Direction |
|---|---|---|---|---|---|---|---|---|---|---|
| 1. Whole NYC (generalization) | 78 | 0.000159 → 0.000157 | -0.000002 | 0.450 | 999 | -0.000012 to +0.000008 | -0.003 (0.412) | -0.013 (0.823) | -0.013 (0.812) | opposite |
| 2. 200 m cells | 69 | 0.000183 → 0.000179 | -0.000004 | 0.454 | 999 | -0.000045 to +0.000021 | -0.008 (0.639) | -0.014 (0.547) | -0.014 (0.579) | concordant |
| 3. Random forest | not run |  |  |  |  |  |  |  |  |  |
| 4. Baseline 2 (adds building age) | 64 | 0.000217 → 0.000213 | -0.000004 | 0.555 | 999 | -0.000025 to +0.000021 | -0.003 (0.452) | +0.000 (0.579) | +0.000 (0.699) | opposite |
| 5. 2-year window | 49 | 0.000214 → 0.000215 | +0.000000 | 0.386 | 999 | -0.000035 to +0.000048 | +0.006 (0.264) | -0.020 (0.841) | -0.020 (0.840) | concordant |
| 6. 3-year window | 36 | 0.000196 → 0.000210 | +0.000014 | 0.294 | 999 | -0.000048 to +0.000078 | +0.042 (0.147) | -0.028 (0.986) | -0.028 (0.985) | concordant |
| 7. Earlier control rule | 68 | 0.000229 → 0.000224 | -0.000005 | 0.599 | 999 | -0.000022 to +0.000018 | -0.006 (0.592) | -0.015 (0.922) | -0.029 (0.920) | opposite |
| 11. Never-case control rule | 64 | 0.000233 → 0.000229 | -0.000004 | 0.410 | 999 | -0.000022 to +0.000023 | -0.003 (0.448) | +0.000 (0.830) | +0.000 (0.836) | opposite |
| 12. Linear-only velocity | 64 | 0.000231 → 0.000228 | -0.000003 | 0.412 | 999 | -0.000019 to +0.000027 | -0.000 (0.372) | +0.031 (0.459) | +0.016 (0.664) | concordant |
| 13. No construction mask | 64 | 0.000231 → 0.000228 | -0.000003 | 0.377 | 999 | -0.000022 to +0.000024 | -0.003 (0.436) | +0.000 (0.856) | +0.000 (0.855) | opposite |
| 14. Availability only: log(1 + valid pixels) (coverage check, §12.14) | 64 | 0.000231 → 0.000241 | +0.000010 | 0.097 | 999 | -0.000020 to +0.000122 | +0.013 (0.124) | +0.078 (0.075) | +0.094 (0.041) | – |
| 15. Ohenhen et al. 2025 VLM, static (exploratory) (retrospective, carries no weight, §12.15) | 64 | 0.000227 → 0.000218 | -0.000009 | 0.654 | 999 | -0.000031 to +0.000053 | +0.001 (0.246) | +0.016 (0.643) | +0.016 (0.641) | – |

Direction uses the same measure as §11 and applies only to velocity fields. Δ columns: change from the baseline, with its p from the same null.

## 5. Sample and exclusions per analysis (§8, §9)

| Analysis | Risk sets | Windows | Rows | Cells | Prevalence | Cells without a static input | Rows without building age | Events from | Of these, not used |
|---|---|---|---|---|---|---|---|---|---|
| Primary: domain, 250 m, logistic regression, Baseline 1, 1-year window | 64 | 60 | 309,972 | 4,887 | 0.000206 | 0 | – | 2017-07-16 | 14 cell not in the population; 3 earlier event in the cell; 1 same cell and date as another event (one risk set) |
| 1. Whole NYC (generalization) | 78 | 74 | 784,157 | 10,149 | 0.000099 | 9 | – | 2017-07-16 | 3 earlier event in the cell; 1 same cell and date as another event (one risk set) |
| 2. 200 m cells | 69 | 65 | 502,812 | 7,346 | 0.000137 | 0 | – | 2017-07-16 | 10 cell not in the population; 2 earlier event in the cell; 1 same cell and date as another event (one risk set) |
| 3. Random forest | not run |  |  |  |  |  |  |  |  |
| 4. Baseline 2 (adds building age) | 64 | 60 | 309,972 | 4,887 | 0.000206 | 0 | 0 | 2017-07-16 | 14 cell not in the population; 3 earlier event in the cell; 1 same cell and date as another event (one risk set) |
| 5. 2-year window | 49 | 46 | 236,025 | 4,871 | 0.000208 | 0 | – | 2018-07-16 | 11 cell not in the population; 3 earlier event in the cell |
| 6. 3-year window | 36 | 33 | 172,381 | 4,857 | 0.000209 | 0 | – | 2019-07-16 | 7 cell not in the population; 2 earlier event in the cell |
| 7. Earlier control rule | 68 | 63 | 335,964 | 4,966 | 0.000202 | 0 | – | 2017-07-16 | 14 cell not in the population |
| 11. Never-case control rule | 64 | 60 | 307,961 | 4,887 | 0.000208 | 0 | – | 2017-07-16 | 14 cell not in the population; 3 earlier event in the cell; 1 same cell and date as another event (one risk set) |
| 12. Linear-only velocity | 64 | 60 | 309,972 | 4,887 | 0.000206 | 0 | – | 2017-07-16 | 14 cell not in the population; 3 earlier event in the cell; 1 same cell and date as another event (one risk set) |
| 13. No construction mask | 64 | 60 | 310,021 | 4,887 | 0.000206 | 0 | – | 2017-07-16 | 14 cell not in the population; 3 earlier event in the cell; 1 same cell and date as another event (one risk set) |
| 14. Availability only: log(1 + valid pixels) (coverage check, §12.14) | 64 | 60 | 309,972 | 4,887 | 0.000206 | 0 | – | 2017-07-16 | 14 cell not in the population; 3 earlier event in the cell; 1 same cell and date as another event (one risk set) |
| 15. Ohenhen et al. 2025 VLM, static (exploratory) (retrospective, carries no weight, §12.15) | 64 | 60 | 310,299 | 4,880 | 0.000206 | 0 | – | 2017-07-16 | 14 cell not in the population; 3 earlier event in the cell; 1 same cell and date as another event (one risk set) |

## 6. Other fold assignments (secondary 9; primary null, no bootstrap)

| Fold seed | PR AUC change | p | ΔROC AUC (p) | ΔTop-10% pooled (p) | ΔTop-10% own set (p) |
|---|---|---|---|---|---|
| 0 | -0.000001 | 0.362 | -0.003 (0.502) | +0.000 (0.407) | +0.000 (0.419) |
| 1 | +0.000001 | 0.362 | +0.000 (0.365) | +0.000 (0.861) | +0.000 (0.857) |
| 2 | -0.000008 | 0.654 | -0.020 (0.923) | -0.016 (0.917) | -0.016 (0.916) |
| 3 | -0.000017 | 0.825 | -0.006 (0.550) | -0.031 (0.938) | -0.016 (0.793) |
| 4 | -0.000009 | 0.528 | -0.007 (0.741) | -0.016 (0.654) | -0.031 (0.874) |
| 5 | -0.000003 | 0.544 | -0.006 (0.641) | +0.000 (0.356) | +0.000 (0.349) |
| 6 | -0.000006 | 0.624 | -0.005 (0.578) | -0.031 (0.913) | -0.016 (0.772) |
| 7 | +0.000092 | 0.101 | -0.009 (0.696) | +0.000 (0.546) | +0.000 (0.556) |
| 8 | -0.000007 | 0.535 | -0.007 (0.619) | -0.016 (0.735) | +0.000 (0.466) |
| 9 | -0.000007 | 0.797 | -0.009 (0.733) | +0.031 (0.380) | +0.031 (0.390) |
