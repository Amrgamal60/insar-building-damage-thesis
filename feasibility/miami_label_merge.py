"""Compute Q0/Q1, select adjudications, and merge v3 reviews with auditable provenance.

Run from Alex/: python3 -I feasibility/miami_label_merge.py q0 --index INDEX --a A.jsonl
  --b B.jsonl --out PRIVATE_REPORT.json
pair (revision 2026-10-20): --index the candidate's stage-0 index, --a the stage-0 Grok reviews,
--b the candidate's reviews of the same 250 cases, --candidate composer|haiku|luna; writes the stage-1
pair (Grok + candidate if it passes Q0, else Grok + Grok). q0 reproduces the stage-0 Grok/Sonnet report.
Other modes: list, merge. Both require --pair PAIR.json; merge also --decisions FILE
and --dossiers DIR. --complete requires exact membership of the frozen 6,667-case population.
Revision 2026-10-20b: with a Grok + Haiku pair, a B review by Grok is accepted only from a stage1-fill chunk
(the wave's unfinished Haiku chunks after a usage limit or three failed calls); reports give agreement per pair.
Raw labels, diagnostics and reports are written only outside Alex; no InSAR file is opened.
"""
import argparse
import copy
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from miami_label_check import check_records, free_text, private_output, read_jsonl, vocabulary, WORD

EXCLUSIONS_V3 = {"20250233697", "20250233943", "20260245339", "F2022010600", "F2023013140",
                 "F2024013772", "20250236234", "F2023013455"}
POS_FIELDS = {"earliest_defect_date", "defect_text_date", "pathway", "complex"}
COMP_FIELDS = {"assessment_date", "assessment_text_date", "approval_wording", "pathway", "complex"}
RULES = Path(__file__).resolve().parent / "miami/audit/label_validation"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unique(paths):
    records = read_jsonl(paths)
    ids = [r.get("case") for r in records]
    if any(not isinstance(c, str) for c in ids) or len(ids) != len(set(ids)):
        raise ValueError("missing or duplicate record IDs")
    return {r["case"]: r for r in records}


def kappa(a, b):
    if len(a) != len(b) or not a:
        raise ValueError("agreement needs equal nonempty case sets")
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[k] * cb[k] for k in ca.keys() | cb.keys()) / n ** 2
    return {"n": n, "agreement": observed,
            "kappa": (observed - expected) / (1 - expected) if expected < 1 else None}


def agreement(a, b, ids):
    result = {}
    for key in sorted(set.intersection(*(set(a[c]) & set(b[c]) for c in ids))):
        aa = [json.dumps(a[c][key], sort_keys=True) for c in ids]
        bb = [json.dumps(b[c][key], sort_keys=True) for c in ids]
        result[key] = kappa(aa, bb)
    for key, field, value in (("struct_described", "category", "STRUCT_DESCRIBED"),
                              ("eng_pass_first", "assessment", "ENG_PASS_FIRST")):
        result[key] = kappa([a[c][field] == value for c in ids], [b[c][field] == value for c in ids])
    return result


def passes_q0(metrics):
    return (all(metrics[k]["kappa"] is not None and metrics[k]["kappa"] >= .8
                for k in ("struct_described", "eng_pass_first")) and metrics["category"]["agreement"] >= .9)


def qualification(a, b, gold, ids, exclusions):
    if not set(exclusions) <= set(ids):
        raise ValueError("calibration exclusion outside batch")
    selected = [c for c in ids if c not in exclusions]
    scores = {"grok": agreement(a, gold, selected), "sonnet": agreement(b, gold, selected)}
    passed = {m: passes_q0(s) for m, s in scores.items()}
    chosen = "grok" if passed["grok"] else "sonnet"
    if chosen != "sonnet" and passed["sonnet"]:
        def rank(role):
            m = chosen if role == "A" else "sonnet"
            return (scores[m]["struct_described"]["kappa"], scores[m]["eng_pass_first"]["kappa"], role == "B")
        base = max(("A", "B"), key=rank)
    else:
        base = "B"
    from miami_label_chunks import model_pins
    pins = model_pins()
    cross = {"grok_sonnet": agreement(a, b, ids)}
    return {"Q0": passed, "metrics": scores, "excluded": sorted(exclusions), "selected_A": chosen,
            "models": {"A": pins[chosen], "B": pins["sonnet"]},
            "base": base, "qualified": passed["sonnet"], "cross_model_agreement": cross}


