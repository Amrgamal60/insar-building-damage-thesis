# Austin variogram-null Monte Carlo calibration

Synthetic data only. No permit table, permit file, private row, outcome, InSAR/OPERA/Sentinel data, or credential store was read. Existing analysis scripts were not modified. All design settings and the coordinator's scale/bias amendments were fixed before inference results.

The full parameter specification and formulas are in [DESIGN.md](DESIGN.md) and [design.json](design.json). The executable data-generating process is [simulation.py](simulation.py). Every dataset and all 99 null statistics are durable under `records/`; [results.json](results.json) contains the aggregate and source hashes.

## Selection result

**Branch 3:** neither null is primary yet. Both fail at least one null cell under the amended rule; the coordinator/user must decide a next design before freezing.

The coordinator added the two 4× scale cells and paired-bias criterion in the pre-scale go (recorded in `coordinator_go.txt`), before any inference result. Test A acceptability requires all three: point rejection rate ≤7.5%, Wilson lower 95% bound ≤5%, and lower 95% t bound for mean paired bias ≤0. A paired bias is observed gain minus that dataset's mean null gain. Power does not enter selection.

## Test A size

Intervals in the rejection columns are 95% Wilson intervals over independent datasets. `OK` below applies the amended rule; `size OK` separately applies the original two size conditions.

| Scenario/link | n | Registered rejection [95% CI] | Conditional rejection [95% CI] | Registered OK / size OK | Conditional OK / size OK |
|---|---:|---|---|---|---|
| N1 / moderate | 200 | 8/200 = 4.0% [2.0%, 7.7%] | 4/200 = 2.0% [0.8%, 5.0%] | True / True | True / True |
| N1 / strong | 200 | 9/200 = 4.5% [2.4%, 8.3%] | 10/200 = 5.0% [2.7%, 9.0%] | True / True | True / True |
| N2 / moderate | 200 | 14/200 = 7.0% [4.2%, 11.4%] | 5/200 = 2.5% [1.1%, 5.7%] | False / True | True / True |
| N2 / strong | 200 | 40/200 = 20.0% [15.0%, 26.1%] | 2/200 = 1.0% [0.3%, 3.6%] | False / False | True / True |
| N3 / moderate | 200 | 13/200 = 6.5% [3.8%, 10.8%] | 8/200 = 4.0% [2.0%, 7.7%] | False / True | False / True |
| N3 / strong | 200 | 2/200 = 1.0% [0.3%, 3.6%] | 3/200 = 1.5% [0.5%, 4.3%] | True / True | True / True |
| N4 / moderate | 200 | 12/200 = 6.0% [3.5%, 10.2%] | 1/200 = 0.5% [0.1%, 2.8%] | True / True | True / True |
| N4 / strong | 200 | 29/200 = 14.5% [10.3%, 20.0%] | 5/200 = 2.5% [1.1%, 5.7%] | False / False | True / True |
| N2_scale / strong | 100 | 30/100 = 30.0% [21.9%, 39.6%] | 0/100 = 0.0% [0.0%, 3.7%] | False / False | True / True |
| N4_scale / strong | 100 | 29/100 = 29.0% [21.0%, 38.5%] | 0/100 = 0.0% [0.0%, 3.7%] | False / False | True / True |

## Observed gains, null draws and paired bias

AP is pooled sklearn average precision in the sampled risk sets, not population precision. Null SD pools 99 draws per dataset descriptively; those draws are not independent datasets. Mean intervals use Student t over datasets, including for paired bias.

