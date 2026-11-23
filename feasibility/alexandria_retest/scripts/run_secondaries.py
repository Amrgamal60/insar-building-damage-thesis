"""Secondary analyses of ALEX_RETEST_PLAN.md §10 on the real outcomes (plan frozen 2026-11-18, a521c23d…).

Each secondary changes one thing in the primary analysis and uses the primary null (c2) unless stated (§10). The
implementation choices that the frozen text leaves open are fixed in §14 of the working plan before any secondary is
computed. Secondaries 12 and 14 are in real_20261118/primary.json (computed with the primary); 11 (P3) is computed by
scripts/run_p3.py. Here: 1b, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, in the order of §10.

Per analysis: T, its 11 components, the seed-42 and mean changes in PR AUC, beta-hat (logistic only), and p of T and
of both PR AUC changes under the stated null; "detected" = T > 0, p(T) < 0.05 and beta-hat < 0 (descriptive, §10).

Usage: python -I scripts/run_secondaries.py --out secondary_real [--only 2 9] [--jobs 16]
"""
import os

for _n in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_n] = "1"
import argparse  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from joblib import Parallel, delayed  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import retest_core as R  # noqa: E402
import run_primary as RP  # noqa: E402

FREEZE = R.RETEST / "freeze"
PRIMARY = R.RETEST / "real_20261118/primary.json"
N_DRAWS, N_RF, N_LOC = 999, 500, 100
ORDER = ["1b", "2", "3", "4", "5", "6", "7", "8", "9", "10", "13"]
LB = R.ROOT / "data/licsbas"


def check_frozen():
    assert R.sha256(FREEZE / "ALEX_RETEST_PLAN_frozen.md") == RP.FROZEN_SHA256, "frozen plan changed"
    for line in (FREEZE / "MANIFEST.sha256").read_text().splitlines():
        h, name = line.split(maxsplit=1)
        assert R.sha256(FREEZE / name) == h, f"frozen file changed: {name}"
    for k in ("retest_core.py", "planted.py", "planted_spline.py", "run_primary.py"):
        assert R.sha256(HERE / k) == R.sha256(FREEZE / "scripts" / k), f"{k} differs from the frozen copy"
    up = json.loads((FREEZE / "UPSTREAM_HASHES.json").read_text())
    h = R.hashes()
    assert h["sources"] == up["sources"] and h["inputs"] == up["inputs"], "upstream code or inputs changed"


# ---------------------------------------------------------------- generic analysis
def analyse(XB, y, folds, v, null_fields, jobs, kind=R.LR, sign=True):
    y = np.asarray(y, int)
    st = R.Stat(XB, y, folds, kind)
    obs = st.of(v)
    bh = R.beta_hat(XB, y, v) if kind == R.LR else None
    nd = Parallel(n_jobs=jobs, batch_size=8)(delayed(st.of)(s) for s in null_fields)
    T = np.array([d["T"] for d in nd])
    P42 = np.array([d["dpr42"] for d in nd])
    Pm = np.array([d["dpr_mean"] for d in nd])
    p = R.p_upper(obs["T"], T)
    out = dict(cells=int(len(y)), positives=int(y.sum()), T=obs["T"], dl_by_assignment=obs["dl"], dpr42=obs["dpr42"],
               dpr_mean=obs["dpr_mean"], beta_hat=bh, p_T=p, p_dpr42=R.p_upper(obs["dpr42"] - 1e-12, P42),
               p_dpr_mean=R.p_upper(obs["dpr_mean"] - 1e-12, Pm), null_median_T=float(np.median(T)),
               null_q95_T=float(np.percentile(T, 95)), draws=int(len(T)))
    out["detected"] = bool(obs["T"] > 0 and p < 0.05 and (bh is None or not sign or bh["per_sd"] < 0))
    return out, dict(T=T, dpr42=P42, dpr_mean=Pm)


