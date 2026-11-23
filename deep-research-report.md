# Deep Literature Review and Research-Opportunity Assessment for an InSAR–Building-Damage MSc Thesis

## Executive assessment

### Bottom line

Your thesis is **not obsolete, and I did not find a peer-reviewed paper that duplicates the exact Austin experiment**: pre-event InSAR, historical parcel covariates, recorded residential foundation-repair permits, risk-set sampling, spatially separated evaluation, and an explicit test of *incremental* predictive value over a strong non-InSAR baseline. The closest public prior art I found is the UK Space Agency’s Admiral/SatSense/Optera project, which combines satellite ground-motion information, property characteristics and insurance claims and explicitly distinguishes fitting past claims from testing future predictive usefulness. However, its public description is an industry case study rather than a peer-reviewed methods paper and does not disclose an Austin-like spatial validation protocol. citeturn329410search2turn329410search8

At the same time, you should **not claim that you are the first to use InSAR to predict building risk, damage, foundation problems, or property losses**. That territory is now clearly occupied. Recent Q1 work includes building-level PS-InSAR risk classification, differential-deformation mapping, InSAR-derived angular distortion, physical settlement forecasting, fragility functions based on surveyed damage, and urban infrastructure risk mapping. citeturn950479search0turn950479search2turn950479search3turn950479search4turn168950search0

The most important result of this review is that the strongest next step is **not another attempt to squeeze a positive result out of Austin**. Your frozen Austin study has already answered its prespecified question: 24-month LOS trend velocity did not add held-out predictive value, and neither the secondary models nor the 1D CNN produced a robust positive result. That conclusion should stay untouched. Your own final result report gives ΔPR-AUC = −0.00058, 95% interval −0.00197 to +0.00034, conditional-null \(p=0.931\); Test B gives a rate ratio of 1.006, 95% CI 0.867–1.168, \(p=0.967\). It also documents 31 Test-A secondary analyses without a positive PR-AUC change whose 95% interval excludes zero, 11 Test-B analyses without \(p<0.05\), and a negative 1D-CNN increment. fileciteturn0file1

My recommendation is therefore a **two-contribution thesis**:

> **Contribution 1 — rigorous negative/limitations result:** demonstrate, with Alexandria → NYC → Austin, that deformation-derived “risk” is not automatically equivalent to prospective prediction of independently recorded structural outcomes, and quantify how spatial validation, label timing, spatial confounding, missing InSAR coverage and choice of incremental-value statistic alter the evidence.

> **Contribution 2 — independent physics-aligned extension:** move from *regional LOS velocity* toward *building-relevant differential deformation plus hydroclimatic forcing*, and test it on an **independent outcome set**. The preferred independent set is post-2017 Alexandria if Mohamadi and colleagues provide reliable georeferenced events; if that does not materialize, use an independent physically validated deformation/damage dataset rather than re-mining the Austin outcome.

That combination is much stronger scientifically than “try a better neural network on Austin.”

### The single most promising literature bridge

Three lines of work fit together unusually well:

**Burnol et al.** show that expansive-clay motion is fundamentally moisture-driven, nonlinear and seasonal, and that the phase relationship between Sentinel-1 displacement and soil moisture contains information about clay depth/thickness. They validated satellite motion against extensometers and electrical resistivity tomography. citeturn698980search1

**Shahbazi et al.** show that *spatial gradients of motion across individual buildings*, with explicit uncertainty, are more structurally meaningful than a single mean velocity; they validated their differential-deformation map with field observations of cracks/fractures and published the code. citeturn950479search4turn950479search5

**Peduto et al.** show that damage severity is better related to settlement-intensity quantities such as differential settlement, rotation and deflection ratio than simply to an absolute velocity. Their later Dutch work uses more than 700 surveyed masonry buildings to derive fragility functions for those quantities. citeturn867131search1turn867131search2

Taken together, these papers suggest a strong explanation for your Austin null: **the primary Austin variable may be physically too coarse, even if the InSAR itself is measuring real soil behavior.** Your clay seasonal contrast supports that interpretation, but does not prove it. The OPERA product is a single ascending LOS field at roughly 30-m posting, while foundation damage is often driven by *differential* movement across a structure or its immediate surroundings. Your own report also shows that the clay seasonal signal was detectable even though repair prediction was not. fileciteturn0file1

That is a scientifically useful finding, not a failure.

## Search scope, novelty boundary, and journal quality

I searched publisher records, DOI/Crossref-style records, OpenAlex-indexed material, Nature/Springer/Elsevier/MDPI/ASCE pages, PubMed/PMC for the statistical literature, and SCImago for current quartiles. Searches covered forward and backward citation themes around Mohamadi, building-damage fragility, differential settlement, PS-InSAR structural monitoring, insurance claims, expansive clay, urban subsidence, incremental prediction and spatial validation. The review emphasizes work from 2021–17 November 2026 but retains older papers when they establish a method your thesis could directly extend.

This is a **rigorous targeted literature review, not a formal PRISMA systematic review**. I cannot certify that every dissertation, proprietary insurance model, gated Scopus record, or unpublished 2026 manuscript has been found. Consequently, the defensible novelty wording is *“I did not identify a peer-reviewed study with this exact design after a targeted multi-source search”*, not *“no one has ever done this.”*

For quartiles, I use **SCImago 2025** whenever possible so papers are compared against one common, recent year. SCImago derives its indicators from Scopus data. citeturn516552search9 Where a journal has category-dependent quartiles, I state that explicitly. Quartile is a property of the journal/category/year, not evidence that any individual paper is scientifically strong.

### High-relevance Q1/Q2 shortlist

