"""Test B null: draws made in parallel (make_testb_surrogates.py --workers 64) against the same draws made one after
another (--workers 1, the 3-draw trial), compared by raw bytes (NaN-safe), with the neighbour counts.
Usage: .venv/bin/python -I check_testb_parallel.py PARALLEL_NPZ SEQUENTIAL_NPZ OUT_JSON
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

par, seq, out = map(Path, sys.argv[1:4])
P, S = np.load(par, allow_pickle=False), np.load(seq, allow_pickle=False)
n = len(S["fields"])
a, b = np.ascontiguousarray(P["fields"][:n]), np.ascontiguousarray(S["fields"])
same_nan = bool(np.array_equal(np.isnan(a), np.isnan(b)))
diff = np.abs(np.nan_to_num(a) - np.nan_to_num(b))
R = dict(parallel=str(par.name), sequential=str(seq.name), draws_compared=int(n), seeds=[int(P["seed"]), int(S["seed"])],
         cells_equal=bool(np.array_equal(P["cells"], S["cells"])), quarters_equal=bool(np.array_equal(P["quarters"], S["quarters"])),
         bytes_identical=bool(a.tobytes() == b.tobytes()), nan_identical=same_nan, max_abs_diff=float(diff.max()),
         k_parallel=[int(x) for x in P["k"][:n]], k_sequential=[int(x) for x in S["k"]],
         sha256_first_draws=hashlib.sha256(a.tobytes()).hexdigest())
R["pass"] = bool(R["bytes_identical"] and R["k_parallel"] == R["k_sequential"] and R["cells_equal"] and R["quarters_equal"]
                 and R["seeds"][0] == R["seeds"][1])
out.write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps(R, indent=1))
