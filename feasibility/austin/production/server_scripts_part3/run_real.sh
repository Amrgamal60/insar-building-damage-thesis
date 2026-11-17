#!/bin/bash
# REAL RUN (AUSTIN_PLAN.md §13 step 5): made once, with the code hashed in §15 before it starts. It refuses to start if
# its output directory exists. Reruns only for logged code errors (§13 step 5).
#   1. Test A, primary analysis and decision (run_tests.py testa, conditional null, 999 draws)
#   2. Test B, key secondary (run_tests.py testb, null seed 2034)
#   3. items reported beside the Test A decision and the Test A specificity check (run_report.py testa)
#   4. the Test B specificity check and its direct comparison (run_report.py testb, null seed 2035)
#   5. secondary 8, null (a): run_tests.py testa with the null (a) file, after that file and its quantiles exist
cd ~/AmrGamal || exit 1
PY=~/AmrGamal/env/venv/bin/python
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
O=$W/real_20261112
C="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet --events $D/events/foundation_events.parquet"
RM="--remodel-events $D/remodel/remodel_events.parquet --remodel-episodes $D/remodel/remodel_first_episodes.parquet"
F=$W/fields_20261111_slips/field_v.npz
SA=$W/surrogates_20261111_slips/surrogates_conditional.npy
QA=$W/quantiles_20261111_slips/surrogate_quantiles.npy
CELLS=$W/testb_cells_20261111/testb_cells.npz
if [ -e $O ]; then echo "$O exists: the real run is made once; not started $(date '+%F %T')" >> $W/real_refused.status; exit 1; fi
mkdir -p $O/nulla
st() { echo "$1 $(date '+%F %T')" >> $O/status; }
st "start"
$PY -I code/austin/production/run_tests.py testa $C --mode real --field $F --surrogates $SA --quantiles $QA \
  --out $O --workers 64 > $O/test_a.log 2>&1
ra=$?; st "testa exit=$ra"
$PY -I code/austin/production/run_tests.py testb $C --mode real --cells $CELLS \
  --surrogates $W/testb_surrogates_20261111/testb_v_seed2034.npz --out $O > $O/test_b.log 2>&1
rb=$?; st "testb exit=$rb"
if [ $ra = 0 ]; then
  $PY -I code/austin/production/run_report.py testa $C $RM --mode real --field $F --surrogates $SA --quantiles $QA \
    --primary $O/test_a.json --out $O --workers 64 > $O/report_a.log 2>&1
  st "report a exit=$?"
fi
if [ $rb = 0 ]; then
  $PY -I code/austin/production/run_report.py testb $C $RM --mode real --cells $CELLS \
    --surrogates $W/testb_surrogates_20261111/testb_v_seed2035.npz --primary $O/test_b.json \
    --primary-panel $O/test_b_panel.csv --out $O --workers 64 > $O/report_b.log 2>&1
  st "report b exit=$?"
fi
until grep -q "quantiles exit" $W/nulla.status 2>/dev/null || grep -q "nulla exit=[1-9]" $W/nulla.status 2>/dev/null; do sleep 60; done
if grep -q "quantiles exit=0" $W/nulla.status; then
  $PY -I code/austin/production/run_tests.py testa $C --mode real --field $F \
    --surrogates $W/surrogates_20261112_nulla/surrogates_nulla.npy --quantiles $W/quantiles_20261112_nulla/surrogate_quantiles.npy \
    --out $O/nulla --workers 64 > $O/nulla/test_a.log 2>&1
  st "nulla exit=$?"
else
  st "nulla not run: its surrogate file or quantiles failed"
fi
st "end"
