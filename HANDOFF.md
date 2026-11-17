# Handoff: NYC replication of the Alexandria InSAR result

Written 2026-10-11 (Cairo time) by Claude (Opus 5.5), session `0e738ef5`, just before the project moved to another PC. On the new PC, Claude's memory and this session's context are gone; this file replaces them. **Start here**, then read `feasibility/nyc/NYC_REPLICATION_PLAN.md` §11–§17.

Everything that lived outside this folder has been copied into `handoff/`. Details are in section 10.

## Update 2026-10-25: Miami settlement review resumed by Codex

**Author of this update and this session's patches: Codex, not Claude.** At the user's request, Codex recovered Claude session `9a7b69ba-2d8d-4506-890e-5b18c890f65d` after its session limit. Detailed authorship, hashes, deviations and steps are in `feasibility/miami/audit/settlement/resume_20261025.json`.

**Later user-requested Astra review, personally performed by the Codex primary agent:** all 74 packet cases and 592 excerpts reviewed, with seven complete dossiers and six additional sets of source lines checked. The immediate referral queue is now 19 specialist cases; 53 documentary decisions are clear (26 GFM and 27 unrelated), and two cases need source records first. Cases `20230219896` and `F2021009354` are held from the working positive pool because of conflicting record conclusions. The 26 clear documentary positives occupy 26 distinct folios; 24 meet the existing two-year coverage rule. These remain source-reported AI coding decisions, not engineer-confirmed cases. Historical 306-case finals and the original 74-case packet remain unchanged. New aggregate results: `feasibility/miami/audit/settlement/triage_summary_20261025.json`; detailed decisions, focused packet, source-record requests, manual decision input and verification are in `Alex_private/miami_settlement/triage_20261025/`. A GPT-6.1 medium-effort subagent performed mechanical integrity checks only; no triage decisions were delegated.

- Claude's completed reader A batches 0–12 and B batches 0–7 were preserved. Codex subagents using `gpt-6-luna` at high effort completed B8–12 and 50 adjudications/verifications under the original substantive rules. All 26 batches pass the original checker. The frozen protocol still describes Claude Sonnet; this model substitution is explicitly logged as a deviation, without rewriting the frozen protocol.
- AI finals: 306 cases, comprising 28 GFM, 14 GEOM_UNRESOLVED, 5 INSUFFICIENT and 259 UNRELATED. GFM and GEOM each have distinct folios within their class. AI agreement is not engineering validation.
- Codex created `feasibility/miami_settlement_finish.py` for validation, assembly, descriptive counts, control-candidate summaries and engineering-review selection. Outputs are `summary.json` and `coverage.json` in the settlement audit directory. Private staging is `/tmp/alex-settlement-resume`; final installation and packet status are recorded in the resume JSON.
- Codex patched `miami_settlement_coverage.py` to cap available series duration at the last observation and report the validity share before documentation. Coverage uses dates and finite/mask validity only. Two-year windows qualify for 26 GFM and 14 GEOM cases.
- On the user's later instruction, any newly started or restarted subagent uses `gpt-6.1-sol` at medium effort. These agents prepare names-free engineering material and assessed-control availability. No third party has been contacted.
- Independent structural/geotechnical review remains pending, arranged by the user. Broad-target labelling remains paused; no training was started. NYC's frozen work was not changed. The pre-existing broad-label preservation mismatch for `LABELLING_LOG.md` was recorded, not repaired or overwritten.

---

## 0. First steps on the new PC

1. **Restore Claude's memory.** Copy `handoff/claude_memory/*.md` into the new memory folder: `~/.claude/projects/<slug>/memory/`. The slug is the working directory's absolute path with `/` replaced by `-` (on the old PC it was `-home-amr-Master-projects`). Section 11 below quotes the same files word for word. Alternatively, tell Claude: "read Alex/HANDOFF.md".
2. **Python environment.** `Alex/.venv` (uv, Python 3.12.7) only works if copied to the same absolute path with the same Python. Otherwise rebuild it:
   ```bash
   cd Alex && uv venv --python 3.12.7 .venv && uv pip install --python .venv/bin/python -r handoff/env/pip_freeze.txt
   ```
   - Key versions: numpy 2.5.3, scikit-learn 1.9.1, scipy 1.18.1, pandas 3.0.6, joblib 1.6.0, cupy 14.2.0 (CUDA 13.1).
   - The lock files used by the preregistration are `feasibility/nyc/out/checkpoint2/LOCK_*.txt`. A different machine or library version must be logged in §14.
   - CuPy (the GPU) is a speed-up only. Without CUDA, `nyc_lib.VariogramNull` falls back to NumPy/SciPy (Codex added this; §14 deviation 5).
   - LiCSBAS (Alexandria only) has its own conda env: `tools/licsbas_env.yml`, Miniforge at `~/miniforge3`.
