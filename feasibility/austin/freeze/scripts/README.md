# Austin analysis scripts before freezing

These scripts implement the methods required by **AUSTIN_PLAN.md §§7–10 and §12 item 20**. All verification here uses synthetic arrays only. No permit file, private row, InSAR/OPERA/Sentinel measurement, outcome table, or credential store was read. The NYC sources, Austin step-0 directory, plan, and memory files were not changed.

The hyperparameters below were fixed before any synthetic fit and were not tuned after seeing verification results. Items left open by the draft plan are **authors' choice, proposed by the script author**. The coordinator explicitly resolved event-month anchoring and registered the acquisition-date temporal null on 2026-11-01; those instructions are recorded below.

## Files

| File | Purpose and plan section |
|---|---|
| `nyc_lib.py` | Byte-identical vendored NYC library; original `VariogramNull`, `Lags`, pooled metrics, spatial block bootstrap helpers (§§9–10). Its NYC application-specific feature constants are inherited source, not Austin feature definitions. |
| `lowmem_null.py` | Byte-identical copy of the step-0 subclass (§10); bool valid-pair mask, eight-window chunks, otherwise NYC arithmetic. |
| `test_b.py` | PPML, 2 km CRV1 errors, exact used-row accounting, labelled quarterly-field null refits (§§8B–10). |
| `deep_model.py` | Fixed paired CPU networks, event-month series resampling, supplied Test A outer folds, acquisition-date temporal null (§12.20). |
| `requirements_austin.txt` | Exact direct dependency versions, including CPU torch and existing CuPy distribution. |
| `checks/check_null.py` | Frozen-source hash/equality test and GPU free-memory check; writes `null_results.json`. |
| `checks/check_test_b.py` | Independent statsmodels comparison, overdispersed 3,000 × 28 recovery/timing, null smoke check; writes `test_b_results.json`. |
| `checks/check_deep.py` | Planted/no-signal, exact repeatability, resampling edge checks, and 300,000-row five-fold timing; writes `deep_behavior_results.json` or `deep_realistic_results.json`. |
| `checks/check_interfaces.py` | Synthetic validation failures, estimation-sample accounting, Test B CLI smoke check; writes `interface_results.json`. |
| `checks/check_temporal_null.py` | Four-draw planted/no-signal temporal-null checks, exact real mask, comparison reuse, per-date variograms; writes `temporal_null_results.json`. |
| `checks/check_temporal_calibration.py` | Ten independent no-signal datasets and one planted dataset, 19 draws each, unchanged registered null; per-replicate records in `checks/calibration/` and aggregate `temporal_calibration_results.json`. |
| `checks/check_temporal_budget.py` | Synthetic 300,000-row/254-date resampling timing and explicit 111,039-pixel full-cost projection; writes `temporal_budget_results.json`. |
| `checks/environment.json` | Python, hardware, package versions, and confirmation that torch has no CUDA runtime. |
| `checks/*_run.log`, `checks/null_step0_equal.log`, `checks/install_torch.log` | Raw synthetic verification output, original step-0 equality rerun, and CPU torch installation record. |
| `conditional_null.py` | Conditional pixel-field null, the primary Test A null chosen on 2026-11-06 (§10); see the calibration section below. |
| `calibration/` | Nuisance-only Monte Carlo calibration of the Test A nulls and Test B size check: design, simulation, drivers, per-dataset records, report `CALIBRATION.md`, coordinator rule check and execution notes. |
| `SHA256SUMS` | Hashes of every file in this directory tree (sources, checks, requirements, README, recorded outputs, calibration records and logs); excludes itself and Python caches. |

## Dependencies and reproducibility commands

Run from `/mnt/data/Master-projects/Alex`. Python 3.12.7; pyfixest 0.60.0, statsmodels 0.15.0, CPU torch 2.9.1+cpu. The largest package download was the 184.4 MB torch wheel. The existing venv had no pip; `python -I -m ensurepip --upgrade` installed the bundled pip. No single download exceeded 1 GB. Dependencies came from PyPI or pytorch.org.

For a fresh matching environment, install CPU torch from its CPU index first, then the pinned requirements using PyPI (the torch requirement is already satisfied):

