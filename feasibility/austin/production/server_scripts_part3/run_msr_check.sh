#!/bin/bash
# MSR null (secondary 8): code check against NYC's dense code on 1,500 null pixels, then stage timing on subsets of
# 10,000, 20,000 and 30,000 null pixels (32 threads), projected to the full field. Outcome-blind; reads the field only.
cd ~/AmrGamal || exit 1
PY=~/AmrGamal/env/venv/bin/python
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet --field $W/fields_20261111_slips/field_v.npz"
O=$W/msr_timing_20261112
mkdir -p $O
echo "start $(date '+%F %T')" >> $O/status
$PY -I code/austin/production/msr_null.py check $A --n 1500 --threads 8 --out $O/msr_check.json > $O/check.log 2>&1
echo "check exit=$? $(date '+%F %T')" >> $O/status
$PY -I code/austin/production/msr_null.py timing $A --sizes 10000 20000 30000 --threads 32 --out $O/msr_timing.json > $O/timing.log 2>&1
echo "timing exit=$? $(date '+%F %T')" >> $O/status
