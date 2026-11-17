"""House pixel centres for the OPERA environment, which has no parquet reader (AUSTIN_PLAN.md §7, §13 step 3).
Writes prop_id, pix_cx and pix_cy of the eligible houses, in prop_id order, from the checkpoint-1 grid
(eligible_grid_folds.parquet, SHA-256 checked against checkpoint1/frame_grid_folds.json). No name or address.
Usage: .venv/bin/python -I feasibility/austin/production/i00_house_pixels.py GRID_PARQUET OUT_NPZ
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

grid, out = Path(sys.argv[1]), Path(sys.argv[2])
rec = json.loads((Path(__file__).resolve().parents[1] / "checkpoint1" / "frame_grid_folds.json").read_text())
assert hashlib.sha256(grid.read_bytes()).hexdigest() == rec["private_outputs_sha256"]["eligible_grid_folds.parquet"]
g = pd.read_parquet(grid, columns=["prop_id", "pix_cx", "pix_cy"])
assert g.prop_id.is_unique and g.prop_id.is_monotonic_increasing
np.savez(out, prop_id=g.prop_id.to_numpy(str), pix_cx=g.pix_cx.to_numpy(float), pix_cy=g.pix_cy.to_numpy(float))
print(len(g), hashlib.sha256(out.read_bytes()).hexdigest())
