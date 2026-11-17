"""Pilot: does InSAR velocity add ranking skill to a fixed urban/coastal baseline? This is a retrospective
association test on 2014-2016 collapses, not a forecast. 250 m cells are primary, 200 m a sensitivity check.
Inputs: data/pilot/target_events.csv (06) and the clipped layers in data/interim/layers (00).
Outputs: data/pilot/*.csv and data/pilot/PILOT_REPORT.md.

Cells: inside the 14 study districts, built-up (>= 1 Google Open Buildings v3 footprint centroid with
confidence >= 0.70) and identified as settled by the historical filter (the cell holds the centre of >= 1 WSF
Evolution 30 m pixel first mapped as settlement in 1985-2015). A cell is positive if a target event's
assigned point falls in it.

Validation: fixed spatial folds. 2 km blocks are dealt into 5 folds (StratifiedGroupKFold, seed 42) once per
resolution on all eligible cells, and every comparison reuses that block -> fold map. Scores are out of fold.
Intervals: 2,000 block-bootstrap resamples of the out-of-fold scores (the models are not refitted)."""
import math
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.transform import xy as pixel_xy
from rasterio.warp import reproject
from shapely import wkt
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data/pilot"
L = ROOT / "data/interim/layers"
RAW = ROOT / "data/raw"
CRS = "EPSG:32636"
RESOLUTIONS = [250, 200]  # primary first
BLOCK_M, N_FOLDS, SEED, N_BOOT, N_DRAWS, TOP_SHARE = 2000, 5, 42, 2000, 20, 0.10
FOLD_SEEDS = range(10)  # robustness check only: other block -> fold assignments
DISTRICTS = ["Al Attarin", "Mina Al-Basal", "Muharam Bik", "Sidi Gabir", "Al Dikhila", "Muntazah", "Al Raml",
             "Kesm than Al Raml", "Al Gumruk", "A L Labban", "Karmuz", "Bab Sharqi", "Al Manshiyya", "Al Amreia"]
BASELINE = ["built_share_2015", "old_share_1975", "height_m", "log_buildings", "elevation_m", "dist_coast_km"]
VELOCITY = {"Shirzaei et al. VLM": "shz_vlm", "Ohenhen et al. 2025 VLM": "nile_vlm"}
LABELS = {  # feature: description (unit), source
    "built_share_2015": ("Built-up share of the cell, 2015 (%)", "GHS-BUILT-S R2023A, 100 m, cell mean"),
    "old_share_1975": ("Share of 2015 built-up surface already built in 1975 (0-1)", "GHS-BUILT-S 1975 / 2015"),
    "height_m": ("Net building height, 2018 (m)", "GHS-BUILT-H ANBH R2023A, cell mean of non-zero pixels"),
    "log_buildings": ("Building count, log(1 + n)", "Google Open Buildings v3, confidence >= 0.70"),
    "elevation_m": ("Ground elevation (m)", "FABDEM v1-2, cell mean"),
    "dist_coast_km": ("Distance from cell centre to the 2021 shoreline (km)", "DSAS shoreline, OSF 98pyu"),
    "shz_vlm": ("Shirzaei et al. VLM, mean of points in the cell (mm/yr)", "VT Figshare 25864435, IGS14"),
    "nile_vlm": ("Ohenhen et al. 2025 VLM at the cell (mm/yr)", "Zenodo 15015923, bilinear from ~900 m"),
    "shz_n": ("Shirzaei et al. points in the cell (count)", "availability, not a velocity"),
}


def md_table(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else str(v) for v in r) + " |")
    return "\n".join(out)


def grid(area, res):
    minx, miny, maxx, maxy = area.bounds
    x0, y0 = math.floor(minx / res) * res, math.ceil(maxy / res) * res
    return from_origin(x0, y0, res, res), (math.ceil((y0 - miny) / res), math.ceil((maxx - x0) / res))


def rowcol(tr, res, x, y):
    return np.floor((tr.f - y) / res).astype(int), np.floor((x - tr.c) / res).astype(int)


