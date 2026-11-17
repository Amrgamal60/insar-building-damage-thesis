#!/bin/bash
# Second queue of the secondary conditional-null surrogate files (AUSTIN_PLAN.md §15, 2026-11-15). Usage: surr_queue2.sh cpu|gpu
# It makes the ten files that surr_queue.sh leaves held (a folder with HELD.txt), in the order the secondaries use them:
#   - the 36-month velocity and the lags 1, 3, 6 and 12 (secondaries 3 and 9): their first windows hold no values, so
#     they are made with make_surrogates_windows.py (checked by check_surr_windows.py, 2026-11-15);
#   - local relative motion and acceleration (secondaries 6, 7), availability, no construction mask and the first-run
#     velocity (secondaries 12 and 13, slip sensitivity): unchanged make_surrogates.py, as in surr_queue.sh. They are
#     held only so that the files are made, and the disk fills, in the order of use.
# A queue claims a field by creating $S/<name>/claim (mkdir is atomic). The CPU queue starts when surr_queue.sh cpu and
# every CPU surrogate run have ended; the GPU queue starts when surr_queue.sh gpu has ended. Settings, quantiles, SHA-256,
# disk rule (138 GB = one file + 100 GB floor) and outcome-blindness are those of surr_queue.sh. If a GPU run fails, its
# claim is released so that the CPU queue takes the field, and the GPU queue stops.
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
P=code/austin/production
FIELDS="v36:w:$FS/field_v36.npz lrm:s:$FS/field_lrm.npz acc:s:$FS/field_acc.npz v_lag1:w:$FS/field_v_lag1.npz
v_lag3:w:$FS/field_v_lag3.npz v_lag6:w:$FS/field_v_lag6.npz v_lag12:w:$FS/field_v_lag12.npz avail:s:$FS/field_avail.npz
v_nomask:s:$FS/field_v_nomask.npz v_firstrun:s:$W/fields_20261111/field_v.npz"
log() { echo "$(date '+%F %T') [$ENGINE q2] $*" >> $ST; }
pending_gb() { local t=0 f; for f in $S/*/surrogates_conditional.tmp.npy; do [ -f "$f" ] && t=$(( t + $(stat -c %s "$f") - $(stat -c %b "$f") * 512 )); done; echo $(( t / 1000000000 )); }
free_gb() { df --output=avail -B1000000000 ~ | tail -1 | tr -dc 0-9; }
log "queue start (waits for the first queue)"
if [ $ENGINE = cpu ]; then
  while pgrep -f "[s]urr_queue.sh cpu" > /dev/null || pgrep -f "[r]un_surr_field.sh" > /dev/null || pgrep -f "[m]ake_surrogates.*--backend cpu" > /dev/null; do sleep 60; done
else
  while pgrep -f "[s]urr_queue.sh gpu" > /dev/null; do sleep 60; done
fi
log "queue running"
while :; do
claimed=0
for item in $FIELDS; do
  name=${item%%:*}; rest=${item#*:}; mode=${rest%%:*}; F=${rest#*:}
  O=$S/$name
  [ -f $O/HELD.txt ] || continue
  mkdir $O/claim 2>/dev/null || continue
  claimed=1
  [ -f $F ] || { log "$name: field $F missing"; continue; }
  waited=0
  while :; do
    fr=$(free_gb); pe=$(pending_gb)
    [ $(( fr - pe )) -ge 138 ] && break
    [ $waited = 0 ] && log "$name waits for disk: free $fr GB, still to be written $pe GB"
    waited=1; sleep 600
  done
  echo "$ENGINE" > $O/engine.txt
  if [ $mode = w ]; then MK="$P/make_surrogates_windows.py make"; QU="$P/make_surrogates_windows.py quantiles"
  else MK="$P/make_surrogates.py"; QU="code/austin/planted_signal/planted_signal.py quantiles"; fi
  log "$name surrogates start (field $F, mode $mode)"
  if [ $ENGINE = gpu ]; then
    timeout 4h $PYG -I $MK $A --field $F --out $O/surrogates_conditional.npy --backend gpu > $O/surr.log 2>&1
    rc=$?
  else
    $PYC -I $MK $A --field $F --out $O/surrogates_conditional.npy --backend cpu --workers 64 > $O/surr.log 2>&1
    rc=$?
  fi
  log "$name surrogates exit=$rc"
  if [ $rc != 0 ]; then
    if [ $ENGINE = gpu ]; then
      t=$(date +%Y%m%d_%H%M%S)
      rm -f $O/surrogates_conditional.tmp.npy; mv $O/surr.log $O/surr.gpufail_$t.log; rm -f $O/engine.txt; rmdir $O/claim
      log "$name: GPU run failed (log surr.gpufail_$t.log); claim released so that the CPU queue takes it; GPU queue stops"
      exit 1
    fi
    continue
  fi
  QW=48; [ $ENGINE = gpu ] && QW=32
  $PYC -I $QU $A --field $F --surrogates $O/surrogates_conditional.npy --out $O/surrogate_quantiles.npy --workers $QW > $O/quantiles.log 2>&1
  log "$name quantiles exit=$?"
  (cd $O && sha256sum surrogates_conditional.npy surrogate_quantiles.npy > sha256.txt)
  log "$name done $(cut -c1-16 $O/sha256.txt | tr '\n' ' ')"
done
[ $claimed = 0 ] && break
done
log "queue end"
