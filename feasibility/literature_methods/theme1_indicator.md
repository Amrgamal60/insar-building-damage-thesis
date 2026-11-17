# Theme 1: The indicator (InSAR quantities used to relate ground motion to damage or failure of individual buildings)

Date of search: 2026-11-17. Important limit on reading depth: almost every publisher site (Elsevier, MDPI, Nature, Wiley/AGU, SSRN, the Granada repository) refused automated fetches (HTTP 403, bot checks or login redirects). I did not try to get around that. So nearly all papers below were read at abstract level (from Crossref, Semantic Scholar or search snippets), and some only through secondary descriptions. Every "Limitations" cell says whether it is quoted from an abstract or not stated in the material I could reach. No full-text limitation sections were read.

## Short answers

**a) Building-scale indicators.**
- Published building-scale indicators are mostly gradient-type: differential settlement, relative rotation / angular distortion, spatial deformation gradient per building, and a "uniform + tipping + curvature" decomposition. They are used in empirical fragility curves or in gradient-intensity classes.
- Evidence for "gradient beats velocity" is thin in what I could read. The closest is Nappo et al. 2021 (Como, CosmoSkyMed): between two gradient-type parameters, differential settlement related better to damage level than relative rotation. That is not a comparison with plain velocity. I did not find, at abstract level, a paper that directly tests a gradient indicator against mean LOS velocity on the same damaged-building set. Zhang et al. 2025 (Engineering Geology, "comparative study on intensity parameters from MT-InSAR") looks like the paper that does this, but I could not read it (see "Identified, not read").
- Barra et al. 2022 (RSE) is the main validated gradient method: gradient intensity map from Sentinel-1 persistent-scatterer displacements, tested by ROC analysis against a field damage inventory (Granada, 633 buildings; the ROC/AUC values were not visible to me).
- Shahbazi et al. 2024 (ISPRS JPRS) computes a per-building gradient from EGMS (Sentinel-1) measurement points and from CosmoSkyMed; the quoted gradient standard deviation is 0.05 mm per year per metre (secondary description). A field survey of visible cracks was used as check.
- Data needs: every method needs several coherent points on or around each building. Sentinel-1 (EGMS) gives few points per building, X-band (CosmoSkyMed, TerraSAR-X) more. Alizadeh 2024 reports that TerraSAR-X found extra collapse-prone points near a collapse site that Sentinel-1 did not. I found no paper that works with 30 m multilooked products at building scale; at 30 m a house is about one pixel, so a within-footprint gradient cannot be formed (my inference, not a published statement).

**b) Precursors of collapse.**
- Buildings: nothing demonstrates a reliable precursor. The Surfside (Champlain Towers South) Sentinel-1 study (Zanjani et al. 2024) reports no displacement signal before collapse. Rodríguez-Antuñano 2023 proposes a trend-homogeneity indicator and tests it on four collapsed structures (Surfside and a partial collapse in Peniscola among them) with no control set that I could see. Alizadeh 2024 (three areas with collapse history) finds SBAS shows collapse-indicative patterns better than PSI; no detection rate in the abstract.
- Bridge: Morandi (Milillo et al. 2019, already assessed) is contested by Lanari et al. 2020 (independent SBAS and tomography analysis of the same CosmoSkyMed data).
- Tailings dams (method transfer only): Brumadinho precursor deformation is reported by Gama 2020 (acceleration for a short period near failure, SBAS and PSI, 26 Sentinel-1B images), Grebby 2021 (ISBAS; timing "foreseeable"; the 40 day figure comes from press coverage, secondary) and Das et al. (arXiv preprint; spectral method flags risk at least five months before). One event, retrospective, no controls in any of them as far as the abstracts say.
- Lead times and detection rates on many cases, with non-collapsed controls: nothing found.

