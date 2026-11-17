# Fixed synthetic calibration design, before scale

The machine-readable specification is `design.json`; `simulation.py` defines all
transformations and random-number order. Parameters were written before the
first null draw. The timing-only pilots use separate seeds 19002026–19002028,
are excluded from inference, and expose only runtimes in `benchmark.json`.
The selection rule was independently registered by the coordinator in
`AUSTIN_PLAN.md` §10 before scale. No outcome, permit, private row, remotely
sensed measurement, credential, or existing raw data are inputs.

## Synthetic city and time

Test A uses a 6,000 m square, a 200 × 200 lattice of 30 m pixel centres, and
4,000 occupied pixels sampled uniformly without replacement. Every occupied
pixel holds one house, and 1,400 additional houses choose pixels uniformly with
replacement, giving 5,400 houses / 4,000 pixels = 1.35. House order is shuffled.
This is about 3.6% of the requested Austin-scale house/pixel counts, not a
geographical reconstruction. Empty pixels carry no parcels and do not enter the
variogram. Pixel sharing is preserved in every surrogate, standardisation and
fold: the 2 km block is determined by the pixel centre.

**Coordinator amendment before any inference result (go reply to
`msg_adbdd6ba2107`):** add N2-strong and N4-strong scale cells, 100 datasets each,
12 km square, 16,000 occupied 30 m pixels, 21,600 houses, approximately 864
events and 36 blocks. Other data-generating parameters are unchanged. Income
has 16 × 16 polygons at this size. New cell IDs are 10 and 11; IDs 8 and 9
remain the power cells. These scale cells enter the null-selection rule.

There are 12 consecutive event months and 12 preceding 24-month windows.
Twelve adjacent 24-month moving sums use 35 monthly independent innovations,
so adjacent windows share 23 innovations. To obtain about 216 events, the
12-month experiment preserves Austin's approximate **six-year cumulative 4%**
first-event incidence. Its monthly hazard is accelerated by roughly six; it is
not claimed to reproduce Austin's per-month event incidence. A 72-month event
simulation with 72 monthly velocity windows is UNVERIFIED. All houses are
eligible, all feature/velocity values observed, and there are no demolitions or
earlier matched episodes. Missingness, censoring and matched-episode exclusions
are therefore UNVERIFIED dimensions of this experiment.

## Baseline features

`z` subtracts the realised city mean and divides by the population SD. A smooth
field is independent standard Gaussian lattice noise filtered by
`scipy.ndimage.gaussian_filter`, circular boundary (`mode='wrap'`), then `z`.
Gaussian filter sigma is not an empirical variogram range: its ideal stationary
correlation is approximately exp(−distance²/(4 sigma²)).

- Soil: `1 + 9*expit(1.2*smooth(sigma=600 m))`, a bounded 1–10 shrink–swell
  index with a high-clay tail; approximate e-folding range 1.2 km.
- Elevation: `180 + 35*smooth(900 m)` metres.
- Slope: `exp(0.6*smooth(450 m))`, a positive terrain proxy.
- Income: 8 × 8 square block-group-like polygons of side 750 m, independent
  N(0, 0.3²) log-income deviations; `log(65000) + polygon deviation +
  0.15*z(polygon mean soil)`. Income is wholly piecewise constant. The
  soil-linked polygon component represents a geology–income pattern.
- Building age: `clip(45 + 15*smooth(360 m), 5, 110)` years at month zero.
- Log living area: `log(1800) + 0.2*z(log income) + N(0, 0.2²)`.
- Log lot area: `log(7500) + 0.15*z(age) + N(0, 0.3²)`.
- Houses sharing a pixel additionally receive independent N(0, 3²),
  N(0, 0.06²), N(0, 0.08²) deviations to age, log living area and log lot area.
  Pixel covariates for the conditional fit are means over the pixel's houses.
- x/y are pixel-centre coordinates in kilometres. Age at the event month adds
  month/12. Baseline 1 includes all seven requested features plus x/y, without
  foundation type. This corresponds to the task's full-feature specification;
  the option-C baseline without living area is UNVERIFIED.

