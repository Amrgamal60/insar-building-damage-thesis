# NYC replication plan: does the Alexandria InSAR result hold in a second city?

**Status:** approved by the supervisor and frozen on 2026-10-08 (written 2026-10-07, revised 2026-10-08). No NYC model has been fitted and no NYC result exists. On 2026-10-07/08, before freezing, the raw OPERA InSAR and the open static layers were downloaded and integrity-checked only (§13 step 3, §15); no InSAR value has been computed or read at any event or cell. The draft was revised after an independent methods review on 2026-10-07 and after a second review on 2026-10-08 (§16). The freeze record is in §15; every later change goes in the deviations log with its date and reason.

**Role in the thesis:** Alexandria is the discovery study and NYC is a preregistered external replication. Every choice below is fixed before NYC modelling starts, and none is tuned on NYC results.

## 1. Question

Does InSAR ground motion measured *before* each structural collapse improve the held-out ranking of collapse locations in New York City? The improvement must be beyond the Alexandria urban baseline and projected coordinates, inside a pre-specified older-building-stock domain (or the whole city, if that domain holds too few events; §6).

The Alexandria result being tested is from the historic core: 250 m cells, logistic regression, baseline + x/y vs baseline + x/y + velocity, change in out-of-fold PR AUC.

| Velocity product | PR AUC | Change | Largest p over six nulls | Source |
|---|---|---|---|---|
| Shirzaei VLM (period not stated) | 0.328 → 0.372 | +0.044 | 0.023 | `data/pilot/VARIOGRAM_NULL.md` |
| LiCSAR, first epoch to Dec 2016 (mostly Nov 2015 – Dec 2016) | 0.328 → 0.413 | +0.085 | 0.005 | `data/pilot/LICSAR_TEST.md` |

Both Alexandria velocities overlap the 2014–2016 collapses, so Alexandria shows a concurrent association. NYC tests a stronger claim: that motion measured *before* each collapse helps. A non-replication therefore does not by itself refute the Alexandria association.

## 2. Prior work and the gap

As of 2026-10-07, from targeted searches rather than a systematic review, the closest studies are:

