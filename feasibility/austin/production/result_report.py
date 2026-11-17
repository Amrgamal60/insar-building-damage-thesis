#!/usr/bin/env python3
"""Austin study (AUSTIN_PLAN.md): the result document.

Runs on the project PC only, after every run of §13 and the secondary report (2026-11-17). Standard library only;
run with python3 -I. It writes AUSTIN_RESULT.md beside the plan. It computes nothing new: no fit, no null, no
bootstrap. Every result number is read from the records below by this code; the plan's fixed settings and
the §11 readings are read from the frozen plan's own text. Each record's hash is checked against the plan's §15
or a hash list (SHA256SUMS*) written when the record was made, so the document can only describe those records.

Records read:
    real_20261112/{test_a,test_b,report_a,report_b}.json, real_20261112/{nulla,msr}/test_a.json   (real run, §13 step 5)
    production/check/{variogram_check_a,variogram_check_b,checks_run1_checks,checks_slips_checks,
                      checks_run1_sign_series_diagnostics,slip_screen,decoy_test_a,decoy_test_b}.json
    planted_signal/run_20261111/planted_signal_summary.json
    checkpoint1/{events_2018,audit_results_2018,link_check_2018}.json
    secondary_real/{AUSTIN_SECONDARY_RESULTS.md,secondary_summary.json}
"""
import hashlib
import json
import re
import statistics
import sys
from math import exp
from pathlib import Path

BASE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
OUT = BASE / "AUSTIN_RESULT.md"
PLAN = (BASE / "AUSTIN_PLAN.md").read_text()
FROZEN_P = BASE / "freeze" / "AUSTIN_PLAN_frozen.md"
FROZEN = FROZEN_P.read_text()
NYC_FROZEN_P = BASE.parent / "nyc" / "freeze" / "NYC_REPLICATION_PLAN_frozen.md"
REAL = BASE / "real_20261112"
CHECK = BASE / "production" / "check"
SEC = BASE / "secondary_real"


def sha(p, n=None):
    h = hashlib.sha256(Path(p).read_bytes()).hexdigest()
    return h[:n] if n else h


# ---------- frozen plans ----------
assert sha(FROZEN_P, 16) == "18627d8275d7859b", "frozen Austin plan changed"
assert sha(NYC_FROZEN_P, 16) == "59a2aa1a573ce8b7", "frozen NYC plan changed"

# ---------- hash lists written when the records were made ----------
LISTED = {}
for sums in [*sorted((BASE / "production").glob("SHA256SUMS*")), *sorted((BASE / "checkpoint1").glob("SHA256SUMS*")),
             *sorted((BASE / "planted_signal").glob("SHA256SUMS*"))]:
    for line in sums.read_text().splitlines():
        m = re.match(r"^([0-9a-f]{64})\s+\*?(.+)$", line.strip())
        if m:
            for root in (sums.parent, BASE):
                LISTED[(root / m.group(2)).resolve()] = m.group(1)

CHECKED = []


def verified(p):
    """The record's SHA-256 must equal its §15 entry (full hash, or the 8-character prefix §15 quotes) or its line in
    a hash list. Returns the parsed JSON (or text for .md)."""
    p = Path(p)
    h = sha(p)
    how = None
    if h in PLAN:
        how = "§15 (full hash)"
    elif LISTED.get(p.resolve()) is not None:
        assert LISTED[p.resolve()] == h, (p, "differs from its hash list")
        how = "hash list"
    elif f"`{h[:8]}…`" in PLAN or f"`{h[:16]}…`" in PLAN or f"{h[:16]}…" in PLAN:
        how = "§15 (prefix)"
    assert how, (p, h, "not recorded in §15 or a hash list")
    CHECKED.append((p.relative_to(BASE).as_posix(), h[:16], how))
    return json.loads(p.read_text()) if p.suffix == ".json" else p.read_text()


# ---------- formatting ----------
MINUS = "−"


def sgn(s):
    return s.replace("-", MINUS)


def f_ch(x):  # a change in PR AUC
    return sgn(f"{x:+.5f}")


def f_m(x, d=4):
    return sgn(f"{x:+.{d}f}")


def f_v(x, d=4):
    return sgn(f"{x:.{d}f}")


def f_p(p):
    return f"{p:.3f}"


def f_ci(ci, f=f_ch):
    return f"{f(ci[0])} to {f(ci[1])}"


def f_int(n):
    return f"{n:,}"


def f_med(x):  # a median count, which can end in .5
    return f"{x:,.0f}" if float(x).is_integer() else f"{x:,.1f}"


def pct(a, b, d=1):
    return f"{100 * a / b:.{d}f}%"


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def frozen_line(start):
    """One line of the frozen plan, found by its opening words (asserted unique)."""
    hits = [ln for ln in FROZEN.splitlines() if ln.startswith(start)]
    assert len(hits) == 1, (start, len(hits))
    return hits[0]


