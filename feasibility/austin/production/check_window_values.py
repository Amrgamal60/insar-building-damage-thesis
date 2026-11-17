"""Independent check of production/i08_window_values.py (outcome-blind: no event, outcome, fold or block is read).

Recomputes, by a separate per-pixel route, what i08 computes with whole-array operations, and compares:
A. Main connected-component label of each product (most common non-zero label among pixels whose centre lies inside
   the full-purpose boundary) and the share of house pixels with label 0: re-read from every .nc file, compared with
   products.csv.
B. house_series.npz: displacement (mm), validity and label flag of 5 house pixels in 8 products, read directly
   from the .nc files at the pixel's row and column.
C. coverage.csv: the rule counts add up to the house pixels; windows.csv: the reference changes in each chain equal
   the reference dates R with R* < R whose first product is dated before the window end.
D. Window values, per pixel, for 4 random months of each family and the full period (seed 11):
   - chain: products with reference date >= R* (the last reference date <= W0) and secondary date < te; each
     product's displacement is put on R* by adding the value, on the same chain, of the product whose secondary date
     equals the product's reference date (searched by date, not by position);
   - validity, label rule (main component per product, from A), completeness rule, construction mask (permits found
     through a pixel -> permit index, not the permit -> pixel slices) and least squares by numpy.linalg.lstsq;
   - compared with i08 at 300 random house pixels per window (v, amp, v_nomask for L24), with the 60-250 m ring
     median and the 100 m count at 8 of them (L24, L12), with the full-period v, amp and good at 300 random subset
     pixels, and with the NYC-design cell mean at 3 random cells (L24).
   - with SLIPS_NPZ (i08 run with --slips): a pixel with a slip whose two dates lie inside the window is invalid;
     slips are looked up per pixel from the slip table, not through i08's date selection.
Writes OUT_JSON with every difference and a pass flag per part.
Usage: OMP_NUM_THREADS=1 OPERA_PYTHON -I check_window_values.py DISP_DIR INSAR_INPUTS_NPZ MASK_PERMITS_NPZ I08_OUT OUT_JSON [SLIPS_NPZ]
"""
import hashlib
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

disp, inputs, mask, res, out_json = map(Path, sys.argv[1:6])
SLIPS = {}
if len(sys.argv) > 6:
    _sl = np.load(sys.argv[6])
    for _p, _a, _b in zip(_sl["pixel"].tolist(), _sl["date_from"].tolist(), _sl["date_to"].tolist()):
        SLIPS.setdefault(_p, []).append((pd.Timestamp(_a, unit="D"), pd.Timestamp(_b, unit="D")))
rng = np.random.default_rng(11)
TOL = 1e-3  # mm/yr or mm; the inputs are float32
R = {}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


R["inputs"] = {p.name: sha256(p) for p in (inputs, mask, res / "run.json") + ((Path(sys.argv[6]),) if len(sys.argv) > 6 else ())}
z = np.load(inputs)
x0, y0, NR, NC = z["grid"]
NR, NC = int(NR), int(NC)
inside = z["inside_city"].ravel()
hr, hc = z["r"], z["c"]
hflat = hr * NC + hc
files = sorted(disp.glob("*.nc"))
prod = pd.read_csv(res / "products.csv")

# ---- A. read every product; main label per product
info = []
for f in files:
    with h5py.File(f, "r") as h:
        info.append(dict(file=f.name, ref=pd.Timestamp(h["identification/reference_datetime"][()].decode()[:10]),
                         sec=pd.Timestamp(h["identification/secondary_datetime"][()].decode()[:10])))
meta = pd.DataFrame(info).sort_values(["sec", "file"]).reset_index(drop=True)
T, P = len(meta), NR * NC
D = np.empty((T, P), np.float64)
V = np.empty((T, P), bool)
CC = np.empty((T, P), np.int16)
for i, name in enumerate(meta.file):
    with h5py.File(disp / name, "r") as h:
        d = h["displacement"][()].ravel().astype(np.float64)
        D[i] = d * 1000.0
        V[i] = (h["recommended_mask"][()].ravel() == 1) & (h["water_mask"][()].ravel() == 1) & np.isfinite(d)
        CC[i] = h["connected_component_labels"][()].ravel()
