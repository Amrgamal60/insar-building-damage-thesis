#!/bin/bash
# Secondary 20, the temporal deep model (AUSTIN_PLAN.md §12 item 20; §15 "Item 20 (deep model): how it is run").
# Usage: run_deep.sh WORKERS. Starts only after run_secondaries.sh has logged "run_secondaries end" (the numbered
# order: 1-19, D1-D2, slip-rule sensitivity, then 20). Then: a decoy smoke on the GPU with the registered generator
# (2 draws over all 254 acquisition dates, 2 resamples; a code and memory check), then the real run with the plan's
# counts (99 draws, 2,000 resamples). Start and end times go to work/secondary/status_real. A failure stops the script;
# a GPU memory failure is handled by the §12 item 20 memory rule as recorded in §15.
WK=${1:?workers}
cd ~/AmrGamal || exit 1
PY="env/gpu/bin/python -I"
P=code/austin/production
D=data/austin_private/checkpoint1; W=work/insar
O=work/secondary/real; SM=work/secondary/smoke_pre; ST=work/secondary/status_real
mkdir -p $O $SM
COMMON="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet --events $D/events/foundation_events.parquet"
DEEP="--field $W/fields_20261111_slips/field_v.npz --house-series $W/windows_20261111_slips/house_series.npz"
log() { echo "$(date '+%F %T') $*" >> $ST; }
# only run_secondaries.sh's own last line counts: "<date> <time> run_secondaries end", nothing after it
w=0
until grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} run_secondaries end$' $ST 2>/dev/null; do
  [ $w = 0 ] && echo "$(date '+%F %T') 20_deep_model waiting (starts after the secondaries' last line)" >> $ST; w=1; sleep 300
done
n=20_deep_model
log "$n smoke start (GPU generator, 2 draws)"
$PY $P/secondary_deep.py --mode decoy $COMMON $DEEP --primary $W/decoy_20261111/test_a.json --out $SM/$n \
  --workers 2 --draws 2 --boot 2 --null gpu > $SM/$n.log 2>&1 || { log "$n smoke FAILED"; exit 1; }
log "$n start"
$PY $P/secondary_deep.py --mode real $COMMON $DEEP --primary $W/real_20261112/test_a.json --out $O/$n \
  --workers $WK > $O/$n.log 2>&1 || { log "$n FAILED"; exit 1; }
log "$n end $(sha256sum $O/$n/result.json | cut -c1-16)"
