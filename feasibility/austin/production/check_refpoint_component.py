"""Which connected component holds the frame's reference point? (§14 entry of 2026-11-11, connected-component rule.)

The frozen rule (NYC §7 step 3) compares each pixel's label with the label at the frame's reference point. That label
is 0 in every granule (production/i03_download_refpoint.py), so the §14 rule uses the city's main component instead:
the most common non-zero label among pixels whose centre lies inside the full-purpose boundary. This check asks
whether the two name the same component, by reading, for each of the 254 products:
  - the label at the reference point and the most common non-zero label in the 11 x 11 window around it (from the
    subset file when the point lies inside the subset, otherwise from i03's window file);
  - the city's main component, computed here from the subset file and insar_inputs.npz (inside_city).
No displacement is read. Runs on the project PC (the reference-point windows are there).
Usage: OPERA_PYTHON -I check_refpoint_component.py OPERA_DIR INSAR_INPUTS_NPZ OUT_DIR
"""
import hashlib
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

opera, inputs, out = map(Path, sys.argv[1:4])
HALF = 5


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


inside = np.load(inputs)["inside_city"]
pts = pd.read_csv(opera / "reference_points.csv")
with h5py.File(opera / "disp" / pts.file[0], "r") as h:
    x, y = h["x"][()], h["y"][()]
grid = json.loads((Path(__file__).resolve().parents[1] / "checkpoint1" / "frame_grid_folds.json").read_text())["frame_grid"]
r0, c0 = int(round((grid["ymax"] - y[0] - 15) / 30)), int(round((x[0] - grid["xmin"] - 15) / 30))
assert inside.shape == (len(y), len(x))
rows = []
for _, g in pts.iterrows():
    with h5py.File(opera / "disp" / g.file, "r") as h:
        cc = h["connected_component_labels"][()]
        if g.inside_subset:
            r, c = g.ref_row - r0, g.ref_col - c0
            w = cc[r - HALF:r + HALF + 1, c - HALF:c + HALF + 1]
    if not g.inside_subset:
        f = sorted((opera / "refpoint").glob(g.file[:-3] + "*"))
        assert len(f) == 1, g.file
        with h5py.File(f[0], "r") as h:
            w = h["connected_component_labels"][()]
    assert w.shape == (2 * HALF + 1, 2 * HALF + 1)
    nz = w[w > 0].astype(np.int64)
    near = int(np.bincount(nz).argmax()) if nz.size else -1
    ci = cc[inside]
    labs, cnt = np.unique(ci[ci > 0], return_counts=True)
    main = int(labs[cnt.argmax()])
    rows.append(dict(file=g.file, reference_date=g.reference_date, secondary_date=g.secondary_date,
                     inside_subset=bool(g.inside_subset), label_at_point=int(w[HALF, HALF]),
                     window_main_label=near, window_share=float((w == near).mean()), city_main_label=main,
                     city_share=float((ci == main).mean()), same=near == main))
d = pd.DataFrame(rows)
out.mkdir(parents=True, exist_ok=True)
d.to_csv(out / "refpoint_component.csv", index=False)
R = dict(inputs={p.name: sha256(p) for p in (opera / "reference_points.csv", opera / "refpoint" / "MANIFEST.sha256", inputs)},
         products=len(d), label_zero_at_point=int((d.label_at_point == 0).sum()),
         point_inside_subset=int(d.inside_subset.sum()),
         window_label_equals_city_main=int(d.same.sum()),
         window_share_min=float(d.window_share.min()),
         city_main_not_1={r.file[30:65]: r.city_main_label for r in d.itertuples() if r.city_main_label != 1},
         csv_sha256=sha256(out / "refpoint_component.csv"))
(out / "refpoint_component.json").write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps(R, indent=1))
