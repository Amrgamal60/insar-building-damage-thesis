# Pilot: urban/coastal baseline with and without InSAR velocity

**Scope:** a retrospective association test on the 2014–2016 inventory. It asks whether velocity improves the ranking of collapse cells beyond a fixed urban/coastal baseline. It is not a forecast: neither velocity product can be shown to precede the collapses. 250 m cells are primary; 200 m is a sensitivity check.
**Reproduce:** `.venv/bin/python scripts/06_pilot_sample.py && .venv/bin/python scripts/07_pilot_models.py` (after 00–03).

## Result

- **Linear model: no gain.** Adding Shirzaei VLM to the logistic-regression baseline moves out-of-fold ROC AUC from 0.823 to 0.825 (95% interval of the change -0.010 to +0.013; 1783 cells, 46 positive). Under 10 other fold assignments the change is +0.001 (-0.004 to +0.003).
- **Random forest: a small, consistent gain.** ROC AUC 0.851 → 0.865 (95% interval of the change -0.011 to +0.037), PR AUC 0.101 → 0.151, recall in top 10% 0.413 → 0.543. Velocity raised ROC AUC in 10 of 10 other fold assignments (+0.021 (+0.014 to +0.030)) and across 20 location draws (+0.024 (-0.001 to +0.039)). At 200 m: 0.822 → 0.843 (+0.010 to +0.032).
- **Ohenhen VLM (~900 m grid): no gain.** Logistic regression 0.881 → 0.877, random forest 0.891 → 0.888.
- **InSAR coverage is itself a signal.** The Shirzaei point count alone scores 0.734 out of fold, so velocity is compared only on cells that have it.
- **What the gain is not:** evidence that deformation preceded the collapses (the Shirzaei period is unknown), or proof that velocity rather than location drives it (see §9).

## 1. Target sample

