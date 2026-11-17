"""Exercise metric sorting on reversed arrays in parallel and check index integrity."""
import json
import os
import time
import numpy as np
from joblib import Parallel, delayed, parallel_config
from sklearn.metrics import average_precision_score, roc_auc_score


def check(seed):
    rng = np.random.default_rng(seed)
    y = np.zeros(502812, dtype=np.int64)
    y[rng.choice(len(y), 69, replace=False)] = 1
    for iteration in range(12):
        score = rng.random(len(y))
        if iteration % 2:
            score = np.round(score, 3)
        reversed_score = score[::-1]
        index = np.argsort(reversed_score, kind="stable")
        assert index.min() == 0 and index.max() == len(y) - 1
        assert np.unique(index).size == len(y)
        assert np.all(np.diff(reversed_score[index]) >= 0)
        assert np.isfinite(average_precision_score(y, score))
        assert np.isfinite(roc_auc_score(y, score))
    return seed


if __name__ == "__main__":
    started = time.monotonic()
    print("CPU dispatch", np._core._multiarray_umath.__cpu_dispatch__, flush=True)
    print("Disabled", os.environ.get("NPY_DISABLE_CPU_FEATURES"), flush=True)
    with parallel_config(backend="loky", inner_max_num_threads=1):
        results = Parallel(n_jobs=8)(delayed(check)(seed) for seed in range(8))
    print(json.dumps({"workers": len(results), "iterations_per_worker": 12,
                      "seconds": round(time.monotonic() - started, 2), "passed": True}), flush=True)