3. **Earthdata login.** Only needed for new NASA/ASF downloads.
   - The user creates `~/.netrc` (`machine urs.earthdata.nasa.gov login … password …`, `chmod 600`) themselves.
   - **Never write the password in chat or in any file.** The user asked for this explicitly. It was never stored in this folder; the login name is redacted in the transcripts.
4. **Test the new PC's RAM before any long run.** The old PC's memory corrupted data (section 4). Use one of:
   - memtest86+ from the boot menu;
   - kernel option `memtest=4` and check `dmesg` for "bad mem";
   - or a userspace `memtester`.
   
   ECC memory is ideal.
5. **Paths.** The code uses paths relative to `Alex/feasibility/nyc`. The calculation checkpoints are fingerprinted by file contents, not paths, so they stay valid after copying, as long as the code and data are byte-identical.

---

## 1. The project in brief

- **The user:** a Master's student. Their supervisor approves the plans. The user also uses ChatGPT and OpenAI Codex on this project, and Codex worked in this folder overnight on 10–11 Oct (section 5). Check for concurrent edits by another agent before changing anything.
- **Alexandria (the original result):** an earlier study by the user, in `Alex/data`, `Alex/scripts` and `data/README.md`. InSAR ground velocity (Shirzaei VLM, then LiCSAR/LiCSBAS) added predictive value for building collapses in Alexandria (250 m cells, logistic regression, held-out PR AUC, spatial nulls). The reports are `data/pilot/PILOT_REPORT.md` and `data/pilot/LICSAR_TEST.md`.
- **NYC (current work):** a **preregistered external replication** of that result in New York City, using NYC DOB collapse events, OPERA DISP-S1 InSAR (frame F08622, 30 m, EPSG:32618) and PLUTO building data.
  - **Plan:** `feasibility/nyc/NYC_REPLICATION_PLAN.md`. The supervisor approved it, and it was frozen 2026-10-08.
  - **Frozen copy:** `feasibility/nyc/freeze/NYC_REPLICATION_PLAN_frozen.md`, SHA-256 `59a2aa1a573ce8b7cf7ede7fd1e870bea2768c259978c716872f177041588a5d`. **Never edit it.**
- **Decision rule (§11):** replicated if and only if, in the primary analysis, the held-out change in PR AUC from adding InSAR is positive **and** the variogram-matching null gives p < 0.05.
  - **Primary analysis:** the older-building domain, 250 m, logistic regression, Baseline 1 + x/y, 1-year window.
  - **Reported alongside:** directional concordance and the largest p across the six nulls.
- **Design facts:**
  - **Primary population:** the older-building domain, 5,001 eligible 250 m cells, 65 events, 64 risk sets.
  - **Whole NYC:** 10,320 cells, 79 events. This is secondary 1.
  - **Risk sets** use the "first" control rule; "earlier" and "never" are secondaries 7 and 11.
  - **Models:**
    - LR: StandardScaler + C = 1.
    - RF: 500 trees, min_samples_leaf 5, max_features sqrt, class_weight balanced_subsample, random_state 0.
  - **Folds:** 5 folds from 2 km blocks, seed 42.
  - **Metrics:** PR AUC (primary), ROC AUC, top-10% capture, and top-10% capture per risk set.
  - **Primary null:** variogram-matching, 999 draws, seed 2027.
  - **Bootstrap:** refit block bootstrap, 2,000 resamples for LR and 500 for RF.

---

## 2. Rules that must hold (from the user and the plan)

- **§13 order:** checkpoint 2 → InSAR + outcome-blind checks → decoy run (seed 99) → **one** real run → report. Steps 1–4 are done; the real run is partly done.
- **Log every change after the freeze in §14 of the plan,** saying whether any NYC result had been seen. Deviations 1–8 exist. Any new change gets the next number (9).
- **Never tune after results.** No changes to study area, windows, features, folds, models or nulls. Anything added later is labelled exploratory.
- **Reruns of the real run are only for code errors,** logged with before and after values. Execution-only changes (machine, worker count, checkpoints) don't change results, but are still logged.
- **The GPU is a speed-up only.**
  - cuML's random forest is a different model (histogram splits, no balanced_subsample), so it **cannot** replace secondary 3. At most it could be an extra, labelled exploratory.
  - The user asked "Random forest will take lot of time! Why not use gpu?" and accepted this answer.