def pair_decision(a, b, gold, ids, exclusions, candidate="composer"):
    """Revision 2026-10-20: Grok's stage-0 reviews stay A; the candidate is B if it passes Q0, else a second Grok."""
    if not set(exclusions) <= set(ids):
        raise ValueError("calibration exclusion outside batch")
    if candidate == "grok":
        raise ValueError("the candidate must be another model")
    selected = [c for c in ids if c not in exclusions]
    scores = {"grok": agreement(a, gold, selected), candidate: agreement(b, gold, selected)}
    passed = {m: passes_q0(s) for m, s in scores.items()}
    chosen = candidate if passed[candidate] else "grok"
    if chosen == candidate and passed["grok"]:
        def rank(role):
            m = "grok" if role == "A" else chosen
            return (scores[m]["struct_described"]["kappa"], scores[m]["eng_pass_first"]["kappa"], role == "B")
        base = max(("A", "B"), key=rank)
    else:
        base = "B"
    from miami_label_chunks import model_pins
    pins = model_pins()
    return {"Q0": passed, "metrics": scores, "excluded": sorted(exclusions), "selected_B": chosen,
            "pair": f"grok-{chosen}", "models": {"A": pins["grok"], "B": pins[chosen]}, "base": base,
            "qualified": passed["grok"], "fill_needed": chosen == "grok",
            "cross_model_agreement": {f"grok_{candidate}": agreement(a, b, ids)}}


def linkmap(r):
    return {x["case"]: x for x in r.get("related", [])}


def relations_differ(a, b):
    aa, bb = linkmap(a), linkmap(b)
    return any((aa.get(c, {}).get("relation") == "SAME_EPISODE" or bb.get(c, {}).get("relation") == "SAME_EPISODE")
               and aa.get(c, {}).get("relation") != bb.get(c, {}).get("relation") for c in aa.keys() | bb.keys())


def reasons(a, b):
    out = []
    if a["category"] != b["category"]:
        out.append("category")
    if a["assessment"] != b["assessment"]:
        out.append("assessment")
    if a["category"] == b["category"] == "STRUCT_DESCRIBED":
        out.extend(sorted(k for k in POS_FIELDS if a[k] != b[k]))
        if relations_differ(a, b):
            out.append("same_episode")
    if a["assessment"] == b["assessment"] == "ENG_PASS_FIRST":
        out.extend(sorted(k for k in COMP_FIELDS if a[k] != b[k]))
        if relations_differ(a, b):
            out.append("same_episode")
    if (a["confidence"] == "low" or b["confidence"] == "low") and (
            "STRUCT_DESCRIBED" in (a["category"], b["category"]) or "ENG_PASS_FIRST" in (a["assessment"], b["assessment"])):
        out.append("low_confidence")
    return sorted(set(out))


def adjudication_list(a, b, ids):
    why = {c: reasons(a[c], b[c]) for c in ids}
    rest = [c for c in sorted(ids) if not why[c] and (
        a[c]["category"] == b[c]["category"] == "STRUCT_DESCRIBED"
        or a[c]["assessment"] == b[c]["assessment"] == "ENG_PASS_FIRST")]
    for c in random.Random(20261021).sample(rest, round(.1 * len(rest))):
        why[c] = ["random_10pct"]
    return {c: why[c] for c in ids if why[c]}


def disagreements(a, b):
    return {k: {"A": copy.deepcopy(a.get(k)), "B": copy.deepcopy(b.get(k))}
            for k in sorted(a.keys() | b.keys()) if a.get(k) != b.get(k)}


