#!/bin/bash
# Test B null surrogates of the Test B secondaries (AUSTIN_PLAN.md §12 items 15-17; §14 slip-rule sensitivity), with
# the unchanged make_testb_surrogates.py and the Test B null of §10 (seed 2034, 999 draws), each on its own field of
# testb_cells.npz: lags 1, 3, 6, 12 (item 15), the 24-month window (16), amplitude, local relative motion and
# acceleration (17), and the first-run velocity (slip-rule sensitivity). 16 workers, beside the Test A surrogate queue.
# Outcome-blind: reads only the cell field.
cd ~/AmrGamal || exit 1
W=~/AmrGamal/work/insar
O=$W/testb_surr2
mkdir -p $O
for f in v_lag1 v_lag3 v_lag6 v_lag12 v24 amp lrm acc v_run1; do
  [ -e $O/testb_${f}_seed2034.npz ] && continue
  echo "$f start $(date '+%F %T')" >> $O/status
  env/venv/bin/python -I code/austin/production/make_testb_surrogates.py $W/testb_cells_20261111/testb_cells.npz \
    $O/testb_${f}_seed2034.npz --field $f --seed 2034 --workers 16 > $O/${f}.log 2>&1
  echo "$f exit=$? $(date '+%F %T')" >> $O/status
done
echo "all done $(date '+%F %T')" >> $O/status
