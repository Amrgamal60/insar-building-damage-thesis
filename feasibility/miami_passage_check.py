"""Miami-Dade label validation: check every supporting passage against its dossier line (PROTOCOL_v2.md §5), and flag
words in passages that could be personal names. No InSAR file is opened.

For each JSON Lines record and each passage field (category_passage, assessment_passage, defect_passage,
complex_passage), the cited line must exist in the case's dossier and the quote must be a contiguous piece of it
(compared after collapsing whitespace; the line ID and the date/code prefix may be left out). Words in a quote that are
neither in the lower-case English word list (/usr/share/dict/american-english) nor in the standard wording of the
viewer's codes (violations.csv, activities.csv of the first audit) nor plain numbers are flagged for a person to look at.
Flags are printed only; nothing with possible names is written by this script.
Run from Alex/:  python3 -I feasibility/miami_passage_check.py --dossiers <dir> FILE.jsonl [FILE.jsonl ...]
"""
import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "miami" / "audit"
FIELDS = ("category_passage", "assessment_passage", "defect_passage", "complex_passage")
WORD = re.compile(r"[A-Za-z][A-Za-z'’]+")
DOMAIN = {"spalled", "spalling", "spall", "spalls", "rebar", "rebars", "porte", "cochere", "pavillion", "cbs", "sqft",
          "sq", "ft", "lf", "struc", "bldg", "nov", "efus", "fbc", "mdfr", "goldkey", "recertification", "recert", "unpermitted"}


def vocabulary():
    words = {w.strip() for w in open("/usr/share/dict/american-english", encoding="utf-8") if w.strip().islower()}
    words |= {w.rstrip("'s") for w in list(words)}
    for name, col in (("violations.csv", "description"), ("activities.csv", "description")):
        with open(ROOT / "label_sample" / name, newline="") as fh:
            for r in csv.DictReader(fh):
                words |= {w.lower() for w in WORD.findall(r[col])}
    return words | DOMAIN


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def lines(path):
    out = {}
    for ln in path.read_text().splitlines():
        m = re.match(r"^([HTVSAF]\d+|F-) (.*)$", ln)
        if m:
            out[m.group(1)] = norm(m.group(2))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dossiers", required=True)
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    vocab = vocabulary()
    cache, bad, flags, n = {}, [], [], 0
    for f in a.files:
        for k, raw in enumerate(open(f), 1):
            if not raw.strip():
                continue
            r = json.loads(raw)
            cn = r["case"]
            if cn not in cache:
                cache[cn] = lines(Path(a.dossiers) / f"{cn}.txt")
            for fld in FIELDS:
                p = r.get(fld)
                if not p:
                    continue
                n += 1
                line, quote = p.get("line", ""), norm(p.get("quote", ""))
                if line not in cache[cn]:
                    bad.append((f, cn, fld, f"line {line} not in dossier"))
                elif not quote or quote not in cache[cn][line]:
                    bad.append((f, cn, fld, f"quote not found in {line}"))
                odd = sorted({w for w in WORD.findall(quote) if w.lower().rstrip("'s") not in vocab and w.lower() not in vocab})
                if odd:
                    flags.append((cn, fld, odd))
    print(json.dumps({"passages": n, "failed": len(bad), "flagged_for_names": len(flags)}))
    for b in bad:
        print("FAIL", *b)
    for fl in flags:
        print("FLAG", *fl)


if __name__ == "__main__":
    main()
