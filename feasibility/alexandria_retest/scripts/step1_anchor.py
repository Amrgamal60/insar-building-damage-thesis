"""Step 1 of ALEX_RETEST_PLAN.md (§12): anchor, generating model, beta-hat and the pixel field.

Real outcomes are used only as §8 allows: (a) the anchor, with the original statistic and code only (seed-42
change in PR AUC and the original plain variogram-matching null draws); (b) the generating baseline model M0;
(c) beta-hat, the velocity coefficient of the original M1 refitted on all cells. The new statistic T and the new
nulls are NOT computed on real outcomes here.

Outputs (feasibility/alexandria_retest/step1/): generating_model.json, step1.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retest_core as R  # noqa: E402

OUT = R.RETEST / "step1"


def main():
    OUT.mkdir(exist_ok=True)
    H = R.hashes()
    c, f, allc = R.load_cells()
    y, XB, v = c.positive.to_numpy(int), R.design(c), c[R.COL].to_numpy(float)
    folds = R.fold_matrix(allc, c)
    assert np.array_equal(folds[0], c.fold.to_numpy()), "seed-42 fold map differs from the cells' saved folds"

    # (a) anchor: the original statistic, folds and plain variogram-matching null (seed 42 only)
    mb = R.S.metrics(y, R.S.oof(XB, y, folds[0], R.LR))["pr"]
    md = R.S.metrics(y, R.S.oof(np.c_[XB, v], y, folds[0], R.LR))["pr"]
    obs = md - mb
    orig = pd.read_csv(R.P.PILOT / "licsar_test_nulls.csv")
    orig = orig[(orig.test == "primary") & (orig.null == "Variogram-matching")].sort_values("draw").delta_pr.to_numpy()
    surr, _ = R.T17.surrogates(v, c[["x", "y"]].to_numpy(float), R.RES, 999)
    vm = surr["Variogram-matching"]
    null = np.array([R.S.metrics(y, R.S.oof(np.c_[XB, s], y, folds[0], R.LR))["pr"] - mb for s in vm])
    anchor = dict(baseline_pr=mb, velocity_pr=md, change=obs,
                  rounded=[round(mb, 3), round(md, 3), round(obs, 3)],
                  plain_null_max_abs_diff_vs_original=float(np.max(np.abs(null - orig))),
                  plain_null_p=(1 + int(np.sum(null >= obs - 1e-12))) / (1 + len(null)))
    assert anchor["rounded"] == [0.328, 0.413, 0.085], anchor
    assert anchor["plain_null_max_abs_diff_vs_original"] < 1e-12, anchor
    assert abs(anchor["plain_null_p"] - 0.005) < 1e-12, anchor

    # (b) generating model M0 on all 241 cells
    m0 = R.S.model(R.LR).fit(XB, y)
    gen = dict(columns=list(R.S.SET_B), scaler_mean=m0[0].mean_.tolist(), scaler_scale=m0[0].scale_.tolist(),
               coefficients_on_standardised_columns=m0[-1].coef_[0].tolist(), intercept=float(m0[-1].intercept_[0]),
               fitted_on="241 primary cells, real labels (32 positive), StandardScaler + LogisticRegression C=1",
               in_sample_roc_auc=float(roc_auc_score(y, m0.predict_proba(XB)[:, 1])),
               oof_seed42_roc_auc=float(roc_auc_score(y, R.S.oof(XB, y, folds[0], R.LR))))
    gpath = OUT / "generating_model.json"
    gpath.write_text(json.dumps(gen, indent=1) + "\n")

    # (c) beta-hat of the original M1 on all cells
    bh = R.beta_hat(XB, y, v)

    # pixel field (outcome-blind)
    px = R.PixelField(f)
    field = dict(field_cells=len(f), pixels=int(len(px.v)), pixels_per_cell_median=float(np.median(px.count)),
                 blocks_field=int(len(np.unique(px.block))), blocks_primary=int(c.block.nunique()),
                 positives_per_fold_seed42=[int(y[folds[0] == k].sum()) for k in range(5)],
                 cells_per_fold_seed42=[int((folds[0] == k).sum()) for k in range(5)],
                 min_positives_in_a_training_set=int(min(y[fo != k].sum() for fo in folds for k in range(5))),
                 min_positives_in_a_test_fold=int(min(y[fo == k].sum() for fo in folds for k in range(5))))

    rec = dict(step="step 1", plan="ALEX_RETEST_PLAN.md draft 2", anchor=anchor, generating_model_sha256=R.sha256(gpath),
               generating_model=dict(in_sample_roc_auc=gen["in_sample_roc_auc"], oof_seed42_roc_auc=gen["oof_seed42_roc_auc"]),
               beta_hat=bh, collapse_median=float(np.median(v[y == 1])), background_median=float(np.median(v[y == 0])),
               field=field, **H)
    (OUT / "step1.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: rec[k] for k in ("anchor", "generating_model", "beta_hat", "collapse_median", "background_median", "field")}, indent=1))


if __name__ == "__main__":
    main()