**c) Independent record of many damaged buildings.**
- Citing-paper search done on the four seed papers (OpenAlex id for each; 70, 63, 28 and 18 citing works; 168 unique). Relevant 2022 to 2026 items found that test InSAR against a damage or collapse record: Barra 2022 (field damage inventory, ROC), Ohenhen and Shirzaei 2022 (Lagos; 152 building failures since 2005, links subsidence to foundation damage; abstract only), Pan et al. 2026 (IEEE JSTARS; PS subsidence and tilt plus building attributes in ML models, cracked-building labels, accuracy 0.81 to 0.91, recall 0.71 to 1.00, on-site inspection), Du et al. 2024 (Turkey 2023 earthquake, checked against optical imagery), Zheng et al. 2026 (IEEE JSTARS; no outcome validation stated in abstract), Alizadeh 2024 (three collapse areas).
- Of these, only Pan 2026 reports held-out-style accuracy; I did not see (abstract level) spatial blocking, a no-InSAR baseline, or an explicit "motion before the outcome" design in any of them.
- Two 2026 Earth's Future items (a Comment and a Reply on Fouad et al. 2025) cite the Fouad paper; not read.

**d) Vertical / east-west decomposition.**
- Papers: Di Carlo 2021 (J. Civil Struct. Health Monit.) uses vertical and E-W components of PS displacements for building damage assessment; Du et al. 2025 (Struct. Control Health Monit.) builds 3D building displacement from LOS using domain-knowledge constraints because SAR is insensitive to N-S motion; Du et al. 2024 (IJDRR) measures horizontal deformation for portfolio damage after the Turkey earthquake. Brouwer and Hanssen 2021 (IGARSS, outside the filter) argue that the two-geometry decomposition can be biased.
- I found no paper that tests whether adding E-W (versus vertical or LOS only) improves a damage indicator against a damage record. For the Austin-type design (one ascending track, LOS only) the published literature gives no direct evidence either way.

## Paper table (passes the venue filter; most recent first within sub-question)

Venue quartiles were looked up on scimagojr.com journal pages through search-result snippets (the Scimago site itself returned a Cloudflare block to direct fetches). Year shown is the latest year visible in the snippet (2025 unless stated). All DOIs checked against Crossref on 2026-11-17: VERIFIED (title, journal, year match).

### Sub-question a (indicators)

| Field | Zheng et al. 2026 |
|---|---|
| Citation | Zheng, Liu, Yu, Deng et al. 2026. Integrated Multipattern Building Risk Assessment Based on MT-InSAR Measurements. IEEE JSTARS. 10.1109/jstars.2026.3731596 |
| DOI check | VERIFIED |
| Venue | IEEE journal |
| Read depth | abstract only |
| What it does | Fits a dominant inclination plane per building; splits InSAR deformation into uniform, tipping and curvature components; rates each against engineering thresholds, then combines. Applied to two reclaimed areas in Hong Kong. No outcome validation stated in the abstract. |
| Limitations | Not stated in the abstract; full text not read. The abstract says single-indicator methods "capture only limited aspects" of deformation. |
| Data needed | Several PS per building (to fit a plane and curvature); resolution not stated in abstract. |
| Use for us | Design 3 only as a way to define per-house tilt/curvature features, but at 30 m one pixel per house is too few points (my note). |

| Field | Pan et al. 2026 |
|---|---|
| Citation | Pan, Xu, Zhou, Li et al. 2026. Artificial intelligence-based assessment of large-scale building safety risk in non-disaster scenarios by integrating InSAR-derived... IEEE JSTARS. 10.1109/jstars.2026.3673968 |
| DOI check | VERIFIED (title truncated in Crossref output; journal and year match) |
| Venue | IEEE journal |
| Read depth | abstract only |
| What it does | Combines building census data, PS-InSAR subsidence and tilt, and remote-sensing environment variables; trains SVM, RF, LightGBM, MLP, CRNN, TabNet to detect cracked buildings. Reports accuracy 0.91/0.81/0.90 and recall 0.71/0.72/1.00 (LightGBM, three area types); on-site inspection. Split scheme (random or spatial) not stated in the abstract. |
| Limitations | Not stated in the abstract. |
| Data needed | PS subsidence and tilt per building, building attributes, crack labels. |
| Use for us | Design 3: an example of adding InSAR-derived tilt and subsidence to a non-InSAR feature set for damage labels. Whether motion preceded the label is not stated. |

