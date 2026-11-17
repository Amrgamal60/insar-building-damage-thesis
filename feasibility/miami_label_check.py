"""Check v3 labels, exact chunk coverage, cited evidence and names; never open InSAR.

Run from Alex/: python3 -I feasibility/miami_label_check.py --index INDEX.json
  --chunk CHUNK_ID --dossiers PRIVATE_DIR OUTPUT.jsonl [--flags-file PRIVATE.json]
The default output contains diagnostics without quotes or possible personal names.
Only --show-flags prints flagged words (use only inside a private reviewer log).
Reviewer mode: python3 -I .../miami_label_check.py --call PRIVATE_CALL_DIR, and nothing else.
The expected cases, dossier folder and output come from the launcher's call.json in that folder;
the output must be the folder's output.jsonl. FLAG lines show only words from that output.
"""
import argparse
import calendar
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from miami_passage_check import WORD, lines, norm, vocabulary

FIELDS = {
    "case", "category", "category_passage", "element", "condition", "deficiency_basis", "basis_passage",
    "assessment", "assessment_passage", "assessment_date", "assessment_text_date", "approval_wording",
    "pathway", "open_date", "earliest_defect_date", "defect_passage", "defect_text_date", "defect_text_passage",
    "building", "complex", "complex_passage", "related", "confidence", "note",
}
PASSAGES = ("category_passage", "assessment_passage", "defect_passage", "defect_text_passage",
            "basis_passage", "complex_passage")
ENUMS = {
    "category": {"STRUCT_DESCRIBED", "EVENT", "DEFICIENCY_UNDESCRIBED", "OTHER_PHYS", "ADMIN_ONLY", "UNCLEAR"},
    "assessment": {"ENG_DEFECT_DESCRIBED", "INSP_DEFECT_DESCRIBED", "EVENT_DAMAGE", "ENG_DEFECT_UNDESCRIBED",
                   "ENG_PASS_AFTER_REJECTION", "ENG_PASS_FIRST", "INSP_NO_DEFECT_EXPLICIT", "INSP_NO_DEFECT_NOTED", "NONE"},
    "pathway": {"RECERT", "COMPLAINT", "OTHER_AGENCY", "CARRYOVER", "INSPECTOR", "OTHER"},
    "complex": {"YES", "NO", "UNCLEAR"}, "confidence": {"high", "medium", "low"},
    "deficiency_basis": {"", "FINDING", "UNSTATED", "DOCUMENTARY"},
    "approval_wording": {"", "STRUCTURAL", "GENERIC"},
}
RELATIONS = {"SAME_EPISODE", "SIBLING_BUILDING", "SEPARATE_EPISODE", "UNCLEAR"}
TYPES = {"SINGLE_FAMILY", "MULTIFAMILY", "COMMERCIAL", "OTHER", "UNKNOWN"}
DEFECT = {"STRUCT_DESCRIBED", "DEFICIENCY_UNDESCRIBED", "EVENT"}
APPROVAL = {"ENG_PASS_FIRST", "ENG_PASS_AFTER_REJECTION"}
ID = re.compile(r"^[A-Za-z0-9_-]+$")


def dossier_lines(path):
    """Keep every F- entry: the fixed dossier format reuses that ID for missing linked cases."""
    result = {}
    for raw in Path(path).read_text().splitlines():
        match = re.match(r"^([HTVSAF]\d+|F-) (.*)$", raw)
        if not match:
            continue
        lid, text = match.groups()
        if lid in result:
            if lid != "F-":
                raise ValueError("duplicate dossier line ID")
            result[lid] += "\n" + norm(text)
        else:
            result[lid] = norm(text)
    return result


def read_jsonl(paths):
    records = []
    def object_unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate object key")
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError("non-JSON numeric constant")
    for path in paths:
        for number, raw in enumerate(Path(path).read_text().splitlines(), 1):
            if raw.strip():
                try:
                    record = json.loads(raw, object_pairs_hook=object_unique, parse_constant=invalid_constant)
                except ValueError:
                    raise ValueError(f"invalid JSON at record {number}") from None
                if not isinstance(record, dict):
                    raise ValueError(f"record {number} is not an object")
                records.append(record)
    return records


def date_range(value, partial=False):
    """Inclusive bounds for an ISO day, month or year; reject malformed dates."""
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}(?:-\d{2}){0,2}", value):
        raise ValueError("invalid date")
    parts = [int(x) for x in value.split("-")]
    if len(parts) == 3:
        d = date(*parts)
        return d, d
    if not partial:
        raise ValueError("full date required")
    if len(parts) == 2:
        y, m = parts
        return date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])
    return date(parts[0], 1, 1), date(parts[0], 12, 31)


def line_date(line_id, text):
    if line_id.startswith("A"):
        m = re.match(r"(\d{4}-\d{2}-\d{2})\b", text)
    elif line_id.startswith("V"):
        m = re.search(r"\| date (\d{4}-\d{2}-\d{2})\b", text)
    else:
        m = None
    return m.group(1) if m else ""