def merge_record(a, b, base="B", decision=None):
    reviews = {"A": a, "B": b}
    take = decision["take"] if decision else base
    if take not in reviews:
        raise ValueError("decision must take A or B")
    result = copy.deepcopy(reviews[take])
    overrides = decision.get("set", {}) if decision else {}
    if not isinstance(overrides, dict) or set(overrides) - (set(a) - {"case"}):
        raise ValueError("invalid adjudication fields")
    result.update(copy.deepcopy(overrides))
    settled = set(overrides)
    if decision:
        settled |= {"category", "assessment"}
        if result["category"] == "STRUCT_DESCRIBED":
            settled |= POS_FIELDS | {"related"}
        if result["assessment"] == "ENG_PASS_FIRST":
            settled |= COMP_FIELDS | {"related"}
    # Any adjudicated field wins. Automatic changes carry the supporting passage too.
    if result["category"] == "DEFICIENCY_UNDESCRIBED" and "deficiency_basis" not in overrides:
        rank = {"": 0, "DOCUMENTARY": 1, "UNSTATED": 2, "FINDING": 3}
        source = max((a, b), key=lambda r: rank.get(r.get("deficiency_basis", ""), -1))
        result["deficiency_basis"] = source["deficiency_basis"]
        if "basis_passage" not in overrides:
            result["basis_passage"] = copy.deepcopy(source["basis_passage"])
    if result["assessment"] == "ENG_PASS_AFTER_REJECTION" and "approval_wording" not in overrides:
        result["approval_wording"] = "STRUCTURAL" if a["approval_wording"] == b["approval_wording"] == "STRUCTURAL" else "GENERIC"
        if result["approval_wording"] == "GENERIC":
            source = next((r for r in (reviews[take], a, b) if r["approval_wording"] == "GENERIC"), None)
            if source is None:
                raise ValueError("GENERIC wording has no supporting approval; adjudicate wording and passage")
            for k in ("assessment_passage", "assessment_date", "assessment_text_date"):
                if k not in overrides:
                    result[k] = copy.deepcopy(source[k])
    if "related" not in settled:
        aa, bb = linkmap(a), linkmap(b)
        merged = []
        for cn in sorted(aa.keys() | bb.keys()):
            av, bv = aa.get(cn), bb.get(cn)
            source = linkmap(reviews[take]).get(cn) or av or bv
            link = copy.deepcopy(source)
            ar, br = (av or {}).get("relation"), (bv or {}).get("relation")
            if ar == br:
                link["relation"] = ar
            elif ar == "SAME_EPISODE" or br == "SAME_EPISODE":
                other = bv if ar == "SAME_EPISODE" else av
                if other:
                    link = copy.deepcopy(other)
                else:
                    link["relation"] = "UNCLEAR"
                    link["reason"] = "Reviewers did not agree on a same-episode link."
            else:
                link["relation"] = "UNCLEAR"
                link["reason"] = "Reviewers differed on the relation."
            merged.append(link)
        result["related"] = merged
    diff = disagreements(a, b)
    if decision:
        result["adjudication"] = {"take": take, "set": copy.deepcopy(overrides), "reason": decision["reason"]}
    result["field_disagreements"] = {k: v for k, v in diff.items() if k not in settled}
    return result


def checked_inputs(paths, role, index, dossiers, models=None, resolved_models=None, fill=None):
    """fill: the Grok identity a moved B chunk may carry ({"model", "resolved", "index_sha256" or None})."""
    rows, provenance = [], {}
    for path in paths:
        path = Path(path)
        meta = json.loads(path.with_suffix(".meta.json").read_text())
        if (meta["reviewer"] != role or meta["guide_hashes"] != index["guide_hashes"]
                or meta["output_sha256"] != sha(path) or not meta.get("checked")):
            raise ValueError("review provenance mismatch")
        actual = meta.get("resolved_models")
        if not actual or not isinstance(actual, list) or any(not isinstance(m, str) for m in actual):
            raise ValueError("missing resolved model identity")
        if "fill_of" in meta:
            if (role != "B" or not fill or meta["model"] != fill["model"] or sorted(actual) != sorted(fill["resolved"])
                    or (fill["index_sha256"] and meta["fill_of"].get("index_sha256") != fill["index_sha256"])):
                raise ValueError("a Grok B review is accepted only for this wave's moved Haiku chunks")
        else:
            if models is not None and meta["model"] != models[role]:
                raise ValueError("review is not from the qualified model for this role")
            if resolved_models is not None and sorted(actual) != sorted(resolved_models[role]):
                raise ValueError("resolved model changed since qualification")
        chunk_rows = read_jsonl([path])
        summary, _, _ = check_records(chunk_rows, meta["cases"], dossiers)
        if summary["failed"]:
            raise ValueError("review does not pass the checker")
        rows.extend(chunk_rows)
        for r in chunk_rows:
            if r["case"] in provenance:
                raise ValueError("duplicate review for role")
            provenance[r["case"]] = {k: meta[k] for k in ("model", "resolved_models", "reviewer", "guide_hashes", "output_sha256", "chunk_sha256", "call_id")}
            if "fill_of" in meta:
                provenance[r["case"]]["fill_of"] = meta["fill_of"]
    values = {r["case"]: r for r in rows}
    if set(values) != set(index["cases"]):
        raise ValueError("reviewer coverage differs from manifest")
    return values, provenance


