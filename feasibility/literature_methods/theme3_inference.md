# Theme 3: Inference under spatial autocorrelation

Search date: 2026-11-17. Common brief followed: BRIEF_COMMON.md.

## Important caveat on the venue filter

Scimago (scimagojr.com) returned HTTP 403 to both curl and WebFetch. I did not try to bypass this. So NO quartile could be
looked up from Scimago. Every journal below is marked "quartile not verified". A web search turned up aggregator pages
(not Scimago) that disagree on Biometrics; I did not use them. The caller must check the quartiles (for example in a
browser) before relying on the venue filter. For this reason I list papers in one table with the venue field marked, and I
give no count of "papers that passed the filter". Citation details were checked against Crossref (VERIFIED) in every case
listed as such.

"Read depth" meaning: full text = I read the paper text (PDF/XML) for the points quoted; abstract only = abstract (and
sometimes a web summary of it) only; secondary = a web summary tool read the page for me, so quotes are only as good as that.
Where the preprint was read instead of the journal version, I say so.

## Short answers

### a) Spatial-autocorrelation-preserving null models

- Variogram matching (Viladomat 2014; Burt 2020 BrainSMASH): permute, smooth, rescale so the variogram of the surrogate
  matches the target. Viladomat 2014 (abstract) says the method keeps the initial autocorrelation. Burt 2020 (preprint full
  text, secondary read) fits the variogram only on the closest 25 percent of pairwise distances, "because SA is primarily a
  local effect", and states that the method assumes maps are normally distributed and stationary. So long-range variance is not
  fitted by construction. That matches your check that the surrogates fit the short range but carry too little long-range
  variance (my inference, not a statement in the paper). BrainSMASH exposes the distance cut-off and kernel as parameters;
  I did not find a paper that fits all ranges or a multi-scale or nested variogram inside this approach.
- Moran spectral randomization (Wagner and Dray 2015; full text read): uses eigenvectors of a spatial weights matrix, works for
  irregular points. Type I error was correct for stationary data, "but was sensitive to linear trend" (abstract). Deflated type I
  error when one variable had a linear trend. The authors say non-stationarity "remains an unsolved problem" (Discussion) and
  that Fourier randomization is also known to be trend-sensitive. Software: R package adespatial (`msr`).
- Wavelet surrogates (Deblauwe, Kennel, Couteron 2012; abstract only): dual-tree complex wavelet matching of spectra of white
  noise to the target image, for regular lattices. Claimed "excellent" type I error "even with strong and long-range
  autocorrelation, which is not the case for alternative methods" (abstract; alternatives included random shifts and IAAFT
  Fourier surrogates). This is the only paper I found that explicitly claims better long-range behaviour. Needs a regular grid.
- Benchmark (Markello and Misic 2021; preprint full text read, secondary): ten null frameworks (spin variants, Moran spectral
  randomization, BrainSMASH Burt-2018 and Burt-2020, naive). Naive nulls: false positive rate near 100 percent at high
  autocorrelation. All spatially constrained nulls were still inflated (most conservative about 13 percent at nominal 5 percent in
  their highest-autocorrelation setting). Moran spectral randomization had "categorically higher" false positive rates than
  spin nulls; BrainSMASH was sensitive to hyperparameters. The simulations reported false-positive rates only, not power. The
  authors say matching autocorrelation may not be sufficient (higher-order structure, non-stationarity). This benchmark is for
  cortical surface data (spin tests need a sphere), so spin tests do not transfer to a city grid; the other results are the
  relevant part.
- Other: Mrkvicka 2021 (random shift, not read beyond title/DOI), Clifford-Richardson-Hemon 1989 (effective-sample-size
  corrected t test, citation verified only; not read), Fulcher 2021 (ensemble nulls in gene-category enrichment; abstract: spatial
  autocorrelation and gene coexpression drive false positives).
