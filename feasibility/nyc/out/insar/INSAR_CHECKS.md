# InSAR checks before outcomes are joined

**Plan:** `NYC_REPLICATION_PLAN.md` §7 ("Before outcomes are joined"), §10, §13 step 3. **Reproduce:** `~/miniforge3/envs/opera/bin/python -I scripts/09_insar_velocities.py raw out`, then `../../.venv/bin/python -I scripts/10_insar_checks.py raw out`. No model is fitted and no InSAR value is compared with events.

## 1. Sign check (LaGuardia runways, full period, line of sight)

| Runway cells with a value | Runway cells: median LOS velocity (mm/yr) | Eligible cells: median (mm/yr) | Brooklyn+Queens eligible cells: median (mm/yr) | Runway cells below the city median | Result |
|---|---|---|---|---|---|
| 19 of 23 | -2.27 | -1.46 | -1.37 | 14 of 19 | pass |

The runway cells are the 250 m cells crossed by the OSM centre lines of runways 13/31 and 04/22. Positive line of sight = toward the satellite.

## 2. Coverage

**Pixels** (median over windows; share of the pixels whose centre is in an eligible 250 m cell; each pixel is counted under the first rule it fails):

| Window (days) | Pixels in eligible 250 m cells | Masked at a reference change | Component rule | Completeness rule | Construction mask | Valid |
|---|---|---|---|---|---|---|
| 1095 | 716,732 | 6.2% | 7.8% | 0.0% | 21.2% | 64.9% |
| 365 | 716,732 | 4.9% | 2.1% | 0.0% | 16.0% | 76.8% |
| 730 | 716,732 | 5.7% | 7.5% | 0.0% | 19.0% | 68.2% |

**Cells** with a value per window, and the raw (unstandardised) velocity's window median and IQR over eligible cells:

| Cell size | Window (days) | Windows | Eligible cells with a value: min / median | Domain cells with a value: min / median | Raw window median (mm/yr): range | Raw IQR (mm/yr): range |
|---|---|---|---|---|---|---|
| 200 m | 1095 | 42 | 15,000 / 15,015 of 15,438 | 7,307 / 7,310 of 7,475 | -13.5 to +9.0 | 1.3 to 3.1 |
| 200 m | 365 | 77 | 15,045 / 15,323 of 15,438 | 7,327 / 7,419 of 7,475 | -36.7 to +35.9 | 2.7 to 30.5 |
| 200 m | 730 | 60 | 15,011 / 15,035 of 15,438 | 7,314 / 7,323 of 7,475 | -15.6 to +18.3 | 1.3 to 4.2 |
| 250 m | 1095 | 42 | 10,019 / 10,030 of 10,320 | 4,898 / 4,903 of 5,001 | -13.6 to +9.0 | 1.2 to 3.1 |
| 250 m | 365 | 77 | 10,042 / 10,237 of 10,320 | 4,906 / 4,965 of 5,001 | -36.6 to +36.0 | 2.7 to 30.4 |
| 250 m | 730 | 60 | 10,031 / 10,040 of 10,320 | 4,901 / 4,907 of 5,001 | -15.6 to +18.3 | 1.3 to 4.2 |

The raw window velocities carry large offsets and spreads that change from window to window (no correction layers are applied, §7). The window standardisation of §7 removes each window's landmass medians and scales by its IQR, as planned.

## 3. Variogram check of the primary null (999 surrogates, seed 2027; 20 windows, seed 7)

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

Figure: `insar_checks.png` (coverage map, full-period velocity with the runway cells, one window's variogram check).
