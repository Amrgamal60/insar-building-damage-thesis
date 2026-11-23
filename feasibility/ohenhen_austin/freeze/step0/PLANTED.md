# Planted check (OHENHEN_AUSTIN_PLAN.md §9; synthetic outcomes only)

Field-size reference (outcome only, 2018-08-01 to 2021-12-31, 1223 events, 213 blocks): between-block SD of the log rate 0.628.

Rejection = IRR > 1 and one-sided p < 0.05. V = unadjusted flag; U adj = flag adjusted for Baseline 1 + x/y.

| Cell | Kind | Datasets | Events (flagged) | Block SD | V r1 | V r2 | V r3 | V r4 | U adj (r1, r2, r3, r4) | T>0 share |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | V null (range 1 km, SD 0.5, IRR 1.00) | 1000 | 836 (43.0) | 0.253 | 0.053 ok | 0.036 ok | 0.030 ok | 0.038 ok |  |  |
| 2 | V null (range 3 km, SD 0.5, IRR 1.00) | 1000 | 838 (43.6) | 0.400 | 0.074 NO | 0.038 ok | 0.032 ok | 0.055 ok |  |  |
| 3 | V null (range 8 km, SD 0.5, IRR 1.00) | 1000 | 836 (43.0) | 0.428 | 0.105 NO | 0.060 ok | 0.046 ok | 0.044 ok |  |  |
| 4 | V null (range 15 km, SD 0.5, IRR 1.00) | 1000 | 837 (43.4) | 0.387 | 0.130 NO | 0.092 NO | 0.073 NO | 0.064 NO |  |  |
| 5 | V null (range 3 km, SD 1.0, IRR 1.00) | 1000 | 838 (42.8) | 0.767 | 0.070 NO | 0.042 ok | 0.024 ok | 0.027 ok |  |  |
| 6 | V null (range 3 km, SD 0.5, trend, IRR 1.00) | 1000 | 835 (42.8) | 0.451 | 0.114 NO | 0.077 NO | 0.054 ok | 0.059 ok |  |  |
| 7 | U null (range 3 km, SD 0.5, IRR 1.00) | 500 | 795 (92.0) | 0.781 | 0.996 | 0.996 | 0.990 | 0.970 | 0.086, 0.054, 0.058, 0.056 | 0.244 |
| 8 | U null (reported) (range 3 km, SD 0.5, IRR 1.00) | 500 | 795 (85.4) | 0.725 | 0.996 | 0.988 | 0.970 | 0.930 | 0.064, 0.042, 0.042, 0.040 | 0.192 |
| 9 | V power (range 3 km, SD 0.5, IRR 1.50) | 500 | 837 (63.1) | 0.404 | 0.786 | 0.694 | 0.652 | 0.568 |  |  |
| 10 | V power (range 3 km, SD 0.5, IRR 2.00) | 500 | 836 (80.9) | 0.407 | 0.996 | 0.990 | 0.976 | 0.938 |  |  |
| 11 | U power (range 3 km, SD 0.5, IRR 1.50) | 500 | 794 (128.7) | 0.834 | 1.000 | 1.000 | 1.000 | 1.000 | 0.890, 0.838, 0.824, 0.730 | 0.798 |

**Rule:** none acceptable: the user decides; chosen inference: None; power at IRR 1.5 (cell 9): None; complete: True.
