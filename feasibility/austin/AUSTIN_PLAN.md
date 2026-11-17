# Austin study plan: ground motion before recorded foundation-repair permits

**Working title:** "A Spatiotemporal Framework for Assessing Ground-Motion-Related Building Repair Risk Using InSAR Time Series and Delayed Administrative Records".
- This is the supervisor's proposed title of 2026-10-30, with "seismic time series" replaced by "InSAR time series". The data are satellite radar measurements of near-surface ground movement along the satellite's line of sight, not seismic records.
- In this study "repair risk" means the likelihood or rate of *recorded* foundation-repair permits. It does not mean independently validated physical damage, or that ground movement caused the repairs.

**Status:** DRAFT 10 (2026-11-06, by Claude), approved by the user and frozen on 2026-11-07, with the conditional null (b) as the primary Test A null.
- The reference-data order (§5) was approved by the user on 2026-10-31.
- Option C is registered as the fallback, with eligibility from 2019-10-01.
- The identifier crosswalk is complete, and the rule taken from it is registered in §5 (`step0/ID_CROSSWALK.md`).
- The Test A null was calibrated on synthetic data. Under the rule registered in §10, neither candidate null was acceptable in every scenario, so the choice fell to the user. On 2026-11-06 the user chose the conditional null as primary (§10).
- No InSAR file for Austin has been downloaded or read.
- No baseline feature has been built and no model has been fitted to real data.
- The analysis scripts that must be fixed before freezing are written and checked on synthetic data only (`scripts/README.md`).
- What is already known about the Austin data is listed in §3.
- The frozen copy is `freeze/AUSTIN_PLAN_frozen.md`, with its SHA-256 in §15. Later changes go only into the deviations log (§14).

**Role in the thesis:**
- **Alexandria** is the discovery study: InSAR velocity concurrent with collapses improved held-out ranking.
- **NYC** is a preregistered replication that tested motion *before* collapse. It was not replicated (p = 0.418), and the direction was opposite.
- **Miami** showed that administrative "unsafe structure" records rarely describe ground or foundation movement. Only 26 documented cases were found in 6,667. The work is parked (`miami/audit/settlement/`).
- **Austin** keeps the same question, as the supervisor decided on 2026-10-28, with an outcome tied to the mechanism InSAR can see: foundation movement.

**How the supervisor's guidance of 2026-10-30 is implemented:**
- the permit date is a delayed administrative observation;
- an area-level count analysis with eligible buildings as exposure;
- a property-level analysis where building characteristics exist;
- prespecified lags;
- physical indicators and statistical models before any deep learning.

**Design summary.** Every hierarchy and choice below is the authors' methodological choice, with its reason. None of it was specified by the supervisor. The user approves the plan before freezing. The supervisor is consulted only if the work is blocked (as in §6).
1. **Outcome:** the first recorded qualifying foundation-repair permit in the City's issued-permit records, dated by its application date (§4).
   - Its date is treated as a **delayed administrative observation** of when damage was discovered, not the date damage occurred.
   - A parcel without a recorded permit has a valid zero for this outcome. It is never read as "undamaged". Neither analysis predicts when cracks appear.
2. **Primary analysis: Test A (property level).** Key secondary analysis: **Test B (area level)** (§1, §11).
   - **Test A, where:** does ground motion improve the held-out ranking of the parcel that records a repair, beyond building, soil, terrain, location and neighbourhood income? Its output is the relative likelihood of a *recorded repair permit*. Building susceptibility to damage is the motivation, not the claim.
   - **Test B, when:** within the same 250 m area, does the rate of recorded repair permits rise after periods of greater ground motion? This uses Poisson regression of quarterly counts of recorded repair permits (by application date), with the number of eligible houses at risk as exposure.
   - **Why Test A is primary:**
     - It answers the thesis question directly: does InSAR before the outcome improve the held-out location of that outcome? Test B measures a within-area association over time, not held-out prediction.
     - It keeps the result comparable with Alexandria and NYC, which used the same test.
     - It uses the finest data available: each property's own pixel and building characteristics.
     - Test B's power depends on how much motion varies over time within an area beyond the city-wide pattern. That cannot be known before InSAR is processed, so a decision resting on Test B could be uninformative.
   - **Why Test B is the key secondary analysis, and not one among many:**
     - It is the design least exposed to the main weakness of permit data. Comparing each area with itself removes everything about the area that does not change, such as soil, house age and income.
     - It is fully prespecified (model, window, exposure, null and reading) and is reported whatever its result.
   - Only Test A carries the decision, so no multiple-testing correction is applied. Test B's p-value is nominal secondary evidence, and a positive Test B never stands in for Test A.
3. **Unit:**
   - Test A uses the single-family parcel, with the 30 m pixel at the parcel.
   - Test B uses 250 m cells by calendar quarter.
   - Parcel coordinates come from the TCAD parcel polygons (§5).
4. **Primary indicator and window:** trend velocity, over the 24 months before the event month (Test A) or the 12 months before the quarter (Test B).
   - Velocity keeps continuity with Alexandria and NYC.
   - The other physical indicators (seasonal amplitude, local relative motion, acceleration) form one fixed list for both tests (§7) and are secondary.
5. **Lags:** windows ending 1, 3, 6 and 12 months before the event month or quarter, beside lag 0. All five are reported, and none is chosen after the results (§12). They are analysis windows, not estimates of the true delay.
6. **Controls in Test A:** 50 sampled per event (a nested case-control design), because every risk set holds about 145,000 parcels (§8).
7. **Deep learning:** not a starting point. A temporal model is the last secondary analysis, run only after everything else, and carries no decision (§12).
8. **Checks that make the result readable** (§4, §7, §11). None of them changes the decision.
   - **Clay contrast:** does InSAR's seasonal amplitude separate the soil classes? This is outcome-blind.
   - **Permits and drought:** do repairs follow droughts? Permits only.
   - **Negative control:** remodel permits, giving a specificity check with its effect size. Passing the check does not prove the result is free of owner or reporting bias.
   - **Sale-triggered and owner-initiated repairs:** the two are split in a secondary analysis.
9. **Reference data: historical TCAD rolls are preferred but not required.** The order below was approved by the user on 2026-10-31. Options and evidence are in `step0/REFERENCE_DATA_OPTIONS.md`.
   - **The official request stays active, with the certified 2018 roll as its priority.**
     - The request for the certified rolls 2016–2025 was sent under the Texas Public Information Act on 2026-10-30 (text: `step0/TCAD_PIA_REQUEST_draft.md`; TCAD reference R010955-110226).
     - On 2026-11-06 TCAD quoted 22 files at $4 each. The user narrowed the request the same day to the certified 2018 roll export and the 2018 parcel layer (expected about $8, revised estimate awaited), and withdrew the other years.
     - Without the yearly rolls, the sale analysis (secondary 14) is not expected to run (§4).
     - **Scheduling (the authors' choice):** checkpoint 1 starts when the 2018 files are in hand, or earlier if the user decides to proceed under C. The freeze does not wait.
   - **Order:**
     - **A, the TCAD certified 2018 roll,** if it is in hand when checkpoint 1 starts. The study period starts on 2018-08-01.
     - **Otherwise C, registered as the fallback:** the public TxGIO 2019 parcel layer, with characteristics verified stable (§5). Eligibility begins after September 2019, so the study period starts on 2019-10-01 and the population is fixed before every event.
     - The 2026 roll alone (D) is not used as the reference, because it cannot remove survivor bias.
   - **Every option:**
     - uses only pre-event or verified-stable characteristics in prespecified analyses;
     - keeps demolished houses at risk until their demolition, and examines demolition as a possibly informative competing outcome (§5, §12 D1–D2);
     - drops analyses that need records that are not available. For example, the sale analysis needs yearly deed records, which a single 2018 roll does not provide (§4).
10. **Townhouses:** the primary population is detached single-family houses only (TCAD improvement type 01). Townhouses (type 16), which TCAD also codes A1, are left out (§5). They share walls and foundations on small lots, and one 30 m pixel covers several units.
11. **What completes the thesis:**
    - Test A with its null and bootstrap, and Test B with its null;
    - the label audit, the parcel link check, the coverage report, the remodel negative controls, and the survivorship and link checks;
    - under option C, sensitivity P0.
    - Everything else is additional and may be reported as not run (§13).

**Outstanding data limitations** (open at 2026-10-30; each is resolved or reported before or at checkpoint 1):
1. **Historical property records:** no certified TCAD roll from before the study start is in hand yet, and the request is pending. The registered fallback (C) has these limits:
   - **Shorter study period:** it starts on 2019-10-01 instead of 2018-08-01, about 14 months (16%) shorter.
   - **Fewer baseline characteristics:** living area and foundation type have no verifiable pre-event source. They are out of Baseline 1, and any use of their 2026 values is exploratory (§9).
   - **No sale analysis:** there are no yearly deed records, so secondary 14 is removed (§4).
   - **Identifier changes:** in any source, a parcel whose property ID changes (replat, split, merger) can lose the link to its later permits. A documented outcome-blind crosswalk was built (`step0/ID_CROSSWALK.md`, §5). It recovers little: no house by `geo_id` under a new property ID, and 21 renumbered, 126 merged and 49 split lots by polygon overlap. 1,891 houses stay unresolved, and the roll export has no previous-ID field. Lost permits at changed accounts are measured by the link check, and sensitivity P1 shows how much the result depends on them (§5, §12).
   - **The "missing 1.4%" is reconciled:** 2,152 houses of 2019 keep their property ID and recorded year built and are townhouses (type 16) in 2026. They are the same buildings, not lost houses, and are left out under C (§5). The other 5,736 houses outside the 2026 detached population (rebuilt, no longer A1, split, merged, unresolved and smaller groups) stay in (`step0/ID_CROSSWALK.md`).
2. **Parcel link for the qualifying repairs:** the 87% match rate (step 0) is for permits of all types. The rate for the repair permits themselves is measured at checkpoint 1 (§4).
3. **Event count:** unknown until checkpoint 1. Below 300 events, the plan returns to the supervisor (§6).
4. **InSAR coverage at houses:** unknown until step 3. Vegetation and coherence loss may leave some houses or areas without valid pixels. A coordinate inside the satellite frame does not guarantee a usable measurement there.
5. **Under-recording:** unpermitted repairs and unrepaired damage cannot be measured. They are not errors in the recorded-permit outcome, but they limit any reading as physical damage (§4).
6. **Neighbourhood income** is an estimate for a block group, with sampling error, not a household value (§9).
   - It is available for 99.97% of detached houses (block group or tract).
   - Its median relative margin of error is 0.26.
7. **Satellite geometry:** one ascending track gives line-of-sight motion only. Vertical and east–west motion cannot be separated.

## 1. Questions

A recorded repair permit shows that an owner applied for, and was issued, a permit to repair a foundation. Damage may have begun months or years earlier, and many damaged houses never get a permit. The study therefore does not predict when cracks appear. It asks two questions about ground motion measured by InSAR *before* the recorded permits:

- **A. Where (primary).** Does line-of-sight motion in the 24 months before a recorded foundation-repair permit (dated by its application) improve the held-out ranking of the parcel that records it? The improvement must be beyond a baseline of building, soil, terrain, location and neighbourhood-income features, among Austin single-family parcels. The answer concerns the likelihood of a recorded repair permit, not independently validated physical damage.
- **B. When (key secondary).** Within the same 250 m area, is the rate of recorded repair permits higher in quarters that follow greater ground motion? The comparison is with other quarters in that area, after removing the city-wide pattern of each quarter. Drought years, for example, raise repairs everywhere.

Why A is primary and B is the key secondary analysis is set out in the design summary (point 2). It is the authors' choice.

Question A is the NYC question with one change: the outcome is a foundation repair, not a collapse. That outcome is about ground or foundation movement by construction. A null result here is therefore harder to explain by a mismatch between outcome and signal than NYC's was.

Question B compares each area with itself. Soil, house age, income and anything else about an area that does not change over the study period cannot explain its result. Changes within an area over time, such as a wave of house sales, still can; the remodel negative control (§11) checks for this.

## 2. Prior work and the gap

The studies and the four-part gap are those of `nyc/NYC_REPLICATION_PLAN.md` §2:
1. independent outcome validation;
2. InSAR that precedes the outcome;
3. spatial controls;
4. replication across cities.

A focused literature check (step 0, 2026-10-28; 25 studies, every DOI checked against Crossref; `step0/LITERATURE.md`) found no study that combines the four parts for this outcome. It was a targeted check, not a systematic review. What exists, separately:
- **InSAR measuring shrink–swell, with no damage or repair record:** e.g. Burnol et al. 2021 (France), Scoular et al. 2019 (London Clay, where persistent scatterers could not statistically separate shrink–swell classes), and a central Texas site (Glaser et al. 2025, abstract only).
- **InSAR with a damage survey:** fragility curves fitted on the surveyed buildings, with motion that does not end before the damage (Peduto et al. 2019, soft clay and peat in four Dutch cities; Ezquerro et al. 2020, Pistoia). None is a held-out test against building, soil, terrain and location.
- **Texas foundation-repair records against soil or geology, without InSAR:** Hudak 1998 (78 contractor addresses, Denton) and Williams 2008 (Dallas–Fort Worth).
- **Clay-subsidence insurance claims against climate or drought, without InSAR:** Harrison et al. 2012 (south-east England) and Barthélemy et al. 2024 (France).

## 3. What is already known about the Austin data (disclosure)

From the readiness check (`feasibility/candidates/READINESS_REPORT.md`, 2026-10-26) and Claude's review of it:
- **Dataset:** Austin "Issued Construction Permits" (`3syk-w9eu`), public domain, 2,381,895 rows.
- **Keyword matches:**
  - 26,797 permits match the foundation keywords after exclusions, of all permit types;
  - 11,734 were issued on or after 2016-07-01;
  - in the matched superset, 7,422 building permits (BP) were issued on or after 2016-07-01, on 6,577 parcels.
- **Precision sample** (seed 20261026, 60 permits read by hand): 42 of 60 are repairs of an existing foundation.
  - Among building permits only: 35 of 41 (85%; 95% CI 71–94%).
  - Among building permits with work class Repair or Remodel: 35 of 38 (92%). The three building permits excluded by that rule (work class New or Addition) were all new construction.
  - Most false matches are plumbing permits for "tunnel under the foundation" drain repairs.
  - **The building-permit and work-class restrictions in §4 were chosen after seeing this sample.** They rest on label quality only, not on InSAR. The 38-permit figure is a small sample; the label audit (§4) re-estimates precision on the final events.
- **Satellite coverage:** OPERA DISP-S1 frame 28482 (track 107, ascending) contains every geocoded matched permit point. It has 254 granules, 2016-07-10 to 2025-11-20 (CMR metadata only; no granule opened).
- **TCAD data (step 0, 2026-10-28; `step0/TCAD_AVAILABILITY.md`):**
  - **Rolls:** the only full certified roll publicly downloadable now is 2026. No certified roll dated 2016 or earlier could be obtained without the user's action (a records request or purchase). A public research copy of the 2018 *preliminary* export exists; it is not official.
  - **Permit link:** `tcad_id` in the permit table is TCAD's `geo_id`, not `prop_id`. A random 500 permits of all types (seed 2032) matched the 2026 roll exactly for 436 (87.2%).
  - **Fields in the 2026 roll:** deed date 99.5% filled (one roll gives only the latest transfer); year built, living area and lot area about 100%; foundation type (slab, pier and beam, other) 94.6% of the diagnostic population below.
  - **Diagnostic population, from the 2026 roll:** 146,857 A1 parcels with main dwelling built by 2015 have centroids inside the full-purpose boundary (version of 2026-10-27). They occupy 112,072 unique 30 m cells. A1 includes 2,399 townhouses (TCAD improvement type 16). Without them, which is the primary population (§5), there are 144,458 parcels in 111,039 cells.
  - These counts read no permit outcome and no InSAR value.
- **Not yet known:**
  - the event count under §4;
  - the parcel population in the reference roll (§5);
  - any baseline feature;
  - any InSAR value.

## 4. Outcome

- **Source:** the copy of `3syk-w9eu` downloaded at checkpoint 1 (§13). It is hashed, with its download date.
- **What the outcome is:** the first recorded qualifying permit in the City's dataset of *issued* permits, dated by its application date.
  - Applications that were refused, withdrawn or never issued are not in the dataset.
  - "First" means first observed in these records (from 1980), not necessarily the house's first physical repair.
  - A house without a recorded permit has a valid zero for this outcome. That zero is not a claim that the house is undamaged.
- **Event rule** (scripted at checkpoint 1, unchanged after freezing):
  1. **Building permits for repair or remodel only:** `permittype` = BP and `work_class` is Repair or Remodel. This excludes New, Demolition, Addition, Addition and Remodel, Shell and Relocation.
  2. **Keywords and exclusions:** the locked regex and exclusion rules of `feasibility/candidates/keyword_protocol.md` (2026-10-26), on the same five fields.
  3. **Residential:** `permit_class_mapped` = Residential.
  4. **Parcel:** a non-blank `tcad_id` that matches a parcel of the reference roll (§5) in the primary population.
  5. **Event date *t_e*:** the application date (`applieddate`). If it is missing, the issue date is used, and that is counted.
  6. **One episode:** matched permits on the same parcel within 365 days are one episode, dated by the first.
  7. **First repair only:** the parcel's earliest matched episode in the whole record (from 1980) is its event. A parcel whose first episode falls before the study period is never a case and never a control.
  8. **No recent construction on the parcel:** events are excluded when the same parcel has a BP with work class New, Demolition, Addition, Addition and Remodel, Shell or Relocation dated in the 3 years before *t_e*.
- **Study period:** *t_e* from 2018-08-01 (reference option A) or 2019-10-01 (option C, §5) to 2025-11-30. The 24-month window (§7) must start on or after the first granule (2016-07-10) and end before the last granule plus 12 days.
- **Label audit before InSAR:** 100 events drawn with seed 2028 are read by hand and classed with the categories of the readiness check. The precision and its 95% CI are reported. Events are not removed because of the audit.
- **Parcel link check before InSAR:** the step-0 match rate (436/500, 87%) came from permits of all types.
  - At checkpoint 1, the share of permits meeting rules 1–3 whose `tcad_id` matches a parcel of the reference roll is reported, with a 95% CI.
  - It is reported overall and by the parcel's matching status (matched to the primary population, matched to another parcel type, unmatched).
  - It is reported only. Unmatched permits are not repaired by hand or by address matching.
- **Permits and drought (labels only, before InSAR):** clay shrinks in drought, so repairs should follow dry years.
  - **Measure:** the Spearman correlation between annual counts of matched repair permits (issue year 2008–2025, building permits with the work-class rule) and the previous year's mean Palmer Drought Severity Index for the NOAA climate division that contains Austin.
  - **Expected:** negative. Drier years are followed by more repairs.
  - This is reported only. It supports reading the permits as a record of ground movement, but it does not change any rule.
- **Sale-triggered and owner-initiated repairs** (secondary analysis 14):
  - **Condition:** it runs only if certified yearly rolls with deed dates for every year from the year before the study start to 2025 are in hand when checkpoint 1 starts. A single 2018 roll does not provide sale histories, so option A alone does not qualify.
  - **Rule:** a transfer is a change in the deed date between consecutive yearly rolls. An event within 183 days after a transfer is *sale-triggered*. Other events are *owner-initiated*.
  - **Otherwise:** secondary 14 is removed. No partial substitute (for example, the 2026 latest deed date) is used.
- **Negative-control outcome: remodel permits** (§11). These involve the same owner behaviour (cost, sales, following permit rules) with no ground mechanism.
  - **Matching permits:** residential BPs with work class Remodel whose description matches `kitchen|bath(?:room)?|cabinet|counter ?top|interior remodel` (case-insensitive) and does not match the foundation regex.
  - **Rules:** the episode, first-event, recent-construction and study-period rules above apply unchanged.
  - **Sample:** as many control events as there are foundation events, drawn with seed 2031, with the same count in every calendar month.
- **Known limits:**
  - A permit records the owner's decision to repair. Its date is a delayed indicator of when damage was discovered, not when it occurred. Its timing follows sales, inspections and income as well as distress.
  - The absence of a permit does not show that a house is undamaged. Unpermitted repairs and unrepaired damage are outside the outcome. They are not errors in the recorded-permit outcome, but they limit any reading as physical damage.
    - If this under-recording is unrelated to ground motion, it weakens both tests but does not create a false positive.
    - If it follows income, which in Austin also follows geology, it could. Neighbourhood income in Baseline 1, the remodel negative control and Test B's area fixed effects address this.
  - Some matched permits are maintenance or have causes unrelated to ground movement. The label audit estimates their share.
  - These limits are reported. The rules above are not revised for them.

## 5. Parcels and eligibility

- **Reference data** (order approved by the user on 2026-10-31; options, evidence and reasons in `step0/REFERENCE_DATA_OPTIONS.md`): fixed when checkpoint 1 starts, from what is in hand then, in this order.
  - **A. TCAD certified roll for tax year 2018** (or the latest year up to 2018 that TCAD sends), with its parcel layer.
    - It describes each property on 1 January 2018, before the study starts.
    - All features in §9 come from it.
  - **C. TxGIO StratMap 2019 parcel layer for Travis County** (tax year 2019, extracted September 2019; the public copy downloaded in step 0, hashed at checkpoint 1). This is the registered fallback.
    - **Eligibility begins after September 2019:** the study period starts on 2019-10-01 (§4). Every population fact therefore predates every event.
    - **Population:** A1, built by 2015 (2019 value), with the centroid of its 2019 polygon inside the study area: 151,944 houses (step 0).
      - Membership is fixed from 2019 data alone. A house stays in whatever became of its account by 2026: rebuilt, reclassified, split, merged, or with no 2026 match.
      - The population is described as **A1 historical houses**. The 2019 layer has no improvement type, so it cannot prove that every house was detached.
    - **Townhouse exclusion:** left out are the 2,152 houses whose property ID is unchanged in 2026, whose 2026 main improvement is a townhouse (type 16), and whose recorded year built is the same in both years.
      - **Registered assumption:** an unchanged recorded year built means an unchanged building, so these houses were townhouses in 2019 too. This is an assumption, not established history.
      - All other houses stay in. Where their 2019 type cannot be checked (rebuilt, reclassified, split, merged or unmatched), it is reported as unknown, not as detached.
      - **Survivor bias in this step:** only houses whose account survived can be checked, so townhouses demolished or renumbered before 2026 stay in. Sensitivity P0 (§12) drops the exclusion and uses no 2026 information at all.
    - **Stable characteristics:** year built and lot area come from this layer. Both are verified stable between 2019 and 2026 for the same houses: year built is identical for 99.7%, and lot area is within 1% for 96.5%.
    - Living area and foundation type are not in Baseline 1 (§9).
    - **Identifier crosswalk** (`step0/ID_CROSSWALK.md`, `step0/id_crosswalk.json`, from `step0/scripts_refdata/id_crosswalk.py`). It is outcome-blind: no permit, InSAR or outcome data were read. It was built by a Codex worker, and Claude's rerun reproduced its output byte for byte.
      - **Stages and result:**
        - same property ID: 149,857 houses, all with the same `geo_id`;
        - the same `geo_id` under a new property ID: none;
        - polygon overlap: 21 one-to-one renumberings, 126 merged lots and 49 split lots;
        - unresolved: 1,891.
      - **Why 1,891 are unresolved:** not a misregistration between the layers (same-ID polygons agree, median IoU 0.999997) and not missing pages. Most (1,837) fall in gaps of the 2026 hosted layer.
        - Condominium conversion, re-subdivision and address-confidentiality suppression are plausible causes, but none is verified.
        - The roll export has no previous- or parent-ID field.
      - **Registered rule:**
        1. **Population:** fixed from 2019 alone (above). The crosswalk enters only the townhouse exclusion, and only through stage 1 (same property ID).
        2. **Permit linkage:** a permit links to a 2019 house through that house's 2019 `geo_id`, whatever happened to the account later.
        3. **Ambiguous keys:** three 2019 `geo_id`s each belong to two houses (six houses, none in the townhouse group). Their permits cannot be allocated, so the six are left out of the population.
        4. **Split and merged lots:** permits filed under a successor's new key are not given to any 2019 house, and are not shared out by area. The 2019 house keeps the permits filed under its own key.
        5. **Renumberings:** the new keys of the 21 renumbered lots are not used. The number of qualifying events filed under the 19 that are in the certified 2026 roll is reported at checkpoint 1 (geometry alone cannot date when the new key began).
        6. **No 2026 match is not demolition:** an unresolved or changed account stays in the population and at risk. Only a total demolition permit ends time at risk. No demolition date is inferred from the 2026 roll.
      - **Primary population under C:** 151,944 − 2,152 townhouses − 6 ambiguous keys = **149,786 houses** (step-0 count; recounted at checkpoint 1).
      - **Under option A,** permits link through the 2018 `geo_id` by rules 2–4 and 6. No 2026 information enters A's population.
  - **Later arrivals:** rolls that arrive after checkpoint 1 starts are not used in any prespecified analysis. Anything done with them is exploratory.
- **Demolition (at risk):** an eligible house stops being at risk on the date of its first total-demolition permit after the study start (application date; issue date if missing). This is an administrative censoring date: the permit does not show when the house was actually removed.
  - **Definition:** a total demolition is a residential BP with work class Demolition whose description does not match `\bpartial\b` (case-insensitive).
  - **Audit:** at checkpoint 1, 50 such permits (seed 2036) are read by hand, and the share that demolish the main house is reported with its 95% CI.
  - **Effect:** through the shared at-risk rule (§8), the house leaves the Test A control pool for later risk sets, and the Test B exposure *n* from the next quarter. Demolition censoring is counted and reported.
- **Is demolition an informative competing outcome?** The censoring rule above assumes demolition is unrelated to foundation trouble. That assumption is examined, not presumed.
  - **At checkpoint 1, from permits only, before any InSAR value:**
    - **(a) Foundation mentions:** the share of total-demolition permits whose description matches the locked foundation regex (§4 rule 2), with its 95% CI.
    - **(b) Demolition after a repair:** the demolition rate per house-year among eligible houses after a matched foundation episode, against houses without one. Person-time is split at the episode date, and the comparison is a Mantel–Haenszel rate ratio over building-age deciles, with its 95% CI.
  - **With InSAR:** secondary analyses D1–D2 (§12) test whether ground motion predicts demolition, and how the result changes when demolition is treated as part of the outcome.
  - **Reading:** if (b) gives a rate ratio above 1 with an interval excluding 1, or D1 associates motion with demolition, censoring may be informative. The primary result is then reported with that caveat, and D2 shows how the result changes when demolition counts as part of the outcome. No decision changes.
- **Survivorship check** (checkpoint 1, reported only):
  - the number and share of events (§4 rules 1–3) at reference-population houses that are no longer in the 2026 detached population;
  - the number of houses censored by demolition;
  - **link check:** permits of all types per house-year linked through reference-year keys, by year and by crosswalk category (option C: the categories of `step0/ID_CROSSWALK.md`; option A: 2018 property ID present or absent in the 2026 roll). A falling rate at changed or unresolved accounts shows permits lost to key changes. Sensitivity P1 (§12) shows how much the result depends on it.
- **Study area:** the City of Austin full-purpose jurisdiction (official boundary, downloaded and hashed at checkpoint 1), within frame 28482.
- **Primary population:** single-family residential parcels (TCAD state code A1 or its equivalent in the roll) whose main improvement is a detached single-family dwelling (improvement type 01, "1 FAM DWELLING"), with a recorded year built of 2015 or earlier.
  - **Main improvement:** the type 01 improvement with the largest living area (floor codes 1/2, 1ST, 2ND, 3RD, 4TH, 5TH, ADDL), ties broken by improvement ID. Year built is that of its first floor (zero is missing).
  - Parcels whose main improvement is a townhouse (type 16) are left out. Townhouses share walls and foundations on small lots, and one 30 m pixel covers several units.
  - Under option C, the population is the 2019 one defined under reference data above.
- **Parcel point:** the centroid of the parcel polygon, in EPSG:32614 (UTM 14N).
- **Eligible:** a parcel in the primary population with a valid parcel point inside the study area.

## 6. Population size check

The number of events meeting §4 inside the primary population is computed once, at checkpoint 1, before any InSAR value. If it is below 300, the plan returns to the supervisor before the InSAR step. There is no other switch.

## 7. InSAR (processed blind to outcomes)

**Product:** OPERA L3 DISP-S1 v1 (CMR C3294057315-ASF), frame 28482, plus its STATIC layers. Subsets are clipped to the study area plus a 2 km buffer.

**Processing:** as NYC §7, steps 1–3, unchanged:
- the full `displacement` layer;
- the recommended mask and water mask;
- re-referencing across reference-date changes;
- connected-component validity.

Velocities stay in line of sight, positive toward the satellite.

**Construction mask:** for each window, pixels within 50 m of a parcel with a BP of work class New, Demolition, Addition, Addition and Remodel, Shell or Relocation are dropped. This applies to permits issued from 365 days before the window start to the window end.

**Windows:**
- For an event in calendar month *m*, the window is the 24 months ending on the last day before the first day of *m*.
- Events in the same month share one window. That gives one window per study month: 88 under option A (2018-08 to 2025-11), and 74 under option C (2019-10 to 2025-11).
- Only acquisitions inside the window are used, so every value precedes *t_e*.

**Window fit:** the NYC fit d = a + v·t + b·sin(2πt/365.25) + c·cos(2πt/365.25), with the NYC completeness rule: valid on at least 80% of dates and at least once in each 91-day quarter.

**Physical indicators** (one fixed list, used by both tests):
1. **Trend velocity** v, from the window fit. This is the primary indicator of both tests.
2. **Seasonal amplitude** √(b² + c²), from the window fit. It is the seasonal swing of the pixel, expected to reflect shrink–swell where the clay contrast check (below) is demonstrated.
3. **Local relative motion:**
   - for a parcel, its pixel's velocity minus the median of valid pixels 60–250 m away;
   - for a 250 m cell, the interquartile range of the velocities of its valid parcel pixels.

   This is motion relative to the surroundings, at the 30 m pixel scale. It is **not** differential settlement across a foundation, which needs deformation measured within the building (as in settlement–damage studies) and which 30 m pixels cannot resolve.
4. **Acceleration:** the velocity of the last 12 months of the window minus that of the 12 months before them.

These are proposed features of the ground near a house, not measures of damage.

**Parcel value:** the value of the pixel whose centre is nearest the parcel point. If that pixel is invalid for the window, the parcel has no value for that window. Neighbouring parcels can share a pixel.

**Cell value (Test B):**
- **Cells:** the UTM 14N grid of 250 m cells with edges at multiples of 250 m. A cell is used if it holds at least one eligible parcel point.
- **Value:** the mean of the parcel values of its eligible parcels, in mm/yr (each parcel counted once, so a pixel shared by several parcels is weighted by them).
- **Missing:** a cell with fewer than 3 parcel values in a window has no value for that window.

**Window standardisation (Test A,** as NYC, over all eligible parcels with a value): subtract the window median, divide by the interquartile range, and winsorise at the 0.5th and 99.5th percentiles. There are no landmass groups. Test B uses raw mm/yr, because its quarter fixed effects remove each quarter's city-wide level.

**Windows:**
- **Test A:** as above, 24 months ending before the event month (one window per study month).
- **Test B:** the 12 months ending on the day before each calendar quarter starts. The quarters are the complete quarters inside the study period: 28 under option A (2018-Q4 to 2025-Q3) and 24 under option C (2019-Q4 to 2025-Q3).
  - Twelve months is one full seasonal cycle, so trend and seasonal swing can be separated. It is short enough for a cell's velocity to change from year to year, which Test B needs.

**Lagged windows** (§12): the same windows, ending 1, 3, 6 or 12 months earlier. Each lag uses only the events whose window starts on or after the first granule.

**Other windows,** with the same rules:
- Test A: 12 months, for continuity with NYC, on the same events as the primary analysis; and 36 months, for events from 2019-08 (all events under option C).
- Test B: 24 months.

**Checks before outcomes are joined:**
- **Sign check:** the full-period velocity of closed or active landfill footprints in the study area (TCEQ municipal solid waste sites, downloaded at checkpoint 1) is compared with the area median. Settling landfills should move away from the satellite.
  - If the landfills are not below the median, work stops until the cause is found and logged.
  - If no landfill falls in the subset, this is recorded and the check is skipped.
- **Clay contrast check:** does InSAR's seasonal amplitude separate the soil classes? This uses no outcome.
  - For every pixel holding an eligible parcel point, the seasonal amplitude √(b² + c²) is fitted over the full series (2016-07 to 2025-11).
  - Parcels are grouped by SSURGO linear extensibility into the NRCS shrink–swell classes: low (< 3%), moderate (3–6%), high (6–9%) and very high (≥ 9%).
  - **Contrast demonstrated** if the median amplitude of the high and very high classes exceeds that of the low class, with a 95% block-bootstrap interval (2 km blocks) above zero. **Not demonstrated** otherwise.
  - The label is reported before outcomes are joined. It sets how a null result is read (§11) and changes nothing else.
  - A demonstrated contrast supports reading the seasonal signal as clay movement at the level of soil classes. It is a diagnostic, not a physical validation of each house's motion.
- **Coverage report:** valid-parcel counts per window.
- **Variogram check** (§10).
- **Allowed changes:** as NYC. Processing may be corrected after these checks and logged, never after any comparison with outcomes.

## 8. Designs

**Shared at-risk rule** (Tests A and B, the negative controls and D1–D2). A house is at risk of a first recorded permit at date *t* if:
1. it is in the primary population and eligible (§5);
2. it is not demolition-censored on or before *t* (§5);
3. it has no matched foundation episode (§4 rules 1–4 and 6, any date from 1980) on or before *t*, whether or not that episode became an event.

A house whose first matched episode is not an event (for example, excluded by rule 8 for recent construction) therefore leaves both tests at that episode's date and is never a case. One function implements this rule for both tests.

### 8A. Test A: nested case-control risk sets

- **Case:** each event (§4) whose parcel is eligible and has a value in its window.
- **Risk set for event *e*:** the event parcel plus 50 controls.
  - Controls are drawn without replacement (seed 2029, in event order) from eligible parcels with a value in the same window.
  - A control must be at risk at *t_e* under the shared rule above. The case is at risk until *t_e*.
  - A parcel with a later event is a valid control.
  - The draw happens after InSAR values exist, but it uses only eligibility and validity, never the values themselves.
- **Same window:** cases and controls in a risk set take values from one window.
- **Pooling:** rows are (risk set, parcel) pairs. A parcel may be a control in several risk sets.
- **Missing data:** events and draws lost to missing values are counted and reported.
- **Meaning of a control:** a control is a parcel with no recorded qualifying permit by *t_e*. It is not assumed to be undamaged.

### 8B. Test B: area–quarter panel

- **Rows:** (cell, quarter) pairs, for cells used in Test B (§7) and the quarters of §7.
- **Why quarters:** a 250 m cell holds a few dozen houses, and each house can have at most one first repair. Monthly counts per cell would be almost all zeros, so the quarter is the main unit. Monthly counts are run as secondary 19.
- **Count *y*:** the events (§4) whose parcel lies in the cell and whose *t_e* falls in the quarter.
- **Exposure *n*:** the houses in the cell that are at risk under the shared rule at the start of the quarter.
  - Counting houses at the start of the quarter, not house-time within it, is an approximation. It is close because first permits and demolitions are rare within a quarter (about 0.2% of houses).
- **Predictor:** the cell's velocity for the 12 months before the quarter (§7). It is a fixed area field: the pixels of all eligible houses count, whether or not the house is still at risk, so the predictor does not depend on outcomes.
- **Rows used:** the cell has a value for that quarter and *n* > 0. Cells with no event in any quarter add nothing to a model with cell fixed effects. They are counted and reported.
- **Meaning of a zero:** a zero count means no recorded qualifying permit, not no damage. The model estimates a rate of recorded permits, not a rate of damage.

## 9. Features, models, folds, metrics

This section describes Test A, except for the last subsection, which describes Test B.

| Feature | Source (all dated before the study period (§4) unless stated) |
|---|---|
| Building age at *t_e* | Reference roll year built |
| Living area, log | Reference roll (A only; see Baseline 1) |
| Lot area, log | Parcel polygon of the reference data |
| Soil shrink–swell: linear extensibility, weighted 0–150 cm | NRCS SSURGO/gSSURGO for Travis County |
| Terrain slope and elevation | USGS 3DEP 1 m DEM, mean within the parcel |
| Neighbourhood income, log | Median household income of the parcel's 2015 block group, ACS 2011–2015 five-year (B19013, 2015 dollars). The tract median is used where the block-group median is suppressed. |
| Coordinates | Parcel point x, y in km (UTM 14N) |
| Velocity | Window velocity, standardised (§7) |

- **Baseline 1 (primary):** building age, log living area, log lot area, soil shrink–swell, slope and elevation, and log neighbourhood income, plus x/y.
  - Foundation type (slab or pier-and-beam) is also added if the reference roll records it for at least 90% of eligible parcels.
  - **Under reference option C** (§5), living area and foundation type have no verifiable pre-event source, so they are left out of Baseline 1.
    - Any analysis that uses their 2026 values is **exploratory**. It is labelled so, kept out of the secondary list, and not presented as evidence of prospective predictive performance, because those values were recorded after the events.
    - A 2026 value is carried to a 2019 house only if the property ID and the recorded year built are unchanged.
  - This is decided at checkpoint 1, before any InSAR value exists.
- **Neighbourhood income in Baseline 1 is the authors' methodological choice,** made on data availability:
  - **Why include it:**
    - The main alternative explanation of permit data is owner behaviour: who can afford a repair, and who applies for a permit.
    - In Austin, income also follows the east–west geology, so leaving it out could let ground motion take credit for income.
    - Including it makes the test of InSAR's added value stricter.
  - **Why the data allow it:**
    - The ACS 2011–2015 estimates are public and cover the years before the study period, so no value postdates the events.
    - Coverage was checked in step 0 (`step0/ACS_INCOME_AVAILABILITY.md`; source: the 2015 ACS five-year summary file, because the Census API now requires a key; Claude re-derived every count below independently).
      - Of Travis County's 580 block groups, 568 (97.9%) have a published median; of its 218 tracts, 215 (98.6%).
      - Of the 144,458 detached houses in the 2026 diagnostic:
        - 99.42% have a block-group median;
        - 0.56% (806) take the tract median;
        - 0.03% (39) have neither, 30 of them because their centroid lies outside the county's block groups.
      - The safeguard below is therefore not expected to trigger. It is still applied at checkpoint 1 to the reference-roll population.
  - **Limits:**
    - It is a neighbourhood estimate with sampling error, not a household's income. Its margins of error are reported.
      - Block-group relative margin of error: median 0.26, 90th percentile 0.53.
      - 67 block groups (7.6% of detached houses) have a margin above half the estimate.
    - NYC's Baseline 1 had no income. Secondary analysis 5 reports the Austin result without income, for comparison.
  - **Safeguard:** if, at checkpoint 1, income (with the tract fallback) is missing for more than 10% of eligible parcels, it moves to Baseline 2, and that is logged. This is decided before any InSAR value exists.
- **Baseline 2 (secondary):** Baseline 1 plus:
  - the parcel's count of non-foundation BPs in the 5 years before *t_e*, a proxy for permit propensity;
  - tree canopy share within the parcel, from the City of Austin canopy layer closest to 2016, if one exists at checkpoint 1.
- **Velocity model:** the baseline plus the window velocity.
- **Missing inputs:** as NYC. Rows missing an input of either compared model are left out of that comparison and counted. Both models are fitted on identical rows.
- **Models:** logistic regression as in NYC §9 (primary). Random forest as in NYC §9 (secondary).
- **Folds:** 2 km blocks on the UTM 14N grid, 5 folds by StratifiedGroupKFold (shuffle, seed 42).
  - A parcel's block is the block of the centre of its pixel (§7, parcel value), so parcels that share a pixel are always in the same fold.
  - The label is "parcel holds an event".
  - The fold map is computed once on all eligible parcels.
  - Every row takes its parcel's fold, and all scores are out of fold.
- **Primary metric:** change in pooled out-of-fold PR AUC, from Baseline 1 + x/y to Baseline 1 + x/y + velocity.
  - **PR AUC** in this plan means average precision (scikit-learn `average_precision_score`, as NYC), not the trapezoidal area under the precision–recall curve.
  - **What it measures:** discrimination in the sampled risk sets. The case share (about 1 in 51 rows) is set by the design. The metric compares the two models on those rows. It is not citywide precision, and model scores are not calibrated risks. No population-level precision or risk is reported.
- **Secondary metrics:** as NYC: pooled ROC AUC, both top-10% capture forms (also on the sampled rows), and a refit block bootstrap interval over 2 km blocks.
  - The bootstrap resamples whole 2 km blocks, so all rows of a parcel move together. Risk sets are not kept intact, because the pooled metric does not use them. The interval is conditional on the drawn controls.

### Test B model

- **Model:** Poisson regression of *y* with log *n* as offset, cell fixed effects, quarter fixed effects and the cell velocity. This is fitted by maximum likelihood (PPML, for example pyfixest `fepois`), fixed in `scripts/` before freezing.
  - **Why Poisson:** Poisson pseudo-maximum likelihood with fixed effects stays consistent under overdispersion if the conditional mean is correctly specified. The common conditional negative-binomial fixed-effects model is not a true fixed-effects estimator (Allison and Waterman 2002), and PPML avoids that issue.
  - Overdispersion affects only the errors, which the cluster-robust errors and the null (§10) address. Neither repairs a wrong mean model, omitted time-varying confounding or a wrong exposure.
- **Effect:** the rate ratio per interquartile range of cell velocity (IQR over all used rows), with a 95% interval from errors clustered by 2 km block.
- **Statistic for the null:** the absolute value of the velocity coefficient, |β|.

## 10. Inference: variogram-matching null

### Test A

- **Method:** the conditional variogram null (`scripts/conditional_null.py`), chosen by the user on 2026-11-06 after the calibration below. 999 draws (seed 2027) and the NYC p formula.
  - For each window, velocity on the pixel field is regressed on the pixel means of the Baseline 1 features without x/y, using a fixed gradient-boosting fit (settings fixed in the script, in-sample, no outcome data).
  - The residual field is replaced by variogram-matched surrogates, generated as in NYC §10 with shared randomness across windows. The fitted field is then added back.
  - **Secondary:** the NYC null itself (variogram surrogates of the whole velocity field) is reported beside it with the same draws and seed (§12 item 8). The calibration found it too lenient when velocity tracks a misspecified soil effect.
- **Null hypothesis:** given Baseline 1 + x/y, the parcel's velocity carries no further information about which house records a qualifying permit. The surrogates keep velocity's fitted dependence on the baseline features and the spatial structure of the rest. A gain that velocity gets only by standing in for the baseline features, or that any field with that structure could produce by chance, is therefore not counted as evidence.
- **Calibration before freezing** (synthetic data only; `scripts/calibration/CALIBRATION.md`):
  - **Concern:** surrogates lose the real field's link with the baseline features. If velocity tracks clay and the true clay effect is nonlinear, real velocity could stand in for the unmodelled part of the soil effect. It would then beat the surrogates although it adds nothing beyond the features.
  - **Simulation:** a synthetic city in which velocity depends on soil, terrain and income, and permits depend only on the baseline features.
    - Null scenarios: N1 correctly specified; N2 nonlinear soil effect; N3 a hidden spatial field independent of velocity; N4 = N2 + N3. Each runs at two strengths of the velocity–baseline link, with 200 datasets and 99 draws per dataset, in a small city (5,400 houses, about 216 events per dataset).
    - **Scale cells:** N2 and N4 at the strong link are repeated in a city four times larger (21,600 houses, about 864 events, 100 datasets). A systematic proxy gain grows relative to chance as events increase, and Austin has about 25 times more events than the small city.
    - Power scenarios add an effect of the velocity residual and are reported only.
  - **Nulls compared:**
    - (a) the registered null above;
    - (b) a conditional null (`scripts/conditional_null.py`). It keeps the fitted link between velocity and the baseline features (a fixed gradient-boosting fit per window, without coordinates) and replaces only the residual by variogram-matched surrogates.
  - **Acceptable** in a null scenario (scale cells included) if all three hold:
    - the rejection rate's lower 95% Wilson bound is at most 0.05;
    - its point estimate is at most 0.075 (with 99 draws the exact nominal rate is 0.04);
    - no positive bias is detected: per dataset, the observed statistic minus the mean of its null draws, averaged over datasets, has a 95% interval whose lower bound is at most 0.
  - **Rule** (registered 2026-11-01, before any calibration result):
    1. If (a) is acceptable in every null scenario, it stays primary, and (b) is reported as a secondary null.
    2. Otherwise, if (b) is acceptable in every null scenario, (b) becomes the primary null with the same draws and seed, and (a) is secondary.
    3. Otherwise neither is primary yet, and the user decides before freezing.
  - **Result** (`scripts/calibration/CALIBRATION.md`; the selection was rechecked independently by Claude): **branch 3.** Rejection rates are per cell, with the nominal rate 0.04 for the calibration's 99 draws (0.049 with the study's 999).
    - **(a), the NYC null, was not acceptable in six of ten cells.** With a nonlinear soil effect and the strong link it rejected 20% (N2) and 14.5% (N4) of datasets in the small city, and 30% and 29% in the larger city. It also showed positive bias in N2 and N3 at the moderate link. The inflation grew with the number of events.
    - **(b), the conditional null, kept the rejection rate at 0–5% in all ten cells.** It failed only the bias criterion, in one cell: N3 at the moderate link (a hidden spatial field independent of velocity). There, the mean bias was +0.00028 in average precision, about a quarter of the null's spread, with 95% interval +0.00008 to +0.00048. The rejection rate in that cell was 4.0%, and only 42% of datasets had a positive bias. Null (a) showed the same pattern there, twice as large.
    - **Choice:** neither null was primary under the rule, so the user decided (rule 3). On 2026-11-06 the user chose (b) as primary, with (a) as secondary.
    - **Limits:**
      - N3-moderate's bias is reported, not resolved. Chance is one explanation: a one-sided 2.5% criterion across ten cells fails at least once about 22% of the time even for an unbiased null. Another is that surrogates matched to a 480 m range reproduce a smoother hidden field less well than real velocity does.
      - (b) rejected none of 100 datasets in either larger-city cell, so it may be conservative at Austin's size.
      - **(b) has less power.** In the power scenarios (N1 at the strong link plus an effect of the velocity residual; small city, 100 datasets each), (b) detected the effect in 18% of datasets at β = −0.2 and 60% at β = −0.4; (a) detected it in 35% and 84%. (a) is acceptable in N1, so the difference is a cost of (b), not leniency of (a). Under (b) the null draws themselves gained (mean +0.0030 in average precision at β = −0.4, against +0.0080 observed). This is consistent with the in-sample fit absorbing part of the residual effect into the field that every surrogate keeps. Power did not enter the rule, and the user's choice was made before the power cells finished.
      - Austin has about 25 times the small city's events; the larger city has 4 times. Behaviour at Austin's size is extrapolated.
      - The scenarios are synthetic. They cannot show every way the real velocity field relates to the features.
