#!/bin/bash
# Secondary 11 of ALEX_RETEST_PLAN.md (frozen 2026-11-18): P3 = the linear fit from 2019-01-01 to the last epoch on
# the same LiCSBAS cumulative displacement (step 16's cum_filt.h5) and mask (step 15's), decomposed as P1.
# Mirrors scripts/15_licsbas_run.sh steps 2-3 for P3 only: LiCSBAS_cum2vel.py -s 20190101, LiCSBAS_flt2geotiff.py,
# LiCSBAS_decomposeLOS.py (np.bool8 shim as in 15). Writes only new P3 files; P1, P2, E and N are not touched.
# Usage: bash feasibility/alexandria_retest/scripts/run_p3.sh > feasibility/alexandria_retest/secondary_real/p3_run.log 2>&1
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LB="$ROOT/tools/LiCSBAS"
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate licsbas
export LICSBAS_PATH="$LB" PATH="$LB/bin:$PATH" PYTHONPATH="$LB/LiCSBAS_lib" MPLBACKEND=Agg
FRAMES=(065D_05935_131108 131A_05957_110910)
P3_START=20190101

for frame in "${FRAMES[@]}"; do
  W="$ROOT/data/licsbas/$frame"
  cd "$W"
  test ! -e velocity/P3.vel.geo.tif || { echo "velocity/P3 exists in $frame; refusing to overwrite"; exit 1; }
  echo "== $frame $(date -Is)"
  LiCSBAS_cum2vel.py -s "$P3_START" -i TS_GEOCml1/cum_filt.h5 --mask TS_GEOCml1/results/mask -o velocity/P3
  LiCSBAS_flt2geotiff.py -i velocity/P3.vel.mskd -p GEOCml1/EQA.dem_par -o velocity/P3.vel.geo.tif
done

D="$ROOT/data/licsbas/decomposed"
cd "$D"
test ! -e P3_UD.geo.tif || { echo "decomposed/P3_UD exists; refusing to overwrite"; exit 1; }
: > P3.files.txt
for frame in "${FRAMES[@]}"; do
  V="../$frame/velocity"
  echo "$V/P3.vel.geo.tif $V/E.geo.tif $V/N.geo.tif" >> P3.files.txt
done
python -c 'import runpy, sys, numpy as np; np.bool8 = np.bool_; sys.argv = sys.argv[1:]; runpy.run_path(sys.argv[0], run_name="__main__")' \
  "$LB/bin/LiCSBAS_decomposeLOS.py" -f P3.files.txt -o P3_
sha256sum "$D/P3_UD.geo.tif" "$D/P3_EW.geo.tif" ../*/velocity/P3.vel.geo.tif
echo "== finished $(date -Is)"
