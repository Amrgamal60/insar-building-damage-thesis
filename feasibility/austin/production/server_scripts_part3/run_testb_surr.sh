#!/bin/bash
# Test B null surrogates (AUSTIN_PLAN.md §10 Test B, seed 2034; remodel Test B, seed 2035), queued behind the Test A
# surrogates so that at most 64 worker processes run at once (§14 compute location).
cd ~/AmrGamal
W=~/AmrGamal/work/insar
until [ -f $W/surr.status ]; do sleep 60; done
grep -q "surr exit=0" $W/surr.status || { echo "testb not started: Test A run failed" > $W/testb_surr.status; exit 1; }
mkdir -p $W/testb_surrogates_20261111
for s in 2034 2035; do
  env/venv/bin/python -I code/austin/production/make_testb_surrogates.py $W/testb_cells_20261111/testb_cells.npz \
    $W/testb_surrogates_20261111/testb_v_seed$s.npz --field v --seed $s --workers 64 > $W/testb_surr_$s.log 2>&1
  echo "testb $s exit=$?" >> $W/testb_surr.status
done
