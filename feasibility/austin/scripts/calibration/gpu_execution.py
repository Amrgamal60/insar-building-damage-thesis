"""Execution-only GPU producer with unchanged nulls and CPU OOF refits.

No scientific settings differ from run_calibration.py. GPU window chunking is
one instead of eight to bound memory; equality to the eight-window CPU adapter
is checked on the first actual draw of each method/dataset, tolerance 1e-11.
Only one process creates a CUDA context. CPU fit workers use spawn and hide CUDA.
"""
import os
for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[name] = "1"
import copy
import gc
import hashlib
import json
import multiprocessing as mp
from multiprocessing import shared_memory
from pathlib import Path
import subprocess
import time
import numpy as np
import nyc_lib as N
from lowmem_null import LowMemVariogramNull
from conditional_null import ConditionalVariogramNull
from cpu_null import CPULowMemVariogramNull
from simulation import city_a, city_b, standardise_at_rows, FEATURES
from run_calibration import source_hashes, atomic_json, spec_seed

HERE = Path(__file__).resolve().parent
_SHARED = None


def cpu_init():
    os.environ["CUDA_VISIBLE_DEVICES"] = ""


def shared_fit(specs, velocity, baseline):
    global _SHARED
    names = tuple(s[0] for s in specs)
    if _SHARED is None or _SHARED[0] != names:
        if _SHARED is not None:
            for memory in _SHARED[1]:
                memory.close()
        memories = [shared_memory.SharedMemory(name=s[0]) for s in specs]
        arrays = [np.ndarray(s[1], dtype=np.dtype(s[2]), buffer=m.buf) for s, m in zip(specs, memories)]
        _SHARED = names, memories, arrays
    X, y, fold = _SHARED[2]
    prediction = N.oof(np.column_stack([X, velocity]), y, fold, N.LR)
    return float(N.average_precision_score(y, prediction)-baseline)


def current_free():
    out = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], text=True, timeout=15)
    return int(out.splitlines()[0])


def ready(label):
    # Includes >=1 GiB reserve, conservative CUDA context overhead and pool.
    need = 2400 if label.startswith("A_") and int(label[2:]) < 10 else 4000
    return current_free() >= need


def bounded_cupy():
    free = current_free()
    allowed = min(8192, free-1024)
    if allowed < 1200:
        raise MemoryError("Not enough VRAM after mandatory one-GiB reserve")
    import cupy as cp
    gc.collect()
    cp.get_default_memory_pool().free_all_blocks()
    cp.get_default_memory_pool().set_limit(size=(allowed-512)*1024**2)
    return cp, dict(free_before_mib=free, allowed_total_mib=allowed, pool_cap_mib=allowed-512)


def make_engine(kind, fields, xy, covariates, chunk=1, cpu=False):
    factory = CPULowMemVariogramNull if cpu else LowMemVariogramNull
    if kind == "registered":
        return factory(fields, xy, 30., kmax=1000, max_lag=16, chunk=chunk)
    return ConditionalVariogramNull(fields, xy, 30., covariates, feature_names=FEATURES,
        kmax=1000, max_lag=16, chunk=chunk, null_factory=factory)