def bincount(tr, shape, res, x, y, w=None):
    r, c = rowcol(tr, res, x, y)
    ok = (r >= 0) & (r < shape[0]) & (c >= 0) & (c < shape[1])
    flat = r[ok] * shape[1] + c[ok]
    n = shape[0] * shape[1]
    return np.bincount(flat, weights=None if w is None else w[ok], minlength=n).reshape(shape)


def resample(paths, tr, shape, rs, src_nodata=None):
    dst = np.full(shape, np.nan, "float32")
    for p in paths:
        with rasterio.open(p) as s:
            tmp = np.full(shape, np.nan, "float32")
            nd = s.nodata if src_nodata is None else src_nodata
            reproject(s.read(1).astype("float32"), tmp, src_transform=s.transform, src_crs=s.crs, src_nodata=nd,
                      dst_transform=tr, dst_crs=CRS, dst_nodata=np.nan, resampling=rs)
        dst = np.where(np.isnan(dst), tmp, dst)
    return dst


def load_points():
    b = duckdb.sql("select longitude, latitude from read_csv_auto('" + str(ROOT / "data/interim/google_buildings_v3_alex.csv") +
                   "') where confidence >= 0.70").df()
    bp = gpd.GeoSeries(gpd.points_from_xy(b.longitude, b.latitude), crs=4326).to_crs(CRS)
    with rasterio.open(L / "wsf_evolution_year.tif") as s:
        yr = s.read(1)
        r_, c_ = np.nonzero((yr >= 1985) & (yr <= 2015))
        wx, wy = pixel_xy(s.transform, r_, c_)
        wp = gpd.GeoSeries(gpd.points_from_xy(wx, wy), crs=s.crs).to_crs(CRS)
    shz = pd.read_csv(RAW / "insar_vlm_shirzaei/LLIVS_IGS14_Alexandria.csv", header=None,
                      names=["lon", "lat", "inc", "vlm_cm", "std_cm"]).groupby(["lon", "lat"], as_index=False).vlm_cm.mean()
    sp = gpd.GeoSeries(gpd.points_from_xy(shz.lon, shz.lat), crs=4326).to_crs(CRS)
    return bp, wp, sp, shz.vlm_cm.values * 10  # mm/yr


def build_cells(res, area, pts, events):
    bp, wp, sp, shz_mm = pts
    tr, shape = grid(area, res)
    inside = bp.within(area).values
    nb = bincount(tr, shape, res, bp.x.values[inside], bp.y.values[inside])
    settled = bincount(tr, shape, res, wp.x.values, wp.y.values) > 0
    n_shz = bincount(tr, shape, res, sp.x.values, sp.y.values)
    s_shz = bincount(tr, shape, res, sp.x.values, sp.y.values, shz_mm)
    b15 = resample([L / "ghs_built_s_2015.tif"], tr, shape, Resampling.average)
    b75 = resample([L / "ghs_built_s_1975.tif"], tr, shape, Resampling.average)
    anbh = resample([L / "ghs_built_h_anbh_2018.tif"], tr, shape, Resampling.average, src_nodata=0)
    dem = resample(sorted((RAW / "dem_fabdem").glob("*.tif")), tr, shape, Resampling.average)
    nile = resample([L / "nile_vlm_ohenhen2025.tif"], tr, shape, Resampling.bilinear) * 10  # cm/yr -> mm/yr

    rows, cols = np.nonzero(nb > 0)
    xc, yc = tr.c + (cols + 0.5) * res, tr.f - (rows + 0.5) * res
    shore = gpd.read_file(RAW / "collapse_osf/Figures 4 and 5/2021.shp").to_crs(CRS).union_all()
    cells = pd.DataFrame({"row": rows, "col": cols, "x": xc, "y": yc, "settled": settled[rows, cols],
                          "built_share_2015": b15[rows, cols] / 100.0,
                          "old_share_1975": np.clip(b75[rows, cols] / np.where(b15[rows, cols] > 0, b15[rows, cols], np.nan), 0, 1),
                          "height_m": anbh[rows, cols], "log_buildings": np.log1p(nb[rows, cols]),
                          "elevation_m": dem[rows, cols],
                          "dist_coast_km": shapely.distance(shapely.points(xc, yc), shore) / 1000.0,
                          "shz_n": n_shz[rows, cols],
                          "shz_vlm": np.where(n_shz[rows, cols] > 0, s_shz[rows, cols] / np.maximum(n_shz[rows, cols], 1), np.nan),
                          "nile_vlm": nile[rows, cols]})
    cells["block"] = (np.floor(cells.x / BLOCK_M).astype(int).astype(str) + "_" + np.floor(cells.y / BLOCK_M).astype(int).astype(str))
    er, ec = rowcol(tr, res, events.x_utm36.values, events.y_utm36.values)
    pos = set(zip(er, ec))
    cells["positive"] = [(r, c) in pos for r, c in zip(cells.row, cells.col)]
    info = {"positive_cells": len(pos), "positive_built": int(cells.positive.sum()),
            "positive_eligible": int((cells.positive & cells.settled).sum()),
            "built_cells": len(cells), "eligible_cells": int(cells.settled.sum())}
    return cells[cells.settled].reset_index(drop=True), tr, info