```sh
.venv/bin/python -I -m pip install --index-url https://download.pytorch.org/whl/cpu 'torch==2.9.1+cpu'
.venv/bin/python -I -m pip install --index-url https://pypi.org/simple -r feasibility/austin/scripts/requirements_austin.txt
.venv/bin/python -I -m pip check
```

Rerun verification, in this order. Each command creates only synthetic check outputs under this directory. Numbers in JSON and logs are regenerated, so runtime fields and GPU floating-point differences need not be byte-identical. CPU score hashes and numerical assertions should match on the recorded environment. Cross-version/CPU-architecture bit equality is **UNVERIFIED**.

```sh
.venv/bin/python -I feasibility/austin/scripts/checks/check_null.py
.venv/bin/python -I feasibility/austin/scripts/checks/check_test_b.py
.venv/bin/python -I feasibility/austin/scripts/checks/check_deep.py
.venv/bin/python -I feasibility/austin/scripts/checks/check_deep.py --realistic
.venv/bin/python -I feasibility/austin/scripts/checks/check_interfaces.py
.venv/bin/python -I feasibility/austin/scripts/checks/check_temporal_null.py
.venv/bin/python -I feasibility/austin/scripts/checks/check_temporal_budget.py
.venv/bin/python -I feasibility/austin/scripts/checks/check_temporal_calibration.py
```

The original step-0 equality command was also rerun, without editing it:

```sh
.venv/bin/python -I feasibility/austin/step0/timing/check_equal.py /mnt/data/Master-projects/Alex/feasibility/austin/scripts
```

The null check queries `nvidia-smi` first and records **UNVERIFIED** instead of running if less than 2,048 MiB is free; the larger temporal smoke check requires 6,000 MiB. No GPU process is stopped or changed. The production generator still requires enough free VRAM for its full field; the smoke check does not prove that full-date memory fits.

## Null module (§10)

Both copies are exact, including arithmetic and source bytes:

- `nyc_lib.py`: `619e4de49415bc2f33cc7e54cd91f26740a37de8c0fcd0d990503a93f4546db1`, matching `feasibility/nyc/scripts/nyc_lib.py`.
- `lowmem_null.py`: `84a6e78ef074d6ae29f1dbbe1b76d0f8bd46d35a8d3850da73a8c5ccaadf87e9`, matching `feasibility/austin/step0/timing/lowmem_null.py`.

Normal settings stay kmax=1,000, max_lag=16, chunk=8; Test A uses 999 draws/seed 2027, Test B 999/2034, the remodel Test B 999/2035. The equality smoke check deliberately uses the original step-0 smaller setting, kmax=200/chunk=3, to compare within modest memory. It requires identical pair counts, missingness, and selected k, with max absolute surrogate difference ≤1e-11; CUDA sparse arithmetic is not bit-reproducible. The inherited null uses one permutation, neighbour count and white-noise vector across all windows per draw.

## Test B (§§8B–10)

`fit_panel(panel)` takes a pandas table with `cell, quarter, y, n, v, block`. Inputs must already obey §8B. It rejects missing/nonfinite values, n≤0, negative/noninteger counts, duplicate cell-quarter rows, and cells crossing blocks. It fits `y ~ v | cell + quarter` by `pyfixest.fepois`, offset `log(n)`, CRV1 by 2 km block. No baseline features enter this model.

Fixed authors' choices: IWLS tolerance 1e-10, at most 100 iterations; FE demeaning tolerance 1e-10; pyfixest singleton removal and FE separation checks (`['fe']`). Continuous-regressor separation beyond the FE check is **UNVERIFIED**; nonconvergence or an unidentified coefficient fails explicitly. Rows are never silently dropped for missing input. Counts of dropped rows, cells and quarters, input all-zero cells/quarters, exact used input row positions, retained blocks and fitting success are exposed. The pinned package's post-selection `_data` identifies the actual sample and its length must equal its fitted N.

The output reports β, CRV1 SE, IQR of raw v **over exactly the estimation rows**, exp(β·IQR), its 95% normal Wald interval exp((β±1.959963984540054·SE)·IQR), and |β|. Both packages use the same CRV1 finite-sample factor: **G/(G−1) · (N−1)/(N−K)**. `pyfixest.ssc(k_adj=True,k_fixef='full',G_adj=True,G_df='conventional')` counts all fixed effects; statsmodels `cov_cluster(..., use_correction=True)` counts the explicit dummy design columns. For the connected synthetic panels K = retained cells + retained quarters (including the velocity coefficient). Disconnected FE graphs have not been independently checked.

