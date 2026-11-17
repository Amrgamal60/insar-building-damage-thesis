# Test statistics compared inside the same surrogate null (exploratory, synthetic events only)

Datasets per cell: 100, 100, 100. Null draws per dataset: 999. Same synthetic datasets, folds and surrogates as the planted-signal check of 2026-11-11; the frozen statistic (ap) reproduces those records with max |difference| 0.0e+00.

Share of datasets detected (p < 0.05, with the sign condition where one applies), 95% Wilson interval:

| Statistic | 1. nothing added | 4. beta = -0.1 | 5. beta = -0.2 |
|---|---|---|---|
| change in out-of-fold average precision (frozen Test A) | 5/100 [2, 11]% | 34/100 [25, 44]% | 75/100 [66, 82]% |
| change in out-of-fold log-likelihood | 7/100 [3, 14]% | 66/100 [56, 75]% | 100/100 [96, 100]% |
| change in in-sample log-likelihood | 9/100 [5, 16]% | 68/100 [58, 76]% | 100/100 [96, 100]% |
| velocity coefficient, negative tail | 7/100 [3, 14]% | 55/100 [45, 64]% | 96/100 [90, 98]% |
| |velocity coefficient| | 7/100 [3, 14]% | 55/100 [45, 64]% | 96/100 [90, 98]% |

Paired against ap on the same datasets (detected by this statistic only / by ap only; exact McNemar p):

| Statistic | 1. nothing added | 4. beta = -0.1 | 5. beta = -0.2 |
|---|---|---|---|
| oofll | 5 / 3; p 0.727 | 34 / 2; p 1.94e-08 | 25 / 0; p 5.96e-08 |
| llr | 7 / 3; p 0.344 | 37 / 3; p 1.95e-08 | 25 / 0; p 5.96e-08 |
| coef | 6 / 4; p 0.754 | 25 / 4; p 0.000104 | 23 / 2; p 1.94e-05 |
| abscoef | 6 / 4; p 0.754 | 25 / 4; p 0.000104 | 23 / 2; p 1.94e-05 |

p deciles (0,.1], ..., (.9,1]:

- 1. nothing added: ap [12, 6, 12, 14, 13, 8, 8, 8, 8, 11]; oofll [16, 6, 15, 11, 14, 8, 5, 7, 5, 13]; llr [10, 9, 10, 8, 16, 11, 8, 9, 7, 12]; coef [14, 8, 9, 10, 9, 10, 12, 6, 7, 15]; abscoef [10, 5, 10, 8, 15, 10, 10, 12, 9, 11]
- 4. beta = -0.1: ap [47, 13, 4, 6, 7, 6, 3, 5, 4, 5]; oofll [77, 15, 2, 0, 1, 2, 2, 0, 0, 1]; llr [76, 13, 4, 4, 1, 0, 2, 0, 0, 0]; coef [68, 10, 10, 5, 4, 1, 0, 1, 1, 0]; abscoef [68, 10, 10, 5, 4, 1, 0, 1, 1, 0]
- 5. beta = -0.2: ap [83, 8, 1, 4, 2, 1, 0, 1, 0, 0]; oofll [100, 0, 0, 0, 0, 0, 0, 0, 0, 0]; llr [100, 0, 0, 0, 0, 0, 0, 0, 0, 0]; coef [100, 0, 0, 0, 0, 0, 0, 0, 0, 0]; abscoef [100, 0, 0, 0, 0, 0, 0, 0, 0, 0]

Source hashes: `planted_signal.py` 977f626f1c72ab25e6c3f70b062fe1010252b9027f0e8bba113f4acad882b8f4, `testa_core.py` f4d71575c3179ef2f6ac7aeff8e0a26c14ab515db76ad937e411fae9e6e38430, `nyc_lib.py` 619e4de49415bc2f33cc7e54cd91f26740a37de8c0fcd0d990503a93f4546db1, `statistic_comparison.py` 4f74ad9d205b3c4391598bc50ce44240cbbc334019ddca3f2ed4420fe37dfe9c.
