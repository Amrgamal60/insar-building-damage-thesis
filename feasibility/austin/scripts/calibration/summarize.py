"""Audit durable Monte Carlo records and generate the calibration report."""
import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[key] = "1"
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import numpy as np
from scipy.stats import norm, t

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
from run_calibration import source_hashes, specifications, spec_seed, atomic_json


def wilson(k, n):
    z = norm.ppf(.975)
    p = k/n
    centre = (p+z*z/(2*n))/(1+z*z/n)
    half = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [float(centre-half), float(centre+half)]


def moments(values):
    x = np.asarray(values, dtype=float)
    return dict(mean=float(x.mean()), sd=float(x.std(ddof=1)), n=int(x.size))


def mean_interval(values):
    m = moments(values)
    half = float(t.ppf(.975, m["n"]-1)*m["sd"]/np.sqrt(m["n"]))
    return dict(**m, ci95=[m["mean"]-half, m["mean"]+half])


def hist(p):
    return np.bincount(np.clip(np.ceil(np.asarray(p)*10).astype(int)-1, 0, 9), minlength=10).tolist()


def summarize_cell(records, kind=None):
    observed = np.asarray([r["observed"] for r in records])
    nulls = [r if kind is None else r["nulls"][kind] for r in records]
    p = [r["p"] for r in nulls]
    k = sum(v < .05 for v in p)
    n = len(records)
    interval = wilson(k, n)
    bias = [r["observed"]-np.mean(s["statistics"]) for r, s in zip(records, nulls)]
    bias_summary = mean_interval(bias)
    size_ok = interval[0] <= .05 and k/n <= .075
    bias_ok = bias_summary["ci95"][0] <= 0
    return dict(datasets=n, rejections=k, rejection_rate=k/n, wilson95=interval,
        size_acceptable=size_ok, bias_acceptable=bias_ok,
        acceptable=size_ok and bias_ok, p_histogram_deciles=hist(p),
        observed=mean_interval(observed), observed_positive_share=float(np.mean(observed > 0)),
        null_pooled=moments([s for r in nulls for s in r["statistics"]]),
        null_dataset_means=moments([np.mean(r["statistics"]) for r in nulls]),
        paired_bias=bias_summary,
        positive_gain_rejections=sum(s["p"] < .05 and r["observed"] > 0 for r, s in zip(records, nulls)))


def audit(config):
    expected = specifications(config, "A")+specifications(config, "S")+specifications(config, "B")
    fingerprint = source_hashes()
    records, missing, errors = [], [], []
    expected_paths = set()
    for spec in expected:
        test, cell, rep, scenario, link, effect = spec
        path = HERE/"records"/f"{test}_{cell:02d}_{rep:04d}.json"
        expected_paths.add(path.name)
        if not path.exists():
            missing.append(path.name)
            continue
        r = json.loads(path.read_text())
        try:
            assert r["status"] == "complete"
            assert r["spec"] == list(spec)
            assert r["source_hashes"] == fingerprint
            assert r["seed"] == spec_seed(config, test, cell, rep)
            methods = r["nulls"].values() if test == "A" else [r]
            for null in methods:
                assert len(null["statistics"]) == config["null"]["draws"]
                assert np.isfinite(null["statistics"]).all()
                exceed = int(np.sum(np.asarray(null["statistics"]) >= r["observed"]))
                assert null["exceedances"] == exceed
                assert null["p"] == (1+exceed)/(1+config["null"]["draws"])
                assert null["reject"] == (null["p"] < .05)
            assert np.isfinite(r["observed"])
        except (AssertionError, KeyError) as exc:
            errors.append(dict(path=path.name, error=repr(exc)))
        records.append(r)
    unexpected = [p.name for p in (HERE/"records").glob("*.json") if p.name not in expected_paths]
    return records, dict(expected=len(expected), complete=len(records), missing=missing,
                         validation_errors=errors, unexpected=unexpected, source_hashes=fingerprint)


def pc(x):
    return f"{100*x:.1f}%"


def rate_cell(s):
    return f"{s['rejections']}/{s['datasets']} = {pc(s['rejection_rate'])} [{pc(s['wilson95'][0])}, {pc(s['wilson95'][1])}]"


