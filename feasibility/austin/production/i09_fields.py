"""Test A field files (AUSTIN_PLAN.md §7 indicators, §12 secondaries) in the format fixed by testa_core.save_field.
Outcome-blind: only prop_id and complete_b1 (features) and prop_id, pix_i, pix_j (grid) are read; no event,
outcome, fold or block column.

Every field is (88 study months 2018-08 .. 2025-11, the eligible-house pixels in testa_core.Geometry order), NaN where
the pixel has no value for the month's window. Sources are the i08 outputs (I08_OUT/L24.npz, L12.npz, L36.npz):
  v            trend velocity, 24-month window ending before the month (primary, §7 indicator 1)
  amp          seasonal amplitude sqrt(b^2 + c^2), mm, same window (indicator 2; secondary 6)
  lrm          local relative motion: v minus the median v of the valid pixels 60-250 m from the pixel's centre
               (indicator 3; secondary 6)
  acc          acceleration: v of the 12 months before the month minus v of the 12 months before those
               (indicator 4; secondary 6), each half with its own window rules
  v_nomask     v without the construction mask (secondary 13)
  avail        the number of valid pixels within 100 m of the pixel's centre, itself included (secondary 12);
               a count, never NaN
  v12          trend velocity, 12-month window (secondary 3)
  v36          trend velocity, 36-month window; NaN before 2019-08 (secondary 3, events from 2019-08)
  v_lag1, v_lag3, v_lag6, v_lag12
               the 24-month window ending 1, 3, 6 or 12 months earlier (secondary 9); NaN where that window would
               start before the first granule (2016-07-10), i.e. where the month minus the lag is before 2018-08
Writes OUT/field_<name>.npz (save_field) and OUT/fields.json (sources, hashes, valid-pixel counts per field), and
reads each file back with testa_core.load_field.
Usage: .venv/bin/python -I i09_fields.py FEATURES_PARQUET GRID_PARQUET I08_OUT OUT
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "planted_signal"))
import testa_core as C  # noqa: E402

LAGS = (1, 3, 6, 12)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


features, grid, src, out = map(Path, sys.argv[1:5])
rec = Path(__file__).resolve().parents[1] / "checkpoint1"
want = {"features": json.loads((rec / "features_2018.json").read_text())["private_outputs_sha256"]["features_2018.parquet"],
        "grid": json.loads((rec / "frame_grid_folds.json").read_text())["private_outputs_sha256"]["eligible_grid_folds.parquet"]}
assert sha256(features) == want["features"] and sha256(grid) == want["grid"]
out.mkdir(parents=True, exist_ok=False)
f = pd.read_parquet(features, columns=["prop_id", "complete_b1"])
g = pd.read_parquet(grid, columns=["prop_id", "pix_i", "pix_j"])
assert (f.prop_id.to_numpy() == g.prop_id.to_numpy()).all()
geo = C.Geometry(pd.DataFrame({"pix_i": g.pix_i, "pix_j": g.pix_j, "complete_b1": f.complete_b1}))

F = {}
for fam in ("L24", "L12", "L36"):
    with np.load(src / f"{fam}.npz", allow_pickle=False) as z:
        assert np.array_equal(z["pix_i"], geo.pix_i) and np.array_equal(z["pix_j"], geo.pix_j)
        F[fam] = {k: np.asarray(z[k]) for k in z.files}
        F[fam]["months"] = [str(m) for m in z["months"]]


def at(fam, key, months):
    """Rows of family `fam`, field `key`, for the given months (NaN rows for months the family does not have)."""
    pos = {m: k for k, m in enumerate(F[fam]["months"])}
    a = F[fam][key]
    return np.stack([a[pos[m]].astype(np.float64) if m in pos else np.full(a.shape[1], np.nan) for m in months])


M = C.MONTHS
shift = lambda k: [str(pd.Period(m, "M") - k) for m in M]  # noqa: E731
assert F["L24"]["months"] == M and F["L12"]["months"][0] == shift(12)[0] and F["L36"]["months"][0] == "2019-08"
fields = {
    "v": (at("L24", "v", M), "L24 v"),
    "amp": (at("L24", "amp", M), "L24 amp"),
    "lrm": (at("L24", "lrm", M), "L24 lrm"),
    "acc": (at("L12", "v", M) - at("L12", "v", shift(12)), "L12 v at m minus L12 v at m-12"),
    "v_nomask": (at("L24", "v_nomask", M), "L24 v_nomask"),
    "avail": (at("L24", "avail", M), "L24 avail"),
    "v12": (at("L12", "v", M), "L12 v"),
    "v36": (at("L36", "v", M), "L36 v"),
    **{f"v_lag{k}": (at("L24", "v", shift(k)), f"L24 v at m-{k}") for k in LAGS},
}
assert np.isfinite(fields["avail"][0]).all()
R = dict(inputs={"features": sha256(features), "grid": sha256(grid), "i08_run": sha256(src / "run.json"),
                 **{f"{fam}.npz": sha256(src / f"{fam}.npz") for fam in ("L24", "L12", "L36")}},
         testa_core=sha256(Path(C.__file__)), pixels=len(geo.pix_i), months=[M[0], M[-1], len(M)], fields={})
for name, (v, how) in fields.items():
    p = out / f"field_{name}.npz"
    C.save_field(p, v, geo, meta=dict(field=name, source=how, i08_run_sha256=R["inputs"]["i08_run"]))
    back = C.load_field(p, geo)
    assert np.array_equal(back, v, equal_nan=True)
    n = np.isfinite(v).sum(1)
    R["fields"][name] = dict(source=how, sha256=sha256(p), months_with_values=int((n > 0).sum()),
                             valid_pixels_min=int(n[n > 0].min()), valid_pixels_median=float(np.median(n[n > 0])),
                             valid_pixels_max=int(n.max()))
(out / "fields.json").write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps({k: (v["months_with_values"], v["valid_pixels_median"]) for k, v in R["fields"].items()}, indent=1))
