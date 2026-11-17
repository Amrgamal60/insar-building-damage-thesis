# Theme 4: Study design and validation (search of 17 November 2026)

## Caveats that apply to the whole file

- Venue: Scimago (scimagojr.com) returned a Cloudflare anti-bot page (HTTP 403) to curl and to WebFetch. I did not try to bypass it. No quartile could be looked up, so every journal below is marked "quartile not verified". The venue filter is therefore NOT confirmed for any row. The caller must check the quartiles before treating a row as passing. IEEE journals (LGRS, JSTARS) pass by the IEEE rule.
- Read depth: the abstracts came from OpenAlex. I did not read full texts. Limitations are quoted or paraphrased from abstracts only. Where an abstract had none, I write "not retrieved" and add nothing. Where a limitation is my own, it is labelled "OWN".
- DOI check: Crossref was queried. Some calls later in the session returned empty or non-JSON responses (apparent rate limit or network drop). Those rows are marked UNVERIFIED, with the OpenAlex title match noted.
- No paper in the hazard literature (landslide, sinkhole, pipe break, building failure) was found that uses case-crossover, nested case-control with risk-set sampling, or self-controlled case series. See 4b.

## Short answers

### a) Spatial cross-validation and what it estimates
- Random CV on spatially structured data gives optimistic error (Roberts 2017; Ploton 2020: a non-spatial CV suggested more than half of biomass variance explained, spatial CV showed "quasi-null" power; landslide-specific, Remote Sensing 2025: random CV 6 to 18% higher than spatial CV).
- Block CV needs a considered blocking rule. Roberts 2017 warn that blocking can "unwittingly induce extrapolations" by restricting predictor ranges and so overestimate interpolation error.
- Wadoux 2021 argue spatial CV is not the right way to estimate map accuracy; only a probability sample gives design-unbiased map accuracy (title and argument; abstract not retrieved, so I do not quote them).
- Milà 2022 (NNDM LOO) and Linnenbrink 2024 (kNNDM, k-fold) choose the fold design so that the test-to-train nearest-neighbour distances match the prediction-to-training distances. This ties the fold design to the intended prediction area, not to a fixed block size. Brenning 2022 (spatial prediction error profiles) says to assess the model over the intended spatial prediction horizon. Airola 2019 (spatial leave-pair-out) targets AUC bias from both pooling and autocorrelation, with few positives.
- Meyer and Pebesma 2021 define a dissimilarity index and an area of applicability: where the CV estimate can be expected to hold.
- Block size: none of the abstracts gives a number. Brenning 2022 mentions the range of autocorrelation as a reference (abstract cut off). A fixed 2 km block is our design's own choice; the papers support choosing it from the autocorrelation range or from NND matching, but I did not read a stated rule.

### b) Designs for dated events with time-varying exposure
- Method papers found: case-crossover (Maclure 1991, DOI verified, abstract not retrieved), case-time-control (Suissa 1995; the 2013 Epidemiology paper on autocorrelated exposure), exchangeability in case-crossover (Mittleman and Mostofsky 2014 (author names from memory, not checked)), SCCS (Whitaker 2006), equivalence of case-crossover and time series (Lu and Zeger 2007).
- Stated assumptions: case-time-control needs exposure measurable at two or more times and removes time-invariant confounders by design; it handles population-level time trends but assumes independence of within-person exposure history (that paper found it "quite robust" to violations in simulation). Case-crossover obeys the same exchangeability rules as case-control (carryover, period effects, selection bias). SCCS infers within individuals from cases only.
- Applications with event counts in natural hazards or infrastructure: NOTHING FOUND in my searches (landslide, sinkhole, water main, building collapse). The pipe-failure literature surfaced (Water 2020 comparison; Sci. Rep. 2024; review 2022) is survival or machine-learning modelling; I did not read these and list them as not read.
- Note the fit for us: all the case-only designs compare a unit with itself, so they need the same unit to be observed at several times. OWN: a house with a single velocity per window gives a self-comparison only if several windows per house exist; the case-control with 50 controls per case already uses risk-set style sampling.

