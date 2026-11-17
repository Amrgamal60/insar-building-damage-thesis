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

(empty)

## 15. Freeze record

- **Plan approved by:** the user, on 2026-11-07: draft 10, with the conditional null (b) as the primary Test A null and power results descriptive only (§10, §16). The supervisor was not consulted, because the work was not blocked (header).
- **Frozen copy:** `freeze/AUSTIN_PLAN_frozen.md`, saved 2026-11-07 (EET; UTC timestamp in `freeze/FROZEN_AT.txt`), SHA-256: ______
- **Scripts:** `freeze/scripts/`, a copy of `scripts/` without Python caches: 2,301 files, including the 2,200 calibration records. Every entry of its `SHA256SUMS` was verified in the copy. `scripts/SHA256SUMS` SHA-256: `9fa37e9fab6c7b062c173720cf6f000c1fcc102fb02e7dfa6910da9e7cb18425`
- **Calibration report:** `freeze/CALIBRATION.md`, a copy of `scripts/calibration/CALIBRATION.md` with the coordinator's addendum, SHA-256: `a4e63692abedea0dbfbfb4a7d74a7020304926d2e644d27fefdb601f65971f6a`
  - Independent selection check `scripts/calibration/coordinator_rule_check.json`, SHA-256: `0064d7a8edcfffff0b3ade4c488d143b5150ad8b91a286916c6e1a28a5aa22fc`
- **Keyword protocol (§4):** `feasibility/candidates/keyword_protocol.md` (2026-10-26), copied to `freeze/keyword_protocol.md`, SHA-256: `3a74c0b9f40ef226d3332206e537f11cd9b71c65a7ae5acce1af5516e87934fb`
- **Timing-gate setting (§10):** neighbour cap 1,000 and 999 draws for both Test A nulls: the conditional null (primary) and the NYC null (secondary 8), with seed 2027. Test B: 999 draws, seed 2034. Timing evidence `step0/timing/SHA256SUMS`, SHA-256: `41653da4707f30941d62326b3090cfafdc64296a707d6abbbb07466ce882b1d5`
- **Reference data at freezing:** option A waits for TCAD's certified 2018 roll and 2018 parcel layer (request R010955-110226, narrowed on 2026-11-06). Option C is the registered fallback (§5, design summary point 9).
- **NYC freeze unchanged:** `feasibility/nyc/freeze/NYC_REPLICATION_PLAN_frozen.md`, SHA-256 `59a2aa1a573ce8b7cf7ede7fd1e870bea2768c259978c716872f177041588a5d`, checked at this freeze.
- **Freeze manifest:** `freeze/MANIFEST.sha256`, covering every file in `freeze/`, SHA-256: ______

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
