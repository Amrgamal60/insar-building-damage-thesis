#!/bin/bash
# Real runs of the secondary analyses in numbered order (AUSTIN_PLAN.md §12; §15 "Secondary analyses: how each is
# computed", 2026-11-15). Usage: run_secondaries.sh WORKERS [FIRST_ITEM]
# Per item: wait for its null file(s); a decoy smoke with its own files (3 draws; code check); then the real run with the
# plan's counts. Start and end times go to work/secondary/status_real. A failed smoke or run stops the script.
# After the item's real run, each large Test A surrogate file it alone still needs is deleted (§15 "Surrogate files
# deleted after use"), after its SHA-256 is re-checked against the file's meta. The primary file is kept; amplitude, local
# relative motion and acceleration are kept until secondary 7 has run. Cell (secondary 1) and Test B files are small
# and kept.
WK=${1:?workers}; FIRST=${2:-1_nyc_design}
cd ~/AmrGamal || exit 1
PY="env/venv/bin/python -I"
P=code/austin/production
D=data/austin_private/checkpoint1; SEC=$D/secondary; W=work/insar; S=$W/surr2; FS=$W/fields_20261111_slips
O=work/secondary/real; SM=work/secondary/smoke_pre; ST=work/secondary/status_real
mkdir -p $O $SM
COMMON="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet --events $D/events/foundation_events.parquet"
CELLS=$W/testb_cells_20261111/testb_cells.npz
log() { echo "$(date '+%F %T') $*" >> $ST; }
started=0
go() { [ $started = 1 ] && return 0; [ "$1" = "$FIRST" ] && started=1; [ $started = 1 ]; }
wait_file() { local w=0; while [ ! -e "$1" ]; do [ $w = 0 ] && log "waits for $1"; w=1; sleep 300; done; }
primary() { echo "--field $1=$FS/field_v.npz --surrogates $1=$W/surrogates_20261111_slips/surrogates_conditional.npy --quantiles $1=$W/quantiles_20261111_slips/surrogate_quantiles.npy"; }
own() {  # name [field path]; ready when the quantile file's meta exists (written last by every maker)
  local f=${2:-$FS/field_$1.npz}
  wait_file $S/$1/surrogate_quantiles.npy.json
  echo "--field $1=$f --surrogates $1=$S/$1/surrogates_conditional.npy --quantiles $1=$S/$1/surrogate_quantiles.npy"
}
drop() {  # delete a Test A surrogate file after use, its SHA-256 re-checked against its meta (write_surrogates)
  local d=$S/$1 want got
  want=$($PY -c 'import json, sys; print(json.load(open(sys.argv[1]))["sha256"])' $d/surrogates_conditional.npy.json)
  got=$(sha256sum $d/surrogates_conditional.npy | cut -d" " -f1)
  if [ -n "$want" ] && [ "$want" = "$got" ]; then rm -f $d/surrogates_conditional.npy; log "deleted $1 surrogates (${want:0:16}, hash re-checked)"
  else log "NOT deleted $1 surrogates: hash differs (${want:0:16} vs ${got:0:16})"; fi
}
runA() {  # name args...
  local n=$1; shift
  go $n || return 0
  log "$n smoke start"
  $PY $P/secondary_a.py run --secondary $n --mode decoy $COMMON "$@" --out $SM/$n --workers 3 --draws 3 --boot 2 > $SM/$n.log 2>&1 \
    || { log "$n smoke FAILED"; exit 1; }
  log "$n start"
  $PY $P/secondary_a.py run --secondary $n --mode real $COMMON "$@" --out $O/$n --workers $WK > $O/$n.log 2>&1 \
    || { log "$n FAILED"; exit 1; }
  log "$n end $(sha256sum $O/$n/result.json | cut -c1-16)"
}
runB() {  # name surrogates
  local n=$1 sb=$2
  go $n || return 0
  wait_file $sb.run.json
  log "$n smoke start"
  $PY $P/secondary_b.py run --secondary $n --mode decoy $COMMON --cells $CELLS --surrogates $sb --out $SM/$n --workers 3 --draws 3 > $SM/$n.log 2>&1 \
    || { log "$n smoke FAILED"; exit 1; }
  log "$n start"
  $PY $P/secondary_b.py run --secondary $n --mode real $COMMON --cells $CELLS --surrogates $sb --out $O/$n --workers $WK > $O/$n.log 2>&1 \
    || { log "$n FAILED"; exit 1; }
  log "$n end $(sha256sum $O/$n/result.json | cut -c1-16)"
}
log "run_secondaries start (workers $WK, from $FIRST)"
# 1. NYC design
if go 1_nyc_design; then
  C1="$COMMON --cells $CELLS --nyc-cells $W/windows_20261111_slips/nyc_cells_L24.npz --surrogates $W/sec1_cells/surrogates_cells.npy --quantiles $W/sec1_cells/quantiles_cells.npy"
  wait_file $W/sec1_cells/surrogates_cells.npy.run.json
  log "1_nyc_design smoke start"
  $PY $P/secondary_cells.py --mode decoy $C1 --out $SM/1_nyc_design --workers 3 --draws 3 --boot 2 > $SM/1_nyc_design.log 2>&1 \
    || { log "1_nyc_design smoke FAILED"; exit 1; }
  log "1_nyc_design start"
  $PY $P/secondary_cells.py --mode real $C1 --out $O/1_nyc_design --workers $WK > $O/1_nyc_design.log 2>&1 \
    || { log "1_nyc_design FAILED"; exit 1; }
  log "1_nyc_design end $(sha256sum $O/1_nyc_design/result.json | cut -c1-16)"