`null_test(panel, surrogate_fields, quarters, cells)` takes an iterable of `(quarter,cell)` fields, optionally the `(field,k)` tuples yielded by `VariogramNull.draws`. Axis labels are explicit; no sort order is guessed. Default 999 successful refits, retaining the observed estimation sample, with p_B=(1+number of |β*|≥|β|)/(1+draws). A missing surrogate value, extra row removal, failed fit or wrong draw count fails the whole run; unsuccessful draws are not deleted. Generate Test B fields using the vendored NYC/low-memory class with quarters as windows and seed 2034; pass its iterator directly to `null_test`. The input field is the §7 raw quarterly cell velocity, not the property pixel field.

CLI:

```sh
.venv/bin/python -I feasibility/austin/scripts/test_b.py prepared_panel.csv test_b_result.json
# Optional --surrogates surrogates.npz; NPZ keys fields[draw,quarter,cell], quarters, cells.
```

Only the synthetic CSV created temporarily by the checker was passed to that CLI in this task.

## Temporal networks (§12.20): fixed choices

All are authors' choices proposed by the script author except the explicitly coordinator-registered window/null construction. No setting is selected from real data.

1. **Grid and reference.** T is the first day of the CASE's event month. Window [T−24 calendar months,T); grid T−[732,720,…,12] days, 61 slots. Pick the nearest acquisition within 6 days, tie to the earlier date, with no interpolation. A slot whose inclusive ±6-day neighbourhood crosses the window boundary is masked. Thus the leftmost slot is normally structurally masked. A missing nearest acquisition stays missing; a farther valid one does not replace it. Subtract the first valid sampled displacement in each row. Missing values=0, mask=0, valid mask=1. Every case/control in a risk set uses the case's window. This uses the same pre-month information as Test A.
2. **Inputs and scaling.** Referenced displacement is in mm. Baseline 1 is the exact upstream checkpoint design matrix (option C excludes living area and foundation type; any required foundation indicator coding is supplied upstream). Mean/SD scaling of baseline columns uses inner-training rows only; constants have SD=1. Divide referenced series by a single SD over inner-training valid values, without centring; constants/all-missing have scale=1. No row-specific scaling, winsorisation or imputation. Missing baseline rows must be removed from both models upstream and counted there; this fitter rejects them. This preserves relative series amplitude and avoids validation/test leakage.
3. **Encoder.** Two channels (value,mask); Conv1d(2→8,k=5,pad=2), ReLU; Conv1d(8→8,k=3,pad=1), ReLU; AdaptiveAvgPool1d(4); Flatten; Linear(32→8), ReLU. Local filters and four time bins retain coarse shape at low parameter count.
4. **Head and comparison.** Linear(p+8→16), ReLU, Linear(16→1); comparison removes the series branch and eight inputs, retaining p→16→1 and identical training rules. Baseline-input weights, first-layer bias and output-layer weights/bias start identically in each pair. Width and loss stay the same; no dropout. This isolates the series contribution.
5. **Loss/training.** Weighted binary cross-entropy on logits, positive weight Nnegative/Npositive from inner-training rows; both networks use it. AdamW lr=0.001, weight_decay=0.0001, betas=(0.9,0.999), eps=1e-8. Batch=1,024; cap=16 epochs; shuffled batches; no schedule, augmentation or tuning. The weighting reflects roughly 50 controls/case.
6. **Early stopping.** Minimum inner-validation weighted BCE, min_delta=0.0001, patience=3 complete epochs. Restore the best epoch and predict the outer holdout; do not refit on all outer-training rows. This keeps stopping outside the held-out blocks.
7. **Folds.** Input the exact Test A parcel/block map, generated upstream by StratifiedGroupKFold(5,shuffle=True,random_state=42) on all eligible parcels with label `parcel holds an event`; never regenerate it on repeated risk-set rows. Every block must have one supplied outer fold. Within each outer-training sample take the first split of SGKF(5,shuffle=True,random_state=4242+outer_fold), grouped by 2 km block and stratified by row y. Inner training and validation must each contain both classes. Block lists and train-only scaling are saved per fold.
8. **Randomness/device.** Model seeds 2040+outer_fold; batch seeds 3040+outer_fold, identical for both networks. Seed Python, NumPy and torch. CPU float32 only; one torch compute thread and one interop thread; torch deterministic algorithms enabled; MKLDNN deterministic enabled. The installed CPU wheel has no CUDA runtime. This makes repeated runs reproducible and leaves the GPU server available.
9. **Outputs.** `oof_scores` returns both finite OOF probability arrays in original row order plus audit metadata. CLI input NPZ keys: `baseline[row,p]`, `series[row,61]`, `mask[row,61]`, `y[row]`, `block[row]`, `fold[row]`, optionally `row_id[row]`. Output NPZ keeps those row identifiers, y/block/fold and the `comparison`/`series` scores; an adjacent audit JSON records folds/stopping/scaling/timing. Apply pooled PR AUC and the existing production refit block bootstrap to exactly these paired rows. The check's fixed-score bootstrap diagnoses synthetic noise only; it does not replace the plan's refit bootstrap.