- **Compute budget (§13.6):** secondaries share 7 days of wall-clock time, ending **2026-10-15 16:27:20 Africa/Cairo**. Unfinished ones are reported as "not run". Codex's deviations 5–8 kept this deadline.
  - Moving to a new PC is a new deviation. Recommended: keep the original deadline, unless the supervisor agrees otherwise, and log the decision.
- **Subagents use Sonnet** (the user said "sonnets 5.5"). The GPU may be used freely; dependencies may be installed into the venv.
- **The user's loop instruction (2026-10-08):** "Go ahead, review your steps and /loop until plan is all done … Ill sleep for a while until you finish". The loop prompt was:
  > /loop Work through NYC_REPLICATION_PLAN.md §13 in order until the plan is complete: finish checkpoint 2 (2016–2022 PLUTO releases and their dates, baseline features, fold maps, lock file, hashes), then the InSAR velocities with their outcome-blind checks, then the decoy run (seed 99), then the one real run and its report. Review each step against the frozen plan before moving on. Log every deviation in §14. Never tune after results. Subagents use Sonnet 5.5.
- **The next study (section 8) starts only after the NYC real run and report are finished.**

---

## 3. Where things stand (2026-10-11 08:40 Cairo)

**Nothing is running.** The last process died at 00:25 on 10-11.

### Finished

**The primary decides the outcome: NOT REPLICATED.** In the plan's wording: "not replicated, with opposite deformation direction".

| Analysis | Rows / risk sets | ΔPR AUC (InSAR − base) | p (PR) | Other |
|---|---|---|---|---|
| **Primary** (VM null, 999; bootstrap 2,000) | 309,972 / 64 | −3.66e-06 (0.000231 → 0.000227), 95% CI [−2.08e-05, 2.25e-05] | **0.418** | ROC Δ −0.0032 (p 0.45); top-10% capture Δ 0 (p 0.85); direction **opposite** (median standardised diff +0.037, 47% of risk sets below 0; raw LOS diff −0.72 mm/yr); coefficient −0.0157 |
| s8: the other nulls on the primary | — | same observed | free perm. 0.422 (2,000); within-block perm. 0.481 (2,000); MSR 0.371 (999); AA-MSR 0.380 (999); VM rank-remapped 0.395 (999) | **largest p across the six nulls: 0.481** |
| s9: ten other fold seeds (0–9) | 309,972 / 64 | negative in 8 of 10 | 0.10–0.83 | seed 7 lowest (Δ +9.2e-05, p 0.101) |
| s1: whole NYC | 784,157 / 78 | −1.78e-06, CI [−1.19e-05, 7.79e-06] | 0.450 | ROC p 0.412; direction opposite |

- **Where the results are:** `feasibility/nyc/out/models/real/result_*.json` and `null_*.csv`.
- **The decoy run** (seed 99, fake outcome) is in `out/models/decoy/`. Its report is `DECOY_REPORT.md` and its manifest is `57390ac7…`. Decoy primary p = 0.153; secondaries 0.09–0.88. It is recorded in §15.

### Not finished

- **s2 (200 m):** all 999 null draws are saved (`null_s2.csv`, verified, `checkpoints/s2/0e3b75…/null_complete.json`). Bootstrap resamples: 395 of 2,000 checkpointed, in `out/models/real/checkpoints/s2/0e3b75…/bootstrap/`.
- **s4–s7 and s11–s15** (logistic regression) have not started. Note that s10 (ROC AUC and both top-10% capture forms) is not a separate run; its metrics are reported for every analysis.
- **s3, the random forest,** runs last. It took about 2.6 days with 16 workers on the old PC, without repeat checks.
- **The full primary recheck is pending.** This means recomputing the observed fits, all 999 null draws and all 2,000 bootstrap resamples, then comparing them with the saved values.
  - Codex's `resume_real.py` runs it automatically (`restart_20261010/verify_metrics.py --full`, which writes `FULL_PRIMARY_VERIFICATION.json`) before building the report.
  - My simpler alternative is `handoff/scratchpad/verify_primary.py`.
  - The sampled checks so far agree within about 3e-10 (section 4).
- **Not done yet:** the report (`NYC_RESULT.md`), the §15 result record, and merging the logs.

---

## 4. Crash history and the RAM fault (why the project is moving)