| Study | Data and outcome | What it shows | What it does not test |
|---|---|---|---|
| [Mohamadi, Balz & Younes 2020](https://doi.org/10.3390/rs12203307), *Remote Sensing* 12:3307 | PS-InSAR and district-office collapse records, Alexandria | Collapses fall in emerging deformation hot or cold spots | Controls beyond location, held-out validation, null models |
| [Ohenhen & Shirzaei 2022](https://doi.org/10.1029/2022EF003219), *Earth's Future* 10:e2022EF003219 | Sentinel-1 VLM 2018–2021, 43 geolocated collapses, Lagos | Most collapses lie in high-subsidence areas (descriptive overlay) | Any statistical test. The authors say they could not test the relationship further. |
| [Sadhasivam et al. 2025](https://doi.org/10.1038/s41893-025-01663-0), *Nature Sustainability* | Sentinel-1 VLM 2015–2023, five Indian megacities | Building damage risk from differential subsidence, assuming uniform building vulnerability | Validation against observed damage. The authors call for a spatially explicit, temporally resolved damage record. |
| [Ohenhen et al. 2025](https://doi.org/10.1038/s44284-025-00240-y), *Nature Cities* | VLM 2015–2021, 28 US cities including NYC | Subsidence-based infrastructure risk maps | Validation against an observed damage or collapse catalogue |
| [Peduto et al. 2019](https://doi.org/10.1016/j.sandf.2018.12.009), *Soils and Foundations* | DInSAR settlement and surveyed damage to masonry buildings, the Netherlands | Empirical fragility curves from an independent damage survey | Incremental held-out value over baseline and location, spatial nulls |
| [Yang, Huang, Li & Chang 2026](https://doi.org/10.1016/j.rse.2026.115454), *Remote Sensing of Environment* | PS-InSAR | Building risk levels derived from InSAR-based IBUSI/IBDS indicators. The displacement observations are validated. | As far as we can tell from the paper, it does not validate incremental predictive value against an independent catalogue of observed structural collapses. |

**The gap this thesis addresses** has four parts. Each has been addressed separately, but no study we found combines them:
1. Independent outcome validation: InSAR is tested against a catalogue of observed structural collapses, not against risk indices built from InSAR itself.
2. InSAR that precedes the outcome in time.
3. Spatial controls: a baseline plus coordinates, spatially separated folds and autocorrelation-preserving nulls.
4. Replication across cities.

We do not claim that data-driven use of InSAR for building risk is new.

## 3. What is already known about the NYC data (disclosure)

The feasibility audit (`out/AUDIT.md`, 2026-10-07) and the methods review produced the following before this plan was frozen:
- event counts at each cleaning stage;
- events per borough and per year (of the 82 events from 2017-07-16 on, 26 are in Brooklyn and 24 in the Bronx);
- the building age of the event lots: median 91 years, and 76% at least 80 years old;
- the OPERA coverage dates.

The event building ages motivated looking at older building stock, which the Alexandria result had already suggested. The domain threshold in §6 comes from the conventional NYC age class, not from these numbers. No InSAR value, baseline feature or model output for NYC has been computed, and the domain's event count (§6) was not computed before the 30-event rule was written.

## 4. Outcome (frozen)

- **Catalogue:** NYC Emergency Management "Emergency Response Incidents" (NYC Open Data `pasr-j7fb`). Types `Structural-Collapse` and `Structural-Partial Collapse`. The copy downloaded on 2026-10-07 is `raw/incidents.csv` (records 2011-05 to 2022-08).
- **Event rule** (`scripts/01_audit_events.py`, then `scripts/02_freeze_events.py`, both unchanged after freezing):
  1. Merge reports at the same address within 3 days.
  2. Geocode to an address-level tax lot in the stated borough with NYC Planning Geosearch.
  3. Require the geocoded point to be within 150 m of the OEM point, where a usable one exists.
  4. Require a PLUTO record for the lot.
  5. Exclude events with major works on the lot in the 365 days before the event: BIS permits NB, DM or A1, or DOB NOW Full Demolition, Foundation, Earth Work or Support of Excavation.
  6. Exclude events with a new-building, demolition or excavation permit on another lot of the same tax block within 50 m in those 365 days.
- **Result:** 185 events (2011-05-16 to 2022-06-29), frozen as `out/events_final.csv`, one row per event with ID, date and lot point.
- **Event cell:** the cell holding the event's geocoded lot point.
- **Known limit:** OEM records no cause, so the permit rules are a proxy. They are not revised after this plan, and known misses stay in the data. One example is 331 Madison Ave (2015); it falls outside the InSAR period in any case.
- **Construction near controls:** §7 masks InSAR pixels near permitted works for every cell, so cases and controls are treated the same way.

## 5. Cells and eligibility

- **Study area:** the five boroughs, from NYC DCP Borough Boundaries (clipped to shoreline), downloaded on 2026-10-08 with its source metadata and hashed in `raw/STATIC_MANIFEST.sha256`.
- **Grid:** EPSG:32618 (UTM 18N). Square cells of 250 m (primary) and 200 m (sensitivity), aligned to multiples of the cell size.
- **Lot point:** a lot is assigned to the cell holding its PLUTO XCoord/YCoord point (NY State Plane, reprojected to UTM 18N), the release's approximate location of the lot. Lots without coordinates are not assigned.
- **Reference PLUTO:** PLUTO 15v1, the only release labelled 2015 in NYC DCP's archive. Its data files are dated 2015-06-22, before the first OPERA date (2016-07-16) and every analysed event. It was downloaded on 2026-10-08 and is hashed in `raw/STATIC_MANIFEST.sha256`. It alone fixes the study population: eligibility (below), the domain and the event count (§6). The population is therefore the same for every event.
- **Event PLUTO:** for the two time-varying features in §9 (building count and building age), each event uses the latest PLUTO release whose data files are dated before *t_e*. Every cell in that event's risk set uses the same release.
  - A release's date is the newest date of the data files inside its archive, which is when DCP built it, not its version label. The date of every release is recorded at checkpoint 2.
  - If a release cannot be downloaded or lacks NumBldgs or YearBuilt, the previous usable release is used and the substitution is logged.
- **Eligible cells:**
  - **built-up:** the lots whose lot point falls in the cell hold at least one building (the sum of their NumBldgs is at least 1) in the reference PLUTO. This replaces Alexandria's footprint rule (§9).
  - **settled:** as in Alexandria, the cell holds the centre of at least one 30 m WSF Evolution pixel first mapped as settlement in 1985–2015.
- **Landmass groups:** each cell is assigned by borough polygon to one of four landmass groups, used for referencing in §7:
  - Manhattan;
  - the Bronx;
  - Brooklyn with Queens;
  - Staten Island.

## 6. Primary population: older building stock, with a pre-set switch

- **Rule:** at each resolution, a cell is in the domain if at least 5 tax lots in the reference PLUTO with a recorded year built have their lot point in it, and more than half of those lots were built before 1940. Lots with year built 0 or missing are not counted.
- **Why 1940:** "pre-war" (built before 1940) is the conventional age class for New York City's building stock. It marks the end of the period dominated by load-bearing masonry construction. The majority rule and the 5-lot minimum are fixed here and are not varied.
- **Analogy to Alexandria:** Alexandria's historic core was a set of central districts with old building stock. The NYC domain tests that reading of the core, using building age alone and not NYC events.
- **Event count and switch** (this rule was written before the count was computed):
  - **Count:** the events in `out/events_final.csv` dated on or after 2017-07-16 whose 250 m cell is eligible (§5), is in the domain and holds no earlier event (§8). The count uses only the reference PLUTO, the borough boundaries and WSF, and no InSAR. It is computed once, at checkpoint 2, and recorded in §15.
  - **30 or more:** the domain is the primary population. The whole of NYC (all eligible cells) is secondary analysis 1, the generalization analysis.
  - **Fewer than 30:** the whole of NYC becomes the primary population and the domain becomes secondary analysis 1.
  - The choice is made once, at 250 m, and holds for every analysis, 200 m cells included. Events lost later to InSAR coverage or the per-pixel completeness rule (§7, §8) do not reopen it.
  - **If the switch applies,** the primary test is broader than the Alexandria result, which came from the historic core. A non-replication across the whole city would then say less about Alexandria's core finding.
- In the rest of this plan, **the primary population** means whichever of the two this rule selects.

## 7. InSAR (processed blind to outcomes)

**Product.** [OPERA L3 DISP-S1 v1](https://www.earthdata.nasa.gov/data/catalog/asf-opera-l3-disp-s1-v1-1) (CMR collection C3294057315-ASF), frame F08622 (Sentinel-1 track 33, ascending). Its granules run from 2016-07-16, the earliest date in the frame's CMR record, and cover all five boroughs. It is the only usable time series: the descending tracks 113 and 11 have about 10 acquisitions each over NYC, and LiCSAR has one epoch.

**Geometry and sign.** Line-of-sight unit vectors come from the DISP-S1 STATIC layers (C3959290248-ASF). In OPERA's convention a positive line-of-sight value means motion toward the satellite. The variable is called **line-of-sight ground deformation**, not vertical subsidence: one viewing geometry cannot separate vertical from east-west motion.

**Software.** opera-utils 0.25.8, pinned now. Any other library is pinned in a lock file hashed at checkpoint 2. NYC files are read as subsets clipped to the five boroughs.

**Processing,** fixed before any NYC InSAR is opened:
1. **Layer and masks.** Use the full `displacement` layer, not the short-wavelength one. Apply the product's recommended mask and water mask. Correction layers are not applied. Exact layer names are recorded from the first granule.
2. **Re-referencing.** For each window, chain each pixel's displacement across the product's reference-date changes, starting from the last reference date on or before the window start.
3. **Invalid pixels.** A pixel is invalid for a window if it is masked at a reference change inside the window, or if its connected-component label at any epoch in the window is 0 or differs from the label at the frame's reference point.
4. **No vertical projection.** Velocities stay in line of sight, positive toward the satellite. Over NYC the LOS up-component is 0.78–0.81 (STATIC layer, read 2026-10-08). Dividing by it would only rescale by a nearly constant factor, and would add an assumption of no horizontal motion.
5. **Construction mask (all cells alike).** For each window, drop pixels within 50 m of the lot point of any BIS NB/DM/A1 or DOB NOW Full Demolition/Foundation/Earth Work/Support of Excavation permit issued between 365 days before the window start and the event date. The permits come from a citywide extract of permits issued 2013–2022 from both DOB systems, downloaded on 2026-10-08 and hashed in `raw/STATIC_MANIFEST.sha256`.

**Window velocity.** For event *e* on date *t_e*, the primary window is the 365 days before *t_e*, using only acquisitions strictly before the event date.
- Each pixel's displacement is fitted with d = a + v·t + b·sin(2πt/365.25) + c·cos(2πt/365.25), so an annual (mostly thermal) cycle does not bias the slope v. The velocity is v, in mm/yr.
- A pixel has a value only if it is valid on at least 80% of the window's acquisition dates and on at least one date in each 91-day quarter of the window.

**Cell value.** The mean of the valid pixels whose centres fall in the cell, as in Alexandria's LiCSAR rule. Cells with no valid pixel have no value for that window.

**Window standardisation** (a declared difference from Alexandria, where one window made it unnecessary), in order, outcome-blind, over all eligible NYC cells with a value, whichever population is primary:
1. subtract the window's median within each landmass group, which removes the frame reference and any offset between landmasses, such as unwrapping jumps across rivers;
2. divide by the window's interquartile range;
3. winsorise at the window's 0.5th and 99.5th percentiles.

The unstandardised line-of-sight velocities (mm/yr) are kept for reporting (§11) and are not a model input.

**Robustness windows.** The 730 days and 1,095 days before *t_e*, using the same rules.

**Before outcomes are joined:**
- **Sign check:** the full-period (2016-07 to 2022-08) line-of-sight velocity of the LaGuardia Airport runway cells, a documented subsidence area, must be below the city median (motion away from the satellite). If it is not, work stops until the cause is found and logged.
- **Reports from the InSAR alone:** the coverage maps, per-window valid-cell counts and the variogram check (§10).
- **Allowed changes:** processing may be corrected after these outcome-blind checks, with every change logged, but never after any InSAR value has been compared with outcomes.

## 8. Design: event risk sets (no temporal leakage)

- **Event sample:** each event in `out/events_final.csv` dated on or after 2017-07-16 (82 events city-wide) whose cell is eligible, is in the primary population, holds no earlier event and has a window value. 2017-07-16 is one year after the frame's earliest date. Any further loss from the per-pixel completeness rule is counted and reported.
- **First event per cell:** a cell holding an earlier event in `out/events_final.csv` is neither a case nor a control. "Earlier" means any date from 2011-05-16 on, including events before 2017-07-16. So only a cell's first event can be a case, and a cell can be a control only up to its first event. The rule applies to cases and controls alike. Excluding earlier-collapse cells from the controls alone would leave repeat-collapse cells only among the cases and inflate the result.
- **Risk sets:** each event *e* defines a risk set:
  - the event's cell (positive);
  - every eligible cell in the primary population that has a value for the same window and holds no event dated on or before *t_e* (controls).
- **Same window for cases and controls:** all cells in a risk set get their InSAR value from that one calendar window.
- **Later events:** a cell that has an event after *t_e* is a valid control for *e*, because nothing after *t_e* is used. With a single window, as in Alexandria, this rule is the same as Alexandria's "background = cells without a target event".
- **Secondary control rules:**
  - the "never-case" rule, which excludes from the controls every cell that ever holds an event (secondary 11);
  - the earlier draft's rule (secondary 7): an earlier event outside the window excludes a cell from neither role, and two events in one cell form two risk sets.
- **Pooling:** rows are (risk set, cell) pairs pooled across risk sets, so a control cell appears once per risk set. Two first events in one cell on the same date form one risk set with that cell as its single positive.
- **Missing data:** events dropped for a missing window value are counted and reported.

## 9. Features, models, folds, metrics

| Setting | Alexandria (discovery) | NYC (this plan) |
|---|---|---|
| Built-up share 2015 | GHS-BUILT-S R2023A, 100 m, cell mean | same |
| Share of 2015 built-up already built in 1975 | GHS-BUILT-S 1975 / 2015 | same |
| Net building height 2018 | GHS-BUILT-H ANBH R2023A, mean of non-zero pixels | same |
| Building count, log(1 + n) | Google Open Buildings v3, confidence ≥ 0.70 | log(1 + sum of NumBldgs), event PLUTO (§5) (Google does not cover the US; current footprints postdate events) |
| Ground elevation | FABDEM v1-2, cell mean | same |
| Distance to the coast | DSAS 2021 shoreline | OpenStreetMap coastline, which follows NYC's tidal waters; snapshot of 2026-10-08, hashed in `raw/STATIC_MANIFEST.sha256` |
| Coordinates | cell centre x, y in km (UTM 36N) | cell centre x, y in km (UTM 18N) |
| Velocity | one window, mm/yr | one window per event, line of sight, standardised (§7) |

- **Baseline 1 (primary):** the six features above plus x/y.
- **Baseline 2 (secondary, harder):** Baseline 1 plus the median building age at the event date (event year minus year built) of the event-PLUTO lots in the cell with a recorded year built.
- **Velocity model:** the baseline plus the window velocity.
- **Missing inputs:** a cell missing any input of the compared models is left out of that comparison, and the cells left out are counted. Both models are always fitted on identical rows.
- **Logistic regression (primary):** StandardScaler then LogisticRegression(C = 1.0, max_iter = 5000), fitted within each training fold.
- **Random forest (secondary):** 500 trees, min_samples_leaf 5, max_features sqrt, class_weight balanced_subsample, random_state 0.
- **Folds:**
  - 2 km blocks on the UTM 18N grid, dealt into 5 folds by StratifiedGroupKFold (shuffle, seed 42). Groups are blocks; the label is "cell holds one of the 185 events", as in Alexandria.
  - The fold map is computed once per resolution on all eligible NYC cells and reused by every analysis.
  - A row takes its cell's fold. All scores are out of fold.
- **Primary metric:** change in PR AUC, computed by `average_precision_score` over all pooled out-of-fold rows, from Baseline 1 + x/y to Baseline 1 + x/y + velocity.
- **Secondary metrics:**
  - pooled ROC AUC;
  - top-10% capture in two forms: Alexandria's pooled recall (the share of positive rows among the top 10% of all pooled rows), and the share of events whose cell ranks in the top 10% of its own risk set (new; not computed in Alexandria).
- **Interval** (secondary): a refit block bootstrap resampling 2 km blocks with all their rows across risk sets. 2,000 resamples for logistic regression, 500 for random forest.
- **Prevalence:** one event per risk set among all its cells. PR AUC values will be far lower than Alexandria's 0.33, so only the change and its null test are compared.

## 10. Primary inference: variogram-matching null

- **Method:** Burt et al. 2020 variogram-matching surrogates, plain version, as in `scripts/11_msr_variogram_check.py`, adapted so the windows share their randomness. The windows overlap heavily, and drawing them independently would make p too small.
  - Each draw uses one permutation of the cells, one neighbour count k and one white-noise vector, over the union of primary-population cells with a value in any window, and applies them to every window.
  - For each window, the permuted field is smoothed over each cell and its k nearest cells with an exponential kernel. It is then rescaled and given the noise with that window's own α and β, fitted so its variogram matches the window's observed one at lags of 1–16 cell widths. A cell without a value in a window takes the window median for the smoothing only, and surrogates are used only on the window's valid cells.
  - k is chosen per draw from 15 geometric steps between 2 and min(0.9 × cells, 1,000), to best fit the mean of the windows' variograms. The cap of 1,000 neighbours is for computation; it is the default of the sampled variant in Burt et al.'s BrainSMASH.
  - Neighbours and variogram pairs are stored as sparse lists, not dense matrices.
- **Draws:** each draw replaces every window's field with its surrogate and refits the velocity model on the same folds. 999 draws, seed 2027.
- **p-value:** p = (1 + draws with a change ≥ observed) / (1 + 999).
- **Variogram check before any p-value:** for 20 windows chosen by seed 7, before outcomes are joined, the observed variogram is compared with the surrogates' 95% range at each lag, as in `MSR_VARIOGRAM_CHECK.md`, at 1–16 cell widths and at longer lags up to 20 km. The check is reported first. Whatever it shows, the primary null is not changed.

## 11. Decision rule

The Alexandria result is **replicated in NYC** (incremental-value replication) if and only if, in the primary analysis (primary population from §6, 250 m, logistic regression, Baseline 1 + x/y, 12-month window):
1. the held-out change in PR AUC from adding InSAR is positive, **and**
2. the variogram-matching null gives p < 0.05.

Otherwise it is **not replicated**. The effect size is reported with its interval and is not required to match Alexandria's.

Reported beside the decision, without changing it:
- **Directional concordance**, a separate label. Alexandria's collapse cells moved down relative to background cells; there, "collapse cells' median vertical velocity below the background cells'" was a criterion.
  - **Measure:** for each risk set, the event cell's standardised velocity minus the median of its controls' standardised velocities.
  - **Label:** the direction is **concordant** with Alexandria if the median of these differences is below zero, meaning event cells move away from the satellite relative to their controls, as relative subsidence would. It is **opposite** if the median is above zero.
  - **Reported with it:** the same differences in raw line-of-sight mm/yr, and the sign of the velocity coefficient fitted on all rows.
  - The two labels are stated together, for example "incremental-value replication with opposite deformation direction".
- **Largest p across the six nulls** (§12.8 plus the primary), Alexandria's LiCSAR-test standard.

## 12. Secondary analyses (reported, no decision attached)

Each changes one thing in the primary analysis and is tested with the primary null (999 draws; 500 for the random forest):
1. The other population (§6): the whole of NYC (all eligible cells) if the domain is primary, as the generalization analysis; or the domain, if the switch applied.
2. 200 m cells.
3. Random forest.
4. Baseline 2 (adds building age at the event).
5. The 2-year window (events on or after 2018-07-16).
6. The 3-year window (events on or after 2019-07-16).
7. The earlier control rule (§8): an earlier event outside the window excludes a cell from neither role, and two events in one cell form two risk sets.
8. The other nulls on the primary analysis:
   - free and within-2 km-block permutation, 2,000 draws each;
   - MSR and amplitude-adjusted MSR, 999 each;
   - variogram-matching rank-remapped to the observed values, 999.
9. Ten other fold assignments (seeds 0–9).
10. ROC AUC and both top-10% capture forms, for every analysis.
11. The never-case control rule (§8).
12. A linear-only window velocity (no annual terms).
13. No construction mask.
14. Availability only: a model using each cell's count of valid InSAR pixels, to check whether coverage alone tracks collapse cells (in Alexandria it did).
15. Exploratory and retrospective: Ohenhen et al. 2025 NYC mean VLM (2015–2021) as a static velocity, the analogue of the Alexandria Shirzaei analysis. It does not precede most events and carries no weight.

There is no correction for multiple tests; only the primary test carries the decision.

## 13. Order of work and safeguards

1. **Approval and freeze.** The supervisor approves this plan. A copy is saved as `freeze/NYC_REPLICATION_PLAN_frozen.md` and its SHA-256 is recorded in §15, with the event file and the audit inputs. The frozen copy is never edited; later entries go only into §14 and the checkpoint record in §15.
2. **Checkpoint 2, static layers.**
   - Build the grid, the landmass groups, eligibility, the domain and the fold maps.
   - Count the events (§6) and record the count and the primary population in §15. This happens before any InSAR value is computed.
   - Download the PLUTO releases dated 2016–2022, record each release's date (§5), and build the Baseline 1 and 2 features.
   - The citywide permit extract was downloaded early (2026-10-08, §15).
   - Hash the grid, domain, features, fold maps, event sample, PLUTO releases and the lock file.
3. **InSAR.** Download OPERA F08622 and STATIC subsets (needs a free NASA Earthdata login). Compute the window velocities, run the sign check, and produce the coverage report and the variogram check.
   - *Done early, 2026-10-07/08, before freezing:* raw files only (172 DISP-S1 granules and the 3 STATIC layers), hashed in the freeze record. The only checks run were integrity checks: the files open, share one grid and have no date gaps; STATIC matched ASF's MD5s; LOS-up component 0.78–0.81. No velocity was computed and no InSAR value was read at an event or cell.
4. **Decoy run.** Run the full pipeline once on a decoy outcome: each event moved to a random eligible cell of the primary population (seed 99), keeping its date. The decoy cells are the only positives and the risk-set rules apply to them. This checks the code end to end. Decoy results are saved and labelled, and nothing changes because of them except outright code errors, which are logged.
5. **Real run, once,** only after steps 2–4. The primary and secondary analyses run on the real events. The primary analysis runs whatever the variogram check showed and however many events remain after InSAR losses. Reruns are allowed only to fix code errors, logged with before and after values.
6. **Compute budget.** The primary analysis and its null always run to completion. Secondary analyses share a budget of 7 days of wall-clock time on the project PC; any not finished are reported as "not run".
7. **No tuning.** The study area, time windows, features, folds, models and nulls are not changed after NYC results are seen. Any analysis added afterwards is labelled exploratory.

## 14. Deviations log

Each entry: date, what changed, why, and whether any NYC result had been seen.

1. **2026-10-08, connected-component rule (§7, processing step 3). No NYC result seen; no velocity computed yet.**
   - **Frozen rule:** a pixel is invalid for a window if its connected-component label at any epoch in the window is 0 or differs from the label at the frame's reference point.
   - **Found in the granules (outcome-blind, from metadata and label layers only):**
     1. The reference pixel itself has label 0 and no displacement in every granule. It sits inside one uniform component.
     2. Each of the 12 reference dates has its own reference point. Six are in New Jersey; the other six are in eastern Queens or just across the city line on Long Island. The 2021-10-30 point lies outside the downloaded subset, so an 11 × 11 pixel window around it was fetched for its 15 granules (`scripts/08_download_refpoint.py`, `raw/opera/refpoint/`).
     3. The rivers split NYC into three components, matching the landmass groups: Manhattan with the Bronx, Brooklyn with Queens, and Staten Island. A component never spans New Jersey and NYC.
   - **Consequence:** read literally (label 0 at the reference point), the rule rejects every pixel. Read as "the component around the reference point", it rejects:
     - Manhattan, the Bronx and Staten Island in every window;
     - every NYC pixel in every window with an epoch referenced to a New Jersey point. That is every window except the 1-year windows of events from about October 2018 to May 2019.
   - **Change:** at each epoch, the comparison label is the main component of the pixel's landmass group: the most common non-zero label among the pixels whose centre lies in the group's borough polygons. This is the reference the plan already uses for landmass groups: each window's group median is subtracted to remove "any offset between landmasses, such as unwrapping jumps across rivers" (§7, standardisation step 1). A step shared by a whole component shifts all its pixels alike and is removed by that subtraction. A pixel outside its group's main component (a small island of pixels unwrapped separately) is still rejected. The label-0 part of the rule is unchanged.
2. **2026-10-08, decoy-run draw counts (§13 step 4). No NYC result seen.** The plan does not fix draw counts for the decoy, whose only purpose is to check the code end to end.
   - **Full counts, as in the real run:** the primary analysis (999 null draws, 2,000 bootstrap resamples), secondary 8 and secondary 9.
   - **Reduced counts:** the other secondary analyses use 199 null draws and 199 resamples; the random forest uses 16 and 16. The random forest alone would take about a day at full counts.
   - **Unchanged:** every code path. The real run uses the full counts of §9–§12 everywhere.
3. **2026-10-08, code error found by the decoy run (§13 step 4): bootstrap block labels. No NYC result seen.**
   - **Error:** the refit bootstrap passed the 2 km block labels to its worker processes as pandas' pyarrow-backed string array. The array arrived corrupted in the workers.
   - **Before:** the decoy run stopped at the start of secondary 1's bootstrap with a segmentation fault in one worker and an out-of-range row index (549,756,596,579 for 815,916 rows) in another. A standalone rerun failed the same way within a minute ("Wrapping 292_22�3 failed").
   - **Fix:** the workers receive integer block codes numbered in label order. Each resample is therefore the same as with intact labels.
   - **After:** secondary 1's 199 resamples finish (276 s). The decoy primary's first 32 resamples reproduce the saved ones exactly, so its bootstrap was not affected.
   - **Unchanged:** the rest of the decoy run. The bootstrap is the only step that sends block labels to workers; the within-block permutation uses them in the main process. The run resumed with the analyses not yet finished.
4. **2026-10-08 to 10, real run stopped in secondary 8; resumed unchanged (§13 step 5). The primary result had been seen (p = 0.418); no secondary result existed.**
   - **Before:** the real run finished the primary analysis (16:49:41) and stopped at 16:52:39, early in secondary 8's free permutations. A worker raised "x is neither increasing nor decreasing" inside `roc_auc_score`, on a score vector that the same code path had handled for every earlier draw. No secondary 8 output was written.
   - **Diagnosis: a suspected memory fault in the project PC, not a code error.**
     - Rerunning draws 0–399 alone with the same code gave no error.
     - Draws 400–1,999 failed differently: an out-of-range row index of 549,755,967,131 = 2^39 + 153,243.
     - The decoy crash in deviation 3 had the index 549,756,596,579 = 2^39 + 782,691. Both are a valid index with bit 39 set, and the corrupted text "292_22�3" fits the same flip.
     - The PC is a laptop with non-ECC memory (no error reporting), running at 95–99 °C under load. A userspace memory test was started but stopped before it reported, so the fault is not confirmed.
   - **Consequence for deviation 3:** the pyarrow diagnosis there may have been this fault instead. The fix (integer block codes) changes no resample and stays.
   - **Change:** none to code or counts. The code hashes in `CODE_REAL_RUN.sha256` were checked unchanged, and the run was restarted on 2026-10-10 with the same command. Finished analyses (the primary) are skipped; the rest run from the start.
   - **Risk and check:** the flip is silent for floating-point values (a relative change of at most about 1e-4) and for most other data, and crashes integer indices. A later crash of this kind leads to the same restart, logged here. The primary result was computed before any crash; it can be checked by recomputing its observed fits and draws (all seeded) and comparing them exactly.

5. **2026-10-10, Codex resume after secondary 2's bootstrap crash. NYC primary and secondary results had been seen.**
   - **Before:** secondary 1 finished; secondary 2 (200 m) stopped at 21:50:55 Cairo time while `boot_rep` computed ROC AUC, with `ValueError: x is neither increasing nor decreasing`. No completed secondary 2 result exists. This traceback does not establish a hardware diagnosis; the suspected memory fault of deviation 4 remains unconfirmed.
   - **Authorization:** the user instructed Codex to resume. Completed primary, secondary 1, secondary 8 and all ten secondary 9 results are retained; the model script already skips their result files.
   - **Execution environment:** Codex's restricted session exposes no CUDA device. `nyc_lib.VariogramNull` now selects NumPy/SciPy when CUDA is unavailable, using the existing operations, fields, seeds, smoothing candidates, and draw order. CUDA remains the preferred backend when available. Models, features, windows, folds, null definitions and draw/resample counts are unchanged.
   - **CPU validation:** recomputed the first seed-2027 draw for the primary and 200 m analyses from their fingerprint-matching fields. Both choose the saved GPU draw's smoothing k=169. The primary matches exactly after float32 storage; the 200 m draw's maximum absolute difference is 5.960464477539063e-08 (within the stated 5e-7 absolute/relative tolerances). Evidence: `out/models/restart_20261010/CPU_VERIFICATION.json`; the original backend source is retained as `nyc_lib_before.py` there.
   - **Restart:** `scripts/resume_real.py` launches `scripts/11_models.py raw out --real --jobs 16`, logs to `out/models/codex_resume.log`, and writes `out/models/restart_20261010/status.json`. It does not suppress failed draws or change their seeds. Previously completed outputs are hashed before launch and checked again before report generation.
   - **Original budget retained:** the secondary-analysis deadline is 2026-10-15 16:27:20 Africa/Cairo, seven days after the initial real run. The supervisor stops unfinished work at that deadline and generates the existing report with missing results marked not run; it also generates the report if the run finishes normally. A crash stops the supervisor for inspection.
   - **Provenance:** resumed source hashes are in `out/models/restart_20261010/CODE_RESUME.sha256`. The frozen plan and completed result files are preserved. Recomputing the primary fits and draws to address the suspected memory fault is still pending.

6. **2026-10-10, baseline CPU execution after the first Codex restart failed. NYC results had been seen.**
   - **Before:** the jobs=16 restart stopped at 23:41:08 Cairo time, during secondary 2's null draws, with a worker SIGSEGV inside NumPy's `argsort` called by `average_precision_score`. It did not produce any new completed analysis. Traceback retained in `out/models/codex_resume.log`.
   - **Execution change only:** the model subprocess now receives `NPY_DISABLE_CPU_FEATURES=X86_V3` and `OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=OMP_NUM_THREADS=1`. This uses baseline NumPy CPU dispatch and limits each BLAS/OpenMP worker to one thread; jobs=16, scientific algorithms, packages, seeds, counts, and the original deadline are retained. The suspected hardware fault is still unconfirmed; a sorting/library execution problem is also possible. This is an execution workaround, not a diagnosis.
   - **Checks before restarting:** 8 workers each passed 12 sorting/metric integrity checks on 502,812-row synthetic arrays, including reversed arrays and tied scores (`sorting_baseline.log`). On the real primary data, both observed model fits, 16 null draws spanning 0–998, and the first 16 bootstrap resamples reproduce the saved metrics within 1e-12 absolute tolerance (`METRIC_VERIFICATION.json`). These checks preserve the existing outputs and do not tune any statistical choice.
   - **Primary integrity check:** after the remaining analyses finish, or their original budget expires, the supervisor recomputes the primary's observed metrics, all 999 null draws and all 2,000 bootstrap resamples, comparing them against the saved outputs and requiring the primary p-values to agree. It writes `FULL_PRIMARY_VERIFICATION.json` and generates the final report only if verification succeeds. A failure is logged and stops processing; no failed draw is discarded.
   - **Provenance:** baseline restart code/evidence hashes are in `out/models/restart_20261010/CODE_RESUME_BASELINE.sha256`; the earlier restart manifest remains intact. The frozen plan and previously completed results remain protected by `COMPLETED_BEFORE.json`.

7. **2026-10-11 (Cairo), restart with eight workers and calculation checkpoints. NYC results had been seen.**
   - **Before:** the baseline-CPU, jobs=16 attempt stopped at 23:47:19 on 10 October during secondary 2's null calculations. `average_precision_score` encountered index 549,756,137,364 for 502,812 rows. This is 2^39 + 323,476; the lower index is valid. Disabling X86_V3 did not prevent the failure. The hardware-versus-library cause remains unresolved.
   - **Authorization and execution change:** the user instructed Codex to start. Parallelism is reduced to eight workers, including the later full primary integrity check. Models, input data, seeds, draw/resample counts, folds and decision rules are unchanged; the original 15 October deadline still applies. Lower parallelism may leave the random forest unfinished, which the existing report will disclose as not run.
   - **Interrupted calculation recovery:** `11_models.py` now persists each completed null draw and bootstrap resample atomically, with a seed and checksum. Cache directories are fingerprinted from fields, the model specification, baseline inputs, outcomes, folds, risk sets, block codes, counts and source code. A raised exception is not converted into a result or discarded draw. Restarting reuses completed calculations for the same fingerprint and recomputes the missing seeds.
   - **Existing completed null tables:** a saved table is reused only if its size/columns/finite values are valid and 16 uniformly spaced seeded draws reproduce its metrics within 1e-12 absolute tolerance. Its fingerprint, file hash and checked seeds are recorded; subsequent use requires both fingerprint and file hash to match. Parsing uses round-trip floating-point precision. Original null-draw functions and bootstrap functions are unchanged.
   - **Validation:** the primary's observed metrics and sampled draws were compared with their saved values using the checkpoint path before launch (`metrics_checkpoints.log`, `metrics_checkpoints_repeat.log`). Both attempts detected a mismatch, so the eight-worker production run was not launched; see deviation 8. Previously completed result files and the frozen plan remained unchanged. Source/evidence for this attempted restart is retained in the logs and verification checkpoint directories.
   - **Monitoring:** `status.json` includes completed calculation counts. The later full primary check also checkpoints its verification calculations, so an interruption can resume without replacing the original primary result. No full primary integrity claim is made until that check succeeds.

8. **2026-10-11 (Cairo), four workers and repeated numerical calculations after consistency checks failed. NYC results had been seen.**
   - **Before:** the first checkpoint validation differed from the saved primary null at draw 864 (PR AUC difference 3.10682816e-10, and a ROC AUC difference). A fresh validation reproduced that draw but differed on another sampled draw. The failed verification checkpoint records and both logs are retained. No original primary result or null table was replaced. These failures show that the execution problem can affect numbers without crashing; they do not establish its hardware or software cause.
   - **Execution checks:** observed metrics and each new seeded null/bootstrap calculation must now produce two agreeing results within 1e-12 absolute tolerance, in at most six attempts at the same seed. Known out-of-bounds/non-monotonic errors are recorded and the identical calculation is retried; unrelated exceptions still stop processing. Input array hashes are checked before and after every attempt. Completed checkpoints contain their attempt records and a checksum, and are reused only under the identical field/data/model/source fingerprint. No new Monte Carlo seed is substituted, no failed seed is removed, and statistical draw counts and definitions are unchanged.
   - **Validation:** with four workers, the repeat-checked primary observed metrics, 16 sampled null draws and 16 bootstrap resamples reproduce their saved metrics (`metrics_repeat_checked.log`, `METRIC_VERIFICATION.json`). This is a sampled integrity check; the full check remains required before the final report. Source/evidence hashes: `out/models/restart_20261010/CODE_RESUME_REPEAT.sha256`.
   - **Production restart:** `resume_real.py` now uses jobs=4, while retaining baseline CPU dispatch, one BLAS/OpenMP thread per worker, the original seeds/counts, protected completed results, and the original seven-day deadline. Repeated calculations and reduced parallelism increase runtime; any secondary analysis not finished by that deadline remains explicitly not run. The full primary check also uses four workers and independently stored verification checkpoints.

   - **Bounded recovery:** `watch_real.py` can restart the identical four-worker command from verified checkpoints at most three times after a worker segmentation fault, out-of-bounds index or non-monotonic metric error. Each restart is recorded in `AUTOMATIC_RESTARTS.jsonl`. It does not retry failed full-primary verification, changed inputs/checksums, unrelated errors or an exhausted budget. Source hash: `WATCH_CODE.sha256` in the restart directory.

9. **2026-10-14 (Cairo), execution moved to a new PC; sixteen workers; BLAS kernel pinned to the old PC's. NYC results had been seen.**
   - **Before:** every restart of deviations 5–8 failed within minutes on 10–11 October (worker segmentation faults; the same seed failed five times with index 2^39 + 195,577). The old laptop (i9-10980HK, 64 GB non-ECC, 95–99 °C under load) was retired. Nothing ran from 2026-10-11 00:25 until this restart. Completed then: the primary, secondaries 1, 8 and 9 (all ten seeds), and for secondary 2 its 999 null draws and 389 of 2,000 bootstrap resamples (seeds 0–388, checkpointed).
   - **New PC:** Dell Precision 5820 Tower, i9-10900X (10 cores, 20 threads, AVX-512), 64 GB non-ECC (the kernel reports ECC disabled), NVIDIA RTX 3090 24 GB. No memory test was run (none was available without administrator access); the repeat checks of deviation 8 stay on. The Python 3.12.7 environment has the same packages as the old PC (identical `pip freeze`).
   - **Copy verified:** the frozen plan, the code hashes in `CODE_RESUME_REPEAT.sha256`, every data manifest of §15 (checkpoint 2, InSAR, decoy, PLUTO archive, static layers, frozen inputs), the completed-result snapshot `COMPLETED_BEFORE.json` (45 files) and the checksum of every secondary 2 checkpoint all match. The only manifest lines that differ are the code changes of deviations 5–8.
   - **CPU difference found before launch:** on this CPU OpenBLAS uses its SkylakeX (AVX-512) kernel; the old laptop used Haswell. With SkylakeX, the primary's observed metrics and 16 sampled null draws match the saved values within 1e-16, but of the first 64 bootstrap resamples 9 differ in ROC AUC (up to 1.24e-07) and 3 in PR AUC (up to 7.9e-10), outside the full primary recheck's 1e-12 tolerance. With `OPENBLAS_CORETYPE=Haswell` all of them match within 1e-16. These are rounding differences in the logistic regression fits; no calculation failed. Evidence: `out/models/restart_20261010/newpc_20261014/repro_*.log`.
   - **Execution changes only:**
     - `OPENBLAS_CORETYPE=Haswell` is added to the run's environment, so new calculations use the old PC's BLAS kernel and secondary 2's remaining resamples are computed as its first 389 were.
     - `NPY_DISABLE_CPU_FEATURES=X86_V3` (deviation 6) is kept. On this CPU NumPy's X86_V4 (AVX-512) dispatch stays enabled, so it is not the baseline dispatch described in deviation 6; the check above ran with this setting.
     - Workers go from 4 to 16 in `resume_real.py` and in the full primary recheck (`verify_metrics.py`).
     - The old PC's verification checkpoints (16 null draws, 16 resamples) are moved to `newpc_20261014/oldpc_verification_checkpoints_f9a6f849/`, so the full primary recheck recomputes every value on the new PC.
     - **Unchanged:** `11_models.py` and `nyc_lib.py` (so the secondary 2 checkpoints stay valid), repeat checks, seeds, draw and resample counts, models, folds, nulls and decision rules.
   - **Deadline:** the original budget is kept. Secondary analyses stop at 2026-10-15 16:27:20 Africa/Cairo, and unfinished ones are reported as not run. About 3.9 days of the budget were lost to the failures and the move, so the random forest (secondary 3) cannot finish. An extension would need the supervisor's agreement and would be logged here.
   - **Provenance:** `out/models/restart_20261010/CODE_RESUME_NEWPC.sha256` (`038664ee…`), with the machine record `newpc_20261014/MACHINE_NEWPC.txt`. The run is launched with `scripts/resume_real.py` and appends to `out/models/codex_resume.log`.

10. **2026-10-15 (Cairo), secondary 3 (random forest) completed after the compute budget. All NYC results had been seen, including the report.**
   - **Before:** the §13.6 budget expired at 2026-10-15 16:27:25. The random forest then had 383 of its 500 null draws and none of its 500 bootstrap resamples, and `NYC_RESULT.md` reports it as not run (§15).
   - **Change:** at the user's instruction, the random forest is run to completion after the budget, with `scripts/11_models.py raw out --real --jobs 16 --only s3` and the execution environment of deviation 9. It resumes from its saved checkpoints (fingerprint `d8a54c14…`). The code is unchanged (`CODE_RESUME_NEWPC.sha256`). The model, seeds, counts (500 null draws, 500 resamples) and the primary null are as frozen (§12.3).
   - **Status of the result:** it carries no decision (§11, §12) and is not part of the budgeted run. Wherever it is reported, it is labelled "completed after the compute budget". `NYC_RESULT.md` and its §15 record stay unchanged as the report of the budgeted run; the random forest result goes into a separate addendum.
   - **No deadline** (user's instruction): the run continues until all 500 null draws and 500 resamples are done. It started 2026-10-15 at about 17:08 Cairo time and reused the 383 saved null draws.
   - **Not used:** `resume_real.py`. Its deadline has passed, so it would skip the model and rebuild the report.
   - **Log:** `out/models/s3_postbudget.log`.
   - **Outcome:** finished 2026-10-16 20:44:37 Cairo; PR AUC change +0.000031, p = 0.052 (500 draws), direction opposite. Recorded in §15 and `out/models/real/NYC_RESULT_S3_ADDENDUM.md`.

## 15. Freeze record

- **Plan approved by:** the supervisor, on 2026-10-08. While the supervisor was unreachable, the design was also reviewed with two AI assistants (ChatGPT and Claude); see §16.
- **Frozen copy:** `freeze/NYC_REPLICATION_PLAN_frozen.md`, saved 2026-10-08T05:44:48Z, SHA-256: `59a2aa1a573ce8b7cf7ede7fd1e870bea2768c259978c716872f177041588a5d`
- **Checkpoint 2, filled in after freezing** (2026-10-08, `scripts/04_grid_domain.py`; outputs and report in `out/checkpoint2/`; no InSAR value read):
  - events counted under §6: **65** at 250 m. They form 64 risk sets, because NYC110 and NYC111 (2018-05-13, same tax block) share a cell and a date (§8). The 200 m count, 70, is reported only.
  - primary population: **the older-building domain** (65 ≥ 30), with 5,001 eligible 250 m cells. The whole of NYC (10,320 eligible 250 m cells, 79 events) is secondary analysis 1.
  - `out/checkpoint2/MANIFEST.sha256` (script, cell tables, event-cell tables, report): `a7aa55a1ec3ee5792cab805824e1712e5a2cb960390cd087a37746cec87265c6`
- **Checkpoint 2, completed after freezing** (2026-10-08, `scripts/05_download_pluto.sh`, `06_features.py`, `07_lock_and_hash.sh`; outputs in `out/checkpoint2/`; no InSAR value read):
  - **PLUTO releases:** the 25 releases labelled 2016–2022 in DCP's archive (16v1 to 22v2; no 18v2 plain zip or 22v3 exists), downloaded 2026-10-08, hashed in `raw/pluto_archive/MANIFEST.sha256`. Release dates (newest CSV in the archive) run from 2016-03-30 (16v1) to 2022-08-11 (22v2) and are listed in `pluto_releases.csv`. Every release has NumBldgs and YearBuilt, so no substitution was needed. The 82 events from 2017-07-16 use 20 different event PLUTOs, 16v2 to 22v1 (`event_pluto.csv`).
  - **Features:** 10,320 eligible cells at 250 m and 15,438 at 200 m (`features_<res>m.csv`). Missing inputs at 250 m: old_share_1975 9 cells, height_m 7 cells (200 m: 6 and 4). Time-varying building count and median year built per release and cell: `pluto_cells_<res>m.csv`.
  - **Fold maps:** 254 blocks of 2 km; 177 eligible 250 m cells hold one of the 185 events (178 at 200 m). Five folds of 2,064 cells at 250 m, with 35–36 event cells each (`folds_<res>m.csv`).
  - **Event sample:** `event_sample_<res>m.csv`, with 65 domain cases and 79 whole-NYC cases at 250 m (70 and 80 at 200 m).
  - **Lock files:** `LOCK_venv.txt` (Alex/.venv; CuPy 14.2.0 was added on 2026-10-08 so the variogram null can run on the GPU, as a speed-up only), `LOCK_opera.txt` (conda env with opera-utils 0.25.8), `LOCK_machine.txt`.
  - `out/checkpoint2/MANIFEST_PART2.sha256` (scripts 05–07, PLUTO archive manifest, releases, event PLUTO, features, folds, PLUTO cell tables, event samples, lock files, part-1 manifest): `3049dada2e8743b57c9861bf48c4ec0bdea7303249107a38b550c52255120d2e`
- **InSAR, §13 step 3** (2026-10-08, `scripts/08_download_refpoint.py`, `09_insar_velocities.py`, `10_insar_checks.py`, `nyc_lib.py`; report `out/insar/INSAR_CHECKS.md`; no InSAR value compared with events):
  - **Windows:** 77 one-year, 60 two-year and 42 three-year windows (the distinct dates of the 82 events from 2017-07-16, 2018-07-16 and 2019-07-16), plus the full period. Connected components follow deviation 1 (§14).
  - **Sign check: pass.** The 19 LaGuardia runway cells with a value have a median full-period line-of-sight velocity of −2.27 mm/yr. The median of the eligible 250 m cells is −1.46 mm/yr.
  - **Coverage:** in 1-year windows, 76.8% of the pixels in eligible 250 m cells are valid (median over windows). The construction mask removes 16.0%. Eligible 250 m cells with a value range from 10,042 to 10,320 per window; domain cells from 4,906 to 5,001.
  - **Raw window velocities** carry large window-wide offsets and spreads: medians from −36.6 to +36.0 mm/yr and IQRs from 2.7 to 30.4 mm/yr in 1-year windows. The §7 standardisation removes these as planned.
  - **Variogram check:** 20 windows (seed 7) against the primary null's 999 surrogates (seed 2027).
    - Lags 1–16 cell widths: inside the 95% range at 194 of 320 window-lags. The surrogates are rougher than the field at 250 m (median 1.69× the observed) and close to it at 0.75–4 km.
    - 1 km bins from 4 to 20 km: inside at 79 of 320. Beyond 5 km the surrogates carry 45–90% of the observed semivariance.
    - The primary null is unchanged (§10).
  - **Analysis structure:** to build the null, the check computed the primary analysis's windows and union cells. That step needs the event dates and cells and whether each event cell has a window value, but compares no InSAR value with outcomes. Event counts and losses appear only with the results.
  - **Code fixes before the decoy run** (from an independent read-only review of scripts 09–11 on 2026-10-08; no result had been computed):
    - a crash in the check's report;
    - Baseline 2 drops a whole risk set when the event cell lacks a building age;
    - cached surrogates carry a fingerprint of their field, so a stale file is never reused;
    - the amplitude-adjusted MSR's last remap uses each window's observed values.
  - `out/insar/MANIFEST.sha256` (scripts 08–10, `nyc_lib.py`, the reference-point manifest, all InSAR outputs and the primary surrogates): `bbd5f50a581d64d6085fc9318a581f2d1fba6d0b66836e942c5d56a7c270d36b`
- **Decoy run, §13 step 4** (2026-10-08, 09:50–16:26; `scripts/11_models.py --decoy --quick 199 --quick-rf 16`; report `out/models/decoy/DECOY_REPORT.md`; no real outcome used):
  - **Decoy:** the 185 events moved to random domain cells at 250 m (seed 99), keeping their dates. All 185 decoy cells are domain cells.
  - **Completed:** every analysis of §11 and §12.
    - Full counts: the primary (999 null draws, 2,000 resamples), secondary 8 and secondary 9.
    - Reduced counts (§14 deviation 2): 199 draws and resamples for the other secondary analyses; 16 for the random forest.
  - **Code error found and fixed:** the bootstrap's block labels (§14 deviation 3). The run stopped once at secondary 1's bootstrap and resumed with the unfinished analyses after the fix.
  - **Outputs behave as a fake outcome should:**
    - Primary PR AUC change +0.000014, variogram-matching p = 0.153. The other five nulls give p = 0.12–0.16.
    - Secondary analyses: p = 0.09–0.88. The ten fold seeds: p = 0.10–0.52.
    - Every null and bootstrap draw has a value, and the null distributions centre near zero.
  - **Timings that set the real run's schedule:**
    - Primary: 44 min.
    - Each random-forest null draw: about 40 min on one core; each random-forest resample: about 80 min. At full counts (500 and 500 on 16 cores), the random forest alone needs about 2.6 days of the 7-day budget.
  - **Report script revised after the decoy** (from an independent read-only review against §9–§12; no real result existed). Before, `12_report.py`:
    - said "largest p across the six nulls" even when secondary 8 was missing;
    - dropped missing fold seeds silently, and showed only PR AUC for them;
    - cut the variogram check to its summary bullets;
    - did not state the sign convention behind the direction label;
    - did not report missing-input counts or event drops for the secondary analyses.
    
    Now each is reported. The real report also refuses to build unless the primary null has 999 draws. The decision rule and every computed number are unchanged.
  - `out/models/decoy/MANIFEST.sha256` (report, decoy events, results, null and bootstrap draws, event logs, run log): `57390ac74bd7633328f25ca6e8f81c065258bb1f553e9312779769178946a5fe`
- **Code for the real run, hashed before it starts** (`out/models/CODE_REAL_RUN.sha256`: `39e85bdb3ad81ef08bff1e3e2ae49918b8650ecfc9d5cd2333c69acf40953a3d`):
  - `scripts/nyc_lib.py` `4ab32839…` (unchanged since the InSAR stage);
  - `scripts/11_models.py` `b8ce5629…`;
  - `scripts/12_report.py` `1e572ccd…`;
  - the primary surrogates (unchanged since the InSAR stage).
- **Real run, §13 step 5: result** (started 2026-10-08 16:27:20 Cairo; interruptions and execution changes in §14 deviations 4–9; analyses stopped at the budget deadline 2026-10-15 16:27:25; report built 16:50:45):
  - **Decision (§11): not replicated, with opposite deformation direction.** Primary PR AUC 0.000231 → 0.000227 (change −0.000004; 95% refit-bootstrap interval −0.000021 to +0.000023); variogram-matching p = 0.418 (999 draws). Direction: median standardised difference +0.037 (47% of risk sets below 0), raw line of sight −0.72 mm/yr, velocity coefficient −0.016. Largest p across the six nulls: 0.481 (within-block permutation).
  - **Completed:** the primary, secondaries 1, 2, 4–9 and 11–15 (secondary 10's metrics are reported for every analysis). Every secondary PR AUC p is ≥ 0.097 (lowest: secondary 14, availability only, whose own-risk-set top-10% change has p = 0.041; no decision is attached to secondaries, §12).
  - **Not run:** secondary 3 (random forest). The budget expired with 383 of its 500 null draws and none of its 500 resamples done; those checkpoints (`checkpoints/s3/d8a54c14…`) are kept but not used or reported.
  - **Full primary recheck: passed** (`out/models/restart_20261010/FULL_PRIMARY_VERIFICATION.json`). On the new PC, the observed metrics were recomputed exactly; all 999 null draws and all 2,000 bootstrap resamples agree with the saved values within 1e-16 (tolerance 1e-12); the four primary p-values are identical. The saved primary result was therefore not affected by the old PC's suspected memory fault. The recheck used a fresh checkpoint fingerprint (`3cd9eedb…`); the old PC's verification checkpoints (deviation 9) predate the final code of deviation 8, so they would not have been reused in any case.
  - **Previously completed outputs** (`COMPLETED_BEFORE.json`, 45 files) were verified unchanged at the end of the run.
  - **Hashes:**
    - `out/models/real/NYC_RESULT.md`: `0b0b2e8b61bac2945eeb1c16c788a42bf8a5c33afa11face66c5ca0c656e8ef9`
    - `out/models/restart_20261010/RESULT_MANIFEST.sha256` (23 result files, all null and bootstrap tables, the report): `1ef6d9c1fa2a3b7357b79ead2142d05fe8083f5e1bb38560bd7ba436ea80183f`
    - `out/models/restart_20261010/FULL_PRIMARY_VERIFICATION.json`: `7ea268e96b6b814692407450247f24934cf9b08ef34ce9803b2f031de45ce33e`
    - `out/models/REAL_RUN_MERGED.log` (merged record of `real_run_live.log`, `real_run.log`, `codex_resume.log` and the new-PC supervisor log; the sources are unchanged): `bd23d5b100c937ceb8f903680f342f10adb15fd3594413347a356caae442d55b`
  - **Reproduction:** the report's command line omits the execution environment. Rerunning on another CPU needs the settings of deviations 6 and 9 (`OPENBLAS_CORETYPE=Haswell`, one BLAS thread per worker), as in `scripts/resume_real.py`.
- **Secondary 3 (random forest), completed after the compute budget** (§14 deviation 10; all NYC results had been seen; no decision attached; `NYC_RESULT.md` and the record above are unchanged):
  - **Finished** 2026-10-16 20:44:37 Cairo (`out/models/s3_postbudget.log`, ALLDONE, no errors). All 500 null draws were computed on the new PC (2026-10-15 03:00–21:06, `OPENBLAS_CORETYPE=Haswell`); all 500 resamples returned a result.
  - **Result:** PR AUC 0.000213 → 0.000244 (change +0.000031; 95% refit-bootstrap interval −0.000065 to +0.000623); variogram-matching p = 26/501 = 0.052 (500 draws). ROC AUC 0.451 → 0.469 (p = 0.395); top-10% pooled −0.016 (p = 0.120); top 10% of own risk set +0.000 (p = 0.052). Direction: opposite (+0.037, the same rows and field as the primary analysis).
  - **For reading it:** both random-forest ROC AUCs are below 0.5 (the primary logistic regression gives 0.533 and 0.530). It is one of 12 secondary analyses with a result, none with a decision and none corrected for multiple comparisons.
  - **Report:** `out/models/real/NYC_RESULT_S3_ADDENDUM.md`, built by `scripts/13_s3_addendum.py out --real`.
  - **Hashes:**
    - `out/models/real/NYC_RESULT_S3_ADDENDUM.md`: `3adca43bfb834f97b70580f9cbe95b8408ddbdd6d3bdc79350ddcd4823243108`
    - `out/models/real/result_s3.json`: `b0064d94337f2c85e8ad7391045c653019a3c47909c7c2848e3588a407c58762`
    - `out/models/real/null_s3.csv`: `d4ec654ec11ee14a676cd96909d68f2610c727b57faf843e5339bd32444e6fc4`
    - `out/models/real/boot_s3.csv`: `58e2118e2a3cbe158930a01e55eb640fdc60fc0a1113478512a664674c8a399e`
    - `scripts/13_s3_addendum.py`: `b807bc096ab4099eb60d162ae550a08d84ece968cad4bc735e5b28400928c55d`
- Inputs frozen on 2026-10-07:

| File | SHA-256 |
|---|---|
| `raw/incidents.csv` | `0467527086adf60f05c7252de94b5f8a4d3d55fa10f325df07511959c6fb8750` |
| `out/events_clean.csv` | `2653a605baa22640485baa640af03ec141edbbc9be4acfe196d1f9e0e97238ac` |
| `out/events_final.csv` (185 events) | `dccefeb082f159f242f235af5f8f6d3d845016d2a3a8b94be9373514ae6251cb` |
| `scripts/01_audit_events.py` | `15094c34be5b4868368773d65f1ca488568e1d2df395ac3c6082814acc124264` |
| `scripts/02_freeze_events.py` | `96655837cf0dcfcc58ef3934765acb39c3edd97bd0d8ee6cbcba600eced1cb4a` |
| `raw/geosearch.json` | `a932901ba932a33348477f3ea087629740cb0e6e95d895b27762bce3a9a41afe` |
| `raw/pluto.json` | `ce2168b5b041f1716a47b25a296ae14b1cf09f394ebbb444f8d2a7c5e108e3d0` |
| `raw/permits_blocks.json` | `be3bab95b31c538ec6fa0005e9f531b9ac78962cb9d7367830960a9156395cb1` |
| `raw/opera/MANIFEST.sha256` (SHA-256 of 172 DISP-S1 granules, secondary dates 2016-09-26 to 2022-08-26, + STATIC F08622; added 2026-10-08) | `3237a1688ac7006efd33fcea5dcdfb6e80bd7e83244ef909b085d0b64d9f9fe5` |
| `raw/STATIC_MANIFEST.sha256` (raw open layers: PLUTO 15v1, borough boundaries, WSF, GHSL, FABDEM, OSM, permits 2013–2022, Ohenhen NYC; added 2026-10-08) | `6014cdc4d74a78b1ac9e329a1be4d7f64558408f7f3a3c9668c7b0a8efb86d3a` |
| `scripts/03_download_static.sh` | `08bc1a71d9dbeae051a8b672e6e394154fdbb5d39516504ebd2ff8dd57ba2518` |

## 16. Revisions before freezing

**First review (2026-10-07).** An independent methods review of the first draft led to these changes. All were made before any NYC InSAR or model existed:
1. **Construction mask** for every cell (§7). Before, only cases were screened for nearby works.
2. **Shared surrogates** across windows (§10). Independent surrogates per window would make p too small.
3. **Annual terms** in the window velocity, plus per-pixel completeness rules (§7).
4. **Window standardisation** and winsorising, and a defined bootstrap unit (§7, §9).
5. **DISP-S1 rules** fixed: re-referencing per window, connected components, layer choice, a pinned opera-utils version, and the LaGuardia sign check (§7).
6. **Controls** may include cells with later events (risk-set rule). Before, every cell with an event at any date was excluded, which used future outcomes. The never-case rule became secondary (§8).
7. **Landmass-group referencing** and long-lag variogram checks (§5, §7, §10).
8. **One PLUTO release from 2015** for building count, age and the domain, replacing building footprints made after the events (§5, §9).
9. **Checkpoint hashing**, the primary null for secondary analyses, decoy positives, and an explicit "runs regardless" rule (§12, §13).
10. **Direction and largest-p reporting** beside the decision (§11).
11. **Compute budget** and sparse storage (§10, §13).
12. **Factual fixes:** the event-freeze step is scripted and hashed; the 2017-07-16 cutoff is stated; the LiCSAR period is restated; the top-10% definition is clarified.

**Second review (2026-10-08).** While the supervisor could not be reached, the design was reviewed with two AI assistants; the supervisor then approved the revised plan. These changes were made before any InSAR value was computed and before the domain's event count was known:
1. **Freeze record:** a frozen copy of the plan with its SHA-256, and checkpoint results recorded after freezing (§13, §15).
2. **30-event switch** for the primary population, written before the count (§6).
3. **First event per cell:** a cell with an earlier event is neither a case nor a control. The earlier rule becomes secondary 7 (§8, §12).
4. **Event-specific PLUTO** releases for building count and age. Eligibility, the domain and the event count stay on PLUTO 15v1 (§5, §9). Lots are placed by PLUTO's XCoord/YCoord, since the 2015 release has no lot polygons.
5. **Line of sight** kept, with no vertical projection. The variable is named line-of-sight ground deformation, and the sign check is in line of sight (§7). The old secondary 7 (line of sight vs vertical) is dropped.
6. **Incremental-value replication and directional concordance** are reported as separate labels, with a defined direction measure and raw line-of-sight medians (§11).

## 17. After the replication: next study (not part of the preregistration)

Added 2026-10-10, after the primary result was known. Nothing here changes §1–§16 or the NYC run; this work starts only when the NYC real run and its report (§13 step 5) are finished.

**Supervisor's request (2026-10-10, on the 7 October brief "Candidate Coastal-Region Research Cases"):** download every dataset named in the brief, and choose a deep-learning algorithm to link satellite data with predicting collapses in coastal cities.

**Outcome confirmed by the supervisor (2026-10-15):** "الانهيارات الأرضية" here means building collapse, not ground failure (landslides, sinkholes). This matches the brief's building outcomes (dangerous-building orders, unsafe structures, collapses).

**Steps, in order:**
1. **Two cities beside NYC: Hong Kong and Miami-Dade.** Chosen from the files already downloaded (2026-10-07) and the brief:
   - **Hong Kong, main case:** about 1,320 buildings with Section 26 dangerous-building orders and 80 with Section 26A building-defect orders, each with latitude and longitude; official building records with age, type and use. It has the most labels. Whether they are enough for a deep-learning model depends on the final usable sample, its spatial grouping and missing data, not on the count alone (2026-10-17). S26 orders ("dangerous buildings") and S26A orders ("investigation of building defects") stay separate labels, and neither is called a collapse. How many of them relate to ground movement is unknown.
   - **Miami-Dade, second case:** unsafe-structure cases with an open date and a folio number, which places each case on its parcel; the county's property records give building age and use. Florida lies in OPERA DISP-S1's North American coverage, so a ready-made InSAR time series and the NYC code can be reused (the frame and its dates are to be confirmed). The barrier-island Sentinel-1 series in the brief (2016–2023) is a second InSAR source.
   - **Mumbai, reserve:** it replaces Miami-Dade if Miami-Dade fails its check (step 2). Its C-1 lists are annual (2018–2020 and 2023–2026 located, 2021–2022 missing), are PDFs of addresses that would need geocoding, and the public InSAR is one static velocity map (2015–2023).
   - **Lagos, not used:** the catalogue holds 106 collapses from 1978 to 2022 with street addresses; 22 are from 2015 on and about 8 fall after the public InSAR starts (2018–2021, one static velocity map). That is too few to train or test a model.
   - **NYC:** ~~the finished replication serves as an external test~~ (changed 2026-10-17 after the GPT review). NYC is a previously analysed benchmark, not a fresh or confirmatory test: its labels and results were seen before this study was designed. Testing across cities is a cross-outcome transfer experiment, since a Hong Kong order, a Miami-Dade case and an NYC collapse are different outcomes.
2. **Download and audit the two cities' datasets in the brief.** One audit table per city: number of labels, whether each has a date and coordinates, InSAR type (a static velocity map or a time series), years of InSAR before the events, overlap between labels and InSAR, and the building layers.
   - **Miami-Dade's check:** the unsafe-structure cases can be exported in bulk, with open dates, and at least 100 cases from 2017 on fall inside the InSAR coverage. If not, Mumbai is audited in its place.
3. **Hong Kong order dates, checked first.** The current file (updated 2026-09-07) gives cumulative order counts per building, with no issue dates. If the monthly snapshots since May 2023 are still available, each building's order date is the first month it appears. If not, the design falls back to "orders by 2026" against earlier InSAR, and this is stated as a weakness.
4. **InSAR time series for Hong Kong:** Sentinel-1 interferograms from ASF HyP3 (free, using the existing Earthdata login), then a MintPy time series, giving an X × Y × time stack before each order.
5. **Choose the deep-learning model from the data shape:**
   - static velocity maps only: a small CNN on multi-channel patches (velocity plus building layers);
   - a real time series: a temporal CNN, LSTM or ConvLSTM. Spatial attention is added only if it beats a plain ConvLSTM by a margin worth reporting.
6. **Same safeguards as NYC:** a written and frozen plan before labels and InSAR are linked; folds of spatial blocks; logistic regression and random forest as baselines on the same folds; a spatially realistic null; a decoy run.

**Review 2026-10-17 (GPT, through the user; agreed):** no predictive training yet.
- **Miami-Dade first:** a blinded label check of about 100 cases (no InSAR values); repeat cases deduplicated by property and episode, with each property kept together in validation; coverage counted in each case's own pre-case window.
- **Hong Kong:** bounded checks only: a synthetic-signal test of the processing, a matched comparison with the NTU map, and a hand sample of order records.
- **Model:** chosen only after one city has a defensible outcome and suitable measurements. Comparison: baseline, then + a static deformation summary, then + a small temporal model, on identical samples and splits, with a measurement-availability-only baseline.
- **Wording:** HyP3 10 × 2 looks is a product of about 80 m resolution on a 40 m grid (ASF), not 40 m resolution.

**Draft research question:** does a spatiotemporal deep-learning model of InSAR deformation add predictive information about building failure in coastal cities beyond building, urban and location information, under spatially separated validation and spatially realistic null tests?

**Status, steps 2–3 (2026-10-16; the user asked to start the downloads while s3 runs; no outcome–InSAR association computed):**
- **Downloads:** `Alex/feasibility/download_hk_miami.py` → `feasibility/hongkong/` and `feasibility/miami/` (`downloads/<source>/`, with URL and SHA-256 per file in `audit/download_log.csv`). Owner, mailing and violator-name fields are left out. Audit numbers: `feasibility/audit_hk_miami.py`.
- **Hong Kong** (`feasibility/hongkong/AUDIT_REPORT.md`): 1,319 S26 and 80 S26A buildings, all with coordinates and block-ID links to 51,354 buildings. **Step 3 answer: no order dates and no monthly back copies** (data.gov.hk archive and Wayback checked), so the fallback applies: orders May 2023 – Sep 2026 against InSAR before May 2023. Sentinel-1 ascending tracks 11 and 113 from June 2015.
- **Miami-Dade** (`feasibility/miami/AUDIT_REPORT.md`): 6,667 dated unsafe-structure cases since 2017, almost all in unincorporated Miami-Dade. **The go/no-go check passes on footprint:** all of them lie inside OPERA DISP-S1 frame 12638, 2016-07 to 2026-02; coherence is still to be checked once the data are downloaded. The brief's barrier-island series overlaps only 3 cases, so OPERA is the InSAR source. Risk: the 2021–22 jump in cases follows Surfside and the recertification push, so a sample of cases must be checked before a plan is frozen.
- **Earthdata login set up 2026-10-16** (written to `~/.netrc` by Claude, with the user's permission).
- **Miami OPERA: done.** 254 granules, 11 GB, via `feasibility/download_miami_opera.sh`.
  - **Go/no-go: passes on valid pixels.** 6,527 of 6,667 cases since 2017 (4,034 folios) are valid in at least 80% of granules.
  - **Reference point:** only the 2017-11-21 one lies outside the subset; its windows come from `feasibility/download_miami_refpoint.py`. All 15 were fetched. As in NYC, the reference pixel itself has label 0 and no displacement, inside a uniform component (all 120 neighbours valid, label 1).
- **Hong Kong HyP3** (the user chose the "pre-2023 core"): `feasibility/hk_hyp3_submit.py`.
  - Track 11 ascending, bursts 021605–021607 IW3, 224 dates from 2015-06-15 to 2023-04-22.
  - 862 pairs (3 nearest dates plus about one year), INSAR_ISCE_MULTI_BURST at 10x2 looks (40 m) with the water mask: 862 credits of 8,000. All submitted 2026-10-16.
  - The test pair covered all 1,319 S26 buildings, with median coherence 0.65 at 12 days.
  - Products are fetched by `feasibility/hk_hyp3_download.py` (HyP3 keeps them for 14 days). The MintPy time series comes next (conda env `insar`).
  - **2 jobs failed** on ASF's side (burst download error, not the data): 2019-07-12 → 07-24 and 2019-07-12 → 08-05. The date keeps 5 other pairs, so the network stays connected. Resubmitted 2026-10-17 at the user's request (2 credits, 7,136 left; `hk_hyp3_submit.py --resubmit-failed`; record in `hongkong/hyp3/failed_logs/`).
  - **MintPy input:** `feasibility/hk_mintpy_prep.py` clips each product, straight from its zip, to one fixed 40 m grid: the bounding box of the 51,354 private buildings plus 1 km (UTM 49N, 1,558 × 1,063 pixels; no order data used). It writes `hongkong/mintpy/hk_T011.cfg`. Settings: tropospheric correction by height correlation (no ERA5 account), no deramping, DEM-error correction on, automatic reference point.
  - **All 862 pairs downloaded** (2026-10-17 03:00 Cairo, including the 2 resubmitted) and clipped: 224 dates, one connected network. MintPy (`smallbaselineApp.py hk_T011.cfg`, log `hongkong/mintpy/mintpy.log`) started 2026-10-17 03:05 Cairo.
  - **MintPy checks** (`feasibility/hk_mintpy_checks.py`; only coherence is read at the order buildings, no velocity): the automatic reference point fell in Shenzhen (row 29, col 775; 114.145 E, 22.551 N).
    - Run 1 (no unwrapping correction): 13.5% of land at temporal coherence ≥ 0.7; 132 of 1,389 order buildings on such a pixel (141 within 1 pixel), median 0.344; no valid pixel on the airport platform, so the sign check could not run; Spearman ρ with the NTU map 0.38 (15,794 points). Kept in `hongkong/mintpy/run1_nocorrection/`.
    - Run 2 (bridging added to `hk_T011.cfg`): 13.6% of land; 142 buildings (164 within 1 pixel), median 0.572; airport still empty; NTU ρ 0.393 (15,918 points). Valid pixels lie only in the north-west, near the reference; Tin Shui Wai shows about −2 to −4 mm/yr in the line of sight.
    - Cause: triplet closures show whole-cycle offsets of unwrapped components relative to the distant reference. Their share rises with the perpendicular baseline (0.18 below 50 m, 0.51 at 150 m or more) and is higher for wet-season dates. Inside 11 × 11 pixel urban blocks, referenced to the block itself, it falls to 1–15%.
  - **Locally referenced product** (`feasibility/hk_local_reference.py`, added 2026-10-17 before any order data were linked; commands in the script): every interferogram minus the mean of the same unwrapped component within 1 km, then inversion, DEM-error correction and velocity.
    - 30.5% of land at temporal coherence ≥ 0.7; 1,099 of 1,389 order buildings on such a pixel (1,147 within 1 pixel), median 0.914.
    - It measures motion relative to the surrounding 1 km only: settlement of a whole district (such as Tin Shui Wai) is removed.
    - NTU check with both maps referenced the same way: ρ 0.07 (25,345 points). Run 2, referenced the same way after the fact, gives 0.074, so the drop comes from removing the large-scale signal both maps share. Where both products are valid, the local product and run 2 (referenced after the fact) agree with ρ 0.61 (102,708 pixels).
    - The local values are small: 5–95% range −0.35 to 0.51 mm/yr, against −5.8 to 5.5 mm/yr for the NTU map referenced the same way. NTU's local settlement spots (below −3 mm/yr, 3,606 points) do not show in either of our products.
    - Which product, or both, enters the deep-learning study is to be fixed in that study's frozen plan before any order data are linked to InSAR values.
    - Note: `dem_error.py` writes `demErr.h5` and `timeseriesResidual.h5` under fixed names, and the local run overwrote run 2's. Both were rebuilt from `timeseries_tropHgt.h5`: the rebuilt corrected series matches run 2's within 4 × 10⁻⁷ m. The local files are now `*_local.h5`.
  - **Bounded checks after the GPT review (2026-10-17; no order data used):**
    - **Synthetic test** (`feasibility/hk_synthetic_test.py`, results in `hongkong/mintpy/synth/SYNTH_TEST.json`):
      - Setup: 34 Gaussian bowls of −5 mm/yr in the line of sight, linear in time, with widths σ = 40 m to 2.56 km. They were added to the clipped HyP3 unwrapped phase, then run through the local product's own steps: local reference, inversion, DEM-error correction, velocity. HyP3's multilooking, filtering and unwrapping are not tested.
      - Share of the bowl's centre value recovered (median): σ 40 m 0.98, 80 m 0.94, 160 m 0.81, 320 m 0.47, 640 m 0.17, 1.28 km 0.04, 2.56 km 0.01. The bare 1 km mean subtraction on a full grid gives 0.99, 0.96, 0.84, 0.50, 0.18, 0.05 and 0.01, so masks, inversion and DEM-error correction lose only 1–4% more.
      - The sign is kept. Nothing appears away from the bowls (largest 0.0002 mm/yr).
      - Around each bowl the referencing adds an opposite halo of up to 0.17 mm/yr (σ 160 m).
      - Against the real product's noise (0.4–0.5 mm/yr), a −5 mm/yr bowl stays visible up to σ ≈ 320 m: the correlation of the full product with the bowl is 0.76–0.90 for σ ≤ 160 m, 0.66 at 320 m, 0.25 at 640 m and about 0 above that.
      - So the local product is a high-pass measurement. It keeps motion narrower than about 300 m (σ) and removes motion wider than about 1 km.
    - **NTU comparison** (`feasibility/hk_ntu_compare.py`, `hongkong/NTU_COMPARISON.md`): settings table, then the comparison on the same pixels in vertical mm/yr, with our velocities also refitted to NTU's period.
      - With the same plane removed from both, run 2 agrees with ρ 0.20 for either period (0.25–0.30 on 0.5–1 km blocks). Its earlier ρ 0.39 came mostly from large-scale trends, and over NTU's period the raw agreement is negative.
      - At the 1 km local scale every product agrees at only 0.07–0.08.
      - NTU's values spread 4–8 times wider than ours. The cause is unresolved: NTU's map is interpolated and uses a sparser network.
    - **Order sample** (`feasibility/hk_order_sample.py`, summary in `hongkong/audit/order_sample_summary.json`): the user accepted the Buildings Department's legal notices on 2026-10-17.
      - Setup: 30 S26 and 15 S26A buildings (seeded) were looked up by block ID in the BD Orders Search, one request every 3 s.
      - The notices allow personal, non-commercial internal use only and forbid reproducing or passing on the material. So the raw results stay outside the project, and only counts are kept.
      - **Result:** every sampled building has orders of its type issued from 1 May 2023 on, and their number equals the open data's cumulative count (30/30 and 15/15). So the open data counts orders issued since May 2023, and each order's issue date can be recovered.
      - S26: 68 orders. Issued 10 in 2023 (May–Dec), 7 in 2024, 13 in 2025 and 38 in 2026 (to September); 27 on common parts, the rest on individual units; 57 outstanding, 11 complied. Four buildings also still list older outstanding S26 orders (2017–2023).
      - S26A: 19 orders. Issued 9 in 2023, 2 in 2024, 6 in 2025 and 2 in 2026; 11 on common parts.
      - The search gives no reason for an order, so what the orders mean is still unknown. The order documents are sold separately.
      - Dating all 1,399 buildings would take about 1,400 lookups, which is the user's call. Publishing per-building dates would need BD's written permission.
- **Miami-Dade checks after the GPT review (2026-10-17; no InSAR value used):**
  - **Coverage in each case's own pre-case window** (`feasibility/audit_miami_prewindow.py`, `miami/audit/opera_prewindow.json`; only pixel validity is read). A case qualifies when its window [open − W, open) starts inside the OPERA series, it opened at most 90 days after the last granule, and its pixel is valid in ≥ 80% of the window's granules. These settings are provisional, to be fixed in the frozen plan.
    - W = 2 years: 6,039 cases, 3,712 folios (3,679 counting each folio's first case since 2017).
    - W = 1 year: 6,203 cases, 3,839 folios. W = 3 years: 5,780 cases, 3,493 folios.
  - **Label audit** (`miami/audit/label_sample/`: `PROTOCOL.md`, `AUDIT.md`, `classification.csv`; scripts `feasibility/miami_case_sample.py` and `feasibility/miami_label_audit.py`). Setup:
    - 100 cases: 10 per year 2017–2026, split by case-number prefix, seed 20261017.
    - Read in the county's public case viewer: codes, structure assessments and the inspectors' and engineers' notes.
    - The raw pages hold names and stay outside the project.
    - The protocol was written after 6 cases had been read, and the code rule was fixed before the other 94.
    - **Hand categories (100 cases; share of all cases weighted by the sampling design, with a stratified bootstrap interval):**
      - documented structural deterioration (STRUCT): 19, 15% (8–23%);
      - fire or other sudden damage: 13, 13%;
      - other physical problems, mostly work without permits: 28, 16%;
      - reports rejected or repairs required with the nature not stated: 9, 17%;
      - administrative only: 27, 35%;
      - unclear: 4, 5%.
    - **The public violation codes can't give the label.** The rule fixed in advance finds hand STRUCT with precision 0.26 and recall 0.26:
      - recertification cases carry only the recertification codes, whatever the engineer found;
      - the "deteriorated structure" code is used for fires and as boilerplate in unpermitted-work cases.
    - **A STRUCT label would need the free text of every case:** about 6,700 viewer fetches and a text rule validated on this sample. Since about 2023 recertification rejections give no public reason.
    - **What STRUCT records:** spalling, corrosion, decayed roof structure, or "structural report rejected, repairs required". Settlement or tilt of a building is recorded in none of the 100. Sagging or structural cracking is mentioned in 3 cases: two buildings and one pool deck.
    - **Dating:** for recertification cases the open date follows building age, not a finding; the deficiency is documented 0–3 years later (median about 0.6 years).
    - **Repeats:** complexes are split into one case per building (4 pairs in the sample share a folio, and sibling series of 13–16 buildings exist); many digit-prefix cases continue an earlier case on the same property.
    - **Rough size of a STRUCT outcome with a 2-year window:** about 900 cases (450–1,400), or about 550 folios (290–850), assuming the same share per folio.
- **User's instruction after the label audit (2026-10-17):**
  - **Miami-Dade has priority.** An independent validation batch comes before any full download.
  - **Recheck the positives.** A rejection or a repair requirement alone is not evidence of a described structural defect. Fix the guide, then test it on 200–300 new cases: InSAR-blind, independently reviewed, with a supporting passage for every classification.
  - **Keep dates and units apart.** Case-opening dates and earliest-defect dates are kept separately. Buildings, properties and complexes are distinguished, and only same-episode cases are merged.
  - **Comparison group.** Find out whether a documented comparison group exists that went through a similar assessment.
  - **What the batch decides.** Whether to collect the full data and freeze the plan. No model training. The ~550 properties are not a confirmed sample.
  - **Hong Kong.** The sample results are kept. No full dating until research-use and publication permission is clarified: a draft request to BD is in `hongkong/audit/BD_PERMISSION_REQUEST_DRAFT.md`, for the user to send.
  - **NYC** stays a completed study, and its primary conclusion does not change.
- **Validation work so far** (`miami/audit/label_validation/`):
  - **Guide v2 / v2.1** (`PROTOCOL_v2.md`, `REVIEWER_INSTRUCTIONS.md`). Hashes in `FIXED.sha256`, fixed before any batch case was read. The guide sets out:
    - categories, an assessment field for comparison groups, separate dates, and building/property/complex/episode rules;
    - the review procedure: reviewers A and B independent, my adjudication, κ before adjudication;
    - a keyword screen;
    - decision rules R, P, D, Y, C and S.
  - **Recheck of the development set** (`DEV_RECHECK.md`): 11 of the 19 v1 positives remain, and one v1 non-positive becomes positive. That gives 12 of 100, a weighted share of 9.7% (4.2–15.5%), down from 15% under v1. The 100 cases shaped the guide, so they don't validate it.
  - **Validation batch:** 250 new cases, proportional to open year × prefix, seed 20261018 (`feasibility/miami_validation_sample.py`). Fetched 2026-10-17; result below.
  - **Recertification registry:** the county's public registry lists about 36,900 recertification cases since 1996, each with year, issue date, folio, building number, an enforcement flag and status. Its detail pages sit behind a browser-verification step and were not opened. It is a possible source of buildings that went through recertification without an unsafe case; using it needs the user's approval.
- **Validation batch result** (2026-10-18; `miami/audit/label_validation/VALIDATION_REPORT.md`; no InSAR file opened):
  - **Every decision rule passes:**
    - κ before adjudication 1.00 (STRUCT_DESCRIBED) and 0.98 (ENG_PASS_FIRST);
    - 666 of 666 passages found in their lines;
    - 22 of 22 positives dated with a passage;
    - 339 projected positive building-episodes (95% bootstrap 198–502), or 404–487 under the divisors added afterwards;
    - recertification ENG_PASS_FIRST 22 against 11 recertification positives;
    - screen recall 22 of 22.
  - **Positives:** 22 of 250 (8.8%). The 93 cases with only a rejection or repair requirement are not positives. Only 2 of 22 describe settlement or loss of plumb; the rest describe material deterioration (spalling, corrosion, termites, rot).
  - **Dates:** for recertification cases the earliest defect comes 0.01–4.4 years after the opening (median 0.72), so the two dates stay separate.
  - **Comparison group:** found only within recertification (first structural report approved). Caveats:
    - an approval doesn't mean no deterioration;
    - both groups are late recertifications;
    - 59% of recertification cases sit in an undescribed middle group;
    - the registry option still needs the user's approval.
  - **Reviewers:** both are instances of one model, so the 40-case human check (`human_check.csv`) is recommended.
  - **Decision:**
    - **Full download:** yes by the rules; started 2026-10-18 with the user's permission (`feasibility/miami_full_fetch.py`, about two days). The raw pages hold names and stay outside the project (`Alex_private/miami_viewer_raw/`); the project gets name-free tables in `miami/full/`.
    - **Plan freeze:** the batch supports it, but it is not done. Guide v3, the human check and the user's design choices come first (report §13).
    - **No model trained.**
- **Guide v3 and the full labelling plan** (2026-10-18; drafts, not fixed yet):
  - **Guide v3:** `miami/audit/label_validation/PROTOCOL_v3.md` and `REVIEWER_INSTRUCTIONS_v3.md`. Positives are defined as before. The adjudication conventions are written in, plus five consistency rules that change 8 batch labels, none of them a positive or comparison case.
  - **Labelling plan:** `LABELLING_PLAN.md`. The user decided:
    - two reviewers for every case;
    - the human check before stage 1;
    - late cases labelled last;
    - Haiku tested in stage 0, and if it passes, Haiku plus Sonnet per case.
  - **Stop rules:** Q0–Q3.
  - **Hand-off:** OpenAI Codex runs the labelling (user, 2026-10-18), using `HANDOFF_MIAMI_LABELLING.md` in the project root. Codex orchestrates and adjudicates; the reviewers are Claude instances started through the `claude` command line.
  - **Five gaps fixed** after a review the same day: stage-0 cases get final v3 labels, so the final set holds exactly 6,667 cases; undated evidence leaves the date empty; exact chunk coverage is checked; any substantive revision repeats stage 0; secondary-field disagreements are settled by fixed rules and kept.
  - **Three details fixed before freezing** (user's review, 2026-10-18):
    - **Undated complaints.** The older complaint sentences in `PROTOCOL_v3.md` and `REVIEWER_INSTRUCTIONS_v3.md` now follow rule 18: cite the earliest dated line, and an undated complaint only if no dated line documents the defect.
    - **Comparison cases.** Agreed ENG_PASS_FIRST cases that differ on `complex` are now adjudicated.
    - **Reviewer isolation is enforced, not only instructed.**
      - **Set-up:** one folder per call; `--restricted --safe-mode --tools "Read,Write,Bash"`, `dontAsk`; one `Edit` rule for the call's `output.jsonl`; one exact Bash rule for the checker's `--call` mode, which reads everything from the folder's manifest.
      - **Bugs fixed** in Codex's draft launcher (`miami_label_run.py`): its `Write(...)` rule denied the output write, and its probe crashed on refusal events.
      - **Probe** on synthetic files, real layout: Haiku and Sonnet each passed all 22 checks (refused reads, writes and commands outside the folder; forbidden token never seen). Synthetic tests: 19 pass.
      - Refused attempts outside the folder fail the chunk.
  - **Hand-off withdrawn** (user, 2026-10-18 about 18:00): `HANDOFF_MIAMI_LABELLING.md` was deleted and Claude runs the labelling. Codex's unfinished Luna reviewer was removed; a copy is in `Alex_private/codex_luna_backup_20261018/`. Reviewers stay as the user decided: Haiku and Sonnet in stage 0, Sonnet in every pair. Exact model IDs are pinned in `REVIEWER_MODELS.json`. 27 synthetic tests pass. The isolation probe is rerun before stage 0.
  - **Reviewers moved to Cursor** (user, 2026-10-18 evening). The pair is Grok 4.7 (A) and Sonnet (B), run as fresh subagents by a Sonnet coordinator that labels nothing, in one Cursor window. Haiku is dropped; if Grok fails Q0, the pair is Sonnet + Sonnet. Claude builds the workspace, records and checks every output, computes Q0–Q3 and adjudicates. There is no hand-off file.
    - **Isolation is by instruction only in Cursor**, which is weaker than the enforced Claude launcher; the plan says so and the study reports it. The workspace holds no labels, batch results or InSAR files.
    - **Recording step:** `miami_label_run.py --record` checks each output against the chunk index and freezes a private copy with its `.meta.json`. Only recorded outputs are merged.
    - **Stage 0 built:** 250 cases, 18 chunks each for A and B, in different orders, in `Alex_private/miami_labels_full/cursor/stage0`. 30 synthetic tests pass. Nothing is hashed until the user approves and gives Cursor's exact model names.
  - **Guide v3 approved and fixed** (user, 2026-10-18 21:39 Cairo): both v3 guide files are in `FIXED.sha256`. The labelling plan, reviewer models and scripts are not fixed yet.
  - **Labelling plan, reviewer models and scripts approved and fixed** (user, 2026-10-18 21:41 Cairo): they are in `FIXED.sha256`, with a private freeze file for the launcher. Exact Cursor model names are not recorded (user's choice); the plan states this as a limitation. Stage 0 is ready and has not started.
  - **Stage 0 done** (2026-10-19): all 500 reviews recorded with no check failures. Q0 passed for both models: Grok κ 0.920 (STRUCT_DESCRIBED), 0.943 (ENG_PASS_FIRST), category 0.934; Sonnet 0.920, 0.972, 0.946. The stage-1 pair is Grok (A) and Sonnet (B), with Sonnet as base. 41 of the 250 cases go to adjudication. The human check is still needed before stage 1.
  - **Stage 0 adjudicated and merged** (2026-10-20): the 41 listed cases were settled from the dossiers, and the merge passed all 796 passage checks. The final v3 labels for the 250 batch cases have 19 positives, all dated, against the batch's 22: both reviewers read two batch positives as undescribed deficiencies, and the third, which they read as administrative or unclear, was adjudicated UNCLEAR. The 22 ENG_PASS_FIRST comparison cases are the same as in the batch. The stage-1 dossiers are built (6,417; about 75 hours of Cursor). The human check is still needed before stage 1.
  - **Reviewer revision** (2026-10-20, the user's decision): Composer replaces Sonnet as reviewer B if it passes Q0 on the same 250 cases; otherwise the pair is Grok + Grok. Stage 1 runs three chunk numbers at once (about 25 hours instead of 75). The guide is unchanged; the scripts, plan and model list were revised, tested and re-hashed. The Composer test workspace is built.
  - **Composer test** (2026-10-20): Composer matched Grok on the two key outcomes (κ 0.920 and 0.943) but failed Q0 on category agreement (0.810), mostly by reading missing or unapproved recertification reports as a deficiency finding. By the fixed rule, the stage-1 pair is Grok + Grok; the 250 cases get a second Grok review with wave 1.
  - **Haiku test** (2026-10-20): Luna, run in the Codex CLI, could not pass. Haiku, run in the Claude Code launcher with enforced isolation, passed Q0 (κ 0.920 and 1.000, category agreement 0.942), without the error that failed Composer and Luna. The stage-1 pair is Grok (Cursor) + Haiku (Claude Code), run side by side. The 250 cases need 63 adjudications for the new pair.
  - **Stage-1 method** (user, 2026-10-20, labelling-plan revision 2026-10-20b): Grok labels A in Cursor while Haiku labels B in the Claude Code launcher. When Haiku reaches the Claude usage limit, the launcher stops and the wave's remaining B chunks go unchanged to a second Grok in Cursor; the next wave starts with Haiku again. Agreement is reported separately for Grok + Haiku and Grok + Grok cases. 41 tests pass; isolation probe 22/22 on the current CLI.
  - **Grok + Haiku on the 250 cases** (2026-10-20): Claude settled the 63 listed cases and the merge passed all 792 passage checks. It gives the same 19 positives, with the same dates, and the same 22 ENG_PASS_FIRST cases as the Grok + Sonnet final. Categories differ in 3 cases and assessments in 4, none of them positive or comparison cases. Pathway and complex differ more often, because outside positives and comparison cases the base reviewer's (Haiku's) value is kept and flagged. Next: the human check, then stage-1 wave 1.
  - **Human check done** (2026-10-25; VALIDATION_REPORT §12). The user labelled all 40 cases.
    - Category agreement with the v3 labels was 18 of 40 (κ 0.34). The differences go against written rules of the guide, so it is not revised.
    - The check does not independently confirm the labels.
    - None of the 40 cases has an expected deformation signature.
  - **Broad-target labelling paused; exploratory refinement of the Miami outcome** (user, 2026-10-25; `miami/audit/settlement/PROTOCOL_SETTLEMENT.md`). This is recorded before any predictive analysis.
    - Documented ground/foundation-movement building distress is separated from geometric distortion of unresolved cause, unrelated conditions and insufficient evidence.
    - The review covers the 100 settlement-screen matches and a seeded sample of 206 non-matches. Two blind AI readers are followed by Claude's adjudication and then an independent engineer.
    - It will report unique-building counts, pre-documentation OPERA coverage (validity only) and control-group availability.
    - "40–80 cases" is an unverified estimate.
    - NYC's result is unchanged. Hong Kong is not assumed preferable. No InSAR value is read and no model is trained until the cohort is established.
  - **Settlement review finished** (2026-10-25, in Codex after Claude's usage limit; LABELLING_LOG has the details).
    - There are two deviations, both accepted by the user. First, reader B's last five batches and the adjudication used GPT models. Second, only 19 specialist cases plus 2 records-first cases go to the engineer, after Codex reviewed the 74 packet cases itself.
    - AI results for the 306 cases: GFM 28, GEOM_UNRESOLVED 14, INSUFFICIENT 5, UNRELATED 259 (κ 0.93). After Codex's review, 26 GFM count as documentary positives on 26 folios, and 24 of them have a qualifying 2-year pre-documentation OPERA window. These are not engineer-confirmed.
    - About 40 more cases are estimated among the non-matches (per-stratum 95% bounds 11–101 for stratum H). There are 35 candidate assessed controls, not yet checked as comparable.
  - **Candidate label sources: readiness check** (2026-10-26; `feasibility/candidates/READINESS_REPORT.md` and `readiness.json`). This is a facts-only check by another agent, reviewed by Claude. No InSAR value was read and no model was fitted. The user has told the supervisor about these results; the choice is theirs.
    - **Austin, TX (open permit data, public domain).**
      - 26,797 permits match foundation keywords. In a sample of 60, 42 are true foundation repairs.
      - Restricted to building permits, 35 of 41 sampled are repairs: 85% (95% 71–94%). Most false matches are plumbing "tunnel under the foundation" permits.
      - Since 2016-07-01 there are 7,422 matching building permits on 6,577 parcels. 91% are residential.
      - One OPERA DISP-S1 frame (28482, ascending) contains every geocoded matched permit: 254 granules, 2016-07-10 to 2025-11-20.
      - Permits carry the appraisal-district parcel ID (`tcad_id`). The appraisal extract itself is not yet checked.
      - Not coastal. The restriction to building permits must be fixed in a protocol before any InSAR link.
    - **Houston, TX: no usable open data.** The only permit-level layer is new construction (2015–2021). Its 21 keyword matches are all new construction, with no repairs. Repair permits would need a records request.
    - **Noto Peninsula, Japan (Vescovo et al. GeoPackage v2.5, CC BY 4.0).**
      - 140,208 buildings, 3,461 of them destroyed (`damage_val`). Wajima has 1,310 destroyed of 26,700 buildings; Suzu has 1,767 of 23,001. About 24,000 are obstructed or inconsistent.
      - Each building has fire, tsunami and slope-failure flags and a USGS MMI value.
      - Sentinel-1 has 12-day pairs across the 2024-01-01 earthquake on descending tracks 17 (2023-12-30 → 2024-01-11) and 119 (2023-12-25 → 2024-01-06). There is no OPERA coverage of Japan.
      - The task would be damage mapping, not prediction.
  - **Supervisor decision** (reported by the user, 2026-10-28): keep the same research question, and the city need not be coastal.
    - So the next study is Austin, the only candidate that keeps the question with enough events. Noto (damage mapping) is not pursued.
    - A preregistered Austin plan comes next. No InSAR value is linked before it is frozen.
    - User choices (2026-10-28): the unit is the parcel, deep learning is a secondary tier, and Miami and Hong Kong are parked. The draft plan is `feasibility/austin/AUSTIN_PLAN.md`, awaiting supervisor approval.