```sh
.venv/bin/python -I feasibility/austin/scripts/deep_model.py prepared_synthetic_rows.npz synthetic_oof.npz
```

`resample_series` resamples one parcel; `series_from_fields` groups rows by event month for efficient identical resampling from date-by-pixel fields. They share the same nearest-date lookup and were checked for exact equality.

## Registered temporal null (§12.20, coordinator decision 2026-11-01)

The field is all unique Test A eligible parcel pixels, with **acquisition dates as windows** over the full study displacement series. Use `LowMemVariogramNull(kmax=1000,max_lag=16,chunk=8)`, 99 draws, seed **2037**. Each draw shares one permutation, neighbour count and noise vector across all acquisition dates. Date-wise variograms are matched by the inherited method; temporal information is carried by the common spatial mixing. Its temporal autocovariance preservation is **UNVERIFIED**, rather than assumed exact: per-date fitted scale/noise coefficients can vary.

`temporal_null_test` takes baseline, acquisition dates, the re-referenced date-by-pixel displacement fields, row→pixel mapping, case event dates, y, blocks, supplied outer folds and pixel coordinates. It constructs real and surrogate row series with the same `series_from_fields` code. The real acquisition-valid mask is imposed before referencing; optional additional **real row/step masks** (e.g. construction masking) are applied identically before the first-valid reference. Masks must agree exactly on every draw. A surrogate cannot fill a missing real acquisition.

Fit both observed networks once; per draw refit only the series network, reusing comparison OOF scores exactly, with unchanged folds, seed, optimiser and stopping rules. Statistic = pooled PR AUC(series)−pooled PR AUC(comparison). p=(1+surrogate statistics≥observed statistic)/(1+99). Failure, changed masks or a wrong draw count fails the whole run. Draws stream through memory; all 99 displacement cubes need not be stored. Each draw records generation, resampling and series-only refit time, selected k and **per-date relative variogram RMSE**, defined as sqrt(mean_lag((surrogate semivariance−target semivariance)²))/mean_lag(target semivariance). These use the class's own `lags.vario` and `target`; the class itself has no pre-existing named fit-metric output.

The temporal null is optional only under the plan's compute-budget clause; its construction is fixed here, not chosen later. Production 99-draw execution and full 254-date GPU allocation remain **UNVERIFIED** until actually run. The cost projection below is conditional on memory fitting.

## Recorded verification results (synthetic only, 2026-11-01)

### Null equality

PASS: 3,327 synthetic cells × 11 windows, four draws; pair counts and selected k identical (103, 53, 53, 74). Maximum absolute difference 3.10862446895e-14, below 1e-11. The unchanged step-0 checker separately gave a maximum 1.73e-14. GPU before the frozen-source check: NVIDIA GeForce RTX 3090, 24576, 22406 (MiB).

### Test B independent agreement and recovery

Statsmodels uses GLM Poisson with intercept, C(cell), C(quarter), velocity and log-exposure offset, IWLS tolerance 1e-12, plus `cov_cluster(use_correction=True)`. Both β and clustered SE must agree within absolute 1e-7.