**Timeline (Cairo time):**
- **10-08 16:27:** the real run starts (16 workers). The primary finishes at 16:49:41.
- **10-08 16:52:** crash early in s8. `roc_auc_score` raised "x is neither increasing nor decreasing". Logged as §14 deviation 4.
- **10-08:** the diagnosis reruns failed with out-of-range indices of 2^39 plus a valid index. The decoy crash (deviation 3) had the same signature, as did the garbled string "292_22�3".
  - A userspace memory test was started but never finished.
  - The user then said "Enough. Resume what we are doing".
- **10-10 17:52:** resumed unchanged and detached (`handoff/scratchpad/launch_real.sh`). It ran s8, s9 and s1 cleanly for about 4 hours, with no crash.
- **10-10 21:50:55:** crash in s2's bootstrap (`boot_rep`), the same ROC "x is neither increasing nor decreasing" error. My session had hit its usage limit, so the user asked Codex to resume.
- **10-10 23:40 to 10-11 00:25, Codex restarted five times.** Every attempt crashed within 15 seconds to 9 minutes:
  1. a worker segfault inside NumPy's `argsort`;
  2. IndexError 549,756,137,364 = 2^39 + 323,476, even with NumPy's AVX2 code paths disabled;
  3. a worker segfault;
  4. the **same seed failed 5 times in a row with the identical index** 549,756,009,465 (2^39 + 195,577);
  5. the main process itself segfaulted.
- **The silent errors:** a recheck of the saved primary null differed at draw 864 by 3.1e-10 in PR AUC. Another recheck matched that draw but differed on a different one. The machine can change numbers without crashing.

**Assessment:** a faulty RAM cell (or memory path) at bit 39. It is very likely, though no memory test confirmed it.
- The same bit appears across unrelated code (pyarrow strings, sort indices, ROC curves). The identical repeated failure is what a defective cell does when a worker reuses the same memory.
- It is a laptop (i9-10980HK, 64 GB **non-ECC**) running at 95–99 °C under load.
- Bit 39 in a float64 is a mantissa bit: at most about 1.2e-4 relative error, so silent float errors are tiny. In int64 indices it adds 2^39, which crashes.
- The primary's p = 0.418 cannot be moved by errors of that size. The pending full recheck is still required before the report.
- **Also on the old PC:** on 10-11 `nvidia-smi` reported "Driver/library version mismatch" (an automatic driver update). The GPU there needs a reboot before CuPy works again.

---

## 5. What Codex changed (§14 deviations 5–8; read them in the plan)

All of these are execution-only. Models, seeds, draw and resample counts, folds and decision rules are unchanged.

- **Deviation 5:** a CPU fallback for the variogram null when there is no CUDA. It matched the saved GPU draws: the primary exactly, s2 within 6e-8 (`restart_20261010/CPU_VERIFICATION.json`). The original library is kept as `restart_20261010/nyc_lib_before.py`.
- **Deviation 6:** `NPY_DISABLE_CPU_FEATURES=X86_V3` (baseline NumPy dispatch) and one BLAS/OpenMP thread per worker. It did not prevent the failures. On a healthy machine it is harmless but optional; if you drop it, log that.
- **Deviation 7:** per-draw **checkpoints** in `out/models/real/checkpoints/<tag>/<fingerprint>/{null,bootstrap}/`, each saved atomically with its seed and a checksum. Saved null tables are reused only after 16 sampled draws reproduce them within 1e-12.
- **Deviation 8:** **repeat checks**. Every seeded calculation runs until two results agree within 1e-12, with at most 6 attempts at the same seed. Input hashes are checked before and after. Known index or non-monotone errors trigger a retry; other errors stop the run. Workers went down to 4.
  - **Bounded auto-restart:** `scripts/watch_real.py` restarts at most 3 times. Restarts are recorded in `restart_20261010/AUTOMATIC_RESTARTS.jsonl`.
- **The new code:**
  - `scripts/11_models.py` (SHA-256 `1d3ca0cc…`) and `scripts/nyc_lib.py` (`619e4de4…`); hashes in `restart_20261010/CODE_RESUME_REPEAT.sha256`.
  - The hashes of the code that started the real run are in `out/models/CODE_REAL_RUN.sha256` (`11_models.py` `b8ce5629…`, `nyc_lib.py` `4ab32839…`, `12_report.py` `1e572ccd…`, unchanged).
  - The checkpoint fingerprints include the source code's bytes, so editing `11_models.py` or `nyc_lib.py` again invalidates the saved checkpoints.
