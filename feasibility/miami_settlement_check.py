"""Check one reader batch of the settlement review (PROTOCOL_SETTLEMENT.md §6-7).

Every case of the batch is present once, in order; enums are valid; every quote is a verbatim piece (<= 300 chars) of
its dossier line; doc_date equals the date of the line that documents it; UNRELATED has no doc_date.
Run from Alex/:  python3 -I feasibility/miami_settlement_check.py --reader A --batch 3      (or --all)
Prints PASS, or FAIL lines with the reason. Exit code 1 on any FAIL.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRIV = ROOT.parent.parent / "Alex_private" / "miami_settlement"
DOS = ROOT.parent.parent / "Alex_private" / "miami_dossiers_full"
CLASSES = {"GFM", "GEOM_UNRESOLVED", "INSUFFICIENT", "UNRELATED"}
SOURCES = {"INSPECTOR", "ENGINEER", "AGENCY", "PUBLIC_COMPLAINT", "OWNER_OR_OTHER", "NONE"}
TYPES = {"SINGLE_FAMILY", "MULTIFAMILY", "COMMERCIAL", "OTHER", "UNKNOWN"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def lines(case):
    d = {}
    for ln in (DOS / f"{case}.txt").read_text(errors="replace").splitlines():
        m = re.match(r"^([A-Z]+\d+) (.*)$", ln)
        if m:
            d[m.group(1)] = m.group(2)
    return d


def line_date(text):
    m = re.match(r"^(\d{4}-\d{2}-\d{2}) \|", text)
    return m.group(1) if m else None


def check_passage(p, L, what):
    if not isinstance(p, dict) or set(p) != {"line", "quote"}:
        return [f"{what} not {{line, quote}}"]
    if p["line"] not in L:
        return [f"{what} line {p['line']} not in dossier"]
    q = p["quote"]
    if not isinstance(q, str) or not q.strip() or len(q) > 300:
        return [f"{what} quote empty or > 300 chars"]
    if q not in L[p["line"]]:
        return [f"{what} quote not verbatim in {p['line']}"]
    return []


def check_record(r, case):
    L, errs = lines(case), []
    if r.get("class") not in CLASSES:
        errs.append(f"class {r.get('class')!r}")
    if r.get("confidence") not in {"high", "medium", "low"}:
        errs.append("confidence")
    if r.get("source") not in SOURCES:
        errs.append(f"source {r.get('source')!r}")
    b = r.get("building")
    if not isinstance(b, dict) or b.get("type") not in TYPES or b.get("complex") not in {"YES", "NO", "UNCLEAR"}:
        errs.append("building")
    if r.get("passage") is not None:
        errs += check_passage(r["passage"], L, "passage")
    elif r.get("class") != "UNRELATED":
        errs.append("passage missing")
    dd = r.get("doc_date", "")
    if r.get("class") == "UNRELATED":
        if dd:
            errs.append("UNRELATED with doc_date")
    elif dd:
        if not DATE.match(dd):
            errs.append("doc_date format")
        src = r.get("doc_passage") or r.get("passage")
        if r.get("doc_passage") is not None:
            errs += check_passage(r["doc_passage"], L, "doc_passage")
        if isinstance(src, dict) and src.get("line") in L and line_date(L[src["line"]]) != dd:
            errs.append(f"doc_date {dd} is not the date of line {src.get('line')}")
    td = r.get("text_date", "")
    if td and not re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", td):
        errs.append("text_date format")
    if not isinstance(r.get("episode_cases", []), list):
        errs.append("episode_cases not a list")
    return errs


def check_batch(reader, n, batches):
    cases = batches[reader][n]
    f = PRIV / f"reader_{reader}" / f"batch_{n:02d}.jsonl"
    if not f.exists():
        return [f"{f.name}: missing"]
    out = []
    try:
        recs = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    except json.JSONDecodeError as e:
        return [f"{f.name}: invalid JSON ({e})"]
    got = [r.get("case") for r in recs]
    if got != cases:
        out.append(f"{f.name}: cases differ from the list (missing {sorted(set(cases) - set(got))}, "
                   f"extra {sorted(set(got) - set(cases))}, order ok={sorted(got) == sorted(cases)})")
    for r in recs:
        if r.get("case") in cases:
            out += [f"{f.name} {r['case']}: {e}" for e in check_record(r, r["case"])]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reader", choices=["A", "B"])
    ap.add_argument("--batch", type=int)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    batches = json.loads((PRIV / "review_batches.json").read_text())
    todo = [(rd, i) for rd in ("A", "B") for i in range(len(batches[rd]))] if a.all else [(a.reader, a.batch)]
    fails = []
    for rd, i in todo:
        fails += check_batch(rd, i, batches)
    for x in fails:
        print("FAIL", x)
    if not fails:
        print("PASS", len(todo), "batch(es)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