| Field | Shahbazi et al. 2024 |
|---|---|
| Citation | Shahbazi, Barra, Gao, Crosetto 2024. Detection of buildings with potential damage using differential deformation maps. ISPRS J. Photogramm. Remote Sens. 10.1016/j.isprsjprs.2024.10.008 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, ISPRS JPRS journal page, SJR 3.694) |
| Read depth | secondary source (search-result descriptions; publisher page refused) |
| What it does | Per-building spatial gradient of deformation from EGMS measurement points; Monte Carlo estimate of gradient uncertainty (0.05 mm/yr/m); applied to Barcelona 2017 to 2021; compared with a CosmoSkyMed dataset (149 vs 155 buildings flagged); field survey for visible cracks. Code on GitHub (per the description). |
| Limitations | Not read. |
| Data needed | EGMS (Sentinel-1) measurement points associated with each building; X-band for denser points. |
| Use for us | Design 3 could borrow the gradient uncertainty idea; needs several points per building footprint. |

| Field | Nappo et al. 2021 |
|---|---|
| Citation | Nappo, Peduto, Polcari, Livio et al. 2021. Subsidence in Como historic centre (northern Italy): Assessment of building vulnerability combining hydrogeological and stratigraphic features, and Cosmo-SkyMed InSAR data. Int. J. Disaster Risk Reduction. 10.1016/j.ijdrr.2021.102115 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, IJDRR journal page, Safety Research) |
| Read depth | abstract only |
| What it does | Empirical fragility curves for masonry and reinforced-concrete buildings using two InSAR-derived intensity parameters (differential settlement, relative rotation) against in-situ damage severity. States differential settlement "related better to distinct damage levels". No velocity comparison, no held-out test in the abstract. |
| Limitations | Not stated in the abstract. |
| Data needed | X-band CosmoSkyMed PS, several points per building. |
| Use for us | Evidence on which gradient-type parameter relates to damage; design 3 would need multiple points per house. |

| Field | Barra et al. 2022 |
|---|---|
| Citation | Barra, Reyes-Carmona, Herrera et al. 2022. From satellite interferometry displacements to potential damage maps: A tool for risk reduction and urban planning. Remote Sens. Environ. 10.1016/j.rse.2022.113294 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, RSE journal page, SJR 4.266; Geology and Soil Science rows) |
| Read depth | secondary source (abstract snippets; repository PDF refused) |
| What it does | Semi-automatic gradient intensity map, gradient vectors with time series and a potential-damage map from wide-area PS displacement maps; Granada province; 192 of 633 buildings flagged moderate or high; about 15% of area high or very high gradient class; ROC test against a damage inventory from field surveys. |
| Limitations | Not read. |
| Data needed | PS displacement map over the city with enough density for local gradients. |
| Use for us | Design 3 or 2: a validated gradient-to-damage method with ROC test; AUC values not seen. |

| Field | Di Carlo et al. 2021 |
|---|---|
| Citation | Di Carlo, Miano, Giannetti, Mele et al. 2021. On the integration of multi-temporal synthetic aperture radar interferometry products and historical surveys data for buildings structural monitoring. J. Civil Struct. Health Monit. 10.1007/s13349-021-00518-4 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, SJR 1.005, J. Civil Struct. Health Monit. page) |
| Read depth | abstract only (plus a search-snippet note that it uses vertical and E-W components) |
| What it does | Integrates DInSAR time series and mean velocity with historical sources, 3D models and GIS positioning of reflectors; increasing-accuracy approaches; two case studies (Italy). Not a statistical validation on many buildings. |
| Limitations | Not stated in the abstract. |
| Data needed | PS positioned on a building, 3D model, both geometries for vertical and E-W components. |
| Use for us | Sub-question d reference for per-building decomposition; case-study scale only. |

