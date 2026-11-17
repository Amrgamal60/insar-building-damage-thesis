"""Check unchanged primary metrics and sampled draws under baseline CPU dispatch."""
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[3]
full = "--full" in sys.argv
jobs = 16  # new PC, 2026-10-14 (§14 deviation 9); was 4
sys.argv = ["11_models.py", str(root / "raw"), str(root / "out"), "--real", "--jobs", str(jobs)]
spec = importlib.util.spec_from_file_location("nyc_metric_check", root / "scripts/11_models.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
ctx = M.N.Context(M.CP2, M.INS, M.RAW, 250)
a = M.N.prepare("primary", ctx, M.real_events())
r = a["rows"]
Xb, v, y, rs = r[a["feats"]].values, r.vel.values, r.y.values.astype(int), r.rs.values
fold = ctx.fold[r.cell.values]
blocks = np.unique(np.asarray(ctx.cells.block.values, dtype=object), return_inverse=True)[1][r.cell.values]
check_fp = M.checkpoint_fingerprint(a, [Xb, v, y, fold, rs, blocks], 999, 2000)
check_root = Path(__file__).parent / "verification_checkpoints" / check_fp
null_check, boot_check = check_root / "null", check_root / "bootstrap"
null_check.mkdir(parents=True, exist_ok=True)
boot_check.mkdir(parents=True, exist_ok=True)
saved = json.loads((M.RUN / "result_primary.json").read_text())
args_base = (Xb, y, fold, rs, M.LR)
args_velocity = (np.c_[Xb, v], y, fold, rs, M.LR)
mb, _ = M.reproducible_rep(M.metrics_of, args_base, M.array_digest(args_base))
mv, _ = M.reproducible_rep(M.metrics_of, args_velocity, M.array_digest(args_velocity))
observed = {}
for k in M.METRICS:
    observed[k] = {"base": mb[k], "with_velocity": mv[k],
                   "base_difference": mb[k] - saved[k + "_base"],
                   "velocity_difference": mv[k] - saved[k + "_vel"]}
    np.testing.assert_allclose([mb[k], mv[k]], [saved[k + "_base"], saved[k + "_vel"]], rtol=0, atol=1e-12)
print("Observed primary metrics match saved result", flush=True)
path, fw, fu = M.surrogates(a, "primary", 999)
wpos, upos = fw[r.win.values], fu[r.cell.values]
M.expect_arrays(null_check, wpos, upos, Xb, y, fold, rs)
M.expect_arrays(boot_check, blocks, Xb, v, y, fold)
draws = list(range(999)) if full else np.linspace(0, 998, 16, dtype=int).tolist()
nd = pd.DataFrame(M.par(M.delayed(M.checkpoint_rep)(null_check, d, M.null_rep, path, d,
                                                  wpos, upos, Xb, y, fold, rs, M.LR, mb) for d in draws))
old_null = pd.read_csv(M.RUN / "null_primary.csv").iloc[draws]
null_diff = {}
for k in M.METRICS:
    np.testing.assert_allclose(nd[k].values, old_null[k].values, rtol=0, atol=1e-12)
    null_diff[k] = float(np.max(np.abs(nd[k].values - old_null[k].values)))
print(f"{len(draws)} primary null draws match", flush=True)
n_boot = 2000 if full else 16
bt = pd.DataFrame(M.par(M.delayed(M.checkpoint_rep)(boot_check, s, M.boot_rep, s,
                                                  blocks, Xb, v, y, fold, M.LR) for s in range(n_boot)))
old_boot = pd.read_csv(M.RUN / "boot_primary.csv").iloc[:n_boot]
boot_diff = {}
for k in ("pr", "roc", "top10"):
    np.testing.assert_allclose(bt[k].values, old_boot[k].values, rtol=0, atol=1e-12)
    boot_diff[k] = float(np.max(np.abs(bt[k].values - old_boot[k].values)))
evidence = {"observed": observed, "null_draws_checked": draws, "null_max_abs_differences": null_diff,
            "bootstrap_seeds_checked": list(range(n_boot)), "bootstrap_max_abs_differences": boot_diff,
            "absolute_tolerance": 1e-12, "full_primary_recomputation": full}
if full:
    for k in M.METRICS:
        assert M.p_value(nd[k].tolist(), mv[k] - mb[k]) == saved[k + "_p"]
    evidence["primary_p_values_match"] = True
filename = "FULL_PRIMARY_VERIFICATION.json" if full else "METRIC_VERIFICATION.json"
(Path(__file__).parent / filename).write_text(json.dumps(evidence, indent=2) + "\n")
print(f"Observed metrics, {len(draws)} null draws and {n_boot} bootstrap resamples verified", flush=True)