### c) Uncertain locations and dates
- Positional error in geocoding: Mazumdar 2008 simulated three geocode types; the abstract says the odds from top-quality geocodes could be largely recovered with TIGER or E-911 geocodes (the second half of the sentence is cut off in what I retrieved). The 2013 Environ Health near-highway study compared parcel, TIGER and StreetMap geocodes against a gold standard in a near-highway study (N = 703). Area-based geocoding (GeoHealth 2021) keeps the matched area rather than a centroid. SC-SIMEX (Stat Med 2022) shows that coarsening gives exposure error with heterogeneous variance and non-zero mean, and the bias can be "away from the null"; it extends SIMEX to correct this.
- Reporting delay in administrative records: nothing found that passes the filter. Only epidemiology nowcasting items and preprints surfaced (see lists below).

### d) Rare events and small numbers of positives
- Firth penalisation: reduces coefficient bias but biases predicted probabilities towards one-half, worse at stronger imbalance (Puhr 2017, two corrections proposed). King and Zeng 2001 is the standard rare-events logistic reference (DOI verified; abstract not retrieved).
- Minimum events: Riley 2018 propose criteria based on shrinkage of at least 0.9, optimism in R-squared of at most 0.05 and precision of the overall risk. These are for model development, not for validating a test statistic.
- Precision-recall against ROC: Saito and Rehmsmeier 2015 show ROC plots can be deceptive on imbalanced data (abstract). Davis and Goadrich 2006 is a conference paper (outside the filter).
- Stability of average precision with 30 to 60 positives: no paper found that gives a number. NOTHING FOUND.

### e) Under-recording, PU learning and negative controls
- PU framing: Landslide papers treat "no record" as unlabelled (Geoenvironmental Disasters 2024; IEEE LGRS 2021; IEEE JSTARS 2021 and 2024 listed). Ward 2009 gives an EM algorithm for presence-only data, noting prevalence is only identifiable under assumptions (abstract cut off). Bekker and Davis 2020 is the PU survey (abstract not retrieved). Phillips 2009 on sample-selection bias in presence-only models.
- Incomplete inventories: Steger 2017 simulated removal of landslides in forests and selected municipalities and tested mixed-effects models.
- Negative controls: Lipsitch 2010 (DOI verified; abstract not retrieved). Commentary on imperfect negative-control exposures (Epidemiology 2016) listed, not read.

## Paper table

All "Venue" cells: quartile not verified (Scimago blocked), unless stated.

