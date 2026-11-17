#!/bin/bash
# Check of make_surrogates_windows.py (AUSTIN_PLAN.md §15, 2026-11-15) before it makes any secondary file: the primary
# velocity field with its first 12 windows blanked, 3 draws (CPU engine, 3 workers) and their quantiles, compared with
# draws 0-2 of the primary surrogate and quantile files (check_surr_windows.py). Outcome-blind.
cd ~/AmrGamal || exit 1
PY=~/AmrGamal/env/venv/bin/python
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet"
P=code/austin/production
O=$W/surr2_check
mkdir -p $O
echo "start $(date '+%F %T')" >> $O/status
$PY -I $P/check_surr_windows.py blank $A --field $W/fields_20261111_slips/field_v.npz --out $O/field_v_blank12.npz --blank 12 > $O/blank.log 2>&1 || { echo "blank failed" >> $O/status; exit 1; }
$PY -I $P/make_surrogates_windows.py make $A --field $O/field_v_blank12.npz --out $O/surr3.npy --backend cpu --workers 3 --draws 3 > $O/make.log 2>&1 || { echo "make failed $(date '+%F %T')" >> $O/status; exit 1; }
$PY -I $P/make_surrogates_windows.py quantiles $A --field $O/field_v_blank12.npz --surrogates $O/surr3.npy --out $O/q3.npy --workers 3 > $O/q.log 2>&1 || { echo "quantiles failed" >> $O/status; exit 1; }
$PY -I $P/check_surr_windows.py compare --new $O/surr3.npy --primary $W/surrogates_20261111_slips/surrogates_conditional.npy \
  --new-quantiles $O/q3.npy --primary-quantiles $W/quantiles_20261111_slips/surrogate_quantiles.npy --out $O/surr_windows_check.json --blank 12 > $O/compare.log 2>&1
echo "compare exit=$? $(date '+%F %T')" >> $O/status
