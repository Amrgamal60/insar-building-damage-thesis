"""Compare readers A and B of the settlement review and list the cases Claude settles (PROTOCOL_SETTLEMENT.md §7).

Settled by Claude: class differs; or either reader says GFM, GEOM_UNRESOLVED or INSUFFICIENT and they differ on
folio, building label, doc_date or same-episode cases. Every case either reader calls GFM or GEOM_UNRESOLVED is also
listed for verification, since it goes on to the engineer.
Writes Alex_private/miami_settlement/compare.json (private: holds quotes) and prints a name-free summary.
Run from Alex/:  python3 -I feasibility/miami_settlement_compare.py
"""
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRIV = ROOT.parent.parent / "Alex_private" / "miami_settlement"
SCREEN = ROOT / "miami" / "audit" / "settlement" / "screen.json"
KEEP = ("GFM", "GEOM_UNRESOLVED", "INSUFFICIENT")


def load(reader):
    out = {}
    for f in sorted((PRIV / f"reader_{reader}").glob("batch_*.jsonl")):
        for line in f.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["case"]] = r
    return out


def kappa(pairs):
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n / n
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0


def stratum_of(screen):
    s = {c: "MATCH" for c in screen["match_terms"]}
    for k, cases in screen["sample"].items():
        for c in cases:
            s[c] = k
    return s


def main():
    A, B = load("A"), load("B")
    strat = stratum_of(json.loads(SCREEN.read_text()))
    both = sorted(set(A) & set(B))
    settle, verify, table = [], [], collections.Counter()
    for c in both:
        a, b = A[c], B[c]
        table[(a["class"], b["class"])] += 1
        why = []
        if a["class"] != b["class"]:
            why.append("class")
        elif a["class"] in KEEP:
            ba, bb = a.get("building") or {}, b.get("building") or {}
            if (ba.get("folio") or "").strip() != (bb.get("folio") or "").strip():
                why.append("folio")
            if (ba.get("label") or "").strip().lower() != (bb.get("label") or "").strip().lower():
                why.append("building_label")
            if a.get("doc_date", "") != b.get("doc_date", ""):
                why.append("doc_date")
            if sorted(a.get("episode_cases") or []) != sorted(b.get("episode_cases") or []):
                why.append("episode")
        row = {"case": c, "stratum": strat.get(c), "why": why, "A": a, "B": b}
        if why:
            settle.append(row)
        elif a["class"] in ("GFM", "GEOM_UNRESOLVED"):
            verify.append(row)
    summ = {
        "cases_A": len(A), "cases_B": len(B), "cases_both": len(both),
        "class_table_A_by_B": {f"{k[0]}|{k[1]}": v for k, v in sorted(table.items())},
        "agree_class": sum(v for k, v in table.items() if k[0] == k[1]),
        "kappa_class": kappa([(A[c]["class"], B[c]["class"]) for c in both]),
        "kappa_GFM": kappa([(A[c]["class"] == "GFM", B[c]["class"] == "GFM") for c in both]),
        "kappa_GFM_or_GEOM": kappa([(A[c]["class"] in ("GFM", "GEOM_UNRESOLVED"),
                                     B[c]["class"] in ("GFM", "GEOM_UNRESOLVED")) for c in both]),
        "to_settle": len(settle), "settle_reasons": dict(collections.Counter(w for r in settle for w in r["why"])),
        "agreed_positive_to_verify": len(verify),
        "by_stratum_any_reader_keep": dict(collections.Counter(
            strat.get(c) for c in both if A[c]["class"] in KEEP or B[c]["class"] in KEEP)),
    }
    (PRIV / "compare.json").write_text(json.dumps({"summary": summ, "settle": settle, "verify": verify}, indent=1) + "\n")
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
