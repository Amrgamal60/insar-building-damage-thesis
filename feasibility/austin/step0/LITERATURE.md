# Austin step 0: literature check

Checked 2026-10-28. Read-only. No InSAR data were opened and `AUSTIN_PLAN.md` was not edited.

The Austin question is whether line-of-sight motion in the 24 months before a residential foundation-repair permit improves held-out ranking of that parcel beyond building, soil, terrain and location features. Section 2 claims that studies of expansive-clay damage and InSAR do not test that held-out incremental value against a city-wide repair record. Twenty-five studies were assessed. Every DOI in `literature.json` was queried at `https://api.crossref.org/works/<DOI>`.

**Verification: 25 VERIFIED, 0 UNVERIFIED.**

## Verdict on the §2 gap claim

**SUPPORTED.**

No assessed study tests held-out, spatially blocked, incremental value of InSAR from before a repair against a non-InSAR baseline and a city-wide repair record. The four parts of the NYC gap are still uncombined for this outcome.

What exists, separately:

1. **Independent outcome.** Peduto et al. (2019), Nicodemo et al. (2020) and Ezquerro et al. (2020) pair DInSAR or Sentinel-1 velocity with a building damage survey. Hudak (1998) and Williams (2008) use Texas foundation-repair records against geology or soil, with no InSAR. Harrison et al. (2012) and Barthélemy et al. (2024) use subsidence insurance claims against climate or a drought index, with no InSAR. None of these outcomes is a city-wide permit file scored with preceding InSAR.
2. **InSAR before the outcome.** Not shown for a damage or repair catalogue. Damage-survey papers combine motion and damage on the same buildings. Nicodemo et al. (2020) align settlement with the dated onset of damage; that is not a window that ends before the event. Miller and Shirzaei (2019) map subsidence before Hurricane Harvey flooding, which is a different outcome.
3. **Spatial controls.** No assessed study uses a building, soil, terrain and location baseline, spatially blocked folds, and an autocorrelation-preserving null.
4. **Replication across cities.** Single-city or single-region studies exist. No study repeats a held-out repair test in more than one city.

Peduto et al. (2019) is settlement of soft clay and peat, not expansive-clay shrink-swell. The shrink-swell InSAR papers (Burnol et al. 2021; te Brake et al. 2013; Scoular et al. 2019; Toure et al. 2025; the central Texas and Houston abstracts) have no repair catalogue.

## Closest prior work

