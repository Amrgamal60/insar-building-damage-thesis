"""Exploratory comparison of test statistics inside the same surrogate null (after the Austin result).

Asked by the user on 2026-11-17 after the literature search (literature_methods/SYNTHESIS.md, Pepe et al. 2013:
testing the predictor's coefficient or likelihood may have more power than the change in discrimination).
This is NOT part of the frozen Austin analysis and changes no decision of AUSTIN_PLAN.md §11: it measures, on
synthetic events only, whether another statistic would have detected the planted velocity effect more often.
No real event is joined to a velocity value (the real events enter only as the dates file, as in the
planted-signal check).

Everything up to the statistic is the hashed planted-signal code, imported unchanged (planted_signal.py
977f626f..., testa_core.py f4d71575...): the same synthetic datasets (seeds [20261110, cell, dataset]), risk
sets, folds, Baseline 1 + x/y design, observed field and the same 999 stored conditional-null surrogates with
their quantiles. For the observed field and each surrogate draw, five statistics are computed from one set
of model fits (frozen nyc_lib model: StandardScaler + LogisticRegression C=1):
  ap      change in pooled out-of-fold average precision (the frozen Test A statistic; anchor, must equal
          the 2026-11-11 records exactly);
  oofll   change in pooled out-of-fold log-likelihood (held-out; same fold fits as ap);
  llr     change in in-sample log-likelihood, both models fitted on all rows;
  coef    coefficient of the standardised velocity in the full model fitted on all rows (per unit of u);
  abscoef |coef|.
p-values (as testa_core.p_value, add-one): upper tail for ap, oofll, llr, abscoef; lower tail for coef
(planted beta is negative). "Detects" = p < 0.05, plus the sign condition: ap > 0 (the §11 rule), oofll > 0,
coef < 0. llr and abscoef have no sign condition.

Commands: run (cells x datasets, resume-safe records), summarise (summary json + markdown; checks anchor).
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor, as_completed  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
from scipy.stats import binomtest  # noqa: E402
from sklearn.metrics import average_precision_score  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
import planted_signal as P  # noqa: E402
import testa_core as C  # noqa: E402

N = C.N
STATS = ["ap", "oofll", "llr", "coef", "abscoef"]
LOWER_TAIL = {"coef"}
SIGN = {"ap": 1, "oofll": 1, "coef": -1}  # required sign of the observed value; others none
WANT_SOURCES = {"planted_signal.py": "977f626f1c72ab25e6c3f70b062fe1010252b9027f0e8bba113f4acad882b8f4",
                "testa_core.py": "f4d71575c3179ef2f6ac7aeff8e0a26c14ab515db76ad937e411fae9e6e38430"}


def loglik(y, p):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return float(np.sum(y * np.log(p) + (1 - y) * np.log1p(-p)))


class Stats:
    def __init__(self, X, y, fold):
        self.X, self.y, self.fold = X, y, fold
        s0 = N.oof(X, y, fold, N.LR)
        assert np.isfinite(s0).all()
        self.ap0 = float(average_precision_score(y, s0))  # identical to testa_core.oof_ap
        self.oofll0 = loglik(y, s0)
        m0 = N.model(N.LR).fit(X, y)
        self.ll0 = loglik(y, m0.predict_proba(X)[:, 1])

    def of(self, u):
        assert np.isfinite(u).all()
        X1 = np.column_stack([self.X, u])
        s1 = N.oof(X1, self.y, self.fold, N.LR)
        assert np.isfinite(s1).all()
        m1 = N.model(N.LR).fit(X1, self.y)
        coef = float(m1[-1].coef_[0, -1] / m1[0].scale_[-1])
        return dict(ap=float(average_precision_score(self.y, s1)) - self.ap0,
                    oofll=loglik(self.y, s1) - self.oofll0,
                    llr=loglik(self.y, m1.predict_proba(X1)[:, 1]) - self.ll0,
                    coef=coef, abscoef=abs(coef))


def p_of(name, observed, null):
    null = np.asarray(null, dtype=float)
    k = int(np.sum(null <= observed)) if name in LOWER_TAIL else int(np.sum(null >= observed))
    return (1 + k) / (1 + len(null))


def detects(name, observed, p):
    return bool(p < 0.05 and (name not in SIGN or SIGN[name] * observed > 0))


def analyse(cell, dataset, draws):
    """planted_signal.analyse with the statistic loop replaced; every step before it is the same call."""
    t0 = time.perf_counter()
    h, geo = P.CTX["h"], P.CTX["geo"]
    house, t_ep, diag = P.synthetic_events(cell, dataset)
    holds = np.zeros(len(h), dtype=bool)
    holds[house] = True
    fold_h = C.fold_of_houses(h, holds)
    crng = np.random.default_rng(np.random.SeedSequence([P.MASTER, cell, dataset, C.CONTROL_SEED]))
    rows = C.risk_sets(house, P.CTX["dates"], P.CTX["windows"], t_ep, P.CTX["t_dem"], P.CTX["HV"], crng)
    rows, lost = C.drop_incomplete(rows, h)
    X = C.design(h, rows["house"], rows["date"])
    y, fold, win = rows["y"], fold_h[rows["house"]], rows["window"]
    pix = geo.house_null[rows["house"]]
    assert (pix >= 0).all()
    S = Stats(X, y, fold)
    observed = S.of(P.CTX["U"][win, rows["house"]])
    null = {k: [] for k in STATS}
    for d in range(draws):
        raw = np.asarray(P.CTX["store"].S[d][win, pix], dtype=np.float64)
        for k, v in S.of(C.standardise(raw, win, P.CTX["qS"][d])).items():
            null[k].append(v)
    p = {k: p_of(k, observed[k], null[k]) for k in STATS}
    return dict(cell=cell, dataset=dataset, label=P.CELLS[cell]["label"], rows=int(len(y)), cases=int(y.sum()),
                control_rows_dropped_missing_inputs=lost, diagnostics=diag, draws=draws,
                baseline=dict(ap=S.ap0, oofll=S.oofll0, ll=S.ll0), observed=observed, statistics=null, p=p,
                detects={k: detects(k, observed[k], p[k]) for k in STATS},
                elapsed_seconds=time.perf_counter() - t0)


SOURCES = {}


def run_job(spec):
    cell, dataset, draws, folder = spec
    path = Path(folder) / f"cell{cell}_ds{dataset:03d}.json"
    if path.exists():
        rec = json.loads(path.read_text())
        assert rec["sources"] == SOURCES and rec["fingerprints"] == P.CTX["fingerprints"] and rec["draws"] == draws
        return rec, True
    rec = analyse(cell, dataset, draws)
    rec.update(sources=SOURCES, fingerprints=P.CTX["fingerprints"], status="complete")
    P.atomic_json(path, rec)
    return rec, False


def cmd_run(a):
    P.build_context(a)
    assert {k: P.CTX["sources"][k] for k in WANT_SOURCES} == WANT_SOURCES, "planted-signal code changed"
    SOURCES.update(P.CTX["sources"], **{"statistic_comparison.py": C.sha256(Path(__file__))})
    draws = a.draws if a.draws is not None else P.CTX["store"].draws
    records = a.out / "records"
    records.mkdir(parents=True, exist_ok=True)
    jobs = [(c, d, draws, str(records)) for d in range(a.datasets) for c in a.cells]
    log = open(a.out / "run.log", "a")

    def say(msg):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    say(f"setup {P.CTX['setup_seconds']:.1f} s; {len(jobs)} jobs; {a.workers} workers; draws {draws}")
    with ProcessPoolExecutor(a.workers, mp_context=mp.get_context("fork")) as ex:
        for fut in as_completed([ex.submit(run_job, j) for j in jobs]):
            rec, cached = fut.result()
            took = "cached" if cached else "%.0f s" % rec["elapsed_seconds"]
            say(f"cell {rec['cell']} dataset {rec['dataset']}: " +
                ", ".join(f"{k} p {rec['p'][k]:.3f}" for k in STATS) + f"; {took}")
    say("run complete")


def anchor(rec, original_folder):
    """Max |difference| between this record's ap values and the 2026-11-11 planted-signal record."""
    o = json.loads((original_folder / f"cell{rec['cell']}_ds{rec['dataset']:03d}.json").read_text())
    n = rec["draws"]
    diffs = [abs(rec["observed"]["ap"] - o["observed"]), abs(rec["baseline"]["ap"] - o["baseline_average_precision"])]
    diffs += list(np.abs(np.asarray(rec["statistics"]["ap"]) - np.asarray(o["statistics"][:n])))
    return float(max(diffs)), o["meets_rule"], o["p"]


