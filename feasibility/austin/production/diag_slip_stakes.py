"""What do the lasting cycle slips (diag_unwrap_steps.py, 15-epoch windows) do to the Test A primary field?
Outcome-blind: reads the primary field (i09 field_v.npz), the slip table and the house-to-pixel map. Changes nothing.

For each 24-month window [m - 24 months, m) and each house pixel with a detected slip whose two epochs both lie in the
window (a slip before the window start only shifts the whole window's series and leaves v unchanged): counts the
house-window values affected, and places them in the window's distribution over all eligible houses with a value
(each house counted once, as the §7 standardisation): the share beyond the 0.5th and 99.5th percentiles (the
winsorising points) and the median percentile rank. Also: the windows touched, and how many house-window values a
mask of these pixel-windows would remove.
Usage: .venv/bin/python -I diag_slip_stakes.py FIELD_V_NPZ SLIPS_CSV_GZ INSAR_INPUTS_NPZ OUT_JSON
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

field, slips, inputs, out = map(Path, sys.argv[1:5])
F = np.load(field)
v, months = F["v"], [str(m) for m in F["months"]]
z = np.load(inputs)
w = np.bincount(z["house_pixel"], minlength=v.shape[1])  # houses per pixel
S = pd.read_csv(slips, parse_dates=["date_from", "date_to"])
aff = np.zeros(v.shape, bool)
for k, m in enumerate(months):
    p = pd.Period(m, "M")
    W0, te = (p - 24).start_time, p.start_time
    s = S[(S.date_from >= W0) & (S.date_to < te)]
    aff[k, s.pixel.unique()] = True
has = np.isfinite(v)
A = aff & has
lo_out = hi_out = 0
ranks = []
for k in range(len(months)):
    ok = has[k]
    vals, wt = v[k, ok], w[ok]
    order = np.argsort(vals)
    cw = np.cumsum(wt[order]) / wt.sum()
    q005, q995 = vals[order][np.searchsorted(cw, 0.005)], vals[order][np.searchsorted(cw, 0.995)]
    a = A[k]
    lo_out += int((w[a] * (v[k, a] < q005)).sum())
    hi_out += int((w[a] * (v[k, a] > q995)).sum())
    pos = np.searchsorted(vals[order], v[k, a]) / len(vals)
    ranks.extend(np.repeat(pos, w[a]))
n_aff = int((w[None, :] * A).sum())
R = dict(slips=int(len(S)), slip_pixels=int(S.pixel.nunique()),
         windows_touched=int(A.any(1).sum()), first_touched=months[int(np.argmax(A.any(1)))],
         last_touched=months[len(months) - 1 - int(np.argmax(A.any(1)[::-1]))],
         house_window_values_with_value=int((w[None, :] * has).sum()), house_window_values_affected=n_aff,
         share_affected=n_aff / int((w[None, :] * has).sum()),
         affected_houses_per_touched_window=dict(median=float(np.median((w[None, :] * A).sum(1)[A.any(1)])),
                                                 max=int((w[None, :] * A).sum(1).max())),
         affected_above_99_5=hi_out, affected_below_0_5=lo_out,
         share_affected_beyond_winsorising_points=(hi_out + lo_out) / max(n_aff, 1),
         affected_percentile_rank_quantiles={str(q): float(np.quantile(ranks, q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)})
out.write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps(R, indent=1))
