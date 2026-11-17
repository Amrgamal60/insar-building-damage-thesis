"""Pre-documentation OPERA DISP-S1 coverage of the settlement-review buildings (PROTOCOL_SETTLEMENT.md §9).

Outcome-blind, as audit_miami_prewindow.py: per granule only pixel validity is read (finite displacement and
recommended_mask == 1). No displacement value is used, printed or related to a case.
For each adjudicated GFM / GEOM_UNRESOLVED case with a doc_date, at its dossier H2 point:
  inside the downloaded frame subset; granules and years of series before doc_date; and for W = 1, 2, 3 years whether
  the window [doc_date - W, doc_date) qualifies: starts inside the series (>= first date), doc_date no later than
  90 days after the last granule, and the pixel valid in >= 80% of the window's granules.
Input  Alex_private/miami_settlement/final.jsonl
Writes miami/audit/settlement/coverage.json (case numbers, folios, counts; no names, no InSAR values)
Run from Alex/:  OMP_NUM_THREADS=1 ~/miniforge3/envs/opera/bin/python -I feasibility/miami_settlement_coverage.py
"""
import json
import re
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent
PRIV = ROOT.parent.parent / "Alex_private" / "miami_settlement"
DOS = ROOT.parent.parent / "Alex_private" / "miami_dossiers_full"
D = ROOT / "miami" / "downloads" / "opera_disp"
OUT = ROOT / "miami" / "audit" / "settlement" / "coverage.json"
SHARE, LATE_DAYS = 0.8, 90


def point(case):
    for ln in (DOS / f"{case}.txt").read_text(errors="replace").splitlines():
        m = re.match(r"^H2 .*point: \[(-?[\d.]+), (-?[\d.]+)\]", ln)
        if m:
            return float(m.group(1)), float(m.group(2))
    return None


def main():
    recs = [json.loads(x) for x in (PRIV / "final.jsonl").read_text().splitlines() if x.strip()]
    recs = [r for r in recs if r["class"] in ("GFM", "GEOM_UNRESOLVED")]
    files = sorted(D.glob("*.nc"))
    obs = pd.to_datetime([re.search(r"_VV_\d{8}T\d{6}Z_(\d{8})T", f.name).group(1) for f in files])
    first = pd.Timestamp(re.search(r"_VV_(\d{8})T", files[0].name).group(1))
    with h5py.File(files[0]) as h:
        x, y = h["x"][:], h["y"][:]
    tr = Transformer.from_crs("EPSG:4326", "EPSG:32617", always_xy=True)
    rows = []
    for r in recs:
        p = point(r["case"])
        row = {"case": r["case"], "class": r["class"], "folio": (r.get("building") or {}).get("folio", ""),
               "doc_date": r.get("doc_date", ""), "has_point": p is not None}
        if p and r.get("doc_date"):
            X, Y = tr.transform(*p)
            ci, ri = int(round((X - x[0]) / (x[1] - x[0]))), int(round((Y - y[0]) / (y[1] - y[0])))
            row["inside_subset"] = bool(0 <= ri < len(y) and 0 <= ci < len(x))
            row.update(ri=ri, ci=ci)
        rows.append(row)
    pts = [w for w in rows if w.get("inside_subset")]
    valid = np.zeros((len(files), len(pts)), bool)
    if pts:
        rr, cc = np.array([w["ri"] for w in pts]), np.array([w["ci"] for w in pts])
        for k, f in enumerate(files):
            with h5py.File(f) as h:
                valid[k] = np.isfinite(h["displacement"][:][rr, cc]) & (h["recommended_mask"][:][rr, cc] == 1)
    for j, w in enumerate(pts):
        d = pd.Timestamp(w["doc_date"])
        before = obs < d
        w["granules_before_doc"] = int(before.sum())
        # Codex 2026-10-25: observations stop at the last granule, even for later documents.
        w["years_of_series_before_doc"] = round(max(0.0, (min(d, obs.max()) - first).days / 365.25), 2)
        w["valid_share_before_doc"] = round(float(valid[before, j].mean()), 3) if before.any() else None
        w["doc_within_90d_of_last_granule"] = bool(d <= obs.max() + pd.Timedelta(days=LATE_DAYS))
        for W in (1, 2, 3):
            s = d - pd.DateOffset(years=W)
            inwin = (obs >= s) & before
            n = int(inwin.sum())
            share = float((valid[:, j] & np.asarray(inwin)).sum() / n) if n else 0.0
            w[f"window_{W}y"] = {"granules": n, "valid_share": round(share, 3),
                                 "qualifies": bool(s >= first and w["doc_within_90d_of_last_granule"] and n > 0
                                                   and share >= SHARE)}
    for w in rows:
        w.pop("ri", None), w.pop("ci", None)
    summ = {"cases": len(rows), "inside_subset": len(pts),
            "series": [str(first.date()), str(obs.max().date())], "granules": len(files)}
    for cls in ("GFM", "GEOM_UNRESOLVED"):
        sub = [w for w in pts if w["class"] == cls]
        summ[cls] = {"cases_inside": len(sub), **{f"qualifying_{W}y": sum(w[f"window_{W}y"]["qualifies"] for w in sub)
                                                  for W in (1, 2, 3)},
                     "qualifying_2y_folios": len({w["folio"] for w in sub if w["window_2y"]["qualifies"]})}
    OUT.write_text(json.dumps({"rule": __doc__.split("\n\n")[0], "summary": summ, "cases": rows}, indent=1) + "\n")
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
