#!/bin/bash
# Null (a), secondary 8: the GPU file was chosen by the rule fixed in AUSTIN_PLAN.md §15 before the GPU run (all 999
# draws complete; every draw held by both files agrees). Same commands as run_nulla.sh's quantiles step and
# run_real.sh's step 5, with the GPU file: per-draw window quantiles (48 workers), then run_tests.py testa (unchanged)
# into real_20261112/nulla/. Its p is the null (a) p (secondary 8); its meets_rule field is never quoted.
cd ~/AmrGamal || exit 1
PY=~/AmrGamal/env/venv/bin/python
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet"
F=$W/fields_20261111_slips/field_v.npz
S=$W/surrogates_20261112_nulla_gpu/surrogates_nulla.npy
Q=$W/quantiles_20261112_nulla_gpu
O=$W/real_20261112
[ -z "$(ls -A $O/nulla 2>/dev/null)" ] || { echo "nulla (GPU file) not started: $O/nulla not empty $(date '+%F %T')" >> $O/status; exit 1; }
mkdir -p $Q $O/nulla
echo "nulla (GPU file) quantiles start $(date '+%F %T')" >> $O/status
$PY -I code/austin/planted_signal/planted_signal.py quantiles $A --field $F --surrogates $S \
  --out $Q/surrogate_quantiles.npy --workers 48 > $W/quantiles_nulla_gpu.log 2>&1
rc=$?; echo "nulla (GPU file) quantiles exit=$rc $(date '+%F %T')" >> $O/status
[ $rc = 0 ] || exit 1
$PY -I code/austin/production/run_tests.py testa $A --events $D/events/foundation_events.parquet --mode real --field $F \
  --surrogates $S --quantiles $Q/surrogate_quantiles.npy --out $O/nulla --workers 64 > $O/nulla/test_a.log 2>&1
echo "nulla exit=$? (GPU file) $(date '+%F %T')" >> $O/status
echo "end $(date '+%F %T')" >> $O/status
