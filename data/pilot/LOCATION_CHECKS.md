# Location checks for the velocity gain

**Question:** does Shirzaei velocity still add ranking skill once location is controlled? Same 63 reviewed events, same Shirzaei-covered cells and same spatial folds as the pilot (`PILOT_REPORT.md`); no new features, no tuning.
**Reproduce:** `.venv/bin/python scripts/08_location_checks.py` (after 06 and 07).

- **Feature sets on identical cells:** A = baseline; B = baseline + x/y; C = baseline + velocity; D = baseline + x/y + velocity. x/y are the cell centre's UTM 36N coordinates (km): a location control, not a claimed cause.
- **Comparisons:** velocity without coordinates (A → C) and with coordinates (B → D).
- **Historic core:** fixed before this run as the 7 central districts named in the audit (Karmouz, Moharam Bek, El Gomrok, El Labban, Attarin, Manshiya, Mina El-Basal). A cell is in the core if its centre lies inside them; core models are trained and tested on core cells only.
- **Splits:** the values are for the primary split (seed 42); the Δ columns summarise the 10 other block → fold assignments used in the pilot's fold check. "Splits up" = splits where velocity raised the metric.
- **Top 10%:** share of collapse cells among the highest-ranked 10% of cells. With few positives, PR AUC and top-10% capture matter more than small ROC AUC differences.

## Result

- **Full area: the velocity gain is mostly location.** With x/y in the random forest, velocity no longer raises ROC AUC (−0.004, up in 3 of 10 splits) or top-10% capture (−3 pts, 1 of 10). PR AUC still rises (+0.040, 10 of 10), a gain confined to the very top of the ranking. The linear model shows no full-area gain with or without x/y.
- **Historic core: velocity adds, with and without x/y.** In the linear model it raised PR AUC and ROC AUC in 10 of 10 splits at both 250 m and 200 m (with x/y: PR +0.052 and ROC +0.028 at 250 m; PR +0.068 and ROC +0.020 at 200 m). Top-10% capture rose at 250 m (+6 pts, 10 of 10) but was mixed at 200 m. The random forest's core gain with x/y held at 250 m but not at 200 m.
- **Direction:** inside the core, collapse cells sink faster than background cells (median −4.0 vs −3.0 mm/yr at 250 m); outside it there is no difference, which would explain why the full-area linear model saw nothing.
- **Limits:** 241 core cells and 32 collapse cells at 250 m; no significance test yet; the Shirzaei observation period is still unknown, so this is a retrospective association, not a precursor.

## Random forest (250 m)

| Experiment | Cells (collapse cells) | PR AUC: baseline → + velocity | Δ PR AUC, other splits: median (range), splits up | Collapse cells in top 10%: baseline → + velocity | Δ Collapse cells in top 10%, other splits: median (range), splits up | ROC AUC: baseline → + velocity | Δ ROC AUC, other splits: median (range), splits up |
|---|---|---|---|---|---|---|---|
| Full area, no coordinates | 1,783 (46) | 0.101 → 0.151 | +0.049 (+0.045 to +0.064), 10 of 10 | 41% → 54% | +7 pts (+4 pts to +11 pts), 10 of 10 | 0.851 → 0.865 | +0.021 (+0.014 to +0.030), 10 of 10 |
| Full area, with coordinates | 1,783 (46) | 0.228 → 0.272 | +0.040 (+0.023 to +0.057), 10 of 10 | 83% → 78% | -3 pts (-4 pts to +2 pts), 1 of 10 | 0.906 → 0.907 | -0.004 (-0.008 to +0.017), 3 of 10 |
| Historic core only | 241 (32) | 0.257 → 0.290 | +0.048 (+0.027 to +0.060), 10 of 10 | 25% → 28% | +5 pts (-3 pts to +12 pts), 7 of 10 | 0.722 → 0.761 | +0.032 (+0.016 to +0.044), 10 of 10 |
| Historic core, with coordinates | 241 (32) | 0.249 → 0.285 | +0.030 (+0.019 to +0.044), 10 of 10 | 19% → 28% | +6 pts (+0 pts to +9 pts), 9 of 10 | 0.753 → 0.768 | +0.008 (+0.003 to +0.015), 10 of 10 |

Coordinates alone (A → B, primary split): full area: PR AUC 0.101 → 0.228, ROC AUC 0.851 → 0.906; historic core: PR AUC 0.257 → 0.249, ROC AUC 0.722 → 0.753.

## Logistic regression (250 m)

