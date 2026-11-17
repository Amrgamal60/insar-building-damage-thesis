# Literature search for methods, November 2026: synthesis

Written 2026-11-17 by Claude, at the user's request, before any retest is planned. Six searches ran in parallel
(Sonnet subagents), one per decision a new plan would have to make. Their full tables, DOIs and search logs are in
`theme1_indicator.md` to `theme6_outcome_ml.md`; the brief they worked from is `BRIEF_COMMON.md`.

**The rule this search works under.** Nothing found here can change the Austin or NYC decisions: those plans are
frozen and their results are seen (§13 point 7 of both). On those cities any new method is exploratory only. A
method can enter a retest only through a new plan frozen before its data are analysed, and its power is measured
there by a planted-signal check, not taken from a paper. The search asked what published methods exist, what
their authors say limits them, and what data they need. It did not ask which method would turn a null positive.

## 1. How far to trust this search

- **Size:** about 140 papers across the six tables (15, 21, 24, about 30, 36 and 17).
- **DOIs:** checked at Crossref for every row except 8 in theme 4 (Crossref stopped answering) and one preprint.
- **Venue filter (Q1, Q2 or IEEE): only partly confirmed.**
  - IEEE journals pass by rule: 16 in theme 5, and several in themes 1 and 6.
  - Scimago refuses automated access, and the block was not bypassed. Themes 1, 2 and 5 took quartiles from
    search-result snippets of Scimago pages or from aggregators. Themes 3, 4 and 6 have **no quartile verified**.
  - **To close this:** the Scimago journal table downloaded in a browser (one file) lets every journal be checked
    exactly. Until then no paper outside IEEE is confirmed as passing the filter.
- **Read depth is shallow.** Publishers refused most automated fetches. Nearly all rows are abstract-level. Full
  text was read for about ten: Yunjun 2019, Staniewicz 2026 (about two thirds), Wagner and Dray 2015, Winkler 2014,
  Dupont 2022 (preprint), the Gilbert preprint, Ezquerro 2020 and Peduto 2019. So most "limitations" are what an
  abstract states. Before a paper is cited in the thesis, or a method enters a plan, its full text must be read.
- **Search limits:** the free OpenAlex and Semantic Scholar budgets ran out part-way, and the network dropped at
  times. Themes 3 (conditional spatial permutation), 4 (block-size rules, location imputation) and 6 (claims
  records, null results) were searched less than planned. "Nothing found" in those means nothing found with
  reduced tools.
- **Rechecked by Claude against Europe PMC:** the abstracts of Pepe 2013 and Vickers 2011 say what theme 2 reports
  (quoted in section 2); Markello and Misic 2021 and Burt 2020 exist as cited.

## 2. What the literature says, by decision

Class: **R** = could enter a new frozen plan for a retest. **E** = on Austin or NYC, exploratory only.
**D** = needs data we do not have.

### The test statistic (theme 2)

| Finding | Source | Limits stated | Class |
|---|---|---|---|
| Every "no improvement in performance" null is the same hypothesis as "the new predictor is not a risk factor given the baseline". Testing the change in AUC of nested models with standard procedures is "extremely conservative". Recommended: test the predictor's coefficient (Wald or likelihood ratio), then report the change in discrimination as an effect size. | Pepe et al. 2013, *Statistics in Medicine*, 10.1002/sim.5727 (abstract rechecked) | Results are for independent rows and parametric tests. | R, E |
| In simulation the AUC-difference test had size below 0.006 in every configuration and "much lower power than the likelihood ratio and Wald tests". | Vickers et al. 2011, *BMC Med Res Methodol*, 10.1186/1471-2288-11-13 (abstract rechecked) | Simulation with two normal predictors. | R, E |
| Same conclusion by other routes. | Demler 2012; Seshan 2013 (theme 2 table) | Chen et al. 2013 dispute it for small samples: likelihood ratio and Wald tests can have inflated error there. Relevant to a design with about 30 positive cells. | R |
| A randomisation test that redraws the predictor given the covariates is valid with any statistic; a likelihood-based statistic is the most powerful against a point alternative. | Conditional randomisation test: Candès 2018; Tansey 2022; Liu 2022; Katsevich and Ramdas 2022 (theme 2 table) | All need the distribution of the predictor given the covariates, and all assume independent rows. None treats spatial fields. | R |
| Intervals built from cross-validation folds undercover, because fold errors are correlated. | Bates, Hastie and Tibshirani 2023, *JASA*, 10.1080/01621459.2023.2197686 | Not spatial. | R |
| No journal paper gives a valid test of the change in average precision between nested models. | Theme 2, nothing found | The closest is an arXiv preprint (Zhou 2020). | – |

