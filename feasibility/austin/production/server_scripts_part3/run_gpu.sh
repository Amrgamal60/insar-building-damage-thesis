#!/bin/bash
# Test A conditional-null surrogates on the server GPU (AUSTIN_PLAN.md §15 part 3, frozen GPU path), during a pause of
# another service's inference deployment that the user approved on 2026-11-11. Order:
#   1. switch off ArgoCD auto-sync on `root`, then `ai-inference`; scale sglang-vision to 0; wait for the GPU to free;
#   2. run make_surrogates.py --backend gpu under a 4 h time limit;
#   3. ALWAYS (success, failure, timeout, or this script being signalled): wait for our GPU memory to be released,
#      scale sglang-vision back to 1, and restore both syncPolicies from the copies saved before (ai-inference, then root).
cd ~/AmrGamal || exit 1
G=~/AmrGamal/work/gpu_pause
W=~/AmrGamal/work/insar
NV=~/AmrGamal/env/nvidia550/root/usr
export LD_LIBRARY_PATH=$NV/lib/x86_64-linux-gnu
export PATH=$NV/bin:$PATH
KC="docker exec k3d-mcait-testing-server-0 kubectl"
D=~/AmrGamal/data/austin_private/checkpoint1
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet"
OUT=$W/surrogates_20261111_slips_gpu
log() { echo "$(date '+%F %T') $*" >> $G/pause.log; }
free_mib() { nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1; }
RESTORED=0
restore() {
  [ "$RESTORED" = 1 ] && return
  RESTORED=1
  log "restore: start (gpu free $(free_mib) MiB)"
  for i in $(seq 60); do f=$(free_mib); [ -n "$f" ] && [ "$f" -ge 22500 ] && break; sleep 10; done
  log "restore: gpu free $(free_mib) MiB before scale-up"
  $KC scale deploy sglang-vision -n platform-services --replicas=1 >> $G/pause.log 2>&1; log "restore: scale rc=$?"
  $KC patch application ai-inference -n argocd --type merge -p "{\"spec\":{\"syncPolicy\":$(cat $G/sync_ai-inference.json)}}" >> $G/pause.log 2>&1; log "restore: ai-inference sync rc=$?"
  $KC patch application root -n argocd --type merge -p "{\"spec\":{\"syncPolicy\":$(cat $G/sync_root.json)}}" >> $G/pause.log 2>&1; log "restore: root sync rc=$?"
  echo "restore issued $(date '+%F %T')" > $G/restore.status
}
trap restore EXIT
trap 'log "signal TERM"; exit 143' TERM
trap 'log "signal INT"; exit 130' INT
trap 'log "signal HUP"; exit 129' HUP

log "pause: start (gpu free $(free_mib) MiB)"
$KC patch application root -n argocd --type merge -p '{"spec":{"syncPolicy":{"automated":null}}}' >> $G/pause.log 2>&1 || { log "pause: root patch failed"; exit 1; }
$KC patch application ai-inference -n argocd --type merge -p '{"spec":{"syncPolicy":{"automated":null}}}' >> $G/pause.log 2>&1 || { log "pause: ai-inference patch failed"; exit 1; }
sleep 5
log "pause: root sync=$($KC get application root -n argocd -o jsonpath='{.spec.syncPolicy}') ai-inference sync=$($KC get application ai-inference -n argocd -o jsonpath='{.spec.syncPolicy}')"
$KC scale deploy sglang-vision -n platform-services --replicas=0 >> $G/pause.log 2>&1 || { log "pause: scale failed"; exit 1; }
for i in $(seq 60); do f=$(free_mib); [ -n "$f" ] && [ "$f" -ge 22500 ] && break; sleep 10; done
sleep 60
log "pause: after 60 s settle: replicas=$($KC get deploy sglang-vision -n platform-services -o jsonpath='{.spec.replicas}') root sync=$($KC get application root -n argocd -o jsonpath='{.spec.syncPolicy}') ai-inference sync=$($KC get application ai-inference -n argocd -o jsonpath='{.spec.syncPolicy}') gpu free $(free_mib) MiB"
f=$(free_mib)
if [ -z "$f" ] || [ "$f" -lt 22500 ]; then log "pause: GPU not freed ($f MiB); aborting"; echo "gpu exit=not-freed" > $W/surr_gpu.status; exit 1; fi
[ "$($KC get deploy sglang-vision -n platform-services -o jsonpath='{.spec.replicas}')" = "0" ] || { log "pause: replicas reverted; aborting"; echo "gpu exit=reverted" > $W/surr_gpu.status; exit 1; }

mkdir -p $OUT
log "gpu: start"
timeout 4h ~/AmrGamal/env/gpu/bin/python -I code/austin/production/make_surrogates.py $A --field $W/fields_20261111_slips/field_v.npz --out $OUT/surrogates_conditional.npy --backend gpu > $W/surr_gpu.log 2>&1
rc=$?
echo "gpu exit=$rc" > $W/surr_gpu.status
log "gpu: exit=$rc"
exit 0
