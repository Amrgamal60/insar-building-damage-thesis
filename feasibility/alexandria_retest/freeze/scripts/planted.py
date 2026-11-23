"""Step 0 planted-signal check of ALEX_RETEST_PLAN.md §9 (synthetic outcomes only).

Commands
  prepare    (PC) gather the fixed inputs into step0/planted_inputs.npz + .json: the 241 primary cells' design,
             P1 velocity, blocks and grid keys; all 3,300 eligible cells' keys, blocks and real labels (for the
             fold rule); the generating model; beta-hat; the cell-2 feature; the cell-4 location field; the
             cell-8 neighbour lists; the surrogate cell values of c1, c2 and the plain null. No real label of the
             241 cells is stored (the fold rule needs only labels elsewhere; the primary cells get the synthetic
             ones).
  run        (server) cells 1-8 x datasets, one resume-safe record per (cell, dataset); timing gate.
  summarise  rates, Wilson intervals, paired bias, power; the rule of §9 applied.

Fixed details (§9 leaves them to the script):
- eta = generating intercept + standardised Baseline 1 + x/y @ coefficients + the cell's term. 32 positives are
  drawn one at a time without replacement among the remaining cells, with probability exp(eta - max) / sum.
- Cell terms: 2: 0.65 t; 3: 0.7 H (H drawn first from the dataset's generator); 4: 0.7 L; 5-7: beta u, u = z(P1
  velocity over the 241 cells, population SD); 8: as 6, then each positive moves with probability 0.2 to a
  uniformly drawn free 8-neighbour among the 241 cells (positives handled in drawing order; none free: stays).
- Folds: retest_core.fold_matrix with the synthetic labels (original fold_map on all 3,300 eligible cells; real
  labels outside the 241 cells), 11 assignments.
- Per dataset: T and the seed-42 change in PR AUC, observed and under each of the nulls c1, c2 (pixel surrogates
  averaged into cells) and plain (original cell-level variogram matching), 999 draws each; beta-hat of the
  dataset; M0's seed-42 out-of-fold ROC AUC. Records keep p, exceedances, null mean and SD; the full null arrays
  go to a per-record .npz beside it.
- Rejection (the §7 item 1 rule): p < 0.05, statistic > 0 and beta-hat < 0.
- Seeds: SeedSequence([20261118, cell, dataset]).
- Timing gate: jobs run dataset-major; after the first `workers` jobs the projected hours are written to
  projection.json before any further job; above 24 h every cell runs 300 datasets instead of 500.
"""
import os

for _n in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_n] = "1"
import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import multiprocessing as mp  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor, as_completed  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.ndimage import gaussian_filter  # noqa: E402
from scipy.stats import norm, spearmanr, t as student_t  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import retest_core as R  # noqa: E402

MASTER = 20261118
N_POS = 32
CELLS = {1: "1. nothing added", 2: "2. 0.65 t (nonlinear covariate)", 3: "3. 0.7 H (hidden field)",
         4: "4. 0.7 L (smooth location that velocity tracks)", 5: "5. beta = -0.25", 6: "6. beta = -0.5",
         7: "7. beta = observed", 8: "8. beta = -0.5 + 20% location noise"}
NO_EFFECT = (1, 2, 3, 4)
NULLS = ("c1", "c2", "plain")
STATS = ("T", "dpr42")
H_SPACING, H_SIGMA_M, H_PAD_M, L_SIGMA_M = 50.0, 600.0, 2400.0, 1000.0
GATE_HOURS, FULL, FALLBACK = 24.0, 500, 300


def z(a):
    a = np.asarray(a, float)
    return (a - a.mean()) / a.std()


def atomic_json(path, obj):
    tmp = path.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, indent=1, allow_nan=False) + "\n")
    tmp.replace(path)


