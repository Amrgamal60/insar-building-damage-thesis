"""Report of a model run (NYC_REPLICATION_PLAN.md §11, §12): the decision, its labels and every secondary analysis,
built from the saved results of scripts/11_models.py. The variogram check (out/insar/INSAR_CHECKS.md) is reported first.
Usage (from feasibility/nyc): ../../.venv/bin/python -I scripts/12_report.py out --decoy|--real|--test"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(sys.argv[1])
MODE = sys.argv[2].lstrip("-")
RUN = OUT / "models" / MODE
INS = OUT / "insar"
NAME = {"real": "NYC_RESULT.md", "decoy": "DECOY_REPORT.md", "test": "TEST_REPORT.md"}[MODE]
spec = importlib.util.spec_from_file_location("nyc_lib", Path(__file__).resolve().parent / "nyc_lib.py")
N = importlib.util.module_from_spec(spec)
spec.loader.exec_module(N)
ORDER = ["primary", "s1", "s2", "s3", "s4", "s5", "s6", "s7", "s11", "s12", "s13", "s14", "s15"]
OTHER_NULLS = ["Free permutation", "Within-block permutation", "MSR", "MSR, amplitude-adjusted", "Variogram-matching, observed values"]
METRICS = (("pr", "PR AUC (primary)"), ("roc", "ROC AUC"),
           ("top10", "Top-10% recall, pooled (share of events in the top 10% of all rows)"),
           ("top10_rs", "Top 10% of own risk set (share of events)"))
NOTES = {"s14": "coverage check, §12.14", "s15": "retrospective, carries no weight, §12.15"}


def md(df):
    cols = list(df.columns)
    return "\n".join(["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join("---" for _ in cols) + "|"] +
                     ["| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else str(v) for v in r) + " |"
                      for r in df.itertuples(index=False)])


def fp(p):
    """p of 999 draws is a multiple of 0.001; others (2,000 draws) get five decimals so 0.04998 never reads 0.050."""
    if p < 0.001:
        return "< 0.001"
    return f"{p:.3f}" if abs(round(p, 3) - p) < 1e-12 else f"{p:.5f}"


def load(tag):
    p = RUN / f"result_{tag}.json"
    return json.loads(p.read_text()) if p.exists() else None


def num(x, k, sign=False):
    """PR AUC is near the prevalence (about 2 in 10,000 rows), so it needs six decimals."""
    return f"{x:{'+' if sign else ''}.{6 if k == 'pr' else 4}f}"


def ci(r, k):
    return f"{num(r[f'{k}_ci_lo'], k, True)} to {num(r[f'{k}_ci_hi'], k, True)}" if f"{k}_ci_lo" in r else "–"


def delta_p(r, k):
    return f"{r[f'{k}_delta']:+.3f} ({fp(r[f'{k}_p'])})"


def drops(tag):
    p = RUN / f"events_{tag}.csv"
    if not p.exists():
        return "–"
    d = pd.read_csv(p).dropped.fillna("").astype(str)
    d = d[d != ""].value_counts()
    return "; ".join(f"{v} {k}" for k, v in d.items()) or "none"


def variogram_check():
    p = INS / "INSAR_CHECKS.md"
    if not p.exists():
        return "**MISSING:** `out/insar/INSAR_CHECKS.md`. The variogram check must be reported first (§10)."
    t = p.read_text(encoding="utf-8")
    if "## 3. Variogram check" not in t:
        return "**MISSING:** `out/insar/INSAR_CHECKS.md` has no variogram-check section (§10)."
    head, body = t.split("## 3. Variogram check", 1)[1].split("\n\n", 1)
    body = body.split("\n## ")[0].split("\nFigure:")[0].rstrip()
    note = ("\n\nIn the decoy run this check describes the real primary analysis's windows and surrogates, not the decoy's."
            if MODE == "decoy" else "")
    return (f"**Variogram check{head.rstrip()}**\n\n{body}\n\n"
            f"Full check and figure: `out/insar/INSAR_CHECKS.md`, `out/insar/insar_checks.png`.{note}")


def main():
    P = load("primary")
    if P is None:
        sys.exit("no primary result")
    if MODE == "real" and int(P["null_draws"]) != 999:
        sys.exit(f"the primary null has {P['null_draws']} draws, not the 999 of §10: not a valid real run")
    s8 = load("s8")
    rep = P["pr_delta"] > 0 and P["pr_p"] < 0.05
    decision = "replicated" if rep else "not replicated"
    direction = P.get("direction_label", "none")
    dword = direction if direction in ("concordant", "opposite") else "undetermined"
    combined = (f"incremental-value replication with {dword} deformation direction" if rep
                else f"no incremental-value replication ({dword} deformation direction)")
    coef = P.get("coef_field_all_rows", float("nan"))
    coef_word = "concordant" if coef < 0 else "opposite" if coef > 0 else "undetermined"
    if s8:
        six = [("Variogram-matching (primary)", P["pr_p"])] + [(n, s8[n]["pr_p"]) for n in OTHER_NULLS]
        largest = (f"{fp(max(p for _, p in six))} (PR AUC p of each: "
                   + "; ".join(f"{n} {fp(p)}" for n, p in six) + ")")
    else:
        largest = f"not available: secondary 8 not run (the primary null alone gives {fp(P['pr_p'])})"
    boot = P.get("boot_resamples")
    boot_text = f"{boot} of {2000 if P['model'] == N.LR else 500} resamples" if boot else "no bootstrap result"

    prim = pd.DataFrame([{"Metric": lab, "Baseline 1 + x/y": num(P[f'{k}_base'], k), "+ velocity": num(P[f'{k}_vel'], k),
                          "Change": num(P[f'{k}_delta'], k, True), "p (variogram-matching)": fp(P[f"{k}_p"]),
                          "Null median": num(P[f'{k}_null_median'], k, True), "95% refit-bootstrap interval": ci(P, k)}
                         for k, lab in METRICS])
    null_tab = [{"Null": "Variogram-matching (primary, §10)", "Draws": int(P["null_draws"]),
                 **{f"p, {lab.split(' (')[0]}": fp(P[f"{k}_p"]) for k, lab in METRICS}}]
    if s8:
        null_tab += [{"Null": n, "Draws": int(s8[n]["draws"]), **{f"p, {lab.split(' (')[0]}": fp(s8[n][f"{k}_p"]) for k, lab in METRICS}}
                     for n in OTHER_NULLS]
    null_tab = pd.DataFrame(null_tab)

    sec, sample = [], []
    for k in ORDER:
        r = load(k)
        label = N.SPEC[k][1] + (f" ({NOTES[k]})" if k in NOTES else "")
        if r is None:
            sec.append({"Analysis": label, "Risk sets": "not run"})
            sample.append({"Analysis": label, "Risk sets": "not run"})
            continue
        sample.append({"Analysis": label, "Risk sets": f"{r['risk_sets']}", "Windows": f"{r['windows']}", "Rows": f"{r['rows']:,}",
                       "Cells": f"{r['cells']:,}", "Prevalence": f"{r['risk_sets'] / r['rows']:.6f}",
                       "Cells without a static input": f"{r['cells_missing_static']}",
                       "Rows without building age": f"{r['rows_missing_age']}" if N.SPEC[k][8] else "–",
                       "Events from": N.LENGTHS[N.SPEC[k][4]], "Of these, not used": drops(k)})
        if k == "primary":
            continue
        sec.append({"Analysis": label, "Risk sets": f"{r['risk_sets']}",
                    "PR AUC": f"{num(r['pr_base'], 'pr')} → {num(r['pr_vel'], 'pr')}", "Change": num(r['pr_delta'], 'pr', True),
                    "p": fp(r["pr_p"]), "Draws": f"{int(r['null_draws'])}", "Interval": ci(r, "pr"),
                    "ΔROC AUC (p)": delta_p(r, "roc"), "ΔTop-10% pooled (p)": delta_p(r, "top10"),
                    "ΔTop-10% own set (p)": delta_p(r, "top10_rs"), "Direction": r.get("direction_label", "–")})
    seeds = []
    for sd in range(10):
        r = load(f"s9_seed{sd}")
        seeds.append({"Fold seed": sd, "PR AUC change": "not run"} if r is None else
                     {"Fold seed": sd, "PR AUC change": num(r['pr_delta'], 'pr', True), "p": fp(r["pr_p"]),
                      "ΔROC AUC (p)": delta_p(r, "roc"), "ΔTop-10% pooled (p)": delta_p(r, "top10"),
                      "ΔTop-10% own set (p)": delta_p(r, "top10_rs")})

    title = {"real": "NYC replication: result", "decoy": "NYC decoy run (code check, not a result)",
             "test": "NYC smoke test (code check only)"}[MODE]
    lines = [f"# {title}", "",
             "**Plan:** `NYC_REPLICATION_PLAN.md` (frozen copy `freeze/NYC_REPLICATION_PLAN_frozen.md`), §11–§13. "
             f"**Reproduce:** `../../.venv/bin/python -I scripts/11_models.py raw out --{MODE if MODE != 'test' else 'decoy --test N'}`, then "
             f"`scripts/12_report.py out --{MODE}`.", ""]
    if MODE == "decoy":
        lines += ["**Decoy outcome:** each of the 185 events moved to a random eligible domain cell at 250 m (seed 99), keeping "
                  "its date (§13 step 4). These numbers check the code end to end and say nothing about InSAR and collapses. "
                  "Nothing changes because of them except outright code errors, which are logged in §14. Secondary analyses "
                  "other than 8 and 9 used reduced draw counts (§14 deviation 2).", ""]
    lines += ["## 1. Variogram check (reported first, §10)", "", variogram_check(), "",
              "## 2. Decision (§11)", "",
              f"- **Incremental-value replication: {decision}.** Primary analysis (domain, 250 m, logistic regression, Baseline 1 + "
              f"x/y, 1-year window): out-of-fold PR AUC {num(P['pr_base'], 'pr')} → {num(P['pr_vel'], 'pr')}, change {num(P['pr_delta'], 'pr', True)}; "
              f"variogram-matching null p = {fp(P['pr_p'])} ({P['null_draws']} draws). Rule: change > 0 and p < 0.05.",
              f"- **Directional concordance: {dword}.** Line-of-sight velocity is positive toward the satellite. Measure: the "
              f"median over risk sets of (event cell − median of its controls), standardised velocity: "
              f"{P.get('direction_median', float('nan')):+.3f} ({100 * P.get('direction_share_below_0', float('nan')):.0f}% of "
              "risk sets below 0). Below 0 is concordant with Alexandria: event cells move away from the satellite relative "
              "to their controls, as relative subsidence would. Above 0 is opposite.",
              f"  - Same measure in raw line of sight: {P.get('direction_raw_mm_yr_median', float('nan')):+.2f} mm/yr. Raw values "
              "are not standardised, so they keep each window's landmass-group medians and spread. Medians pooled over rows "
              f"(controls repeat across risk sets, so these need not differ by the value above): event cells "
              f"{P.get('event_raw_mm_yr_median', float('nan')):+.2f}, control rows {P.get('control_raw_mm_yr_median', float('nan')):+.2f} mm/yr.",
              f"  - Velocity coefficient in a logistic regression fitted on all rows (standardised, conditional on the baseline "
              f"features): {coef:+.3f}, sign {coef_word} (negative = concordant).",
              f"- **Together:** {combined}.",
              f"- **Effect size:** {num(P['pr_delta'], 'pr', True)} (95% refit-bootstrap interval {ci(P, 'pr')}, {boot_text}).",
              f"- **Largest p across the six nulls** (Alexandria's LiCSAR standard, reported only): {largest}.",
              "",
              f"**Sample:** {P['risk_sets']} risk sets over {P['windows']} windows; {P['rows']:,} rows; {P['cells']:,} cells; "
              f"prevalence {P['risk_sets'] / P['rows']:.6f} (one event per risk set, §9). Events from "
              f"{N.LENGTHS[365]} not used: {drops('primary')}. Cells without a static input: {P['cells_missing_static']}.",
              "", md(prim), "",
              "The bootstrap interval is not computed for the own-risk-set top-10% share.", "",
              "## 3. All nulls on the primary analysis (primary and secondary 8)", "", md(null_tab),
              "" if s8 else "\nSecondary 8: not run.", "",
              "## 4. Secondary analyses (no decision attached; primary null unless stated)", "", md(pd.DataFrame(sec)), "",
              "Direction uses the same measure as §11 and applies only to velocity fields. Δ columns: change from the "
              "baseline, with its p from the same null.", "",
              "## 5. Sample and exclusions per analysis (§8, §9)", "", md(pd.DataFrame(sample)), "",
              "## 6. Other fold assignments (secondary 9; primary null, no bootstrap)", "", md(pd.DataFrame(seeds)), ""]
    (RUN / NAME).write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
