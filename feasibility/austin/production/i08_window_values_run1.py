"""InSAR window values (AUSTIN_PLAN.md §7, §13 step 3), blind to outcomes: no event, outcome, fold or block is read.

Adapted from NYC scripts/09_insar_velocities.py (frozen NYC §7 steps 1-3); the steps that are unchanged keep its
code. Runs in the OPERA environment (opera-utils 0.25.8, the NYC re-referencing function) on the processing server.

Per window [W0, te): W0 = the first day of month m - L months, te = the first day of month m (the window is the
L months ending on the last day before m). Acquisitions dated W0 <= date < te are used.
1. Layer and masks (NYC step 1): `displacement` (m -> mm), `recommended_mask` == 1 and `water_mask` == 1 on each
   date.
2. Re-referencing (NYC step 2): the chain starts at the last reference date R* <= W0; products with reference
   date >= R* and secondary date < te are chained with opera-utils' rebase_timeseries (NaN at a reference change
   propagates). If R* >= W0, R* is itself a window epoch with displacement 0.
3. Invalid for the window (NYC step 3, with the §14 deviation of 2026-11-11): masked at a reference change in the
   chain; or, at any window epoch, a connected-component label of 0 or a label other than the city's main
   component (the most common non-zero label among pixels whose centre lies inside the full-purpose boundary).
4. Line of sight, positive toward the satellite; no vertical projection.
5. Construction mask (§7, §14 entry of 2026-11-11): pixels whose centre is within 50 m of the parcel polygon (or
   permit point) of a mask permit issued from W0 - 365 days to the window's last day (te - 1 day). The
   permit-to-pixel table is production/i06_mask_permits.py's.
Fit (NYC): least squares d = a + v t + b sin(2 pi t / 365.25) + c cos(2 pi t / 365.25) on the pixel's valid dates
(t in days from W0; v in mm/yr; b, c in mm), only for pixels valid on >= 80% of the window's dates and on >= 1 date
in each 91-day quarter from W0 (the last quarter takes the leftover days).

Window families (by end month m):
  L24: m = 2018-08 .. 2025-11 (88; Test A primary; lags 1/3/6/12 are the same windows at m - lag).
  L12: m = 2017-08 .. 2025-11 (100; Test A 12 months; Test B 12 months and its lags; secondary 19).
  L36: m = 2019-08 .. 2025-11 (76; Test A 36 months).
  full: W0 = the first reference date, te = the day after the last acquisition, no construction mask (as NYC's
        sign-check period); for the sign and clay contrast checks.
Values at the eligible house pixels (insar_inputs.npz, testa_core.Geometry order):
  v (indicator 1), amp = sqrt(b^2 + c^2) (indicator 2), lrm = v minus the median v of the valid pixels whose
  centre is 60-250 m from the pixel's centre (indicator 3; NaN if none), for L24 and L12; v_nomask (secondary 13)
  and avail = the number of valid pixels whose centre is within 100 m of the pixel's centre, itself included
  (secondary 12), for L24; v for L36. Acceleration (indicator 4) = v of L12 at m minus v of L12 at m - 12, made
  downstream. "Valid" means a value after the construction mask.
NYC-design cells (secondary 1), L24: mean and count of the valid pixels whose centre lies in each eligible 250 m
cell.
Outputs in OUT: L24.npz, L12.npz, L36.npz, nyc_cells_L24.npz, full.npz (whole subset), house_series.npz (each
product's displacement in mm, validity and label flag at the house pixels, for the deep model, secondary 20),
windows.csv, coverage.csv, products.csv, layers.txt, run.json.
Usage: OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
         OPERA_PYTHON -I i08_window_values.py DISP_DIR INSAR_INPUTS_NPZ MASK_PERMITS_NPZ OUT [--workers N]
"""
import argparse
import hashlib
import json
import os
import platform
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import h5py
import numpy as np
import opera_utils
import pandas as pd
from opera_utils.disp import rebase_timeseries

