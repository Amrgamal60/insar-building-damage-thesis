"""Write HAZARD_TX_RESULT.md from the real run's results.json (plan §12 step 7).

Generated, not hand-copied: every number comes from <run_dir>/real/results.json, <run_dir>/decoy/results.json and
real/events_<city>.json. The script asserts the frozen plan's hash, and the code hashes recorded in results.json
against freeze/MANIFEST.sha256. It changes no number and makes no decision; the reading is the one run_ht.py wrote
(plan §8).

Usage: python -I scripts/result_report.py real_20261122
       python -I scripts/result_report.py --synthetic step0/synthetic_run2_20261122 OUT.md   (layout check only)
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
FROZEN = "d6f25de61ac85dd81f6e46f6a66b6ce71901bc741ce0b30156749a31ff570224"
CITIES = {"dallas": "Dallas", "sanantonio": "San Antonio"}
CODE = ("run_ht.py", "build_events.py", "hx_infer.py", "ht_core.py", "planted_flex.py", "planted_ht.py")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def manifest():
    return {name: h for h, name in (ln.split(maxsplit=1) for ln in (HERE / "freeze/MANIFEST.sha256").read_text().splitlines())}


def b(x, edge):
    return edge if x is None else f"{x:.2f}"


def iv(d, lv):
    return f"{b(d[f'lo{lv}'], '<0.2')} to {b(d[f'hi{lv}'], '>5')}"


def fp(p):
    return "<0.0001" if p < 1e-4 else f"{p:.4g}"


def pct(x, k=1):
    return f"{100 * x:.{k}f}%"


def n(x):
    return f"{x:,.0f}"


def interpretation(w, R, P, S, e, num, TB, s2, s3, s5, s6, s16, ch):
    """§6, written after the real result was seen (2026-11-23). Every number is read from results.json. The answer is
    the frozen §8 reading; everything else here is descriptive and claims nothing beyond it."""
    F, T, s1 = R["flow"], P["T_by_city"], S["s1_city"]
    dl = {c: T[c]["dl_by_assignment"] for c in CITIES}
    pos = {c: sum(v > 0 for v in dl[c]) for c in CITIES}
    rt = S["s1_ratio"]["ratio_dallas_over_sanantonio"]
    fl_ev = {c: num[c]["events_flagged"] for c in CITIES}
    pe = num["pooled"]
    sa = T["sanantonio"]["also_reported"]
    s13 = {k: d[k] for k, d in S["s13_not_chosen"].items()}
    s15, s17 = S["s15_current_layer"]["adjusted"], S["s17_dallas_broad"]["pooled"]
    s10, s9, s4 = S["s10_edges"]["adjusted"], S["s9_map_user"]["adjusted"], S["s4_risk"]["U"]
    yrs = S["s8_by_year"]
    s12 = S["s12_three_cities"]

    w("*Written 2026-11-23, after the real result was seen. Every number below is read from `results.json`.*")
    w("")
    w("**Answer to the prespecified question (plan §8).** The reading is **\"" + P["reading"] + "\"**. The hazard flag "
      f"(β classes 2–3) was associated with more first foundation-repair permits beyond the flexible Baseline 1: pooled "
      f"adjusted IRR {e['irr']:.2f} (90% {iv(e, '90')}), one-sided p {fp(e['p_one_sided'])}. It also gave a positive "
      f"held-out gain (T {P['T']:+.2f}). Under the frozen rule, this means the published layer adds held-out "
      "information about which houses receive a foundation-repair permit. The 90% upper bound "
      f"({e['hi90']:.2f}) is below δ = 1.5, the smallest enrichment the plan judged worth acting on as a screen. So "
      "an enrichment of that size is excluded at the level the test uses.")
    w("")
    w("**What the result rests on.**")
    w("")
    w(f"- **San Antonio carries the result.** It holds {n(fl_ev['sanantonio'])} of the "
      f"{n(fl_ev['sanantonio'] + fl_ev['dallas'])} flagged events. Its T is {T['sanantonio']['T']:+.2f}, positive in "
      f"{pos['sanantonio']} of 11 fold assignments, and its adjusted IRR is {s1['sanantonio'][ch]['irr']:.2f} "
      f"(95% {iv(s1['sanantonio'][ch], '95')}).")
    w(f"  - Dallas has {n(F['dallas']['flagged']['rows'])} flagged houses and {n(fl_ev['dallas'])} flagged events. Its "
      f"crude rates are flat ({num['dallas']['rate_flagged_per_1000']:.2f} vs {num['dallas']['rate_other_per_1000']:.2f} "
      f"per 1,000 house-years), its T is {T['dallas']['T']:+.2f} ({pos['dallas']} of 11 positive), and its adjusted "
      f"IRR is {s1['dallas'][ch]['irr']:.2f} (95% {iv(s1['dallas'][ch], '95')}).")
    w("  - Plan §11 expected Dallas to be uninformative on its own. It is: it neither supports nor contradicts the "
      "pooled estimate.")
    w(f"  - The ratio of IRRs (Dallas / San Antonio) is {rt['irr']:.2f} (95% {iv(rt, '95')}). This does not show "
      "heterogeneity, but it cannot exclude it.")
    w("  - So this is a San Antonio finding inside a pooled test. It is not a replication in two cities.")
    w(f"- **The gain is in fit, not in ranking.** T is an out-of-fold log-likelihood gain. Ranking measures barely move: "
      f"in San Antonio, ROC AUC changes by {sa['d_roc_auc']:+.4f} and PR AUC by {sa['d_pr_auc']:+.4f}.")
    w(f"  - The flag marks {pct(pe['houses_flagged'] / (pe['houses_flagged'] + pe['houses_other']))} of houses and holds "
      f"{pct(pe['events_flagged'] / (pe['events_flagged'] + pe['events_other']))} of events. That concentration is "
      f"unadjusted (pooled IRR {s2['pooled'][ch]['irr']:.2f}), and the baseline already captures most of it "
      f"(adjusted {e['irr']:.2f}).")
    w("  - These data give no support to a claim that the layer improves screening or targeting beyond the baseline.")
    w(f"- **T is less certain than the IRR test.** The block bootstrap of pooled T runs from {TB['ci95'][0]:+.1f} to "
      f"{TB['ci95'][1]:+.1f}, and {pct(TB['share_le_0'])} of resamples are at or below 0. Under a planted IRR of 1.5, "
      "5.5% were (plan §7).")
    w("  - The §8 reading uses the point value of T, as prespecified. The interval is descriptive.")
    w("")
    w("**Descriptive caveats from the secondaries** (nominal; no claim beyond §8):")
    w("")
    w(f"- **Within neighbourhoods (secondary 6).** With 2 km block fixed effects, the IRR falls to {s6[ch]['irr']:.2f} "
      f"(95% {iv(s6[ch], '95')}; p {fp(s6[ch]['p_one_sided'])}).")
    w("  - Part of the adjusted excess may be neighbourhood-level, such as differences in recording, contractor "
      "activity or income beyond the tract, rather than a difference between nearby houses.")
    w("  - These data cannot separate that from the loss of contrast when flagged houses cluster inside blocks.")
    w(f"- **Baseline choice (secondary 16).** The linear Baseline 1 gives {s16['pooled'][ch]['irr']:.2f} (95% "
      f"{iv(s16['pooled'][ch], '95')}) against {e['irr']:.2f} under the flexible one. The planted check found the "
      "linear baseline anti-conservative (plan §9.2: nonlinear soil gave 23% false demonstrations).")
    w(f"  - The Austin lead ({s12['austin']['irr']:.2f}) used the linear baseline. Compared like for like: San Antonio "
      f"{s16['sanantonio'][ch]['irr']:.2f} and Dallas {s16['dallas'][ch]['irr']:.2f}.")
    w(f"  - The three-city summary ({s12['random_effects']['irr']:.2f}, secondary 12) also uses the linear baseline. It "
      "is not the estimate of this study.")
    w(f"- **Vertical land motion (secondary 5)** points the other way. Per 1 mm/yr of subsidence, the IRR is "
      f"{s5['unadjusted'][ch]['irr']:.2f} unadjusted and {s5['adjusted'][ch]['irr']:.2f} adjusted. Austin showed the "
      "same direction (0.79; plan, design summary).")
    w("  - The information found here is in the layer's differential-settlement (angular-distortion) classes, not in "
      "the subsidence rate near the house. This study does not explain the direction.")
    w("- **Robustness of the primary estimate:**")
    w("  - other inferences (secondary 13): " + "; ".join(
          f"{k} {d['irr']:.2f}, p {fp(d['p_one_sided'])}" for k, d in s13.items()) + ";")
    w(f"  - San Antonio houses with a recent construction permit removed (secondary 15): {s15[ch]['irr']:.2f};")
    w(f"  - Dallas broader outcome (secondary 17): {s17[ch]['irr']:.2f};")
    w(f"  - houses near a flag edge excluded (secondary 10): {s10[ch]['irr']:.2f}, T {s10['T']:+.2f};")
    w(f"  - the map user's domain (secondary 9): {s9[ch]['irr']:.2f};")
    w(f"  - trend per hazard class (secondary 3): {s3['trend_adjusted'][ch]['irr']:.2f};")
    w(f"  - the risk flag (classes 3–4, secondary 4) is weaker: {s4[ch]['irr']:.2f}, T {s4['T']:+.2f}.")
    w("- **By year (secondary 8):** " + "; ".join(
          f"{y} {d[ch]['irr']:.2f} (p {fp(d[ch]['p_one_sided'])})" for y, d in yrs.items()) +
      f". Years with nominal p below 0.05: {sum(d[ch]['p_one_sided'] < 0.05 for d in yrs.values())} of {len(yrs)}.")
    w(f"- **Demolition as the outcome (secondary 11):** {S['s11_demolition']['V'][ch]['irr']:.2f}.")
    w(f"- **Class 3 is almost absent** ({n(s3['rates']['sanantonio']['3']['houses'])} San Antonio houses; "
      f"{n(s3['rates']['dallas']['3']['houses'])} in Dallas). In practice the flag is class 2.")
    w("")
    w("**Scope.**")
    w("")
    w("- The outcome is a permit: an owner's decision to repair, not verified damage. Nothing here is a causal "
      "statement about ground motion and foundations.")
    w("- The result applies inside the map's domain only (InSAR-coherent areas; flow in §2).")
    w("- For the thesis question: in this frozen test, a published InSAR-derived hazard product added a small amount "
      "of held-out information about recorded foundation repairs, almost entirely in San Antonio.")
    w("  - The enrichment was below the size the plan set as useful (δ).")
    w("  - It did not improve ranking.")
    w("")


def main(run_dir, synthetic=False, out=None):
    if synthetic:
        R = json.loads((HERE / run_dir / "results.json").read_text())
        res_path, D = HERE / run_dir / "results.json", None
    else:
        res_path = HERE / run_dir / "real/results.json"
        R = json.loads(res_path.read_text())
        D = json.loads((HERE / run_dir / "decoy/results.json").read_text())
    res_sha = sha(res_path)
    assert sha(HERE / "freeze/HAZARD_TX_PLAN_frozen.md") == FROZEN, "frozen plan changed"
    M = manifest()
    assert M["HAZARD_TX_PLAN_frozen.md"] == FROZEN
    for k in CODE:
        assert R["sources"][k] == M[f"scripts/{k}"] == sha(HERE / "scripts" / k), f"{k} differs from the frozen copy"
    assert R["label"] == ("SYNTHETIC RUN (code check, no permit read; not a result)" if synthetic else "REAL RUN")
    assert R["chosen_inference"] == "r4" and not R["errors"], R["errors"]
    if D is not None:
        assert D["label"] == "DECOY RUN (code check, not a result)" and D["sources"] == R["sources"]
    ch = R["chosen_inference"]
    P, S, F, T = R["primary"], R["secondaries"], R["flow"], R["times"]
    e = P["estimate"]
    num = P["numbers"]
    TB = R["T_bootstrap"]
    EV = {k: json.loads((HERE / f"real/events_{k}.json").read_text()) for k in ("dallas", "dallas_broad", "sanantonio")}
    for k, v in EV.items():
        assert v["script_sha256"] == M["scripts/build_events.py"], f"events_{k}.json not from the frozen build_events.py"
    L = []
    w = L.append

    w("# Result: confirmatory external test of a published InSAR differential-settlement hazard layer against "
      "recorded foundation repairs in San Antonio and Dallas (2022–2025)")
    w("")
    if synthetic:
        w("> **SYNTHETIC LAYOUT CHECK — NOT A RESULT.** Outcomes were drawn by the planted generator (IRR 1.5); no "
          "permit was read.")
        w("")
    w(f"- **Plan:** `HAZARD_TX_PLAN.md`, frozen 2026-11-22 (`freeze/HAZARD_TX_PLAN_frozen.md`, SHA-256 "
      f"`{FROZEN[:16]}…`).")
    w("- **Deviations (§14):** one, procedural. The event tables were built on the PC, not the server, so that raw "
      "permit text stayed in the private area. Only the tables (house id, dates, status) went to the server, with "
      "hashes checked there. No rule, input or output changed.")
    w(f"- **Run:** `scripts/run_ht.py {'synthetic' if synthetic else 'real'}` on the server, {T['start']} to {T['end']} "
      f"EET, with 96 workers. Output `{res_path.relative_to(HERE)}` (SHA-256 `{res_sha[:16]}…`). The code hashes "
      "recorded in it match `freeze/MANIFEST.sha256`.")
    if D is not None:
        de = D["primary"]["estimate"]
        w(f"- **Decoy run first** (§12 step 6; code check, not a result): the real tables given to random houses of the "
          f"same city. Its pooled adjusted IRR was {de['irr']:.2f} (90% {iv(de, '90')}, one-sided p "
          f"{fp(de['p_one_sided'])}) and T {D['primary']['T']:+.2f}, with no task errors. Its reading was "
          f"\"{D['primary']['reading']}\".")
    w(f"- **Inference:** {ch} is a wild cluster score bootstrap over {e['clusters']} twelve-km blocks (Webb weights, "
      "9,999 draws, seed [2071, 0]). It was chosen by the planted-check rule (plan §9.3.1).")
    w("  - Intervals come from test inversion over IRR 0.2–5. A bound written **>5** or **<0.2** lies beyond the grid.")
    w("  - The estimate, p and intervals come from the frozen Ohenhen–Austin `oa_core.infer`. The faster block "
      f"engine gave {'the same values' if R['primary_check']['equal'] else 'DIFFERENT values'} (`primary_check`).")
    w("- **How this document is made:** it is generated by `scripts/result_report.py` from the files above. It "
      "changes no number and makes no decision.")
    w("- **Outcome:** \"event\" means a house's first recorded foundation-repair episode in 2022–2025 (plan §5). It is "
      "a permit, not independently verified damage, and no reading here is about cause.")
    w("")

    w("## 1. Decision (plan §8: pooled, one test)")
    w("")
    w("| Test | Adjusted IRR | 90% interval | 95% interval | One-sided p | T (held-out gain) | Reading |")
    w("|---|---|---|---|---|---|---|")
    w(f"| Hazard flag (β classes 2–3), beyond the flexible Baseline 1, both cities | **{e['irr']:.2f}** | {iv(e, '90')} | "
      f"{iv(e, '95')} | {fp(e['p_one_sided'])} | {P['T']:+.2f} | **{P['reading']}** |")
    w("")
    w(f"- **Rejected at α = 0.05 (one-sided):** {'yes' if P['rejected'] else 'no'}. Added information demonstrated "
      f"(rejected and T > 0): {'yes' if P['demonstrated'] else 'no'}. δ = IRR 1.5.")
    w("- **T by city** (mean over 11 fold assignments of the out-of-fold log-likelihood gain of M1 over M0): " + "; ".join(
        f"{CITIES[c]} {P['T_by_city'][c]['T']:+.2f} (assignments {min(P['T_by_city'][c]['dl_by_assignment']):+.2f} to "
        f"{max(P['T_by_city'][c]['dl_by_assignment']):+.2f}; {sum(v > 0 for v in P['T_by_city'][c]['dl_by_assignment'])} "
        "of 11 positive)" for c in CITIES) + ".")
    q = TB["quantiles"]
    w(f"- **Block bootstrap of pooled T** (2,000 resamples of 2 km blocks within city; {TB['kept']:,} kept): median "
      f"{q['50']:+.1f}, 95% interval {TB['ci95'][0]:+.1f} to {TB['ci95'][1]:+.1f}, {pct(TB['share_le_0'])} of "
      "resamples at or below 0.")
    w("  - Descriptive. The plan stated in advance that this interval is wide by construction: under a planted IRR of 1.5 "
      "it was −7.3 to +86.5 around T = 42.7 (plan §7). The §8 reading uses the point value of T.")
    w("- **Planted power (plan §9.3.1, flexible baseline, r4):** 100% at IRR 1.5 and 100% at IRR 1.74, pooled. Null "
      "cells rejected at most 5.4%. Dallas alone: about 39% at 1.5 and 63% at 1.74.")
    w("")

    w("## 2. Flow (RECORD/STROBE)")
    w("")
    w("```")
    for c in CITIES:
        f, ev = F[c], EV[c]["counts"]
        fs = ev["first_episode_status"]
        w(f"{CITIES[c]}")
        w(f"  {n(f['eligible'])} eligible houses")
        w(f"    -> {n(f['eligible'] - f['mapped'])} outside the map's domain (no class)")
        w(f"  {n(f['mapped'])} mapped")
        w(f"    -> {n(f['mapped'] - f['at_risk'])} not at risk on 2022-01-01 (first foundation episode before 2022, or "
          "demolished)")
        w(f"  {n(f['at_risk'])} at risk")
        w(f"    -> {n(f['at_risk'] - f['primary_rows'])} with incomplete Baseline 1")
        w(f"  {n(f['primary_rows'])} primary rows     flagged {n(f['flagged']['rows'])} | other {n(f['other']['rows'])}")
        w(f"    person-years                    {n(f['flagged']['person_years'])} | {n(f['other']['person_years'])}")
        w(f"    events                          {n(f['flagged']['events'])} | {n(f['other']['events'])}")
        w(f"    censored by demolition          {n(f['flagged']['demolished'])} | {n(f['other']['demolished'])}")
        w(f"    first episode not an event      {n(f['flagged']['first_episode_not_event'])} | "
          f"{n(f['other']['first_episode_not_event'])}  (construction permit in the 3 years before)")
        w(f"  Event construction, all eligible houses (build_events): {n(ev['events'])} events; "
          f"{n(fs.get('first episode before the study period', 0))} first episodes before 2022; "
          f"{n(fs.get('excluded: construction permit in the 3 years before', 0))} excluded for recent construction")
        w("")
    w("```")
    w("")
    w(f"- **Events by year (all eligible houses):** " + "; ".join(
        f"{CITIES[c]} " + ", ".join(f"{y} {n(v)}" for y, v in EV[c]["counts"]["events_by_year"].items()) for c in CITIES) + ".")
    w(f"- **Dallas, broader outcome (secondary 17):** {n(EV['dallas_broad']['counts']['events'])} events, against "
      f"{n(EV['dallas']['counts']['events'])} under the primary rule.")
    if not synthetic:
        w("- **Synthetic outcomes in the pre-freeze check** were drawn for the same houses, so only the eligible and "
          "mapped counts match the synthetic run. The at-risk and later counts depend on the real permits, and the "
          "events and person-time are real.")
    w("")

    w(f"## 3. Headline numbers (all {ch})")
    w("")
    w("| Contrast | Houses | Events | IRR | 90% interval | 95% interval | One-sided p |")
    w("|---|---|---|---|---|---|---|")
    s2 = S["s2_V"]

    def row(lab, blk, d):
        w(f"| {lab} | {n(blk['rows'])} | {n(blk['events'])} | {d['irr']:.2f} | {iv(d, '90')} | {iv(d, '95')} | "
          f"{fp(d['p_one_sided'])} |")
    row("Unadjusted (V), pooled, city-stratified", s2["pooled"], s2["pooled"][ch])
    for c in CITIES:
        row(f"Unadjusted (V), {CITIES[c]}", s2[c], s2[c][ch])
    row("**Adjusted (primary)**, pooled", P["rows"], e)
    for c in CITIES:
        s1 = S["s1_city"][c]
        row(f"Adjusted, {CITIES[c]} (secondary 1)", s1, s1[ch])
    w("")
    w(f"- **Mantel–Haenszel IRR** over city × age stratum (unadjusted otherwise): {s2['mantel_haenszel_city_x_age']:.2f}.")
    w("- **Incidence per 1,000 house-years, primary rows:** " + "; ".join(
        f"{CITIES[c]} flagged {num[c]['rate_flagged_per_1000']:.2f} vs other {num[c]['rate_other_per_1000']:.2f} "
        f"({n(num[c]['events_flagged'])} and {n(num[c]['events_other'])} events)" for c in CITIES) + ".")
    pe = num["pooled"]
    w(f"- **As a screen (primary rows, pooled):** the flag marks {pct(pe['houses_flagged'] / (pe['houses_flagged'] + pe['houses_other']))} "
      f"of houses and holds {pct(pe['events_flagged'] / (pe['events_flagged'] + pe['events_other']))} of events.")
    w("")

    w("## 4. Held-out gain in detail (plan §7)")
    w("")
    for c in CITIES:
        t = P["T_by_city"][c]
        a = t["also_reported"]
        cm = a["calibration_M1"]
        w(f"**{CITIES[c]}.** T {t['T']:+.2f}. By assignment (seed 42, then 0–9): " +
          ", ".join(f"{v:+.2f}" for v in t["dl_by_assignment"]) + ".")
        w(f"- Change from M0 to M1: PR AUC {a['d_pr_auc']:+.4f}, ROC AUC {a['d_roc_auc']:+.4f}, Brier score "
          f"{a['d_brier']:+.2e}. Calibration of M1 (out of fold): intercept {cm['intercept']:+.3f}, slope {cm['slope']:.3f}.")
        w("")
        w("| Decile of M1 | Houses | Observed | Predicted |")
        w("|---|---|---|---|")
        for d in a["deciles_M1"]:
            w(f"| {d['decile'] + 1} | {n(d['houses'])} | {pct(d['observed'], 2)} | {pct(d['predicted'], 2)} |")
        w("")

    w(f"## 5. Secondary analyses (plan §10; descriptive, nominal p, no multiplicity correction, no claim beyond §8)")
    w("")
    w(f"All rows use {ch} unless stated. \"p\" is one-sided for IRR > 1. \"T\" is the pooled held-out gain where the plan "
      "asks for it.")
    w("")
    w("| # | Analysis | Houses | Events | IRR | 95% interval | p | Note |")
    w("|---|---|---|---|---|---|---|---|")

    def srow(k, lab, blk, d, note=""):
        w(f"| {k} | {lab} | {n(blk['rows']) if blk else '—'} | {n(blk['events']) if blk else '—'} | {d['irr']:.2f} | "
          f"{iv(d, '95')} | {fp(d['p_one_sided'])} | {note} |")
    for c in CITIES:
        s1 = S["s1_city"][c]
        srow(1, f"{CITIES[c]}, adjusted", s1, s1[ch], f"T {P['T_by_city'][c]['T']:+.2f}; r3 p {fp(s1['r3']['p_one_sided'])}")
    rt = S["s1_ratio"]["ratio_dallas_over_sanantonio"]
    srow(1, "Ratio of IRRs, Dallas / San Antonio", None, rt, "heterogeneity")
    for k in ("built to 1949", "built 1950-1979", "built 1980-2019"):
        srow(2, f"V within age stratum: {k.replace('-', '–')}", s2[k], s2[k][ch])
    s3 = S["s3_classes"]
    srow(3, "Trend per hazard-class step (0–3), unadjusted", s3["trend_unadjusted"], s3["trend_unadjusted"][ch])
    srow(3, "Trend per hazard-class step, adjusted", s3["trend_adjusted"], s3["trend_adjusted"][ch])
    s4 = S["s4_risk"]
    srow(4, "Risk flag (classes 3–4), V", s4["V"], s4["V"][ch])
    srow(4, "Risk flag, adjusted", s4["U"], s4["U"][ch], f"T {s4['U']['T']:+.2f}")
    s5 = S["s5_vlm"]
    srow(5, "VLM within 50 m, per 1 mm/yr of subsidence, unadjusted", s5["unadjusted"], s5["unadjusted"][ch],
         f"{n(s5['houses_with_vlm'])} houses with VLM")
    srow(5, "VLM, adjusted", s5["adjusted"], s5["adjusted"][ch])
    s6 = S["s6_block_fe"]
    srow(6, "Within 2 km blocks (block fixed effects + feature splines)", s6, s6[ch], f"{s6[ch]['clusters']} clusters")
    for k, d in S["s7_foundation"].items():
        srow(7, f"Dallas, {k} foundation, adjusted", d, d[ch])
    for y, d in S["s8_by_year"].items():
        srow(8, f"Year {y}, adjusted", d, d[ch])
    s9 = S["s9_map_user"]
    srow(9, "Map user's domain (unmapped = not flagged), V", s9["V"], s9["V"][ch])
    srow(9, "Map user's domain, adjusted", s9["adjusted"], s9["adjusted"][ch])
    s10 = S["s10_edges"]
    srow(10, "Excluding houses within 30 m of a flag edge, adjusted", s10["adjusted"], s10["adjusted"][ch],
         f"{n(s10['houses_excluded_in_primary_rows'])} excluded; T {s10['adjusted']['T']:+.2f}")
    s11 = S["s11_demolition"]
    srow(11, "Demolition as the outcome, V", s11["V"], s11["V"][ch])
    for k, d in S["s13_not_chosen"].items():
        srow(13, f"Primary under {k}", d, d[k], f"{d[k]['clusters']} clusters")
    s15 = S["s15_current_layer"]
    srow(15, "San Antonio houses with a 2022–2025 construction permit removed", s15["adjusted"], s15["adjusted"][ch],
         f"{n(s15['houses_removed_from_primary_rows'])} removed; T {s15['adjusted']['T']:+.2f}")
    s16 = S["s16_linear"]
    srow(16, "Linear Baseline 1 + linear x/y, pooled", s16["pooled"], s16["pooled"][ch], f"T {s16['pooled']['T']:+.2f}")
    for c in CITIES:
        srow(16, f"Linear baseline, {CITIES[c]}", s16[c], s16[c][ch])
    s17 = S["s17_dallas_broad"]
    srow(17, "Dallas broader outcome: pooled primary", s17["pooled"], s17["pooled"][ch], f"T {s17['pooled']['T']:+.2f}")
    srow(17, "Dallas broader outcome: Dallas", s17["dallas"], s17["dallas"][ch])
    w("")
    w("Secondary 14 (remodel negative control) was removed before freezing: neither city has a remodel-only permit "
      "type (plan §10).")
    w("")
    w("**Incidence per 1,000 house-years by hazard class** (secondary 3, mapped houses at risk):")
    w("")
    w("| Class | " + " | ".join(f"{CITIES[c]} houses | events | rate" for c in CITIES) + " |")
    w("|---|" + "---|---|---|" * len(CITIES))
    for k in ("0", "1", "2", "3"):
        w(f"| {k} | " + " | ".join(f"{n(s3['rates'][c][k]['houses'])} | {n(s3['rates'][c][k]['events'])} | "
                                   f"{s3['rates'][c][k]['per_1000']:.2f}" for c in CITIES) + " |")
    w("")
    s12 = S["s12_three_cities"]
    re_ = s12["random_effects"]
    au = s12["austin"]
    w(f"**Three cities, descriptive (secondary 12).** Austin (hypothesis-generating; {au['baseline']}, {au['inference']}): "
      f"{au['irr']:.2f} (95% {au['lo95']:.2f} to {au['hi95']:.2f}). Linear baseline: " + "; ".join(
          f"{CITIES[c]} {s12['linear_by_city'][c]['irr']:.2f} (95% {iv(s12['linear_by_city'][c], '95')})" for c in CITIES) +
      f". Random-effects summary {re_['irr']:.2f} (95% {re_['lo95']:.2f} to {re_['hi95']:.2f}; τ² {re_['tau2']:.3f}; "
      f"Q {re_['Q']:.2f}); it {re_['label']}.")
    w("")

    w("## 6. Interpretation")
    w("")
    if synthetic:
        w("(Written after the real result; not produced for the synthetic layout check.)")
        w("")
    else:
        interpretation(w, R, P, S, e, num, TB, s2, s3, s5, s6, s16, ch)

    w("## 7. RECORD/STROBE checklist (cohort design)")
    w("")
    w("| Item | Where |")
    w("|---|---|")
    for item, where in [
        ("1 Title and abstract; RECORD 1.1–1.3", "Paper draft (not yet written). Data: public hazard layer (figshare 27606942), appraisal roll (Dallas 2022) and current county parcel layer (San Antonio), city permit records; linkage in plan §3–§5"),
        ("2 Background", "Plan §2"),
        ("3 Objectives (prespecified)", "Plan §1, frozen before any house was linked to an outcome"),
        ("4 Study design", "Two-city cohort with a fixed start (2022-01-01) after the layer's data end (plan §5)"),
        ("5 Setting and dates", "Dallas and San Antonio, TX; follow-up 2022-01-01 to 2025-12-31"),
        ("6 Participants; RECORD 6.1–6.3", "Plan §5 (population, look-back, recent-construction rule); flow in §2 here"),
        ("7 Variables; RECORD 7.1", "Outcome: plan §5 permit types; exposure: plan §6; confounders: flexible Baseline 1 (plan §7)"),
        ("8 Data sources and measurement", "Plan §4, with file hashes"),
        ("9 Bias", "Plan §11; secondaries 6, 8, 10, 15, 17 (§5 here)"),
        ("10 Study size", "Fixed by the data; power from the planted check (plan §9)"),
        ("11 Quantitative variables", "Binary flag; class trend (secondary 3); VLM per mm/yr (secondary 5)"),
        ("12 Statistical methods", "Plan §7–§8, §10; complete cases on Baseline 1 (counts in §2); demolition censors follow-up"),
        ("RECORD 12.1–12.3", "Whole eligible populations; permit-to-house linkage in plan §3 (link checks); deviation 1 in plan §14"),
        ("13 Participants; RECORD 13.1", "§2 here"),
        ("14 Descriptive data", "Plan §3 (step 0); person-years in §2 here"),
        ("15 Outcome data", "§2–§3 here"),
        ("16 Main results", "§1 and §3 here"),
        ("17 Other analyses", "§4–§5 here"),
        ("18 Key results", "§1 and §6 here"),
        ("19 Limitations; RECORD 19.1", "Plan §11: permits record owners' decisions to repair; current San Antonio layer"),
        ("20 Interpretation", "§6 here"),
        ("21 Generalisability", "Plan §11 (map domain; two cities)"),
        ("22 Funding; RECORD 22.1", "Funding: to be stated in the paper. Protocol frozen with code hashes (`freeze/`); scripts in `scripts/`"),
    ]:
        w(f"| {item} | {where} |")
    w("")
    w("## 8. Files")
    w("")
    w(f"- `{res_path.relative_to(HERE)}` ({res_sha[:16]}…)" + ("" if synthetic else f", `{run_dir}/decoy/results.json`"))
    w("- `real/events_dallas.json`, `real/events_dallas_broad.json`, `real/events_sanantonio.json` (counts; private "
      "tables in the private area, SHA256SUMS)")
    w("- `freeze/` (plan, scripts, planted outputs; `MANIFEST.sha256`)")
    w("- This file, made by `scripts/result_report.py`")
    text = "\n".join(L) + "\n"
    out = Path(out) if out else HERE / "HAZARD_TX_RESULT.md"
    out.write_text(text)
    print(out, sha(out))


if __name__ == "__main__":
    if sys.argv[1] == "--synthetic":
        main(sys.argv[2], synthetic=True, out=sys.argv[3])
    else:
        main(sys.argv[1])
