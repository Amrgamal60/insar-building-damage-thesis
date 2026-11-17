"""Timing/memory-only GPU pilot; no outcome statistics are inspected or output."""
import os
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import sys
import json
import time
import subprocess
import copy
import gc
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
from simulation import city_a, city_b, FEATURES
from lowmem_null import LowMemVariogramNull
from conditional_null import ConditionalVariogramNull
from cpu_null import CPULowMemVariogramNull
from run_calibration import atomic_json
import nyc_lib as N


def main():
    config = json.loads((HERE/"design.json").read_text())
    state = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], text=True)
    free = int(state.strip().splitlines()[0])
    if free < 900:
        raise RuntimeError(f"Only {free} MiB free; no GPU pilot")
    import cupy as cp
    cp.get_default_memory_pool().set_limit(size=700*1024**2)
    results = dict(gpu_free_before_mib=free, pool_cap_mib=700, timings=[])
    for label in ("small", "scale", "B"):
        cfg = copy.deepcopy(config)
        if label == "scale":
            for key in ("side_m", "occupied_pixels", "houses"):
                cfg["a"][key] = cfg["a"]["scale_cells"][key]
        data = city_b(cfg, 19002032) if label == "B" else city_a(cfg, 19002030, "N1", "strong")
        for kind in (("registered",) if label == "B" else ("registered", "conditional")):
            start = time.perf_counter()
            opts = dict(kmax=1000, max_lag=16)
            try:
                if label == "B":
                    engine = N.VariogramNull(data["fields"], data["xy"], 250., **opts)
                elif kind == "registered":
                    engine = LowMemVariogramNull(data["fields"], data["xy"], 30., chunk=1, **opts)
                else:
                    engine = ConditionalVariogramNull(data["fields"], data["xy"], 30., data["pixel_cov"],
                        feature_names=FEATURES, chunk=1, **opts)
                setup = time.perf_counter()-start
                t0 = time.perf_counter()
                for fields, k in engine.draws(5, np.random.default_rng(2033)):
                    assert fields.shape == data["fields"].shape and np.isfinite(fields).all()
                elapsed = time.perf_counter()-t0
                results["timings"].append(dict(city=label, method=kind, setup_seconds=setup,
                    draw_seconds=elapsed/5, pool_mib=cp.get_default_memory_pool().total_bytes()/1024**2, status="PASS"))
            except cp.cuda.memory.OutOfMemoryError as exc:
                results["timings"].append(dict(city=label, method=kind, status="MEMORY_LIMIT", error=str(exc)))
            finally:
                if "engine" in locals():
                    del engine
                gc.collect()
                cp.get_default_memory_pool().free_all_blocks()
        del data
        gc.collect()
    atomic_json(HERE/"benchmark_gpu.json", results)
    print(json.dumps(results, indent=2), flush=True)


if __name__ == "__main__":
    main()