- **Supervisor script:** `scripts/resume_real.py` launches `11_models.py raw out --real --jobs 4` with the environment of deviation 6, and logs to `out/models/codex_resume.log` and `restart_20261010/status.json`. When the run finishes or the deadline passes, it runs the full primary recheck, then `12_report.py`. The worker count (4) is hard-coded on line 63.

---

## 6. How to resume on the new PC

1. Do the checks in section 0: RAM test, environment, and hashes:
   ```bash
   cd Alex/feasibility/nyc && sha256sum -c out/models/restart_20261010/CODE_RESUME_REPEAT.sha256
   ```
2. Add **§14 deviation 9** before launching. It records:
   - execution moved to a new PC because of the memory fault in section 4;
   - the new machine (CPU, RAM, ECC yes or no, memory-test result) and the library versions;
   - the worker count;
   - the deadline decision;
   - that NYC results had been seen.
3. Launch, detached so it survives the session closing. **Recommended: Codex's current code** (checkpoints + repeat checks), with as many workers as the new PC allows:
   ```bash
   cd Alex/feasibility/nyc
   setsid nohup ../../.venv/bin/python -I scripts/11_models.py raw out --real --jobs <N> >> out/models/real_run_newpc.log 2>&1 < /dev/null &
   ```
   - Alternatively, change `--jobs 4` in `resume_real.py` and run `../../.venv/bin/python -I scripts/resume_real.py`. That also does the deadline cut-off, the full primary recheck and the report. Changing `resume_real.py` doesn't touch the checkpoint fingerprints, which only cover `11_models.py` and `nyc_lib.py`.
   - Finished analyses (those with a `result_<tag>.json`) are skipped. s2 resumes from its checkpoints.
   - **Code order:** primary → s8 → s9 → s1 → s2 → the other LR secondaries → s3 (RF) last.
4. **Timing.** On the old PC at 16 workers without repeat checks, the LR secondaries took about 6–8 h and the RF about 2.6 days. Repeat checks roughly double that. If the RF can't finish by the deadline, it is reported as "not run".
5. **Watching the run:**
   - `tail` the log;
   - `ls out/models/real/` for new `result_*.json` files;
   - count files in `checkpoints/<tag>/*/bootstrap/`.
   
   py-spy needs ptrace permission.

### When it ends
1. **The full primary recheck**, if `resume_real.py` didn't already run it:
   ```bash
   ../../.venv/bin/python -I out/models/restart_20261010/verify_metrics.py --full
   ```
   or `handoff/scratchpad/verify_primary.py`. Record the result.
2. **The report:**
   ```bash
   ../../.venv/bin/python -I scripts/12_report.py out --real
   ```
   This writes `NYC_RESULT.md`. Review it against §11–§12: missing analyses are marked "not run", and the direction label and largest p across the six nulls are stated.
3. **Logs.** Merge them into one record, without editing a log while anything writes to it:
   - `out/models/real_run_live.log` is the **complete** record of the 10-08 run and the 10-10 resume, up to the 21:50 crash.
     - It was copied from the process's output, because on 10-10 a `sed -i` gave `real_run.log` a new inode and the process kept writing to the deleted file.
     - Its 17:52:53 note says "after 2 min"; the correct wording, "under a minute", is in `real_run.log`.
   - `out/models/real_run.log` is a stale copy up to 17:53, plus the final line `EXIT 1 2026-10-10 21:50:55`.
   - `out/models/codex_resume.log` is Codex's five attempts.
   - Then the new PC's log.
4. **§15:** record the result, the hashes of the outputs and the report, and the end time.
5. **Tell the user and the supervisor;** then the next study (section 8).

---

## 7. File map (`Alex/feasibility/nyc/`)

- `NYC_REPLICATION_PLAN.md`: the living plan.
  - §1–§13 are the design; §14 holds deviations 1–8; §15 is the freeze record (checkpoint 2, InSAR, decoy, real-run start); §16 lists revisions before freezing; §17 is the next study.