def safe(fn, *args, **kw):
    """An analysis whose fold assignment leaves a training fold without a positive is reported, not computed."""
    try:
        return fn(*args, **kw)
    except AssertionError as e:
        if "no positive" not in str(e):
            raise
        return dict(not_computed=str(e)), {}


class Field(R.PixelField):
    """R.PixelField for another raster, cell column and cell size (secondaries 5, 7, 8); same checks."""

    def __init__(self, f, tif, col, res):
        x, y, v = R.L16.pixels(tif)
        x0 = np.unique(np.round(f.x - (f.col + 0.5) * res, 3))
        y0 = np.unique(np.round(f.y + (f.row + 0.5) * res, 3))
        assert len(x0) == len(y0) == 1
        from rasterio.transform import from_origin
        r, cc = R.P.rowcol(from_origin(x0[0], y0[0], res, res), res, x, y)
        cell = pd.Index(f.row * 100_000 + f.col).get_indexer(r * 100_000 + cc)
        keep = cell >= 0
        self.xy, self.v, self.cell, self.n_cells = np.c_[x[keep], y[keep]], v[keep], cell[keep], len(f)
        self.count = np.bincount(self.cell, minlength=self.n_cells)
        assert (self.count > 0).all(), "every field cell must hold a pixel"
        self.cells = f.reset_index(drop=True)
        assert np.allclose(self.to_cells(self.v[None, :])[0], f[col].to_numpy(float), rtol=0, atol=1e-9)
        lc = pd.read_csv(R.P.PILOT / f"licsar_cells_{res}m.csv")[["row", "col", f"{col}_n"]]
        n_saved = f[["row", "col"]].merge(lc, on=["row", "col"], how="left")[f"{col}_n"].to_numpy(int)
        assert np.array_equal(self.count, n_saved), "pixel counts differ from the cell counts"


def c2_cells(px):
    """999 c2 surrogates on the pixel field px (seed 2043), averaged into its cells; explained variance."""
    S_pix, ks, explained = R.pixel_surrogates("c2", px, N_DRAWS)
    return px.to_cells(S_pix), explained


def grid_origin(c, res):
    from rasterio.transform import from_origin
    x0 = np.unique(np.round(c.x - (c.col + 0.5) * res, 3))
    y0 = np.unique(np.round(c.y + (c.row + 0.5) * res, 3))
    assert len(x0) == len(y0) == 1
    return from_origin(x0[0], y0[0], res, res)


def folds_with_labels(allc, c, all_labels):
    """The original fold rule (07's fold_map, seed 42 then 0-9) on all eligible cells with the given labels."""
    a = allc.copy()
    a["positive"] = np.asarray(all_labels, bool)
    return np.array([c.block.map(R.P.fold_map(a, seed=s)).to_numpy(np.int64) for s in R.FOLD_SEEDS])


def labels_from_points(cells, tr, res, x, y):
    r, cc = R.P.rowcol(tr, res, np.asarray(x, float), np.asarray(y, float))
    hit = set(zip(r.tolist(), cc.tolist()))
    return np.array([(a, b) in hit for a, b in zip(cells.row, cells.col)])