def num(x):
    return f"{x:.7f}"


def ci(s):
    return f"{num(s['mean'])} [{num(s['ci95'][0])}, {num(s['ci95'][1])}]"


def make_report(result):
    lines = ["# Austin variogram-null Monte Carlo calibration", "",
        "Synthetic data only. No permit table, permit file, private row, outcome, InSAR/OPERA/Sentinel data, or credential store was read. Existing analysis scripts were not modified. All design settings and the coordinator's scale/bias amendments were fixed before inference results.", "",
        "The full parameter specification and formulas are in [DESIGN.md](DESIGN.md) and [design.json](design.json). The executable data-generating process is [simulation.py](simulation.py). Every dataset and all 99 null statistics are durable under `records/`; [results.json](results.json) contains the aggregate and source hashes.", "",
        "## Selection result", "", result["selection"]["conclusion"], "",
        "The coordinator added the two 4× scale cells and paired-bias criterion in the pre-scale go (recorded in `coordinator_go.txt`), before any inference result. Test A acceptability requires all three: point rejection rate ≤7.5%, Wilson lower 95% bound ≤5%, and lower 95% t bound for mean paired bias ≤0. A paired bias is observed gain minus that dataset's mean null gain. Power does not enter selection.", "",
        "## Test A size", "",
        "Intervals in the rejection columns are 95% Wilson intervals over independent datasets. `OK` below applies the amended rule; `size OK` separately applies the original two size conditions.", "",
        "| Scenario/link | n | Registered rejection [95% CI] | Conditional rejection [95% CI] | Registered OK / size OK | Conditional OK / size OK |",
        "|---|---:|---|---|---|---|"]
    for cell in result["a_null"]:
        a, b = cell["registered"], cell["conditional"]
        lines.append(f"| {cell['label']} | {a['datasets']} | {rate_cell(a)} | {rate_cell(b)} | {a['acceptable']} / {a['size_acceptable']} | {b['acceptable']} / {b['size_acceptable']} |")
    lines += ["", "## Observed gains, null draws and paired bias", "",
        "AP is pooled sklearn average precision in the sampled risk sets, not population precision. Null SD pools 99 draws per dataset descriptively; those draws are not independent datasets. Mean intervals use Student t over datasets, including for paired bias.", "",
        "| Cell | Observed ΔAP mean ± SD | Observed mean [95% t CI] | Share >0 | Registered null mean ± SD | Conditional null mean ± SD |",
        "|---|---|---|---:|---|---|"]
    for cell in result["a_null"]+result["a_power"]:
        a, b = cell["registered"], cell["conditional"]
        o, na, nb = a["observed"], a["null_pooled"], b["null_pooled"]
        lines.append(f"| {cell['label']} | {num(o['mean'])} ± {num(o['sd'])} | {ci(o)} | {pc(a['observed_positive_share'])} | {num(na['mean'])} ± {num(na['sd'])} | {num(nb['mean'])} ± {num(nb['sd'])} |")
    lines += ["", "| Cell | Registered paired bias mean [95% t CI] | Conditional paired bias mean [95% t CI] | g_hat in-sample variance explained: mean ± SD |",
              "|---|---|---|---|"]
    for cell in result["a_null"]+result["a_power"]:
        ev = cell["g_hat_explained_variance"]
        lines.append(f"| {cell['label']} | {ci(cell['registered']['paired_bias'])} | {ci(cell['conditional']['paired_bias'])} | {ev['mean']:.3f} ± {ev['sd']:.3f} |")
    lines += ["", "Observed mean ΔAP is systematically positive in the descriptive across-dataset sense when its mean interval's lower bound exceeds zero. This does not by itself show added information beyond baseline features: in N2/N4 it can be a proxy for their omitted nonlinear effect. The paired-bias intervals assess its ranking relative to each null.", "",
        "## Power (report only)", "",
        "| A1 residual effect, link | n | Registered power [95% Wilson CI] | Conditional power [95% Wilson CI] | Observed ΔAP mean ± SD | g_hat variance explained |",
        "|---|---:|---|---|---|---|"]
    for cell in result["a_power"]:
        a, b = cell["registered"], cell["conditional"]
        o = a["observed"]
        lines.append(f"| {cell['label']} | {a['datasets']} | {rate_cell(a)} | {rate_cell(b)} | {num(o['mean'])} ± {num(o['sd'])} | {cell['g_hat_explained_variance']['mean']:.3f} |")
    lines += ["", "Power null-draw means/SD, paired-bias intervals and observed mean intervals are also in `results.json` (same summary schema as null cells). The effect is on generated residual r, not on total v. Power does not change the selection rule.", "",
        "## p-value histograms", "",
        "Each vector counts right-closed deciles (0,.1], (.1,.2], …, (.9,1]. Uniform ranks on the 99-draw grid give 10% per decile and strict p<.05 has exact nominal 4% under exchangeability.", "",
        "| Cell | Registered p deciles | Conditional p deciles |", "|---|---|---|"]
    for cell in result["a_null"]+result["a_power"]:
        lines.append(f"| {cell['label']} | {cell['registered']['p_histogram_deciles']} | {cell['conditional']['p_histogram_deciles']} |")
    lines += ["", "## Realised synthetic-city diagnostics", "",
        "Correlations are realised finite-city values, not rejection/regeneration targets. Adjacent-window correlation is calculated over occupied pixels; the event count varies by independent hazard draws.", "",
        "| Cell | Events mean ± SD | Velocity–soil corr mean ± SD | Adjacent-window corr mean ± SD |",
        "|---|---|---|---|"]
    for cell in result["a_null"]+result["a_power"]:
        e, s, w = cell["diagnostics"]["events"], cell["soil_velocity_correlation"], cell["adjacent_window_correlation"]
        lines.append(f"| {cell['label']} | {e['mean']:.1f} ± {e['sd']:.1f} | {s['mean']:.3f} ± {s['sd']:.3f} | {w['mean']:.4f} ± {w['sd']:.4f} |")
    b = result["b"]
    lines += ["", "## Test B basic size", "",
        f"Rejection: **{rate_cell(b)}**. Original size acceptability: **{b['size_acceptable']}**. The report-only paired-bias diagnostic is **{ci(b['paired_bias'])}**, with lower-bound criterion passing: **{b['bias_acceptable']}**. No Test B switch is attached.", "",
        f"Observed |β|: mean {num(b['observed']['mean'])}, SD {num(b['observed']['sd'])}; null |β|: mean {num(b['null_pooled']['mean'])}, SD {num(b['null_pooled']['sd'])}. p deciles: **{b['p_histogram_deciles']}**.", "",
        "The unchanged `test_b.fit_panel` and `null_test` fit PPML with cell/quarter fixed effects, log exposure offset, and CRV1 by 2 km blocks. The unchanged `nyc_lib.VariogramNull` uses quarters as windows, 99 draws, k cap 1,000 and its existing NumPy/SciPy CPU fallback. The observed estimation sample is fixed across null refits, including FE separation removals.", "",
        "## Diagnosis and proposed next step", "", result["diagnosis"], "",
        "## Implementation, audit and runtime", "",
        "Registered Test A uses exactly the inherited `LowMemVariogramNull._vario` and `VariogramNull.draws`; only NumPy/SciPy constructor allocation replaces CuPy/cupyx in the calibration adapter. A real GPU comparison on a small synthetic masked field agreed to 2.40e−14, with identical chosen k and masks. Original nyc_lib, lowmem_null and test_b hashes remain unchanged and are recorded per dataset. The conditional production module defaults to the unchanged GPU class and accepts a compatible backend factory for CPU checks.", "",
        "The conditional fit is separate in-sample HGB per window on seven pixel-mean covariates excluding x/y: squared error, learning rate .1, 100 iterations, 15 leaves, minimum leaf 20, L2=1, max bins 255, no early stopping, random_state=0. Residual fields enter the same generator; g_hat is added back before parcel standardisation and identical OOF refits. The explained-variance figures above are in-sample, not predictive validation.", "",
        f"Record audit: **{result['audit']['complete']}/{result['audit']['expected']}** expected datasets complete, no missing/mismatched/extra records, every p-value recomputed from all 99 saved statistics, and no dataset or draw discarded. Total sum of dataset compute times: {result['runtime']['sum_dataset_hours']:.3f} hours (parallel work overlaps). Individual dataset runtime median {result['runtime']['median_dataset_seconds']:.2f} s; maximum {result['runtime']['max_dataset_seconds']:.2f} s. Actual run logs provide wall-time progress; timing-only projections were not treated as completed inference.", "",
        f"The initial nvidia-smi check found 1,186 MiB free. One bounded GPU unit-check process used a 15.23 MiB CuPy pool (256 MiB cap). Completed-dataset devices: **{result['execution_devices']}**. GPU eligibility follows the later coordinator rule: at most min(8 GiB, free minus 1 GiB), one producer, automatic CPU fallback. No other GPU process was stopped and no packages were installed. CPU workers use one thread each; concurrency can be capped for RAM. Completed records resume atomically and reject changed source/config hashes.", "",
        "## Rerun commands", "", "Run from `/mnt/data/Master-projects/Alex` in the existing `.venv`; no install is required. The original coordinator go is recorded in this directory. The following commands reuse all verified completed records; do not overwrite the design or source mid-run.", "", "```sh",
        ".venv/bin/python -I feasibility/austin/scripts/calibration/check_conditional.py",
        ".venv/bin/python -I feasibility/austin/scripts/calibration/check_execution.py",
        ".venv/bin/python -I feasibility/austin/scripts/calibration/run_workload.py",
        ".venv/bin/python -I feasibility/austin/scripts/calibration/summarize.py",
        "```", "",
        "The GPU unit check requires at least 700 MiB free before CUDA initialisation. Existing unit_results.json documents the completed check. The workload driver enforces cell-complete scheduling and records actual device use; its optional GPU path checks the first actual draw against CPU for each method/dataset. Rerunning verification changes runtime/log file hashes, so refresh the delivered manifest after intentional reruns.", "",
        "## Limits", "",
        "These scenarios test specific nuisance processes; passing them does not prove size in Austin, conditional exchangeability, or identifiability of a physical effect. Austin-scale event counts, heterogeneous coverage/construction masks, missing covariates, demolition and matched-episode histories, and the option-C reduced baseline are UNVERIFIED. Test A accelerates monthly incidence to keep six-year cumulative incidence in twelve months; a full 72-month, 72-window experiment is UNVERIFIED. The large cells have approximately 864 events, still below Austin's expected count. Soil/income/terrain are synthetic proxies with periodic boundaries, not reconstructed Austin geography. Only full-feature logistic Baseline 1 is calibrated; random forests and the deep model are UNVERIFIED here.", "",
        "In-sample flexible residualisation can overfit, preserve incidental baseline relationships, and leave spatially varying residual means/variances; it cannot guarantee that residuals are independent of features. Variogram matching targets limited lags, not all higher-order or joint temporal structure. This experiment does not validate unknown real conditional distributions or establish that its hidden field is the only form of spatial confounding. Finite Monte Carlo intervals and the amended multi-cell pass/fail rule add uncertainty; size/power are conditional on this fixed generator and event/control sampling. Unit arithmetic equality is established on the recorded small field and environment, not bit equality across machines or all city sizes.", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--progress", action="store_true", help="Audit counts only, permit incomplete runs")
    args = ap.parse_args()
    config = json.loads((HERE/"design.json").read_text())
    records, audit_result = audit(config)
    if args.progress:
        print(json.dumps(dict(expected=audit_result["expected"], complete=audit_result["complete"],
                             by_cell=dict(Counter(f"{r['spec'][0]}_{r['spec'][1]:02d}" for r in records)),
                             errors=audit_result["validation_errors"], unexpected=audit_result["unexpected"]), indent=2))
        return
    if audit_result["missing"] or audit_result["validation_errors"] or audit_result["unexpected"]:
        atomic_json(HERE/"incomplete_audit.json", audit_result)
        raise RuntimeError("Incomplete or inconsistent calibration; no inference report produced")
    a_null, a_power = [], []
    for cell in range(12):
        rs = [r for r in records if r["test"] == "A" and r["spec"][1] == cell]
        first = rs[0]
        label = f"{first['scenario']} / {first['link']}"
        if first["scenario"] == "A1":
            label += f" / β={first['effect']}"
        out = dict(label=label, cell_id=cell, scenario=first["scenario"], link=first["link"],
                   effect=first["effect"], registered=summarize_cell(rs, "registered"),
                   conditional=summarize_cell(rs, "conditional"),
                   g_hat_explained_variance=moments([v for r in rs for v in r["g_hat_explained_variance"]]),
                   diagnostics={key: moments([r["diagnostics"][key] for r in rs])
                                for key in ("events", "rows", "houses", "occupied_pixels", "blocks")},
                   soil_velocity_correlation=moments([v for r in rs for v in r["diagnostics"]["soil_velocity_correlations"]]),
                   adjacent_window_correlation=moments([v for r in rs for v in r["diagnostics"]["adjacent_window_correlations"]]))
        (a_power if first["scenario"] == "A1" else a_null).append(out)
    fail_a = [c["label"] for c in a_null if not c["registered"]["acceptable"]]
    fail_b = [c["label"] for c in a_null if not c["conditional"]["acceptable"]]
    if not fail_a:
        branch = 1
        conclusion = "**Branch 1:** registered null remains primary; conditional null is secondary. Registered null is acceptable in every small and scale null cell under the amended rule."
    elif not fail_b:
        branch = 2
        conclusion = "**Branch 2:** conditional null becomes primary; registered null is secondary. Registered null fails at least one cell; conditional null is acceptable in all small and scale null cells under the amended rule."
    else:
        branch = 3
        conclusion = "**Branch 3:** neither null is primary yet. Both fail at least one null cell under the amended rule; the coordinator/user must decide a next design before freezing."
    diagnosis = (f"Registered failing cells: {', '.join(fail_a) or 'none'}. Conditional failing cells: {', '.join(fail_b) or 'none'}. "
        "Separate size failures from positive paired-bias failures using the table above. Under N2/N4, velocity contains a nonlinear function of soil omitted from the fitted linear baseline, so an observed AP gain can represent an existing-feature proxy. A registered surrogate breaks that relationship; keeping an estimated mean only partially addresses the problem when its residual process is not conditionally exchangeable. N3/N4 also expose the effect of finite-city overlap of independent spatial fields. These are mechanism-based interpretations of the fixed design, not proof of a unique empirical cause. "
        + ("A proposed alternative, NOT implemented or selected here, is to define the target explicitly as value beyond a fixed flexible baseline model that includes nonlinear soil effects and interactions, with spatially honest nuisance fitting; then calibrate a conditional generator that models residual covariance/variance given baseline features on fresh prespecified synthetic scenarios and independent seeds. Any such change affects the estimand/model and requires the coordinator/user's registration before a new run. The current failed null is not repaired by tuning its threshold, effect size, or HGB settings on these results." if branch == 3 else
           "The selected primary is supported only for the tested generator family. Keep the other null as secondary and retain the calibration limitations; no threshold, scenario effect or HGB setting was tuned on the results."))
    b_records = [r for r in records if r["test"] == "B"]
    times = [r["elapsed_seconds"] for r in records]
    result = dict(audit=audit_result, a_null=a_null, a_power=a_power, b=summarize_cell(b_records),
                  execution_devices=dict(Counter(r.get("execution_backend", "cpu_legacy") for r in records)),
                  selection=dict(branch=branch, conclusion=conclusion,
                                 registered_failing_cells=fail_a, conditional_failing_cells=fail_b),
                  diagnosis=diagnosis, runtime=dict(sum_dataset_hours=sum(times)/3600,
                  median_dataset_seconds=float(np.median(times)), max_dataset_seconds=max(times)))
    atomic_json(HERE/"results.json", result)
    (HERE/"CALIBRATION.md").write_text(make_report(result))
    print(conclusion)
    for cell in a_null:
        print(cell["label"], rate_cell(cell["registered"]), rate_cell(cell["conditional"]))
    for cell in a_power:
        print(cell["label"], rate_cell(cell["registered"]), rate_cell(cell["conditional"]))
    print("Test B", rate_cell(result["b"]))


if __name__ == "__main__":
    main()
