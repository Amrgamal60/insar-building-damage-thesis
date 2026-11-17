"""Acceptance check of deep_field.build_field (AUSTIN_PLAN.md §12 item 20; outcome-blind).

For every pixel and 24-month window (the 88 Test A windows) where the Test A field has a velocity, the §7 trend model
(i08's fit_coef, copied unchanged) is refitted on the built field's valid acquisitions in [W0, te) and its velocity is
compared with the field's. Agreement to rounding shows that chain, validity, dates and pixel order match i08 for
every value Test A uses. Pixels carried across a broken link are reported separately.
Usage: python -I check_deep_field.py HOUSE_SERIES FIELD_V OUT.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deep_field as DF  # noqa: E402


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


def main(series, field_v, out):
    with np.load(field_v, allow_pickle=False) as z:
        months, pix_i, pix_j, v = list(z["months"]), z["pix_i"], z["pix_j"], np.asarray(z["v"], np.float64)
    dates, field, info = DF.build_field(series, pix_i, pix_j)
    valid = np.isfinite(field)
    with np.load(series, allow_pickle=False) as z:
        Vz, sec, ref = z["valid"], z["secondary"].astype("datetime64[D]"), z["reference"]
    links = [int(np.flatnonzero(sec == r)[0]) for r in np.unique(ref) if (sec == r).any()]
    carried = (~Vz[links]).any(0)
    diffs, n_cmp, n_unfit, worst = [], 0, 0, None
    n_cmp_carried, max_carried = 0, 0.0
    for w, m in enumerate(months):
        te = pd.Timestamp(m + "-01")
        W0 = te - pd.DateOffset(months=24)
        rows = np.flatnonzero((dates >= np.datetime64(W0)) & (dates < np.datetime64(te)))
        t = ((dates[rows] - np.datetime64(W0)).astype("timedelta64[D]").astype(np.int64)).astype(float)
        have = np.flatnonzero(np.isfinite(v[w]))
        coef = fit_coef(field[rows][:, have], valid[rows][:, have], t)
        mine = coef[:, 1] * 365.25
        d = np.abs(mine - v[w, have])
        n_unfit += int((~np.isfinite(mine)).sum())
        d = np.where(np.isfinite(d), d, np.inf)
        n_cmp += len(have)
        diffs.append(float(d.max()))
        c = carried[have]
        if c.any():
            n_cmp_carried += int(c.sum())
            max_carried = max(max_carried, float(d[c].max()))
        if worst is None or d.max() > worst[0]:
            k = int(np.argmax(d))
            worst = (float(d.max()), m, int(have[k]), float(v[w, have[k]]), float(mine[k]))
    R = dict(field_info=info, field_v=str(field_v), field_v_sha256=DF.sha256(field_v), windows=len(months),
             pixel_windows_compared=n_cmp, pixel_windows_not_fitted=n_unfit,
             max_abs_diff_mm_per_yr=max(diffs), max_abs_diff_per_window=diffs,
             carried_pixels=int(carried.sum()), carried_pixel_windows_compared=n_cmp_carried,
             carried_max_abs_diff_mm_per_yr=max_carried,
             worst=dict(diff=worst[0], month=worst[1], pixel=worst[2], field_v=worst[3], refit=worst[4]))
    R["pass"] = bool(n_unfit == 0 and R["max_abs_diff_mm_per_yr"] < 1e-3)
    Path(out).write_text(json.dumps(R, indent=1) + "\n")
    print(json.dumps({k: R[k] for k in R if k != "max_abs_diff_per_window"}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
