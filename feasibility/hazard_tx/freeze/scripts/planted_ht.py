"""Planted check of HAZARD_TX_PLAN.md §9 (synthetic outcomes only; the real map and the real mapped houses).

  prepare   -> step0/planted_inputs.npz + planted_inputs.json (houses with a hazard class and complete Baseline 1,
               flag, city, blocks, Baseline 1, generating predictor; the planning event counts; the outcome-only
               field-size reference). No permit is linked to any map value.
  run       -> OUT/records/cell{c:02d}_ds{d:04d}.json (resume-safe), OUT/projection.json after the first round
  summarise -> OUT/planted_summary.json, OUT/PLANTED.md (acceptability, rule, power)

Synthetic world (§9):
- Rows: the primary analysis rows (§7), i.e. mapped houses with complete Baseline 1, in every city given to prepare.
- Fixed follow-up of FU_YEARS for every house; Bernoulli events with logit = a_city + eta. a_city is solved per
  dataset so that each city's expected count equals its planning figure (eligible houses whose first linked
  foundation permit on record was issued 2022-2025, from the link table, x the share of eligible houses that are
  mapped and complete).
- Hidden field: stationary Gaussian random field from 2,000 random Fourier features, squared-exponential covariance
  with correlation 0.05 at the stated range (length scale = range / sqrt(2 ln 20)), SD as stated, coordinates in km.
  Cities are hundreds of km apart, so one field over all rows is independent between cities.
- Trend (cell 6): a linear trend of 1 logit per 40 km in a random direction, centred on each city.
- Generating model (cells 7-10): the Austin generating coefficients
  (feasibility/austin/planted_signal/generating_coefficients.json), transported unchanged, on Baseline 1 columns
  standardised within each city (mean and SD over the rows). Cell 8 replaces the soil term by its square
  (standardised), so the adjusted model is misspecified (reported, not part of the rule).
- Flag effect: log IRR x flag (cells 9 and 10).

Fits per dataset (all cells): the primary pooled adjusted Poisson model (ht_core.pooled_design: a city intercept and
city x Baseline 1 terms, flag last) under r1-r4; the unadjusted flag (city intercepts + flag) under r1-r4, reported.
Cells 7-10: T per city (out-of-fold log-likelihood gain of nyc_lib LR, 11 fold assignments computed from the label),
pooled T = sum over cities.
Acceptability (§9, as Ohenhen-Austin) is judged on the primary adjusted test in null cells 1-6. Rule (D2, user
2026-11-19): r3 if acceptable in all null cells; otherwise the first acceptable of r1, r2, r4; otherwise the user decides.
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
import ht_core as H  # noqa: E402

C = H.C
MASTER = 20261120
N_RFF = 2000
LEN_FACTOR = np.sqrt(2 * np.log(20))
GEN = H.ROOT / "feasibility/austin/planted_signal/generating_coefficients.json"
# cell: (kind, range_km, sd, trend, generating, soil_squared, log_irr, datasets)
CELLS = {
    1: ("null", 1, 0.5, False, False, False, 0.0, 1000),
    2: ("null", 3, 0.5, False, False, False, 0.0, 1000),
    3: ("null", 8, 0.5, False, False, False, 0.0, 1000),
    4: ("null", 15, 0.5, False, False, False, 0.0, 1000),
    5: ("null", 3, 1.0, False, False, False, 0.0, 1000),
    6: ("null", 3, 0.5, True, False, False, 0.0, 1000),
    7: ("U null", 3, 0.5, False, True, False, 0.0, 500),
    8: ("U null, soil squared (reported)", 3, 0.5, False, True, True, 0.0, 500),
    9: ("power", 3, 0.5, False, True, False, np.log(1.5), 500),
    10: ("power", 3, 0.5, False, True, False, np.log(1.74), 500),
}
NULL = [1, 2, 3, 4, 5, 6]
T_CELLS = [7, 8, 9, 10]


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


def outcome_only(city, h):
    """Planning count and field-size reference from the link table. Uses account numbers and 2 km blocks of ALL
    eligible houses; no map value is read here."""
    lid = "ACCOUNT_NUM" if city == "dallas" else H.ID_COL[city]  # San Antonio's link table is keyed by PropID
    L = pd.read_parquet(H.LINKS[city], columns=["permit_type", "issue_date", lid, "target"]).rename(columns={lid: "ACCOUNT_NUM"})
    L = L[L.permit_type.eq(H.EVENT_TYPE[city]) & L.target.eq("population house")]
    first = L.groupby("ACCOUNT_NUM").issue_date.min()
    fu = first.index[(first >= H.START) & (first <= H.END)]  # first permit on record (Dallas from 2021, San Antonio from 2020-07-20) falls in follow-up
    hb = h.set_index("ACCOUNT_NUM").b2
    nb = hb.value_counts()
    ref = {}
    for name, acc in (("2021 (before follow-up)", L[L.issue_date.dt.year.eq(2021)].ACCOUNT_NUM.unique()),
                      ("2022-2025 (follow-up; outcome only)", fu)):
        O = pd.Series(acc).map(hb).value_counts().reindex(nb.index, fill_value=0)
        ref[name] = dict(houses_with_event=int(O.sum()), blocks=int(len(O)), between_block_sd_log=block_sd_log(O.to_numpy(), nb.to_numpy()))
    return dict(eligible_houses=len(h), houses_with_first_permit_in_follow_up=int(len(fu)),
                houses_with_permit_any_year=int(len(first)), field_size_reference=ref)


def cmd_prepare(a):
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    assert not (out / "planted_inputs.npz").exists(), "planted inputs exist: choose a new --out"
    gen = json.loads(GEN.read_text())
    assert gen["columns"] == H.B1, gen["columns"]
    coef = np.array(gen["coefficients_on_standardised_columns"])
    soil = H.B1.index("lep_0_150")
    parts, rec = [], dict(cities={}, fu_years=H.FU_YEARS, generating_coefficients_sha256=H.sha256(GEN))
    for k, city in enumerate(a.cities):
        h = H.load_city(city)
        oo = outcome_only(city, h)
        m = h[h.mapped & h.complete_b1].reset_index(drop=True)
        cc = H.B1_BY_CITY[city]
        idx = [H.B1.index(c) for c in cc]  # a column the city lacks (San Antonio: slab) has no generating term there
        Z = m[cc].to_numpy(float)
        Z = (Z - Z.mean(0)) / Z.std(0)
        eta_gen = Z @ coef[idx]
        s = cc.index("lep_0_150")
        sq = Z[:, s] ** 2
        sq = (sq - sq.mean()) / sq.std()
        eta_gen_sq = eta_gen - coef[soil] * Z[:, s] + coef[soil] * sq
        share = len(m) / len(h)
        target = oo["houses_with_first_permit_in_follow_up"] * share
        parts.append(pd.DataFrame(dict(city=k, flag=m.flag, b2=m.b2, b6=m.b6, b12=m.b12,
                                       eta_gen=eta_gen, eta_gen_sq=eta_gen_sq)).join(m[H.B1].fillna(0.0).reset_index(drop=True)))
        rec["cities"][city] = dict(index=k, eligible=len(h), mapped=int(h.mapped.sum()), mapped_complete=len(m),
                                   flagged=int(m.flag.sum()), share_mapped_complete=share, target_events=target,
                                   expected_flagged_events_if_unrelated=target * float(m.flag.mean()),
                                   blocks=dict(b2=int(m.b2.nunique()), b6=int(m.b6.nunique()), b12=int(m.b12.nunique()),
                                               b2_with_flagged=int(m.b2[m.flag == 1].nunique()),
                                               b6_with_flagged=int(m.b6[m.flag == 1].nunique()),
                                               b12_with_flagged=int(m.b12[m.flag == 1].nunique())),
                                   outcome_only=oo, inputs=H.input_hashes(city), links_sha256=H.sha256(H.LINKS[city]))
    d = pd.concat(parts, ignore_index=True)
    np.savez(out / "planted_inputs.npz", city=d.city.to_numpy(np.int64), x_km=d.x_km.to_numpy(float), y_km=d.y_km.to_numpy(float),
             flag=d.flag.to_numpy(float), b2=pd.factorize(d.b2)[0], b6=pd.factorize(d.b6)[0], b12=pd.factorize(d.b12)[0],
             XB=d[H.B1].to_numpy(float), eta_gen=d.eta_gen.to_numpy(float), eta_gen_sq=d.eta_gen_sq.to_numpy(float),
             target=np.array([rec["cities"][c]["target_events"] for c in a.cities]), city_names=np.array(a.cities),
             col_mask=np.array([[b in H.B1_BY_CITY[c] for b in H.B1] for c in a.cities]))
    rec.update(city_order=list(a.cities), rows=len(d), npz_sha256=H.sha256(out / "planted_inputs.npz"), sources=H.source_hashes(),
               note="No permit was linked to any map value: planning counts and the field-size reference use eligible houses only.")
    atomic_json(out / "planted_inputs.json", rec)
    print(json.dumps(rec, indent=1, default=str))


# ---------------------------------------------------------------- one dataset
_CTX = {}


def ctx(inputs):
    if not _CTX:
        d = np.load(inputs / "planted_inputs.npz")
        _CTX.update({k: d[k] for k in d.files})
        _CTX["xy"] = np.c_[_CTX["x_km"], _CTX["y_km"]]
        cities = _CTX["city"]
        _CTX["cities"] = sorted(set(cities.tolist()))
        names = [str(v) for v in _CTX["city_names"]] if "city_names" in _CTX else ["dallas"]  # the Dallas-only npz of 11-19
        _CTX["names"] = dict(enumerate(names))
        if "col_mask" not in _CTX:
            _CTX["col_mask"] = np.ones((len(names), len(H.B1)), bool)
        frame = pd.DataFrame(_CTX["XB"], columns=H.B1)
        _CTX["X_adj"] = H.pooled_design(frame, cities, _CTX["flag"], names=_CTX["names"])
        _CTX["X_unadj"] = H.pooled_design(frame, cities, _CTX["flag"], cols=[])
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
    """Synthetic outcomes of one dataset (all rows)."""
    K = ctx(inputs)
    kind, rng_km, sd, trend, generating, squared, lirr, _ = CELLS[cell]
    rng = np.random.default_rng([MASTER, cell, ds])
    eta = gaussian_field(K["xy"], rng_km, sd, rng)
    if trend:
        th = rng.uniform(0, 2 * np.pi)
        for c in K["cities"]:
            s = K["city"] == c
            u = (K["x_km"][s] - K["x_km"][s].mean()) * np.cos(th) + (K["y_km"][s] - K["y_km"][s].mean()) * np.sin(th)
            eta[s] += u / 40.0
    if generating:
        eta = eta + (K["eta_gen_sq"] if squared else K["eta_gen"])
    eta = eta + lirr * K["flag"]
    p = np.empty(len(eta))
    for c in K["cities"]:
        s = K["city"] == c
        a0 = brentq(lambda a: expit(a + eta[s]).sum() - K["target"][c], -30, 10)
        p[s] = expit(a0 + eta[s])
    return (rng.random(len(p)) < p).astype(float)


def run_one(cell, ds, inputs, out):
    path = out / "records" / f"cell{cell:02d}_ds{ds:04d}.json"
    if path.exists():
        return 0.0
    t0 = time.perf_counter()
    K = ctx(inputs)
    y = draw(cell, ds, inputs)
    off = np.full(len(y), np.log(H.FU_YEARS))
    groups = {k: K[k] for k in ("b2", "b6", "b12")}
    x = K["flag"]
    rec = dict(cell=cell, ds=ds, events=int(y.sum()), flagged_events=int(y[x == 1].sum()),
               events_by_city={str(c): int(y[K["city"] == c].sum()) for c in K["cities"]},
               flagged_events_by_city={str(c): int(y[(K["city"] == c) & (x == 1)].sum()) for c in K["cities"]})
    O, nb = np.bincount(groups["b2"], weights=y), np.bincount(groups["b2"])
    rec["block_sd_log"] = block_sd_log(O[nb > 0], nb[nb > 0])
    rec["block_sd_log_by_city"] = {}
    for c in K["cities"]:
        bc = np.unique(groups["b2"][K["city"] == c])
        rec["block_sd_log_by_city"][str(c)] = block_sd_log(O[bc], nb[bc])
    seed = [H.SEED_WILD, cell, ds]
    for key, X in (("adjusted", K["X_adj"]), ("unadjusted", K["X_unadj"])):
        fit = C.fit_flag(X, y, off)
        rec[key] = {m: {k: v for k, v in C.infer(X, y, off, groups, m, seed, interval=False, fit=fit).items()
                        if k in ("log_irr", "p_one_sided")} for m in H.METHODS}
    if len(K["cities"]) > 1:  # each city's own adjusted test (descriptive), r3 only
        rec["adjusted_by_city"] = {}
        for c in K["cities"]:
            s = K["city"] == c
            Xc = H.pooled_design(pd.DataFrame(K["XB"][s], columns=H.B1), K["city"][s], x[s], names=K["names"])
            gc = {k: v[s] for k, v in groups.items()}
            r = C.infer(Xc, y[s], off[s], gc, "r3", seed, interval=False)
            rec["adjusted_by_city"][str(c)] = dict(log_irr=r["log_irr"], p_one_sided=r["p_one_sided"])
    if cell in T_CELLS:
        rec["T_by_city"] = {}
        for c in K["cities"]:
            s = K["city"] == c
            folds = H.fold_assignments(groups["b2"][s], y[s])
            T, _ = H.t_statistic(K["XB"][s][:, K["col_mask"][c]], x[s], y[s], folds)
            rec["T_by_city"][str(c)] = T
        rec["T"] = float(sum(rec["T_by_city"].values()))
    rec["seconds"] = time.perf_counter() - t0
    atomic_json(path, rec)
    return rec["seconds"]


def cmd_run(a):
    from concurrent.futures import ProcessPoolExecutor
    (a.out / "records").mkdir(parents=True, exist_ok=True)
    jobs = []
    nmax = max(v[-1] for v in CELLS.values())
    cells = a.cells or list(CELLS)
    for ds in range(nmax):  # dataset-major
        for cell in cells:
            if ds < CELLS[cell][-1] and not (a.out / "records" / f"cell{cell:02d}_ds{ds:04d}.json").exists():
                jobs.append((cell, ds))
    if a.limit:
        jobs = jobs[:a.limit]
    print(f"{len(jobs)} jobs, {a.workers} workers", flush=True)
    t0 = time.time()
    done, secs = 0, []
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


def rejected(r, key, m):
    return r[key][m]["p_one_sided"] < 0.05 and r[key][m]["log_irr"] > 0


def rate(recs, key, m):
    k = sum(rejected(r, key, m) for r in recs)
    lo, hi = C.wilson(k, len(recs))
    return dict(rejections=k, n=len(recs), rate=k / len(recs) if recs else None, wilson95=[lo, hi],
                mean_log_irr=float(np.mean([r[key][m]["log_irr"] for r in recs])),
                mean_log_irr_ci95=t_interval([r[key][m]["log_irr"] for r in recs]))


def cmd_summarise(a):
    recs = {}
    for p in sorted((a.out / "records").glob("cell*_ds*.json")):
        r = json.loads(p.read_text())
        recs.setdefault(r["cell"], []).append(r)
    inp = json.loads((a.inputs / "planted_inputs.json").read_text())
    S = dict(inputs=dict(npz_sha256=inp["npz_sha256"], cities={c: {k: v for k, v in d.items() if k not in ("inputs",)}
                                                               for c, d in inp["cities"].items()}),
             fu_years=H.FU_YEARS, cells={})
    for cell, rs in sorted(recs.items()):
        spec = CELLS[cell]
        d = dict(kind=spec[0], range_km=spec[1], sd=spec[2], trend=spec[3], generating=spec[4], soil_squared=spec[5],
                 irr=float(np.exp(spec[6])), datasets=len(rs), planned=spec[-1],
                 events_mean=float(np.mean([r["events"] for r in rs])), flagged_events_mean=float(np.mean([r["flagged_events"] for r in rs])),
                 block_sd_log_median=float(np.median([r["block_sd_log"] for r in rs])),
                 block_sd_log_median_by_city={c: float(np.median([r["block_sd_log_by_city"][c] for r in rs]))
                                              for c in rs[0].get("block_sd_log_by_city", {})},
                 adjusted={m: rate(rs, "adjusted", m) for m in H.METHODS},
                 unadjusted={m: rate(rs, "unadjusted", m) for m in H.METHODS})
        if cell in NULL:
            for m in H.METHODS:
                v = d["adjusted"][m]
                ci = v["mean_log_irr_ci95"]
                v["acceptable"] = bool(v["wilson95"][0] <= 0.05 and v["rate"] <= 0.075 and ci is not None and ci[0] <= 0)
        if "T" in rs[0]:
            T = np.array([r["T"] for r in rs])
            d["T"] = dict(mean=float(T.mean()), q05=float(np.quantile(T, 0.05)), median=float(np.median(T)),
                          q95=float(np.quantile(T, 0.95)), share_positive=float((T > 0).mean()))
            d["demonstrated"] = {m: float(np.mean([(r["T"] > 0) and rejected(r, "adjusted", m) for r in rs])) for m in H.METHODS}
        if "adjusted_by_city" in rs[0]:  # per-city r3 tests (descriptive; D1 alternative: Holm over two cities)
            names = inp.get("city_order", [])
            d["by_city"] = {}
            for c in rs[0]["adjusted_by_city"]:
                o = [k for k in rs[0]["adjusted_by_city"] if k != c]
                pc = np.array([r["adjusted_by_city"][c]["p_one_sided"] if r["adjusted_by_city"][c]["log_irr"] > 0 else 1.0 for r in rs])
                po = np.array([min(r["adjusted_by_city"][k]["p_one_sided"] if r["adjusted_by_city"][k]["log_irr"] > 0 else 1.0 for k in o) for r in rs]) if o else np.ones(len(rs))
                holm = (pc < 0.025) | ((pc < 0.05) & (po < 0.025))
                e = dict(name=names[int(c)] if names else c, r3_reject_05=float(np.mean(pc < 0.05)), r3_reject_025=float(np.mean(pc < 0.025)),
                         r3_reject_holm=float(np.mean(holm)), mean_log_irr=float(np.mean([r["adjusted_by_city"][c]["log_irr"] for r in rs])))
                if "T_by_city" in rs[0]:
                    tp = np.array([r["T_by_city"][c] > 0 for r in rs])
                    e.update(T_share_positive=float(tp.mean()), demonstrated_05=float(np.mean(tp & (pc < 0.05))),
                             demonstrated_025=float(np.mean(tp & (pc < 0.025))), demonstrated_holm=float(np.mean(tp & holm)))
                d["by_city"][c] = e
            if "T_by_city" in rs[0] and len(rs[0]["adjusted_by_city"]) > 1:
                anyh = np.zeros(len(rs), bool)
                for c in rs[0]["adjusted_by_city"]:
                    o = [k for k in rs[0]["adjusted_by_city"] if k != c]
                    pc = np.array([r["adjusted_by_city"][c]["p_one_sided"] if r["adjusted_by_city"][c]["log_irr"] > 0 else 1.0 for r in rs])
                    po = np.array([min(r["adjusted_by_city"][k]["p_one_sided"] if r["adjusted_by_city"][k]["log_irr"] > 0 else 1.0 for k in o) for r in rs])
                    tp = np.array([r["T_by_city"][c] > 0 for r in rs])
                    anyh |= tp & ((pc < 0.025) | ((pc < 0.05) & (po < 0.025)))
                d["holm_any_city_demonstrated"] = float(anyh.mean())
        S["cells"][str(cell)] = d
    complete = all(str(c) in S["cells"] and S["cells"][str(c)]["datasets"] == CELLS[c][-1] for c in CELLS)
    chosen = None
    if all(str(c) in S["cells"] for c in NULL):  # §9 rule (D2, user 2026-11-19): r3 if acceptable, else r1, r2, r4 in order
        for m in ("r3", "r1", "r2", "r4"):
            if all(S["cells"][str(c)]["adjusted"][m]["acceptable"] for c in NULL):
                chosen = m
                break
    pw = {str(c): S["cells"][str(c)]["demonstrated"][chosen] for c in (9, 10) if chosen and str(c) in S["cells"]}
    S["rule"] = dict(complete=complete, chosen_inference=chosen,
                     branch=("r3 acceptable in null cells 1-6 (adjusted test)" if chosen == "r3" else
                             "r3 not acceptable: first acceptable of r1, r2, r4" if chosen else "none acceptable: the user decides"),
                     acceptable_in_all_null_cells=[m for m in H.METHODS if all(S["cells"].get(str(c), {}).get("adjusted", {}).get(m, {}).get("acceptable") for c in NULL)],
                     power_demonstrated=pw)
    S["record_count"] = sum(len(v) for v in recs.values())
    atomic_json(a.out / "planted_summary.json", S)
    lines = ["# Planted check (HAZARD_TX_PLAN.md §9; synthetic outcomes only)", ""]
    for c, ci in S["inputs"]["cities"].items():
        lines.append(f"- **{c}:** {ci['mapped_complete']:,} rows (mapped, complete Baseline 1), {ci['flagged']:,} flagged; target "
                     f"{ci['target_events']:.0f} events ({ci['expected_flagged_events_if_unrelated']:.1f} flagged if unrelated); "
                     f"blocks b2/b6/b12 {ci['blocks']['b2']}/{ci['blocks']['b6']}/{ci['blocks']['b12']} "
                     f"(with flagged houses {ci['blocks']['b2_with_flagged']}/{ci['blocks']['b6_with_flagged']}/{ci['blocks']['b12_with_flagged']}).")
        for k, v in ci["outcome_only"]["field_size_reference"].items():
            lines.append(f"  - field-size reference, {k}: {v['houses_with_event']} houses with an event, {v['blocks']} blocks, "
                         f"between-block SD of the log rate {v['between_block_sd_log']:.3f}")
    lines += ["", "Rejection = IRR > 1 and one-sided p < 0.05. Adjusted = the primary model (city intercepts, city x Baseline 1, flag). "
              "'ok'/'NO' = acceptability (null cells 1-6). Demonstrated = rejected and T > 0.", "",
              "| Cell | Kind | Datasets | Events (flagged) | Block SD | " + " | ".join(f"adj {m}" for m in H.METHODS) +
              " | unadj r1-r4 | T>0 | demonstrated r1-r4 |",
              "|---|---|---|---|---|" + "---|" * len(H.METHODS) + "---|---|---|"]
    for c, d in S["cells"].items():
        vv = " | ".join(f"{d['adjusted'][m]['rate']:.3f}" + ("" if "acceptable" not in d["adjusted"][m] else (" ok" if d["adjusted"][m]["acceptable"] else " NO"))
                        for m in H.METHODS)
        ua = ", ".join(f"{d['unadjusted'][m]['rate']:.3f}" for m in H.METHODS)
        tp = f"{d['T']['share_positive']:.3f}" if "T" in d else ""
        dm = ", ".join(f"{d['demonstrated'][m]:.3f}" for m in H.METHODS) if "demonstrated" in d else ""
        lines.append(f"| {c} | {d['kind']} (range {d['range_km']} km, SD {d['sd']}{', trend' if d['trend'] else ''}, IRR {d['irr']:.2f}) | "
                     f"{d['datasets']} | {d['events_mean']:.0f} ({d['flagged_events_mean']:.1f}) | {d['block_sd_log_median']:.3f} | {vv} | {ua} | {tp} | {dm} |")
    if any("by_city" in d for d in S["cells"].values()):
        lines += ["", "Per city (r3, each city's own adjusted model; descriptive, and the D1 alternative of Holm over two cities). "
                  "Cells: rejection at 0.05 / 0.025 / Holm; for cells with T: demonstrated (own T > 0) at 0.05 / Holm. Block SD = median per city.", "",
                  "| Cell | City | Block SD | Reject 0.05 | Reject 0.025 | Reject Holm | Demonstrated 0.05 | Demonstrated Holm |", "|---|---|---|---|---|---|---|---|"]
        for cc, d in S["cells"].items():
            for k, e in d.get("by_city", {}).items():
                lines.append(f"| {cc} | {e['name']} | {d['block_sd_log_median_by_city'].get(k, float('nan')):.3f} | {e['r3_reject_05']:.3f} | {e['r3_reject_025']:.3f} | "
                             f"{e['r3_reject_holm']:.3f} | {e.get('demonstrated_05', float('nan')):.3f} | {e.get('demonstrated_holm', float('nan')):.3f} |")
            if "holm_any_city_demonstrated" in d:
                lines.append(f"| {cc} | either city (Holm) |  |  |  |  |  | {d['holm_any_city_demonstrated']:.3f} |")
    lines += ["", f"**Rule:** {S['rule']['branch']}; chosen inference: {chosen}; power (demonstrated) at IRR 1.5 (cell 9) and 1.74 (cell 10): "
              f"{pw}; complete: {complete}."]
    (a.out / "PLANTED.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("prepare")
    pr.add_argument("--cities", nargs="+", default=["dallas"])
    pr.add_argument("--out", type=Path, required=True, help="new folder for planted_inputs.npz/json (never overwritten)")
    r = sub.add_parser("run")
    r.add_argument("--inputs", type=Path, default=H.STUDY / "step0")
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--workers", type=int, default=16)
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--cells", type=int, nargs="*")
    s = sub.add_parser("summarise")
    s.add_argument("--inputs", type=Path, default=H.STUDY / "step0")
    s.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    {"prepare": cmd_prepare, "run": cmd_run, "summarise": cmd_summarise}[a.cmd](a)


if __name__ == "__main__":
    main()