| Cell | Observed ΔAP mean ± SD | Observed mean [95% t CI] | Share >0 | Registered null mean ± SD | Conditional null mean ± SD |
|---|---|---|---:|---|---|
| N1 / moderate | -0.0004023 ± 0.0015202 | -0.0004023 [-0.0006143, -0.0001904] | 35.5% | -0.0004079 ± 0.0016697 | -0.0003914 ± 0.0016933 |
| N1 / strong | -0.0004675 ± 0.0018867 | -0.0004675 [-0.0007306, -0.0002044] | 29.0% | -0.0005021 ± 0.0016800 | -0.0005022 ± 0.0017474 |
| N2 / moderate | -0.0005355 ± 0.0095948 | -0.0005355 [-0.0018734, 0.0008024] | 40.0% | -0.0018820 ± 0.0094475 | -0.0004838 ± 0.0106049 |
| N2 / strong | 0.0043665 ± 0.0125404 | 0.0043665 [0.0026179, 0.0061152] | 62.5% | -0.0018752 ± 0.0089151 | 0.0044598 ± 0.0137006 |
| N3 / moderate | 0.0003344 ± 0.0024018 | 0.0003344 [-0.0000005, 0.0006693] | 41.0% | -0.0001968 ± 0.0022594 | 0.0000503 ± 0.0021423 |
| N3 / strong | -0.0002262 ± 0.0020064 | -0.0002262 [-0.0005059, 0.0000536] | 44.0% | -0.0002176 ± 0.0024905 | -0.0002654 ± 0.0021132 |
| N4 / moderate | -0.0001418 ± 0.0123605 | -0.0001418 [-0.0018653, 0.0015818] | 39.5% | -0.0011977 ± 0.0094066 | -0.0000042 ± 0.0110433 |
| N4 / strong | 0.0029987 ± 0.0119042 | 0.0029987 [0.0013388, 0.0046586] | 55.5% | -0.0015503 ± 0.0106587 | 0.0032586 ± 0.0133992 |
| N2_scale / strong | 0.0018079 ± 0.0099559 | 0.0018079 [-0.0001675, 0.0037834] | 55.0% | -0.0014812 ± 0.0039024 | 0.0022431 ± 0.0103480 |
| N4_scale / strong | 0.0027439 ± 0.0084166 | 0.0027439 [0.0010738, 0.0044139] | 61.0% | -0.0010938 ± 0.0048327 | 0.0028646 ± 0.0089920 |
| A1 / strong / β=-0.2 | 0.0016679 ± 0.0031465 | 0.0016679 [0.0010436, 0.0022922] | 76.0% | -0.0003156 ± 0.0016010 | 0.0004819 ± 0.0021776 |
| A1 / strong / β=-0.4 | 0.0079504 ± 0.0061640 | 0.0079504 [0.0067273, 0.0091734] | 94.0% | -0.0003631 ± 0.0019639 | 0.0029604 ± 0.0042744 |

| Cell | Registered paired bias mean [95% t CI] | Conditional paired bias mean [95% t CI] | g_hat in-sample variance explained: mean ± SD |
|---|---|---|---|
| N1 / moderate | 0.0000055 [-0.0001920, 0.0002030] | -0.0000109 [-0.0001934, 0.0001715] | 0.735 ± 0.026 |
| N1 / strong | 0.0000346 [-0.0001913, 0.0002605] | 0.0000347 [-0.0001180, 0.0001875] | 0.825 ± 0.022 |
| N2 / moderate | 0.0013465 [0.0000393, 0.0026537] | -0.0000517 [-0.0006379, 0.0005345] | 0.729 ± 0.026 |
| N2 / strong | 0.0062417 [0.0045536, 0.0079298] | -0.0000933 [-0.0007998, 0.0006133] | 0.826 ± 0.024 |
| N3 / moderate | 0.0005313 [0.0001987, 0.0008639] | 0.0002842 [0.0000849, 0.0004834] | 0.732 ± 0.027 |
| N3 / strong | -0.0000085 [-0.0002485, 0.0002315] | 0.0000393 [-0.0001052, 0.0001838] | 0.824 ± 0.024 |
| N4 / moderate | 0.0010559 [-0.0005907, 0.0027025] | -0.0001376 [-0.0008612, 0.0005860] | 0.731 ± 0.026 |
| N4 / strong | 0.0045490 [0.0029020, 0.0061960] | -0.0002599 [-0.0010096, 0.0004898] | 0.826 ± 0.022 |
| N2_scale / strong | 0.0032891 [0.0013627, 0.0052155] | -0.0004352 [-0.0010814, 0.0002110] | 0.683 ± 0.020 |
| N4_scale / strong | 0.0038376 [0.0021882, 0.0054871] | -0.0001207 [-0.0007265, 0.0004850] | 0.677 ± 0.020 |
| A1 / strong / β=-0.2 | 0.0019835 [0.0014013, 0.0025656] | 0.0011860 [0.0007519, 0.0016201] | 0.826 ± 0.022 |
| A1 / strong / β=-0.4 | 0.0083134 [0.0071566, 0.0094703] | 0.0049900 [0.0042813, 0.0056987] | 0.827 ± 0.022 |

