"""Coordinator's independent application of the registered Test A null-selection rule.

AUSTIN_PLAN.md §10 (registered 2026-11-01) and calibration/DESIGN.md: a null is
acceptable in a null cell if (1) Wilson 95% lower bound of the rejection rate <= .05,
(2) point rate <= .075, (3) the 95% Student-t interval of the paired bias
(observed minus the dataset's own mean of 99 null statistics) has lower bound <= 0.
Null cells: A_00-A_07 (small), A_10-A_11 (4x). Refuses to run unless all are complete.
"""
import glob
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

CAL = Path("/mnt/data/Master-projects/Alex/feasibility/austin/scripts/calibration")
sys.path[:0] = [str(CAL), str(CAL.parent)]
from run_calibration import source_hashes

NULL_CELLS = [f"A_{c:02d}" for c in (0, 1, 2, 3, 4, 5, 6, 7, 10, 11)]
EXPECTED = {**{c: 200 for c in NULL_CELLS[:8]}, "A_10": 100, "A_11": 100}
Z = stats.norm.ppf(.975)


def wilson(k, n):
    p = k/n
    centre = (p+Z**2/(2*n))/(1+Z**2/n)
    half = Z*np.sqrt(p*(1-p)/n+Z**2/(4*n**2))/(1+Z**2/n)
    return centre-half, centre+half


missing = [c for c in NULL_CELLS if not (CAL/f"complete_{c}.json").exists()]
if missing:
    sys.exit(f"not complete: {missing}; rule not applied")
fingerprint = source_hashes()
rows, ok = [], {"registered": True, "conditional": True}
for cell in NULL_CELLS:
    files = sorted(glob.glob(str(CAL/"records"/f"{cell}_*.json")))
    records = [json.loads(Path(f).read_text()) for f in files]
    assert len(records) == EXPECTED[cell], (cell, len(records))
    assert all(r["status"] == "complete" and r["source_hashes"] == fingerprint for r in records), cell
    assert all(r["effect"] == 0. for r in records), cell
    backends = dict(zip(*np.unique([r.get("execution_backend", "cpu") for r in records], return_counts=True)))
    for kind in ("registered", "conditional"):
        nulls = [r["nulls"][kind] for r in records]
        for r, x in zip(records, nulls):
            assert len(x["statistics"]) == 99
            exceed = int(np.sum(np.asarray(x["statistics"]) >= r["observed"]))
            assert exceed == x["exceedances"] and abs((1+exceed)/100-x["p"]) < 1e-12 and x["reject"] == (x["p"] < .05)
        n = len(records)
        k = sum(x["reject"] for x in nulls)
        lo, hi = wilson(k, n)
        bias = np.array([r["observed"]-np.mean(x["statistics"]) for r, x in zip(records, nulls)])
        b_mean, b_se = bias.mean(), bias.std(ddof=1)/np.sqrt(n)
        b_lo = b_mean-stats.t.ppf(.975, n-1)*b_se
        b_hi = b_mean+stats.t.ppf(.975, n-1)*b_se
        acceptable = lo <= .05 and k/n <= .075 and b_lo <= 0
        ok[kind] = bool(ok[kind] and acceptable)
        rows.append(dict(cell=cell, scenario=records[0]["scenario"], link=records[0]["link"], null=kind,
                         n=n, rejections=int(k), rate=k/n, wilson_lo=float(lo), wilson_hi=float(hi),
                         bias_mean=float(b_mean), bias_lo=float(b_lo), bias_hi=float(b_hi),
                         crit_wilson=bool(lo <= .05), crit_point=bool(k/n <= .075), crit_bias=bool(b_lo <= 0),
                         acceptable=bool(acceptable), backends={str(a): int(b) for a, b in backends.items()}))

print(f"{'cell':5} {'scenario':9} {'link':8} {'null':11} {'n':>3} {'rej':>3} {'rate':>6} {'Wilson 95%':>15} "
      f"{'bias mean':>10} {'bias 95% t':>22} {'W':>2}{'P':>2}{'B':>2} acc")
for r in rows:
    print(f"{r['cell']:5} {r['scenario']:9} {r['link']:8} {r['null']:11} {r['n']:3d} {r['rejections']:3d} "
          f"{r['rate']:6.3f} [{r['wilson_lo']:.3f}, {r['wilson_hi']:.3f}] {r['bias_mean']:10.5f} "
          f"[{r['bias_lo']:+.5f}, {r['bias_hi']:+.5f}] {'y' if r['crit_wilson'] else 'N':>2}"
          f"{'y' if r['crit_point'] else 'N':>2}{'y' if r['crit_bias'] else 'N':>2} {'YES' if r['acceptable'] else 'NO'}")
branch = 1 if ok["registered"] else 2 if ok["conditional"] else 3
print("acceptable everywhere:", ok, "-> branch", branch)
(Path(__file__).with_suffix(".json")).write_text(json.dumps(dict(rows=rows, ok=ok, branch=branch), indent=1))