**What it means for us, and what it does not.**
- **The warning does not transfer directly.** Pepe et al. blame "invalid procedures for inference rather than the
  measure itself", and the size below 0.006 in Vickers et al. is for a standard AUC test applied to fitted nested
  models. Our test uses the same measure with a randomisation null, and its size and power were measured on the real
  field by the planted-signal check: 5% false positives with nothing added, and 34%, 75% and 100% power at odds
  ratios of 1.11, 1.22 and 1.49. So Test A was not the conservative test these papers describe.
- **What remains is a hypothesis:** that inside the same surrogate null, the fitted coefficient or the gain in
  log-likelihood would have more power than the change in out-of-fold average precision. The support is one result
  (Katsevich and Ramdas 2022), read at abstract level and proved for independent rows. Test B already uses |β|.
- **By Pepe's result both statistics test the same hypothesis,** so this is a question of power, not of meaning.
- **It can be measured, not assumed:** rerun planted cells 1, 4 and 5 with the coefficient as the statistic. That
  uses synthetic outcomes only and touches no real result.
- **Measured on 2026-11-17 (synthetic only; `feasibility/austin/planted_signal/statistic_comparison.py`, records in
  `statcmp_20261117/` and `statcmp_20261117_cells23/`, §15 of the Austin plan).** Planted cells 1–5, 100 datasets
  each, the same datasets and 999 surrogates as the planted-signal check. The frozen statistic reproduced the
  2026-11-11 records exactly.

  | Statistic | False positives, cells 1–3 pooled (300) | Power β = −0.1 | Power β = −0.2 |
  |---|---|---|---|
  | Change in out-of-fold average precision (frozen) | 7.0% | 34% | 75% |
  | Change in out-of-fold log-likelihood | 4.7% | 66% | 100% |
  | Change in in-sample log-likelihood | 8.0% (above 5%, p 0.017) | 68% | 100% |
  | Velocity coefficient, negative tail | 4.0% | 55% | 96% |

  The hypothesis held: the held-out log-likelihood gain about doubled power at β = −0.1 with no rise in false
  positives, including under the two misspecified cells. Limits: one city's design, an effect planted in the
  model's own log-linear form, 100 datasets per cell.

### Inference under spatial autocorrelation (theme 3)

