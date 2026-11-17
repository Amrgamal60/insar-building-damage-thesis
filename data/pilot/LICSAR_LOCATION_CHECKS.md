# Location checks with LiCSAR velocity (secondary check 6)

**Plan:** `LICSAR_TEST_PLAN.md`; the design is `LOCATION_CHECKS.md`'s with LiCSAR vertical velocity P1 in place of Shirzaei velocity, on the eligible cells that have a LiCSAR value. No decision is attached.
**Reproduce:** `.venv/bin/python scripts/18_licsar_location_checks.py` (after 16).

- **Feature sets on identical cells:** A = baseline; B = baseline + x/y; C = baseline + velocity; D = baseline + x/y + velocity.
- **Splits:** values for the primary split (seed 42); the Δ columns summarise the 10 other block → fold assignments. "Splits up" = splits where velocity raised the metric.

## Result

- **Full area: velocity adds nothing once location is controlled, as with Shirzaei.** Logistic regression: PR AUC −0.003 without x/y and +0.002 with (the same at 200 m). The random forest gains PR AUC without x/y (+0.010 at 250 m, +0.077 at 200 m), but with x/y the gain is +0.014 and +0.018 and ROC AUC does not rise (5 and 2 of 10 splits), so the city-wide gain is location.
- **Historic core: velocity adds in the linear model at both sizes.** At 250 m, PR AUC +0.067 without x/y and +0.093 with, ROC AUC +0.043 and +0.045, in 10 of 10 splits each (Shirzaei: PR +0.071 and +0.052). At 200 m, on 510 cells, the gains are smaller: PR +0.027 (9 of 10) and +0.030 (10 of 10), ROC +0.026 and +0.025 (10 of 10); Shirzaei gave +0.068 on its 347 cells. The random forest adds in the core at 250 m (PR +0.063 and +0.048, 10 of 10) but not at 200 m, as with Shirzaei.
- **Outside the core the direction is reversed, which reflects a difference between the products.** In the core the collapse cells' median is below the background's (250 m: 0.06 vs 0.35 mm/yr). Outside it is above (2.21 vs −0.63; single-layer ROC AUC 0.80). On the 1,522 cells outside the core that have both products, LiCSAR gives 2.26 vs 0.43 and Shirzaei −3.12 vs −3.10, so Shirzaei shows no difference. Five of the 16 outside collapse cells are in Bab Sharqi, which LiCSAR shows moving up relative to the frame references (district median +2.4 mm/yr) and Shirzaei moving down (−2.3). District medians of the two products differ by about 0 (Kesm than Al Raml) to 5.7 mm/yr (Al Raml). This is a long-wavelength difference: the LiCSAR run has no GNSS tie, atmospheric correction or deramping. Outside the core, LiCSAR velocity therefore mostly marks location, and x/y removes it.
- **Reading:** as with Shirzaei, the velocity result is confined to the historic core; city-wide, velocity adds nothing beyond location. The long-wavelength differences do not explain the core result, which compares cells inside the core with x/y controlled and also passes the within-block (2 km) null (`LICSAR_TEST.md`).

## Logistic regression (250 m)

| Experiment | Cells (collapse cells) | PR AUC: baseline → + velocity | Δ PR AUC, other splits: median (range), splits up | Collapse cells in top 10%: baseline → + velocity | Δ Collapse cells in top 10%, other splits: median (range), splits up | ROC AUC: baseline → + velocity | Δ ROC AUC, other splits: median (range), splits up |
|---|---|---|---|---|---|---|---|
| Full area, no coordinates | 2,872 (50) | 0.073 → 0.068 | -0.003 (-0.008 to -0.003), 0 of 10 | 46% → 46% | -4 pts (-10 pts to +0 pts), 0 of 10 | 0.863 → 0.861 | -0.005 (-0.010 to -0.002), 0 of 10 |
| Full area, with coordinates | 2,872 (50) | 0.073 → 0.078 | +0.002 (-0.000 to +0.004), 9 of 10 | 50% → 50% | +0 pts (-2 pts to +4 pts), 4 of 10 | 0.867 → 0.871 | +0.003 (-0.002 to +0.006), 9 of 10 |
| Historic core only | 341 (34) | 0.246 → 0.330 | +0.067 (+0.053 to +0.077), 10 of 10 | 29% → 35% | +3 pts (+0 pts to +9 pts), 8 of 10 | 0.765 → 0.816 | +0.043 (+0.030 to +0.050), 10 of 10 |
| Historic core, with coordinates | 341 (34) | 0.326 → 0.409 | +0.093 (+0.076 to +0.120), 10 of 10 | 29% → 38% | +6 pts (+3 pts to +12 pts), 10 of 10 | 0.807 → 0.854 | +0.045 (+0.031 to +0.052), 10 of 10 |

Coordinates alone (A → B, primary split): full area: PR AUC 0.073 → 0.073, ROC AUC 0.863 → 0.867; historic core: PR AUC 0.246 → 0.326, ROC AUC 0.765 → 0.807.

## Random forest (250 m)