- `freeze/`: the frozen copy and `FROZEN_AT.txt`.
- **Scripts:**

  | Script | What it does |
  |---|---|
  | `01_audit_events.py`, `02_freeze_events.py` | events → `out/events_final.csv`, `out/AUDIT.md`, `out/funnel.md` |
  | `03_download_static.sh` | static layers |
  | `04_grid_domain.py` | grid, domain, eligibility (checkpoint 2) |
  | `05_download_pluto.sh`, `06_features.py`, `07_lock_and_hash.sh` | PLUTO 16v1–22v2, features, lock files and hashes |
  | `08_download_refpoint.py`, `09_insar_velocities.py`, `10_insar_checks.py` | InSAR (report: `out/insar/INSAR_CHECKS.md`, manifest `bbd5f50a…`) |
  | `nyc_lib.py` | shared library (`SPEC` of analyses, `prepare`, `VariogramNull`, metrics) |
  | `11_models.py` | all analyses (`--decoy` / `--real`, `--jobs`, `--only`, `--surrogates-only`) |
  | `12_report.py` | `NYC_RESULT.md` / `DECOY_REPORT.md` |
  | `resume_real.py`, `watch_real.py` | Codex's supervisor and watcher |

- `out/checkpoint2/`: grid, features, folds, event samples, lock files. Manifests: `MANIFEST.sha256` `a7aa55a1…` and `MANIFEST_PART2.sha256` `3049dada…`.
- `out/insar/`: window velocities and checks.
- `out/models/decoy/`: decoy outputs. `out/models/real/`: real-run outputs.
  - `surr_<name>.npy` are cached null surrogates (float32, several GB). `s3`, `s4` and `s11` reuse the primary's file.
  - `checkpoints/` holds Codex's per-draw checkpoints.
- `out/models/restart_20261010/`: Codex's verification evidence, hashes, status and restart log.
- `raw/`: OPERA granules, STATIC layers, the refpoint subset, the PLUTO archive, and the DOB and permit data (about 18 GB total).

---

## 8. Next study (plan §17; not part of the preregistration)

- **The supervisor's request (2026-10-10, in Arabic):** download every dataset in the brief (`handoff/uploads/Coastal_InSAR_Research_Candidates_Supervisor_Brief.pdf`). Then choose a deep-learning model that links satellite data to predicting "الانهيارات الأرضية" in coastal cities.
  - **Still to confirm with the supervisor:** whether that means building collapse or ground failure (landslides).
- **The user's choice:** only the best 2 cities beside NYC, not all four.
  - **Hong Kong (main):** about 1,320 S26 and 80 S26A buildings (Buildings Ordinance orders) with lat/lon, plus building records.
    - Check first: do monthly order snapshots since May 2023 exist, so orders can be dated? §17 gives a fallback.
    - Data already fetched: `handoff/scratchpad/hk/s26.csv`, `hk/s26a.csv`; building info in `hkbi/bi.zip` and `hkbi/x/BDBIAR_BDBIAR_converted.csv`.
  - **Miami-Dade (second):** unsafe-structure cases with open date and folio, plus property records. OPERA DISP-S1 covers North America, so the NYC code can be reused (frame to be confirmed).
    - **Go/no-go check:** a bulk export with open dates and **at least 100 cases since 2017 inside InSAR coverage**. If it fails, audit Mumbai.
    - Data already fetched: `handoff/scratchpad/miami_dl/Miami.zip` and `miami_x/Miami_TA048_velocity_InSAR.tif` (a published velocity map).
  - **Mumbai (reserve):** annual C-1 dangerous-building PDFs. 2018–2020 and 2023–2026 were located; 2021–22 are missing. Needs geocoding; static VLM (VT Figshare 25856260).
    - Codex prepared an audit in `feasibility/mumbai/`, plus `README_CITY_DATASETS.md` and `download_audit_cities.py`. **No files were downloaded:** Codex had no network. Rerun `download_audit_cities.py --download` with network access.
  - **Lagos (not used):** only about 8 collapses after its 2018–2021 InSAR; descriptive only. Codex's audit is in `feasibility/lagos/`.
- **Steps (§17):**
  1. Audit the two cities.
  2. Hong Kong order dates.
  3. Sentinel-1 via ASF HyP3 + MintPy.
  4. **Choose the model from the shape of the data and the number of labels:** a CNN for static maps; a temporal CNN, LSTM or ConvLSTM for time series; attention only if it beats a plain ConvLSTM.
  5. The same safeguards as NYC: frozen plan, spatial folds, LR/RF baselines, spatial null, decoy run.
  
  The user preferred this critique over GPT's "Spatial-Attention ConvLSTM first" proposal.

---

## 9. Lessons and gotchas (learned the hard way)

