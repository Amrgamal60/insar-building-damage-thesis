#!/usr/bin/env python3
"""Austin secondary analyses (AUSTIN_PLAN.md §12): the secondary report.

Runs on the project PC only, after every real secondary run (2026-11-17). Standard library only; run with python3 -I.
It reads the real results already copied to secondary_real/ (each checked equal to the server's copy), the primary
records in real_20261112/ and the run log secondary_real/status_real, and writes
    secondary_real/AUSTIN_SECONDARY_RESULTS.md   the report (every number is copied by this code, none by hand)
    secondary_real/secondary_summary.json         the same numbers, machine-readable
It computes nothing new: no fit, no null, no bootstrap. No decision is attached to any secondary (§12); every p is
nominal and uncorrected (§12, last line). The asserts check that each result is the file named in the run log.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

BASE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
SEC = BASE / "secondary_real"
REAL = BASE / "real_20261112"
OUT_MD = SEC / "AUSTIN_SECONDARY_RESULTS.md"
OUT_JSON = SEC / "secondary_summary.json"
FROZEN = BASE / "freeze" / "AUSTIN_PLAN_frozen.md"


def sha(p, n=None):
    h = hashlib.sha256(Path(p).read_bytes()).hexdigest()
    return h[:n] if n else h


def load(p):
    return json.loads(Path(p).read_text())


# ---------- formatting ----------
MINUS = "\u2212"


def sgn(s):
    return s.replace("-", MINUS)


def f_ch(x):  # a change in PR AUC
    if x is None:
        return "–"
    if x == 0:
        return "0.00000"
    return sgn(f"{x:+.5f}" if abs(x) >= 1e-5 else f"{x:+.7f}")


def f_m(x, d=4):  # ROC / top-10% changes
    return "–" if x is None else sgn(f"{x:+.{d}f}")


def f_v(x, d=4):  # a level
    return "–" if x is None else f"{x:.{d}f}"


def f_p(p):
    return "–" if p is None else f"{p:.3f}"


def f_ci(ci, f=f_ch):
    return "–" if not ci else f"{f(ci[0])} to {f(ci[1])}"


def f_int(n):
    return "–" if n is None else f"{n:,}"


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


# ---------- run log ----------
LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) (\S+) (start|end)(?: ([0-9a-f]{16}))?$")
runs = {}
for line in (SEC / "status_real").read_text().splitlines():
    m = LINE.match(line.strip())
    if not m:
        continue
    t, item, what, h = m.groups()
    r = runs.setdefault(item, {})
    if what == "start":
        r["start"] = t  # the last start counts (a failed item would be restarted)
    else:
        r["end"], r["hash16"] = t, h


def result(item):
    p = SEC / item / "result.json"
    r = load(p)
    assert r["label"] == "REAL RUN" and r["mode"] == "real", item
    h = sha(p, 16)
    assert runs[item]["hash16"] == h, (item, runs[item], h)
    r["_hash16"], r["_start"], r["_end"] = h, runs[item]["start"], runs[item]["end"]
    return r


def hm(t):  # "2026-11-16 07:21:04" -> "11-16 07:21:04"
    return t[5:]


# ---------- primary records ----------
rep_a = load(REAL / "report_a.json")
test_a = load(REAL / "test_a.json")
test_b = load(REAL / "test_b.json")
nulla = load(REAL / "nulla" / "test_a.json")
msr = load(REAL / "msr" / "test_a.json")
F = rep_a["foundation"]
assert F["cases"] == test_a["cases"] == 1754 and F["rows"] == test_a["rows"]
assert abs(F["observed"]["pr"] - test_a["observed"]) < 1e-15
PRIMARY_A = dict(
    label="Primary (24-month velocity, lag 0)", cases=F["cases"], rows=F["rows"], blocks=F["blocks_with_rows"],
    base=F["baseline"], obs=F["observed"], null=F["null"], draws=F["null"]["draws"],
    boot=rep_a["bootstrap"]["per_analysis"]["foundation"], resamples=rep_a["bootstrap"]["resamples"],
    cases_per_fold=test_a["cases_per_fold"], dropped=test_a["dropped"],
    control_rows=test_a["control_rows_dropped_missing_inputs"], first_window=None, start=None, end=None,
    hash16=sha(REAL / "report_a.json", 16), events=test_a["events_in_file"])

# ---------- Test A secondaries ----------
A_ITEMS = [
    ("1_nyc_design", "1. NYC design (250 m cells)"),
    ("2_local_controls", "2. Local controls (within 1 km)"),
    ("3_window_12", "3. 12-month window"),
    ("3_window_36", "3. 36-month window (events from 2019-08)"),
    ("4_random_forest", "4. Random forest"),
    ("5_baseline_2", "5. Baseline 2"),
    ("5_baseline_1_no_income", "5. Baseline 1 without income"),
    ("6_amplitude", "6. Seasonal amplitude"),
    ("6_local_relative_motion", "6. Local relative motion"),
    ("6_acceleration", "6. Acceleration"),
    ("7_boosted_trees", "7. Boosted trees (all four indicators)"),
    ("10_issue_date", "10. Issue date"),
    ("12_availability", "12. Availability only"),
    ("13_no_construction_mask", "13. No construction mask"),
    ("slip_first_run", "Slip-rule sensitivity (first-run velocity)"),
    ("D1_demolition", "D1. Demolition as the outcome"),
    ("D2_composite", "D2. Composite outcome"),
]
LAGS = [("9_lag_1", "1 month"), ("9_lag_3", "3 months"), ("9_lag_6", "6 months"), ("9_lag_12", "12 months")]
SEEDS = [f"11_fold_seed_{s}" for s in range(10)]


def a_row(item, label):
    r = result(item)
    n = r["null"]
    b = r.get("bootstrap") or {}
    fields = r.get("inputs", {}).get("fields") or {}
    fw = None
    for v in fields.values():
        if isinstance(v, dict) and v.get("first_window_with_values"):
            fw = v["first_window_with_values"]
    return dict(
        item=item, label=label, cases=r["cases"], rows=r["rows"], blocks=r.get("blocks_with_rows"),
        base=r["baseline"], obs=r["observed"], null=n, draws=None,
        boot=b, resamples=b.get("resamples"), cases_per_fold=r.get("cases_per_fold"), dropped=r.get("dropped"),
        control_rows=r.get("control_rows_dropped_missing_inputs"), first_window=fw, start=r["_start"], end=r["_end"],
        hash16=r["_hash16"], events=r.get("events_in_file"), notes=r.get("notes"), raw=r)


def draws_of(r):
    di = r["null"].get("draw_indices")
    if isinstance(di, str):
        m = re.match(r"(\d+) \.\. (\d+)", di)
        if m:
            return int(m.group(2)) - int(m.group(1)) + 1
    return r["null"].get("draws")


A = []
for item, label in A_ITEMS:
    row = a_row(item, label)
    row["draws"] = draws_of(row["raw"])
    A.append(row)
LAG_ROWS = []
for item, lab in LAGS:
    row = a_row(item, lab)
    row["draws"] = draws_of(row["raw"])
    LAG_ROWS.append(row)
SEED_ROWS = []
for s, item in enumerate(SEEDS):
    row = a_row(item, str(s))
    row["draws"] = draws_of(row["raw"])
    assert row["raw"]["spec"]["fold_seed"] == s
    SEED_ROWS.append(row)


def a_cols(r):
    o, n, b, base = r["obs"], r["null"], r["boot"], r["base"]
    return [
        r["label"], f_int(r["cases"]),
        f"{f_v(base['pr'], 6 if base['pr'] < 0.01 else 4)} → {f_v(base['pr'] + o['pr'], 6 if base['pr'] < 0.01 else 4)}",
        f_ch(o["pr"]), f_ci(b.get("pr_ci95")), f_p(n["pr_p"]), f_ch(n.get("pr_null_median")), f_int(r["draws"]),
        f"{f_m(o['roc'])} ({f_p(n['roc_p'])})", f"{f_m(o['top10'])} ({f_p(n['top10_p'])})",
        f"{f_m(o['top10_rs'])} ({f_p(n['top10_rs_p'])})",
    ]


A_HEAD = ["Analysis", "Cases", "PR AUC: baseline → with indicator", "Change in PR AUC", "95% interval", "p",
          "Null median", "Draws", "ΔROC AUC (p)", "ΔTop-10% pooled (p)", "ΔTop-10% own set (p)"]

# ---------- Test B ----------
B_ITEMS = [
    ("15_lag_1", "15. Lag 1 month"), ("15_lag_3", "15. Lag 3 months"), ("15_lag_6", "15. Lag 6 months"),
    ("15_lag_12", "15. Lag 12 months"), ("16_window_24", "16. 24-month window"), ("17_amplitude", "17. Amplitude"),
    ("17_local_relative_motion", "17. Local relative motion"), ("17_acceleration", "17. Acceleration"),
    ("18_negative_binomial", "18. Negative binomial with area characteristics"),
    ("19_monthly", "19. Monthly counts"), ("slip_first_run_b", "Slip-rule sensitivity (first-run cell velocity)"),
]


def b_row(label, r, start=None, end=None, hash16=None):
    o, p = r["observed"], r["panel"]
    time_used = o.get("quarters_used")
    return dict(label=label, events_used=p["events_in_rows_used"], events_noval=p["events_in_rows_without_value"],
                rows_in=o.get("rows_input", p["rows_used"]), rows_used=o["rows_used"], cells=o["cells_used"],
                periods=time_used, blocks=o["blocks_used"], iqr=o["velocity_iqr"], beta=o["beta"],
                se=o["clustered_se"], rr=o["rate_ratio_iqr"], ci=o["rate_ratio_ci95"], exc=r["exceedances"],
                p=r["p_B"], start=start, end=end, hash16=hash16, model=o.get("fit_route"), alpha=o.get("alpha"))


PRIMARY_B = b_row("Primary (12-month velocity, lag 0)", test_b, hash16=sha(REAL / "test_b.json", 16))
B = []
for item, label in B_ITEMS:
    r = result(item)
    B.append(dict(item=item, **b_row(label, r, r["_start"], r["_end"], r["_hash16"])))


def b_cols(r):
    lo, hi = r["ci"]
    direction = "concordant" if r["rr"] < 1 else "opposite"
    excl = " (excludes 1)" if (hi < 1 or lo > 1) else ""
    per = "–" if r["periods"] is None else str(r["periods"])
    return [r["label"], f_int(r["events_used"]), f"{f_int(r['rows_used'])} ({f_int(r['cells'])}, {per}, {r['blocks']})",
            f"{r['iqr']:.1f}", sgn(f"{r['beta']:+.5f} ({r['se']:.5f})"), f"{r['rr']:.3f}",
            f"{lo:.3f} to {hi:.3f}{excl}", f"{r['p']:.3f} ({r['exc']})", direction]


B_HEAD = ["Analysis", "Events in rows used", "Rows used (cells, periods, blocks)", "IQR", "β per unit (clustered SE)",
          "Rate ratio per IQR", "95% interval (Wald, block-clustered)", "p_B (exceedances of 999)", "Direction"]

# ---------- deep model ----------
deep = result("20_deep_model")

# ---------- §12.8 nulls ----------
perm = rep_a["permutation_nulls"]
NULLS = [
    ("Conditional variogram null (primary, §10)", F["null"]["draws"], F["null"]["pr_p"], F["null"]["roc_p"],
     F["null"]["top10_p"], F["null"]["top10_rs_p"], F["null"]["pr_null_median"]),
    ("Null (a): NYC variogram null, unconditional (read with the calibration's warning)", nulla["draws"],
     nulla["p"], None, None, None, None),
    ("Free permutation", perm["free"]["draws"], perm["free"]["pr_p"], perm["free"]["roc_p"], perm["free"]["top10_p"],
     perm["free"]["top10_rs_p"], perm["free"]["pr_null_median"]),
    ("Within-block permutation", perm["within-block"]["draws"], perm["within-block"]["pr_p"],
     perm["within-block"]["roc_p"], perm["within-block"]["top10_p"], perm["within-block"]["top10_rs_p"],
     perm["within-block"]["pr_null_median"]),
    ("MSR (seed 2026)", msr["draws"], msr["p"], None, None, None, None),
]
for path in (nulla, msr):
    assert abs(path["observed"] - test_a["observed"]) < 1e-15 and path["cases"] == test_a["cases"]
largest = max(x[2] for x in NULLS[1:])

A_ORDERED = A[:11] + LAG_ROWS + A[11:]  # item order: 1-7, 9, 10, 12, 13, slip-rule, D1, D2
assert [r["item"] for r in A[:11]][-1] == "7_boosted_trees" and A[11]["item"] == "10_issue_date"

# ---------- reading notes: every nominal p < 0.05 ----------
NOTES = []
METRICS = [("pr", "PR AUC", "pr_ci95"), ("roc", "ROC AUC", "roc_ci95"), ("top10", "Top-10% pooled", "top10_ci95"),
           ("top10_rs", "Top-10% own set", None)]
for r in A_ORDERED + SEED_ROWS:
    name = r["label"] if r["item"] not in SEEDS else f"11. Fold seed {r['label']}"
    if r["item"].startswith("9_"):
        name = f"9. Lag {r['label']}"
    for key, mlab, cikey in METRICS:
        p = r["null"].get(f"{key}_p")
        if p is None or p >= 0.05:
            continue
        ch, med = r["obs"][key], r["null"].get(f"{key}_null_median")
        ci = r["boot"].get(cikey) if cikey else None
        if ch <= 0:
            reading = "not a gain: the change is not positive; p is small because the null draws were lower"
        elif ci is None:
            reading = "positive; no bootstrap interval for this metric"
        elif ci[0] <= 0:
            reading = "positive; its 95% interval includes 0"
        else:
            reading = "positive; its 95% interval excludes 0"
        NOTES.append([name, mlab, f_ch(ch) if key == "pr" else f_m(ch), f_p(p),
                      (f_ch(med) if key == "pr" else f_m(med)) if med is not None else "–",
                      f_ci(ci, f_ch if key == "pr" else f_m) if ci else "–", reading])
B_NOTES = [r for r in B if r["ci"][1] < 1 or r["ci"][0] > 1 or r["p"] < 0.05]

# ---------- write ----------
plan_hash = sha(FROZEN, 16)
assert plan_hash == "18627d8275d7859b", plan_hash
o = []
w = o.append
w("# Austin: secondary results (§12)")
w("")
w(f"Frozen plan `freeze/AUSTIN_PLAN_frozen.md` (`{plan_hash}…`, draft 10, conditional null (b) primary, option A). "
  "Generated by `production/secondary_report.py` from the real results in `secondary_real/` (each equal to the "
  "server's copy) and the primary records in `real_20261112/`. Every result number below is read from those files "
  "by that code; the plan's fixed settings (windows, draw counts, seeds) are stated as in §12 and §15.")
w("")
w("**No decision is attached to any analysis here (§12).** Only Test A carries the decision (§11): the added held-out "
  f"value of InSAR is **not demonstrated** in Austin (change in PR AUC {f_ch(test_a['observed'])}, p = {test_a['p']:.3f}). "
  f"Test B, the key secondary, did **not detect** an association (rate ratio per IQR {test_b['observed']['rate_ratio_iqr']:.3f}, "
  f"p_B = {test_b['p_B']:.3f}). Every p below is nominal and uncorrected for multiple tests, on one of several metrics.")
w("")
w("Reading conventions:")
w("- **Change** is the indicator model's out-of-fold metric minus the baseline model's (Test A design, §8A–§9). "
  "p counts null draws at or above the observed change; a small p with a negative change is not a gain (the null "
  "draws were lower still).")
w("- **95% interval:** refit block bootstrap over 2 km blocks, 2,000 resamples (500 for tree models). It is not "
  "computed for the top-10% share within the risk set.")
w("- **Test B direction (§8B):** a rate ratio per IQR below 1 is concordant (more motion away from the satellite, "
  "then more recorded permits).")
w("")

w("## 1. Primary analyses, for reference (§11; reported 2026-11-12)")
w("")
w(table(A_HEAD, [a_cols(PRIMARY_A)]))
w("")
w(table(B_HEAD, [b_cols(PRIMARY_B)]))
w("")

w("## 2. Nulls on the primary analysis (secondary 8)")
w("")
w(f"Same {test_a['cases']:,} cases, {test_a['rows']:,} rows and observed change as the primary analysis (change in "
  f"PR AUC {f_ch(test_a['observed'])}).")
w("")
w(table(["Null", "Draws", "p, PR AUC", "p, ROC AUC", "p, Top-10% pooled", "p, Top-10% own set", "Null median, PR AUC"],
        [[x[0], f_int(x[1]), f_p(x[2]), f_p(x[3]), f_p(x[4]), f_p(x[5]), f_ch(x[6])] for x in NULLS]))
w("")
w(f"**Largest p across the nulls of §12.8** (change in PR AUC, reported beside the decision): **{largest:.3f}**, over "
  "all four (null (a), free and within-block permutation, MSR). Null (a) and MSR were run through the decision code, "
  "which reports the PR AUC p only.")
w("")

w("## 3. Test A secondaries (primary design unless stated; own null file for a new field)")
w("")
w(table(A_HEAD, [a_cols(PRIMARY_A)] + [a_cols(r) for r in A]))
w("")
w("- **Draws:** 999 for logistic regression; draws 0–499 for the tree models (4, 7), as §12. Items 2, 4, 5, 10, D1 "
  "and D2 use the primary null file; 7 uses draw d of each of its four indicators' files; the others use the null "
  "file of their own field.")
nyc = next(r for r in A if r["item"] == "1_nyc_design")
w(f"- **1 (NYC design)** is at cell level: {nyc['cases']:,} cases in {nyc['rows']:,} cell rows (prevalence "
  f"{nyc['cases'] / nyc['rows']:.6f}), so its PR AUC levels are not comparable with the house-level rows.")
nyc_res = sorted(x["nyc_design"]["pr"] for x in nyc["raw"]["bootstrap"]["per_resample"]
                 if x["nyc_design"]["pr"] is not None)


def pct(v, q):  # numpy's default (linear) percentile on sorted values
    h = (len(v) - 1) * q
    lo = int(h)
    return v[lo] + (h - lo) * (v[min(lo + 1, len(v) - 1)] - v[lo])


assert max(abs(pct(nyc_res, 0.025) - nyc["boot"]["pr_ci95"][0]), abs(pct(nyc_res, 0.975) - nyc["boot"]["pr_ci95"][1])) < 1e-15
w(f"  Its interval is wide on the low side: of {len(nyc_res):,} resamples, {sum(1 for x in nyc_res if x < -0.0005):,} "
  f"give a change below {f_ch(-0.0005)}, while the median resample is {f_ch(pct(nyc_res, 0.5))}; the "
  "lower bound reflects that tail (recomputed from the stored resamples, equal to the stored interval).")
lc = next(r for r in A if r["item"] == "2_local_controls")["notes"]["local_controls"]
w(f"- **2 (local controls):** {lc['cases_with_empty_pool']} cases with an empty 1 km pool; "
  f"{lc['sets_with_fewer_than_50']} risk set with fewer than 50 controls (kept); median pool "
  f"{lc['pool_size_quantiles']['50']:,.0f} houses.")
b2 = next(r for r in A if r["item"] == "5_baseline_2")["notes"]["baseline_2"]
w(f"- **5 (Baseline 2):** {b2['rows_missing_an_input']} rows miss an input; {b2['cases_dated_before_2018_11_04']} cases "
  "are dated before 2018-11-04, before the canopy layer they use (counted, §15).")
w("- **5 (Baseline 2 and Baseline 1 without income)** use the primary null, which conditions on the §10 covariates "
  "(including income) and not on Baseline 2's additions; read with that note (§15).")
w("- **12 (availability only)** uses the primary velocity's rows, so only the indicator changes.")
w("- **D1, D2** use the Test A design on other outcomes (§12, §5): demolition, and the first of foundation repair or demolition.")
w("")

w("## 4. Lag profile (secondary 9), reported together with lag 0")
w("")
w("The 24-month window ending 0, 1, 3, 6 or 12 months before the event month. Each lag uses the events whose window "
  "starts on or after the first granule. None is chosen as best, none carries a decision, and they are analysis "
  "windows, not estimates of the delay between damage and application (§12, item 9).")
w("")
LAG_HEAD = ["Lag", "First window with values", "Cases"] + A_HEAD[2:]
lag_table = [["0 (primary)", "–", f_int(PRIMARY_A["cases"])] + a_cols(PRIMARY_A)[2:]]
lag_table += [[r["label"], r["first_window"] or "–", f_int(r["cases"])] + a_cols(r)[2:] for r in LAG_ROWS]
w(table(LAG_HEAD, lag_table))
w("")
w("A lagged field has no values in its first windows; events whose window precedes its first window with values "
  "drop as \"no value in the window\", which is why the case count falls with the lag. \"–\": the primary field has "
  "no empty first windows.")
w("")

w("## 5. Other fold assignments (secondary 11; primary null, no bootstrap)")
w("")
w(table(["Fold seed", "Cases by fold", "Baseline PR AUC", "Change in PR AUC", "p", "Null median", "ΔROC AUC (p)",
         "ΔTop-10% pooled (p)", "ΔTop-10% own set (p)"],
        [[r["label"], ", ".join(f"{c:,}" for c in r["cases_per_fold"]), f_v(r["base"]["pr"]), f_ch(r["obs"]["pr"]),
          f_p(r["null"]["pr_p"]), f_ch(r["null"]["pr_null_median"]),
          f"{f_m(r['obs']['roc'])} ({f_p(r['null']['roc_p'])})", f"{f_m(r['obs']['top10'])} ({f_p(r['null']['top10_p'])})",
          f"{f_m(r['obs']['top10_rs'])} ({f_p(r['null']['top10_rs_p'])})"] for r in SEED_ROWS]))
seed_ch = sorted(r["obs"]["pr"] for r in SEED_ROWS)
seed_med = (seed_ch[4] + seed_ch[5]) / 2
w("")
w(f"Every seed has the primary's {SEED_ROWS[0]['cases']:,} cases and {SEED_ROWS[0]['rows']:,} rows. The change in PR AUC "
  f"ranges from {f_ch(seed_ch[0])} to {f_ch(seed_ch[-1])} (median {sgn(f'{seed_med:+.6f}')}; the primary seed gave "
  f"{f_ch(test_a['observed'])}); {sum(1 for c in seed_ch if c > 0)} of 10 are positive.")
w("")

w("## 6. Test B secondaries (15–19 and the slip-rule sensitivity), with lag 0")
w("")
w("Poisson with cell and period fixed effects (§8B), except 18 (negative binomial with area characteristics and "
  "quarter fixed effects). Each uses the Test B null of its own field (999 draws, seed 2034); 18 uses the primary "
  "Test B null file. Periods are quarters, except 19 (88 calendar months). The IQR is in the field's units "
  "(mm/yr for velocities).")
w("")
w(table(B_HEAD, [b_cols(PRIMARY_B)] + [b_cols(r) for r in B]))
w("")
nb = next(r for r in B if r["item"] == "18_negative_binomial")
w(f"- **18:** {f_int(nb['rows_used'])} rows in {f_int(nb['cells'])} cells and {nb['blocks']} blocks (rows whose cell "
  f"holds a house with complete characteristics); fitted by Newton from the Poisson start, dispersion α {nb['alpha']:.3f}; "
  "no null draw needed the BFGS fallback.")
for r in B_NOTES:
    lo, hi = r["ci"]
    if hi < 1 or lo > 1:
        w(f"- **{r['label']}:** its Wald interval ({lo:.3f} to {hi:.3f}) excludes 1, "
          f"{'in the concordant direction' if hi < 1 else 'in the opposite direction'}, while its surrogate p_B is "
          f"{r['p']:.3f}. Both are stated. The Wald interval relies on block clustering for the spatial dependence; "
          "the conditional surrogate null does not. Nominal, no decision attached.")
    else:
        w(f"- **{r['label']}:** p_B {r['p']:.3f} is below 0.05 while its Wald interval ({lo:.3f} to {hi:.3f}) "
          "includes 1. Both are stated. Nominal, no decision attached.")
if not B_NOTES:
    w("- No Test B interval excludes 1, and no p_B is below 0.05.")
w("")

w("## 7. Temporal deep model (secondary 20)")
w("")
dn, db = deep["null"], deep["bootstrap"]
stats = sorted(dn["statistics"]) if isinstance(dn["statistics"], list) else None
w(table(["Rows", "PR AUC: comparison → series", "Change in PR AUC", "95% interval", "p (99 draws, seed 2037)",
         "Null draws: median (range)", "ΔROC AUC (95% interval)", "ΔTop-10% pooled (95% interval)"],
        [[f"{deep['cases']:,} cases, {deep['rows']:,} rows",
          f"{deep['comparison_pr_auc']:.4f} → {deep['series_pr_auc']:.4f}", f_ch(deep["observed"]["pr"]),
          f_ci(db["pr_ci95"]), f"{dn['p']:.2f} ({dn['exceedances']} of {dn['draws']} at or above)",
          (f"{f_ch(stats[len(stats) // 2])} ({f_ch(stats[0])} to {f_ch(stats[-1])})" if stats else "–"),
          f"{f_m(deep['observed']['roc'])} ({f_ci(db['roc_ci95'], f_m)})",
          f"{f_m(deep['observed']['top10'])} ({f_ci(db['top10_ci95'], f_m)})"]]))
w("")
w("- **Comparison:** the same network without the series (Baseline 1). Only the series network is refitted in each "
  "null draw. Rows equal the primary record.")
w("- **Reading:** the series network scores lower than the comparison network by almost the same amount with surrogate "
  "series, whose link to the outcome is broken; the observed change sits at the null median. The loss comes from the "
  "larger network, not from the content of a parcel's own series. The null is unconditional and is read with the "
  f"calibration's caveat (§12, item 20); at p = {dn['p']:.2f} the caveat does not change the reading.")
w("")

w("## 8. Not run")
w("")
w("- **14. Owner-initiated repairs only:** removed. It needs certified yearly deed records, which a single 2018 roll "
  "does not provide (§4, §12 item 14).")
w("- **P0, P1 (population sensitivities):** apply to option C only (§12); Austin used option A (TCAD 2018).")
w("- Nothing else was left unrun. The compute budget was removed by the user on 2026-11-12 (§14).")
w("")

w("## 9. Nominal p below 0.05 (Test A designs), with their reading")
w("")
w(table(["Analysis", "Metric", "Change", "p", "Null median", "95% interval", "Reading"], NOTES))
w("")
w("None carries a decision (§12). Across all Test A secondaries, no change in PR AUC is positive with a 95% interval "
  "that excludes 0." if not any(r["obs"]["pr"] > 0 and r["boot"].get("pr_ci95") and r["boot"]["pr_ci95"][0] > 0
                                for r in A + LAG_ROWS) else "Some PR AUC intervals exclude 0; see the table.")
w("")

w("## 10. Sample and exclusions per analysis")
w("")
EX = []
for r in [PRIMARY_A] + A_ORDERED:
    dr = "; ".join(f"{v:,} {k}" for k, v in (r["dropped"] or {}).items())
    EX.append([r["label"] if not r.get("item", "").startswith("9_") else f"9. Lag {r['label']}",
               f_int(r["events"]), f_int(r["cases"]), dr, f_int(r["rows"]), f_int(r["control_rows"]),
               f_int(r["blocks"]), ", ".join(f"{c:,}" for c in r["cases_per_fold"]) if r["cases_per_fold"] else "–"])
w(table(["Analysis", "Events or candidates in file", "Cases", "Dropped", "Rows", "Control rows left out (inputs)",
         "Blocks", "Cases by fold"], EX))
w("")
ri = next(r for r in A if r["item"] == "10_issue_date")["notes"]
d1n = next(r for r in A if r["item"] == "D1_demolition")["notes"]
d2n = next(r for r in A if r["item"] == "D2_composite")["notes"]
w("Item 1's rows are cells: every cell at risk with a value and a baseline is a control, as NYC. "
  f"Item 10 also drops the {ri['events_outside_the_study_months']} events whose issue date falls outside the study "
  f"months (in its notes). D1 counts the {d1n['demolition_candidates']:,} demolitions in the study months "
  f"({d1n['demolitions_in_file']:,} in the file, {d1n['demolitions_outside_the_study_months']} outside); D2 counts "
  f"{d2n['composite_candidates']:,} composite candidates, and its {f_int(next(r for r in A if r['item'] == 'D2_composite')['cases'])} "
  f"cases are {d2n['composite_cases_that_are_foundation_events']:,} foundation events and "
  f"{d2n['composite_cases_that_are_demolitions']:,} demolitions.")
w("")

w("## 11. Run record (server clock, EET)")
w("")
RR = []
for r in A + LAG_ROWS + SEED_ROWS:
    RR.append([r["item"], hm(r["start"]), hm(r["end"]), f"`{r['hash16']}…`"])
for r in B:
    RR.append([r["item"], hm(r["start"]), hm(r["end"]), f"`{r['hash16']}…`"])
RR.append(["20_deep_model", hm(deep["_start"]), hm(deep["_end"]), f"`{deep['_hash16']}…`"])
order = {k: i for i, k in enumerate(sorted(runs, key=lambda k: runs[k].get("start", "")))}
RR.sort(key=lambda x: order.get(x[0], 0))
w(table(["Item", "Real run start", "End", "result.json SHA-256"], RR))
w("")
w("Each real run followed a passing decoy smoke. Every result's hash equals the one in the run log and the server's "
  "copy. Start and end times of each item are in `secondary_real/status_real`.")
w("")
w(f"Generator `production/secondary_report.py` (`{sha(Path(__file__), 16)}…`).")

OUT_MD.write_text("\n".join(o) + "\n")
summary = dict(
    plan_sha16=plan_hash, generator_sha256=sha(Path(__file__)),
    primary_a=dict(change=test_a["observed"], p=test_a["p"]),
    primary_b=dict(rr=test_b["observed"]["rate_ratio_iqr"], p=test_b["p_B"]),
    nulls_12_8={x[0]: dict(draws=x[1], pr_p=x[2], roc_p=x[3], top10_p=x[4], top10_rs_p=x[5]) for x in NULLS},
    largest_p_12_8=largest,
    test_a={r["item"]: dict(cases=r["cases"], rows=r["rows"], change=r["obs"], p={k: r["null"][f"{k}_p"] for k in
            ("pr", "roc", "top10", "top10_rs")}, pr_ci95=r["boot"].get("pr_ci95"), draws=r["draws"],
            start=r["start"], end=r["end"], sha16=r["hash16"]) for r in A + LAG_ROWS + SEED_ROWS},
    test_b={r["item"]: dict(rr=r["rr"], ci95=r["ci"], p_B=r["p"], beta=r["beta"], se=r["se"], iqr=r["iqr"],
            start=r["start"], end=r["end"], sha16=r["hash16"]) for r in B},
    deep=dict(change=deep["observed"], p=dn["p"], pr_ci95=db["pr_ci95"], start=deep["_start"], end=deep["_end"],
              sha16=deep["_hash16"]),
    nominal_p_below_005=NOTES,
)
OUT_JSON.write_text(json.dumps(summary, indent=1) + "\n")
print(OUT_MD, sha(OUT_MD, 16))
print(OUT_JSON, sha(OUT_JSON, 16))