| Citation | DOI check | Venue | Read depth | What it does | Limitations (as stated) | Data needed | Use for us |
|---|---|---|---|---|---|---|---|
| Linnenbrink et al. (2024) kNNDM CV: k-fold nearest-neighbour distance matching cross-validation for map accuracy estimation. Geosci. Model Dev. 17, 5897. 10.5194/gmd-17-5897-2024 | VERIFIED (Crossref) | Geoscientific Model Development; quartile not verified | abstract only | k-fold CV that matches the ECDF of test-to-train distances to prediction-to-train distances; simulation with several sampling distributions | Abstract only; motivates it as LOO NNDM cannot scale to large datasets. Rest not retrieved | point locations, prediction area | Designs 2 and 3: choose folds from the target prediction area, not a fixed 2 km. Needs event locations and the area of the city |
| Brenning A (2022) Spatial machine-learning model diagnostics: a model-agnostic distance-based approach. Int. J. Geogr. Inf. Sci. (print 2023) 10.1080/13658816.2022.2131789 | VERIFIED (Crossref) | IJGIS; quartile not verified | abstract only | Spatial prediction error profiles and variable importance profiles by prediction distance | "Limitations of related cross-validation techniques are outlined" (abstract) | point data with predictions | Design 3: profile error by distance from training folds |
| Karasiak N et al. (2022) Spatial dependence between training and test sets: another pitfall of classification accuracy assessment in remote sensing. Machine Learning 111. 10.1007/s10994-021-05972-1 | VERIFIED (Crossref says 2021 online) | Machine Learning; quartile not verified | not retrieved (no abstract) | Title only read | not retrieved | not retrieved | listed for completeness; read before citing |
| Milà et al. (2022) Nearest neighbour distance matching leave-one-out cross-validation for map validation. Methods Ecol. Evol. 13, 1304. 10.1111/2041-210X.13851 | VERIFIED | Methods in Ecol. Evol.; quartile not verified | abstract only | NNDM LOO CV; two simulations varying prediction area, autocorrelation, sampling | LOO is fine with short autocorrelation or gridded sampling (abstract, cut off) | points, prediction area | Designs 1 to 3 as for kNNDM; LOO cost on 150,000 houses is large (OWN) |
| Meyer H, Pebesma E (2021) Predicting into unknown space? Estimating the area of applicability of spatial prediction models. Methods Ecol. Evol. 10.1111/2041-210X.13650 | VERIFIED | MEE; quartile not verified | abstract only | Dissimilarity index in weighted predictor space; AOA threshold from CV | Abstract only | predictors at training and prediction cells | Designs 2 and 3: flag cells where velocity features are out of the training range |
| Meyer H, Pebesma E (2022) Machine learning-based global maps of ecological variables and the challenge of assessing them. Nat. Commun. 13. 10.1038/s41467-022-29838-9 | VERIFIED | Nature Communications; quartile not verified | abstract only (two sentences) | Discusses whether map quality can be assessed | not retrieved | none | background only |
| Wadoux et al. (2021, author list not checked) Spatial cross-validation is not the right way to evaluate map accuracy. Ecol. Model. 457, 109692. 10.1016/j.ecolmodel.2021.109692 | VERIFIED | Ecological Modelling; quartile not verified | title only (no abstract returned) | not retrieved beyond title | not retrieved | not retrieved | read before citing; relevant because our target is held-out predictive comparison, not a map (OWN) |
| Ploton P et al. (2020) Spatial validation reveals poor predictive performance of large-scale ecological mapping models. Nat. Commun. 11. 10.1038/s41467-020-18321-y | VERIFIED | Nature Communications; quartile not verified | abstract only | 11.8 million tree dataset, random forest; non-spatial vs spatial validation | not retrieved | large inventory | Design 3: motivates blocked CV and a null with weak predictors |
| Roberts DR et al. (2017) Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography 40. 10.1111/ecog.02881 | VERIFIED | Ecography; quartile not verified | abstract only | Review of block CV in ecology | Blocking may "unwittingly induce extrapolations" and overestimate interpolation error (abstract) | structured data | Designs 1 to 3: block choice and extrapolation trade-off |
| Airola A et al. (2019) The spatial leave-pair-out cross-validation method for reliable AUC estimation of spatial classifiers. Data Min. Knowl. Disc. 33. 10.1007/s10618-018-00607-x | UNVERIFIED (Crossref empty; OpenAlex title match, year 2018 online) | Data Mining and Knowledge Discovery; quartile not verified | abstract only | Corrects AUC bias from pooling and autocorrelation; few positives, mineral prospectivity | not retrieved | few positives, no verified negatives | Design 1 (about 30 positives); AUC rather than AP |
| Random cross-validation produces biased assessment of machine learning performance in regional landslide susceptibility prediction (2025). Remote Sens. 17, 213. 10.3390/rs17020213 | VERIFIED | Remote Sensing; quartile not verified | abstract only | Random vs spatial CV on landslide susceptibility, 7 ML models | R-CV 6 to 18% more optimistic than S-CV (abstract); authors list not retrieved | landslide inventory | Hazard example for the CV choice |
| Mittleman MA, Mostofsky E (2014) Exchangeability in the case-crossover design. Int. J. Epidemiol. 43. 10.1093/ije/dyu081 | VERIFIED | IJE; quartile not verified | abstract only | Frames case-crossover confounding as exchangeability; carryover, period effects, selection bias | Issues "identical" to those in case-control and cohort studies (abstract) | cases with several time points | Design 3: risk of a pre-event period differing systematically from earlier periods |
| Mittleman or similar authors, On the validity of the case-time-control design for autocorrelated exposure histories. Epidemiology 2013. 10.1097/ede.0000000000000001 | UNVERIFIED (Crossref empty; OpenAlex title and 2013 match). Author names not retrieved, so not cited by name | Epidemiology; quartile not verified | abstract only | Case-time-control with conditional logistic regression; splines for time trends in exposure | Design "quite robust" to violating within-person independence in simulation (abstract) | cases plus matched controls, repeat exposure | Design 3: same-unit before and after contrast with control houses |
| Suissa S (1995) The case-time-control design. Epidemiology 6. 10.1097/00001648-199505000-00010 | VERIFIED | Epidemiology; quartile not verified | abstract only | Case-control subjects as own controls; needs exposure at two or more times; asthma example with 129 cases and 655 controls | not retrieved | repeated exposure | Design 3 |
| Whitaker HJ et al. (2006) Tutorial in biostatistics: the self-controlled case series method. Stat. Med. 25. 10.1002/sim.2302 | VERIFIED (Crossref year 2005 online) | Statistics in Medicine; quartile not verified | abstract only | Cases only, within-individual comparison; origins, assumptions, limitations | assumptions listed in the paper, not retrieved | cases only | Needs repeated events or observation periods; fit to single collapse events is unclear (OWN) |
| Lu Y, Zeger SL (2007) On the equivalence of case-crossover and time series methods in environmental epidemiology. Biostatistics 8. 10.1093/biostatistics/kxl013 | UNVERIFIED (Crossref empty; OpenAlex match) | Biostatistics; quartile not verified | abstract only | Case-crossover with conditional logistic regression equals time-series model for common exposure | not retrieved | daily exposure | Area-level Poisson panel (Design 3) |
| Mazumdar S et al. (2008) Geocoding accuracy and the recovery of relationships between environmental exposures and health. Int. J. Health Geogr. 7, 13. 10.1186/1476-072X-7-13 | VERIFIED | IJHG; quartile not verified | abstract only | Simulation of orthophoto, TIGER, E-911 geocodes: power depends on strength, positional accuracy, completeness | rest of abstract not retrieved | known locations | Designs 1 and 2: simulate 130 m error on 250 m cells |
| Positional error and time-activity patterns in near-highway proximity studies: an exposure misclassification analysis. Environ. Health 12, 75 (2013). 10.1186/1476-069X-12-75 | VERIFIED | Environmental Health; quartile not verified | abstract only | Parcel, TIGER, StreetMap geocodes vs gold standard; N = 703 | not retrieved | addresses | Design 1 |
| Area-based geocoding: an approach to exposure assessment incorporating positional uncertainty. GeoHealth (2021). 10.1029/2021GH000430 | VERIFIED | GeoHealth; quartile not verified | abstract only | Keeps the matched area rather than a centroid; pesticide and breast cancer case-control | not retrieved | exposure surface plus geocode areas | Design 1: use the street-level uncertainty region as the unit |
| Split and combine simulation extrapolation algorithm to correct geocoding coarsening of built environment features. Stat. Med. 41 (2022). 10.1002/sim.9338 | VERIFIED | Statistics in Medicine; quartile not verified | abstract only | SC-SIMEX for buffer counts | Coarsening gives non-zero mean error and bias can be away from the null (abstract) | point exposures, buffer counts | Design 1 or 2 if exposure is a buffer summary |
| Puhr R et al. (2017) Firth's logistic regression with rare events: accurate effect estimates and predictions? Stat. Med. 36. 10.1002/sim.7273 | VERIFIED | Statistics in Medicine; quartile not verified | abstract only | Corrects Firth's biased predicted probabilities by intercept adjustment or augmentation | Firth biases predictions towards one-half, worse with stronger imbalance (abstract) | small samples, rare outcomes | Designs 1 to 3 if probabilities are used |
| Riley RD et al. (2019) Minimum sample size for developing a multivariable prediction model: Part II, binary and time-to-event outcomes. Stat. Med. 38. 10.1002/sim.7992 | VERIFIED (Crossref says 2018 online) | Statistics in Medicine; quartile not verified | abstract only | Three criteria for n and E | development only (OWN) | expected R-squared | Design 1 and 2: events per parameter |
| Saito T, Rehmsmeier M (2015) The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. PLOS ONE 10. 10.1371/journal.pone.0118432 | VERIFIED | PLOS ONE; quartile not verified | abstract only | ROC plots can mislead with many negatives | not retrieved | imbalanced labels | Designs 1 to 3: report AP |
| King G, Zeng L (2001) Logistic regression in rare events data. Political Analysis 9. 10.1093/oxfordjournals.pan.a004868 | VERIFIED | Political Analysis; quartile not verified | not retrieved | Standard rare-events reference | not retrieved | not retrieved | read before citing |
| Lipsitch M, Tchetgen Tchetgen E, Cohen T (2010) Negative controls. Epidemiology 21. 10.1097/EDE.0b013e3181d61eeb | VERIFIED (title "Negative Controls") | Epidemiology; quartile not verified | not retrieved | not retrieved | not retrieved | not retrieved | Design 3 remodel-permit control: check the conditions before citing |
| Ward G et al. (2009) Presence-only data and the EM algorithm. Biometrics 65. 10.1111/j.1541-0420.2008.01116.x | VERIFIED (Crossref 2009) | Biometrics; quartile not verified | abstract only | EM estimate of presence-absence model from presence-only plus background | prevalence identifiable only under conditions (abstract cut off) | presence points plus background sample | Designs 1 to 3 if "no record" is unlabelled |
| Bekker J, Davis J (2020) Learning from positive and unlabeled data: a survey. Machine Learning 109. 10.1007/s10994-020-05877-5 | VERIFIED | Machine Learning; quartile not verified | title only | not retrieved | not retrieved | not retrieved | read before citing |
| Enhancing landslide susceptibility mapping using a positive-unlabeled machine learning approach (2024). Geoenvironmental Disasters 11. 10.1186/s40677-024-00281-w | VERIFIED | Geoenv. Disasters; quartile not verified | abstract only | PU framing; Chamoli district; non-random split for spatial bias | not retrieved | inventory plus 11 factors | hazard PU example |
| Steger S et al. (2017) The influence of systematically incomplete shallow landslide inventories on statistical susceptibility models. Landslides. 10.1007/s10346-017-0820-0 | VERIFIED | Landslides; quartile not verified | abstract only | Simulated removal of landslides in forests and selected municipalities; mixed-effects models | not retrieved | inventory plus covariates | Designs 1 to 3: simulate under-recording |
| Landslide Susceptibility Modeling Using Bagging-Based Positive-Unlabeled Learning. IEEE Geosci. Remote Sens. Lett. (2021). 10.1109/LGRS.2020.2989497 | VERIFIED (Crossref 2021) | IEEE journal | title only | PU bagging | not retrieved | inventory | background |

