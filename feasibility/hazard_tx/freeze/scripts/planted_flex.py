"""Planted check of the FLEXIBLE Baseline 1 (HAZARD_TX_PLAN.md §9.3; synthetic outcomes only).

Asked by the user on 2026-11-22 after the pooled planted check (§9.2) found no inference acceptable in all null cells
(r3 and r4 fail the 15 km field) and a 23% false demonstration rate when soil acts nonlinearly (cell 8): "flexible
baseline, check first". The synthetic worlds are those of planted_ht.py, unchanged (same inputs npz, same CELLS, same
draw() and seeds), so each dataset here is the same dataset as in the linear run; only the adjustment changes.

Flexible Baseline 1, per city (authors' choices, fixed before this run; knots from the city's primary rows, no outcome):
- each continuous Baseline 1 feature (building age, log living area, log lot area, soil LEP, slope, elevation, log
  income): a restricted cubic spline (Harrell), knots at the 5%, 27.5%, 50%, 72.5% and 95% quantiles (4 columns;
  tied knots are merged, fewer than 3 distinct knots leaves the linear term only);
- the slab indicator where the city's Baseline 1 has it (Dallas), linear;
- location: a tensor-product surface of restricted cubic splines of x and of y (5 knots each at the same quantiles):
  the 4 + 4 main-effect columns and their 16 products (24 columns). It replaces linear x/y (which it contains).
The pooled model is as §7 otherwise: a city intercept, city x standardised flexible columns, one flag term.
The standardised columns of each city are orthonormalised (SVD; directions with singular value below 1e-8 of the
largest dropped as numerically null): the column space, and so every fitted value and the flag estimate, is unchanged,
while Newton converges (the products are nearly collinear: Hessian condition about 1e13 before).
T uses the same flexible columns as M0 (M1 = M0 + flag), nyc_lib LR as in planted_ht.py.

Inference: identical in value to oa_core.infer (r1-r4, p only), computed faster by using the block structure. With the
flag fixed at 0 the pooled model separates by city, so the restricted fit is the per-city fits; the efficient scores
are summed by cluster and passed to oa_core.wild_p with oa_core.webb_weights drawn exactly as infer draws them. The
full fit is oa_core.poisson_fit on the pooled design, warm-started from the restricted fit. `check` reproduces records
of the linear run (planted_ht.py) through this path with the linear design.

  run       --out DIR [--design flex|linear] -> DIR/records (same record schema as planted_ht.py), DIR/flex_design.json
  check     --linear-records DIR             -> compares this path (linear design) with stored linear records
  summarise --out DIR                        -> planted_ht.cmd_summarise + a header naming the flexible baseline
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ht_core as H  # noqa: E402
import planted_ht as P  # noqa: E402

C = H.C
Q = [0.05, 0.275, 0.5, 0.725, 0.95]  # Harrell's default quantiles for 5 knots
CONT = ["building_age", "log_living_area", "log_lot_area", "lep_0_150", "slope_deg", "elevation_m", "log_income"]
INPUTS_DEFAULT = H.STUDY / "step0/planted_pooled_20261122"
RANK_TOL = 1e-8  # singular values below this share of the largest are numerically null and dropped


def rcs(x, t):
    """Restricted cubic spline basis (Harrell, normalised by (t_k - t_1)^2): x, then k - 2 nonlinear terms."""
    x = np.asarray(x, float)
    k = len(t)
    cols = [x]
    if k >= 3:
        def cube(u):
            return np.maximum(u, 0.0) ** 3
        for j in range(k - 2):
            cols.append((cube(x - t[j]) - cube(x - t[k - 2]) * (t[k - 1] - t[j]) / (t[k - 1] - t[k - 2])
                         + cube(x - t[k - 1]) * (t[k - 2] - t[j]) / (t[k - 1] - t[k - 2])) / (t[k - 1] - t[0]) ** 2)
    return np.column_stack(cols)


def knots(x):
    return np.unique(np.quantile(np.asarray(x, float), Q))


def flex_columns(XB_c, name):
    """Flexible Baseline 1 of one city (rows = that city's primary rows, columns of XB in H.B1 order)."""
    own = H.B1_BY_CITY[name]
    cols, labels, kn = [], [], {}
    for k in CONT:
        if k not in own:
            continue
        x = XB_c[:, H.B1.index(k)]
        t = knots(x)
        B = rcs(x, t)
        cols.append(B)
        labels += [f"{k}:{i}" for i in range(B.shape[1])]
        kn[k] = [float(v) for v in t]
    if "foundation_slab" in own:
        cols.append(XB_c[:, [H.B1.index("foundation_slab")]])
        labels.append("foundation_slab")
    tx, ty = knots(XB_c[:, H.B1.index("x_km")]), knots(XB_c[:, H.B1.index("y_km")])
    bx, by = rcs(XB_c[:, H.B1.index("x_km")], tx), rcs(XB_c[:, H.B1.index("y_km")], ty)
    te = (bx[:, :, None] * by[:, None, :]).reshape(len(XB_c), -1)
    cols += [bx, by, te]
    labels += [f"x:{i}" for i in range(bx.shape[1])] + [f"y:{i}" for i in range(by.shape[1])] + \
              [f"x{i}*y{j}" for i in range(bx.shape[1]) for j in range(by.shape[1])]
    kn["x_km"], kn["y_km"] = [float(v) for v in tx], [float(v) for v in ty]
    return np.hstack(cols), labels, kn


def linear_columns(XB_c, name, col_mask_c):
    """The linear Baseline 1 of planted_ht.py (for `check`): the city's own B1 columns."""
    return XB_c[:, col_mask_c], [b for b, m in zip(H.B1, col_mask_c) if m], {}


# ---------------------------------------------------------------- context
_K = {}


def kctx(inputs, design):
    if _K:
        assert _K["design"] == design
        return _K
    K = P.ctx(inputs)  # npz, cities, names, col_mask, X_unadj (and the linear X_adj, unused here)
    _K.update(design=design, rows={}, F={}, Zc={}, labels={}, knots={}, rank={})
    n, x = len(K["city"]), K["flag"]
    parts = []
    for c in K["cities"]:
        s = np.flatnonzero(K["city"] == c)
        name = K["names"][c]
        F, labels, kn = (flex_columns(K["XB"][s], name) if design == "flex"
                         else linear_columns(K["XB"][s], name, K["col_mask"][c]))
        mu, sd = F.mean(0), F.std(0)
        sd[sd == 0] = 1.0
        Fs = (F - mu) / sd
        if design == "flex":  # orthonormalise (same column space; the spline products are nearly collinear)
            U, S, _ = np.linalg.svd(Fs, full_matrices=False)
            keep = S > RANK_TOL * S[0]
            _K["rank"][name] = dict(columns=int(Fs.shape[1]), kept=int(keep.sum()),
                                    smallest_kept_ratio=float(S[keep][-1] / S[0]))
            Fs = U[:, keep] * np.sqrt(len(s))
            F = Fs  # T uses the same orthonormal columns (nyc_lib LR standardises them again: unchanged)
        _K["rows"][c], _K["F"][c], _K["labels"][c], _K["knots"][name] = s, F, labels, kn
        _K["Zc"][c] = np.c_[np.ones(len(s)), Fs]  # the city's block of the pooled design (indicator, columns)
        ind = (K["city"] == c).astype(float)
        Z = np.zeros((n, Fs.shape[1]))
        Z[s] = Fs
        parts += [ind, Z]
    _K["X"] = np.column_stack(parts + [np.asarray(x, float)])
    return _K


def design_record(inputs, design):
    K, F = P.ctx(inputs), kctx(inputs, design)
    return dict(design=design, columns_per_city={K["names"][c]: len(F["labels"][c]) for c in K["cities"]},
                pooled_columns=int(F["X"].shape[1]), orthonormalised=F["rank"], rank_tol=RANK_TOL, labels={K["names"][c]: F["labels"][c] for c in K["cities"]},
                knots=F["knots"], quantiles=Q, npz_sha256=H.sha256(inputs / "planted_inputs.npz"),
                sources=H.source_hashes())


# ---------------------------------------------------------------- inference (values as oa_core.infer, p only)
def adjusted_fast(K, F, y, off, groups, seed):
    x = K["flag"]
    n = len(y)
    mu, xt = np.empty(n), np.empty(n)
    b_r, b_init = {}, []
    for c in K["cities"]:
        s, Zc = F["rows"][c], F["Zc"][c]
        b, m_, Hz = C.poisson_fit(Zc, y[s], off[s])
        xt[s] = x[s] - Zc @ C.solve(Hz, (Zc * m_[:, None]).T @ x[s])
        mu[s], b_r[c] = m_, b
        b_init.append(b)
    u = xt * (y - mu)
    fit = C.poisson_fit(F["X"], y, off, b_init=np.r_[np.concatenate(b_init), 0.0])
    est = float(fit[0][-1])
    out = {}
    for m in H.METHODS:
        if m == "r1":
            r = C.infer(F["X"], y, off, groups, "r1", seed, interval=False, fit=fit)
            out[m] = dict(log_irr=r["log_irr"], p_one_sided=r["p_one_sided"])
            continue
        gidx, G = C.group_index(groups[H.BLOCK_OF[m]])
        W = C.webb_weights(np.random.default_rng(seed), C.N_WILD, G)
        out[m] = dict(log_irr=est, p_one_sided=float(C.wild_p(np.bincount(gidx, weights=u, minlength=G), W)[0]))
    by_city = {}
    if len(K["cities"]) > 1:  # each city's own adjusted test, r3 (its restricted fit is the same block)
        for c in K["cities"]:
            s, Zc = F["rows"][c], F["Zc"][c]
            gidx, G = C.group_index(groups["b6"][s])
            W = C.webb_weights(np.random.default_rng(seed), C.N_WILD, G)
            p = float(C.wild_p(np.bincount(gidx, weights=u[s], minlength=G), W)[0])
            bc = C.poisson_fit(np.c_[Zc, x[s]], y[s], off[s], b_init=np.r_[b_r[c], 0.0])[0]
            by_city[str(c)] = dict(log_irr=float(bc[-1]), p_one_sided=p)
    return out, by_city


def run_one(cell, ds, inputs, out, design):
    path = out / "records" / f"cell{cell:02d}_ds{ds:04d}.json"
    if path.exists():
        return 0.0
    t0 = time.perf_counter()
    K, F = P.ctx(inputs), kctx(inputs, design)
    y = P.draw(cell, ds, inputs)
    off = np.full(len(y), np.log(H.FU_YEARS))
    groups = {k: K[k] for k in ("b2", "b6", "b12")}
    x = K["flag"]
    rec = dict(cell=cell, ds=ds, design=design, events=int(y.sum()), flagged_events=int(y[x == 1].sum()),
               events_by_city={str(c): int(y[K["city"] == c].sum()) for c in K["cities"]},
               flagged_events_by_city={str(c): int(y[(K["city"] == c) & (x == 1)].sum()) for c in K["cities"]})
    O, nb = np.bincount(groups["b2"], weights=y), np.bincount(groups["b2"])
    rec["block_sd_log"] = P.block_sd_log(O[nb > 0], nb[nb > 0])
    rec["block_sd_log_by_city"] = {}
    for c in K["cities"]:
        bc = np.unique(groups["b2"][K["city"] == c])
        rec["block_sd_log_by_city"][str(c)] = P.block_sd_log(O[bc], nb[bc])
    seed = [H.SEED_WILD, cell, ds]
    rec["adjusted"], by_city = adjusted_fast(K, F, y, off, groups, seed)
    fit = C.fit_flag(K["X_unadj"], y, off)
    rec["unadjusted"] = {m: {k: v for k, v in C.infer(K["X_unadj"], y, off, groups, m, seed, interval=False, fit=fit).items()
                             if k in ("log_irr", "p_one_sided")} for m in H.METHODS}
    if by_city:
        rec["adjusted_by_city"] = by_city
    if cell in P.T_CELLS:
        rec["T_by_city"] = {}
        for c in K["cities"]:
            s = F["rows"][c]
            folds = H.fold_assignments(groups["b2"][s], y[s])
            T, _ = H.t_statistic(F["F"][c], x[s], y[s], folds)
            rec["T_by_city"][str(c)] = T
        rec["T"] = float(sum(rec["T_by_city"].values()))
    rec["seconds"] = time.perf_counter() - t0
    P.atomic_json(path, rec)
    return rec["seconds"]


# ---------------------------------------------------------------- commands
def cmd_run(a):
    from concurrent.futures import ProcessPoolExecutor
    (a.out / "records").mkdir(parents=True, exist_ok=True)
    dj = a.out / "flex_design.json"
    rec = design_record(a.inputs, a.design)
    if dj.exists():
        old = json.loads(dj.read_text())
        assert old["sources"] == rec["sources"] and old["design"] == rec["design"], "different code or design: refusing a mixed run"
    else:
        P.atomic_json(dj, rec)
    jobs = []
    nmax = max(v[-1] for v in P.CELLS.values())
    cells = a.cells or list(P.CELLS)
    for ds in range(nmax):  # dataset-major, as planted_ht.py
        for cell in cells:
            if ds < P.CELLS[cell][-1] and not (a.out / "records" / f"cell{cell:02d}_ds{ds:04d}.json").exists():
                jobs.append((cell, ds))
    if a.limit:
        jobs = jobs[:a.limit]
    print(f"{len(jobs)} jobs, {a.workers} workers, design {a.design}, columns {rec['columns_per_city']}", flush=True)
    t0 = time.time()
    done, secs = 0, []
    with ProcessPoolExecutor(a.workers) as ex:
        for s in ex.map(run_one, *zip(*jobs), [a.inputs] * len(jobs), [a.out] * len(jobs), [a.design] * len(jobs), chunksize=1):
            done += 1
            secs.append(s)
            if done == min(len(jobs), 4 * a.workers):
                proj = dict(first_round=done, mean_job_seconds=float(np.mean(secs)), workers=a.workers, jobs=len(jobs),
                            projected_hours=float(np.mean(secs) * len(jobs) / a.workers / 3600),
                            written=time.strftime("%Y-%m-%d %H:%M:%S"))
                P.atomic_json(a.out / "projection.json", proj)
                print("projection", proj, flush=True)
            if done % 500 == 0:
                print(done, f"{(time.time() - t0) / 60:.1f} min", flush=True)
    print("done", done, f"{(time.time() - t0) / 60:.1f} min", flush=True)


def cmd_check(a):
    """This path with the linear design must reproduce the stored linear records (planted_ht.py)."""
    import tempfile
    worst, rows = 0.0, []
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        (out / "records").mkdir()
        for cell, ds in a.pairs:
            run_one(cell, ds, a.inputs, out, "linear")
            new = json.loads((out / "records" / f"cell{cell:02d}_ds{ds:04d}.json").read_text())
            old = json.loads((a.linear_records / f"cell{cell:02d}_ds{ds:04d}.json").read_text())
            for key in ("adjusted", "unadjusted"):
                for m in H.METHODS:
                    for f in ("log_irr", "p_one_sided"):
                        d = abs(new[key][m][f] - old[key][m][f])
                        worst = max(worst, d if f == "log_irr" else 0.0)
                        rows.append((cell, ds, key, m, f, old[key][m][f], new[key][m][f]))
                        assert d < (1e-6 if f == "log_irr" else 1e-12), rows[-1]
            for c in old.get("adjusted_by_city", {}):
                for f in ("log_irr", "p_one_sided"):
                    d = abs(new["adjusted_by_city"][c][f] - old["adjusted_by_city"][c][f])
                    rows.append((cell, ds, f"city {c}", "r3", f, old["adjusted_by_city"][c][f], new["adjusted_by_city"][c][f]))
                    assert d < (1e-6 if f == "log_irr" else 1e-12), rows[-1]
            if "T" in old:
                for c in old["T_by_city"]:
                    rows.append((cell, ds, f"T city {c}", "", "T", old["T_by_city"][c], new["T_by_city"][c]))
                    assert abs(new["T_by_city"][c] - old["T_by_city"][c]) < 1e-9, rows[-1]
            print(f"cell {cell} ds {ds}: reproduced ({new['seconds']:.1f} s here)", flush=True)
    print(f"all {len(a.pairs)} records reproduced; largest log IRR difference {worst:.2e}")
    # flexible design: the fast path against oa_core.infer itself on the same design
    _K.clear()
    K, F = P.ctx(a.inputs), kctx(a.inputs, "flex")
    groups = {k: K[k] for k in ("b2", "b6", "b12")}
    for cell, ds in a.flex_pairs:
        y = P.draw(cell, ds, a.inputs)
        off = np.full(len(y), np.log(H.FU_YEARS))
        seed = [H.SEED_WILD, cell, ds]
        fast, by_city = adjusted_fast(K, F, y, off, groups, seed)
        for m in H.METHODS:
            r = C.infer(F["X"], y, off, groups, m, seed, interval=False)
            print(f"flex cell {cell} ds {ds} {m}: fast {fast[m]['log_irr']:.10f} p {fast[m]['p_one_sided']:.6g} | "
                  f"oa_core {r['log_irr']:.10f} p {r['p_one_sided']:.6g}", flush=True)
            assert abs(fast[m]["log_irr"] - r["log_irr"]) < 1e-6 and abs(fast[m]["p_one_sided"] - r["p_one_sided"]) < 1e-9
        for c in K["cities"]:
            s = F["rows"][c]
            r = C.infer(np.c_[F["Zc"][c], K["flag"][s]], y[s], off[s], {k: v[s] for k, v in groups.items()}, "r3", seed, interval=False)
            print(f"flex cell {cell} ds {ds} city {c} r3: fast {by_city[str(c)]} | oa_core {r['log_irr']:.10f} p {r['p_one_sided']:.6g}")
            assert abs(by_city[str(c)]["log_irr"] - r["log_irr"]) < 1e-6 and abs(by_city[str(c)]["p_one_sided"] - r["p_one_sided"]) < 1e-9
    print(f"flexible design: fast path equals oa_core.infer on {len(a.flex_pairs)} dataset(s); rank {F['rank']}")


def cmd_summarise(a):
    P.cmd_summarise(argparse.Namespace(inputs=a.inputs, out=a.out))
    d = json.loads((a.out / "flex_design.json").read_text())
    S = json.loads((a.out / "planted_summary.json").read_text())
    S["design"] = dict(baseline=d["design"], columns_per_city=d["columns_per_city"], pooled_columns=d["pooled_columns"],
                       flex_design_sha256=H.sha256(a.out / "flex_design.json"))
    P.atomic_json(a.out / "planted_summary.json", S)
    md = (a.out / "PLANTED.md").read_text().split("\n")
    md[0] = "# Planted check of the FLEXIBLE Baseline 1 (HAZARD_TX_PLAN.md §9.3; synthetic outcomes only)"
    md.insert(1, "")
    md.insert(2, f"Adjusted model here: city intercepts and city x the FLEXIBLE Baseline 1 (restricted cubic splines of each continuous "
                 f"feature, slab linear in Dallas, a spline surface of x and y; columns per city {d['columns_per_city']}; "
                 f"`flex_design.json`). Same synthetic datasets as the linear run (planted_ht.py).")
    (a.out / "PLANTED.md").write_text("\n".join(md))
    print("\n".join(md[:4]))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--inputs", type=Path, default=INPUTS_DEFAULT)
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--design", choices=["flex", "linear"], default="flex")
    r.add_argument("--workers", type=int, default=16)
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--cells", type=int, nargs="*")
    k = sub.add_parser("check")
    k.add_argument("--inputs", type=Path, default=INPUTS_DEFAULT)
    k.add_argument("--linear-records", type=Path, default=INPUTS_DEFAULT / "records")
    k.add_argument("--pairs", type=lambda s: tuple(int(v) for v in s.split(":")), nargs="+",
                   default=[(1, 0), (4, 0), (9, 0)])
    k.add_argument("--flex-pairs", type=lambda s: tuple(int(v) for v in s.split(":")), nargs="+",
                   default=[(4, 0), (8, 0)])
    s = sub.add_parser("summarise")
    s.add_argument("--inputs", type=Path, default=INPUTS_DEFAULT)
    s.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    {"run": cmd_run, "check": cmd_check, "summarise": cmd_summarise}[a.cmd](a)


if __name__ == "__main__":
    main()