| Panel | Used rows | K | G | β difference | SE difference | CRV1 factor |
|---|---:|---:|---:|---:|---:|---:|
| Poisson | 960 | 92 | 10 | 8.882e-16 | 3.723e-13 | 1.2275985663 |
| Overdispersed + zero FEs | 847 | 88 | 10 | 1.665e-16 | 1.196e-12 | 1.2384716733 |

The deliberate separation panel drops 3 cells and 1 quarter (113 rows); the reported IQR and model comparison use its 847 retained rows. The identity-surrogate smoke draw recovers the observed β exactly; the two-draw null smoke gives p_B=0.666666666667.

On 3,000 cells × 28 quarters, Gamma–Poisson counts with gamma shape 2, true β=−0.35: fitted β=-0.350313315855, CRV1 SE=0.006200851478, absolute recovery error 0.000313315854631. It retains 83,748/84,000 rows and 2,991 cells; 9 all-zero cells dropped, all 28 quarters retained. IQR=1.70404785391; rate ratio=0.55048770678, 95% CI [0.539204320339, 0.5620072093]. One fit: **0.218688 s**; 999 refits: **218.469 s (3.641 min)**, projected, excluding surrogate generation.

### Deep behavior, determinism and realistic timing

Synthetic behavior set: 30,600 rows, nine baseline features, 61 steps, roughly 1/51 cases, 2 km group-fold input. There are 857 parameters in the series network and 177 in the comparison when p=9. The same frozen choices were used in every run.

| Check | Comparison PR AUC | Series PR AUC | Change | Paired fixed-score block 95% interval |
|---|---:|---:|---:|---|
| Planted signal | 0.050120522 | 0.700180564 | 0.650060043 | [0.611808650, 0.684733753] |
| No series signal | 0.048216022 | 0.049764068 | 0.001548046 | [-0.002058647, 0.006298576] |

Planted-signal lower interval >0. With no signal, gain 0.001548046 is 0.732 bootstrap SD, below the fixed 3-SD check. These are 300 paired fixed-score bootstrap draws/seed 909 for diagnosis, not production refit intervals.

Two runs with identical seeds gave **exactly identical float32 score arrays for both networks**. SHA-256:

- Comparison: `a11749ad3b8b740e2a96e707aabdd5c7f22a3f65c2a6d80bd3311db3eb77edfe`.
- Series: `0c470d99779724376db204cdee7022b6bfba2e491bfdba118b95a1ff0d88d427`.

Realistic set: **300,000 rows × 61 steps**, nine baseline columns, full five-fold paired fit **191.593303 s (3.193 min)**. Comparison training/prediction 32.154811 s, series training/prediction 156.403831 s, shared preprocessing 3.034661 s. PR AUC comparison=0.044970630, series=0.754940495. The five series fits ran 6/14/9/10/8 epochs and restored epochs 3/11/6/7/5. The naïve 99 complete paired refits projection is 5.269 h; the registered null reuses comparison scores and the refined total is below.

### Temporal null smoke checks

25 synthetic 2 km blocks with 10,000 pixels, 62 acquisition-date fields, 20,400 risk-set rows; four draws per scenario, fixed seed 2037. Field and individual-series resampling agree exactly; every surrogate step mask equals the real step mask; every comparison score is reused. The planted signal exceeded all four surrogate changes.

| Scenario | Observed ΔPR AUC | Surrogate ΔPR AUCs | p | Median date-wise relative RMSE range |
|---|---:|---|---:|---|
| Planted | 0.295074360 | 0.003889476, 0.003089603, 0.002687194, 0.002821414 | 0.200 | 0.007997–0.019216 |
| No signal | 0.002334221 | 0.000806432, 0.000131651, 0.000762884, -0.000691499 | 0.200 | 0.008926–0.018186 |

Largest relative variogram RMSE over all dates/draws/scenarios: **0.040329** (4.03%). Per-date values are retained in JSON. Both scenarios have p=0.2; the no-signal observed gain also outranked the four null draws. **This is an implementation smoke check only:** four draws have minimum attainable p=0.2, so they cannot establish calibration at 0.05 or demonstrate that the no-signal null is well calibrated. The larger independent no-signal network check above assesses gain relative to sampling noise. Full 99-draw synthetic null calibration remains **UNVERIFIED**.

### Full temporal-null cost projection and limits