| Finding | Source | Limits stated | Class |
|---|---|---|---|
| Variogram-matching surrogates fit the variogram on the nearest distances only (the closest 25% in the software's default) and assume normal, stationary maps. | Burt et al. 2020, *NeuroImage*, 10.1016/j.neuroimage.2020.117038 (preprint, secondary read) | Long-range structure is not fitted by construction. This matches our variogram checks (my inference). | – |
| In a benchmark of ten spatial nulls, every spatially constrained null still had inflated false-positive rates; matching autocorrelation "may not be sufficient". | Markello and Misic 2021, *NeuroImage*, 10.1016/j.neuroimage.2021.118052 | Brain-surface data. Only false-positive rates were reported, no power. | – |
| Moran spectral randomisation has correct error for stationary data but is sensitive to a linear trend; non-stationarity "remains an unsolved problem". | Wagner and Dray 2015, *Methods Ecol Evol*, 10.1111/2041-210x.12407 (full text) | – | – |
| Wavelet surrogates are the one method found that claims good error control "even with strong and long-range autocorrelation". | Deblauwe et al. 2012, *PLoS ONE*, 10.1371/journal.pone.0048766 (abstract only) | Needs a regular grid. Not read in full. | R (after a calibration) |
| The effect of a predictor that is almost a function of location cannot be identified; it needs variation that location does not explain. | Paciorek 2010; Dupont et al. 2022 (Spatial+), 10.1111/biom.13656; Gilbert et al. (preprint) | Spatial+ assumes linear effects. These are estimation papers, not tests. | R (as a diagnostic) |
| Randomising only the residual of the predictor after the covariates is standard outside spatial data. | Freedman and Lane 1983; Winkler et al. 2014, 10.1016/j.neuroimage.2014.01.060 (full text) | Needs exchangeable errors. No spatial version was found, so our conditional null has no direct published precedent. | – |

**What it means for us.**
- One benchmark, on brain maps and read second-hand, found unconditional spatial nulls too lenient. Our own
  calibration (plan §10) found the same of the unconditional null (a) under a nonlinear soil effect, and found the
  conditional null (b) possibly conservative at Austin's size. The evidence on direction is therefore thin and mixed.
- The Alexandria discovery was tested only with unconditional nulls (largest p 0.005, about 30 positive cells), and
  its own report found them rougher than the field at the shortest lag. It is the result that has not yet met the
  stricter null.

### The indicator (themes 1 and 5)

| Finding | Source | Limits stated | Class |
|---|---|---|---|
| Building-scale indicators in the literature are gradients: differential settlement, angular distortion, a per-building deformation gradient. The main validated one tests a gradient map against 633 surveyed buildings by ROC analysis. | Barra et al. 2022 (*RSE*); Shahbazi et al. 2024 (*ISPRS J*); Peduto 2019; Nappo 2021 (theme 1 table) | All need several coherent points on or around each building: persistent scatterers, ideally X-band. Abstract-level reads. | D |
| No paper was found that shows a gradient indicator beating plain velocity on the same buildings. | Theme 1; Zhang et al. 2025 (*Engineering Geology*) may, but was not read | – | – |
| No reliable precursor of building collapse has been demonstrated. The Surfside study reports no signal before the collapse; the Morandi bridge signal is contested; the tailings-dam precursors are single retrospective cases without controls. | Zanjani 2024; Lanari 2020; Rodríguez-Antuñano 2023 (themes 1 and 6) | Case studies. No detection or false-alarm rates on many cases with controls. | – |
| Velocity precision improves with record length. About 1 mm/yr needs regularly sampled Sentinel-1 records longer than 5 years; two years gave differences of 8 to 10 mm/yr (1σ) against GNSS and levelling in one valley. | Havazli 2021; Liu 2022; Cigna 2021 (theme 5 table; quartiles from aggregators) | None gives a figure for one 30 m pixel over 24 months. Nothing found on the smallest detectable difference between a building and its neighbours. | – |
| OPERA DISP-S1: L1 network inversion, no tropospheric or ionospheric correction, relative to the frame, no residual unwrapping-error rate reported. | Staniewicz et al. 2026, *IEEE TGRS*, 10.1109/TGRS.2026.3685947 | The authors say dates or regions with large residuals should be masked. Our slip screen did this after the fact. | – |
| On 2,000 random Sentinel-1 points, constant extrapolation beat seasonal ARIMA and LSTM forecasts. Deep-learning change-point detectors were validated mostly on simulated data. | Hill 2021 (*JGR Solid Earth*); Lattari 2022, Kulshrestha 2022 (IEEE) | No false-alarm rates on stable areas in any abstract read. | – |

**What it means for us.** The indicators the literature trusts cannot be formed from a 30 m product, where a house
is about one pixel, or from 100 m LiCSAR cells. They need a persistent-scatterer point cloud. And a 24-month
velocity at a single pixel may be noisier than the motion differences between houses; no paper found quantifies
this, so it is a hypothesis about our null result, not an established cause.

### Methods of this kind that Austin already ran

Several things the literature suggests were preregistered secondaries in Austin (§12). None carries a decision, and
none shows a gain (`secondary_real/AUSTIN_SECONDARY_RESULTS.md`; change in PR AUC, 95% interval, nominal p):

| Literature idea | Austin secondary | Change | 95% interval | p |
|---|---|---|---|---|
| Gradient against the surroundings | 6. Local relative motion (house against its 250 m ring) | −0.00003 | −0.00103 to +0.00063 | 0.217 |
| Seasonal (shrink-swell) signal | 6. Seasonal amplitude | −0.00026 | −0.00182 to +0.00060 | 0.879 |
| Acceleration as a precursor | 6. Acceleration | −0.00010 | −0.00087 to +0.00021 | 0.666 |
| Shorter or longer record | 3. 12-month window | −0.00038 | −0.00107 to +0.00016 | 1.000 |
| | 3. 36-month window | −0.00110 | −0.00307 to +0.00112 | 0.850 |
| Lead time before the event | 9. Lags 1, 3, 6 and 12 months | −0.00052, −0.00015, −0.00023, −0.00075 | all include 0 | 0.949, 0.004, 0.047, 0.721 |
| Machine learning | 4. Random forest | +0.00105 | −0.00279 to +0.00320 | 0.056 |
| | 7. Boosted trees, all four indicators | −0.00070 | −0.00637 to +0.00557 | 0.180 |
| Deep learning on the time series | 20. Deep model | −0.00371 | −0.00537 to +0.00165 | 0.52 |

The two small p values at lags 3 and 6 come with negative changes: the surrogate fields lost more, so they are not
gains. The local-relative-motion indicator is only the nearest analogue of a building gradient at 30 m; it is not
the within-building gradient the literature uses.

### Design and validation (theme 4; no quartile verified)

| Finding | Source | Limits stated | Class |
|---|---|---|---|
| Fold design can be chosen so that test-to-training distances match the distances at which the model will be used, instead of a fixed block size. | Milà et al. 2022, 10.1111/2041-210X.13851; Linnenbrink et al. 2024, 10.5194/gmd-17-5897-2024; Meyer and Pebesma 2021, 10.1111/2041-210X.13650 | Blocking can force extrapolation (Roberts 2017, 10.1111/ecog.02881). Abstract-level reads. | R |
| Case-only designs (case-crossover, case-time-control) compare a unit with itself at other times and remove everything fixed about the unit. | Maclure 1991; Suissa 1995 (theme 4 table) | No natural-hazard or building application was found. They need the exposure at several times for the same unit. Test B is our area-level version of this idea. | R |
| Location error can bias an exposure–outcome association in either direction, not only toward zero. | SC-SIMEX paper (*Statistics in Medicine* 2022); area-based geocoding (*GeoHealth* 2021) (theme 4 table) | Methods exist to correct it; not read in full. Matters for Alexandria, where events are placed on a street (median extent 127 m), not a cell. | R |
| Nothing found on how stable average precision is with 30 to 60 positives. | Theme 4, nothing found | – | – |

### Outcome records and prediction studies (theme 6; no quartile verified outside IEEE)

- **No study found does what this thesis does:** InSAR features against a real damage record, held out, spatially
  separated, compared with a baseline without InSAR. Published work is fragility curves fitted and checked on the
  same buildings, risk maps with no damage record, and retrospective looks at known collapse sites without controls.
- **The published risk thresholds are untested, and their authors say so.** Ohenhen 2025 and Sadhasivam 2025 both
  state they could not validate against damage records. A third paper uses a different threshold set.
- **Where a check exists it is weak.** In Ezquerro 2020 (full text read) the share of damaged buildings across the
  five predicted-probability classes is 52, 39, 48, 64 and 68%, on the same data used to fit.
- **Null results are almost unpublished.** None framed as such passed the search. Publication bias is likely.

## 3. What this means for a retest of Alexandria

1. **A true "before" test is not possible on the present inventory.** The 2014–2016 events overlap the start of
   Sentinel-1 (October 2014): only 11 events have two or more years of earlier data (`data/inventory/AUDIT_REPORT.md`,
   finding 6). It needs events from 2017 on. The only known source, the GPS-located inventory of Mohamadi et al.
   (255 collapses, 2001–2019), was requested from its authors on 2026-09-29; no reply is recorded.
2. **What can be done with the data in hand** is a stricter test of the concurrent association, not a precursor test:
   - the conditional null of the Austin plan (null b) in place of the six unconditional nulls;
   - the coefficient or log-likelihood gain as the statistic;
   - the event's street extent carried through, instead of one cell per event;
   - a planted-signal check at Alexandria's size (about 30 positive cells), to know what the test can see.
   The Alexandria data have been seen, so this is a robustness analysis under a plan frozen in advance, and it
   must be labelled so.
3. **A building-scale indicator needs new InSAR processing** (persistent scatterers; X-band if obtainable), for any city.

## 4. Bottom line on power

- **Measured (2026-11-17, synthetic only, section 2):** inside the same surrogate null, the change in out-of-fold
  log-likelihood had 66% and 100% power at β = −0.1 and −0.2, against 34% and 75% for the change in average
  precision, with pooled false positives of 4.7% against 7.0%. It keeps the held-out framing, so it is the
  candidate primary statistic for any new frozen plan, with the change in average precision reported as the effect
  size. The published warnings about discrimination tests concern a different, invalid procedure.
- **Do not expect this to reverse Austin.** The hypothesis tested is the same. In the Austin record the velocity
  coefficient on all rows was +0.0085 and the median case-minus-control difference +0.009 standardised units, both
  close to zero and both in the opposite direction. Any such reanalysis there would be exploratory.
- **Most likely real limit, not yet shown:** indicator noise and resolution. The literature's working indicators
  are building-scale gradients from dense points; ours is a 24-month trend at one 30 m pixel.
- **The other indicators, windows, lags and models the literature points to were already run in Austin** as
  preregistered secondaries, without a gain (section 2).
- **The thesis is not behind the literature.** No study was found that applies the test this thesis applies (theme
  6 was searched with reduced tools), and the best-known risk maps are unvalidated by their authors' own account.

## 5. Still to do before any of this is cited or used

1. Check every journal's quartile against the Scimago table (needs the file from a browser).
2. Read in full the papers a plan would rest on: Pepe 2013, Vickers 2011, Chen 2013, Katsevich and Ramdas 2022,
   Deblauwe 2012, Barra 2022, Shahbazi 2024, Zhang 2025, Milà 2022, and the SC-SIMEX paper.
3. Rerun the under-searched questions (section 1) when the search services allow.
4. Yang 2026 and Ma 2022 are still abstract-only (the open copies refused automated download).
