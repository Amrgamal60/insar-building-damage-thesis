# NYC decoy run (code check, not a result)

**Plan:** `NYC_REPLICATION_PLAN.md` (frozen copy `freeze/NYC_REPLICATION_PLAN_frozen.md`), §11–§13. **Reproduce:** `../../.venv/bin/python -I scripts/11_models.py raw out --decoy`, then `scripts/12_report.py out --decoy`.

**Decoy outcome:** each of the 185 events moved to a random eligible domain cell at 250 m (seed 99), keeping its date (§13 step 4). These numbers check the code end to end and say nothing about InSAR and collapses. Nothing changes because of them except outright code errors, which are logged in §14. Secondary analyses other than 8 and 9 used reduced draw counts (§14 deviation 2).

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

In the decoy run this check describes the real primary analysis's windows and surrogates, not the decoy's.

## 2. Decision (§11)

- **Incremental-value replication: not replicated.** Primary analysis (domain, 250 m, logistic regression, Baseline 1 + x/y, 1-year window): out-of-fold PR AUC 0.000188 → 0.000203, change +0.000014; variogram-matching null p = 0.153 (999 draws). Rule: change > 0 and p < 0.05.
- **Directional concordance: opposite.** Line-of-sight velocity is positive toward the satellite. Measure: the median over risk sets of (event cell − median of its controls), standardised velocity: +0.146 (42% of risk sets below 0). Below 0 is concordant with Alexandria: event cells move away from the satellite relative to their controls, as relative subsidence would. Above 0 is opposite.
  - Same measure in raw line of sight: +0.40 mm/yr. Raw values are not standardised, so they keep each window's landmass-group medians and spread. Medians pooled over rows (controls repeat across risk sets, so these need not differ by the value above): event cells +0.64, control rows -0.59 mm/yr.
  - Velocity coefficient in a logistic regression fitted on all rows (standardised, conditional on the baseline features): +0.087, sign opposite (negative = concordant).