# ---------------------------------------------------------------- secondaries
def s1b(ctx, a):
    """§10.1: the mean-of-11 PR AUC change under the primary null and the original six (the primary run recorded the
    seed-42 change only). Recomputed with the same draws; T must equal the primary run's null T."""
    c, XB, v, y, folds = ctx["c"], ctx["XB"], ctx["v"], ctx["y"], ctx["folds"]
    saved = np.load(R.RETEST / "real_20261118/primary_nulls.npz")
    surr, _ = R.T17.surrogates(v, c[["x", "y"]].to_numpy(float), R.RES, N_DRAWS)
    nperm = RP.N_PERM if N_DRAWS == 999 else N_DRAWS
    sets = {"primary (c2)": ctx["sz"]["c2_cells241"][:N_DRAWS], **{f"original: {k}": s for k, s in surr.items()},
            "original: Free permutation": R.T17.permutations(v, c.block.to_numpy(), "free", nperm),
            "original: Within-block permutation": R.T17.permutations(v, c.block.to_numpy(), "within-block", nperm)}
    out, arrays = {}, {}
    for k, fields in sets.items():
        r, arr = analyse(XB, y, folds, v, fields, a.jobs)
        assert np.allclose(arr["T"], saved[f"{k}|T"][:len(arr["T"])], rtol=0, atol=1e-8), f"{k}: null T differs from the primary run"
        out[k] = {kk: r[kk] for kk in ("p_T", "p_dpr42", "p_dpr_mean", "draws")}
        arrays[k] = arr
    orig = [k for k in out if k.startswith("original: ")]
    out["largest p of the original six"] = {kk: max(out[k][kk] for k in orig) for kk in ("p_T", "p_dpr42", "p_dpr_mean")}
    out["observed"] = dict(dpr42=r["dpr42"], dpr_mean=r["dpr_mean"], T=r["T"])
    return out, arrays


def s2(ctx, a):
    """Smooth location: additive cubic B-spline bases of x and of y (5 quantile knots, degree 3) and x*y added."""
    from sklearn.preprocessing import SplineTransformer
    c = ctx["c"]
    bx = SplineTransformer(n_knots=5, degree=3, knots="quantile").fit_transform(c[["x_km"]])
    by = SplineTransformer(n_knots=5, degree=3, knots="quantile").fit_transform(c[["y_km"]])
    XB2 = np.c_[ctx["XB"], bx, by, (c.x_km * c.y_km).to_numpy(float)]
    r, arr = analyse(XB2, ctx["y"], ctx["folds"], ctx["v"], ctx["sz"]["c2_cells241"][:N_DRAWS], a.jobs)
    r["design_columns"] = int(XB2.shape[1])
    return r, dict(main=arr)


def s3(ctx, a):
    """All 341 core cells with a LiCSAR value; c2 regenerated on their pixel field."""
    f = ctx["f"]
    px = R.PixelField(f)
    nulls, expl = c2_cells(px)
    r, arr = analyse(R.design(f), f.positive.to_numpy(int), R.fold_matrix(ctx["allc"], f), f[R.COL].to_numpy(float),
                     nulls, a.jobs)
    r.update(pixels=int(len(px.v)), c2_explained=expl)
    return r, dict(main=arr)


def s4(ctx, a):
    """Location uncertainty: 100 redraws of each event's point along its street geometry (07's random_point; points
    stay fixed), seed 2044; labels and folds rebuilt on all eligible cells per labeling; statistic = mean T over the
    labelings; each null draw is scored on the same labelings."""
    from shapely import wkt
    c, allc, XB, v = ctx["c"], ctx["allc"], ctx["XB"], ctx["v"]
    ev = pd.read_csv(R.P.PILOT / "target_events.csv")
    geoms = ev.geometry_wkt.map(wkt.loads)
    tr = grid_origin(c, R.RES)
    assert np.array_equal(labels_from_points(c, tr, R.RES, ev.x_utm36, ev.y_utm36), ctx["y"].astype(bool)), \
        "event points do not reproduce the primary labels"
    assert np.array_equal(labels_from_points(allc, tr, R.RES, ev.x_utm36, ev.y_utm36), allc.positive.to_numpy(bool)), \
        "event points do not reproduce the eligible cells' labels"
    rng = np.random.default_rng(R.SEED_LOC)
    labelings = []
    for _ in range(N_LOC):
        p = [R.P.random_point(g, rng) for g in geoms]
        px_, py_ = [q.x for q in p], [q.y for q in p]
        labelings.append((labels_from_points(c, tr, R.RES, px_, py_), labels_from_points(allc, tr, R.RES, px_, py_)))
    fields = np.vstack([v[None, :], ctx["sz"]["c2_cells241"][:N_DRAWS]])

    def one(d):
        yc, ya = labelings[d]
        folds = folds_with_labels(allc, c, ya)
        try:
            st = R.Stat(XB, yc.astype(int), folds)
        except AssertionError:
            return d, None, None, int(yc.sum())
        return d, np.array([st.of(s)["T"] for s in fields]), R.beta_hat(XB, yc.astype(int), v)["per_sd"], int(yc.sum())

    res = Parallel(n_jobs=a.jobs)(delayed(one)(d) for d in range(N_LOC))
    kept = [r for r in res if r[1] is not None]
    M = np.array([r[1] for r in kept])  # (labelings, 1 + draws)
    Tbar = M.mean(axis=0)
    p = R.p_upper(Tbar[0], Tbar[1:])
    bmean = float(np.mean([r[2] for r in kept]))
    pos = [r[3] for r in res]
    out = dict(labelings=N_LOC, kept=len(kept), skipped=[r[0] for r in res if r[1] is None],
               positives_range=[int(min(pos)), int(max(pos))], positives_mean=float(np.mean(pos)),
               T_mean=float(Tbar[0]), T_by_labeling_range=[float(M[:, 0].min()), float(M[:, 0].max())],
               T_by_labeling_share_positive=float(np.mean(M[:, 0] > 0)), beta_hat_mean=bmean, p_T=p,
               null_median_T=float(np.median(Tbar[1:])), null_q95_T=float(np.percentile(Tbar[1:], 95)), draws=int(len(Tbar) - 1))
    out["detected"] = bool(Tbar[0] > 0 and p < 0.05 and bmean < 0)
    return out, dict(T_by_labeling=M)