| Experiment | Cells (collapse cells) | PR AUC: baseline → + velocity | Δ PR AUC, other splits: median (range), splits up | Collapse cells in top 10%: baseline → + velocity | Δ Collapse cells in top 10%, other splits: median (range), splits up | ROC AUC: baseline → + velocity | Δ ROC AUC, other splits: median (range), splits up |
|---|---|---|---|---|---|---|---|
| Full area, no coordinates | 1,783 (46) | 0.083 → 0.084 | -0.001 (-0.005 to +0.004), 4 of 10 | 41% → 39% | +0 pts (-4 pts to +7 pts), 3 of 10 | 0.823 → 0.825 | +0.001 (-0.004 to +0.003), 5 of 10 |
| Full area, with coordinates | 1,783 (46) | 0.080 → 0.082 | +0.000 (-0.003 to +0.004), 5 of 10 | 37% → 41% | +4 pts (-2 pts to +9 pts), 8 of 10 | 0.823 → 0.824 | +0.001 (-0.006 to +0.003), 6 of 10 |
| Historic core only | 241 (32) | 0.289 → 0.352 | +0.071 (+0.052 to +0.088), 10 of 10 | 22% → 34% | +12 pts (+6 pts to +12 pts), 10 of 10 | 0.721 → 0.759 | +0.036 (+0.025 to +0.040), 10 of 10 |
| Historic core, with coordinates | 241 (32) | 0.328 → 0.372 | +0.052 (+0.044 to +0.060), 10 of 10 | 25% → 31% | +6 pts (+3 pts to +9 pts), 10 of 10 | 0.746 → 0.775 | +0.028 (+0.019 to +0.029), 10 of 10 |

Coordinates alone (A → B, primary split): full area: PR AUC 0.083 → 0.080, ROC AUC 0.823 → 0.823; historic core: PR AUC 0.289 → 0.328, ROC AUC 0.721 → 0.746.

## Random forest at 200 m (sensitivity)

| Experiment | Cells (collapse cells) | PR AUC: baseline → + velocity | Δ PR AUC, other splits: median (range), splits up | Collapse cells in top 10%: baseline → + velocity | Δ Collapse cells in top 10%, other splits: median (range), splits up | ROC AUC: baseline → + velocity | Δ ROC AUC, other splits: median (range), splits up |
|---|---|---|---|---|---|---|---|
| Full area, no coordinates | 2,465 (49) | 0.088 → 0.130 | +0.051 (+0.025 to +0.060), 10 of 10 | 45% → 55% | +7 pts (+0 pts to +10 pts), 9 of 10 | 0.822 → 0.843 | +0.022 (+0.005 to +0.035), 10 of 10 |
| Full area, with coordinates | 2,465 (49) | 0.207 → 0.220 | +0.012 (+0.002 to +0.016), 10 of 10 | 71% → 73% | -2 pts (-4 pts to +2 pts), 1 of 10 | 0.904 → 0.911 | +0.003 (-0.008 to +0.012), 7 of 10 |
| Historic core only | 347 (36) | 0.224 → 0.268 | +0.026 (+0.006 to +0.045), 10 of 10 | 19% → 28% | +0 pts (-3 pts to +6 pts), 4 of 10 | 0.728 → 0.740 | +0.005 (-0.008 to +0.019), 7 of 10 |
| Historic core, with coordinates | 347 (36) | 0.225 → 0.239 | +0.010 (-0.008 to +0.028), 9 of 10 | 19% → 17% | +0 pts (-6 pts to +8 pts), 2 of 10 | 0.736 → 0.734 | -0.008 (-0.020 to +0.005), 3 of 10 |

## Logistic regression at 200 m (sensitivity)

| Experiment | Cells (collapse cells) | PR AUC: baseline → + velocity | Δ PR AUC, other splits: median (range), splits up | Collapse cells in top 10%: baseline → + velocity | Δ Collapse cells in top 10%, other splits: median (range), splits up | ROC AUC: baseline → + velocity | Δ ROC AUC, other splits: median (range), splits up |
|---|---|---|---|---|---|---|---|
| Full area, no coordinates | 2,465 (49) | 0.070 → 0.065 | -0.005 (-0.008 to +0.000), 1 of 10 | 39% → 35% | +0 pts (-6 pts to +4 pts), 4 of 10 | 0.840 → 0.835 | -0.005 (-0.010 to +0.001), 2 of 10 |
| Full area, with coordinates | 2,465 (49) | 0.066 → 0.062 | -0.005 (-0.007 to +0.000), 2 of 10 | 39% → 37% | -2 pts (-8 pts to +2 pts), 1 of 10 | 0.837 → 0.831 | -0.006 (-0.012 to +0.000), 2 of 10 |
| Historic core only | 347 (36) | 0.242 → 0.342 | +0.068 (+0.039 to +0.118), 10 of 10 | 25% → 28% | +3 pts (-3 pts to +6 pts), 7 of 10 | 0.719 → 0.766 | +0.036 (+0.008 to +0.046), 10 of 10 |
| Historic core, with coordinates | 347 (36) | 0.195 → 0.288 | +0.068 (+0.036 to +0.109), 10 of 10 | 25% → 31% | +1 pts (-3 pts to +6 pts), 5 of 10 | 0.711 → 0.746 | +0.020 (+0.004 to +0.032), 10 of 10 |

## Direction of the velocity difference (descriptive)

Shirzaei VLM in covered cells; negative = subsidence. Single-layer AUC below 0.5 = lower (more negative) values in collapse cells.

| Cell size | Region | Cells (collapse cells) | VLM median, collapse cells (mm/yr) | VLM median, background (mm/yr) | Single-layer AUC |
|---|---|---|---|---|---|
| 250 m | historic core | 241 (32) | -4.0 | -3.0 | 0.38 |
| 250 m | outside the core | 1,548 (14) | -3.1 | -3.1 | 0.50 |
| 200 m | historic core | 347 (36) | -4.0 | -3.0 | 0.34 |
| 200 m | outside the core | 2,122 (13) | -3.0 | -3.1 | 0.49 |
