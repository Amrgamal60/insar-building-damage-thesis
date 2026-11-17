"""Further diagnostics after the sign check came out "not below" (AUSTIN_PLAN.md §7). Outcome-blind: reads DISP
displacement, the i08 outputs, the landfill perimeters and the parcels' soil linear extensibility; no event, outcome,
fold or block. Changes nothing; it describes.

1. Step test at the two active landfills with valid pixels (perimeters 16 and 17): the full-period chained series of
   up to 8 valid pixels in the 100-500 m ring around each and of up to 8 valid footprint pixels, and, for comparison,
   of 8 random valid house pixels. Per pixel: the largest change between consecutive epochs and the residual
   standard deviation about the full-period fit. A phase-unwrapping error would show as a step of about 28 mm
   (half the C-band wavelength, 27.7 mm) at one epoch.
2. Sign test from clay seasonality: the full-period seasonal terms b, c at every valid house pixel (as i08, t in days
   from 2016-07-10), averaged over the parcels of the high and very high classes and of the low class (each parcel
   once). The difference of the two seasonal curves cancels terms common to both groups (thermal, atmospheric). If
   positive is toward the satellite (up), its trough should fall in the dry late summer to autumn, when clay shrinks.
   Calendar months of the trough and peak, with a 95% bootstrap interval over 2 km blocks (500 draws, seed 2026).
The chain is i08's (opera-utils rebase_timeseries), on the full period: first reference date to the day after the
last acquisition, no construction mask.
Usage: OPERA_PYTHON -I diag_sign_series.py DISP_DIR I08_OUT INSAR_INPUTS_NPZ LEP_NPZ PERIMETERS BOUNDARY OUT_JSON
"""
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import shapely
from opera_utils.disp import rebase_timeseries
from pyproj import Transformer
from shapely.geometry import shape