| Field | Zhu et al. 2018 |
|---|---|
| Citation | Zhu, Wan, Fei, Qiao et al. 2018. Detection of Building and Infrastructure Instabilities by Automatic Spatiotemporal Analysis of Satellite SAR Interferometry Measurements. Remote Sensing 10(11):1816. 10.3390/rs10111816 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, Remote Sensing page, Earth and Planetary Sciences miscellaneous) |
| Read depth | abstract only |
| What it does | Spatial anomaly (hierarchical clustering, large and inhomogeneous deformation) plus temporal anomaly (decompose into periodic and piecewise-linear parts; detect velocity changes and accelerations); COSMO-SkyMed over Chinese sites; checked with in-field surveys. |
| Limitations | Not stated in the abstract. |
| Data needed | X-band PS time series. |
| Use for us | Time-series anomaly flags per point; case-study validation only. |

| Field | Bianchini et al. 2015 |
|---|---|
| Citation | Bianchini, Pratesi, Nolesini, Casagli 2015. Building Deformation Assessment by Means of Persistent Scatterer Interferometry Analysis on a Landslide-Affected Area: The Volterra (Italy) Case Study. Remote Sensing 7(4):4678. 10.3390/rs70404678 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, Remote Sensing page) |
| Read depth | abstract only |
| What it does | Derives the maximum settlement direction of each building from COSMO-SkyMed PS, compared with geology, construction features and on-field evidence of damage; discusses misreading structural failure as ground motion. |
| Limitations | The abstract itself warns about difficulty attributing PS motion to ground rather than structural failure. |
| Data needed | X-band PS on individual buildings. |
| Use for us | Caveat on interpreting single-structure PS motion; not a design input. |

### Sub-question b (precursors)

| Field | Zanjani et al. 2024 |
|---|---|
| Citation | Zanjani, Amelung et al. 2024. InSAR Observations of Construction-Induced Coastal Subsidence on Miami's Barrier Islands, Florida. Earth and Space Science. 10.1029/2024ea003852 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago, Earth and Space Science page: Environmental Science miscellaneous Q1 for 2015 to 2025 per snippet; quartile of the Earth and Planetary row after 2017 not seen) |
| Read depth | secondary source (university press release and news coverage; paper page refused) |
| What it does | Sentinel-1 2016 to 2023; 2 to 8 cm subsidence on 35 coastal buildings; analyses Champlain Towers South and reports no displacement signal before the 2021 collapse. |
| Limitations | Not read. |
| Data needed | Sentinel-1 time series, 222 images (per press coverage). |
| Use for us | A negative result for a precursor at a famous building collapse (one event). |

| Field | Rodríguez-Antuñano et al. 2023 |
|---|---|
| Citation | Rodríguez-Antuñano, Martínez-Sánchez, Cabaleiro, Riveiro 2023. Anticipating the Collapse of Urban Infrastructure: A Methodology Based on Earth Observation and MT-InSAR. Remote Sensing 15(15):3867. 10.3390/rs15153867 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, Remote Sensing page) |
| Read depth | abstract only (plus search description naming Peniscola and Surfside among the four cases) |
| What it does | Year-to-year displacement trend of each point compared with its neighbours; homogeneity decides stable vs vulnerable zone; tested on four recently collapsed structures. No controls and no detection rate in the abstract. |
| Limitations | Not stated in the abstract. |
| Data needed | MT-InSAR time series over multiple years; neighbour points. |
| Use for us | Neighbour-contrast idea is a spatial-gradient indicator on time series; case studies only. |

| Field | Alizadeh et al. 2024 |
|---|---|
| Citation | Alizadeh, Maghsoudi, Managhebi, Azadnejad 2024. Collapse Hotspot Detection in Urban Area Using Sentinel-1 and TerraSAR-X Dataset with SBAS and PSI Techniques. Land 13(12):2237. 10.3390/land13122237 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, Land page, SJR 0.775) |
| Read depth | abstract only |
| What it does | 144 Sentinel-1 images in three areas with a history of collapses; SBAS beats PSI at showing collapse-indicative behaviour and locating points near real collapse sites; 36 TerraSAR-X images add collapse-prone points near one accident site. Number of collapses, lead time, controls not given in the abstract. |
| Limitations | Not stated in the abstract. |
| Data needed | Dense time series; X-band for extra points. |
| Use for us | Evidence that point density (X vs C band) changes what is found near collapse sites. |