def fold_map(cells, seed=SEED):
    y = cells.positive.values.astype(int)
    fold = np.full(len(cells), -1)
    for k, (_, te) in enumerate(StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed).split(cells, y, cells.block)):
        fold[te] = k
    return dict(zip(cells.block, fold))


def model(kind):
    if kind == "logistic regression":
        return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))
    return RandomForestClassifier(n_estimators=500, min_samples_leaf=5, max_features="sqrt",
                                  class_weight="balanced_subsample", n_jobs=-1, random_state=0)


def oof(X, y, fold, kind):
    s = np.full(len(y), np.nan)
    for k in range(N_FOLDS):
        tr, te = fold != k, fold == k
        if te.any() and y[tr].sum() > 0:
            s[te] = model(kind).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return s


def recall_top(y, s, share=TOP_SHARE):
    k = max(1, int(round(share * len(s))))
    return y[np.argsort(-s)[:k]].sum() / y.sum()


def fold_aucs(y, s, fold):
    return [roc_auc_score(y[fold == k], s[fold == k]) for k in range(N_FOLDS)
            if 0 < y[fold == k].sum() < (fold == k).sum()]


def block_boot(y, sa, sb, blocks, rng):
    ub, inv = np.unique(blocks, return_inverse=True)
    members = [np.flatnonzero(inv == i) for i in range(len(ub))]
    res = []
    for _ in range(N_BOOT):
        idx = np.concatenate([members[i] for i in rng.integers(0, len(ub), len(ub))])
        yy = y[idx]
        if 0 < yy.sum() < len(yy):
            a, b = roc_auc_score(yy, sa[idx]), roc_auc_score(yy, sb[idx])
            pa, pb = average_precision_score(yy, sa[idx]), average_precision_score(yy, sb[idx])
            res.append((a, b, b - a, pb - pa))
    return np.percentile(np.array(res), [2.5, 97.5], axis=0)


def compare(cells, folds, vel, kind, rng, y=None):
    """Baseline vs baseline + velocity on the identical cells where every input exists."""
    c = cells[np.isfinite(cells[BASELINE + [vel]]).all(axis=1)]
    if vel == "shz_vlm":
        c = c[c.shz_n > 0]
    yy = (c.positive.values if y is None else y[c.index.values]).astype(int)
    fold = c.block.map(folds).values
    sa = oof(c[BASELINE].values, yy, fold, kind)
    sb = oof(c[BASELINE + [vel]].values, yy, fold, kind)
    ok = np.isfinite(sa) & np.isfinite(sb)
    yy, sa, sb, fold, blocks = yy[ok], sa[ok], sb[ok], fold[ok], c.block.values[ok]
    out = {"cells": len(yy), "positive cells": int(yy.sum()),
           "ROC AUC, baseline": roc_auc_score(yy, sa), "ROC AUC, + velocity": roc_auc_score(yy, sb),
           "PR AUC, baseline": average_precision_score(yy, sa), "PR AUC, + velocity": average_precision_score(yy, sb),
           "prevalence": yy.mean(),
           f"recall in top {TOP_SHARE:.0%}, baseline": recall_top(yy, sa), f"recall in top {TOP_SHARE:.0%}, + velocity": recall_top(yy, sb)}
    fa, fb = fold_aucs(yy, sa, fold), fold_aucs(yy, sb, fold)
    out["fold ΔAUC"] = ", ".join(f"{b - a:+.3f}" for a, b in zip(fa, fb))
    if rng is not None:
        lo, hi = block_boot(yy, sa, sb, blocks, rng)
        out["ΔROC AUC 95% interval"] = f"{lo[2]:+.3f} to {hi[2]:+.3f}"
        out["ΔPR AUC 95% interval"] = f"{lo[3]:+.3f} to {hi[3]:+.3f}"
    return out