- **Field:** the field is the set of unique pixels holding at least one eligible parcel point. Surrogates are generated on pixels and read at the parcels. This keeps parcels that share a pixel identical, as in the data.
  - For the conditional null's fit, a pixel's features are the means over its parcels with complete Baseline 1 inputs (§9, missing inputs). A pixel with no such parcel is left out of the field and counted.
- **Compute:** this runs on the project GPU with the NYC CuPy implementation, in its memory-lean form (`scripts/lowmem_null.py`, a byte-identical copy of `step0/timing/lowmem_null.py`).
  - The NYC class keeps a dense float64 mask of valid cell pairs per window. At Austin's size that is 10.8 GB, plus an equal copy, and it does not fit in 24 GB.
  - The memory-lean form stores the mask as true/false and works through 8 windows at a time. Everything else is inherited unchanged.
  - On a test field it gave the same neighbour count on every draw, and surrogates within 1.8e-14 of the NYC class. The NYC class run twice differs from itself by the same order (1.7e-14), because the GPU's sparse routines are not bit-reproducible.
- **Gate before freezing:** a timing test on a synthetic field of the same size, with no InSAR or outcome data.
  - If 999 draws are projected to take more than 5 days, the neighbour cap is lowered from 1,000 to 300.
  - If that is still more than 5 days, the draws fall to 499.
  - The chosen setting is recorded in §15 before freezing.
  - **Result (2026-10-30, `step0/timing/`):** detached-house diagnostic, 111,039 cells and 88 windows, neighbour cap 1,000. Setup took 78 s and each draw 6.9 s, so 999 draws are projected at 1.9 hours. **The setting stays at a cap of 1,000 and 999 draws.** The surrogate file is about 39 GB on disk.
  - **Conditional null:** its draws are the same generator applied to the residual field, so the draw cost above applies. Its added cost is one gradient-boosting fit per window, which runs on the CPU.
    - **Result (2026-11-06, `step0/timing/conditional_timing.py`, `conditional_timing_88w.json`):** the production class, with a stand-in for the variogram generator, on synthetic fields of the same size (111,039 pixels, 88 windows, 7 features, 20 CPU threads). The 88 fits took 23 s (0.26 s per window), adding the fitted field back took 0.04 s per draw, and peak memory was 1.3 GB. With the generator timing above, 999 draws are projected at 2.0 hours, and both nulls together at about 4 hours. Two surrogate files take about 78 GB on disk. **The gate setting is unchanged:** a cap of 1,000 and 999 draws.
- **Variogram check:** as NYC, for 20 windows (seed 7), reported first, and never used to change the null.

### Test B

- **Method:** the same NYC implementation, applied to the cell field.
  - The field is the cells used in Test B, with the quarterly windows of §7 (28 under option A, 24 under option C) sharing one permutation, one neighbour count and one noise vector per draw.
  - Each draw replaces every quarter's cell velocities with surrogates, and the Poisson model is refitted.
  - The surrogates keep the spatial structure of motion. They break the link between an area's own motion history and its own repair history.
- **Draws:** 999, seed 2034.
- **p-value:** p_B = (1 + draws with |β| ≥ observed |β|) / (1 + 999).
- **Variogram check:** as Test A, for 5 quarters (seed 8).
- **Size check before freezing:** the rejection rate of this null on synthetic panels with no velocity effect (overdispersed counts, a hidden cell-by-quarter field) is reported in the calibration report. No switch is attached.
  - **Result (`scripts/calibration/CALIBRATION.md`; 200 panels, 99 draws each):** 5 rejected (2.5%, Wilson 95% interval 1.1–5.7%).
    - With 99 draws, p < 0.05 requires at most 3 draws at or above the observed |β|, so the exact nominal rate in this calibration is 4%. With the study's 999 draws it is 4.9%.
    - No inflation above the nominal level was detected in the tested synthetic scenario. The p-values were close to uniform, and no positive bias was detected (mean +0.0010 in |β|, 95% interval −0.0015 to +0.0035).
    - This is a calibration check of one synthetic scenario, not proof of exact type-I error control.
- **Compute:** a few thousand cells, so no timing gate is needed.

## 11. Decision rule

Only Test A, the primary analysis, carries the study's decision (design summary, point 2).

**Test A (decision).** Added held-out value of InSAR is **demonstrated in Austin** if and only if, in the primary analysis (single-family parcels, logistic regression, Baseline 1 + x/y, 24-month window):
1. the change in PR AUC is positive, **and**
2. the primary null of §10 gives p_A < 0.05.

Otherwise added value is **not demonstrated** in the primary analysis. That is not evidence that ground motion carries no information. The conclusion concerns 24-month trend velocity in this logistic model; other indicators, windows and models are secondary analyses. The change in PR AUC and its interval show whether a useful gain is excluded or the result is inconclusive.

**Test B (key secondary, prespecified reading, no decision).** An association between ground motion and the rate of recorded repair permits is reported as **detected** if p_B < 0.05, and **not detected** otherwise. p_B is nominal secondary evidence.
- The rate ratio per IQR and its 95% interval are always reported, whatever p_B is.
- **Direction,** reported beside the reading:
  - **Concordant** if the rate ratio per IQR is below 1, so more motion away from the satellite (subsidence or shrinkage) is followed by more recorded permits.
  - **Opposite** if it is above 1.

Reported beside the Test A decision, without changing it:
- **Directional concordance:** as NYC. For each risk set, the case's standardised velocity minus the controls' median.
  - **Concordant** if the median of these differences is below zero (relative motion away from the satellite).
  - **Opposite** if it is above zero.
- The same differences in raw mm/yr.
- The largest p across the nulls of §12.8.
- **Specificity check:** the primary analysis is repeated unchanged on the remodel negative control (§4).
  - Its controls are drawn with seed 2030, and the same null is used (999 draws).
  - **Reported:** the negative control's change in PR AUC with its block-bootstrap 95% interval, its p, and its change as a share of the foundation result's change.
  - **Negative-control gain detected** if its change in PR AUC is positive and its p < 0.05; **not detected** otherwise.
  - "Not detected" does not show that remodel permits have no gain, and does not prove that the foundation result is free of owner, income or reporting bias. The effect size and interval are read with it.
  - **Direct comparison** (reported, no decision): the foundation change in PR AUC minus the remodel change, with a 95% interval from the same refit block bootstrap (both analyses refitted on the same resampled blocks). A difference between the two is claimed only from this interval, never from their separate labels.

**Specificity check of Test B:** Test B is repeated unchanged with remodel control events as the counts, using the same null (999 draws, seed 2035).
- **Reported:** its rate ratio per IQR with the cluster-robust 95% interval, and its p.
- **Negative-control association detected** if its p < 0.05; **not detected** otherwise. As for Test A, "not detected" is not proof that bias is absent.
- **Direct comparison** (reported, no decision): the difference between the foundation and remodel log rate ratios per IQR, with a 95% interval from a bootstrap over 2 km blocks (both models refitted on the same resampled blocks).

**Reading each test** (fixed now, so it cannot be argued afterwards). All readings concern *recorded* repair permits. None is a claim about physical damage that has been independently validated, or about cause.

| Test | Decision | Label | Reading |
|---|---|---|---|
| A | Gain demonstrated | Negative control not detected | Velocity adds held-out information about which parcels record a qualifying permit, beyond the baseline, in the sampled risk sets. No comparable remodel gain was detected. Owner or reporting bias is reduced as an explanation, not excluded. |
| A | Gain demonstrated | Negative control detected | Remodel permits show a gain too, so the gain may reflect neighbourhoods or owner behaviour rather than ground motion. It is reported as a predictive gain without a mechanism claim. |
| A | Not demonstrated | Clay contrast demonstrated | The seasonal signal separates the soil classes as expected, yet a gain from 24-month velocity in locating recorded repairs was not demonstrated. The interval of the change shows whether a useful gain is excluded or the result is inconclusive. |
| A | Not demonstrated | Clay contrast not demonstrated | The prespecified soil-class contrast was not demonstrated either, so the result says little about the hypothesis. |
| B | Detected | Negative control not detected | In the same area, recorded permits rise after more motion, beyond city-wide quarters such as drought years. No comparable remodel association was detected. Area-level changes in owner behaviour are reduced as an explanation, not excluded. |
| B | Detected | Negative control detected | Remodel permits follow motion too, so the association may reflect area-level changes in owner behaviour or permit-taking. No mechanism claim. |
| B | Not detected | Clay contrast demonstrated | An association between within-area motion and later recorded permits was not detected at quarterly resolution. The rate-ratio interval shows how large an association remains compatible with the data. |
| B | Not detected | Clay contrast not demonstrated | As for Test A, the result says little about the hypothesis. |

**Reading Test A's decision together with Test B** (Test B never changes the decision):
- **Both:** Test A demonstrated a ranking gain, and Test B detected the within-area association over time.
- **A only:** Test A demonstrated a ranking gain. Test B did not detect the specified within-area association over time.
- **B only:** Test B detected the within-area association. Test A did not demonstrate a ranking gain beyond the baseline.
- **Neither:** read through the clay-contrast label, as in the table, with the effect sizes and intervals.

## 12. Secondary analyses (reported, no decision attached)

**Test A.** Each changes one thing in the Test A primary analysis. Unless stated otherwise, it is tested with the Test A null (999 draws; 500 for tree models).
1. **NYC design:** 250 m cells with risk sets as NYC §8, cell value as the mean of valid pixels, and the event label as any event in the cell. This is for continuity with Alexandria and NYC.
2. **Local controls:** the 50 controls are drawn within 1 km of the case. This asks whether the parcel's own motion matters beyond its neighbourhood.
3. The 12-month window (NYC continuity, same events) and the 36-month window (events from 2019-08).
4. Random forest.
5. **Baseline variants:** Baseline 2; and Baseline 1 without neighbourhood income, which matches NYC's Baseline 1 for comparison.
6. **Other physical indicators** (§7, indicators 2–4), each added alone to Baseline 1:
   - seasonal amplitude;
   - local relative motion;
   - acceleration (all study events).
7. **Boosted trees** (scikit-learn HistGradientBoostingClassifier, defaults, random_state 0), on Baseline 1 plus all four physical indicators.
8. **Other nulls on the primary analysis:** the NYC variogram null, null (a) of the §10 calibration (999 draws, seed 2027, read with the calibration's warning); free and within-block permutation (2,000 draws each); MSR (999).
9. **Lag profile:** the 24-month window ending 1, 3, 6 or 12 months before the event month. Each lag uses the events whose window starts on or after the first granule.
   - The five lags (with lag 0, the primary) are reported together in one table.
   - None is chosen as "best", and none carries a decision.
   - They are analysis windows, not estimates of the true delay between damage and application.
10. Issue date instead of application date.
11. Ten other fold seeds (0–9).
12. **Availability only:** the count of valid pixels within 100 m of the parcel.
13. No construction mask.
14. **Owner-initiated repairs only** (§4). Sale-triggered events are left out. This runs only if certified yearly deed records are in hand at checkpoint 1 (§4); otherwise it is removed. Their timing is expected to lie closer to the movement.

**Test B (key secondary) variants.** Each changes one thing in Test B (§8B–§10) and uses the Test B null (999 draws).

15. **Lag profile:** the 12-month window ending 1, 3, 6 or 12 months before the quarter starts. It is reported with lag 0, as in 9.
16. The 24-month window.
17. **Other physical indicators** (§7, indicators 2–4), each in place of velocity.
18. **Negative binomial with area characteristics:**
    - negative binomial regression with quarter fixed effects, log *n* as offset, and, instead of cell fixed effects, the cell means of the Baseline 1 features (age, log living area, log lot area, soil linear extensibility, slope, elevation, log neighbourhood income, x/y);
    - this compares areas with each other as well as over time, so static confounders are controlled only through these features.
19. **Monthly counts:** the cell counts by calendar month (the study months: 88 under option A, 74 under option C), with month fixed effects and the 12 months before each month. Counts in 250 m cells are very sparse by month, which is why the quarter is the main unit of Test B.

**Demolition as a competing outcome** (Test A design, Test A null, no decision; §5):

- **D1. Demolition as the outcome:**
  - **Cases:** the first total demolitions of eligible houses in the study period.
  - **Controls:** 50 per case, drawn from houses at risk.
  - **Same as the primary:** baseline, windows and comparison.
  - **Question:** does preceding ground motion predict demolition?
- **D2. Composite outcome:** the first of foundation repair or total demolition.

**Population sensitivities, option C only** (Test A design, Test A null, no decision; §5):

- **P0. No 2026 information:** the 2,152 houses of the townhouse exclusion are kept (151,938 houses at step 0). This removes the only 2026 input to the population.
- **P1. Confirmed continuity:** only houses with the same property ID in 2026, in the 2026 detached population, and with the same recorded year built (143,605 houses at step 0).
  - It drops houses whose type or permit linkage is uncertain.
  - It shows how much the result depends on restricting to houses that survived to 2026 and stayed linked. It changes several selection mechanisms at once, so it cannot isolate the direction or size of survivor bias.

**Last, and only if the budget allows** (§13):

20. **Temporal deep model** (Test A rows):
    - **Input:** the parcel pixel's displacement series over the §7 window of the event month (the 24 months ending before the event month; every row of a risk set uses the case's window, as §8A), resampled to 12-day steps, with missing steps masked, alongside Baseline 1. The step grid and referencing are fixed in the script.
    - **Model:** a small 1D-CNN encoder, fixed before freezing in `scripts/` with its hyperparameters. Trained within the same folds, with early stopping on an inner block split.
    - **Comparison:** the same network without the series.
    - **Reporting:** change in PR AUC with the block bootstrap. It is null-tested with 99 surrogate draws if the compute budget allows.
    - **Surrogates for that null** (seed 2037):
      - The variogram-matching null of §10 is applied to the pixel field of Test A. Each acquisition date's displacement field is one window, and one permutation, neighbour count and noise vector are shared across all dates in a draw.
      - Each surrogate pixel series is therefore a smoothed mix of real pixel series. Spatial and temporal structure are kept, while the link between a parcel's own series and its outcome is broken.
      - Series are built from the surrogates by the same code as the real ones, and the real mask is applied, so missingness is identical.
      - This construction is unconditional, like null (a) of §10, and was registered before the calibration. The calibration showed that such a null can be too lenient when the input stands in for the baseline features, so this p is read with that caveat. The deep model carries no decision.
      - Only the series network is refitted in each draw. The comparison network does not use the series, so its scores are computed once.
      - p = (1 + draws with a change ≥ observed) / (1 + 99).
    - **Memory:** if the surrogate step does not fit in GPU memory, only an implementation change that keeps the arithmetic (for example smaller window chunks) is allowed. It must be checked equal on a synthetic field and logged (§14). Otherwise the null is reported as not run.
    - It is not a starting point: it runs after secondaries 1–19, D1–D2 and P0–P1 and carries no decision.

Secondary analyses are not corrected for multiple tests. Only Test A carries the decision (§11).

## 13. Order of work and safeguards

0. **Before freezing** (no events built, no InSAR):
   - check which TCAD roll years and fields can be obtained (year built, state code, deed date, foundation type, parcel polygons);
   - run the timing gate for Test A on a synthetic field (§10), and time the conditional null's added fits;
   - calibrate the Test A null and apply the selection rule (§10);
   - run the focused literature check (§2);
   - record all of these in §16.
1. **Approval and freeze.** The user approves. Copies of the plan, of `scripts/` (with `SHA256SUMS`) and of the calibration report go into `freeze/`, and their hashes into §15, with the keyword protocol and the timing-gate setting (§10).
2. **Checkpoint 1: static data and events, no InSAR.**
   - Download and hash: the permit table, the reference data fixed by §5 (the TCAD rolls and parcel layer if option A; otherwise the 2019 TxGIO layer) and the 2026 roll (already hashed), the city boundary, SSURGO, the 3DEP DEM, ACS, the canopy layer (if any), the TCEQ landfill sites and the NOAA drought index.
   - Build eligibility (under C, rerun the crosswalk script and check that its output hash matches `step0/id_crosswalk.json`), events and the remodel control events (§4), the population count (§6), features (including the foundation-type decision) and folds.
   - Run the label audit, the parcel link check, the survivorship and link checks, the demolition audit and the demolition checks (a)–(b) (§5), and the permits-and-drought check (§4). Mark sale-triggered events.
   - Hash everything.
3. **InSAR.** Download frame 28482 and its STATIC layers. Compute window values for both tests and the physical indicators. Run the sign check, the clay contrast check, the coverage report and the variogram checks.
4. **Decoy run:** each event is moved to a random eligible parcel (seed 99), keeping its date. Both tests are run on the decoys. Only outright code errors are fixed, and they are logged.
5. **Real run, once,** for both tests. Reruns only for logged code errors.
6. **Compute budget:** Test A (primary) and Test B (key secondary) and their nulls always run to completion, as do the other core analyses of design summary point 11. Secondary analyses 1–19, D1–D2 and P0–P1 share 7 days on the project PC. The deep model (20) runs only in what is left of those 7 days. Any not finished are reported as "not run".
7. **No tuning.** Nothing in §4–§12 changes after Austin results are seen. Anything added afterwards is labelled exploratory.

## 14. Deviations log

- **2026-11-10. Addition: planted-signal check of Test A at Austin's size.** Proposed by Claude and approved by the user on 2026-11-10, before events were built (§4 rules 4–8) and before any InSAR file was opened. No rule in §4–§12 is changed. The check is descriptive and carries no decision.
  - **Why:** the calibration (§10) used synthetic fields and stopped at about 864 events. There, the conditional null rejected none of 100 datasets in either larger-city cell, and it detected the planted effects in 18% and 60% of datasets. Its false-positive rate and power at Austin's size are unknown, so a "not demonstrated" result could not be told apart from a weak test.
  - **What:** the frozen Test A primary analysis is run on synthetic events placed on the real houses.
    - Each synthetic dataset uses the real Baseline 1 features, the real standardised window velocities (§7) and the same 999 conditional-null surrogate fields (seed 2027) as the real run.
    - No real event is joined to an InSAR value. Real events supply only their dates and their number.
  - **When:** after the decoy run (§13 step 4) and before the real run (step 5). The surrogate fields are generated first; they depend on velocity and features only.
  - **Generating coefficients:** at checkpoint 1, the §9 logistic model is fitted once to "house holds an event" on the Baseline 1 features and x/y, over all eligible houses with complete inputs, with building age taken at 2018-08-01.
    - It uses events and baseline features only. The coefficients are saved and hashed before any InSAR file is opened.
  - **Synthetic events:** one for each real event that is usable in the primary comparison, at that event's date, in date order.
    - **Candidates:** houses with complete Baseline 1 inputs and a value in the event's window that are at risk at that date. Here a house is at risk if it is eligible (§5), not demolition-censored by that date, has no matched foundation episode before 2018-08-01, and holds no earlier synthetic event in the same dataset. Real episodes inside the study period are ignored.
    - **Draw:** one candidate, with probability proportional to exp(η). η is the generating coefficients applied to the house's features (age advanced to the event date), plus the cell's term below.
    - **Controls:** 50 per synthetic event by the §8A rule, applied to the synthetic events.
  - **Cells,** 100 datasets each. Cells 1–3 add no velocity effect and measure the false-positive rate. Cells 4–6 plant one and measure power.
    1. Nothing added: the baseline is correctly specified.
    2. 0.65·t, a nonlinear soil effect that the linear baseline omits (calibration scenario N2). s is soil linear extensibility, z-scored over the houses with complete inputs, and t = z(max(s − 0.7, 0)²).
    3. 0.7·H, hidden spatial clustering independent of velocity (calibration scenario N3). H is white noise on the 30 m pixel grid, smoothed by a Gaussian filter with sigma 600 m and z-scored. It is fixed in time and redrawn for each dataset.
    4. β·u with β = −0.1, where u is the house's standardised velocity in the event's window (§7), the model's own input.
    5. β·u with β = −0.2.
    6. β·u with β = −0.4.

    Cells 4–6 correspond to odds ratios of 1.11, 1.22 and 1.49 per interquartile range of motion away from the satellite.
  - **Analysis of each dataset:** the frozen primary analysis, unchanged: the fold map recomputed from the synthetic labels (seed 42), the §9 logistic models, the change in PR AUC, the 999 stored surrogate draws with the §10 p formula, and the §11 rule (a positive change and p < 0.05).
  - **Seeds:** numpy `SeedSequence([20261110, cell, dataset])` for the event draws and the hidden field, and `SeedSequence([20261110, cell, dataset, 2029])` for the controls. Cells are numbered 1–6 as above, and datasets 0–99.
  - **Compute:** CPU only, because the surrogate fields already exist. The check has its own time and takes none of the 7 days of §13 point 6. If the first datasets project more than 72 hours for all six cells, each cell falls to 50 datasets. Nothing else changes.
  - **Reported** in `planted_signal/PLANTED_SIGNAL.md`, written and hashed before the real run, with the hash in §15. For each cell:
    - the share of datasets meeting the §11 rule, with a 95% Wilson interval;
    - the mean observed and mean null change in PR AUC, and the paired bias with its t interval (as in the calibration);
    - the p-value deciles and the event count.

    Every dataset is kept. None is rerun except for a logged code error.
  - **Reading** (fixed now, so it cannot be argued afterwards):
    - Whatever the check shows, the real run goes ahead once, and the decision rule, the null, the draws and the indicators stay as frozen.
    - **If Test A is not demonstrated,** cells 4–6 are reported beside it as the sensitivity of the test at Austin's size: which planted effects it detected, and how often. This does not turn the result into evidence of no effect.
    - **If Test A is demonstrated,** cells 1–3 are reported beside it as the measured false-positive rates. A cell whose lower Wilson bound is above 0.05 is stated as a limit of the result. The label itself does not change.
    - The user is told the check's result before the real run starts.
  - **Limits:**
    - The events are synthetic. Their generating model is the linear baseline plus the stated term. Real permits may cluster in ways that none of cells 1–3 represents.
    - All datasets share Austin's velocity fields and one surrogate set. The rates are conditional on them, as the real run is, so the datasets are not fully independent.
    - The planted effect acts through the whole standardised velocity. Part of it lies in the fitted field that every surrogate keeps, so power against an effect of the residual alone may differ.
    - Test B, the other indicators and the secondary models are not covered.
  - **Script:** in `planted_signal/`, outside the frozen `scripts/`. It is written, checked on synthetic data and hashed into §15 before any InSAR file is opened.
- **2026-11-10. Canopy layer for Baseline 2 (§9): the 2018 layer.** Proposed by Claude and approved by the user on 2026-11-10, before any InSAR file was opened. It affects Baseline 2 only, which is a secondary analysis.
  - **Rule as frozen:** "the City of Austin canopy layer closest to 2016, if one exists at checkpoint 1".
  - **What exists** (checked 2026-11-10): City layers for 2006, 2010, 2014, 2018 and 2022.
    - 2014 and 2018 are both two years from 2016, so the rule does not choose between them.
    - The 2014 layer is published only as map tiles (`tree_canopy_2014_22`, tiles only, export disabled). No downloadable copy was found on the City's public servers.
  - **Choice:** the 2018 layer (`Tree_canopy_2018` feature service, derived by the City from 1 m NAIP imagery of 2018). It is downloaded and hashed at checkpoint 1.
    - **Exception:** if the City supplies the 2014 layer as data before any InSAR file is opened, the 2014 layer is used instead. It is equally close to 2016 and predates the study period.
  - **Consequence:** the 2018 imagery over the study area is dated 2018-11-01 and 2018-11-03, three months after the study period starts. For events dated before 2018-11-04, the canopy value postdates the event. Their number is reported with Baseline 2.
  - **Why 2018 and not 2010:**
    - The 2010 layer is eight years older than the study start and predates the 2011 drought. A house built after 2010 would take the canopy of its lot before construction.
    - Canopy is in Baseline 2 to make the baseline stricter. A stale layer is a weaker control, which would favour velocity. Any information the 2018 layer takes from the first three months of events can only strengthen the baseline, which works against velocity.
- **2026-11-10. Landfill footprints for the sign check (§7): the City of Austin's landfill perimeters.** Proposed by Claude and approved by the user on 2026-11-10, before any InSAR file was opened. The check's rule is unchanged.
  - **Rule as frozen:** the full-period velocity of "closed or active landfill footprints in the study area (TCEQ municipal solid waste sites, downloaded at checkpoint 1)" is compared with the area median.
  - **What exists** (checked 2026-11-10): TCEQ publishes its sites as points only, with no footprints.
  - **Choice:** the footprints are the City of Austin's "Landfill Perimeters" layer (`maps.austintexas.gov`, `Shared/Environmental_1`, layer 10), which holds the landfills whose exact boundary is known.
    - It has 46 perimeters. 39 intersect the full-purpose boundary, covering about 756 ha: 35 inactive and 4 active.
    - Every perimeter that intersects the study area is used. The City's 34 other sites, known only by approximate location, are not used.
    - A pixel belongs to a footprint if its centre lies inside a perimeter. The landfill value is the median full-period velocity of the valid footprint pixels, and it is compared with the median of all valid pixels of the subset.
  - **TCEQ sites:** still downloaded and hashed at checkpoint 1 (§13 step 2) and listed beside the perimeters. They define no footprint.
  - **Note:** most of these landfills closed between the 1950s and the 1980s and may have stopped settling. The years each site was active are reported with the check. If the landfills are not below the median, work stops until the cause is found and logged, as frozen.
  - **Privacy:** the layer has an owner-name field. The raw copy stays in the private area, and no project file carries that field.