| Field | Gama et al. 2020 |
|---|---|
| Citation | Gama, Mura, Paradella, de Oliveira 2020. Deformations Prior to the Brumadinho Dam Collapse Revealed by Sentinel-1 InSAR Data Using SBAS and PSI Techniques. Remote Sensing 12(21):3664. 10.3390/rs12213664 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, Remote Sensing page) |
| Read depth | abstract only |
| What it does | 26 Sentinel-1B descending images (March 2018 to January 2019); persistent deformation trends to collapse; acceleration "for a short period near the failure"; max accumulated -39 mm (SBAS), -48 mm (PSI). One dam, retrospective, no controls in the abstract. |
| Limitations | The abstract frames Sentinel-1 as complementary to in-situ monitoring. |
| Data needed | Sentinel-1 time series, DSM. |
| Use for us | Method transfer is weak (dam geometry, one event). |

| Field | Grebby et al. 2021 |
|---|---|
| Citation | Grebby, Sowter, Gluyas, Toll et al. 2021. Advanced analysis of satellite data reveals ground deformation precursors to the Brumadinho Tailings Dam collapse. Communications Earth & Environment. 10.1038/s43247-020-00079-2 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, SJR 3.168, Earth and Planetary Sciences miscellaneous rank 7 of 385) |
| Read depth | abstract only; lead time (about 40 days) from press coverage, secondary |
| What it does | ISBAS InSAR; parts of the dam wall and tailings showed deformation not consistent with consolidation; collapse timing "would have been foreseeable". One event, retrospective. |
| Limitations | Not stated in the abstract. |
| Data needed | Sentinel-1 stack; intermittent coherence method for vegetated surfaces. |
| Use for us | Shows the retrospective-precursor design and its weakness (one case, no controls). |

| Field | Lanari et al. 2020 (Comment) |
|---|---|
| Citation | Lanari, Reale, Bonano, Verde et al. 2020. Comment on "Pre-Collapse Space Geodetic Observations of Critical Infrastructure: The Morandi Bridge, Genoa, Italy" by Milillo et al. (2019). Remote Sensing 12(24):4011. 10.3390/rs12244011 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, Remote Sensing page) |
| Read depth | abstract only |
| What it does | Reprocesses the same ascending and descending CosmoSkyMed data with SBAS and tomography; says the published pre-collapse deformation results are "questionable". |
| Limitations | It is itself a rebuttal; Milillo et al. published a reply (10.3390/rs12244016, not read). |
| Data needed | High-resolution X-band, two geometries. |
| Use for us | Warns that building/bridge precursor claims depend on processing choices. |

### Sub-question c (independent record, 2022 to 2026) and citing-paper search

| Field | Ohenhen and Shirzaei 2022 |
|---|---|
| Citation | Ohenhen, Shirzaei 2022. Land Subsidence Hazard and Building Collapse Risk in the Coastal City of Lagos, West Africa. Earth's Future. 10.1029/2022ef003219 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, SJR 3.116, Earth's Future page) |
| Read depth | abstract only |
| What it does | Radar acquisitions 2018 to 2021; subsidence linked to foundation damage and to a collapse record (over 200 casualties in 152 failures since 2005); estimates 255 to 4,000 buildings at high risk. Validation statistics not in the abstract. |
| Limitations | Not stated in the abstract. |
| Data needed | Multi-year time series; collapse inventory. |
| Use for us | Design 1 analogue (collapse record, coastal city). Found by citing-paper search. |

| Field | Du et al. 2024 |
|---|---|
| Citation | Du, Feng, Wu 2024. InSAR-based rapid damage assessment of urban building portfolios following the 2023 Turkey earthquake. Int. J. Disaster Risk Reduction. 10.1016/j.ijdrr.2024.104317 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, IJDRR page) |
| Read depth | secondary source (search fragments) |
| What it does | Measures horizontal deformation of building portfolios (Adiyaman, Nurdagi) after the earthquake; checked against optical remote sensing imagery. Post-event, not before. |
| Limitations | One stated in fragments: InSAR covers large areas but has difficulty capturing horizontal building movement. |
| Data needed | Co-seismic InSAR in more than one geometry. |
| Use for us | Not a pre-event design; relevant only for horizontal-component discussion. |

