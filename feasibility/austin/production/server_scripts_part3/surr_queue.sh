#!/bin/bash
# Queue of the secondary conditional-null surrogate files (AUSTIN_PLAN.md §15, 2026-11-15). Usage: surr_queue.sh cpu|gpu
# The CPU queue and the GPU queue walk the same list, in the numbered order of §12, and each field is made by one of
# them only: a queue claims a field by creating its folder (mkdir is atomic) and skips claimed fields.
# Per field, with the primary file's settings (§10: ConditionalVariogramNull, cap 1,000, max lag 16, chunk 8, 999
# draws, seed 2027) and the field changed:
#   - surrogates: make_surrogates.py, on the CPU engine of §14 (64 workers) or on the frozen GPU path (§14: "the frozen
#     GPU path may run there instead"); the engine is written to engine.txt;
#   - per-draw window quantiles: planted_signal.py quantiles (unchanged);
#   - SHA-256 of the surrogate file.
# Outcome-blind: reads only the field and the checkpoint-1 tables. If the GPU run fails, its folder is renamed so that
# the CPU queue takes the field. Disk: a field starts only when free space, less the part of files still being written,
# is at least 38 GB (one file) + 100 GB (floor); otherwise the queue waits. The list is walked again until a pass claims
# nothing.
ENGINE=$1
case "$ENGINE" in cpu|gpu) ;; *) echo "usage: $0 cpu|gpu"; exit 2 ;; esac
cd ~/AmrGamal || exit 1
PYC=~/AmrGamal/env/venv/bin/python
PYG=~/AmrGamal/env/gpu/bin/python
W=~/AmrGamal/work/insar
D=~/AmrGamal/data/austin_private/checkpoint1
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet"
FS=$W/fields_20261111_slips
S=$W/surr2
ST=$S/status
mkdir -p $S
FIELDS="v12:$FS/field_v12.npz v36:$FS/field_v36.npz amp:$FS/field_amp.npz lrm:$FS/field_lrm.npz acc:$FS/field_acc.npz
v_lag1:$FS/field_v_lag1.npz v_lag3:$FS/field_v_lag3.npz v_lag6:$FS/field_v_lag6.npz v_lag12:$FS/field_v_lag12.npz
avail:$FS/field_avail.npz v_nomask:$FS/field_v_nomask.npz v_firstrun:$W/fields_20261111/field_v.npz"
log() { echo "$(date '+%F %T') [$ENGINE] $*" >> $ST; }
pending_gb() { local t=0 f; for f in $S/*/surrogates_conditional.tmp.npy; do [ -f "$f" ] && t=$(( t + $(stat -c %s "$f") - $(stat -c %b "$f") * 512 )); done; echo $(( t / 1000000000 )); }
free_gb() { df --output=avail -B1000000000 ~ | tail -1 | tr -dc 0-9; }
log "queue start"
if [ $ENGINE = cpu ]; then
  while pgrep -f "[m]ake_surrogates.py.*--backend cpu" > /dev/null; do sleep 60; done
fi
while :; do
claimed=0
for item in $FIELDS; do
  name=${item%%:*}; F=${item#*:}
  mkdir $S/$name 2>/dev/null || continue
  claimed=1
  O=$S/$name
  [ -f $F ] || { log "$name: field $F missing"; continue; }
  waited=0
  while :; do
    fr=$(free_gb); pe=$(pending_gb)
    [ $(( fr - pe )) -ge 138 ] && break
    [ $waited = 0 ] && log "$name waits for disk: free $fr GB, still to be written $pe GB"
    waited=1; sleep 600
  done
  echo "$ENGINE" > $O/engine.txt
  log "$name surrogates start (field $F)"
  if [ $ENGINE = gpu ]; then
    timeout 4h $PYG -I code/austin/production/make_surrogates.py $A --field $F --out $O/surrogates_conditional.npy --backend gpu > $O/surr.log 2>&1
    rc=$?
  else
    $PYC -I code/austin/production/make_surrogates.py $A --field $F --out $O/surrogates_conditional.npy --backend cpu --workers 64 > $O/surr.log 2>&1
    rc=$?
  fi
  log "$name surrogates exit=$rc"
  if [ $rc != 0 ]; then
    if [ $ENGINE = gpu ]; then
      rm -f $O/surrogates_conditional.tmp.npy
      mv $O $S/${name}.gpufail_$(date +%Y%m%d_%H%M%S); log "$name: GPU run failed; folder renamed so that the CPU queue takes it"
      exit 1
    fi
    continue
  fi
  QW=48; [ $ENGINE = gpu ] && QW=32
  $PYC -I code/austin/planted_signal/planted_signal.py quantiles $A --field $F --surrogates $O/surrogates_conditional.npy \
    --out $O/surrogate_quantiles.npy --workers $QW > $O/quantiles.log 2>&1
  log "$name quantiles exit=$?"
  (cd $O && sha256sum surrogates_conditional.npy surrogate_quantiles.npy > sha256.txt)
  log "$name done $(cut -c1-16 $O/sha256.txt | tr '\n' ' ')"
done
[ $claimed = 0 ] && break   # a pass that claims nothing ends the queue (a field freed by a failed GPU run is taken on the next pass)
done
log "queue end"