- **Never edit a log in place** (`sed -i`) while a process writes to it. It replaces the inode, and the process keeps writing to the deleted file. Recover through `/proc/<pid>/fd/1`.
- **`pkill -f <pattern>` kills your own shell** if the pattern appears in the command line. Kill by explicit PID.
- **Launch long runs detached** (`setsid nohup … &`), never attached to the Claude session.
- **joblib (loky) memmaps** go to `/dev/shm/joblib_memmapping_folder_*`. Their file count is a crude progress signal.
- **The memory test** at 8 processes × 2 OOM'd (about 4.5 GB each); size it to the free RAM.
- **pyarrow-backed string arrays** sent to joblib workers caused trouble. Block labels are now integer codes (deviation 3).
- **Sandboxed agents** (Codex) may have no network and no GPU. Check before planning downloads or GPU work.
- **Two agents** (Claude and Codex) must not run or edit this project at the same time.

---

## 10. What is in `handoff/`

- `claude_memory/`: Claude's memory files from the old PC, verbatim (also quoted in section 11).
- `scratchpad/`: everything from the old session's temporary folder, except the Earthdata cookies, the installers and the py-spy env.
  - **Run helpers:** `launch_real.sh`, `mirror_log.sh`.
  - **Checks:** `verify_primary.py` (exact primary recompute; usage `verify_primary.py n_boot`), `repro_boot.py`, `repro_s8.py`, `types_s8.py`, `boot_*_check.csv`, `memtest.py` (never completed).
  - **Next-study data:** `hk/`, `hkbi/`, `miami_dl/`, `miami_x/`, `bct_dl/BuildingCollapseTable.xlsx`.
  - **Sources and papers:** `lagos.txt/.xml`, `tay.txt` (Tay et al. 2022, Nature Sustainability), `ntu.json` and `ntu_readme/` (DR-NTU dataset 10.21979/N9/GPVX0F), `osfdl/` (Alexandria OSF), `sbca/`, `rome/`, `dl/` (Mumbai MCGM web-archive lookups), `licsar33.json`, `opera/README.md`.
  - **Backups and early work:** `pilot_bak/`, `inventory_bak/` (Alexandria pilot and inventory backups from 2026-10-07), `t1/` (report test), `plan_inputs.sha256`.
- `uploads/`: the supervisor brief PDF.
- `transcripts/`: the full Claude session (`claude_session_0e738ef5.jsonl`) and the three Codex sessions of 2026-10-10, with the Earthdata login redacted. Search them for any detail this file lacks.
- `env/`: `pip_freeze.txt` and `machine.txt` (the old PC).

---

## 11. Claude's memory files, verbatim (old PC, 2026-10-11)

These were mostly written before the 10-10 21:50 crash (one line added 2026-10-11); sections 3–6 above supersede the status parts.

### MEMORY.md (index)
```
- [GPU allowed](gpu-allowed.md) — user permits installing GPU deps and using the RTX 2080 Super (CUDA) for heavy compute
- [NYC replication frozen](nyc-replication-frozen.md) — plan frozen 2026-10-08; primary done p=0.418; s8 crash (RAM?) §14 dev 4; resumed 2026-10-10 17:52; crashed again, moving PCs 2026-10-11 (Alex/HANDOFF.md)
- [Next study: Hong Kong + Miami DL](next-study-hong-kong.md) — after NYC report: supervisor DL coastal study, plan §17; HK + Miami-Dade, Mumbai reserve
```

### gpu-allowed.md
```
---
name: gpu-allowed
description: User permits installing GPU dependencies and using the local CUDA GPU for heavy compute
metadata:
  type: user
---

The user said (2026-10-08) that whenever GPU use would help, Claude may download the needed dependencies and use it; CUDA is installed. The machine has an NVIDIA GeForce RTX 2080 Super Max-Q (8 GB, driver 595.91.07).

**Why:** heavy steps in the NYC replication (999-draw variogram nulls, block bootstraps) can be slow on CPU.
**How to apply:** for heavy numeric work, GPU libraries (e.g. CuPy, cuML, PyTorch) may be installed into the project venv without asking. Results must stay identical in method to the frozen plan [[nyc-replication-frozen]]; the GPU is only a speed-up, never a change of model or null.
```

