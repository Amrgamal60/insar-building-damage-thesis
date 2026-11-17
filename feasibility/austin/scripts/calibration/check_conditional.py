"""Small conditional API checks and CPU-versus-unchanged-GPU arithmetic check."""
import os
for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[name] = "1"
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
from conditional_null import ConditionalVariogramNull, HGB_SETTINGS
from cpu_null import CPULowMemVariogramNull
from lowmem_null import LowMemVariogramNull


class IdentityNull:
    def __init__(self, fields, *args, **kwargs):
        self.fields = fields.copy()
    def draws(self, n_draws, rng):
        for _ in range(n_draws):
            yield self.fields.copy(), 2


def main():
    rng = np.random.default_rng(202611010)
    xy = np.unique(rng.integers(0, 40, (600, 2)), axis=0).astype(float)*30+15
    X = rng.standard_normal((len(xy), 3))
    fields = np.array([X[:, 0]**2 + .3*rng.normal(size=len(xy)) for _ in range(3)])
    fields[0, :10] = np.nan
    a = ConditionalVariogramNull(fields, xy, 30, X, null_factory=IdentityNull)
    restored = next(a.draws(1, rng))[0]
    assert np.array_equal(np.isnan(restored), np.isnan(fields))
    assert np.nanmax(np.abs(restored-fields)) < 1e-14
    assert min(a.explained_variance) > .7
    b = ConditionalVariogramNull(fields, xy, 30, X, null_factory=IdentityNull)
    assert np.allclose(a.fitted, b.fitted, equal_nan=True)
    failures = 0
    for kw in [dict(covariates=X[:-1]), dict(covariates=X, feature_names=["x", "age", "soil"]),
               dict(covariates=np.full_like(X, np.nan)), dict(covariates=X, res=-1)]:
        opts = dict(fields=fields, xy=xy, res=30, null_factory=IdentityNull)
        opts.update(kw)
        try:
            ConditionalVariogramNull(**opts)
        except ValueError:
            failures += 1
        else:
            raise AssertionError("Invalid input accepted")
    result = dict(identity_reconstruction=True, exact_nan_mask=True, deterministic_hgb=True,
                  invalid_input_checks=failures, hgb_settings=HGB_SETTINGS,
                  hgb_explained_variance=a.explained_variance)
    # Query BEFORE CUDA initialization, use one small GPU process and a 256 MiB pool.
    state = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], text=True)
    result["gpu_free_mib_before"] = int(state.strip().splitlines()[0])
    if result["gpu_free_mib_before"] < 700:
        raise RuntimeError("Need 700 MiB free for bounded CPU/GPU equality check; no scale run authorized")
    import cupy as cp
    cp.get_default_memory_pool().set_limit(size=256*1024**2)
    gpu = LowMemVariogramNull(fields, xy, 30, kmax=100, chunk=2)
    cpu = CPULowMemVariogramNull(fields, xy, 30, kmax=100, chunk=2)
    errors = []
    for (fg, kg), (fc, kc) in zip(gpu.draws(3, np.random.default_rng(2033)), cpu.draws(3, np.random.default_rng(2033))):
        error = float(np.nanmax(np.abs(fg-fc)))
        assert kg == kc and error < 1e-11
        assert np.array_equal(np.isnan(fg), np.isnan(fc))
        errors.append(error)
    result.update(cpu_gpu_max_abs_difference=max(errors), cpu_gpu_chosen_k_identical=True,
                  unchanged_draw_method=cpu.draws.__func__ is gpu.draws.__func__,
                  unchanged_vario_method=cpu._vario.__func__ is gpu._vario.__func__,
                  gpu_pool_total_mib=cp.get_default_memory_pool().total_bytes()/1024**2,
                  status="PASS")
    (HERE/"unit_results.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
