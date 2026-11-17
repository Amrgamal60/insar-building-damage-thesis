#!/bin/bash
# Test A conditional-null surrogates (AUSTIN_PLAN.md §10; §14 compute location): corrected primary field, CPU engine, 64 workers.
cd ~/AmrGamal
PY=~/AmrGamal/env/venv/bin/python
D=~/AmrGamal/data/austin_private/checkpoint1
W=~/AmrGamal/work/insar
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet"
mkdir -p $W/surrogates_20261111_slips
$PY -I code/austin/production/make_surrogates.py $A --field $W/fields_20261111_slips/field_v.npz --out $W/surrogates_20261111_slips/surrogates_conditional.npy --backend cpu --workers 64 > $W/surr.log 2>&1
echo "surr exit=$?" > $W/surr.status
