"""HAZARD_TX analysis (HAZARD_TX_PLAN.md §5-§10): cohort, primary (pooled adjusted IRR of the hazard flag beyond the
flexible Baseline 1, r4; held-out gain T), the §8 decision, and secondaries 1-17 (14 removed).

Modes:
  synthetic  pre-freeze code check. NO permit or event file is read. First episodes, events, demolitions and
             construction exits are drawn for the real houses: events of the primary rows from the planted generator
             (planted_ht.draw, cell 9: IRR 1.5 with the Austin generating model and a 3 km field), other houses at
             their city's rate; look-back episodes, demolitions and construction exits at fixed shares (seed 2071).
             Labelled SYNTHETIC in every output.
  decoy      after the events are built (post-freeze): every real table is kept but given to random houses of the
             same city (seed 2071). Labelled DECOY.
  real       refused until the frozen plan exists and its SHA-256 equals the one written beside it at freezing
             (freeze/HAZARD_TX_PLAN_frozen.sha256), so this file is not edited at freezing.

Inference (plan §7): the chosen inference is read from the flexible planted summary (r4). The primary's estimate,
p and intervals come from oa_core.infer on the full pooled design (the frozen Ohenhen-Austin code); every model is
also fitted by hx_infer.BlockModel (the same values by the per-city structure, faster), which is used for the
secondaries, and the two are compared on the primary (`primary_check`).
Person-time and follow-up: the frozen Ohenhen-Austin follow() (run_analysis.py, hash asserted).

Usage: python -I run_ht.py synthetic|decoy|real --out DIR [--events DIR] [--jobs N] [--boot 2000] [--only a,b]
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ht_core as H  # noqa: E402
import hx_infer as X  # noqa: E402

C = H.C
STUDY = H.STUDY
# the private data root: the PC's Alex_private, or (server) the folder in HT_PRIVATE with the same layout
PRIV = Path(os.environ.get("HT_PRIVATE", str(H.PRIV)))
if PRIV != H.PRIV:
    for _c in H.CITIES:
        H.CITIES[_c] = {k: PRIV / Path(v).relative_to(H.PRIV) for k, v in H.CITIES[_c].items()}
FROZEN_PLAN = STUDY / "freeze/HAZARD_TX_PLAN_frozen.md"
FROZEN_HASH_FILE = STUDY / "freeze/HAZARD_TX_PLAN_frozen.sha256"  # written once at freezing (this file is not edited)
CITY_ORDER = ["dallas", "sanantonio"]
START, END = H.START, H.END
DAY = pd.Timedelta(days=1)
SEED = [H.SEED_WILD, 0]
DECOY_SEED = 2071
FLEX = STUDY / "step0/planted_flex_20261122"
PINNED = {  # every input the analysis reads besides the step-0 city tables (hashed by ht_core.input_hashes)
    "flex_design.json": (FLEX / "flex_design.json", "2ae6d676cf01866ae5bacf47c42e765be1ddf0962505b63d3e02a277c8a8a303"),
    "planted_summary.json": (FLEX / "planted_summary.json", "dc5d22e3c2968bdeb12273a0802831a50222c1cae8a48a1ff134449e6a71cc03"),
    "planted_flex.py": (HERE / "planted_flex.py", "a07981ce121971da23db25d9f288b512751769bdc324374a21b5e705b4df1de2"),
    "oa run_analysis.py": (H.OA / "run_analysis.py", "e96c46a043c7bed757cf87ee33c8b5731f0f0b1dc63f6a4ccd21de9261d37631"),
    "oa results.json": (STUDY.parent / "ohenhen_austin/real_20261118/results.json",
                        "57b1d1105a282d40751ced7037fe979eed36f10a3ebca3b9f528ac7f5cd74437"),
    "dallas_VLM.csv": (PRIV / "ohenhen2025_tx_vlm_20261122/dallas_VLM.csv",
                       "064709f8dbbc6c2510ef861096600759d74fb1d34142e1d5529fa302c9d18ab9"),
    "sanAntonio_VLM.csv": (PRIV / "ohenhen2025_tx_vlm_20261122/sanAntonio_VLM.csv",
                           "3047bebe9dc100e4cca1c2f9d8e768bca337cca22c6c69428c66480da166005a"),
    "beta_dallas.tif": (PRIV / "ohenhen2025_tx_20261118/beta_dallas.tif",
                        "b9b1c8c887df6244c8b891908a5d213175bd293f4e4371f80cc65c53a9899ddc"),
    "beta_sanAntonio.tif": (PRIV / "ohenhen2025_tx_20261118/beta_sanAntonio.tif",
                            "263c1a822c8f71ca9b666f62bdcfa1da1f2d67039e96eaee53ed19b1ae3ad7b1"),
}
MAP_NAME = {"dallas": "dallas", "sanantonio": "sanAntonio"}
HAZARD_CLASSES = (2, 3)
AGE_STRATA = [(None, 1949, "built to 1949"), (1950, 1979, "built 1950-1979"), (1980, 2019, "built 1980-2019")]


def pinned_ok(name):
    p, s = PINNED[name]
    assert H.sha256(p) == s, f"{name} changed"
    return p


def assert_frozen():
    ok = FROZEN_PLAN.exists() and FROZEN_HASH_FILE.exists()
    assert ok and H.sha256(FROZEN_PLAN) == FROZEN_HASH_FILE.read_text().split()[0], \
        "real outcomes are refused until the plan is frozen (freeze/HAZARD_TX_PLAN_frozen.md and .sha256)"


pinned_ok("oa run_analysis.py")
pinned_ok("planted_flex.py")
sys.path.insert(0, str(H.OA))
import run_analysis as OR  # noqa: E402  (frozen Ohenhen-Austin: follow())
import planted_flex as PF  # noqa: E402  (rcs, CONT, RANK_TOL as in the flexible planted check)
import planted_ht as P  # noqa: E402

follow = OR.follow
FD = json.loads(pinned_ok("flex_design.json").read_text())


def atomic_json(path, obj):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)) + "\n")
    tmp.replace(path)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- houses and outcome world
def load_houses():
    from pyproj import Transformer
    h = pd.concat([H.load_city(c) for c in CITY_ORDER], ignore_index=True)
    h["lon"], h["lat"] = Transformer.from_crs(32614, 4326, always_xy=True).transform(h.x.to_numpy(), h.y.to_numpy())
    h["risk_flag_x"] = (h.risk_class >= 3).astype(float)
    return h


def world_from_tables(hids, first, ev, dem):
    W = pd.DataFrame(dict(hid=np.asarray(hids, dtype=object)))
    for col, t, src in (("t_ep", first, "t_first"), ("t_dem", dem, "t_demolition"), ("t_event", ev, "t_first")):
        assert t.hid.is_unique
        j = W[["hid"]].merge(pd.DataFrame({"hid": t.hid.astype(object).to_numpy(), col: t[src].astype("datetime64[ns]").to_numpy()}),
                             on="hid", how="left", validate="one_to_one")
        W[col] = j[col].astype("datetime64[ns]").to_numpy()
    known = set(W.hid)
    for t in (first, ev, dem):
        assert t.hid.isin(known).all(), "a table names a house outside the population (id format?)"
    has = W.t_event.notna()
    assert (W.t_event[has] == W.t_ep[has]).all(), "event is not its house's first matched episode"
    return W


def read_tables(folder):
    f = Path(folder)
    t = dict(first=pd.read_parquet(f / "first_episodes.parquet", columns=["hid", "t_first", "status"]),
             ev=pd.read_parquet(f / "events.parquet"), dem=pd.read_parquet(f / "demolition.parquet"))
    if (f / "construction_2022_2025.parquet").exists():
        t["con"] = pd.read_parquet(f / "construction_2022_2025.parquet")
    return t


def synthetic_tables(h):
    """Pre-freeze code check: tables drawn for the real houses; no permit is read (see module docstring)."""
    inputs = H.STUDY / "step0/planted_pooled_20261122"
    K = P.ctx(inputs)
    rng = np.random.default_rng(DECOY_SEED)
    y_pl = P.draw(9, 0, inputs)
    out = {}
    span = (END - START).days + 1
    for k, c in enumerate(CITY_ORDER):
        assert K["names"][k] == c
        hc = h[h.city == c]
        prim = (hc.mapped & hc.complete_b1).to_numpy()
        s = K["city"] == k
        assert prim.sum() == s.sum() and np.allclose(hc.x_km.to_numpy()[prim], K["x_km"][s]), "planted rows differ"
        ev_house = np.zeros(len(hc), bool)
        ev_house[np.flatnonzero(prim)] = y_pl[s] == 1
        rate = y_pl[s].mean()
        ev_house[~prim] = rng.random((~prim).sum()) < rate
        hid = hc.hid.to_numpy()
        t_ev = START + pd.to_timedelta(rng.integers(0, span, len(hc)), unit="D")
        lb = ~ev_house & (rng.random(len(hc)) < 0.02)
        t_lb = pd.Timestamp("2019-01-01") + pd.to_timedelta(rng.integers(0, (START - pd.Timestamp("2019-01-01")).days, len(hc)), unit="D")
        first = pd.concat([pd.DataFrame(dict(hid=hid[ev_house], t_first=t_ev[ev_house], status="event")),
                           pd.DataFrame(dict(hid=hid[lb], t_first=t_lb[lb], status="first episode before the study period"))])
        excl = first.status.eq("event") & (rng.random(len(first)) < 0.03)
        first.loc[excl, "status"] = "excluded: construction permit in the 3 years before"
        ev = first.loc[first.status.eq("event"), ["hid", "t_first"]]
        dm = rng.random(len(hc)) < 0.003
        t_dm = pd.Timestamp("2019-01-01") + pd.to_timedelta(rng.integers(0, (END - pd.Timestamp("2019-01-01")).days, len(hc)), unit="D")
        dem = pd.DataFrame(dict(hid=hid[dm], t_demolition=t_dm[dm]))
        out[c] = dict(first=first.reset_index(drop=True), ev=ev.reset_index(drop=True), dem=dem)
        if c == "sanantonio":
            out[c]["con"] = pd.DataFrame(dict(hid=hid[rng.random(len(hc)) < 0.01]))
        if c == "dallas":  # secondary 17: some extra events under the broader outcome
            add = ~ev_house & ~lb & (rng.random(len(hc)) < 0.004)
            fb = pd.concat([first, pd.DataFrame(dict(hid=hid[add], t_first=t_ev[add], status="event"))], ignore_index=True)
            out["dallas_broad"] = dict(first=fb, ev=fb.loc[fb.status.eq("event"), ["hid", "t_first"]].reset_index(drop=True), dem=dem)
    return out


def decoy_tables(h, real):
    """Real tables, each given to random houses of the same city (first episodes and events keep their pairing)."""
    rng = np.random.default_rng(DECOY_SEED)
    out = {}
    for name, t in real.items():
        c = name.replace("_broad", "")
        houses = h.hid[h.city == c].to_numpy()

        def remap(*tables):
            m = dict(zip(tables[0].hid, rng.choice(houses, len(tables[0]), replace=False)))
            return [tt.assign(hid=tt.hid.map(m)) for tt in tables]
        first, ev = remap(t["first"], t["ev"])
        (dem,) = remap(t["dem"])
        out[name] = dict(first=first, ev=ev, dem=dem)
        if "con" in t:
            (out[name]["con"],) = remap(t["con"])
    return out


def world(h, tables, dallas_key="dallas"):
    first = pd.concat([tables[dallas_key]["first"], tables["sanantonio"]["first"]], ignore_index=True)
    ev = pd.concat([tables[dallas_key]["ev"], tables["sanantonio"]["ev"]], ignore_index=True)
    dem = pd.concat([tables[dallas_key]["dem"], tables["sanantonio"]["dem"]], ignore_index=True)
    for t in (first, ev, dem):
        assert t.hid.is_unique and t.hid.isin(set(h.hid)).all()
    return world_from_tables(h.hid, first, ev, dem)


# ---------------------------------------------------------------- designs
def spline_columns(frame, city, features=True, surface=True):
    """The flexible Baseline 1 columns of one city with the knots FIXED in flex_design.json (plan §7)."""
    kn, own = FD["knots"][city], H.B1_BY_CITY[city]
    cols = []
    if features:
        for k in PF.CONT:
            if k in own:
                cols.append(PF.rcs(frame[k].to_numpy(float), kn[k]))
        if "foundation_slab" in own:
            cols.append(frame[["foundation_slab"]].to_numpy(float))
    if surface:
        bx, by = PF.rcs(frame.x_km.to_numpy(float), kn["x_km"]), PF.rcs(frame.y_km.to_numpy(float), kn["y_km"])
        cols += [bx, by, (bx[:, :, None] * by[:, None, :]).reshape(len(frame), -1)]
    return np.hstack(cols)


def orthonormal(F):
    """Standardise, then orthonormalise (SVD; directions below RANK_TOL of the largest dropped), scaled to mean
    square 1, as planted_flex.kctx."""
    mu, sd = F.mean(0), F.std(0)
    sd[sd == 0] = 1.0
    Fs = (F - mu) / sd
    U, S, _ = np.linalg.svd(Fs, full_matrices=False)
    keep = S > PF.RANK_TOL * S[0]
    return U[:, keep] * np.sqrt(len(F))


def linear_columns(frame, city):
    Z = frame[H.B1_BY_CITY[city]].to_numpy(float)
    sd = Z.std(0)
    sd[sd == 0] = 1.0
    return (Z - Z.mean(0)) / sd


def columns(frame, city, design):
    if design == "flex":
        return orthonormal(spline_columns(frame, city))
    if design == "linear":
        return linear_columns(frame, city)
    if design == "features":  # secondary 6: feature splines without the surface
        return orthonormal(spline_columns(frame, city, surface=False))
    raise ValueError(design)


# ---------------------------------------------------------------- one model
G = {}  # the run's context (filled in main; read by forked workers)


def model(sel, y, py, x, design="flex", fe=False):
    """BlockModel on rows `sel` (bool over houses): per city an intercept + design columns (or fixed effects of the
    2 km blocks holding events, with the feature splines). Returns (model, per-city columns, sub-row index)."""
    h = G["h"]
    sub = np.flatnonzero(sel)
    city = h.city.to_numpy()[sub]
    if fe:
        hold = pd.Series(y[sub]).groupby(h.b2.to_numpy()[sub]).transform("sum").to_numpy() > 0
        sub, city = sub[hold], city[hold]
    blocks, cols = [], {}
    for c in CITY_ORDER:
        r = np.flatnonzero(city == c)
        if not len(r):
            continue
        frame = h.iloc[sub[r]]
        if design == "none":
            Z, F, fe_c = np.ones((len(r), 1)), None, None
        elif fe:
            F = columns(frame, c, "features")
            Z, fe_c = F, np.unique(frame.b2.to_numpy(), return_inverse=True)[1]
        else:
            F = columns(frame, c, design)
            Z, fe_c = np.c_[np.ones(len(r)), F], None
        blocks.append((r, Z, fe_c))
        cols[c] = (r, F)
    groups = {k: h[k].to_numpy()[sub] for k in ("b2", "b6", "b12")}
    M = X.BlockModel(blocks, x[sub], y[sub], np.log(py[sub]), groups)
    return M, cols, sub


def describe(sub, y, py, x):
    xs = x[sub]
    d = dict(rows=int(len(sub)), events=int(y[sub].sum()), person_years=float(py[sub].sum()))
    if np.isin(xs, (0, 1)).all():  # flag counts only for a 0/1 predictor (secondary 5 is continuous)
        d |= dict(flagged_rows=int((xs == 1).sum()), flagged_events=int(y[sub][xs == 1].sum()))
    return d


def fit(sel, y, py, x, design="flex", methods=None, interval=True, fe=False, T=False, extra=False):
    M, cols, sub = model(sel, y, py, x, design, fe)
    out = describe(sub, y, py, x) | dict(design=design + (" + 2 km block fixed effects" if fe else ""))
    for m in (methods or [G["chosen"]]):
        out[m] = M.infer(m, SEED, interval=interval)
    if T:
        out |= t_by_city(cols, sub, y, x, extra=extra)
    return out


def t_by_city(cols, sub, y, x, extra=False):
    """T per city on its own folds (2 km blocks, label = event), summed (plan §7). extra: the 'also reported'
    measures from the seed-42 assignment (ΔPR AUC, ΔROC AUC, ΔBrier, calibration of M1, deciles)."""
    h = G["h"]
    out = dict(T_by_city={}, T=0.0)
    for c, (r, F) in cols.items():
        yy, xx = y[sub[r]].astype(int), x[sub[r]]
        folds = H.fold_assignments(h.b2.to_numpy()[sub[r]], yy)
        T, dl = C.t_statistic(F, xx, yy, folds)
        out["T_by_city"][c] = dict(T=T, dl_by_assignment=dl)
        out["T"] += T
        if extra:
            out["T_by_city"][c]["also_reported"] = also_reported(F, xx, yy, folds[0])
    return out


def also_reported(F, x, y, fold):
    import statsmodels.api as sm
    from sklearn.metrics import average_precision_score, roc_auc_score
    s0, s1 = C.N.oof(F, y, fold, C.N.LR), C.N.oof(np.c_[F, x], y, fold, C.N.LR)
    p = np.clip(s1, 1e-15, 1 - 1e-15)
    lg = np.log(p / (1 - p))
    slope = sm.GLM(y, sm.add_constant(lg), family=sm.families.Binomial()).fit().params[1]
    inter = sm.GLM(y, np.ones((len(y), 1)), family=sm.families.Binomial(), offset=lg).fit().params[0]
    dec = pd.qcut(s1, 10, labels=False, duplicates="drop")
    return dict(d_pr_auc=float(average_precision_score(y, s1) - average_precision_score(y, s0)),
                d_roc_auc=float(roc_auc_score(y, s1) - roc_auc_score(y, s0)),
                d_brier=float(np.mean((s1 - y) ** 2) - np.mean((s0 - y) ** 2)),
                calibration_M1=dict(intercept=float(inter), slope=float(slope)),
                deciles_M1=[dict(decile=int(k), houses=int((dec == k).sum()), observed=float(y[dec == k].mean()),
                                 predicted=float(s1[dec == k].mean())) for k in np.unique(dec)])


def numbers(sel, y, py, x):
    out = {"pooled": C.unadjusted(y[sel], py[sel], x[sel] == 1)}
    for c in CITY_ORDER:
        s = sel & (G["h"].city.to_numpy() == c)
        out[c] = C.unadjusted(y[s], py[s], x[s] == 1)
    return out


def decision(r, T):
    """§8 readings; the 90% interval matches the one-sided 0.05 test."""
    rej = bool(r["p_one_sided"] < 0.05 and r["log_irr"] > 0)
    hi = np.inf if r["hi90"] is None else r["hi90"]
    if rej and T > 0:
        return rej, ("Added information demonstrated, enrichment of δ or more not excluded" if hi >= 1.5
                     else "Added information demonstrated, enrichment below δ")
    if rej:
        return rej, "Not demonstrated: association beyond the baseline without a held-out gain"
    if hi < 1:
        return rej, "Not demonstrated, opposite"
    if hi < 1.5:
        return rej, "Not demonstrated, useful enrichment excluded"
    return rej, "Not demonstrated, inconclusive"


# ---------------------------------------------------------------- inputs of secondaries 5 and 10
def vlm_at_houses(h):
    from pyproj import Transformer
    from scipy.spatial import cKDTree
    out = np.full(len(h), np.nan)
    tr = Transformer.from_crs(4326, 32614, always_xy=True)
    for c in CITY_ORDER:
        v = pd.read_csv(pinned_ok(f"{MAP_NAME[c]}_VLM.csv"))
        vx, vy = tr.transform(v.longitude_deg.to_numpy(), v.latitude_deg.to_numpy())
        s = np.flatnonzero(h.city.to_numpy() == c)
        idx = cKDTree(np.c_[vx, vy]).query_ball_point(np.c_[h.x.to_numpy()[s], h.y.to_numpy()[s]], r=50)
        vals = v.VLM_mmPerYr.to_numpy()
        out[s] = [vals[i].mean() if len(i) else np.nan for i in idx]
    return out


def near_flag_edge(h, metres=30.0):
    """Within `metres` of a map-cell edge whose neighbouring cell has a different flag (Ohenhen-Austin's rule, on the
    hazard layer: classes 2-3)."""
    import rasterio
    near = np.zeros(len(h), bool)
    for c in CITY_ORDER:
        s = np.flatnonzero(h.city.to_numpy() == c)
        with rasterio.open(pinned_ok(f"beta_{MAP_NAME[c]}.tif")) as r:
            a = r.read(1).astype(float)
            a[~np.isfinite(a) | (a < -1e30)] = np.nan
            if r.nodata is not None:
                a[a == r.nodata] = np.nan
            tf = r.transform
        lon, lat = h.lon.to_numpy()[s], h.lat.to_numpy()[s]
        colf, rowf = (lon - tf.c) / tf.a, (lat - tf.f) / tf.e
        rr, cc = np.floor(rowf).astype(int), np.floor(colf).astype(int)
        fr, fc = rowf - rr, colf - cc
        wx, wy = abs(tf.a) * 111_320 * np.cos(np.radians(lat)), abs(tf.e) * 110_574

        def flag_of(r_, c_):
            ok = (r_ >= 0) & (r_ < a.shape[0]) & (c_ >= 0) & (c_ < a.shape[1])
            return np.where(ok, a[np.clip(r_, 0, a.shape[0] - 1), np.clip(c_, 0, a.shape[1] - 1)], np.nan)
        own = np.isin(flag_of(rr, cc), HAZARD_CLASSES)
        nb_near = np.zeros(len(s), bool)
        for dr, dc, dist in ((0, -1, fc * wx), (0, 1, (1 - fc) * wx), (-1, 0, fr * wy), (1, 0, (1 - fr) * wy)):
            nb = flag_of(rr + dr, cc + dc)
            nb_near |= np.isfinite(nb) & (np.isin(nb, HAZARD_CLASSES) != own) & (dist <= metres)
        near[s] = nb_near
    return near


def random_effects(est):
    """DerSimonian-Laird on the log scale; est: {name: (log_irr, se)}."""
    b = np.array([v[0] for v in est.values()])
    se = np.array([v[1] for v in est.values()])
    w = 1 / se ** 2
    fe = np.sum(w * b) / w.sum()
    q = float(np.sum(w * (b - fe) ** 2))
    tau2 = max(0.0, (q - (len(b) - 1)) / (w.sum() - np.sum(w ** 2) / w.sum()))
    wr = 1 / (se ** 2 + tau2)
    m, s = np.sum(wr * b) / wr.sum(), np.sqrt(1 / wr.sum())
    return dict(irr=float(np.exp(m)), lo95=float(np.exp(m - 1.959964 * s)), hi95=float(np.exp(m + 1.959964 * s)),
                tau2=float(tau2), Q=q, label="includes the hypothesis-generating Austin estimate")


def se_from(r):
    return None if r.get("lo95") is None or r.get("hi95") is None else (np.log(r["hi95"]) - np.log(r["lo95"])) / (2 * 1.959964)


# ---------------------------------------------------------------- tasks (each returns a dict; run in forked workers)
def task(name):
    h, F, y, py, x = G["h"], G["F"], G["y"], G["py"], G["x"]
    city = h.city.to_numpy()
    comp, mapped = h.complete_b1.to_numpy(bool), h.mapped.to_numpy(bool)
    A, Pm = F["at"], F["at"] & comp
    ch = G["chosen"]
    if name == "primary_oa":  # the claim: oa_core.infer on the full pooled design
        M, cols, sub = model(Pm, y, py, x)
        Xf = M.full_design()
        fitf = C.fit_flag(Xf, y[sub], np.log(py[sub]))
        return {m: C.infer(Xf, y[sub], np.log(py[sub]), M.groups, m, SEED, interval=(m == ch), fit=fitf) for m in (ch,)} | \
            dict(full_design_columns=int(Xf.shape[1]))
    if name == "primary_block":
        return fit(Pm, y, py, x, methods=list(C.METHODS))
    if name == "primary_T":
        M, cols, sub = model(Pm, y, py, x)
        return t_by_city(cols, sub, y, x, extra=True)
    if name.startswith("tboot_"):
        lo, hi = (int(v) for v in name.split("_")[1:])
        M, cols, sub = model(Pm, y, py, x)
        b2 = h.b2.to_numpy()
        folds = {c: H.fold_assignments(b2[sub[r]], y[sub[r]].astype(int)) for c, (r, _) in cols.items()}
        pos = {c: pd.Series(np.arange(len(r))).groupby(b2[sub[r]]).apply(lambda s: s.to_numpy()) for c, (r, _) in cols.items()}
        out = []
        for i in range(lo, hi):
            rng = np.random.default_rng([H.SEED_BOOT_T, i])
            tot = 0.0
            try:
                for c, (r, Fc) in cols.items():
                    ub = pos[c].index.to_numpy()
                    idx = np.concatenate([pos[c][b] for b in rng.choice(ub, len(ub), replace=True)])
                    tot += C.t_statistic(Fc[idx], x[sub[r]][idx], y[sub[r]][idx].astype(int), folds[c][:, idx])[0]
                out.append(tot)
            except AssertionError:
                out.append(None)
        return out
    if name == "s1_city":
        out = {}
        for c in CITY_ORDER:
            out[c] = fit(Pm & (city == c), y, py, x, methods=[ch, "r3"])
        return out
    if name == "s1_ratio":  # heterogeneity: log(IRR Dallas / IRR San Antonio) by oa_core.infer on the full design
        M, cols, sub = model(Pm, y, py, x)
        Xf = M.full_design()
        Xr = np.c_[Xf, Xf[:, -1] * (city[sub] == "dallas")]
        r = C.infer(Xr, y[sub], np.log(py[sub]), M.groups, ch, SEED, interval=True)
        return dict(ratio_dallas_over_sanantonio=r)
    if name == "s2_V":
        out = dict(pooled=fit(A, y, py, x, design="none", methods=[ch]), numbers=numbers(A, y, py, x))
        for c in CITY_ORDER:
            out[c] = fit(A & (city == c), y, py, x, design="none", methods=[ch])
        yb = h.year_built.to_numpy()
        for lo, hi_, lab in AGE_STRATA:
            s = A & (yb <= hi_) & ((yb >= lo) if lo else True)
            out[lab] = fit(s, y, py, x, design="none", methods=[ch])
        strata = np.select([yb <= 1949, yb <= 1979], [0, 1], 2) + 3 * (city == "sanantonio")
        out["mantel_haenszel_city_x_age"] = C.mantel_haenszel(y[A], py[A], x[A], strata[A])
        return out
    if name == "s3_classes":
        bc = h.beta_class.to_numpy()
        rates = {c: {str(k): dict(houses=int((A & (city == c) & (bc == k)).sum()), events=int(y[A & (city == c) & (bc == k)].sum()),
                                  per_1000=float(1000 * y[A & (city == c) & (bc == k)].sum() / max(py[A & (city == c) & (bc == k)].sum(), 1e-12)))
                     for k in range(4)} for c in CITY_ORDER}
        cls = np.nan_to_num(bc)
        return dict(rates=rates, trend_unadjusted=fit(A, y, py, cls, design="none", methods=[ch]),
                    trend_adjusted=fit(Pm, y, py, cls, methods=[ch]))
    if name == "s4_risk":
        dom = h.risk_class.notna().to_numpy()
        Fr = follow(G["W"].t_ep, G["W"].t_dem, G["W"].t_event, START, END, dom)
        xr = h.risk_flag_x.to_numpy()
        return dict(V=fit(Fr["at"], Fr["y"], Fr["py"], xr, design="none", methods=[ch]),
                    numbers=numbers(Fr["at"], Fr["y"], Fr["py"], xr),
                    U=fit(Fr["at"] & comp, Fr["y"], Fr["py"], xr, methods=[ch], T=True))
    if name == "s5_vlm":
        vlm = vlm_at_houses(h)
        dom = np.isfinite(vlm)
        sub_ = np.nan_to_num(-vlm)  # subsidence positive, mm/yr
        return dict(houses_with_vlm=int((A & dom).sum()),
                    unadjusted=fit(A & dom, y, py, sub_, design="none", methods=[ch]),
                    adjusted=fit(Pm & dom, y, py, sub_, methods=[ch]))
    if name == "s6_block_fe":
        return fit(Pm, y, py, x, fe=True, methods=[ch])
    if name == "s7_foundation":
        slab = h.foundation_slab.to_numpy()
        d = city == "dallas"
        return {"slab": fit(Pm & d & (slab == 1), y, py, x, methods=[ch]),
                "pier and beam": fit(Pm & d & (slab == 0), y, py, x, methods=[ch])}
    if name == "s8_by_year":
        out = {}
        for Y in (2022, 2023, 2024, 2025):
            y0, y1 = np.datetime64(f"{Y}-01-01", "ns"), np.datetime64(f"{Y}-12-31", "ns")
            e = F["exit"]
            days = np.where(e < y0, 0, np.clip((np.minimum(e, y1) - y0) / np.timedelta64(1, "D") + 1, 0, None))
            evY = (y == 1) & (e >= y0) & (e <= y1)
            full = (e == np.datetime64(END, "ns")) & (y == 0) & (F["demolished"] == 0)  # followed to the end: whole day
            days = np.where((e >= y0) & (e <= y1) & ~full, days - 0.5, days)  # follow()'s half-day exit convention
            rY = Pm & (days > 0)
            out[str(Y)] = fit(rY, evY.astype(float), days / 365.25, x, methods=[ch])
        return out
    if name == "s9_map_user":
        Fa = follow(G["W"].t_ep, G["W"].t_dem, G["W"].t_event, START, END, np.ones(len(h), bool))
        return dict(V=fit(Fa["at"], Fa["y"], Fa["py"], x, design="none", methods=[ch]),
                    numbers=numbers(Fa["at"], Fa["y"], Fa["py"], x),
                    adjusted=fit(Fa["at"] & comp, Fa["y"], Fa["py"], x, methods=[ch]))
    if name == "s10_edges":
        edge = near_flag_edge(h)
        return dict(houses_excluded_in_primary_rows=int((Pm & edge).sum()),
                    adjusted=fit(Pm & ~edge, y, py, x, methods=[ch], T=True))
    if name == "s11_demolition":
        return dict(V=fit(A, F["demolished"], py, x, design="none", methods=[ch]), numbers=numbers(A, F["demolished"], py, x))
    if name == "s13_not_chosen":
        return {m: fit(Pm, y, py, x, methods=[m]) for m in C.METHODS if m != ch}
    if name == "s15_current_layer":
        con = set(G["tables"]["sanantonio"]["con"].hid)
        keep = ~h.hid.isin(con).to_numpy()
        return dict(houses_removed_from_primary_rows=int((Pm & ~keep).sum()),
                    adjusted=fit(Pm & keep, y, py, x, methods=[ch], T=True))
    if name == "s16_linear":
        out = dict(pooled=fit(Pm, y, py, x, design="linear", methods=[ch], T=True))
        for c in CITY_ORDER:
            out[c] = fit(Pm & (city == c), y, py, x, design="linear", methods=[ch])
        return out
    if name == "s17_dallas_broad":
        Wb = world(h, G["tables"], dallas_key="dallas_broad")
        Fb = follow(Wb.t_ep, Wb.t_dem, Wb.t_event, START, END, mapped)
        Pb = Fb["at"] & comp
        return dict(pooled=fit(Pb, Fb["y"], Fb["py"], x, methods=[ch], T=True),
                    dallas=fit(Pb & (city == "dallas"), Fb["y"], Fb["py"], x, methods=[ch]))
    raise ValueError(name)


def run_task(name):
    t0 = time.time()
    try:
        return name, task(name), None, time.time() - t0
    except Exception:
        return name, None, traceback.format_exc(), time.time() - t0


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["synthetic", "decoy", "real"])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--events", type=Path, help="decoy/real: folder with dallas/, dallas_broad/, sanantonio/ (build_events.py)")
    ap.add_argument("--jobs", type=int, default=32)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--only", default="", help="synthetic only: comma-separated task names (timing and checks)")
    a = ap.parse_args(argv)
    if a.mode == "real":
        assert_frozen()
        assert not a.only and a.boot == 2000, "the real run is complete"
    if a.mode != "synthetic":
        assert a.events, "--events is required"
    label = {"synthetic": "SYNTHETIC RUN (code check, no permit read; not a result)",
             "decoy": "DECOY RUN (code check, not a result)", "real": "REAL RUN"}[a.mode]
    a.out.mkdir(parents=True, exist_ok=True)
    PS = json.loads(pinned_ok("planted_summary.json").read_text())
    ch = PS["rule"]["chosen_inference"]
    assert ch == "r4" and PS["design"]["baseline"] == "flex", "plan §7: flexible baseline, r4"
    times = {"start": now()}
    R = dict(label=label, mode=a.mode, chosen_inference=ch, sources=H.source_hashes(),
             inputs={c: H.input_hashes(c) for c in CITY_ORDER} | {k: v[1] for k, v in PINNED.items()},
             planted_power_demonstrated=PS["rule"]["power_demonstrated"])
    h = load_houses()
    if a.mode == "synthetic":
        tables = synthetic_tables(h)
    else:
        real = {k: read_tables(a.events / k) for k in ("dallas", "dallas_broad", "sanantonio")}
        R["event_tables_sha256"] = {f"{k}/{f.name}": H.sha256(f) for k in real for f in sorted((a.events / k).glob("*.parquet"))}
        tables = real if a.mode == "real" else decoy_tables(h, real)
    W = world(h, tables)
    F = follow(W.t_ep, W.t_dem, W.t_event, START, END, h.mapped.to_numpy(bool))
    x = h.flag.to_numpy(float)
    G.update(h=h, W=W, F=F, y=F["y"], py=F["py"], x=x, chosen=ch, tables=tables)
    comp, city = h.complete_b1.to_numpy(bool), h.city.to_numpy()
    flow = {}
    for c in CITY_ORDER + ["pooled"]:
        s = np.ones(len(h), bool) if c == "pooled" else city == c
        flow[c] = dict(eligible=int(s.sum()), mapped=int((s & h.mapped).sum()), at_risk=int((s & F["at"]).sum()),
                       primary_rows=int((s & F["at"] & comp).sum()))
        for f, nm in ((1, "flagged"), (0, "other")):
            q = s & F["at"] & comp & (x == f)
            flow[c][nm] = dict(rows=int(q.sum()), events=int(F["y"][q].sum()), person_years=float(F["py"][q].sum()),
                               demolished=int(F["demolished"][q].sum()), first_episode_not_event=int(F["first_episode_not_event"][q].sum()))
    R["flow"] = flow
    print(label, json.dumps(flow), flush=True)
    names = ["primary_oa", "primary_block", "primary_T", "s1_city", "s1_ratio", "s2_V", "s3_classes", "s4_risk", "s5_vlm",
             "s6_block_fe", "s7_foundation", "s8_by_year", "s9_map_user", "s10_edges", "s11_demolition", "s13_not_chosen",
             "s15_current_layer", "s16_linear", "s17_dallas_broad"]
    chunk = 25
    names += [f"tboot_{i}_{min(i + chunk, a.boot)}" for i in range(0, a.boot, chunk)]
    if a.only:
        assert a.mode == "synthetic"
        names = [n for n in names if n in a.only.split(",") or any(n.startswith(p) and p.endswith("_") for p in a.only.split(","))]
    import multiprocessing as mp
    res, errors, secs = {}, {}, {}
    with mp.get_context("fork").Pool(a.jobs) as pool:
        for name, out, err, dt in pool.imap_unordered(run_task, names):
            secs[name] = round(dt, 1)
            if err:
                errors[name] = err
                print("ERROR", name, err, flush=True)
            else:
                res[name] = out
            print(now(), name, f"{dt:.0f}s", "error" if err else "ok", flush=True)
            atomic_json(a.out / "partial.json", dict(done=sorted(res), errors=sorted(errors), seconds=secs))
    times["tasks_end"] = now()
    # assemble
    if "primary_oa" in res and "primary_T" in res:
        r = res["primary_oa"][ch]
        T = res["primary_T"]["T"]
        rej, reading = decision(r, T)
        R["primary"] = dict(rows=describe(np.flatnonzero(F["at"] & comp), F["y"], F["py"], x), estimate=r, T=T,
                            T_by_city=res["primary_T"]["T_by_city"], rejected=rej, demonstrated=bool(rej and T > 0),
                            reading=reading, numbers=numbers(F["at"] & comp, F["y"], F["py"], x))
    if "primary_block" in res and "primary_oa" in res:
        a1, b1 = res["primary_block"][ch], res["primary_oa"][ch]
        R["primary_check"] = dict(block_model=a1, oa_core=b1, equal=bool(
            abs(a1["log_irr"] - b1["log_irr"]) < 1e-8 and all(
                (a1[k] is None and b1[k] is None) or (a1[k] is not None and b1[k] is not None and abs(a1[k] - b1[k]) < 1e-6)
                for k in ("p_one_sided", "lo90", "hi90", "lo95", "hi95"))))
    boots = [v for n in sorted(res) if n.startswith("tboot_") for v in res[n]]
    if boots:
        kept = [v for v in boots if v is not None]
        R["T_bootstrap"] = dict(resamples=len(boots), kept=len(kept),
                                ci95=np.percentile(kept, [2.5, 97.5]).tolist() if kept else None,
                                quantiles={q: float(np.percentile(kept, q)) for q in (5, 25, 50, 75, 95)} if kept else None,
                                share_le_0=float(np.mean(np.asarray(kept) <= 0)) if kept else None, values=boots)
    S = {k: v for k, v in res.items() if k.startswith("s")}
    if "s16_linear" in res:
        A_ = json.loads(pinned_ok("oa results.json").read_text())
        au = A_["secondaries"]["2_hazard"]["U"]["adjusted"][A_["chosen_inference"]]
        est = {"austin (generating)": (np.log(au["irr"]), se_from(au))}
        for c in CITY_ORDER:
            rc = res["s16_linear"][c][ch]
            if se_from(rc) is not None:
                est[c] = (rc["log_irr"], se_from(rc))
        S["s12_three_cities"] = dict(austin=dict(irr=au["irr"], lo95=au["lo95"], hi95=au["hi95"], inference=A_["chosen_inference"],
                                                 baseline="linear Baseline 1 + x/y"),
                                     linear_by_city={c: res["s16_linear"][c][ch] for c in CITY_ORDER},
                                     primary_by_city={c: res["s1_city"][c][ch] for c in CITY_ORDER} if "s1_city" in res else None,
                                     random_effects=random_effects(est) if len(est) > 1 else None)
    R.update(secondaries=S, errors=errors, task_seconds=secs, times=times | {"end": now()})
    atomic_json(a.out / "results.json", R)
    print(label, "done", json.dumps(R.get("primary", {}).get("reading")), json.dumps(R["times"]), "errors:", sorted(errors), flush=True)
    return R


if __name__ == "__main__":
    main()
