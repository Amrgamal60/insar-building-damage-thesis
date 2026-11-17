"""Cycle-slip screen (§14 entry of 2026-11-11, "Lasting cycle slips"): finds, at every pixel of the DISP subset,
lasting steps of about one phase cycle in the chained series. Outcome-blind: reads only DISP layers and the pixel
grid. i08_window_values.py --slips then makes a pixel invalid for every window that contains one of its slips.

Settings (authors' choices, fixed and hashed before the screen was run):
  - Series: each product's displacement (mm) put on the first reference date as in i08 (the product whose secondary
    date equals a product's reference date carries the chain). Where that crossing product is invalid at a pixel
    (recommended mask, water mask, finite), the chain restarts at 0 and a new segment begins; steps are looked for
    within segments only. Values are used where valid and on the city's main component (§14 entry of 2026-11-11).
    Epoch 0 is the first reference date (value 0).
  - City common mode: at each epoch, the median value over the eligible-house pixels whose chain is unbroken
    (segment 0) and valid at that epoch. It is subtracted from every pixel.
  - Step at epoch e: B = mean of the valid values of epochs e-14 .. e (same segment as the last valid value at or
    before e), A = mean of the valid values of epochs e+1 .. e+15 (same segment as the first valid value after e).
    The jump J is the first valid value after e minus the last valid value at or before e (same segment).
    A slip is recorded if |A - B| >= 20 mm, |J| >= 20 mm, and each side has at least 8 valid values.
    Half the C-band wavelength is 27.7 mm; 15 epochs is about 6 months at the 12-day revisit, long enough that
    atmospheric episodes of a few weeks are not counted.
  - Each slip is stored as (pixel, date of the last valid value before it, date of the first valid value after it,
    A - B, J); duplicates of the same pair of dates at a pixel are dropped.
Mask rule (in i08): a pixel is invalid for a window [W0, te) if one of its slips has both dates inside it
(W0 <= date_from and date_to < te). A slip before the window start only shifts the whole window's series by a
constant and does not change the fit.
Outputs: OUT/slips.npz (pixel = flat subset index r * ncols + c, date_from, date_to as days since 1970-01-01, step,
jump; testable = per pixel, the number of epochs at which the test could be made), OUT/slips.json (settings, counts,
dates, house pixels).
Usage: OMP_NUM_THREADS=1 OPERA_PYTHON -I i11_slip_screen.py DISP_DIR INSAR_INPUTS_NPZ OUT [--workers N]
"""
import argparse
import hashlib
import json
import platform
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

MIN_STEP, MIN_JUMP, HALF, MIN_SIDE = 20.0, 20.0, 15, 8
DISP_FILES, DISP_MANIFEST = 254, "e261a28f544f41a618d605629925e0628f11b8a759a19fb35766f3ea01611fac"
G = {}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def chain(cols):
    """Restartable chain on the given subset columns: values (T+1 x n, NaN where not usable), segment ids."""
    meta, D, V, Lok = G["meta"], G["D"], G["V"], G["Lok"]
    T, n = len(meta), len(cols)
    val = np.full((T + 1, n), np.nan)
    seg = np.zeros((T + 1, n), np.int16)
    use = np.zeros((T + 1, n), bool)
    val[0], use[0] = 0.0, True
    base, bseg = {meta.ref[0]: np.zeros(n)}, {meta.ref[0]: np.zeros(n, np.int16)}
    cur = np.zeros(n, np.int16)
    raw = np.full((T + 1, n), np.nan)  # chained value at every epoch where the product is valid (carries the chain)
    raw[0] = 0.0
    for k in range(T):
        r = meta.ref[k]
        if r not in base:
            j = G["crossing"][r]  # the product whose secondary date is r
            ok = V[j, cols] & np.isfinite(raw[j + 1])
            cur = np.where(ok, seg[j + 1], cur + 1).astype(np.int16)
            base[r], bseg[r] = np.where(ok, raw[j + 1], 0.0), cur.copy()
        v = V[k, cols]
        raw[k + 1] = np.where(v, base[r] + D[k, cols], np.nan)
        seg[k + 1] = bseg[r]
        use[k + 1] = v & Lok[k, cols]
    val = np.where(use, raw, np.nan)
    return val, seg, use


