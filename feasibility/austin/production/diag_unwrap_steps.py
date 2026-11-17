"""How common are lasting steps of about one phase cycle at the house pixels? (Diagnostic after the sign check came out
"not below", AUSTIN_PLAN.md §7.) Outcome-blind: reads only i08's house_series.npz, products.csv and full.npz, and the
pixel grid. Changes nothing; it describes.

At the two active landfills with valid pixels, the full-period series relative to the city shows two lasting steps
of +28.5 and +24.3 mm (2019-11, 2021-01), close to half the C-band wavelength (27.7 mm): the signature of a
phase-unwrapping cycle slip, which the re-referencing chain then carries forward. This script looks for such steps
at every house pixel valid for the full period.
  - Series: i08's full-period chain at the house pixels (opera-utils rebase_timeseries), minus the city's common mode
    (the median over valid house pixels at each epoch).
  - Step at epoch k: the mean of the next HALF valid epochs minus the mean of the previous HALF (k included), counted
    if its size is at least 20 mm and the change from epoch k to k+1 alone is at least 20 mm. Within HALF epochs only
    the largest is kept.
  - Reported: the share of valid house pixels with at least one step; the step sizes (a peak near +-27.7 mm marks
    cycle slips; atmospheric noise gives no peak); the epochs where steps fall and whether they coincide with a
    reference change; the 2 km blocks (pixel centre) with the most stepped pixels; and the full-period velocity of
    stepped and unstepped pixels.
Run with HALF = 4 and HALF = 15 (about 6 months each side, so that episodes lasting weeks are not counted).
Usage: OPERA_PYTHON -I diag_unwrap_steps.py I08_OUT INSAR_INPUTS_NPZ OUT_JSON [HALF]
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from opera_utils.disp import rebase_timeseries

res, inputs, out = map(Path, sys.argv[1:4])
MIN_STEP, HALF = 20.0, int(sys.argv[4]) if len(sys.argv) > 4 else 4
z = np.load(inputs)
prod = pd.read_csv(res / "products.csv", parse_dates=["ref", "sec"])
W0 = prod.ref.min()
refs = list(prod.ref)
cross = [k for k in range(len(prod) - 1) if prod.ref[k + 1] != prod.ref[k]]
t = np.r_[0.0, (prod.sec - W0).dt.days.to_numpy(float)]
dates = np.r_[np.datetime64(W0.date()), prod.sec.values.astype("datetime64[D]")]
hs = np.load(res / "house_series.npz")
D, V, L = hs["displacement_mm"], hs["valid"], hs["label_ok"]
reb = rebase_timeseries(np.where(V, D, np.nan).astype(np.float32), refs)
Dw = np.vstack([np.zeros((1, D.shape[1]), np.float32), reb]).astype(np.float64)
Vw = np.vstack([np.ones((1, D.shape[1]), bool), V & np.isfinite(reb)])
F = np.load(res / "full.npz")
NC = F["v"].shape[1]
hp = z["r"] * NC + z["c"]
good = F["good"].ravel()[hp]
vfull = F["v"].ravel()[hp]
Dw[~Vw] = np.nan
Dw[:, ~good] = np.nan
common = np.nanmedian(Dw[:, good], axis=1)
Rel = Dw - common[:, None]

n_ep, P = Rel.shape
steps = []  # (pixel, epoch k, step size, single jump)
for p in np.flatnonzero(good):
    s = Rel[:, p]
    ok = np.flatnonzero(np.isfinite(s))
    y = s[ok]
    if len(y) < 2 * HALF + 1:
        continue
    cs = np.r_[0.0, np.cumsum(y)]
    k = np.arange(HALF - 1, len(y) - HALF)
    before = (cs[k + 1] - cs[k + 1 - HALF]) / HALF
    after = (cs[k + 1 + HALF] - cs[k + 1]) / HALF
    st, jump = after - before, y[k + 1] - y[k]
    cand = np.flatnonzero((np.abs(st) >= MIN_STEP) & (np.abs(jump) >= MIN_STEP))
    kept = []
    for i in cand[np.argsort(-np.abs(st[cand]))]:
        if any(abs(i - j) < HALF for j in kept):
            continue
        steps.append((p, int(ok[k[i]]), int(ok[k[i] + 1]), float(st[i]), float(jump[i])))
        kept.append(i)
S = pd.DataFrame(steps, columns=["pixel", "epoch", "epoch_to", "step", "jump"])
R = dict(house_pixels=int(len(hp)), valid_full_period=int(good.sum()), min_step_mm=MIN_STEP, half_window_epochs=HALF,
         common_mode_sd_about_trend_mm=float(np.std(common - np.polyval(np.polyfit(t, common, 1), t))),
         relative_resid_sd_median_mm=float(np.nanmedian(np.nanstd(Rel[:, good] - np.nanmean(Rel[:, good], 0), 0))))
pix_with = S.pixel.unique()
R["pixels_with_a_step"] = int(len(pix_with))
R["share_with_a_step"] = float(len(pix_with) / good.sum())
R["houses_on_stepped_pixels"] = int(np.isin(z["house_pixel"], pix_with).sum())
hist, edges = np.histogram(np.abs(S.step), bins=np.arange(20, 82, 4))
R["step_size_histogram_abs_mm"] = {f"{int(a)}-{int(b)}": int(n) for a, b, n in zip(edges[:-1], edges[1:], hist)}
R["steps"] = int(len(S))
R["steps_positive"] = int((S.step > 0).sum())
cross_epochs = set(int(k) + 1 for k in cross)  # epoch index (epoch 0 = first reference date) of each crossing product
S["date_from"] = dates[S.epoch.to_numpy()].astype(str)
S["date_to"] = dates[S.epoch_to.to_numpy()].astype(str)
S["at_reference_change"] = S.epoch.isin(cross_epochs)  # the jump is from a crossing product to the next ministack
R["steps_at_reference_change"] = int(S.at_reference_change.sum())
top = S.groupby(["date_from", "date_to"]).size().sort_values(ascending=False).head(12)
R["most_common_step_dates"] = {f"{a} -> {b}": int(n) for (a, b), n in top.items()}
pi, pj = z["pix_i"], z["pix_j"]
blk = (np.floor((pi * 30 + 15) / 2000).astype(int) * 1000 + np.floor((pj * 30 + 15) / 2000).astype(int))
stepped = np.isin(np.arange(len(hp)), pix_with)
tb = pd.DataFrame({"block": blk, "good": good, "stepped": stepped}).groupby("block").agg(valid=("good", "sum"), stepped=("stepped", "sum"))
tb["share"] = tb.stepped / tb.valid.clip(lower=1)
tb = tb[tb.valid >= 100].sort_values("share", ascending=False)
R["blocks_with_100_valid_pixels"] = int(len(tb))
R["block_share_quantiles"] = {str(q): float(tb.share.quantile(q)) for q in (0.5, 0.9, 0.99, 1.0)}
R["top_blocks"] = [dict(block_x_km=int(b // 1000) * 2, block_y_km=int(b % 1000) * 2, valid=int(r.valid), stepped=int(r.stepped),
                        share=round(float(r.share), 3)) for b, r in tb.head(10).iterrows()]
R["full_period_v_median"] = dict(stepped=float(np.median(vfull[stepped & good])), unstepped=float(np.median(vfull[~stepped & good])))
S.to_csv(Path(str(out).replace(".json", ".csv.gz")), index=False)
out.write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps(R, indent=1))
