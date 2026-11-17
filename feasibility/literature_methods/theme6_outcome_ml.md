# Theme 6: Outcome records and machine-learning studies that use InSAR to predict building damage

Search date: 17 November 2026. Searcher: subagent. Plain-English notes; no em dashes.

## Method notes that affect how far to trust this file

- Scimago could not be queried. scimagojr.com sits behind a Cloudflare challenge (HTTP 403 to a script and to the fetch tool) and I did not try to bypass it. So no quartile below is "looked up on Scimago". Where a web search returned a Scimago-derived figure from a third-party page, I give it as a secondary hint only. Every venue that is not an IEEE journal is therefore marked "quartile not verified". The venue filter must be checked by hand before the papers are cited as filter-passing.
- OpenAlex stopped answering after the first batch of queries ("Rate limit exceeded", free budget used up). Semantic Scholar rate-limited too. I did not register for a key, because that needs an e-mail address and the brief forbids it. After that point the search used web search, Crossref (DOI checks) and direct open-access PDFs. This means the search was less exhaustive than planned, especially for sub-questions (b) and (e). Treat "nothing found" below as "nothing found with reduced tooling".
- DOI check: all main-table DOIs were confirmed in Crossref (title, journal, year). Exception noted per row.

## Short answers

**(a) ML or statistics that use InSAR features to predict building damage, 2018 to 2026.**
I found no paper that trains a supervised model on InSAR-derived features against a real damage record (survey, claims, inspection) with a held-out, spatially separated test, and compares it with a no-InSAR baseline. What exists falls in four groups:
1. Empirical fragility curves (one InSAR settlement parameter against surveyed damage class, maximum-likelihood fit on the same buildings): Peduto 2019, Ezquerro 2020, Nappo 2021. Label is a survey; InSAR precedes the survey; no hold-out, no no-InSAR baseline.
2. Machine learning where the InSAR velocity is the thing being modelled, not a predictor of damage: Xu 2023 (Lanzhou). The "risk" classes are built from InSAR rates and ancillary layers, so the label is InSAR-derived (CIRCULAR, flagged below). No damage record is used.
3. Retrospective checks at known collapse sites, no model and no controls: Rodriguez-Antunano 2023 (four collapses, one is Champlain Towers South, Miami; Sentinel-1 ascending only for Miami), Alizadeh 2024 (four collapse sites, Tehran, 15 months of images before each collapse). Mohamadi 2020 (already assessed) is the larger version.
4. Unsupervised anomaly detection on PS time series, no damage label: Kuzu 2023 (IEEE JSTARS, abstract only).
Earthquake damage classifiers (InSAR coherence plus survey labels, for example Karimzadeh 2018, the 2025 Myanmar and 2025 arXiv causal-Bayes papers) use co-event or post-event SAR, so motion is not "before the label" in the sense of the thesis. I list them under "Identified, not read".
A caution on one result I saw in a conference paper: Wikby, Haaf and Karstunen 2025 (Gothenburg, ISGSR) use a random forest, but it emulates a physics-based subsidence model; InSAR is only a validation target and building damage is computed by a strain method. It is not an InSAR-to-damage model.

**(b) Ground motion linked to administrative or insurance damage records, 2020 to 2026, beyond the "already assessed" list.**
Very little. I found no peer-reviewed paper that joins InSAR motion to claim-level or municipal foundation-damage records. Closest items: Nappo 2021 (Como, 600 buildings, 2019 damage survey, Cosmo-SkyMed; abstract only), Argyriou 2024 (Cyprus, ground-truth visits to deformed structures, label is deformation, not claims), and the French drought-claims work that uses a soil-moisture index and claims but no InSAR (Barthelemy 2024 is already assessed; a HESS 2025 follow-up with trees is in "Identified, not read"). The CLAYEXP project (Sentinel-1 plus claims plus CatNat decrees, municipal exposure index) and the ESA GEO-SHIELD pilot with an insurer are described on project pages only; I found no results paper. Dutch foundation-damage work with InSAR (FunderMaps, Gouda, SkyGeo) appears in grey literature and conference papers only. Nothing found for UK subsidence claims or Belgium beyond Drougkas 2020 (already assessed). The BGS GeoClimate Shrink-Swell user guide (NORA, 2026) is a hazard dataset guide, not a validation against claims.

**(c) Full-text reading of the four papers.**
- Ezquerro 2020: full text read (open, PMC). Details below.
- Peduto 2019: full text read (open post-embargo author copy at TU Delft repository). Details below.
- Ma 2022: open access on the publisher site, but the publisher page was not retrievable by my tools (fetch refused or failed). Abstract only. Cannot report validation design in detail.
- Yang 2026: a green copy exists at University of Twente (research.utwente.nl, file listed as the published PDF, 51.6 MB, Taverne licence). The server returned HTTP 403 to my fetch. I did not try to get round that. Abstract only, from the repository page.