def private_output(path):
    project = Path(__file__).resolve().parents[1]
    target = Path(path).resolve()
    if target == project or project in target.parents:
        raise ValueError("raw outputs and name flags must stay outside the project")
    return target


def check_records(records, expected, dossiers, vocab=None, final=False):
    errors, flags, passages = [], [], 0
    expected = list(expected)
    if len(expected) != len(set(expected)):
        raise ValueError("duplicate case IDs in the expected list")
    counts = Counter(r.get("case") for r in records if isinstance(r.get("case"), str))
    for cn in expected:
        if counts[cn] != 1:
            errors.append((cn, "coverage", "case must occur exactly once"))
    for cn in counts.keys() - set(expected):
        errors.append((cn if ID.fullmatch(cn) else "?", "coverage", "unexpected case"))
    for i, r in enumerate(records):
        cn = r.get("case")
        tag = cn if isinstance(cn, str) and ID.fullmatch(cn) else f"record-{i + 1}"
        def fail(field, message):
            errors.append((tag, field, message))
        extra = {"adjudication", "field_disagreements", "review_provenance"} if final else set()
        if set(r) - FIELDS - extra or FIELDS - set(r):
            fail("schema", "missing or extra fields")
        if not isinstance(cn, str) or not ID.fullmatch(cn) or cn not in set(expected):
            fail("case", "invalid or unexpected case ID")
            continue
        for field, allowed in ENUMS.items():
            if not isinstance(r.get(field), str) or r[field] not in allowed:
                fail(field, "value outside allowed set")
        for field in ("element", "condition", "note", "open_date", "earliest_defect_date",
                      "assessment_date", "assessment_text_date", "defect_text_date"):
            if not isinstance(r.get(field), str):
                fail(field, "must be a string")
        try:
            content = dossier_lines(Path(dossiers) / f"{cn}.txt")
        except (OSError, ValueError):
            fail("dossier", "missing or unreadable dossier")
            continue
        for field in PASSAGES:
            p = r.get(field)
            if p is None:
                continue
            if not isinstance(p, dict) or set(p) != {"line", "quote"}:
                fail(field, "passage must have line and quote")
                continue
            line, quote = p.get("line"), p.get("quote")
            if not isinstance(line, str) or not isinstance(quote, str):
                fail(field, "line and quote must be strings")
                continue
            passages += 1
            if (not quote.strip() or len(quote) > 300 or line not in content
                    or not any(norm(quote) in text for text in content.get(line, "").split("\n"))):
                fail(field, "quote absent from cited line, empty, or longer than 300 characters")
        def required(field, yes, otherwise_empty=False):
            if yes and not r.get(field):
                fail(field, "required")
            if not yes and otherwise_empty and r.get(field) not in (None, ""):
                fail(field, "must be empty for this classification")
        required("category_passage", True)
        required("assessment_passage", r.get("assessment") != "NONE", True)
        required("basis_passage", r.get("category") == "DEFICIENCY_UNDESCRIBED", True)
        required("deficiency_basis", r.get("category") == "DEFICIENCY_UNDESCRIBED", True)
        required("approval_wording", r.get("assessment") in APPROVAL, True)
        required("defect_passage", r.get("category") in DEFECT, True)
        required("complex_passage", r.get("complex") == "YES")
        if r.get("category") == "STRUCT_DESCRIBED":
            required("element", True)
            required("condition", True)
        for field in ("open_date", "earliest_defect_date", "assessment_date", "defect_text_date", "assessment_text_date"):
            value = r.get(field)
            if value:
                try:
                    date_range(value, field.endswith("text_date"))
                except (ValueError, TypeError):
                    fail(field, "invalid ISO date or precision")
        header = re.search(r"\bopen date: (\d{4}-\d{2}-\d{2})", content.get("H1", ""))
        if not header or r.get("open_date") != header.group(1):
            fail("open_date", "does not match H1")
        for field, passage in (("earliest_defect_date", "defect_passage"), ("assessment_date", "assessment_passage")):
            p = r.get(passage)
            ld = line_date(p.get("line", ""), content.get(p.get("line", ""), "")) if isinstance(p, dict) else ""
            if r.get(field) != ld:
                fail(field, "must match the cited line date; undated lines require empty date")
        for field, passage in (("defect_text_date", "defect_passage"), ("assessment_text_date", "assessment_passage")):
            value = r.get(field)
            if not value:
                if field == "defect_text_date" and r.get("defect_text_passage") is not None:
                    fail("defect_text_passage", "requires a text date")
                continue
            p = r.get("defect_text_passage") or r.get(passage) if field == "defect_text_date" else r.get(passage)
            ld = line_date(p.get("line", ""), content.get(p.get("line", ""), "")) if isinstance(p, dict) else ""
            try:
                if not ld or date_range(value, True)[0] >= date_range(ld)[0]:
                    fail(field, "text date must be earlier than its evidence line date")
            except (ValueError, TypeError):
                pass  # already reported as an invalid date
        building = r.get("building")
        if not isinstance(building, dict) or set(building) != {"label", "type", "stories"}:
            fail("building", "invalid building fields")
        elif (not isinstance(building["label"], str) or building["type"] not in TYPES
              or (building["stories"] is not None and (type(building["stories"]) is not int or building["stories"] < 0))):
            fail("building", "invalid building values")
        related = r.get("related")
        seen_related = set()
        if not isinstance(related, list):
            fail("related", "must be a list")
        else:
            for link in related:
                if not isinstance(link, dict) or set(link) != {"case", "relation", "line", "reason"}:
                    fail("related", "invalid relation fields")
                    continue
                target = link.get("case")
                if not isinstance(target, str) or not ID.fullmatch(target) or target in seen_related or target == cn:
                    fail("related", "invalid or duplicate related case")
                    continue
                seen_related.add(target)
                line = link.get("line")
                if (link.get("relation") not in RELATIONS or not isinstance(link.get("reason"), str)
                        or not isinstance(line, str) or line not in content
                        or not re.search(r"(?<![A-Za-z0-9])" + re.escape(target) + r"(?![A-Za-z0-9])", content.get(line, ""))):
                    fail("related", "invalid relation or case absent from cited line")
            f_cases = {m.group(0) for lid, text in content.items() if lid.startswith("F")
                       for m in re.finditer(r"^[A-Za-z]*\d{8,}", text, re.M)}
            if not f_cases <= seen_related:
                fail("related", "not every F-line case was listed")
        if vocab is not None:
            for field, text in free_text(r):
                odd = sorted({w for w in WORD.findall(text) if w.lower() not in vocab and w.lower().rstrip("'s") not in vocab})
                if odd:
                    flags.append({"case": cn, "field": field, "words": odd})
    return {"records": len(records), "expected": len(expected), "passages": passages,
            "failed": len(errors), "flagged_for_names": len(flags)}, errors, flags


