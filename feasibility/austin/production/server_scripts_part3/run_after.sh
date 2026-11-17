#!/bin/bash
# After the queued runs: (1) byte check of the parallel Test B null against the 3-draw sequential trial;
# (2) per-draw window quantiles of the Test A surrogates (planted_signal.py quantiles), after the variogram checks.
cd ~/AmrGamal
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet"
until grep -q "testb 2034 exit" $W/testb_surr.status 2>/dev/null || grep -q "not started" $W/testb_surr.status 2>/dev/null; do sleep 60; done
if grep -q "testb 2034 exit=0" $W/testb_surr.status; then
  env/venv/bin/python -I code/austin/production/check_testb_parallel.py $W/testb_surrogates_20261111/testb_v_seed2034.npz $W/testb_smoke/s3.npz $W/testb_parallel_check.json > $W/testb_parallel_check.log 2>&1
  echo "bytecheck exit=$?" >> $W/after.status
fi
until grep -q "vario b exit" $W/vario.status 2>/dev/null || grep -q "not started" $W/vario.status 2>/dev/null; do sleep 60; done
grep -q "surr exit=0" $W/surr.status || { echo "quantiles not started" >> $W/after.status; exit 1; }
mkdir -p $W/quantiles_20261111_slips
env/venv/bin/python -I code/austin/planted_signal/planted_signal.py quantiles $A --field $W/fields_20261111_slips/field_v.npz \
  --surrogates $W/surrogates_20261111_slips/surrogates_conditional.npy --out $W/quantiles_20261111_slips/surrogate_quantiles.npy --workers 48 > $W/quantiles.log 2>&1
echo "quantiles exit=$?" >> $W/after.status