**(d) City-scale risk maps without a damage record (Ohenhen 2025, Sadhasivam 2025).**
Both use angular distortion from InSAR vertical motion between adjacent points, then bin it. Ohenhen: beta over a 25-year linear extrapolation, four classes in degrees (low below 0.02, medium 0.02 to 0.04, high 0.04 to 0.12, very high above 0.12 degrees, roughly 1/2900, 1/1400, 1/480 in ratio form), then combined with building density. Sadhasivam: total angular distortion over the InSAR period (and 10, 30, 50-year linear projections), four classes 0.0006, 0.002, 0.008 rad (the figure labels them 1/1500, 1/500, 1/120), from Skempton and MacDonald, Polshin and Tokar, and a California damaged-homes study; uniform vulnerability assumed for all buildings. Both authors say in their own text that they could not validate against damage (Ohenhen: lack of spatially resolved building damage data in US cities; Sadhasivam: calls for a standardised, georeferenced damage record). Lenardon Sanchez 2024 (Land) uses a third scheme (0.03%, 0.06%, 0.2% over 30 years, scaled by period length) and also has no damage validation. I found no later peer-reviewed paper that validates or criticises these thresholds. A search found only press coverage of Ohenhen. The thresholds also differ across the three papers by up to a factor of about 3 at the low end, which the papers do not reconcile. Ohenhen states the critical value varies with construction, foundation and soil.