# ---------- records ----------
test_a = verified(REAL / "test_a.json")
test_b = verified(REAL / "test_b.json")
rep_a = verified(REAL / "report_a.json")
rep_b = verified(REAL / "report_b.json")
nulla = verified(REAL / "nulla" / "test_a.json")
msr = verified(REAL / "msr" / "test_a.json")
vg_a = verified(CHECK / "variogram_check_a.json")
vg_b = verified(CHECK / "variogram_check_b.json")
chk1 = verified(CHECK / "checks_run1_checks.json")
chk = verified(CHECK / "checks_slips_checks.json")
seas = verified(CHECK / "checks_run1_sign_series_diagnostics.json")["clay_seasonality"]
slips = verified(CHECK / "slip_screen.json")
dec_a = verified(CHECK / "decoy_test_a.json")
dec_b = verified(CHECK / "decoy_test_b.json")
planted = verified(BASE / "planted_signal" / "run_20261111" / "planted_signal_summary.json")
verified(BASE / "planted_signal" / "PLANTED_SIGNAL.md")
ev = verified(BASE / "checkpoint1" / "events_2018.json")
audit = verified(BASE / "checkpoint1" / "audit_results_2018.json")
link = verified(BASE / "checkpoint1" / "link_check_2018.json")
drought = verified(BASE / "checkpoint1" / "drought_check.json")
sec_md = SEC / "AUSTIN_SECONDARY_RESULTS.md"
verified(sec_md)
summ = verified(SEC / "secondary_summary.json")

for r in (test_a, test_b, rep_a, rep_b, nulla, msr):
    assert r["label"] == "REAL RUN" and r["mode"] == "real"
assert rep_a["primary_check"]["pass"] and rep_b["primary_check"]["pass"]
assert summ["plan_sha16"] == sha(FROZEN_P, 16)
assert summ["generator_sha256"] == sha(BASE / "production" / "secondary_report.py")

fa, ra = rep_a["foundation"], rep_a["remodel"]
fb, rb = rep_b["foundation"], rep_b["remodel"]
# the report's rebuilt analysis equals the decision record
assert fa["observed"]["pr"] == test_a["observed"] and fa["null"]["pr_p"] == test_a["p"]
assert fa["cases"] == test_a["cases"] and fa["rows"] == test_a["rows"] and fa["dropped"] == test_a["dropped"]
assert fa["null"]["statistics"]["pr"] == test_a["statistics"]
assert abs(fb["observed"]["rate_ratio_iqr"] - test_b["observed"]["rate_ratio_iqr"]) < 1e-12
assert fb["panel"] == test_b["panel"]
assert summ["primary_a"] == {"change": test_a["observed"], "p": test_a["p"]}
assert summ["primary_b"] == {"rr": test_b["observed"]["rate_ratio_iqr"], "p": test_b["p_B"]}
# the secondary-8 nulls ran on the same analysis
for r in (nulla, msr):
    assert (r["cases"], r["rows"], r["observed"]) == (test_a["cases"], test_a["rows"], test_a["observed"])
# Test B counts the events whose house is at risk at the event date (§8B): the demolition-censored ones are not counted
DEMO = "demolition-censored on or before the event date"
assert test_a["events_in_file"] - test_a["dropped"][DEMO] == test_b["panel"]["events_counted"]
assert ev["foundation"]["events"] == test_a["events_in_file"]

L = []
w = L.append

# ======================================================================================================== header
w("# Austin study: result")
w("")
w(f"**Plan:** `AUSTIN_PLAN.md`, frozen copy `freeze/AUSTIN_PLAN_frozen.md` (SHA-256 `{sha(FROZEN_P, 16)}…`; draft 10, "
  "approved and frozen 2026-11-07). Reference data option A (TCAD certified 2018 roll and parcel layer); study period "
  f"{ev['study_period'][0]} to {ev['study_period'][1]}. Primary Test A null: the conditional variogram null (b).")
w("")
w("**How this document is made:** `python3 -I production/result_report.py` writes it from the records of the real run, "
  "the checks and the secondary report. Every result number is read from those records by that code, and every "
  "record's hash is checked against §15 or the hash list written with it (section 11). The §11 readings are quoted from the frozen plan. Nothing here "
  "is a new analysis, and nothing in §4–§12 changed after the results were seen (§13 point 7).")
w("")
w("**What the outcome is:** the first recorded qualifying foundation-repair permit in the City's issued-permit records, "
  "dated by application date. All readings concern *recorded* repair permits, not independently validated physical "
  "damage, and not cause (§4, §11).")
w("")

# ======================================================================================================== summary
pr_hi = rep_a["bootstrap"]["per_analysis"]["foundation"]["pr_ci95"][1]
w("## Summary")
w("")
w(f"- **Test A (primary, decision): added held-out value of InSAR is NOT demonstrated in Austin.** Change in PR AUC "
  f"{f_ch(test_a['observed'])} (95% interval {f_ci(rep_a['bootstrap']['per_analysis']['foundation']['pr_ci95'])}), "
  f"p_A = {f_p(test_a['p'])} with the conditional null ({test_a['draws']} draws).")
w(f"- **Test B (key secondary, no decision): association not detected.** Rate ratio per IQR "
  f"{test_b['observed']['rate_ratio_iqr']:.3f} (95% interval {f_ci(test_b['observed']['rate_ratio_ci95'], lambda x: f'{x:.3f}')}), "
  f"p_B = {f_p(test_b['p_B'])}.")
w(f"- **Clay contrast: {chk['clay_contrast']['label']}**, so the §11 reading is the row \"clay contrast demonstrated\" "
  "for both tests, and \"Neither\" together.")
w(f"- **Beside the decision:** largest p across the nulls of §12.8 {summ['largest_p_12_8']:.3f}; "
  f"directional concordance {fa['concordance']['direction_label']}; remodel negative control: "
  f"{ra['specificity']['label'].lower()} (Test A) and {rb['label'].lower()} (Test B).")
w(f"- **Sign check: {chk1['sign_check']['result']}** in the first run ({f_m(chk1['sign_check']['difference_mm_yr'], 2)} mm/yr) "
  f"and **{chk['sign_check']['result']}** on the corrected values ({f_m(chk['sign_check']['difference_mm_yr'], 2)}). "
  "Outcome-blind diagnostics logged three findings; one of them, lasting cycle slips, was corrected before any outcome "
  "was compared. The sign was confirmed another way, by the clay seasonal curve (section 6).")