1. **Peduto, Korff, Nicodemo, Marchese and Ferlisi (2019),** *Soils and Foundations*, [10.1016/j.sandf.2018.12.009](https://doi.org/10.1016/j.sandf.2018.12.009). Closest building-level link between DInSAR settlement and an independent damage survey (more than 700 masonry buildings, four Dutch cities). It differs from Austin in five ways: the soil is compressible soft clay and peat, not expansive clay; the outcome is a visual damage survey, not permits; fragility curves are fit on the surveyed buildings, not held out against a non-InSAR baseline; the motion is not a 24-month window that ends before the outcome; there is no spatial block or replication.

2. **Williams (2008),** *Environmental Geology*, [10.1007/s00254-008-1571-y](https://doi.org/10.1007/s00254-008-1571-y). Closest metro-scale use of foundation repairs as the outcome against soil, in Dallas-Fort Worth. It differs because there is no InSAR, and the visible abstract does not describe a held-out or spatially blocked model. The publisher abstract is truncated, so the direction and strength of the soil relationship are not reported here.

3. **Hudak (1998),** *GeoJournal*, [10.1023/a:1006965231244](https://doi.org/10.1023/a:1006965231244). Closest use of foundation-repair contractor addresses (78 houses in Denton) against local geology. It differs because there is no InSAR, the sample is a company file rather than a city-wide permit census, and the visible abstract does not describe a predictive or held-out test.

Next nearest, and not in the three: Glaser, Gangi and Nelson (2025), [10.1130/abs/2025am-6858](https://doi.org/10.1130/abs/2025am-6858), is the only assessed Sentinel-1 study of expansive clay in central Texas, and it compares seasonal motion with a lab swell estimate at a solar site, with no damage outcome (abstract only). Barthélemy et al. (2024), [10.5194/nhess-24-999-2024](https://doi.org/10.5194/nhess-24-999-2024), use official French clay-subsidence claims, at municipality-year scale, with no InSAR.

## Suggested wording for AUSTIN_PLAN.md §2

Do not edit the plan from this note. Replacement text:

> Studies of expansive-clay motion and of settlement damage do not test the held-out incremental value of InSAR against a city-wide record of repairs. The four-part gap in `nyc/NYC_REPLICATION_PLAN.md` §2 still applies to this outcome: an independent outcome, InSAR that precedes that outcome, spatial controls, and replication across cities. No study found in the step-0 check combines them.
>
> InSAR has measured shrink-swell at instrumented clay sites and in cities (Burnol et al. 2021, Chaingy; te Brake et al. 2013, the Netherlands; Scoular et al. 2019, London Clay; Glaser et al. 2025, a central Texas solar site, abstract only). Those studies do not use a repair catalogue. Scoular et al. (2019) could not statistically separate shrink-swell classes in TerraSAR-X persistent scatterers over three London areas. Welch et al. (2024) measured drought subsidence of expansive soil with GPS, not InSAR, at the University of Houston Coastal Center, and found the signal prominent in open fields and minor in built-up areas.
>
> Fragility curves that combine DInSAR or Sentinel-1 velocity with a damage survey (Peduto et al. 2019, four Dutch cities on soft clay and peat; Ezquerro et al. 2020, Pistoia) are fit on the surveyed buildings. They are not a held-out test against building, soil, terrain and location, and the motion is not a window that ends before a repair. Foundation-repair records in north Texas have been compared with geology or soil without InSAR (Hudak 1998, 78 contractor addresses in Denton; Williams 2008, a GIS of repairs and soils in Dallas-Fort Worth). UK and French subsidence claims have been compared with climate or a drought index, again without InSAR (Harrison et al. 2012; Barthélemy et al. 2024).
>
> The check is recorded in `feasibility/austin/step0/LITERATURE.md`.

## Group A. InSAR or ground motion and shrink-swell

Houston and Gulf Coast rows are aquifer or extraction subsidence, included so they are not mistaken for clay-repair studies. Welch et al. (2024) is GPS, not InSAR.

| Study | Area | Outcome (source) | Motion product and whether it precedes the outcome | Unit | Non-InSAR baseline | Held-out and spatially blocked | Result | Gap parts | Check |
|---|---|---|---|---|---|---|---|---|---|
| Burnol et al. 2021, *Atmosphere*, [10.3390/atmos12101262](https://doi.org/10.3390/atmos12101262) | Chaingy, France | None (extensometers) | Sentinel-1 MT-InSAR. Not applicable | Site | No | No / No | Sentinel-1 matched extensometer shrink-swell over more than three years. | None | VERIFIED. Full abstract |
| te Brake et al. 2013, *Vadose Zone Journal*, [10.2136/vzj2012.0098](https://doi.org/10.2136/vzj2012.0098) | Dutch clay polders | None (in situ shrinkage) | TerraSAR-X. Not applicable | Field | No | No / No | Differential phase resembled in situ clay shrinkage in a test period. | None | VERIFIED. Full abstract |
| Scoular et al. 2019, *QJEGH*, [10.1144/qjegh2018-160](https://doi.org/10.1144/qjegh2018-160) | Three London areas on London Clay | None (LEACS shrink-swell classes) | TerraSAR-X PSI, 2011–2017. Not applicable | Scatterers | No | No / No | Seasonal cycles were present, and PSI could not statistically isolate shrink-swell. | None | VERIFIED. Full abstract |
| Toure et al. 2025, *Egyptian Journal of Remote Sensing and Space Sciences*, [10.1016/j.ejrs.2025.08.002](https://doi.org/10.1016/j.ejrs.2025.08.002) | Diamniadio, Senegal | Exposure map derived from InSAR, not a damage survey | Sentinel-1 PS/DS, 2017–2024. Not applicable | 11 sites | No | No / No | Seasonal amplitudes were 0.5–5 mm; angular distortion locally reached 2.5×10⁻³. | None | VERIFIED. Full abstract |
| Jiang et al. 2023, *Frontiers in Environmental Science*, [10.3389/fenvs.2023.1287128](https://doi.org/10.3389/fenvs.2023.1287128) | Canal slope, Huixian, China | None | Sentinel-1, 2017–2022. Not applicable | Slope | No | No / No | Unstable zones were generally under 20 mm/year and seasonal, with acceleration at the July 2021 rainfall. | None | VERIFIED. Full abstract |
| Glaser, Gangi and Nelson 2025, GSA abstract, [10.1130/abs/2025am-6858](https://doi.org/10.1130/abs/2025am-6858) | Central Texas solar site | None (lab PVR) | Sentinel-1, 2020–2025. Not applicable | Site | No | No / No | After removing ~2.95 mm/year, seasonal motion was about ±5 mm, with a 2020 peak rise of ~36 mm against a 2-inch lab PVR. | None | VERIFIED. Abstract only. Crossref lists "ANS Geo" first; Glaser is the presenting author |
| Shang, Si and Lu 2026, EGU abstract, [10.5194/egusphere-egu26-15806](https://doi.org/10.5194/egusphere-egu26-15806) | Houston | None stated | InSAR plus a tropospheric network. Not applicable | Not stated | No | No / No | The abstract proposes a Houston expansive-clay processing framework and reports no repair test. | None | VERIFIED. Abstract only |
| Le Corvec 2026, EGU abstract, [10.5194/egusphere-egu26-21004](https://doi.org/10.5194/egusphere-egu26-21004) | Toulouse | None | Two Sentinel-1 pipelines. Not applicable | Urban series | No | No / No | Both pipelines found weak subsidence and a seasonal clay signal. No damage catalogue. | None | VERIFIED. Abstract only |
| Liu et al. 2022, *Remote Sensing*, [10.3390/rs14236184](https://doi.org/10.3390/rs14236184) | Houston | None | Sentinel-1 and GPS. Not applicable | Region | No | No / No | Monitors groundwater-withdrawal subsidence. No clay-repair analysis in the abstract. | None | VERIFIED |
| Qiao et al. 2023, *IJAEOG*, [10.1016/j.jag.2023.103544](https://doi.org/10.1016/j.jag.2023.103544) | Texas Gulf Coast | None | Sentinel-1 PS, 2016–2022. Not applicable | Coast | No | No / No | Nineteen hotspots were attributed to hydrocarbons, groundwater and salt domes, not to foundation repairs. | None | VERIFIED. Full abstract |
| Miller and Shirzaei 2019, *Remote Sensing of Environment*, [10.1016/j.rse.2019.03.022](https://doi.org/10.1016/j.rse.2019.03.022) | Houston-Galveston | Harvey flood extent | ALOS and Sentinel-1 before the cyclone. Precedes the flood, not a repair | Flooded area | No | No / No | 85 percent of the flooded area had subsided faster than 5 mm/year. | None | VERIFIED. Full abstract |
| Welch et al. 2024, *Geophysical Research Letters*, [10.1029/2023GL107549](https://doi.org/10.1029/2023GL107549) | University of Houston Coastal Center | None | GPS, not InSAR. Not applicable | GPS sites | No | No / No | Drought subsidence of 1–2 dm in expansive soil was prominent in open fields and minor in built-up areas. | None | VERIFIED. Full abstract |

No assessed paper measures shrink-swell with InSAR in Austin, Dallas-Fort Worth, or San Antonio. The Dallas-Fort Worth and San Antonio queries did not return an expansive-clay InSAR study in the top hits.

## Group B. InSAR and building damage

| Study | Area | Outcome (source) | Motion product and whether it precedes the outcome | Unit | Non-InSAR baseline | Held-out and spatially blocked | Result | Gap parts | Check |
|---|---|---|---|---|---|---|---|---|---|
| Peduto et al. 2019, *Soils and Foundations*, [10.1016/j.sandf.2018.12.009](https://doi.org/10.1016/j.sandf.2018.12.009) | Four Dutch cities | Visual damage severity (survey). Soft soil, not expansive clay | DInSAR differential settlement, rotation, deflection ratio. Does not precede | Building | No | No / No | Fragility curves on more than 700 masonry buildings. No held-out incremental test. | 1, as a survey | VERIFIED. Full abstract |
| Nicodemo, Peduto and Ferlisi 2020, *PIAHS*, [10.5194/piahs-382-651-2020](https://doi.org/10.5194/piahs-382-651-2020) | One Dutch urban area | Damage severity (repeat surveys) | Long DInSAR series, taken at damage onset. Does not precede an administrative event | Building | No | No / No | Fragility curves depend on dating the onset of damage. | 1, as a survey | VERIFIED. Full abstract |
| Ezquerro et al. 2020, *Sensors*, [10.3390/s20102749](https://doi.org/10.3390/s20102749) | Pistoia, Italy | Field damage survey | Sentinel-1 and COSMO-SkyMed velocity. Does not precede | Building, then loss map | No | No / No | Velocity and surveys were turned into damage-probability and loss maps. | 1, as a survey | VERIFIED. Full abstract |
| Del Soldato et al. 2019, *Remote Sensing*, [10.3390/rs11121486](https://doi.org/10.3390/rs11121486) | Two hamlets, Tuscany | Landslide damage class (three surveys) | ERS, ENVISAT, COSMO-SkyMed, Sentinel-1. Does not precede | Structure | No | No / No | Sentinel-1 slope velocity and field damage gave fragility curves. Landslides, not clay shrink-swell. | 1, as a survey | VERIFIED. Full abstract |
| Drougkas et al. 2020, *Structural Health Monitoring*, [10.1177/1475921720942120](https://doi.org/10.1177/1475921720942120) | Belgium | Damage calculated from InSAR plus analytical models. Compared with on-site observations; the statistic is not in the abstract | InSAR over nearly 30 years. Damage is computed from the motion | Building | No competing baseline | No / No | Country-scale calculated damage for heritage. Not an independent repair register and not a held-out test. | None. The outcome is derived from InSAR | VERIFIED. Full abstract |
| Milillo et al. 2018, *Remote Sensing*, [10.3390/rs10020287](https://doi.org/10.3390/rs10020287) | London Crossrail | Tunnelling strain versus levelling | COSMO-SkyMed through tunnelling. Does not precede | Building | Greenfield trough, not a fitted parcel baseline | No / No | Greenfield strain was high by up to 50 percent for about 71 percent of the analysed buildings. | None | VERIFIED. Full abstract |
| Giardina et al. 2018, *Structural Control and Health Monitoring*, [10.1002/stc.2285](https://doi.org/10.1002/stc.2285) | London Crossrail | Post-tunnelling building deformation | MT-InSAR after excavation. Does not precede | Building | Greenfield indicators | No / No | InSAR displacements, checked against traditional monitoring, show soil-structure interaction that greenfield assumptions miss. | None | VERIFIED. Full abstract |

## Group C. Insurance claims and clay shrink-swell

| Study | Area | Outcome (source) | Motion product and whether it precedes the outcome | Unit | Non-InSAR baseline | Held-out and spatially blocked | Result | Gap parts | Check |
|---|---|---|---|---|---|---|---|---|---|
| Harrison et al. 2012, *Proceedings of the Geologists' Association*, [10.1016/j.pgeola.2012.05.002](https://doi.org/10.1016/j.pgeola.2012.05.002) | South-east England | Subsidence claims | None | Region | Climate and GeoSure. No InSAR arm | No / No | Two-year precipitation below 350 mm coincided with higher claims; above 394 mm, with lower claims. A quarterly mean maximum above 22.6 °C coincided with a claims peak. | 1, as regional claims | VERIFIED. Full abstract |
| Barthélemy et al. 2024, *NHESS*, [10.5194/nhess-24-999-2024](https://doi.org/10.5194/nhess-24-999-2024) | 20 French municipalities | CCR clay-subsidence claims by municipality-year | None | Municipality-year | Drought index only | No / No | A soil-wetness drought index was rank-correlated with claims. InSAR was not used. | 1, as aggregated claims | VERIFIED. Full abstract |
| Kaveh, Deffontaines and Fruneau 2007, *Revue Française de Géotechnique*, [10.1051/geotech/2007120201](https://doi.org/10.1051/geotech/2007120201) | Eastern Île-de-France | Local damage claims, discussed | Radar interferometry (abstract: DLnSAR) with maps. No pre-outcome test | Local area | No formal model | No / No | The abstract concludes that swelling soil, urban fabric, topography and trees locally explain the claims. | None | VERIFIED. Full abstract |

No assessed study links InSAR to a UK, French, Belgian or Dutch insurer's clay-subsidence claim file and then tests held-out incremental value.

## Group D. Permits, contractor records, complaints

No assessed study links InSAR to building permits, foundation-repair contractor records, or municipal complaints.

Hudak (1998) uses contractor addresses and does not use InSAR (group F). OpenAlex queries that combined InSAR with permits or contractor records returned large counts (205, 865 and 6,322). The top works were generic subsidence papers, not permit studies. A SatSense vendor page (2022, `https://satsense.com/case-studies/using-insar-to-settle-insurance-claims-quicker`) describes InSAR used to interpret one UK shrink-swell claim. It is not a journal study, has no DOI, and reports no held-out test. It is not one of the 25.

## Group E. Held-out incremental test

No assessed study tests held-out predictive value of InSAR for building damage beyond a non-InSAR baseline.

Fragility curves in group B are fit on the same surveyed buildings. Drougkas et al. (2020) calculate damage from InSAR. Earthquake SAR classifiers were excluded: they use post-event backscatter or coherence, not pre-event ground motion. OpenAlex queries for cross-validation or held-out prediction of building damage with InSAR returned 2,076 and 607 works; the top ranks were earthquake damage detection, landslide forecasting, or subsidence-field prediction, not this design.

## Group F. Texas foundation damage without InSAR

| Study | Area | Outcome (source) | Motion product | Unit | Non-InSAR baseline | Held-out and spatially blocked | Result | Gap parts | Check |
|---|---|---|---|---|---|---|---|---|---|
| Hudak 1998, *GeoJournal*, [10.1023/a:1006965231244](https://doi.org/10.1023/a:1006965231244) | Denton, Texas | 78 damaged houses (repair companies) | None | Address | Geology. No model in the visible text | No / No | Contractor addresses were evaluated against local geology. The publisher abstract is truncated, so the association is not stated here. | 1, as a small repair file | VERIFIED. Abstract opening only |
| Williams 2008, *Environmental Geology*, [10.1007/s00254-008-1571-y](https://doi.org/10.1007/s00254-008-1571-y) | Dallas-Fort Worth | Foundation repairs (GIS) | None | Regional GIS | Soil conditions. No held-out model in the visible text | No / No | A GIS relates repairs to soils. The publisher abstract is truncated, so the relationship is not stated here. | 1, as a regional repair file | VERIFIED. Abstract opening only |
| Williams 2003, *Environmental Geology*, [10.1007/s00254-003-0836-8](https://doi.org/10.1007/s00254-003-0836-8) | Denton County | Soils hazard under urban growth. Repairs are not stated | None | Not stated | Not a predictive test in the visible text | No / No | A GIS of urban growth is framed against soils-related hazards. The publisher abstract is truncated. | None | VERIFIED. Abstract opening only |

The ASCE Texas Section residential-foundation guideline (2022) is a practice document, not a study of permits or InSAR, and is not assessed.

## Identified and not assessed

Abstracts were not obtained without a paywall, so these are not in `literature.json` and are not in the 25. Crossref confirmed title and first author on 2026-10-28 unless noted.

- Qu, Lu, Zhang, Bawden, Kim, Zhao and Qu (2015), *Remote Sensing of Environment*, [10.1016/j.rse.2015.08.027](https://doi.org/10.1016/j.rse.2015.08.027). Houston-Galveston multi-temporal InSAR. First author Feifei Qu.
- Peduto, Nicodemo, Maccabiani and Ferlisi (2017), *Engineering Geology*, [10.1016/j.enggeo.2016.12.018](https://doi.org/10.1016/j.enggeo.2016.12.018). Dutch damage surveys and DInSAR. First author Dario Peduto.
- Peduto, Ferlisi, Nicodemo, Reale, Pisciotta and Gullà (2017), *Landslides*, [10.1007/s10346-017-0826-7](https://doi.org/10.1007/s10346-017-0826-7). Landslide fragility curves. First author Dario Peduto.
- Capes and Teeuw (2017), *IJAEOG*, [10.1016/j.jag.2017.01.010](https://doi.org/10.1016/j.jag.2017.01.010). European urban geohazards and InSAR. First author Renalt Capes.
- Biswas, Zenodo [10.5281/zenodo.22086047](https://doi.org/10.5281/zenodo.22086047). Crossref returned 404. The Zenodo API did not return a record. Not assessed.

## Search log

Date of all searches: 2026-10-28. OpenAlex counts are `meta.count`. Crossref `total-results` for `query.title` was 10⁵–10⁷ even when the target paper was the first hit, so those totals are not used as hit counts. Semantic Scholar was used to retrieve abstracts by DOI, not as a counted discovery search. Web search returned no hit count.

### OpenAlex (`api.openalex.org/works?search=`)

| Group | Query | Count |
|---|---|---|
| A | InSAR expansive clay shrink-swell | 37 |
| A | InSAR shrink swell clay Sentinel-1 | 65 |
| A | InSAR Austin Texas ground deformation clay | 92 |
| A | InSAR Houston Galveston subsidence Sentinel-1 | 79 |
| A | InSAR Houston Galveston subsidence | no count returned |
| A | InSAR Dallas Fort Worth subsidence | 18 |
| A | Sentinel-1 San Antonio ground deformation | 191 |
| A | OPERA displacement expansive soil | 503 |
| A | InSAR "expansive clay" | 81 |
| A | "shrink-swell" InSAR | 89 |
| A | "Yazoo clay" InSAR | 3 |
| A | Austin InSAR deformation | 514 |
| B | Peduto InSAR building damage fragility | 81 |
| B | DInSAR settlement-induced building damage fragility curves | 109 |
| B | InSAR building damage expansive clay | 153 |
| B | Peduto building damage InSAR | 294 |
| B | Nicodemo fragility InSAR | 59 |
| C | InSAR London Clay subsidence insurance claims | 18 |
| C | InSAR shrink swell insurance claims United Kingdom | 1 |
| C | InSAR retrait-gonflement argiles sécheresse | 2 |
| C | Sentinel-1 clay shrinkage building damage France | 97 |
| C | InSAR clay subsidence damage Belgium Netherlands | 101 |
| C | "London Clay" InSAR | 49 |
| C | "shrink-swell" insurance claims subsidence | 44 |
| C | retrait-gonflement InSAR | 9 |
| D | InSAR building permits foundation repair | 205 |
| D | InSAR subsidence building permit records | 865 |
| D | ground motion foundation repair contractor records | 6322 |
| D | "Dallas" InSAR subsidence foundation | 34 |
| D | "Fort Worth" InSAR subsidence | request failed |
| E | InSAR building damage cross-validation prediction | 2076 |
| E | InSAR predictive model building damage held-out | 607 |
| E | "building damage" InSAR "cross-validation" | 86 |
| E | machine learning InSAR building damage prediction validation | 1684 |
| F | Texas expansive soil foundation damage permits | 1931 |
| F | Austin foundation repair expansive clay | 383 |
| F | expansive clay residential foundation damage Texas appraisal | 42 |
| F | "foundation repair" expansive soil Texas | 12 |
| F | Houston subsidence InSAR building damage | 241 |
| F | "foundation" permits expansive Austin Texas | 3692 |

High counts on permit, Austin, OPERA, machine-learning and cross-validation queries were diffuse. Relevant items were taken from the first page, then checked by title search.

### Crossref title queries

Used to recover the canonical DOI. The first hit was the intended paper for: Scoular et al. 2019; te Brake et al. 2013; Williams 2008; Hudak 1998; Welch et al. 2024; Burnol et al. 2021; Harrison et al. 2012; Miller and Shirzaei 2019; Qu et al. 2015; Drougkas et al. 2020; Ezquerro et al. 2020; Peduto et al. 2017 *Engineering Geology*; Barthélemy et al. 2024; Liu et al. 2022; Kaveh et al. 2007; Giardina et al. 2018. Williams (2003) was then confirmed by DOI.

### Web search

No hit count was returned. Queries: "InSAR shrink-swell expansive clay Sentinel-1 building damage"; "Peduto Nicodemo fragility curves DInSAR"; "InSAR London Clay insurance claims subsidence BGS"; "Texas expansive clay residential foundation damage permits appraisal Austin Dallas"; "InSAR OR PSInSAR subsidence claims shrink-swell foundation repair"; "cross-validation InSAR building damage subsidence prediction baseline"; Williams 2008 and Hudak 1998 abstract phrases. Publisher and NERC pages supplied the abstracts cited above. Springer full abstracts for Hudak (1998) and Williams (2003, 2008) were not on the public landing page; only the truncated meta description was used.

## Addendum 2026-11-10: novelty check after freezing

Added by Claude after the plan was frozen. It concerns the literature only. No rule, test, threshold or hypothesis of `AUSTIN_PLAN.md` changed, and the frozen copy is untouched.

**Why:** on 2026-11-10 the user shared an outside novelty review (GPT) that named seven items and said the 25-study check had missed two of them. Each item was checked against a primary source. The 25 studies above stay as they were; the items below are not added to that count.

| Item | Checked against | What it is | Independent outcome record | Held-out test beyond a non-InSAR baseline | Already in the thesis record |
|---|---|---|---|---|---|
| Yang, Huang, Li and Chang 2026, *Remote Sensing of Environment*, [10.1016/j.rse.2026.115454](https://doi.org/10.1016/j.rse.2026.115454) | Crossref (title, four authors, journal, August 2026 issue) and the University of Twente repository page | Kunming, 106 TerraSAR-X Stripmap images 2017–2019. Two indicators (how suitable the radar data are for a building; the building's deformation signature) give five deformation modes and four risk levels. | None stated on the repository page | None stated | **Yes.** It is in the prior-work table of `nyc/NYC_REPLICATION_PLAN.md` §2 (2026-10-07), which `AUSTIN_PLAN.md` §2 adopts. It is not one of the 25 because step 0 searched expansive clay and foundation repairs only. |
| "Admiral – Subsidence hazard risk score", in *USB Grant Case Studies: Overview of Grant Projects*, UK Space Agency, Unlocking Space for Business programme, PDF created 2025-03-21, pages 9–10 | The PDF itself (`assets.publishing.service.gov.uk/media/67dd784a64220b68ed6a6f7a/Grant_Case_Studies_-_Detailed_Case_Studies.pdf`, SHA-256 `4d2de2a90fd37dde424e2c58b4acd5d9739f0ad5e1b7f937fa96e76a03e9b7dc`) | An insurer's grant project with SatSense (satellite processing) and Optera (subsidence investigation). A property subsidence risk score built on observed cyclical movement, with overlays of known risk factors. | Yes: the insurer's own subsidence claims | Not described. The score is "validated against Admiral's historic claims experience" and its "future predictive power validated against recent claims". | **No, new.** Group D above noted only a 2022 SatSense vendor page. |
| Ma et al. 2022, *International Journal of Applied Earth Observation and Geoinformation*, [10.1016/j.jag.2022.103076](https://doi.org/10.1016/j.jag.2022.103076) | Crossref (title, journal, November 2022) | Building risk from multi-temporal InSAR with numerical modelling | UNVERIFIED (paper not read) | UNVERIFIED | No, new |
| Sadhasivam et al. 2025, *Nature Sustainability*, [10.1038/s41893-025-01663-0](https://doi.org/10.1038/s41893-025-01663-0) | Crossref | Building damage risk from subsidence in five Indian megacities | No | No | Yes, NYC plan §2 |
| Ezquerro et al. 2020; Williams 2008 | – | – | – | – | Yes, groups B and F above |

**What the Admiral case study says, and does not say:**
- It reports that "encouraging results have been seen in identifying past subsidence claims using satellite data", and that "the ongoing challenge is iterating the score to make it more future predictive".
- It gives no sample size, no model, no figures, no validation design and no comparison with a baseline without satellite data. It is a two-page programme case study, not a peer-reviewed study.
- It is the closest known work in kind: satellite ground motion before and after an outcome, tested against an independent record of that outcome, with a separate check on later outcomes.
- Its reported pattern, easier retrospective identification than forward prediction, is the same contrast as Alexandria (motion concurrent with the collapses) against NYC (motion before them).

**Also relevant, already in the thesis record:** Ohenhen et al. 2025 (*Nature Cities*, [10.1038/s44284-025-00240-y](https://doi.org/10.1038/s44284-025-00240-y); NYC plan §2) maps subsidence-based building risk in the 28 most populous US cities without validation against a damage record. Austin is among the 28 most populous US cities. Press coverage gives 706 Austin buildings in its high and very high risk classes; that figure was not checked against the paper.

**Further searches on 2026-11-10** (web search, targeted, read at the level of result summaries only):
- Queries: InSAR with subsidence insurance claims and machine learning; InSAR with Dutch foundation-damage records; Sentinel-1 with UK subsidence claims; InSAR with Texas foundation-repair records or permits.
- Nothing closer was found. The results were French claims models without InSAR, the British Geological Survey's property subsidence assessment (calibrated against subsidence interpreted from InSAR, not tested on claims), a Dutch house-price study that uses subsidence as a proxy because it lacks damage records, and a 2025 conference abstract on InSAR over expansive clay in central Texas with no repair record.

**Effect on the §2 gap claim:** it stands, with narrower wording.
- "No study we found" must not be read as "no one has compared InSAR with later damage records". An insurer has done so with claims, without publishing a method or results.
- The claim that remains is the specific one: a held-out, spatially blocked test of what InSAR measured before a recorded repair adds beyond building, soil, terrain, location and income, with a spatial null and a within-area analysis over time.
- **Suggested sentence for the write-up:** "An insurer-led project (Admiral, with SatSense and Optera; UK Space Agency case study, 2025) scored property subsidence risk from InSAR and checked it against historic and recent claims. It reports encouraging retrospective results and describes forward prediction as an open challenge, but it publishes no method or figures."

**Still to do at write-up, not before:**
- a related-work matrix that separates physical damage surveys, administrative repair records and insurance claims; whether the motion precedes the outcome; whether the test is held out; and whether it is incremental over a baseline without InSAR;
- full-text reading of Yang et al. 2026, Ma et al. 2022, Ezquerro et al. 2020 and Peduto et al. 2019, not abstracts;
- a search of dissertations and of the papers citing these.

**Limits of this addendum:** the Yang paper's full text was not re-read today, because the repository refused a scripted download. Its row rests on the repository's abstract page and on the earlier entry in the NYC plan. Search-engine summaries are not a systematic review.