## Velocity

Let `s=z(soil)`, `t=z(max(s−0.7,0)²)`, and
`g=z(0.85*s + 0.6*t + 0.2*z(slope) + 0.1*z(elevation) + 0.15*z(log income))`.
Coordinates are not in `g`. The residual is
`r_w = sqrt(0.8)*S_w + sqrt(0.2)*E_w`.
`S_w = sqrt(0.7)*S_static + sqrt(0.3)*sum(S_month[w:w+24])/sqrt(24)`;
the spatial innovations and static field have Gaussian sigma 240 m (approximate
e-folding range 480 m). `E_w` uses the identical formula with independent
white pixel noise. Thus temporal correlation is intentionally strong, and
there is spatial plus white noise. All innovations are independent of the
baseline and hidden hazard field in the data-generating process. Finite-city
chance correlations are retained, not removed.

Velocity is `v_w = g + a*r_w`, where
`a=sqrt((corr(g,soil)/rho)²−1)` and rho is 0.3 (moderate) or 0.6 (strong).
These target correlations are in expectation; realised correlations are
reported. No field is rejected or regenerated to obtain a preferred correlation.
Units are arbitrary synthetic mm/year-like units; standardisation makes their
overall scale irrelevant for Test A.

## Events, scenarios, folds and statistic

The monthly first-event hazard is logistic. Its baseline logit is an intercept
plus coefficients `(0.2, 0.1, −0.1, 0.3, 0.1, 0.1, 0.3)` multiplying city-z-scored
`(age, log living area, log lot area, soil, slope, elevation, log income)`.
Age increases by month/12. x/y have true coefficients zero. A scalar intercept
is solved by Brent's method on [−30, 5] to give exactly 0.04 mean expected
12-month first-event incidence; it uses probabilities only, never realised
events. Independent monthly Bernoulli hazards are generated, keeping each
house's first month. Independent uniform within-month times determine event
order and contemporaneous risk eligibility.

- N1: baseline logit alone.
- N2: baseline plus `0.65*t` (nonlinear high-clay tail).
- N3: baseline plus `0.7*H`, where H is an independent smooth field with sigma
  600 m, sampled at the house's pixel and time invariant.
- N4: N2 plus N3.
- A1: N1 plus `beta*r_w`, beta = −0.2 or −0.4, at the strong link only.
  The effect is on the generated residual beyond g, not on total velocity.

All null scenarios run at both rho values, 200 independent datasets per cell.
Each A1 effect has 100 independent datasets. Dataset seeds are one uint32 from
`SeedSequence([20261101, test_id, cell_id, replicate])`, test IDs 1 (A), 2 (B).
Cell IDs 0–7 order N1–N4, each moderate then strong; IDs 8,9 are A1 −0.2,−0.4.
The same dataset and null RNG seed are used for the two null constructions.

Every event receives 50 controls without replacement from houses whose first
event time is strictly later (including never events), using
`SeedSequence([dataset_seed,2029])`. Cases/controls use the case's one window.
Repeated control appearances are allowed. Controls and cases share the same
eligible pixel-valid population. Risk-set eligibility is asserted in code.
No seed or failed fit is silently discarded. A bad seed is recorded as an error
and prevents a complete report.

`nyc_lib.fold_map` is used unchanged on ALL eligible houses with the first-event
label; 9 blocks of 2 km, five StratifiedGroupKFold folds, shuffle, dataset seed.
All rows of each house/pixel stay in its fold. The requested per-dataset seed
replaces the production seed 42 solely for independent synthetic replication.
`nyc_lib.oof` and `model(LR)` are unchanged: training-fold StandardScaler then
LogisticRegression(C=1, max_iter=5000), default solver, five refits. Metric is
pooled sklearn average_precision_score, exactly `metrics()['pr']`.
Statistic is velocity-model AP minus baseline AP. Baseline scores are cached
because rows, folds and covariates are identical across draws.

