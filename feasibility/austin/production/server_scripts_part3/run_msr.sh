#!/bin/bash
# MSR null (secondary 8, AUSTIN_PLAN.md §12 item 8 "MSR (999)"): the 999 MSR fields (seed 2026) of the Test A null
# field (msr_null.py make, 32 threads; it stops if the threshold or the eigen self-check fails), their per-draw window
# quantiles (48 workers), then run_tests.py testa, unchanged, with that file into real_20261112/msr/. The MSR p is
# reported as secondary 8 only; the "meets_rule" field of that test_a.json is never quoted.
cd ~/AmrGamal || exit 1
PY=~/AmrGamal/env/venv/bin/python
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet"
F=$W/fields_20261111_slips/field_v.npz
S=$W/surrogates_20261112_msr
Q=$W/quantiles_20261112_msr
O=$W/real_20261112/msr
if [ -e $O ]; then echo "$O exists; not started $(date '+%F %T')" >> $W/msr.status; exit 1; fi
mkdir -p $S $Q $O
echo "msr start $(date '+%F %T')" >> $W/msr.status
$PY -I code/austin/production/msr_null.py make $A --field $F --out $S/surrogates_msr.npy --threads 32 > $W/msr.log 2>&1
rc=$?; echo "msr exit=$rc $(date '+%F %T')" >> $W/msr.status
[ $rc = 0 ] || exit 1
$PY -I code/austin/planted_signal/planted_signal.py quantiles $A --field $F \
  --surrogates $S/surrogates_msr.npy --out $Q/surrogate_quantiles.npy --workers 48 > $W/quantiles_msr.log 2>&1
rc=$?; echo "quantiles exit=$rc $(date '+%F %T')" >> $W/msr.status
[ $rc = 0 ] || exit 1
$PY -I code/austin/production/run_tests.py testa $A --events $D/events/foundation_events.parquet --mode real --field $F \
  --surrogates $S/surrogates_msr.npy --quantiles $Q/surrogate_quantiles.npy --out $O --workers 64 > $O/test_a.log 2>&1
echo "testa exit=$? $(date '+%F %T')" >> $W/msr.status
