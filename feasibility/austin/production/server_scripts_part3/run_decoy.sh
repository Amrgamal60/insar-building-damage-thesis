#!/bin/bash
# Decoy run (AUSTIN_PLAN.md §13 step 4): Test A and Test B on the decoy outcome (seed 99), after the quantiles and the
# Test B byte check. Code check only; nothing changes because of it except outright code errors, which are logged.
cd ~/AmrGamal
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
C="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet --events $D/events/foundation_events.parquet"
until grep -q "quantiles" $W/after.status 2>/dev/null; do sleep 60; done
grep -q "quantiles exit=0" $W/after.status && grep -q "bytecheck exit=0" $W/after.status && grep -q "\"pass\": true" $W/testb_parallel_check.json \
  || { echo "decoy not started: quantiles or Test B byte check did not pass" > $W/decoy.status; exit 1; }
env/venv/bin/python -I code/austin/production/run_tests.py testa $C --mode decoy --field $W/fields_20261111_slips/field_v.npz \
  --surrogates $W/surrogates_20261111_slips/surrogates_conditional.npy --quantiles $W/quantiles_20261111_slips/surrogate_quantiles.npy \
  --out $W/decoy_20261111 --workers 64 > $W/decoy_a.log 2>&1
echo "decoy a exit=$?" >> $W/decoy.status
env/venv/bin/python -I code/austin/production/run_tests.py testb $C --mode decoy --cells $W/testb_cells_20261111/testb_cells.npz \
  --surrogates $W/testb_surrogates_20261111/testb_v_seed2034.npz --out $W/decoy_20261111 > $W/decoy_b.log 2>&1
echo "decoy b exit=$?" >> $W/decoy.status