main = []
for i in range(T):
    labs, cnt = np.unique(CC[i][inside & (CC[i] > 0)], return_counts=True)
    main.append(int(labs[cnt.argmax()]))
meta["main"] = main
meta["house_label0"] = [(CC[i][hflat] == 0).mean() for i in range(T)]
LOK = (CC > 0) & (CC == np.array(main, np.int16)[:, None])
m = meta.merge(prod, on="file", how="outer", validate="one_to_one", indicator=True)
R["A"] = dict(products=T, matched=int((m._merge == "both").sum()), main_label_differences=int((m.main != m.main_label).sum()),
              house_label0_max_diff=float((m.house_label0 - m.house_pixels_label0).abs().max()),
              products_main_not_1=m.loc[m.main != 1, "file"].str[30:65].tolist())
R["A"]["pass"] = R["A"]["matched"] == T == len(prod) and R["A"]["main_label_differences"] == 0 and R["A"]["house_label0_max_diff"] < 1e-12

# ---- B. house series
hs = np.load(res / "house_series.npz")
assert (hs["secondary"] == meta.sec.values.astype("datetime64[D]")).all() and (hs["reference"] == meta.ref.values.astype("datetime64[D]")).all()
bp, bt = rng.choice(len(hflat), 5, replace=False), rng.choice(T, 8, replace=False)
diffs = []
for t in bt:
    with h5py.File(disp / meta.file[t], "r") as h:
        for p in bp:
            dv = float(h["displacement"][hr[p], hc[p]]) * 1000.0
            a = float(hs["displacement_mm"][t, p])
            diffs.append(0.0 if (np.isnan(dv) and np.isnan(a)) else abs(dv - a))
            assert bool(hs["valid"][t, p]) == bool(V[t, hflat[p]]) and bool(hs["label_ok"][t, p]) == bool(LOK[t, hflat[p]])
R["B"] = dict(pixels=bp.tolist(), products=bt.tolist(), max_abs_diff_mm=float(np.nanmax(diffs)), flags_equal=True)
R["B"]["pass"] = R["B"]["max_abs_diff_mm"] < 1e-3

# ---- C. coverage sums, reference changes
cov, win = pd.read_csv(res / "coverage.csv"), pd.read_csv(res / "windows.csv")
parts = ["masked_at_reference_change", "component_label_rule", "completeness_rule", "valid_before_construction_mask"]
if "cycle_slip_rule" in cov:
    parts.insert(3, "cycle_slip_rule")
refs = sorted(set(meta.ref))
first_sec = meta.groupby("ref").sec.min()
exp = []
for _, w in win.iterrows():
    W0, te = pd.Timestamp(w.start), pd.Timestamp(w.end_exclusive)
    rstar = max(r for r in refs if r <= W0)
    exp.append(int(sum((r > rstar) and first_sec[r] < te for r in refs)))
R["C"] = dict(coverage_rows=len(cov), sums_equal=bool((cov[parts].sum(axis=1) == cov.house_pixels).all()),
              valid_plus_mask_equal=bool((cov.valid + cov.construction_mask == cov.valid_before_construction_mask).all()),
              reference_change_mismatches=int((np.array(exp) != win.reference_changes_in_chain.values).sum()),
              reference_dates_inside_window_differs=int(sum(
                  e != sum(pd.Timestamp(w.start) < r < pd.Timestamp(w.end_exclusive) for r in refs)
                  for e, (_, w) in zip(exp, win.iterrows()))))
R["C"]["pass"] = R["C"]["sums_equal"] and R["C"]["valid_plus_mask_equal"] and R["C"]["reference_change_mismatches"] == 0

# ---- D. per-pixel recomputation
mk = np.load(mask)
pday, ptr, ppix = mk["issue_day"].astype(np.int64), mk["ptr"], mk["pixel"].astype(np.int64)
owner = np.repeat(np.arange(len(pday)), np.diff(ptr))
order = np.argsort(ppix, kind="stable")
spix, sown = ppix[order], owner[order]


def masked(flat, W0, te):
    lo = (W0 - pd.Timedelta(days=365)).to_datetime64().astype("datetime64[D]").astype(np.int64)
    hi = (te - pd.Timedelta(days=1)).to_datetime64().astype("datetime64[D]").astype(np.int64)
    a, b = np.searchsorted(spix, flat, "left"), np.searchsorted(spix, flat, "right")
    days = pday[sown[a:b]]
    return bool(((days >= lo) & (days <= hi)).any())