QUARTER, MIN_SHARE, PERMIT_LEAD, PERMIT_M = 91, 0.8, 365, 50.0
RING_M, AVAIL_M = (60.0, 250.0), 100.0
LAYERS = ["displacement", "recommended_mask", "water_mask", "connected_component_labels"]
FAMILIES = {"L24": (24, "2018-08"), "L12": (12, "2017-08"), "L36": (36, "2019-08")}
LAST_MONTH = "2025-11"
DISP_FILES, DISP_MANIFEST = 254, "e261a28f544f41a618d605629925e0628f11b8a759a19fb35766f3ea01611fac"
THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_CORETYPE")
G = {}  # arrays shared with forked workers


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def blas_info():
    try:
        from threadpoolctl import threadpool_info
        return [{k: i.get(k) for k in ("internal_api", "version", "num_threads", "architecture")} for i in threadpool_info()]
    except ImportError:
        cfg = np.show_config(mode="dicts") if np.lib.NumpyVersion(np.__version__) >= "1.26.0" else None
        return cfg.get("Build Dependencies", {}).get("blas") if cfg else None


def fit_coef(D, valid, t):
    """NYC fit (scripts/09_insar_velocities.py, annual=True), returning all coefficients (NaN where not fitted)."""
    X = np.stack([np.ones_like(t), t, np.sin(2 * np.pi * t / 365.25), np.cos(2 * np.pi * t / 365.25)], 1)
    k = X.shape[1]
    ok = valid.sum(0) > k
    W = valid[:, ok].astype(np.float64)
    A = (W.T @ (X[:, :, None] * X[:, None, :]).reshape(len(t), k * k)).reshape(-1, k, k)
    b = (W * np.where(valid[:, ok], D[:, ok], 0.0)).T @ X
    coef = np.full((D.shape[1], k), np.nan)
    coef[ok] = np.linalg.solve(A, b[..., None])[:, :, 0]
    return coef


def offsets(lo, hi):
    r = int(np.ceil(hi / 30))
    dr, dc = np.meshgrid(np.arange(-r, r + 1), np.arange(-r, r + 1), indexing="ij")
    d = 30.0 * np.hypot(dr, dc)
    keep = (d >= lo) & (d <= hi)
    return dr[keep], dc[keep]


def neighbours(r, c, lo, hi, NR, NC):
    """Flat subset index of the pixels at centre distance [lo, hi] from each (r, c); -1 outside the subset."""
    dr, dc = offsets(lo, hi)
    rr, cc = r[:, None] + dr[None], c[:, None] + dc[None]
    ok = (rr >= 0) & (rr < NR) & (cc >= 0) & (cc < NC)
    return np.where(ok, rr * NC + cc, -1)


def construction_mask(W0, te):
    """Boolean over the subset: pixels masked by permits issued in [W0 - 365 days, te - 1 day]."""
    lo = np.datetime64(W0 - pd.Timedelta(days=PERMIT_LEAD), "D").astype(np.int64)
    hi = np.datetime64(te - pd.Timedelta(days=1), "D").astype(np.int64)
    day, ptr = G["issue_day"], G["ptr"]
    i0, i1 = np.searchsorted(day, lo, "left"), np.searchsorted(day, hi, "right")
    m = np.zeros(G["P"], bool)
    m[G["pixel"][ptr[i0]:ptr[i1]]] = True
    return m, int(i1 - i0)