- Gaussian random field simulation with fitted Matern, multi-scale or nested variograms as a surrogate generator for
  hypothesis tests: nothing found as a dedicated benchmark. Wagner and Dray used RandomFields exponential simulation only as
  test data.
- Dutilleul effective sample size: found only through search hits (SpatialPack, a 2007 JSPI paper); not read.

### b) Spatial confounding

- Hodges and Reich 2010 (abstract): adding a spatial random effect can change the fixed-effect estimate; it is not an
  adjustment for spatially structured missing covariates ("debunk the common belief"). They propose restricted spatial regression
  (RSR). Paciorek 2010 (abstract): bias depends on scales; fit a spatial term only if the covariate varies at a scale smaller than
  the unmeasured confounding.
- Hanks 2015 and Khan and Calder 2020 (abstracts): RSR gives overly narrow intervals under misspecification, and "typically
  perform[s] worse than non-spatial methods".
- Dupont, Wood, Augustin 2022 (Spatial+, full text of the preprint read): replace the covariate by its residual after regressing
  it on a thin-plate spatial smooth, then fit the spatial model with that residual. Consistent if the covariate "is not
  completely spatial". Limitation stated in the Discussion: covariate effects must be linear; derivations are specific to thin
  plate splines; the problem is nearly collinear columns when location explains the covariate. Software: mgcv.
- Thaden and Kneib 2018 (abstract): structural equation / path model to separate direct and indirect (via spatial) covariate effects.
- Gilbert, Ogburn, Datta 2024 (abstract): GLS with a Matern or squared-exponential working covariance is infill-consistent for the
  linear exposure effect under spatial confounding as long as the exposure has some non-spatial noise; OLS and RSR are biased.
  Gilbert et al. (arXiv preprint, full text read): coordinates as proxy for an unmeasured confounder; needs a non-spatial component
  of exposure for positivity; recommend double machine learning (flexible regression of both exposure and outcome on location /
  covariates). The text states that if the exposure is purely a function of space, positivity "is likely to be violated" and the
  effect cannot be identified. This is the closest published statement to your situation (a smooth predictor competing with
  location).
- Khan and Berrett 2026 (abstract): two different phenomena ("analysis model" and "data generation" confounding) are conflated;
  in most cases ordinary spatial linear mixed models do help inference on coefficients.
- Reich et al. 2021 review (abstract): methods that use spatial structure for unmeasured confounding, plus interference.
- Guan et al. 2023 and Keller and Szpiro 2020 (abstracts): spectral / scale-specific adjustment. Key assumption (Guan):
  confounding at global scales dissipates at local scales.
- Mäkinen 2022 (abstract): coarse-scale covariates are biased if an unobserved covariate acts at a finer scale.
- Double machine learning under spatial dependence: Gilbert (above); Fink 2023 (abstract) uses DML for citizen-science trends.
  I did not find a paper that gives a size/power study of DML tests with spatially dependent data.
- Recommendation for "does a spatial covariate matter beyond location": these papers are about the estimated effect (bias,
  coverage), not about a permutation-style test. Nothing found that recommends a specific test for the presence of an effect in
  the presence of a nearly-spatial covariate, other than Spatial+ (decorrelate) and GLS/DML with the non-spatial-variation condition.

### c) Residual randomisation and partial permutation

- Freedman and Lane 1983 and Winkler et al. 2014 (full text of Winkler read): permute residuals of the reduced (nuisance-only)
  model, add back the nuisance fit, refit the full model, recompute the statistic. Winkler et al. recommend Freedman-Lane and
  Smith; they need exchangeable (or symmetric) errors. In their notes, the permutation "would violate the ancillarity principle"
  (the X-Z relationship is destroyed) yet the methods "perform satisfactorily well" in simulations. This is not spatial.
- Spatial precedent for "randomise only the part of the predictor not explained by covariates": nothing found in the exact
  form. Closest: Spatial+ (residualise the covariate on space, estimator not a test); Wagner and Dray 2015 offer joint
  randomisation of a group of variables with within-group correlations fixed, and randomisation with a fixed correlation to the
  original (abstract). I found no "partial MSR" paper by Dray. Viladomat 2014 tests a pair of fields only.