Observed mean ΔAP is systematically positive in the descriptive across-dataset sense when its mean interval's lower bound exceeds zero. This does not by itself show added information beyond baseline features: in N2/N4 it can be a proxy for their omitted nonlinear effect. The paired-bias intervals assess its ranking relative to each null.

## Power (report only)

| A1 residual effect, link | n | Registered power [95% Wilson CI] | Conditional power [95% Wilson CI] | Observed ΔAP mean ± SD | g_hat variance explained |
|---|---:|---|---|---|---|
| A1 / strong / β=-0.2 | 100 | 35/100 = 35.0% [26.4%, 44.7%] | 18/100 = 18.0% [11.7%, 26.7%] | 0.0016679 ± 0.0031465 | 0.826 |
| A1 / strong / β=-0.4 | 100 | 84/100 = 84.0% [75.6%, 89.9%] | 60/100 = 60.0% [50.2%, 69.1%] | 0.0079504 ± 0.0061640 | 0.827 |

Power null-draw means/SD, paired-bias intervals and observed mean intervals are also in `results.json` (same summary schema as null cells). The effect is on generated residual r, not on total v. Power does not change the selection rule.

## p-value histograms

Each vector counts right-closed deciles (0,.1], (.1,.2], …, (.9,1]. Uniform ranks on the 99-draw grid give 10% per decile and strict p<.05 has exact nominal 4% under exchangeability.

| Cell | Registered p deciles | Conditional p deciles |
|---|---|---|
| N1 / moderate | [18, 18, 19, 22, 27, 13, 25, 23, 21, 14] | [15, 19, 20, 22, 29, 15, 17, 27, 20, 16] |
| N1 / strong | [25, 17, 19, 19, 12, 22, 31, 23, 19, 13] | [21, 20, 20, 14, 22, 24, 20, 20, 23, 16] |
| N2 / moderate | [28, 20, 22, 19, 13, 19, 20, 28, 16, 15] | [10, 18, 14, 30, 19, 32, 29, 23, 16, 9] |
| N2 / strong | [74, 29, 19, 14, 10, 13, 11, 12, 7, 11] | [10, 16, 26, 22, 23, 26, 25, 23, 19, 10] |
| N3 / moderate | [20, 28, 21, 18, 28, 14, 25, 16, 19, 11] | [16, 15, 22, 24, 27, 21, 29, 20, 13, 13] |
| N3 / strong | [13, 26, 22, 27, 16, 19, 22, 25, 25, 5] | [16, 22, 20, 17, 27, 20, 21, 22, 26, 9] |
| N4 / moderate | [27, 17, 24, 19, 15, 24, 18, 23, 16, 17] | [6, 20, 21, 28, 19, 24, 25, 20, 27, 10] |
| N4 / strong | [54, 24, 24, 17, 15, 15, 15, 15, 9, 12] | [10, 22, 18, 16, 24, 29, 28, 26, 17, 10] |
| N2_scale / strong | [43, 5, 6, 4, 3, 1, 6, 4, 9, 19] | [1, 6, 12, 17, 15, 15, 11, 10, 8, 5] |
| N4_scale / strong | [44, 10, 5, 4, 1, 9, 5, 6, 6, 10] | [2, 7, 12, 16, 18, 10, 12, 16, 5, 2] |
| A1 / strong / β=-0.2 | [50, 14, 9, 3, 5, 2, 3, 3, 5, 6] | [39, 17, 10, 7, 6, 3, 7, 2, 1, 8] |
| A1 / strong / β=-0.4 | [91, 2, 2, 0, 1, 2, 1, 1, 0, 0] | [75, 14, 4, 3, 1, 2, 0, 1, 0, 0] |

## Realised synthetic-city diagnostics

Correlations are realised finite-city values, not rejection/regeneration targets. Adjacent-window correlation is calculated over occupied pixels; the event count varies by independent hazard draws.

