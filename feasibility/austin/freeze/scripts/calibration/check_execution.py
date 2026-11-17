"""CPU-emulated GPU scheduling check: identical OOF/null statistics, shared memory."""
import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[key] = "1"
from pathlib import Path
import sys
import json
from types import SimpleNamespace
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import run_calibration as R
import gpu_execution as G
from cpu_null import CPULowMemVariogramNull
from conditional_null import ConditionalVariogramNull
from simulation import FEATURES


def cpu_engine(kind, fields, xy, covariates, chunk=1, cpu=False):
    if kind == "registered":
        return CPULowMemVariogramNull(fields, xy, 30., kmax=1000, chunk=chunk)
    return ConditionalVariogramNull(fields, xy, 30., covariates, feature_names=FEATURES,
        chunk=chunk, null_factory=CPULowMemVariogramNull)


def main():
    config = json.loads((HERE/"design.json").read_text())
    config["null"]["draws"] = 3
    spec = ("A", 0, 9999, "N1", "moderate", 0.)
    seed = R.spec_seed(config, "A", 0, 9999)
    a = R.run_a(config, "N1", "moderate", 0., seed, 3)
    G.make_engine = cpu_engine
    G.bounded_cupy = lambda: (SimpleNamespace(get_default_memory_pool=lambda:
        SimpleNamespace(free_all_blocks=lambda: None)), dict(emulation=True))
    with ProcessPoolExecutor(max_workers=2, mp_context=mp.get_context("spawn"), initializer=G.cpu_init) as pool:
        b = G.run_a_gpu(config, spec, pool)
    assert a["observed"] == b["observed"]
    errors = {}
    for kind in ("registered", "conditional"):
        errors[kind] = float(np.max(np.abs(np.asarray(a["nulls"][kind]["statistics"])-b["nulls"][kind]["statistics"])))
        assert errors[kind] <= 1e-12
        assert a["nulls"][kind]["p"] == b["nulls"][kind]["p"]
    result = dict(status="PASS", actual_gpu=False, shared_memory_cpu_refits_identical=True,
                  max_statistic_difference=errors, chunk_equality_checks=b["equality_checks"])
    R.atomic_json(HERE/"execution_unit_results.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