PLANS = {}


def plan(W0, te):
    """Chain of the window, found by dates: (product, base product or None), crossing products, window epochs."""
    if (W0, te) not in PLANS:
        rstar = max(r for r in refs if r <= W0)
        ch = meta[(meta.ref >= rstar) & (meta.sec < te)].sort_values("sec")
        links = []
        for k, row in ch.iterrows():
            prev = ch.index[ch.sec == row.ref]
            assert row.ref == rstar or len(prev) == 1
            links.append((k, None if row.ref == rstar else int(prev[0])))
        crossing = [int(ch.index[ch.sec == r][0]) for r in ch.ref.unique() if r != rstar]
        epochs = [(row.sec, k) for k, row in ch.iterrows() if row.sec >= W0]
        if rstar >= W0:
            prev = meta.index[meta.sec == rstar]
            epochs.insert(0, (rstar, int(prev[0]) if len(prev) else None, "zero"))
        PLANS[(W0, te)] = links, crossing, epochs
    return PLANS[(W0, te)]


def pixel_value(flat, W0, te, use_mask=True):
    """(v mm/yr, amp mm, good before mask, masked) for one subset pixel."""
    links, crossing, epochs = plan(W0, te)
    cum = {}
    for k, base in links:
        cum[k] = (0.0 if base is None else cum[base]) + (D[k, flat] if V[k, flat] else np.nan)
    chain_ok = all(V[k, flat] for k in crossing)
    ep = []
    for e in epochs:
        if len(e) == 3:  # the chain's reference date inside the window: displacement 0
            k = e[1]
            ep.append((e[0], 0.0, bool(V[k, flat]) if k is not None else True, bool(LOK[k, flat]) if k is not None else True))
        else:
            k = e[1]
            ep.append((e[0], cum[k], bool(V[k, flat]) and np.isfinite(cum[k]), bool(LOK[k, flat])))
    t = np.array([(e[0] - W0).days for e in ep], float)
    y = np.array([e[1] for e in ep])
    ok = np.array([e[2] for e in ep])
    lab = all(e[3] for e in ep)
    nq = (te - W0).days // 91
    q = np.minimum(t // 91, nq - 1)
    complete = ok.sum() >= 0.8 * len(t) and all(ok[q == j].any() for j in range(nq))
    slipped = any(W0 <= a and b < te for a, b in SLIPS.get(int(flat), []))
    good = chain_ok and lab and complete and not slipped
    v = amp = np.nan
    if good:
        tt = t[ok]
        X = np.c_[np.ones_like(tt), tt, np.sin(2 * np.pi * tt / 365.25), np.cos(2 * np.pi * tt / 365.25)]
        coef = np.linalg.lstsq(X, y[ok], rcond=None)[0]
        v, amp = coef[1] * 365.25, float(np.hypot(coef[2], coef[3]))
    mk_ = masked(flat, W0, te) if use_mask else False
    return v, amp, good, mk_


def near(a, b):
    return (np.isnan(a) and np.isnan(b)) or abs(a - b) <= TOL


def ring(p, lo, hi):
    rr, cc = np.meshgrid(np.arange(hr[p] - 9, hr[p] + 10), np.arange(hc[p] - 9, hc[p] + 10), indexing="ij")
    d = 30.0 * np.hypot(rr - hr[p], cc - hc[p])
    s = (d >= lo) & (d <= hi) & (rr >= 0) & (rr < NR) & (cc >= 0) & (cc < NC)
    return (rr[s] * NC + cc[s]).tolist()


R["D"] = {}
fams = {"L24": (24, "2018-08"), "L12": (12, "2017-08"), "L36": (36, "2019-08")}
for fam, (L, first) in fams.items():
    F = np.load(res / f"{fam}.npz")
    months = list(F["months"])
    for mth in rng.choice(months, 4, replace=False):
        mi = months.index(mth)
        per = pd.Period(mth, "M")
        W0, te = (per - L).start_time, per.start_time
        sp = rng.choice(len(hflat), 300, replace=False)
        bad = dict(v=0, amp=0, v_nomask=0)
        mx = dict(v=0.0, amp=0.0)
        for p in sp:
            v, amp, good, mk_ = pixel_value(int(hflat[p]), W0, te)
            keep = good and not mk_
            ev, ea = (v, amp) if keep else (np.nan, np.nan)
            bad["v"] += not near(ev, float(F["v"][mi, p]))
            if np.isfinite(ev):
                mx["v"] = max(mx["v"], abs(ev - float(F["v"][mi, p])))
            if fam != "L36":
                bad["amp"] += not near(ea, float(F["amp"][mi, p]))
                if np.isfinite(ea):
                    mx["amp"] = max(mx["amp"], abs(ea - float(F["amp"][mi, p])))
            if fam == "L24":
                bad["v_nomask"] += not near(v if good else np.nan, float(F["v_nomask"][mi, p]))
        rec = dict(window=f"{fam} {mth}", pixels=300, valid=int(np.isfinite(F["v"][mi, sp]).sum()), mismatches=bad,
                   max_abs_diff=mx)
        if fam != "L36":
            lb = dict(lrm=0, avail=0, ring_pixels=0)
            cand = [p for p in sp if np.isfinite(F["v"][mi, p])][:8]
            for p in cand:
                vals = []
                for q_ in ring(p, 60.0, 250.0):
                    v, _, good, mk_ = pixel_value(q_, W0, te)
                    if good and not mk_:
                        vals.append(v)
                exp_lrm = float(F["v"][mi, p]) - float(np.median(vals)) if vals else np.nan
                lb["lrm"] += not near(exp_lrm, float(F["lrm"][mi, p]))
                lb["ring_pixels"] += len(vals) != int(F["lrm_ring_valid"][mi, p])
                if fam == "L24":
                    n = 0
                    for q_ in ring(p, 0.0, 100.0):
                        _, _, good, mk_ = pixel_value(q_, W0, te)
                        n += good and not mk_
                    lb["avail"] += n != int(F["avail"][mi, p])
            rec["neighbourhood"] = dict(pixels=len(cand), mismatches=lb)
        if fam == "L24":
            C = np.load(res / "nyc_cells_L24.npz")
            cbad = 0
            for ci in rng.choice(len(C["cell_x"]), 3, replace=False):
                cx, cy = int(C["cell_x"][ci]), int(C["cell_y"][ci])
                xs, ys = x0 + 30.0 * np.arange(NC), y0 - 30.0 * np.arange(NR)
                cols = np.flatnonzero(np.floor(xs / 250) == cx)
                rows = np.flatnonzero(np.floor(ys / 250) == cy)
                vals = []
                for r_ in rows:
                    for c_ in cols:
                        v, _, good, mk_ = pixel_value(int(r_ * NC + c_), W0, te)
                        if good and not mk_:
                            vals.append(v)
                cbad += not (near(float(np.mean(vals)) if vals else np.nan, float(C["mean"][mi, ci])) and len(vals) == int(C["count"][mi, ci]))
            rec["nyc_cells"] = dict(cells=3, mismatches=cbad)
        R["D"][rec["window"]] = rec
        print(json.dumps(rec), flush=True)

Fz = np.load(res / "full.npz")
W0, te = meta.ref.min(), meta.sec.max() + pd.Timedelta(days=1)
sp = rng.choice(P, 300, replace=False)
fb = dict(v=0, amp=0, good=0)
for p in sp:
    v, amp, good, _ = pixel_value(int(p), W0, te, use_mask=False)
    fb["v"] += not near(v, float(Fz["v"].ravel()[p]))
    fb["amp"] += not near(amp, float(Fz["amp"].ravel()[p]))
    fb["good"] += good != bool(Fz["good"].ravel()[p])
R["D"]["full"] = dict(pixels=300, good=int(Fz["good"].ravel()[sp].sum()), mismatches=fb)
print(json.dumps(R["D"]["full"]), flush=True)


R["D_pass"] = all(all(v == 0 for v in rec["mismatches"].values()) and
                  all(v == 0 for v in rec.get("neighbourhood", {}).get("mismatches", {}).values()) and
                  rec.get("nyc_cells", {}).get("mismatches", 0) == 0 for rec in R["D"].values())
R["pass"] = all(R[k]["pass"] for k in "ABC") and R["D_pass"]
out_json.write_text(json.dumps(R, indent=1, default=str) + "\n")
print("PASS" if R["pass"] else "FAIL", {k: R[k]["pass"] for k in "ABC"}, R["D_pass"])