def free_text(record, prefix=""):
    """Include all strings, including nested decisions and A/B disagreement values."""
    if isinstance(record, dict):
        for key, value in record.items():
            yield from free_text(value, f"{prefix}.{key}".strip("."))
    elif isinstance(record, list):
        for i, value in enumerate(record):
            yield from free_text(value, f"{prefix}[{i}]")
    elif isinstance(record, str):
        non_text = {"case", "category", "assessment", "deficiency_basis", "approval_wording", "pathway", "type",
                    "complex", "confidence", "line", "review_provenance"}
        if not set(prefix.split(".")) & non_text:
            yield prefix, record


def check_call(call):
    """Reviewer mode: everything but the folder comes from the manifest the reviewer cannot write."""
    call = private_output(call)
    manifest = json.loads((call / "call.json").read_text())
    output = Path(manifest["output"]).resolve()
    if output != call / "output.jsonl":
        raise ValueError("manifest output is not this call folder's output.jsonl")
    return check_records(read_jsonl([output]), manifest["cases"], manifest["dossiers"], vocabulary())


def main_call(argv):
    if len(argv) != 2:
        print("FAIL input: reviewer mode takes only --call <call folder>")
        return 1
    try:
        summary, errors, flags = check_call(argv[1])
    except ValueError as exc:
        print(f"FAIL input: {exc}")
        return 1
    except (OSError, KeyError, TypeError):
        print("FAIL input: missing or unreadable call manifest, output or dossier")
        return 1
    print(json.dumps(summary))
    for error in errors:
        print("FAIL", *error)
    for flag in flags:
        print("FLAG", json.dumps(flag))
    return bool(errors)


def main():
    if sys.argv[1:2] == ["--call"]:
        return main_call(sys.argv[1:])
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index", required=True)
    ap.add_argument("--chunk", required=True)
    ap.add_argument("--dossiers", required=True)
    ap.add_argument("--flags-file")
    ap.add_argument("--show-flags", action="store_true")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    try:
        index = json.loads(Path(a.index).read_text())
        expected = index["cases"] if a.chunk == "ALL" else index["chunks"][a.chunk]["cases"]
        summary, errors, flags = check_records(read_jsonl(a.files), expected, a.dossiers, vocabulary(), a.final)
        if a.flags_file:
            private_output(a.flags_file).write_text(json.dumps(flags, indent=2) + "\n")
        print(json.dumps(summary))
        for error in errors:
            print("FAIL", *error)
        if a.show_flags:
            for flag in flags:
                print("FLAG", json.dumps(flag))
        return bool(errors)
    except (OSError, ValueError, KeyError, TypeError):
        print("FAIL input: unreadable or invalid index, dossier, vocabulary or JSON Lines")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
