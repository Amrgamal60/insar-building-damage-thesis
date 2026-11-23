# Planted check (HAZARD_TX_PLAN.md §9; synthetic outcomes only)

- **dallas:** 97,764 rows (mapped, complete Baseline 1), 1,145 flagged; target 1068 events (12.5 flagged if unrelated); blocks b2/b6/b12 214/41/15 (with flagged houses 66/29/12).
  - field-size reference, 2021 (before follow-up): 337 houses with an event, 229 blocks, between-block SD of the log rate 0.798
  - field-size reference, 2022-2025 (follow-up; outcome only): 2266 houses with an event, 229 blocks, between-block SD of the log rate 0.708
- **sanantonio:** 214,417 rows (mapped, complete Baseline 1), 14,456 flagged; target 6394 events (431.1 flagged if unrelated); blocks b2/b6/b12 314/51/18 (with flagged houses 197/44/15).
  - field-size reference, 2021 (before follow-up): 2905 houses with an event, 345 blocks, between-block SD of the log rate 0.728
  - field-size reference, 2022-2025 (follow-up; outcome only): 10544 houses with an event, 345 blocks, between-block SD of the log rate 0.672

Rejection = IRR > 1 and one-sided p < 0.05. Adjusted = the primary model (city intercepts, city x Baseline 1, flag). 'ok'/'NO' = acceptability (null cells 1-6). Demonstrated = rejected and T > 0.

| Cell | Kind | Datasets | Events (flagged) | Block SD | adj r1 | adj r2 | adj r3 | adj r4 | unadj r1-r4 | T>0 | demonstrated r1-r4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | null (range 1 km, SD 0.5, IRR 1.00) | 1000 | 7464 (445.0) | 0.415 | 0.060 ok | 0.050 ok | 0.049 ok | 0.044 ok | 0.062, 0.047, 0.050, 0.044 |  |  |
| 2 | null (range 3 km, SD 0.5, IRR 1.00) | 1000 | 7463 (444.5) | 0.528 | 0.080 NO | 0.065 NO | 0.060 ok | 0.050 ok | 0.083, 0.069, 0.048, 0.035 |  |  |
| 3 | null (range 8 km, SD 0.5, IRR 1.00) | 1000 | 7461 (443.0) | 0.550 | 0.082 NO | 0.073 NO | 0.053 ok | 0.048 ok | 0.147, 0.133, 0.079, 0.057 |  |  |
| 4 | null (range 15 km, SD 0.5, IRR 1.00) | 1000 | 7466 (449.4) | 0.521 | 0.097 NO | 0.086 NO | 0.071 NO | 0.068 NO | 0.255, 0.231, 0.153, 0.118 |  |  |
| 5 | null (range 3 km, SD 1.0, IRR 1.00) | 1000 | 7459 (442.2) | 0.839 | 0.086 NO | 0.069 NO | 0.054 ok | 0.047 ok | 0.085, 0.060, 0.037, 0.037 |  |  |
| 6 | null (range 3 km, SD 0.5, trend, IRR 1.00) | 1000 | 7462 (451.3) | 0.575 | 0.063 ok | 0.052 ok | 0.048 ok | 0.040 ok | 0.291, 0.266, 0.219, 0.197 |  |  |
| 7 | U null (range 3 km, SD 0.5, IRR 1.00) | 500 | 7460 (772.2) | 0.781 | 0.062 | 0.054 | 0.054 | 0.042 | 1.000, 1.000, 1.000, 1.000 | 0.164 | 0.042, 0.040, 0.036, 0.032 |
| 8 | U null, soil squared (reported) (range 3 km, SD 0.5, IRR 1.00) | 500 | 7468 (807.4) | 0.814 | 0.320 | 0.286 | 0.244 | 0.224 | 1.000, 1.000, 1.000, 1.000 | 0.406 | 0.290, 0.268, 0.230, 0.204 |
| 9 | power (range 3 km, SD 0.5, IRR 1.50) | 500 | 7462 (1061.0) | 0.808 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000, 1.000, 1.000, 1.000 | 1.000 | 1.000, 1.000, 1.000, 1.000 |
| 10 | power (range 3 km, SD 0.5, IRR 1.74) | 500 | 7462 (1186.4) | 0.821 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000, 1.000, 1.000, 1.000 | 1.000 | 1.000, 1.000, 1.000, 1.000 |

Per city (r3, each city's own adjusted model; descriptive, and the D1 alternative of Holm over two cities). Cells: rejection at 0.05 / 0.025 / Holm; for cells with T: demonstrated (own T > 0) at 0.05 / Holm. Block SD = median per city.

| Cell | City | Block SD | Reject 0.05 | Reject 0.025 | Reject Holm | Demonstrated 0.05 | Demonstrated Holm |
|---|---|---|---|---|---|---|---|
| 1 | dallas | 0.242 | 0.031 | 0.012 | 0.013 | nan | nan |
| 1 | sanantonio | 0.238 | 0.050 | 0.023 | 0.023 | nan | nan |
| 2 | dallas | 0.397 | 0.022 | 0.008 | 0.009 | nan | nan |
| 2 | sanantonio | 0.392 | 0.059 | 0.029 | 0.029 | nan | nan |
| 3 | dallas | 0.429 | 0.036 | 0.014 | 0.015 | nan | nan |
| 3 | sanantonio | 0.423 | 0.054 | 0.024 | 0.024 | nan | nan |
| 4 | dallas | 0.391 | 0.022 | 0.009 | 0.009 | nan | nan |
| 4 | sanantonio | 0.390 | 0.074 | 0.047 | 0.048 | nan | nan |
| 5 | dallas | 0.751 | 0.030 | 0.012 | 0.012 | nan | nan |
| 5 | sanantonio | 0.736 | 0.053 | 0.027 | 0.027 | nan | nan |
| 6 | dallas | 0.443 | 0.023 | 0.011 | 0.012 | nan | nan |
| 6 | sanantonio | 0.449 | 0.046 | 0.027 | 0.028 | nan | nan |
| 7 | dallas | 0.572 | 0.034 | 0.010 | 0.010 | 0.030 | 0.010 |
| 7 | sanantonio | 0.703 | 0.054 | 0.028 | 0.028 | 0.042 | 0.026 |
| 7 | either city (Holm) |  |  |  |  |  | 0.036 |
| 8 | dallas | 0.569 | 0.014 | 0.004 | 0.004 | 0.014 | 0.004 |
| 8 | sanantonio | 0.737 | 0.258 | 0.166 | 0.166 | 0.256 | 0.166 |
| 8 | either city (Holm) |  |  |  |  |  | 0.168 |
| 9 | dallas | 0.577 | 0.388 | 0.258 | 0.388 | 0.380 | 0.380 |
| 9 | sanantonio | 0.731 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| 9 | either city (Holm) |  |  |  |  |  | 1.000 |
| 10 | dallas | 0.577 | 0.638 | 0.496 | 0.638 | 0.616 | 0.616 |
| 10 | sanantonio | 0.745 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| 10 | either city (Holm) |  |  |  |  |  | 1.000 |

**Rule:** none acceptable: the user decides; chosen inference: None; power (demonstrated) at IRR 1.5 (cell 9) and 1.74 (cell 10): {}; complete: True.
