"""Miami-Dade label audit, step 2: tables for the 100-case sample (NYC plan §17; protocol in
feasibility/miami/audit/label_sample/PROTOCOL.md). No InSAR value is read.

Inputs (feasibility/miami/audit/label_sample/): cases.csv, violations.csv and sample.json from miami_case_sample.py, and
classification.csv (hand classification, name-free summaries). Applies the protocol's code rule, which was fixed before
the remaining cases were read, and writes audit_tables.json: hand categories overall and by open year, prefix group and
pathway; the hand x code cross-table; agreement of STRUCT_code with hand STRUCT, overall and by pathway; repeat folios
within the sample; and population shares of each hand category, weighted by the sampling design (each case stands for
its year and prefix group: pool size / cases drawn), with a seeded stratified bootstrap interval. Groups with no case
drawn (6 of the 6,667 cases) are left out of the weighted shares.
classification.csv is rewritten in sample order with folio, year, prefix group and code category added (PROTOCOL.md).
Run from Alex/:  python3 -I feasibility/miami_label_audit.py
"""
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

D = Path(__file__).resolve().parent / "miami" / "audit" / "label_sample"
SEED, BOOT = 20261017, 2000
RECERT_DESC = ("FAILURE TO OBTAIN 40 YR", "FAILURE OF THE OWNER OF A 40 YEAR OLD BUILDING")


def code_rule(descs):
    up = [d.upper() for d in descs]
    has = lambda *ks: any(k in d for d in up for k in ks)
    if has("DETERIORATED STRUCTURE", "PARTIALLY DESTROYED", "SAGGING", "LEANING"):
        return "STRUCT_code"
    if has("DAMAGED BY THE ELEMENTS"):
        return "EVENT_code"
    if has("VACANT", "DEBRIS", "ELECTRICAL OR MECHANICAL", "UNSANITARY", "WITHOUT PERMIT"):
        return "OTHER_PHYS_code"
    if up and all(d.startswith("9020") or d.startswith("8-11") or any(k in d for k in RECERT_DESC) for d in up):
        return "ADMIN_code"
    return "OTHER_code"


def read(name):
    with open(D / name, newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    cases = {r["case"]: r for r in read("cases.csv")}
    viol = defaultdict(list)
    for r in read("violations.csv"):
        viol[r["case"]].append(r["description"])
    hand = read("classification.csv")
    assert {h["case"] for h in hand} == set(cases), "classification must cover exactly the sampled cases"
    rows = []
    for h in hand:
        c = cases[h["case"]]
        rows.append({**h, "year": int(c["year"]), "prefix_group": c["prefix_group"], "folio": c["folio"],
                     "code_category": code_rule(viol[h["case"]])})
    cat = lambda f: {str(k): dict(Counter(r["hand_category"] for r in rows if f(r) == k)) for k in sorted({f(r) for r in rows})}
    cross = Counter((r["hand_category"], r["code_category"]) for r in rows)
    s_hand = {r["case"] for r in rows if r["hand_category"] == "STRUCT"}
    s_code = {r["case"] for r in rows if r["code_category"] == "STRUCT_code"}
    folios = Counter(r["folio"] for r in rows)
    by_path = {}
    for pw in sorted({r["pathway"] for r in rows}):
        h = {r["case"] for r in rows if r["pathway"] == pw and r["hand_category"] == "STRUCT"}
        c = {r["case"] for r in rows if r["pathway"] == pw and r["code_category"] == "STRUCT_code"}
        by_path[pw] = {"cases": sum(r["pathway"] == pw for r in rows), "hand": len(h), "code": len(c), "both": len(h & c)}
    design = json.loads((D / "sample.json").read_text())["design"]
    strata = defaultdict(list)
    for r in rows:
        strata[(str(r["year"]), r["prefix_group"])].append(r["hand_category"])
    weight = {k: design[k[0]]["by_group"][k[1]] / len(v) for k, v in strata.items()}
    cats = sorted({r["hand_category"] for r in rows})

    def shares(st):
        tot = sum(weight[k] * len(v) for k, v in st.items())
        return {c: sum(weight[k] * v.count(c) for k, v in st.items()) / tot for c in cats}

    rng = random.Random(SEED)
    boot = [shares({k: [rng.choice(v) for _ in v] for k, v in strata.items()}) for _ in range(BOOT)]
    pct = lambda xs, q: sorted(xs)[int(q * (len(xs) - 1))]
    weighted = {c: {"share": round(x, 3), "boot_2.5": round(pct([b[c] for b in boot], 0.025), 3),
                    "boot_97.5": round(pct([b[c] for b in boot], 0.975), 3)} for c, x in shares(strata).items()}
    order = {c: i for i, c in enumerate(json.loads((D / "sample.json").read_text())["cases"])}
    cols = ["case", "folio", "year", "prefix_group", "hand_category", "confidence", "pathway", "first_deficiency_date",
            "deformation_mention", "code_category", "evidence"]
    with open(D / "classification.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows({k: r[k] for k in cols} for r in sorted(rows, key=lambda r: order[r["case"]]))
    out = {"cases": len(rows), "hand_overall": dict(Counter(r["hand_category"] for r in rows)),
           "hand_confidence": dict(Counter(r["confidence"] for r in rows)),
           "hand_by_year": cat(lambda r: r["year"]), "hand_by_prefix_group": cat(lambda r: r["prefix_group"]),
           "hand_by_pathway": cat(lambda r: r["pathway"]),
           "hand_x_code": {f"{a} | {b}": n for (a, b), n in sorted(cross.items())},
           "struct": {"hand": len(s_hand), "code": len(s_code), "both": len(s_hand & s_code),
                      "code_precision": round(len(s_hand & s_code) / len(s_code), 3) if s_code else None,
                      "code_recall": round(len(s_hand & s_code) / len(s_hand), 3) if s_hand else None,
                      "by_pathway": by_path},
           "cases_without_violation_codes": sum(not viol[r["case"]] for r in rows),
           "weighted_population_share": weighted, "weighted_cases_represented": round(sum(weight[k] * len(v) for k, v in strata.items())),
           "deformation_mention": sum(r["deformation_mention"] == "yes" for r in rows),
           "first_deficiency_dated": sum(bool(r["first_deficiency_date"]) for r in rows),
           "folios_repeated_in_sample": {f: n for f, n in folios.items() if n > 1}}
    (D / "audit_tables.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
