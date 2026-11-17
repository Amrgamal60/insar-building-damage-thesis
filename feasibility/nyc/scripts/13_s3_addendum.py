"""Addendum for secondary 3 (random forest), completed after the compute budget (NYC_REPLICATION_PLAN.md §14
deviation 10). Uses the formatting of scripts/12_report.py and writes out/models/real/NYC_RESULT_S3_ADDENDUM.md.
NYC_RESULT.md is not touched. The addendum carries no decision (§11, §12).
Usage (from feasibility/nyc): ../../.venv/bin/python -I scripts/13_s3_addendum.py out --real"""
import importlib.util
import sys
from pathlib import Path

import pandas as pd

spec = importlib.util.spec_from_file_location("report", Path(__file__).resolve().parent / "12_report.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)  # reads sys.argv[1:3] (out --real) itself
N = R.N


def main():
    if R.MODE != "real":
        sys.exit("the addendum is for the real run only")
    r, P = R.load("s3"), R.load("primary")
    if r is None:
        sys.exit("no result_s3.json")
    if int(r["null_draws"]) != 500:
        sys.exit(f"s3 has {r['null_draws']} null draws, not the 500 of §12.3")
    boot = int(r.get("boot_resamples", 0))  # resamples that return None (as in 12_report.py) are left out
    label = N.SPEC["s3"][1]
    same = ("The measure depends on the rows and the velocity field, not on the model, and equals the primary analysis's."
            if abs(r.get("direction_median", 0) - P.get("direction_median", 1)) < 1e-12 else
            f"The primary analysis gives {P.get('direction_median', float('nan')):+.3f} ({P.get('direction_label', '–')}).")
    metrics = pd.DataFrame([{"Metric": lab, "Baseline 1 + x/y": R.num(r[f"{k}_base"], k), "+ velocity": R.num(r[f"{k}_vel"], k),
                             "Change": R.num(r[f"{k}_delta"], k, True), "p (variogram-matching)": R.fp(r[f"{k}_p"]),
                             "Null median": R.num(r[f"{k}_null_median"], k, True), "95% refit-bootstrap interval": R.ci(r, k)}
                            for k, lab in R.METRICS])
    row = lambda x, name: {"Analysis": name, "Model": x["model"], "PR AUC": f"{R.num(x['pr_base'], 'pr')} → {R.num(x['pr_vel'], 'pr')}",
                           "Change": R.num(x["pr_delta"], "pr", True), "p": R.fp(x["pr_p"]), "Draws": f"{int(x['null_draws'])}",
                           "Interval": R.ci(x, "pr"), "ΔROC AUC (p)": R.delta_p(x, "roc"),
                           "ΔTop-10% pooled (p)": R.delta_p(x, "top10"), "ΔTop-10% own set (p)": R.delta_p(x, "top10_rs"),
                           "Direction": x.get("direction_label", "–")}
    both = pd.DataFrame([row(P, "Primary (for comparison, from NYC_RESULT.md)"), row(r, label)])
    sample = pd.DataFrame([{"Risk sets": f"{r['risk_sets']}", "Windows": f"{r['windows']}", "Rows": f"{r['rows']:,}",
                            "Cells": f"{r['cells']:,}", "Prevalence": f"{r['risk_sets'] / r['rows']:.6f}",
                            "Cells without a static input": f"{r['cells_missing_static']}",
                            "Events from": N.LENGTHS[N.SPEC['s3'][4]], "Of these, not used": R.drops("s3")}])
    n_sec = sum(1 for k in R.ORDER if k != "primary" and R.load(k) is not None)
    k_null = round(r["pr_p"] * (int(r["null_draws"]) + 1))
    notes = [f"- **p:** p = (1 + k)/(1 + draws), where k is the number of null draws at least as large as the observed "
             f"change (`11_models.py`); here k = {k_null - 1} of {int(r['null_draws'])}, so p = {k_null}/{int(r['null_draws']) + 1} "
             f"= {R.fp(r['pr_p'])}. The rule of §11 (change > 0 and p < 0.05) applies only to the primary analysis."]
    if min(r["roc_base"], r["roc_vel"]) < 0.5:
        notes.append(f"- **Ranking below chance:** the random forest's out-of-fold ROC AUC is {r['roc_base']:.4f} without and "
                     f"{r['roc_vel']:.4f} with velocity, both below 0.5; the logistic regression of the primary analysis gives "
                     f"{P['roc_base']:.4f} and {P['roc_vel']:.4f}.")
    notes.append(f"- **Multiplicity:** counting this one, {n_sec} of the secondary analyses listed in §4 of `NYC_RESULT.md` now have a result "
                 "(plus secondary 8's other nulls and secondary 9's fold seeds). None carries a decision, and no correction "
                 "for multiple comparisons is applied.")
    lines = ["# NYC replication: secondary 3 (random forest), completed after the compute budget", "",
             "**Status:** completed after the compute budget (§13.6 expired 2026-10-15 16:27:25), at the user's instruction, "
             "with no deadline (§14 deviation 10). All NYC results, including `NYC_RESULT.md`, had been seen before it was "
             "resumed. Model, seeds, counts (500 null draws, 500 refit-bootstrap resamples) and the primary null are as "
             "frozen (§12.3); the code is unchanged. **It carries no decision** (§11, §12) and does not change "
             "`NYC_RESULT.md`, which stays the report of the budgeted run (decision: not replicated).", "",
             "**Reproduce:** `../../.venv/bin/python -I scripts/11_models.py raw out --real --jobs 16 --only s3` (execution "
             "environment of deviation 9; resumes from `out/models/real/checkpoints/s3/`), then "
             "`scripts/13_s3_addendum.py out --real`.", "",
             "## 1. Result", "", R.md(metrics), "",
             f"- **Direction (same measure as §11):** {r.get('direction_label', '–')}; median over risk sets "
             f"{r.get('direction_median', float('nan')):+.3f} ({100 * r.get('direction_share_below_0', float('nan')):.0f}% of "
             "risk sets below 0; below 0 is concordant with Alexandria). " + same,
             f"- **Refit bootstrap:** {boot} of 500 resamples gave a result.",
             f"- **Run time of the resumed process** (started 2026-10-15 at about 17:08 Cairo; the budgeted part is not "
             f"counted): {r.get('seconds', float('nan')) / 3600:.1f} h.", "",
             "## 2. Beside the primary analysis", "", R.md(both), "",
             "Δ columns: change from the baseline, with its p from the same null (variogram-matching, §10).", "",
             "## 3. Sample (§8, §9)", "", R.md(sample), "",
             "## 4. Notes (facts for reading the result; no decision attached)", "", *notes, ""]
    out = R.RUN / "NYC_RESULT_S3_ADDENDUM.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
