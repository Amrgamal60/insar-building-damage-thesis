#!/bin/bash
# Decoy smoke of the Test A secondaries (secondary_a.py; AUSTIN_PLAN.md §15, 2026-11-15): code checks with few draws and
# resamples, not results. Fields whose surrogate files are not made yet are replaced by files that exercise the same
# code path: the primary velocity under the names of the four indicators (7) and of availability (12), and the
# 12-window-blanked check field of make_surrogates_windows.py for the 36-month window (3). Usage: smoke_secondary_a.sh [NAMES]
cd ~/AmrGamal || exit 1
D=data/austin_private/checkpoint1
W=work/insar
O=work/secondary/smoke
mkdir -p $O
COMMON="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet --events $D/events/foundation_events.parquet"
F=$W/fields_20261111_slips/field_v.npz; S=$W/surrogates_20261111_slips/surrogates_conditional.npy; Q=$W/quantiles_20261111_slips/surrogate_quantiles.npy
fsq() { echo "--field $1=$F --surrogates $1=$S --quantiles $1=$Q"; }
SEC=$D/secondary
declare -A ARGS
ARGS[2_local_controls]="$(fsq v)"
ARGS[3_window_36]="--field v36=$W/surr2_check/field_v_blank12.npz --surrogates v36=$W/surr2_check/surr3.npy --quantiles v36=$W/surr2_check/q3.npy"
ARGS[4_random_forest]="$(fsq v)"
ARGS[5_baseline_2]="$(fsq v) --other-bp $SEC/other_bp_dates.parquet"
ARGS[5_baseline_1_no_income]="$(fsq v)"
ARGS[7_boosted_trees]="$(fsq v) $(fsq amp) $(fsq lrm) $(fsq acc)"
ARGS[10_issue_date]="$(fsq v) --issue-events $SEC/foundation_events_issue.parquet --issue-episodes $SEC/foundation_first_episodes_issue.parquet"
ARGS[11_fold_seed_0]="$(fsq v)"
ARGS[12_availability]="$(fsq avail) --mask-field $F"
ARGS[D1_demolition]="$(fsq v)"
ARGS[D2_composite]="$(fsq v)"
NAMES=${*:-"2_local_controls 3_window_36 4_random_forest 5_baseline_2 5_baseline_1_no_income 7_boosted_trees 10_issue_date 11_fold_seed_0 12_availability D1_demolition D2_composite"}
for n in $NAMES; do
  t0=$(date +%s)
  env/venv/bin/python -I code/austin/production/secondary_a.py run --secondary $n --mode decoy $COMMON ${ARGS[$n]} \
    --out $O/$n --workers 3 --draws 3 --boot 2 > $O/$n.log 2>&1
  echo "$n exit=$? seconds=$(( $(date +%s) - t0 )) $(date '+%F %T')" >> $O/status_a
done
