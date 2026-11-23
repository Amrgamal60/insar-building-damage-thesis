"""Planted check of OHENHEN_AUSTIN_PLAN.md §9 (synthetic outcomes only; the real map and the real mapped houses).

  prepare   -> step0/planted_inputs.npz + planted_inputs.json (houses, flag, blocks, generating predictor; and the
               outcome-only field-size reference: between-block SD of the log event rate, 2018-08-01 to 2021-12-31,
               all eligible houses, no map value used)
  run       -> OUT/records/cell{c:02d}_ds{d:04d}.json (resume-safe), OUT/projection.json after the first round
  summarise -> OUT/planted_summary.json, OUT/PLANTED.md (acceptability, rule, power)

Synthetic world (§9): fixed follow-up of FU_YEARS for every house; Bernoulli events with logit = a + eta, a solved
per dataset so that the expected count equals the planning figure (837 for all mapped houses; scaled by the share of
houses with complete Baseline 1 in the U cells). Hidden field: stationary Gaussian random field from 2,000 random
Fourier features, squared-exponential covariance with correlation 0.05 at the stated range (length scale =
range / sqrt(2 ln 20)), standard deviation as stated, coordinates in km.
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
import pandas as pd  # noqa: E402
from scipy.optimize import brentq  # noqa: E402
from scipy.special import expit  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oa_core as C  # noqa: E402

MASTER = 20261119
TARGET_EVENTS = 837.0
N_RFF = 2000
LEN_FACTOR = np.sqrt(2 * np.log(20))
# cell: (kind, range_km, sd, trend, generating, soil_squared, log_irr, datasets)
CELLS = {
    1: ("V null", 1, 0.5, False, False, False, 0.0, 1000),
    2: ("V null", 3, 0.5, False, False, False, 0.0, 1000),
    3: ("V null", 8, 0.5, False, False, False, 0.0, 1000),
    4: ("V null", 15, 0.5, False, False, False, 0.0, 1000),
    5: ("V null", 3, 1.0, False, False, False, 0.0, 1000),
    6: ("V null", 3, 0.5, True, False, False, 0.0, 1000),
    7: ("U null", 3, 0.5, False, True, False, 0.0, 500),
    8: ("U null (reported)", 3, 0.5, False, True, True, 0.0, 500),
    9: ("V power", 3, 0.5, False, False, False, np.log(1.5), 500),
    10: ("V power", 3, 0.5, False, False, False, np.log(2.0), 500),
    11: ("U power", 3, 0.5, False, True, False, np.log(1.5), 500),
}
V_NULL = [1, 2, 3, 4, 5, 6]
U_CELLS = [7, 8, 11]


def atomic_json(path, obj):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1) + "\n")
    tmp.replace(path)


# ---------------------------------------------------------------- prepare
def block_sd_log(events_per_block, houses_per_block):
    """Moment estimate of the SD (log scale) of a multiplicative block effect beyond Poisson."""
    O = np.asarray(events_per_block, float)
    E = np.asarray(houses_per_block, float) * O.sum() / np.sum(houses_per_block)
    s2 = (np.sum((O - E) ** 2) - np.sum(E)) / np.sum(E ** 2)
    return float(np.sqrt(np.log1p(max(s2, 0.0))))


def cmd_prepare(a):
    out = C.STUDY / "step0"
    h = C.load_houses()
    m = h[h.mapped].reset_index(drop=True)
    gen = json.loads(C.INPUTS["feasibility/austin/planted_signal/generating_coefficients.json"].read_text())
    assert gen["columns"] == ["building_age"] + C.B1[1:], gen["columns"]
    comp = m.complete_b1.to_numpy(bool)
    Z = (m[C.B1].to_numpy(float) - np.array(gen["scaler_mean"])) / np.array(gen["scaler_scale"])
    coef = np.array(gen["coefficients_on_standardised_columns"])
    eta_gen = np.where(comp, np.nan_to_num(Z) @ coef, np.nan)
    soil = C.B1.index("lep_0_150")
    zs = np.nan_to_num(Z[:, soil])
    sq = zs ** 2
    sq = (sq - sq[comp].mean()) / sq[comp].std()
    eta_gen_sq = np.where(comp, np.nan_to_num(Z) @ coef - coef[soil] * zs + coef[soil] * sq, np.nan)
    # outcome-only field-size reference (no map value): all eligible houses, events 2018-08-01..2021-12-31
    ev = pd.read_parquet(C.CP1 / "events/foundation_events.parquet", columns=["prop_id", "t_first"])
    ev = ev[(ev.t_first >= "2018-08-01") & (ev.t_first <= "2021-12-31")]
    hb = h.set_index("prop_id").b2
    O = ev.prop_id.map(hb).dropna().value_counts().reindex(hb.unique(), fill_value=0)
    ref = dict(events=int(O.sum()), blocks=int(len(O)), between_block_sd_log=block_sd_log(O.to_numpy(), hb.value_counts().reindex(O.index).to_numpy()))
    np.savez(out / "planted_inputs.npz", x_km=m.x_km.to_numpy(float), y_km=m.y_km.to_numpy(float), flag=m.flag.to_numpy(float),
             complete=comp, b2=pd.factorize(m.b2)[0], b6=pd.factorize(m.b6)[0], b12=pd.factorize(m.b12)[0],
             fold42=m.fold.to_numpy(np.int64), XB=np.nan_to_num(m[C.B1].to_numpy(float)), eta_gen=eta_gen, eta_gen_sq=eta_gen_sq)
    rec = dict(mapped_houses=len(m), flagged=int(m.flag.sum()), complete_b1=int(comp.sum()), flagged_complete=int(m.flag[comp].sum()),
               blocks=dict(b2=int(m.b2.nunique()), b6=int(m.b6.nunique()), b12=int(m.b12.nunique()),
                           b2_with_flagged=int(m.b2[m.flag == 1].nunique()), b6_with_flagged=int(m.b6[m.flag == 1].nunique()),
                           b12_with_flagged=int(m.b12[m.flag == 1].nunique())),
               fu_years=C.FU_YEARS, target_events=TARGET_EVENTS, field_size_reference=ref,
               npz_sha256=C.sha256(out / "planted_inputs.npz"), sources=C.source_hashes(), inputs=C.input_hashes())
    atomic_json(out / "planted_inputs.json", rec)
    print(json.dumps({k: rec[k] for k in ("mapped_houses", "flagged", "complete_b1", "blocks", "field_size_reference")}, indent=1))


# ---------------------------------------------------------------- one dataset
_CTX = {}


def ctx(inputs):
    if not _CTX:
        d = np.load(inputs / "planted_inputs.npz")
        _CTX.update({k: d[k] for k in d.files})
        _CTX["xy"] = np.c_[_CTX["x_km"], _CTX["y_km"]]
    return _CTX


def gaussian_field(xy, range_km, sd, rng, chunk=8000):
    ell = range_km / LEN_FACTOR
    w = rng.normal(0, 1 / ell, size=(2, N_RFF))
    ph = rng.uniform(0, 2 * np.pi, N_RFF)
    out = np.empty(len(xy))
    for i in range(0, len(xy), chunk):
        out[i:i + chunk] = np.cos(xy[i:i + chunk] @ w + ph).sum(1)
    return sd * np.sqrt(2 / N_RFF) * out


def draw(cell, ds, inputs):
    """Synthetic outcomes of one dataset: (rows mask, y)."""
    K = ctx(inputs)
    kind, rng_km, sd, trend, generating, squared, lirr, _ = CELLS[cell]
    rng = np.random.default_rng([MASTER, cell, ds])
    rows = K["complete"] if generating else np.ones(len(K["flag"]), bool)
    eta = gaussian_field(K["xy"], rng_km, sd, rng)
    if trend:
        th = rng.uniform(0, 2 * np.pi)
        u = (K["x_km"] - K["x_km"].mean()) * np.cos(th) + (K["y_km"] - K["y_km"].mean()) * np.sin(th)
        eta = eta + u / 40.0
    if generating:
        eta = eta + (K["eta_gen_sq"] if squared else K["eta_gen"])
    eta = eta + lirr * K["flag"]
    eta = eta[rows]
    target = TARGET_EVENTS * rows.sum() / len(rows)
    a0 = brentq(lambda a: expit(a + eta).sum() - target, -30, 10)
    y = (rng.random(rows.sum()) < expit(a0 + eta)).astype(float)
    return rows, y


def run_one(cell, ds, inputs, out):
    path = out / "records" / f"cell{cell:02d}_ds{ds:04d}.json"
    if path.exists():
        return 0.0
    t0 = time.perf_counter()
    K = ctx(inputs)
    rows, y = draw(cell, ds, inputs)
    py = np.full(rows.sum(), C.FU_YEARS)
    off = np.log(py)
    groups = {k: K[k][rows] for k in ("b2", "b6", "b12")}
    x = K["flag"][rows]
    rec = dict(cell=cell, ds=ds, events=int(y.sum()), flagged_events=int(y[x == 1].sum()), rows=int(rows.sum()))
    O = np.bincount(groups["b2"], weights=y)
    nb = np.bincount(groups["b2"])
    keep = nb > 0
    rec["block_sd_log"] = block_sd_log(O[keep], nb[keep])
    X = C.design(None, None, x)
    fit = C.fit_flag(X, y, off)
    rec["V"] = {m: {k: v for k, v in C.infer(X, y, off, groups, m, [C.SEED_WILD, cell, ds], interval=False, fit=fit).items()
                    if k in ("log_irr", "p_one_sided")} for m in C.METHODS}
    if cell in U_CELLS:
        XB = K["XB"][rows]
        cols = list(range(XB.shape[1]))
        Xa = C.design(cols, pd.DataFrame(XB), x)
        fa = C.fit_flag(Xa, y, off)
        rec["U_adjusted"] = {m: {k: v for k, v in C.infer(Xa, y, off, groups, m, [C.SEED_WILD, cell, ds], interval=False, fit=fa).items()
                                 if k in ("log_irr", "p_one_sided")} for m in C.METHODS}
        folds = C.fold_assignments(groups["b2"], K["fold42"][rows], y)
        T, dl = C.t_statistic(XB, x, y, folds)
        rec["U_T"], rec["U_dl"] = T, dl
    rec["seconds"] = time.perf_counter() - t0
    atomic_json(path, rec)
    return rec["seconds"]


def cmd_run(a):
    from concurrent.futures import ProcessPoolExecutor
    (a.out / "records").mkdir(parents=True, exist_ok=True)
    jobs = []
    nmax = max(v[-1] for v in CELLS.values())
    for ds in range(nmax):  # dataset-major
        for cell, spec in CELLS.items():
            if ds < spec[-1] and not (a.out / "records" / f"cell{cell:02d}_ds{ds:04d}.json").exists():
                jobs.append((cell, ds))
    if a.limit:
        jobs = jobs[:a.limit]
    print(f"{len(jobs)} jobs, {a.workers} workers", flush=True)
    t0 = time.time()
    done = 0
    secs = []
    with ProcessPoolExecutor(a.workers) as ex:
        for s in ex.map(run_one, *zip(*jobs), [a.inputs] * len(jobs), [a.out] * len(jobs), chunksize=1):
            done += 1
            secs.append(s)
            if done == min(len(jobs), 4 * a.workers):
                proj = dict(first_round=done, mean_job_seconds=float(np.mean(secs)), workers=a.workers, jobs=len(jobs),
                            projected_hours=float(np.mean(secs) * len(jobs) / a.workers / 3600),
                            written=time.strftime("%Y-%m-%d %H:%M:%S"))
                atomic_json(a.out / "projection.json", proj)
                print("projection", proj, flush=True)
            if done % 500 == 0:
                print(done, f"{(time.time() - t0) / 60:.1f} min", flush=True)
    print("done", done, f"{(time.time() - t0) / 60:.1f} min", flush=True)


# ---------------------------------------------------------------- summarise
def t_interval(v):
    v = np.asarray(v, float)
    if len(v) < 2:
        return None
    from scipy.stats import t
    se = v.std(ddof=1) / np.sqrt(len(v))
    q = t.ppf(0.975, len(v) - 1)
    return [float(v.mean() - q * se), float(v.mean() + q * se)]


def rate(recs, key, m):
    k = sum(1 for r in recs if r[key][m]["p_one_sided"] < 0.05 and r[key][m]["log_irr"] > 0)
    lo, hi = C.wilson(k, len(recs))
    return dict(rejections=k, n=len(recs), rate=k / len(recs) if recs else None, wilson95=[lo, hi])


def cmd_summarise(a):
    recs = {}
    for p in sorted((a.out / "records").glob("cell*_ds*.json")):
        r = json.loads(p.read_text())
        recs.setdefault(r["cell"], []).append(r)
    inp = json.loads((C.STUDY / "step0/planted_inputs.json").read_text())
    S = dict(cells={}, field_size_reference=inp["field_size_reference"], fu_years=C.FU_YEARS)
    for cell, rs in sorted(recs.items()):
        spec = CELLS[cell]
        d = dict(kind=spec[0], range_km=spec[1], sd=spec[2], trend=spec[3], generating=spec[4], soil_squared=spec[5],
                 irr=float(np.exp(spec[6])), datasets=len(rs), planned=spec[-1],
                 events_mean=float(np.mean([r["events"] for r in rs])), flagged_events_mean=float(np.mean([r["flagged_events"] for r in rs])),
                 block_sd_log_median=float(np.median([r["block_sd_log"] for r in rs])),
                 V={m: rate(rs, "V", m) | dict(mean_log_irr=float(np.mean([r["V"][m]["log_irr"] for r in rs])),
                                               mean_log_irr_ci95=t_interval([r["V"][m]["log_irr"] for r in rs])) for m in C.METHODS})
        if cell in V_NULL:
            for m in C.METHODS:
                v = d["V"][m]
                v["acceptable"] = bool(v["wilson95"][0] <= 0.05 and v["rate"] <= 0.075 and v["mean_log_irr_ci95"][0] <= 0)
        if "U_T" in rs[0]:
            T = np.array([r["U_T"] for r in rs])
            d["U_adjusted"] = {m: rate(rs, "U_adjusted", m) for m in C.METHODS}
            d["U_T"] = dict(mean=float(T.mean()), q05=float(np.quantile(T, 0.05)), median=float(np.median(T)),
                            q95=float(np.quantile(T, 0.95)), share_positive=float((T > 0).mean()))
            d["U_detected"] = {m: float(np.mean([(r["U_T"] > 0) and r["U_adjusted"][m]["p_one_sided"] < 0.05 and r["U_adjusted"][m]["log_irr"] > 0
                                                 for r in rs])) for m in C.METHODS}
        S["cells"][str(cell)] = d
    complete = all(str(c) in S["cells"] and S["cells"][str(c)]["datasets"] == CELLS[c][-1] for c in CELLS)
    chosen = None
    if all(str(c) in S["cells"] for c in V_NULL):
        for m in C.METHODS:
            if all(S["cells"][str(c)]["V"][m]["acceptable"] for c in V_NULL):
                chosen = m
                break
    S["rule"] = dict(complete=complete, chosen_inference=chosen, branch="first acceptable of r1-r4" if chosen else "none acceptable: the user decides",
                     power_at_delta=S["cells"].get("9", {}).get("V", {}).get(chosen, {}).get("rate") if chosen else None)
    S["record_count"] = sum(len(v) for v in recs.values())
    atomic_json(a.out / "planted_summary.json", S)
    lines = ["# Planted check (OHENHEN_AUSTIN_PLAN.md §9; synthetic outcomes only)", "",
             f"Field-size reference (outcome only, 2018-08-01 to 2021-12-31, {S['field_size_reference']['events']} events, "
             f"{S['field_size_reference']['blocks']} blocks): between-block SD of the log rate {S['field_size_reference']['between_block_sd_log']:.3f}.", "",
             "Rejection = IRR > 1 and one-sided p < 0.05. V = unadjusted flag; U adj = flag adjusted for Baseline 1 + x/y.", "",
             "| Cell | Kind | Datasets | Events (flagged) | Block SD | " + " | ".join(f"V {m}" for m in C.METHODS) + " | U adj (r1, r2, r3, r4) | T>0 share |",
             "|---|---|---|---|---|" + "---|" * len(C.METHODS) + "---|---|"]
    for c, d in S["cells"].items():
        vv = " | ".join(f"{d['V'][m]['rate']:.3f}" + ("" if "acceptable" not in d["V"][m] else (" ok" if d["V"][m]["acceptable"] else " NO")) for m in C.METHODS)
        ua = ", ".join(f"{d['U_adjusted'][m]['rate']:.3f}" for m in C.METHODS) if "U_adjusted" in d else ""
        tp = f"{d['U_T']['share_positive']:.3f}" if "U_T" in d else ""
        lines.append(f"| {c} | {d['kind']} (range {d['range_km']} km, SD {d['sd']}{', trend' if d['trend'] else ''}, IRR {d['irr']:.2f}) | {d['datasets']} | "
                     f"{d['events_mean']:.0f} ({d['flagged_events_mean']:.1f}) | {d['block_sd_log_median']:.3f} | {vv} | {ua} | {tp} |")
    lines += ["", f"**Rule:** {S['rule']['branch']}; chosen inference: {chosen}; power at IRR 1.5 (cell 9): {S['rule']['power_at_delta']}; complete: {complete}."]
    (a.out / "PLANTED.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare")
    r = sub.add_parser("run")
    r.add_argument("--inputs", type=Path, default=C.STUDY / "step0")
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--workers", type=int, default=16)
    r.add_argument("--limit", type=int, default=0)
    s = sub.add_parser("summarise")
    s.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    {"prepare": cmd_prepare, "run": cmd_run, "summarise": cmd_summarise}[a.cmd](a)


if __name__ == "__main__":
    main()