def cmd_summarise(a):
    recs = [json.loads(p.read_text()) for p in sorted((a.out / "records").glob("cell*_ds*.json"))]
    assert len({json.dumps([r["sources"], r["fingerprints"], r["draws"]]) for r in recs}) == 1, "mixed records"
    anchors = []
    for r in recs:
        diff, met, p_orig = anchor(r, a.original / "records")
        anchors.append(diff)
        if r["draws"] == 999:
            assert met == r["detects"]["ap"] and p_orig == r["p"]["ap"], f"cell {r['cell']} ds {r['dataset']}: ap decision differs"
    cells = {}
    for c in sorted({r["cell"] for r in recs}):
        rs = sorted([r for r in recs if r["cell"] == c], key=lambda r: r["dataset"])
        n = len(rs)
        out = dict(label=P.CELLS[c]["label"], datasets=n, statistics={})
        for k in STATS:
            hits = sum(r["detects"][k] for r in rs)
            ci = binomtest(hits, n).proportion_ci(method="wilson")
            out["statistics"][k] = dict(detects=hits, share=hits / n, wilson95=[ci.low, ci.high],
                                        p_deciles=P.deciles([r["p"][k] for r in rs]),
                                        observed_mean=float(np.mean([r["observed"][k] for r in rs])),
                                        null_mean=float(np.mean([np.mean(r["statistics"][k]) for r in rs])))
        # paired comparison with ap on the same datasets: datasets detected by one statistic only
        out["paired_vs_ap"] = {}
        for k in STATS[1:]:
            only_k = sum(r["detects"][k] and not r["detects"]["ap"] for r in rs)
            only_ap = sum(r["detects"]["ap"] and not r["detects"][k] for r in rs)
            m = only_k + only_ap
            out["paired_vs_ap"][k] = dict(only_this=only_k, only_ap=only_ap,
                                          exact_mcnemar_p=binomtest(only_k, m).pvalue if m else 1.0)
        cells[c] = out
    S = dict(draws=recs[0]["draws"], sources=recs[0]["sources"], fingerprints=recs[0]["fingerprints"],
             anchor_max_abs_diff=max(anchors), records=len(recs), cells=cells)
    P.atomic_json(a.out / "statistic_comparison_summary.json", S)
    names = dict(ap="change in out-of-fold average precision (frozen Test A)", oofll="change in out-of-fold log-likelihood",
                 llr="change in in-sample log-likelihood", coef="velocity coefficient, negative tail", abscoef="|velocity coefficient|")
    lines = ["# Test statistics compared inside the same surrogate null (exploratory, synthetic events only)", "",
             f"Datasets per cell: {', '.join(str(c['datasets']) for c in cells.values())}. Null draws per dataset: {S['draws']}. "
             f"Same synthetic datasets, folds and surrogates as the planted-signal check of 2026-11-11; the frozen statistic "
             f"(ap) reproduces those records with max |difference| {S['anchor_max_abs_diff']:.1e}.", "",
             "Share of datasets detected (p < 0.05, with the sign condition where one applies), 95% Wilson interval:", "",
             "| Statistic | " + " | ".join(c["label"] for c in cells.values()) + " |",
             "|---|" + "---|" * len(cells)]
    for k in STATS:
        lines.append(f"| {names[k]} | " + " | ".join(
            f"{c['statistics'][k]['detects']}/{c['datasets']} [{100 * c['statistics'][k]['wilson95'][0]:.0f}, {100 * c['statistics'][k]['wilson95'][1]:.0f}]%"
            for c in cells.values()) + " |")
    lines += ["", "Paired against ap on the same datasets (detected by this statistic only / by ap only; exact McNemar p):", "",
              "| Statistic | " + " | ".join(c["label"] for c in cells.values()) + " |", "|---|" + "---|" * len(cells)]
    for k in STATS[1:]:
        lines.append(f"| {k} | " + " | ".join(
            f"{c['paired_vs_ap'][k]['only_this']} / {c['paired_vs_ap'][k]['only_ap']}; p {c['paired_vs_ap'][k]['exact_mcnemar_p']:.3g}"
            for c in cells.values()) + " |")
    lines += ["", "p deciles (0,.1], ..., (.9,1]:", ""]
    for c in cells.values():
        lines.append(f"- {c['label']}: " + "; ".join(f"{k} {c['statistics'][k]['p_deciles']}" for k in STATS))
    lines += ["", "Source hashes: " + ", ".join(f"`{k}` {v}" for k, v in S["sources"].items()) + "."]
    (a.out / "STATISTIC_COMPARISON.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run")
    for k in ("features", "grid", "episodes", "censoring", "field", "surrogates", "quantiles", "event_dates", "out"):
        r.add_argument("--" + k.replace("_", "-"), type=Path, required=True)
    r.add_argument("--coefficients", type=Path, default=HERE / "generating_coefficients.json")
    r.add_argument("--workers", type=int, required=True)
    r.add_argument("--cells", type=int, nargs="+", default=[1, 4, 5])
    r.add_argument("--datasets", type=int, default=100)
    r.add_argument("--draws", type=int, default=None)
    s = sub.add_parser("summarise")
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--original", type=Path, required=True, help="folder of the 2026-11-11 planted-signal run")
    a = p.parse_args(argv)
    {"run": cmd_run, "summarise": cmd_summarise}[a.command](a)


if __name__ == "__main__":
    main()
