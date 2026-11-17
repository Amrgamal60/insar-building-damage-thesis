#!/bin/bash
# Conditional-null surrogates (AUSTIN_PLAN.md §10: ConditionalVariogramNull, cap 1,000, max lag 16, chunk 8, 999 draws,
# seed 2027) of one secondary field, on the CPUs (§14 engine, 64 workers), then their per-draw window quantiles
# (48 workers). Outcome-blind: reads the field and the checkpoint-1 tables only. Same commands as the primary file's
# (make_surrogates.py, planted_signal.py quantiles), with the field changed.
# Usage: run_surr_field.sh NAME FIELD.npz      -> work/insar/surr2/NAME/{surrogates_conditional.npy, surrogate_quantiles.npy}
NAME=$1; F=$2
cd ~/AmrGamal || exit 1
PY=~/AmrGamal/env/venv/bin/python
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet"
O=$W/surr2/$NAME
ST=$W/surr2/status
mkdir -p $O
[ -e $O/surrogates_conditional.npy ] && { echo "$NAME exists; not started $(date '+%F %T')" >> $ST; exit 1; }
avail=$(df --output=avail -BG ~ | tail -1 | tr -dc 0-9)
[ "$avail" -ge 140 ] || { echo "$NAME not started: only ${avail} GB free (floor: 100 GB after a 38 GB file) $(date '+%F %T')" >> $ST; exit 1; }
echo "$NAME start $(date '+%F %T') field $F" >> $ST
$PY -I code/austin/production/make_surrogates.py $A --field $F --out $O/surrogates_conditional.npy --backend cpu --workers 64 > $O/surr.log 2>&1
rc=$?; echo "$NAME surrogates exit=$rc $(date '+%F %T')" >> $ST
[ $rc = 0 ] || exit 1
$PY -I code/austin/planted_signal/planted_signal.py quantiles $A --field $F --surrogates $O/surrogates_conditional.npy \
  --out $O/surrogate_quantiles.npy --workers 48 > $O/quantiles.log 2>&1
echo "$NAME quantiles exit=$? $(date '+%F %T')" >> $ST
