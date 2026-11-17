"""Does the hashed Test A core (planted_signal/testa_core.py) and planted-signal driver give the project PC's
results on another machine, from the same input files? Synthetic velocity only; no InSAR file.

The planted-signal check (planted_signal/check, run on the PC on 2026-11-10) left its inputs and records in a
work directory: the synthetic field, its 20 surrogate draws, the event dates, the surrogate quantiles and one
record per dataset (cells 1-6, datasets 0-1). This script copies nothing new: on this machine it reruns
planted_signal.py's event-dates, quantiles and run commands on those same files, then compares every output
with the PC's.

 1. Event dates: byte-identical file and identical drop counts.
 2. Surrogate quantiles: identical, or the largest difference.
 3. Records: integer fields, p-values and the §11 rule identical; floating-point fields equal or the largest
    difference (timing and host fields excluded).
 4. Kernels: hashes of a few numpy and scipy results that the synthetic field uses, to show where two machines'
    floating point differs (written out for comparison between machines; no assertion).
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
from scipy.ndimage import gaussian_filter  # noqa: E402

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "planted_signal")]
import testa_core as C  # noqa: E402
import planted_signal as PS  # noqa: E402

TIMING = {"null_seconds", "elapsed_seconds"}

p = argparse.ArgumentParser()
for k in ("features", "grid", "episodes", "censoring", "events", "reference", "work", "out"):
    p.add_argument(f"--{k}", type=Path, required=True)
p.add_argument("--workers", type=int, default=12)
a = p.parse_args()
ref, W = a.reference, a.work
W.mkdir(parents=True, exist_ok=True)
R = dict(host=platform.node(), python=platform.python_version(), numpy=np.__version__, sources=PS.source_hashes(),
         check_sha256=C.sha256(Path(__file__)), reference_record_count=len(list((ref / "run" / "records").glob("*.json"))))
field, sur = ref / "synthetic_field.npz", ref / "surrogates_conditional.npy"
common = ["--features", str(a.features), "--grid", str(a.grid), "--episodes", str(a.episodes),
          "--censoring", str(a.censoring), "--field", str(field)]

# 1. event dates
PS.main(["event-dates"] + common + ["--events", str(a.events), "--out", str(W / "event_dates.csv")])
mine, theirs = json.loads((W / "event_dates.csv.json").read_text()), json.loads((ref / "event_dates.csv.json").read_text())
R["1_event_dates"] = dict(identical=C.sha256(W / "event_dates.csv") == C.sha256(ref / "event_dates.csv"),
                          cases=mine["cases"], dropped_identical=mine["dropped"] == theirs["dropped"])

# 2. surrogate quantiles
PS.main(["quantiles"] + common + ["--surrogates", str(sur), "--out", str(W / "surrogate_quantiles.npy"), "--workers", str(a.workers)])
q1, q0 = np.load(W / "surrogate_quantiles.npy"), np.load(ref / "surrogate_quantiles.npy")
R["2_quantiles"] = dict(identical=bool(np.array_equal(q1, q0)), max_abs_diff=float(np.abs(q1 - q0).max()))

# 3. records (the server's own dates and quantiles; they are compared above)
PS.main(["run"] + common + ["--surrogates", str(sur), "--quantiles", str(W / "surrogate_quantiles.npy"),
                            "--event-dates", str(W / "event_dates.csv"), "--workers", str(a.workers), "--datasets", "2",
                            "--projection-hours", "72", "--out", str(W / "run")])


def flat(d, prefix=""):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from flat(v, f"{prefix}{k}.")
        else:
            yield f"{prefix}{k}", v


per = {}
for f in sorted((ref / "run" / "records").glob("*.json")):
    r0, r1 = (dict(flat(json.loads(x.read_text()))) for x in (f, W / "run" / "records" / f.name))
    exact, maxdiff, differ = True, 0.0, []
    for k, v0 in r0.items():
        if k in TIMING or k.startswith("fingerprints.event_dates") or k.startswith("fingerprints.quantiles"):
            continue
        v1 = r1[k]
        if isinstance(v0, list) and v0 and isinstance(v0[0], float):
            d = float(np.max(np.abs(np.asarray(v0) - np.asarray(v1))))
        elif isinstance(v0, float):
            d = abs(v0 - v1)
        else:
            if v0 != v1:
                differ.append(k)
            continue
        if d > 0:
            exact = False
            maxdiff = max(maxdiff, d)
    per[f.stem] = dict(floats_identical=exact, max_abs_float_diff=maxdiff, other_fields_differing=differ,
                       p_identical=r0["p"] == r1["p"], rule_identical=r0["meets_rule"] == r1["meets_rule"])
R["3_records"] = per
R["3_all_p_and_rule_identical"] = all(v["p_identical"] and v["rule_identical"] for v in per.values())
R["3_no_other_field_differs"] = all(not v["other_fields_differing"] for v in per.values())
R["3_max_abs_float_diff"] = max(v["max_abs_float_diff"] for v in per.values())


# 4. kernels behind the synthetic field
def h(x):
    return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()[:16]


rng = np.random.default_rng(20261111)
x = rng.standard_normal((1500, 1500))
g = gaussian_filter(x, 16)
R["4_kernels"] = dict(standard_normal=h(x), gaussian_filter=h(g), mean=repr(float(g.mean())), std=repr(float(g.std())),
                      sqrt=h(np.sqrt(np.abs(x))), exp=h(np.exp(x)), sum_axis0=h(x.sum(0)))
a.out.parent.mkdir(parents=True, exist_ok=True)
a.out.write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps({k: v for k, v in R.items() if k != "3_records"}, indent=1))