disp, res, inputs, lep_npz, perim, boundary, out = map(Path, sys.argv[1:8])
OMEGA = 2 * np.pi / 365.25
rng = np.random.default_rng(2026)
R = {}
z = np.load(inputs)
x0, y0, NR, NC = z["grid"]
NR, NC = int(NR), int(NC)
prod = pd.read_csv(res / "products.csv", parse_dates=["ref", "sec"])
files = list(prod.file)
W0, te = prod.ref.min(), prod.sec.max() + pd.Timedelta(days=1)
refs = list(prod.ref)
cross = [k for k in range(len(prod) - 1) if prod.ref[k + 1] != prod.ref[k]]
t = np.r_[0.0, (prod.sec - W0).dt.days.to_numpy(float)]  # epoch 0 = the first reference date, displacement 0
nq = (te - W0).days // 91
q = np.minimum((t // 91).astype(int), nq - 1)


def chain(D, V, L):
    """Full-period chained series (epochs x pixels, epoch 0 first) and i08's validity (good)."""
    reb = rebase_timeseries(np.where(V, D, np.nan).astype(np.float32), refs)
    Dw = np.vstack([np.zeros((1, D.shape[1]), np.float32), reb])
    Vw = np.vstack([np.ones((1, D.shape[1]), bool), V & np.isfinite(reb)])
    Lw = np.vstack([np.ones((1, D.shape[1]), bool), L])
    complete = (Vw.sum(0) >= 0.8 * len(t)) & np.all([Vw[q == k].any(0) for k in range(nq)], axis=0)
    good = V[cross].all(0) & Lw.all(0) & complete
    return Dw, Vw, good


def fit(Dw, Vw, good):
    X = np.c_[np.ones_like(t), t, np.sin(OMEGA * t), np.cos(OMEGA * t)]
    coef = np.full((Dw.shape[1], 4), np.nan)
    for p in np.flatnonzero(good):
        coef[p] = np.linalg.lstsq(X[Vw[:, p]], Dw[Vw[:, p], p].astype(float), rcond=None)[0]
    return coef


# ---- 1. step test
F = np.load(res / "full.npz")
ok = F["good"] & np.isfinite(F["v"])
XX, YY = np.meshgrid(F["x"], F["y"])
tr = Transformer.from_crs("EPSG:4326", "EPSG:32614", always_xy=True)
to_utm = lambda g: shapely.transform(g, lambda a: np.c_[tr.transform(a[:, 0], a[:, 1])])  # noqa: E731
city = shapely.union_all([to_utm(shape(f["geometry"])) for f in json.loads(boundary.read_text())["features"]])
polys = {f["properties"]["LANDFILLS_PERIMETER_ID"]: shapely.make_valid(to_utm(shape(f["geometry"])))
         for f in json.loads(perim.read_text())["features"]}
anyfoot = np.zeros(ok.shape, bool)
for g in polys.values():
    if g.intersects(city):
        anyfoot |= shapely.contains_xy(g, XX, YY)
groups = {}
for pid in (16, 17):
    g = polys[pid]
    d = shapely.distance(g, shapely.points(XX.ravel(), YY.ravel())).reshape(ok.shape)
    ring = np.flatnonzero(((d > 100) & (d <= 500) & ~anyfoot & ok).ravel())
    foot = np.flatnonzero((shapely.contains_xy(g, XX, YY) & ok).ravel())
    groups[f"{pid} ring"] = rng.choice(ring, min(8, len(ring)), replace=False)
    groups[f"{pid} footprint"] = rng.choice(foot, min(8, len(foot)), replace=False)
hp = z["r"] * NC + z["c"]
groups["house pixels"] = rng.choice(hp[ok.ravel()[hp]], 8, replace=False)
pix = np.concatenate(list(groups.values()))
D = np.empty((len(files), len(pix)), np.float32)
V = np.empty((len(files), len(pix)), bool)
L = np.empty((len(files), len(pix)), bool)
rr, cc = pix // NC, pix % NC
for i, f in enumerate(files):
    with h5py.File(disp / f, "r") as h:
        d = h["displacement"][()]
        D[i] = d[rr, cc] * 1000.0
        V[i] = (h["recommended_mask"][()][rr, cc] == 1) & (h["water_mask"][()][rr, cc] == 1) & np.isfinite(d[rr, cc])
        lab = h["connected_component_labels"][()]
        L[i] = (lab[rr, cc] > 0) & (lab[rr, cc] == prod.main_label[i])
Dw, Vw, good = chain(D, V, L)
coef = fit(Dw, Vw, good)
X = np.c_[np.ones_like(t), t, np.sin(OMEGA * t), np.cos(OMEGA * t)]
step = {}
k0 = 0
for name, pp in groups.items():
    rows = []
    for j in range(k0, k0 + len(pp)):
        m = Vw[:, j]
        y = Dw[m, j].astype(float)
        jumps = np.abs(np.diff(y))
        resid = y - X[m] @ coef[j] if good[j] else np.full(m.sum(), np.nan)
        kmax = int(np.argmax(jumps))
        rows.append(dict(pixel=int(pix[j]), good=bool(good[j]), v=float(coef[j, 1] * 365.25), max_jump_mm=float(jumps.max()),
                         max_jump_between=[str(pd.Timestamp(W0 + pd.Timedelta(days=float(t[m][kmax]))).date()),
                                           str(pd.Timestamp(W0 + pd.Timedelta(days=float(t[m][kmax + 1]))).date())],
                         jumps_over_14mm=int((jumps > 14).sum()), resid_sd_mm=float(np.nanstd(resid)),
                         first_half_v=float(np.polyfit(t[m][t[m] < t[-1] / 2], y[t[m] < t[-1] / 2], 1)[0] * 365.25),
                         second_half_v=float(np.polyfit(t[m][t[m] >= t[-1] / 2], y[t[m] >= t[-1] / 2], 1)[0] * 365.25)))
    k0 += len(pp)
    step[name] = rows
R["step_test"] = step
np.savez(Path(str(out).replace(".json", "_series.npz")), t=t, D=Dw, V=Vw, pixel=pix,
         group=np.repeat(list(groups), [len(p) for p in groups.values()]))

# ---- 2. sign from clay seasonality
hs = np.load(res / "house_series.npz")
Dw, Vw, good = chain(hs["displacement_mm"], hs["valid"], hs["label_ok"])
Fv = F["v"].ravel()[hp]
assert (good == F["good"].ravel()[hp]).all()
Xg = np.c_[np.ones_like(t), t, np.sin(OMEGA * t), np.cos(OMEGA * t)]
W = Vw[:, good].astype(np.float64)
A = (W.T @ (Xg[:, :, None] * Xg[:, None, :]).reshape(len(t), 16)).reshape(-1, 4, 4)
b = (W * np.where(Vw[:, good], Dw[:, good], 0.0)).T @ Xg
cf = np.full((len(hp), 4), np.nan)
cf[good] = np.linalg.solve(A, b[..., None])[:, :, 0]
assert np.allclose(cf[good, 1] * 365.25, Fv[good], atol=1e-3)
lep = np.load(lep_npz)["lep_0_150"]
house = z["house_pixel"]
B_, C_ = cf[house, 2], cf[house, 3]
use = np.isfinite(B_) & np.isfinite(lep)
hi, lo = use & (lep >= 6.0), use & (lep < 3.0)
pi, pj = z["pix_i"][house], z["pix_j"][house]
block = np.unique(np.floor((pi * 30 + 15) / 2000).astype(np.int64) * 1_000_000 + np.floor((pj * 30 + 15) / 2000).astype(np.int64),
                  return_inverse=True)[1]


def extremes(db, dc):
    """Calendar month (1-12) and day of year of the trough and peak of db sin(wt) + dc cos(wt), t from W0."""
    phi = np.arctan2(db, dc)  # curve = amp cos(wt - phi): peak at wt = phi
    t_peak = (phi / OMEGA) % 365.25
    t_trough = (t_peak + 365.25 / 2) % 365.25
    doy = lambda tt: int(round((W0.dayofyear - 1 + tt) % 365.25)) + 1  # noqa: E731
    month = lambda tt: int((W0 + pd.Timedelta(days=float(tt))).month)  # noqa: E731
    return dict(peak_month=month(t_peak), peak_day_of_year=doy(t_peak), trough_month=month(t_trough),
                trough_day_of_year=doy(t_trough), amplitude_mm=float(np.hypot(db, dc)))


def group_diff(idx):
    h, l_ = idx[hi[idx]], idx[lo[idx]]
    return B_[h].mean() - B_[l_].mean(), C_[h].mean() - C_[l_].mean()


allidx = np.arange(len(house))
db, dc = group_diff(allidx)
R["clay_seasonality"] = dict(
    parcels_high_or_very_high=int(hi.sum()), parcels_low=int(lo.sum()),
    high_minus_low=extremes(db, dc),
    high=extremes(B_[hi].mean(), C_[hi].mean()), low=extremes(B_[lo].mean(), C_[lo].mean()))
members = pd.Series(allidx).groupby(block).apply(np.asarray).to_list()
boot = []
for _ in range(500):
    idx = np.concatenate([members[k] for k in rng.integers(0, len(members), len(members))])
    boot.append(extremes(*group_diff(idx))["trough_day_of_year"])
boot = np.array(boot)
centre = R["clay_seasonality"]["high_minus_low"]["trough_day_of_year"]
off = ((boot - centre + 182) % 365) - 182  # circular offsets from the point estimate
R["clay_seasonality"]["trough_day_of_year_interval_95"] = [int((centre + np.percentile(off, 2.5)) % 365),
                                                           int((centre + np.percentile(off, 97.5)) % 365)]
out.write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps(R["clay_seasonality"], indent=1))
for name, rows in step.items():
    print(name, [(round(r["v"], 1), round(r["max_jump_mm"], 1), r["jumps_over_14mm"], round(r["resid_sd_mm"], 1),
                  round(r["first_half_v"], 1), round(r["second_half_v"], 1)) for r in rows])
