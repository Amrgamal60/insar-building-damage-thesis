# NYC replication: secondary 3 (random forest), completed after the compute budget

**Status:** completed after the compute budget (§13.6 expired 2026-10-15 16:27:25), at the user's instruction, with no deadline (§14 deviation 10). All NYC results, including `NYC_RESULT.md`, had been seen before it was resumed. Model, seeds, counts (500 null draws, 500 refit-bootstrap resamples) and the primary null are as frozen (§12.3); the code is unchanged. **It carries no decision** (§11, §12) and does not change `NYC_RESULT.md`, which stays the report of the budgeted run (decision: not replicated).

**Reproduce:** `../../.venv/bin/python -I scripts/11_models.py raw out --real --jobs 16 --only s3` (execution environment of deviation 9; resumes from `out/models/real/checkpoints/s3/`), then `scripts/13_s3_addendum.py out --real`.

## 1. Result

| Metric | Baseline 1 + x/y | + velocity | Change | p (variogram-matching) | Null median | 95% refit-bootstrap interval |
|---|---|---|---|---|---|---|
| PR AUC (primary) | 0.000213 | 0.000244 | +0.000031 | 0.05190 | -0.000011 | -0.000065 to +0.000623 |
| ROC AUC | 0.4510 | 0.4694 | +0.0184 | 0.39521 | +0.0127 | -0.0601 to +0.0891 |
| Top-10% recall, pooled (share of events in the top 10% of all rows) | 0.1406 | 0.1250 | -0.0156 | 0.11976 | -0.0625 | -0.1057 to +0.0828 |
| Top 10% of own risk set (share of events) | 0.1406 | 0.1406 | +0.0000 | 0.05190 | -0.0625 | – |

- **Direction (same measure as §11):** opposite; median over risk sets +0.037 (47% of risk sets below 0; below 0 is concordant with Alexandria). The measure depends on the rows and the velocity field, not on the model, and equals the primary analysis's.
- **Refit bootstrap:** 500 of 500 resamples gave a result.
- **Run time of the resumed process** (started 2026-10-15 at about 17:08 Cairo; the budgeted part is not counted): 27.6 h.

## 2. Beside the primary analysis

| Analysis | Model | PR AUC | Change | p | Draws | Interval | ΔROC AUC (p) | ΔTop-10% pooled (p) | ΔTop-10% own set (p) | Direction |
|---|---|---|---|---|---|---|---|---|---|---|
| Primary (for comparison, from NYC_RESULT.md) | logistic regression | 0.000231 → 0.000227 | -0.000004 | 0.418 | 999 | -0.000021 to +0.000023 | -0.003 (0.450) | +0.000 (0.851) | +0.000 (0.857) | opposite |
| 3. Random forest | random forest | 0.000213 → 0.000244 | +0.000031 | 0.05190 | 500 | -0.000065 to +0.000623 | +0.018 (0.39521) | -0.016 (0.11976) | +0.000 (0.05190) | opposite |

Δ columns: change from the baseline, with its p from the same null (variogram-matching, §10).

## 3. Sample (§8, §9)

| Risk sets | Windows | Rows | Cells | Prevalence | Cells without a static input | Events from | Of these, not used |
|---|---|---|---|---|---|---|---|
| 64 | 60 | 309,972 | 4,887 | 0.000206 | 0 | 2017-07-16 | 14 cell not in the population; 3 earlier event in the cell; 1 same cell and date as another event (one risk set) |

## 4. Notes (facts for reading the result; no decision attached)

- **p:** p = (1 + k)/(1 + draws), where k is the number of null draws at least as large as the observed change (`11_models.py`); here k = 25 of 500, so p = 26/501 = 0.05190. The rule of §11 (change > 0 and p < 0.05) applies only to the primary analysis.
- **Ranking below chance:** the random forest's out-of-fold ROC AUC is 0.4510 without and 0.4694 with velocity, both below 0.5; the logistic regression of the primary analysis gives 0.5330 and 0.5298.
- **Multiplicity:** counting this one, 12 of the secondary analyses listed in §4 of `NYC_RESULT.md` now have a result (plus secondary 8's other nulls and secondary 9's fold seeds). None carries a decision, and no correction for multiple comparisons is applied.
