"""Compare CPU null generation against existing GPU output without fitting models."""
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[3]
sys.argv = [str(root / "scripts/11_models.py"), str(root / "raw"), str(root / "out"), "--real", "--jobs", "16"]
spec = importlib.util.spec_from_file_location("nyc_models_cpu_check", root / "scripts/11_models.py")
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)
events = models.real_events()
checks = []
for key, res in [("primary", 250), ("s2", 200)]:
    started = time.monotonic()
    ctx = models.N.Context(models.CP2, models.INS, models.RAW, res)
    a = models.N.prepare(key, ctx, events)
    meta = np.load(models.RUN / f"surr_{key}_meta.npz", allow_pickle=False)
    assert str(meta["fp"]) == models.N.fingerprint(a), "cached field fingerprint differs"
    null = models.N.VariogramNull(a["null_fields"], a["xy"], a["res"])
    generated, k = next(null.draws(1, np.random.default_rng(models.NULL_SEED)))
    cached = np.load(models.RUN / f"surr_{key}.npy", mmap_mode="r")[0]
    expected_k = int(pd.read_csv(models.RUN / f"surr_{key}_k.csv").iloc[0]["k"])
    assert int(k) == expected_k, f"smoothing k differs: {k} vs {expected_k}"
    np.testing.assert_allclose(generated.astype(np.float32), cached, rtol=5e-7, atol=5e-7, equal_nan=True)
    check = {"analysis": key, "draw": 0, "seed": models.NULL_SEED, "k": int(k),
             "max_abs_difference_float32": float(np.nanmax(np.abs(generated.astype(np.float32) - cached))),
             "exact_float32_match": bool(np.array_equal(generated.astype(np.float32), cached, equal_nan=True)),
             "rtol": 5e-7, "atol": 5e-7, "seconds": round(time.monotonic() - started, 2)}
    checks.append(check)
    print(json.dumps(check), flush=True)
    del null, ctx, a, generated, cached
(Path(__file__).parent / "CPU_VERIFICATION.json").write_text(json.dumps(checks, indent=2) + "\n")
print("CPU null verification passed", flush=True)
