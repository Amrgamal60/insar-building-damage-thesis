# Test statistics compared inside the same surrogate null (exploratory, synthetic events only)

Datasets per cell: 100, 100. Null draws per dataset: 999. Same synthetic datasets, folds and surrogates as the planted-signal check of 2026-11-11; the frozen statistic (ap) reproduces those records with max |difference| 0.0e+00.

Share of datasets detected (p < 0.05, with the sign condition where one applies), 95% Wilson interval:

| Statistic | 2. 0.65 t (nonlinear soil) | 3. 0.7 H (hidden spatial field) |
|---|---|---|
| change in out-of-fold average precision (frozen Test A) | 11/100 [6, 19]% | 5/100 [2, 11]% |
| change in out-of-fold log-likelihood | 4/100 [2, 10]% | 3/100 [1, 8]% |
| change in in-sample log-likelihood | 10/100 [6, 17]% | 5/100 [2, 11]% |
| velocity coefficient, negative tail | 3/100 [1, 8]% | 2/100 [1, 7]% |
| |velocity coefficient| | 3/100 [1, 8]% | 4/100 [2, 10]% |

Paired against ap on the same datasets (detected by this statistic only / by ap only; exact McNemar p):

| Statistic | 2. 0.65 t (nonlinear soil) | 3. 0.7 H (hidden spatial field) |
|---|---|---|
| oofll | 2 / 9; p 0.0654 | 2 / 4; p 0.688 |
| llr | 7 / 8; p 1 | 4 / 4; p 1 |
| coef | 3 / 11; p 0.0574 | 1 / 4; p 0.375 |
| abscoef | 3 / 11; p 0.0574 | 3 / 4; p 1 |

p deciles (0,.1], ..., (.9,1]:

- 2. 0.65 t (nonlinear soil): ap [20, 6, 7, 12, 9, 5, 4, 12, 8, 17]; oofll [18, 11, 12, 10, 11, 6, 6, 8, 7, 11]; llr [17, 6, 14, 10, 6, 9, 12, 5, 9, 12]; coef [14, 8, 14, 10, 9, 9, 8, 2, 15, 11]; abscoef [8, 11, 8, 7, 9, 10, 10, 11, 15, 11]
- 3. 0.7 H (hidden spatial field): ap [11, 10, 12, 7, 8, 7, 11, 12, 9, 13]; oofll [14, 7, 10, 6, 7, 12, 13, 12, 7, 12]; llr [12, 8, 13, 9, 7, 5, 13, 9, 15, 9]; coef [9, 9, 11, 8, 7, 8, 14, 9, 20, 5]; abscoef [6, 10, 7, 13, 7, 7, 8, 17, 17, 8]

Source hashes: `planted_signal.py` 977f626f1c72ab25e6c3f70b062fe1010252b9027f0e8bba113f4acad882b8f4, `testa_core.py` f4d71575c3179ef2f6ac7aeff8e0a26c14ab515db76ad937e411fae9e6e38430, `nyc_lib.py` 619e4de49415bc2f33cc7e54cd91f26740a37de8c0fcd0d990503a93f4546db1, `statistic_comparison.py` 4f74ad9d205b3c4391598bc50ce44240cbbc334019ddca3f2ed4420fe37dfe9c.