def single_layer(cells, feats):
    rows = []
    y = cells.positive.values
    for f in feats:
        v = cells[f].values.astype(float)
        ok = np.isfinite(v)
        vp, vb = v[ok & y], v[ok & ~y]
        auc = roc_auc_score(y[ok], v[ok]) if len(vp) and len(vb) else np.nan
        rows.append({"Layer": LABELS[f][0], "Source": LABELS[f][1],
                     "Eligible cells with a value (%)": f"{100 * ok.mean():.1f}",
                     "Positive cells with a value": len(vp), "Background cells with a value": len(vb),
                     "Median, positive": f"{np.median(vp):.2f}", "Median, background": f"{np.median(vb):.2f}",
                     "AUC": f"{auc:.2f}", "Direction": "higher in positive cells" if auc > 0.5 else "lower in positive cells"})
    return pd.DataFrame(rows)


def random_point(geom, rng):
    if geom.geom_type == "Point":
        return geom
    parts = [p for p in getattr(geom, "geoms", [geom]) if p.length > 0] if geom.geom_type != "MultiPoint" else list(geom.geoms)
    if geom.geom_type == "MultiPoint":
        return parts[rng.integers(len(parts))]
    w = np.array([p.length for p in parts])
    p = parts[rng.choice(len(parts), p=w / w.sum())]
    return p.interpolate(rng.uniform(0, p.length))


def fmt(d):
    return {k: (f"{v:.3f}" if isinstance(v, float) else v) for k, v in d.items()}


