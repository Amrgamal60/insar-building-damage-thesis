#!/bin/bash
# Variogram checks (AUSTIN_PLAN.md §10), queued behind the Test A and Test B surrogates (at most 64 workers at once).
cd ~/AmrGamal
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
until grep -q "testb 2035 exit" $W/testb_surr.status 2>/dev/null || grep -q "not started" $W/testb_surr.status 2>/dev/null; do sleep 60; done
grep -q "surr exit=0" $W/surr.status || { echo "vario not started" > $W/vario.status; exit 1; }
env/venv/bin/python -I code/austin/production/check_variogram.py a $D/features/features_2018.parquet $D/grid_folds/eligible_grid_folds.parquet \
  $W/fields_20261111_slips/field_v.npz $W/surrogates_20261111_slips/surrogates_conditional.npy $W/variogram_20261111 --workers 48 > $W/vario_a.log 2>&1
echo "vario a exit=$?" >> $W/vario.status
grep -q "testb 2034 exit=0" $W/testb_surr.status && env/venv/bin/python -I code/austin/production/check_variogram.py b \
  $W/testb_cells_20261111/testb_cells.npz $W/testb_surrogates_20261111/testb_v_seed2034.npz $W/variogram_20261111 > $W/vario_b.log 2>&1
echo "vario b exit=$?" >> $W/vario.status
