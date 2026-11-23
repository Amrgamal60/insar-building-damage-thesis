"""Analysis of OHENHEN_AUSTIN_PLAN.md §5-§11: cohort, V (decision), U, secondaries 1-13.

Modes:
  decoy  every real date is kept but given to random houses (first foundation episodes, demolitions, remodel
         episodes: each table to its own random distinct houses, seed 2071; events keep the mapping of their episode).
         Nothing about which house had which outcome is in reach. Labelled DECOY in every output.
  real   refused until the frozen plan exists and its SHA-256 equals FROZEN_SHA256 (set at freezing).

Person-time (§5): days from 2022-01-01 to the exit date; a house followed to the end gets (END - START) + 1 days,
an exit by episode or demolition (exit - START) + 0.5 days (mid-day convention); years of 365.25 days.
An event needs the house's first matched episode in follow-up, equal to its event date, before any demolition.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oa_core as C  # noqa: E402

sys.path.insert(0, str(C.AUSTIN / "planted_signal"))
import testa_core as TC  # noqa: E402

FROZEN_PLAN = C.STUDY / "freeze/OHENHEN_AUSTIN_PLAN_frozen.md"
FROZEN_SHA256 = "60aac893384f145d82c9b806ae3711938fc8f6c29264eb40e87f5b27d9358f75"  # set at freezing 2026-11-18
DECOY_SEED = 2071
EV = C.CP1 / "events"
RM = C.CP1 / "remodel_controls_amended"
PERMITS = C.CP1 / "permits_3syk-w9eu_20261109/3syk-w9eu_checkpoint1.csv"
PARCELS_2018 = C.PRIV / "austin/tcad/raw/traviscad.govqa.us_R010955-110226_gis2018/2018_Shapefiles.zip"
AGE_STRATA = [(-np.inf, 1989, "built to 1989"), (1990, 2009, "built 1990-2009"), (2010, 2015, "built 2010-2015")]
DAY = pd.Timedelta(days=1)


def atomic_json(path, obj):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)) + "\n")
    tmp.replace(path)


# ---------------------------------------------------------------- outcome world
def load_world(mode, h):
    ep = pd.read_parquet(EV / "foundation_first_episodes.parquet", columns=["prop_id", "t_first", "status"])
    ev = pd.read_parquet(EV / "foundation_events.parquet", columns=["prop_id", "t_first"])
    dem = pd.read_parquet(EV / "demolition_censoring.parquet", columns=["prop_id", "t_demolition"])
    rep = pd.read_parquet(RM / "remodel_first_episodes_amended.parquet", columns=["prop_id", "t_first"])
    rev = pd.read_parquet(RM / "remodel_control_events_amended.parquet", columns=["prop_id", "t_first"])
    for t in (ep, dem, rep):
        assert t.prop_id.is_unique and t.prop_id.isin(set(h.prop_id)).all()
    assert ev.prop_id.isin(set(ep.prop_id)).all() and rev.prop_id.isin(set(rep.prop_id)).all()
    if mode == "decoy":
        rng = np.random.default_rng(DECOY_SEED)
        houses = h.prop_id.to_numpy()

        def remap(*tables):
            m = dict(zip(tables[0].prop_id, rng.choice(houses, len(tables[0]), replace=False)))
            for t in tables:
                t["prop_id"] = t.prop_id.map(m)

        remap(ep, ev)
        remap(dem)
        remap(rep, rev)
    W = pd.DataFrame(dict(prop_id=h.prop_id))
    W["t_ep"] = h.prop_id.map(ep.set_index("prop_id").t_first).astype("datetime64[ns]")
    W["t_dem"] = h.prop_id.map(dem.set_index("prop_id").t_demolition).astype("datetime64[ns]")
    W["t_event"] = h.prop_id.map(ev.set_index("prop_id").t_first).astype("datetime64[ns]")
    W["t_rep"] = h.prop_id.map(rep.set_index("prop_id").t_first).astype("datetime64[ns]")
    W["t_revent"] = h.prop_id.map(rev.set_index("prop_id").t_first).astype("datetime64[ns]")
    has = W.t_event.notna()
    assert (W.t_event[has] == W.t_ep[has]).all(), "event is not its house's first matched episode"
    has = W.t_revent.notna()
    assert (W.t_revent[has] == W.t_rep[has]).all()
    return W


def follow(t_ep, t_dem, t_event, start, end, domain):
    """Cohort at risk at the end of the day before `start` (Austin at_risk), followed to `end` (inclusive)."""
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    at = TC.at_risk(start - DAY, t_ep.to_numpy("datetime64[ns]"), t_dem.to_numpy("datetime64[ns]")) & np.asarray(domain, bool)
    big = pd.Timestamp("2262-01-01")
    ep = t_ep.fillna(big).to_numpy("datetime64[ns]")
    dm = t_dem.fillna(big).to_numpy("datetime64[ns]")
    endn = np.datetime64(end, "ns")
    exit_ = np.minimum(np.minimum(ep, dm), endn)
    by_end = exit_ == endn
    event = at & (ep <= endn) & (ep < dm) & (t_event.to_numpy("datetime64[ns]") == ep)
    demol = at & (dm <= endn) & (dm <= ep)
    days = (exit_ - np.datetime64(start, "ns")) / np.timedelta64(1, "D")
    days = np.where(by_end & ~event & ~demol, days + 1, days + 0.5)
    return dict(at=at, y=event.astype(float), py=np.where(at, days / 365.25, 0.0), demolished=demol.astype(float),
                exit=exit_, first_episode_not_event=at & (ep <= endn) & (ep < dm) & ~event)


# ---------------------------------------------------------------- V-type and U-type analyses
def groups_of(h, rows):
    return {k: h[k].to_numpy()[rows] for k in ("b2", "b6", "b12")}


def v_analysis(h, rows, y, py, x, chosen, seed, cols=None, extra=None, methods=None, interval=True):
    """Poisson IRR of the last column x on `rows`, optionally adjusted for `cols` (+ `extra` columns)."""
    frame = h.loc[rows, cols] if cols else None
    X = C.design(cols, frame, x[rows]) if extra is None else np.column_stack([C.design(cols, frame, np.zeros(rows.sum()))[:, :-1], extra, x[rows]])
    off = np.log(py[rows])
    fit = C.fit_flag(X, y[rows], off)
    out = dict(rows=int(rows.sum()), events=int(y[rows].sum()), person_years=float(py[rows].sum()))
    for m in (methods or [chosen]):
        out[m] = C.infer(X, y[rows], off, groups_of(h, rows), m, seed, interval=interval, fit=fit)
    return out


def headline_numbers(y, py, x, rows):
    u = C.unadjusted(y[rows], py[rows], x[rows] == 1)
    if u["irr"] is not None:
        e1, t1, r0 = u["events_flagged"], u["py_flagged"], u["events_other"] / u["py_other"]
        excess = e1 - t1 * r0
        u.update(rate_difference_per_1000=u["rate_flagged_per_1000"] - u["rate_other_per_1000"],
                sensitivity=e1 / max(1, e1 + u["events_other"]), share_flagged_with_event=e1 / max(1, u["houses_flagged"]),
                excess_events_flagged=float(excess), flagged_houses_per_excess_event=float(u["houses_flagged"] / excess) if excess > 0 else None)
    return u


def rd_interval(n, r):
    """Rate-difference intervals implied by the IRR intervals, the rate among other mapped houses held fixed (§7)."""
    if n.get("irr") is None:
        return None
    r0 = n["rate_other_per_1000"]
    return {lv: [None if r[f"lo{lv}"] is None else r0 * (r[f"lo{lv}"] - 1), None if r[f"hi{lv}"] is None else r0 * (r[f"hi{lv}"] - 1)]
            for lv in ("90", "95")}


def u_analysis(h, rows, y, x, chosen, seed, boot, jobs, py):
    from joblib import Parallel, delayed
    from sklearn.metrics import average_precision_score, roc_auc_score
    XB = h.loc[rows, C.B1].to_numpy(float)
    yy, xx = y[rows].astype(int), x[rows]
    blocks = h.b2.to_numpy()[rows]
    folds = C.fold_assignments(blocks, h.fold.to_numpy()[rows], yy)
    T, dl = C.t_statistic(XB, xx, yy, folds)
    s0, s1 = C.N.oof(XB, yy, folds[0], C.N.LR), C.N.oof(np.c_[XB, xx], yy, folds[0], C.N.LR)
    lg = np.log(np.clip(s1, 1e-15, 1 - 1e-15) / (1 - np.clip(s1, 1e-15, 1 - 1e-15)))
    import statsmodels.api as sm
    slope = sm.GLM(yy, sm.add_constant(lg), family=sm.families.Binomial()).fit().params[1]
    inter = sm.GLM(yy, np.ones((len(yy), 1)), family=sm.families.Binomial(), offset=lg).fit().params[0]
    dec = pd.qcut(s1, 10, labels=False, duplicates="drop")
    deciles = [dict(decile=int(k), houses=int((dec == k).sum()), observed=float(yy[dec == k].mean()), predicted=float(s1[dec == k].mean())) for k in np.unique(dec)]
    out = dict(rows=int(rows.sum()), events=int(yy.sum()), T=T, dl_by_assignment=dl,
               d_pr42=float(average_precision_score(yy, s1) - average_precision_score(yy, s0)),
               d_roc42=float(roc_auc_score(yy, s1) - roc_auc_score(yy, s0)),
               d_brier42=float(np.mean((s1 - yy) ** 2) - np.mean((s0 - yy) ** 2)),
               calibration_M1=dict(intercept=float(inter), slope=float(slope)), deciles_M1=deciles)
    out["adjusted"] = v_analysis(h, rows, y, py, x, chosen, seed, cols=C.B1)
    if boot:
        ub = np.unique(blocks)

        def rep(i):
            rng = np.random.default_rng([C.SEED_BOOT_T, i])
            idx = np.concatenate([np.flatnonzero(blocks == b) for b in rng.choice(ub, len(ub), replace=True)])
            try:
                return C.t_statistic(XB[idx], xx[idx], yy[idx], folds[:, idx])[0]
            except AssertionError:
                return None
        reps = Parallel(n_jobs=jobs)(delayed(rep)(i) for i in range(boot))
        kept = [r for r in reps if r is not None]
        out["T_bootstrap"] = dict(resamples=boot, kept=len(kept), ci95=np.percentile(kept, [2.5, 97.5]).tolist() if kept else None)
    a = out["adjusted"][chosen]
    out["detected_at_005"] = bool(T > 0 and a["p_one_sided"] < 0.05 and a["log_irr"] > 0)  # secondaries' descriptive reading
    return out


def holm(p):
    """Holm over the two co-primary tests (draft 3): {name: one-sided p} -> (level, rejected) per test. The smaller p
    is tested at 0.025; the other at 0.05 only if the first is rejected, otherwise the procedure stops (level 0.025)."""
    (n1, p1), (n2, p2) = sorted(p.items(), key=lambda t: (t[1], t[0] != "V"))
    r1 = p1 < 0.025
    return {n1: 0.025, n2: 0.05 if r1 else 0.025}, {n1: r1, n2: bool(r1 and p2 < 0.05)}


def reading(r, level, rejected, word=("validated", "not validated")):
    """§10 readings from the interval whose level matches the test's Holm level (0.025 -> 95%, 0.05 -> 90%)."""
    hi = r["hi95"] if level == 0.025 else r["hi90"]
    hi_v = np.inf if hi is None else hi
    if rejected:
        return f"{word[0]}, enrichment of delta or more not excluded" if hi_v >= 1.5 else f"{word[0]}, enrichment below delta"
    if hi_v < 1:
        return f"{word[1]}, opposite"
    if hi_v < 1.5:
        return f"{word[1]}, useful enrichment excluded"
    return f"{word[1]}, inconclusive"