**(e) Negative or null results.**
No paper framed as "InSAR did not relate to damage or claims" passed my filter. Partial and weak findings:
- Ezquerro 2020 (Pistoia): the damage-probability bins do not rise cleanly with the share of damaged buildings: 52, 39, 48, 64, 68 percent damaged across five probability classes, validated on the same data used to fit. The authors say the extreme bins are under- and over-estimated.
- Peduto 2019: authors warn that InSAR covers about 5 years but damage may have accumulated over decades, which may overstate the damage class tied to a given settlement.
- Sciortino 2023 (L'Aquila, GIScience and Remote Sensing; abstract only via a search summary): finds a correlation of post-seismic velocity with damage intensity, but also finds no spatial correlation between neighbouring points and curve shapes independent of damage intensity.
- Conference only: a 2026 ICSMGE paper reports no clear correlation between PS data and crack development at one church (Hochheim) on shrink-prone clay (from a search summary; not read).
- Bonaldo 2023 (Rome, one palace): authors say velocity alone is not reliable as a stability index; time series were needed.
Publication bias is likely: I could not search it properly.

## Paper table

Venue column: "QNV" = quartile not verified (Scimago blocked). Secondary hints (third-party pages, not Scimago): Remote Sensing of Environment Q1 (2024); IJAEOG Q1 (a search summary quoting a Scimago category page, Computers in Earth Sciences, Scopus data March 2026); Soils and Foundations Q1 (2024, aggregator); Remote Sensing Q1 (aggregator). These are not verified.

### Sub-question (c): four papers

**1. Yang, Huang, Li and Chang 2026.** From PS-InSAR observations to building-level risk: A data-driven framework for urban structural resilience. Remote Sensing of Environment 341, 115454. DOI 10.1016/j.rse.2026.115454.
- DOI check: VERIFIED (Crossref: title, journal, 2026).
- Venue: QNV (aggregator hint Q1).
- Read depth: abstract only (repository page). Full-text PDF at research.utwente.nl returned 403.
- What it does: Kunming, 106 TerraSAR-X images 2017 to 2019. Two indices per building: a data-reliability score for the PS data and a deformation index (magnitude, direction, spatial variability). Five deformation modes (settlement, uplift, tilting, torsion, coupled) and four risk levels. About 25% of buildings show measurable risk. From the abstract no damage record, held-out set or baseline is mentioned, and the risk class comes from InSAR alone, so it would be CIRCULAR as an outcome (unconfirmed without full text).
- Limitations: not read.
- Data needed: building-level PS density, a TerraSAR-X-class stack, footprints.
- Use for us: the per-building reliability idea (how many PS a building has) could be a stratifier. Needs full text before any judgement. No design uses it directly: our pixels are 30 m, not building-level PS.

**2. Ma, Zheng, Zhang, Wu and Yu 2022.** Building risk monitoring and prediction using integrated multi-temporal InSAR and numerical modeling techniques. IJAEOG, November 2022, article 103076. DOI 10.1016/j.jag.2022.103076.
- DOI check: VERIFIED.
- Venue: QNV (hint Q1).
- Read depth: abstract only (OpenAlex abstract). Publisher page not retrievable.
- What it does: Persistent and distributed scatterers from TerraSAR-X, COSMO-SkyMed and Sentinel-1 over Kowloon (Hong Kong) and Futian (Shenzhen). Angular distortion at district scale flags 10 of 807 buildings (Kowloon) and 2 of 145 (Futian) as medium risk. Back-analysis gives geological and hydrological conditions. Time series at three buildings (Lucky, BMW, Jingli) are simulated by a numerical groundwater-loading model that "agreed well" with measurements, then extended to 2021. Validation is InSAR against model, not against damage (from the abstract and a search summary).
- Limitations: not read.
- Data needed: multi-sensor PS time series on buildings, groundwater and loading data.
- Use for us: none for the three designs (building-level numerical modelling).

**3. Ezquerro et al. 2020** (Ezquerro, Del Soldato, Solari, Tomas, Herrera and co-authors; the full author list was not checked). Vulnerability Assessment of Buildings due to Land Subsidence Using InSAR Data in the Ancient Historical City of Pistoia (Italy). Sensors 20(10), 2749. DOI 10.3390/s20102749.
- DOI check: VERIFIED.
- Venue: QNV.
- Read depth: full text (PMC open copy).
- What it does: Sentinel-1 (86 ascending, 93 descending, SqueeSAR, Tuscany Region system) plus COSMO-SkyMed (60 ascending images Jan 2015 to Mar 2018; 34 descending Feb 2015 to Dec 2017), decomposed to vertical and E-W. Two field campaigns on 26 June and 1 August 2018 record damage on 227 buildings, chosen "randomly through several inspection tracks", outside-only inspection, mostly historic masonry, damage only G0 to G2. Damage grouped to binary (G1+G2 vs none). Empirical lognormal fragility curve P(damage given vertical velocity) fitted per sensor, then velocities interpolated (IDW, 5 m) to probability classes and a damage map, then loss maps (OMI value database, 5% loss ratio).
- Validation design: InSAR ends before the survey (March 2018 vs June 2018). Validation of the damage-probability map is the damaged share per probability bin, done on the same buildings used to fit the curve ("the frequency curves definition and validation was performed using the same data"). Table 3: bins 0-20, 20-40, 40-60, 60-80, 80-100 percent probability contain 52, 39, 48, 64, 68 percent damaged buildings. No hold-out, no spatial split, no no-InSAR baseline, no discrimination metric. The Sentinel-1 versus COSMO-SkyMed comparison is InSAR-to-InSAR (RMSE 0.37 and 0.36 cm/yr).
- Limitations (stated, Section 5 and conclusions): extreme probability bins under- and over-estimate damage; one construction type assumed for all buildings although foundations range from 12th-century masonry to recent concrete; subsidence only began in 2015, so little accumulated damage; damage mostly facade-only and very low; "final damage probability ... must be reevaluated and validated with updated displacement and damage campaigns"; recommends yearly campaigns, inner inspection, crackmeters.
- Data needed: per-building PS velocity (CSK-class density), a building damage inventory with grades, cadastral map.
- Use for us: design 3 only as a descriptive comparison curve. The empirical-fragility step could be an explainable secondary (probability of a repair permit versus velocity), but same-data fitting would have to be replaced by the existing blocked cross-validation. Needs a building-level velocity and a clean outcome, which design 3 has; designs 1 and 2 have street-level or 250 m outcomes, too coarse for building-level curves.

**4. Peduto, Korff, Nicodemo, Marchese and Ferlisi 2019.** Empirical fragility curves for settlement-affected buildings: Analysis of different intensity parameters for seven hundred masonry buildings in The Netherlands. Soils and Foundations (April 2019; volume and pages not checked). DOI 10.1016/j.sandf.2018.12.009.
- DOI check: VERIFIED (title, journal, 2019).
- Venue: QNV (hint Q1).
- Read depth: full text (TU Delft repository, author version, CC BY-NC-ND, embargo expired).
- What it does: four Dutch urban areas on soft Holocene clay and peat, 706 masonry buildings (180 shallow-founded, 526 piled). TerraSAR-X stripmap stack 2009 to 2014 (285 images in the Schiedam test area, 133 ascending, 162 descending), vertical settlement profiles from PS; three settlement-related intensity parameters (differential settlement, rotation, deflection ratio; a fourth, horizontal strain or tilt, is discussed as future work). Visual facade damage surveys in April-May 2015 (310 buildings in one area), February-March 2016 (81 buildings in Zaanstad) and others, graded D0 to D5, D4 and D5 merged. Fragility curves are lognormal CDFs with one common dispersion, fitted by maximum likelihood, separately for shallow and piled foundations. InSAR accuracy was tested against 83 levelling benchmarks (PS within 2 m buffer, 2009-2014).
- Validation design: InSAR period (to 2014) precedes the surveys (2015-2016). No hold-out, no spatial blocking and no no-InSAR baseline in the text I read. The curves are compared with published Zhang and Ng (2005) curves, which is a plausibility check, not a test. Differential settlement was best of the parameters tried, by judgement of fit ("easier and more precise estimation").
- Limitations (stated, Sections 7 and 8): InSAR covers about 5 years while damage may have accumulated over decades (houses 35 to 100 years old), which "may have led to an overestimation of the damage category"; no dates of damage onset, age, repairs or maintenance; damage visible only from outside, one grade per building; no sagging versus hogging distinction; curves "once further validated" could be used; calls for exact dating of damage onset relative to the InSAR window and a homogeneous building sample.
- Data needed: per-building PS (X-band stripmap density), surveys with grade, foundation type.
- Use for us: design 3. The two lessons that bear on the clay design are the mismatch between the InSAR window and the time damage built up (the repair-permit date is a dated outcome, which partly removes it) and foundation-type stratification. Method itself (fragility curve) is not a held-out test.

### Sub-question (a): ML and statistical models with InSAR features

**5. Xu, Wu, Zhang, Liu and Jing 2023.** Land Subsidence Monitoring and Building Risk Assessment Using InSAR and Machine Learning in a Loess Plateau City: Lanzhou, China. Remote Sensing 15(11), 2851. DOI 10.3390/rs15112851.
- DOI check: VERIFIED. Venue: QNV. Read depth: full text (MDPI open PDF), risk-assessment section read closely, rest skimmed.
- What it does: SBAS-InSAR 26 Oct 2014 to 12 Dec 2021. A random-forest step weighs causes of subsidence; factor weights (InSAR rate 0.498, cumulative subsidence 0.213, precipitation 0.076, faults 0.062, lithology 0.054, building height 0.036, river 0.035, railway 0.026) are combined by overlay and cut into five classes by natural breaks. "Building risk" is read off the overlay with building height.
- CIRCULAR FLAG: the largest weights are InSAR rate and cumulative InSAR subsidence, and the classes come from the same inputs. There is no damage record, no held-out set, no baseline. Not a damage predictor.
- Limitations: static hazard, assumes no change in building density or pumping (stated in Section 4.4). No damage validation.
- Use for us: none, except as an example to avoid (label built from the predictor).

**6. Kuzu, Bagaglini, Wang and Dumitru 2023.** Automatic Detection of Building Displacements Through Unsupervised Learning From InSAR Data. IEEE JSTARS. DOI 10.1109/JSTARS.2023.3297267.
- DOI check: VERIFIED. Venue: IEEE journal. Read depth: abstract only (Semantic Scholar).
- What it does: LSTM autoencoder with soft-DTW loss on EGMS persistent-scatterer series in Rome; detects trend, noise and step anomalies; compared with other unsupervised methods. From the abstract the evaluation uses injected or labelled anomaly types, not damage records.
- Limitations: not read.
- Data needed: PS time series (EGMS Level 2a type).
- Use for us: none directly; EGMS series are Europe only. Possibly a way to flag step-like changes in a PS series (not applicable to OPERA at 30 m).

**7. Rodriguez-Antunano, Martinez-Sanchez, Cabaleiro and Riveiro 2023.** Anticipating the Collapse of Urban Infrastructure: A Methodology Based on Earth Observation and MT-InSAR. Remote Sensing 15(15), 3867. DOI 10.3390/rs15153867.
- DOI check: VERIFIED. Venue: QNV. Read depth: full text for method, results headings and Discussion/Conclusions; case details skimmed.
- What it does: Sentinel-1 StaMPS PS time series; per tile, year-to-year change of the accumulated displacement trend; pixels beyond mean plus 2 sigma of the tile are flagged as vulnerable. Four known collapses: Line 12 Mexico City Metro (Mar 2015 to May 2021), Caprigliola bridge, a building in Font Nova (Penyiscola), and Champlain Towers South in Miami (ascending only, 9 Oct 2016 to 21 June 2021, no descending data).
- Validation: retrospective, at the four collapse sites only. There are no non-collapse control sites, so the false-alarm rate cannot be estimated beyond the authors' note that many flagged points are vegetation false alarms (for one case only 5 flagged areas are in built-up land). No baseline, no held-out set. InSAR precedes the event.
- Limitations (stated, Section 5): the 2-sigma cutoff "could not be verified" for Miami without descending images; the yearly comparison needs large data volumes; suggests testing LOS decomposition and machine learning "to discern potential false risks".
- Data needed: Sentinel-1 PS series (StaMPS), several years before the event.
- Use for us: design 2 (Miami site is the same type of event) as a descriptive probe. It shows that a single collapse site flagged by a per-tile trend filter has no estimate of how often such flags occur elsewhere, which is exactly what the matched-control design supplies.

**8. Alizadeh, Maghsoudi, Managhebi and Azadnejad 2024 (journal volume 13, published 2025).** Collapse Hotspot Detection in Urban Area Using Sentinel-1 and TerraSAR-X Dataset with SBAS and PSI Techniques. Land 13(12), 2237. DOI 10.3390/land13122237.
- DOI check: VERIFIED. Venue: QNV. Read depth: partial (abstract, dataset and limitations sections).
- What it does: Tehran, four known collapse sites (Abshenasan Blvd, Shariati St, Karimkhan St, Moghadam Sq), 108-image Sentinel-1A stacks covering the 15 months before each collapse, plus a 36-image TerraSAR-X stack for one site. Compares PSI (StaMPS) and SBAS (MintPy) at the collapse sites. Says SBAS finds "behavior patterns indicative of collapse" near the sites.
- Validation: visual at four known sites; no controls, no metric. InSAR precedes the event.
- Limitations (stated, Section 3.4): unwrapping errors in MintPy, sparse points in StaMPS, TerraSAR-X cost.
- Use for us: design 1 (street-level collapses; same weakness in locating the exact point). A reminder that the 15-month pre-event window and a few sites do not give a test.

**9. Diao, Wu, Chen, Yang et al. 2019.** Identifying the Cause of Abnormal Building Damage in Mining Subsidence Areas Using InSAR Technology. IEEE Access. DOI 10.1109/ACCESS.2019.2956094.
- DOI check: VERIFIED. Venue: IEEE journal. Read depth: abstract only.
- What it does: seven RadarSat-2 images (Oct 2013 to Mar 2014), Fengfeng coal field; deformation pattern follows the F29 fault; attributes damage at one village to fault activation by theory and a material simulation.
- Use for us: none (mining, single village).

### Sub-question (b): administrative, survey and claims records

**10. Nappo, Peduto, Polcari, Livio, Ferrario, Comerci, Stramondo and Michetti 2021.** Subsidence in Como historic centre (northern Italy): Assessment of building vulnerability combining hydrogeological and stratigraphic features, Cosmo-SkyMed InSAR and damage data. International Journal of Disaster Risk Reduction, 2021, article 102115. DOI 10.1016/j.ijdrr.2021.102115.
- DOI check: VERIFIED (title, journal, 2021). Venue: QNV. Read depth: abstract only (Semantic Scholar; the paper is closed).
- What it does: InSAR vertical settlement correlates with groundwater level more than with compressible-unit thickness; then fragility curves from two InSAR-derived intensity parameters (differential settlement, relative rotation), for masonry and reinforced concrete. Differential settlement relates better to damage levels. The 2026 IAEG conference paper by Nappo and Michetti (outside the filter) says the 2019 survey covered 600 buildings in D1 to D4 by crack width, and that damaged buildings sit where cumulative vertical motion exceeded 10 mm in the years before 2019.
- Limitations: not read.
- Use for us: design 3 as a comparison of effect size type (settlement versus damage class). Needs full text.

**11. Argyriou, Prodromou, Theocharidis, Fotiou et al. 2024.** Integration of Multi-Source Datasets for Assessing Ground Swelling/Shrinking Risk in Cyprus: The Case Studies of Pyrgos-Parekklisia and Moni. Remote Sensing 16(17), 3185. DOI 10.3390/rs16173185.
- DOI check: VERIFIED. Venue: QNV. Read depth: partial (abstract, methods and validation lines).
- What it does: Sentinel-1 coherence change (normalised coherence difference), Sentinel-2 NDVI, DEM derivatives and soil/geology layers in a multi-criteria decision analysis (weighted overlay) for swelling-shrinking zones 2016 to 2022. Accuracy of the MCDA map: overall 72.4%, kappa 0.66, against PS-InSAR results and ground-truth locations with verified deformed structures from site visits (from the abstract and Figure 17 caption).
- Notes: the target is zones of swelling/shrinking, partly defined by PS-InSAR itself, so the PS agreement is partly circular. Ground truth is a set of visited structures, not a damage register. No held-out split is described in the parts I read.
- Use for us: design 3 only as context: shows coherence, not velocity, can serve as a clay-activity indicator where PS is sparse.

### Sub-question (d): thresholds and city-scale maps

**12. Ohenhen, Zhai, Lucy, Werth, Carlson, Khorrami, Onyike, Sadhasivam, Tiwari, Ghobadi-Far, Sherpa, Lee, Zehsaz and Shirzaei 2025.** Land subsidence risk to infrastructure in US metropolises. Nature Cities 2, 543-554. DOI 10.1038/s44284-025-00240-y.
- DOI check: VERIFIED by Crossref search result (title, Nature Cities, 8 May 2025); direct DOI call failed once. Venue: QNV. Read depth: full text of the open PDF; threshold and limitations passages read closely.
- What it does: Sentinel-1 2015 to 2021 vertical land motion for 28 US cities. Angular distortion beta from adjacent-point differences over an assumed 25-year linear projection; four classes (low below 0.02 degrees, medium 0.02 to 0.04, high 0.04 to 0.12, very high above 0.12); combined with Microsoft building footprint density into a risk level. More than 29,000 buildings are in high or very high risk areas.
- Thresholds: from earlier studies and standard geotechnical practice (refs in paper: Burland and Wroth, Skempton and MacDonald, Boscardin and Cording). The authors add that critical beta varies with construction, foundation and soil: framed or load-bearing brick up to 0.19 degrees; brick-infill frames moderate to severe above 0.38 degrees; structures on sand or soft clay may fail above 0.02 degrees.
- Limitations (stated, Discussion): "lack of spatially resolved building damage data in US cities" limits any cross-validation or correlation with documented damage; calls for building-scale beta, foundation type and soil metadata; linear 25-year extrapolation.
- Data needed: ascending and descending vertical motion at about 100 m, footprints.
- Use for us: design 3 (Austin-type clay cities are in their set). Their lack-of-damage-data statement is the gap the thesis addresses. The thresholds are for engineered tilt, not for seasonal clay cycling, and they are cumulative, so they do not map onto a 24-month trend velocity.

**13. Sadhasivam, Zhai, Ohenhen, Shirzaei et al. 2025 (author list not verified in full).** Building damage risk in sinking Indian megacities. Nature Sustainability 8, 1467-1479. DOI 10.1038/s41893-025-01663-0.
- DOI check: VERIFIED. Venue: QNV. Read depth: full text of open PDF; methods threshold passage and Discussion read.
- What it does: Sentinel-1 vertical motion for Delhi, Mumbai, Bengaluru, Chennai, Kolkata; beta per building footprint (Google Open Buildings, 13.27 million footprints) times the InSAR period, then 10, 30, 50-year linear projections; classes 0.0006, 0.002, 0.008 rad (figure labels 1/1500, 1/500, 1/120); risk matrix of beta class by footprint density on a 0.2 km grid; uniform vulnerability assumed.
- Threshold sources named: Skempton and MacDonald; Polshin and Tokar (USSR code, 1/500 as the upper bound for moderate to severe damage); a study of thousands of damaged California homes for 1/120 (severe).
- Limitations (stated): vulnerability data "not available", so uniform vulnerability; cumulative beta reflects only partial distortion over the InSAR period, not the building's life; sublinear motion may change projections; news-media collapse counts 1989 to 2023 are only cautiously linked ("we call for creating a comprehensive building damage record that is spatially explicit, temporally resolved and standardized"); the authors also note not all cracks mean settlement.
- Use for us: design 3. Useful as a statement of what the field says is missing.

**14. Lenardon Sanchez and Farias 2024.** Multi-Decadal Land Subsidence Risk Assessment at Major Italian Cities by Integrating PSInSAR with Urban Vulnerability. Land 13(12), 2103. DOI 10.3390/land13122103.
- DOI check: VERIFIED. Venue: QNV. Read depth: partial (abstract, threshold section, results).
- What it does: ERS, Envisat, COSMO-SkyMed and EGMS Sentinel-1 for Rome, Bologna, Florence over 30 years. Total angular distortion classes: low below 0.03%, medium 0.03 to 0.06%, high 0.06 to 0.2%, very high 0.2% or more (0.2% is called a typical threshold for high probability of severe damage); thresholds scaled in proportion for a sub-period (for Sentinel-1, 1/6 of the 30-year values). Hazard crossed with Urban Atlas land use and population at block level. High to very high risk land: 36.15, 11.44 and 0.43 km2.
- No damage validation in the parts read.
- Use for us: shows a third, different threshold set, which supports treating thresholds as untested.

### Sub-question (e) and other items found

**15. Bonaldo, Caprino, Lorenzoni and da Porto 2023.** Monitoring Displacements and Damage Detection through Satellite MT-InSAR Techniques: A New Methodology and Application to a Case Study in Rome (Italy). Remote Sensing 15(5), 1177. DOI 10.3390/rs15051177.
- DOI check: VERIFIED. Venue: QNV. Read depth: partial (abstract and conclusions).
- What it does: one XVI-century palace, COSMO-SkyMed 2011 to 2019 SBAS; seasonal versus irreversible components (moving average, ARX regression on temperature); damage identification compared with on-site inspection information.
- Limitations (stated): velocity alone is "not reliable ... as an index for assessing building stability"; no transducer data to validate; temperature correlation weakened by noise and by non-structural scatterers.
- Use for us: a caution for design 3 that seasonal clay motion and a trend velocity are different quantities.

**16. Sciortino, Marini, Guerriero and Mazzanti 2023.** Satellite A-DInSAR pattern recognition for seismic vulnerability mapping at city scale: insights from the L'Aquila (Italy) case study. GIScience and Remote Sensing. DOI 10.1080/15481603.2023.2293522.
- DOI check: VERIFIED (title, journal, 2023). Venue: QNV. Read depth: secondary (search-result summary of the abstract). Not read in full.
- What it does (per summary): post-seismic A-DInSAR in the historic centre, geostatistics and cluster analysis against building damage intensity and reconstruction; reports a correlation of average post-seismic velocity with damage intensity, but neighbouring points lack consistent velocities and curve shapes look independent of damage intensity or reconstruction.
- Use for us: a partial null-type finding on point-level spatial coherence; earthquake damage, not subsidence.

**17. Scoccola, Fabbrocino and Sandoli 2026.** DInSAR-based fully remote assessment of building damage. Journal of Civil Structural Health Monitoring. DOI 10.1007/s13349-026-01080-7.
- DOI check: VERIFIED. Venue: QNV. Read depth: abstract only (Crossref); full text redirected to a login cookie page.
- What it does: workflow combining web-based inspection and structural-feature tools with DInSAR for damage assessment; one real building in Rome.
- Use for us: none for the three designs (single-building workflow).

## Found, outside the venue filter

- Wikby, Haaf and Karstunen 2025. Modeling Subsidence and Building Damage in Central Gothenburg Using Machine Learning. 9th ISGSR proceedings, DOI 10.3850/GRF-25280825_ISGSR-080-P041-CD. Conference. Random-forest metamodel of a creep model, validated against InSAR and a bellow-hose; damage by a strain method; no damage record. Read (4 pages).
- Nappo and Michetti 2026. Monitoring Subsidence and Building Vulnerability in Como, Italy: 30 Years of InSAR. IAEG 2026 proceedings, DOI 10.59490/6ad29a388073d51c18bd0093. Conference. 600 buildings, 2019 survey D1-D4. Read.
- Liu and Xiong 2026. Auditing observability bias in InSAR-derived subsidence exposure estimates (Chao Phraya delta). Research Square preprint, DOI 10.21203/rs.3.rs-10530259/v1. Preprint. Argues that missing or weakly observed InSAR cells change exposure counts; states no dense site-level validation. Skimmed. Relevant to the "unobserved cells" problem in design 3 (houses with no coherent pixel).
- Li and Xu 2025. Multi-class Seismic Building Damage Assessment from InSAR Imagery using Quadratic Variational Causal Bayesian Inference. arXiv 2502.18546. Preprint; earthquake. Not read.
- EGU 2026 abstracts: EGMS+ machine-learning projection of subsidence and structural damage (DOI 10.5194/egusphere-egu26-18341); EGMS differential-subsidence risk workflow (10.5194/egusphere-egu26-6608); Toulouse shrink-swell with two Sentinel-1 pipelines (EGU26-21004). Abstracts, not read beyond summaries.
- ICSMGE 2026 paper on drought-induced settlement at heritage sites (church at Hochheim): reported "no clear correlation between PS data and crack development" (from a search summary; title and authors not captured).
- Verberne et al. 2023, JGR Earth Surface, DOI 10.1029/2022JF007031 (South Flevoland, InSAR on objects without foundation; clay shrinkage by groundwater lowering; "1 m phreatic drop = 1 cm subsidence in 5 years"). Journal paper but no damage record; only the key points and metadata were read. Not placed in the main table.
- BGS GeoClimate Shrink-Swell user guide, NORA 2026 (OR/25/076): report, not a journal paper.
- Peduto, Nicodemo, Ferlisi IAHS 2020 (Zaanstad): conference series; Nicodemo 2020 already assessed.
- Cigna, Esquivel Ramirez and Tapete 2021, Remote Sensing 13(23), 4800 (Sentinel-1 PSI and SBAS accuracy against GNSS and levelling): journal, but about measurement accuracy, no damage; read the first page only.

## Identified, not read

- Karimzadeh, Matsuoka and Miyajima 2018, Sequential SAR Coherence Method for the Monitoring of Buildings in Sarpole-Zahab, Iran, Remote Sensing 10, 1255 (DOI 10.3390/rs10081255). Coherence-based earthquake damage; found via a search summary. Not read.
- Foroughnia, Macchiarulo, Milillo, Whitworth, Gavin and Giardina 2025, InSAR-based assessment of post-earthquake building reconstruction: The Nepal case study, IJAEOG, DOI 10.1016/j.jag.2025.104883. Crossref confirms; open, but publisher page not retrievable. Relevance low (reconstruction after an earthquake).
- Barthelemy-type follow-up in HESS 2025 (hess-29-2321-2025): soil-moisture drought index versus French subsidence claims with trees; no InSAR. Download failed.
- CLAYEXP project (spaceclimateobservatory.org/clayexp) and ESA GEO-SHIELD (business.esa.int/projects/geo-shield): project pages; no results paper found.
- Atmosphere 2021, 12(10), 1262: Sentinel-1 P-SBAS on clay shrink-swell at Chaingy against extensometers (measurement validation, no damage).
- Alizadeh and co-authors' related PSI work; Mohamadi 2020 is already assessed.
- Dutch grey literature: KCAF position paper 2023, FunderMaps, SkyGeo/ISSMGE Geo-resilience 2023 paper (Scoular, already assessed), Gouda municipality slides listing InSAR as supplementary research for pile foundations.
- Sinkhole and bridge papers (Nature Communications 2025 long-span bridges with InSAR availability; Dead Sea sinkhole exceedance NHESS 2026): hazard inventories, not building damage. Not read.
- Remote Sensing 2020, 12(23), 3976 (PS-InSAR plus ML for road surface motion): label is road profile, not buildings; not read.

## Search log (17 November 2026)

OpenAlex (works search, from 2018 or 2019; stopped answering partway):
1. InSAR machine learning building damage prediction subsidence
2. InSAR building collapse risk machine learning
3. InSAR clay shrink-swell insurance claims subsidence damage
4. InSAR foundation damage funderingsschade
5. InSAR building damage inspection records statistical relationship
6. InSAR deformation does not correlate with building damage
7. retrait-gonflement des argiles InSAR sinistres
8. clay shrink-swell InSAR building damage claims
9. drought subsidence insurance claims InSAR houses
10. foundation damage Netherlands InSAR building
11. unsafe buildings register InSAR
12. InSAR building damage survey comparison masonry damage level
13. InSAR derived angular distortion building damage classification
14. building damage prediction random forest InSAR settlement damaged buildings field survey
15. Yang Huang Li Chang Kunming building InSAR
16. building collapse prediction InSAR Kunming
17. InSAR sinkhole collapse building inventory prediction
18. InSAR derived deformation features predicts building damage not significant
(Later OpenAlex queries returned "Rate limit exceeded". Also DOI lookups for the four sub-question (c) papers succeeded before that.)

Crossref: DOI checks for every main-table DOI; bibliographic searches for Alizadeh, Orihuela (no useful hit), Nepal, Scoccola, Lenardon, Kuzu, Nappo, Karimzadeh, Mohamadi, Ohenhen.
Semantic Scholar (DOI abstracts only, limited by 429): Kuzu, Diao, Nappo, Mohamadi, Foroughnia (none), Land 2025 review, GeoAI paper.

Web search (standard or extended mode):
- InSAR clay shrink-swell subsidence insurance claims houses relationship Sentinel-1 study
- InSAR ground motion and building damage records no significant relationship validation of subsidence building risk maps
- machine learning InSAR building damage label inspection records subsidence vulnerability random forest spatial cross-validation
- InSAR building damage machine learning predict damaged buildings subsidence Remote Sensing 2024 2025 features velocity classifier survey labels
- Ohenhen 2025 Nature Cities building damage subsidence angular distortion threshold critique or validation
- InSAR foundation damage Netherlands funderingsschade woningen gemeente schadegegevens bodemdaling
- InSAR vertical land motion angular distortion building damage risk validation with observed damage records city-scale
- Sentinel-1 InSAR subsidence compared with building damage complaints or repair records
- InSAR building collapse risk prediction logistic regression collapsed buildings inventory case-control
- InSAR expansive clay soil swelling shrinking Texas, Oklahoma, Colorado houses foundation damage
- InSAR peat or clay Netherlands wooden pile foundation damage municipality damage reports
- satellite InSAR drought subsidence France clay sinistres or claims Sentinel-1 municipalities CatNat
- InSAR time series post-earthquake damage intensity lack of spatial correlation (L'Aquila)
- InSAR PS velocity no correlation with observed building damage cracks survey
- Scimago quartile look-ups (four searches): returned third-party aggregator figures only.

Fetches: Twente repository page (Yang 2026; PDF 403), TU Delft repository (Peduto PDF, read), PMC (Ezquerro, read), Nature PDFs (Ohenhen, Sadhasivam, read), MDPI PDFs (Xu, Bonaldo, Rodriguez-Antunano, Alizadeh, Lenardon, Argyriou, Cigna, read), ISGSR PDF (Wikby), Research Square PDF (Liu), Springer, IEEE Xplore, ScienceDirect, Scimago (blocked or login redirects; not bypassed).

## What this means for the thesis (labelled as my own view, not from the papers)

- The gap the thesis fills is real in this search: no paper found tests InSAR against a dated damage record with spatially blocked held-out validation and a no-InSAR baseline. The two risk-map papers say so themselves.
- The only validation actually used in this literature is fitting a curve of damage grade on InSAR settlement and checking it on the same buildings (Ezquerro, Peduto). Those results are descriptive.
- Three limitations recur and apply to the three designs: InSAR window shorter than damage history (Peduto), outside-only or facade-only damage grading (Peduto, Ezquerro), and no control sites in collapse case studies (Rodriguez-Antunano, Alizadeh).