For **111,039 pixels × 254 dates**, projected generator setup 224.270 s and draw 19.916 s, or 36.599 min for 99 draws plus setup. This extrapolates the registered step-0 synthetic-value timing (77.7 s setup, 6.9 s/draw, 88 windows) linearly by 254/88, assuming the same spatial pair density and hardware; it is **not a new full-date GPU benchmark**.

A separately timed fully synthetic resampling uses 111,039 pixels, 254 dates, 300,000 rows over 88 event months: **1.193027 s/draw**. Measured series-only refit cost, conservatively including all shared preprocessing: **159.438492 s/draw**. Generation + resampling + 99 series-only refits totals **5.027 h**; scaling every series fit to the 16-epoch cap gives **8.088 h**. Early stopping and CPU/GPU load can change these estimates. Observed paired fit and diagnostic variogram reporting are outside this 99-draw total.

The boolean valid-pair mask alone is 3.896 GB at 254 dates and the original 15,338,069 pairs; one float64 date cube is 0.226 GB. Storing all 99 float32 date cubes would use 11.169 GB, so the API streams them. **Full-date GPU memory is UNVERIFIED:** the historical 88-window run recorded a 22.01 GB transient pool before dropping to an 11.04 GB pool during draws, and the extra date masks can exceed currently free VRAM during setup. Time extrapolation does not resolve this. Do not treat the projection as proof of full-scale feasibility.

### Interface and environment checks

All 13 interface assertions pass, including invalid inputs, missing draws, block leakage rejection, exact cached-comparison behavior, disjoint inner/outer blocks, both CLIs, exact CLI/API deep scores and row IDs. All Python files compile; `pip check` reports no broken requirements.

The additional coordinator-requested calibration uses independent dataset seeds 1717–1726 (no signal) and 1716 (planted), 100 case parcels and 50 controls each (5,100 rows), 10,000 synthetic pixels in 25 blocks, and 62 acquisition dates. It otherwise uses the same generator as the temporal smoke check. Each dataset uses 19 draws/seed 2037 and the unchanged model/fold/stopping settings; no replicate or seed is discarded. It records all p-values, observed/null gain summaries, and marginal/lag-one series diagnostics. Completed replicates are durable JSON checkpoints validated against the model/generator/requirements source hashes; delete only `checks/calibration/` when an intentional full rerun is wanted.

## Remaining verification limits

- Full 999-draw Test B and 99-draw temporal-null executions were projected, not run. Their full inferential calibration is UNVERIFIED.
- Full 254-date GPU allocation is UNVERIFIED and may need an outcome-blind implementation memory fix before the optional temporal null can run. No other GPU process was touched.
- CPU bit equality is checked on the recorded environment, not across packages or CPU architectures.
- Temporal autocovariance preservation and continuous-regressor separation beyond pyfixest’s FE check are UNVERIFIED.
- No real-data fit or feature extraction was performed. Upstream eligibility, fold-map construction, Baseline 1 coding and production refit bootstrap remain the later checkpoint’s work.

