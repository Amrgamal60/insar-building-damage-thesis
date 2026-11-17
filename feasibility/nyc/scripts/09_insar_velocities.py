"""InSAR window velocities (NYC_REPLICATION_PLAN.md §7, §13 step 3), blind to outcomes: no value is compared with events.
For every window (each distinct event date of the 82 events from 2017-07-16, for the 365-day window; those from
2018-07-16 for 730 days; those from 2019-07-16 for 1,095 days) and for the full period (sign check), computes per-pixel
line-of-sight velocities from OPERA DISP-S1 F08622 and averages them over the eligible 250 m and 200 m cells.

Per window [W0, t_e), W0 = t_e - length, with the acquisitions dated W0 <= date < t_e:
1. Layer and masks: `displacement` (m -> mm), `recommended_mask` == 1 and `water_mask` == 1 on each date.
2. Re-referencing: the chain starts at the last reference date R* <= W0; products with reference date >= R* and
   secondary date < t_e are chained with opera-utils' rebase_timeseries (NaN at a reference change propagates).
3. Invalid for the window: masked at a reference change inside the window; or, at any window epoch, a connected-
   component label of 0 or a label other than the main component of the pixel's landmass group (deviation 1 in §14:
   the frozen rule compared with the label at the frame's reference point, which is 0 itself in every granule and lies
   in New Jersey or on Long Island, so almost no NYC pixel would remain). The main component of a group at an epoch is the
   most common non-zero label among the pixels whose centre lies in the group's borough polygons. A pixel takes the
   group of the borough polygon holding its centre, else of the nearest polygon.
4. No vertical projection: velocities stay in line of sight, positive toward the satellite.
5. Construction mask: pixels within 50 m of the lot point (the permit's own coordinates, as in the event audit) of any
   BIS NB/DM/A1 or DOB NOW Full Demolition/Foundation/Earth Work/Support of Excavation permit issued from W0 - 365 days
   to t_e (inclusive) are dropped.
Velocity: least squares d = a + v t + b sin(2 pi t / 365.25) + c cos(2 pi t / 365.25) on the pixel's valid dates
(t in days, v reported in mm/yr); a linear-only fit (secondary 12) on the same dates. A pixel has a value only if
valid on >= 80% of the window's acquisition dates and on >= 1 date in each 91-day quarter from W0 (the last quarter
takes the 1-3 leftover days).
Cell value: mean of the valid pixels whose centres fall in the cell; v_nomask (secondary 13) skips step 5.
Sign check (full period): W0 = 2016-07-16 (the first reference date, an epoch with displacement 0), t_e = the day
after the last acquisition, no construction mask (it is defined per event); 250 m cells crossed by the LaGuardia
runways (OSM) and every eligible 250 m cell.
Outputs (out/insar/): windows.csv, cells_<res>m.csv.gz, coverage.csv, sign_check.csv, layers.txt.
Usage (from feasibility/nyc): ~/miniforge3/envs/opera/bin/python -I scripts/09_insar_velocities.py raw out"""
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import shapely
from opera_utils.disp import rebase_timeseries
from pyproj import Transformer

RAW, OUT = Path(sys.argv[1]), Path(sys.argv[2])
CP2, INS = OUT / "checkpoint2", OUT / "insar"
CRS, RESOLUTIONS = "EPSG:32618", [250, 200]
LENGTHS = {365: "2017-07-16", 730: "2018-07-16", 1095: "2019-07-16"}  # window length (days): first event date used
QUARTER, MIN_SHARE, PERMIT_M, PERMIT_LEAD = 91, 0.8, 50.0, 365
GROUPS = ["Manhattan", "Bronx", "Brooklyn+Queens", "Staten Island"]
LANDMASS = {"Manhattan": "Manhattan", "Bronx": "Bronx", "Brooklyn": "Brooklyn+Queens", "Queens": "Brooklyn+Queens",
            "Staten Island": "Staten Island"}
LAYERS = ["displacement", "recommended_mask", "water_mask", "connected_component_labels"]
TO_UTM = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)


def grid_origin(cells, res):
    return float((cells.x - (cells.col + 0.5) * res).iloc[0]), float((cells.y + (cells.row + 0.5) * res).iloc[0])


def cell_index(x, y, cells, res):
    """Index into `cells` of the cell holding each point, -1 outside."""
    x0, y0 = grid_origin(cells, res)
    r, c = np.floor((y0 - y) / res).astype(np.int64), np.floor((x - x0) / res).astype(np.int64)
    key = pd.Series(np.arange(len(cells)), index=pd.MultiIndex.from_arrays([cells.row.values, cells.col.values]))
    return key.reindex(pd.MultiIndex.from_arrays([r, c])).fillna(-1).to_numpy(dtype=np.int64)


