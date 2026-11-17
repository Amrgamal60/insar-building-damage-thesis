"""Resume-safe synthetic Monte Carlo runner; sources and config locked per record."""
import os
for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[name] = "1"
import argparse
import copy
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback
import resource
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
import nyc_lib as N
from conditional_null import ConditionalVariogramNull
from cpu_null import CPULowMemVariogramNull
from simulation import city_a, city_b, standardise_at_rows, FEATURES


def source_hashes():
    names = [HERE/"design.json", HERE/"simulation.py", HERE/"cpu_null.py", Path(__file__),
             HERE.parent/"conditional_null.py", HERE.parent/"nyc_lib.py",
             HERE.parent/"lowmem_null.py", HERE.parent/"test_b.py"]
    return {str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in names}


def atomic_json(path, result):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(f".tmp-{os.getpid()}")
    temp.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    temp.replace(path)


def spec_seed(config, test, cell, replicate):
    # Independent streams per test/cell/replicate, no Python hash dependence.
    entropy = [config["master_seed"], 1 if test == "A" else 2, cell, replicate]
    return int(np.random.SeedSequence(entropy).generate_state(1)[0])


def a_stat(data, fields, baseline):
    motion = standardise_at_rows(fields, data)
    prediction = N.oof(np.column_stack([data["X"], motion]), data["y"], data["fold"], N.LR)
    return float(N.average_precision_score(data["y"], prediction)-baseline)


def run_a(config, scenario, link, effect, seed, draws):
    t0 = time.perf_counter()
    generation_config = config
    base_scenario = scenario
    if scenario.endswith("_scale"):
        generation_config = copy.deepcopy(config)
        for key in ("side_m", "occupied_pixels", "houses"):
            generation_config["a"][key] = config["a"]["scale_cells"][key]
        base_scenario = scenario.removesuffix("_scale")
    data = city_a(generation_config, seed, base_scenario, link, effect)
    setup_data = time.perf_counter()-t0
    prediction = N.oof(data["X"], data["y"], data["fold"], N.LR)
    # Exactly sklearn average_precision_score, as N.metrics()['pr']; no trapezoid PR AUC.
    baseline = float(N.average_precision_score(data["y"], prediction))
    observed = a_stat(data, data["fields"], baseline)
    null_opts = config["null"].copy()
    null_opts.pop("draws")
    out = dict(test="A", scenario=scenario, link=link, effect=effect, seed=seed,
               observed=observed, baseline_average_precision=baseline,
               diagnostics=data["diagnostics"], data_setup_seconds=setup_data, nulls={})
    for kind in ("registered", "conditional"):
        start = time.perf_counter()
        if kind == "registered":
            engine = CPULowMemVariogramNull(data["fields"], data["xy"], 30., **null_opts)
        else:
            engine = ConditionalVariogramNull(data["fields"], data["xy"], 30., data["pixel_cov"],
                feature_names=FEATURES, null_factory=CPULowMemVariogramNull, **null_opts)
            out["g_hat_explained_variance"] = engine.explained_variance
        setup = time.perf_counter()-start
        stats, ks = [], []
        null_rng = np.random.default_rng(np.random.SeedSequence([seed, 2033]))
        for field, k in engine.draws(draws, null_rng):
            stats.append(a_stat(data, field, baseline))
            ks.append(int(k))
        exceed = int(np.sum(np.asarray(stats) >= observed))
        p = (1+exceed)/(1+draws)
        out["nulls"][kind] = dict(statistics=stats, chosen_k=ks, exceedances=exceed,
            p=p, reject=p < .05, positive_gain_decision=p < .05 and observed > 0,
            setup_seconds=setup, total_seconds=time.perf_counter()-start)
        del engine
    out["elapsed_seconds"] = time.perf_counter()-t0
    return out


def run_b(config, seed, draws):
    from test_b import null_test
    import warnings
    t0 = time.perf_counter()
    data = city_b(config, seed)
    # B explicitly uses original VariogramNull (CPU fallback); only CUDA visibility
    # differs. Do not monkey-patch the library or refit estimator.
    opts = config["null"].copy()
    opts.pop("draws")
    opts.pop("chunk")
    engine = N.VariogramNull(data["fields"], data["xy"], 250., **opts)
    start = time.perf_counter()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*separated.*")
        result = null_test(data["panel"], engine.draws(draws, np.random.default_rng(np.random.SeedSequence([seed, 2034]))),
                           np.arange(config["b"]["quarters"]), np.arange(len(data["xy"])), expected_draws=draws)
    return dict(test="B", seed=seed, diagnostics=data["diagnostics"],
                observed=result["observed"]["null_statistic"], observed_fit=result["observed"],
                statistics=[r["null_statistic"] for r in result["draws"]],
                signed_betas=[r["beta"] for r in result["draws"]],
                exceedances=result["exceedances"], p=result["p_B"], reject=result["p_B"] < .05,
                null_refit_seconds=time.perf_counter()-start, elapsed_seconds=time.perf_counter()-t0)