| Paper | Exact bibliographic record and relevance | Ranking status |
|---|---|---|
| **Yang, Mengshi; Huang, Weibin; Li, Menghua; Chang, Ling (2026)** | *From PS-InSAR observations to building-level risk: A data-driven framework for urban structural resilience.* **Remote Sensing of Environment 341, 115454.** DOI: [10.1016/j.rse.2026.115454](https://doi.org/10.1016/j.rse.2026.115454). 106 TerraSAR-X Stripmap images, Kunming; introduces IBUSI data-suitability and IBDS deformation-signature features and classifies settlement/uplift/tilting/torsion/coupled behavior. It does **not** test future repair or damage records. citeturn950479search0turn950479search1 | **SCImago 2025 Q1**, Remote Sensing of Environment, e.g. Soil Science / Computers in Earth Sciences. citeturn651769search1turn651769search0 |
| **Sadhasivam, Nitheshnirmal; Ohenhen, Leonard; Khorrami, Mohammad; Werth, Susanna; Shirzaei, Manoochehr (2025)** | *Building damage risk in sinking Indian megacities.* **Nature Sustainability 8, 1467–1479.** DOI: [10.1038/s41893-025-01663-0](https://doi.org/10.1038/s41893-025-01663-0). >13 million buildings in five cities; InSAR-derived differential settlement/angular distortion. Authors explicitly distinguish risk from proven collapse causation. citeturn950479search2 | **Q1**; Nature Sustainability is a top-quartile sustainability journal in current rankings. |
| **Ohenhen, Leonard O.; Zhai, G.; Lucy, J.; et al. (2025)** | *Land subsidence risk to infrastructure in US metropolises.* **Nature Cities 2, 543–554.** DOI: [10.1038/s44284-025-00240-y](https://doi.org/10.1038/s44284-025-00240-y). 28 US cities, including Austin; Sentinel-1 ~28-m deformation, angular distortion and infrastructure-risk matrix. It maps risk rather than validating against observed repair/damage outcomes. citeturn698980search2turn698980search5 | Nature reports a 2025 JIF of 15.3; I did **not** obtain a directly verifiable SCImago/JCR category quartile from an authoritative accessible record during this search, so I do not assign one here. citeturn516552search1 |
| **Wang, Bing; Guo, Shanchuan; Xia, Junshi; Li, Hairui; Geng, Xiaoyan; Zhang, Xingang; Xia, Zilong; Du, Peijun (2026)** | *Long-term deformation monitoring and potential building damage assessment in resource-based arid urban agglomerations.* **International Journal of Applied Earth Observation and Geoinformation 149, 105271.** DOI: [10.1016/j.jag.2026.105271](https://doi.org/10.1016/j.jag.2026.105271). ALOS-1/PALSAR + Sentinel-1; building-level potential-damage classes, not observed future damage labels. citeturn101479search3turn101479search4 | **SCImago 2025 Q1**, Earth-Surface Processes/Computers in Earth Sciences. citeturn651769search2turn651769search0 |
| **Ma, Peifeng; Zheng, Yi; Zhang, Zhengjia; Wu, Zherong; Yu, Chang (2022)** | *Building risk monitoring and prediction using integrated multi-temporal InSAR and numerical modeling techniques.* **IJAEO 114, 103076.** DOI: [10.1016/j.jag.2022.103076](https://doi.org/10.1016/j.jag.2022.103076). 807 Kowloon + 145 Futian buildings; TerraSAR-X/COSMO-SkyMed/Sentinel-1; forecasts physical settlement through numerical modelling, not future repair records. citeturn950479search3 | **SCImago 2025 Q1.** citeturn651769search2 |
| **Barra, Anna; Reyes-Carmona, Cristina; Herrera, Gerardo; Galve, Jorge Pedro; Solari, Lorenzo; Mateos, Rosa María; Azañón, José Miguel; Béjar-Pizarro, Marta; López-Vinielles, Juan; Palamà, Riccardo; Crosetto, Michele; Sarro, Roberto; Cuervas-Mons, José; Monserrat, Oriol (2022)** | *From satellite interferometry displacements to potential damage maps: A tool for risk reduction and urban planning.* **Remote Sensing of Environment.** DOI: [10.1016/j.rse.2022.113294](https://doi.org/10.1016/j.rse.2022.113294). Uses gradient intensity, angular distortion and field-survey damage inventory; 192 of 633 buildings identified as moderate/high potential damage. citeturn168950search1turn317578search2 | **SCImago 2025 Q1.** citeturn651769search1 |
| **Shahbazi, Saeedeh; Barra, Anna; Gao, Qi; Crosetto, Michele (2024)** | *Detection of buildings with potential damage using differential deformation maps.* **ISPRS Journal of Photogrammetry and Remote Sensing 218B, 57–69.** DOI: [10.1016/j.isprsjprs.2024.10.008](https://doi.org/10.1016/j.isprsjprs.2024.10.008). EGMS 2017–2021 + COSMO-SkyMed, building-specific spatial deformation gradient, Monte-Carlo uncertainty and field crack survey. Code is public. citeturn950479search4turn950479search5 | **SCImago 2025 Q1**, including Computer Science Applications. citeturn651769search4 |
| **Peduto, Dario; Korff, Mandy; Nicodemo, Gianfranco; Marchese, Antonio; Ferlisi, Settimio (2019)** | *Empirical fragility curves for settlement-affected buildings: Analysis of different intensity parameters for seven hundred masonry buildings in The Netherlands.* **Soils and Foundations 59(2), 380–397.** DOI: [10.1016/j.sandf.2018.12.009](https://doi.org/10.1016/j.sandf.2018.12.009). >700 surveyed buildings; differential settlement, rotation and deflection ratio. citeturn867131search1turn867131search2 | **SCImago 2025 Q1**, Civil & Structural Engineering and Geotechnical Engineering & Engineering Geology. citeturn867131search0 |
| **Peduto, Dario; Nicodemo, Gianfranco; Maccabiani, Jos; Ferlisi, Settimio (2017)** | *Multi-scale analysis of settlement-induced building damage using damage surveys and DInSAR data: A case study in The Netherlands.* **Engineering Geology 218, 117–133.** DOI: [10.1016/j.enggeo.2016.12.018](https://doi.org/10.1016/j.enggeo.2016.12.018). High-resolution DInSAR + damage surveys + foundation type; derives fragility relationships. citeturn168950search0turn168950search4 | **SCImago 2025 Q1**, Geology. citeturn651769search3turn651769search5 |
| **Ezquerro, Pablo; Del Soldato, Matteo; Solari, Lorenzo; Tomás, Roberto; Raspini, Federico; Ceccatelli, Mattia; Fernández-Merodo, José Antonio; Casagli, Nicola; Herrera, Gerardo (2020)** | *Vulnerability Assessment of Buildings due to Land Subsidence Using InSAR Data in the Ancient Historical City of Pistoia (Italy).* **Sensors 20, 2749.** DOI: [10.3390/s20102749](https://doi.org/10.3390/s20102749). 227 field-surveyed buildings; 53% had visible damage; empirical fragility mapping. citeturn317578search0 | **SCImago 2025 best quartile Q1**, although category-specific quartiles vary; treat as category dependent. citeturn179184search4 |
| **Liu, Yuzhou; Cao, Wenxi; Shi, Zhongqi; Yue, Qingrui; Chen, Tiandong; Tian, Lu; Zhong, Rumian; Liu, Yuke (2023)** | *Evaluation of Post-Tunneling Aging Buildings Using the InSAR Nonuniform Settlement Index.* **Remote Sensing 15, 3467.** DOI: [10.3390/rs15143467](https://doi.org/10.3390/rs15143467). 147 COSMO-SkyMed scenes, one collapsed plus eight adjacent aging buildings; 3-D settlement plane/inclination index validated against leveling/manual inspection. citeturn168950search2 | **SCImago 2025 Q1** in its listed Earth/Planetary category; other ranking systems/categories can place Remote Sensing differently, so state category/year whenever citing quartile. citeturn179184search1 |
| **Mohamadi, Bahaa; Balz, Timo; Younes, Ali (2020)** | *Towards a PS-InSAR Based Prediction Model for Building Collapse: Spatiotemporal Patterns of Vertical Surface Motion in Collapsed Building Areas—Case Study of Alexandria, Egypt.* **Remote Sensing 12, 3307.** DOI: [10.3390/rs12203307](https://doi.org/10.3390/rs12203307). 124 ascending + 129 descending Sentinel-1 acquisitions, 68 collapses for pattern discovery and four 2019 collapses for validation. citeturn698980search0turn317578search3 | **SCImago 2025 Q1** under the currently listed category; quartile is category/year dependent. citeturn179184search1 |
| **Li, Menghua; Gao, Xinning; Yang, Mengshi; Tang, Li; Tang, Bo-Hui (2024)** | *Evaluating the stability of architectural heritage from the perspective of InSAR: a practical study on Jianchuan Ancient Town.* **Heritage Science 12, 394.** DOI: [10.1186/s40494-024-01488-8](https://doi.org/10.1186/s40494-024-01488-8). 74 TerraSAR-X images; 1,891 buildings; velocity, rotational deformation and time-series behavior. citeturn101479search2 | **SCImago 2024 Q1** in Conservation/Archaeology but **Q2** in Computer Science Applications, Materials Science and several other categories; 2025 page was not yet available in the retrieved record. citeturn797856search0 |
| **Scoccola, S.; Fabbrocino, G.; Sandoli, A. (2026)** | *DInSAR-based fully remote assessment of building damage.* **Journal of Civil Structural Health Monitoring 16, article 39.** DOI: [10.1007/s13349-026-01080-7](https://doi.org/10.1007/s13349-026-01080-7). Integrates remote visual inspection and differential-displacement time series; detailed Rome case study. citeturn168950search3 | **SCImago 2025 Q1.** citeturn797856search1 |
| **Dallari, Veronica; Grassi, Francesca; Mancini, Francesco; Bassoli, Elisa; Vincenzi, Loris (2026)** | *An automated GIS-supported multi-temporal DInSAR approach for estimating foundation settlements and associated uncertainties of buildings in urban areas.* **Developments in the Built Environment 28, 101062.** DOI: [10.1016/j.dibe.2026.101062](https://doi.org/10.1016/j.dibe.2026.101062). Online in 2026 and assigned to the December issue; high-resolution dual-orbit COSMO-SkyMed over ~70 km² in Modena, building-specific rigid-body motion and uncertainty. citeturn101479search0turn103780search1 | **SCImago 2025 Q1** in Architecture, Building & Construction, Civil & Structural Engineering and Computer Science Applications. citeturn797856search2 |
| **Burnol, André; Foumelis, Michael; Gourdier, Sébastien; Deparis, Jacques; Raucoules, Daniel (2021)** | *Monitoring of Expansive Clays over Drought-Rewetting Cycles Using Satellite Remote Sensing.* **Atmosphere 12, 1262.** DOI: [10.3390/atmos12101262](https://doi.org/10.3390/atmos12101262). Sentinel-1 P-SBAS + SMOS soil moisture + extensometers + ERT; directly relevant to Austin clay physics. citeturn698980search1 | **SCImago 2025 Q2** in Atmospheric Science/Environmental Science; JCR 2025 reported as Q3 in the accessible secondary ranking. It is included because it is mechanistically indispensable, not because it meets a strict JCR-Q1/Q2 filter. citeturn516552search2turn516552search3 |
| **Mzungu, Noel Philmon; Negulescu, Caterina; Bertrand, Étienne; Perringaux, Arthur; Boissier, Laurent; Gourdier, Sébastien; Colas, Bastien; Leone, Frédéric; Grandjean, Gilles (2025)** | *A novel clay shrink-swell buildings damage model: From unstructured insurance data to the creation of buildings database, and the proposition of damage severity scale.* **International Journal of Disaster Risk Reduction 127, 105636.** DOI: [10.1016/j.ijdrr.2025.105636](https://doi.org/10.1016/j.ijdrr.2025.105636). 10,325 loss-adjustment reports, 155 manually annotated, LLM/RAG-assisted structuring and a shrink-swell damage-severity scale. No InSAR, but highly relevant to outcome quality and AI. citeturn698980search3 | **SCImago 2025 Q1**, including Geology/Geotechnical Engineering/Safety Research. citeturn516552search4turn516552search5 |
| **Bardet, Jean-Pierre (online 2026; issue 2027)** | *Secondary Compression of Deep Foundations in Carbonate Soils: An InSAR Study of Sunny Isles, Florida.* **Journal of Geotechnical and Geoenvironmental Engineering 153(1).** DOI: [10.1061/JGGEFK.GTENG-15394](https://doi.org/10.1061/JGGEFK.GTENG-15394). >20 high-rises, six-year InSAR, building-specific settlement and long-term foundation-serviceability extrapolation. citeturn101479search1 | **SCImago 2025 Q1**, Geotechnical Engineering & Engineering Geology. citeturn179184search0 |

Two important conclusions follow from this list. First, **Q1 literature is rapidly moving from mean regional velocity toward building attribution, differential displacement, angular distortion, rotations and uncertainty**. citeturn950479search4turn101479search0turn950479search0 Second, surprisingly few papers validate those derived risk quantities against *future independently recorded damage*, rather than concurrent field damage, deformation-derived classes, numerical predictions or risk matrices. That gap is where your work remains strongest. citeturn317578search0turn950479search2turn950479search3

## What the core papers actually did — and where they stopped

The most useful distinction for your thesis is between **forecasting deformation** and **forecasting an independent outcome**. A study can call its output “risk” or “prediction” while still deriving both the predictor and risk label from the same InSAR field. That is scientifically different from asking whether past InSAR predicts later repair, claim or damage records.

| Core study | Data and outcome | Validation and main result | What it did **not** establish — opportunity for you |
|---|---|---|---|
| **Mohamadi et al. 2020, Alexandria** | 124 ascending + 129 descending Sentinel-1 scenes, Jan 2015–May 2019. Asc/desc LOS were combined into vertical motion; 5-m interpolated surfaces and emerging hot/cold-spot analysis. 68 collapses from May 2015–Dec 2018; four whole-building collapses Jan–May 2019 used for detailed validation. citeturn698980search0turn317578search3 | 66/68 historical collapses had a new hot/cold pattern before the incident; all four validation collapses were within 38–75 m of an identified pattern. Critically, the paper itself reports that the resulting vulnerability maps covered more than 50% of the validation area and said prediction accuracy needed improvement. citeturn317578search3 | No large held-out event/control cohort; no strong building/soil baseline; no spatial CV; no false-positive rate over all non-collapse buildings; no prospective PR-AUC/calibration; only four later validation collapses. **This is the cleanest “resume where they stopped” opportunity if post-2017/2019 data become available.** |
| **Peduto et al. 2017 / 2019** | High-resolution DInSAR plus direct damage surveys in Dutch soft-soil areas. Later paper used >700 masonry buildings on shallow/piled foundations and evaluated differential settlement, rotation and deflection ratio. citeturn168950search0turn867131search1 | Empirical fragility functions linked physically meaningful settlement-intensity parameters to surveyed damage. Later work explicitly compared which intensity parameter best represented building damage. citeturn867131search1 | Mainly concurrent/retrospective fragility; not an out-of-area prospective test using future administrative outcomes. Their work strongly suggests your Austin mean velocity is not the best mechanical quantity. |
| **Ezquerro et al. 2020** | Pistoia, Italy; InSAR plus two 2018 field campaigns, 227 buildings, visible external damage. 53% displayed some cracks/damage; most damage was low severity. citeturn317578search0 | Empirical damage probabilities and vulnerability maps were produced from surveyed damage and displacement. citeturn317578search0 | Survey and InSAR are essentially contemporaneous; no future event prediction, no spatial holdout, and building typology was assumed broadly homogeneous when extrapolating. |
| **Burnol et al. 2021** | 183 ascending and 178 descending Sentinel-1 acquisitions, 2016–2019; P-SBAS; 90×90-m cells; SMOS moisture; extensometers; soil sensors; electrical resistivity tomography. citeturn698980search1 | Direct satellite–ground comparison found a few-mm seasonal shrink/swell signal; wavelets identified annual/subannual cycles; displacement–moisture phase was linked to clay depth/thickness and checked against ERT. citeturn698980search1 | Did not predict building damage. Its future-work recommendation is effectively to scale the remote-sensing method to larger areas for shrink-swell risk. **Austin can extend this physical mechanism, but only independent outcome validation would make it more than another hazard map.** |
| **Barra et al. 2022** | ~215k PSI measurement points over ~700 km²; Active Deformation Areas; gradient intensity/gradient vectors/time series; five Granada coastal resorts; 633 buildings. citeturn317578search2 | 192/633 buildings classified moderate/high potential damage; field-survey damage inventory used in ROC evaluation. citeturn317578search2 | Damage was surveyed in the area being mapped; not a future-outcome test. Nevertheless, the gradient feature is far more mechanically aligned than a single pixel’s velocity. |
| **Ma et al. 2022** | TerraSAR-X, COSMO-SkyMed and Sentinel-1 with PS+distributed scatterers; 807 Kowloon and 145 Futian buildings. citeturn950479search3 | 10 Kowloon + 2 Futian buildings reached medium risk; three selected buildings were back-analysed with numerical geotechnical models and settlement projected to 2021. citeturn950479search3 | “Prediction” means numerical prediction of physical settlement/risk, not independent future damage or repair. A future damage-label validation remains open. |
| **Liu et al. 2023** | 147 COSMO-SkyMed scenes, 2013–2022. PS clusters were associated with building footprints; a 3-D settlement plane and inclination angle define a Nonuniform Settlement Index. One collapsed building + eight adjacent aging buildings. citeturn168950search2 | Static-level measurements and manual inspection agreed well with the proposed index. citeturn168950search2 | Validation sample is only nine buildings and one collapse. This is proof of mechanism, not population-level prediction. |
| **Shahbazi et al. 2024** | EGMS Sentinel-1 2017–2021 over Barcelona; measurement points assigned to individual buildings; differential-deformation spatial gradients; COSMO-SkyMed comparison. citeturn950479search4 | 149 EGMS and 155 CSK buildings detected; Monte-Carlo gradient uncertainty ≈0.05 mm yr⁻¹ m⁻¹; field survey checked visible cracks/fractures. Source code is public. citeturn950479search4turn950479search5 | No prospective future-damage cohort. **Its open-source gradient calculation is one of the best methods to borrow if you can obtain sufficiently dense PS points per Austin building.** |
| **Ohenhen et al. 2025** | Sentinel-1-derived deformation at about 28-m resolution, 2015–2021, 28 large US cities; angular distortion between adjacent pixels; building density/exposure risk. citeturn698980search2 | >29,000 buildings were located in high/very-high damage-risk areas across the studied cities. Austin was one of the cities. citeturn698980search2 | No observed building-damage or repair label was used to validate the risk matrix. **Your Austin permit experiment is therefore a valuable empirical check on exactly this family of risk mapping.** |
| **Sadhasivam et al. 2025** | 1,299 Sentinel-1 images over five Indian megacities, 2015–2023 depending on city, >13 million buildings; vertical land motion and differential-settlement/angular-distortion metrics. citeturn950479search2 | 2,406 buildings were estimated to have high current structural-damage risk. The paper explicitly notes that differential subsidence can impair structures but that no direct link to the plotted collapse incidents was proven. citeturn950479search2 | No standardized time-resolved damage registry was available for a real prospective validation. This is almost exactly the empirical gap Austin tries to address. |
| **Yang et al. 2026** | 106 TerraSAR-X Stripmap images, 2017–2019, Kunming. IBUSI measures point number/density/coverage/coherence; IBDS measures deformation magnitude, direction and spatial heterogeneity. citeturn950479search0 | Buildings are classified into settlement, uplift, tilting, torsion and coupled modes, then four risk levels; ~25% showed measurable risk. citeturn950479search0 | Risk categories are derived from InSAR signatures themselves; there is no later repair/damage/claim outcome. **A very strong extension is to ask whether IBUSI/IBDS-like signatures predict external outcomes.** |
| **Mzungu et al. 2025** | 10,325 French insurance loss-adjustment reports, 2000–2021; 155 manually annotated and then scaled with LLM/RAG; building/environment variables and a clay shrink-swell damage severity scale. citeturn698980search3 | Produces a structured damage database and severity model from messy real insurance reports. citeturn698980search3 | No InSAR. **This is highly complementary to your work: it solves the outcome-label problem while Burnol/Shahbazi solve the physical-exposure problem.** |

A particularly important observation comes from the Dutch literature: a later analysis emphasized that **the exact dating of damage onset and the intensity parameter at that time matter when constructing forecasting models**. citeturn317578search4 This directly supports your decision not to treat permit date as crack-onset date.

## What this literature says about your Austin design

### The negative result is informative, but narrower than “InSAR does not work”

The Austin result is internally consistent: the primary metric declined slightly, the confidence interval was tight around a small effect, several spatial nulls did not rescue it, secondaries did not show robust gains, and the deep model also failed to improve PR-AUC. fileciteturn0file1

What it rules out most directly is:

> **A practically material held-out ranking gain from the specific OPERA-derived pre-permit features tested, in the subset of Austin houses with usable measurements and covariates, under your specified models and outcome definition.**

It does **not** rule out:

1. foundation-scale differential deformation;
2. higher-resolution PS/DS building motion;
3. vertical/horizontal decomposition from multiple viewing geometries;
4. moisture-coupled seasonal deformation;
5. a relationship with physical damage rather than permit behavior;
6. small effects below your test’s power;
7. effects in the one-third of eligible events without usable primary-window InSAR.

Your result report says 961 of 2,846 eligible events lacked a usable primary InSAR value, and 1,754 cases entered Test A. That is substantial missingness. fileciteturn0file1

### Your measurement/outcome mismatch is probably the biggest scientific limitation

OPERA DISP-S1 provides displacement in the radar **line of sight** rather than foundation deformation components. A single ascending track therefore cannot independently identify vertical and east–west motion. Your own frozen study acknowledges this. fileciteturn0file1

The structural literature increasingly emphasizes **differential** rather than absolute deformation. Peduto uses differential settlement, rotation and deflection ratio; Barra uses spatial gradients; Liu estimates a building settlement plane and inclination; Shahbazi explicitly computes gradients from points associated with each building; Dallari et al. use dual-orbit high-resolution data to recover building motion and uncertainty. citeturn867131search1turn317578search2turn168950search2turn950479search4turn101479search0

For a typical detached Austin house, a 30-m grid cell may be similar to or larger than the structure itself. That makes it intrinsically difficult to estimate **differential movement across the foundation** from OPERA alone. The fact that you detected a clay-related seasonal amplitude contrast but not a repair-prediction signal is compatible with a scenario in which the satellite sees genuine neighborhood-scale soil motion but not the local deformation that drives structural distress. This is an inference from your result plus the building-mechanics literature, not something the existing data prove. fileciteturn0file1 citeturn698980search1turn867131search1

### Seasonal and hydroclimatic features are physically better motivated than velocity — but Austin can no longer provide a clean confirmatory test of them

Burnol’s instrumented clay site is important because the useful signal was cyclic and phase-related to moisture, not simply a long-term linear trend. citeturn698980search1

A stronger physically informed feature set would therefore contain quantities such as:

\[
A=\text{seasonal amplitude}
\]

\[
\phi=\text{phase lag between soil moisture and displacement}
\]

\[
\nabla v=\text{local spatial gradient of motion}
\]

\[
\Delta v_{\text{building-neighbourhood}}
=\text{building motion minus surrounding motion}
\]

plus uncertainty, temporal coherence, drought/precipitation history and clay properties.

But because you have already examined Austin seasonal amplitude, relative motion, acceleration, windows, lags and multiple models, a new hand-crafted feature found after seeing the negative result would be **exploratory**. It can generate a hypothesis, but it should not be used to rewrite the frozen result. fileciteturn0file1

The clean solution is: **develop the new physics-informed representation using Austin without claiming confirmation, then freeze it and evaluate it on a genuinely independent city/time period.**

### Coefficient tests and likelihood tests do not answer exactly the same scientific question as ΔPR-AUC

This is important for the simulation work Claude started.

Pepe, Kerr, Longton and Wang show that, under conventional risk-model assumptions, the formal null of “no incremental prediction information from \(Y\) given \(X\)” can be expressed as the conditional-risk-factor null \(D\perp Y\mid X\), and they argue that coefficient/likelihood tests can be more statistically powerful than testing changes in performance measures. They also emphasize that **estimation of the magnitude of predictive improvement is more important than repeatedly testing whether the improvement is exactly zero**. citeturn276779search0turn276779search1

Begg, Gonen and Seshan separately warn that naïve inferential comparisons of ROC AUCs derived from nested fitted risk models can be invalid because predictions are correlated and the expanded model has a built-in tendency to exploit the added marker. citeturn276779search2

This does **not** mean you should replace Austin’s frozen PR-AUC result with a coefficient \(p\)-value. The questions differ:

| Statistic | Best interpretation |
|---|---|
| **Held-out ΔPR-AUC / Average Precision** | Does adding InSAR improve ranking of rare future outcomes on held-out data? |
| **Held-out Δlog-likelihood / log-loss** | Does adding InSAR improve probabilistic predictive fit on unseen data? |
| **Likelihood-ratio / coefficient test** | Is InSAR conditionally associated with the outcome under the specified model? |
| **Directional coefficient** | Is that conditional association in a pre-specified physical direction? |
| **Calibration / Brier score** | Are predicted probabilities better calibrated/accurate? |

A predictor can have a statistically nonzero coefficient yet improve ranking by a negligible amount. Conversely, a useful nonlinear prediction signal may have a poor linear coefficient. Therefore your new methodological chapter should treat **conditional association** and **practical incremental prediction** as separate estimands, even if their idealized null hypotheses overlap.

### Your spatial-null concern is real

Spatial cross-validation is well justified: random CV can underestimate error whenever training and test samples remain spatially dependent, and this is specifically documented in remote-sensing classification. citeturn276779search5turn534736search3

Spatial confounding is also a recognized problem when a spatial predictor and unobserved spatial process overlap; Spatial+ is one established approach for separating covariate structure from a spatial smooth. citeturn276779search3turn276779search4

Your Austin report shows the surrogate fields did not reproduce the observed variogram particularly well at several distances: only 58/720 Test-A window-bin checks fell inside the surrogate 95% range, and long-range semivariance was substantially under-represented. fileciteturn0file1 That makes the exact numerical interpretation of the spatial-null \(p\)-value less secure than the raw negative ΔPR-AUC itself.

A classical Conditional Randomization Test can achieve finite-sample Type-I control when the conditional distribution \(X\mid Z\) used for resampling is correctly known; modern distilled CRT methods allow flexible predictive statistics. citeturn534736search0 But Model-X theory commonly assumes independent sampled rows and a valid covariate-generating distribution; it should **not** simply be imported into your spatial risk-set data and called exact. citeturn534736search1

For your thesis, the correct methodological contribution would be:

> simulate spatial fields with known causal/data-generating structures, vary long-range correlation, nonlinear soil confounding, missingness, risk-set sampling and signal strength, then empirically compare Type-I error and power of your conditional variogram null, block permutation, MSR, coefficient/LR tests and held-out predictive statistics.

That is more defensible than arguing from one Austin p-value.

## Where to resume, which papers to combine, and which direction is best

### “Resume from where they stopped”

| Prior work | Explicit/open problem | Concrete extension with your project | Minimum extra data | Novelty / feasibility |
|---|---|---|---|---|
| **Mohamadi 2020** citeturn317578search3 | Vulnerability zones were broad; only four later collapses validated; paper calls for improved prediction accuracy and a more complete risk model. | Freeze a **strictly prospective** Alexandria protocol: pre-event-only InSAR, all eligible buildings/controls, soil/building covariates, spatial CV and calibrated prediction. Compare hot/cold-spot features with modern gradient/time-series features. | ≥~100 accurately dated/geocoded post-2017 collapses would be desirable; cause/structural metadata greatly improves value. | **Very high novelty if data arrive; medium/high data risk.** |
| **Sadhasivam 2025 / Ohenhen 2025** citeturn950479search2turn698980search2 | Sophisticated risk maps but limited direct validation against standardized time-resolved damage records. | Treat Austin permits as an external validation of **differential-settlement risk mapping**, not merely of velocity. Reproduce their angular-distortion concept where resolution permits; validate on independent labels. | Better-res displacement or dense PS points; outcome independent of feature development. | **Strong conceptual continuation; Austin OPERA resolution is the bottleneck.** |
| **Shahbazi 2024** citeturn950479search4 | Differential-deformation tool validated with concurrent field observations, not future damage. | Apply public code to a new city with high-density PS points and ask whether the gradient predicts *subsequent* repair/damage. | EGMS/high-res PS data + dated damage records. | **Excellent, but not straightforward in Texas because EGMS does not cover the US.** |
| **Peduto 2017/2019** citeturn168950search0turn867131search1 | Fragility curves need further external validation and accurate damage onset. | Convert your outcome from binary administrative permit toward severity/onset where possible; test differential settlement/rotation with proper temporal ordering. | Engineer/insurance/inspection labels or detailed post-event records. | **High scientific strength; outcome access is hard.** |
| **Burnol 2021** citeturn698980search1 | Proposed scaling moisture–InSAR phase analysis from an instrumented site to regional shrink-swell risk. | Build a **physics-informed clay-response representation** combining soil moisture, drought/precipitation, clay class and InSAR phase/amplitude; then test it against independent damage labels. | Surface/soil-moisture series + independent deformation or damage validation. | **Excellent fit for Austin mechanism and MSc AI.** |
| **Yang 2026** citeturn950479search0 | Risk level comes from InSAR signatures; external clinical/structural outcome validation remains absent. | Use IBUSI-like quality features and IBDS-like deformation signatures as inputs to an externally validated predictive model. | PS-level point density/coherence/coverage and future outcome records. | **Strong AI/remote-sensing contribution; requires higher-resolution PS data.** |
| **Mzungu 2025** citeturn698980search3 | Strong damage labels from insurance text but no InSAR exposure. | Combine their NLP damage-severity construction with InSAR/hydroclimate features if similar claims can be accessed. | Insurance/loss-adjuster reports or an equivalent inspection corpus. | **Potentially strongest Q1 project, but data permissions are the biggest risk.** |
| **Dallari et al. 2026** citeturn101479search0turn103780search1 | Building motion/uncertainty identified, but no future structural outcome. | Add independent prospective damage/repair labels and ask if uncertainty-aware building motion predicts them. | High-res dual-orbit SAR + building footprints + dated outcomes. | **Excellent research gap, expensive data.** |

### Paper combinations that are genuinely complementary

| Combination | Technically meaningful synthesis |
|---|---|
| **Burnol 2021 + Shahbazi 2024 + your Austin framework** | Build a *moisture-conditioned differential-deformation* representation: wavelet/harmonic phase and amplitude relative to soil moisture + building-level spatial gradients + uncertainty. Evaluate against subsequent repair labels with your risk-set/spatial-holdout design. This joins physical forcing, structural deformation and independent outcomes rather than simply stacking features. citeturn698980search1turn950479search4 |
| **Mohamadi 2020 + Yang 2026 + your NYC/Austin validation discipline** | Replace broad ArcGIS hot/cold zones with IBUSI quality screening and IBDS-style building signatures; freeze features before looking at new Alexandria collapses; evaluate with all-at-risk controls, spatial CV, AP/log-loss and calibration. citeturn317578search3turn950479search0 |
| **Peduto 2019 + Sadhasivam 2025 + your administrative outcome study** | Use physically grounded intensity measures—differential settlement, rotation, deflection/angular distortion—then determine whether their *prospective* values predict independently recorded outcomes. This directly connects engineering fragility with city-scale Earth observation. citeturn867131search1turn950479search2 |
| **Mzungu 2025 + Burnol 2021 + Shahbazi 2024** | Highest-quality “full chain”: NLP-derived verified shrink-swell damage severity → moisture-driven soil deformation → building-level differential InSAR. It would allow ordinal damage prediction rather than a noisy binary permit proxy. citeturn698980search3turn698980search1turn950479search4 |
| **Pepe 2013 + spatial CRT/Spatial+ + your Austin simulations** | A methodological paper on *what does “incremental information” mean in spatial rare-event prediction?* Compare association tests with out-of-sample ranking/probability metrics under spatial confounding and imperfect \(X\mid Z\) resampling. citeturn276779search1turn276779search3turn534736search0 |
| **Ohenhen/Sadhasivam + Austin** | Their published risk mapping says differential settlement identifies potentially vulnerable urban buildings; Austin provides a rare external administrative outcome. A negative validation is scientifically useful because it tests whether a hazard/risk map translates into observed downstream action. citeturn698980search2turn950479search2 |

### Ranked thesis directions

Scores are my assessment on a 1–5 scale, not empirical measurements.

| Direction | Novelty | MSc AI fit | Feasible in months | Risk of unusable/null result | Q1/Q2 paper potential | Overall |
|---|---:|---:|---:|---:|---:|---|
| **A. Negative-result + methodological thesis across Alexandria/NYC/Austin** | 4 | 5 | **5** | Low | 3–4 | **1st now** |
| **B. Prospective post-2017 Alexandria replication** | **5** | 4 | 3 if data arrive, 1 if not | Medium/high | **4–5** | **1st if Mohamadi supplies good data** |
| **C. Physics-informed seasonal + differential deformation + moisture, independently validated** | **5** | **5** | 3 | Medium | **5** | **Best scientific extension** |
| **D. Cross-city/domain-shift modelling** | 3–4 | **5** | 3 | High because outcomes differ across cities | 3–4 | Secondary |
| **E. Multi-source high-resolution deformation + verified structural damage/insurance outcomes** | **5** | **5** | 1–2 without partner/data access | High access risk | **5** | Do only with confirmed data |
| **F. Keep tuning Austin until something becomes positive** | 1 | 3 | 4 | Severe scientific/p-hacking risk | 1 | **Do not do** |

**Direction A** is the safest thesis because you already possess the data, analysis and reproducibility record. Its originality is methodological rather than “new positive predictor.” The paper becomes much stronger if you build a general simulation benchmark rather than merely presenting three city case studies.

**Direction B** becomes my preferred empirical extension if the Alexandria author supplies a sufficiently large, accurately geocoded post-2017 inventory. Mohamadi’s paper itself leaves a clear next step: its four-event validation was tiny and its vulnerability layer was geographically broad. citeturn317578search3

**Direction C** has the strongest intellectual link to the modern Q1 literature. It directly addresses what Austin could not: moisture-driven seasonality and differential movement rather than a single regional velocity. Burnol, Peduto, Shahbazi and Yang together provide a coherent methodological foundation. citeturn698980search1turn867131search1turn950479search4turn950479search0

**Direction D**, domain adaptation, sounds attractive for Computer Engineering, but Alexandria collapse, NYC collapse/administrative events and Austin repair permits are not the same label-generating process. A model that “transfers” between them may mostly learn administrative/domain differences. I would not make it the primary contribution unless you can harmonize outcomes.

**Direction E** could plausibly support a strong Q1 submission, but only if the data are secured first. Do not design a thesis around commercial TerraSAR-X/COSMO-SkyMed or insurer damage reports unless access is confirmed.

## Recommended primary plan and fallback

### Recommended primary thesis

I would title the research program along the lines of:

**From InSAR Hazard Mapping to Prospective Structural Outcomes: Spatially Validated Tests of Incremental Predictive Value and Physically Informed Building Deformation**

The contribution statement should be:

> **This thesis evaluates whether remotely sensed deformation features that are commonly used to infer building risk translate into independently observed future structural outcomes. It first quantifies the failure of regional LOS trend velocity to improve spatially held-out prediction of administrative repair outcomes, then evaluates the statistical conditions under which incremental-value claims are reliable, and finally tests a pre-specified, physically aligned deformation representation on an independent dataset if suitable labels are obtained.**

That claim is narrower and stronger than “AI predicts building collapse using satellite data.”

### Work that can be done now

**Keep Austin frozen.** No replacement primary metric, no reinterpretation of a new coefficient test as the original outcome. Your final Austin report remains the record. fileciteturn0file1

Build a **methods benchmark** with no further Austin outcome mining. Simulate data under:

- no InSAR effect, correctly specified baseline;
- nonlinear soil confounding;
- long-range hidden spatial confounding;
- weak/moderate/large InSAR effects;
- feature effects through regional velocity versus local gradients;
- MNAR-like InSAR missingness linked to construction/activity;
- varying spatial ranges;
- risk-set case-control sampling;
- label delay between latent damage and administrative permit;
- varying event prevalence.

For every scenario, compare **Type-I error, power, bias and estimated predictive gain** for conditional variogram null, within-block permutation, MSR, coefficient/LR test, held-out Δlog-loss and held-out ΔAverage Precision. Spatial+ is worth including as a regression-based confounding control, and a CRT-style test should only be labelled valid when your generator genuinely supplies or accurately estimates \(X\mid Z\). citeturn276779search3turn534736search0

Pre-specify two separate hypotheses:

\[
H_{\text{assoc}}:
Y\perp X_{\mathrm{InSAR}}\mid Z
\]

and

\[
H_{\text{utility}}:
\Delta \text{predictive performance}
\leq \delta_{\min}
\]

where \(\delta_{\min}\) is a practically meaningful improvement chosen *before* seeing a new validation set. This directly follows the distinction emphasized by Pepe et al.: test conditional risk-factor information cleanly, but estimate prediction improvement and compare it to a useful threshold rather than obsessing over “anything greater than zero.” citeturn276779search1

### Preferred independent empirical extension

If Mohamed/Mohamadi provides new Alexandria data, use **post-2017 events not previously used for feature selection**.

Minimum viable dataset:

- precise building coordinates or parcel/building IDs;
- actual collapse/serious-damage date;
- ideally collapse cause and severity;
- ≥100 events is a sensible practical goal, although formal minimum should come from simulation-based power using actual spatial prevalence;
- a complete at-risk building population, not just cases;
- pre-event Sentinel-1 coverage;
- building footprints;
- basic building age/height/use where possible;
- soil/geology;
- ascending and descending tracks if geometry permits.

Before opening outcome-linked InSAR, freeze:

**Primary exposure:** one building-relevant metric—preferably differential deformation/rotation or an IBDS-like signature, not a list of 30 candidate features.

**Primary temporal rule:** for example, all observations ending ≥3 or 6 months before collapse.

**Primary comparator:** building/geology/location baseline.

**Primary evaluation:** spatially separated and temporally prospective held-out log-loss + AP estimation, with association inference reported separately.

**Negative controls:** randomly shifted event dates/locations, outcomes unrelated to settlement if available, and regions/buildings where the deformation mechanism is implausible.

**Independent physical check:** GNSS/leveling or at least agreement of asc/desc-derived motion where available.

The stop/go criterion should be simple: **if the new inventory is too small, poorly located, lacks credible event dates, or substantially overlaps the events used in feature development, do not call it a prospective replication.**

### If Alexandria data do not arrive

Then the thesis should remain **A + methodological extension**, not become an endless city search.

A strong final structure would be:

**Study 1:** Alexandria discovery and limitations.

**Study 2:** NYC prospective non-replication.

**Study 3:** Austin large frozen independent-outcome test.

**Study 4:** simulation benchmark explaining when common spatial/incremental-value procedures succeed or fail.

**Synthesis:** why hazard mapping, structural deformation and administrative damage outcomes should not be treated as interchangeable validation targets.

That is a coherent MSc thesis even without a positive result.

### If you can obtain one new technical resource

Do **not** spend it on a bigger neural network first.

Spend it on **higher-resolution building-level deformation**.

Shahbazi’s published code is directly useful:  
[GitHub — detecting-differential-deformation](https://github.com/saeedehshahbazi/detecting-differential-deformation) citeturn950479search4

If you can obtain sufficiently dense PS/DS points from Sentinel-1 SLC/CSLC processing or commercial X-band data, calculate within-building/near-building gradients and uncertainty. If most detached houses have fewer than the minimum number of reliable points needed to estimate a gradient, stop and report that the sensor/data product is not suitable for foundation-scale inference rather than forcing interpolation.

### Publication targets

A **Q1 submission is plausible but not guaranteed**; publication depends on the finished contribution, not just the journal quartile.

For a strong new remote-sensing method with independent validation, **Remote Sensing of Environment** and **ISPRS Journal of Photogrammetry and Remote Sensing** are Q1 but have a high bar: a single-city negative result alone is unlikely to be enough. citeturn651769search1turn651769search4

For a physically grounded Earth-observation application with strong validation, **International Journal of Applied Earth Observation and Geoinformation** is a credible Q1 target. citeturn651769search2

For a foundation/settlement/damage contribution, **Engineering Geology** or **Soils and Foundations** are Q1 and fit the mechanistic framing well. citeturn651769search3turn867131search0

For structural monitoring, **Journal of Civil Structural Health Monitoring** is currently Q1 by SCImago and would be a plausible outlet if the contribution centers on structural-health validation rather than remote-sensing methodology itself. citeturn797856search1

A rigorous negative result is publishable **when the negative finding closes an important empirical gap, the study has meaningful sensitivity to plausible effects, and the limitations are quantified**. Your Austin study has several of those ingredients—large historical population, frozen analysis, real outcomes, planted-signal simulations, multiple controls—but the spatial-null mismatch, missing InSAR coverage and outcome/measurement mismatch need to be part of the paper’s central argument rather than buried in limitations. fileciteturn0file1

## Priority reading, milestones, and what to tell your supervisor

### Reading order

The most efficient reading sequence is:

1. **Mohamadi et al. 2020** — read methods §§2.2–2.5 and validation/results carefully. It establishes exactly where the Alexandria work stopped: 68 main cases, four later validation cases, 38–75-m validation distances, and vulnerability zones covering >50% of the test area. [DOI](https://doi.org/10.3390/rs12203307) citeturn317578search3
2. **Peduto et al. 2019** — understand why differential settlement, rotation and deflection ratio are more meaningful than raw velocity. [DOI](https://doi.org/10.1016/j.sandf.2018.12.009) citeturn867131search1
3. **Burnol et al. 2021** — understand moisture–deformation phase lag, wavelets and instrumented validation of expansive clay. [DOI](https://doi.org/10.3390/atmos12101262) citeturn698980search1
4. **Shahbazi et al. 2024** — study building-specific differential gradients and uncertainty; inspect the public code. [DOI](https://doi.org/10.1016/j.isprsjprs.2024.10.008) citeturn950479search4
5. **Sadhasivam et al. 2025** — see how a state-of-the-art Q1 paper goes from subsidence to building risk while explicitly acknowledging the missing direct damage link. [DOI](https://doi.org/10.1038/s41893-025-01663-0) citeturn950479search2
6. **Yang et al. 2026** — use IBUSI/IBDS as inspiration for quality-aware building signatures, not as an external risk label. [DOI](https://doi.org/10.1016/j.rse.2026.115454) citeturn950479search0
7. **Dallari et al. 2026** — building attribution, dual-orbit motion and uncertainty; especially important if you obtain higher-resolution data. [DOI](https://doi.org/10.1016/j.dibe.2026.101062) citeturn101479search0
8. **Mzungu et al. 2025** — shows what a much stronger damage label looks like and how AI/NLP can contribute without pretending text labels are physical measurements. [DOI](https://doi.org/10.1016/j.ijdrr.2025.105636) citeturn698980search3
9. **Pepe et al. 2013** — essential before interpreting Claude’s coefficient/log-likelihood simulations. [DOI](https://doi.org/10.1002/sim.5727) citeturn276779search0turn276779search1
10. **Dupont, Wood & Augustin 2022** and **Roberts et al. 2017** — spatial confounding and spatial validation. [Spatial+ DOI](https://doi.org/10.1111/biom.13656); [CV DOI](https://doi.org/10.1111/ecog.02881). citeturn276779search4turn276779search5
11. **Liu et al. 2022, distilled CRT** — useful only after understanding the assumptions behind \(X\mid Z\) resampling. [DOI](https://doi.org/10.1093/biomet/asab039) citeturn534736search0turn534736search5
12. **Karasiak et al. 2022** — remote-sensing-specific evidence for spatially independent validation. [DOI](https://doi.org/10.1007/s10994-021-05972-1) citeturn534736search3

### Milestones and stop/go rules

**Immediately:** freeze the Austin result permanently; create a literature matrix separating deformation prediction, damage association and prospective external-outcome prediction. Your `AUSTIN_RESULT.md` is already sufficiently detailed to anchor that chapter. fileciteturn0file1

**Next few weeks:** finish the methods simulation, but add the difficult nonlinear-soil scenario rather than comparing statistics only under easy nulls. Report both false-positive rate and power. Do not select the “best statistic” based only on which one finds Austin significant.

**In parallel:** wait for the Alexandria author response and investigate whether the 2017+ inventory contains enough precise events for a fresh validation.

**Go for Alexandria** only if the new events are genuinely later/independent, accurately geocoded and sufficiently numerous.

**Go for the building-scale Austin extension** only if you can demonstrate adequate PS/DS density per house and preferably obtain an independent physical validation source. If that requirement fails, do not interpolate a 30-m regional field and call it foundation-scale motion.

**Go for insurer/engineer labels** only after obtaining actual permission/access. Mzungu demonstrates why such labels would materially improve the thesis, but data-access risk is substantial. citeturn698980search3

### Ten questions to take to your supervisor

1. **Do you agree that the frozen Austin negative result should remain a main thesis contribution rather than be replaced by a post-hoc positive metric?**
2. **Should the thesis’s central claim be “validation of InSAR-derived risk against independent outcomes” rather than “prediction of building collapse”?**
3. **If we obtain post-2017 Alexandria collapses, would you consider a strictly frozen prospective replication the preferred final experiment?**
4. **Would you support making differential deformation/rotation rather than LOS mean velocity the next physical hypothesis, based on Peduto, Shahbazi and Yang?**
5. **Is a methodological chapter comparing spatial incremental-value tests sufficiently aligned with the Computer Engineering/AI degree?**
6. **Should conditional association and incremental predictive utility be declared as two distinct research questions?**
7. **What minimum external validation would you require before we claim that a satellite feature reflects foundation-scale structural distress—GNSS, leveling, engineer survey, insurance damage severity, or something else?**
8. **Would the department accept a thesis whose strongest empirical conclusion is negative if the methods, independent validation and failure analysis are rigorous?**
9. **Do we have institutional collaborators who could provide structural inspection or insurance claims data, or access to TerraSAR-X/COSMO-SkyMed?**
10. **Which publication path should drive the last phase: remote sensing (RSE/IJAEO/ISPRS), geotechnical engineering (Engineering Geology/Soils and Foundations), or structural health monitoring?**

### Evidence-based answer to “what exactly should I do next?”

**Do not change Austin’s primary result. Do not keep trying architectures until one becomes significant.**

Use the next stage to make the thesis answer a broader and more important question:

> **When does InSAR-derived ground deformation actually translate into independently observed future building damage or repair, and how should that incremental information be validated under spatial dependence?**

Complete the statistical benchmark now. At the same time, pursue the new Alexandria inventory. If it arrives with sufficient quality, make **prospective Alexandria** the independent confirmatory experiment and combine Mohamadi’s spatiotemporal concept with the newer building-level differential-deformation/quality ideas of Shahbazi and Yang. citeturn317578search3turn950479search4turn950479search0

If Alexandria does not become usable, write the thesis around the **Alexandria → NYC → Austin evidence chain plus a rigorous methodological simulation study**, and make the central result that hazard maps and real-world predictive utility are not equivalent.

If you can secure higher-resolution PS/DS or engineering/insurance labels, add a physics-informed extension based on **Burnol + Peduto + Shahbazi**: soil-moisture phase/seasonality + differential building deformation + independently observed damage. That is, in my assessment, the most scientifically original route and the one with the strongest Q1 potential. citeturn698980search1turn867131search1turn950479search4

The strongest thesis is therefore **not one that finds a positive result at all costs**. It is one that shows, with increasingly rigorous experiments, exactly which step in the chain

**satellite displacement → soil/foundation deformation → structural damage → administrative record**

is supported by evidence, which step is not, and what additional measurements are required before researchers can legitimately call an InSAR building-risk map a predictive structural-health model.