def borough_groups(px, py):
    """Landmass group code (1-4) of each pixel centre: the borough polygon holding it (inside), else the nearest."""
    gj = json.loads((RAW / "boroughs/borough_boundaries.geojson").read_text())
    polys = {}
    for f in gj["features"]:
        g = shapely.transform(shapely.geometry.shape(f["geometry"]), lambda a: np.c_[TO_UTM.transform(a[:, 0], a[:, 1])])
        polys.setdefault(GROUPS.index(LANDMASS[f["properties"]["boroname"]]) + 1, []).append(g)
    polys = {k: shapely.union_all(v) for k, v in polys.items()}
    inside = np.zeros(len(px), np.int8)
    for k, g in polys.items():
        inside[shapely.contains_xy(g, px, py)] = k
    return inside, polys


def nearest_group(px, py, polys):
    pts = shapely.points(px, py)
    d = np.stack([shapely.distance(pts, polys[k]) for k in sorted(polys)])
    return (np.argmin(d, 0) + 1).astype(np.int8)


def permits():
    bis = pd.read_csv(RAW / "permits/bis_nb_dm_a1_2013_2022.csv", dtype=str)
    now = pd.read_csv(RAW / "permits/now_excav_demo_2013_2022.csv", dtype=str)
    p = pd.concat([pd.DataFrame({"date": pd.to_datetime(bis.issuance_date, format="%m/%d/%Y", errors="coerce"),
                                 "lat": pd.to_numeric(bis.gis_latitude, errors="coerce"),
                                 "lon": pd.to_numeric(bis.gis_longitude, errors="coerce")}),
                   pd.DataFrame({"date": pd.to_datetime(now.issued_date.str[:10], format="%Y-%m-%d", errors="coerce"),
                                 "lat": pd.to_numeric(now.latitude, errors="coerce"),
                                 "lon": pd.to_numeric(now.longitude, errors="coerce")})], ignore_index=True)
    n_all = len(p)
    p = p.dropna()
    x, y = TO_UTM.transform(p.lon.values, p.lat.values)
    return p.assign(x=x, y=y).reset_index(drop=True), n_all


def construction_mask(pm, shape, X0, Y0, start, end):
    """Boolean full-grid mask of pixels within 50 m of a permit issued in [start, end]."""
    s = pm[(pm.date >= start) & (pm.date <= end)]
    m = np.zeros(shape, bool)
    r0, c0 = np.rint((Y0 - s.y.values) / 30).astype(int), np.rint((s.x.values - X0) / 30).astype(int)
    for dr in range(-3, 4):
        for dc in range(-3, 4):
            r, c = r0 + dr, c0 + dc
            ok = (r >= 0) & (r < shape[0]) & (c >= 0) & (c < shape[1])
            d = np.hypot(X0 + c * 30.0 - s.x.values, Y0 - r * 30.0 - s.y.values)
            ok &= d <= PERMIT_M
            m[r[ok], c[ok]] = True
    return m, len(s)


def fit(D, valid, t, annual=True):
    """Per-pixel weighted least squares; returns v in mm/yr (NaN where not fitted)."""
    cols = [np.ones_like(t), t]
    if annual:
        cols += [np.sin(2 * np.pi * t / 365.25), np.cos(2 * np.pi * t / 365.25)]
    X = np.stack(cols, 1)  # (epochs, k)
    k = X.shape[1]
    ok = valid.sum(0) > k  # only complete pixels are passed as valid, so this excludes nothing in practice
    W = valid[:, ok].astype(np.float64)
    A = (W.T @ (X[:, :, None] * X[:, None, :]).reshape(len(t), k * k)).reshape(-1, k, k)
    b = (W * np.where(valid[:, ok], D[:, ok], 0.0)).T @ X
    v = np.full(D.shape[1], np.nan)
    v[ok] = np.linalg.solve(A, b[..., None])[:, 1, 0] * 365.25
    return v