def window(spec):
    family, month, W0, te, use_mask = spec
    meta, D, V, Lok, P = G["meta"], G["D"], G["V"], G["Lok"], G["P"]
    refs = G["refs"]
    rstar = refs[refs <= np.datetime64(W0)].max()
    ch = meta[(meta.ref >= rstar) & (meta.sec < te)]
    rebased = rebase_timeseries(np.where(V[ch.index], D[ch.index], np.nan), list(ch.ref))
    inw = (ch.sec >= W0).values
    Dw, Vw, Lw = rebased[inw], V[ch.index[inw]] & np.isfinite(rebased[inw]), Lok[ch.index[inw]]
    dates = ch.sec[inw]
    cross = ch.index[:-1][(ch.ref.values[1:] != ch.ref.values[:-1])]  # the product just before a reference change
    if rstar >= np.datetime64(W0):  # the chain's reference epoch is itself a window date: displacement 0
        prev = meta.index[meta.sec == rstar]
        v0 = V[prev[0]] if len(prev) else np.ones(P, bool)
        Dw, Vw = np.vstack([np.zeros((1, P), np.float32), Dw]), np.vstack([v0, Vw])
        Lw = np.vstack([Lok[prev[0]] if len(prev) else np.ones(P, bool), Lw])
        dates = pd.concat([pd.Series([pd.Timestamp(rstar)]), dates])
    del rebased
    t = (pd.to_datetime(dates.values) - W0).days.values.astype(float)
    L = (te - W0).days
    n_ep, n_q = len(t), L // QUARTER
    q = np.minimum((t // QUARTER).astype(int), n_q - 1)
    chain_ok = V[cross].all(0) if len(cross) else np.ones(P, bool)
    label_ok = Lw.all(0)
    n_valid = Vw.sum(0)
    quarters_ok = np.all([Vw[q == k].any(0) for k in range(n_q)], axis=0)
    complete = (n_valid >= MIN_SHARE * n_ep) & quarters_ok
    good = chain_ok & label_ok & complete
    coef = fit_coef(Dw, np.where(good, Vw, False), t)
    del Dw, Vw, Lw
    v_all = coef[:, 1] * 365.25
    amp_all = np.hypot(coef[:, 2], coef[:, 3])
    if use_mask:
        cmask, n_perm = construction_mask(W0, te)
    else:
        cmask, n_perm = np.zeros(P, bool), 0
    keep = good & ~cmask
    v_keep = np.where(keep, v_all, np.nan)
    hp = G["house_flat"]
    win = dict(family=family, month=month, start=str(W0.date()), end_exclusive=str(te.date()),
               chain_reference=str(pd.Timestamp(rstar).date()), epochs=n_ep,
               reference_changes_in_chain=len(cross), quarters=n_q, permits_in_mask=n_perm,
               subset_pixels_masked=int(cmask.sum()))
    hw = G["house_weight"]
    cov = dict(family=family, month=month, house_pixels=len(hp),
               masked_at_reference_change=int((~chain_ok[hp]).sum()),
               component_label_rule=int((chain_ok & ~label_ok)[hp].sum()),
               completeness_rule=int((chain_ok & label_ok & ~complete)[hp].sum()),
               valid_before_construction_mask=int(good[hp].sum()),
               construction_mask=int((good & cmask)[hp].sum()), valid=int(keep[hp].sum()),
               houses=int(hw.sum()), houses_valid=int(hw[keep[hp]].sum()))
    out = dict(win=win, cov=cov)
    if family == "full":
        out.update(v=v_all.astype(np.float64), amp=amp_all, good=good)
        return out
    out["v"] = v_keep[hp]
    if family == "L36":
        return out
    out["amp"] = np.where(keep, amp_all, np.nan)[hp]
    ring = G["ring"]
    vr = np.where(ring >= 0, v_keep[np.maximum(ring, 0)], np.nan)
    with warnings.catch_warnings():  # all-NaN rings give NaN
        warnings.simplefilter("ignore", RuntimeWarning)
        med = np.nanmedian(vr, axis=1)
    out["lrm"] = out["v"] - med
    out["lrm_ring_valid"] = np.isfinite(vr).sum(1).astype(np.int16)
    if family == "L24":
        out["v_nomask"] = np.where(good, v_all, np.nan)[hp]
        av = G["avail"]
        out["avail"] = np.where(av >= 0, keep[np.maximum(av, 0)], False).sum(1).astype(np.int16)
        pc = G["pix_cell"]
        m = keep & (pc >= 0)
        cnt = np.bincount(pc[m], minlength=G["ncells"])
        out["cell_mean"] = np.where(cnt > 0, np.bincount(pc[m], v_all[m], minlength=G["ncells"]) / np.maximum(cnt, 1), np.nan)
        out["cell_count"] = cnt.astype(np.int32)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("disp", type=Path)
    ap.add_argument("inputs", type=Path)
    ap.add_argument("mask", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    assert sha256(a.disp / "MANIFEST.sha256") == DISP_MANIFEST
    listed = {ln.split()[1].lstrip("*") for ln in (a.disp / "MANIFEST.sha256").read_text().splitlines() if ln.strip()}
    files = sorted(a.disp.glob("*.nc"))
    assert len(files) == DISP_FILES and {f.name for f in files} == {Path(n).name for n in listed if n.endswith(".nc")}
    a.out.mkdir(parents=True, exist_ok=False)
    T0 = time.time()
    run = dict(host=platform.node(), started=time.strftime("%Y-%m-%d %H:%M:%S %Z"), script_sha256=sha256(Path(__file__)),
               inputs=dict(insar_inputs=sha256(a.inputs), mask_permits=sha256(a.mask),
                           disp_manifest=sha256(a.disp / "MANIFEST.sha256")),
               environment={k: os.environ.get(k) for k in THREAD_VARS},
               versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                             h5py=h5py.__version__, opera_utils=opera_utils.__version__, blas=blas_info()),
               settings=dict(quarter_days=QUARTER, min_share=MIN_SHARE, permit_lead_days=PERMIT_LEAD, permit_m=PERMIT_M,
                             ring_m=RING_M, avail_m=AVAIL_M, families=FAMILIES, last_month=LAST_MONTH), workers=a.workers)

    z = np.load(a.inputs, allow_pickle=False)
    x0, y0, NR, NC = z["grid"]
    NR, NC = int(NR), int(NC)
    G["P"] = NR * NC
    hp = (z["r"] * NC + z["c"]).astype(np.int64)
    G["house_flat"] = hp
    G["house_weight"] = np.bincount(z["house_pixel"], minlength=len(hp))
    G["ring"] = neighbours(z["r"], z["c"], *RING_M, NR, NC)
    G["avail"] = neighbours(z["r"], z["c"], 0.0, AVAIL_M, NR, NC)
    inside = z["inside_city"].ravel()
    xs, ys = x0 + 30.0 * np.arange(NC), y0 - 30.0 * np.arange(NR)
    XX, YY = np.meshgrid(xs, ys)
    ckey = np.floor(XX.ravel() / 250).astype(np.int64) * 1_000_000 + np.floor(YY.ravel() / 250).astype(np.int64)
    cell_key = z["cell_x"] * 1_000_000 + z["cell_y"]
    pos = np.searchsorted(cell_key, ckey)
    pos = np.minimum(pos, len(cell_key) - 1)
    G["pix_cell"] = np.where(cell_key[pos] == ckey, pos, -1)
    G["ncells"] = len(cell_key)
    mk = np.load(a.mask, allow_pickle=False)
    G["issue_day"], G["ptr"], G["pixel"] = mk["issue_day"].astype(np.int64), mk["ptr"], mk["pixel"].astype(np.int64)
    assert np.all(np.diff(G["issue_day"]) >= 0)

    meta = []
    for f in files:
        with h5py.File(f, "r") as h:
            meta.append({"file": f, "ref": pd.Timestamp(h["identification/reference_datetime"][()].decode()[:10]),
                         "sec": pd.Timestamp(h["identification/secondary_datetime"][()].decode()[:10])})
    meta = pd.DataFrame(meta).sort_values("sec").reset_index(drop=True)
    with h5py.File(meta.file[0], "r") as h:
        X, Y = h["x"][:], h["y"][:]
        (a.out / "layers.txt").write_text("Layers used, as named in " + meta.file[0].name + ":\n" + "\n".join(
            f"{k}: {h[k].attrs.get('long_name', '')} ({h[k].attrs.get('units', '')})" for k in LAYERS) + "\n")
    assert (float(X[0]), float(Y[0]), len(Y), len(X)) == (x0, y0, NR, NC)
    T = len(meta)
    D = np.empty((T, G["P"]), np.float32)
    V = np.empty((T, G["P"]), bool)
    Lok = np.empty((T, G["P"]), bool)
    main_label, main_share, house_label0 = [], [], []
    for i, f in enumerate(meta.file):
        with h5py.File(f, "r") as h:
            d = h["displacement"][:].ravel()
            rec, wat, cc = (h[k][:].ravel() for k in LAYERS[1:])
        D[i] = (d * 1000.0).astype(np.float32)
        V[i] = (rec == 1) & (wat == 1) & np.isfinite(d)
        ci = cc[inside]
        nz = ci[ci > 0].astype(np.int64)
        lab = int(np.bincount(nz).argmax())
        main_label.append(lab)
        main_share.append(float((ci == lab).mean()))
        Lok[i] = (cc > 0) & (cc == lab)
        house_label0.append(float((cc[hp] == 0).mean()))
        if i % 25 == 0:
            print(f"read {i} {f.name[30:65]} main label {lab}", flush=True)
    meta["main_label"], meta["main_share_inside_city"], meta["house_pixels_label0"] = main_label, main_share, house_label0
    G.update(meta=meta, D=D, V=V, Lok=Lok, refs=np.sort(meta.ref.unique()))
    np.savez(a.out / "house_series.npz", reference=meta.ref.values.astype("datetime64[D]"),
             secondary=meta.sec.values.astype("datetime64[D]"), displacement_mm=D[:, hp], valid=V[:, hp], label_ok=Lok[:, hp],
             pix_i=z["pix_i"], pix_j=z["pix_j"])
    run["read_seconds"] = time.time() - T0
    print(f"read {T} products in {run['read_seconds']:.0f} s", flush=True)

    specs = [("full", "full", meta.ref.min(), meta.sec.max() + pd.Timedelta(days=1), False)]  # slowest first
    for fam, (L, first) in FAMILIES.items():
        for m in pd.period_range(first, LAST_MONTH, freq="M"):
            specs.append((fam, str(m), (m - L).start_time, m.start_time, True))
    results = {}
    with ProcessPoolExecutor(a.workers, mp_context=get_context("fork")) as ex:
        for spec, res in zip(specs, ex.map(window, specs)):
            results[(spec[0], spec[1])] = res
            print(spec[0], spec[1], res["cov"]["valid"], "of", res["cov"]["house_pixels"], "house pixels valid;",
                  res["win"]["epochs"], "epochs", flush=True)
    run["window_seconds"] = time.time() - T0 - run["read_seconds"]

    pix = dict(pix_i=z["pix_i"], pix_j=z["pix_j"])
    for fam in FAMILIES:
        months = [s[1] for s in specs if s[0] == fam]
        keys = [k for k in ("v", "amp", "lrm", "lrm_ring_valid", "v_nomask", "avail") if k in results[(fam, months[0])]]
        np.savez(a.out / f"{fam}.npz", months=np.array(months),
                 **{k: np.stack([results[(fam, m)][k] for m in months]) for k in keys}, **pix)
    months = [s[1] for s in specs if s[0] == "L24"]
    np.savez(a.out / "nyc_cells_L24.npz", months=np.array(months), cell_x=z["cell_x"], cell_y=z["cell_y"],
             mean=np.stack([results[("L24", m)]["cell_mean"] for m in months]),
             count=np.stack([results[("L24", m)]["cell_count"] for m in months]))
    f = results[("full", "full")]
    np.savez(a.out / "full.npz", v=f["v"].reshape(NR, NC), amp=f["amp"].reshape(NR, NC), good=f["good"].reshape(NR, NC),
             x=xs, y=ys, inside_city=z["inside_city"])
    pd.DataFrame([r["win"] for r in results.values()]).to_csv(a.out / "windows.csv", index=False)
    pd.DataFrame([r["cov"] for r in results.values()]).to_csv(a.out / "coverage.csv", index=False)
    meta.drop(columns="file").assign(file=[p.name for p in meta.file]).to_csv(a.out / "products.csv", index=False)
    run["seconds"] = time.time() - T0
    run["finished"] = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    run["outputs"] = {p.name: sha256(p) for p in sorted(a.out.iterdir()) if p.name != "run.json"}
    (a.out / "run.json").write_text(json.dumps(run, indent=1, default=str) + "\n")
    print("ALLDONE", f"{run['seconds']:.0f} s", flush=True)


if __name__ == "__main__":
    main()
