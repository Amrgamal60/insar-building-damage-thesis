"""Miami-Dade settlement screen and review sample (PROTOCOL_SETTLEMENT.md §3-4, exploratory refinement 2026-10-25).

Reproduces the keyword screen first run on 2026-10-25 (fixed as run), draws the seeded random sample of non-matching
dossiers, and assigns the review cases to blind batches for readers A and B. Reads only the full dossiers; no label,
no InSAR file.

Writes
  miami/audit/settlement/screen.json                        name-free: matches (case, terms, line IDs), strata, sample
  Alex_private/miami_settlement/screen_contexts.jsonl       match contexts (may hold names)
  Alex_private/miami_settlement/review_batches.json         reader A and B batches (case numbers only)
Run from Alex/:  ~/miniforge3/envs/opera/bin/python -I feasibility/miami_settlement_screen.py
"""
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
DOS = ROOT.parent.parent / "Alex_private" / "miami_dossiers_full"
PRIV = ROOT.parent.parent / "Alex_private" / "miami_settlement"
OUT = ROOT / "miami" / "audit" / "settlement" / "screen.json"
SEED, N_H, N_L, D_MAX, BATCH = 20261025, 150, 50, 60, 25

PHYS = r"(crack|foundation|footing|floor|slab|wall|ground|soil|column|pile|structure|building|dwelling)"
PATS = {
    "settlement": r"settl(e|ed|ement|ing)[^.|]{0,40}" + PHYS + "|" + PHYS + r"[^.|]{0,40}settl(e|ed|ement|ing)",
    "subsidence": r"subsiden|subsided",
    "sinkhole": r"sink ?hole|sinking",
    "foundation": r"foundation[^.|]{0,60}(crack|fail|settl|damag|expos|undermin|sink|deterior|compromis)"
                  r"|(crack|fail|settl|damag|expos|undermin|sink|deterior|compromis)[^.|]{0,60}foundation",
    "undermined": r"undermin",
    "plumb_lean": r"out[- ]of[- ]plumb|\bleaning\b|\btilt",
}
FIN = r"settlement (amount|agreement|due|offer|letter)|enfc|enforcement settlement|lien|settled as follows|payment"
NONBLDG = r"fence|gate|carport|sign|pole|tree|shed|canopy|wall fence"
DISTRESS = r"crack|sag|collaps|structural damage|deform|bow(ed|ing)|buckl|depress|uneven|displac|shift"


def body(text):
    return [ln for ln in text.splitlines() if not re.match(r"^(F|V)\d+ ", ln)]


def screen(lines):
    """Return (hits, dropped_plumb): hits = {term: [line ids]}; dropped_plumb = a plumb_lean hit removed by NONBLDG."""
    hits, dropped, ctx = {}, False, []
    for ln in lines:
        lid = ln.split(" ", 1)[0]
        for k, p in PATS.items():
            for m in re.finditer(p, ln, re.I):
                a = ln[max(0, m.start() - 60):m.end() + 60]
                if k == "settlement" and re.search(FIN, a, re.I):
                    continue
                if k == "plumb_lean" and re.search(NONBLDG, a, re.I):
                    dropped = True
                    continue
                hits.setdefault(k, [])
                if lid not in hits[k]:
                    hits[k].append(lid)
                ctx.append({"term": k, "line": lid, "context": a})
    return hits, dropped, ctx


def main():
    cases = sorted(p.stem for p in DOS.glob("*.txt"))
    matches, ctx_all, drop_only, H, L = {}, [], [], [], []
    for c in cases:
        lines = body((DOS / f"{c}.txt").read_text(errors="replace"))
        hits, dropped, ctx = screen(lines)
        if hits:
            matches[c] = hits
            ctx_all += [dict(x, case=c) for x in ctx]
        elif dropped:
            drop_only.append(c)
        elif any(re.search(DISTRESS, ln, re.I) for ln in lines):
            H.append(c)
        else:
            L.append(c)
    rng = np.random.default_rng(SEED)
    sH = sorted(rng.choice(H, N_H, replace=False).tolist())
    sL = sorted(rng.choice(L, N_L, replace=False).tolist())
    sD = drop_only if len(drop_only) <= D_MAX else sorted(rng.choice(drop_only, D_MAX, replace=False).tolist())
    review = sorted(set(matches) | set(sH) | set(sL) | set(sD))
    batches = {}
    for reader in ("A", "B"):
        order = rng.permutation(review).tolist()
        batches[reader] = [order[i:i + BATCH] for i in range(0, len(order), BATCH)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "protocol": "PROTOCOL_SETTLEMENT.md", "seed": SEED, "dossiers": len(cases),
        "matches": len(matches), "match_terms": {c: matches[c] for c in sorted(matches)},
        "strata": {"H": len(H), "L": len(L), "D_plumb_dropped_only": len(drop_only)},
        "sample": {"H": sH, "L": sL, "D": sD}, "review_cases": len(review)}, indent=1) + "\n")
    PRIV.mkdir(parents=True, exist_ok=True)
    with open(PRIV / "screen_contexts.jsonl", "w") as f:
        for x in ctx_all:
            f.write(json.dumps(x) + "\n")
    (PRIV / "review_batches.json").write_text(json.dumps({"seed": SEED, "batch_size": BATCH, **batches}, indent=1) + "\n")
    print(json.dumps({"matches": len(matches), "H": len(H), "L": len(L), "D": len(drop_only),
                      "sample": [len(sH), len(sL), len(sD)], "review": len(review),
                      "batches": {k: len(v) for k, v in batches.items()}}))


if __name__ == "__main__":
    main()