w("- **Secondary analyses:** no Test A secondary has a positive change in PR AUC with a 95% interval excluding 0, and no "
  "Test B secondary has p_B < 0.05 (section 8).")
w("")

# ======================================================================================================== 1 variogram
def vg_summary(v, lag_px, label, unit):
    bins = list(v["per_bin"].items())
    lag = bins[:16]
    long = bins[16:]
    r_l1 = lag[0][1]["median_ratio"]
    r_l2 = [b[1]["median_ratio"] for b in lag[1:]]
    tot = v["lags_1_16_inside"][1] + v["long_bins_inside"][1]
    inside = v["lags_1_16_inside"][0] + v["long_bins_inside"][0]
    assert inside + v["below"] + v["above"] == tot
    far = [b[1]["median_ratio"] for b in bins if re.match(r"^1[5-9]-|^19-20", b[0])]
    out = [
        f"- **{label}:** the {v['draws']} surrogates of the null file (`{v['surrogates_sha256'][:8]}…`; neighbour count "
        + ", ".join(f"{k} in {n}" for k, n in v["chosen_k"]["counts"].items())
        + f" draws), {len(v['windows'])} {unit}s (seed {v['seed']}): " + ", ".join(v["windows"]) + ".",
        f"  - **Lags 1–16 ({lag_px}):** observed semivariance inside the surrogates' 95% range at "
        f"{v['lags_1_16_inside'][0]} of {v['lags_1_16_inside'][1]} {unit}-lags. Median surrogate / observed: "
        f"{r_l1:.2f}× at lag 1, {min(r_l2):.2f}–{max(r_l2):.2f}× at lags 2–16.",
        f"  - **1 km bins from {long[0][0].split('-')[0]} to 20 km:** inside at {v['long_bins_inside'][0]} of "
        f"{v['long_bins_inside'][1]}. Median surrogate / observed {long[0][1]['median_ratio']:.2f}× in the first bin, "
        f"{min(far):.2f}–{max(far):.2f}× at 15–20 km.",
        f"  - **All {tot} {unit}-bins:** {inside} inside, {v['below']} below and {v['above']} above the range.",
    ]
    return out


w("## 1. Variogram checks (reported first, §10)")
w("")
w("As NYC: the observed semivariance in each lag bin against the 2.5–97.5% range of the surrogates. Whatever they show, "
  "no null is changed (§10). Full tables by distance: appendix A.")
w("")
for s in vg_summary(vg_a, "30–480 m", "Test A, conditional null", "window"):
    w(s)
for s in vg_summary(vg_b, "250 m to 4 km", "Test B null (seed 2034)", "quarter"):
    w(s)
w("- **Reading** (as recorded in §15 before the real run):")
w("  - The pattern is NYC's: surrogates rougher than the field at the first lags, and too little long-range semivariance "
  "beyond a few km. The §10 null matches the residual's short-lag variogram only, so long-range structure in velocity that "
  "the baseline features do not explain is under-represented in the surrogates. The frozen plan does not name this as a "
  "limitation; it is reported here with Test A.")
w("  - Test A's counts inside are low because its 95% ranges are very narrow with this many pixels; the ratios carry more "
  "information than the counts.")
w("  - What this means for Test A is read with the planted-signal check (section 5), not by changing the null.")
w("")

# ======================================================================================================== 2 decision
fn = fa["null"]
ci = rep_a["bootstrap"]["per_analysis"]["foundation"]
w("## 2. Decision (§11)")
w("")
w("**Rule:** " + frozen_line("Only Test A, the primary analysis, carries"))
w("Added value is demonstrated if and only if, in the primary analysis (single-family parcels, logistic regression, "
  "Baseline 1 + x/y, 24-month window), the change in PR AUC is positive **and** p_A < 0.05.")
w("")
pos = test_a["observed"] > 0
w(f"- **Test A: added held-out value of InSAR is NOT demonstrated in Austin.** The change in PR AUC is "
  f"{'positive' if pos else 'not positive'} ({f_ch(test_a['observed'])}), and p_A = {f_p(test_a['p'])} "
  f"({test_a['exceedances']} of {test_a['draws']} draws at or above the observed change; seed 2027).")
assert not pos and test_a["p"] >= 0.05 and not test_a["meets_rule"]
w("- " + frozen_line("Otherwise added value is **not demonstrated**"))
w("")
w(table(
    ["Metric", "Baseline 1 + x/y", "+ velocity", "Change", "p (conditional null)", "Null median", "95% refit-bootstrap interval"],
    [
        ["PR AUC (primary)", f_v(fa["baseline"]["pr"], 5), f_v(fa["velocity"]["pr"], 5), f_ch(fa["observed"]["pr"]),
         f_p(fn["pr_p"]), f_ch(fn["pr_null_median"]), f_ci(ci["pr_ci95"])],
        ["ROC AUC", f_v(fa["baseline"]["roc"]), f_v(fa["velocity"]["roc"]), f_m(fa["observed"]["roc"]),
         f_p(fn["roc_p"]), f_m(fn["roc_null_median"]), f_ci(ci["roc_ci95"], f_m)],
        ["Top-10% capture, pooled", f_v(fa["baseline"]["top10"]), f_v(fa["velocity"]["top10"]), f_m(fa["observed"]["top10"]),
         f_p(fn["top10_p"]), f_m(fn["top10_null_median"]), f_ci(ci["top10_ci95"], f_m)],
        ["Top-10% capture within the risk set", f_v(fa["baseline"]["top10_rs"]), f_v(fa["velocity"]["top10_rs"]),
         f_m(fa["observed"]["top10_rs"]), f_p(fn["top10_rs_p"]), f_m(fn["top10_rs_null_median"]), "not bootstrapped (as fixed)"],
    ]))