Count: about 30 rows, none quartile-verified. The caller should treat the roughly 12 most relevant as: Linnenbrink 2024, Milà 2022, Meyer 2021, Roberts 2017, Mittleman 2014, case-time-control 2013 and 1995, Mazumdar 2008, GeoHealth 2021, SC-SIMEX 2022, Puhr 2017, Saito 2015, Ward 2009, Steger 2017.

## Found, outside the venue filter

- Davis J, Goadrich M (2006) The relationship between precision-recall and ROC curves. ICML (conference).
- Elkan C, Noto K (2008) Learning classifiers from only positive and unlabeled data. KDD (conference).
- Brenning A (2012) Spatial cross-validation and bootstrap for the assessment of prediction rules in remote sensing: the R package sperrorest. IGARSS (conference).
- Quantifying spatial under-reporting disparities in resident crowdsourcing, Nature Computational Science 2023, 10.1038/s43588-023-00572-6: not read; quartile not verified and Crossref returned no record at check. Could be moved into the table after check.
- A Bayesian spatial model to correct under-reporting in urban crowdsourcing, AAAI 2024 (conference).
- Assessing the performance of spatial cross-validation approaches for models of spatially structured data, arXiv 2303.07334 (preprint).
- Assessing reporting delays in ACLED conflict event data, arXiv 2603.25964 (preprint).
- Spatial information explained by prediction models under block cross-validation, ISPRS J. Photogramm. Remote Sens. 2026 (found by title; journal may pass the filter; not read).

