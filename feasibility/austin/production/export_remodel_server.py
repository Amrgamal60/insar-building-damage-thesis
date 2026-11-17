"""Name-free copies of the remodel negative-control tables for the server (AUSTIN_PLAN.md §15, "Items reported beside
the decision", remodel world): property ID and first-permit date only.

Inputs (private, checkpoint 1, c1_06_remodel_controls.py; hash-checked against checkpoint1/remodel_controls_2018.json):
  remodel_control_events_amended.parquet   1,491 sampled remodel control events
  remodel_first_episodes_amended.parquet   9,235 houses with a matched remodel permit from 1980 (any status)
Outputs (OUT, private): remodel_events.parquet and remodel_first_episodes.parquet with columns prop_id, t_first;
a record of hashes (RECORD, JSON). No permit number, work class, description or other field is written.
Usage: python -I export_remodel_server.py PRIVATE_DIR OUT RECORD
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


src, out, record = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
want = json.loads((HERE.parent / "checkpoint1" / "remodel_controls_2018.json").read_text())["private_outputs_sha256"]
out.mkdir(parents=True, exist_ok=False)
R = dict(inputs={}, outputs={})
for name, new, n in (("remodel_control_events_amended.parquet", "remodel_events.parquet", 1491),
                     ("remodel_first_episodes_amended.parquet", "remodel_first_episodes.parquet", 9235)):
    assert sha(src / name) == want[name], name
    d = pd.read_parquet(src / name, columns=["prop_id", "t_first"])
    assert len(d) == n and d.prop_id.is_unique and d.prop_id.notna().all() and d.t_first.notna().all()
    d.to_parquet(out / new, index=False)
    R["inputs"][name] = want[name]
    R["outputs"][new] = dict(sha256=sha(out / new), rows=len(d), columns=list(d.columns),
                             t_first_min=str(d.t_first.min()), t_first_max=str(d.t_first.max()))
record.write_text(json.dumps(R, indent=1) + "\n")
print(json.dumps(R, indent=1))