def main():
    ev = pd.read_csv(PILOT / "target_events.csv")
    adm = gpd.read_file(RAW / "admin_geoboundaries/geoBoundaries-EGY-ADM2.geojson").to_crs(CRS)
    area = adm[adm.shapeName.isin(DISTRICTS)].union_all()
    pts = load_points()
    rng = np.random.default_rng(SEED)
    R = {}
    for res in RESOLUTIONS:
        cells, tr, info = build_cells(res, area, pts, ev)
        folds = fold_map(cells)
        cells["fold"] = cells.block.map(folds)
        cells.to_csv(PILOT / f"cells_{res}m.csv", index=False)
        y = cells.positive.values
        cov = pd.DataFrame([{"Cells": name, "Count": int(m.sum()),
                             "With ≥ 1 Shirzaei point (%)": f"{100 * (cells.shz_n[m] > 0).mean():.1f}",
                             "With an Ohenhen value (%)": f"{100 * np.isfinite(cells.nile_vlm[m]).mean():.1f}",
                             "With all baseline inputs (%)": f"{100 * np.isfinite(cells.loc[m, BASELINE]).all(axis=1).mean():.1f}"}
                            for name, m in (("Positive", y), ("Background", ~y), ("All eligible", np.ones(len(y), bool)))])
        sl = single_layer(cells, BASELINE + ["shz_vlm", "nile_vlm", "shz_n"])
        sl.to_csv(PILOT / f"single_layer_{res}m.csv", index=False)

        base_ok = np.isfinite(cells[BASELINE]).all(axis=1).values
        cb = cells[base_ok]
        yb, fb = cb.positive.values.astype(int), cb.block.map(folds).values
        avail = []
        for name, X in (("Has ≥ 1 Shirzaei point", (cb.shz_n.values > 0).astype(float)[:, None]),
                        ("Shirzaei point count, log(1 + n)", np.log1p(cb.shz_n.values)[:, None]),
                        ("Has an Ohenhen value", np.isfinite(cb.nile_vlm.values).astype(float)[:, None]),
                        ("Urban/coastal baseline (for reference)", cb[BASELINE].values)):
            s = oof(X, yb, fb, "logistic regression")
            avail.append({"Predictor(s), all eligible cells with baseline inputs": name, "Cells": len(yb),
                          "Positive cells": int(yb.sum()), "Out-of-fold ROC AUC": f"{roc_auc_score(yb, s):.3f}",
                          "PR AUC": f"{average_precision_score(yb, s):.3f}", "Prevalence": f"{yb.mean():.3f}"})
        avail = pd.DataFrame(avail)
        avail.to_csv(PILOT / f"availability_{res}m.csv", index=False)

        comp = []
        for prod, vel in VELOCITY.items():
            for kind in ("logistic regression", "random forest"):
                comp.append({"Velocity product": prod, "Model": kind, **fmt(compare(cells, folds, vel, kind, rng))})
        comp = pd.DataFrame(comp)
        comp.to_csv(PILOT / f"comparison_{res}m.csv", index=False)
        R[res] = dict(cells=cells, info=info, cov=cov, sl=sl, avail=avail, comp=comp, folds=folds, tr=tr)
        print(res, info)
        print(comp[["Velocity product", "Model", "cells", "positive cells", "ROC AUC, baseline", "ROC AUC, + velocity", "ΔROC AUC 95% interval"]].to_string(index=False))

    # location-assignment sensitivity: 250 m, logistic regression, both products
    res = RESOLUTIONS[0]
    cells, tr = R[res]["cells"], R[res]["tr"]
    geoms = ev.geometry_wkt.map(wkt.loads)
    key = {(r, c): i for i, (r, c) in enumerate(zip(cells.row, cells.col))}
    draws = []
    drng = np.random.default_rng(SEED + 1)
    for d in range(N_DRAWS):
        p = [random_point(g, drng) for g in geoms]
        r, c = rowcol(tr, res, np.array([q.x for q in p]), np.array([q.y for q in p]))
        y = np.zeros(len(cells), bool)
        y[[key[k] for k in zip(r, c) if k in key]] = True
        for prod, vel, kind in (("Shirzaei et al. VLM", "shz_vlm", "logistic regression"), ("Shirzaei et al. VLM", "shz_vlm", "random forest"),
                                ("Ohenhen et al. 2025 VLM", "nile_vlm", "logistic regression")):
            o = compare(cells, R[res]["folds"], vel, kind, None, y=y)
            draws.append({"draw": d, "Velocity product": prod, "Model": kind, "positive cells": o["positive cells"],
                          "base": o["ROC AUC, baseline"], "vel": o["ROC AUC, + velocity"]})
    draws = pd.DataFrame(draws)
    draws["delta"] = draws.vel - draws.base
    draws.to_csv(PILOT / "location_sensitivity_250m.csv", index=False)
    sens = draws.groupby(["Velocity product", "Model"]).agg(
        draws=("draw", "count"), positive_cells=("positive cells", lambda s: f"{s.min()}–{s.max()}"),
        base=("base", lambda s: f"{s.median():.3f} ({s.min():.3f}–{s.max():.3f})"),
        vel=("vel", lambda s: f"{s.median():.3f} ({s.min():.3f}–{s.max():.3f})"),
        delta=("delta", lambda s: f"{s.median():+.3f} ({s.min():+.3f} to {s.max():+.3f})")).reset_index()
    sens.columns = ["Velocity product", "Model", "Draws", "Positive cells", "ROC AUC, baseline: median (range)",
                    "ROC AUC, + velocity: median (range)", "ΔROC AUC: median (range)"]
    print(sens.to_string(index=False))

    # fold-assignment check (250 m, Shirzaei): the same comparison under 10 other block -> fold assignments
    seeds = []
    for sd in FOLD_SEEDS:
        fm = fold_map(cells, seed=sd)
        for kind in ("logistic regression", "random forest"):
            o = compare(cells, fm, "shz_vlm", kind, None)
            seeds.append({"seed": sd, "Model": kind, "base": o["ROC AUC, baseline"], "vel": o["ROC AUC, + velocity"],
                          "pr_base": o["PR AUC, baseline"], "pr_vel": o["PR AUC, + velocity"]})
    seeds = pd.DataFrame(seeds)
    seeds.to_csv(PILOT / "fold_seed_check_250m.csv", index=False)
    rng_ = lambda v: f"{v.median():+.3f} ({v.min():+.3f} to {v.max():+.3f})"
    fsc = pd.DataFrame([{"Model": k, "Fold assignments": len(g), "ΔROC AUC: median (range)": rng_(g.vel - g.base),
                         "ΔPR AUC: median (range)": rng_(g.pr_vel - g.pr_base),
                         "Assignments where velocity raised ROC AUC": f"{int((g.vel > g.base).sum())} of {len(g)}"}
                        for k, g in seeds.groupby("Model")])
    print(fsc.to_string(index=False))
    write_report(R, sens, fsc)


