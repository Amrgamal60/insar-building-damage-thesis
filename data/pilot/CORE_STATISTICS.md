# Statistics for the historic-core velocity result

**Comparison:** baseline + x/y vs baseline + x/y + Shirzaei velocity, on the Shirzaei-covered cells of the historic core (the 7 central districts named in the audit). Same 63 events, same primary spatial folds (seed 42), no new features, no tuning.
**Reproduce:** `.venv/bin/python scripts/09_core_statistics.py` (after 07 and 08).
**Primary test, fixed before this run:** logistic regression, 250 m, change in PR AUC. Everything else is secondary, with no correction for multiple tests.

- **Refit block bootstrap** (2,000 resamples for logistic regression, 500 for the random forest): 2 km blocks are resampled with replacement, and copies keep their block's fold. Both models are refitted and the out-of-fold change is recomputed; the interval is the 2.5–97.5 percentiles.
- **Free permutation:** velocity is shuffled among all core cells and the velocity model refitted; this tests any association beyond baseline + x/y.
- **Within-block permutation:** velocity is shuffled only inside each 2 km block. The null keeps the ~2 km velocity pattern, so this asks whether finer-scale alignment with collapse cells adds anything.
- **p-values** are one-sided: (1 + null changes ≥ observed) / (1 + permutations); < 0.001 = no permutation reached the observed change.

## Result

- **Primary test: the association passes both permutation tests, but the size of the gain is uncertain.** Logistic regression at 250 m: PR AUC 0.328 → 0.372 (+0.044). Free permutation p = 0.011, within-block p = 0.018. The refit-bootstrap interval for the change, −0.014 to +0.130, includes zero.
- **Same picture at 200 m:** PR AUC +0.093 (p < 0.001 in both permutation tests; interval −0.034 to +0.159). ROC AUC and top-10% capture give p = 0.003–0.051 across both sizes, with every interval including zero.
- **Random forest: not significant.** At 250 m p = 0.05–0.11 for all three metrics; at 200 m there is no clear gain.
- **Reading:** on these 32 core collapse cells, velocity's link to collapse cells beyond baseline + x/y is unlikely to be chance. The within-block null gives similar p-values, so it is not only a ~2 km pattern. How much it improves the ranking in another sample of blocks is not pinned down.
- **Limits:** the permutations break velocity's spatial smoothness below 2 km, so a smooth-field null could be stricter. Only the primary test was fixed in advance; there is no multiple-test correction. The Shirzaei period is unknown, so this is a retrospective association.

| Cell size | Model | Metric | Cells (collapse cells) | Baseline + x/y → + velocity | Change | 95% refit-bootstrap interval | p, free permutation | p, within-block permutation |
|---|---|---|---|---|---|---|---|---|
| 250 m | logistic regression | PR AUC | 241 (32) | 0.328 → 0.372 | +0.044 | -0.014 to +0.130 | 0.011 | 0.018 |
| 250 m | logistic regression | ROC AUC | 241 (32) | 0.746 → 0.775 | +0.029 | -0.018 to +0.072 | 0.014 | 0.036 |
| 250 m | logistic regression | Collapse cells in top 10% | 241 (32) | 25% → 31% | +6 pts | -5 pts to +17 pts | 0.044 | 0.051 |
| 250 m | random forest | PR AUC | 241 (32) | 0.249 → 0.285 | +0.036 | -0.040 to +0.098 | 0.108 | 0.094 |
| 250 m | random forest | ROC AUC | 241 (32) | 0.753 → 0.768 | +0.015 | -0.036 to +0.045 | 0.066 | 0.058 |
| 250 m | random forest | Collapse cells in top 10% | 241 (32) | 19% → 28% | +9 pts | -9 pts to +15 pts | 0.062 | 0.052 |
| 200 m | logistic regression | PR AUC | 347 (36) | 0.195 → 0.288 | +0.093 | -0.034 to +0.159 | < 0.001 | < 0.001 |
| 200 m | logistic regression | ROC AUC | 347 (36) | 0.711 → 0.746 | +0.035 | -0.020 to +0.085 | 0.003 | 0.012 |
| 200 m | logistic regression | Collapse cells in top 10% | 347 (36) | 25% → 31% | +6 pts | -9 pts to +17 pts | 0.028 | 0.031 |
| 200 m | random forest | PR AUC | 347 (36) | 0.225 → 0.239 | +0.013 | -0.039 to +0.061 | 0.080 | 0.128 |
| 200 m | random forest | ROC AUC | 347 (36) | 0.736 → 0.734 | -0.001 | -0.028 to +0.030 | 0.305 | 0.315 |
| 200 m | random forest | Collapse cells in top 10% | 347 (36) | 19% → 17% | -3 pts | -10 pts to +8 pts | 0.956 | 0.962 |