def other_layer(ctx, a, res, col, tif):
    c, _ = R.T17.test_cells(res, "shirzaei", col, ctx["adm"])
    allc = pd.read_csv(R.P.PILOT / f"cells_{res}m.csv")
    px = Field(c, tif, col, res)
    nulls, expl = c2_cells(px)
    r, arr = analyse(R.design(c), c.positive.to_numpy(int), R.fold_matrix(allc, c), c[col].to_numpy(float), nulls, a.jobs)
    r.update(pixels=int(len(px.v)), c2_explained=expl, layer=col, resolution_m=res)
    return r, dict(main=arr)


def s5(ctx, a):
    """200 m cells (original secondary 2); c2 regenerated on their pixel field."""
    return other_layer(ctx, a, 200, R.COL, R.P1_TIF)


def s6(ctx, a):
    """Random forest (original settings), the first 500 c2 draws; no beta-hat (sign condition not applicable)."""
    r, arr = analyse(ctx["XB"], ctx["y"], ctx["folds"], ctx["v"], ctx["sz"]["c2_cells241"][:N_RF], a.jobs, kind=R.T17.RF)
    return r, dict(main=arr)


def s7(ctx, a):
    """P2, the full period (original secondary 4)."""
    return other_layer(ctx, a, 250, "lic_ud_p2", R.L16.LAYERS["lic_ud_p2"][0])


def s8(ctx, a):
    """Each frame's line of sight, P1 (original secondary 5)."""
    out, arrays = {}, {}
    for col in ("lic_los_065D_p1", "lic_los_131A_p1"):
        out[col], arrays[col] = other_layer(ctx, a, 250, col, R.L16.LAYERS[col][0])
    return out, {k: v["main"] for k, v in arrays.items()}