Each field, real or surrogate, is standardised over ALL 5,400 eligible houses,
including pixel multiplicity: subtract the window median, divide by its IQR,
winsorise at its 0.5th/99.5th percentiles. Standardisation is rerun for each draw.

## Nulls and arithmetic

Both use 99 draws, k cap 1,000, 15 logarithmically spaced candidate neighbour
counts as inherited, 16 lags at 30 m, eight-window chunks, and exactly the
inherited permutation/noise ordering. One permutation, selected k and white
noise vector are shared across windows. Per-dataset null RNG is
`SeedSequence([dataset_seed,2033])` for BOTH methods, intentionally paired.

(a) Registered: the unchanged LowMemVariogramNull arithmetic on total velocity.
The calibration-only `cpu_null.py` subclasses it, replacing constructor device
allocations with NumPy/SciPy arrays. Both `_vario` and `draws` are the original
inherited methods, not rewrites. The unit check against the actual unchanged
GPU class had maximum absolute difference 2.40e−14, same k and masks. Neither
existing script was edited.

(b) Conditional: `conditional_null.ConditionalVariogramNull` fits separate,
in-sample, outcome-blind HistGradientBoostingRegressor models of window velocity
on the seven pixel-mean baseline covariates, EXCLUDING coordinates. Fixed:
squared-error loss, learning_rate=0.1, max_iter=100, max_leaf_nodes=15,
max_depth=None, min_samples_leaf=20, l2_regularization=1, max_bins=255,
early_stopping=False, random_state=0, categorical_features=None. No tuning or
validation split. Residuals `v−g_hat` enter the identical generator and each draw
returns `g_hat + residual_surrogate`. In-sample explained variance is
`1−var(residual)/var(v)` for each window. The production default uses
LowMemVariogramNull directly; a compatible CPU factory is supplied only here.
The module preserves velocity masks and has identity, determinism, invalid
input, mask and CPU/GPU arithmetic unit checks.

p = `(1 + count(null_statistic >= observed))/(1+99)`. Rejection is strictly
p < .05, i.e. at most 3 exceedances, exact 0.04 under exchangeability.
For completeness the report also distinguishes the production decision, which
additionally requires observed gain > 0; calibration uses the requested p-only
rejection rule. Matching variograms or fitting a conditional mean does not prove
exchangeability, a correct conditional variance, or preservation of temporal
covariance.

## Test B

200 independent 50 × 60 grids of 250 m cells (3,000 cells, 15 × 12.5 km),
24 quarters. Initial cell exposure is uniform integer 25–55; exposure falls by
the count of first events each quarter. Soil is a smooth Gaussian field with
sigma 3 cells. Cell FE is `0.35*soil + N(0,0.25²)`; quarter FE is
`0.25*sin(2*pi*q/8)`. A hidden field has spatial Gaussian sigma 2.5 cells,
AR(1) 0.6 across quarters, and coefficient 0.5 in log mean. Its innovations are
independent of velocity and soil. Log mean is `log(exposure) − 6.4 + cell FE +
quarter FE + 0.5*hidden`. Gamma–Poisson shape 2, scale 1/2 gives overdispersion;
Poisson counts are capped at the remaining houses (a practically rare cap,
explicitly part of this synthetic process). No velocity effect is present.

Quarter velocity is `0.6*soil + 0.8*(sqrt(0.8)*rolling_spatial +
sqrt(0.2)*rolling_white)`, each rolling component sums four independent quarter
fields / 2. Spatial sigma is 2.5 cells. Thus soil is absorbed by cell FE,
time-varying velocity is spatially correlated, and the hidden field is an
independent omitted spatial nuisance. 2 km block IDs follow the cell centres.

The unchanged `test_b.fit_panel` and `null_test` use PPML with cell/quarter FE,
offset log(exposure), full-FE-count CRV1 by 2 km block, frozen tolerances and
sample-accounting rules. `nyc_lib.VariogramNull` is used unchanged with its
documented CPU fallback (`CUDA_VISIBLE_DEVICES=''`), 99 draws, cap 1,000 and
16 lags at 250 m, quarters as windows. Null RNG is
`SeedSequence([dataset_seed,2034])`. The statistic is absolute beta, and its
two-sided p follows the identical plus-one formula. Separated all-zero cells
are removed by the existing fit; null refits must retain its exact used sample.