w("")
st = sorted(test_a["statistics"])
w(f"- **Null draws** (PR AUC change): median {f_ch(statistics.median(st))}, maximum {f_ch(st[-1])}. "
  f"{test_a['exceedances']} of {test_a['draws']} draws lie at or above the observed change.")
w(f"- **Interval:** refit block bootstrap, {rep_a['bootstrap']['resamples']:,} resamples over the "
  f"{rep_a['bootstrap']['universe_blocks']} blocks of 2 km holding rows of either analysis; "
  f"{ci['resamples_without_value']} resamples lacked a value. "
  f"It excludes changes above {f_ch(pr_hi)}, which is {pct(pr_hi, fa['baseline']['pr'])} of the baseline's PR AUC "
  f"({f_v(fa['baseline']['pr'], 3)}). §11 set no number for a \"useful\" gain, so this upper limit is reported as it is. "
  f"PR AUC here is average precision on the sampled risk sets (1 case and on average "
  f"{(test_a['rows'] - test_a['cases']) / test_a['cases']:.1f} controls each, after controls missing an input were dropped), "
  "not city-wide precision.")
w("")
c = fa["concordance"]
w(f"**Directional concordance** (§11; {f_int(c['risk_sets'])} risk sets, {c['risk_sets_without_controls']} without controls; "
  "below 0 is concordant):")
w(f"- Standardised: median of (case − median of its controls) {f_m(c['direction_median'])}, so the label is "
  f"**{c['direction_label']}**; {pct(c['direction_share_below_0'], 1)} of risk sets lie below 0.")
w(f"- Raw: median {f_m(c['direction_raw_mm_yr_median'], 3)} mm/yr ({pct(c['direction_raw_share_below_0'], 1)} below 0). "
  f"Median velocity of cases {c['event_raw_mm_yr_median']:.2f} mm/yr, of controls {c['control_raw_mm_yr_median']:.2f} mm/yr.")
w(f"- Coefficient of the standardised velocity, logistic model on all rows: {f_m(c['coef_field_all_rows'])}.")
w("- Both medians are close to zero: case and control velocities barely differ.")
w("")
w(f"**Largest p across the nulls of §12.8:** {summ['largest_p_12_8']:.3f} (section 4).")
w("")

# ======================================================================================================== 3 test B
ob = test_b["observed"]
pb = test_b["panel"]
bfb = rep_b["bootstrap"]
w("## 3. Test B (key secondary, prespecified reading, no decision)")
w("")
w(f"- **Association not detected:** rate ratio per IQR ({ob['velocity_iqr']:.1f} mm/yr) **{ob['rate_ratio_iqr']:.3f}**, "
  f"95% interval {f_ci(ob['rate_ratio_ci95'], lambda x: f'{x:.3f}')} (Wald, errors clustered by 2 km block); "
  f"β = {f_m(ob['beta'], 5)} per mm/yr (clustered SE {ob['clustered_se']:.5f}).")
assert not test_b["detected"] and test_b["p_B"] >= 0.05
w(f"- **p_B = {f_p(test_b['p_B'])}** ({test_b['exceedances']} of {len(test_b['statistics'])} draws with |β| at or above the "
  "observed; seed 2034). p_B is nominal secondary evidence.")
w(f"- **Direction:** {'opposite (rate ratio above 1)' if ob['rate_ratio_iqr'] > 1 else 'concordant (rate ratio below 1)'}; "
  "the estimate is close to 1.")
lr = bfb["per_analysis"]["foundation"]["log_rr_iqr_ci95"]
w(f"- **Block bootstrap** ({bfb['resamples_used']:,} resamples over {bfb['universe_blocks']} blocks, "
  f"{bfb['failed_fits']['foundation']['count']} failed fits): log rate ratio per IQR {f_ci(lr, lambda x: f_m(x, 3))}, "
  f"i.e. a rate ratio of {exp(lr[0]):.3f}–{exp(lr[1]):.3f}.")
w(f"- **Panel:** {f_int(pb['rows_used'])} cell-quarter rows; the model keeps {f_int(ob['rows_used'])} rows in "
  f"{f_int(ob['cells_used'])} cells, {ob['quarters_used']} quarters and {ob['blocks_used']} blocks "
  f"({f_int(ob['all_zero_cells_input'])} cells with no event in any quarter drop out under the cell fixed effects).")
w("")

# ======================================================================================================== 4 beside
w("## 4. Reported beside the decision (§11, §12.8)")
w("")
w("### Nulls of §12.8 (change in PR AUC; same analysis and observed change)")
w("")
pn = rep_a["permutation_nulls"]


def med(r):
    return f_ch(statistics.median(r["statistics"]))