### d) Spatial block bootstrap and block choice

- Nordman and Lahiri 2004 (abstract): optimal block size for variance estimation on regular grids depends on region geometry
  and the field; theory is for variance of a statistic, not for a performance difference.
- Zhu and Morgan 2004 (title only): block bootstrap to compare spatial variables over subregions.
- Roberts 2017 (abstract): block cross-validation is "nearly universally more appropriate"; blocks can induce extrapolation.
- Rabinowicz and Rosset 2020 (abstract): ordinary CV is biased for correlated data; bias-corrected CV.
- Bates, Hastie, Tibshirani 2023 (abstract): naive CV standard errors are too small, coverage may be "far below" nominal; they
  propose nested CV for the variance. Not spatial, but about the CI of a CV-estimated error.
- Wadoux 2021 (not read): argues against spatial CV for map accuracy.
- A paper on block bootstrap for the uncertainty of an out-of-fold average-precision difference: nothing found.

## Paper table

All DOI checks were via `https://api.crossref.org/works/<DOI>` on 2026-11-17. Venue column: Scimago not accessible (403), so
"quartile not verified" throughout.

| # | Citation | DOI check | Venue | Read depth | What it does | Limitations (authors) | Data needed | Use for us |
|---|---|---|---|---|---|---|---|---|
| 1 | Markello RD, Misic B (2021) Comparing spatial null models for brain maps. NeuroImage . 10.1016/j.neuroimage.2021.118052 | VERIFIED | NeuroImage, quartile not verified | preprint full text, read through a web summary tool (first 100k characters; Discussion not read) | Compares 10 nulls (spin variants, Moran spectral, BrainSMASH, naive) in simulations with known truth and two empirical datasets; false-positive rates only | Abstract: "even these frameworks suffer from inflated false positive rates and variable performance across analyses". Results: matching autocorrelation may not be sufficient | Cortical surface or parcellated brain maps; distance matrix | Designs 1-3: benchmark of nulls that match autocorrelation but still inflate; spin tests not applicable (need sphere). No power numbers reported |
| 2 | Burt JB, Helmer M, Shinn M, Anticevic A, Murray JD (2020) Generative modeling of brain maps with spatial autocorrelation. NeuroImage . 10.1016/j.neuroimage.2020.117038 | VERIFIED | NeuroImage, quartile not verified | preprint (bioRxiv) full text, read via web tool up to the Discussion (cut off); journal version abstract read | BrainSMASH: surrogates by permute, smooth with a kernel, rescale to fit the target variogram. Fit uses only the nearest 25 percent of distances; assumes normal and stationary maps | Preprint Methods: "assumptions ... are that maps are normally distributed and stationary". Discussion limitations not read. Own note: long-range variance is not fitted by design | A map of values plus a pairwise distance matrix, any dimension; open-source Python package `brainsmash` | Designs 2 and 3: this is the variogram-matched surrogate family in use. The distance-percentile and kernel choices are the knobs relevant to the long-range deficit |
| 3 | Wagner HH, Dray S (2015) Generating spatially constrained null models for irregularly spaced data using Moran spectral randomization methods. Methods Ecol Evol . 10.1111/2041-210x.12407 | VERIFIED | Methods in Ecology and Evolution, quartile not verified | full text (open PDF) | MSR via Moran eigenvector maps for irregular points; algorithms for single, joint, and fixed-correlation randomization. Type I error tested on simulated correlation data | Abstract: correct type I error for stationary data but "sensitive to linear trend"; Discussion: non-stationarity "remains an unsolved problem"; regression use not assessed | Point or grid coordinates, spatial weights; R package adespatial | Designs 2-3: needs stationarity; trend (large-scale gradient) will break it. Joint randomization could keep correlated covariates together |
| 4 | Viladomat J, Mazumder R, McInturff A, McCauley DJ, Hastie T (2014) Assessing the significance of global and local correlations under spatial autocorrelation: a nonparametric approach. Biometrics . 10.1111/biom.12139 | VERIFIED | Biometrics, quartile not verified | abstract only | Permute, then smooth and scale one variable to keep autocorrelation but break correlation with the other; Monte Carlo test | Not read | Two fields on a grid | Designs 1-3: original variogram-type surrogate test (the Viladomat name in the brief); test for a pair of fields only |
| 5 | Deblauwe V, Kennel P, Couteron P (2012) Testing pairwise association between spatially autocorrelated variables: a new approach using surrogate lattice data. PLoS ONE 7:e48766. 10.1371/journal.pone.0048766 | VERIFIED | PLoS ONE, quartile not verified | abstract only | Dual-tree complex wavelet surrogates; compared with a corrected parametric test, randomization, random rotations/shifts and IAAFT; claims good type I error with long-range autocorrelation | Not read | Regular lattice (image) data | Designs 2-3: only paper found that claims it handles long-range autocorrelation; requires gridded predictor (the 30 m velocity grid qualifies; cell-level data would not) |
| 6 | Dupont E, Wood SN, Augustin NH (2022) Spatial+: a novel approach to spatial confounding. Biometrics . 10.1111/biom.13656 | VERIFIED | Biometrics, quartile not verified | full text (arXiv preprint) | Replace covariate by residual from a spatial smooth of the covariate, then fit the spatial model; theory for thin-plate splines; simulations | Discussion: "covariate effects in the model must be linear"; derivations specific to thin-plate splines; works if covariate is not completely spatial | Coordinates plus covariate; GAM software mgcv | Design 3: matches "keep only the non-spatial part of the covariate". Estimator, not a permutation test |
| 7 | Hodges JS, Reich BJ (2010) Adding spatially-correlated errors can mess up the fixed effect you love. Am Stat . 10.1198/tast.2010.10052 | VERIFIED | The American Statistician, quartile not verified | abstract only | Shows spatial random effect acts as shrunken canonical regressors; restricted spatial regression | Debunks that spatial effects adjust for spatially structured missing covariates | Areal or point data | Designs 2-3: warns against reading the spatial effect as a confounder adjustment |
| 8 | Paciorek CJ (2010) The importance of scale for spatial-confounding bias and precision of spatial regression estimators. Stat Sci . 10.1214/10-STS326 | VERIFIED | Statistical Science, quartile not verified | abstract only | Analytic and simulation results for bias by spatial scale of covariate and residual | Not read | Gridded or point data | Designs 2-3: spatial term helps only when the covariate varies at smaller scale than the confounder |
| 9 | Khan K, Calder CA (2020) Restricted spatial regression methods: implications for inference. JASA . 10.1080/01621459.2020.1788949 | VERIFIED (Crossref gives the title; I did not check year of issue beyond DOI) | JASA, quartile not verified | abstract only | Shows RSR methods "typically perform worse than non-spatial methods" for areal data | Not read | Areal data | Design 3: caution on RSR-type fixes |
| 10 | Hanks EM, Schliep EM, Hooten MB, Hoeting JA (2015) Restricted spatial regression in practice. Environmetrics . 10.1002/env.2331 | VERIFIED | Environmetrics, quartile not verified | abstract only | RSR in the geostatistical setting; credible intervals can be too narrow under misspecification | Abstract states the narrow intervals | Geostatistical data | Design 3: same caution |
| 11 | Khan K, Berrett C (2026) Re-thinking spatial confounding in spatial linear mixed models. Stat Sci. 10.1214/25-STS976 | VERIFIED | Statistical Science, quartile not verified | abstract only | Two conflated types of spatial confounding; usually the spatial mixed model helps | Not read | Linear spatial mixed models | Designs 2-3: framing of which confounding type applies |
| 12 | Gilbert B, Ogburn EL, Datta A (2024) Consistency of common spatial estimators under spatial confounding. Biometrika. 10.1093/biomet/asae070 | VERIFIED | Biometrika, quartile not verified | abstract only | OLS and RSR biased; GLS with Matern/squared-exponential covariance infill-consistent if exposure has non-spatial variation | Condition: some non-spatial noise in the exposure | Geostatistical data | Design 3: states the condition that matters when a covariate is smooth |
| 13 | Gilbert B, Datta A, Casey JA, Ogburn EL (arXiv 2112.14946, v12 Oct 2024) A causal inference framework for spatial confounding. 10.48550/arxiv.2112.14946 | UNVERIFIED (arXiv record not in Crossref check; preprint) | preprint, outside venue filter | full text (PDF) | Coordinates as proxy confounder; double machine learning; positivity needs a non-spatial component of the exposure | Text: purely spatial exposure makes positivity likely to fail | Coordinates, exposure, outcome | Listed here for its recommendation; see "outside the venue filter" |
| 14 | Thaden H, Kneib T (2018) Structural equation models for dealing with spatial confounding. Am Stat . 10.1080/00031305.2017.1305290 | VERIFIED | The American Statistician, quartile not verified | abstract only | Path analysis / SEM within geoadditive models to separate direct and indirect effects | Not read | Regression data with spatial and covariate effects | Design 3: structural-equation alternative to Spatial+ |
| 15 | Reich BJ, Yang S, Guan Y, Giffin AB, Miller MJ, Rappold A (2021) A review of spatial causal inference methods for environmental and epidemiological applications. Int Stat Rev . 10.1111/insr.12452 | VERIFIED | International Statistical Review, quartile not verified | abstract only | Review of methods exploiting spatial structure against unmeasured confounding; interference; simulation | Not read | Observational spatial data | Designs 2-3: review entry point |
| 16 | Guan Y, Page GL, Reich BJ, Ventrucci M, Yang S (2023) Spectral adjustment for spatial confounding. Biometrika . 10.1093/biomet/asac069 | VERIFIED | Biometrika, quartile not verified | abstract only | Spectral-domain adjustment; adds a spatially smoothed version of the exposure to the response mean | Assumption: confounding at global scales dissipates at local scales | Areal or geostatistical | Design 3 |
| 17 | Winkler AM, Ridgway GR, Webster MA, Smith SM, Nichols TE (2014) Permutation inference for the general linear model. NeuroImage . 10.1016/j.neuroimage.2014.01.060 | VERIFIED | NeuroImage, quartile not verified | full text (Europe PMC) | Compares approximate permutation methods with nuisance variables (Freedman-Lane, Smith, ter Braak, others); simulations; recommend Freedman-Lane and Smith | Requires exchangeable or symmetric errors; ancillarity violated but methods still "perform satisfactorily" | Any regression data; software PALM and randomise | Designs 1-3: published template for residual-based partial permutation; not spatial |
| 18 | Freedman D, Lane D (1983) A nonstochastic interpretation of reported significance levels. J Bus Econ Stat . 10.1080/07350015.1983.10509354 | VERIFIED | J Business & Economic Statistics, quartile not verified | secondary (via Winkler et al.) | Origin of the residual-permutation scheme under the reduced model | Authors called p-values descriptive ("non-stochastic") per Winkler | Regression data | As above; cited as standard reference |
| 19 | Roberts DR et al. (2017) Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography . 10.1111/ecog.02881 | VERIFIED | Ecography, quartile not verified | abstract only | Review and simulations; block CV nearly always better than random | Abstract: blocking can induce extrapolation | Any structured data | Design 3: supports blocked CV; block-size advice only qualitative |
| 20 | Rabinowicz A, Rosset S (2022) Cross-validation for correlated data. JASA . 10.1080/01621459.2020.1801451 | VERIFIED (Crossref issued year 2020 online) | JASA, quartile not verified | abstract only | Bias-corrected CV for correlated data | Not read | Correlated data | Design 3 |
| 21 | Bates S, Hastie T, Tibshirani R (2023) Cross-validation: what does it estimate and how well does it do it? JASA. 10.1080/01621459.2023.2197686 | VERIFIED | JASA, quartile not verified | abstract only | Naive CV standard errors are too small; nested CV for correct coverage | Abstract: usual intervals "may have coverage far below the desired level" | Any iid-ish data | Design 3: confidence interval for out-of-fold metric differences; not spatial |
| 22 | Nordman DJ, Lahiri SN (2004) On optimal spatial subsample size for variance estimation. Ann Stat . 10.1214/009053604000000779 | VERIFIED | Annals of Statistics, quartile not verified | abstract only | Optimal block size for spatial subsampling variance estimators on regular grids | Optimal size depends "in an intricate way" on region geometry and the field | Regular grid | Design 3: block-size theory for a statistic's variance |
| 23 | Fulcher BD, Arnatkeviciute A, Fornito A (2021) Overcoming false-positive gene-category enrichment in the analysis of spatially resolved transcriptomic brain atlas data. Nat Commun . 10.1038/s41467-021-22862-1 | VERIFIED | Nature Communications, quartile not verified | abstract only | Ensemble null models accounting for spatial autocorrelation and gene coexpression | Not read | Brain atlases | Designs 1-3: example of a null that models two dependences at once |
| 24 | Clifford P, Richardson S, Hemon D (1989) Assessing the significance of the correlation between two spatial processes. Biometrics . 10.2307/2532039 | VERIFIED | Biometrics, quartile not verified | not read (title and DOI only) | Modified t test with effective sample size from estimated autocorrelation | Not read | Two fields on a grid | Standard reference; not read |

