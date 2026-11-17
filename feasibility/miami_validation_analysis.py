"""Miami-Dade label validation: agreement, dating, yield, comparison groups, screen and decision rules for the 250-case
batch (miami/audit/label_validation/PROTOCOL_v2.md §8). No InSAR file is opened; pixel coverage enters only as one
aggregate factor from the earlier outcome-blind audit (miami/audit/opera_prewindow.json).

Inputs (label_validation/): sample.json and cases.csv (miami_validation_sample.py); reviewer files given with --a and
--b (JSON Lines, REVIEWER_INSTRUCTIONS.md); final.jsonl (after adjudication, same fields plus "adjudication").
--dossiers is the dossier folder (outside the project), used for the keyword screen.
Writes label_validation/validation_tables.json; without final.jsonl, only agreement_before_adjudication.json.
Run from Alex/:  python3 -I feasibility/miami_validation_analysis.py --dossiers <dir> --a A/*.jsonl --b B/*.jsonl
"""
import argparse
import csv
import glob
import json
import random
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "miami"
D = ROOT / "audit" / "label_validation"
SEED, BOOT = 20261018, 2000
ELIGIBLE = (date(2018, 7, 5), date(2026, 5, 8))  # 2-year window inside the OPERA series; opened <= 90 d after the last
EL = (r"FOUNDATION|FOOTING|PILE|SLAB|BEAM|LINTEL|JOIST|GIRDER|COLUMN|WALL|TRUSS|RAFTER|PURLIN|ROOF STRUCT|ROOF DECK|"
      r"SHEATHING|STAIR|STRINGER|LANDING|BALCON|WALKWAY|CATWALK|CANOPY|CANTILEVER|PARAPET|CARPORT|PORCH|CONCRETE|REBAR|"
      r"REINFORC|STEEL|FRAM|MEMBER")
CO = (r"SPALL|CRACK|DELAMIN|CORRO|RUST|ROT|TERMITE|DETERIORAT|SAG|LEAN|PLUMB|DEFLECT|SETTL|SUBSID|UNDERMIN|COLLAPS|"
      r"EXPOSED|FAIL|BUCKL|BROKEN|MISSING|DAMAGE")
EL_RE, CO_RE = re.compile(r"\b(" + EL + ")", re.I), re.compile(r"\b(" + CO + ")", re.I)


def jl(paths):
    out = {}
    for p in paths:
        for ln in open(p):
            if ln.strip():
                r = json.loads(ln)
                out[r["case"]] = r
    return out


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n / n
    return {"n": n, "agreement": round(po, 3), "kappa": round((po - pe) / (1 - pe), 3) if pe < 1 else None}


def screen(path):
    for ln in path.read_text().splitlines():
        if ln[:1] in "TSA" and EL_RE.search(ln) and CO_RE.search(ln):
            return True
    return False