def cumulative_reviews(a, b, pa, pb, history_a, history_b, index, dossiers, pair, fill=None):
    """Q1 uses all earlier paired reviews without changing this wave's adjudication sample."""
    if bool(history_a) != bool(history_b):
        raise ValueError("both history reviewer sets are required")
    required_history = set()
    batch_cases = set()
    if index.get("stage") == "stage1" and index.get("wave", 0) > 1:
        from miami_label_chunks import ordered_population
        _, batch, stage1, _ = ordered_population()
        required_history = set(stage1[:(index["wave"] - 1) * 500])
        batch_cases = set(batch)
    if not history_a and required_history:
        raise ValueError("later waves require all earlier reviews for cumulative Q1")
    if not history_a:
        return a, b, pb
    cases_a = [c for p in history_a for c in json.loads(Path(p).with_suffix(".meta.json").read_text())["cases"]]
    cases_b = [c for p in history_b for c in json.loads(Path(p).with_suffix(".meta.json").read_text())["cases"]]
    if len(cases_a) != len(set(cases_a)) or len(cases_b) != len(set(cases_b)) or set(cases_a) != set(cases_b):
        raise ValueError("unpaired or duplicate history reviews")
    if not required_history <= set(cases_a):
        raise ValueError("history omits earlier stage1 cases")
    if required_history and not set(cases_a) <= required_history | batch_cases:
        raise ValueError("history includes a future stage1 case")
    if set(cases_a) & set(a):
        raise ValueError("history repeats a current-wave case")
    from miami_label_chunks import ordered_population
    population, _, _, _ = ordered_population()
    if not set(cases_a) <= set(population):
        raise ValueError("history outside the study population")
    history_index = dict(index, cases=cases_a)
    ha, _ = checked_inputs(history_a, "A", history_index, dossiers, pair["models"], pair["resolved_models"])
    hb, hpb = checked_inputs(history_b, "B", history_index, dossiers, pair["models"], pair["resolved_models"],
                             dict(fill, index_sha256=None) if fill else None)
    return dict(ha, **a), dict(hb, **b), dict(hpb, **pb)


def fill_identity(pair, index, index_path):
    """A second Grok may stand in for B only when the qualified B is another model."""
    if pair.get("selected_B") in (None, "grok"):
        return None
    return {"model": pair["models"]["A"], "resolved": pair["resolved_models"]["A"],
            "index_sha256": sha(index_path) if index.get("stage") == "stage1" else None}


def by_pair(a, b, provenance, pair):
    """Agreement separately for Grok + B-model cases and Grok + Grok cases (moved chunks); reported, not a rule."""
    groups = {}
    for c in sorted(a):
        groups.setdefault("grok-grok" if "fill_of" in provenance[c] else pair.get("pair", "pair"), []).append(c)
    return {name: {"cases": len(ids), "agreement": agreement(a, b, ids)} for name, ids in sorted(groups.items())}