Note: volume and page numbers are omitted on purpose (not checked); some years are online-first years. Check before citing.

## Found, outside the venue filter

- Gilbert, Datta, Casey, Ogburn (arXiv 2112.14946) preprint (row 13).
- Spatial+ as originally posted: arXiv 2009.09420 (the journal version is row 6).
- Mäkinen et al. 2022 Ecography "Spatial confounding in Bayesian species distribution modeling" (10.1111/ecog.06183; Crossref VERIFIED; abstract read: coarse-scale covariates biased if an unobserved covariate acts at finer scale). Journal, quartile not verified; kept here only because I did not fit it in the table.
- Keller JP, Szpiro AA (2020) Selecting a scale for spatial confounding adjustment. JRSS A, 10.1111/rssa.12556 (VERIFIED; abstract: best selection by information criterion on an outcome model without exposure). Journal quartile not verified.
- Marques I, Kneib T, Klein N (2022) Mitigating spatial confounding by explicitly correlating Gaussian random fields. Environmetrics, 10.1002/env.2727 (VERIFIED; abstract not read).
- Fink D et al. (2023) A double machine learning trend model for citizen science data. Methods Ecol Evol, 10.1111/2041-210x.14186 (VERIFIED; abstract not read).
- Papadogeorgou G, Choirat C, Zigler CM (2019) Adjusting for unmeasured spatial confounding with distance adjusted propensity score matching. Biostatistics, 10.1093/biostatistics/kxx074 (Crossref search hit only).
- Preprints and software: Markello and Misic bioRxiv 10.1101/2020.08.13.249797; Burt bioRxiv 10.1101/2020.02.18.955054; "The impact of heterogeneous spatial autocorrelation on comparisons of brain maps" bioRxiv 10.1101/2024.06.14.598987; "Spatial Confounding: A review of concepts, challenges, and current approaches" arXiv 2602.17792; BrainSMASH (github.com/murraylab/brainsmash); adespatial (CRAN); neuromaps (software); SpatialPack (CRAN); blockCV (CRAN).
- Conference or non-journal: none.

