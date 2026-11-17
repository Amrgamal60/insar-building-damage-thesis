#!/bin/bash
# Run LiCSBAS on the two clipped LiCSAR frames and derive the velocities of data/pilot/LICSAR_TEST_PLAN.md.
#  1. Per frame: batch_LiCSBAS.sh as shipped (tools/LiCSBAS), steps 02 and 11-16. Only the start step and the input and
#     output folders are changed; the diff is printed first.
#  2. Per frame: P1 (first epoch to 2016-12-31) and P2 (full period) velocity, the linear fit to step 16's cum_filt.h5
#     masked with step 15's mask (LiCSBAS_cum2vel.py), written as GeoTIFF with the E and N LOS unit vectors.
#  3. Vertical (UD) and east-west (EW) velocity from the two frames, for P1 and P2 (LiCSBAS_decomposeLOS.py, run with
#     np.bool8 set to np.bool_ because NumPy 2 removed it).
# Outputs: data/licsbas/<frame>/ (GEOCml1, TS_GEOCml1, log, velocity/) and data/licsbas/decomposed/.
# Usage: bash scripts/15_licsbas_run.sh [start_step [frame ...]] > data/licsbas/run.log 2>&1
#   Runs in the conda env licsbas, not base. Default: step 02 for both frames. To resume an interrupted run, give the
#   LiCSBAS step to restart from and the frame(s), e.g. `13 131A_05957_110910`; the decomposition always uses both frames.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LB="$ROOT/tools/LiCSBAS"
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate licsbas
export LICSBAS_PATH="$LB" PATH="$LB/bin:$PATH" PYTHONPATH="$LB/LiCSBAS_lib" MPLBACKEND=Agg
FRAMES=(065D_05935_131108 131A_05957_110910)
P1_END=20161231
START="${1:-02}"
if [ $# -gt 1 ]; then RUN=("${@:2}"); else RUN=("${FRAMES[@]}"); fi

for frame in "${RUN[@]}"; do
  W="$ROOT/data/licsbas/$frame"
  mkdir -p "$W/velocity"
  cd "$W"
  sed -e "s/^start_step=\"01\"/start_step=\"$START\"/" \
      -e "s|^p02_GEOCdir=\"\"|p02_GEOCdir=\"../../raw/insar_licsar/$frame/GEOC\"|" \
      -e 's|^p02_GEOCmldir=""|p02_GEOCmldir="GEOCml1"|' "$LB/batch_LiCSBAS.sh" > batch_LiCSBAS.sh
  chmod +x batch_LiCSBAS.sh
  echo "== $frame $(date -Is): changes to the shipped batch_LiCSBAS.sh"
  diff "$LB/batch_LiCSBAS.sh" batch_LiCSBAS.sh || true
  ./batch_LiCSBAS.sh
  for p in P1 P2; do
    end=()
    if [ "$p" = P1 ]; then end=(-e "$P1_END"); fi
    LiCSBAS_cum2vel.py "${end[@]}" -i TS_GEOCml1/cum_filt.h5 --mask TS_GEOCml1/results/mask -o "velocity/$p"
    LiCSBAS_flt2geotiff.py -i "velocity/$p.vel.mskd" -p GEOCml1/EQA.dem_par -o "velocity/$p.vel.geo.tif"
  done
  for c in E N; do
    LiCSBAS_flt2geotiff.py -i "GEOCml1/$c.geo" -p GEOCml1/EQA.dem_par -o "velocity/$c.geo.tif"
  done
done

D="$ROOT/data/licsbas/decomposed"
mkdir -p "$D"
cd "$D"
for p in P1 P2; do
  : > "$p.files.txt"
  for frame in "${FRAMES[@]}"; do
    V="../$frame/velocity"
    echo "$V/$p.vel.geo.tif $V/E.geo.tif $V/N.geo.tif" >> "$p.files.txt"
  done
  python -c 'import runpy, sys, numpy as np; np.bool8 = np.bool_; sys.argv = sys.argv[1:]; runpy.run_path(sys.argv[0], run_name="__main__")' \
    "$LB/bin/LiCSBAS_decomposeLOS.py" -f "$p.files.txt" -o "${p}_"
done
echo "== finished $(date -Is)"
