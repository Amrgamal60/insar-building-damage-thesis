"""Secondary 11 of ALEX_RETEST_PLAN.md (frozen 2026-11-18): persistence. P3 (2019-01-01 to the last epoch, made by
scripts/run_p3.sh) against P1 on the 241 primary cells. Descriptive only (no null, no p-value), as §10 says.

Cell value = mean of the valid P3 vertical pixels whose centres fall in the cell (the rule of 16_licsar_cells.py and
retest_core.PixelField). Reported: cells and pixels with P3; Spearman and Pearson correlation of P1 and P3 over cells
(and over pixels present in both); medians for collapse and background cells; and, on the cells with both values,
T and beta-hat of P3 and of P1 (descriptive; the original fold assignments restricted to those cells).

Usage: python -I scripts/p3_compare.py --out secondary_real
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retest_core as R  # noqa: E402
import run_secondaries as RS  # noqa: E402

P3_TIF = R.ROOT / "data/licsbas/decomposed/P3_UD.geo.tif"


def cell_means(c, tif):
    x, y, v = R.L16.pixels(tif)
    tr = RS.grid_origin(c, R.RES)
    r, cc = R.P.rowcol(tr, R.RES, x, y)
    cell = pd.Index(c.row * 100_000 + c.col).get_indexer(r * 100_000 + cc)
    k = cell >= 0
    n = np.bincount(cell[k], minlength=len(c))
    s = np.bincount(cell[k], weights=v[k], minlength=len(c))
    key = dict(zip(zip(x[k].round(6), y[k].round(6)), v[k]))
    return np.where(n > 0, s / np.maximum(n, 1), np.nan), n, key


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    RS.check_frozen()
    c, _, allc = R.load_cells()
    y, XB, v1 = c.positive.to_numpy(int), R.design(c), c[R.COL].to_numpy(float)
    v3, n3, pix3 = cell_means(c, P3_TIF)
    v1_check, n1, pix1 = cell_means(c, R.P1_TIF)
    assert np.allclose(v1_check, v1, rtol=0, atol=1e-9), "the P1 cell rule does not reproduce the cell values"
    both = np.isfinite(v3)
    common = sorted(set(pix1) & set(pix3))
    p1p = np.array([pix1[k] for k in common])
    p3p = np.array([pix3[k] for k in common])
    rows = np.flatnonzero(both)
    folds = R.fold_matrix(allc, c)[:, rows]
    desc = {}
    for name, vv in (("P3", v3), ("P1", v1)):
        st = R.Stat(XB[rows], y[rows], folds)
        o = st.of(vv[rows])
        desc[name] = dict(T=o["T"], dpr42=o["dpr42"], dpr_mean=o["dpr_mean"], beta_hat=R.beta_hat(XB[rows], y[rows], vv[rows]))
    out = dict(
        p3_tif_sha256=R.sha256(P3_TIF), p1_tif_sha256=R.sha256(R.P1_TIF), cells=int(len(c)), cells_with_p3=int(both.sum()),
        positives_with_p3=int(y[both].sum()), pixels_p3_in_cells=int(n3.sum()), pixels_p1_in_cells=int(n1.sum()),
        pixels_in_both=int(len(common)),
        spearman_cells=float(pd.Series(v1[both]).corr(pd.Series(v3[both]), method="spearman")),
        pearson_cells=float(np.corrcoef(v1[both], v3[both])[0, 1]),
        spearman_pixels=float(pd.Series(p1p).corr(pd.Series(p3p), method="spearman")),
        medians=dict(P1=dict(collapse=float(np.median(v1[both & (y == 1)])), background=float(np.median(v1[both & (y == 0)]))),
                     P3=dict(collapse=float(np.median(v3[both & (y == 1)])), background=float(np.median(v3[both & (y == 0)])))),
        descriptive_on_common_cells=desc, **R.hashes())
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "secondary_11_p3.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps({k: out[k] for k in out if k not in ("sources", "inputs")}, indent=1, default=float))


if __name__ == "__main__":
    main()
