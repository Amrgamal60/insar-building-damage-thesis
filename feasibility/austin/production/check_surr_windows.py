"""Check of make_surrogates_windows.py (AUSTIN_PLAN.md §15, 2026-11-15) on the primary field. Outcome-blind.

  blank    the primary velocity field with its first B windows set to NaN (as the 36-month field and the lag-12
           field have 12 empty leading windows), written with testa_core.save_field.
  compare  the wrapper's first draws on the blanked field against the same draws of the primary surrogate file
           and of its quantile file:
             - the B empty windows must be NaN in every draw and in the quantiles;
             - in windows B..87 every draw whose neighbour count k equals the primary draw's k must be identical
               (same float32 values, same NaN), and so must its quantiles;
             - pass: all of this holds, and at least one draw has an unchanged k.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "planted_signal")]
import testa_core as C  # noqa: E402


def cmd_blank(a):
    h = C.load_houses(a.features, a.grid, a.episodes, a.censoring)
    geo = C.Geometry(h)
    v = C.load_field(a.field, geo)
    v[:a.blank] = np.nan
    C.save_field(a.out, v, geo, meta=dict(source=str(a.field), source_sha256=C.sha256(a.field), blanked_windows=a.blank,
                                          purpose="check of make_surrogates_windows.py"))
    print(a.out, C.sha256(a.out))


def cmd_compare(a):
    B = a.blank
    Sn, Sp = np.load(a.new, mmap_mode="r"), np.load(a.primary, mmap_mode="r")
    kn = json.loads(Path(str(a.new) + ".json").read_text())["chosen_k"]
    kp = json.loads(Path(str(a.primary) + ".json").read_text())["chosen_k"]
    qn, qp = np.load(a.new_quantiles), np.load(a.primary_quantiles)
    rows, ok = [], True
    for d in range(Sn.shape[0]):
        x, y = np.asarray(Sn[d]), np.asarray(Sp[d])
        lead_nan = bool(np.isnan(x[:B]).all() and np.isnan(qn[d][:, :B]).all())
        same_nan = bool(np.array_equal(np.isnan(x[B:]), np.isnan(y[B:])))
        f = np.isfinite(x[B:]) & np.isfinite(y[B:])
        diff = np.abs(x[B:][f].astype(np.float64) - y[B:][f].astype(np.float64))
        identical = bool(same_nan and np.array_equal(x[B:][f], y[B:][f]))
        q_identical = bool(np.array_equal(qn[d][:, B:], qp[d][:, B:]))
        same_k = int(kn[d]) == int(kp[d])
        rows.append(dict(draw=d, k_new=int(kn[d]), k_primary=int(kp[d]), leading_windows_nan=lead_nan,
                         same_missing=same_nan, identical=identical, quantiles_identical=q_identical,
                         values_differing=int((diff > 0).sum()), max_abs_diff=float(diff.max()) if diff.size else 0.0))
        ok &= lead_nan and (not same_k or (identical and q_identical))
    ok &= any(r["k_new"] == r["k_primary"] for r in rows)
    out = dict(check="make_surrogates_windows.py on the primary field with its first windows blanked",
               blanked_windows=B, draws=rows, pass_=bool(ok),
               files=dict(new=C.sha256(a.new), primary_meta_sha256=json.loads(Path(str(a.primary) + ".json").read_text())["sha256"]))
    Path(a.out).write_text(json.dumps(out, indent=1).replace('"pass_"', '"pass"') + "\n")
    print(json.dumps(out, indent=1).replace('"pass_"', '"pass"'))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("blank")
    for k in ("features", "grid", "episodes", "censoring", "field", "out"):
        s.add_argument(f"--{k}", type=Path, required=True)
    s.add_argument("--blank", type=int, default=12)
    s = sub.add_parser("compare")
    for k in ("new", "primary", "new_quantiles", "primary_quantiles", "out"):
        s.add_argument(f"--{k.replace('_', '-')}", dest=k, type=Path, required=True)
    s.add_argument("--blank", type=int, default=12)
    a = p.parse_args()
    {"blank": cmd_blank, "compare": cmd_compare}[a.command](a)


if __name__ == "__main__":
    main()