def verify_wave_reports(paths, a, b, ids, guide_hashes):
    """Preserve every wave's mandatory adjudications and random 10% in the final merge."""
    covered, required = set(), set()
    for path in paths:
        report = json.loads(Path(path).read_text())
        cases = report["case_ids"]
        if (len(cases) != len(set(cases)) or covered & set(cases) or not set(cases) <= set(ids)
                or report["guide_hashes"] != guide_hashes or report.get("Q1", {}).get("status") not in {"pass", "inspect"}):
            raise ValueError("wave reports overlap, changed guide or have invalid coverage")
        expected = adjudication_list(a, b, cases)
        if report["adjudications"] != expected:
            raise ValueError("wave audit selection differs from the paired reviews")
        covered.update(cases)
        required.update(expected)
    if covered != set(ids):
        raise ValueError("wave reports must cover the entire final population")
    return required


def write_private(path, data):
    path = private_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(data)
    temporary.replace(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("q0", "pair", "list", "merge"))
    ap.add_argument("--index", required=True)
    ap.add_argument("--a", nargs="+", required=True, help="A reviews (stage-0 Grok outputs for q0 and pair)")
    ap.add_argument("--b", nargs="+", required=True, help="B reviews (the candidate's test outputs for pair)")
    ap.add_argument("--candidate", choices=("composer", "haiku", "luna"), default="composer", help="pair mode: the B model tested")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dossiers", required=True)
    ap.add_argument("--pair")
    ap.add_argument("--decisions")
    ap.add_argument("--exclusions", help="hashed revision exclusion list; default is the 8 guide-v3 cases")
    ap.add_argument("--complete", action="store_true")
    ap.add_argument("--history-a", nargs="+", help="all earlier A reviews, for cumulative Q1")
    ap.add_argument("--history-b", nargs="+", help="all earlier B reviews, for cumulative Q1")
    ap.add_argument("--wave-reports", nargs="+", help="saved per-wave adjudication lists; required for --complete")
    a = ap.parse_args()
    try:
        index = json.loads(Path(a.index).read_text())
        ids = index["cases"]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate manifest case")
        pair = json.loads(Path(a.pair).read_text()) if a.pair else None
        if a.mode in ("list", "merge") and (not pair or not pair.get("qualified") or pair["guide_hashes"] != index["guide_hashes"]):
            raise ValueError("qualified pair under this guide required")
        from miami_label_chunks import model_pins
        pins = model_pins()
        candidates = ("grok", a.candidate) if a.mode == "pair" else ("grok", "sonnet")
        models = pair["models"] if a.mode in ("list", "merge") else {"A": pins[candidates[0]], "B": pins[candidates[1]]}
        resolved = pair["resolved_models"] if a.mode in ("list", "merge") else None
        fill = fill_identity(pair, index, a.index) if a.mode in ("list", "merge") else None
        A, pa = checked_inputs(a.a, "A", index, a.dossiers, models, resolved)
        B, pb = checked_inputs(a.b, "B", index, a.dossiers, models, resolved, fill)
        if a.mode in ("q0", "pair"):
            if set(ids) != set(json.loads((RULES / "sample.json").read_text())["cases"]):
                raise ValueError("Q0 must cover the complete fixed 250-case batch")
            gold = unique([RULES / "final.jsonl"])
            excluded = json.loads(Path(a.exclusions).read_text()) if a.exclusions else EXCLUSIONS_V3
            if a.mode == "q0":
                report = qualification(A, B, gold, ids, excluded)
            else:
                report = pair_decision(A, B, gold, ids, excluded, a.candidate)
            report["guide_hashes"] = index["guide_hashes"]
            actual = {}
            for role, provenance in zip(candidates, (pa, pb)):
                identities = {tuple(sorted(p["resolved_models"])) for p in provenance.values()}
                if len(identities) != 1:
                    raise ValueError("model identity changed within calibration")
                actual[role] = list(next(iter(identities)))
            report["candidate_resolved_models"] = actual
            if a.mode == "q0":
                report["resolved_models"] = {"A": actual[report["selected_A"]], "B": actual["sonnet"]}
            else:
                report["resolved_models"] = {"A": actual["grok"], "B": actual[report["selected_B"]]}
            write_private(a.out, json.dumps(report, indent=2) + "\n")
            print(json.dumps({"Q0": report["Q0"], "qualified": report["qualified"], "models": report["models"], "base": report["base"]}))
            return 0 if report["qualified"] else 2
        ca, cb, cpb = cumulative_reviews(A, B, pa, pb, a.history_a, a.history_b, index, a.dossiers, pair, fill)
        cumulative = agreement(ca, cb, sorted(ca))
        metrics = agreement(A, B, ids)
        why = adjudication_list(A, B, ids)
        # Final population merge reuses the per-wave audit decisions instead of drawing a new 10%.
        report = {"cases": len(ids), "case_ids": ids, "guide_hashes": index["guide_hashes"],
                  "agreement": metrics, "cumulative_agreement": cumulative, "adjudications": why}
        if fill:
            report["by_pair"] = by_pair(A, B, pb, pair)
            report["cumulative_by_pair"] = by_pair(ca, cb, cpb, pair)
        kappas = [cumulative[k]["kappa"] for k in ("struct_described", "eng_pass_first")]
        report["Q1"] = {"status": "undefined" if None in kappas else "stop" if min(kappas) < .6 else "inspect" if min(kappas) < .8 else "pass"}
        if a.mode == "list":
            write_private(a.out, json.dumps(report, indent=2) + "\n")
            print(json.dumps({"cases": len(ids), "adjudications": len(why), "Q1": report["Q1"]}))
            return 2 if report["Q1"]["status"] in ("stop", "undefined") else 0
        if report["Q1"]["status"] in ("stop", "undefined"):
            write_private(str(a.out) + ".stop.json", json.dumps(report, indent=2) + "\n")
            raise ValueError("Q1 must pass before merging a wave")
        if not a.decisions:
            raise ValueError("merge requires decisions, including an empty decisions file when none are listed")
        decisions = unique([a.decisions])
        if a.complete and not a.wave_reports:
            raise ValueError("final merge needs saved wave audit selections")
        required = verify_wave_reports(a.wave_reports, A, B, ids, index["guide_hashes"]) if a.complete else set(why)
        if a.complete:
            report["adjudications"] = {c: reasons(A[c], B[c]) or ["random_10pct"] for c in ids if c in required}
            report["audit_scope"] = "saved_wave_reports"
        if not required <= set(decisions) or not set(decisions) <= set(ids):
            raise ValueError("missing adjudication or decision outside population")
        for d in decisions.values():
            if set(d) != {"case", "take", "set", "reason"} or not isinstance(d["reason"], str) or not d["reason"].strip():
                raise ValueError("invalid adjudication record")
        final = []
        for c in ids:
            r = merge_record(A[c], B[c], pair["base"], decisions.get(c))
            r["review_provenance"] = {"A": pa[c], "B": pb[c]}
            final.append(r)
        summary, errors, flags = check_records(final, ids, a.dossiers, vocabulary(), final=True)
        if errors:
            write_private(str(a.out) + ".checks.json", json.dumps({"summary": summary, "errors": errors, "flags": flags}, indent=2) + "\n")
            raise ValueError("final labels failed Q2; private diagnostics saved")
        if a.complete:
            from miami_label_chunks import ordered_population
            us, _, _, _ = ordered_population()
            if len(final) != 6667 or set(ids) != set(us):
                raise ValueError("final dataset must equal the 6,667-case population")
        positives = [r for r in final if r["category"] == "STRUCT_DESCRIBED"]
        dated = sum(bool(r["earliest_defect_date"] and r["defect_passage"]) for r in positives)
        report["Q3"] = {"positives": len(positives), "dated": dated, "pass": dated / len(positives) >= .8 if positives else False}
        report["Q2"] = summary
        report["field_disagreements"] = dict(Counter(k for r in final for k in r["field_disagreements"]))
        write_private(a.out, "".join(json.dumps(r) + "\n" for r in final))
        write_private(str(a.out) + ".report.json", json.dumps(report, indent=2) + "\n")
        write_private(str(a.out) + ".name_flags.json", json.dumps(flags, indent=2) + "\n")
        print(json.dumps({"final": len(final), "adjudications": len(decisions), "Q2": summary, "Q3": report["Q3"], "name_check_pending": len(flags)}))
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        print("FAIL merge inputs, qualification, provenance or final checks; inspect private diagnostics", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
