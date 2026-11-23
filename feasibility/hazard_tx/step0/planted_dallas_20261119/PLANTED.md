# Planted check (HAZARD_TX_PLAN.md §9; synthetic outcomes only)

- **dallas:** 97,764 rows (mapped, complete Baseline 1), 1,145 flagged; target 1068 events (12.5 flagged if unrelated); blocks b2/b6/b12 214/41/15 (with flagged houses 66/29/12).
  - field-size reference, 2021 (before follow-up): 337 houses with an event, 229 blocks, between-block SD of the log rate 0.798
  - field-size reference, 2022-2025 (follow-up; outcome only): 2266 houses with an event, 229 blocks, between-block SD of the log rate 0.708

Rejection = IRR > 1 and one-sided p < 0.05. Adjusted = the primary model (city intercepts, city x Baseline 1, flag). 'ok'/'NO' = acceptability (null cells 1-6). Demonstrated = rejected and T > 0.

| Cell | Kind | Datasets | Events (flagged) | Block SD | adj r1 | adj r2 | adj r3 | adj r4 | unadj r1-r4 | T>0 | demonstrated r1-r4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | null (range 1 km, SD 0.5, IRR 1.00) | 1000 | 1068 (12.6) | 0.242 | 0.078 NO | 0.036 ok | 0.031 ok | 0.031 ok | 0.082, 0.032, 0.027, 0.031 |  |  |
| 2 | null (range 3 km, SD 0.5, IRR 1.00) | 1000 | 1066 (12.4) | 0.397 | 0.064 NO | 0.026 ok | 0.022 ok | 0.024 ok | 0.069, 0.020, 0.019, 0.022 |  |  |
| 3 | null (range 8 km, SD 0.5, IRR 1.00) | 1000 | 1068 (12.7) | 0.429 | 0.064 NO | 0.034 ok | 0.036 ok | 0.036 ok | 0.071, 0.027, 0.030, 0.033 |  |  |
| 4 | null (range 15 km, SD 0.5, IRR 1.00) | 1000 | 1068 (12.6) | 0.391 | 0.059 ok | 0.019 ok | 0.022 ok | 0.027 ok | 0.075, 0.025, 0.028, 0.031 |  |  |
| 5 | null (range 3 km, SD 1.0, IRR 1.00) | 1000 | 1066 (12.7) | 0.751 | 0.074 NO | 0.032 ok | 0.030 ok | 0.026 ok | 0.070, 0.030, 0.025, 0.028 |  |  |
| 6 | null (range 3 km, SD 0.5, trend, IRR 1.00) | 1000 | 1067 (12.6) | 0.443 | 0.053 ok | 0.021 ok | 0.023 ok | 0.026 ok | 0.061, 0.028, 0.027, 0.033 |  |  |
| 7 | U null (range 3 km, SD 0.5, IRR 1.00) | 500 | 1067 (16.5) | 0.572 | 0.070 | 0.036 | 0.034 | 0.022 | 0.286, 0.158, 0.166, 0.130 | 0.172 | 0.052, 0.036, 0.030, 0.016 |
| 8 | U null, soil squared (reported) (range 3 km, SD 0.5, IRR 1.00) | 500 | 1068 (15.2) | 0.569 | 0.032 | 0.014 | 0.014 | 0.014 | 0.208, 0.106, 0.108, 0.102 | 0.192 | 0.032, 0.014, 0.014, 0.012 |
| 9 | power (range 3 km, SD 0.5, IRR 1.50) | 500 | 1069 (24.4) | 0.577 | 0.558 | 0.414 | 0.388 | 0.348 | 0.844, 0.686, 0.656, 0.604 | 0.552 | 0.510, 0.410, 0.380, 0.340 |
| 10 | power (range 3 km, SD 0.5, IRR 1.74) | 500 | 1069 (28.3) | 0.577 | 0.798 | 0.652 | 0.638 | 0.598 | 0.962, 0.890, 0.864, 0.816 | 0.782 | 0.754, 0.638, 0.616, 0.580 |

**Rule:** r3 acceptable in null cells 1-6 (adjusted test); chosen inference: r3; power (demonstrated) at IRR 1.5 (cell 9) and 1.74 (cell 10): {'9': 0.38, '10': 0.616}; complete: True.