| Cell | Events mean ± SD | Velocity–soil corr mean ± SD | Adjacent-window corr mean ± SD |
|---|---|---|---|
| N1 / moderate | 215.5 ± 15.4 | 0.298 ± 0.098 | 0.9889 ± 0.0015 |
| N1 / strong | 216.0 ± 14.7 | 0.596 ± 0.057 | 0.9927 ± 0.0011 |
| N2 / moderate | 214.7 ± 13.2 | 0.292 ± 0.096 | 0.9887 ± 0.0015 |
| N2 / strong | 215.1 ± 14.1 | 0.605 ± 0.061 | 0.9928 ± 0.0012 |
| N3 / moderate | 216.0 ± 14.2 | 0.291 ± 0.100 | 0.9888 ± 0.0015 |
| N3 / strong | 216.3 ± 14.2 | 0.597 ± 0.065 | 0.9927 ± 0.0012 |
| N4 / moderate | 217.2 ± 13.1 | 0.294 ± 0.109 | 0.9888 ± 0.0015 |
| N4 / strong | 216.4 ± 13.4 | 0.604 ± 0.060 | 0.9927 ± 0.0011 |
| N2_scale / strong | 866.4 ± 27.0 | 0.602 ± 0.029 | 0.9928 ± 0.0005 |
| N4_scale / strong | 867.9 ± 26.2 | 0.595 ± 0.030 | 0.9927 ± 0.0006 |
| A1 / strong / β=-0.2 | 213.8 ± 14.3 | 0.597 ± 0.059 | 0.9928 ± 0.0011 |
| A1 / strong / β=-0.4 | 218.1 ± 13.6 | 0.602 ± 0.054 | 0.9928 ± 0.0011 |

## Test B basic size

Rejection: **5/200 = 2.5% [1.1%, 5.7%]**. Original size acceptability: **True**. The report-only paired-bias diagnostic is **0.0009948 [-0.0015127, 0.0035023]**, with lower-bound criterion passing: **True**. No Test B switch is attached.

Observed |β|: mean 0.0260377, SD 0.0177182; null |β|: mean 0.0250429, SD 0.0189958. p deciles: **[23, 22, 21, 23, 18, 15, 24, 21, 16, 17]**.

The unchanged `test_b.fit_panel` and `null_test` fit PPML with cell/quarter fixed effects, log exposure offset, and CRV1 by 2 km blocks. The unchanged `nyc_lib.VariogramNull` uses quarters as windows, 99 draws, k cap 1,000 and its existing NumPy/SciPy CPU fallback. The observed estimation sample is fixed across null refits, including FE separation removals.

## Diagnosis and proposed next step

Registered failing cells: N2 / moderate, N2 / strong, N3 / moderate, N4 / strong, N2_scale / strong, N4_scale / strong. Conditional failing cells: N3 / moderate. Separate size failures from positive paired-bias failures using the table above. Under N2/N4, velocity contains a nonlinear function of soil omitted from the fitted linear baseline, so an observed AP gain can represent an existing-feature proxy. A registered surrogate breaks that relationship; keeping an estimated mean only partially addresses the problem when its residual process is not conditionally exchangeable. N3/N4 also expose the effect of finite-city overlap of independent spatial fields. These are mechanism-based interpretations of the fixed design, not proof of a unique empirical cause. A proposed alternative, NOT implemented or selected here, is to define the target explicitly as value beyond a fixed flexible baseline model that includes nonlinear soil effects and interactions, with spatially honest nuisance fitting; then calibrate a conditional generator that models residual covariance/variance given baseline features on fresh prespecified synthetic scenarios and independent seeds. Any such change affects the estimand/model and requires the coordinator/user's registration before a new run. The current failed null is not repaired by tuning its threshold, effect size, or HGB settings on these results.

## Implementation, audit and runtime

Registered Test A uses exactly the inherited `LowMemVariogramNull._vario` and `VariogramNull.draws`; only NumPy/SciPy constructor allocation replaces CuPy/cupyx in the calibration adapter. A real GPU comparison on a small synthetic masked field agreed to 2.40e−14, with identical chosen k and masks. Original nyc_lib, lowmem_null and test_b hashes remain unchanged and are recorded per dataset. The conditional production module defaults to the unchanged GPU class and accepts a compatible backend factory for CPU checks.

The conditional fit is separate in-sample HGB per window on seven pixel-mean covariates excluding x/y: squared error, learning rate .1, 100 iterations, 15 leaves, minimum leaf 20, L2=1, max bins 255, no early stopping, random_state=0. Residual fields enter the same generator; g_hat is added back before parcel standardisation and identical OOF refits. The explained-variance figures above are in-sample, not predictive validation.