# ---------------------------------------------------------------- inputs of secondaries 3, 7, 11
def vlm_at_houses(h):
    from pyproj import Transformer
    from scipy.spatial import cKDTree
    v = pd.read_csv(C.INPUTS["ohenhen/austin_VLM.csv"])
    vx, vy = Transformer.from_crs(4326, 32614, always_xy=True).transform(v.longitude_deg.to_numpy(), v.latitude_deg.to_numpy())
    idx = cKDTree(np.c_[vx, vy]).query_ball_point(np.c_[h.x, h.y], r=50)
    vals = v.VLM_mmPerYr.to_numpy()
    return np.array([vals[i].mean() if len(i) else np.nan for i in idx])


def new_construction_near(h, radius=150, min_permits=10):
    import pyogrio
    from scipy.spatial import cKDTree
    p = pd.read_csv(PERMITS, usecols=["permittype", "work_class", "permit_class_mapped", "tcad_id", "applieddate", "issue_date"], dtype=str)
    d = pd.to_datetime(p.applieddate.str[:10], errors="coerce").fillna(pd.to_datetime(p.issue_date.str[:10], errors="coerce"))
    sel = (p.permittype == "BP") & (p.work_class == "New") & (p.permit_class_mapped == "Residential") & (d >= "2015-01-01") & (d <= "2021-12-31")
    p = p[sel]
    par = pyogrio.read_dataframe(f"/vsizip/{PARCELS_2018}/2018_Shapefiles/Parcel_poly.shp", columns=["PID_10"]).to_crs(32614)
    par = par[par.PID_10.notna()].drop_duplicates("PID_10")
    cen = par.set_index(par.PID_10.astype(str)).geometry.centroid
    key = p.tcad_id.fillna("").str.strip()
    linked = key.isin(cen.index)
    pts = cen.loc[key[linked]]
    count = np.zeros(len(h), int)
    if len(pts):
        tree = cKDTree(np.c_[pts.x.to_numpy(), pts.y.to_numpy()])
        count = np.array([len(i) for i in tree.query_ball_point(np.c_[h.x, h.y], r=radius)])
    near = count >= min_permits
    return near, dict(new_residential_bp_2015_2021=int(sel.sum()), linked_to_2018_parcel=int(linked.sum()), unlinked=int((~linked).sum()),
                      min_permits_within_150m=min_permits, houses_excluded=int(near.sum()),
                      flagged_houses_excluded=int((near & (h.flag.to_numpy() == 1)).sum()))