### nyc-replication-frozen.md
```
---
name: nyc-replication-frozen
description: "NYC replication plan frozen 2026-10-08; decoy done; real run primary done (p=0.418), crashed in s8 from suspected RAM fault, resumed 2026-10-10"
metadata:
  type: project
---

Alex/feasibility/nyc/NYC_REPLICATION_PLAN.md was approved by the supervisor and frozen on 2026-10-08. The read-only copy is freeze/NYC_REPLICATION_PLAN_frozen.md (SHA-256 59a2aa1a…). The primary population is the older-building domain (65 events at 250 m, 64 risk sets).

Status on 2026-10-08:
- Checkpoint 2 is done (MANIFEST_PART2 3049dada…).
- The InSAR stage is done (out/insar/MANIFEST bbd5f50a…).
- The decoy is done (out/models/decoy/MANIFEST 57390ac7…; DECOY_REPORT.md).
- §14 deviations:
  1. Connected-component rule.
  2. Reduced decoy draw counts.
  3. The bootstrap's block labels were pyarrow strings that arrived corrupted in joblib workers; they are now integer codes.
- The real run (§13 step 5) started 2026-10-08 16:27. It runs detached (setsid); the log is out/models/real_run.log, and the code is hashed in out/models/CODE_REAL_RUN.sha256 (39e85bdb…).
  - It takes about 3 days; the random forest is last and takes about 2.6 days.
  - If it stops, rerun the same command (`../../.venv/bin/python -I scripts/11_models.py raw out --real --jobs 16`). Finished analyses are skipped. Log any code fix in §14 with before and after values.
  - 2026-10-08 16:52 it crashed in s8 (primary already done: p = 0.418, not replicated). Suspected non-ECC RAM bit-39 flips (same signature as the decoy crash), logged as §14 deviation 4. The user said to stop diagnosing; it was resumed unchanged 2026-10-10 17:52, detached (setsid) via scratchpad launch_real.sh. Budget for secondaries ends ~2026-10-15 16:27.
  - The live log is out/models/real_run_live.log (copied every minute from the running process by scratchpad mirror_log.sh): a `sed -i` on real_run.log on 10-10 replaced its inode, so the process writes to the deleted file. Never edit a log in place while a run writes to it. Merge the two logs at the end.
  - When it ends: run `scripts/12_report.py out --real` to get NYC_RESULT.md, record the result and hashes in §15, and update this memory.
  - 2026-10-11: it crashed again 10-10 21:50 in s2's bootstrap; Codex then resumed it 5 times overnight (checkpoints, repeat checks, 4 jobs; §14 dev 5–8) and every attempt crashed (bit-39 RAM fault). The user is moving the project to another PC. Full state and resume steps: Alex/HANDOFF.md (copies of memory, scratchpad, transcripts in Alex/handoff/).

**Why:** this is a preregistered replication. Every change after the freeze goes in §14, with whether any NYC result had been seen.
**How to apply:** never edit the frozen copy; follow §13's order. The user asked (2026-10-08) to loop until the plan is done, with Sonnet subagents for side work. Never tune after results. See also [[gpu-allowed]].
```

### next-study-hong-kong.md
```
---
name: next-study-hong-kong
description: After the NYC report, next work is the supervisor's deep-learning coastal study; Hong Kong + Miami-Dade (Mumbai reserve); plan in NYC plan §17
metadata:
  type: project
---

On 2026-10-10 the supervisor (after the 7 Oct brief on Mumbai/Hong Kong/Lagos/Miami) asked to download every dataset in the brief and pick a deep-learning model linking satellite data to collapse prediction in coastal cities. The user said to start it only after the NYC ML steps (real run + report) finish. Steps are in Alex/feasibility/nyc/NYC_REPLICATION_PLAN.md §17 (not part of the preregistration).

Cities (user, 2026-10-10: only the best 2 beside NYC, not all four): Hong Kong (main) + Miami-Dade (OPERA time series, folio-located unsafe-structure cases; must pass a bulk-export / ≥100 cases since 2017 check), Mumbai as reserve, Lagos dropped. Order: audit the two → Hong Kong (≈1,320 S26 + 80 S26A buildings with coordinates; first check whether monthly order snapshots since May 2023 exist to date orders) → Sentinel-1 via ASF HyP3 + MintPy → choose DL model from data shape (CNN if static maps; temporal CNN/LSTM/ConvLSTM if time series; attention only if it beats plain ConvLSTM) → same safeguards as NYC (frozen plan, spatial folds, LR/RF baselines, spatial null, decoy). Lagos is descriptive only (≈8 collapses after its 2018–2021 InSAR). Still to confirm with the supervisor: "الانهيارات الأرضية" may mean ground failure, not building failure.

**Why:** the user preferred my critique over GPT's ConvLSTM-first proposal (data and label count decide the model).
**How to apply:** don't start before the NYC report is done; then begin with step 1–3 of §17. Related: [[nyc-replication-frozen]].
```