def s9(ctx, a):
    """Timing: positives = cells whose target events are all in 2014-2015, or cells with a 2016 target event; the
    same background cells; the original folds and the c2 draws restricted to the analysed cells."""
    c = ctx["c"]
    ev = pd.read_csv(R.P.PILOT / "target_events.csv")
    tr = grid_origin(c, R.RES)
    r_, c_ = R.P.rowcol(tr, R.RES, ev.x_utm36.to_numpy(float), ev.y_utm36.to_numpy(float))
    key = pd.Index(c.row * 100_000 + c.col).get_indexer(r_ * 100_000 + c_)
    years = pd.Series(ev.event_date_start.str[:4].astype(int).to_numpy())[key >= 0].groupby(key[key >= 0]).agg(list)
    assert set(years.index) == set(np.flatnonzero(ctx["y"])), "event cells differ from the primary positives"
    early = [i for i, ys in years.items() if max(ys) <= 2015]
    late = [i for i, ys in years.items() if 2016 in ys]
    bg = np.flatnonzero(ctx["y"] == 0)
    out, arrays = {}, {}
    for name, pos in (("all events 2014-2015", early), ("a 2016 event", late)):
        rows = np.sort(np.r_[bg, pos])
        y = np.isin(rows, pos).astype(int)
        out[name], arrays[name] = safe(analyse, ctx["XB"][rows], y, ctx["folds"][:, rows], ctx["v"][rows],
                                       ctx["sz"]["c2_cells241"][:N_DRAWS, rows], a.jobs)
        out[name]["positive_cells"] = int(len(pos))
    out["cells_in_both"] = int(len(set(early) & set(late)))
    return out, arrays


def s10(ctx, a):
    """Radar coverage: (a) valid-pixel count as the only added predictor, under the original plain
    variogram-matching null of the count (§14); (b) the primary analysis with the count added to M0 and M1."""
    c = ctx["c"]
    lc = pd.read_csv(R.P.PILOT / "licsar_cells_250m.csv")[["row", "col", f"{R.COL}_n"]]
    n = c[["row", "col"]].merge(lc, on=["row", "col"], how="left")[f"{R.COL}_n"].to_numpy(float)
    assert np.isfinite(n).all()
    surr, _ = R.T17.surrogates(n, c[["x", "y"]].to_numpy(float), R.RES, N_DRAWS)
    ra, arr_a = analyse(ctx["XB"], ctx["y"], ctx["folds"], n, surr["Variogram-matching"], a.jobs, sign=False)
    ra["null"] = "original plain variogram-matching, on the count"
    rb, arr_b = analyse(np.c_[ctx["XB"], n], ctx["y"], ctx["folds"], ctx["v"], ctx["sz"]["c2_cells241"][:N_DRAWS], a.jobs)
    rb["null"] = "primary (c2)"
    sp = float(pd.Series(n).corr(pd.Series(ctx["v"]), method="spearman"))
    return dict(a_count_only=ra, b_count_in_baseline=rb, count_median_collapse=float(np.median(n[ctx["y"] == 1])),
                count_median_background=float(np.median(n[ctx["y"] == 0])), spearman_count_velocity=sp), \
        dict(a=arr_a, b=arr_b)


def s13(ctx, a):
    """Lesser damage: label = cell with a located partial-element event and no target event (same 241 cells).
    Partial-element events: the target rule with severity partial_element (cause rule unchanged); located as 06 does
    (street level, highest-ranked record); review-queue records without a decision are excluded (06's rule:
    unresolved records never get forced coordinates). Folds rebuilt on all eligible cells with this label."""
    spec = importlib.util.spec_from_file_location("pilot06", R.ROOT / "scripts/06_pilot_sample.py")
    S6 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(S6)
    inv = R.ROOT / "data/inventory"
    ev = pd.read_csv(inv / "events.csv")
    rec = pd.read_csv(inv / "inventory_geocoded.csv").set_index("record_id")
    queue = pd.read_csv(inv / "review_queue.csv").set_index("record_id")
    sel = ev[(ev.severity_class == "partial_element") & ~ev.cause_group.isin(S6.CAUSE_DROP)]
    pts, n_queue_excluded = [], 0
    for e in sel.itertuples():
        cands = []
        for rid in e.record_ids.split(";"):
            if rid not in rec.index or rec.loc_category[rid] not in S6.STREET_LEVEL:
                continue
            d = S6.DECISIONS.get(rid, (None, None))[0]
            if d == "exclude" or (rid in queue.index and d is None):
                n_queue_excluded += rid in queue.index and d is None
                continue
            cands.append((S6.CAT_RANK[rec.loc_category[rid]], rec.x_utm36[rid], rec.y_utm36[rid]))
        if cands:
            pts.append(max(cands, key=lambda t: t[0])[1:])
    x, yv = np.array([p[0] for p in pts]), np.array([p[1] for p in pts])
    c, allc = ctx["c"], ctx["allc"]
    tr = grid_origin(c, R.RES)
    lc = labels_from_points(c, tr, R.RES, x, yv) & (ctx["y"] == 0)
    la = labels_from_points(allc, tr, R.RES, x, yv) & ~allc.positive.to_numpy(bool)
    folds = folds_with_labels(allc, c, la)
    r, arr = safe(analyse, ctx["XB"], lc.astype(int), folds, ctx["v"], ctx["sz"]["c2_cells241"][:N_DRAWS], a.jobs)
    r.update(events_selected=int(len(sel)), events_located=int(len(pts)), queue_records_excluded=int(n_queue_excluded),
             partial_cells_with_target_event=int((labels_from_points(c, tr, R.RES, x, yv) & (ctx["y"] == 1)).sum()))
    return r, dict(main=arr)