# ---------------------------------------------------------------- prepare (PC)
def cmd_prepare(a):
    out = R.RETEST / "step0"
    c, f, allc = R.load_cells()
    step1 = json.loads((R.RETEST / "step1/step1.json").read_text())
    gpath = R.RETEST / "step1/generating_model.json"
    assert R.sha256(gpath) == step1["generating_model_sha256"]
    G = json.loads(gpath.read_text())
    assert G["columns"] == list(R.S.SET_B)
    sz = np.load(out / "surrogates.npz")
    XB, v = R.design(c), c[R.COL].to_numpy(float)
    # cell 2: baseline feature (no x/y) most correlated with velocity, ties by BASELINE order
    rho = [abs(spearmanr(c[k], v).statistic) for k in R.P.BASELINE]
    j = int(np.argmax(rho))
    s = z(c[R.P.BASELINE[j]])
    t_soil = z(np.maximum(s - 0.7, 0) ** 2)
    # cell 4: Gaussian-kernel smooth of the field cells' velocity, read at the 241 cells
    fxy, cxy = f[["x", "y"]].to_numpy(float), c[["x", "y"]].to_numpy(float)
    d2 = ((cxy[:, None, :] - fxy[None, :, :]) ** 2).sum(-1)
    w = np.exp(-d2 / (2 * L_SIGMA_M ** 2))
    L = z((w @ f[R.COL].to_numpy(float)) / w.sum(1))
    # cell 8: 8-neighbours among the 241 cells
    key = {(r, q): i for i, (r, q) in enumerate(zip(c.row, c.col))}
    nbr = [[key[(r + dr, q + dq)] for dr in (-1, 0, 1) for dq in (-1, 0, 1)
            if (dr or dq) and (r + dr, q + dq) in key] for r, q in zip(c.row, c.col)]
    nbr_flat, nbr_ptr = np.concatenate([np.asarray(n, np.int64) for n in nbr]), np.cumsum([0] + [len(n) for n in nbr])
    # cell 3 grid over the 241 cells' centres, padded
    x0, y0 = cxy[:, 0].min() - H_PAD_M, cxy[:, 1].min() - H_PAD_M
    gi = np.rint((cxy[:, 0] - x0) / H_SPACING).astype(np.int64)
    gj = np.rint((cxy[:, 1] - y0) / H_SPACING).astype(np.int64)
    shape = (int(gj.max() + H_PAD_M / H_SPACING + 1), int(gi.max() + H_PAD_M / H_SPACING + 1))
    arrays = dict(XB=XB, v=v, block=c.block.to_numpy(str), row=c.row.to_numpy(), col=c.col.to_numpy(),
                  all_row=allc.row.to_numpy(), all_col=allc.col.to_numpy(), all_block=allc.block.to_numpy(str),
                  all_positive=allc.positive.to_numpy(bool).copy(), t_soil=t_soil, L=L, nbr_flat=nbr_flat, nbr_ptr=nbr_ptr,
                  gi=gi, gj=gj, grid_shape=np.asarray(shape),
                  c1=sz["c1_cells241"], c2=sz["c2_cells241"], plain=sz["plain_cells241"])
    # the primary cells' real labels are blanked in all_positive: the fold rule receives synthetic ones there
    pos_idx = pd.Index(allc.row * 100_000 + allc.col).get_indexer(c.row * 100_000 + c.col)
    arrays["all_positive"][pos_idx] = False
    arrays["primary_in_all"] = pos_idx
    np.savez(out / "planted_inputs.npz", **arrays)
    meta = dict(generating_model=G, generating_model_sha256=step1["generating_model_sha256"],
                beta_hat_per_sd=step1["beta_hat"]["per_sd"], cell2_feature=R.P.BASELINE[j],
                cell2_abs_spearman={k: float(r) for k, r in zip(R.P.BASELINE, rho)},
                surrogates_sha256=R.sha256(out / "surrogates.npz"), inputs_sha256=R.sha256(out / "planted_inputs.npz"),
                planted_py_sha256=R.sha256(Path(__file__)), retest_core_sha256=R.sha256(HERE / "retest_core.py"))
    (out / "planted_inputs.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(json.dumps({k: meta[k] for k in ("beta_hat_per_sd", "cell2_feature", "cell2_abs_spearman", "inputs_sha256")}, indent=1))


# ---------------------------------------------------------------- run (server)
CTX = {}


def load_ctx(folder):
    meta = json.loads((folder / "planted_inputs.json").read_text())
    assert hashlib.sha256((folder / "planted_inputs.npz").read_bytes()).hexdigest() == meta["inputs_sha256"]
    A = dict(np.load(folder / "planted_inputs.npz"))
    G = meta["generating_model"]
    mean, scale = np.asarray(G["scaler_mean"]), np.asarray(G["scaler_scale"])
    coef = np.asarray(G["coefficients_on_standardised_columns"])
    CTX.update(A=A, meta=meta, eta0=G["intercept"] + ((A["XB"] - mean) / scale) @ coef, u=z(A["v"]),
               allc=pd.DataFrame({"row": A["all_row"], "col": A["all_col"], "block": A["all_block"], "positive": A["all_positive"]}),
               c=pd.DataFrame({"row": A["row"], "col": A["col"], "block": A["block"]}),
               sources=dict(planted_py=R.sha256(Path(__file__)), retest_core=R.sha256(HERE / "retest_core.py"),
                            inputs=meta["inputs_sha256"]))


def term(cell, rng):
    A = CTX["A"]
    if cell == 1:
        return np.zeros(len(A["v"]))
    if cell == 2:
        return 0.65 * A["t_soil"]
    if cell == 3:
        g = gaussian_filter(rng.standard_normal(tuple(A["grid_shape"])), sigma=H_SIGMA_M / H_SPACING, mode="reflect", truncate=4.0)
        return 0.7 * z(g[A["gj"], A["gi"]])
    if cell == 4:
        return 0.7 * A["L"]
    beta = {5: -0.25, 6: -0.5, 8: -0.5}.get(cell)
    if cell == 7:
        beta = -abs(CTX["meta"]["beta_hat_per_sd"])
    return beta * CTX["u"]


def draw_labels(cell, dataset):
    rng = np.random.default_rng(np.random.SeedSequence([MASTER, cell, dataset]))
    eta = CTX["eta0"] + term(cell, rng)
    remaining = np.ones(len(eta), bool)
    chosen = []
    for _ in range(N_POS):
        idx = np.flatnonzero(remaining)
        w = np.exp(eta[idx] - eta[idx].max())
        k = idx[rng.choice(len(idx), p=w / w.sum())]
        chosen.append(k)
        remaining[k] = False
    y = np.zeros(len(eta), int)
    y[chosen] = 1
    moved = 0
    if cell == 8:
        A = CTX["A"]
        for k in chosen:
            if rng.random() < 0.2:
                nb = A["nbr_flat"][A["nbr_ptr"][k]:A["nbr_ptr"][k + 1]]
                free = nb[y[nb] == 0]
                if len(free):
                    j = free[rng.integers(len(free))]
                    y[k], y[j] = 0, 1
                    moved += 1
    assert y.sum() == N_POS
    return y, moved


def analyse(cell, dataset):
    t0 = time.perf_counter()
    A = CTX["A"]
    y, moved = draw_labels(cell, dataset)
    folds = R.fold_matrix(CTX["allc"], CTX["c"], y)
    st = R.Stat(A["XB"], y, folds)
    obs = st.of(A["v"])
    bh = R.beta_hat(A["XB"], y, A["v"])["per_sd"]
    out = dict(cell=cell, dataset=dataset, moved=moved, beta_hat=bh,
               positives_per_fold_seed42=[int(y[folds[0] == k].sum()) for k in range(5)],
               m0_oof_roc_seed42=float(roc_auc_score(y, R.S.oof(A["XB"], y, folds[0], R.LR))),
               observed=dict(T=obs["T"], dpr42=obs["dpr42"]), nulls={})
    arrays = {}
    for nl in NULLS:
        draws = [st.of(s) for s in A[nl]]
        for k in STATS:
            x = np.array([d[k] for d in draws])
            arrays[f"{nl}_{k}"] = x
            p = R.p_upper(obs[k], x)
            out["nulls"][f"{nl}_{k}"] = dict(p=p, exceed=int(np.sum(x >= obs[k])), null_mean=float(x.mean()),
                                             null_sd=float(x.std(ddof=1)), rejects=bool(p < 0.05 and obs[k] > 0 and bh < 0))
    out["elapsed_seconds"] = time.perf_counter() - t0
    return out, arrays


def run_job(spec):
    cell, dataset, folder = spec
    path = Path(folder) / f"cell{cell}_ds{dataset:03d}.json"
    if path.exists():
        rec = json.loads(path.read_text())
        assert rec["sources"] == CTX["sources"], f"{path}: different sources; refusing a mixed run"
        return rec, True
    rec, arrays = analyse(cell, dataset)
    rec.update(sources=CTX["sources"], status="complete")
    np.savez_compressed(Path(folder) / f"cell{cell}_ds{dataset:03d}_nulls.npz", **arrays)
    atomic_json(path, rec)
    return rec, False


def cmd_run(a):
    load_ctx(a.inputs)
    rec_dir = a.out / "records"
    rec_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(c, d, str(rec_dir)) for d in range(a.datasets) for c in a.cells]
    log = open(a.out / "run.log", "a")

    def say(msg):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    say(f"{len(jobs)} jobs; {a.workers} workers; sources {CTX['sources']}")
    proj_path = a.out / "projection.json"
    with ProcessPoolExecutor(a.workers, mp_context=mp.get_context("fork")) as ex:
        def run(batch):
            res = []
            for fut in as_completed([ex.submit(run_job, j) for j in batch]):
                rec, cached = fut.result()
                res.append(rec)
                say(f"cell {rec['cell']} ds {rec['dataset']}: T {rec['observed']['T']:+.3f}, " +
                    ", ".join(f"{k} p {v['p']:.3f}" for k, v in rec["nulls"].items() if k.endswith("_T")) +
                    ("; cached" if cached else f"; {rec['elapsed_seconds']:.0f} s"))
            return res
        done = 0
        if proj_path.exists():
            proj = json.loads(proj_path.read_text())
        else:
            first = run(jobs[:a.workers])
            done = a.workers
            secs = float(np.mean([r["elapsed_seconds"] for r in first]))
            hours = secs * len(jobs) / a.workers / 3600
            n = a.datasets if hours <= GATE_HOURS else min(a.datasets, FALLBACK)
            proj = dict(first_round=len(first), mean_job_seconds=secs, workers=a.workers, jobs=len(jobs),
                        projected_hours=hours, gate_hours=GATE_HOURS, datasets_per_cell=n, fallback_applied=n < a.datasets,
                        written=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
            atomic_json(proj_path, proj)
            say(f"projection {hours:.1f} h -> datasets per cell {n}")
        run([j for j in jobs[done:] if j[1] < proj["datasets_per_cell"]])
    say("run complete")


# ---------------------------------------------------------------- summarise
def wilson(k, n):
    zq = norm.ppf(.975)
    p = k / n
    centre = (p + zq * zq / (2 * n)) / (1 + zq * zq / n)
    half = zq * math.sqrt(p * (1 - p) / n + zq * zq / (4 * n * n)) / (1 + zq * zq / n)
    return [centre - half, centre + half]


def t_interval(x):
    x = np.asarray(x, float)
    if len(x) < 2:
        return dict(mean=float(x.mean()), ci95=None)
    m, sd, n = float(x.mean()), float(x.std(ddof=1)), len(x)
    h = float(student_t.ppf(.975, n - 1) * sd / math.sqrt(n))
    return dict(mean=m, ci95=[m - h, m + h])


def cmd_summarise(a):
    proj = json.loads((a.out / "projection.json").read_text())
    recs = [json.loads(p.read_text()) for p in sorted((a.out / "records").glob("cell*_ds*.json"))]
    recs = [r for r in recs if r["dataset"] < proj["datasets_per_cell"]]
    assert len({json.dumps(r["sources"]) for r in recs}) == 1, "mixed records"
    S = dict(projection=proj, sources=recs[0]["sources"], cells={})
    for c in sorted({r["cell"] for r in recs}):
        rs = sorted([r for r in recs if r["cell"] == c], key=lambda r: r["dataset"])
        assert [r["dataset"] for r in rs] == list(range(proj["datasets_per_cell"])), f"cell {c} incomplete"
        n = len(rs)
        cell = dict(label=CELLS[c], datasets=n, m0_oof_roc_mean=float(np.mean([r["m0_oof_roc_seed42"] for r in rs])),
                    beta_hat_mean=float(np.mean([r["beta_hat"] for r in rs])),
                    min_positives_in_a_fold=int(min(min(r["positives_per_fold_seed42"]) for r in rs)), tests={})
        for k in rs[0]["nulls"]:
            hits = sum(r["nulls"][k]["rejects"] for r in rs)
            stat = k.split("_", 1)[1]
            bias = t_interval([r["observed"][stat] - r["nulls"][k]["null_mean"] for r in rs])
            lo, hi = wilson(hits, n)
            cell["tests"][k] = dict(rejects=hits, rate=hits / n, wilson95=[lo, hi], paired_bias=bias,
                                    acceptable=bool(lo <= 0.05 and hits / n <= 0.075 and bias["ci95"] is not None and bias["ci95"][0] <= 0) if c in NO_EFFECT else None)
        S["cells"][c] = cell
    acc = {nl: all(S["cells"][c]["tests"][f"{nl}_T"]["acceptable"] for c in NO_EFFECT if c in S["cells"]) for nl in ("c1", "c2")}
    if acc["c1"] and acc["c2"]:
        r1, r2 = (S["cells"][6]["tests"][f"{nl}_T"]["rate"] for nl in ("c1", "c2"))
        choice, branch = ("c1" if r1 > r2 else "c2"), 1
    elif acc["c1"] or acc["c2"]:
        choice, branch = ("c1" if acc["c1"] else "c2"), 2
    else:
        choice, branch = None, 3
    S["rule"] = dict(acceptable=acc, branch=branch, primary_null=choice,
                     power_at_observed=S["cells"][7]["tests"][f"{choice}_T"]["rate"] if choice and 7 in S["cells"] else None)
    atomic_json(a.out / "planted_summary.json", S)
    lines = ["# Planted-signal check at Alexandria's size (ALEX_RETEST_PLAN.md §9)", "",
             f"Datasets per cell: {proj['datasets_per_cell']} (projection {proj['projected_hours']:.1f} h on {proj['workers']} workers). "
             "999 null draws per null. Rejection: p < 0.05, statistic > 0 and beta-hat < 0. Cells 1-4 have no velocity effect.", "",
             "| Cell | " + " | ".join(f"{nl} {s}" for nl in NULLS for s in STATS) + " | M0 ROC AUC | mean beta-hat |",
             "|---|" + "---|" * (len(NULLS) * len(STATS) + 2)]
    for c, d in S["cells"].items():
        cells = []
        for nl in NULLS:
            for s in STATS:
                t = d["tests"][f"{nl}_{s}"]
                flag = "" if t["acceptable"] in (None, True) else " ✗"
                cells.append(f"{100 * t['rate']:.1f}% [{100 * t['wilson95'][0]:.1f}, {100 * t['wilson95'][1]:.1f}]{flag}")
        lines.append(f"| {d['label']} | " + " | ".join(cells) + f" | {d['m0_oof_roc_mean']:.3f} | {d['beta_hat_mean']:+.2f} |")
    lines += ["", "✗ = not acceptable (§9: lower Wilson bound > 0.05, rate > 0.075, or paired bias interval above 0).", "",
              f"**Rule of §9:** T acceptable in cells 1-4 under c1: {acc['c1']}, under c2: {acc['c2']} -> branch {branch}; "
              f"primary null: {choice}; power at the observed effect (cell 7): "
              + (f"{100 * S['rule']['power_at_observed']:.1f}%" if S['rule']['power_at_observed'] is not None else "n/a") + ".", "",
              "Paired bias (observed minus null mean; mean [95% t]) in cells 1-4:", ""]
    for c in NO_EFFECT:
        if c in S["cells"]:
            lines.append(f"- {S['cells'][c]['label']}: " + "; ".join(
                f"{k} {v['paired_bias']['mean']:+.4f} " + (f"[{v['paired_bias']['ci95'][0]:+.4f}, {v['paired_bias']['ci95'][1]:+.4f}]" if v['paired_bias']['ci95'] else "[n<2]")
                for k, v in S["cells"][c]["tests"].items()))
    lines += ["", "Sources: " + json.dumps(S["sources"]) + "."]
    (a.out / "PLANTED.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    r = sub.add_parser("run")
    r.add_argument("--inputs", type=Path, required=True)
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--workers", type=int, required=True)
    r.add_argument("--cells", type=int, nargs="+", default=list(CELLS))
    r.add_argument("--datasets", type=int, default=FULL)
    s = sub.add_parser("summarise")
    s.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    {"prepare": cmd_prepare, "run": cmd_run, "summarise": cmd_summarise}[a.command](a)


if __name__ == "__main__":
    main()