## Identified, not read

- Mrkvicka T, Dvorak J, Gonzalez JA, Mateu J (2021) Revisiting the random shift approach for testing in spatial statistics. Spatial Statistics, 10.1016/j.spasta.2020.100430 (Crossref VERIFIED).
- Wadoux AMJ-C, Heuvelink GBM, de Bruin S, Brus DJ (2021) Spatial cross-validation is not the right way to evaluate map accuracy. Ecol Modelling 457:109692, 10.1016/j.ecolmodel.2021.109692 (VERIFIED).
- Zhu J, Morgan GD (2004) Comparison of spatial variables over subregions using a block bootstrap. JABES, 10.1198/1085711043154 (VERIFIED).
- Dutilleul-type modified t test: Dutilleul 1993 (not located); a 2007 JSPI paper ( "Modified tests for assessing the multiple correlation between one spatial process and several others", 10.1016/j.jspi.2007.06.022, OpenAlex hit; not Crossref-checked); SpatialPack (CRAN, arXiv 1611.05289).
- Alexander-Bloch et al. 2018 (spin test), Vos de Wael 2020 (BrainSpace), Vazquez-Rodriguez 2019: known from the literature, not searched or verified.
- Lahiri's book on resampling for dependent data and Hall 1985 on block methods: not searched, no details given here.
- Hodges-Reich, Paciorek, Khan-Calder, Hanks, Thaden-Kneib, Reich 2021, Gilbert 2024 and Guan 2023 full texts: only abstracts read.
- A published test of whether a spatial predictor adds out-of-sample skill under spatial blocking: nothing found.