- **Together:** no incremental-value replication (opposite deformation direction).
- **Effect size:** +0.000014 (95% refit-bootstrap interval -0.000021 to +0.000054, 2000 of 2000 resamples).
- **Largest p across the six nulls** (Alexandria's LiCSAR standard, reported only): 0.162 (PR AUC p of each: Variogram-matching (primary) 0.153; Free permutation 0.15442; Within-block permutation 0.12394; MSR 0.160; MSR, amplitude-adjusted 0.133; Variogram-matching, observed values 0.162).

**Sample:** 81 risk sets over 76 windows; 389,658 rows; 4,864 cells; prevalence 0.000208 (one event per risk set, §9). Events from 2017-07-16 not used: 1 earlier event in the cell. Cells without a static input: 0.

| Metric | Baseline 1 + x/y | + velocity | Change | p (variogram-matching) | Null median | 95% refit-bootstrap interval |
|---|---|---|---|---|---|---|
| PR AUC (primary) | 0.000188 | 0.000203 | +0.000014 | 0.153 | -0.000001 | -0.000021 to +0.000054 |
| ROC AUC | 0.4654 | 0.4826 | +0.0172 | 0.230 | -0.0013 | -0.0241 to +0.0749 |
| Top-10% recall, pooled (share of events in the top 10% of all rows) | 0.0617 | 0.0988 | +0.0370 | 0.094 | +0.0000 | -0.0494 to +0.0789 |
| Top 10% of own risk set (share of events) | 0.0617 | 0.0864 | +0.0247 | 0.218 | +0.0000 | – |

The bootstrap interval is not computed for the own-risk-set top-10% share.

## 3. All nulls on the primary analysis (primary and secondary 8)

| Null | Draws | p, PR AUC | p, ROC AUC | p, Top-10% recall, pooled | p, Top 10% of own risk set |
|---|---|---|---|---|---|
| Variogram-matching (primary, §10) | 999 | 0.153 | 0.230 | 0.094 | 0.218 |
| Free permutation | 2000 | 0.15442 | 0.19440 | 0.12144 | 0.23588 |
| Within-block permutation | 2000 | 0.12394 | 0.15142 | 0.11194 | 0.26387 |
| MSR | 999 | 0.160 | 0.241 | 0.087 | 0.202 |
| MSR, amplitude-adjusted | 999 | 0.133 | 0.207 | 0.068 | 0.169 |
| Variogram-matching, observed values | 999 | 0.162 | 0.220 | 0.103 | 0.211 |


## 4. Secondary analyses (no decision attached; primary null unless stated)

| Analysis | Risk sets | PR AUC | Change | p | Draws | Interval | ΔROC AUC (p) | ΔTop-10% pooled (p) | ΔTop-10% own set (p) | Direction |
|---|---|---|---|---|---|---|---|---|---|---|
| 1. Whole NYC (generalization) | 81 | 0.000123 → 0.000126 | +0.000003 | 0.220 | 199 | -0.000017 to +0.000026 | +0.003 (0.175) | +0.049 (0.140) | +0.037 (0.270) | opposite |
| 2. 200 m cells | 71 | 0.000099 → 0.000097 | -0.000002 | 0.875 | 199 | -0.000011 to +0.000011 | -0.004 (0.760) | -0.014 (0.880) | +0.000 (0.605) | opposite |
| 3. Random forest | 81 | 0.000247 → 0.000259 | +0.000011 | 0.29412 | 16 | -0.000068 to +0.000105 | +0.011 (0.23529) | +0.049 (0.23529) | +0.049 (0.17647) | opposite |
| 4. Baseline 2 (adds building age) | 81 | 0.000183 → 0.000197 | +0.000014 | 0.125 | 199 | -0.000026 to +0.000034 | +0.017 (0.205) | -0.012 (0.345) | +0.012 (0.110) | opposite |
| 5. 2-year window | 62 | 0.000196 → 0.000198 | +0.000002 | 0.325 | 199 | -0.000047 to +0.000045 | -0.002 (0.305) | +0.016 (0.415) | +0.016 (0.415) | opposite |
| 6. 3-year window | 44 | 0.000230 → 0.000259 | +0.000029 | 0.090 | 199 | -0.000032 to +0.000100 | +0.026 (0.075) | +0.023 (0.500) | +0.000 (0.790) | opposite |
| 7. Earlier control rule | 82 | 0.000188 → 0.000204 | +0.000016 | 0.100 | 199 | -0.000026 to +0.000052 | +0.019 (0.145) | +0.037 (0.050) | +0.024 (0.110) | opposite |
| 11. Never-case control rule | 81 | 0.000190 → 0.000204 | +0.000014 | 0.130 | 199 | -0.000031 to +0.000035 | +0.016 (0.205) | +0.025 (0.195) | +0.025 (0.205) | opposite |
| 12. Linear-only velocity | 81 | 0.000188 → 0.000185 | -0.000004 | 0.685 | 199 | -0.000028 to +0.000017 | -0.012 (0.745) | +0.012 (0.390) | +0.000 (0.700) | opposite |
| 13. No construction mask | 81 | 0.000188 → 0.000204 | +0.000016 | 0.125 | 199 | -0.000024 to +0.000041 | +0.020 (0.185) | +0.037 (0.130) | +0.025 (0.220) | opposite |
| 14. Availability only: log(1 + valid pixels) (coverage check, §12.14) | 81 | 0.000188 → 0.000182 | -0.000006 | 0.785 | 199 | -0.000037 to +0.000022 | -0.010 (0.650) | +0.000 (0.665) | +0.000 (0.665) | – |
| 15. Ohenhen et al. 2025 VLM, static (exploratory) (retrospective, carries no weight, §12.15) | 81 | 0.000189 → 0.000196 | +0.000007 | 0.300 | 199 | -0.000031 to +0.000047 | +0.004 (0.445) | +0.025 (0.260) | +0.025 (0.260) | – |

Direction uses the same measure as §11 and applies only to velocity fields. Δ columns: change from the baseline, with its p from the same null.

## 5. Sample and exclusions per analysis (§8, §9)

| Analysis | Risk sets | Windows | Rows | Cells | Prevalence | Cells without a static input | Rows without building age | Events from | Of these, not used |
|---|---|---|---|---|---|---|---|---|---|
| Primary: domain, 250 m, logistic regression, Baseline 1, 1-year window | 81 | 76 | 389,658 | 4,864 | 0.000208 | 0 | – | 2017-07-16 | 1 earlier event in the cell |
| 1. Whole NYC (generalization) | 81 | 76 | 813,782 | 10,145 | 0.000100 | 9 | – | 2017-07-16 | 1 earlier event in the cell |
| 2. 200 m cells | 71 | 68 | 516,568 | 7,339 | 0.000137 | 0 | – | 2017-07-16 | 10 cell not in the population; 1 earlier event in the cell |
| 3. Random forest | 81 | 76 | 389,658 | 4,864 | 0.000208 | 0 | – | 2017-07-16 | 1 earlier event in the cell |
| 4. Baseline 2 (adds building age) | 81 | 76 | 389,658 | 4,864 | 0.000208 | 0 | 0 | 2017-07-16 | 1 earlier event in the cell |
| 5. 2-year window | 62 | 59 | 296,431 | 4,844 | 0.000209 | 0 | – | 2018-07-16 | 1 earlier event in the cell |
| 6. 3-year window | 44 | 41 | 209,092 | 4,825 | 0.000210 | 0 | – | 2019-07-16 | 1 earlier event in the cell |
| 7. Earlier control rule | 82 | 77 | 404,846 | 4,966 | 0.000203 | 0 | – | 2017-07-16 | none |
| 11. Never-case control rule | 81 | 76 | 386,424 | 4,864 | 0.000210 | 0 | – | 2017-07-16 | 1 earlier event in the cell |
| 12. Linear-only velocity | 81 | 76 | 389,658 | 4,864 | 0.000208 | 0 | – | 2017-07-16 | 1 earlier event in the cell |
| 13. No construction mask | 81 | 76 | 389,722 | 4,864 | 0.000208 | 0 | – | 2017-07-16 | 1 earlier event in the cell |
| 14. Availability only: log(1 + valid pixels) (coverage check, §12.14) | 81 | 76 | 389,658 | 4,864 | 0.000208 | 0 | – | 2017-07-16 | 1 earlier event in the cell |
| 15. Ohenhen et al. 2025 VLM, static (exploratory) (retrospective, carries no weight, §12.15) | 81 | 76 | 390,090 | 4,856 | 0.000208 | 0 | – | 2017-07-16 | 1 earlier event in the cell |

## 6. Other fold assignments (secondary 9; primary null, no bootstrap)

| Fold seed | PR AUC change | p | ΔROC AUC (p) | ΔTop-10% pooled (p) | ΔTop-10% own set (p) |
|---|---|---|---|---|---|
| 0 | +0.000009 | 0.203 | +0.024 (0.155) | -0.025 (0.989) | -0.012 (0.910) |
| 1 | +0.000005 | 0.296 | +0.020 (0.253) | -0.049 (0.933) | -0.049 (0.941) |
| 2 | +0.000006 | 0.297 | -0.004 (0.609) | -0.012 (0.953) | -0.012 (0.954) |
| 3 | +0.000003 | 0.348 | +0.011 (0.296) | +0.000 (0.730) | +0.000 (0.718) |
| 4 | -0.000003 | 0.517 | +0.021 (0.225) | -0.012 (0.815) | -0.012 (0.835) |
| 5 | +0.000003 | 0.405 | +0.020 (0.263) | -0.025 (0.853) | +0.000 (0.360) |
| 6 | +0.000008 | 0.258 | +0.023 (0.257) | +0.000 (0.627) | +0.012 (0.326) |
| 7 | +0.000005 | 0.310 | +0.016 (0.307) | +0.049 (0.068) | +0.049 (0.075) |
| 8 | +0.000017 | 0.102 | +0.038 (0.096) | +0.012 (0.489) | +0.000 (0.764) |
| 9 | +0.000002 | 0.330 | +0.011 (0.264) | +0.012 (0.334) | +0.012 (0.335) |
