"""New-PC reproduction check of the saved real primary (read-only: writes nothing into the project).
Recomputes the observed fits, 16 null draws (Codex's linspace sample) and the first n bootstrap resamples with the
run's own code (scripts/11_models.py, imported) and compares them with out/models/real/{result,null,boot}_primary.*.
Usage, from feasibility/nyc: python -I repro_newpc.py n_boot jobs"""
import importlib.util, json, sys
from pathlib import Path
import numpy as np, pandas as pd

NYC = Path("/mnt/data/Master-projects/Alex/feasibility/nyc")
n_boot, jobs = int(sys.argv[1]), sys.argv[2]
sys.argv = ["11_models.py", str(NYC / "raw"), str(NYC / "out"), "--real", "--jobs", jobs]
spec = importlib.util.spec_from_file_location("m11", NYC / "scripts/11_models.py")
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
N, RUN = M.N, M.RUN
res = json.loads((RUN / "result_primary.json").read_text())
ctx = N.Context(M.CP2, M.INS, M.RAW, 250)
a = N.prepare("primary", ctx, M.real_events())
r = a["rows"]
Xb, v, y, rs = r[a["feats"]].values, r.vel.values, r.y.values.astype(int), r.rs.values
fold = ctx.fold[r.cell.values]
mb, mv = M.metrics_of(Xb, y, fold, rs, M.LR), M.metrics_of(np.c_[Xb, v], y, fold, rs, M.LR)
for k in M.METRICS:
    print(f"observed {k}: base diff {mb[k] - res[k + '_base']:.3g}, vel diff {mv[k] - res[k + '_vel']:.3g}", flush=True)
path, fw, fu = M.surrogates(a, "primary", 999)
wpos, upos = fw[r.win.values], fu[r.cell.values]
draws = np.linspace(0, 998, 16, dtype=int).tolist()
nd = pd.DataFrame(M.par(M.delayed(M.null_rep)(path, d, wpos, upos, Xb, y, fold, rs, M.LR, mb) for d in draws))
old = pd.read_csv(RUN / "null_primary.csv").iloc[draws]
for k in M.METRICS:
    diff = np.abs(nd[k].values - old[k].values)
    print(f"null {k}: identical {int((diff == 0).sum())}/{len(draws)}, within 1e-12 {int((diff <= 1e-12).sum())}, "
          f"max |diff| {diff.max():.3g}", flush=True)
blocks = np.unique(np.asarray(ctx.cells.block.values, dtype=object), return_inverse=True)[1][r.cell.values]
bt = pd.DataFrame(M.par(M.delayed(M.boot_rep)(s, blocks, Xb, v, y, fold, M.LR) for s in range(n_boot)))
ob = pd.read_csv(RUN / "boot_primary.csv").iloc[:n_boot]
for k in ("pr", "roc", "top10"):
    diff = np.abs(bt[k].values - ob[k].values)
    print(f"boot {k}: identical {int((diff == 0).sum())}/{n_boot}, within 1e-12 {int((diff <= 1e-12).sum())}, "
          f"max |diff| {diff.max():.3g}", flush=True)