w(table(
    ["Null", "Draws", "p, PR AUC", "p, ROC AUC", "p, Top-10% pooled", "p, Top-10% own set", "Null median, PR AUC"],
    [
        ["Conditional variogram null (primary, §10)", test_a["draws"], f_p(fn["pr_p"]), f_p(fn["roc_p"]), f_p(fn["top10_p"]),
         f_p(fn["top10_rs_p"]), f_ch(fn["pr_null_median"])],
        ["Null (a): NYC variogram null, unconditional (the calibration found it too lenient, §10)", nulla["draws"],
         f_p(nulla["p"]), "–", "–", "–", med(nulla)],
        ["Free permutation", f_int(pn["free"]["draws"]), f_p(pn["free"]["pr_p"]), f_p(pn["free"]["roc_p"]),
         f_p(pn["free"]["top10_p"]), f_p(pn["free"]["top10_rs_p"]), f_ch(pn["free"]["pr_null_median"])],
        ["Within-block permutation", f_int(pn["within-block"]["draws"]), f_p(pn["within-block"]["pr_p"]),
         f_p(pn["within-block"]["roc_p"]), f_p(pn["within-block"]["top10_p"]), f_p(pn["within-block"]["top10_rs_p"]),
         f_ch(pn["within-block"]["pr_null_median"])],
        ["MSR", msr["draws"], f_p(msr["p"]), "–", "–", "–", med(msr)],
    ]))
w("")
w(f"Largest p: **{summ['largest_p_12_8']:.3f}**. Null (a) and MSR were run for PR AUC only (§15). Their p's are secondary 8 only.")
w("")

sp = ra["specificity"]
rn = ra["null"]
rci = rep_a["bootstrap"]["per_analysis"]["remodel"]
w("### Specificity check, Test A: remodel negative control")
w("")
w(f"- The primary analysis repeated unchanged on {f_int(ra['events_in_file'])} remodel control events (§14 rule, "
  f"controls seed 2030, the same {rn['draws']} surrogates): {f_int(ra['cases'])} cases, {f_int(ra['rows'])} rows. Dropped: "
  + "; ".join(f"{n} {k}" for k, n in ra["dropped"].items()) + ".")
w(f"- Baseline PR AUC {f_v(ra['baseline']['pr'])}. **Change {f_ch(sp['change_pr'])}, 95% interval {f_ci(sp['ci95'])}, "
  f"p = {f_p(sp['p'])}. Label: {sp['label']}.**")
w(f"- Share of the foundation change: {f_m(sp['share_of_foundation_change'], 2)}. The foundation change is "
  f"{'positive' if sp['foundation_change_positive'] else 'negative'}, so this share has no useful reading; it is reported as computed.")
w(f"- Its other metrics (nominal): ROC AUC {f_m(ra['observed']['roc'])} (p {f_p(rn['roc_p'])}); pooled top-10% "
  f"{f_m(ra['observed']['top10'])} (p {f_p(rn['top10_p'])}); top-10% within the risk set {f_m(ra['observed']['top10_rs'])} "
  f"(p {f_p(rn['top10_rs_p'])}).")
if rn["top10_rs_p"] < 0.05:
    w("  The last p is below 0.05, on one of four uncorrected metrics of the negative control. §11 labels the negative "
      "control by PR AUC only, so it carries no label.")
dp = rep_a["bootstrap"]["difference_pr"]
w(f"- **Direct comparison:** foundation change minus remodel change, on the same {dp['resamples_used']:,} resampled blocks: "
  f"{f_ch(dp['observed'])}, 95% interval {f_ci(dp['ci95'])}. No difference is claimed.")
w("- \"Not detected\" does not show that remodel permits have no gain, and does not prove the foundation result free of "
  "owner, income or reporting bias (§11).")
w("")
ro = rb["observed"]
rpn = rb["panel"]
w("### Specificity check, Test B: remodel counts")
w("")
w(f"- Remodel events: {f_int(rpn['events_counted'])} counted, {f_int(rpn['events_counted_in_quarters'])} inside the "
  f"{ob['quarters_input']} quarters, {f_int(rpn['events_in_rows_used'])} in rows used. Exposure: {rpn['exposure']}.")
w(f"- The model keeps {f_int(ro['rows_used'])} rows in {f_int(ro['cells_used'])} cells, {ro['quarters_used']} quarters and "
  f"{ro['blocks_used']} blocks.")
rlr = bfb["per_analysis"]["remodel"]["log_rr_iqr_ci95"]
w(f"- **Rate ratio per IQR {ro['rate_ratio_iqr']:.3f}, 95% interval {f_ci(ro['rate_ratio_ci95'], lambda x: f'{x:.3f}')}**; "
  f"bootstrap interval of the log rate ratio {f_ci(rlr, lambda x: f_m(x, 3))}. "
  f"**p = {f_p(rb['p_B'])}** ({rb['exceedances']} of {rb['draws']}, seed 2035). **Label: {rb['label']}.**")
dl = bfb["difference_log_rr_iqr_ci95"]
w(f"- **Direct comparison:** foundation minus remodel log rate ratio per IQR, on the same {bfb['resamples_used']:,} resampled "
  f"blocks: {f_m(bfb['observed_difference_log_rr_iqr'], 3)}, 95% interval {f_ci(dl, lambda x: f_m(x, 3))}. No difference is claimed.")
w("")

# ======================================================================================================== reading
w("### Reading, as fixed in §11")
w("")
w(f"The clay contrast was {chk['clay_contrast']['label']} (section 6), so the rows read:")
w("")
w(frozen_line("| Test | Decision | Label | Reading |"))
w("|---|---|---|---|")
w(frozen_line("| A | Not demonstrated | Clay contrast demonstrated |"))
w(frozen_line("| B | Not detected | Clay contrast demonstrated |"))
w("")
w("Together (Test B never changes the decision): " + frozen_line("- **Neither:**")[2:])
w("")

