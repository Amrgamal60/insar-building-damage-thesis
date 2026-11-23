# Variogram check of the retest nulls (outcome-blind; read before any planted or real p-value)

999 draws per null; pixel field 1357 pixels in the 241 primary cells; cell level on the same cells.
Cells give the surrogates' median as a multiple of the observed semivariance; * = observed outside the surrogates' 95% range.

## Pixel level (lag unit 100 m)

| Null | explained variance | lag 1 | lag 2 | lag 3 | lag 4 | lag 5 | lag 6 | lag 7 | lag 8 | lag 9 | lag 10 | lag 11 | lag 12 | lag 13 | lag 14 | lag 15 | lag 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pairs | | 4624 | 6196 | 7670 | 10960 | 11188 | 12958 | 18453 | 15854 | 19077 | 18608 | 20601 | 22393 | 20556 | 23342 | 20543 | 20036 |
| c1 linear conditional, baseline | 0.485 | 2.98* | 1.71* | 1.30* | 1.19 | 1.07 | 1.00 | 0.95 | 0.88 | 0.87 | 0.85 | 0.86 | 0.82 | 0.78 | 0.81 | 0.80 | 0.75 |
| c2 linear conditional, baseline + x/y | 0.629 | 2.30* | 1.34* | 1.06 | 0.99 | 0.93 | 0.91 | 0.90 | 0.87 | 0.88 | 0.86 | 0.87 | 0.84 | 0.81 | 0.83 | 0.83 | 0.80 |
| a unconditional pixel null | 0.000 | 2.00* | 1.28 | 1.05 | 1.06 | 0.99 | 0.98 | 1.00 | 0.97 | 1.01 | 1.01 | 1.05 | 1.02 | 0.98 | 1.05 | 1.05 | 0.99 |

## Cell level (lag unit 250 m)

| Null | explained variance | lag 1 | lag 2 | lag 3 | lag 4 | lag 5 | lag 6 |
|---|---|---|---|---|---|---|---|
| pairs | | 693 | 899 | 1061 | 1843 | 1403 | 1767 |
| c1 linear conditional, baseline | 0.485 | 0.95 | 0.85 | 0.76 | 0.72 | 0.71 | 0.69 |
| c2 linear conditional, baseline + x/y | 0.629 | 0.77* | 0.77 | 0.76 | 0.76 | 0.76 | 0.75 |
| a unconditional pixel null | 0.000 | 0.76 | 0.84 | 0.84 | 0.87 | 0.89* | 0.89* |
| original plain variogram-matching (cell level) |  | 1.93* | 1.43 | 1.22 | 1.11 | 1.04 | 0.97 |