## Identified, not read

- Maclure M (1991) The case-crossover design. Am. J. Epidemiol. 10.1093/oxfordjournals.aje.a115853 (DOI verified; no abstract retrieved).
- Landslide PU: IEEE JSTARS 2021 (10.1109/jstars.2021.3125741) and 2024 (10.1109/jstars.2024.3452182), both IEEE journals, abstracts not retrieved, DOI not verified.
- Imperfect negative control exposures, Epidemiology 2016, 10.1097/ede.0000000000000454.
- Effect of geocoding errors on traffic-related air pollutant exposure, J. Expo. Sci. Environ. Epidemiol. 2015, 10.1038/jes.2015.1 (Crossref empty).
- Impact of geocoding methods on associations between long-term exposure to urban air pollution and lung function, Environ. Health Perspect. 2013, 10.1289/ehp.1206016.
- Geocoding accuracy in the Agricultural Health Study, Int. J. Health Geogr. 2014, 10.1186/1476-072X-13-37.
- Pipe failure: Water 2020 (10.3390/w12041153), Sci. Rep. 2024 (10.1038/s41598-024-69855-w), Water Sci. Technol. Water Supply 2022 review (10.2166/ws.2022.019). Survival models for water mains; event counts not checked.
- Riley 2020 minimum sample size for external validation, Stat. Med. 10.1002/sim.8766 (continuous outcome); Riley 2021 simulation-based external validation sample size, J. Clin. Epidemiol. 10.1016/j.jclinepi.2021.02.011.
- Boyd 2013 AUC-PR confidence intervals; Weighted and unweighted AUC-PR, PLOS ONE 2014, 10.1371/journal.pone.0092209 (possibly relevant to AP stability; not read).
- Plotting ROC and PR curves from presence and background data, Ecol. Evol. 2021, 10.1002/ece3.7826.
- Brenning 2012 IGARSS paper is the conference version; Brenning 2023 is the IJGIS print year of the 2022 paper above.