def write_report(R, sens, fsc):
    counts = pd.read_csv(PILOT / "sample_counts.csv")
    dec = pd.read_csv(PILOT / "review_decisions.csv")
    p, s = R[250], R[200]
    c250 = p["comp"].set_index(["Velocity product", "Model"])
    c200 = s["comp"].set_index(["Velocity product", "Model"])
    lr, rf = c250.loc[("Shirzaei et al. VLM", "logistic regression")], c250.loc[("Shirzaei et al. VLM", "random forest")]
    olr, orf = c250.loc[("Ohenhen et al. 2025 VLM", "logistic regression")], c250.loc[("Ohenhen et al. 2025 VLM", "random forest")]
    rf200 = c200.loc[("Shirzaei et al. VLM", "random forest")]
    fs = fsc.set_index("Model")
    loc = sens.set_index(["Velocity product", "Model"])
    top = f"recall in top {TOP_SHARE:.0%}"
    count_auc = p["avail"].set_index(p["avail"].columns[0]).loc["Shirzaei point count, log(1 + n)", "Out-of-fold ROC AUC"]
    result = [
        "## Result",
        "",
        f"- **Linear model: no gain.** Adding Shirzaei VLM to the logistic-regression baseline moves out-of-fold ROC AUC from "
        f"{lr['ROC AUC, baseline']} to {lr['ROC AUC, + velocity']} (95% interval of the change {lr['ΔROC AUC 95% interval']}; {lr['cells']} cells, "
        f"{lr['positive cells']} positive). Under 10 other fold assignments the change is {fs.loc['logistic regression', 'ΔROC AUC: median (range)']}.",
        f"- **Random forest: a small, consistent gain.** ROC AUC {rf['ROC AUC, baseline']} → {rf['ROC AUC, + velocity']} "
        f"(95% interval of the change {rf['ΔROC AUC 95% interval']}), PR AUC {rf['PR AUC, baseline']} → {rf['PR AUC, + velocity']}, {top} "
        f"{rf[top + ', baseline']} → {rf[top + ', + velocity']}. Velocity raised ROC AUC in "
        f"{fs.loc['random forest', 'Assignments where velocity raised ROC AUC']} other fold assignments "
        f"({fs.loc['random forest', 'ΔROC AUC: median (range)']}) and across {N_DRAWS} location draws "
        f"({loc.loc[('Shirzaei et al. VLM', 'random forest'), 'ΔROC AUC: median (range)']}). At 200 m: {rf200['ROC AUC, baseline']} → "
        f"{rf200['ROC AUC, + velocity']} ({rf200['ΔROC AUC 95% interval']}).",
        f"- **Ohenhen VLM (~900 m grid): no gain.** Logistic regression {olr['ROC AUC, baseline']} → {olr['ROC AUC, + velocity']}, "
        f"random forest {orf['ROC AUC, baseline']} → {orf['ROC AUC, + velocity']}.",
        f"- **InSAR coverage is itself a signal.** The Shirzaei point count alone scores {count_auc} out of fold, so velocity is "
        "compared only on cells that have it.",
        "- **What the gain is not:** evidence that deformation preceded the collapses (the Shirzaei period is unknown), or proof "
        "that velocity rather than location drives it (see §9).",
        "",
    ]
    lines = [
        "# Pilot: urban/coastal baseline with and without InSAR velocity",
        "",
        "**Scope:** a retrospective association test on the 2014–2016 inventory. It asks whether velocity improves the ranking of "
        "collapse cells beyond a fixed urban/coastal baseline. It is not a forecast: neither velocity product can be shown to "
        "precede the collapses. 250 m cells are primary; 200 m is a sensitivity check.",
        "**Reproduce:** `.venv/bin/python scripts/06_pilot_sample.py && .venv/bin/python scripts/07_pilot_models.py` (after 00–03).",
        "",
        *result,
        "## 1. Target sample",
        "",
        "Rule: the most severe part is total or partial structural, and the recorded cause is not an external accident (gas, fire, "
        "vehicle, factory) or active demolition/construction work on or next to the building. Every other recorded cause is kept; "
        "the inventory has no blank causes (\"deterioration\" is the workbook's own wording, تقادم وتهالك العقار).",
        "",
        md_table(counts),
        "",
        f"Review decisions for records inside the sample (`review_decisions.csv`): {int((dec.decision == 'keep').sum())} kept, "
        f"{int((dec.decision == 'relocate').sum())} relocated to the junction its article names, {int((dec.decision == 'exclude').sum())} excluded "
        "(a fuzzy-only match, a street 1 km outside its district, and one street placed from a single Overture place). "
        "Records outside this sample were not reviewed.",
        "",
        md_table(pd.DataFrame([{"Cell size": f"{res} m", "Positive cells": R[res]["info"]["positive_cells"],
                                "… built-up": R[res]["info"]["positive_built"],
                                "… built-up and settled (analysed)": R[res]["info"]["positive_eligible"],
                                "Eligible cells": R[res]["info"]["eligible_cells"],
                                "Built-up cells not identified as settled": R[res]["info"]["built_cells"] - R[res]["info"]["eligible_cells"]}
                               for res in RESOLUTIONS])),
        "",
        "## 2. Cells and the historical filter",
        "",
        "- **Built-up:** the cell holds at least one Google Open Buildings v3 footprint centroid with confidence ≥ 0.70, inside the 14 study districts.",
        "- **Settled (historical filter):** the cell also holds the centre of at least one 30 m WSF Evolution pixel (DLR) whose first "
        "settlement year is 1985–2015. Built-up cells without one are *not identified as settled by the historical filter*; that does "
        "not establish they were developed after 2015 (WSF can miss sparse or small settlement). Only eligible cells (built-up and settled) are analysed.",
        "- **Positive:** a target event's assigned point falls in the cell. Several events can share a cell.",
        "",
        "## 3. Deformation products",
        "",
        md_table(pd.DataFrame([
            {"": "Source", "Shirzaei et al.": "[InSAR-Based Coastal Land Subsidence](https://data.lib.vt.edu/articles/dataset/InSAR-Based_Coastal_Land_Subsidence/25864435), VT Figshare, CC0",
             "Ohenhen et al. 2025": "[The Global Threat of Sinking Deltas](https://doi.org/10.5281/zenodo.15015923), Zenodo v1, CC-BY-4.0 (data for Ohenhen et al. 2025, *Nature*)"},
            {"": "File used", "Shirzaei et al.": "`LLIVS_IGS14_Alexandria.csv`", "Ohenhen et al. 2025": "`gridVLM/nile_vlm.tif`"},
            {"": "Form", "Shirzaei et al.": "points: lon, lat, radar incidence angle, VLM, VLM standard deviation",
             "Ohenhen et al. 2025": "raster, EPSG:4326, 0.00833° (~900 m) cells"},
            {"": "Quantity", "Shirzaei et al.": "one mean vertical land motion per point, not a time series",
             "Ohenhen et al. 2025": "one mean vertical land motion per cell, not a time series"},
            {"": "Units", "Shirzaei et al.": "cm/yr (README); converted to mm/yr here",
             "Ohenhen et al. 2025": "not stated in the file or record; values fit cm/yr (92% of Nile pixels < −0.5, and the paper reports 80% of the Nile delta sinking faster than 5 mm/yr); converted to mm/yr here"},
            {"": "Reference frame", "Shirzaei et al.": "IGS14 (README)", "Ohenhen et al. 2025": "not stated in the file or record"},
            {"": "Observation period", "Shirzaei et al.": "not documented; requested from the authors on 2026-09-29",
             "Ohenhen et al. 2025": "Sentinel-1, 2014–2023 (per the paper)"},
            {"": "Use here", "Shirzaei et al.": "mean of the distinct points in a cell (duplicate coordinates averaged first); cells without a point have no value",
             "Ohenhen et al. 2025": "bilinear sample onto the cell grid; cells outside the grid's valid area have no value"},
        ])),
        "",
        "## 4. Coverage for the final target (250 m)",
        "",
        md_table(p["cov"]),
        "",
        "At 200 m: " + "; ".join(f"{r['Cells']} {r['Count']} cells, {r['With ≥ 1 Shirzaei point (%)']}% with a Shirzaei point"
                                 for _, r in s["cov"].iterrows()) + ".",
        "",
        "## 5. Single-layer scores (250 m)",
        "",
        "**Metric:** ROC AUC of the raw layer value = the probability that a random positive cell has a higher value than a random "
        "background cell (ties count half). **Sign:** above 0.5 = higher in positive cells, below 0.5 = lower; 0.5 = no separation, "
        "and 0.24 separates as strongly as 0.76. **Missing data:** a cell without a value is left out of that layer's score only "
        "(no imputation); the counts below are the cells used. Eligible cells only. Descriptive, not a model score.",
        "",
        md_table(p["sl"]),
        "",
        "## 6. Availability-only diagnostic",
        "",
        "Whether a cell merely *has* InSAR data, used as the only predictor under the same spatial folds (logistic regression). "
        "A high score means coverage itself tracks collapse cells, which is why the velocity comparison below uses only cells that "
        "have velocity data.",
        "",
        md_table(p["avail"]),
        "",
        "## 7. Baseline vs baseline + velocity",
        "",
        f"Baseline (fixed before any run): {', '.join(LABELS[f][0] for f in BASELINE)}. Each comparison uses the identical cells "
        "where every baseline input and that velocity exist (for Shirzaei, cells with ≥ 1 point). Out-of-fold scores from 5 fixed "
        f"spatial folds (2 km blocks). Recall in the top {TOP_SHARE:.0%} = share of positive cells among the highest-ranked "
        f"{TOP_SHARE:.0%} of cells. Intervals: {N_BOOT:,} block-bootstrap resamples of the out-of-fold scores, models not refitted.",
        "",
        "**250 m (primary)**",
        "",
        md_table(p["comp"]),
        "",
        "**200 m (sensitivity)**",
        "",
        md_table(s["comp"]),
        "",
        "**Fold-assignment check (250 m, Shirzaei).** The same comparison under 10 other block → fold assignments "
        "(seeds 0–9), to see whether a gain depends on one split:",
        "",
        md_table(fsc),
        "",
        "## 8. Location-assignment sensitivity (250 m)",
        "",
        f"Each event's point was redrawn uniformly along its matched street geometry ({N_DRAWS} draws; intersections and the one "
        "junction stay fixed), the positive cells recomputed, and the same comparison rerun with the same folds.",
        "",
        md_table(sens),
        "",
        "## 9. Limits and next checks",
        "",
        "- **Small sample:** 46–50 positive cells. The intervals resample out-of-fold scores without refitting the models, so they "
        "understate the uncertainty.",
        "- **Velocity may stand in for location.** Velocity varies smoothly across the city, so a random forest can use it as a finer "
        "map of where the old core is, not as deformation. Not tested here. The next check is to add cell coordinates (or a smooth "
        "location term) to the baseline and to compare within the historic core only.",
        "- **Not a precursor test:** the Shirzaei period is unknown, and Ohenhen covers 2014–2023, overlapping and following the events.",
        "- **The baseline marks the dense historic core;** velocity is judged only on what it adds to it.",
        "- **News-derived labels:** background cells may hold unrecorded collapses.",
        "",
    ]
    (PILOT / "PILOT_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