- **2026-11-10. Remodel negative control (§4): work class Repair or Remodel, and fewer control events.** Proposed by Claude and approved by the user on 2026-11-10, after the foundation events were built and before any InSAR file was opened. It affects the two specificity checks of §11 only. The foundation outcome, Test A, Test B and their decision rules are unchanged.
  - **Rule as frozen:** the matching permits are "residential BPs with work class Remodel" whose description matches the remodel regex and does not match the foundation regex. The sample is "as many control events as there are foundation events, drawn with seed 2031, with the same count in every calendar month".
  - **Why it cannot be applied:** it gives 16 control events against 2,846 foundation events (§15). The City almost stopped using work class Remodel for residential building permits after 2016: 67 permits in 2018 and 6 in 2025. Kitchen and bathroom remodels are now filed under work class Repair.
  - **Amended rule:**
    - **Matching permits:** residential BPs with work class Repair or Remodel, the two classes of the foundation outcome (§4 rule 1). The description rule is unchanged: the description matches `kitchen|bath(?:room)?|cabinet|counter ?top|interior remodel` (case-insensitive) and does not match the foundation regex.
    - **Rules:** the episode, first-event, recent-construction and study-period rules apply unchanged.
    - **Sample:** the months are taken in calendar order with one generator (seed 2031). A month with more candidate control events than foundation events gives the foundation count, drawn without replacement. Any other month gives all its candidates.
  - **What was seen before the decision** (permits only):
    - Under the amended matching rule there are 1,545 candidate control events. 15 of the 88 months have enough to match the foundation count, and the sample rule gives about 1,491.
    - 40 descriptions were read. Most are kitchen or bathroom remodels. A few are other work that mentions a kitchen or bathroom, such as fire-damage repair and a garage conversion.
  - **Consequences:**
    - The specificity checks run with about half the planned control events. A "not detected" result is weaker evidence than planned, and it is reported as such. The direct comparison and its interval (§11) are unchanged.
    - The control events do not have the foundation events' calendar distribution. Both are reported by year.
    - The control outcome now has the same work classes as the foundation outcome.
  - **Frozen-rule result:** the 16 events stay in the private area and are not analysed.
  - The counts are in §15.
- **2026-11-10. Compute location: all heavy runs on the processing server.** Decided by the user on 2026-11-10 ("Run all heavy runs on the server"), before any InSAR file was opened. No rule in §4–§12 changes: the models, nulls, settings, seeds and decision rule stay as frozen.
  - **Rules as frozen:**
    - §10: the surrogate fields are made "on the project GPU with the NYC CuPy implementation, in its memory-lean form".
    - §13 point 6: secondary analyses 1–19, D1–D2 and P0–P1 "share 7 days on the project PC", and the deep model (20) runs in what is left.
  - **Machine:** the processing server on the project's local network. It is on-premises, has 2 × Xeon Platinum 8358 (128 threads) and 1 TB of memory, and is shared with other users.
    - Its Python environment has the project PC's package versions, without CuPy.
    - On 2026-11-10 the frozen interface, Test B and deep-model checks reproduced their recorded results on it (Test B within 5e-14).
  - **What runs there:** the window values and indicators computed from the InSAR files (§7), the surrogate fields (§10), the decoy run (§13 step 4), the planted-signal check (§14), the real run (step 5) and all secondary analyses.
    - Each analysis runs wholly on one machine, and the machine is recorded with its result.
  - **What stays on the project PC:** the plan, the reports, the record of results and the hashes of record.
    - Downloads that need the Earthdata login also stay there, because the server cannot reach it. The credential is not copied. The downloaded files are copied to the server, and their hashes are checked there.
  - **Surrogate backend (§10):** the server's GPU cannot be used (driver and library version mismatch). The surrogates are made on its CPUs.
    - **Engine:** the calibration's CPU adapter, `calibration/cpu_null.py`. It allocates the unchanged memory-lean class with NumPy and SciPy instead of CuPy. In the calibration's unit check it equalled the GPU class within 2.4e-14, with identical neighbour counts.
    - **Parallel draws:** `production/parallel_draws.py` runs the draws in parallel with identical arithmetic. Each draw's generator state is found by replaying the generator's two calls per draw, and the draws are stored in draw order.
    - This is an implementation change that keeps the arithmetic. Its check on a synthetic field is entered in §15 before any surrogate of the real field is made.
    - If that check fails, the surrogates are made by the frozen GPU path on the project PC. If the server's GPU is repaired first, the frozen GPU path may run there instead. The engine that ran is recorded.
    - The settings do not change: neighbour cap 1,000, 999 draws and seed 2027 (Test B: 999 draws, seed 2034; remodel Test B: seed 2035). The pre-freeze timing gate (§10) is settled and is not reapplied, whatever the CPU time.
  - **Compute budget (§13 point 6):** the 7 days become 7 wall-clock days on the server, from the start of the first secondary analysis.
    - At most 64 worker processes run at once, half the server's threads, because the machine is shared.
    - The analyses start in their numbered order: 1–19, then D1–D2, then the deep model (20). P0–P1 do not apply under option A.
    - Test A, Test B, their nulls and the other core analyses still run to completion. The planted-signal check keeps its own time (§14).
  - **Consequence:** the server has about six times the PC's threads and 16 times its memory. More of the secondary analyses, and more of the deep model, may finish within the 7 days than on the PC. No rule or decision changes, and an analysis that does not finish is still reported as "not run".
  - **Data on the server:** the user stated on 2026-11-10 that the server is on-premises and that data may be moved there. The runs use the checkpoint-1 tables keyed by property ID, which carry no names or addresses, the InSAR files and the fields derived from them.
- **2026-11-11. Construction mask (§7): distance to the parcel polygon, and where a permit's parcel is.** Proposed by Claude and decided by the user on 2026-11-11, after the InSAR files were downloaded and before any displacement value was read. Only permits, parcel layers and the pixel grid were used. The rule's work classes, distance and dates are unchanged.
  - **Rule as frozen:** "pixels within 50 m of a parcel with a BP of work class New, Demolition, Addition, Addition and Remodel, Shell or Relocation are dropped", for permits issued from 365 days before the window start to the window end.
  - **Two points the wording leaves open:**
    - **Distance to what:** NYC's rule says "the lot point". Austin's says "a parcel", while the rest of the plan says "parcel point" wherever it means the centroid (§5, §7).
    - **Where the parcel is:** checkpoint 1 links a permit to a parcel through the 2018 roll (§5 rule 2). That link places only 64% of the 84,387 mask permits issued from 2015-07 to 2025-11, and 55% of those of work class New. Lots created after 2018, in new subdivisions and replats, have keys that are not in the 2018 roll.
  - **Seen before the decision** (permits, parcels and pixel centres only; Test A windows every third month from 2018-08 to 2025-11):
    - **Share of the 114,058 house pixels dropped per window:** about 36% when distance is measured to the polygon and about 22% when it is measured to the centroid. Parcels over 5 ha are not the cause: without them, the polygon reading still drops 35%. The cause is the number of permits: about 19,000–27,000 fall in each window's three years, many of work class Addition and Remodel and many infill New and Demolition permits.
    - **Where the 84,387 permits can be placed:**
      - 76.2% by a 2018 polygon, matched on the roll's `geo_id` or on the layer's own `PID_10`;
      - 9.8% more by the TCAD "Parcels Dec 2025" layer (the step-0 copy);
      - 0.03% more by the 2019 StratMap layer, which is therefore not used;
      - 11.3% more by the permit's own coordinates;
      - 2.7% cannot be placed.
    - Where a permit has both a polygon and coordinates (61,400 permits), the coordinates lie inside the polygon 98.5% of the time and within 50 m of it 99.5% of the time.
  - **Decision:**
    - **Distance:** from the pixel centre to the parcel polygon, which is zero inside the parcel, at most 50 m. This is the literal reading. The user chose it as the literal reading of §7, as for the standardisation sets (§15), at the cost of more dropped pixels.
    - **Location, in this order:**
      1. The 2018 TCAD parcel polygon, matched on the 2018 roll's `geo_id` or, failing that, on the layer's `PID_10`.
      2. Only where no 2018 parcel has the key: the parcel of the TCAD "Parcels Dec 2025" layer, matched on `geo_id`. No 2018 value exists for these lots, so the TCAD rule against replacing 2018 values does not apply.
      3. Otherwise the permit's own coordinates in the City permit dataset, with the distance measured to that point.
      4. Otherwise the permit masks nothing, and the number is reported.
  - **Permit coordinates:** `permit_number`, `latitude` and `longitude` of the mask permits, fetched from 3syk-w9eu on 2026-11-10 (`production/i04_permit_points.py`). No address, name or description column was requested.
    - They are joined to the checkpoint-1 table by permit number, which is unique in both. The row identifier cannot be used, because the City republished the dataset at 16:53 UTC that day, after the checkpoint-1 download, and every row identifier changed.
    - All 270,654 mask permits of the checkpoint-1 table were found; 236,035 have coordinates.
  - **Consequences:**
    - Fewer houses have a value in each window than under the centroid reading. The coverage report (§7) gives the counts per window.
    - Houses near frequent rebuilding drop out of more windows.
    - Lots that were never in a TCAD layer we hold, and permits without coordinates, are not masked. They are 2.7% of the mask permits.
- **2026-11-11. Connected-component rule (§7, "as NYC §7, steps 1–3"): the main component inside the city instead of the label at the frame's reference point.** Proposed by Claude and decided by the user on 2026-11-11, after the InSAR files were downloaded and before any displacement value was read. Only connected-component labels and product metadata were read. This is the Austin counterpart of NYC's deviation 1.
  - **Rule as frozen** (NYC §7 step 3, taken unchanged): a pixel is invalid for a window if its connected-component label at any epoch in the window is 0 or differs from the label at the frame's reference point.
  - **Found in the granules:**
    - Each product's reference point lies about 60 km south-west of the city, outside the downloaded subset (frame rows about 4,400–4,700, columns about 1,100–3,300). Windows of 11 × 11 pixels around it are fetched with `production/i03_download_refpoint.py`.
    - In every window fetched so far, the reference pixel itself has label 0 and no displacement, inside a uniform component of label 1, as in NYC. The full count over the 254 products is entered in §15.
    - Inside the full-purpose boundary (839,735 pixels), the most common non-zero label covers 88.2–97.7% of pixels at each epoch (median 95.6%); the rest are label 0. At the 114,058 house pixels it covers 98.9–99.9% (median 99.8%). No house pixel ever carries another non-zero label.
    - In 10 of the 254 epochs, the city's main component has label 2, 3 or 4, not 1: one in 2018-12, one in 2019-08 and eight in 2023-07 to 2024-10. Label numbers are assigned per product.
  - **Consequence of the frozen wording:**
    - Read literally (label 0 at the reference point), the rule rejects every pixel.
    - Read as "the component around the reference point", it rejects every Austin pixel at those 10 epochs, and so in every window that contains one of them.
  - **Change:** at each epoch, the comparison label is the city's main component: the most common non-zero label among the pixels whose centre lies inside the full-purpose boundary (vnwj-xmz9, §15).
    - This is NYC's deviation 1 with Austin as a single landmass group. The plan has no landmass groups (§7, standardisation).
    - The label-0 part of the rule is unchanged, and a pixel outside the main component is still rejected.
    - A step shared by the whole component shifts all its pixels alike. Test A's window standardisation removes it, and so do Test B's quarter effects.
  - **Correction (2026-11-11, after the reference-point windows of all 254 products were read; `production/check_refpoint_component.py`, `production/check/refpoint_component.json`).** Two statements above, written when only some windows had been read, are wrong. The rule decided is unchanged, and so are the values it gives.
    - **Where the point lies:** for reference date 2018-06-30 (15 products), the reference point lies inside the subset and inside the full-purpose boundary, in north Austin (frame row 1,464, column 5,726). For the other 16 reference dates (239 products), it lies outside the subset, about 60 km south-west.
    - **The component around the point:** the label at the point is 0 in all 254 products. The most common non-zero label in the 11 × 11 window around it equals the city's main component in all 254 products, including the 10 epochs where that label is 2, 3 or 4 rather than 1. That label covers at least 95.9% of each window.
    - **So the consequence stated above is wrong.** Read as "the component around the reference point", the frozen rule does not reject every Austin pixel at those 10 epochs. It names the same component as the main component inside the city in every product. The two readings give identical validity and values. Only the literal reading (label 0 at the point) rejects every pixel.