Record audit: **2200/2200** expected datasets complete, no missing/mismatched/extra records, every p-value recomputed from all 99 saved statistics, and no dataset or draw discarded. Total sum of dataset compute times: 206.067 hours (parallel work overlaps). Individual dataset runtime median 280.80 s; maximum 3056.06 s. Actual run logs provide wall-time progress; timing-only projections were not treated as completed inference.

The initial nvidia-smi check found 1,186 MiB free. One bounded GPU unit-check process used a 15.23 MiB CuPy pool (256 MiB cap). Completed-dataset devices: **{'cpu': 2001, 'gpu': 199}**. GPU eligibility follows the later coordinator rule: at most min(8 GiB, free minus 1 GiB), one producer, automatic CPU fallback. No other GPU process was stopped and no packages were installed. CPU workers use one thread each; concurrency can be capped for RAM. Completed records resume atomically and reject changed source/config hashes.

## Rerun commands

Run from `/mnt/data/Master-projects/Alex` in the existing `.venv`; no install is required. The original coordinator go is recorded in this directory. The following commands reuse all verified completed records; do not overwrite the design or source mid-run.

```sh
.venv/bin/python -I feasibility/austin/scripts/calibration/check_conditional.py
.venv/bin/python -I feasibility/austin/scripts/calibration/check_execution.py
.venv/bin/python -I feasibility/austin/scripts/calibration/run_workload.py
.venv/bin/python -I feasibility/austin/scripts/calibration/summarize.py
```

The GPU unit check requires at least 700 MiB free before CUDA initialisation. Existing unit_results.json documents the completed check. The workload driver enforces cell-complete scheduling and records actual device use; its optional GPU path checks the first actual draw against CPU for each method/dataset. Rerunning verification changes runtime/log file hashes, so refresh the delivered manifest after intentional reruns.

## Limits

These scenarios test specific nuisance processes; passing them does not prove size in Austin, conditional exchangeability, or identifiability of a physical effect. Austin-scale event counts, heterogeneous coverage/construction masks, missing covariates, demolition and matched-episode histories, and the option-C reduced baseline are UNVERIFIED. Test A accelerates monthly incidence to keep six-year cumulative incidence in twelve months; a full 72-month, 72-window experiment is UNVERIFIED. The large cells have approximately 864 events, still below Austin's expected count. Soil/income/terrain are synthetic proxies with periodic boundaries, not reconstructed Austin geography. Only full-feature logistic Baseline 1 is calibrated; random forests and the deep model are UNVERIFIED here.

In-sample flexible residualisation can overfit, preserve incidental baseline relationships, and leave spatially varying residual means/variances; it cannot guarantee that residuals are independent of features. Variogram matching targets limited lags, not all higher-order or joint temporal structure. This experiment does not validate unknown real conditional distributions or establish that its hidden field is the only form of spatial confounding. Finite Monte Carlo intervals and the amended multi-cell pass/fail rule add uncertainty; size/power are conditional on this fixed generator and event/control sampling. Unit arithmetic equality is established on the recorded small field and environment, not bit equality across machines or all city sizes.

## Coordinator addendum (2026-11-06)

Added by the coordinator (Claude) after `summarize.py` wrote the sections above. Rerunning `summarize.py` rewrites this file without this section.

- **Independent check.** `coordinator_rule_check.py` applies the registered rule to the records without this report's code. All 20 null-cell rows (rejections, Wilson bounds, paired-bias means and intervals, acceptability) are identical, and both give branch 3 (`coordinator_rule_check.json`). Power (A_08, A_09) and the Test B size check were also recounted from the records' saved statistics, with the same counts.
- **Execution history.** The run was moved between workers, scheduled partly on the GPU, killed once by systemd-oomd, stopped at the user's request, and resumed on 2026-11-06. Details are in [COORDINATOR_EXECUTION_NOTES.md](COORDINATOR_EXECUTION_NOTES.md). Every record carries the same source fingerprint.
- **Decision under branch 3.** On 2026-11-06 the user chose the conditional null (b) as the primary Test A null, with the registered null (a) as secondary (AUSTIN_PLAN.md §10). The alternative proposed in the diagnosis above was not adopted. The choice was made from the null cells, before the power cells finished; power does not enter the rule. Under (b), the bias failure in N3 / moderate is reported as a limit, not resolved.
