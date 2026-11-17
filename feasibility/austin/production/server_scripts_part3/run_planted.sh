#!/bin/bash
# Planted-signal check of Test A (AUSTIN_PLAN.md §14 entry of 2026-11-10; server per §15 "Where the planted-signal
# check runs"): dates of the usable real events, then cells 1-6 x datasets 0-99 (resume-safe records; first-round
# projection with the 72 h fallback), then the summary. Re-running this script resumes: the dates file is kept.
cd ~/AmrGamal || exit 1
PY=~/AmrGamal/env/venv/bin/python
PS=code/austin/planted_signal/planted_signal.py
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
O=$W/planted_20261111
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet --field $W/fields_20261111_slips/field_v.npz"
mkdir -p $O
if [ ! -f $O/event_dates.csv.json ]; then
  $PY -I $PS event-dates $A --events $D/events/foundation_events.parquet --out $O/event_dates.csv > $W/planted_dates.log 2>&1
  rc=$?; echo "dates exit=$rc $(date '+%F %T')" >> $W/planted.status
  [ $rc = 0 ] || exit 1
fi
$PY -I $PS run $A --surrogates $W/surrogates_20261111_slips/surrogates_conditional.npy \
  --quantiles $W/quantiles_20261111_slips/surrogate_quantiles.npy --event-dates $O/event_dates.csv --out $O --workers 64 >> $W/planted_run.log 2>&1
rc=$?; echo "run exit=$rc $(date '+%F %T')" >> $W/planted.status
[ $rc = 0 ] || exit 1
$PY -I $PS summarise --out $O >> $W/planted_run.log 2>&1
echo "summarise exit=$? $(date '+%F %T')" >> $W/planted.status
