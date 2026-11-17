"""Miami-Dade label validation: which cases I adjudicate, and the final labels (PROTOCOL_v2.md §6). No InSAR file is
opened. Written before any reviewer output was read.

list:  writes label_validation/adjudication_list.csv. A case is adjudicated when
         - reviewers A and B differ on the category or the assessment;
         - both say STRUCT_DESCRIBED but give different earliest-defect dates;
         - either says STRUCT_DESCRIBED or ENG_PASS_FIRST (so every final positive and comparison case is checked);
         - either gives a SAME_EPISODE link (merges change the episode count);
       plus a seeded random 10% (seed 20261020) of the remaining agreed cases.
merge: writes label_validation/final.jsonl in batch order. Each case starts from reviewer A's record. A decision in
       --decisions (JSON Lines: {"case", "take": "A"|"B", "set": {field: value, ...}, "reason"}) replaces it with the
       chosen reviewer's record and then the fields in "set"; the record then carries "adjudication": {"take", "changed",
       "reason"}. Every listed case needs a decision (take A with an empty "set" when A stands).
       Words in any free-text field that are not in the word list are printed for a manual name check.
Run from Alex/:  python3 -I feasibility/miami_adjudication.py list --a A/*.jsonl --b B/*.jsonl
                 python3 -I feasibility/miami_adjudication.py merge --a ... --b ... --decisions decisions.jsonl
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from miami_passage_check import WORD, vocabulary  # noqa: E402
from miami_validation_analysis import D, jl  # noqa: E402

SEED = 20261020
TEXT = ("element", "condition", "note")


def reasons(a, b):
    out = []
    if a["category"] != b["category"]:
        out.append("category")
    if a["assessment"] != b["assessment"]:
        out.append("assessment")
    if a["category"] == b["category"] == "STRUCT_DESCRIBED" and a["earliest_defect_date"] != b["earliest_defect_date"]:
        out.append("defect_date")
    if "STRUCT_DESCRIBED" in (a["category"], b["category"]):
        out.append("positive")
    if "ENG_PASS_FIRST" in (a["assessment"], b["assessment"]):
        out.append("comparison")
    if any(x["relation"] == "SAME_EPISODE" for r in (a, b) for x in r.get("related", [])):
        out.append("same_episode")
    return out


def strings(r):
    for k in TEXT:
        yield k, r.get(k) or ""
    yield "building.label", (r.get("building") or {}).get("label") or ""
    for x in r.get("related", []):
        yield "related.reason", x.get("reason") or ""
    adj = r.get("adjudication") or {}
    yield "adjudication.reason", adj.get("reason") or ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("list", "merge"))
    ap.add_argument("--a", nargs="+", required=True)
    ap.add_argument("--b", nargs="+", required=True)
    ap.add_argument("--decisions")
    a = ap.parse_args()
    ids = json.loads((D / "sample.json").read_text())["cases"]
    A, B = jl(a.a), jl(a.b)
    assert set(A) == set(B) == set(ids), "both reviewer files must cover the batch"
    why = {c: reasons(A[c], B[c]) for c in ids}
    rest = [c for c in ids if not why[c]]
    for c in random.Random(SEED).sample(rest, round(0.1 * len(rest))):
        why[c] = ["random_10pct"]
    listed = [c for c in ids if why[c]]
    if a.step == "list":
        with open(D / "adjudication_list.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["case", "reasons", "a_category", "b_category", "a_assessment", "b_assessment"])
            for c in listed:
                w.writerow([c, ";".join(why[c]), A[c]["category"], B[c]["category"], A[c]["assessment"],
                            B[c]["assessment"]])
        print(f"{len(listed)} of {len(ids)} cases listed; agreed cases not otherwise listed: {len(rest)}")
        return
    dec = jl([a.decisions])
    assert set(dec) <= set(ids), "decision for a case outside the batch"
    missing = [c for c in listed if c not in dec]
    assert not missing, f"no decision for listed cases: {missing}"
    final = []
    for c in ids:
        r = dict(A[c])
        if c in dec:
            d = dec[c]
            r = dict({"A": A, "B": B}[d["take"]][c])
            r.update(d.get("set", {}))
            changed = sorted(k for k in r if r[k] != A[c].get(k))
            r["adjudication"] = {"take": d["take"], "changed": changed, "reason": d["reason"]}
        final.append(r)
    vocab = vocabulary()
    for r in final:
        for k, s in strings(r):
            odd = sorted({w for w in WORD.findall(s) if w.lower().rstrip("'s") not in vocab and w.lower() not in vocab})
            if odd:
                print("CHECK", r["case"], k, odd)
    with open(D / "final.jsonl", "w") as fh:
        for r in final:
            fh.write(json.dumps(r) + "\n")
    print(f"final.jsonl: {len(final)} cases, {sum(c in dec for c in ids)} adjudicated")


if __name__ == "__main__":
    main()
