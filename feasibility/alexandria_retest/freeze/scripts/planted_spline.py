"""Planted check of the flexible-baseline secondary (ALEX_RETEST_PLAN.md, draft 4, secondary 14; synthetic outcomes only).

Asked by the user on 2026-11-18 after the §9 planted check ended in branch 3 ("c2 + spline check"): c2 becomes the
primary null, and a secondary with a flexible baseline is added because every null failed planted cell 2 (a
nonlinear elevation effect that velocity, |rho| 0.58 with elevation, partly carries beyond the linear baseline).
This script measures that secondary's false-positive rate in cells 1 and 2 and its power at the observed effect
(cell 7), on the same synthetic datasets as the main check (planted.draw_labels, same seeds), so the two are paired.

Flexible baseline (fixed here, before any run; features only, no outcome):
- each of the six baseline features is replaced by its cubic B-spline basis (scikit-learn SplineTransformer, degree
  3, 5 knots at the quantiles 0, .25, .5, .75, 1 of the 241 cells, include_bias=False: 6 columns per feature);
  a feature whose five quantile knots are not distinct gets 5 uniform knots over its range instead;
- x_km and y_km stay linear (secondary 2 treats smooth location);
- M0 = that design; M1 = M0 + cell P1 velocity; the frozen logistic pipeline (StandardScaler, C = 1) as in §5.

Per dataset: T (mean over the 11 fold assignments of the out-of-fold log-likelihood gain) and the seed-42 change in
PR AUC under the primary null c2 (the same 999 cell surrogates as the main check); beta-hat of the flexible M1.
Rejection: p < 0.05, T > 0 and beta-hat < 0. Acceptable (cells 1-2) as in §9: Wilson lower bound <= 0.05, rate
<= 0.075, paired-bias interval lower bound <= 0. Reported only; no rule depends on it.

Commands: run (server; resume-safe records; timing gate as planted.py, fallback 300 datasets above 24 h);
summarise (PLANTED_SPLINE.md, planted_spline_summary.json).
"""
import os

for _n in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_n] = "1"
import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor, as_completed  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import planted as PL  # noqa: E402
import retest_core as R  # noqa: E402

CELLS = (1, 2, 7)
NO_EFFECT = (1, 2)
NULL = "c2"
N_KNOTS, DEGREE = 5, 3
GATE_HOURS, FULL, FALLBACK = 24.0, 500, 300


def spline_design(XB, names):
    """Cubic B-spline bases of the baseline columns (quantile knots; uniform if they tie) + linear x/y."""
    from sklearn.preprocessing import SplineTransformer
    nb = len(R.P.BASELINE)
    assert list(names[:nb]) == list(R.P.BASELINE) and list(names[nb:]) == ["x_km", "y_km"]
    blocks, knots = [], {}
    for j, k in enumerate(R.P.BASELINE):
        x = XB[:, [j]]
        q = np.quantile(x[:, 0], np.linspace(0, 1, N_KNOTS))
        kind = "quantile" if len(np.unique(q)) == N_KNOTS else "uniform"
        st = SplineTransformer(n_knots=N_KNOTS, degree=DEGREE, knots=kind, include_bias=False).fit(x)
        blocks.append(st.transform(x))
        knots[k] = kind
    X = np.hstack(blocks + [XB[:, nb:]])
    return X, knots


def load():
    PL.load_ctx(R.RETEST / "step0")
    A = PL.CTX["A"]
    XS, knots = spline_design(A["XB"], list(R.S.SET_B))
    PL.CTX.update(XS=XS, knots=knots)
    PL.CTX["sources_spline"] = dict(PL.CTX["sources"], planted_spline_py=R.sha256(Path(__file__)),
                                    design_sha256=hashlib.sha256(np.ascontiguousarray(XS).tobytes()).hexdigest())


def analyse(cell, dataset, draws=None):
    t0 = time.perf_counter()
    A, XS = PL.CTX["A"], PL.CTX["XS"]
    y, moved = PL.draw_labels(cell, dataset)
    folds = R.fold_matrix(PL.CTX["allc"], PL.CTX["c"], y)
    st = R.Stat(XS, y, folds)
    obs = st.of(A["v"])
    bh = R.beta_hat(XS, y, A["v"])["per_sd"]
    sur = A[NULL] if draws is None else A[NULL][:draws]
    nd = [st.of(s) for s in sur]
    out = dict(cell=cell, dataset=dataset, moved=moved, beta_hat=bh, observed=dict(T=obs["T"], dpr42=obs["dpr42"]),
               dl=obs["dl"], nulls={})
    arrays = {}
    for k in ("T", "dpr42"):
        x = np.array([d[k] for d in nd])
        arrays[f"{NULL}_{k}"] = x
        p = R.p_upper(obs[k], x)
        out["nulls"][f"{NULL}_{k}"] = dict(p=p, exceed=int(np.sum(x >= obs[k])), null_mean=float(x.mean()),
                                           null_sd=float(x.std(ddof=1)), rejects=bool(p < 0.05 and obs[k] > 0 and bh < 0))
    out["draws"] = len(sur)
    out["elapsed_seconds"] = time.perf_counter() - t0
    return out, arrays


