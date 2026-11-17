#!/bin/bash
# Null (a), the NYC variogram null, for Test A secondary 8 (AUSTIN_PLAN.md §12 item 8): 999 surrogates (seed 2027) of
# the whole corrected velocity field on the CPUs (64 workers), then their per-draw window quantiles (48 workers),
# as the conditional null's file. Outcome-blind: reads the field and the checkpoint-1 tables only.
cd ~/AmrGamal || exit 1
PY=~/AmrGamal/env/venv/bin/python
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet"
F=$W/fields_20261111_slips/field_v.npz
O=$W/surrogates_20261112_nulla
mkdir -p $O $W/quantiles_20261112_nulla
echo "nulla start $(date '+%F %T')" >> $W/nulla.status
$PY -I code/austin/production/make_surrogates_nulla.py $A --field $F --out $O/surrogates_nulla.npy --workers 64 > $W/nulla.log 2>&1
rc=$?; echo "nulla exit=$rc $(date '+%F %T')" >> $W/nulla.status
[ $rc = 0 ] || exit 1
$PY -I code/austin/planted_signal/planted_signal.py quantiles $A --field $F \
  --surrogates $O/surrogates_nulla.npy --out $W/quantiles_20261112_nulla/surrogate_quantiles.npy --workers 48 > $W/quantiles_nulla.log 2>&1
echo "quantiles exit=$? $(date '+%F %T')" >> $W/nulla.status