| Experiment | Cells (collapse cells) | PR AUC: baseline → + velocity | Δ PR AUC, other splits: median (range), splits up | Collapse cells in top 10%: baseline → + velocity | Δ Collapse cells in top 10%, other splits: median (range), splits up | ROC AUC: baseline → + velocity | Δ ROC AUC, other splits: median (range), splits up |
|---|---|---|---|---|---|---|---|
| Full area, no coordinates | 2,872 (50) | 0.091 → 0.102 | +0.010 (+0.004 to +0.015), 10 of 10 | 50% → 50% | +0 pts (-2 pts to +10 pts), 4 of 10 | 0.856 → 0.869 | -0.002 (-0.016 to +0.008), 4 of 10 |
| Full area, with coordinates | 2,872 (50) | 0.180 → 0.205 | +0.014 (+0.005 to +0.025), 10 of 10 | 80% → 82% | +2 pts (-2 pts to +8 pts), 6 of 10 | 0.906 → 0.896 | -0.000 (-0.010 to +0.006), 5 of 10 |
| Historic core only | 341 (34) | 0.212 → 0.293 | +0.063 (+0.038 to +0.094), 10 of 10 | 24% → 29% | +4 pts (-6 pts to +9 pts), 9 of 10 | 0.745 → 0.762 | +0.011 (+0.004 to +0.023), 10 of 10 |
| Historic core, with coordinates | 341 (34) | 0.232 → 0.291 | +0.048 (+0.038 to +0.063), 10 of 10 | 21% → 35% | +15 pts (+9 pts to +18 pts), 10 of 10 | 0.791 → 0.803 | +0.013 (+0.010 to +0.027), 10 of 10 |

Coordinates alone (A → B, primary split): full area: PR AUC 0.091 → 0.180, ROC AUC 0.856 → 0.906; historic core: PR AUC 0.212 → 0.232, ROC AUC 0.745 → 0.791.

## Logistic regression (200 m)

| Experiment | Cells (collapse cells) | PR AUC: baseline → + velocity | Δ PR AUC, other splits: median (range), splits up | Collapse cells in top 10%: baseline → + velocity | Δ Collapse cells in top 10%, other splits: median (range), splits up | ROC AUC: baseline → + velocity | Δ ROC AUC, other splits: median (range), splits up |
|---|---|---|---|---|---|---|---|
| Full area, no coordinates | 4,141 (53) | 0.066 → 0.063 | -0.003 (-0.005 to +0.001), 1 of 10 | 57% → 60% | -1 pts (-4 pts to +6 pts), 4 of 10 | 0.891 → 0.888 | -0.002 (-0.006 to +0.002), 2 of 10 |
| Full area, with coordinates | 4,141 (53) | 0.064 → 0.066 | +0.002 (-0.000 to +0.003), 9 of 10 | 55% → 62% | +2 pts (+0 pts to +6 pts), 8 of 10 | 0.891 → 0.893 | +0.002 (-0.001 to +0.004), 8 of 10 |
| Historic core only | 510 (38) | 0.233 → 0.284 | +0.027 (-0.004 to +0.047), 9 of 10 | 32% → 26% | +0 pts (-5 pts to +5 pts), 4 of 10 | 0.774 → 0.804 | +0.026 (+0.013 to +0.029), 10 of 10 |
| Historic core, with coordinates | 510 (38) | 0.369 → 0.416 | +0.030 (+0.017 to +0.058), 10 of 10 | 39% → 39% | +1 pts (-3 pts to +3 pts), 5 of 10 | 0.820 → 0.852 | +0.025 (+0.014 to +0.032), 10 of 10 |

Coordinates alone (A → B, primary split): full area: PR AUC 0.066 → 0.064, ROC AUC 0.891 → 0.891; historic core: PR AUC 0.233 → 0.369, ROC AUC 0.774 → 0.820.

## Random forest (200 m)

| Experiment | Cells (collapse cells) | PR AUC: baseline → + velocity | Δ PR AUC, other splits: median (range), splits up | Collapse cells in top 10%: baseline → + velocity | Δ Collapse cells in top 10%, other splits: median (range), splits up | ROC AUC: baseline → + velocity | Δ ROC AUC, other splits: median (range), splits up |
|---|---|---|---|---|---|---|---|
| Full area, no coordinates | 4,141 (53) | 0.087 → 0.168 | +0.077 (+0.065 to +0.093), 10 of 10 | 51% → 51% | +4 pts (-2 pts to +11 pts), 8 of 10 | 0.868 → 0.871 | +0.006 (-0.003 to +0.025), 9 of 10 |
| Full area, with coordinates | 4,141 (53) | 0.195 → 0.219 | +0.018 (+0.008 to +0.028), 10 of 10 | 72% → 75% | +1 pts (-6 pts to +4 pts), 5 of 10 | 0.918 → 0.903 | -0.005 (-0.025 to +0.011), 2 of 10 |
| Historic core only | 510 (38) | 0.233 → 0.239 | +0.000 (-0.023 to +0.029), 5 of 10 | 42% → 37% | -3 pts (-5 pts to +0 pts), 0 of 10 | 0.783 → 0.775 | -0.001 (-0.007 to +0.003), 4 of 10 |
| Historic core, with coordinates | 510 (38) | 0.286 → 0.291 | +0.013 (-0.003 to +0.025), 9 of 10 | 47% → 45% | +3 pts (-8 pts to +8 pts), 7 of 10 | 0.816 → 0.807 | -0.008 (-0.013 to -0.002), 0 of 10 |

Coordinates alone (A → B, primary split): full area: PR AUC 0.087 → 0.195, ROC AUC 0.868 → 0.918; historic core: PR AUC 0.233 → 0.286, ROC AUC 0.783 → 0.816.

## Direction of the velocity difference (descriptive)

LiCSAR vertical velocity P1; negative = subsidence relative to each frame's reference. Single-layer ROC AUC below 0.5 = lower values in collapse cells.

| Cell size | Region | Cells (collapse cells) | Median, collapse cells (mm/yr) | Median, background (mm/yr) | Single-layer ROC AUC |
|---|---|---|---|---|---|
| 250 m | historic core | 341 (34) | 0.06 | 0.35 | 0.50 |
| 250 m | outside the core | 2,531 (16) | 2.21 | -0.63 | 0.80 |
| 200 m | historic core | 510 (38) | 0.23 | 0.42 | 0.46 |
| 200 m | outside the core | 3,631 (15) | 2.21 | -0.45 | 0.80 |