def near_flag_edge(h, metres=30.0):
    import rasterio
    with rasterio.open(C.INPUTS["ohenhen/risk_austin.tif"]) as r:
        a = r.read(1).astype(float)
        a[~np.isfinite(a) | (a < -1e30)] = np.nan
        tf = r.transform
    colf = (h.lon.to_numpy() - tf.c) / tf.a
    rowf = (h.lat.to_numpy() - tf.f) / tf.e
    rr, cc = np.floor(rowf).astype(int), np.floor(colf).astype(int)
    fr, fc = rowf - rr, colf - cc
    wx = abs(tf.a) * 111_320 * np.cos(np.radians(h.lat.to_numpy()))
    wy = abs(tf.e) * 110_574
    flag_of = lambda r_, c_: np.where((r_ >= 0) & (r_ < a.shape[0]) & (c_ >= 0) & (c_ < a.shape[1]),
                                      a[np.clip(r_, 0, a.shape[0] - 1), np.clip(c_, 0, a.shape[1] - 1)], np.nan)
    own = np.isin(flag_of(rr, cc), C.FLAG_CLASSES)
    near = np.zeros(len(h), bool)
    for dr, dc, dist in ((0, -1, fc * wx), (0, 1, (1 - fc) * wx), (-1, 0, fr * wy), (1, 0, (1 - fr) * wy)):
        nb = flag_of(rr + dr, cc + dc)
        near |= np.isfinite(nb) & (np.isin(nb, C.FLAG_CLASSES) != own) & (dist <= metres)
    return near


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["decoy", "real"])
    ap.add_argument("--planted-summary", type=Path, required=True)
    ap.add_argument("--inference-choice", type=Path, help="the user's choice when the planted rule chose none (branch 2)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--skip", default="", help="decoy only: comma-separated secondary numbers to skip")
    a = ap.parse_args(argv)
    if a.mode == "real":
        assert FROZEN_SHA256 and FROZEN_PLAN.exists() and C.sha256(FROZEN_PLAN) == FROZEN_SHA256, \
            "real outcomes are refused until the plan is frozen (FROZEN_SHA256)"
        assert not a.skip, "no secondary is skipped in the real run"
    skip = {int(s) for s in a.skip.split(",") if s}
    label = "REAL RUN" if a.mode == "real" else "DECOY RUN (code check, not a result)"
    PS = json.loads(a.planted_summary.read_text())
    chosen = PS["rule"]["chosen_inference"]
    if chosen is None and a.inference_choice:
        IC = json.loads(a.inference_choice.read_text())
        assert IC["planted_summary_sha256"] == C.sha256(a.planted_summary), "the choice was made on another planted summary"
        chosen = IC["chosen_inference"]
    assert chosen in C.METHODS, "the planted rule chose no inference: the user decides first"
    power_V, power_U = PS["cells"]["9"]["V"][chosen]["rate"], PS["cells"]["11"]["U_detected"][chosen]
    others = [m for m in C.METHODS if m != chosen]
    a.out.mkdir(parents=True, exist_ok=True)
    times = {"start": time.strftime("%Y-%m-%d %H:%M:%S")}
    R = dict(label=label, chosen_inference=chosen, planted_summary_sha256=C.sha256(a.planted_summary),
             sources=C.source_hashes() | {"testa_core.py": C.sha256(C.AUSTIN / "planted_signal/testa_core.py")}, inputs=C.input_hashes())

    h = C.load_houses()
    W = load_world(a.mode, h)
    mapped = h.mapped.to_numpy()
    x = h.flag.to_numpy()
    F = follow(W.t_ep, W.t_dem, W.t_event, C.START, C.END, mapped)
    rows, y, py = F["at"], F["y"], F["py"]
    comp = h.complete_b1.to_numpy(bool)
    flow = dict(eligible=len(h), mapped=int(mapped.sum()), at_risk=int(rows.sum()), complete_b1=int((rows & comp).sum()))
    for f, name in ((1, "flagged"), (0, "other")):
        s = x == f
        flow[name] = dict(mapped=int((mapped & s).sum()), at_risk=int((rows & s).sum()), complete_b1=int((rows & comp & s).sum()),
                          events=int(y[rows & s].sum()), person_years=float(py[rows & s].sum()),
                          demolished=int(F["demolished"][rows & s].sum()), first_episode_not_event=int(F["first_episode_not_event"][rows & s].sum()))
    R["flow"] = flow
    print(label, json.dumps(flow), flush=True)

    # V (§7, §10)
    seed = [C.SEED_WILD, 0]
    V = v_analysis(h, rows, y, py, x, chosen, seed, methods=C.METHODS)
    V["numbers"] = headline_numbers(y, py, x, rows)
    r = V[chosen]
    V["numbers"]["rate_difference_interval_per_1000"] = rd_interval(V["numbers"], r)
    V["power_at_delta_planted"] = power_V
    R["V"] = V
    times["V"] = time.strftime("%Y-%m-%d %H:%M:%S")
    print("V", {k: r[k] for k in ("irr", "lo90", "hi90", "lo95", "hi95", "p_one_sided")}, flush=True)

    # headline table
    strata = np.select([h.year_built.to_numpy() <= 1989, h.year_built.to_numpy() <= 2009], [0, 1], 2)
    dummies = np.column_stack([(strata == 1), (strata == 2)]).astype(float)[rows]
    R["headline"] = dict(
        unadjusted=r,
        age_stratified=v_analysis(h, rows, y, py, x, chosen, seed, extra=dummies)[chosen] | dict(
            mantel_haenszel=C.mantel_haenszel(y[rows], py[rows], x[rows], strata[rows])),
        adjusted_baseline1=v_analysis(h, rows & comp, y, py, x, chosen, seed, cols=C.B1)[chosen])
    times["headline"] = time.strftime("%Y-%m-%d %H:%M:%S")

    # U (§8)
    R["U"] = u_analysis(h, rows & comp, y, x, chosen, seed, a.boot, a.jobs, py)
    for m in others:
        R["U"]["adjusted"][m] = v_analysis(h, rows & comp, y, py, x, m, seed, cols=C.B1)[m]
    times["U"] = time.strftime("%Y-%m-%d %H:%M:%S")
    # co-primary decisions with Holm (§10, draft 3)
    ua = R["U"]["adjusted"][chosen]
    level, rej = holm({"V": r["p_one_sided"], "U": ua["p_one_sided"]})
    V["holm_level"], V["holm_rejected"] = level["V"], rej["V"]
    V["decision"] = reading(r, level["V"], rej["V"])
    near1 = (r["lo95"] if level["V"] == 0.025 else r["lo90"]) if r["irr"] >= 1 else (r["hi95"] if level["V"] == 0.025 else r["hi90"])
    V["e_value"] = dict(irr=C.e_value(r["irr"]), bound_nearer_1=C.e_value(near1) if near1 is not None and (near1 - 1) * (r["irr"] - 1) > 0 else 1.0)
    U = R["U"]
    U["holm_level"], U["holm_rejected"], U["power_at_delta_planted"] = level["U"], rej["U"], power_U
    if rej["U"] and U["T"] <= 0:
        U["decision"] = "added information not demonstrated: association beyond the baseline without a held-out gain (T <= 0)"
    else:
        U["decision"] = reading(ua, level["U"], rej["U"] and U["T"] > 0, word=("added information demonstrated", "added information not demonstrated"))
    print("V", V["decision"], "| U", U["decision"], "| T", U["T"], flush=True)
    atomic_json(a.out / "results.json", R | dict(times=times))

    # secondaries (§11)
    S = {}
    if 1 not in skip:
        rc = h.risk.to_numpy()
        S["1_per_class"] = dict(rates={str(int(k)): dict(houses=int((rows & (rc == k)).sum()), events=int(y[rows & (rc == k)].sum()),
                                                         per_1000=float(1000 * y[rows & (rc == k)].sum() / py[rows & (rc == k)].sum()))
                                       for k in range(5) if (rows & (rc == k)).any()},
                                trend_per_class=v_analysis(h, rows, y, py, np.nan_to_num(rc), chosen, seed)[chosen])
    if 2 not in skip:
        hz = h.hazard.notna().to_numpy()
        xh = h.hazard_flag.to_numpy()
        Fh = follow(W.t_ep, W.t_dem, W.t_event, C.START, C.END, hz)
        hc = h.hazard.to_numpy()
        S["2_hazard"] = dict(V=v_analysis(h, Fh["at"], Fh["y"], Fh["py"], xh, chosen, seed),
                             numbers=headline_numbers(Fh["y"], Fh["py"], xh, Fh["at"]),
                             rates={str(int(k)): float(1000 * Fh["y"][Fh["at"] & (hc == k)].sum() / Fh["py"][Fh["at"] & (hc == k)].sum())
                                    for k in range(4) if (Fh["at"] & (hc == k)).any()},
                             overlap_in_cohort=pd.crosstab(x[rows], np.nan_to_num(xh)[rows]).to_dict(),
                             U=u_analysis(h, Fh["at"] & comp, Fh["y"], xh, chosen, seed, 0, a.jobs, Fh["py"]))
    if 3 not in skip:
        vlm = vlm_at_houses(h)
        sub = -vlm  # subsidence positive, mm/yr
        dom = np.isfinite(vlm)
        Fv = follow(W.t_ep, W.t_dem, W.t_event, C.START, C.END, dom)
        low = dom & (vlm <= np.nanpercentile(vlm, 10))
        S["3_vlm"] = dict(houses_with_vlm=int(dom.sum()), V_per_mm_yr=v_analysis(h, Fv["at"], Fv["y"], Fv["py"], np.nan_to_num(sub), chosen, seed),
                          U=u_analysis(h, Fv["at"] & comp, Fv["y"], np.nan_to_num(sub), chosen, seed, 0, a.jobs, Fv["py"]),
                          lowest_decile_overlap=dict(with_risk_flag=int((low & (x == 1)).sum()), with_hazard_flag=int((low & (h.hazard_flag.to_numpy() == 1)).sum()), lowest_decile=int(low.sum())))
    if 4 not in skip:
        Fa = follow(W.t_ep, W.t_dem, W.t_event, C.START, C.END, np.ones(len(h), bool))
        S["4_map_user"] = dict(V=v_analysis(h, Fa["at"], Fa["y"], Fa["py"], x, chosen, seed), numbers=headline_numbers(Fa["y"], Fa["py"], x, Fa["at"]))
    if 5 not in skip:
        S["5_age"] = {lab: v_analysis(h, rows & (strata == k), y, py, x, chosen, seed)[chosen] for k, (_, _, lab) in enumerate(AGE_STRATA)}
        S["5_age"]["adjusted_for_age_only"] = v_analysis(h, rows, y, py, x, chosen, seed, cols=["building_age"])[chosen]
    if 6 not in skip:
        ev_blocks = pd.Series(y[rows]).groupby(h.b2.to_numpy()[rows]).sum()
        keep = rows & h.b2.isin(ev_blocks[ev_blocks > 0].index).to_numpy()
        fe = pd.get_dummies(h.b2[keep], drop_first=True).to_numpy(float)
        S["6_block_fixed_effects"] = v_analysis(h, keep, y, py, x, chosen, seed, extra=fe)
        S["6_block_fixed_effects"]["blocks_without_events_dropped"] = int(len(ev_blocks) - (ev_blocks > 0).sum())
    if 7 not in skip:
        near, info = new_construction_near(h)
        S["7_construction"] = dict(info, V=v_analysis(h, rows & ~near, y, py, x, chosen, seed), numbers=headline_numbers(y, py, x, rows & ~near))
    if 8 not in skip:
        Fr = follow(W.t_rep, W.t_dem, W.t_revent, C.START, C.END, mapped)
        S["8_remodel"] = dict(V=v_analysis(h, Fr["at"], Fr["y"], Fr["py"], x, chosen, seed), numbers=headline_numbers(Fr["y"], Fr["py"], x, Fr["at"]),
                              U=u_analysis(h, Fr["at"] & comp, Fr["y"], x, chosen, seed, 0, a.jobs, Fr["py"]))
    if 9 not in skip:
        S["9_by_year"] = {}
        st = np.datetime64(C.START, "ns")
        for Y in (2022, 2023, 2024, 2025):
            y0, y1 = np.datetime64(f"{Y}-01-01", "ns"), np.datetime64(f"{Y}-12-31" if Y < 2025 else "2025-11-30", "ns")
            e = F["exit"]
            days = np.clip((np.minimum(e, y1) - y0) / np.timedelta64(1, "D") + 1, 0, None)
            days = np.where(e < y0, 0, days)
            evY = (y == 1) & (e >= y0) & (e <= y1)
            rY = rows & (days > 0)
            S["9_by_year"][str(Y)] = v_analysis(h, rY, evY.astype(float), days / 365.25, x, chosen, seed)[chosen] | dict(events=int(evY[rY].sum()))
        del st
    if 10 not in skip:
        Fo = follow(W.t_ep, W.t_dem, W.t_event, "2018-08-01", "2021-12-31", mapped)
        Fp = follow(W.t_ep, W.t_dem, W.t_event, "2018-08-01", C.END, mapped)
        at0 = Fo["at"]
        ep_in = at0 & W.t_ep.between("2018-08-01", "2021-12-31").to_numpy()
        S["10_overlapping"] = dict(label="retrospective: the InSAR period overlaps the outcomes",
                                   period_2018_2021=v_analysis(h, at0, Fo["y"], Fo["py"], x, chosen, seed),
                                   pooled_2018_2025=v_analysis(h, Fp["at"], Fp["y"], Fp["py"], x, chosen, seed),
                                   depletion={name: dict(at_risk_2018_07_31=int((at0 & (x == f)).sum()), first_episode_2018_08_to_2021_12=int((ep_in & (x == f)).sum()),
                                                         share=float((ep_in & (x == f)).sum() / max(1, (at0 & (x == f)).sum())))
                                              for f, name in ((1, "flagged"), (0, "other"))})
    if 11 not in skip:
        edge = near_flag_edge(h)
        S["11_cell_edges"] = dict(houses_excluded_in_cohort=int((rows & edge).sum()), V=v_analysis(h, rows & ~edge, y, py, x, chosen, seed))
    if 12 not in skip:
        S["12_demolition"] = dict(V=v_analysis(h, rows, F["demolished"], py, x, chosen, seed), numbers=headline_numbers(F["demolished"], py, x, rows))
    S["13_inference_not_chosen"] = dict(V={m: V[m] for m in others}, U_adjusted={m: R["U"]["adjusted"][m] for m in others})
    times["end"] = time.strftime("%Y-%m-%d %H:%M:%S")
    R.update(secondaries=S, times=times)
    atomic_json(a.out / "results.json", R)
    print(label, "done", json.dumps(times), flush=True)


if __name__ == "__main__":
    main()