# ======================================================================================================== 5 planted
w("## 5. Sensitivity of Test A at Austin's size (planted-signal check)")
w("")
m = re.search(r"Cells 4–6 correspond to odds ratios of ([\d.]+), ([\d.]+) and ([\d.]+) per interquartile range", PLAN)
assert m
ors = dict(zip(("4", "5", "6"), m.groups()))
cells = planted["cells"]
n_ev = cells["4"]["synthetic_events"][0]
assert n_ev == test_a["cases"]
w(f"Fixed in §14 (2026-11-10) and run before the real run: synthetic outcomes on the real field, {f_int(n_ev)} events per "
  f"dataset (the real run's case count), {planted['draws']} null draws, {planted['projection']['datasets_per_cell']} "
  "datasets per cell. Test A is not demonstrated, "
  "so §14 reports cells 4–6 as the test's sensitivity:")
w("")
w(table(
    ["Cell", "Odds ratio per IQR", "Meets the §11 rule [95% Wilson]", "Mean observed change [95% t]", "Paired bias [95% t]"],
    [[sgn(cells[k]["label"]), ors[k],
      f"{cells[k]['meets_rule']}/{cells[k]['datasets']} = {100 * cells[k]['share']:.0f}% "
      f"[{100 * cells[k]['wilson95'][0]:.1f}, {100 * cells[k]['wilson95'][1]:.1f}]",
      f"{f_ch(cells[k]['observed']['mean'])} [{f_ci(cells[k]['observed']['ci95'])}]",
      f"{f_ch(cells[k]['paired_bias']['mean'])} [{f_ci(cells[k]['paired_bias']['ci95'])}]"] for k in ("4", "5", "6")]))
w("")
fp_rates = ", ".join(f"{100 * cells[k]['share']:.0f}%" for k in ("1", "2", "3"))
w(f"Cells 1–3 (no velocity effect; rejection rates {fp_rates}) are in "
  "`planted_signal/PLANTED_SIGNAL.md`; §14 reports them beside a demonstrated result only.")
w("")

# ======================================================================================================== 6 checks
sc1, sc = chk1["sign_check"], chk["sign_check"]
cc = chk["clay_contrast"]
cov = chk["coverage"]["L24"]
fpp = chk["full_period_pixels"]
w("## 6. Checks before outcomes (§7, §13 steps 3–4)")
w("")
w(f"- **Sign check (§7): {sc['result']}.** First run: landfill median {f_m(sc1['landfill_median_mm_yr'], 2)} mm/yr "
  f"against a subset median of {f_m(sc1['subset_median_mm_yr'], 2)} (difference {f_m(sc1['difference_mm_yr'], 2)}; "
  f"{f_int(sc1['valid_footprint_pixels'])} valid footprint pixels at {sc1['perimeters_with_valid_pixels']} of "
  f"{sc1['perimeters_used']} perimeters). By §7 work stopped until the cause was found and logged.")
w("  - **Diagnostics** (outcome-blind, §15) logged three findings: a west–east regional gradient, with most landfills "
  "east of the subset's median; no detectable pooled settlement at the old landfills; and lasting phase-unwrapping cycle "
  "slips (steps near one half-wavelength) in a north-east zone holding the "
  f"active landfills. The slip screen found slips at {f_int(slips['house_pixels_with_slip'])} of "
  f"{f_int(slips['house_pixels'])} house pixels ({pct(slips['house_pixels_with_slip'], slips['house_pixels'])}; "
  f"{f_int(slips['houses_on_slip_pixels'])} houses).")
w("  - **Correction:** decided by the user on 2026-11-11 (§14, \"Lasting cycle slips\"), before any outcome was compared: "
  "a pixel has no value in a window that contains one of its slips. All analyses use the corrected fields; the first "
  "run's fields serve the slip-rule sensitivity analysis (secondary report).")
w(f"  - **On the corrected values:** landfills {f_m(sc['landfill_median_mm_yr'], 2)} against "
  f"{f_m(sc['subset_median_mm_yr'], 2)} mm/yr (difference {f_m(sc['difference_mm_yr'], 2)}): still **{sc['result']}**. "
  "The result stands as recorded.")
hl = seas["high_minus_low"]
w(f"  - **The sign itself is confirmed** another way: the seasonal curve of the high and very high clay classes minus the "
  f"low class has its trough at day of year {hl['trough_day_of_year']} (95% interval "
  f"{seas['trough_day_of_year_interval_95'][0]}–{seas['trough_day_of_year_interval_95'][1]}), in late September: clay "
  "shrinking in the dry season, as expected if positive is toward the satellite.")
w(f"- **Clay contrast (§7): {cc['label']}.** High and very high classes minus the low class, median full-period seasonal "
  f"amplitude: {f_m(cc['statistic_mm'], 2)} mm, 95% block-bootstrap interval {cc['interval_95'][0]:.2f} to "
  f"{cc['interval_95'][1]:.2f} ({cc['blocks']} blocks of 2 km, {f_int(cc['draws'])} draws, seed {cc['seed']}). By class: "
  + ", ".join(f"{k} {v['median_amplitude_mm']:.2f} mm ({f_int(v['used'])} parcels)" for k, v in cc["by_class"].items()) + ".")
w(f"- **Coverage (§7):** in the 24-month windows a median of {f_med(cov['valid']['median'])} of "
  f"{f_int(fpp['house_pixels'])} house pixels and {f_med(cov['houses_valid']['median'])} of "
  f"{f_int(ev['population_houses'])} houses have a value. The construction mask removes a median of "
  f"{f_med(cov['construction_mask']['median'])} house pixels per window, the largest loss.")