| Field | Confuorto et al. 2022 |
|---|---|
| Citation | Confuorto, Medici, Bianchini, Del Soldato 2022. Machine Learning for Defining the Probability of Sentinel-1 Based Deformation Trend Changes Occurrence. Remote Sensing 14(7):1748. 10.3390/rs14071748 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, Remote Sensing page) |
| Read depth | abstract only |
| What it does | About 20,000 trend-change anomalies (acceleration/deceleration) in Tuscany Sentinel-1 data 2018 to 2020; random forest predicts where anomalies occur from ten variables; cross-validated on 2020 to 2021 anomalies and official inventories. The outcome is an InSAR anomaly, not building damage. |
| Limitations | Not stated in the abstract. |
| Data needed | Regional MT-InSAR service, time series. |
| Use for us | Anomaly (change-point) definition on Sentinel-1 series with a later-period check. |

### Sub-question d (decomposition)

| Field | Du et al. 2025 |
|---|---|
| Citation | Du, Feng, Wu 2025. Domain Knowledge Embedded InSAR-Based 3D Displacement Monitoring of Urban Buildings. Structural Control and Health Monitoring. 10.1155/stc/8864614 |
| DOI check | VERIFIED |
| Venue | Q1 (Scimago 2025, SJR 1.147, Struct. Control Health Monit. page) |
| Read depth | abstract only |
| What it does | Because SAR is insensitive to N-S motion, adds domain-knowledge constraints linking N-S and E-W building motion to extract 3D displacement from LOS; one tower in Chongqing, 2018 to 2021. |
| Limitations | The abstract states the N-S insensitivity of SAR as the reason for the model. |
| Data needed | LOS series (one tower), constraints from structure. |
| Use for us | Shows decomposition needs extra assumptions beyond two geometries; single building. |

## Found, outside the venue filter
- Das, Priyadarshana, Grebby. Monitoring the risk of a tailings dam collapse through spectral analysis of satellite InSAR time-series data. arXiv 2302.00781 (preprint, 2023). Precursory signal at least five months before the Brumadinho failure. Read: arXiv abstract.
- Brouwer and Hanssen 2021. IGARSS paper on bias of ascending/descending decomposition (TU Delft repository). Read: search description only.
- Pompeii vertical-displacement-gradient paper, ISPRS Annals X-M-2-2025, 29 (conference series). Gradient along wall directions from two geometries. Read: search description only.
- Yu and Hu 2022. EGU22-2114 abstract: Surfside coherence and amplitude changes. Conference abstract.
- Poggi et al. EGU24-16313: A-DInSAR vertical/horizontal velocity intensity for more than 4,000 masonry buildings (Apennines). Conference abstract.
- Peduto et al. 2016 IMEKO TC-4: two-scale fragility procedure with DInSAR settlement. Conference.
- Calvo 2025 (Australian Centre for Geomechanics paper): InSAR trend indicators at Cadia and Brumadinho. Conference.
- Using InSAR stacking techniques to predict bridge collapse due to scour, IGARSS 2018 (10.1109/igarss.2018.8517566): Tadcaster bridge; precursor over a month before collapse (secondary description).
- Piahs 2020 proceedings: "Land subsidence risk maps and InSAR based angular distortion structural vulnerability assessment" (10.5194/piahs-382-583-2020).
- Vendor press release (GlobeNewswire, June 2026) claiming InSAR could have tracked pool-deck differential subsidence before Surfside. Marketing claim, not evidence.
- Shahbazi 2025 follow-up (Spain-wide flagged buildings, IEEE JSTARS per search description): not located by DOI; not read.