def run_job(job):
    config, spec, fingerprint, folder = job
    test, cell, replicate, scenario, link, effect = spec
    path = Path(folder)/f"{test}_{cell:02d}_{replicate:04d}.json"
    if path.exists():
        cached = json.loads(path.read_text())
        if cached["source_hashes"] != fingerprint or cached["spec"] != list(spec):
            raise RuntimeError(f"Source/config mismatch in {path}; refusing mixed run")
        return str(path), True, cached["elapsed_seconds"]
    seed = spec_seed(config, test, cell, replicate)
    try:
        if test == "A":
            result = run_a(config, scenario, link, effect, seed, config["null"]["draws"])
        else:
            result = run_b(config, seed, config["null"]["draws"])
        result.update(source_hashes=fingerprint, spec=list(spec), status="complete")
        atomic_json(path, result)
        return str(path), False, result["elapsed_seconds"]
    except Exception:
        atomic_json(Path(folder)/"errors"/path.name,
                    dict(spec=list(spec), seed=seed, source_hashes=fingerprint, traceback=traceback.format_exc()))
        raise


def specifications(config, test):
    if test == "B":
        return [("B", 0, rep, "size", "none", 0.) for rep in range(config["b"]["datasets"])]
    if test == "S":
        scale = config["a"]["scale_cells"]
        return [("A", cell, rep, scenario+"_scale", scale["link"], 0.)
                for cell, scenario in zip(scale["cell_ids"], scale["scenarios"])
                for rep in range(scale["datasets_per_cell"])]
    specs = []
    cell = 0
    for scenario in config["a"]["null_scenarios"]:
        for link in config["a"]["target_soil_correlations"]:
            specs += [("A", cell, rep, scenario, link, 0.) for rep in range(config["a"]["datasets_per_null_cell"])]
            cell += 1
    for effect in config["a"]["power_effects"]:
        specs += [("A", cell, rep, "A1", config["a"]["power_link"], effect)
                  for rep in range(config["a"]["datasets_per_power_cell"])]
        cell += 1
    return specs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["benchmark", "benchmark-scale", "A", "S", "B"])
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--benchmark-draws", type=int, default=3)
    args = ap.parse_args()
    config = json.loads((HERE/"design.json").read_text())
    # Original VariogramNull supports an explicit CPU fallback; no CUDA at scale.
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    if args.mode == "benchmark-scale":
        a = run_a(config, "N2_scale", "strong", 0., 19002029, args.benchmark_draws)
        out = dict(status="timing_only", draws_per_null=args.benchmark_draws,
                   a_seconds=a["elapsed_seconds"], a_setup_seconds=a["data_setup_seconds"],
                   a_null_timings={k: {s: v[s] for s in ("setup_seconds", "total_seconds")} for k, v in a["nulls"].items()},
                   max_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                   source_hashes=source_hashes())
        atomic_json(HERE/"benchmark_scale.json", out)
        print(json.dumps(out, indent=2), flush=True)
        return
    if args.mode == "benchmark":
        t0 = time.perf_counter()
        a = run_a(config, "N1", "strong", 0., 19002026, args.benchmark_draws)
        b = run_b(config, 19002027, args.benchmark_draws)
        warmed_b = run_b(config, 19002028, args.benchmark_draws)
        out = dict(status="timing_only_before_approval", a_seconds=a["elapsed_seconds"],
                   draws_per_null=args.benchmark_draws,
                   a_setup_seconds=a["data_setup_seconds"],
                   a_null_timings={k: {s: v[s] for s in ("setup_seconds", "total_seconds")} for k, v in a["nulls"].items()},
                   b_seconds=b["elapsed_seconds"], b_refit_seconds=b["null_refit_seconds"],
                   b_warmed_seconds=warmed_b["elapsed_seconds"],
                   b_warmed_refit_seconds=warmed_b["null_refit_seconds"],
                   elapsed_seconds=time.perf_counter()-t0, source_hashes=source_hashes())
        atomic_json(HERE/"benchmark.json", out)
        print(json.dumps(out, indent=2), flush=True)
        return
    approval = HERE/"coordinator_go.txt"
    if not approval.exists():
        raise RuntimeError("Required coordinator design go has not been recorded")
    specs = specifications(config, args.mode)
    if args.limit is not None:
        specs = specs[:args.limit]
    fingerprint = source_hashes()
    folder = HERE/"records"
    start = time.perf_counter()
    done = 0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_job, (config, spec, fingerprint, str(folder))) for spec in specs]
        for future in as_completed(futures):
            path, cached, elapsed = future.result()
            done += 1
            print(json.dumps(dict(completed=done, total=len(specs), path=path, cached=cached,
                                  dataset_seconds=elapsed, wall_seconds=time.perf_counter()-start)), flush=True)


if __name__ == "__main__":
    main()