def run_job(spec):
    cell, dataset, folder = spec
    path = Path(folder) / f"cell{cell}_ds{dataset:03d}.json"
    if path.exists():
        rec = json.loads(path.read_text())
        assert rec["sources"] == PL.CTX["sources_spline"], f"{path}: different sources; refusing a mixed run"
        return rec, True
    rec, arrays = analyse(cell, dataset)
    rec.update(sources=PL.CTX["sources_spline"], status="complete")
    np.savez_compressed(Path(folder) / f"cell{cell}_ds{dataset:03d}_nulls.npz", **arrays)
    PL.atomic_json(path, rec)
    return rec, False


def cmd_run(a):
    load()
    rec_dir = a.out / "records"
    rec_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(c, d, str(rec_dir)) for d in range(a.datasets) for c in a.cells]
    log = open(a.out / "run.log", "a")

    def say(msg):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    say(f"{len(jobs)} jobs; {a.workers} workers; knots {PL.CTX['knots']}; sources {PL.CTX['sources_spline']}")
    proj_path = a.out / "projection.json"
    with ProcessPoolExecutor(a.workers, mp_context=mp.get_context("fork")) as ex:
        def run(batch):
            res = []
            for fut in as_completed([ex.submit(run_job, j) for j in batch]):
                rec, cached = fut.result()
                res.append(rec)
                v = rec["nulls"][f"{NULL}_T"]
                say(f"cell {rec['cell']} ds {rec['dataset']}: T {rec['observed']['T']:+.3f}, {NULL}_T p {v['p']:.3f}"
                    + ("; cached" if cached else f"; {rec['elapsed_seconds']:.0f} s"))
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
            PL.atomic_json(proj_path, proj)
            say(f"projection {hours:.1f} h -> datasets per cell {n}")
        run([j for j in jobs[done:] if j[1] < proj["datasets_per_cell"]])
    say("run complete")


def cmd_summarise(a):
    proj = json.loads((a.out / "projection.json").read_text())
    recs = [json.loads(p.read_text()) for p in sorted((a.out / "records").glob("cell*_ds*.json"))]
    recs = [r for r in recs if r["dataset"] < proj["datasets_per_cell"]]
    assert len({json.dumps(r["sources"]) for r in recs}) == 1, "mixed records"
    main_dir = R.RETEST / "step0/planted_20261117/records"
    S = dict(projection=proj, sources=recs[0]["sources"], cells={})
    lines = ["# Planted check of the flexible-baseline secondary (ALEX_RETEST_PLAN.md secondary 14)", "",
             f"Datasets per cell: {proj['datasets_per_cell']}; null {NULL}, 999 draws; the same synthetic datasets as "
             "the main check (`step0/planted_20261117/`), so the linear-baseline column is paired. Rejection: p < 0.05, "
             "T > 0, beta-hat < 0.", "",
             "| Cell | flexible baseline: T under c2 | paired bias | linear baseline (main check): T under c2 | mean beta-hat (flexible) |",
             "|---|---|---|---|---|"]
    for c in sorted({r["cell"] for r in recs}):
        rs = sorted([r for r in recs if r["cell"] == c], key=lambda r: r["dataset"])
        assert [r["dataset"] for r in rs] == list(range(proj["datasets_per_cell"])), f"cell {c} incomplete"
        n = len(rs)
        hits = sum(r["nulls"][f"{NULL}_T"]["rejects"] for r in rs)
        lo, hi = PL.wilson(hits, n)
        bias = PL.t_interval([r["observed"]["T"] - r["nulls"][f"{NULL}_T"]["null_mean"] for r in rs])
        main = [json.loads((main_dir / f"cell{c}_ds{r['dataset']:03d}.json").read_text()) for r in rs]
        mhits = sum(m["nulls"][f"{NULL}_T"]["rejects"] for m in main)
        both = sum(r["nulls"][f"{NULL}_T"]["rejects"] and m["nulls"][f"{NULL}_T"]["rejects"] for r, m in zip(rs, main))
        acc = bool(lo <= 0.05 and hits / n <= 0.075 and bias["ci95"][0] <= 0) if c in NO_EFFECT else None
        S["cells"][c] = dict(label=PL.CELLS[c], datasets=n, rejects=hits, rate=hits / n, wilson95=[lo, hi], paired_bias=bias,
                             acceptable=acc, linear_rejects=mhits, linear_rate=mhits / n, both_reject=both,
                             beta_hat_mean=float(np.mean([r["beta_hat"] for r in rs])),
                             raw_p_below_005=float(np.mean([r["nulls"][f"{NULL}_T"]["p"] < 0.05 for r in rs])))
        d = S["cells"][c]
        flag = "" if acc in (None, True) else " ✗"
        lines.append(f"| {d['label']} | {100 * d['rate']:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}]{flag} | "
                     f"{bias['mean']:+.3f} [{bias['ci95'][0]:+.3f}, {bias['ci95'][1]:+.3f}] | {100 * d['linear_rate']:.1f}% | "
                     f"{d['beta_hat_mean']:+.2f} |")
    PL.atomic_json(a.out / "planted_spline_summary.json", S)
    lines += ["", "✗ = not acceptable by the §9 criteria (reported only; no rule depends on it).", "",
              "Sources: " + json.dumps(S["sources"]) + "."]
    (a.out / "PLANTED_SPLINE.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--workers", type=int, required=True)
    r.add_argument("--cells", type=int, nargs="+", default=list(CELLS))
    r.add_argument("--datasets", type=int, default=FULL)
    s = sub.add_parser("summarise")
    s.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    {"run": cmd_run, "summarise": cmd_summarise}[a.command](a)


if __name__ == "__main__":
    main()