def main():
    INS.mkdir(parents=True, exist_ok=True)
    files = sorted((RAW / "opera/disp").glob("*.nc"))
    meta = []
    for f in files:
        with h5py.File(f) as h:
            meta.append({"file": f, "ref": pd.Timestamp(h["identification/reference_datetime"][()].decode()[:10]),
                         "sec": pd.Timestamp(h["identification/secondary_datetime"][()].decode()[:10])})
    meta = pd.DataFrame(meta).sort_values("sec").reset_index(drop=True)
    with h5py.File(files[0]) as h:
        X, Y = h["x"][:], h["y"][:]
        (INS / "layers.txt").write_text("Layers used, as named in " + files[0].name + ":\n" + "\n".join(
            f"{k}: {h[k].attrs.get('long_name', '')} ({h[k].attrs.get('units', '')})" for k in LAYERS) + "\n")
    X0, Y0, shape = float(X[0]), float(Y[0]), (len(Y), len(X))
    XX, YY = np.meshgrid(X, Y)
    px_all, py_all = XX.ravel(), YY.ravel()

    cells = {res: pd.read_csv(CP2 / f"features_{res}m.csv") for res in RESOLUTIONS}
    full = pd.read_csv(CP2 / "cells_250m.csv")  # every 250 m cell with a lot, for the runway cells
    rw = json.loads((RAW / "osm/lga_runways.json").read_text())["elements"]
    seg = [shapely.LineString(np.c_[TO_UTM.transform(*np.array([[p["lon"], p["lat"]] for p in e["geometry"]]).T)]) for e in rw]
    dense = np.concatenate([shapely.get_coordinates(shapely.line_interpolate_point(s, np.r_[np.arange(0, s.length, 10.0), s.length]))
                            for s in seg])  # runway centre lines sampled every 10 m
    x0, y0 = grid_origin(cells[250], 250)
    rwc = pd.DataFrame({"row": np.floor((y0 - dense[:, 1]) / 250).astype(int), "col": np.floor((dense[:, 0] - x0) / 250).astype(int)}).drop_duplicates()
    rwc["x"], rwc["y"] = x0 + (rwc.col + 0.5) * 250, y0 - (rwc.row + 0.5) * 250
    rwc = rwc.reset_index(drop=True)

    idx = {res: cell_index(px_all, py_all, cells[res], res) for res in RESOLUTIONS}
    rw_idx = cell_index(px_all, py_all, rwc, 250)
    sel = np.flatnonzero((idx[250] >= 0) | (idx[200] >= 0) | (rw_idx >= 0))
    px, py = px_all[sel], py_all[sel]
    inside_all, polys = borough_groups(px_all, py_all)
    grp = inside_all[sel].copy()
    out = grp == 0
    grp[out] = nearest_group(px[out], py[out], polys)
    print(f"{len(sel):,} pixels selected; {int(out.sum()):,} outside the borough polygons take the nearest", flush=True)

    T, P = len(meta), len(sel)
    D = np.empty((T, P), np.float32)
    V = np.empty((T, P), bool)
    Lok = np.empty((T, P), bool)
    main_label = []
    for i, f in enumerate(meta.file):
        with h5py.File(f) as h:
            d = h["displacement"][:].ravel()
            rec, wat, cc = (h[k][:].ravel() for k in LAYERS[1:])
        D[i] = (d[sel] * 1000.0).astype(np.float32)
        V[i] = (rec[sel] == 1) & (wat[sel] == 1) & np.isfinite(d[sel])
        labs = {}
        for g in range(1, 5):
            lg = cc[(inside_all == g) & (cc > 0)].astype(np.int64)
            labs[g] = int(np.bincount(lg).argmax()) if len(lg) else -1
        main_label.append(labs)
        ccs = cc[sel]
        Lok[i] = (ccs > 0) & (ccs == np.array([labs[g] for g in range(1, 5)], float)[grp - 1])
        if i % 20 == 0:
            print("read", i, f.name[30:65], labs, flush=True)
    meta["main_labels"] = [" ".join(f"{GROUPS[g - 1]}:{v}" for g, v in m.items()) for m in main_label]
    pm, n_permits = permits()

    ev = pd.read_csv(CP2 / "event_sample_250m.csv")
    ev = ev[ev.from_start]
    wins = [(L, pd.Timestamp(d)) for L, first in LENGTHS.items() for d in sorted(ev.date[ev.date >= first].unique())]
    end = meta.sec.max() + pd.Timedelta(days=1)
    wins.append((int((end - meta.ref.min()).days), end))  # full period, sign check
    refs = np.sort(meta.ref.unique())
    pix_cell = {res: idx[res][sel] for res in RESOLUTIONS}

    win_rows, cov_rows, tables = [], [], {res: [] for res in RESOLUTIONS}
    sign = None
    for wi, (L, te) in enumerate(wins):
        full_period = wi == len(wins) - 1
        wid = "full" if full_period else f"{L}d_{te.date()}"
        W0 = te - pd.Timedelta(days=L)
        rstar = refs[refs <= W0].max()
        ch = meta[(meta.ref >= rstar) & (meta.sec < te)]
        rebased = rebase_timeseries(np.where(V[ch.index], D[ch.index], np.nan), list(ch.ref))
        inw = (ch.sec >= W0).values
        Dw, Vw, Lw = rebased[inw], V[ch.index[inw]] & np.isfinite(rebased[inw]), Lok[ch.index[inw]]
        dates = ch.sec[inw]
        cross = ch.index[:-1][(ch.ref.values[1:] != ch.ref.values[:-1])]  # the product just before a reference change
        if rstar >= W0:  # the chain's reference epoch is itself a window date: displacement 0
            prev = meta.index[meta.sec == rstar]
            v0 = V[prev[0]] if len(prev) else np.ones(P, bool)
            Dw, Vw = np.vstack([np.zeros((1, P), np.float32), Dw]), np.vstack([v0, Vw])
            Lw = np.vstack([Lok[prev[0]] if len(prev) else np.ones(P, bool), Lw])
            dates = pd.concat([pd.Series([rstar]), dates])
        t = (pd.to_datetime(dates.values) - W0).days.values.astype(float)
        n_ep, n_q = len(t), L // QUARTER
        q = np.minimum((t // QUARTER).astype(int), n_q - 1)
        chain_ok = V[cross].all(0) if len(cross) else np.ones(P, bool)
        label_ok = Lw.all(0)
        n_valid = Vw.sum(0)
        quarters_ok = np.all([Vw[q == k].any(0) for k in range(n_q)], axis=0)
        complete = (n_valid >= MIN_SHARE * n_ep) & quarters_ok
        good = chain_ok & label_ok & complete
        vw = np.where(good, Vw, False)
        v_ann = fit(Dw, vw, t, annual=True)
        v_lin = fit(Dw, vw, t, annual=False)
        if full_period:
            cmask, n_perm = np.zeros(P, bool), 0
        else:
            cm, n_perm = construction_mask(pm, shape, X0, Y0, W0 - pd.Timedelta(days=PERMIT_LEAD), te)
            cmask = cm.ravel()[sel]
        keep = good & ~cmask
        win_rows.append({"window": wid, "length_days": L, "event_date": te.date(), "start": W0.date(), "chain_reference": pd.Timestamp(rstar).date(),
                         "epochs": n_ep, "reference_changes_in_window": len(cross), "quarters": n_q, "permits_in_mask": n_perm})
        e250 = pix_cell[250] >= 0
        cov_rows.append({"window": wid, "pixels_in_eligible_250m_cells": int(e250.sum()),
                         "masked_at_reference_change": int((e250 & ~chain_ok).sum()),
                         "component_label_rule": int((e250 & chain_ok & ~label_ok).sum()),
                         "completeness_rule": int((e250 & chain_ok & label_ok & ~complete).sum()),
                         "valid_before_construction_mask": int((e250 & good).sum()),
                         "construction_mask": int((e250 & good & cmask).sum()), "valid": int((e250 & keep).sum())})
        for res in RESOLUTIONS:
            pc = pix_cell[res]
            n = len(cells[res])
            agg = {}
            for name, count, ok, v in (("v", "n_px", keep, v_ann), ("v_linear", None, keep, v_lin),
                                       ("v_nomask", "n_px_nomask", good, v_ann)):
                m = ok & (pc >= 0)
                cnt = np.bincount(pc[m], minlength=n)
                agg[name] = np.where(cnt > 0, np.bincount(pc[m], v[m], minlength=n) / np.maximum(cnt, 1), np.nan)
                if count:
                    agg[count] = cnt
            t_ = pd.DataFrame({"window": wid, "row": cells[res].row.values, "col": cells[res].col.values, **agg})
            tables[res].append(t_[(t_.n_px > 0) | (t_.n_px_nomask > 0)])
        if full_period:
            m = keep & (rw_idx[sel] >= 0)
            cnt = np.bincount(rw_idx[sel][m], minlength=len(rwc))
            rwc = rwc.assign(v=np.where(cnt > 0, np.bincount(rw_idx[sel][m], v_ann[m], minlength=len(rwc)) / np.maximum(cnt, 1), np.nan), n_px=cnt)
            sign = rwc
        print(wid, win_rows[-1]["epochs"], "epochs;", cov_rows[-1], flush=True)

    pd.DataFrame(win_rows).to_csv(INS / "windows.csv", index=False)
    pd.DataFrame(cov_rows).to_csv(INS / "coverage.csv", index=False)
    meta.drop(columns="file").assign(file=[f.name for f in meta.file]).to_csv(INS / "products.csv", index=False)
    for res in RESOLUTIONS:
        pd.concat(tables[res], ignore_index=True).to_csv(INS / f"cells_{res}m.csv.gz", index=False,
                                                         compression={"method": "gzip", "mtime": 0})
    sign.to_csv(INS / "sign_check.csv", index=False)
    print("permits:", n_permits, "rows,", len(pm), "with coordinates")
    print("ALLDONE")


if __name__ == "__main__":
    main()
