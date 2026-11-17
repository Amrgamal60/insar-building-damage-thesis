#!/bin/bash
# Download OPERA DISP-S1 frame 12638 (Miami), clipped to the box holding all unsafe-structure cases since 2017
# (NYC plan §17 step 2; same tool and version as NYC: opera-utils 0.25.8 in conda env "opera").
# Needs ~/.netrc for urs.earthdata.nasa.gov. Reruns until every granule is present and readable; broken files are
# deleted and fetched again. Ends by writing MANIFEST.sha256. Usage (from Alex/): bash feasibility/download_miami_opera.sh
set -uo pipefail
PY=~/miniforge3/envs/opera/bin/python
OUT=feasibility/miami/downloads/opera_disp
BBOX="-80.56 25.32 -80.11 25.99"
mkdir -p "$OUT"
for attempt in $(seq 1 60); do
  echo "$(date -u +%FT%TZ) attempt $attempt"
  ~/miniforge3/envs/opera/bin/opera-utils disp-s1-download --frame-id 12638 --bbox $BBOX \
      --product-version 1.0 --num-workers 4 --output-dir "$OUT"
  # Keep only files that open and hold a full displacement layer; anything else is removed and fetched again.
  "$PY" -I - "$OUT" <<'EOF'
import sys
from pathlib import Path
import h5py
bad = 0
for p in sorted(Path(sys.argv[1]).glob("*.nc")):
    try:
        with h5py.File(p, "r") as h:
            d = h["displacement"]
            assert d.ndim == 2 and min(d.shape) > 0
            d[-1, -1]
    except Exception as e:
        print("broken, removed:", p.name, repr(e)[:120], flush=True)
        p.unlink()
        bad += 1
print("checked; broken:", bad, flush=True)
EOF
  n=$(ls "$OUT"/*.nc 2>/dev/null | wc -l)
  want=$("$PY" -I -c "from opera_utils.disp import search; print(len(search(frame_id=12638, product_version='1.0')))")
  echo "$(date -u +%FT%TZ) have $n of $want granules"
  if [ "$n" -ge "$want" ] && [ "$want" -gt 0 ]; then
    (cd "$OUT" && sha256sum *.nc > MANIFEST.sha256)
    echo "$(date -u +%FT%TZ) ALLDONE $n"
    exit 0
  fi
  sleep 120
done
echo "$(date -u +%FT%TZ) gave up after 60 attempts"
exit 1