Official API references used for implementation: [pyfixest fepois](https://pyfixest.org/reference/estimation.api.fepois.fepois.html), [statsmodels cov_cluster](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html). Numerical conclusions above come from the local synthetic checks.

Verify the delivered source/output manifest before rerunning checks (reruns change timing/log hashes):

```sh
(cd feasibility/austin/scripts && sha256sum -c SHA256SUMS)
```

## Additional 19-draw temporal-null calibration (coordinator request)

The registered construction and all model hyperparameters are unchanged. Ten independently generated **no-signal** datasets (seeds 1717–1726) and one planted dataset (seed 1716) each use 100 case parcels plus 50 controls/case (**5,100 rows**), the same 10,000-pixel/25-block/62-date generator as the earlier smoke check, 19 surrogate draws, and surrogate seed 2037. No dataset or draw was discarded. The serial sum of replicate times was 26.822 minutes; independent batches reduced wall time to 13.764 minutes. Both are below the requested one-hour budget.

| Dataset seed | No-signal p | Observed ΔPR AUC | Mean null ΔPR AUC |
|---:|---:|---:|---:|
| 1717 | 0.90 | 0.000755370 | 0.001225989 |
| 1718 | 0.35 | -0.001819488 | -0.002365489 |
| 1719 | 0.60 | -0.000464698 | -0.000463236 |
| 1720 | 0.10 | 0.000202616 | 0.000012275 |
| 1721 | 0.50 | 0.001901622 | 0.001696988 |
| 1722 | 0.65 | 0.000283309 | 0.000377588 |
| 1723 | 0.30 | 0.008205089 | 0.003469615 |
| 1724 | 0.70 | 0.001205681 | 0.001746155 |
| 1725 | 0.75 | -0.001227601 | -0.000403350 |
| 1726 | 0.70 | 0.000389431 | 0.000454831 |

Mean p = **0.555**; **0/10** at 0.05. The exact expectation under uniform ranks on the attainable grid 0.05,0.10,…,1 is **0.525**, approximately the requested 0.5. With ten datasets, this is a limited calibration diagnostic rather than a precise type-I error estimate.

Observed gains: mean **0.000943133**, sample SD **0.002776396** across the ten datasets. The 190 pooled null gains: mean **0.000575137**, sample SD **0.002416569**; null draws within a dataset are not independent of their common fitted baseline. The ten paired differences (observed minus that dataset's mean null gain) have mean **0.000367997**, SD **0.001586501**, and descriptive t(9) 95% interval **[-0.000766918, 0.001502911]**. This calibration gives no clear evidence that observed gains are systematically inflated relative to the null draws.

Planted dataset: observed gain **0.052279492**, null gains range **0.001836119–0.005132977**, exceeding all 19 draws, **p=0.05** (the minimum attainable at 19 draws).

### Marginal/temporal diagnostics and interpretation

These summaries use the resampled, referenced raw series before training-only SD scaling; all real masks match exactly. Each real mean averages ten datasets; each null mean averages their 190 draws.

| Diagnostic | Real mean | Null mean |
|---|---:|---:|
| Raw series SD | 0.616731 | 0.532671 |
| Excess kurtosis | 1.799717 | 2.674314 |
| Pooled lag-one correlation | 0.939365 | 0.967078 |
| Mean squared step / marginal variance | 0.121159 | 0.065971 |
| Valid-step share | 0.905124 | 0.905124 |

The null is **smoother and heavier-tailed** in these synthetic data: first differences relative to variance are smaller and excess kurtosis is larger. Matching each date's spatial variogram does not mathematically fix its marginal distribution or the full temporal covariance. The inherited class fits date-specific scaling coefficients and adds one shared noise vector with date-specific amplitudes, so temporal covariance need not be preserved exactly; this is consistent with the measured mismatch, not proof of a unique cause. Training-only SD scaling removes a single scale factor, not kurtosis or temporal dependence.

The largest absolute correlation between a unique sampled pixel's series endpoint and any of the nine baseline features was **0.038050** across no-signal datasets. Coordinates are not supplied as a hidden feature in this synthetic generator; pixel latent values are independent across synthetic locations. Thus the available diagnostics do not suggest a strong baseline/series association as the source of the earlier four-draw ranking. The original four-draw result can occur by chance (minimum p=0.2), and the expanded p-values show no excess of small values in these ten replicates.

No correction to the registered construction was made. If the coordinator requires closer temporal matching despite this limited calibration, a **proposed, unimplemented authors' choice** is a temporal-specific residual generator with an explicitly estimated cross-date covariance, together with a prespecified marginal-distribution restoration and the same fixed real masks, followed by a fresh independent calibration. Merely asserting that shared permutations/noise preserve temporal structure exactly is not supported by these diagnostics. The coordinator must approve and register any such alternative before use; this proposal is not silently substituted into the frozen method.

All 11 complete replicate records, per-draw gains, series diagnostics, variogram errors, exact-mask checks, fold audit data, and timings are in `checks/calibration/`; the aggregate is `checks/temporal_calibration_results.json`; `checks/temporal_calibration_replay.log` verifies all cached source hashes, p-value formulas and aggregate arithmetic without refitting. The full-size 254-date GPU allocation and production 99-draw temporal-null execution remain **UNVERIFIED**.

## Coordinator review (Claude, 2026-11-01)

- **Rerun:** `check_null.py`, `check_test_b.py`, `check_interfaces.py` and `check_deep.py` were rerun on a copy of this directory, in the scratchpad, so the recorded outputs here were not overwritten.
  - **Null:** the largest difference was 2.2e-14, with identical k. This is within the 1e-11 tolerance (GPU sparse arithmetic is not bit-reproducible).
  - **Test B:** the agreement figures differ from those recorded only at the 1e-15 level.
  - **Interfaces and deep-model behaviour:** identical results, including the score hashes.
- **Temporal null:** the registered construction is kept unchanged, and the proposed alternative is not adopted. The ten no-signal datasets found no sign of inflation (p mean 0.555, none at 0.05), and the deep model carries no decision. *Correction (2026-11-06):* this note first called those checks a calibration. Ten datasets with 19 draws each are a smoke check: they cannot establish the false-positive rate (AUSTIN_PLAN §16, ninth draft). The smoother, heavier-tailed surrogate series are reported as a limitation.
- **GPU memory:** the plan now says what happens if the full-date surrogate step does not fit in GPU memory (AUSTIN_PLAN §12 item 20). Only an implementation change that keeps the arithmetic, checked equal on a synthetic field and logged, is allowed. Otherwise the null is reported as not run.
- **Test B errors:** the CRV1 factor counts all fixed effects, so its intervals are slightly wider than under the convention of nested fixed effects. It does not affect p_B, which uses |β|.


## Nuisance-only Monte Carlo calibration (Orca-supervised, 2026-11-01)

The new `conditional_null.py` implements an outcome-blind conditional pixel-field null: fixed in-sample HistGradientBoostingRegressor per window on pixel means of the seven baseline covariates, excluding coordinates; the unchanged memory-lean variogram generator randomizes residuals, then adds the fitted mean back. It exposes the same `draws(n_draws, rng)` interface and preserves missing-value masks. Settings and caveats are documented in `calibration/DESIGN.md`; no existing analysis script was edited.

The synthetic calibration is **complete** (2026-11-06): all 2,200 records passed audit. The registered selection rule gave branch 3, and the user chose the conditional null as the primary Test A null (AUSTIN_PLAN §10). See `calibration/CALIBRATION.md` (with the coordinator's addendum), `calibration/results.json`, `calibration/coordinator_rule_check.json`, the logs `calibration/workload_run*.log` and `calibration/COORDINATOR_EXECUTION_NOTES.md`. The fixed workload has 200 datasets in each of eight small Test A null cells, 100 in each of two 4× scale cells, 100 at each of two power effects, and 200 Test B panels: 2,200 datasets total, all with 99 draws. The coordinator registered the scale cells and paired-bias acceptability criterion in the required pre-inference go. The later runtime go retains every count beyond 12 hours and allows one bounded GPU producer when the free-memory reserve permits.

Run/resume from the project root, using the existing environment:

```sh
.venv/bin/python -I feasibility/austin/scripts/calibration/check_conditional.py
.venv/bin/python -I feasibility/austin/scripts/calibration/check_execution.py
.venv/bin/python -I feasibility/austin/scripts/calibration/run_workload.py
.venv/bin/python -I feasibility/austin/scripts/calibration/summarize.py
```

`run_workload.py` completes each cell before starting the next (small nulls, scale, Test B, power), records devices, sends hourly heartbeats and saves atomic per-dataset JSONs. Only cells listed in the coordinator's `calibration/device_policy.json` (A_10 and A_11) may use the GPU path. CPU jobs use the unchanged inherited draw/arithmetic methods, with a NumPy/SciPy allocation adapter for Test A and the original class's CPU fallback for Test B. One small actual-GPU equality check passed within 2.40e-14, with identical chosen k and masks; the shared-memory/parallel-fit execution check matched sequential null statistics exactly. GPU execution, if eligible, additionally checks the first actual draw of every method/dataset against CPU at 1e-11, uses at most min(8 GiB, free minus 1 GiB) and falls back on allocation/equality failure. Other GPU processes are never stopped.

Core source/config hashes are embedded in every record; changed inputs refuse mixed-run resume. `summarize.py` writes results only after auditing all 2,200 datasets, all 99 saved null statistics and every p formula. Rejection is strict p<0.05 (at most 3 exceedances, exact nominal 0.04 under exchangeability). The final report includes Wilson intervals, paired-bias t intervals, observed/null statistic summaries, variance explained and p deciles. Passing a fixed synthetic family cannot establish real-data conditional exchangeability or validate missingness, demolition histories, the option-C reduced baseline, or Austin-scale event counts.
