"""Test B cell fields (AUSTIN_PLAN.md §7 "Cell value (Test B)", §8B, §10 Test B, §12 items 15-17 and 19, §14 slip entry).
Outcome-blind: from the grid table only prop_id, pix_i, pix_j, cell250_x, cell250_y and cell250 are read; no event,
outcome, fold or block column. No count y and no exposure n is built here (they need the events).

Cells: the UTM 14N 250 m cells (edges at multiples of 250 m) holding at least one eligible parcel point, as built at
checkpoint 1 (cell250 = floor(x / 250), floor(y / 250) of the parcel point). Order: cell250_x, then cell250_y.
Parcel value: the value of the parcel's pixel (i08 outputs, one row per eligible-house pixel, testa_core.Geometry order).
Cell value: the mean of the parcel values of its eligible parcels with a value (each parcel once, so a pixel shared by
k parcels counts k times), NaN when fewer than 3 parcels have a value in that window. All eligible parcels count,
whether or not their Baseline 1 inputs are complete (§7 names no completeness rule for cells).

Quarters (§7, option A): the 28 complete quarters 2018-Q4 .. 2025-Q3. A quarter's window is the 12 months ending the
day before the quarter starts, which is i08's L12 window of the quarter's first month ([m - 12 months, m)).
Fields (quarters x cells unless stated):
  v          L12 v at the quarter start (primary), from the corrected run (I08_OUT)
  v_run1     the same from the first run, without the slip rule (§14 added sensitivity analysis), from I08_RUN1
  v_lag1, v_lag3, v_lag6, v_lag12   L12 v at the quarter start minus 1, 3, 6 or 12 months (secondary 15)
  v24        L24 v at the quarter start (secondary 16)
  amp, lrm   L12 seasonal amplitude and local relative motion at the quarter start (secondary 17)
  acc        per parcel L12 v at the quarter start minus L12 v 12 months earlier, then the cell mean (secondary 17)
  v_monthly  L12 v at each of the 88 study months 2018-08 .. 2025-11 (months x cells; secondary 19)
Block of a cell (for Test B's clustered errors, §9): the 2 km block of the UTM 14N grid (edges at multiples of 2,000 m)
that contains the cell. A 250 m cell lies in exactly one such block, so the block is a property of the cell. This is the
authors' choice: the checkpoint-1 house blocks are assigned by pixel centre, and 931 houses' points lie in another
block than their pixels', so a cell's houses can carry two house blocks, which test_b.fit_panel rejects.
Writes OUT/testb_cells.npz and OUT/testb_cells.json (hashes, counts per field).
Usage: .venv/bin/python -I i12_testb_cells.py GRID_PARQUET I08_OUT I08_RUN1 OUT
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "planted_signal"))
import testa_core as C  # noqa: E402

MIN_PARCELS = 3
QUARTERS = pd.period_range("2018Q4", "2025Q3", freq="Q")
LAGS = (1, 3, 6, 12)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


grid, src, run1, out = map(Path, sys.argv[1:5])
rec = Path(__file__).resolve().parents[1] / "checkpoint1"
assert sha256(grid) == json.loads((rec / "frame_grid_folds.json").read_text())["private_outputs_sha256"]["eligible_grid_folds.parquet"]
out.mkdir(parents=True, exist_ok=False)
g = pd.read_parquet(grid, columns=["prop_id", "pix_i", "pix_j", "cell250_x", "cell250_y", "cell250"])
assert g.prop_id.is_unique and g.prop_id.is_monotonic_increasing and len(g) == 149_316
geo = C.Geometry(pd.DataFrame({"pix_i": g.pix_i, "pix_j": g.pix_j, "complete_b1": np.ones(len(g), bool)}))

cx, cy = g.cell250_x.to_numpy(np.int64), g.cell250_y.to_numpy(np.int64)
assert (g.cell250.to_numpy() == np.char.add(np.char.add(cx.astype(str), "_"), cy.astype(str))).all()
key = cx * C.KEY + cy
ukey, house_cell = np.unique(key, return_inverse=True)  # sorted by cell250_x, then cell250_y
n_cells = len(ukey)
cell_x, cell_y = ukey // C.KEY, ukey % C.KEY
labels = np.char.add(np.char.add(cell_x.astype(str), "_"), cell_y.astype(str))
houses = np.bincount(house_cell, minlength=n_cells)
block = np.char.add(np.char.add((cell_x // 8).astype(str), "_"), (cell_y // 8).astype(str))  # 8 x 250 m = 2 km
assert ((cell_x * 250) // 2000 == cell_x // 8).all() and (((cell_x + 1) * 250 - 1) // 2000 == cell_x // 8).all()


def load(folder, fam):
    with np.load(folder / f"{fam}.npz", allow_pickle=False) as z:
        assert np.array_equal(z["pix_i"], geo.pix_i) and np.array_equal(z["pix_j"], geo.pix_j)
        return {k: np.asarray(z[k]) for k in z.files}


F = {"L12": load(src, "L12"), "L24": load(src, "L24"), "L12_run1": load(run1, "L12")}


def rows(fam, key_, months):
    pos = {str(m): k for k, m in enumerate(F[fam]["months"])}
    return np.stack([F[fam][key_][pos[str(m)]].astype(np.float64) for m in months])  # KeyError if a month is missing


def cell_mean(pixel_values):
    """(W, house pixels) -> (W, cells): mean over parcels with a value, NaN below MIN_PARCELS parcels."""
    par = pixel_values[:, geo.house_pixel]  # (W, parcels)
    ok = np.isfinite(par)
    out_ = np.full((len(par), n_cells), np.nan)
    for w in range(len(par)):
        n = np.bincount(house_cell[ok[w]], minlength=n_cells)
        s = np.bincount(house_cell[ok[w]], weights=par[w, ok[w]], minlength=n_cells)
        out_[w] = np.where(n >= MIN_PARCELS, s / np.maximum(n, 1), np.nan)
    return out_


start = [q.asfreq("M", how="start") for q in QUARTERS]
assert len(QUARTERS) == 28 and str(start[0]) == "2018-10" and str(start[-1]) == "2025-07"
shift = lambda ms, k: [m - k for m in ms]  # noqa: E731
M = [pd.Period(m, "M") for m in C.MONTHS]
fields = {
    "v": (cell_mean(rows("L12", "v", start)), "L12 v at the quarter start"),
    "v_run1": (cell_mean(rows("L12_run1", "v", start)), "first-run L12 v at the quarter start"),
    **{f"v_lag{k}": (cell_mean(rows("L12", "v", shift(start, k))), f"L12 v at the quarter start minus {k} months") for k in LAGS},
    "v24": (cell_mean(rows("L24", "v", start)), "L24 v at the quarter start"),
    "amp": (cell_mean(rows("L12", "amp", start)), "L12 amp at the quarter start"),
    "lrm": (cell_mean(rows("L12", "lrm", start)), "L12 lrm at the quarter start"),
    "acc": (cell_mean(rows("L12", "v", start) - rows("L12", "v", shift(start, 12))), "L12 v at the quarter start minus 12 months earlier, per parcel"),
    "v_monthly": (cell_mean(rows("L12", "v", M)), "L12 v at each study month (months x cells)"),
}
np.savez(out / "testb_cells.npz", cells=labels, cell_x=cell_x, cell_y=cell_y,
         xy=np.column_stack([cell_x * 250.0 + 125.0, cell_y * 250.0 + 125.0]), block=block, houses=houses,
         quarters=np.array([str(q) for q in QUARTERS]), quarter_start=np.array([str(m) for m in start]),
         months=np.array(C.MONTHS), **{k: v for k, (v, _) in fields.items()})
with np.load(out / "testb_cells.npz", allow_pickle=False) as z:  # read back
    for k, (v, _) in fields.items():
        assert np.array_equal(z[k], v, equal_nan=True)
R = dict(inputs={"grid": sha256(grid), "i08_run": sha256(src / "run.json"), "L12.npz": sha256(src / "L12.npz"),
                 "L24.npz": sha256(src / "L24.npz"), "i08_run1_run": sha256(run1 / "run.json"),
                 "run1_L12.npz": sha256(run1 / "L12.npz")},
         testa_core=sha256(Path(C.__file__)), parcels=len(g), cells=int(n_cells),
         cells_with_3_or_more_parcels=int((houses >= MIN_PARCELS).sum()),
         parcels_per_cell_median=float(np.median(houses)), blocks=int(len(np.unique(block))),
         quarters=[str(QUARTERS[0]), str(QUARTERS[-1]), len(QUARTERS)], output_sha256=sha256(out / "testb_cells.npz"),
         fields={})
for k, (v, how) in fields.items():
    n = np.isfinite(v).sum(1)
    R["fields"][k] = dict(source=how, rows=int(len(v)), cells_with_a_value_in_any_row=int(np.isfinite(v).any(0).sum()),
                          cells_with_value_min=int(n.min()), cells_with_value_median=float(np.median(n)),
                          cells_with_value_max=int(n.max()), median_value=float(np.nanmedian(v)))
(out / "testb_cells.json").write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps({k: (v["cells_with_a_value_in_any_row"], v["cells_with_value_median"]) for k, v in R["fields"].items()}, indent=1))
print(R["cells"], R["cells_with_3_or_more_parcels"], R["blocks"])
