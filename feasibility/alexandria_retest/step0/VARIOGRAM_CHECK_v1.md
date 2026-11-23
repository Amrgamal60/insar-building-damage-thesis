# Variogram check of the retest nulls (outcome-blind; read before any planted or real p-value)

999 draws per null; pixel field 1821 pixels in 341 cells; cell level on the 241 primary cells.
Cells give the surrogates' median as a multiple of the observed semivariance; * = observed outside the surrogates' 95% range.

## Pixel level (lag unit 100 m)

| Null | explained variance | lag 1 | lag 2 | lag 3 | lag 4 | lag 5 | lag 6 | lag 7 | lag 8 | lag 9 | lag 10 | lag 11 | lag 12 | lag 13 | lag 14 | lag 15 | lag 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pairs | | 6511 | 9094 | 11459 | 16421 | 16811 | 19528 | 27663 | 23706 | 28546 | 27855 | 30429 | 33601 | 30589 | 34827 | 31031 | 30467 |
| c1 conditional, Austin fit (in-sample) | 0.957 | 2.39* | 1.45* | 1.24* | 1.16* | 1.10* | 1.06* | 1.03 | 1.02 | 1.01 | 1.00 | 0.99 | 0.98 | 0.97 | 0.97 | 0.97 | 0.96 |
| c2 conditional, cross-fitted (min leaf 60) | 0.437 | 5.10* | 2.86* | 2.17* | 1.92* | 1.64* | 1.44* | 1.34* | 1.24 | 1.20 | 1.16 | 1.17 | 1.11 | 1.06 | 1.09 | 1.07 | 1.01 |
| a unconditional pixel null | 0.000 | 1.85* | 1.25 | 1.07 | 1.09 | 0.99 | 0.94 | 0.98 | 0.96 | 1.00 | 1.00 | 1.05 | 1.02 | 0.99 | 1.05* | 1.05* | 0.97 |

## Cell level (lag unit 250 m)

| Null | explained variance | lag 1 | lag 2 | lag 3 | lag 4 | lag 5 | lag 6 |
|---|---|---|---|---|---|---|---|
| pairs | | 693 | 899 | 1061 | 1843 | 1403 | 1767 |
| c1 conditional, Austin fit (in-sample) | 0.957 | 1.17* | 1.05 | 1.00 | 0.97 | 0.95 | 0.94 |
| c2 conditional, cross-fitted (min leaf 60) | 0.437 | 2.75* | 2.10* | 1.75* | 1.56 | 1.52 | 1.46 |
| a unconditional pixel null | 0.000 | 1.70* | 1.87* | 1.86* | 1.87* | 1.83* | 1.77* |
| original plain variogram-matching (cell level) |  | 1.93* | 1.43 | 1.22 | 1.11 | 1.04 | 0.97 |