def run_a_gpu(config, spec, pool):
    test, cell, replicate, scenario, link, effect = spec
    seed = spec_seed(config, test, cell, replicate)
    t0 = time.perf_counter()
    cfg = copy.deepcopy(config)
    if scenario.endswith("_scale"):
        for key in ("side_m", "occupied_pixels", "houses"):
            cfg["a"][key] = config["a"]["scale_cells"][key]
    data = city_a(cfg, seed, scenario.removesuffix("_scale"), link, effect)
    data_setup = time.perf_counter()-t0
    baseline_prediction = N.oof(data["X"], data["y"], data["fold"], N.LR)
    baseline = float(N.average_precision_score(data["y"], baseline_prediction))
    original_velocity = standardise_at_rows(data["fields"], data)
    prediction = N.oof(np.column_stack([data["X"], original_velocity]), data["y"], data["fold"], N.LR)
    observed = float(N.average_precision_score(data["y"], prediction)-baseline)
    cp, memory_report = bounded_cupy()
    out = dict(test="A", scenario=scenario, link=link, effect=effect, seed=seed,
        observed=observed, baseline_average_precision=baseline, diagnostics=data["diagnostics"],
        data_setup_seconds=data_setup, nulls={}, execution_backend="gpu",
        gpu_memory=memory_report, equality_checks={})
    memories, shared_specs = [], []
    for array in (data["X"], data["y"], data["fold"]):
        array = np.ascontiguousarray(array)
        memory = shared_memory.SharedMemory(create=True, size=array.nbytes)
        np.ndarray(array.shape, dtype=array.dtype, buffer=memory.buf)[:] = array
        memories.append(memory)
        shared_specs.append((memory.name, array.shape, array.dtype.str))
    try:
        for kind in ("registered", "conditional"):
            start = time.perf_counter()
            engine = make_engine(kind, data["fields"], data["xy"], data["pixel_cov"])
            if kind == "conditional":
                out["g_hat_explained_variance"] = engine.explained_variance
            setup = time.perf_counter()-start
            seedseq = [seed, 2033]
            # Actual first draw, same RNG, CPU chunk=8 versus GPU chunk=1.
            cpu = make_engine(kind, data["fields"], data["xy"], data["pixel_cov"], chunk=8, cpu=True)
            fc, kc = next(cpu.draws(1, np.random.default_rng(np.random.SeedSequence(seedseq))))
            fg, kg = next(engine.draws(1, np.random.default_rng(np.random.SeedSequence(seedseq))))
            delta = float(np.nanmax(np.abs(fc-fg)))
            if kc != kg or delta > 1e-11 or not np.array_equal(np.isnan(fc), np.isnan(fg)):
                raise ArithmeticError(f"CPU/GPU equality failed: k {kc}/{kg}, difference {delta}")
            out["equality_checks"][kind] = dict(max_abs_difference=delta, same_k=True, same_mask=True)
            del cpu, fc, fg
            futures, ks = [], []
            rng = np.random.default_rng(np.random.SeedSequence(seedseq))
            for field, k in engine.draws(config["null"]["draws"], rng):
                motion = standardise_at_rows(field, data)
                futures.append(pool.submit(shared_fit, shared_specs, motion, baseline))
                ks.append(int(k))
            stats = [f.result() for f in futures]
            exceed = int(np.sum(np.asarray(stats) >= observed))
            p = (1+exceed)/(1+len(stats))
            out["nulls"][kind] = dict(statistics=stats, chosen_k=ks, exceedances=exceed,
                p=p, reject=p < .05, positive_gain_decision=p < .05 and observed > 0,
                setup_seconds=setup, total_seconds=time.perf_counter()-start)
            del engine, field
            gc.collect()
            cp.get_default_memory_pool().free_all_blocks()
    finally:
        if "futures" in locals():
            for future in futures:
                try:
                    future.result()
                except Exception:
                    pass
        for memory in memories:
            memory.close()
            memory.unlink()
    out.update(elapsed_seconds=time.perf_counter()-t0, source_hashes=source_hashes(),
        spec=list(spec), status="complete",
        execution_driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    return out


def run_gpu_job(job, pool):
    config, spec, fingerprint, folder = job
    test, cell, replicate, *_ = spec
    path = Path(folder)/f"{test}_{cell:02d}_{replicate:04d}.json"
    if path.exists():
        r = json.loads(path.read_text())
        if r["source_hashes"] != fingerprint or r["spec"] != list(spec):
            raise RuntimeError("Mismatched GPU resume record")
        return str(path), True, r["elapsed_seconds"]
    result = run_a_gpu(config, spec, pool) if test == "A" else run_b_gpu(config, spec, pool)
    atomic_json(path, result)
    return str(path), False, result["elapsed_seconds"]


def b_refits(panel, fields, quarters, cells):
    from test_b import null_test
    return null_test(panel, fields, quarters, cells, expected_draws=99)


def run_b_gpu(config, spec, pool):
    test, cell, replicate, *_ = spec
    seed = spec_seed(config, test, cell, replicate)
    t0 = time.perf_counter()
    data = city_b(config, seed)
    cp, memory_report = bounded_cupy()
    engine = N.VariogramNull(data["fields"], data["xy"], 250., kmax=1000, max_lag=16)
    cpu = CPULowMemVariogramNull(data["fields"], data["xy"], 250., kmax=1000, max_lag=16, chunk=8)
    seedseq = [seed, 2034]
    fc, kc = next(cpu.draws(1, np.random.default_rng(np.random.SeedSequence(seedseq))))
    fg, kg = next(engine.draws(1, np.random.default_rng(np.random.SeedSequence(seedseq))))
    delta = float(np.max(np.abs(fc-fg)))
    if kc != kg or delta > 1e-11:
        raise ArithmeticError(f"Test B CPU/GPU mismatch: k {kc}/{kg}, error {delta}")
    del cpu, fc, fg
    start = time.perf_counter()
    surrogates = np.array([field for field, k in engine.draws(99, np.random.default_rng(np.random.SeedSequence(seedseq)))])
    del engine
    gc.collect()
    cp.get_default_memory_pool().free_all_blocks()
    result = pool.submit(b_refits, data["panel"], surrogates,
                         np.arange(config["b"]["quarters"]), np.arange(len(data["xy"]))).result()
    out = dict(test="B", seed=seed, diagnostics=data["diagnostics"],
        observed=result["observed"]["null_statistic"], observed_fit=result["observed"],
        statistics=[r["null_statistic"] for r in result["draws"]],
        signed_betas=[r["beta"] for r in result["draws"]],
        exceedances=result["exceedances"], p=result["p_B"], reject=result["p_B"] < .05,
        null_refit_seconds=time.perf_counter()-start, elapsed_seconds=time.perf_counter()-t0,
        execution_backend="gpu", gpu_memory=memory_report,
        equality_checks=dict(registered=dict(max_abs_difference=delta, same_k=True)),
        source_hashes=source_hashes(), spec=list(spec), status="complete",
        execution_driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    return out