## Reporting, selection and execution

Every cell reports the rate, Wilson 95% interval, observed-statistic mean/sample
SD, pooled null-statistic mean/sample SD, and right-closed p-decile counts
(0,.1], (.1,.2], ..., (.9,1]. Pooled null SD is descriptive: draws sharing one
dataset are not independent Monte Carlo datasets. Inference on size uses
independent datasets only. Report observed-gain mean interval and positive share
to assess systematic N2/N4 gains, with no tuning in response.

Acceptable means Wilson lower bound ≤ .05 AND point rate ≤ .075. If (a) is
acceptable in every null cell, branch 1 retains it as primary; otherwise if (b)
is acceptable everywhere, branch 2 selects it; otherwise branch 3 selects
neither and leaves a proposed next step to the coordinator/user. Power never
enters selection. Test B has the same reported acceptability check, no switch.

**Coordinator amendment to acceptability before any inference result:** every
null cell, including the two scale cells, additionally requires that the lower
bound of the 95% Student-t interval for paired bias is ≤ 0. Paired bias in a
dataset is its observed statistic minus its own mean of 99 null statistics;
the interval treats datasets as independent and uses t(n−1). This is a third
criterion, not a replacement for either size criterion. The original three
selection branches otherwise remain unchanged. The same bias diagnostic is
reported for B, with both original size acceptability and bias diagnostic
explicit; no Test B switch is attached. The amendment was requested and
registered by the coordinator in the required pre-scale go; it was not chosen
after results. All reporting uses the amended Test A rule.

CPU execution is intended to fit approximately 12 hours. No GPU process runs
at scale. The one small equality process queried nvidia-smi first, observed
1,183 MiB free, and used a 256 MiB bounded CuPy pool (15.23 MiB actually
allocated). Other GPU processes were neither stopped nor changed. All source
hashes/config are recorded per dataset; completed JSONs are atomic and reusable;
source mismatches fail closed. A required recorded coordinator go gates scale.
No package installs or git state changes are performed.

### Execution-only amendment after measured CPU throughput

The coordinator's runtime go (recorded in `coordinator_runtime_go.txt`) retains
every cell and dataset count, permits exceeding 12 hours, and allows one GPU
producer whenever memory fits. Before each GPU start, query free memory;
total own GPU use must be at most min(8 GiB, free minus 1 GiB), with automatic
CPU fallback on allocation failure. Do not stop or change another process.
This supersedes the initial CPU-only execution forecast, not any scientific
parameter in the hashed config. The exploratory GPU timing pilot preceded
this newer reserve rule and is not an inference dataset. At 1,183 MiB free,
the reserve leaves too little room and the approved workload remains CPU.

`run_workload.py` completes cells in order: eight small null cells, two scale
cells, Test B, then the two report-only power cells. It uses 16/6/8 one-thread
CPU workers subject to RAM, saves progress and five-minute heartbeats, and
records a device label and execution-driver hash per dataset. GPU eligibility
is rechecked at CPU-batch boundaries. `gpu_execution.py` uses the same generator
and standardisation/model/metric, one-window memory chunks and spawned CPU fit
workers; every actual GPU dataset compares its first draw for each null against
the eight-window CPU implementation at tolerance 1e-11, including k and mask.
No scientific setting is changed. GPU allocation/equality failure restarts that
dataset on the approved CPU implementation. The new scheduling path has a
CPU-emulated shared-memory check against the original sequential runner.

The initial small-city timing pilot projected about six hours at ideal CPU
scaling. Actual first-batch throughput was 12 datasets in about 210 s, which
projects 8.8 hours for small A at 12 workers, before scale/B. With the added
cells and memory contention, all-CPU total is approximately 18–24 hours; this
is a projection, not verification. Final report must state actual completion
and device counts rather than treating the original forecast as a result.