- **2026-11-11. Lasting cycle slips (§7, processing corrected after the checks): a pixel has no value in a window that contains one of its slips.** Proposed by Claude and decided by the user on 2026-11-11 ("Correct first"). This came after the §7 checks and before any outcome was joined or compared. §7 allows it: "Processing may be corrected after these checks and logged, never after any comparison with outcomes."
  - **Why** (§15, "InSAR step, part 2"):
    - The sign check came out "not below", and that result stands.
    - In finding the cause, the full-period series showed lasting steps of about one phase cycle (half the C-band wavelength is 27.7 mm). They fall on a few dates, mostly 2019-11, 2021-01 and 2022-12/2023-01, and are concentrated in the north-east of the city around the active landfills.
    - Within a product they persist to the end of its ministack. The re-referencing chain then carries them forward, so a window that contains one sees a false trend of tens of mm/yr.
    - About 1.1% of the house pixels with a full-period value have one. In the first run they made up about 40% of the values above the 99.5th percentile of each 24-month window.
    - The connected-component labels did not flag them: the pixels stay on the city's main component.
  - **Rule** (authors' choices, fixed in `production/i11_slip_screen.py` before it was run):
    - **Series:** each pixel's chained series, as in i08. Where a chain's crossing product is invalid at the pixel, the series restarts and steps are sought within each segment only. Values are used where valid and on the main component.
    - **Common mode:** at each epoch, the median over the eligible-house pixels whose chain is unbroken. It is subtracted from every pixel.
    - **Slip at epoch e:** |mean of epochs e+1..e+15 − mean of epochs e−14..e| ≥ 20 mm, the jump between the valid values on either side of e is at least 20 mm, and each side has at least 8 valid values.
    - **Mask:** a pixel is invalid for a window if one of its slips has both dates (the last valid value before the jump and the first after) inside the window. A slip before the window start shifts the whole window's series by a constant and changes no fit.
    - The rule is a validity rule like the component rule (§7, step 3). It is applied before the construction mask.
  - **Scope:**
    - The rule applies to every subset pixel (ring and cell pixels included) and every window: 24, 12 and 36 months, lags, and the full period of the sign and clay checks. It also applies to the field without the construction mask (secondary 13).
    - A pixel where the test cannot be made at some epochs (too few valid values on a side, or a segment boundary) is not masked there. The counts are reported.
  - **Run and checks:**
    - `production/i11_slip_screen.py`, then `production/i08_window_values.py --slips`. Run without `--slips`, the script gives the first run's values; the first run's exact script is kept as `production/i08_window_values_run1.py`.
    - Then `production/check_window_values.py` with the slip table (an independent per-pixel route), i09 and i10. All are run on the server.
  - **The first run is kept, unchanged** (`work/insar/windows_20261111`, `fields_20261111`, `checks_20261111`), and its results stay in §15.
    - **Added sensitivity analysis** (no decision): Test A and Test B primary analyses are repeated on the first run's values, without the slip rule, and reported beside the primary.
    - The sign and clay checks are repeated on the corrected values and reported beside the first results. The first sign-check result, "not below", stays the result of the check.
  - **Script SHA-256 before the run:**
    - `i11_slip_screen.py`: 2d71017f337f0274d6d0a3fbf50e8b9d0cb6e77dc4135c38a924f3e859b1edb7
    - `i08_window_values.py`: fbfeb0e65dc71c0f8b619feba0a5af28375cefa12ae85817ed103eeb153f393f
    - `i08_window_values_run1.py`: 8e16d3e0820f81122cdc5a91c4166e3e4696da5b0b5e2da240960770d48335ca
    - `check_window_values.py`: 786f5051d9090d0f421fbaea0e2c6a466066b24fc1387c897f9fa90c7c8af2aa

- **2026-11-12. Compute budget (§13 point 6): no time limit. Every secondary analysis and the deep model run to completion.** Decided by the user on 2026-11-12 ("Remove the limit").
  - **Rule as frozen:** secondary analyses 1–19, D1–D2 and P0–P1 "share 7 days on the project PC". The deep model (20) runs only in what is left, and any not finished are reported as "not run".
  - **Amended on 2026-11-10 (above):** 7 wall-clock days on the server, from the start of the first secondary analysis.
  - **When:** after the real run's Test A, Test B and the two reports (§15). Of the secondary analyses, only parts of secondary 8 had results: the free and within-block permutation nulls, inside the Test A report. Null (a) and MSR were running. No other secondary analysis, and not the deep model, had started.
  - **Why:** the user has the time, and the 7 days were sized for the project PC. On the server the analyses run several times faster. The reason does not depend on any result.
  - **Change:**
    - Secondaries 1–19, D1–D2 and then the deep model (20) run to completion in their numbered order. P0–P1 do not apply under option A.
    - None is reported as "not run" for lack of time.
    - The deep model's 99-draw null (§12 item 20, "if the compute budget allows") is always run.
    - Each analysis is reported with its start and end times and its machine.
  - **Unchanged:**
    - the analyses, their order, settings, seeds, nulls and labels;
    - the limit of 64 worker processes at once on the shared server;
    - the rule that an analysis failing for another reason (a code error, or the deep model's memory rule in §12) is reported as such.
    - No secondary analysis carries a decision, and the Test A decision stands.

## 15. Freeze record

- **Plan approved by:** the user, on 2026-11-07: draft 10, with the conditional null (b) as the primary Test A null and power results descriptive only (§10, §16). The supervisor was not consulted, because the work was not blocked (header).
- **Frozen copy:** `freeze/AUSTIN_PLAN_frozen.md`, saved 2026-11-07 00:06 EET (2026-11-06T22:06:41Z, `freeze/FROZEN_AT.txt`), SHA-256: `18627d8275d7859b9c7c7011235f177f0774af4d7b03632f9d49d32a7d8515cd`
- **Scripts:** `freeze/scripts/`, a copy of `scripts/` without Python caches: 2,301 files, including the 2,200 calibration records. Every entry of its `SHA256SUMS` was verified in the copy. `scripts/SHA256SUMS` SHA-256: `9fa37e9fab6c7b062c173720cf6f000c1fcc102fb02e7dfa6910da9e7cb18425`
- **Calibration report:** `freeze/CALIBRATION.md`, a copy of `scripts/calibration/CALIBRATION.md` with the coordinator's addendum, SHA-256: `a4e63692abedea0dbfbfb4a7d74a7020304926d2e644d27fefdb601f65971f6a`
  - Independent selection check `scripts/calibration/coordinator_rule_check.json`, SHA-256: `0064d7a8edcfffff0b3ade4c488d143b5150ad8b91a286916c6e1a28a5aa22fc`
- **Keyword protocol (§4):** `feasibility/candidates/keyword_protocol.md` (2026-10-26), copied to `freeze/keyword_protocol.md`, SHA-256: `3a74c0b9f40ef226d3332206e537f11cd9b71c65a7ae5acce1af5516e87934fb`
- **Timing-gate setting (§10):** neighbour cap 1,000 and 999 draws for both Test A nulls: the conditional null (primary) and the NYC null (secondary 8), with seed 2027. Test B: 999 draws, seed 2034. Timing evidence `step0/timing/SHA256SUMS`, SHA-256: `41653da4707f30941d62326b3090cfafdc64296a707d6abbbb07466ce882b1d5`
- **Reference data at freezing:** option A waits for TCAD's certified 2018 roll and 2018 parcel layer (request R010955-110226, narrowed on 2026-11-06). Option C is the registered fallback (§5, design summary point 9).
- **NYC freeze unchanged:** `feasibility/nyc/freeze/NYC_REPLICATION_PLAN_frozen.md`, SHA-256 `59a2aa1a573ce8b7cf7ede7fd1e870bea2768c259978c716872f177041588a5d`, checked at this freeze.
- **Freeze manifest:** `freeze/MANIFEST.sha256`, covering every other file in `freeze/` (2,306 files), SHA-256: `381a8514c006cb2f6468b504eee0581fbd3d4b6f4bec98810d2e5ab807041b92`. All frozen files are read-only.
- **Checkpoint 1, reference data, filled in after freezing** (2026-11-09; `checkpoint1/REFERENCE_DATA_2018.md`; no InSAR file opened, no event built):
  - **Start:** checkpoint 1 started on 2026-11-09, when TCAD's 2018 files for request R010955-110226 were in hand (design summary point 9).
  - **Reference data (§5): option A.** Study period from 2018-08-01.
    - `2018_Certified_Appraisal_Export_Supp_0.zip`, SHA-256 `500f594c05f748aad600edbb5a56612b71ada690ecaffa017292de80d9e20c8d`. Year 2018, supplement 0 in the header and every row.
    - `2018_Shapefiles.zip` (layer `Parcel_poly`, EPSG:2277, last modified 2019-04-06), SHA-256 `64e1a626bd09ad2aad4d0800543e67c162b66b99982a37364c65c95632886c06`.
  - **Study area (§5):** full-purpose boundary vnwj-xmz9, downloaded 2026-11-09, SHA-256 `9656bd73a7a7989ef41fd0610f716a8078d0fe843d0466b21e9acef9f93ede47`. Its geometry is identical to the step-0 copy; only the bytes differ. The frame clip is not yet applied.
  - **Permit table (§4):** 3syk-w9eu, downloaded 2026-11-09 (dataset updated 13:13:18Z), 2,384,452 rows, 13 columns used by the rules, without contractor, applicant, address or location columns. SHA-256 `0e6f003f286473512cc4cb59765df9ddd4a834b70256f788269e0a3b76f28146`.
  - **Primary population (§5):** 149,316 houses in 114,058 unique 30 m cells. Two shared 2018 `geo_id`s left out four houses (rule 3).
  - **Baseline 1 (§9):** year built, living area and lot area are 100% complete. Foundation is recorded for 94.6% of eligible parcels (≥ 90%), so **foundation type is in Baseline 1**.
  - **Parcel link check (§4):** of 13,881 permits meeting rules 1–3, 93.9% (95% CI 93.5–94.3) match a 2018 reference-roll parcel and 84.3% (83.7–84.9) match the primary population.
  - **Not applicable under A:** secondary 14 is removed (§4), and P0–P1 apply to option C only (§12).
  - **Deviations:** none. No frozen rule was changed.
- **Checkpoint 1, events, filled in after freezing** (2026-11-10; `checkpoint1/events_2018.json`, from `checkpoint1/scripts/c1_05_events.py`; no InSAR file opened):
  - **Foundation events (§4): 2,846,** one per house, all dated by application date.
    - Of the 13,881 permits meeting rules 1–3, 11,706 are on population houses (rule 4), at 10,240 houses.
    - The first episode is before the study period at 6,573 houses, which are never a case or a control (rule 7), and after it at 696.
    - Rule 8 (a construction permit in the three years before) excludes 125.
    - By year: 170 (2018, from August), 355, 316, 382, 386, 397, 369 and 471 (2025, to November).
    - All but one event are permits of work class Repair.
    - A recount with separate code gave the same houses and dates.
  - **Population size check (§6):** 2,846 is above 300, so the study continues.
  - **How the wording was applied** (no choice changes an event):
    - **Rule 6:** a permit within 365 days of an episode's first permit belongs to that episode (11,423 episodes). Counting the 365 days from the previous permit gives 11,418. The event is the first permit of the first episode under both readings.
    - **Rule 7:** "from 1980" is taken as dates from 1980-01-01. No matched permit on a population house is earlier or undated.
    - **Rule 8:** the construction permit is dated in the three years before *t_e*, not on *t_e* itself.
  - **Demolition censoring (§5):** 3,797 houses have a total-demolition permit dated on or after 2018-08-01, 3,416 of them inside the study period.
    - Four events fall on or after their house's demolition date. Those houses are not at risk at *t_e* (§8).
  - **Survivorship (§5):** 30 events (1.1%) are at houses no longer in the 2026 detached population. Of the 3,514 permits meeting rules 1–3 in the study period on population houses, 58 (1.7%) are.
  - **Remodel negative control (§4): cannot be built as frozen.**
    - The frozen rule (residential building permits of work class Remodel) gives 16 control events, against the 2,846 needed.
    - **Cause:** the City almost stopped using work class Remodel for residential permits after 2016: 67 permits in 2018 and 6 in 2025. Kitchen and bathroom remodels are now filed under work class Repair.
    - No rule was changed at this point. The user decided on 2026-11-10, and the amended rule is in §14.
  - **Remodel negative control, amended rule** (§14; `checkpoint1/remodel_controls_2018.json`, from `checkpoint1/scripts/c1_06_remodel_controls.py`; no InSAR file opened): **1,491 control events,** 52% of the foundation count.
    - There are 10,144 matching permits on population houses, at 9,235 houses. The first episode is before the study period at 7,465 houses and after it at 157. Rule 8 excludes 68.
    - That leaves 1,545 candidates. All but 16 are permits of work class Repair.
    - **Months:** 11 had more candidates than foundation events and were drawn down to the foundation count. Four had the same number. 73 had fewer, and all their candidates were taken.
    - By year: 103 (2018, from August), 248, 188, 217, 209, 185, 187 and 154 (2025, to November).
    - **Overlap with the foundation outcome:** 171 control events are at houses with a foundation episode at any date, and 87 of these houses hold a foundation event. They stay in, as the frozen rule has no exclusion for them.
    - Two control events fall on or after their house's demolition date.
    - A recount with separate code gave the same candidates and the same month counts. The script also reproduces the 16 events of the frozen rule.
- **Checkpoint 1, audits and label checks, filled in after freezing** (2026-11-10; `checkpoint1/audit_results_2018.json`, `audit_samples_demolition_checks.json` and `drought_check.json`, from `checkpoint1/scripts/c1_07` to `c1_10`; permits only, no InSAR file opened):
  - **Reader:** Claude (an AI model) read each sampled description once, from the permit text only. No engineer and no second reader checked the classes.
  - **Label audit (§4):** of 100 events (seed 2028), 98 are repairs of an existing foundation. Precision 98% (exact 95% CI 93.0–99.8).
    - One is not a foundation repair (fire-damage repair of a detached garage). One is unclear (the foundation is named in a list of remodel work, without a repair statement).
    - 9 of the 98 list the foundation repair with other repair or remodel work.
    - The descriptions say what was repaired, not why. The audit does not show that ground movement caused the repairs.
    - No event was removed.
  - **Demolition audit (§5):** of 50 censoring permits (seed 2036), 38 demolish the main house: 76% (exact 95% CI 61.8–86.9).
    - The other 12 demolish a garage, shed, carport, pool, deck or second unit. Those houses are censored while still standing.
    - Of the 3,797 censoring permits, 607 (16%) carry the City's permit class for residential buildings other than houses.
    - The censoring rule is unchanged. A censored house leaves the control pool and can no longer be a case: 4 events and 2 remodel control events fall on or after their house's censoring date.
    - D1 and D2 (§12) use demolition as an outcome and are read with this share.
  - **Check (a), foundation mentions (§5):** 8 of the 3,797 censoring permits mention the foundation: 0.21% (95% CI 0.11–0.42).
    - Five say the foundation stays, one says it is removed, and two mention it in passing. None gives foundation trouble as a reason.
  - **Check (b), demolition after a repair (§5):** Mantel–Haenszel rate ratio 0.69 (95% CI 0.61–0.79) over deciles of year built.
    - After a matched foundation episode: 240 demolitions in 57,683 house-years (4.2 per 1,000). Without one: 3,176 in 1,024,450 (3.1 per 1,000).
    - The crude ratio is 1.34 (1.18–1.53). Repaired houses are older, and older houses are demolished more often. Within age groups, repaired houses are demolished less often.
    - By the §5 reading (a ratio above 1 with an interval excluding 1), (b) does not indicate informative censoring.
    - This used all 149,316 population houses, because the frame clip (§5) is not yet applied.
  - **Permits and drought (§4):** Spearman ρ = −0.42 (p = 0.086, 18 years) between matched repair permits by issue year (2008–2025, rules 1–2) and the previous year's mean drought index.
    - The sign is as expected: more repairs after drier years. With 18 years, the correlation cannot be told from zero at the 5% level.
    - With rule 3 added, ρ = −0.34 (p = 0.17). On population houses, ρ = −0.40 (p = 0.10).
    - **Division:** NOAA climate division 4107 (Texas, division 7), which contains Travis County in NOAA's county table.
    - **File:** `climdiv-pdsidv-v1.0.0-20261105`, downloaded 2026-11-10, SHA-256 `0873704f4fa13b2ae526c4d45a26e8e3d407927622e772361c0f4d71df5b8002`.
    - Reported only. No rule changes.
- **Checkpoint 1, study area, features and folds, filled in after freezing** (2026-11-10; `checkpoint1/frame_grid_folds.json`, `soil_lep.json`, `terrain_parcels.json`, `terrain_check.json`, `income_2015.json`, `canopy_parcels.json`, `other_bp.json`, `landfills.json` and `features_2018.json`, from `checkpoint1/scripts/c1_11` to `c1_18` and `scripts/server/`; no InSAR file opened):
  - **Frame clip (§5):** all 149,316 population houses lie inside the footprint of frame 28482, and the nearest footprint edge is 13.9 km away. All are eligible.
    - The footprint and the frame's grid come from the public OPERA burst database (release v0.18.0; file hashes in `frame_grid_folds.json`).
  - **Pixel grid, to be confirmed:** the frame's bounding box is snapped to 30 m in EPSG:32614, so pixel edges are taken at multiples of 30 m.
    - This is checked against the coordinates of the first granule at the InSAR step. If the product grid differs, the pixels, blocks and folds are rebuilt, and that is logged in §14.
    - 114,058 pixels hold a house. 68,492 houses share a pixel with another house (at most five in one pixel).
  - **Test B cells (§7):** 5,645 cells of 250 m hold a house, and 5,019 hold three or more.
  - **Folds (§9):** 213 blocks of 2 km. The frozen `nyc_lib.fold_map` (seed 42) was run on the houses in property-ID order. Events per fold: 566, 570, 564, 567 and 579.
  - **Soil (§9):** SSURGO survey area TX453, version 28 of 2026-09-03, SHA-256 `190c943af415a0a27bafee7c6a5f61043d84714c981aed768b01b7d9413383c7`.
    - **Method:** for each soil component, the mean representative linear extensibility over 0–150 cm, weighted by horizon thickness. For each map unit, the mean over its components with a value, weighted by component percentage. A house takes the map unit that contains its parcel point.
    - **Missing:** 1,112 houses (0.7%): 923 on urban land, 139 on pits, 48 outside every map-unit polygon and 2 on water.
  - **Terrain (§9):** 19 tiles of the USGS 3DEP 1 m DEM, all from the 2017 lidar project `TX_Central_B1_2017` (tile hashes in `terrain_parcels.json`).
    - **Method:** slope by Horn's method on the 1 m grid, in degrees. Elevation and slope are the means over the pixels whose centre lies in the parcel.
    - No house is missing. A recomputation with separate code on 60 parcels gave the same values.
  - **Income (§9):** missing for 41 houses (0.03%), so the safeguard is not triggered and **income stays in Baseline 1**. 918 houses (0.6%) take the tract median.
  - **Foundation type (§9):** slab 118,970; pier and beam 21,886; no value 8,460 (5.7%).
    - A house has a value only if its single recorded code is SLAB or PIER AND B. The 8,460 are 8,022 blank and 438 with mixed or other codes.
  - **Complete Baseline 1 inputs: 139,778 houses (93.6%), holding 2,719 of the 2,846 events (95.5%).**
    - By the missing-input rule of §9, the other 9,538 houses and their 127 events are left out of every comparison that uses Baseline 1. For 8,400 of these houses, the foundation type is the only missing input.
    - **Building age** at a date is the decimal year of the date minus the year built. The one house with year built 201 stays in, as the plan has no rule for it.
  - **Baseline 2 (§9):**
    - **Canopy:** the City's 2018 layer (§14), exported by its own service for the envelope of the parcels: 3,092,138 polygons, SHA-256 `de63add98983057542969630044535a5f11ba108313dcacb5d6628fdc2ac846d`. The City did not supply the 2014 layer.
      - **Method:** canopy and parcels are rasterised at 0.5 m. A separate polygon calculation on 300 parcels differs by at most 0.006.
      - No house is missing. The mean share is 0.36.
      - 112 events are dated before 2018-11-04, so their canopy value postdates them (§14).
    - **Other permits:** the dates of 225,371 non-foundation building permits on eligible houses are stored. The count for a row is the number dated in the five years before *t_e*.
  - **Landfills (§7, §14):** the City's landfill perimeters are downloaded: 46 perimeters, of which 39 intersect the study area (755 ha; 35 inactive, 4 active).
    - **TCEQ sites:** "MSW Facilities" (384 in Texas) and "Active Landfills" (193). Neither has a site inside the full-purpose boundary, and each has two within 2 km. Under the frozen wording alone the sign check would have been skipped.
    - File hashes are in `landfills.json`. The raw copies carry owner and facility names and stay in the private area.
  - **Planted-signal check (§14):** the generating coefficients are fitted and saved in `planted_signal/generating_coefficients.json`, SHA-256 `2f67ed802968a6992101894724fdfb09489bb3fb2e8054ef277e37a1c98a9c8b` (139,778 houses, 2,719 events).
  - **Where it ran:** terrain and canopy were computed on the processing server from parcel outlines that carry a property ID and no name or address. The results were copied back and hashed here. Everything else ran on the project PC.
  - **Still open before any InSAR file is opened:** the planted-signal script (§14). It is entered below.
- **Checkpoint 1, planted-signal script (§14), filled in after freezing** (2026-11-10; `planted_signal/`; written by Claude and checked on synthetic velocity fields only; no InSAR file opened):
  - **Files** (all hashes in `planted_signal/SHA256SUMS`, SHA-256 `16a081c18fe4f723d96117daba26a40ca8443489d44a5f05596fe232e24fdefb`):
    - `testa_core.py`, SHA-256 `f4d71575c3179ef2f6ac7aeff8e0a26c14ab515db76ad937e411fae9e6e38430`: the Test A primary analysis in one module. It holds the window standardisation, the shared at-risk rule, the risk sets, the Baseline 1 design, the fold map, the statistic, the p-value, the §11 rule and the formats of the field and surrogate files. The decoy run and the real run import it unchanged.
      - It is new code. `freeze/scripts/` holds the nulls, Test B, the deep model and the calibration, but no script that runs Test A on real data. Check step 1 below shows that the core reproduces the calibration's Test A arithmetic exactly.
    - `planted_signal.py`, SHA-256 `977f626f1c72ab25e6c3f70b062fe1010252b9027f0e8bba113f4acad882b8f4`: the check itself. It has four commands: the dates of the usable real events, the quantiles of the stored surrogates, the run (cells 1–6 × datasets 0–99, one record per dataset) and the summary report.
    - `check_planted_signal.py`, SHA-256 `bc0b24b8a4af37c567189df235f008dd95c29ba86a278548e3c8989f29a4be20`. Its result is `check/check_results.json`, SHA-256 `a33faa7f27f9166003b8e0598ab7e87ddb268625b1c0a2daae9615e8fed9503c`, and its log is `check/check_run.log`, SHA-256 `9be8829cda8ca829ee8079d7299726e0f1bba24d8b8d61e14999536e62fff2f4`.
    - The frozen `nyc_lib.py` it imports matches `freeze/scripts/SHA256SUMS` (`619e4de4…`).
  - **Details the plan leaves to the scripts, fixed here:**
    - Events are taken in order of date, then property ID; the control pool is in property-ID order.
    - An event whose house is demolition-censored on or before the event date is not a case (4 events), by the shared rule (§8).
    - Controls are drawn from the eligible houses that have a value and are at risk. Control rows missing a Baseline 1 input are then dropped and counted ("draws lost to missing values", §8A). About 6.4% of control rows are lost this way.
    - The field file holds velocity on all 114,058 pixels holding an eligible house. The null field (§10) is the 107,243 pixels holding a house with complete inputs; 6,815 pixels (8,133 houses) are left out of it.
    - The surrogate fields are stored as 32-bit floats (relative rounding below 1e-7), as the pre-freeze size estimate of about 39 GB for 999 draws assumed (§16). The observed field stays in 64-bit.
    - The planted-signal details §14 leaves open (hidden-field grid, z-scoring sets, order of draws, the first-round time projection) are written in the script's header.
  - **Standardisation sets (§7), read literally, as the user decided on 2026-11-10:**
    - §7 standardises "over all eligible parcels with a value". The observed field is standardised over all 149,316 eligible houses whose pixel has a value in the window.
    - A surrogate field has values on the null field only, so each surrogate is standardised over the eligible houses with a value in it: the 141,183 houses on null-field pixels.
    - The two sets differ by the 8,133 houses on pixels without a complete house. None of them can be a case or a control row, because all lack a Baseline 1 input. Only the median, interquartile range and clipping points differ.
    - **History:** Claude's first version used the 141,183 houses for both fields. It passed the check and was put to the user, who chose the literal reading. The core was changed and the check rerun, before any InSAR file was opened. The first run's result and log, with the earlier code hashes, are kept in `check/first_run/`.
  - **Check** (synthetic velocity on the real pixel grid; real houses, features, folds, demolition dates and event dates).
    - The settings are not production settings: a synthetic field, 20 surrogate draws from the CPU engine with neighbour cap 200, and 2 datasets per cell. The 12 dataset results test that the pipeline works. They measure neither the false-positive rate nor power.
    1. **Equivalence:** on the frozen calibration record `A_00_0000`, the core's standardisation is bit-identical, and its baseline and observed change in PR AUC (−0.000825) equal the record's.
    2. **Geometry:** 149,316 houses, 139,778 with complete inputs, 114,058 pixels and a null field of 107,243 pixels. The core's fold map reproduces the stored checkpoint-1 folds.
    3. **Synthetic field:** a smooth field tied to pixel soil and elevation, with 96.5% of pixel-windows valid.
    4. **Surrogates:** 20 draws with seed 2027, through the frozen conditional null on its CPU backend. They were made in the first run (269 s per draw) and reused in the rerun: same synthetic field, same surrogate code, file SHA-256 `21c67bad239c47955be00bc05fbd7ddf854e045f70302aa41de544cd736c00c4`. The missing-value pattern is preserved.
       - **Standardisation sets** (step 4b of the result file): recomputed with a separate join of houses to pixels, the observed quantiles (149,316 houses) and a surrogate's quantiles (141,183 houses) equal the core's exactly. The observed set's quantiles differ from the null-field set's in all 88 windows. The planted model's velocity u equals the observed field standardised over all eligible houses.
    5. **Run:** of 2,846 events, 2,620 are usable on the synthetic field: 127 lack a Baseline 1 input, 4 are demolition-censored and 95 have no synthetic value in their window. The 95 and the 2,620 depend on the synthetic field's gaps and are not the real counts.
       - All 12 records were written. The planted terms move selection the planted way. In cell 2, the selected houses' term exceeds the candidates' mean by 1.52 and 1.61. In cell 3, by 0.48 and 0.53.
       - The selected houses' velocity minus the candidates' mean falls with β: +0.27 and +0.28 (cell 1), +0.17 and +0.18 (cell 4), +0.11 and +0.12 (cell 5), and −0.02 and −0.05 (cell 6). It is positive in cell 1 because the synthetic velocity is built from soil and elevation, which the baseline carries.
       - Both cell 6 datasets meet the §11 rule at the minimum p of 1/21, as do three of the four datasets of cells 4 and 5. Dataset 1 of cell 1 also meets it at p = 1/21, which happens about once in 21 under no effect. Reported, not interpreted.
    6. **Independent check** of cases, controls and dropped rows in two datasets (cell 4 dataset 0, cell 3 dataset 1): all 13 conditions hold.
    7. **Selection frequencies:** 400,000 draws on 2022-08-10 (127,138 candidates) match exp(η) by decile of η: χ² 10.6 on 9 degrees of freedom, p 0.30.
    8. **Reproducibility:** two datasets rerun with 2 workers instead of 12 give identical records.
    9. **Timing:** 1.04 s per null statistic and 47 s per dataset outside the null, with 12 workers on the project PC.
       - At 999 draws that is about 1,080 s per dataset, or 15.0 hours for 600 datasets on 12 workers, under the 72 hours of §14.
       - It was measured with the 20-draw surrogate file (0.75 GB) held in memory. The production file (999 draws, about 38 GB) is larger than the PC's free memory, so reading it may slow a run there.
  - **GPU path:** the frozen GPU null returns the same NumPy arrays (windows × pixels) as the CPU backend used here, so the surrogate writer takes either. The writer has not yet run with the GPU backend. It first does at the InSAR step.
  - **Where the planted-signal check runs:** on the processing server, as the user decided on 2026-11-10. §14 names no machine ("CPU only"), so this is not a deviation. The field file, the surrogate file and the feature and event tables it reads are copied there; the records and the report are copied back and hashed here. The first round's projection uses the server's worker count.
  - **Still open before any InSAR file is opened:** nothing. Every item of §13 step 2 is entered above, except marking sale-triggered events, which does not apply because secondary 14 is removed under option A. The machine for every heavy run, including the secondary analyses (§13 point 6), was settled the same day (§14, compute location).
- **InSAR step, part 1: downloads, pixel grid, surrogate engine and construction-mask permits, filled in after freezing** (2026-11-10/11; `production/`, file hashes in `production/SHA256SUMS`, SHA-256 `32bda97eb4595e909e8f560cfe017185109d6492501ad8a27bee7d05ce833d88`; records in `production/check/`). No displacement value was read for any entry below. No outcome was joined.
  - **Surrogate engine on the server (§14, compute location):** checked on the planted-signal check's synthetic field, with the real pixel grid, houses and features (`check_parallel_draws.py`, `check/check_parallel_results.json`).
    1. **Across machines:** at neighbour cap 200, the first 3 draws made in parallel on the server are byte-identical to the same draws made one after another on the project PC by the planted-signal check (file `21c67bad…`). Neighbour counts are identical.
    2. **Parallel against one after another:** at the frozen cap of 1,000, 3 draws written in parallel and one after another on the server give the same file (SHA-256 `43cee0df35d428930226c7538c84235d22f63d4b7218d55838b217ec8db58cd5`) and the same neighbour counts (1,000, 641 and 1,000).
    3. **Time:** with 32 worker processes, 64 draws took 1,792 s. That projects 999 draws at about 7.8 hours, with about 10 GB of memory per worker. The first 3 of those draws equal the ones made one after another.
    - **First attempt, stopped:** the check's byte comparison used `np.array_equal`, which calls two NaN cells unequal. Step 1 therefore reported "not byte-identical", although the largest difference was 0 and the NaN patterns were identical. The check was stopped during step 2 and rerun with a comparison of the raw bytes. The aborted log is kept as `check/parallel_check.first_aborted.log`.
  - **Machine equivalence** (`check_machine_equivalence.py`): the server reran the planted-signal pipeline on the PC's input files: event dates, surrogate quantiles and 12 dataset records. Every output is identical to the PC's, with a largest difference of 0. The two machines' kernel hashes are identical too.
    - A synthetic field generated afresh on the server differed from the PC's, so the comparison uses the PC's files. The cause was not found.
    - The server's environment for the OPERA files is an exact copy of the PC's conda environment, built from its explicit package list.
  - **DISP-S1 download (§7, §13 step 3)** (`i01_download_disp.py`, `check/disp_download.json`): 254 granules of frame 28482, version 1.0, from 2016-07-10 to 2025-11-20, clipped with opera-utils 0.25.8 to the study area plus 2 km. All arrived on the first attempt. The 254 match the count at step 0 (§3).
    - Manifest SHA-256 `e261a28f544f41a618d605629925e0628f11b8a759a19fb35766f3ea01611fac`. Every file's hash was rechecked on the server after copying.
  - **STATIC layers** (`i05_download_static.py`, `check/static_download.json`): the frame's one STATIC granule, `OPERA_L3_DISP-S1-STATIC_F28482_20140403_S1A_v1.0` (CMR C3959290248-ASF). It holds the DEM, the layover and shadow mask, the line-of-sight unit vectors and the metadata, each matching the MD5 published by ASF. Manifest SHA-256 `3d97aada0c79c7430643f54ad4e03ee3da9ff5753fc21e1583bf8979ad777933`. No rule uses them. They are kept for reference.
  - **Pixel grid confirmed** (`i02_grid_check.py`, `check/grid_check.json`; coordinates and grid metadata only):
    - all 254 granules are on EPSG:32614 with 30 m pixels, pixel centres at 30k + 15 m, and identical x and y vectors;
    - the subset is 1,664 × 1,358 pixels (x 600,015–640,725, y 3,328,605–3,378,495);
    - every eligible house's checkpoint-1 pixel lies on it.
    - **The pixel grid assumed at checkpoint 1 holds,** so the pixels, blocks and folds stand and nothing is rebuilt.
  - **Construction-mask permits (§7, §14 entry of 2026-11-11):**
    - **Permit coordinates** (`i04_permit_points.py`, `check/permit_points_fetch.json`): all 270,654 mask permits of the checkpoint-1 table were found by permit number; 236,035 have coordinates. Points file SHA-256 `c59590bfaf48141f150568fa015eea8ed89fc7e8f4affbd5e67aa891f5611eea`.
    - **Pixels per permit** (`i06_mask_permits.py`, `check/construction_mask_permits.json`): 88,191 mask permits were issued from 2015-01-01 to 2025-11-30.
      - Placed by: a 2018 parcel polygon 67,771; a Dec-2025 parcel polygon 8,295; the permit's coordinates 9,774. Unplaced: 2,351.
      - From 2015-07-11, the earliest date any window's mask reaches: 64,231, 8,287 and 9,498 placed, and 2,319 unplaced (2.7%).
      - Every placed permit masks at least one pixel of the subset. A permit masks a median of 17 pixels, at most 9,557 (one large tract).
      - Table SHA-256 `68021fb29372a0960e69aa52e4c34f0b3b82b345587531db8687334ac59457cd`.

- **InSAR step, part 2: window values, fields and the checks before outcomes, filled in after freezing** (2026-11-11; scripts in `production/`, hashes of this part's scripts and records in `production/SHA256SUMS_part2`, SHA-256 `e3027b4cb3fdba12657b444d052dbe4f8b3ec1c321c4e4a3d401ebddda0e7acb`; records in `production/check/`; all heavy runs on the server). No outcome was read, joined or compared. Every script reads only prop_id, pixel, cell, soil and Baseline 1 completeness columns, never an event, fold or block column.
  - **Inputs** (`i07_insar_inputs.py`, `check/insar_inputs.json`): 149,316 eligible houses on 114,058 pixels in 5,645 eligible 250 m cells. 839,735 subset pixels have their centre inside the full-purpose boundary.
  - **Reference-point labels** (`i03_download_refpoint.py`, `check/reference_points.csv`, `check_refpoint_component.py`, `check/refpoint_component.json`):
    - The label at the frame's reference point is 0 in all 254 products.
    - The component around it (the most common non-zero label in the 11 × 11 window) is the city's main component in all 254 products. See the correction note under the §14 connected-component entry.
  - **Window values, first run** (`i08_window_values_run1.py`, 102 s with 24 processes; `check/window_values_run.json`, `_coverage.csv`, `_windows.csv`, `_products.csv`):
    - **How the wording was applied:**
      - The window of study month m is [first day of m − L months, first day of m). The construction mask covers permits issued from 365 days before the window start to the window's last day.
      - The full-period window (sign and clay checks) runs from the first reference date (2016-07-10) to the day after the last acquisition (2025-11-21), with no construction mask, as NYC's sign check.
      - **Acceleration:** the 12-month velocity of the window ending before m minus that of the window ending 12 months earlier, each under its own window rules. Together their masks cover the 24-month window's own permit range.
      - **Local relative motion and the 100 m availability count** are measured from the centre of the parcel's pixel, so parcels sharing a pixel share the value. The user decided this on 2026-11-11 ("Pixel centre").
      - **Lags:** the 24-month window ending 1, 3, 6 or 12 months earlier. There is no value where that window would start before the first granule.
      - **NYC-design cells (secondary 1):** the mean of the valid pixels whose centres fall in an eligible 250 m cell.
      - **Deep model (secondary 20):** each product's displacement, validity and label flag are kept at the house pixels (`house_series.npz`).
    - **Coverage** (house pixels with a value, of 114,058; houses with a value, of 149,316):

      | Window | Epochs | Valid before construction mask (median) | Removed by construction mask (median) | Valid (median, range) | Houses (median) |
      |---|---|---|---|---|---|
      | 24 months (88) | 45–61 | 112,076 | 40,120 | 71,366 (70,020–74,250) | 94,384 |
      | 12 months (100) | 21–31 | 112,766 | 30,962 | 81,510 (79,049–84,572) | 107,460 |
      | 36 months (76) | 73–91 | 111,472 | 47,620 | 63,474 (62,940–64,840) | 84,489 |
      | Full period | 255 | 107,527 | none | 107,527 | 140,374 |

    - **Independent check** (`check_window_values.py`, `check/window_values_check.json`): passed.
      - Main labels were recomputed per product. House series were read directly from the files. The coverage arithmetic and the reference changes per chain were checked.
      - A separate per-pixel route (chain found by dates, `numpy.linalg.lstsq`, mask found from the pixel side) recomputed 12 random windows plus the full period. It covered v, amplitude, the unmasked velocity, local relative motion, the availability count and NYC cell means.
      - There were 0 mismatches, and the largest difference was 3 × 10⁻⁶ mm/yr.
  - **Fields** (`i09_fields.py`, `check/fields.json`): 12 files in testa_core's `save_field` format, each read back with `load_field`: v, amplitude, local relative motion, acceleration, v without construction mask, availability count, 12- and 36-month v, and lags 1, 3, 6 and 12.
  - **Checks before outcomes, first run** (`i10_checks.py`, `check/checks_run1_checks.json`):
    - **Sign check: not below.** Of the 39 perimeters (35 inactive, 4 active), 32 hold valid pixels (1,183 of 8,110 footprint pixels). The landfill median is +8.87 mm/yr, against a subset median of +8.02 (city +8.40), a difference of +0.84. By §7, work stopped until the cause was found and logged.
    - **Clay contrast: demonstrated.**
      - Median full-period amplitude by class: low 2.87 mm (16,027 parcels), moderate 2.61 (90,136), high 3.50 (8,526), very high 3.63 (24,605).
      - The high and very high classes minus the low class: +0.72 mm, 95% block-bootstrap interval 0.41 to 1.03 (213 blocks of 2 km).
      - Bootstrap: 2,000 draws, seed 2026, percentile interval. These are authors' choices: NYC's bootstrap size, fixed before the run.
  - **Cause of the sign-check result** (diagnostics, outcome-blind: `diag_sign_check.py`, `diag_sign_series.py`, `diag_unwrap_steps.py`, `diag_slip_stakes.py`; records `check/checks_run1_*`):
    - **Regional gradient:**
      - The full-period velocity rises from west to east: the city median by 5 km band of x goes from +6.9 to +9.7 mm/yr. A fitted plane gives +0.08 mm/yr per km east.
      - Most landfills lie east of the subset's median, which accounts for their raw excess.
      - After the plane is removed, the pooled landfills sit at the subset median (+0.10 against +0.09 mm/yr). This is a description, not a rerun of the check.
    - **Old landfills** (inactive, closed mostly between the 1940s and the 1980s):
      - There is no detectable pooled settlement. Against their own surroundings (100–500 m outside the perimeter), the median contrast is −0.24 mm/yr, 20 of 30 are below zero, and the pixel-weighted mean is −0.77.
      - Two sites settle clearly: #5 (closed 1982) at −4.6 and #31 (closed 1979) at −5.0 mm/yr against their surroundings.
    - **Active landfills:** only two hold valid pixels (100 of about 3,200 footprint pixels). They lie in a north-east zone at about +15 mm/yr, and their surroundings are as high or higher, so the footprint is not rising relative to its surroundings.
    - **That zone's excess is phase-unwrapping cycle slips:**
      - Against the city's common mode, its series has lasting steps of +28.5 mm (2019-10-23 to 11-04) and +24.3 mm (2020-12-28 to 2021-01-09). Its yearly mean relative to the city goes from about 0 (2016–2018) to +57 mm (2021).
      - Across all house pixels with a full-period value, lasting steps of 20 mm or more (6-month means on either side) were found at 1,228 pixels (1.1%; 1,756 houses).
      - Their sizes peak at 28–32 mm, about one half-wavelength (27.7 mm). They fall mostly on three dates (2019-11, 2021-01, 2022-12/2023-01) and are concentrated in the north-east of the city. Only 6 of 3,152 fall at a reference change.
      - The connected-component labels did not flag them.
      - With 4-epoch means instead, 21.5% of pixels are flagged with no peak near 28 mm. Those are atmospheric episodes of a few weeks, so the 6-month means were used.
    - **What the slips did to the primary field:**
      - In the first run's 24-month field, windows containing a slip held 73,006 house-window values (0.9% of all values), in all 88 windows.
      - Their median percentile rank in their window was 98.9%. 16,494 lay above the 99.5th percentile, about 40% of all values there.
    - **The sign itself is confirmed:**
      - The full-period seasonal curve of the high and very high clay parcels minus the low parcels peaks in late March and has its trough in late September (day of year 272, block-bootstrap 95% interval 260–287). That is clay shrinking in the dry season, as expected if positive is toward the satellite.
      - NYC's sign check passed with the same code and product version.
    - **Logged and resumed:** the cause is logged here. Processing was corrected for the cycle slips before any outcome was compared (§14 entry "Lasting cycle slips", decided by the user on 2026-11-11). The sign check's result remains "not below".
  - **Cycle-slip screen** (`i11_slip_screen.py`, 49 s; `check/slip_screen.json`):
    - The test could be made at 2,048,813 of the 2,259,712 subset pixels, including 113,952 house pixels (median 240 testable epochs). 1,505,850 slips were found at 355,109 pixels.
    - **At house pixels:** 2,741 pixels (2.4%; 4,183 houses). Step sizes peak at 28–32 mm, and the most common dates are 2020-12-28 (2,383), 2019-10-23 (1,116), 2022-12-30 (568) and 2022-05-28 (421).
      - Among the house pixels with a full-period value, it agrees with the diagnostic above: 1,233 against 1,228, with 1,227 in both.
      - The others lack a full-period series, which the diagnostic could not test. They include a second zone in the far south-east.
    - **Within 270 m of a house pixel:** 2.4% of pixels, again with the peak at 28–32 mm.
    - **Further from houses:** elsewhere inside the city 10.0%, outside it 21.9%, with no peak near 28 mm. These are mostly atmospheric differences from the city's common mode. Among the analyses, they reach only the sign check's area median: Test A and Test B use house pixels, their 250 m rings and eligible cells. The rule was applied as logged.
  - **Window values, corrected (primary)** (`i08_window_values.py --slips`, 105 s; `check/window_values_slips_*`):
    - The slip rule removes a median of 753 house pixels per 24-month window (5–2,300). That leaves a median of 70,310 valid house pixels and 92,950 houses (first run 71,366 and 94,384).
    - 12 months: 81,160 and 106,903. 36 months: 62,506 and 82,876. Full period: 106,294 house pixels (1,233 removed by the rule) and 138,611 houses.
    - Of the 73,006 slip-affected house-window values of the first run, 1,106 (0.01% of all values) keep a value. These are slips the diagnostic placed differently.
    - Fields: `fields_20261111_slips/` (`check/fields_slips.json`). This is the field set for the decoy and real runs. The first run's fields serve the added sensitivity analysis.
    - **Independent check of the corrected run** (`check_window_values.py` with the slip table, `check/window_values_check_slips.json`): passed.
      - The checks were the first run's, with the slip rule looked up per pixel from `slips.npz` on the per-pixel route.
      - Labels matched in 254 of 254 products, house series matched exactly, and the coverage sums and reference changes agreed.
      - Across 12 random windows plus the full period there were 0 mismatches. The largest difference was 2.8 × 10⁻⁶ mm/yr.
  - **Checks repeated on the corrected values** (reported beside the first results; `check/checks_slips_checks.json`):
    - Sign check: 945 valid footprint pixels; landfills +8.77 against a subset median of +8.04 (city +8.39). Still not below.
    - Clay contrast: +0.67 mm, 95% interval 0.38 to 0.98, demonstrated. By class: low 2.87, moderate 2.61, high 3.50, very high 3.57 mm.
  - **Still to do in step 3:** the conditional-null surrogate files on the corrected field, and the variogram checks (§10: Test A 20 windows, seed 7; Test B 5 quarters, seed 8). Taken up in part 3 below.
- **InSAR step, part 3: surrogates, Test B cell field and variogram checks** (2026-11-11; scripts in `production/`; records in `production/check/`; all runs on the server). Hashes of part 3's scripts, server job scripts (`production/server_scripts_part3/`) and records are in `production/SHA256SUMS_part3`, SHA-256 `9f8744170f44152b76950f39a0168f625f4aecc9a3fd9387ce37b50d70daea95`. They cover the decoy run below. The PC copies of the scripts equal the ones that ran on the server. No outcome was read, joined or compared. The method entries below were written before any surrogate or check result existed.
  - **Server GPU (§14 compute location):** on 2026-11-11 the user asked to use the server's GPU and 64 workers.
    - The driver mismatch was worked around without any system change. NVIDIA's own user-space libraries for the loaded kernel module (550.163.01), with hashes checked against NVIDIA's repository index, were unpacked into the project's server folder. With them the GPU answers.
    - The GPU is in use by another user's service, which holds 21.7 of its 24 GB. The null needs about 21.5 GB. That service is not ours to stop.
    - **So the surrogates are made on the CPUs,** with the engine of §14, as 64 worker processes, the most §14 allows. The engine that ran is recorded with each file.
    - **Update, 2026-11-11 about 14:00 EET:** the user then allowed that service to be paused. It runs in a Kubernetes cluster on the server, under automatic sync from a Git repository. With the user's approval:
      - its automatic sync is switched off and the service is scaled to 0;
      - the GPU run below is made;
      - the service and its sync settings are then restored exactly as saved.
      The saved copies are on the server in `work/gpu_pause/`. The restore runs automatically when the GPU job ends, whether it succeeds or not. No other workload in that cluster was waiting for the GPU.
  - **Test A conditional-null surrogates** (`make_surrogates.py --backend cpu --workers 64`; field `fields_20261111_slips/field_v.npz`, SHA-256 `7a9ad77f…`): 999 draws, seed 2027, neighbour cap 1,000, on 107,243 null pixels by 88 windows. Started 2026-11-11 12:26 EET.
    - **Result:** all 999 draws completed at 18:46:00 EET, taking 6 h 20 min.
      - File `surrogates_20261111_slips/surrogates_conditional.npy`, SHA-256 `07bf0d54eef4b62389ce81d62732388cbf62c9cc66a22a44e5d67308d556c055`. The hash was recomputed on the server and equals the one recorded in the file's metadata. The file was flushed to disk.
      - Neighbour count 28 in 997 draws and 18 in 2: identical, draw by draw, to the GPU file's.
      - Records: `check/testa_surrogates_cpu.json` and `check/testa_surrogates_cpu.run.json`. The GPU run's record is `check/testa_surrogates_gpu.run.json`.
      - **This is the Test A null file** (see the file-choice rule below).
  - **Test A surrogates, frozen GPU path.** §14 says: "If the server's GPU is repaired first, the frozen GPU path may run there instead." This run uses `make_surrogates.py --backend gpu`: the frozen `LowMemVariogramNull` on CuPy, making the draws one after another. It uses the same field and settings and writes to `surrogates_20261111_slips_gpu/`. This entry was written before the run.
    - **Environment:** CuPy 14.2.0 (`cupy-cuda12x`) with NVIDIA's CUDA 12.4 library wheels, on the user-space driver 550.163.01 (CUDA 12.4), on an NVIDIA A30. NumPy 2.5.3 and SciPy 1.18.1 are the CPU run's own installation. The calibration's GPU check used CuPy 14.2.0 on CUDA 13.2 (RTX 3090). This environment is therefore new, and it is checked below.
    - **Check before the pause** (`check_gpu_small.py`, SHA-256 `b714860e…`; `check/gpu_small_check.json`):
      - What was compared: the GPU class against the §14 CPU engine, on small synthetic masked fields at the production settings (cap 1,000, max lag 16, chunk 8). Four draws went through the engines directly and three through the conditional null.
      - Result: the same neighbour counts and missing values, a largest difference of 1.4 × 10⁻¹⁴, and identical values once stored as float32.
    - It runs as one process beside the CPU run's 64 workers, so that the two can be compared. Its work is on the GPU, with one CPU thread. It is not a draw worker.
    - **Which file is used (fixed now):**
      - **Agreement test:** both files store float32. A float64 difference of about 10⁻¹⁴ can still, rarely, round to neighbouring float32 values. Two draws therefore agree when all of the following hold:
        - they have the same neighbour count;
        - they have the same missing values;
        - every value is identical as float32, or differs by at most one float32 rounding step.
        The share of values that are not identical is reported.
        - **Neighbour counts:** a file records its neighbour counts only when it completes. If the CPU run is stopped first, its counts are never written. Where only one file has counts, value agreement stands in for the count check, because a different count would smooth differently and give different values. (Added at 13:55, before any comparison was made.)
      - **Early check:** the first 3 draws are compared as soon as the GPU file holds them. If they do not agree, the GPU run is stopped.
      - **GPU file used:** if all 999 GPU draws complete and every draw held by both files agrees. The CPU run is then stopped, and the queue below is restarted on the GPU file.
      - **CPU file used:** in every other case.
    - **Pause and start:**
      - Sync was switched off and the service scaled to 0 at 13:49–13:50 EET.
      - At 13:51 the GPU was free (24,050 MiB), the sync settings held, and the replica count stayed at 0.
      - The GPU run started at 13:51. It used 22.3 GB of GPU memory.
    - **Early check** (`check_gpu_cpu_draws.py`, SHA-256 `47d1d370…`; `check/gpu_cpu_first3.json`): draws 0–2 of the GPU file against draws 0–2 of the CPU file. Of 17,453,010 values, none differ: the two are byte-identical, with the same missing values. Passed.
    - **GPU run:** all 999 draws completed at 16:19:40 EET, taking 2 h 28 min (about 8.9 s per draw).
      - File `surrogates_20261111_slips_gpu/surrogates_conditional.npy`, SHA-256 `e1f95841ff17d687…`, shape 999 × 88 × 107,243.
      - Neighbour count 28 in 997 draws and 18 in 2.
    - **Full comparison** (`check/gpu_cpu_all.json`, SHA-256 `84bdf14b…`): the 563 draws the CPU file then held, 3,275,348,210 values in all.
      - Missing values are identical in every draw.
      - 164 values in 144 draws are not identical, a share of 5.0 × 10⁻⁸.
      - Of those, 152 differ by one float32 step; the largest is 1.9 × 10⁻⁶ mm/yr, at a value between 16 and 32.
      - The other 12 differ by 2 to 10 steps. All 12 are values of size below 1.3 × 10⁻⁷ mm/yr, where one float32 step is tiny, and their absolute differences are at most 2.9 × 10⁻¹⁴ mm/yr. This is the same float64-level agreement as the checks above.
    - **Result: the agreement test did not pass as worded,** because of the 12 values more than one step apart. **The CPU file is therefore used,** as the rule says. The CPU run continues and the queue below is unchanged.
      - The weakness of a one-step test for values near zero was seen only after the comparison. It is recorded here as a finding, not as a reason to set the rule aside.
      - The GPU file is kept on the server as a record. It is not used by any analysis.
    - **Incident: the other service did not come back.**
      - At 16:19:41–42 the automatic restore ran as planned: replicas back to 1, and both sync settings back exactly as saved (checked against the saved copies at 16:20).
      - The service's new pod then failed to start ("error mounting /run/nvidia-persistenced/socket … no such file or directory").
      - Cause (read-only checks): on 2026-10-10 06:58 the host's NVIDIA packages were upgraded to 580/570 without a reboot, and nvidia-persistenced stopped. Inside the cluster's node container, all 19 NVIDIA driver files and the persistenced socket are mounts of files since deleted on the host. The running pod kept working, but no GPU pod could start after 2026-10-10. Pausing the service exposed this.
      - My pre-pause checks looked for other workloads waiting for the GPU. They did not test whether a GPU pod could start at all.
      - The user was told at about 16:35. The user chose: notify the service owner, and reboot the server after the CPU file completes (about 19:20). Nothing further was changed in the cluster; the pod starts by itself once the node can mount the driver again.
      - **Reboot, 2026-11-12:** the user asked "Reboot the server".
        - Pre-checks at 08:43, read-only: nobody was logged in and none of our jobs were running. The NVIDIA 580.178.04 kernel module was built (DKMS) for both installed kernels (5.15.0-1104 and -1115). The cluster's containers restart by themselves (`unless-stopped`).
        - `sudo -n systemctl reboot` was issued at 08:43:57.
        - The user then wrote "Forget about rebooting right now", after the command had already gone out. The server was unreachable at 08:49 while it restarted. The user then said to keep going.
        - Every result of part 3 was complete and on disk before the reboot.
  - **Test B cell field** (`i12_testb_cells.py`, `check/testb_cells.json`; reads only property ID, pixel and 250 m cell from the grid table):
    - 5,645 cells of 250 m hold an eligible parcel point (5,019 hold three or more), in 213 blocks of 2 km.
    - A cell's value is the mean over its eligible parcels with a value, and it has none below 3 parcels (§7). Windows are i08's 12-month windows of the 28 quarter starts (2018-10 to 2025-07).
    - Primary field (v, corrected run): 4,982 cells have a value in at least one quarter, a median of 4,622 per quarter.
    - Also written for later analyses: the first run's v (§14 sensitivity analysis), lags 1, 3, 6 and 12 months (secondary 15), the 24-month window (16), amplitude, local relative motion and acceleration (17), and the 88 monthly 12-month windows (19).
    - **Block of a cell (authors' choice):** the 2 km block of the UTM 14N grid that contains the cell. A 250 m cell lies in exactly one such block. The checkpoint-1 house blocks follow the pixel centre, and 931 houses' points lie in another block than their pixel's. That would give some cells two blocks, which `test_b.py` rejects.
    - **Independent check:** cell values recomputed by another route (group means by cell label) for v, first-run v, the 24-month window and acceleration in all 28 quarters: no difference in which cells have a value, largest difference 8.5 × 10⁻¹⁴ mm/yr.
  - **Test B surrogates** (`make_testb_surrogates.py`): the §14 CPU engine at 250 m (cap 1,000, max lag 16, chunk 8) on the 4,982 cells, all 28 quarters per draw. 999 draws each: seed 2034 (Test B) and seed 2035 (remodel Test B), 64 workers. They are queued to start after the Test A file. A 3-draw trial took 7.5 s per draw (neighbour count 169).
    - **Result, seed 2034:** 999 draws completed at 18:52:02 EET, with 330 s of drawing. File `testb_surrogates_20261111/testb_v_seed2034.npz`, SHA-256 `0bc1305e07d0c3481f53bfa36f52aa0696e66138aedea0524c445af3f66f337d`, with a median neighbour count of 169.
    - **Result, seed 2035:** 999 draws completed at 18:57:36 EET, with 330 s of drawing. File `testb_surrogates_20261111/testb_v_seed2035.npz`, SHA-256 `b67577695866d104a4c6bf65212c345fe4c1fff897b52444693dd6214d92df24`, with a median neighbour count of 169.
    - **Parallel against one after another:** the parallel runner was checked on the conditional engine (part 1). For this engine, the first 3 draws of the seed-2034 file are compared by raw bytes with the 3-draw trial made one after another (`check_testb_parallel.py`). The Test B null is not used before this passes.
      - **Result: passed** (`check/testb_parallel_check.json`, SHA-256 `a5d9ebe1…`): byte-identical, with the same neighbour counts, cells, quarters and seed.
  - **Per-draw window quantiles** of the Test A surrogates (`planted_signal.py quantiles`, unchanged), for the decoy run, the planted-signal check and the real run: queued after the variogram checks.
  - **Variogram checks: method** (`check_variogram.py`):
    - As NYC, the observed semivariance in each lag bin is compared with the 2.5–97.5% range of the 999 surrogates. Lags are 1–16 cell widths, then 1 km bins up to 20 km.
    - Test A's field is the null's own field: raw velocity on the null pixels. Windows are `np.sort(default_rng(7).choice(88, 20, replace=False))`.
    - **30 m bins (authors' choice):** lag 16 ends at 0.495 km. The 1 km bins therefore run from (0.495, 1] to (19, 20] km, so no distance up to 20 km is left out. NYC's 250 m cells began them at 4.125 km.
    - **Computation for Test A:** NYC's list of pairs does not scale to 107,243 pixels (about 5 × 10⁹ pairs within 20 km). The same sums are formed exactly by masked FFT correlations on the 30 m grid, zero-padded so that no lag up to 20 km wraps around.
      - Checked on the field before use (`check/variogram_validate_a.json`): lags 1–16 equal the frozen `nyc_lib.Lags.vario` within 4.6 × 10⁻¹⁴, relative. All 36 bins equal direct pair sums on a 6,000-pixel sample within 5.0 × 10⁻¹⁴.
    - Test B uses NYC's direct pair sums and NYC's bins, from (4.125, 5] km. Quarters are `np.sort(default_rng(8).choice(28, 5, replace=False))`.
    - The checks are queued after the Test B surrogates. Whatever they show, no null changes (§10).
  - **Variogram check, Test A: result** (2026-11-11 19:02 EET, 215 s; `check/variogram_check_a.json`, SHA-256 `0ebbed61…`; `check/variogram_check_a.csv`, `33c392f2…`). Reported as §10 requires; the null is not changed.
    - **Inputs:** the 999 surrogates of the Test A null file (`07bf0d54…`), neighbour count 28 in 997 draws. Windows: 2018-08, 2018-12, 2019-06, 2019-07, 2020-01, 2020-06, 2020-07, 2022-01, 2022-02, 2022-03, 2022-08, 2023-05, 2023-10, 2023-12, 2024-01, 2024-04, 2024-05, 2024-09, 2025-09, 2025-11.
    - **Lags 1–16 (30–480 m):** the observed semivariance lies inside the surrogates' 95% range at 43 of 320 window-lags.
      - The surrogates are rougher than the field at short range. As a share of the observed value, the median surrogate is 1.38× at lag 1 (30 m) and 1.07–1.14× at lags 2–16. No window is inside at lags 1–3.
      - Three windows (2020-01, 2022-02, 2022-03) are rougher throughout: 1.24–1.36× at lags 5–16.
    - **1 km bins from 0.5 to 20 km:** inside at 15 of 400 window-bins.
      - The surrogates are close to the field at 0.5–3 km (median 1.11× at 0.5–1 km, 1.03× at 1–2 km, 0.98× at 2–3 km). They carry less semivariance than the field at longer distances: 0.93× at 3–4 km, falling to 0.72–0.74× at 15–20 km.
    - **Over all 720 window-bins:** 58 are inside, 322 are below and 340 are above the range.
    - **Reading:**
      - The pattern is NYC's (§15 of the NYC plan): rougher surrogates at the first lags, and too little long-range variance beyond a few km. NYC's ratios were larger (1.69× at the first lag; 45–90% beyond 5 km).
      - The counts inside are much lower here. With 107,243 pixels, the surrogates' 95% range is very narrow; at lag 1 in 2018-08 it is 0.599–0.620 around a median of 0.610. So a small relative difference already falls outside, and the ratios carry more information than the counts.
      - What this means for Test A is read with the planted-signal check and the decoy run, not by changing the null. The §10 null keeps its fitted link with the baseline features and matches the residual's short-lag variogram only. Long-range structure in velocity that the features do not explain is therefore under-represented in the surrogates. NYC's check showed the same shortfall for its null. The frozen plan does not name it as a limitation, so it is recorded here, to be reported with Test A.
  - **Variogram check, Test B: result** (2026-11-11 19:31 EET, 1,753 s; `check/variogram_check_b.json`, SHA-256 `bbaa122b…`; `check/variogram_check_b.csv`, `209a5464…`). Reported as §10 requires; the null is not changed.
    - **Inputs:** the seed-2034 Test B null (`0bc1305e…`). Neighbour counts: 169 in 743 draws, 264 in 185, 411 in 3, 641 in 14 and 1,000 in 54. Quarters: 2019Q4, 2020Q2, 2020Q4, 2023Q1, 2025Q2.
    - **Lags 1–16 (250 m to 4 km):** the observed semivariance is inside the 95% range at 51 of 80 quarter-lags.
      - The surrogates are rougher at 250 m: 1.51× the observed value (median over quarters). Only 1 quarter is inside there.
      - They are close at 0.5–4 km: 0.91–1.10×.
    - **1 km bins from 4.125 to 20 km:** inside at 37 of 80.
      - The surrogates carry too little semivariance at long range: 0.91× at 4–5 km and 0.70× at 6–7 km, falling to 0.46× at 9–10 km and 0.24× at 19–20 km.
      - Many bins still fall inside because the surrogates' range is wide here. There are only 4,982 cells, and the neighbour count varies between draws.
      - 2025Q2 is inside at 16 of its 16 long bins; 2023Q1 is inside at none.
    - **Over all 160 quarter-bins:** 88 are inside, 11 are below and 61 are above the range.
    - **Reading:** this is the same pattern as Test A and NYC. The long-range shortfall is larger at 250 m than at 30 m. Beyond 5 km the surrogates carry 24–81% of the observed semivariance, against NYC's 45–90%.
  - **Still to do in step 3 after these:** the NYC-null surrogate file for secondary 8 (999 draws, seed 2027, §12 item 8). It is an input to a secondary analysis and holds up neither step 3 nor step 4.
- **Decoy run (§13 step 4): the runner, written before it runs** (`production/run_tests.py`, 2026-11-11). It runs the Test A and Test B primary analyses on the decoy outcome and later, unchanged, on the real one. It imports `testa_core.py` and the frozen `test_b.py` unchanged. Details the plan leaves to the script, fixed in its header:
  - **Decoys:** as NYC (`decoy_events`).
    - Each of the 2,846 events goes to the house numbered `default_rng(99).integers(0, 149_316, 2_846)` in property-ID order, keeping its date. Draws are uniform, with replacement and no redraws.
    - In decoy mode only the date column of the events file is read. No real event's house and no event or fold column enters.
  - **Decoy world, as the planted-signal check's synthetic world:**
    - a real first matched episode before 2018-08-01 is kept, and real episodes inside the study period are ignored;
    - a decoy sets its house's episode date (the earliest decoy, if a house is drawn twice);
    - real demolition dates are kept;
    - folds come from "the house holds a decoy".
  - **Cases:** one function in both worlds, with testa_core's drop reasons plus "not at risk at the event date" (an earlier episode, or an earlier event on the same date, at the house).
    - On the real events it cannot fire. On the planted check's synthetic field (validity only), the function equals `testa_core.real_cases`: 2,620 cases and identical drop counts. The folds recomputed from the events equal checkpoint 1's (`check/run_tests_selfcheck_synthetic.json`).
    - Controls use `default_rng(2029)` in case order (§8A).
  - **Test B panel (§8B):**
    - y counts the events whose house is at risk at the event date, in the cell of the parcel point and the quarter of the date. Baseline 1 completeness and the house's own pixel value do not enter. The 4 real events on houses demolished on or before the event date are therefore not counted, as in Test A.
    - **Exposure date (authors' choice):** n is evaluated with `testa_core.at_risk` on the day before the quarter's first day. `at_risk` ends a house on its episode or demolition date. Evaluated on the first day itself, it would drop from n a house whose event falls on that day while the event counts in y, and remove a house demolished that day from its own quarter, where §5 removes it "from the next quarter".
    - Every counted event's house is checked to be in n of its row.
  - **Smoke tests (code only; numbers mean nothing):**
    - Test A in decoy mode on the planted check's synthetic field with its 20 draws: 2,397 decoy cases, run end to end (`check/run_tests_smoke_a_synthetic.json`).
    - Test B in decoy mode on the cell field with the 3-draw trial null: run end to end (`check/run_tests_smoke_b_3draws.json`).
  - **Queued on the server** after the per-draw quantiles and the Test B byte check, which it requires to pass. Test A uses all 999 draws with 64 workers.
  - **Per-draw window quantiles** (`planted_signal.py quantiles`, 48 workers, 2026-11-11 19:32 EET): `quantiles_20261111_slips/surrogate_quantiles.npy`, SHA-256 `99d9e71b…`, shape 999 × 5 × 88, made from the Test A null file `07bf0d54…` (record `check/testa_surrogate_quantiles.json`).
  - **Decoy run, result** (2026-11-11 19:34 and 19:38 EET; `check/decoy_test_a.json`, SHA-256 `1a3b40fc…`; `check/decoy_test_b.json`, `9d32f091…`). Both runs completed with exit code 0 and no code error. Nothing is changed because of them.
    - **Test A:**
      - Decoys: 2,846 decoy events (seed 99); 21 houses were drawn twice or more.
      - Cases: 1,568. Dropped:
        - 919 with no value in the window;
        - 184 missing a Baseline 1 input;
        - 144 not at risk at the event date;
        - 31 demolition-censored.
      - Rows: 74,829 case and control rows; 5,139 control rows dropped for missing inputs.
      - Folds: cases 362, 337, 304, 262 and 303.
      - Statistic: baseline average precision 0.0215; observed statistic −0.00013; p = 0.248 (247 exceedances of 999). The decision rule is not met, as expected on a random outcome.
      - The loss to "no value in the window" (32% of decoys) is in line with the coverage table of part 2. Test A's primary window is 24 months (§11), and the field file's 88 windows are that window. In 24-month windows a median of 94,384 of 149,316 houses (63%) have a value, mostly because of the construction mask. (Corrected on 2026-11-12: this line first cited the 12-month row.)
    - **Test B:**
      - Events: 2,658 decoy events counted, 2,483 inside the 28 quarters and 2,409 in rows used.
      - Rows: 129,682 cell-quarter rows. The model keeps 47,573 of them in 1,736 cells; rows of cells with no event are dropped by the cell fixed effects.
      - Estimate: β = −0.0039 per mm/yr (clustered SE 0.0029), a rate ratio per IQR (27.1 mm/yr) of 0.90 (95% CI 0.77–1.05).
      - p_B = 0.46 (459 exceedances of 999); not detected.
    - **The decoy run is a code check, not a result.** The step-4 condition is met: both tests run end to end on the real InSAR fields and the real nulls.
    - **Note for the real run:** if real events lose a similar share to missing InSAR values, Test A will have about 1,500 cases rather than about 2,700. The plan's power figures (§10) should be read with that in mind. The plan sets no minimum count: the real run is made once (§13 step 5).
- **Planted-signal check (§14 entry of 2026-11-10): run** (server; job script `work/insar/run_planted.sh`, 64 workers). The `planted_signal/` code on the server matches `planted_signal/SHA256SUMS` (`16a081c1…`).
  - **Usable real events** (`planted_signal.py event-dates`, 2026-11-11 19:42 EET; `planted_20261111/event_dates.csv`, SHA-256 `8bd81249…`):
    - 1,754 of the 2,846 events are usable in the primary comparison.
    - Dropped: 961 with no InSAR value in their window, 127 missing a Baseline 1 input, and 4 demolition-censored.
    - Only dates and validity were used; no velocity value was joined to an event (§14).
    - So the real run's Test A will have 1,754 cases (§13 step 5).
  - **Datasets:** 6 cells × 100 datasets, started 19:42.
    - **Projection** (`planted_20261111/projection.json`, written 19:56:02 after the first 64 jobs): 688 s mean per job, which projects 1.8 h for all 600 jobs. That is below 72 h, so there is no fallback and every cell keeps 100 datasets.
    - **Completed** 2026-11-11 21:40 EET: all 600 records, no code error. Each dataset has 1,754 synthetic events and 999 null draws.
  - **Result** (`planted_signal/PLANTED_SIGNAL.md`, SHA-256 `dca7936df8c3f8f77e8e849fa6f9004d67db7d6826c72e36ae939b88c41bbac7`; summary `planted_signal/run_20261111/planted_signal_summary.json`, `883f7b1e…`; the 600 records, the projection, the dates file and the log are in `planted_signal/run_20261111/`, hashed in `planted_signal/SHA256SUMS_run_20261111`, `1222e2f2…`). Hashes are equal on the server and the PC. Written and hashed before the real run, as §14 requires.

    | Cell | Meets §11 rule [95% Wilson] | Mean observed change [95% t] | Paired bias [95% t] |
    |---|---|---|---|
    | 1. nothing added | 5/100 = 5.0% [2.2, 11.2] | −0.00010 [−0.00016, −0.00003] | +0.00002 [−0.00003, +0.00006] |
    | 2. nonlinear soil, 0.65·t | 11/100 = 11.0% [6.3, 18.6] | −0.00026 [−0.00038, −0.00015] | −0.00001 [−0.00011, +0.00009] |
    | 3. hidden spatial field, 0.7·H | 5/100 = 5.0% [2.2, 11.2] | −0.00009 [−0.00023, +0.00004] | −0.00002 [−0.00008, +0.00005] |
    | 4. β = −0.1 | 34/100 = 34.0% [25.5, 43.7] | +0.00070 [+0.00054, +0.00086] | +0.00037 [+0.00027, +0.00047] |
    | 5. β = −0.2 | 75/100 = 75.0% [65.7, 82.5] | +0.00275 [+0.00253, +0.00298] | +0.00143 [+0.00127, +0.00159] |
    | 6. β = −0.4 | 100/100 = 100.0% [96.3, 100.0] | +0.00948 [+0.00907, +0.00990] | +0.00542 [+0.00513, +0.00572] |

    - **False-positive rates (cells 1–3):**
      - With nothing added, 5.0%, the nominal rate.
      - With the hidden spatial field, also 5.0%. The variogram check's long-range shortfall did not inflate it for clustering of this size (600 m).
      - Under the nonlinear soil effect, 11.0%. Its lower Wilson bound (6.3%) is above 0.05. Its p-values pile up at both ends (deciles: 20 in (0, 0.1] and 17 in (0.9, 1]).
    - **Power (cells 4–6):** 34% at β = −0.1 (OR 1.11 per IQR), 75% at β = −0.2 (OR 1.22), and 100% at β = −0.4 (OR 1.49). The paired bias is positive in all three, so the planted effect is seen beyond what the null's fitted field carries.
    - **Reading, as fixed in §14:**
      - The real run goes ahead once, with nothing changed.
      - If Test A is demonstrated, cells 1–3 are reported beside it. Cell 2 is stated as a limit of the result: if the baseline omits a nonlinear soil effect of this size, the test rejects at about 11% instead of 5%.
      - If Test A is not demonstrated, cells 4–6 are reported as the test's sensitivity at Austin's size, with 1,754 events.
    - The user is told this result before the real run (§14).
  - **Script hashes when queued** (SHA-256, the same on the PC and the server):
    - `run_tests.py` 020c67e0c9f32b01520d45ef9e5b8897eeb720c68c641160219692c72985628b
    - `i12_testb_cells.py` 937d2908c62c038b6adf0086dbf8397951e4992c3fb80b5b9dc700c7a9415fcb
    - `make_testb_surrogates.py` 37daf33fb7463f27ec00fd6432424b7164607bc89b43011fe28ff3dc39e72598
    - `check_variogram.py` 8db333ee843c1f508581b10807b3ab1cd0625f95b6c769452249dc908cf9ee84
    - `check_testb_parallel.py` 9c221ea3e12bb08f81240f10b2faa52384ce78429bac76355f2a07e279d566d3
- **Null (a) surrogates for secondary 8** (2026-11-12; `production/make_surrogates_nulla.py`, job `server_scripts_part3/run_nulla.sh`). The server was back at 08:53 after the reboot.
  - **Engine:** the variogram generator on the whole corrected velocity field of the null-field pixels, with no conditional fit. This is null (a) of §10, "the NYC null itself ... with the same draws and seed".
  - **Settings:** `CPULowMemVariogramNull` (the class the primary file's engine wraps), cap 1,000, max lag 16, chunk 8, seed 2027, 999 draws, 64 workers (`parallel_draws.py`), then per-draw quantiles (`planted_signal.py quantiles`, unchanged).
  - **Inputs:** outcome-blind, reading only the field and the checkpoint-1 tables. Started at 08:55 EET.
  - **Why the CPU:** the vLLM service holds the GPU again. Nothing waits on this file, and the CPU keeps it on the same engine as the primary file.
- **Items reported beside the decision (§9, §11, §12.8): how they are computed, fixed before the real run** (2026-11-12; `production/run_report.py`, written and hashed before the real run).
  - **The decision path is not changed:** `run_tests.py` stays as decoy-tested and gives the decision.
  - **Consistency check:** `run_report.py` rebuilds the same rows with the same `testa_core` calls. It asserts that its change in average precision and its 999 null statistics equal those in `run_tests.py`'s `test_a.json`.
  - The plan leaves the details below to the scripts. They are the authors' choices, written here before any real result.
  - **Secondary metrics (§9):**
    - pooled ROC AUC, pooled top-10% capture and top-10% capture within the risk set, computed with the frozen `nyc_lib.metrics` on the same out-of-fold scores;
    - their p from the same 999 conditional-null draws, as NYC reported a p for each metric.
  - **Directional concordance (§11), as NYC's `11_models.py`:**
    - Per risk set (its rows after controls missing inputs are dropped): the case's standardised velocity minus the median of its controls'.
    - Reported: the median over risk sets and its label, and the share of risk sets below zero.
    - The same differences with the raw velocity (mm/yr), plus the case and control raw medians.
    - The sign of the velocity coefficient in a logistic regression fitted on all rows.
  - **Remodel world (Test A and Test B specificity checks).** §11 says each test is "repeated unchanged" on the remodel negative control. This is read as follows:
    - **Events:** the 1,491 sampled remodel control events of checkpoint 1 (amended rule, §14), at their houses, dated by their first permit. Each must map to an eligible house; this is asserted.
    - **At-risk rule (§8):** item 3 uses the house's first matched remodel episode instead of its first foundation episode.
      - Source: all 9,235 houses of `remodel_first_episodes_amended.parquet`, any date from 1980, whatever their status.
      - Why: §4 applies the episode and first-event rules "unchanged" to remodel permits, including "a parcel whose first episode falls before the study period is never a case and never a control".
      - So the 7,465 houses whose first remodel episode came before the study are never remodel controls. The 54 unsampled candidates leave the risk set at their episode date.
      - Foundation episodes do not enter the remodel analyses. Demolition censoring is unchanged.
    - **Folds:** recomputed by the same function on all eligible houses, with the label "the house holds a remodel control event", as in the decoy world.
    - **Test A settings:** controls with seed 2030 (§11). The same conditional-null surrogate file and per-draw quantiles (999 draws).
    - **Test B:**
      - y counts the remodel events at risk at their date, as for foundation events;
      - n uses the remodel at-risk rule on the day before the quarter;
      - the cells, quarters, field and blocks are unchanged;
      - the null file is seed 2035.
      - **Replaced by the user's choice of 2026-11-12, made before the real run and before any remodel result.** Claude asked the user to choose between this reading and the literal one. §11 says "Test B is repeated unchanged with remodel control events as the counts". The user chose the literal reading ("Literal Test B exposure first"):
        - **Rows, n, v and blocks:** those of the foundation Test B panel, unchanged. n uses the foundation at-risk rule of §8 on the day before the quarter.
        - **y:** the remodel control events whose house is eligible and not demolition-censored on or before the event date (the rule run_tests.py applies to count foundation events), in the cell of the house and the quarter of the event date.
        - **Mismatch reported:** a remodel event may fall at a house that is not in n, because the house had an earlier foundation episode. Such events are counted in y and reported, not asserted away.
        - Remodel Test A is unchanged: it keeps the remodel at-risk rule above.
    - Only property IDs and dates of the remodel files go to the server.
  - **Test A refit block bootstrap (§9, §11 direct comparison):**
    - **Resamples:** 2,000 (NYC for logistic regression); resample *s* uses `default_rng(s)`, *s* = 0–1,999.
    - **Blocks:** the universe is the sorted 2 km blocks holding at least one row of either analysis (foundation or remodel). Each resample draws that many blocks with replacement.
    - **Rows:** each analysis takes all its rows of every drawn block, as many times as the block is drawn, with its own folds. Both analyses are therefore refitted on the same resampled blocks.
    - **Intervals:** the foundation, remodel and difference intervals all come from the same resamples (2.5th and 97.5th percentiles). Where one analysis's blocks fill the whole universe, its interval is NYC's procedure exactly.
    - **Per resample and analysis:**
      - both models are refitted out of fold;
      - the changes in average precision, ROC AUC and pooled top-10% capture are computed with NYC's `boot_rep`;
      - capture within the risk set is not bootstrapped, because resampling breaks the risk sets.
    - **Resamples without a value:** a resample with no case, or only cases, among its finite scores gives no value for that analysis, as NYC. Such resamples are counted per analysis. The difference uses the resamples where both analyses have a value.
  - **Test B direct comparison (§11):**
    - **Resamples:** 2,000, `default_rng(s)`, *s* = 0–1,999. The plan sets no count, so it follows Test A's.
    - **Blocks:** the universe is the sorted 2 km blocks of either panel's input rows (value and n > 0).
    - **Copies:** a block drawn more than once gives distinct copies of its cells and of the block, so the cell fixed effects and clusters stay well defined.
    - **Fit:** both panels are refitted with the frozen `test_b.fit_panel`, unchanged. The log rate ratio per IQR is β × the IQR of that resample's used rows, the estimator of §9 applied to the resample. The difference is foundation minus remodel.
    - **Failed fits** are counted by resample and reported, never dropped silently. The interval uses the resamples where both fits succeed.
  - **Nulls of §12.8:** the largest p across them is reported beside the decision.
    - **Null (a):** `run_tests.py testa`, unchanged, with the null (a) file and its quantiles.
    - **Free and within-block permutation:** 2,000 draws each, as NYC's `perm_fields`, copied unchanged.
      - Keys: `default_rng(10,000 + d).random(P)` over the null-field pixels, one ordering per draw for every window.
      - Within-block: by the pixel's 2 km block.
      - Each permuted field is standardised by its own quantiles over the eligible houses on null-field pixels (`testa_core.surrogate_quantiles`), as the surrogates are.
    - **MSR (999, seed 2026):**
      - NYC's `msr_draws` builds dense matrices of size n × n and a full eigendecomposition. With about 107,000 null pixels, each matrix is about 92 GB.
      - Whether it can run with the same arithmetic is checked separately. If it cannot, it is reported as not run, and the largest p is taken over the nulls that ran.
      - It does not hold up the real run.
  - **Decoy smoke test of `run_report.py`** (code check only; numbers mean nothing):
    - Foundation decoys as in `run_tests.py` (seed 99).
    - The remodel dates are moved to the houses `default_rng(199).integers(0, 149,316, 1,491)`. They are built as the foundation decoy world, with remodel episodes before 2018-08-01 kept and those inside the study ignored.
    - In decoy mode no real remodel event's house is read. The real remodel results are first computed in the real run (§13 step 5).
  - **Server files for the remodel world** (`production/export_remodel_server.py`; record `check/remodel_server_files.json`):
    - Inputs: the two checkpoint-1 remodel tables, hash-checked against `checkpoint1/remodel_controls_2018.json`.
    - Output: copies with the property ID and the first-permit date only:
      - events: 1,491 rows, 2018-08-01 to 2025-11-21, `773f48d3…`;
      - first episodes: 9,235 rows, 1980-01-08 to 2026-10-28, `04e03d52…`.
    - The hashes are equal on the server.
  - **Fix found by the synthetic check, before any run on data:** the Test B bootstrap first used forked workers. These hung after the parent had fitted a panel (pyfixest's thread pools are not fork-safe), so the bootstrap now uses spawned workers. On a synthetic panel it ran 16 resamples with no failed fit.
  - **Decoy smoke test** (2026-11-12 09:10–09:13 EET, server, 48 workers; `server_scripts_part3/run_report_smoke.sh`; records `check/report_smoke_a.json` `6a1cdeb7…` and `check/report_smoke_b.json` `467e479c…`). Code check only; the numbers mean nothing. Run with 20 null draws, 40 resamples and 10 permutations for Test A, and 5 null draws and 40 resamples for Test B.
    - **Test A:**
      - Rebuilt foundation analysis equal to the decoy run's `test_a.json`: cases, rows, drop counts, baseline, observed change and the 20 null statistics, with differences of 0.0.
      - Remodel decoy world: 838 cases.
      - Bootstrap universe: 200 blocks. The foundation rows lie in 198 and the remodel rows in 195; no resample lacked a value.
      - Every item was computed.
    - **Test B:**
      - Rebuilt foundation panel equal to the decoy run's `test_b_panel.csv` and its β, with differences of 0.0.
      - Remodel decoy panel: 1,406 events counted.
      - Bootstrap universe: 192 blocks, with no failed fit in either panel.
    - **Projected time at the plan's counts:** about 30 min for the Test A report and about 15 min for the Test B report.
  - **Self-check on the real field** (`run_tests.py selfcheck`, 2026-11-12; `check/selfcheck_real.json`, `103920ba…`):
    - Inputs: the event dates and the field's validity only; no velocity value is joined to an event.
    - 1,754 cases, with drop counts equal to `testa_core.real_cases` and to the planted check's dates file (`8bd81249…`): 961 with no value, 127 missing an input, 4 demolition-censored.
    - The folds equal checkpoint 1's. Pass.
  - **Real-run job** (`server_scripts_part3/run_real.sh`, staged on the server, not started):
    - Test A (decision), Test B, the Test A report, the Test B report, and null (a) once its file exists.
    - It refuses to start if its output directory exists.
  - **Hashes, first version:** `production/SHA256SUMS_part4`, SHA-256 `05b033a3…`, 12 entries, with `run_report.py` `317bb4f5…`. Replaced by the version below.
  - **Remodel Test B exposure changed to the literal reading** (the user's choice of 2026-11-12, recorded under "Remodel world" above). The change is in `run_report.py` only:
    - the remodel panel takes n from the foundation at-risk rule;
    - its rows, n, v and blocks are asserted equal to the foundation panel's;
    - remodel events at houses not in n are counted and reported.
  - **Second decoy smoke test** (2026-11-12 09:20–09:22 EET, `server_scripts_part3/run_report_smoke2.sh`; records `check/report_smoke2_a.json` `35f261d4…` and `check/report_smoke2_b.json` `b28b66ed…`):
    - Test A: identical to the first smoke test.
    - Test B: the foundation check passes. The remodel decoy panel has the foundation panel's 129,682 rows. 64 counted decoy remodel events lie at houses not in n.
    - No failed bootstrap fit.
  - **Hashes, final:** `production/SHA256SUMS_part4`, SHA-256 `7f4a1650dc126770cb86650ed2e989ff16c8295ab550034095f70308fc2489c4`, 15 entries. Equal on the server. It covers:
    - code: `run_report.py` `ea0315b6…`, `make_surrogates_nulla.py` `76e17860…`, `export_remodel_server.py` `233df91a…`, and `run_tests.py` (unchanged, `020c67e0…`);
    - job scripts: `run_planted.sh`, `run_nulla.sh`, `run_report_smoke.sh`, `run_report_smoke2.sh` and `run_real.sh` `a5edd111…`;
    - records: the six records above.
  - **Labels fixed before the real run:**
    - **Null (a):** `real_20261112/nulla/test_a.json` comes from the decision code, so it carries the "REAL RUN" label and a `meets_rule` field. It is secondary 8 only. Its p is reported as the null (a) p, and its `meets_rule` field is never quoted.
    - **"The largest p across the nulls of §12.8" (§11):** the maximum of the null (a) p and the free and within-block permutation p's, for the change in PR AUC, labelled "over the nulls that ran; MSR not run" until MSR runs.
  - **Go-ahead:** on 2026-11-12 the user chose to start the real run once this change had passed a new smoke test and been hashed.
  - **MSR (secondary 8), not yet coded:**
    - The null field has 107,243 pixels. The longest edge of their minimum spanning tree, which NYC's MSR uses as the neighbour threshold, is 4.9 km, so each pixel has about 12,000 neighbours.
    - NYC's arithmetic needs a dense 107,243 × 107,243 eigendecomposition (92 GB per matrix, several matrices at once).
    - Whether to run it on the shared server is the user's decision. Until it runs, the largest p of §12.8 is over the nulls that ran, and it is labelled so.
    - **User's choice (2026-11-12):** "Timing test first". MSR is coded with NYC's arithmetic, timed on a subset to project memory and hours, and then decided within the 7-day secondary budget.
- **REAL RUN (§13 step 5), made once** (server; `work/insar/run_real.sh`, `a5edd111…`; started 2026-11-12 09:22:34 EET). A first launch at 09:22 failed before running anything ("Permission denied": the copied script lacked execute permission). No output directory was created, so the run below is the first and only one. Records are copied to `real_20261112/` on the PC with the same hashes.
  - **Test A, primary analysis: the decision** (`run_tests.py testa`, finished 09:23:52, exit 0; `real_20261112/test_a.json`, SHA-256 `c50f3da7ff87f6eff1b85410ac1102e77132b073d7771d9506c732da01e3f7b4`):
    - Events: 2,846. Cases: 1,754. Dropped: 961 with no value in the window, 127 missing a Baseline 1 input, 4 demolition-censored. These equal the self-check and the planted check's dates file.
    - Rows: 83,496; 5,958 control rows dropped for missing inputs.
    - Cases by fold: 319, 349, 346, 365, 375. Folds equal checkpoint 1's (asserted).
    - Baseline 1 + x/y: pooled out-of-fold average precision 0.04599.
    - **Change in PR AUC with velocity: −0.00058.**
    - **Conditional null (999 draws, seed 2027): p_A = 0.931** (930 draws at or above the observed change). The null draws have median −0.00042, 95th percentile −0.00023 and maximum +0.00002.
    - **Decision (§11): added held-out value of InSAR is NOT demonstrated in Austin.** The change is not positive, and p_A ≥ 0.05.
  - **Test B, key secondary** (`run_tests.py testb`, finished 09:27:07, exit 0; `real_20261112/test_b.json`, `489e822c79226dac9f9107250265a73cef0a154971e12734e1cf2316b6092647`; panel `real_20261112/test_b_panel.csv`, `af068f18576312826bc185b44ef0580e862d9f6a9aa4374edf3f40c7eaa63ddc`):
    - Events: 2,842 counted, 2,655 inside the 28 quarters, 2,553 in rows used.
    - Rows: 129,682. The model keeps 38,047 rows in 1,397 cells, 28 quarters and 145 blocks.
    - Estimate: β = +0.00022 per mm/yr (clustered SE 0.0028). **Rate ratio per IQR (27.0 mm/yr) 1.006, 95% CI 0.867–1.168.**
    - **p_B = 0.967** (966 exceedances of 999, seed 2034). **Not detected.** The direction is formally opposite (rate ratio above 1), but the estimate is essentially 1.
  - **Reading, as fixed in §11:**
    - The clay contrast was demonstrated (part 2: +0.67 mm, 95% interval 0.38 to 0.98).
    - **Test A:** row "Not demonstrated / Clay contrast demonstrated". The seasonal signal separates the soil classes as expected, yet a gain from 24-month velocity in locating recorded repairs was not demonstrated. The interval of the change (from the Test A report, below) shows whether a useful gain is excluded or the result is inconclusive.
    - **Test B:** row "Not detected / Clay contrast demonstrated". An association between within-area motion and later recorded permits was not detected at quarterly resolution. The rate-ratio interval, 0.87–1.17 per IQR, shows how large an association remains compatible with the data.
    - **Together:** "Neither", read through the clay-contrast label with the effect sizes and intervals.
    - **Planted-signal check, as fixed in §14:** Test A is not demonstrated, so cells 4–6 are reported as the test's sensitivity at Austin's size with 1,754 events: power 34% at an odds ratio of 1.11 per IQR, 75% at 1.22 and 100% at 1.49.
  - **Test A report: items reported beside the decision** (`run_report.py testa`, finished 09:35:40, exit 0; `real_20261112/report_a.json`, SHA-256 `4cf9abe0f9ce1940803f36a179efde9c9cde93e835380bfdb2746018f2d69dee`). None of these changes the decision.
    - **Rebuild check:** the rebuilt foundation analysis equals `test_a.json` (cases, rows, drop counts, baseline, observed change and all 999 null statistics; differences 0.0). Pass.
    - **Interval of the change in PR AUC:** refit block bootstrap, 2,000 resamples over the 201 blocks holding rows of either analysis. The foundation rows lie in 200 blocks, and no resample lacked a value.
      - **95% interval −0.00197 to +0.00034.**
      - It excludes changes above +0.00034, which is 0.7% of the baseline's PR AUC (0.046).
      - §11 set no number for a "useful" gain, so this upper limit is reported as it is.
    - **Secondary metrics** (same out-of-fold scores and the same 999 draws; nominal):

      | Metric | Baseline | Change | p | 95% interval |
      |---|---|---|---|---|
      | ROC AUC | 0.7242 | −0.0015 | 0.287 | −0.0044 to +0.0020 |
      | Pooled top-10% capture | 0.2685 | −0.0006 | 0.501 | −0.0203 to +0.0079 |
      | Top-10% capture within the risk set | 0.2811 | −0.0108 | 0.962 | not bootstrapped (as fixed) |

    - **Directional concordance** (1,754 risk sets, all with controls):
      - **Standardised:** median difference +0.0092, so the label is **opposite**; 49.6% of risk sets lie below 0.
      - **Raw:** median +0.025 mm/yr; 49.6% below 0. The cases' median velocity is 8.30 mm/yr and the controls' 7.91 mm/yr.
      - Coefficient of the standardised velocity over all rows: +0.0085.
      - Both medians are close to zero: case and control velocities barely differ.
    - **Nulls of §12.8** (change in PR AUC):
      - free permutation (2,000 draws): p = 1.000, null median −0.00004;
      - within-block permutation (2,000 draws): p = 0.995, null median −0.00020;
      - null (a): still running (below);
      - MSR: not run (timing in progress).
      - **Largest p so far: 1.000** (free permutation), over the nulls that ran. No further null can raise it.
      - The permutation p's for the other metrics:
        - free: ROC 1.000, pooled top-10% 0.840, within-risk-set top-10% 1.000;
        - within-block: ROC 0.658, pooled top-10% 0.775, within-risk-set top-10% 0.995.
    - **Specificity check, remodel negative control** (controls seed 2030; the same 999 surrogates):
      - Events 1,491. Cases 866. Dropped: 515 with no value in the window, 108 missing a Baseline 1 input, 2 demolition-censored.
      - Rows 41,248; 2,918 control rows dropped. Cases by fold: 170, 158, 179, 176, 183.
      - Baseline PR AUC 0.0274. **Change +0.00011, 95% interval −0.00066 to +0.00098, p = 0.341.**
      - **Label: Negative-control gain not detected.**
      - **Share of the foundation change:** −0.19. The foundation change is negative, so this share has no useful reading; it is reported as computed.
      - **Its secondary metrics** (nominal):
        - ROC AUC −0.0014 (p 0.713);
        - pooled top-10% capture +0.0046 (p 0.135);
        - within-risk-set top-10% capture +0.0150 (p 0.022).
        - The last p is below 0.05, on one of four uncorrected metrics of the negative control. §11 labels the negative control by PR AUC only, so it carries no label.
    - **Direct comparison:** the foundation change minus the remodel change, on the same 2,000 resampled blocks, is −0.00069, 95% interval −0.00225 to +0.00049. No difference is claimed.
  - **Test B report** (`run_report.py testb`, finished 09:40:15, exit 0; `real_20261112/report_b.json`, `1f50166eca6fc8cb7627e280177bb968898cc68c955c388f5cf7b26717545f40`; remodel panel `real_20261112/test_b_panel_remodel.csv`, `9ba023a9133b5f02341c5f6914c2e998900ab3cad30ae7598c603f875c797182`):
    - **Rebuild check:** the foundation panel equals `test_b_panel.csv` (rows, cells, quarters, blocks, counts and n; velocity difference 0.0), and β differs by 2.5 × 10⁻¹⁸. Pass.
    - **Foundation, block bootstrap** (2,000 resamples over 192 blocks, no failed fit): log rate ratio per IQR, 95% interval −0.138 to +0.161, i.e. a rate ratio of 0.871–1.175. The Wald interval is 0.867–1.168.
    - **Specificity check, remodel counts** (exposure from the foundation at-risk rule, the user's choice above):
      - **Remodel events:**
        - 1,489 counted, 1,411 inside the 28 quarters;
        - 1,376 in rows used, 35 in rows without a value;
        - 103 counted events lie at houses not in n.
      - **Panel:** the foundation panel's 129,682 rows (asserted). The model keeps 30,182 rows in 1,099 cells, 28 quarters and 152 blocks.
      - **Estimate:** β = +0.0030 per mm/yr (clustered SE 0.0035). **Rate ratio per IQR (27.0 mm/yr) 1.084, 95% CI 0.899–1.308.** Bootstrap interval of the log rate ratio: −0.104 to +0.274.
      - **p = 0.706** (705 exceedances of 999, seed 2035). **Label: Negative-control association not detected.**
    - **Direct comparison:** foundation minus remodel log rate ratio per IQR, on the same 2,000 resampled blocks (no failed fit in either), is −0.075, 95% interval −0.321 to +0.164. No difference is claimed.
  - **Still running:** null (a), after its surrogate file.
  - **MSR (secondary 8): coded, checked, timed, and started** (written 2026-11-12 ~10:00 EET, before the run).
    - **Code:** `production/msr_null.py` (SHA-256 `14302b9c2be8d3dd…`). It follows NYC's `11_models.msr_draws` (non-amplitude-adjusted, seed 2026, 999 draws), with four changes needed at 107,243 pixels:
      - **Threshold:** the longest edge of the minimum spanning tree of the Delaunay edges. On the full set it is verified by connectivity: pairs closer than t(1 + 10⁻⁹) connect all pixels, and pairs closer than t(1 − 10⁻⁹) do not.
      - **Weights:** built in column blocks with NYC's expression.
      - **q:** a Householder basis of the complement of the constant, in place of `null_space`. The same eigenvalues result, and the same eigenvectors up to sign.
      - **Eigendecomposition:** LAPACK `dsyevd` (the routine numpy and cupy use), from numpy's 64-bit-integer OpenBLAS, in place. Draws are computed 16 at a time with the same sign vectors in the same order.
    - **Built-in safeguards:**
      - The run stops before any draw if the threshold check fails.
      - It also stops if an eigen self-check on 200 random basis columns fails: residual of P w b = λ b, orthonormality and orthogonality to the constant, each ≤ 10⁻⁸. Here w is rebuilt in blocks, and P is the projection off the constant.
    - **Check against NYC's dense code** (1,500 random null pixels; `check/msr_check2.json`, `294dae55…`): pass.
      - Identical threshold (5,415 m on this subset) and identical weights.
      - Eigenvalues within 5 × 10⁻¹⁶ (relative).
      - Eigenvectors of the 1,444 separated eigenvalues agree (|cos| ≥ 1 − 3 × 10⁻¹⁵), and the draws' components along them agree within 1.5 × 10⁻¹¹.
      - Missing values are identical.
      - Self-check: residual 5 × 10⁻¹⁶, orthonormality 3 × 10⁻¹⁵.
      - Whole draws differ, by up to 6.4 mm/yr. This comes from the 55 eigenvalues that are not separated: eigenvectors of near-equal eigenvalues are not unique, so no two eigensolvers give the same ones, including NYC's GPU solver.
    - **Timing** (`check/msr_timing.json`, `4b2eb8dc…`; 32 threads beside the null (a) run, load about 95):
      - Eigendecomposition: 22 s at 10,000 pixels, 160 s at 20,000 and 530 s at 30,000 (∝ n^2.95).
      - **Projection to 107,243 pixels:** about 6.7 h for the eigendecomposition and 0.6 h for the draws, about 7.5 h in all. Peak memory 276 GB; surrogate file 38 GB.
    - **User's choice (2026-11-12): "Run MSR now"**, on the server beside null (a). It counted in the 7-day secondary budget, which the user removed shortly afterwards (§14, 2026-11-12).
    - **Job:** `server_scripts_part3/run_msr.sh` (`f301c9005cea397e…`): `msr_null.py make` (32 threads), then `planted_signal.py quantiles` (48 workers), then `run_tests.py testa` (unchanged) with that file into `real_20261112/msr/`.
      - The MSR p is reported as secondary 8 only. The `meets_rule` field of that file is never quoted.
      - The free-permutation p is already 1.000, so the largest p across the §12.8 nulls cannot change.
  - **Null (a) surrogates also made on the server GPU** (secondary 8; written 2026-11-12 09:46 EET, before the GPU run and before any comparison of null (a) files).
    - **User's request (2026-11-12, verbatim):** "use gpu. stop vllm and use the gpu", then "iam talking about the server not this pc ok?". So the other service's inference deployment (sglang-vision) is paused again, as on 2026-11-11.
    - **The CPU run continues** beside it (`make_surrogates_nulla.py`, 64 workers, started 08:55:20). It is the comparison, and the fallback.
    - **Code:**
      - `production/make_surrogates_nulla_gpu.py` (SHA-256 `93971356b8106938…`) is `make_surrogates_nulla.py` with the frozen `LowMemVariogramNull` on CuPy (`scripts/lowmem_null.py`, the class the CPU adapter wraps), one draw after another.
      - Same field, settings (cap 1,000, max lag 16, chunk 8), seed 2027, 999 draws and file format.
      - Output: `work/insar/surrogates_20261112_nulla_gpu/`.
    - **Job:** `server_scripts_part3/run_gpu_nulla.sh` (`c30292f6d255f312…`), with the 2026-11-11 pause and restore steps and three changes:
      - the sync policies and the deployment are saved again just before the pause;
      - no user-space driver workaround is used (driver 580 since the reboot);
      - after the restore, the job records whether the service's pod becomes ready again.
    - **Checks before the pause (09:44):**
      - The cluster node has no mounts of deleted driver files (0), and nvidia-persistenced is running.
      - The service runs 1/1 and holds 21.4 GB. Both ArgoCD apps have their original automated sync policies.
      - **GPU environment on driver 580.178.04** (`check_gpu_small.py` `b714860e…`, unchanged; record `check/gpu_small_check_580.json` `61cdd916…`): GPU class against the CPU engine.
        - Same neighbour counts and missing values; largest difference 1.3 × 10⁻¹⁴; identical as float32.
        - Pass.
    - **Which file is used (fixed now, before the run):**
      - **Agreement test:** two draws agree when all of the following hold:
        - they have the same missing values;
        - every value is identical as float32, **or** differs by at most one float32 rounding step, **or** differs by at most 10⁻¹² mm/yr in absolute value.
        - The share of values that are not identical is reported, and so is the count more than one step apart.
        - The absolute bound is added for this run because of the finding of 2026-11-11 (above): near zero, a float64-level difference spans several float32 steps.
        - The bound is fixed before any null (a) comparison. The conditional null's file choice (the CPU file) is not revisited.
        - Script: `production/check_gpu_cpu_draws_abs.py` (`ddbb9137fbb96a05…`), which is `check_gpu_cpu_draws.py` plus this bound. On synthetic files it passed one-step, near-zero (5 × 10⁻¹⁴) and identical values, and failed a 10⁻³ difference.
      - **Early check:** draws 0–2 are compared as soon as the GPU file holds them. If they do not agree, the GPU run is stopped and the service is restored.
      - **GPU file used:** if all 999 GPU draws complete and every draw held by both files agrees. Then:
        - the CPU run and the waiting step 5 of `run_real.sh` are stopped;
        - the quantiles (`planted_signal.py quantiles`) and the null (a) Test A step (`run_tests.py testa`, unchanged) run on the GPU file with the same commands, into `real_20261112/nulla/`.
      - **CPU file used:** in every other case. `run_real.sh` then continues unchanged.
    - **Pause:**
      - Sync was switched off and the service scaled to 0 at 09:45. At 09:46:35 the GPU was free (24,164 MiB), and the GPU run started.
      - It used 22.3 GB of GPU memory.
    - **Early check** (`check/nulla_gpu_cpu_first3.json`, `796d8c17…`): draws 0–2 at 09:49.
      - Missing values identical.
      - 1 of 17,453,010 values was not identical, one float32 step apart (1.8 × 10⁻¹² mm/yr).
      - Passed.
    - **GPU run:** all 999 draws completed at 12:18:26 EET, taking 2 h 30 min (about 9.0 s per draw).
      - File `surrogates_20261112_nulla_gpu/surrogates_nulla.npy`, SHA-256 `5f2c68991c19bcf03acef48dc1a167e17e0a0f063f793a50addbfeb0f60b040e`.
      - Neighbour count 28 in all 999 draws. Record `check/nulla_gpu_run.json` (`e5471cb9…`).
    - **Restore** (`check/gpu_pause_20261112.log`, `44843f90…`):
      - At 12:18:39–41 the replicas went back to 1 and both sync policies were restored. They are identical to the copies saved before the pause (checked at 12:49).
      - The service's pod was ready again at 12:22:47 and holds 21.4 GB.
      - All 19 ArgoCD applications are Synced with automated sync. `ai-inference` is still Degraded only from its old `cpu-embedding` pod, as before.
    - **Full comparison** (`check/nulla_gpu_cpu_all.json`, `fd7855b5…`; 12:27): the 432 draws the CPU file then held, 2,513,233,440 values.
      - Missing values identical in every draw.
      - 165 values not identical (a share of 6.6 × 10⁻⁸).
      - 6 values more than one float32 step apart (up to 10 steps), all within 1.4 × 10⁻¹⁴ mm/yr, so none beyond the bound.
      - **Passed.**
    - **Result: the GPU file is used**, as the rule says.
      - At about 12:50 the CPU run (at about draw 490) and `run_real.sh`, which was waiting for it, were stopped by process ID. The CPU partial file is kept on the server as a record.
      - `server_scripts_part3/run_nulla_gpu_after.sh` (`383e1766cea9b682…`) started at 12:51:39. It runs `planted_signal.py quantiles` (48 workers) on the GPU file, then `run_tests.py testa` (unchanged) into `real_20261112/nulla/`, and writes to `real_20261112/status`.
  - **Null (a) result: secondary 8** (finished 12:54:03, exit 0).
    - Record: `real_20261112/nulla/test_a.json`, SHA-256 `3aced26fa06cc8c93a81f160240db06ec152eabe6ef292d013bd2a3c45b3522d`.
    - Quantiles: `quantiles_20261112_nulla_gpu/surrogate_quantiles.npy`, `20a5196b495792c6…`.
    - Same cases, rows and observed change as the primary analysis: 1,754 cases, 83,496 rows, change −0.00058.
    - **Null (a) p = 1.000** (999 of 999 draws at or above the observed change). The draws have median −0.00005, 5th percentile −0.00026, 95th percentile +0.00015, and range −0.00046 to +0.00078.
      - *Corrected 2026-11-17: the median was first written as −0.00006. At full precision it is −0.0000546, which rounds to −0.00005. This was found when the result document was checked against this entry. The other values here, and those of the MSR and primary draws, were rechecked and are unchanged.*
    - The file's `meets_rule` field is not quoted, as fixed above. This p is secondary 8 only.
  - **Largest p across the nulls of §12.8** (change in PR AUC; §11 beside item): **1.000.** It is the largest of null (a) 1.000, free permutation 1.000 and within-block permutation 0.995, over the nulls that ran; MSR is still running. No p can exceed 1.000, so MSR cannot change it.
  - **MSR result: secondary 8** (`run_msr.sh`; recorded on 2026-11-15).
    - **Surrogates:** `msr_null.py make` ran from 10:00:10 to 15:33:38 EET on 2026-11-12, 5.6 h in all (32 threads).
      - File `surrogates_20261112_msr/surrogates_msr.npy`, SHA-256 `63b55ce62477378c64f471009e1b1c11e8e06d49a692f5f670d3b120eba5c334`. Record `check/msr_run.json` (`3ee52004…`).
      - **Threshold:** 4,928 m. The connectivity check passed.
      - **Stage times:** eigendecomposition 5.0 h (the projection was 6.7 h); weights, H w H and basis 8 min; draws 23 min.
      - **Peak memory:** 270 GB.
      - **Eigen self-check** (200 random basis columns): residual 8.3 × 10⁻¹⁸, orthonormality 2.7 × 10⁻¹⁴, orthogonality to the constant 1.3 × 10⁻¹⁴. Passed.
    - **Quantiles:** `quantiles_20261112_msr/surrogate_quantiles.npy`, `c4bc298db17866bb…` (15:34:32).
    - **Test A with the MSR file** (`run_tests.py testa`, unchanged; finished 15:35:31, exit 0):
      - Record `real_20261112/msr/test_a.json`, SHA-256 `c3a6abbc19b281eddbb5bbfcf41da261845ba76b84f05547df73cb7c3676f1cc`.
      - Same 1,754 cases, 83,496 rows and observed change (−0.00058) as the primary analysis.
      - **MSR p = 1.000** (999 of 999 draws at or above the observed change). The draws have median −0.00006, 5th percentile −0.00027, 95th percentile +0.00021, and range −0.00051 to +0.00070.
      - Its `meets_rule` field is not quoted. This p is secondary 8 only.
  - **Largest p across the nulls of §12.8, final: 1.000.** All four nulls ran: null (a) 1.000, free permutation 1.000, within-block permutation 0.995 and MSR 1.000.
- **Secondary analyses: surrogate files** (written 2026-11-15, before any secondary outcome is joined).
  - **Files:** each of these uses the Test A null on its own field, 12 files in all:
    - secondary 3: the 12-month and 36-month velocity;
    - secondary 6: amplitude, local relative motion and acceleration;
    - secondary 9: lags 1, 3, 6 and 12;
    - secondary 12: availability;
    - secondary 13: no construction mask;
    - the slip-rule sensitivity of §14 (2026-11-11): the first-run velocity.
  - **Settings:** as the primary file (§10 conditional null, cap 1,000, max lag 16, chunk 8, 999 draws, seed 2027) with only the field changed, then the per-draw quantiles (`planted_signal.py quantiles`, unchanged). Outcome-blind.
  - **Engine:** either engine that §14 allows on the server, the CPU engine (64 workers) or the frozen GPU path ("the frozen GPU path may run there instead").
    - Two queues walk one list in the numbered order, and each file is made by only one of them. `engine.txt` beside each file records which.
    - No GPU/CPU agreement rule is applied, because §14 allows the frozen GPU path on its own.
    - In the full comparisons of 2026-11-11 and 2026-11-12, every value of the two engines was equal, one float32 step apart, or within 2.9 × 10⁻¹⁴ mm/yr.
  - **GPU:** the user's request (2026-11-15, verbatim) was "stop vllm prmentatly and use gpu".
    - The other service's inference deployment (sglang-vision) is stopped with the 2026-11-12 steps, and there is no automatic restore.
    - Pre-checks passed: no deleted driver mounts, the persistence daemon running, and nothing waiting for the GPU.
    - While the service is stopped, ArgoCD auto-sync is off for `root` and `ai-inference`.
    - `gpu_restore.sh` restores both from the saved copies when the user asks.
  - **Scripts** (`production/server_scripts_part3/`):
    - `surr_queue.sh` (`08818d51e198c438…`), `gpu_stop.sh` (`cd4ce9cda1c62022…`) and `gpu_restore.sh` (`5ed24a7cec025c50…`).
    - The first file (the 12-month velocity) started at 11:26 EET on the CPUs with `run_surr_field.sh` (`d51b7c1c274fc0ff…`), with the same commands.
  - **Disk:** the disk is shared with other services, so a file starts only when at least 138 GB would stay free (one file plus a 100 GB floor).
  - **Surrogate files deleted after use.** On 2026-11-15 the user asked "do we need these files ?". I proposed deleting the four unneeded files now and each secondary file after use, and the user replied "ok".
    - **Deleted** at 11:52 EET, after their SHA-256 values were re-checked against those recorded above:
      - the 2026-11-11 GPU record file (`e1f95841ff17d687…`);
      - the null (a) GPU file (`5f2c68991c19bcf0…`);
      - the MSR file (`63b55ce62477378c…`);
      - the partial CPU null (a) file, which was never used.
    - **Kept:** their `.json` and `.run.json` records, the quantile files and the test records.
    - **From now on:** each secondary's surrogate file is deleted once its test has run and its SHA-256 is recorded.
      - The primary file is kept, because secondaries 2, 4, 5, 7, 10, 11, D1 and D2 use it.
      - The amplitude, local relative motion and acceleration files are kept until secondary 7 has run.
    - **Remaking a deleted file:** a CPU file can be remade exactly from its seed and the code. A GPU file can be remade only to within about 10⁻¹⁴.
  - **Fields whose first windows hold no values** (the 36-month velocity and the lags 1, 3, 6 and 12; secondaries 3 and 9).
    - **What happened:** at 11:38 EET the GPU queue's run on the 36-month field stopped at the input check of the conditional null ("Every window needs at least three finite velocities"). Its first 12 windows hold no value, because no 36-month window fits before the first granule. This was the input check, not a GPU fault. The five fields of this kind were held.
    - **Wrapper:** `production/make_surrogates_windows.py` (`eca19fc3c152608a…`).
      - It runs the same engine, settings and seed on the windows that have values. Each draw is written at full shape, with NaN in the empty windows and under the full field's fingerprint, so the Test A code reads the file like any other. Quantiles are NaN in the empty windows.
      - The arithmetic of the windows that have values is unchanged. The frozen generator makes exactly two random calls per draw, a permutation and a normal vector of length = the number of null pixels, so leaving windows out does not change the random stream. The conditional fits are made window by window.
      - Those empty windows hold no study events. Secondary 3 uses events from 2019-08 for the 36-month window, and secondary 9 uses "the events whose window starts on or after the first granule".
    - **Check:** `production/check_surr_windows.py` (`6acf09c8146c5b9d…`) run by `run_check_windows.sh` (`23b23193b1f58b12…`), 11:55–12:06 EET, outcome-blind.
      - Input: the primary field with its first 12 windows set to NaN (`71fa2788…`). The wrapper made 3 draws on the CPU engine, which were compared with draws 0–2 of the primary file and of its quantile file.
      - **Passed.** The 12 empty windows are NaN in every draw and in the quantiles. Draws 0 and 2 chose the same neighbour count as the primary file (28), and in windows 12–87 their values and quantiles are identical to the primary file's (0 values differ).
      - Draw 1 chose 18 neighbours instead of 28, so its values differ. This is expected: the neighbour count is chosen by matching the variogram of the windows that are used, and that set changed.
      - The 76 explained-variance values of the conditional fits equal the primary run's values for windows 12–87.
  - **Order in which the files are made.** A file is about 38 GB. With the 100 GB floor, only about six more files fit before secondaries start deleting theirs, so the files are made in the order the secondaries use them. Otherwise the files of secondaries 12 and 13 could fill the disk while secondary 3 waits.
    - At 12:11 EET the availability, no-mask and first-run fields were held as well. At 12:39 EET the local relative motion and acceleration fields were held too, so that the 36-month file is made before them. The first queue (`surr_queue.sh`) therefore ends after the amplitude file.
    - `production/server_scripts_part3/surr_queue2.sh` makes the held files in the order of use, on whichever engine is free:
      - the 36-month velocity (wrapper), local relative motion and acceleration;
      - the lags 1, 3, 6 and 12 (wrapper);
      - availability, no construction mask and the first-run velocity.
      - Fields without empty windows use the unchanged `make_surrogates.py`.
    - Settings, quantiles, SHA-256, the disk rule and the engine rule are those of the first queue. Its CPU and GPU instances wait until the first queue has ended.
    - The first version (`6412541dfc0233f1…`, started 12:11 EET) was stopped at 12:39 EET while still waiting, before it had claimed any field. It was restarted as `5bfd37ebe831907f…` with the order above.
  - **Test B variant surrogates.** `production/server_scripts_part3/run_testb_variants.sh` (`b4bd7b1e06fd0142…`) started at 11:58 EET. It runs the unchanged `make_testb_surrogates.py` (`37daf33fb7463f27…`) with seed 2034, as the primary Test B null, 999 draws and 16 workers. Outcome-blind.
    - Fields: lags 1, 3, 6 and 12 (secondary 15); the 24-month velocity (secondary 16); amplitude, local relative motion and acceleration (secondary 17); the first-run velocity (slip-rule sensitivity of Test B).
    - Each file is small (cells × quarters), so it is kept until the secondaries are reported.
  - **Inputs of secondaries 5 and 10 sent to the server.** `production/export_secondary_server.py` (`75d5dd508e92beb8…`) writes only property IDs and dates; no permit number, description or address leaves the private area.
    - `other_bp_dates.parquet` (`0f7f8f013d85796f…`): 225,371 non-foundation building permit dates, for Baseline 2's "count of non-foundation BPs in the 5 years before t_e".
    - `foundation_first_episodes_issue.parquet` (`e53f6ee48239c328…`) and `foundation_events_issue.parquet` (`500ad39c69c335dc…`): the same 10,240 first episodes and 2,846 events as §4, re-dated by the issue date of the episode's first permit (secondary 10). §4 is not re-derived.
      - Every issue date is present, and every application date equals the recorded event date.
      - Episodes: 4,906 issued on the application date, 1 issued before it, 714 issued after 2025-11.
      - Events: 975 issued on the application date, 18 issued after 2025-11.
    - `export.json` (`8f282e6d1808268d…`). The server copies have the same SHA-256.
  - **Secondaries not run under option A:** 14 is removed (§4), and P0–P1 apply to option C only (§12).
- **Secondary analyses: how each is computed** (written 2026-11-15, before any secondary outcome is joined). Where §12 leaves a detail open, the choice below is the authors'. Nothing here changes §4–§11 or the primary results.
  - **Code** (`production/`; hashes in `SHA256SUMS_part5`, recorded before the first real secondary run):
    - `secondary_a.py`: the house-level Test A secondaries (2–7, 9–13, D1, D2, slip-rule sensitivity);
    - `secondary_b.py`: the Test B secondaries (15–19, slip-rule sensitivity);
    - `secondary_cells_null.py` and `secondary_cells.py`: secondary 1, the cell-level null and the analysis;
    - `make_testb_monthly_surrogates.py`: the Test B null of secondary 19;
    - `make_surrogates_windows.py`: the null files of the fields with empty first windows (3, 9).
    - They import `run_tests.py`, `run_report.py`, `testa_core.py`, `test_b.py` and `nyc_lib.py` unchanged. Each secondary changes only the step named below.
  - **Checks before any secondary outcome:**
    - **Anchor, Test A:** the generic path of `secondary_a.py`, run with the primary settings, must rebuild the primary analysis exactly: cases, rows, drops, baseline, observed change and null statistics. Its block bootstrap must equal `run_report.py`'s on the same rows. This is checked in the decoy world against the decoy record, and in the real world against `report_a.json`, which is already reported.
    - **Anchor, Test B:** the field-swap path of `secondary_b.py`, run with the primary field, must rebuild the primary panel, coefficient and null statistics.
    - **Decoy smoke:** each secondary runs in the decoy world with 3 draws before its real run, with its own files once they exist. These are code checks, labelled DECOY, not results.
  - **Common to the Test A secondaries** unless the item says otherwise:
    - **Same as the primary:** the world, the case rule (§8A), 50 controls drawn with seed 2029, Baseline 1 + x/y, logistic regression, the checkpoint-1 fold map, and the §7 standardisation per window.
    - **Validity:** a row needs a value of the secondary's own field in the case's window, so each field keeps its own missing pattern.
    - **Null:** the conditional null (§10 settings, seed 2027) made on the secondary's own field, 999 draws. Tree models use draws 0–499, because §12 says "500 for tree models".
    - **Reported for each:** the change in PR AUC, ROC AUC, top-10% capture and top-10% capture within the risk set, each with p from the same null draws.
    - **Bootstrap:** a refit block bootstrap over the analysis's own 2 km blocks (`run_report.py` arithmetic, seeds 0 to n − 1), with 2,000 resamples for logistic regression and 500 for tree models, as NYC. It gives 95% percentile intervals for the first three changes.
  - **Item by item:**
    1. **NYC design.**
       - **Cells:** the 5,645 cells of 250 m that hold an eligible parcel point (the Test B cells). Value: the mean of the valid pixels whose centre lies in the cell, for the 24-month window of each month (i08, corrected run). A cell with no valid pixel has no value.
       - **Risk sets:** the frozen `nyc_lib.risk_sets` with NYC's rule "first". Each event goes to the cell of its house. A case is the first event of its cell. The controls are every cell with a value and a baseline whose first event is later than the case date, or that has none. As in NYC, controls are not sampled.
       - **Cell baseline:** means over the cell's houses with complete inputs of year built (giving the mean age at the risk set's date) and of the seven static Baseline 1 features, plus the cell centre in km. A cell with no such house has no baseline (5,541 of 5,645 cells have one).
       - **Folds:** each cell takes the fold of its 2 km block in the house fold map.
       - **Null:** a cell-level conditional null with the §10 settings at 250 m, made on the cells with a baseline. Its covariates are their cell means (age at 2018-08-01), with seed 2027 and 999 draws. The observed value is standardised over all cells with a value; a draw is standardised over the null cells with a value.
       - Logistic regression; 2,000 block resamples.
    2. **Local controls:** the pool is the houses whose parcel point lies within 1 km of the case's (distance ≤ 1 km), that have a value and are at risk at the case date, with the case excluded.
       - min(50, pool size) controls are drawn without replacement with seed 2029, in case order.
       - A case with an empty pool is left out. Sets with fewer than 50 controls are kept. Both are counted.
    3. **Windows:**
       - **12-month:** the same events as the primary. A case needs a value in the 12-month window, and the case count is reported next to the primary's 1,754.
       - **36-month:** the field has no value before 2019-08, so events before then drop as "no value in the window" (§12.3: "events from 2019-08").
    4. **Random forest:** NYC's settings (500 trees, minimum leaf 5, square-root features, balanced subsample, random_state 0).
    5. **Baseline variants:**
       - **Baseline 2:** Baseline 1, plus the house's count of non-foundation building permits dated from 5 calendar years before the row date up to the day before it (the raw count), plus the canopy share (2018 layer, §14).
         - Rows missing a Baseline 2 input are left out; if the case misses one, its whole risk set goes. No eligible house misses canopy.
         - Cases dated before 2018-11-04, whose canopy postdates them, are counted.
       - **Baseline 1 without income:** the same rows as the primary, with log income removed from both compared models.
       - Both use the primary null file. That null conditions on the §10 covariates (which include income) and not on Baseline 2's additions, and is read with that note.
    6. **Other indicators:** amplitude, local relative motion and acceleration, each in place of velocity, with its own field, validity and null file.
    7. **Boosted trees:**
       - **Model:** `HistGradientBoostingClassifier` with defaults and random_state 0, fitted out of fold with `nyc_lib.oof`'s fold rule.
       - **Comparison:** Baseline 1 + x/y against Baseline 1 + x/y + the four standardised indicators (velocity, amplitude, local relative motion, acceleration). A row needs a value of all four.
       - **Null:** draw d uses draw d of each indicator's own null file. All four files use seed 2027 on the same null pixels, so a draw shares the permutation and noise stream across indicators, while each file is its own field's surrogate.
       - Draws 0–499; 500 resamples.
    9. **Lag profile:** each lag field with its own file (from the windows wrapper). Events whose window precedes the field's first window drop as "no value in the window" (§12.9). The primary is lag 0 in the table.
    10. **Issue date:** each first matched episode and each event is re-dated by the issue date of the episode's first permit (export of 2026-11-15). §4 is not re-derived.
        - The shared at-risk rule uses the issue-dated episodes. Demolition dates are unchanged.
        - The 18 events issued after 2025-11 fall outside the study months; they are dropped and counted.
        - Primary field and null file, because the field does not depend on the dating.
    11. **Fold seeds:** `testa_core.fold_of_houses` with seeds 0–9 on "the house holds an event"; primary file. A table of change and p per seed, without a bootstrap (NYC's secondary 9).
    12. **Availability only:** the valid-pixel count within 100 m, standardised as §7, with its own null file.
        - The count has a value at every house in every window, so its own validity would admit every row.
        - The rows therefore use the primary velocity's validity: the same cases and controls as the primary, so only the indicator changes.
    13. **No construction mask:** the unmasked velocity with its own validity, which gives more rows, and its own null file.
    15. **Test B with other fields:** lags 1, 3, 6 and 12 (15), the 24-month window (16), and amplitude, local relative motion and acceleration (17), each in place of v.
        - The primary panel, fit and null calls run unchanged, on a cells file whose v is the variant field. That file is written beside the result, with its SHA-256 recorded.
        - **Null:** the Test B null of that field (seed 2034, 999 draws). The file is checked by its field name and by the SHA-256 of its null field.
    18. **Negative binomial:**
        - **Model:** NB2 (statsmodels `NegativeBinomial`, maximum likelihood), with log n as offset and quarter fixed effects. In place of cell fixed effects it uses the cell means, over the cell's eligible houses with complete inputs, of age at 2018-08-01, log living area, log lot area, soil linear extensibility, slope, elevation, log income, slab-foundation share and x/y.
        - **Slab share:** §12.18's list in brackets omits it. It is a Baseline 1 feature (§9) and one of the §10 null covariates, so it is included.
        - **Scaling:** the features are centred and scaled over the rows used; velocity stays in mm/yr.
        - **Rows:** the primary panel's rows whose cell has such a house.
        - **Errors:** clustered by 2 km block (statsmodels' default small-sample correction). The rate ratio per IQR comes with a normal 95% interval.
        - **Fitting:** Newton (100 iterations) started from the Poisson fit of the same design and offset, with α = 0.1. A fit is accepted only at a finite optimum where every score component is at most 10⁻⁶. Otherwise Newton is restarted from the BFGS (2,000) solution. A fit that reaches the optimum by neither route stops the run.
          - **Why:** in the decoy smoke, statsmodels' default start made Newton diverge to NaN while still reporting convergence. BFGS alone stopped short of the optimum, with a largest score component of 1.09 and β −0.003791 against −0.003800. Newton from the Poisson start reached a score of 10⁻¹⁰ in 4 iterations. Only the decoy panel was used.
        - **Null:** |β| with the primary Test B surrogates (seed 2034).
    19. **Monthly counts:** rows are cell × calendar month over the 88 study months.
        - y counts the month's events, n is the houses at risk on the day before the month starts, and v is the cell's 12-month velocity before the month. Rows used have a value and n > 0.
        - Fitted by the frozen `fit_panel` with the month in place of the quarter (cell and month fixed effects).
        - **Null:** the same engine and seed (2034) as the Test B null, on the 88 monthly fields (`make_testb_monthly_surrogates.py`).
    - **D1. Demolition as the outcome:**
      - **Cases:** the first total demolitions of §5 (checkpoint-1 censoring table) dated in the study months, in date then property-ID order.
      - **Dropped:** a case missing a Baseline 1 input, with a matched foundation episode on or before the demolition date, or with no value in the window.
      - **Controls:** 50 at risk at the demolition date under the shared rule, drawn with seed 2029. The checkpoint-1 fold map is used.
    - **D2. Composite outcome:** each house's case date is the earlier of its foundation event and its demolition in the study months.
      - **Dropped:** a case missing an input, with a matched foundation episode before that date that is not the event itself, or with no value. Controls as D1.
    - **Decoy worlds of D1 and D2** (code checks only): the demolition dates are moved to `default_rng(98)` houses and real demolitions are ignored. The foundation episodes are those of the seed-99 decoy world, so no real outcome of either kind is read.
    - **Slip-rule sensitivity (§14):** Test A on the first-run velocity with its own null file, and Test B on the first-run cell velocity with its own Test B null.
  - **Order:** the real runs go in numbered order (1–19, D1–D2, slip-rule sensitivity, then 20), each started after its decoy smoke passes and its null file exists. Start and end times are reported. Surrogate files are deleted after use, as recorded above.
  - **Code fixed before the first real secondary run** (2026-11-15, 14:22 EET; `run_secondaries.sh` re-fixed 14:23 EET; manifest re-hashed 14:34 EET; all times from the server clock, which agrees with the project PC's): `production/SHA256SUMS_part5` (`a5d9185e63fdff9a…`). The server copies were compared with these and are identical. `export_secondary_server.py` runs on the project PC only.
    - **Hashes:**
      - `secondary_a.py` `5a655e57abf9120e…`;
      - `secondary_b.py` `5f2f5d287734d39f…`;
      - `secondary_cells.py` `19d266a26e2eb6ed…`;
      - `secondary_cells_null.py` `93a9b43905b9c191…`;
      - `make_testb_monthly_surrogates.py` `8b8b0f23a14e89b3…`;
      - `run_secondaries.sh` `8803efe27629ac8c…` (14:23 fix: it waits for each file's quantile meta, which every maker writes last, and re-checks a file's hash against its own meta before deleting it; the first version waited for a hash file that the CPU maker does not write);
      - `smoke_secondary_a.sh` `7f3b19e3717dff0f…`.
    - **Unchanged reused code:** `run_tests.py` `020c67e0…`, `run_report.py` `ea0315b6…`, `testa_core.py` `f4d71575…`, `make_surrogates.py` `e0f30649…`, `make_testb_surrogates.py` `37daf33f…` and `parallel_draws.py` `df48a54d…` are as recorded before.
  - **Checks passed** (outcome-blind, or against outcomes already reported):
    - **Anchor, Test A, decoy:** 8 draws. Cases, rows, drops, baseline, observed and null statistics all differ from the decoy record by 0.0. The bootstrap equals `run_report.py`'s.
    - **Anchor, Test A, real:** all 999 draws against `report_a.json`. All four metrics' observed changes and null statistics differ by 0.0. Twenty bootstrap resamples equal `run_report.py`'s.
    - **Anchor, Test B, decoy:** the panel is identical, and β and the null statistics are within 2 × 10⁻¹⁷.
    - **Decoy smokes:** 3 draws each, with stand-in files where a secondary's own file did not exist yet. All passed: 2, 3 (36-month path), 4, 5 (both), 7, 10, 11, 12, D1, D2, 15 (lag 1) and 18.
      - Decoy figures: D1 has 3,797 demolitions, 381 of them outside the study months. Issue dating moves 18 events past 2025-11. Baseline 2 leaves out no rows.
    - **Independent review:** a fresh agent read the code against §12 and this entry. It found no defect affecting a real result.
      - One decoy-only case was fixed: two decoy demolitions on one house and date are now one case.
      - D2's case counts were moved from the drop list to the notes.
    - **Secondary 1 null:** the cell-level null is done (999 draws, 14:16 EET). Surrogates `11dbc2a2886a86be…`, quantiles `6ec911d3d65523bf…`; 5,541 null cells.
    - **Item 20 (deep model):** its runner is not written yet. It will call the frozen `freeze/scripts/deep_model.py` unchanged, and it will be written, smoke-tested on the decoy and hashed here before item 20's real run.
    - **Secondary 19 null:** the monthly Test B null is done (13:59 EET): `1158a35c6b832f11…`, 4,990 cells, every one of the 88 months with values.
    - **More decoy smokes (finished 14:24 and 14:33 EET, on the fixed code):** 19 (monthly; 26 s for 3 draws; 407,624 rows, 156,296 used by the fit) and 1 (NYC design; 579 s at 3 workers; peak memory 6.0 GB) passed on their own null files.
    - **Anchor, Test B, real** (finished 14:24 EET): 20 draws against the reported Test B. β differs by 2.5 × 10⁻¹⁸ and the null statistics by at most 2.3 × 10⁻¹⁷.
    - **GPU path of the window wrapper:** the 36-month file is being made on the GPU through `make_surrogates_windows.py` (started 14:29 EET); its quantile file is checked by the same rule as the CPU files before use.
  - **Secondary 18, full decoy null** (finished 15:43 EET; `work/secondary/decoy_full/18_negative_binomial`): all 999 draws fitted, every one by Newton from the Poisson start, none from the BFGS fallback. It took 64 minutes on 12 workers. This checks that the real null cannot stop on a fit (decoy only; its numbers are not a result).
  - **Real runs launched** 2026-11-15 14:38:49 EET on the server (`run_secondaries.sh 40`), after every check above. Start and end times of each item are in `work/secondary/status_real`.
- **2026-11-15. Item 20 (deep model): how it is run** (authors' choices, recorded before any item 20 result; Claude). The frozen `freeze/scripts/deep_model.py` is called unchanged: `oof_scores` for both networks and `temporal_null_test` for the registered null. New code: `production/deep_field.py` (the field), `production/secondary_deep.py` (the runner), `production/check_deep_field.py` (the check below) and `server_scripts_part3/run_deep.sh` (the launcher).
  - **Rows:** the primary Test A rows by `run_tests.py`'s own path: the same cases, risk sets (seed 2029), dropped rows, design matrix (Baseline 1 + x/y, `testa_core.design`), checkpoint fold map and 2 km blocks. Cases, rows, drops and cases per fold are asserted equal to the primary record of the same world.
  - **Acquisition-date field** (`deep_field.py`, from i08's `house_series.npz`; outcome-blind):
    - One chain from the first reference date, as opera-utils' `rebase_timeseries`: a product's displacement is added to the chained value at its reference date. Rows are the 254 secondary dates; the first reference date, all zeros, is not a row.
    - **Broken links:** 3,696 of the 114,058 house pixels are invalid at one or more of the 16 products that link one reference date to the next. `rebase_timeseries` would leave them missing on every later date. Here the pixel's last valid chained value is carried across the link instead (0 if none).
      - Within any §7 window that has a value, §7 requires the pixel to be valid at every link in that window's chain. So a carried value only shifts the window's series by a constant, which the model's first-valid referencing removes; real rows are unchanged.
      - It keeps each date's field defined for the registered null, whose surrogates mix pixels.
    - **Validity** of a date at a pixel: the product's valid flag (recommended and water masks) and its connected-component flag (§7 step 3).
    - **Pixel set:** all 114,058 unique pixels of the eligible houses, the frozen README's "all unique Test A eligible parcel pixels", in `testa_core.Geometry` order (asserted).
  - **Check of the field** (`check_deep_field.py`, outcome-blind; `work/secondary/deep/check_deep_field.json`): the §7 trend model was refitted on the field's valid acquisitions of each 24-month window, for every pixel and window where the Test A field has a value. That is 6,212,506 pixel-windows, including 125,086 of the 3,696 carried pixels. The largest difference from the Test A velocity is 5.3 × 10⁻⁶ mm/yr (float32 rounding), and none is unfitted. The chain, validity, dates and pixel order therefore match §7 for every value Test A uses.
  - **Series:** the frozen `series_from_fields` on the §7 24-month window of the case's month, shared by every row of a risk set. No further row or step mask is used: the construction and slip rules are window-level, and every row already passes them. The runner asserts:
    - every row's pixel has a Test A value in its window;
    - every in-window acquisition passes the connected-component rule there, so the step masks do not depend on it;
    - every row has at least one unmasked step.
  - **Null:** `temporal_null_test` with its default generator (`LowMemVariogramNull` on the GPU, seed 2037, 99 draws), in the server's GPU environment. Its observed scores are asserted equal to a separate `oof_scores` call.
  - **Bootstrap** (frozen README item 9, "the existing production refit block bootstrap"): as `run_report.joint_bootstrap`, 2,000 resamples.
    - The universe is the 2 km blocks holding rows, and resample s draws them with `default_rng(s)`.
    - Both networks are refitted out of fold by `oof_scores` on the resampled rows.
    - A resample has no value when `oof_scores` rejects it because a fold has no rows or an inner split lacks a class, as `run_report`'s single-class resamples. Any other error fails the run.
    - Workers are forked before the first torch operation, and they run the resamples while the parent runs the null (the frozen null loop is serial). Resamples 0 and 1 are recomputed in the parent and must be identical.
    - Reported: the change in PR AUC with its 95% interval; ROC AUC and top-10% capture alongside, as the other secondaries.
  - **Memory rule (§12 item 20), fixed now:** the default is chunk 8. If the GPU smoke or the real run fails for GPU memory, the same class and seed 2037 are used with a smaller chunk, passed in through `surrogate_fields`. Before use it is checked equal to chunk 8 on a synthetic field and logged in §14. If that also fails, the null is reported as not run.
  - **Order:** `run_deep.sh` starts only after `run_secondaries.sh` logs its end. It first runs a decoy smoke on the GPU with the registered generator (2 draws over all 254 dates, 2 resamples; a code and memory check), then the real run.
  - **Code fixed** (2026-11-15, 15:38 EET): `production/SHA256SUMS_part6` (`e737fb034130ff4b…`): `deep_field.py` `3ca903db1f94cff5…`, `check_deep_field.py` `67d0990b17be74a0…`, `secondary_deep.py` `1e07f3f5e65d3b9d…`, `run_deep.sh` `d157e23aea4cdf5f…`. The server copies are identical, and so are those of `SHA256SUMS_part5`.
  - **Decoy smoke** (CPU, code-check null of 2 pixel-shuffled draws, 2 resamples, 2 workers; `work/secondary/deep/smoke_decoy`): passed.
    - The rows equal the primary decoy record: 1,568 cases and 74,829 rows.
    - Every assertion above held.
    - Run twice: first with the bootstrap after the null, then beside it. The observed scores, null statistics and both resamples are identical between the two runs. The second took 14.7 minutes; the observed fit takes 164 s.
    - **Projected real run** (about 1.85 times the decoy's rows): about 10 hours, set by the serial null of 99 draws. The 2,000 resamples on 32 workers finish within that time.
  - **Launched** 2026-11-15 15:31 EET: `run_deep.sh 32` waits for the end of `run_secondaries.sh`.
    - **Launcher fault, stopped at once:** the first launcher's wait (`7d4745d5…`) matched its own log line, which contained "run_secondaries end". At 15:36 it started its decoy GPU smoke out of order.
      - Claude stopped the launcher and the smoke at 15:38, while the smoke was still fitting the decoy networks on the CPU. No GPU work, no real run and no real outcome had been read.
      - The wait now accepts only `run_secondaries.sh`'s own last line, matched in full (`d157e23a…`), and the launcher's own line no longer contains it. Relaunched at 15:38 EET.
- **2026-11-15. Secondary results, real runs** (§12: reported, no decision attached; Claude). Each p is nominal and uncorrected, on one of four metrics. Copies are on the PC in `secondary_real/`, with sha256 equal to the server's; each item's start and end times are in `secondary_real/status_real`.
  - **1. NYC design** (real run 14:50:53–18:08:08 EET, 40 workers; `secondary_real/1_nyc_design/result.json`, `636849b41fce7c0a…`):
    - **Events and rows:**
      - 2,846 events gave 1,477 cases. Dropped: 1,326 with an earlier event in the cell, 36 without a window value, 5 missing a baseline input, and 2 sharing a cell and date with another event.
      - 6,925,554 rows, with 3,989 to 5,463 controls per set (median 4,663), over 5,529 cells and 210 blocks.
      - Cases by fold: 270, 332, 297, 295, 283.
    - **Baseline PR AUC 0.000475. Change in PR AUC −0.0000032, 95% interval −0.00206 to +0.00004, p = 0.847** (999 draws).
    - **Other metrics:**
      - ROC AUC −0.00084 (interval −0.00291 to +0.00013, p 0.637);
      - pooled top-10% capture −0.00068 (interval −0.0094 to +0.0068, p 0.265);
      - top-10% capture within the risk set +0.0027 (p 0.009; not bootstrapped, as fixed). This change is 4 of the 1,477 cases. The null median is 0.0. The p is nominal, on one of four uncorrected metrics.
    - **Bootstrap:** 2,000 resamples over the 210 blocks, all with a value. The null took 54 minutes and the bootstrap 2.3 hours.
  - **2. Local controls** (real run 18:09:12–18:12:13 EET, 40 workers; `secondary_real/2_local_controls/result.json`, `9cadc9e37ea4fc72…`):
    - **Cases and rows:**
      - 1,754 cases, as the primary. Dropped: 961 with no value in the window, 127 missing a Baseline 1 input, and 4 demolition-censored.
      - 86,518 rows, after 2,918 control rows were dropped for missing inputs. Cases by fold: 319, 349, 346, 365, 375; 169 blocks.
      - The 1 km pools held 32 to 2,092 houses (median 690). No case had an empty pool, and one set had fewer than 50 controls.
    - **Baseline PR AUC 0.0262. Change in PR AUC +0.00012, 95% interval −0.00034 to +0.00061, p = 0.008** (the primary's 999 draws; null median −0.000015).
    - **Other metrics:**
      - ROC AUC +0.0014 (interval −0.0047 to +0.0062, p 0.001);
      - pooled top-10% capture +0.0040 (interval −0.0118 to +0.0107, p 0.160);
      - top-10% capture within the risk set 0.0 (p 0.614).
    - **Reading:**
      - The PR AUC and ROC AUC p's are below 0.05, while their block-bootstrap intervals include zero.
      - The null asks whether a field with the same spatial structure gives as large a change; the interval measures how much the change varies over resampled blocks.
      - Both are reported as computed. The p's are nominal, on uncorrected metrics of a secondary, with no decision attached (§12).
    - **Bootstrap:** 2,000 resamples over the 169 blocks, all with a value. The null took 35 seconds (the primary's stored draws) and the bootstrap 85 seconds.
  - **3. 12-month window** (real run 19:08:07–19:11:21 EET, 40 workers; its own 999 draws, CPU, finished 19:03:57; `secondary_real/3_window_12/result.json`, `959e4dd0b291c80a…`):
    - **Cases and rows:**
      - 1,986 cases from the same 2,846 events. Dropped: 729 with no value in the window, 127 missing a Baseline 1 input, and 4 demolition-censored.
      - 94,612 rows, after 6,674 control rows were dropped for missing inputs. Cases by fold: 382, 396, 391, 406, 411; 199 blocks.
    - **Baseline PR AUC 0.0443. Change in PR AUC −0.00038, 95% interval −0.00107 to +0.00016, p = 1.000** (null median −0.000066).
    - **Other metrics:**
      - ROC AUC −0.00070 (interval −0.0020 to +0.00056, p 0.780);
      - pooled top-10% capture −0.0025 (interval −0.0093 to +0.0059, p 0.496);
      - top-10% capture within the risk set −0.0005 (p 0.813).
    - **Bootstrap:** 2,000 resamples over the 199 blocks, all with a value; 110 seconds.
    - The 12-month surrogate file was then deleted at 19:14:44 after its hash was re-checked (`564fd776f4c8bb54…`).
  - **3. 36-month window** (real run 19:15:32–19:17:56 EET, 40 workers; its own 999 draws, GPU, finished 16:52:14; `secondary_real/3_window_36/result.json`, `820cf3a6081d5d46…`):
    - **Cases and rows:**
      - 1,365 cases, events from 2019-08 (none in 2018). Dropped: 1,350 with no value in the window (including every event before the first 36-month window), 127 missing a Baseline 1 input, and 4 demolition-censored.
      - 64,957 rows, after 4,658 control rows were dropped for missing inputs. Cases by fold: 236, 265, 283, 269, 312; 197 blocks.
    - **Baseline PR AUC 0.0476. Change in PR AUC −0.00110, 95% interval −0.00307 to +0.00112, p = 0.850** (null median −0.00084).
    - **Other metrics:**
      - ROC AUC −0.00064 (interval −0.0087 to +0.0056, p 0.004);
      - pooled top-10% capture −0.0081 (interval −0.0334 to +0.0128, p 0.316);
      - top-10% capture within the risk set −0.0037 (p 0.599).
    - **Reading of the ROC p:** the change is negative. Its p is small because the null's draws lowered ROC AUC further (median −0.0019). The p is nominal, on one of four uncorrected metrics, with no decision attached.
    - **Bootstrap:** 2,000 resamples over the 197 blocks, all with a value; 70 seconds.
    - The 36-month surrogate file was then deleted at 19:21:19 after its hash was re-checked (`49ab8ccba0cc0f31…`).
  - **4. Random forest** (real run 2026-11-15 19:56:02 to 2026-11-16 00:30:28 EET, 40 workers; the primary's draws 0–499; `secondary_real/4_random_forest/result.json`, `08019528964b1b09…`):
    - **Cases and rows:** the primary's: 1,754 cases and 83,496 rows, with 5,958 control rows dropped for missing inputs. Cases by fold: 319, 349, 346, 365, 375; 200 blocks.
    - **Baseline PR AUC 0.0549. Change in PR AUC +0.00105, 95% interval −0.00279 to +0.00320, p = 0.056** (500 draws; null median −0.00053).
    - **Other metrics:**
      - ROC AUC +0.0041 (interval −0.0041 to +0.0128, p 0.060);
      - pooled top-10% capture +0.0103 (interval −0.0196 to +0.0237, p 0.038);
      - top-10% capture within the risk set +0.0108 (p 0.146).
    - **Reading:** with 500 draws, the smallest possible p is 0.002. The PR AUC p is above 0.05; the pooled top-10% p is below it. Each bootstrap interval includes zero. All p's are nominal, on uncorrected metrics, with no decision attached.
    - **Run time:** null 1.7 hours, bootstrap (500 resamples over the 200 blocks, all with a value) 2.7 hours.
  - **5. Baseline 2** (real run 2026-11-16 00:31:27–00:34:30 EET, 40 workers; the primary's 999 draws; `secondary_real/5_baseline_2/result.json`, `f23402bd775d04f7…`):
    - **Cases and rows:** the primary's: 1,754 cases and 83,496 rows, 200 blocks. No row misses a Baseline 2 input, so no risk set or control row was left out.
    - 75 cases are dated before 2018-11-04, so their canopy value postdates them (§14).
    - Mean count of other building permits in the 5 years before the row date: 0.089 on case rows, 0.093 on control rows.
    - **Baseline PR AUC 0.0456. Change in PR AUC −0.00050, 95% interval −0.00168 to +0.00034, p = 0.896** (null median −0.00036).
    - **Other metrics:**
      - ROC AUC −0.0014 (interval −0.0039 to +0.0018, p 0.271);
      - pooled top-10% capture −0.0034 (interval −0.0220 to +0.0072, p 0.839);
      - top-10% capture within the risk set −0.0086 (p 0.842).
    - The null conditions on the §10 covariates and not on Baseline 2's additions (§15, as fixed).
    - **Bootstrap:** 2,000 resamples over the 200 blocks, all with a value; 91 seconds.
  - **5. Baseline 1 without income** (real run 2026-11-16 00:35:28–00:38:18 EET, 40 workers; the primary's 999 draws; `secondary_real/5_baseline_1_no_income/result.json`, `24bd20d2274a7bc5…`):
    - **Cases and rows:** the primary's (1,754 cases, 83,496 rows, 200 blocks).
    - **Baseline PR AUC 0.0459. Change in PR AUC −0.00059, 95% interval −0.00177 to +0.00030, p = 0.899** (null median −0.00044).
    - **Other metrics:**
      - ROC AUC −0.0019 (interval −0.0043 to +0.0018, p 0.470);
      - pooled top-10% capture −0.0074 (interval −0.0222 to +0.0074, p 0.866);
      - top-10% capture within the risk set −0.0137 (p 0.981).
    - **Bootstrap:** 2,000 resamples over the 200 blocks, all with a value; 82 seconds.
  - **6. Seasonal amplitude** (real run 2026-11-16 00:39:07–00:42:02 EET, 40 workers; its own 999 draws, GPU; `secondary_real/6_amplitude/result.json`, `f4ecd4820965f1ca…`):
    - **Cases and rows:** as the primary (1,754 cases, 83,496 rows, 200 blocks).
    - **Baseline PR AUC 0.0460. Change in PR AUC −0.00026, 95% interval −0.00182 to +0.00060, p = 0.879** (null median −0.00016).
    - **Other metrics:**
      - ROC AUC +0.0013 (interval −0.0010 to +0.0052, p 0.013);
      - pooled top-10% capture +0.0017 (interval −0.0123 to +0.0130, p 0.526);
      - top-10% capture within the risk set −0.0029 (p 0.864).
    - The ROC p is below 0.05 while its interval includes zero. It is nominal, on one of four uncorrected metrics, with no decision attached.
    - **Bootstrap:** 2,000 resamples over the 200 blocks, all with a value; 94 seconds.
  - **6. Local relative motion** (real run 00:42:53–00:45:57 EET, 40 workers; its own 999 draws, GPU; `secondary_real/6_local_relative_motion/result.json`, `5bc30b49f0b4659f…`):
    - **Cases and rows:** 1,754 cases, as the primary. 83,482 rows: 5,972 control rows were left out, 14 more than with velocity, because this field keeps its own missing pattern. 200 blocks.
    - **Baseline PR AUC 0.0460. Change in PR AUC −0.00003, 95% interval −0.00103 to +0.00063, p = 0.217** (null median −0.00013).
    - **Other metrics:**
      - ROC AUC +0.00057 (interval −0.0022 to +0.0029, p 0.008);
      - pooled top-10% capture +0.0057 (interval −0.0135 to +0.0138, p 0.054);
      - top-10% capture within the risk set −0.0006 (p 0.299).
    - The ROC p is below 0.05 while its interval includes zero. It is nominal, on one of four uncorrected metrics, with no decision attached.
    - **Bootstrap:** 2,000 resamples over the 200 blocks, all with a value; 102 seconds.
  - **6. Acceleration** (real run 2026-11-16 02:16:45–02:19:52 EET, 40 workers; its own 999 draws, CPU, finished 02:15:41; `secondary_real/6_acceleration/result.json`, `dc766fbb920dc687…`):
    - **Cases and rows:** this field keeps its own missing pattern.
      - 1,755 cases, one more than the primary: 960 have no value in the window, 127 miss a Baseline 1 input, and 4 are demolition-censored.
      - 83,556 rows, after 5,949 control rows were left out. Cases by fold: 320, 349, 346, 365, 375; 200 blocks.
    - **Baseline PR AUC 0.0462. Change in PR AUC −0.00010, 95% interval −0.00087 to +0.00021, p = 0.666** (null median −0.000057).
    - **Other metrics:**
      - ROC AUC −0.00019 (interval −0.0012 to +0.00057, p 0.727);
      - pooled top-10% capture +0.0068 (interval −0.0073 to +0.0074, p 0.146);
      - top-10% capture within the risk set +0.0017 (p 0.725).
    - **Bootstrap:** 2,000 resamples over the 200 blocks, all with a value; 101 seconds.
  - **7. Boosted trees, all four indicators** (real run 2026-11-16 02:23:09–02:29:56 EET, 40 workers; draws 0–499 of the four fields' own files; `secondary_real/7_boosted_trees/result.json`, `0c84fdab071ae509…`):
    - **Cases and rows:** 1,754 cases, as the primary. 83,481 rows: 5,973 control rows were left out, because a row needs all four values. 200 blocks.
    - **Baseline PR AUC 0.0553. Change in PR AUC −0.00070, 95% interval −0.00637 to +0.00557, p = 0.180** (500 draws; null median −0.0021).
    - **Other metrics:**
      - ROC AUC +0.0037 (interval −0.0118 to +0.0170, p 0.006);
      - pooled top-10% capture +0.0131 (interval −0.0343 to +0.0327, p 0.224);
      - top-10% capture within the risk set +0.0074 (p 0.373).
    - The ROC p is below 0.05 while its interval includes zero. It is nominal, on one of four uncorrected metrics, with no decision attached.
    - **Bootstrap:** 500 resamples over the 200 blocks, all with a value; 164 seconds. The null took 55 seconds.
    - The amplitude, local relative motion and acceleration surrogate files were then deleted, each after its hash was re-checked: 02:33:16 (`6587de4df5be9a6f…`), 02:36:28 (`4ad83729546a5325…`) and 02:39:43 (`823755f4a3fafa99…`).
  - **9. Lag 1 month** (real run 2026-11-16 02:40:35–02:43:24 EET, 40 workers; its own 999 draws, GPU; `secondary_real/9_lag_1/result.json`, `123fbdc18a0a0973…`):
    - **Cases and rows:**
      - 1,729 cases. Dropped: 986 with no value in the window (including events whose window precedes the field's first window), 127 missing a Baseline 1 input, and 4 demolition-censored.
      - 82,324 rows, after 5,855 control rows were left out. Cases by fold: 311, 346, 348, 356, 368; 200 blocks.
    - **Baseline PR AUC 0.0466. Change in PR AUC −0.00052, 95% interval −0.00173 to +0.00052, p = 0.949** (null median −0.00032).
    - **Other metrics:**
      - ROC AUC −0.0012 (interval −0.0038 to +0.0014, p 0.483);
      - pooled top-10% capture −0.0075 (interval −0.0188 to +0.0093, p 0.995);
      - top-10% capture within the risk set +0.0017 (p 0.347).
    - **Bootstrap:** 2,000 resamples over the 200 blocks, all with a value; 90 seconds.
    - The lag 1 surrogate file was then deleted at 02:46:40 after its hash was re-checked (`765959e0211d72e1…`).
  - **9. Lag 3 months** (real run 2026-11-16 02:47:31–02:50:19 EET, 40 workers; its own 999 draws, GPU; `secondary_real/9_lag_3/result.json`, `d0edd8eb4e49c09b…`):
    - **Cases and rows:**
      - 1,663 cases. Dropped: 1,052 with no value in the window, 127 missing a Baseline 1 input, and 4 demolition-censored.
      - 79,319 rows, after 5,494 control rows were left out. Cases by fold: 302, 331, 342, 332, 356; 199 blocks.
    - **Baseline PR AUC 0.0472. Change in PR AUC −0.00015, 95% interval −0.00157 to +0.00115, p = 0.004** (null median −0.00068).
    - **Reading of this p:** the change is negative. Its p is small because the null's draws lowered PR AUC further (median −0.00068), so it is not a gain. It is nominal, with no decision attached.
    - **Other metrics:**
      - ROC AUC −0.00064 (interval −0.0025 to +0.0013, p 0.276);
      - pooled top-10% capture −0.0036 (interval −0.0171 to +0.0130, p 0.916);
      - top-10% capture within the risk set −0.0006 (p 0.913).
    - **Bootstrap:** 2,000 resamples over the 199 blocks, all with a value; 87 seconds.
    - The lag 3 surrogate file was then deleted at 02:53:27 after its hash was re-checked (`a9de0dac0b75f8ea…`).
  - **9. Lag 6 months** (real run 2026-11-16 02:59:19–03:02:02 EET, 40 workers; its own 999 draws, GPU, finished 02:55:36; the file hash in the result, `42c978b8f0ef2cd7…`, equals the queue's; `secondary_real/9_lag_6/result.json`, `d24f2d6185215cbc…`):
    - **Cases and rows:**
      - 1,593 cases; the field's first window with values is 2019-02. Dropped: 1,122 with no value in the window, 127 missing a Baseline 1 input, and 4 demolition-censored.
      - 75,894 rows, after 5,349 control rows were left out. Cases by fold: 285, 323, 331, 308, 346; 197 blocks.
    - **Baseline PR AUC 0.0473. Change in PR AUC −0.00023, 95% interval −0.00143 to +0.00083, p = 0.047** (null median −0.00041).
    - **Reading of this p:** as at lag 3, the change is negative. Its p is below 0.05 because the null's draws lowered PR AUC further, so it is not a gain. It is nominal, with no decision attached.
    - **Other metrics:**
      - ROC AUC −0.00051 (interval −0.0025 to +0.0015, p 0.250);
      - pooled top-10% capture −0.0006 (interval −0.0170 to +0.0131, p 0.723);
      - top-10% capture within the risk set −0.0031 (p 0.136).
    - **Bootstrap:** 2,000 resamples over the 197 blocks, all with a value; 83 seconds.
    - The lag 6 surrogate file was then deleted at 03:05:17 after its hash was re-checked (`42c978b8f0ef2cd7…`).
  - **9. Lag 12 months** (real run 2026-11-16 07:21:04–07:22:50 EET, 40 workers; its own 999 draws, CPU, file finished 07:21:04; the file hash in the result, `c29a47969d770bb4…`, equals the queue's; `secondary_real/9_lag_12/result.json`, `64db64572a363118…`):
    - **Cases and rows:**
      - 1,502 cases; the field's first window with values is 2019-08. Dropped: 1,213 with no value in the window, 127 missing a Baseline 1 input, and 4 demolition-censored.
      - 71,533 rows, after 5,069 control rows were left out. Cases by fold: 264, 299, 310, 291, 338; 198 blocks.
    - **Baseline PR AUC 0.0471. Change in PR AUC −0.00075, 95% interval −0.00195 to +0.00078, p = 0.721** (null median −0.00064).
    - **Other metrics:**
      - ROC AUC −0.00088 (interval −0.0046 to +0.0033, p 0.123);
      - pooled top-10% capture −0.0027 (interval −0.0255 to +0.0105, p 0.105);
      - top-10% capture within the risk set −0.0040 (p 0.781).
    - **Bootstrap:** 2,000 resamples over the 198 blocks, all with a value; 45 seconds.
    - The lag 12 surrogate file was then deleted at 07:26:18 after its hash was re-checked (`c29a47969d770bb4…`).
  - **10. Issue date** (real run 2026-11-16 07:27:09–07:29:57 EET, 40 workers; the primary's 999 draws; re-dated events `500ad39c69c335dc…` and episodes `e53f6ee48239c328…`; `secondary_real/10_issue_date/result.json`, `2161d4effa59dda6…`):
    - **Dating:** each event takes the issue date of its episode's first permit (§12.10). The §4 episodes and events are re-dated, not re-derived.
    - **Cases and rows:**
      - 1,732 cases (104 of them in 2018). Dropped: 965 with no value in the window, 126 missing a Baseline 1 input, 5 demolition-censored, and 18 whose issue date falls outside the study months (2025-12: 11; 2026-02: 2; 2026-05: 1; 2026-06: 1; 2026-10: 3).
      - 82,524 rows, after 5,808 control rows were left out. Cases by fold: 313, 348, 344, 358, 369; 201 blocks.
    - **Baseline PR AUC 0.0460. Change in PR AUC −0.00061, 95% interval −0.00188 to +0.00036, p = 0.813** (null median −0.00051).
    - **Other metrics:**
      - ROC AUC −0.0016 (interval −0.0045 to +0.0019, p 0.250);
      - pooled top-10% capture −0.0029 (interval −0.0225 to +0.0079, p 0.560);
      - top-10% capture within the risk set −0.0092 (p 0.928).
    - **Bootstrap:** 2,000 resamples over the 201 blocks, all with a value; 90 seconds.
  - **11. Fold seeds 0–9** (real runs 2026-11-16 07:30:48–07:51:05 EET, 40 workers, one after another, each after its decoy smoke; the primary's 999 draws, `07bf0d54eef4b623…` in every result; no bootstrap, as §15's how-computed entry says; `secondary_real/11_fold_seed_<s>/result.json`):
    - **Cases and rows (the same in every seed):** 1,754 cases. Dropped: 961 with no value in the window, 127 missing a Baseline 1 input, and 4 demolition-censored. 83,496 rows, after 5,958 control rows were left out; 200 blocks. Only the split into five folds changes.
    - **Per seed** (change, with p and null median in brackets; times are the real run's start and end):

      | Seed | Real run | Cases by fold | Baseline PR | Change in PR AUC (p; null median) | Change in ROC AUC (p) | Top-10% capture (p) | Top-10% within the risk set (p) | Hash |
      |---|---|---|---|---|---|---|---|---|
      | 0 | 07:30:48–07:32:08 | 315, 342, 360, 387, 350 | 0.0460 | −0.00019 (0.316; −0.00024) | −0.00090 (0.101) | −0.0017 (0.951) | +0.0000 (0.252) | `9fe532fc4b3d38d2…` |
      | 1 | 07:32:58–07:34:16 | 334, 351, 323, 383, 363 | 0.0460 | −0.00059 (0.222; −0.00070) | −0.00215 (0.728) | −0.0125 (0.842) | −0.0086 (0.635) | `4351b97996b4b69f…` |
      | 2 | 07:35:04–07:36:23 | 332, 341, 338, 384, 359 | 0.0465 | −0.00106 (0.916; −0.00074) | −0.00211 (0.400) | −0.0108 (0.760) | −0.0137 (0.573) | `c534639513b73556…` |
      | 3 | 07:37:10–07:38:27 | 324, 339, 342, 395, 354 | 0.0461 | −0.00006 (0.367; −0.00011) | −0.00026 (0.047) | −0.0006 (0.981) | −0.0051 (0.953) | `4bd1ef17dafe8704…` |
      | 4 | 07:39:15–07:40:33 | 338, 367, 365, 356, 328 | 0.0442 | −0.00030 (0.317; −0.00036) | −0.00119 (0.175) | −0.0074 (0.972) | +0.0034 (0.701) | `17ee3693c7b310d6…` |
      | 5 | 07:41:23–07:42:42 | 331, 385, 357, 353, 328 | 0.0443 | −0.00051 (0.942; −0.00034) | −0.00115 (0.239) | −0.0017 (0.951) | −0.0091 (0.999) | `e937535676c9f890…` |
      | 6 | 07:43:33–07:44:51 | 336, 362, 335, 374, 347 | 0.0461 | −0.00062 (0.033; −0.00096) | −0.00146 (0.481) | −0.0148 (0.970) | −0.0046 (0.510) | `dc2eb150cb286c63…` |
      | 7 | 07:45:38–07:46:56 | 332, 363, 332, 382, 345 | 0.0465 | −0.00066 (0.003; −0.00121) | −0.00215 (0.591) | −0.0182 (0.988) | −0.0063 (0.789) | `5b23f5996ba4c85d…` |
      | 8 | 07:47:43–07:49:01 | 332, 385, 357, 355, 325 | 0.0448 | −0.00032 (0.911; −0.00019) | −0.00106 (0.384) | −0.0051 (1.000) | −0.0114 (1.000) | `53cf74bcc82fb0a2…` |
      | 9 | 07:49:49–07:51:05 | 306, 346, 359, 384, 359 | 0.0463 | −0.00018 (0.069; −0.00037) | −0.00028 (0.250) | −0.0051 (0.952) | −0.0057 (0.925) | `f1c0796801d47974…` |

    - **Summary:** the change in PR AUC is negative under every seed, from −0.00106 to −0.00006 (median −0.000414; the primary's seed gave −0.00058). PR p ranges from 0.003 to 0.942. *Corrected 2026-11-17: the median was first written as −0.00042, computed from rounded values. The secondary report computes it at full precision.*
    - **Reading of the small p values:** seeds 6 and 7 (PR p 0.033 and 0.003) and seed 3's ROC (p 0.047) have negative changes. Their p values are small because the null's draws lowered the metric further (null medians −0.00096, −0.00121 and −0.00068), so none is a gain. All are nominal, with no decision attached.
    - Each null took 29–32 seconds.
  - **12. Availability only** (real run 2026-11-16 07:52:11–07:55:19 EET, 40 workers; its own 999 draws, GPU, file finished 05:34:41; the file hash in the result, `dbc69f1023508657…`, equals the queue's; cases masked by the primary velocity field; `secondary_real/12_availability/result.json`, `7d1ca273647a9605…`):
    - **Cases and rows** (the primary's, through the mask): 1,754 cases. Dropped: 961 with no value in the window, 127 missing a Baseline 1 input, and 4 demolition-censored. 83,496 rows, after 5,958 control rows were left out. Cases by fold: 319, 349, 346, 365, 375; 200 blocks.
    - **Baseline PR AUC 0.0460. Change in PR AUC +0.000043, 95% interval −0.00044 to +0.00032, p = 0.210** (null median −0.000069).
    - **Other metrics:**
      - ROC AUC −0.00020 (interval −0.0014 to +0.0006, p 0.581);
      - pooled top-10% capture +0.0006 (interval −0.0067 to +0.0068, p 0.685);
      - top-10% capture within the risk set +0.0006 (p 0.123).
    - **Bootstrap:** 2,000 resamples over the 200 blocks, all with a value; 90 seconds. The null took 32 seconds.
    - The availability surrogate file was then deleted at 07:58:58 after its hash was re-checked (`dbc69f1023508657…`).
  - **13. No construction mask** (real run 2026-11-16 08:10:01–08:14:02 EET, 40 workers; its own 999 draws, GPU, file finished 08:05:28 and hashed by 08:10:11; the file hash in the result, `aa71f43122fa64f0…`, equals the queue's; `secondary_real/13_no_construction_mask/result.json`, `a5c115dd458e8bb6…`):
    - **Cases and rows:**
      - 2,555 cases, against the primary's 1,754. Dropped: 160 with no value in the window, 127 missing a Baseline 1 input, and 4 demolition-censored.
      - 121,826 rows, after 8,479 control rows were left out. Cases by fold: 450, 541, 511, 509, 544; 201 blocks.
    - **Baseline PR AUC 0.0456. Change in PR AUC −0.00027, 95% interval −0.00135 to +0.00040, p = 0.141** (null median −0.00037).
    - **Other metrics:**
      - ROC AUC −0.00088 (interval −0.0033 to +0.0013, p 0.313);
      - pooled top-10% capture −0.0023 (interval −0.0176 to +0.0052, p 0.633);
      - top-10% capture within the risk set −0.0043 (p 0.735).
    - **Bootstrap:** 2,000 resamples over the 201 blocks, all with a value; 136 seconds. The null took 45 seconds.
    - The no-construction-mask surrogate file was then deleted at 08:17:29 after its hash was re-checked (`aa71f43122fa64f0…`).
  - **First-run velocity file moved from the CPU to the GPU (2026-11-16 08:21:37 EET; authors' choice; recorded before any slip-rule result exists).**
    - **Why:** the CPU queue began the first-run velocity file (slip-rule sensitivity) at 07:21:04. CPU files of this kind took about 7 h (acceleration: 19:05–02:11), so it would have been ready at about 14:30. The GPU had been idle since its queue ended at 08:10:11, and its last three files of this kind took about 2.5 h each. Test B variants take about 3.5 minutes each (15_lag_1: 08:17:41–08:20:54), so the slip-rule runs would have waited about 5 h for the CPU file.
    - **What was done:**
      - At 08:21:37 the CPU maker (PID 850838) was stopped with SIGTERM. Its 64 worker processes were then stopped by their saved PIDs (`work/insar/surr2/v_firstrun_cpu_worker_pids.txt` on the server). The CPU queue logged `v_firstrun surrogates exit=143` and `queue end`.
      - With no maker running, the queue's own release steps were repeated by hand: the partial `.tmp.npy` file and `engine.txt` were removed and the claim was released. The empty CPU log was kept as `surr.cpustop_20261116_082137.log`.
      - At 08:22:27 the unchanged `surr_queue2.sh` (`5bfd37ebe831907f…`) was started as `surr_queue2.sh gpu`. It claimed the field and began the file at 08:22:28 (`engine.txt`: gpu).
    - **Within the plan:** §15's secondary-files entry allows either engine and applies no GPU/CPU agreement rule. Settings, seed, field and outcome-blindness are unchanged. No secondary result was read in making this choice.
    - **Ordering:** the orchestrator is unchanged. It reaches `slip_first_run` after D2 and waits there for the file's quantile record.
  - **15–17. Test B with other fields** (real runs 2026-11-16 08:17:41–08:42:25 EET, one after another, each after its decoy smoke; each with its own Test B null file, 999 draws, seed 2034, made on 2026-11-15 by `run_testb_variants.sh`; each file's SHA-256 in the result equals the file on the server; `secondary_real/<item>/result.json`):
    - **Events:** 2,842 counted, 2,655 inside the 28 quarters. The model is Test B's Poisson with cell and quarter fixed effects; the interval is the Wald interval with errors clustered by 2 km block, as in the primary. "Rows used" is the model's rows after all-zero cells are dropped.
    - **Reading of the direction (§8B):** a rate ratio below 1 is concordant (more motion away from the satellite is followed by more permits).

      | Item | Real run | Events in rows used | Rows used (cells, blocks) | IQR | Rate ratio per IQR (95% CI) | p_B (exceedances) | Hash |
      |---|---|---|---|---|---|---|---|
      | Lag 0 (primary, 2026-11-12) | — | 2,553 | 38,047 (1,397, 145) | 27.0 mm/yr | 1.006 (0.867–1.168) | 0.967 (966) | `489e822c79226dac…` |
      | 15. Lag 1 | 08:17:41–08:20:54 | 2,553 | 38,011 (1,398, 145) | 39.4 mm/yr | 0.849 (0.708–1.018) | 0.425 (424) | `e518cf347074eb3a…` |
      | 15. Lag 3 | 08:21:06–08:24:04 | 2,559 | 38,030 (1,398, 144) | 24.9 mm/yr | 1.119 (0.979–1.279) | 0.466 (465) | `84c37ec5a3a57b40…` |
      | 15. Lag 6 | 08:24:14–08:27:06 | 2,552 | 38,066 (1,401, 144) | 24.0 mm/yr | 0.990 (0.849–1.156) | 0.954 (953) | `7305992f4b8e9874…` |
      | 15. Lag 12 | 08:27:16–08:30:08 | 2,537 | 37,919 (1,396, 144) | 23.3 mm/yr | 1.133 (1.021–1.257) | 0.327 (326) | `318424bee44a0ad3…` |
      | 16. 24-month window | 08:30:18–08:33:20 | 2,449 | 35,924 (1,360, 142) | 10.0 mm/yr | 0.964 (0.816–1.140) | 0.886 (885) | `49439d66b85bfa31…` |
      | 17. Amplitude | 08:33:30–08:36:22 | 2,553 | 38,047 (1,397, 145) | 9.0 | 0.903 (0.778–1.049) | 0.583 (582) | `006419aec2518179…` |
      | 17. Local relative motion | 08:36:32–08:39:24 | 2,553 | 38,047 (1,397, 145) | 1.1 | 0.975 (0.943–1.008) | 0.579 (578) | `68f2f69a811f1995…` |
      | 17. Acceleration | 08:39:34–08:42:25 | 2,451 | 35,971 (1,360, 142) | 47.7 | 0.850 (0.690–1.046) | 0.426 (425) | `089259bd99a9d711…` |

    - **Reading of lag 12:** its Wald interval (1.021–1.257) excludes 1, in the discordant direction, while its surrogate p_B is 0.327. Both are stated. The Wald interval assumes that clustering by block captures the spatial dependence, and the conditional surrogate null does not make that assumption. It is nominal, with no decision attached.
    - No other interval excludes 1, and no p_B is below 0.05. The lags are analysis windows, not estimates of the delay (§12, item 9).
    - Each null took 165–185 seconds.
  - **18. Negative binomial with area characteristics** (real run 2026-11-16 08:42:56–08:55:01 EET; the primary Test B null file, `0bc1305e07d0c348…`; `secondary_real/18_negative_binomial/result.json`, `8bf19dbb51dab6ab…`):
    - **Rows:** 129,682 rows in; 1,035 dropped because their cell holds no house with complete characteristics; 128,647 rows used in 4,934 cells and 192 blocks. Area characteristics: age at start, log living area, log lot area, the 0–150 cm shrink–swell value, slope, elevation, log income, slab foundation, and the x and y coordinates.
    - **Fit:** Newton's method from the Poisson start; dispersion α 1.066. No null draw needed the BFGS start.
    - **Estimate:** β = +0.0023 per mm/yr (clustered SE 0.0037). **Rate ratio per IQR (27.1 mm/yr) 1.066, 95% CI 0.876–1.296. p_B = 0.694** (693 exceedances). The null took 718 seconds.
  - **19. Monthly counts** (real run 2026-11-16 08:55:18–09:02:18 EET; its own monthly Test B null file, `1158a35c6b832f11…`; `secondary_real/19_monthly/result.json`, `65e8d93147d69ec4…`):
    - **Events and rows:** all 2,842 events fall in the 88 study months; 2,727 are in rows used and 115 in rows without a value. 407,624 rows in; the model keeps 124,420 rows in 1,455 cells, 88 months and 145 blocks.
    - **Estimate:** β = −0.0032 per mm/yr (clustered SE 0.0021). **Rate ratio per IQR (33.8 mm/yr) 0.898, 95% CI 0.782–1.030. p_B = 0.475** (474 exceedances). The null took 411 seconds.
  - **D1. Demolition as the outcome** (real run 2026-11-16 09:03:06–09:04:26 EET, 40 workers; the primary's 999 draws; `secondary_real/D1_demolition/result.json`, `6a3ce4fd80f15051…`):
    - **Cases and rows:**
      - 3,797 demolitions in the file; 381 outside the study months; 3,416 candidates. 887 cases. Dropped: 2,121 with no value in the window, 233 with a matched foundation episode on or before the demolition date, and 175 missing a Baseline 1 input.
      - 42,238 rows, after 2,999 control rows were left out. Cases by fold: 132, 247, 179, 129, 200; 198 blocks.
    - **Baseline PR AUC 0.1311. Change in PR AUC −0.00038, 95% interval −0.00137 to +0.00055, p = 0.928** (null median −0.00014).
    - **Other metrics:**
      - ROC AUC +0.00010 (interval −0.0011 to +0.0012, p 0.125);
      - pooled top-10% capture 0.0000 (interval −0.0100 to +0.0083, p 0.863);
      - top-10% capture within the risk set +0.0079 (p 0.015; null median 0). This is 7 of the 887 cases. It is nominal, on one of four uncorrected metrics, has no bootstrap interval, and carries no decision.
    - **Bootstrap:** 2,000 resamples over the 198 blocks, all with a value; 27 seconds.
  - **D2. Composite outcome** (real run 2026-11-16 09:05:15–09:07:56 EET, 40 workers; the primary's 999 draws; `secondary_real/D2_composite/result.json`, `c484379122e07b9b…`):
    - **Cases and rows:**
      - 6,235 composite candidates, as counted by the runner (3,797 demolitions in the file, 381 of them outside the study months). 2,641 cases: 1,754 foundation events and 887 demolitions. Dropped: 3,082 with no value in the window, 302 missing a Baseline 1 input, and 210 with a matched foundation episode before the date that is not the event itself.
      - 125,702 rows, after 8,989 control rows were left out. Cases by fold: 451, 596, 525, 494, 575; 199 blocks.
    - **Baseline PR AUC 0.0474. Change in PR AUC −0.00011, 95% interval −0.00074 to +0.00053, p = 0.986** (null median +0.00016).
    - **Other metrics:**
      - ROC AUC −0.0013 (interval −0.0043 to +0.0009, p 0.920);
      - pooled top-10% capture −0.0008 (interval −0.0086 to +0.0082, p 0.393);
      - top-10% capture within the risk set +0.0011 (p 0.469).
    - **Bootstrap:** 2,000 resamples over the 199 blocks, all with a value; 87 seconds.
  - At 09:07:56 the orchestrator reached `slip_first_run` and waits for the first-run velocity file (GPU, started 08:22:28).
  - **Slip-rule sensitivity, Test A** (first-run velocity, before the cycle-slip correction of §14; real run 2026-11-16 10:53:42–10:55:45 EET, 40 workers; its own 999 draws, GPU, file finished 10:49:52 and hashed by 10:53:56; the file hash in the result, `cf91fac8f91b47a1…`, equals the queue's; `secondary_real/slip_first_run/result.json`, `0dd5480a2937c934…`):
    - **Cases and rows:**
      - 1,833 cases, against the primary's 1,754. Dropped: 882 with no value in the window, 127 missing a Baseline 1 input, and 4 demolition-censored.
      - 87,345 rows, after 6,138 control rows were left out. Cases by fold: 374, 349, 354, 379, 377; 196 blocks.
    - **Baseline PR AUC 0.0463. Change in PR AUC −0.00016, 95% interval −0.00174 to +0.00105, p = 0.233** (null median −0.00055).
    - **Other metrics:**
      - ROC AUC −0.00042 (interval −0.0044 to +0.0024, p 0.055);
      - pooled top-10% capture +0.0005 (interval −0.0207 to +0.0076, p 0.326);
      - top-10% capture within the risk set −0.0038 (p 0.527).
    - **Bootstrap:** 2,000 resamples over the 196 blocks, all with a value; 56 seconds. The null took 20 seconds.
    - The first-run surrogate file was then deleted at 10:58:58 after its hash was re-checked (`cf91fac8f91b47a1…`).
  - **Slip-rule sensitivity, Test B** (first-run cell velocity; real run 2026-11-16 10:59:08–11:02:15 EET; its own Test B null file, 999 draws, seed 2034, `6fd6fb45668cddbc…`, equal to the file on the server; `secondary_real/slip_first_run_b/result.json`, `aba9b8501f012058…`):
    - **Events and rows:** 2,842 counted, 2,655 inside the 28 quarters, 2,581 in rows used and 74 in rows without a value. The model keeps 38,400 rows in 1,399 cells, 28 quarters and 145 blocks.
    - **Estimate:** β = −0.0014 per mm/yr (clustered SE 0.0024). **Rate ratio per IQR (27.0 mm/yr) 0.963, 95% CI 0.848–1.094. p_B = 0.798** (797 exceedances). The null took 181 seconds.
  - **All secondaries 1–19, D1–D2 and the slip-rule sensitivity are done.** `run_secondaries.sh` logged `run_secondaries end` at 11:02:15 EET with no failure. Item 14 (owner-initiated repairs) was removed, because certified yearly deed records were not in hand at checkpoint 1 (§4; §12 item 14). Item 20, the deep model, starts next through `run_deep.sh` (`d157e23aea4cdf5f…`).
  - **20. Deep model: GPU decoy smoke passed; real run started.**
    - **Smoke** (2026-11-16 11:03:30–11:13:49 EET; `work/secondary/smoke_pre/20_deep_model/`; decoy, a code and memory check, not a result): the registered GPU generator at chunk 8, 2 draws over all 254 dates, 2 resamples, 2 workers.
      - Rows equal the primary decoy record (1,568 cases, 74,829 rows; drops, control rows dropped and cases per fold all equal).
      - The null's 2 draws took 515 seconds on the GPU with no memory failure, so the memory rule is not needed.
      - Sources as fixed on 2026-11-15 (`secondary_deep.py` `1e07f3f5…`, `deep_field.py` `3ca903db…`, frozen `deep_model.py` `9ce5ccfb…`, `lowmem_null.py` `84a6e78e…`).
    - **Real run started** at 11:13:49 EET (`run_deep.sh 32`; 99 draws, seed 2037; 2,000 resamples), on the primary's 1,754 cases and 83,496 rows. From the smoke's rate, the serial null should take about 7–8 hours.
  - **20. Deep model, real run** (2026-11-16 11:13:49–16:39:35 EET, 32 workers, GPU null; `secondary_real/20_deep_model/result.json`, `12ac6bc0c79b4b92…`; also `null_draws.json` `e38d77a0b48caf39…`, `fold_audit.json` `e7d9c7566f71c98b…`, `oof_scores.npz` `4dd920f4d83645f4…`, and the log `55e941eae83774a2…`; all equal to the server's):
    - **Rows:** asserted equal to the primary record (`real_20261112/test_a.json`): 1,754 cases, 83,496 rows, the same drops (961 with no value in the window, 127 missing a Baseline 1 input, 4 demolition-censored), 5,958 control rows left out, and cases by fold 319, 349, 346, 365, 375.
    - **Field:** 254 dates, 114,058 pixels, first reference date 2016-07-10, 17 reference dates; 3,696 pixels carried across at least one link; 99.6% of pixel-dates valid, no date without a valid pixel. Across the rows' series, 91.0% of steps are valid, and every row has at least 42 valid steps.
    - **PR AUC:** comparison network (Baseline 1 only) 0.0503; series network 0.0466. **Change in PR AUC −0.0037, 95% interval −0.0054 to +0.0016. Null p = 0.52** (51 of 99 draws at or above the observed change; p = (1 + 51) / 100).
    - **Other metrics** (bootstrap intervals; the null tests PR AUC only): ROC AUC −0.0092 (−0.0163 to +0.0087); top-10% capture −0.0296 (−0.0392 to +0.0173).
    - **Null:** the 99 changes have median −0.00370 and range −0.00387 to −0.00344; the observed change (−0.00371) sits at their median. Neighbour counts 28 or 44; median relative variogram RMSE 0.024 (largest 0.030). Setup 201 seconds; the 99 draws took 19,400 seconds on the GPU without a memory failure.
    - **Reading:** adding the series lowers PR AUC, and it does so by almost the same amount with surrogate series, whose link to the outcome is broken. So the loss comes from the larger network, not from the content of the parcel's own series. The p is unconditional and is read with §12's caveat; here it is 0.52, so the caveat does not change the reading. No decision is attached.
    - **Bootstrap:** 2,000 resamples over the 200 blocks, all with a value; resamples 0 and 1 recomputed in the parent and equal. They ran beside the null.
  - **All runs of §12 are complete** (16:39:35 EET). What remains is the secondary reports.
- **2026-11-17. Secondary report written** (Claude; the user asked for it with "Go").
  - **Report:** `secondary_real/AUSTIN_SECONDARY_RESULTS.md` (`4bfb57719af8e986…`), with the same numbers in `secondary_real/secondary_summary.json` (`ba12c39a0585e900…`).
  - **How it is made:** `production/secondary_report.py` (`7754186df2282329…`; PC only, standard library, `python3 -I`) reads the real results in `secondary_real/`, the primary records in `real_20261112/` and the run log `secondary_real/status_real`.
    - Every result number is read from those files by code. The plan's fixed settings (windows, draw counts, seeds) are stated as in §12 and §15.
    - It fits nothing and runs no null and no bootstrap. Its only computations are the fold-seed median, the percentiles of item 1's stored resamples, and the prevalence.
    - Two runs give byte-identical output.
  - **Checks in the generator:**
    - Every result is labelled REAL RUN, and its SHA-256 equals the hash in the run log's end line.
    - The primary rows equal `test_a.json` and `report_a.json`. The null (a) and MSR records have the primary's cases and observed change.
    - The frozen plan's hash is asserted.
    - Item 1's interval, recomputed from its 2,000 stored resamples, equals the stored one.
  - **Item 1's wide lower bound (−0.00206 against a change of −0.0000032) is real.** 483 of 2,000 resamples give a change below −0.0005, while the median resample is −0.0000047. The report states this beside the table.
  - **Contents:**
    - the primary analyses, for reference;
    - the §12.8 nulls (largest p 1.000);
    - one table of the Test A secondaries (1–7, 10, 12, 13, the slip-rule sensitivity, D1, D2);
    - the lag profile with lag 0 (§12 item 9, one table);
    - the fold seeds;
    - the Test B secondaries with lag 0 (§12 item 15);
    - the deep model;
    - what was not run (14 removed; P0–P1 option C only);
    - every nominal p below 0.05 in the Test A designs, with its reading;
    - samples and exclusions;
    - the run record with each item's start and end times.
  - No decision is attached to any of it (§12). Nothing in §4–§12 changed.
- **2026-11-17. Result document written** (Claude; the user asked for it with "Go").
  - **Document:** `AUSTIN_RESULT.md` (`d8a7c296abcc0f3b923097679fd4ecf9b71048506ba9eb51a2a959126676f28a`), beside the plan.
  - **How it is made:** `production/result_report.py` (`4dbc69fc37c4059980b52b3e282dda6d41c32e528e015966313eb438054cb4e0`; PC only, standard library, `python3 -I`).
    - It reads the real-run records in `real_20261112/`, the check records in `production/check/`, the planted-signal summary, the checkpoint 1 records, and the secondary report and its summary.
    - Every result number is read from those records by code. The §11 decision rule and readings are quoted line for line from the frozen plan. The §14 titles and the planted-signal odds ratios are read from this plan's text.
    - It fits nothing and runs no null and no bootstrap. Its only computations are:
      - medians and maxima of stored null draws;
      - shares, percentages and the mean number of controls per case;
      - the exponential of a stored log-interval.
    - Two runs give byte-identical output.
  - **Checks in the generator:**
    - Both frozen plans' hashes are asserted.
    - Each of the 22 records it reads has its SHA-256 checked against this section (full hash or the quoted prefix) or against the hash list written with it.
    - Both reports' rebuild checks passed. The report's foundation analysis equals `test_a.json` (cases, rows, drops, observed change, p and all 999 null statistics).
    - The null (a) and MSR records have the primary's cases, rows and observed change. The secondary summary's primary values and generator hash match.
    - Test B's 2,842 counted events equal the 2,846 events minus the 4 demolition-censored ones.
  - **Checked against this section:**
    - The null-draw medians and percentiles of the primary, null (a) and MSR records were recomputed at full precision from the stored draws. This found the null (a) median error, corrected above (−0.00006 to −0.00005).
    - An automated pass confirmed that each number of the document's sections 1–7 occurs in the entries above. This test does not tie a number to its place.
    - Claude then read sections 2–7 line by line against the real-run, check, decoy, planted-signal and checkpoint 1 entries. No other disagreement was found.
    - Some numbers are not stated in this section and are read directly from the records:
      - the velocity model's levels and the null medians of the other metrics;
      - cases by year;
      - the clay classes' counts on the corrected values;
      - the corrected sign-check difference;
      - the survivorship link check by year (`checkpoint1/link_check_2018.json`, not reported in §15 before).
  - **Contents:**
    - summary;
    - the variogram checks (first, §10);
    - the decision (§11) with the secondary metrics, the interval and directional concordance;
    - Test B;
    - the items reported beside the decision: the §12.8 nulls, both remodel specificity checks with their direct comparisons, and the §11 readings;
    - the planted-signal sensitivity (cells 4–6, as §14 fixes);
    - the checks before outcomes:
      - the sign check (not below in both runs), with its diagnostics and the slip correction;
      - the clay contrast, coverage and the decoy run;
      - the checkpoint 1 checks of design summary points 8 and 11, including the permits-and-drought check and the survivorship link check by year;
    - samples and exclusions;
    - a summary of the secondary analyses, pointing to the secondary report;
    - the §14 deviations, with a line on the authors' choices that §15 records after the primary result;
    - limits;
    - the record table;
    - the variogram tables by distance.
  - It adds no new analysis and no new reading. Nothing in §4–§12 changed.
- **2026-11-17. Exploratory comparison of test statistics on synthetic events** (Claude; the user approved it with "ok" after the literature search, `feasibility/literature_methods/SYNTHESIS.md` section 2).
  - **What it is:** not part of the frozen analysis. It changes no Austin decision, no §11 reading and nothing in §4–§12. No real event is joined to a velocity value: real events enter only as the dates file of the planted-signal check.
  - **Question:** inside the same conditional-null surrogates, does another statistic detect a planted velocity effect more often than the change in out-of-fold average precision, without more false positives?
  - **Code:** `planted_signal/statistic_comparison.py` (`4f74ad9d205b3c4391598bc50ce44240cbbc334019ddca3f2ed4420fe37dfe9c`). It imports `planted_signal.py` (977f626f…) and `testa_core.py` (f4d71575…) unchanged and asserts their hashes. Same seeds, synthetic datasets, risk sets, folds, design, observed field, 999 stored surrogates (seed 2027) and their quantiles as the planted-signal check.
  - **Statistics, from one set of fits per field (frozen nyc_lib logistic model):** change in out-of-fold average precision (frozen, the anchor); change in out-of-fold log-likelihood; change in in-sample log-likelihood; velocity coefficient (lower tail, as planted); |coefficient|. Detection is p < 0.05 with the sign condition where one applies.
  - **Where and when:** server, 64 workers (`work/insar/run_statcmp.sh`). Cells 1, 4, 5: 2026-11-17 11:22–12:43. Cells 2, 3 (added by Claude to check false positives under misspecification): 12:45–13:37. 100 datasets per cell.
  - **Checks:** the frozen statistic reproduced all 500 planted-signal records exactly (observed, baseline and all 999 null values; max difference 0.0; same p and decision in each). Both summaries were rebuilt on the PC from the copied records, byte-identical.
  - **Records:** `planted_signal/statcmp_20261117/` (summary json `90f29385…`, md `930994f0…`; hash list `SHA256SUMS_statcmp_20261117` `b3100f98…`) and `planted_signal/statcmp_20261117_cells23/` (json `fc248516…`, md `d9f19736…`; `SHA256SUMS_statcmp_20261117_cells23` `6a8d5a09…`).
  - **Result (detected out of 100; cells 1–3 have no velocity effect):**

    | Statistic | 1 | 2 | 3 | 1–3 pooled | 4 (β −0.1) | 5 (β −0.2) |
    |---|---|---|---|---|---|---|
    | Out-of-fold average precision (frozen) | 5 | 11 | 5 | 7.0% | 34 | 75 |
    | Out-of-fold log-likelihood | 7 | 4 | 3 | 4.7% | 66 | 100 |
    | In-sample log-likelihood | 9 | 10 | 5 | 8.0% | 68 | 100 |
    | Velocity coefficient, negative tail | 7 | 3 | 2 | 4.0% | 55 | 96 |
    | Absolute coefficient | 7 | 3 | 4 | 4.7% | 55 | 96 |

    - Paired on the same datasets against the frozen statistic, out-of-fold log-likelihood detected 34 datasets the frozen statistic missed and missed 2 it detected in cell 4 (exact McNemar p 1.9e-8). In cell 5 the counts were 25 and 0 (p 6.0e-8).
    - Pooled rates are the sums of the two summaries' counts. Only the in-sample log-likelihood is above 5% (one-sided binomial p 0.017; the frozen statistic 0.078; scipy binomtest).
  - **Reading (exploratory):** on Austin's design, the change in out-of-fold log-likelihood about doubles power at β = −0.1 without more false positives. It is the candidate primary statistic for any new frozen plan, with the change in average precision as the effect size. Limits: one design, effect planted in the model's own log-linear form, 100 datasets per cell.

## 16. Revisions before freezing

- 2026-10-28: first draft (Claude). The supervisor's decisions of 2026-10-28 are applied: same question, city need not be coastal. The user's choices are applied: parcel unit, deep learning as a secondary tier, Miami and Hong Kong parked.
- 2026-10-28: second draft (Claude, agreed with the user).
  - **Window:** the primary window is now 24 months, with 12 and 36 months secondary. The event period starts 2018-08-01.
  - **Work-class rule:** BP events need work class Repair or Remodel (sample precision 35/38).
  - **Readability checks added:** the clay visibility check, the permits-and-drought check, the remodel negative control with its specificity label, the sale-triggered split (secondary 14) and the conditional foundation-type baseline feature.
  - **Reading table:** a fixed table for interpreting each result was added to §11.
  - **Step 0:** pre-freeze checks added to §13.
- 2026-10-28/29: step 0 results (Orca-supervised workers; Claude reviewed both and released them).
  - **TCAD availability** (Codex, gpt-6.1-sol; `step0/TCAD_AVAILABILITY.md`, manifest with sha256): recorded in §3. 1.16 GB downloaded; raw files and row-level outputs are in `Alex_private/austin/tcad/`. Claude re-checked the 2026 roll hash and that no owner, address or contractor field reached the project files. The reference-roll and townhouse questions are open (points 7 and 8).
  - **Literature** (Grok 4.7; `step0/LITERATURE.md`): recorded in §2. Claude re-queried all 25 DOIs at Crossref; all resolve with matching title, first author and year.
  - **Timing gate (§10):** not yet run. On the 2026 diagnostic (112,072 cells, 88 windows), the NYC implementation needs about 21.5 GB of GPU memory. The surrogate file of 999 draws is about 39 GB on disk.
- 2026-10-30: third draft (Claude, agreed with the user), after the supervisor's response to the permit-timing weakness. The supervisor advised that the permit date is a delayed indicator of damage discovery, that lags be examined, that permit counts by area and period be modelled with Poisson or negative binomial regression against preceding ground motion, that building susceptibility be classified where building characteristics exist, and that deep learning not be the starting point.
  - **Two questions and two decision tests**, corrected together with Holm's method (§1, §11):
    - Test A (where) is the draft 2 primary analysis, unchanged;
    - Test B (when) is new: a Poisson model of quarterly applications in 250 m cells, with cell and quarter fixed effects, the houses at risk as exposure, preceding 12-month cell velocity as predictor, and a variogram-matching null (§8B, §9, §10).
  - **Wording:** the permit date is a delayed indicator of damage discovery; a control or a zero count means "not applied", not "undamaged" (§1, §4, §8).
  - **Physical indicators:** one fixed list (velocity, seasonal amplitude, differential movement, acceleration) for both tests (§7).
  - **Lag profiles:** lags of 1, 3, 6 and 12 months for both tests, reported together, none chosen (§12.9, §12.15).
  - **Negative binomial** with area characteristics instead of area fixed effects added as secondary 18. Test B's primary model is Poisson with fixed effects, because negative binomial with fixed effects is not a true fixed-effects estimator.
  - **Deep model:** renumbered 19, runs last.
  - **Working title:** the supervisor's, with "seismic" replaced by "InSAR", to be confirmed.
  - Controls per risk set restated as about 145,000 parcels, from the step-0 diagnostic.
- 2026-10-30: the user's decisions on the open step-0 points.
  - **Townhouses:** the primary population is detached houses only (improvement type 01) (§5).
  - **Reference roll:** a public-information request to TCAD for the certified rolls 2016–2025. The plan is not frozen before TCAD answers.
  - **Timing gate:** the user will pause the model server that holds the GPU, so the gate can run on the detached-house diagnostic (111,039 cells).
- 2026-10-30: timing gate run (Claude), with the model server paused by the user.
  - The NYC class ran out of GPU memory while building its pair mask. The log is kept: `step0/timing/timing_k1000_nyc_class_OOM.log`.
  - A memory-lean subclass was written and checked against the NYC class (§10).
  - Result: 6.9 s per draw, 1.9 hours for 999 draws. The setting stays at a neighbour cap of 1,000 and 999 draws.
  - Before freezing, the subclass moves to `austin/scripts/`.
  - Step 0 is complete except the TCAD reference rolls (point 9).
- 2026-10-30: wording and reporting fixes (Claude, agreed with the user), after an outside review of the supervisor's response, which the user shared. No test, rule or threshold changed.
  - **Titles:** both are offered to the supervisor. One is his own with "seismic" replaced by "InSAR". The other, "…Linking InSAR-Derived Ground Deformation with Delayed Foundation-Repair Records", avoids "risk".
  - **Test A wording:** "building susceptibility" is replaced by "which parcels record a repair". The output is the likelihood of a recorded repair permit, and susceptibility is the motivation (header, §1).
  - **Indicator 3:** renamed "local relative motion" and stated not to be differential settlement across a foundation (§7, §12).
  - **Specificity:** the labels are now "check passed" or "check failed", with the negative control's effect size and interval reported. A passed check is stated not to prove the absence of bias. The clay check's "visible" is stated to concern soil classes, not each house (§7, §11).
  - **Parcel link check** for qualifying permits added at checkpoint 1, reported only (§4, §13).
  - **Reading table:** reworded to concern recorded repairs, not physical damage or cause.
- 2026-10-30: the user sent the Public Information Act request to TCAD (text: `step0/TCAD_PIA_REQUEST_draft.md`). Waiting for TCAD's reply (records, cost estimate or refusal).
- 2026-10-30: fourth draft (Claude, at the user's direction). The supervisor's guidance of 2026-10-30 is implemented as a design, not put back to him as questions.
  - **Analysis hierarchy (the authors' choice, not the supervisor's):** Test A (property level) is the single primary analysis and carries the decision at p < 0.05. Test B (area-level quarterly counts with eligible houses at risk as exposure) is the key secondary analysis. It is fully prespecified, with its own reading, and reported whatever its result. Holm's correction is removed because only one analysis carries the decision. The reasons are in the design summary, point 2. This replaces the two-decision design of draft 3.
  - **Working title:** the supervisor's, with "InSAR time series". "Repair risk" is defined as the likelihood or rate of recorded repair permits.
  - **Neighbourhood income:** moved from Baseline 2 into Baseline 1 as the authors' choice (§9). The reasons are owner-behaviour confounding and the east–west income–geology pattern, and the data are public and predate the study. A tract fallback, a 10% missingness safeguard and a no-income comparison (secondary 5) are added. Coverage is checked in `step0/ACS_INCOME_AVAILABILITY.md`.
  - **Monthly counts** added as Test B secondary 19. The deep model is renumbered 20.
  - **Outstanding data limitations** listed in the header.
- 2026-10-30: neighbourhood-income coverage checked (step 0; Grok 4.7 as an Orca-supervised worker; `step0/ACS_INCOME_AVAILABILITY.md`, `acs_manifest.json`, scripts in `step0/scripts_acs/`). Raw files are in `Alex_private/austin/acs/`.
  - **Source:** the Census Data API now refuses anonymous requests (it redirects to a "missing key" page). No key was used. The estimates come from the 2015 ACS five-year summary file (Texas tracts and block groups, table B19013 in sequence 59), with the 2015 TIGER block groups.
  - **Coverage:**
    - block groups with a median: 568 of 580;
    - detached houses: 99.42% have a block-group median, 0.56% use the tract fallback, and 0.03% have neither.
  - **Margin of error:** median relative margin 0.26.
  - **Claude's review:**
    - all 10 manifest hashes match the files;
    - every count was reproduced with an independent script;
    - the project files hold aggregate counts only.
  - **Result:** income stays in Baseline 1, and the 10% safeguard is not expected to trigger.
- 2026-10-30: fifth draft (Claude, at the user's direction). The study no longer waits for TCAD, and the supervisor is consulted only if the work is blocked.
  - **Reference roll:** the 2026 certified roll, which is already in hand, is the reference for the primary analysis whatever TCAD answers (§5, design summary point 9). Before, the plan was to be frozen only after TCAD answered, using the earliest obtainable roll.
    - **Why:** its main features do not change with a foundation repair, and its two weaknesses are measured and reported: the survivorship check (§5) and possible post-event updates (header limitation 1).
  - **Sensitivity analysis:** if TCAD's rolls arrive before the real run, Test A is repeated on the earliest received roll and reported beside the primary, with no decision (§5).
  - **Sale split (secondary 14):** a default rule using only the 2026 latest deed date. Events after a parcel's latest sale are classified exactly. Events at parcels sold after the event are "unknown" and left out. The yearly-roll rule applies only if TCAD's rolls arrive (§4).
  - **Approval:** the user approves the plan before freezing (header, §13). The supervisor is consulted only if the work is blocked, as in §6.
  - **Correction:** the closing line of §12 still said that Tests A and B both carry decisions (left over from draft 3). It now says that only Test A does.
- 2026-10-30: sixth draft (Claude, at the user's direction). Historical TCAD rolls are preferred but not a condition for proceeding, and the records request stays active. Draft 5's "2026 roll whatever TCAD answers" is withdrawn.
  - **Outcome-blind evidence** (`step0/refdata_checks.json`, from `step0/scripts_refdata/refdata_checks.py`; public 2019 TxGIO parcel layer vs the 2026 roll, no permit or InSAR data):
    - year built is identical for 99.7% of the same houses, and lot area within 1% for 96.5%;
    - of 151,944 Austin A1 houses built by 2015 in 2019, 94.8% are in the 2026 detached population, 1.6% were rebuilt, and 2.2% left A1 or changed ID;
    - the 2019 layer has no deed dates, living area or foundation type.
  - **Options A–D** with their trade-offs are in `step0/REFERENCE_DATA_OPTIONS.md`.
    - **Proposed:** A (certified 2018 roll) if it is in hand at checkpoint 1, otherwise C (2019 public layer, verified-stable features only). D (2026 only) is not used. All of this is pending the user's approval (§5, design summary point 9).
  - **Common rules added:**
    - demolished houses stay at risk until their first Demolition BP;
    - the survivorship check is extended;
    - later-arriving rolls are exploratory only.
  - **Removed:** the reference-roll sensitivity analysis and draft 5's 2026-only sale rule. Secondary 14 runs only with yearly rolls (option A).
  - **Under C:** living area and foundation type leave Baseline 1. Secondary 5 adds them back as a variant for houses whose year built is unchanged.
- 2026-10-31: the user approved the reference-data order: A (TCAD certified 2018 roll) if it is in hand when checkpoint 1 starts, otherwise C (2019 TxGIO layer, verified-stable features only). Under C the study period keeps its start of 2018-08-01, not the strict 2019-10-01. "Pending approval" was removed from §5 and design summary point 9.
- 2026-10-31: seventh draft (Claude, at the user's direction).
  - **TCAD:** the official request stays active, with the certified 2018 roll as its priority. A follow-up for the user to send is in `step0/TCAD_PIA_FOLLOWUP_draft.md`.
  - **Option C registered as the fallback, with eligibility beginning after September 2019.**
    - The study period under C starts on 2019-10-01 (§4), with 74 monthly windows and 24 quarters (§7).
    - The earlier choice to keep 2018-08-01 under C is withdrawn. Under A the study still starts on 2018-08-01.
  - **The "missing 1.4%" is reconciled** (`step0/id_crosswalk.json`): of the 2,152 houses of 2019 whose 2026 main improvement is not type 01, 2,150 are type 16 townhouses with the same year built in both years.
  - **Identifier crosswalk:** a three-stage outcome-blind crosswalk (property ID, `geo_id`, polygon overlap) was started by Claude (v1: 149,857 by property ID, 2 by `geo_id`, 194 by overlap, 1,891 unresolved).
    - The `geo_id` is unchanged for every surviving property ID.
    - The unresolved group is being investigated by a Codex worker (gpt-6.1-sol, Orca-supervised; report `step0/ID_CROSSWALK.md`). The rule registered from it is inserted in §5 before freezing.
  - **Living area and foundation type** stay out of C's Baseline 1. Any analysis with their 2026 values is exploratory, outside the secondary list, and not evidence of prospective predictive performance (§9). The draft-6 secondary-5 variant is removed.
  - **Demolition:**
    - Censoring is kept, now defined as the first *total* demolition, with a hand audit of 50 permits.
    - Whether demolition is an informative competing outcome is examined: permit checks (a)–(b) at checkpoint 1, before InSAR, and secondary analyses D1–D3 (demolition as the outcome, a composite outcome, and demolished houses kept in the risk sets) with a fixed reading (§5, §12, §13).
  - **Sale analysis (secondary 14):** kept only if certified yearly deed records for the whole period become available. A single 2018 roll does not provide them (§4).
- 2026-10-31: eighth draft (Claude). The identifier crosswalk is complete, and its rule is registered in §5.
  - **Crosswalk** (`step0/ID_CROSSWALK.md`, `step0/id_crosswalk.json`): audited and completed by a Codex worker (gpt-6.1-sol, Orca-supervised), outcome-blind. Claude reran the script and got byte-identical output.
    - **Result:** 149,857 houses by property ID, 0 by `geo_id` under a new property ID, 21 renumbered, 126 merged and 49 split by polygon overlap, and 1,891 unresolved.
    - **Corrections to Claude's v1:** its two `geo_id` matches had zero polygon overlap and are renumberings, and its "no improvement" flag was invalid. The draft-7 entry above gives the v1 counts.
    - **Unresolved:** not misregistration and not missing pages. Most fall in gaps of the 2026 hosted layer. Condominium conversion, re-subdivision and confidentiality suppression remain unverified causes.
  - **Registered (§5):**
    - the population under C is fixed from 2019 alone and called "A1 historical houses";
    - the 2,152 same-ID, same-year 2026 townhouses are left out, under the registered assumption that an unchanged year built means an unchanged building;
    - permits link through the 2019 `geo_id`;
    - six houses with ambiguous keys are left out;
    - successor keys of split, merged and renumbered lots are not used;
    - a house with no 2026 match is not treated as demolished.
    - The primary population under C is 149,786 houses at step 0.
  - **Added:** the link check (§5, checkpoint 1); sensitivities P0 (no 2026 information) and P1 (confirmed continuity) (§12); and the rule that a 2026 value is carried to a 2019 house only with the same property ID and year built (§9).
  - **"Missing 1.4%" restated** from the crosswalk: 2,152 same-ID, same-year townhouses. The draft-7 figure of 2,150 used v1's grouping.
- 2026-11-01: wording fix (Claude): §10 Test B still gave 28 quarterly windows only. It now gives 28 under option A and 24 under option C, as §7 does.
- 2026-11-01: the user confirmed Claude's choice for option C. The 2,152 same-ID, same-year 2026 townhouses stay out of the primary population, and sensitivity P0 keeps them (§5, §12). The crosswalk report had preferred the reverse.
- 2026-11-01: clarification (Claude, answering the script author's question): the deep model's series (§12 item 20) uses the §7 window of the event month, not a window ending at *t_e*. It then uses the same information as the primary analysis, and all rows of a risk set share one window.
- 2026-11-01: the surrogate construction for the deep model's 99-draw null was registered (§12 item 20, seed 2037), at the script author's question, so that it is fixed before any result.
- 2026-11-01: analysis scripts written before freezing (Codex worker, gpt-6.1-sol, Orca-supervised; synthetic data only; `scripts/README.md`, `scripts/SHA256SUMS`). Claude reran the quick checks on a copy and reproduced them.
  - **Null module:** `scripts/lowmem_null.py` and `scripts/nyc_lib.py` are byte-identical to `step0/timing/lowmem_null.py` and the NYC library. Equality with the NYC class holds to 3e-14.
  - **Test B** (`scripts/test_b.py`): pyfixest PPML, which agrees with an independent statsmodels fit to 1e-15 in β and 1e-12 in the clustered SE. On an overdispersed synthetic panel of realistic size it recovers β = −0.3503 (true −0.35). The 999 null refits take about 4 minutes.
  - **Deep model** (`scripts/deep_model.py`):
    - **Fixed:** a small CNN (2→8→8 channels, about 860 parameters), CPU, deterministic, with all hyperparameters fixed.
    - **Synthetic checks:** a planted signal is found (PR AUC gain 0.65), none is found when absent (gain 0.0015, interval spans 0), and reruns are identical.
    - **Cost:** 300,000 rows over five folds take 3.2 minutes.
  - **Deep-model null calibration:** 10 no-signal datasets with 19 draws each. Mean p is 0.555, none is at 0.05, and observed gains are not inflated. A planted signal gives p = 0.05 (the minimum).
    - The surrogate series are somewhat smoother and heavier-tailed than real ones. This is reported as a limitation, and the registered construction is kept.
    - The 99-draw null is projected at 5–8 hours. Whether 254 acquisition dates fit in GPU memory is unverified, and the memory rule is in §12 item 20.
- 2026-11-01: ninth draft (Claude, at the user's direction, after an outside review of the written design that the user shared).
  - **Test A null (§10):** the null hypothesis is stated. Variogram surrogates lose the velocity field's link with the baseline features, so the null could be too lenient if velocity proxies a misspecified clay effect.
    - A synthetic calibration compares the registered null with a conditional (residual) null in nuisance-only scenarios (a Codex worker, Orca-supervised).
    - The rule that selects the primary null was registered before any calibration result.
  - **Metric (§9):** PR AUC is average precision, measured in the sampled risk sets, and is not citywide precision or a calibrated risk. Blocks are assigned by pixel, so parcels that share a pixel are in one fold. The bootstrap keeps a parcel's rows together.
  - **Wording (§11):**
    - "does not add value", "not associated" and "cannot resolve" are replaced by "not demonstrated" or "not detected", limited to 24-month velocity in the logistic model.
    - The negative controls are read as "detected / not detected", with a direct foundation-minus-remodel comparison and its interval.
    - The clay check becomes the clay contrast check, a diagnostic.
  - **Shared at-risk rule (§8):** one rule for both tests. A house whose first matched episode is not an event leaves both tests at that date. Test B counts exposure at the start of the quarter, an approximation. Its predictor is a fixed area field.
  - **Test B (§9):** the Poisson explanation is corrected (consistency needs a correct mean; Allison and Waterman concerns the conditional negative-binomial model).
  - **Demolition:** D3 is removed, and D1–D2 are kept. The censoring date is the demolition permit's date, an administrative date.
  - **Outcome terminology:** the outcome is the first recorded qualifying permit in the issued-permit dataset, dated by application. A house without a permit has a valid zero.
  - **Option C:** the townhouse assumption is called an assumption. P1 shows dependence on restricting to surviving, linked houses, not the direction of survivor bias.
  - **Core analyses** listed (design summary point 11).
  - **Freeze package:** copies of the scripts and the calibration report go into `freeze/`.
  - **Correction:** the deep-model null checks of 2026-11-01 (ten datasets, 19 draws each) are smoke checks. They found no problem in the scenarios tested, but do not establish the false-positive rate. An entry above called them a calibration.
- 2026-11-01: before any calibration result, the selection rule of §10 was extended (Claude): scale cells (N2 and N4 at four times the city size) and a bias criterion were added, because a bias that is small in a small synthetic city grows relative to chance at Austin's event count.
- 2026-11-01/02: calibration run (Codex worker, gpt-6.1-sol, Orca-supervised, then run by Claude after the worker stopped). Execution history, including GPU scheduling, a memory kill and restarts, is in `scripts/calibration/COORDINATOR_EXECUTION_NOTES.md`. No simulation, model, null or decision setting changed, and every record carries the same source fingerprint.
- 2026-11-06: tenth draft (Claude). The null cells were complete on 2026-11-02, and the selection rule gave branch 3 (§10). Claude rechecked the rule independently from the records (`scripts/calibration/coordinator_rule_check.py` and `.json`; rerun on 2026-11-06 with identical output).
  - **The user chose the conditional null (b) as the primary Test A null** on 2026-11-06 (rule 3). Null (a), the NYC null, becomes secondary 8.
  - **§10:** method, null hypothesis, result and limits rewritten for (b). Pixels for its fit use parcels with complete Baseline 1 inputs.
  - **§12:** null (a) added to secondary 8. The deep model's unconditional surrogate null is read with the calibration's caveat.
  - **§13:** the null calibration and the conditional null's timing added to step 0.
  - **Comparability with NYC:** NYC used null (a). The Austin primary null differs, and null (a) is reported beside it for comparison.
- 2026-11-06: TCAD answered request R010955-110226 with a quote of 22 files at $4 each ($88, no file list). The user modified the request to the certified 2018 roll export and the 2018 parcel layer only (expected about $8), and withdrew the other years. Option A remains possible if these arrive before checkpoint 1, and checkpoint 1 is scheduled to wait for them unless the user decides otherwise (design summary point 9). The sale analysis (secondary 14) is not expected to run.
- 2026-11-06: calibration completed (Claude resumed the run stopped on 2026-11-02; execution notes as above). All 2,200 synthetic datasets are complete and audited (`scripts/calibration/CALIBRATION.md`, `results.json`). Claude reproduced the report's null-cell table from the records (20 of 20 rows identical, branch 3) and recounted power and the Test B size check from the records.
  - **Test B size check (§10):** 2.5% of 200 panels rejected.
  - **Power (§10):** lower under (b) than under (a): 18% against 35% at β = −0.2, and 60% against 84% at β = −0.4. Power does not enter the rule. These results arrived after the user's choice of (b).
  - **Conditional null timing (§10):** 23 s of added fitting at full size; 999 draws projected at 2.0 hours. The gate setting is unchanged.
- 2026-11-07: wording before freezing (Claude, at the user's question). The calibration's nominal rate of 4% is explained: it follows from 99 draws per dataset, and the study's 999 draws give 4.9%. The Test B size check is described as a calibration check of the tested synthetic scenario, not proof of exact type-I error control (§10).
- 2026-11-07: **the user approved draft 10 and the conditional null (b) as the primary Test A null.** Power results stay descriptive only. The plan was frozen (§15).