## Search log (all 17 November 2026)

Tools: Crossref API (DOI checks), OpenAlex search and abstract fields, WebSearch, WebFetch. Scimago: curl and WebFetch returned a Cloudflare challenge or 403; not bypassed. One WebSearch for Methods in Ecology and Evolution quartile returned aggregator pages saying Q1 but not Scimago itself; not used.

OpenAlex queries (generic words only):
1. spatial machine-learning model diagnostics distance-based approach
2. spatial dependence between training and test sets another pitfall
3. case-crossover design landslide rainfall
4. nested case-control time-varying exposure landslide OR sinkhole OR pipe failure
5. survival analysis time-varying covariates water main pipe failure
6. positional error geocoding exposure misclassification bias attenuation spatial
7. regression calibration geocoding error multiple imputation residential location
8. reporting delay administrative records bias spatial analysis
9. case-time-control design
10. self-controlled case series natural hazard OR landslide OR flood
11. risk set sampling nested case-control Cox model time-varying covariates tutorial
12. case-crossover design bias time-varying exposure trend selection of control periods
13. sinkhole occurrence statistical model time-varying case-control
14. building collapse risk factors case-control
15. precision-recall area under curve confidence intervals small number of positives
16. minimum number of events validation prediction model sample size rare
17. presence-only data species distribution models prevalence unlabeled pseudo-absence
18. negative control outcome exposure spatial analysis residual confounding
19. landslide time-varying survival model Cox hazard rainfall
20. reporting delay nowcasting underreporting event records
21. case-crossover study of heavy rainfall and landslide or sinkhole or road collapse events
22. case-control study of pipe breaks or water main failures conditional logistic regression
23. positive-unlabeled learning landslide OR hazard susceptibility unreported events
24. spatial cross-validation landslide susceptibility optimistic bias random versus spatial
25. positional uncertainty of event locations landslide inventory effect on susceptibility model
26. positive unlabeled learning spatial under-reporting presence-only reporting bias
27. Last three planned queries (AP variability with few positives; spatial block size choice; variogram-matched surrogate fields) timed out and were NOT completed. Block size, AP stability with 30 to 60 positives, and surrogate-field tests are therefore under-searched.

Not covered because of time and a network drop: multiple imputation of event location, regression calibration for geocoding, discrete-time survival in hazard applications, reporting-delay methods for administrative records.