da, db = dec_a, dec_b
w(f"- **Decoy run (§13 step 4; a code check, not a result):** each event moved to a random house (seed {da['decoy_seed']}). "
  f"Test A: {f_int(da['cases'])} decoy cases, change {f_ch(da['observed'])}, p {f_p(da['p'])}. Test B: rate ratio per IQR "
  f"{db['observed']['rate_ratio_iqr']:.2f}, p_B {f_p(db['p_B'])}. Both ran end to end with no code error; nothing was changed.")
la = audit["label_audit"]["share"]
da_ = audit["demolition_audit"]["share"]
lk = link["link_check_all_dates"]
sv = ev["survivorship"]
w(f"- **Checks at checkpoint 1** (permits only, no InSAR; design summary points 8 and 11): label audit {la['count']}/{la['denominator']} "
  f"foundation repairs ({la['percent']:.0f}%, exact 95% CI {la['clopper_pearson_95'][0]}–{la['clopper_pearson_95'][1]}; "
  f"one AI reader, no engineer); parcel link check: {lk['matched_any_reference_parcel']['percent']:.1f}% of "
  f"{f_int(lk['permits'])} qualifying permits match a 2018 parcel and "
  f"{lk['matched to the primary population']['percent']:.1f}% the primary population; survivorship: "
  f"{sv['events_at_houses_not_in_2026_detached_population']} events ({sv['events_percent']:.1f}%) are at houses no longer in "
  f"the 2026 detached population; demolition audit: {da_['count']}/{da_['denominator']} censoring permits demolish the main "
  f"house ({da_['percent']:.0f}%).")
dr = drought["results"]["rules_1_2"]
w(f"- **Permits and drought (§4, reported only):** Spearman ρ = {f_m(dr['spearman_rho'], 2)} (p = {dr['p_two_sided']:.3f}, "
  f"{dr['n_years']} years) between repair permits by issue year (rules 1–2, {drought['issue_years'][0]}–"
  f"{drought['issue_years'][1]}) and the previous year's mean drought index (NOAA division {drought['climate_division']}).")
slc = link["survivorship_link_check"]
grp = {True: {}, False: {}}
for r in slc:
    grp[r["prop_id_2018_in_2026_roll"]][r["year"]] = r
assert grp[True].keys() == grp[False].keys()
n_in = {r["houses"] for r in grp[True].values()}
n_out = {r["houses"] for r in grp[False].values()}
assert len(n_in) == 1 and len(n_out) == 1
w(f"- **Survivorship link check (§5; option A: 2018 property ID present or absent in the 2026 roll):** permits of all "
  "types per 100 house-years, as recorded; §5 reads a falling rate at absent accounts as permits lost to key changes.")
w("")
w(table(["Year", f"ID in the 2026 roll ({f_int(n_in.pop())} houses)", f"ID absent ({f_int(n_out.pop())} houses)"],
        [[y, f"{grp[True][y]['permits_per_100_house_years']:.1f}", f"{grp[False][y]['permits_per_100_house_years']:.1f}"]
         for y in sorted(grp[True])]))
w("")

# ======================================================================================================== 7 sample
w("## 7. Sample and exclusions")
w("")
fev = ev["foundation"]
w(f"- **Events (§4):** {f_int(fev['events'])} first qualifying foundation-repair permits on the {f_int(ev['population_houses'])} "
  "eligible detached houses, one per house, dated by application date. By year: "
  + ", ".join(f"{y} {n}" for y, n in fev["events_by_year"].items()) + ".")
w(f"- **Test A:** {f_int(test_a['cases'])} cases. Dropped: "
  + "; ".join(f"{n} {k}" for k, n in test_a["dropped"].items())
  + f". {f_int(test_a['rows'])} case and control rows ({f_int(test_a['control_rows_dropped_missing_inputs'])} control rows "
  f"dropped for missing inputs). Cases by fold: {', '.join(str(x) for x in test_a['cases_per_fold'])}. By year: "
  + ", ".join(f"{y} {n}" for y, n in test_a["cases_by_year"].items()) + ".")
lost = test_a["dropped"]["no value in the window"]
w(f"  - {pct(lost, test_a['events_in_file'])} of events are lost for want of an InSAR value in their 24-month window, mostly "
  "to the construction mask (section 6).")
w(f"- **Test B:** {f_int(pb['events_counted'])} events counted (the {test_a['dropped'][DEMO]} demolition-censored events are "
  f"not at risk), {f_int(pb['events_counted_in_quarters'])} inside the {ob['quarters_input']} quarters, "
  f"{f_int(pb['events_in_rows_used'])} in rows used and {pb['events_in_rows_without_value']} in rows without a value.")
w("")

# ======================================================================================================== 8 secondary
ta = summ["test_a"]
tb = summ["test_b"]
gain = [k for k, r in ta.items() if r["change"]["pr"] > 0 and r.get("pr_ci95") and r["pr_ci95"][0] > 0]
nom = summ["nominal_p_below_005"]
neg = [r for r in nom if r[2].startswith(MINUS)]
pb_small = [k for k, r in tb.items() if r["p_B"] < 0.05]
excl = [(k, r) for k, r in tb.items() if r["ci95"][0] > 1 or r["ci95"][1] < 1]
dpm = summ["deep"]


def item_name(k):  # "15_lag_12" -> "item 15, lag 12"
    m = re.match(r"^(\d+|D\d)_(.+)$", k)
    return f"item {m.group(1)}, {m.group(2).replace('_', ' ')}" if m else k.replace("_", " ")
w("## 8. Secondary analyses (§12; reported, no decision attached)")
w("")
w(f"Full report: `secondary_real/AUSTIN_SECONDARY_RESULTS.md` (SHA-256 `{sha(sec_md, 16)}…`), summary "
  f"`secondary_real/secondary_summary.json`. Every p there is nominal and uncorrected.")