def day(s):
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dossiers", required=True)
    ap.add_argument("--a", nargs="+", required=True)
    ap.add_argument("--b", nargs="+", required=True)
    ap.add_argument("--final", default=str(D / "final.jsonl"))
    a = ap.parse_args()
    smp = json.loads((D / "sample.json").read_text())
    cases = {r["case"]: r for r in csv.DictReader(open(D / "cases.csv"))}
    A, B = jl(a.a), jl(a.b)
    ids = smp["cases"]
    assert set(A) == set(B) == set(ids), "both reviewer files must cover the batch"
    F = jl([a.final]) if Path(a.final).exists() else None
    assert F is None or set(F) == set(ids), "the final file must cover the batch"
    out = {"cases": len(ids)}

    # Agreement before adjudication
    pos = lambda r: r["category"] == "STRUCT_DESCRIBED"
    comp = lambda r: r["assessment"] == "ENG_PASS_FIRST"
    out["agreement"] = {
        "struct_described": kappa([pos(A[c]) for c in ids], [pos(B[c]) for c in ids]),
        "eng_pass_first": kappa([comp(A[c]) for c in ids], [comp(B[c]) for c in ids]),
        "category_6": kappa([A[c]["category"] for c in ids], [B[c]["category"] for c in ids]),
        "assessment_9": kappa([A[c]["assessment"] for c in ids], [B[c]["assessment"] for c in ids]),
        "defect_date_same_when_both_positive": sum(A[c]["earliest_defect_date"] == B[c]["earliest_defect_date"]
                                                   for c in ids if pos(A[c]) and pos(B[c])),
        "both_positive": sum(pos(A[c]) and pos(B[c]) for c in ids),
        "either_positive": sum(pos(A[c]) or pos(B[c]) for c in ids)}
    if F is None:  # before adjudication: agreement only
        (D / "agreement_before_adjudication.json").write_text(json.dumps(out, indent=1) + "\n")
        print(json.dumps(out, indent=1))
        return
    out["final_category"] = dict(Counter(F[c]["category"] for c in ids))
    out["final_assessment"] = dict(Counter(F[c]["assessment"] for c in ids))
    out["final_category_by_pathway"] = {p: dict(Counter(F[c]["category"] for c in ids if F[c]["pathway"] == p))
                                        for p in sorted({F[c]["pathway"] for c in ids})}
    out["adjudicated"] = sum(bool(F[c].get("adjudication")) for c in ids)

    # Dating of positives
    P = [c for c in ids if pos(F[c])]
    lags = sorted(round((day(F[c]["earliest_defect_date"]) - day(F[c]["open_date"])).days / 365.25, 2)
                  for c in P if F[c].get("earliest_defect_date"))
    out["positives"] = {"n": len(P), "dated_with_passage": sum(bool(F[c].get("earliest_defect_date"))
                                                               and bool(F[c].get("defect_passage")) for c in P),
                        "lag_years_open_to_defect": lags,
                        "defect_predates_case": sum(bool(F[c].get("defect_predates_case")) for c in P),
                        "by_pathway": dict(Counter(F[c]["pathway"] for c in P)),
                        "by_confidence": dict(Counter(F[c]["confidence"] for c in P)),
                        "complex": dict(Counter(F[c]["complex"] for c in P))}

    # Units: buildings, properties, complexes, episodes
    rel = Counter(x["relation"] for c in ids for x in F[c].get("related", []))
    out["units"] = {"complex": dict(Counter(F[c]["complex"] for c in ids)), "related_links": dict(rel),
                    "cases_with_same_episode_link": sum(any(x["relation"] == "SAME_EPISODE" for x in F[c].get("related", []))
                                                        for c in ids),
                    "folios_in_batch": len({cases[c]["folio"] for c in ids})}

    # Yield: weighted, episode-deduplicated positives in the date-eligible population, times the coverage factor
    st = defaultdict(list)
    for c in ids:
        r = cases[c]
        st[f"{r['year']}|{r['prefix_group']}"].append(c)
    weight = {k: smp["strata"][k]["pool"] / len(v) for k, v in st.items()}
    elig = lambda c: ELIGIBLE[0] <= day(F[c]["open_date"]) <= ELIGIBLE[1]
    rows = []
    for f in sorted(glob.glob(str(ROOT / "downloads" / "building_violations" / "pages" / "*.geojson"))):
        rows += [x["properties"] for x in json.load(open(f))["features"]]
    opened = [datetime.fromtimestamp(r["OPEN_DATE"] / 1000, timezone.utc).date() for r in rows
              if r["CASE_TYPE"] == "Unsafe Structure" and r["OPEN_DATE"]]
    n_elig = sum(ELIGIBLE[0] <= d <= ELIGIBLE[1] for d in opened if d.year >= 2017)
    cover = json.loads((ROOT / "audit" / "opera_prewindow.json").read_text())["window_2y"]["qualifying_cases"] / n_elig

    # Episode divisor. "as_fixed" is the rule of PROTOCOL_v2.md §8 (1 + every SAME_EPISODE link) and decides Y. The other
    # three were added after adjudication (FIXED.sha256, 2026-10-18) because most links point to cases outside the
    # sampled population (code-enforcement cases, recertification parent "B" cases), which can never be drawn:
    #   population_links: 1 + links to Unsafe Structure cases opened in the date-eligible window;
    #   population_links_window_start: the same, and an episode with a linked Unsafe case opened before the window
    #     counts 0 (the episode began before the window);
    #   no_dedup: every positive case counts 1.
    bulk = {r["CASE_NUM"]: r for r in rows}
    opened_on = lambda r: datetime.fromtimestamp(r["OPEN_DATE"] / 1000, timezone.utc).date() if r.get("OPEN_DATE") else None
    unsafe = lambda r: r is not None and r["CASE_TYPE"] == "Unsafe Structure" and opened_on(r) is not None
    links = lambda c: [bulk.get(x["case"]) for x in F[c].get("related", []) if x["relation"] == "SAME_EPISODE"]
    in_pop = lambda c: sum(unsafe(r) and ELIGIBLE[0] <= opened_on(r) <= ELIGIBLE[1] for r in links(c))
    began_before = lambda c: any(unsafe(r) and opened_on(r) < ELIGIBLE[0] for r in links(c))
    divisor = {"as_fixed": lambda c: 1.0 / (1 + len(links(c))),
               "population_links": lambda c: 1.0 / (1 + in_pop(c)),
               "population_links_window_start": lambda c: 0.0 if began_before(c) else 1.0 / (1 + in_pop(c)),
               "no_dedup": lambda c: 1.0}

    def projection(name):
        unit = {c: divisor[name](c) if pos(F[c]) and elig(c) else 0.0 for c in ids}
        total = lambda s: sum(weight[k] * sum(unit[c] for c in v) for k, v in s.items())
        rng = random.Random(SEED)
        boot = sorted(total({k: [rng.choice(v) for _ in v] for k, v in st.items()}) for _ in range(BOOT))
        est = total(st)
        return {"units_in_batch": round(sum(unit.values()), 2), "episodes_before_coverage": round(est),
                "episodes": round(est * cover), "boot_2.5": round(boot[int(0.025 * BOOT)] * cover),
                "boot_97.5": round(boot[int(0.975 * BOOT)] * cover)}

    out["yield"] = {"date_eligible_cases_in_population": n_elig, "coverage_factor": round(cover, 3),
                    **projection("as_fixed"),
                    "positive_cases_in_batch_date_eligible": sum(pos(F[c]) and elig(c) for c in ids),
                    "same_episode_links_of_eligible_positives": dict(Counter(
                        ("unsafe_in_window" if unsafe(r) and ELIGIBLE[0] <= opened_on(r) <= ELIGIBLE[1] else
                         "unsafe_before_window" if unsafe(r) and opened_on(r) < ELIGIBLE[0] else
                         "other_case_type" if r is not None else "not_in_bulk_data")
                        for c in ids if pos(F[c]) and elig(c) for r in links(c))),
                    "post_hoc_variants": {k: projection(k) for k in divisor if k != "as_fixed"}}

    # Comparison groups
    rp = [c for c in ids if F[c]["pathway"] == "RECERT"]
    out["comparison"] = {
        "recert_cases": len(rp),
        "recert_positives": sum(pos(F[c]) for c in rp),
        "recert_eng_pass_first": sum(comp(F[c]) for c in rp),
        "recert_eng_pass_first_dated_with_passage": sum(comp(F[c]) and bool(F[c].get("assessment_date"))
                                                        and bool(F[c].get("assessment_passage")) for c in rp),
        "recert_eng_pass_after_rejection": sum(F[c]["assessment"] == "ENG_PASS_AFTER_REJECTION" for c in rp),
        "recert_assessment": dict(Counter(F[c]["assessment"] for c in rp)),
        "inspector_positives": sum(F[c]["assessment"] == "INSP_DEFECT_DESCRIBED" for c in ids),
        "insp_no_defect_explicit": sum(F[c]["assessment"] == "INSP_NO_DEFECT_EXPLICIT" for c in ids),
        "insp_no_defect_noted": sum(F[c]["assessment"] == "INSP_NO_DEFECT_NOTED" for c in ids)}

    # Keyword screen
    flag = {c: screen(Path(a.dossiers) / f"{c}.txt") for c in ids}
    out["screen"] = {"flagged": sum(flag.values()), "positives": len(P), "positives_flagged": sum(flag[c] for c in P),
                     "recall": round(sum(flag[c] for c in P) / len(P), 3) if P else None,
                     "weighted_share_flagged": round(sum(weight[k] * sum(flag[c] for c in v) for k, v in st.items())
                                                     / sum(weight[k] * len(v) for k, v in st.items()), 3)}

    # Decision rules (PROTOCOL_v2.md §8); P is checked by miami_passage_check.py on final.jsonl
    ag = out["agreement"]
    out["decision"] = {
        "R_reliability": bool(ag["struct_described"]["kappa"] is not None and ag["struct_described"]["kappa"] >= 0.6
                              and ag["eng_pass_first"]["kappa"] is not None and ag["eng_pass_first"]["kappa"] >= 0.6),
        "D_dating": bool(P) and out["positives"]["dated_with_passage"] >= 0.8 * len(P),
        "Y_yield": out["yield"]["episodes"] >= 200 and out["yield"]["boot_2.5"] >= 100,
        "Y_yield_post_hoc_variants": {k: v["episodes"] >= 200 and v["boot_2.5"] >= 100
                                      for k, v in out["yield"]["post_hoc_variants"].items()},
        "C_comparison": out["comparison"]["recert_eng_pass_first_dated_with_passage"] >= out["comparison"]["recert_positives"],
        "S_screen_recall_ge_0.95": out["screen"]["recall"] is not None and out["screen"]["recall"] >= 0.95}
    (D / "validation_tables.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