## Identified, not read
- Zhang, Chen, Yin et al. 2025. Fragility and vulnerability curves of masonry buildings on slow-moving landslides: A comparative study on intensity parameters from MT-InSAR. Engineering Geology. 10.1016/j.enggeo.2025.108212 (DOI VERIFIED; Engineering Geology Q1, Scimago 2025). Most likely the paper that compares intensity parameters; no abstract retrievable, SSRN preprint refused.
- Wang, Guo, Xia et al. 2026. Long-term deformation monitoring and potential building damage assessment in resource-based arid urban agglomerations. Int. J. Applied Earth Observation and Geoinformation. 10.1016/j.jag.2026.105271 (DOI VERIFIED; journal Q1 per Scimago 2025). No abstract retrieved.
- Jianchuan Ancient Town InSAR stability paper (npj Heritage Science, 10.1038/s40494-024-01488-8): LOS velocity with angular distortion and skew; journal quartile not looked up, text refused.
- Wikby et al. 2024. A grid-based methodology for the assessment of time-dependent building damage at large scale. Tunnelling and Underground Space Technology. 10.1016/j.tust.2024.105788 (DOI VERIFIED; quartile not verified; abstract not retrieved).
- Milillo et al. reply to Lanari (10.3390/rs12244016).
- Present-day land subsidence risk in the metropolitan cities of Italy, Scientific Reports 2025 (10.1038/s41598-025-18941-8; quartile not verified).
- Comment and Reply on Fouad et al. 2025, Earth's Future 2026 (10.1029/2025ef006885; 10.1029/2025ef007826), and Assessing regulatory institutions and building collapse in Lagos state, Scientific Reports 2026 (10.1038/s41598-026-46568-w; quartile not verified).
- InSAR-based Hamburg/Como and related items in the citing list (e.g. Monitoring Subsidence and Building Vulnerability in Como, 30 years of InSAR, 2026; Multi-Source Monitoring for Collapse Risk of Inner-City Quay Walls, 2026): conference-type DOIs, not assessed.
- Citing-search items seen but judged off-topic or modelling-only (masonry façade finite-element fragility papers, landslide susceptibility, flood studies) were not followed up.

## Search log (all 2026-11-17)
1. OpenAlex `works/doi:` for the four seed DOIs: W2922306468 (Peduto 2019, 70 citing), W3025999562 (Ezquerro 2020, 63), W3109468082 (Mohamadi 2020, 28), W4407554579 (Fouad 2025, 18).
2. OpenAlex `filter=cites:<id>&per-page=100` for each; 168 unique citing works. The OpenAlex free daily budget was then exhausted, so no further OpenAlex keyword searches were possible; Crossref and web search were used instead.
3. Crossref bibliographic searches: "InSAR differential settlement angular distortion building damage"; "persistent scatterer building deformation indicator damage velocity gradient"; "building collapse precursor InSAR time series acceleration"; "Champlain Towers South InSAR subsidence"; "Morandi bridge InSAR collapse precursors"; "inverse velocity InSAR failure forecasting".
4. Web search (extended): "InSAR building damage differential settlement angular distortion compared with velocity damage survey correlation"; "InSAR precursors building collapse Surfside ... acceleration prior to collapse"; "satellite InSAR pre-failure deformation bridge collapse Morandi Genoa precursors anomaly detection time series".
5. Web search (standard): Surfside Sentinel-1 no pre-collapse deformation; Brumadinho InSAR precursor; MT-InSAR building collapse early warning retrospective China; ascending descending vertical east-west decomposition building damage; abstract lookups for Zhang 2025, Shahbazi 2024, Barra 2022, Wang 2026, Du 2024, Zanjani 2024.
6. Crossref `works/<DOI>` verification and abstract retrieval for all papers listed; Semantic Scholar abstract lookups (several returned no abstract).
7. Scimago quartile lookups by web search restricted to scimagojr.com for: Remote Sensing of Environment, Remote Sensing, ISPRS J. Photogramm. Remote Sens., Int. J. Disaster Risk Reduction, Earth's Future, Land, Int. J. Appl. Earth Obs. Geoinf., Engineering Geology, J. Civil Struct. Health Monit., Communications Earth & Environment, Earth and Space Science, Struct. Control Health Monit. Direct scimagojr.com fetch was blocked by Cloudflare and was not bypassed. IEEE JSTARS: IEEE journal, no lookup needed.
8. Failed fetches (not bypassed): ScienceDirect/linkinghub, MDPI, Nature (login redirect), Wiley/AGU, SSRN, digibug.ugr.es (Anubis), Europe PMC (no full text for these DOIs).