## Search log (all 2026-11-17)

OpenAlex (rate limited with HTTP 429 after about 25 queries, so some queries failed): "Spatial+ novel approach to spatial confounding"; "BrainSMASH generative modeling spatial autocorrelation"; "Moran spectral randomization"; "spatial autocorrelation null models brain maps comparison"; "Restricted spatial regression is not spatial confounding"; "spatial confounding review"; "Adding spatially-correlated errors can mess up the fixed effect you love"; "spatial block bootstrap"; "permutation inference for the general linear model"; "assessing significance of correlation between two spatial processes"; "Viladomat ..."; "Spatial confounding in Bayesian species distribution modeling"; "geoadditive structural equation models spatial confounding"; "double machine learning spatial dependence"; "Gilbert spatial confounding bias"; "cross-validation spatial data block cross-validation prediction error estimation"; "spatial cross-validation performance difference model comparison uncertainty"; "spatial autocorrelation null model gene expression false positive"; "variogram matching long-range surrogate nonstationary"; "Dutilleul modifying the t test..."; "effective sample size spatial autocorrelation correlation Moran eigenvector"; "Fourier phase randomization spatial null model"; "wavelet spatial randomization null model spatial pattern"; "spatial confounding Paciorek importance of scale". Failed on network or 429 and later covered by Crossref: "Khan Berrett ...", "block bootstrap choice of block size spatial data", "conditional permutation test spatial covariate residuals", "spatially constrained permutation test covariates partial Mantel". The last two were never answered: no search result was obtained for conditional spatial permutation or partial Mantel tests, so a gap remains for sub-question c.

Crossref `query.bibliographic`: Roberts 2017; Wadoux 2021; Bates 2023; Nordman Lahiri; Deblauwe; Fortin Payette (Ecoscience 2002, 10.1080/11956860.2002.11682707, not read); Khan Berrett; Mrkvicka; Papadogeorgou.

Crossref DOI checks and Semantic Scholar / OpenAlex abstracts as above. Full text: arXiv PDFs 2009.09420, 2112.14946, 2012.11767 (pdftotext); Wagner-Dray open PDF; Winkler via Europe PMC XML; Markello and Burt via bioRxiv through WebFetch. Web search: Biometrics SJR quartile (aggregators only, not used); Markello PMC; Dupont arXiv. Scimago 403.