w("")
with_ci = [k for k, r in ta.items() if r.get("pr_ci95")]
w(f"- **Test A secondaries** ({len(ta)} analyses, counting each lag and fold seed; {len(with_ci)} have a bootstrap "
  f"interval, the fold seeds have none, as fixed in §15): {len(gain)} with a positive change in PR AUC whose 95% interval excludes 0.")
w(f"- **Nominal p < 0.05** on any metric: {len(nom)} cases. {len(neg)} have a negative change (the null draws were lower "
  f"still), so they are not gains; the other {len(nom) - len(neg)} are positive with intervals that include 0 or no interval.")
w(f"- **Test B secondaries** ({len(tb)} analyses): {len(pb_small)} with p_B < 0.05. Wald intervals excluding 1: "
  + ("; ".join(f"{item_name(k)} (rate ratio {r['rr']:.3f}, {'above 1, the opposite direction' if r['rr'] > 1 else 'below 1, concordant'}, p_B {f_p(r['p_B'])})" for k, r in excl)
     if excl else "none") + ".")
w(f"- **Deep model (item 20):** change in PR AUC {f_ch(dpm['change']['pr'])} (95% interval {f_ci(dpm['pr_ci95'])}), "
  f"p {dpm['p']:.2f}.")
w("- **Not run:** item 14 (sale-triggered repairs; removed under §4: it needs yearly deed records, which the single "
  "2018 roll does not provide) and P0–P1 (defined for option C only). No analysis is \"not run\" for lack of time: the user removed the "
  "compute budget on 2026-11-12 (§14).")
w("")

# ======================================================================================================== 9 deviations
w("## 9. Deviations from the frozen plan (§14)")
w("")
sec14 = PLAN.split("\n## 14. Deviations log", 1)[1].split("\n## 15.", 1)[0]
devs = re.findall(r"^- \*\*(\d{4}-\d\d-\d\d)\. (.+?)\*\*", sec14, flags=re.M)
assert devs
for d, t in devs:
    w(f"- {d}: {t}")
w("")
w("Each is logged with its reason and approval in §14. All were decided before any outcome was compared, except the "
  "compute budget, which changed no analysis.")
w("")
w("§15 also records authors' choices made after the primary result but before the outcome each one concerns, each with "
  "its time: the MSR code (secondary 8), the details §12 leaves open for the secondary runners, the deep model's settings, "
  "and the move of one secondary surrogate file from the CPU to the GPU engine. None changes a rule of §4–§12.")
w("")

# ======================================================================================================== 10 limits
w("## 10. Limits of this result")
w("")
w("- The outcome is recorded permits. Unpermitted repairs and unrepaired damage are not seen (§4).")
w(f"- {pct(lost, test_a['events_in_file'])} of events had no InSAR value in their window; Test A rests on "
  f"{f_int(test_a['cases'])} cases.")
w("- The conclusion concerns 24-month trend velocity in the logistic model; other indicators, windows and models are the "
  "secondary analyses (§11).")
w("- The surrogates under-represent long-range variance (section 1). The planted-signal check measured the test's "
  "behaviour on the real field at this size (section 5).")
w("- The calibration (§10) found the conditional null may be conservative at Austin's size and has less power than "
  "null (a). The other four nulls of §12.8 are reported in section 4.")
w("- The sign check is \"not below\" before and after the slip correction. Only the slips were corrected; the other two "
  "findings are described, not removed (section 6).")
w("- One ascending track gives line-of-sight motion only (plan, outstanding data limitations).")
w("")

# ======================================================================================================== 11 records
w("## 11. Records")
w("")
runs = [("Test A (decision)", test_a), ("Test B", test_b), ("Test A report (beside items)", rep_a),
        ("Test B report", rep_b), ("Null (a), secondary 8", nulla), ("MSR, secondary 8", msr),
        ("Decoy Test A", dec_a), ("Decoy Test B", dec_b)]
w("Run on the processing server (`run_tests.py` `020c67e0…`, `run_report.py` `ea0315b6…`); records copied to the PC with the "
  "same hashes. Every record below was checked by this generator:")
w("")
w(table(["Record", "SHA-256 (16)", "Checked against"], [[f"`{p}`", f"`{h}`", how] for p, h, how in CHECKED]))
w("")
w(table(["Run", "Finished (EET)"], [[n, r["finished"].replace(" EET", "")] for n, r in runs]))
w("")
assert test_a["sources"]["run_tests.py"].startswith("020c67e0") and rep_a["sources"]["run_report.py"].startswith("ea0315b6")
w("**Reproduce this document:** `python3 -I production/result_report.py` (two runs give the same bytes).")
w("")

# ======================================================================================================== appendix
w("## Appendix A. Variogram checks by distance")
w("")
for name, v in (("Test A (conditional null; 30 m pixels)", vg_a), ("Test B (250 m cells)", vg_b)):
    w(f"**{name}:** windows inside the surrogates' 95% range, and the median over windows of surrogate / observed.")
    w("")
    w(table(["Distance", f"Windows inside (of {len(v['windows'])})", "Median surrogate / observed"],
            [[k, b["windows_inside"], f"{b['median_ratio']:.2f}"] for k, b in v["per_bin"].items()]))
    w("")

text = "\n".join(L).rstrip() + "\n"
assert "−" in text and "TODO" not in text
OUT.write_text(text)
print(OUT, sha(OUT, 16), len(text.splitlines()), "lines;", len(CHECKED), "records checked")