def screen(cols):
    val, seg, use = chain(cols)
    y = val - G["common"][:, None]
    use &= np.isfinite(y)
    E, n = y.shape
    idx = np.where(use, np.arange(E)[:, None], -1)
    prev = np.maximum.accumulate(idx, axis=0)  # last usable index <= e
    nxt_src = np.where(use, np.arange(E)[:, None], E)
    nxt = np.minimum.accumulate(nxt_src[::-1], axis=0)[::-1]  # first usable index >= e
    nxt = np.vstack([nxt[1:], np.full((1, n), E)])  # first usable index >= e + 1
    cc = np.arange(n)[None, :]
    okp, okn = prev >= 0, nxt < E
    sp = np.where(okp, seg[np.maximum(prev, 0), cc], -1)
    sn = np.where(okn, seg[np.minimum(nxt, E - 1), cc], -2)
    yp = np.where(okp, y[np.maximum(prev, 0), cc], np.nan)
    yn = np.where(okn, y[np.minimum(nxt, E - 1), cc], np.nan)
    sA, nA, sB, nB = (np.zeros((E, n)) for _ in range(4))
    yz = np.where(use, y, 0.0)
    for d in range(HALF):
        # before: epochs e - d (d = 0 .. 14)
        e0 = np.arange(E) - d
        okb = e0 >= 0
        e0c = np.maximum(e0, 0)
        mb = okb[:, None] & use[e0c] & (seg[e0c] == sp)
        sB += np.where(mb, yz[e0c], 0.0)
        nB += mb
        # after: epochs e + 1 + d
        e1 = np.arange(E) + 1 + d
        oka = e1 < E
        e1c = np.minimum(e1, E - 1)
        ma = oka[:, None] & use[e1c] & (seg[e1c] == sn)
        sA += np.where(ma, yz[e1c], 0.0)
        nA += ma
    testable = (nA >= MIN_SIDE) & (nB >= MIN_SIDE) & (sp == sn)
    with np.errstate(invalid="ignore", divide="ignore"):
        step = sA / nA - sB / nB
    jump = yn - yp
    flag = testable & (np.abs(step) >= MIN_STEP) & (np.abs(jump) >= MIN_JUMP)
    e, p = np.nonzero(flag)
    out = pd.DataFrame(dict(pixel=np.asarray(cols)[p], e_from=prev[e, p], e_to=nxt[e, p], step=step[e, p], jump=jump[e, p]))
    out = out.loc[out.groupby(["pixel", "e_from", "e_to"]).step.apply(lambda s: s.abs().idxmax()).values] if len(out) else out
    return out, testable.sum(0).astype(np.int16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("disp", type=Path)
    ap.add_argument("inputs", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    assert sha256(a.disp / "MANIFEST.sha256") == DISP_MANIFEST
    files = sorted(a.disp.glob("*.nc"))
    assert len(files) == DISP_FILES
    a.out.mkdir(parents=True, exist_ok=False)
    T0 = time.time()
    run = dict(host=platform.node(), started=time.strftime("%Y-%m-%d %H:%M:%S %Z"), script_sha256=sha256(Path(__file__)),
               inputs=dict(insar_inputs=sha256(a.inputs), disp_manifest=DISP_MANIFEST),
               settings=dict(min_step_mm=MIN_STEP, min_jump_mm=MIN_JUMP, half_epochs=HALF, min_valid_per_side=MIN_SIDE),
               workers=a.workers)
    z = np.load(a.inputs, allow_pickle=False)
    x0, y0, NR, NC = z["grid"]
    NR, NC = int(NR), int(NC)
    P = NR * NC
    inside = z["inside_city"].ravel()
    hp = (z["r"] * NC + z["c"]).astype(np.int64)
    meta = []
    for f in files:
        with h5py.File(f, "r") as h:
            meta.append({"file": f, "ref": pd.Timestamp(h["identification/reference_datetime"][()].decode()[:10]),
                         "sec": pd.Timestamp(h["identification/secondary_datetime"][()].decode()[:10])})
    meta = pd.DataFrame(meta).sort_values("sec").reset_index(drop=True)
    T = len(meta)
    D = np.empty((T, P), np.float32)
    V = np.empty((T, P), bool)
    Lok = np.empty((T, P), bool)
    for i, f in enumerate(meta.file):
        with h5py.File(f, "r") as h:
            d = h["displacement"][:].ravel()
            rec, wat, cc = (h[k][:].ravel() for k in ("recommended_mask", "water_mask", "connected_component_labels"))
        D[i] = (d * 1000.0).astype(np.float32)
        V[i] = (rec == 1) & (wat == 1) & np.isfinite(d)
        ci = cc[inside]
        lab = int(np.bincount(ci[ci > 0].astype(np.int64)).argmax())
        Lok[i] = (cc > 0) & (cc == lab)
    crossing = {}
    for r in meta.ref.unique()[1:]:
        j = meta.index[meta.sec == r]
        assert len(j) == 1, r
        crossing[r] = int(j[0])
    G.update(meta=meta, D=D, V=V, Lok=Lok, crossing=crossing)
    val, seg, use = chain(hp)
    ok = use & (seg == 0)
    common = np.array([np.median(val[e, ok[e]]) for e in range(T + 1)])
    G["common"] = common
    del val, seg, use
    dates = np.r_[np.datetime64(meta.ref[0].date()), meta.sec.values.astype("datetime64[D]")]
    run["read_seconds"] = time.time() - T0
    print(f"read {T} products, common mode sd {np.std(common):.1f} mm, {run['read_seconds']:.0f} s", flush=True)

    chunks = np.array_split(np.arange(P), 256)
    parts, testable = [], np.zeros(P, np.int16)
    with ProcessPoolExecutor(a.workers, mp_context=get_context("fork")) as ex:
        for cols, (o, tst) in zip(chunks, ex.map(screen, chunks)):
            parts.append(o)
            testable[cols] = tst
    S = pd.concat(parts, ignore_index=True).sort_values(["pixel", "e_from"]).reset_index(drop=True)
    S["date_from"], S["date_to"] = dates[S.e_from.to_numpy()], dates[S.e_to.to_numpy()]
    np.savez(a.out / "slips.npz", pixel=S.pixel.to_numpy(np.int32),
             date_from=S.date_from.to_numpy().astype("datetime64[D]").astype(np.int64).astype(np.int32),
             date_to=S.date_to.to_numpy().astype("datetime64[D]").astype(np.int64).astype(np.int32),
             step=S.step.to_numpy(np.float32), jump=S.jump.to_numpy(np.float32), testable=testable,
             common=common, epoch_dates=dates.astype(np.int64).astype(np.int32))
    hpset = np.zeros(P, bool)
    hpset[hp] = True
    sh = S[hpset[S.pixel.to_numpy()]]
    hist, edges = np.histogram(np.abs(S.step), bins=np.arange(20, 84, 4))
    R = dict(run, seconds=time.time() - T0, epochs=T + 1, common_mode_sd_mm=float(np.std(common)),
             subset_pixels=P, pixels_testable=int((testable > 0).sum()), house_pixels=len(hp),
             house_pixels_testable=int((testable[hp] > 0).sum()),
             house_pixels_testable_epochs_median=float(np.median(testable[hp])),
             slips=len(S), pixels_with_slip=int(S.pixel.nunique()),
             house_pixels_with_slip=int(sh.pixel.nunique()),
             houses_on_slip_pixels=int(np.isin(hp[z["house_pixel"]], sh.pixel.unique()).sum()),
             positive=int((S.step > 0).sum()),
             step_size_histogram_abs_mm={f"{int(a_)}-{int(b_)}": int(c_) for a_, b_, c_ in zip(edges[:-1], edges[1:], hist)},
             most_common_dates={f"{a_} -> {b_}": int(n_) for (a_, b_), n_ in
                                S.groupby([S.date_from.astype(str), S.date_to.astype(str)]).size().sort_values(ascending=False).head(15).items()},
             house_pixel_most_common_dates={f"{a_} -> {b_}": int(n_) for (a_, b_), n_ in
                                            sh.groupby([sh.date_from.astype(str), sh.date_to.astype(str)]).size().sort_values(ascending=False).head(10).items()})
    R["outputs"] = {"slips.npz": sha256(a.out / "slips.npz")}
    (a.out / "slips.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
    print(json.dumps({k: R[k] for k in R if k not in ("inputs", "settings")}, indent=1, default=str))


if __name__ == "__main__":
    main()