Rule: the most severe part is total or partial structural, and the recorded cause is not an external accident (gas, fire, vehicle, factory) or active demolition/construction work on or next to the building. Every other recorded cause is kept; the inventory has no blank causes ("deterioration" is the workbook's own wording, تقادم وتهالك العقار).

| Stage | Events |
|---|---|
| Events in the inventory | 173 |
| Most severe part total or partial structural | 122 |
| … and cause not an external accident or active works (the target rule) | 103 |
| … located at street level (A or B) | 66 |
| … after the review decisions (final sample) | 63 |

Review decisions for records inside the sample (`review_decisions.csv`): 13 kept, 1 relocated to the junction its article names, 3 excluded (a fuzzy-only match, a street 1 km outside its district, and one street placed from a single Overture place). Records outside this sample were not reviewed.

| Cell size | Positive cells | … built-up | … built-up and settled (analysed) | Eligible cells | Built-up cells not identified as settled |
|---|---|---|---|---|---|
| 250 m | 50 | 50 | 50 | 3300 | 1027 |
| 200 m | 53 | 53 | 53 | 4745 | 1550 |

## 2. Cells and the historical filter

- **Built-up:** the cell holds at least one Google Open Buildings v3 footprint centroid with confidence ≥ 0.70, inside the 14 study districts.
- **Settled (historical filter):** the cell also holds the centre of at least one 30 m WSF Evolution pixel (DLR) whose first settlement year is 1985–2015. Built-up cells without one are *not identified as settled by the historical filter*; that does not establish they were developed after 2015 (WSF can miss sparse or small settlement). Only eligible cells (built-up and settled) are analysed.
- **Positive:** a target event's assigned point falls in the cell. Several events can share a cell.

## 3. Deformation products

|  | Shirzaei et al. | Ohenhen et al. 2025 |
|---|---|---|
| Source | [InSAR-Based Coastal Land Subsidence](https://data.lib.vt.edu/articles/dataset/InSAR-Based_Coastal_Land_Subsidence/25864435), VT Figshare, CC0 | [The Global Threat of Sinking Deltas](https://doi.org/10.5281/zenodo.15015923), Zenodo v1, CC-BY-4.0 (data for Ohenhen et al. 2025, *Nature*) |
| File used | `LLIVS_IGS14_Alexandria.csv` | `gridVLM/nile_vlm.tif` |
| Form | points: lon, lat, radar incidence angle, VLM, VLM standard deviation | raster, EPSG:4326, 0.00833° (~900 m) cells |
| Quantity | one mean vertical land motion per point, not a time series | one mean vertical land motion per cell, not a time series |
| Units | cm/yr (README); converted to mm/yr here | not stated in the file or record; values fit cm/yr (92% of Nile pixels < −0.5, and the paper reports 80% of the Nile delta sinking faster than 5 mm/yr); converted to mm/yr here |
| Reference frame | IGS14 (README) | not stated in the file or record |
| Observation period | not documented; requested from the authors on 2026-09-29 | Sentinel-1, 2014–2023 (per the paper) |
| Use here | mean of the distinct points in a cell (duplicate coordinates averaged first); cells without a point have no value | bilinear sample onto the cell grid; cells outside the grid's valid area have no value |

## 4. Coverage for the final target (250 m)

| Cells | Count | With ≥ 1 Shirzaei point (%) | With an Ohenhen value (%) | With all baseline inputs (%) |
|---|---|---|---|---|
| Positive | 50 | 92.0 | 98.0 | 100.0 |
| Background | 3250 | 53.6 | 95.7 | 99.7 |
| All eligible | 3300 | 54.2 | 95.7 | 99.7 |

At 200 m: Positive 53 cells, 92.5% with a Shirzaei point; Background 4692 cells, 51.6% with a Shirzaei point; All eligible 4745 cells, 52.0% with a Shirzaei point.

## 5. Single-layer scores (250 m)

**Metric:** ROC AUC of the raw layer value = the probability that a random positive cell has a higher value than a random background cell (ties count half). **Sign:** above 0.5 = higher in positive cells, below 0.5 = lower; 0.5 = no separation, and 0.24 separates as strongly as 0.76. **Missing data:** a cell without a value is left out of that layer's score only (no imputation); the counts below are the cells used. Eligible cells only. Descriptive, not a model score.

| Layer | Source | Eligible cells with a value (%) | Positive cells with a value | Background cells with a value | Median, positive | Median, background | AUC | Direction |
|---|---|---|---|---|---|---|---|---|
| Built-up share of the cell, 2015 (%) | GHS-BUILT-S R2023A, 100 m, cell mean | 99.8 | 50 | 3244 | 42.64 | 27.73 | 0.79 | higher in positive cells |
| Share of 2015 built-up surface already built in 1975 (0-1) | GHS-BUILT-S 1975 / 2015 | 99.7 | 50 | 3241 | 1.00 | 0.44 | 0.88 | higher in positive cells |
| Net building height, 2018 (m) | GHS-BUILT-H ANBH R2023A, cell mean of non-zero pixels | 99.8 | 50 | 3242 | 18.01 | 10.76 | 0.79 | higher in positive cells |
| Building count, log(1 + n) | Google Open Buildings v3, confidence >= 0.70 | 100.0 | 50 | 3250 | 5.19 | 4.06 | 0.83 | higher in positive cells |
| Ground elevation (m) | FABDEM v1-2, cell mean | 100.0 | 50 | 3250 | 9.16 | 1.24 | 0.82 | higher in positive cells |
| Distance from cell centre to the 2021 shoreline (km) | DSAS shoreline, OSF 98pyu | 100.0 | 50 | 3250 | 1.38 | 2.70 | 0.27 | lower in positive cells |
| Shirzaei et al. VLM, mean of points in the cell (mm/yr) | VT Figshare 25864435, IGS14 | 54.2 | 46 | 1743 | -3.46 | -3.11 | 0.44 | lower in positive cells |
| Ohenhen et al. 2025 VLM at the cell (mm/yr) | Zenodo 15015923, bilinear from ~900 m | 95.7 | 49 | 3110 | -5.17 | -6.45 | 0.70 | higher in positive cells |
| Shirzaei et al. points in the cell (count) | availability, not a velocity | 100.0 | 50 | 3250 | 5.00 | 1.00 | 0.75 | higher in positive cells |

## 6. Availability-only diagnostic

Whether a cell merely *has* InSAR data, used as the only predictor under the same spatial folds (logistic regression). A high score means coverage itself tracks collapse cells, which is why the velocity comparison below uses only cells that have velocity data.

| Predictor(s), all eligible cells with baseline inputs | Cells | Positive cells | Out-of-fold ROC AUC | PR AUC | Prevalence |
|---|---|---|---|---|---|
| Has ≥ 1 Shirzaei point | 3291 | 50 | 0.658 | 0.023 | 0.015 |
| Shirzaei point count, log(1 + n) | 3291 | 50 | 0.734 | 0.032 | 0.015 |
| Has an Ohenhen value | 3291 | 50 | 0.443 | 0.013 | 0.015 |
| Urban/coastal baseline (for reference) | 3291 | 50 | 0.881 | 0.074 | 0.015 |

## 7. Baseline vs baseline + velocity

Baseline (fixed before any run): Built-up share of the cell, 2015 (%), Share of 2015 built-up surface already built in 1975 (0-1), Net building height, 2018 (m), Building count, log(1 + n), Ground elevation (m), Distance from cell centre to the 2021 shoreline (km). Each comparison uses the identical cells where every baseline input and that velocity exist (for Shirzaei, cells with ≥ 1 point). Out-of-fold scores from 5 fixed spatial folds (2 km blocks). Recall in the top 10% = share of positive cells among the highest-ranked 10% of cells. Intervals: 2,000 block-bootstrap resamples of the out-of-fold scores, models not refitted.

**250 m (primary)**

| Velocity product | Model | cells | positive cells | ROC AUC, baseline | ROC AUC, + velocity | PR AUC, baseline | PR AUC, + velocity | prevalence | recall in top 10%, baseline | recall in top 10%, + velocity | fold ΔAUC | ΔROC AUC 95% interval | ΔPR AUC 95% interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Shirzaei et al. VLM | logistic regression | 1783 | 46 | 0.823 | 0.825 | 0.083 | 0.084 | 0.026 | 0.413 | 0.391 | +0.009, +0.014, -0.007, -0.016, +0.008 | -0.010 to +0.013 | -0.019 to +0.014 |
| Shirzaei et al. VLM | random forest | 1783 | 46 | 0.851 | 0.865 | 0.101 | 0.151 | 0.026 | 0.413 | 0.543 | -0.013, +0.047, +0.043, +0.003, +0.034 | -0.011 to +0.037 | +0.003 to +0.104 |
| Ohenhen et al. 2025 VLM | logistic regression | 3156 | 49 | 0.881 | 0.877 | 0.072 | 0.067 | 0.016 | 0.510 | 0.469 | -0.002, +0.001, -0.018, +0.003, -0.007 | -0.008 to +0.001 | -0.017 to -0.000 |
| Ohenhen et al. 2025 VLM | random forest | 3156 | 49 | 0.891 | 0.888 | 0.094 | 0.079 | 0.016 | 0.633 | 0.592 | +0.009, +0.047, -0.015, -0.055, -0.006 | -0.036 to +0.027 | -0.063 to -0.000 |

**200 m (sensitivity)**

| Velocity product | Model | cells | positive cells | ROC AUC, baseline | ROC AUC, + velocity | PR AUC, baseline | PR AUC, + velocity | prevalence | recall in top 10%, baseline | recall in top 10%, + velocity | fold ΔAUC | ΔROC AUC 95% interval | ΔPR AUC 95% interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Shirzaei et al. VLM | logistic regression | 2465 | 49 | 0.840 | 0.835 | 0.070 | 0.065 | 0.020 | 0.388 | 0.347 | -0.018, -0.001, -0.003, -0.016, +0.003 | -0.015 to +0.006 | -0.019 to +0.002 |
| Shirzaei et al. VLM | random forest | 2465 | 49 | 0.822 | 0.843 | 0.088 | 0.130 | 0.020 | 0.449 | 0.551 | +0.031, +0.015, +0.008, +0.009, +0.054 | +0.010 to +0.032 | +0.010 to +0.097 |
| Ohenhen et al. 2025 VLM | logistic regression | 4570 | 52 | 0.906 | 0.901 | 0.067 | 0.062 | 0.011 | 0.692 | 0.654 | -0.018, -0.006, -0.000, -0.001, -0.007 | -0.009 to -0.001 | -0.012 to -0.000 |
| Ohenhen et al. 2025 VLM | random forest | 4570 | 52 | 0.877 | 0.883 | 0.089 | 0.071 | 0.011 | 0.558 | 0.635 | -0.024, +0.053, -0.009, -0.005, +0.011 | -0.015 to +0.034 | -0.082 to +0.009 |

**Fold-assignment check (250 m, Shirzaei).** The same comparison under 10 other block → fold assignments (seeds 0–9), to see whether a gain depends on one split:

| Model | Fold assignments | ΔROC AUC: median (range) | ΔPR AUC: median (range) | Assignments where velocity raised ROC AUC |
|---|---|---|---|---|
| logistic regression | 10 | +0.001 (-0.004 to +0.003) | -0.001 (-0.005 to +0.004) | 5 of 10 |
| random forest | 10 | +0.021 (+0.014 to +0.030) | +0.049 (+0.045 to +0.064) | 10 of 10 |

## 8. Location-assignment sensitivity (250 m)

Each event's point was redrawn uniformly along its matched street geometry (20 draws; intersections and the one junction stay fixed), the positive cells recomputed, and the same comparison rerun with the same folds.

| Velocity product | Model | Draws | Positive cells | ROC AUC, baseline: median (range) | ROC AUC, + velocity: median (range) | ΔROC AUC: median (range) |
|---|---|---|---|---|---|---|
| Ohenhen et al. 2025 VLM | logistic regression | 20 | 49–55 | 0.889 (0.861–0.902) | 0.887 (0.856–0.898) | -0.003 (-0.005 to -0.002) |
| Shirzaei et al. VLM | logistic regression | 20 | 45–50 | 0.831 (0.783–0.854) | 0.834 (0.784–0.856) | +0.001 (-0.006 to +0.010) |
| Shirzaei et al. VLM | random forest | 20 | 45–50 | 0.818 (0.752–0.868) | 0.843 (0.791–0.884) | +0.024 (-0.001 to +0.039) |

## 9. Limits and next checks

- **Small sample:** 46–50 positive cells. The intervals resample out-of-fold scores without refitting the models, so they understate the uncertainty.
- **Velocity may stand in for location.** Velocity varies smoothly across the city, so a random forest can use it as a finer map of where the old core is, not as deformation. Not tested here. The next check is to add cell coordinates (or a smooth location term) to the baseline and to compare within the historic core only.
- **Not a precursor test:** the Shirzaei period is unknown, and Ohenhen covers 2014–2023, overlapping and following the events.
- **The baseline marks the dense historic core;** velocity is judged only on what it adds to it.
- **News-derived labels:** background cells may hold unrecorded collapses.