FUN = {"1b": s1b, "2": s2, "3": s3, "4": s4, "5": s5, "6": s6, "7": s7, "8": s8, "9": s9, "10": s10, "13": s13}


def main(argv=None):
    global N_DRAWS, N_RF, N_LOC
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only", nargs="+", choices=ORDER)
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--draws", type=int, default=N_DRAWS, help="smoke tests only")
    ap.add_argument("--loc", type=int, default=N_LOC, help="smoke tests only")
    a = ap.parse_args(argv)
    if a.draws != N_DRAWS or a.loc != N_LOC:
        N_DRAWS, N_RF, N_LOC = a.draws, min(N_RF, a.draws), a.loc
        print(f"SMOKE: {N_DRAWS} draws, {N_LOC} labelings", flush=True)
    check_frozen()
    import geopandas as gpd
    c, f, allc = R.load_cells()
    adm = gpd.read_file(R.P.RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(R.P.CRS)
    meta = json.loads((R.RETEST / "step0/planted_inputs.json").read_text())
    assert R.sha256(R.RETEST / "step0/surrogates.npz") == meta["surrogates_sha256"]
    ctx = dict(c=c, f=f, allc=allc, adm=adm, XB=R.design(c), v=c[R.COL].to_numpy(float), y=c.positive.to_numpy(int),
               folds=R.fold_matrix(allc, c), sz=np.load(R.RETEST / "step0/surrogates.npz"))
    assert np.array_equal(ctx["folds"][0], c.fold.to_numpy())
    prim = json.loads(PRIMARY.read_text())
    a.out.mkdir(parents=True, exist_ok=True)
    path = a.out / "secondaries.json"
    rec = json.loads(path.read_text()) if path.exists() else dict(results={}, times={})
    rec.update(plan_sha256=RP.FROZEN_SHA256, primary_sha256=R.sha256(PRIMARY), script_sha256=R.sha256(Path(__file__)),
               **R.hashes())
    rec["results"]["12 (in primary.json)"] = prim["p_values"]["unconditional pixel (a)"]
    rec["results"]["14 (in primary.json)"] = prim["secondary_14"]
    for k in (a.only or ORDER):
        t0 = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{t0} secondary {k} start", flush=True)
        r, arrays = FUN[k](ctx, a)
        rec["results"][k] = r
        rec["times"][k] = dict(start=t0, end=time.strftime("%Y-%m-%d %H:%M:%S"))
        np.savez_compressed(a.out / f"nulls_{k}.npz", **{f"{n}|{s}": v for n, d in arrays.items()
                                                           for s, v in (d.items() if isinstance(d, dict) else [("T", d)])})
        path.write_text(json.dumps(rec, indent=1, default=float) + "\n")
        print(f"{rec['times'][k]['end']} secondary {k} done:", json.dumps(r, default=float)[:600], flush=True)


if __name__ == "__main__":
    main()
