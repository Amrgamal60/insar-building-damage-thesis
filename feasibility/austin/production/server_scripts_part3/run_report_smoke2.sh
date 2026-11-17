#!/bin/bash
# Second smoke test (after the literal remodel Test B exposure, user 2026-11-12) of run_report.py in DECOY mode (code check only; numbers mean nothing): Test A report with 20 null draws,
# 40 bootstrap resamples and 10 permutations; Test B report with 5 null draws and 40 resamples. Checked against the
# decoy run's test_a.json, test_b.json and test_b_panel.csv. No real remodel event's house is read in decoy mode.
cd ~/AmrGamal || exit 1
PY=~/AmrGamal/env/venv/bin/python
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet --events $D/events/foundation_events.parquet --remodel-events $D/remodel/remodel_events.parquet --remodel-episodes $D/remodel/remodel_first_episodes.parquet"
O=$W/report_smoke2_20261112
mkdir -p $O
$PY -I code/austin/production/run_report.py testa $A --mode decoy --field $W/fields_20261111_slips/field_v.npz \
  --surrogates $W/surrogates_20261111_slips/surrogates_conditional.npy --quantiles $W/quantiles_20261111_slips/surrogate_quantiles.npy \
  --primary $W/decoy_20261111/test_a.json --out $O --workers 48 --draws 20 --boot 40 --perm 10 > $W/report_smoke2_a.log 2>&1
echo "smoke a exit=$? $(date '+%F %T')" >> $W/report_smoke2.status
$PY -I code/austin/production/run_report.py testb $A --mode decoy --cells $W/testb_cells_20261111/testb_cells.npz \
  --surrogates $W/testb_surrogates_20261111/testb_v_seed2035.npz --primary $W/decoy_20261111/test_b.json \
  --primary-panel $W/decoy_20261111/test_b_panel.csv --out $O --workers 48 --draws 5 --boot 40 > $W/report_smoke2_b.log 2>&1
echo "smoke b exit=$? $(date '+%F %T')" >> $W/report_smoke2.status
