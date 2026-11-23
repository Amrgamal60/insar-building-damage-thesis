"""Primary analysis, decision and the 2 x 2 of ALEX_RETEST_PLAN.md (§5, §7, §10.1, §10.12).

Real outcomes are read only when the frozen plan exists and its SHA-256 equals FROZEN_SHA256 (filled in at freezing).
Before that, `--synthetic CELL DATASET` runs the same code on a planted dataset's labels (planted.draw_labels), for
checking; `--draws` and `--boot` may then be reduced.

Computed (all from the same fits where possible):
- T (mean over the 11 fold assignments of the out-of-fold log-likelihood gain), its 11 components, Δℓ per fold of
  seed 42, the seed-42 and mean changes in PR AUC, the seed-42 changes in ROC AUC and top-10% recall, beta-hat
  (per SD, per mm/yr, odds ratio), collapse and background medians.
- p of T and of the seed-42 change in PR AUC under: the primary null (chosen by the planted rule), the other linear
  conditional null, the unconditional pixel null (§10.12), and the six original cell-level nulls (§10.1; largest p).
- Refit block bootstrap (2,000 resamples of the 16 blocks, seed 2042; copies keep their block's fold in every
  assignment; resamples where an assignment leaves no positive among scored rows are skipped and counted).
- Leave-one-block-out T.
- The decision of §7 with the planted power at the observed effect (cell 7, primary null).
- Draft 4: the change in Brier score (seed 42 and mean of 11) and the calibration of M0 and M1's seed-42
  out-of-fold predictions (slope from y ~ a + b logit p; intercept in the large from y ~ a + offset(logit p)).
  Because the planted rule ended in branch 3, the primary null and its power at the observed effect come from
  `--null-choice` (step0/null_choice.json, the user's choice), whose planted-summary hash is asserted.
- Draft 4, user decision 2026-11-18 ("Freeze + qualifier"): secondary 14 (flexible baseline: planted_spline.spline_design,
  asserted byte-identical to the design of the planted check) under the primary null with the same draws, and the
  qualifier of §7: a robust decision is qualified when secondary 14 does not reject (T > 0, p < 0.05, beta-hat < 0).
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retest_core as R  # noqa: E402
import planted_spline as SP  # noqa: E402

FROZEN_PLAN = R.RETEST / "freeze/ALEX_RETEST_PLAN_frozen.md"
FROZEN_SHA256 = "a521c23d4623a4431f23d3b1f896554b9ac4274d8e277b1c3d83bc7c14afbe18"  # set at freezing 2026-11-18
N_DRAWS, N_BOOT, N_PERM = 999, 2000, 2000
SPLINE_DESIGN_SHA256 = "a9fa95654ea4d6cf66b578e465cb6e6003ff0b7b728de685aa6a515be0ffdad6"  # planted check, §15


def calibration(y, p):
    """Logistic recalibration of out-of-fold probabilities: slope b of y ~ a + b logit(p); intercept in the large
    a of y ~ a + offset(logit(p))."""
    import statsmodels.api as sm
    p = np.clip(p, 1e-15, 1 - 1e-15)
    lg = np.log(p / (1 - p))
    fam = sm.families.Binomial()
    slope = float(sm.GLM(y, sm.add_constant(lg), family=fam).fit().params[1])
    citl = float(sm.GLM(y, np.ones((len(y), 1)), family=fam, offset=lg).fit().params[0])
    return dict(slope=slope, intercept_in_the_large=citl)


def brier(y, p):
    return float(np.mean((np.asarray(p, float) - y) ** 2))


def oof_pair(XB, v, y, fold):
    s0 = R.S.oof(XB, y, fold, R.LR)
    s1 = R.S.oof(np.c_[XB, v], y, fold, R.LR)
    return s0, s1


def stat_on_rows(XB, v, y, folds):
    """T and the seed-42 PR AUC change on rows whose out-of-fold scores exist in every assignment (bootstrap and
    leave-one-block-out); None if an assignment leaves no positive or no negative among them."""
    dl, dpr = [], None
    for i, f in enumerate(folds):
        s0, s1 = oof_pair(XB, v, y, f)
        ok = np.isfinite(s0) & np.isfinite(s1)
        if not 0 < y[ok].sum() < ok.sum():
            return None
        dl.append(R.loglik(y[ok], s1[ok]) - R.loglik(y[ok], s0[ok]))
        if i == 0:
            dpr = R.S.metrics(y[ok], s1[ok])["pr"] - R.S.metrics(y[ok], s0[ok])["pr"]
    return dict(T=float(np.mean(dl)), dpr42=float(dpr))


def boot_rep(seed, c, XB, v, y, folds):
    rng = np.random.default_rng([R.SEED_BOOT, seed])
    blocks = c.block.unique()
    idx = np.concatenate([np.flatnonzero(c.block.to_numpy() == b) for b in rng.choice(blocks, len(blocks), replace=True)])
    r = stat_on_rows(XB[idx], v[idx], y[idx], folds[:, idx])
    if r is None:
        return None
    r["beta_per_sd"] = R.beta_hat(XB[idx], y[idx], v[idx])["per_sd"]
    return r


def null_stats(st, fields, jobs):
    out = Parallel(n_jobs=jobs)(delayed(st.of)(s) for s in fields)
    return np.array([o["T"] for o in out]), np.array([o["dpr42"] for o in out])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--synthetic", type=int, nargs=2, metavar=("CELL", "DATASET"))
    ap.add_argument("--planted-summary", type=Path, required=True)
    ap.add_argument("--null-choice", type=Path, help="step0/null_choice.json when the planted rule ended in branch 3")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--draws", type=int, default=N_DRAWS)
    ap.add_argument("--perms", type=int, default=N_PERM)
    ap.add_argument("--boot", type=int, default=N_BOOT)
    ap.add_argument("--jobs", type=int, default=16)
    a = ap.parse_args(argv)
    c, _, allc = R.load_cells()
    XB, v = R.design(c), c[R.COL].to_numpy(float)
    if a.synthetic:
        import planted as PL
        PL.load_ctx(R.RETEST / "step0")
        y, _ = PL.draw_labels(*a.synthetic)
        folds = R.fold_matrix(allc, c, y)
        label = f"SYNTHETIC check: planted cell {a.synthetic[0]}, dataset {a.synthetic[1]}"
    else:
        assert FROZEN_SHA256 and FROZEN_PLAN.exists() and R.sha256(FROZEN_PLAN) == FROZEN_SHA256, \
            "real outcomes are refused until the plan is frozen (FROZEN_SHA256)"
        y = c.positive.to_numpy(int)
        folds = R.fold_matrix(allc, c)
        assert np.array_equal(folds[0], c.fold.to_numpy())
        label = "REAL outcomes, frozen plan"
    PS = json.loads(a.planted_summary.read_text())
    primary, power = PS["rule"]["primary_null"], PS["rule"]["power_at_observed"]
    choice = None
    if primary is None and a.null_choice:
        choice = json.loads(a.null_choice.read_text())
        assert choice["planted_summary_sha256"] == R.sha256(a.planted_summary), "the choice was made on another planted summary"
        primary, power = choice["primary_null"], choice["power_at_observed"]
    assert primary in ("c1", "c2"), "the planted rule chose no primary null (branch 3): the user decides first"
    other = "c2" if primary == "c1" else "c1"
    meta = json.loads((R.RETEST / "step0/planted_inputs.json").read_text())
    assert R.sha256(R.RETEST / "step0/surrogates.npz") == meta["surrogates_sha256"], "surrogates differ from the planted check's"
    sz = np.load(R.RETEST / "step0/surrogates.npz")

    # observed
    st = R.Stat(XB, y, folds)
    obs = st.of(v)
    s0, s1 = oof_pair(XB, v, y, folds[0])
    per_fold = [R.loglik(y[folds[0] == k], s1[folds[0] == k]) - R.loglik(y[folds[0] == k], s0[folds[0] == k]) for k in range(5)]
    bh = R.beta_hat(XB, y, v)
    effects = dict(T=obs["T"], T_per_collapse_cell=obs["T"] / y.sum(), dl_by_assignment=obs["dl"], dl_seed42_by_fold=per_fold,
                   dpr42=obs["dpr42"], dpr_mean=obs["dpr_mean"], prevalence=float(y.mean()),
                   pr_seed42=[R.S.metrics(y, s0)["pr"], R.S.metrics(y, s1)["pr"]],
                   droc42=float(roc_auc_score(y, s1) - roc_auc_score(y, s0)),
                   dtop10_42=float(R.P.recall_top(y, s1) - R.P.recall_top(y, s0)),
                   beta_hat=bh, collapse_median=float(np.median(v[y == 1])), background_median=float(np.median(v[y == 0])))
    dbrier = []
    for f in folds:
        b0, b1 = oof_pair(XB, v, y, f)
        dbrier.append(brier(y, b1) - brier(y, b0))
    effects.update(dbrier42=dbrier[0], dbrier_mean=float(np.mean(dbrier)), brier42=[brier(y, s0), brier(y, s1)],
                   calibration42=dict(M0=calibration(y, s0), M1=calibration(y, s1)))

    # nulls: pixel nulls and the original six
    nulls = {}
    for name, key in ((f"primary ({primary})", primary), (f"other ({other})", other), ("unconditional pixel (a)", "a")):
        Tn, Pn = null_stats(st, sz[f"{key}_cells241"][:a.draws], a.jobs)
        nulls[name] = dict(T=Tn, dpr42=Pn)
    surr, _ = R.T17.surrogates(v, c[["x", "y"]].to_numpy(float), R.RES, a.draws)
    six = {**surr, "Free permutation": R.T17.permutations(v, c.block.to_numpy(), "free", a.perms),
           "Within-block permutation": R.T17.permutations(v, c.block.to_numpy(), "within-block", a.perms)}
    for k, fields in six.items():
        Tn, Pn = null_stats(st, fields, a.jobs)
        nulls[f"original: {k}"] = dict(T=Tn, dpr42=Pn)
    pvals = {k: dict(T=R.p_upper(obs["T"], d["T"]), dpr42=R.p_upper(obs["dpr42"] - 1e-12, d["dpr42"]),
                     null_median_T=float(np.median(d["T"])), null_q95_T=float(np.percentile(d["T"], 95)), draws=len(d["T"]))
             for k, d in nulls.items()}
    orig = [k for k in pvals if k.startswith("original: ")]
    two_by_two = {"T, primary null": pvals[f"primary ({primary})"]["T"],
                  "T, original six (largest p)": max(pvals[k]["T"] for k in orig),
                  "PR AUC, primary null": pvals[f"primary ({primary})"]["dpr42"],
                  "PR AUC, original six (largest p)": max(pvals[k]["dpr42"] for k in orig)}

    # bootstrap and leave-one-block-out
    reps = Parallel(n_jobs=a.jobs)(delayed(boot_rep)(i, c, XB, v, y, folds) for i in range(a.boot))
    kept = [r for r in reps if r is not None]
    boot = {k: dict(ci95=np.percentile([r[k] for r in kept], [2.5, 97.5]).tolist()) for k in ("T", "dpr42", "beta_per_sd")}
    boot.update(resamples=a.boot, kept=len(kept))
    lobo = {}
    for b in sorted(c.block.unique()):
        keep = c.block.to_numpy() != b
        r = stat_on_rows(XB[keep], v[keep], y[keep], folds[:, keep])
        lobo[b] = None if r is None else r["T"]

    # decision (§7)
    p = pvals[f"primary ({primary})"]["T"]
    if obs["T"] > 0 and p < 0.05 and bh["per_sd"] < 0:
        decision = "robust to the stricter test"
    elif power is not None and power < 0.80:
        decision = "inconclusive"
    else:
        decision = "not robust to the stricter test"

    # secondary 14 (flexible baseline) under the primary null, same draws; the qualifier of §7 (draft 4)
    XS, knots = SP.spline_design(XB, list(R.S.SET_B))
    design_sha = hashlib.sha256(np.ascontiguousarray(XS).tobytes()).hexdigest()
    assert design_sha == SPLINE_DESIGN_SHA256, "the flexible design differs from the one checked on planted data"
    st14 = R.Stat(XS, y, folds)
    o14 = st14.of(v)
    b14 = R.beta_hat(XS, y, v)["per_sd"]
    T14, P14 = null_stats(st14, sz[f"{primary}_cells241"][:a.draws], a.jobs)
    p14 = R.p_upper(o14["T"], T14)
    rej14 = bool(o14["T"] > 0 and p14 < 0.05 and b14 < 0)
    sec14 = dict(null=primary, T=o14["T"], dl_by_assignment=o14["dl"], dpr42=o14["dpr42"], dpr_mean=o14["dpr_mean"],
                 beta_per_sd=b14, p_T=p14, p_dpr42=R.p_upper(o14["dpr42"] - 1e-12, P14),
                 null_median_T=float(np.median(T14)), null_q95_T=float(np.percentile(T14, 95)), rejects=rej14,
                 knots=knots, design_sha256=design_sha, draws=len(T14))
    nulls[f"secondary 14: flexible baseline, primary ({primary})"] = dict(T=T14, dpr42=P14)
    qualifier = None
    if decision == "robust to the stricter test" and not rej14:
        qualifier = "with a linear baseline only: not robust to a flexible baseline (secondary 14)"
    reading = decision if qualifier is None else f"{decision}, {qualifier}"
    rec = dict(label=label, primary_null=primary, planted_rule=PS["rule"], null_choice=choice, decision=decision,
               qualifier=qualifier, reading=reading, secondary_14=sec14, p_primary=p,
               power_at_observed=power, effects=effects, p_values=pvals, two_by_two=two_by_two, bootstrap=boot,
               leave_one_block_out_T=lobo, criterion2_concordant=bool(effects["collapse_median"] < effects["background_median"]),
               draws=a.draws, perms=a.perms, planted_summary_sha256=R.sha256(a.planted_summary),
               surrogates_sha256=R.sha256(R.RETEST / "step0/surrogates.npz"), **R.hashes())
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "primary.json").write_text(json.dumps(rec, indent=1) + "\n")
    np.savez_compressed(a.out / "primary_nulls.npz", **{f"{k}|{s}": d[s] for k, d in nulls.items() for s in ("T", "dpr42")})
    print(json.dumps({k: rec[k] for k in ("label", "decision", "qualifier", "p_primary", "power_at_observed", "two_by_two", "bootstrap")}, indent=1))
    print("T", round(obs["T"], 3), "dpr42", round(obs["dpr42"], 4), "beta", round(bh["per_sd"], 3))
    print("secondary 14: T", round(o14["T"], 3), "p", p14, "beta", round(b14, 3), "rejects", rej14)


if __name__ == "__main__":
    main()
