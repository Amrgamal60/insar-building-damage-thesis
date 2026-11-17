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

(Empty. Each entry: date, what changed, why, and whether any NYC result had been seen.)

## 15. Freeze record

- **Plan approved by:** the supervisor, on 2026-10-08. While the supervisor was unreachable, the design was also reviewed with two AI assistants (ChatGPT and Claude); see §16.
- **Frozen copy:** `freeze/NYC_REPLICATION_PLAN_frozen.md`, saved 2026-10-08, SHA-256: ______
- **Checkpoint 2, filled in after freezing:**
  - events counted under §6: ______;
  - primary population: ______.
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
