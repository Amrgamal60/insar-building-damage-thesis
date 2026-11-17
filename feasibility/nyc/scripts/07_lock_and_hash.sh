#!/bin/bash
# Close checkpoint 2 (NYC_REPLICATION_PLAN.md §7 "Software", §13 step 2): write the lock files for both Python
# environments and the machine, then hash the checkpoint-2 outputs, the PLUTO archive manifest and the lock files into
# out/checkpoint2/MANIFEST_PART2.sha256. Run after 04, 05 and 06. Usage (from feasibility/nyc): bash scripts/07_lock_and_hash.sh
set -euo pipefail
O=out/checkpoint2
VENV=../../.venv/bin/python; OPERA=~/miniforge3/envs/opera
{ echo "# Alex/.venv (geometry, features, models; CuPy for the variogram null on the GPU)"; $VENV -V
  uv pip freeze --python $VENV; } > $O/LOCK_venv.txt
{ echo "# conda env 'opera' (OPERA DISP-S1 reading and re-referencing; opera-utils 0.25.8)"; $OPERA/bin/python -V
  ~/miniforge3/bin/conda list -p $OPERA --explicit --md5 | grep -v '^#'; echo "# pip"; $OPERA/bin/python -m pip freeze; } > $O/LOCK_opera.txt
{ uname -srm; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
  /usr/local/cuda/bin/nvcc --version | tail -1; nproc; } > $O/LOCK_machine.txt
sha256sum scripts/05_download_pluto.sh scripts/06_features.py scripts/07_lock_and_hash.sh \
  raw/pluto_archive/MANIFEST.sha256 $O/pluto_releases.csv $O/event_pluto.csv \
  $O/features_250m.csv $O/features_200m.csv $O/folds_250m.csv $O/folds_200m.csv \
  $O/pluto_cells_250m.csv $O/pluto_cells_200m.csv $O/event_sample_250m.csv $O/event_sample_200m.csv \
  $O/LOCK_venv.txt $O/LOCK_opera.txt $O/LOCK_machine.txt $O/MANIFEST.sha256 > $O/MANIFEST_PART2.sha256
sha256sum $O/MANIFEST_PART2.sha256