fi
runA 2_local_controls $(primary v)
runA 3_window_12 $(own v12) && go 3_window_12 && [ -e $O/3_window_12/result.json ] && drop v12
runA 3_window_36 $(own v36) && go 3_window_36 && [ -e $O/3_window_36/result.json ] && drop v36
runA 4_random_forest $(primary v)
runA 5_baseline_2 $(primary v) --other-bp $SEC/other_bp_dates.parquet
runA 5_baseline_1_no_income $(primary v)
runA 6_amplitude $(own amp)
runA 6_local_relative_motion $(own lrm)
runA 6_acceleration $(own acc)
runA 7_boosted_trees $(primary v) $(own amp) $(own lrm) $(own acc) && go 7_boosted_trees && [ -e $O/7_boosted_trees/result.json ] && { drop amp; drop lrm; drop acc; }
for k in 1 3 6 12; do
  runA 9_lag_$k $(own v_lag$k) && go 9_lag_$k && [ -e $O/9_lag_$k/result.json ] && drop v_lag$k
done
runA 10_issue_date $(primary v) --issue-events $SEC/foundation_events_issue.parquet --issue-episodes $SEC/foundation_first_episodes_issue.parquet
for k in 0 1 2 3 4 5 6 7 8 9; do runA 11_fold_seed_$k $(primary v); done
runA 12_availability $(own avail) --mask-field $FS/field_v.npz && go 12_availability && [ -e $O/12_availability/result.json ] && drop avail
runA 13_no_construction_mask $(own v_nomask) && go 13_no_construction_mask && [ -e $O/13_no_construction_mask/result.json ] && drop v_nomask
for f in 1 3 6 12; do runB 15_lag_$f $W/testb_surr2/testb_v_lag${f}_seed2034.npz; done
runB 16_window_24 $W/testb_surr2/testb_v24_seed2034.npz
runB 17_amplitude $W/testb_surr2/testb_amp_seed2034.npz
runB 17_local_relative_motion $W/testb_surr2/testb_lrm_seed2034.npz
runB 17_acceleration $W/testb_surr2/testb_acc_seed2034.npz
runB 18_negative_binomial $W/testb_surrogates_20261111/testb_v_seed2034.npz
runB 19_monthly $W/testb_surr2/testb_v_monthly_seed2034.npz
runA D1_demolition $(primary v)
runA D2_composite $(primary v)
runA slip_first_run $(own v_firstrun $W/fields_20261111/field_v.npz) && go slip_first_run && [ -e $O/slip_first_run/result.json ] && drop v_firstrun
runB slip_first_run_b $W/testb_surr2/testb_v_run1_seed2034.npz
log "run_secondaries end"
