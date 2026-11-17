#!/bin/bash
# Null (a) surrogates on the server GPU (AUSTIN_PLAN.md §15, 2026-11-12), during a pause of another service's inference
# deployment that the user asked for on 2026-11-12 ("use gpu. stop vllm and use the gpu"). The CPU run of null (a)
# continues beside it; which file is used is fixed in §15 before this run. Order:
#   1. save the current ArgoCD sync policies and the deployment; switch off auto-sync on `root`, then `ai-inference`;
#      scale sglang-vision to 0; wait for the GPU to free;
#   2. run make_surrogates_nulla_gpu.py (frozen LowMemVariogramNull on CuPy) under a 4 h limit; once the GPU file holds
#      draws 0-2, compare them with the CPU file (early check); stop the GPU run if they do not agree;
#   3. ALWAYS (success, failure, timeout, or this script being signalled): wait for our GPU memory to be released,
#      scale sglang-vision back to 1, restore both sync policies from the copies saved in step 1 (ai-inference, then
#      root), and record whether the service's pod becomes ready again.
# Driver 580 since the reboot of 2026-11-12: no user-space library workaround.
cd ~/AmrGamal || exit 1
G=~/AmrGamal/work/gpu_pause_20261112
W=~/AmrGamal/work/insar
KC="docker exec k3d-mcait-testing-server-0 kubectl"
D=~/AmrGamal/data/austin_private/checkpoint1
A="--features $D/features/features_2018.parquet --grid $D/grid_folds/eligible_grid_folds.parquet --episodes $D/events/foundation_first_episodes.parquet --censoring $D/events/demolition_censoring.parquet"
OUT=$W/surrogates_20261112_nulla_gpu
CPUF=$W/surrogates_20261112_nulla/surrogates_nulla.tmp.npy
mkdir -p $G $OUT
log() { echo "$(date '+%F %T') $*" >> $G/pause.log; }
free_mib() { nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1; }
RESTORED=0
GPID=
restore() {
  [ "$RESTORED" = 1 ] && return
  RESTORED=1
  [ -n "$GPID" ] && kill -0 $GPID 2>/dev/null && { log "restore: stopping GPU run $GPID"; kill $GPID; sleep 10; }
  log "restore: start (gpu free $(free_mib) MiB)"
  for i in $(seq 60); do f=$(free_mib); [ -n "$f" ] && [ "$f" -ge 22500 ] && break; sleep 10; done
  log "restore: gpu free $(free_mib) MiB before scale-up"
  $KC scale deploy sglang-vision -n platform-services --replicas=1 >> $G/pause.log 2>&1; log "restore: scale rc=$?"
  $KC patch application ai-inference -n argocd --type merge -p "{\"spec\":{\"syncPolicy\":$(cat $G/sync_ai-inference.json)}}" >> $G/pause.log 2>&1; log "restore: ai-inference sync rc=$?"
  $KC patch application root -n argocd --type merge -p "{\"spec\":{\"syncPolicy\":$(cat $G/sync_root.json)}}" >> $G/pause.log 2>&1; log "restore: root sync rc=$?"
  echo "restore issued $(date '+%F %T')" > $G/restore.status
  for i in $(seq 120); do
    r=$($KC get deploy sglang-vision -n platform-services -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
    [ "$r" = "1" ] && break; sleep 15
  done
  log "restore: readyReplicas=$r root sync=$($KC get application root -n argocd -o jsonpath='{.spec.syncPolicy}') ai-inference sync=$($KC get application ai-inference -n argocd -o jsonpath='{.spec.syncPolicy}') gpu free $(free_mib) MiB"
  $KC get pods -n platform-services -o wide >> $G/pause.log 2>&1
  echo "service readyReplicas=$r $(date '+%F %T')" >> $G/restore.status
}
trap restore EXIT
trap 'log "signal TERM"; exit 143' TERM
trap 'log "signal INT"; exit 130' INT
trap 'log "signal HUP"; exit 129' HUP

# 1. save, then pause
$KC get application root -n argocd -o json > $G/app_root.before.json 2>> $G/pause.log || { log "save: root failed"; RESTORED=1; exit 1; }
$KC get application ai-inference -n argocd -o json > $G/app_ai-inference.before.json 2>> $G/pause.log || { log "save: ai-inference failed"; RESTORED=1; exit 1; }
$KC get deploy sglang-vision -n platform-services -o json > $G/deploy_sglang-vision.before.json 2>> $G/pause.log || { log "save: deploy failed"; RESTORED=1; exit 1; }
$KC get application root -n argocd -o jsonpath='{.spec.syncPolicy}' > $G/sync_root.json
$KC get application ai-inference -n argocd -o jsonpath='{.spec.syncPolicy}' > $G/sync_ai-inference.json
grep -q automated $G/sync_root.json && grep -q automated $G/sync_ai-inference.json || { log "save: sync policies not as expected: $(cat $G/sync_root.json) / $(cat $G/sync_ai-inference.json)"; RESTORED=1; exit 1; }
log "saved: root sync=$(cat $G/sync_root.json) ai-inference sync=$(cat $G/sync_ai-inference.json) replicas=$($KC get deploy sglang-vision -n platform-services -o jsonpath='{.spec.replicas}')"
log "pause: start (gpu free $(free_mib) MiB)"
$KC patch application root -n argocd --type merge -p '{"spec":{"syncPolicy":{"automated":null}}}' >> $G/pause.log 2>&1 || { log "pause: root patch failed"; exit 1; }
$KC patch application ai-inference -n argocd --type merge -p '{"spec":{"syncPolicy":{"automated":null}}}' >> $G/pause.log 2>&1 || { log "pause: ai-inference patch failed"; exit 1; }
sleep 5
$KC scale deploy sglang-vision -n platform-services --replicas=0 >> $G/pause.log 2>&1 || { log "pause: scale failed"; exit 1; }
for i in $(seq 60); do f=$(free_mib); [ -n "$f" ] && [ "$f" -ge 22500 ] && break; sleep 10; done
sleep 60
log "pause: after 60 s settle: replicas=$($KC get deploy sglang-vision -n platform-services -o jsonpath='{.spec.replicas}') root sync=$($KC get application root -n argocd -o jsonpath='{.spec.syncPolicy}') ai-inference sync=$($KC get application ai-inference -n argocd -o jsonpath='{.spec.syncPolicy}') gpu free $(free_mib) MiB"
f=$(free_mib)
if [ -z "$f" ] || [ "$f" -lt 22500 ]; then log "pause: GPU not freed ($f MiB); aborting"; echo "gpu exit=not-freed" > $W/nulla_gpu.status; exit 1; fi
[ "$($KC get deploy sglang-vision -n platform-services -o jsonpath='{.spec.replicas}')" = "0" ] || { log "pause: replicas reverted; aborting"; echo "gpu exit=reverted" > $W/nulla_gpu.status; exit 1; }

# 2. GPU run with the early check
log "gpu: start"
echo "gpu start $(date '+%F %T')" > $W/nulla_gpu.status
timeout 4h ~/AmrGamal/env/gpu/bin/python -I code/austin/production/make_surrogates_nulla_gpu.py $A \
  --field $W/fields_20261111_slips/field_v.npz --out $OUT/surrogates_nulla.npy > $W/nulla_gpu.log 2>&1 &
GPID=$!
PER=$((88 * 107243 * 4))
EARLY=0
while kill -0 $GPID 2>/dev/null; do
  if [ $EARLY = 0 ] && [ -f $OUT/surrogates_nulla.tmp.npy ]; then
    held=$(( $(stat -c %b $OUT/surrogates_nulla.tmp.npy) * 512 / PER - 1 ))
    if [ $held -ge 3 ]; then
      ~/AmrGamal/env/venv/bin/python -I code/austin/production/check_gpu_cpu_draws_abs.py $OUT/surrogates_nulla.tmp.npy $CPUF \
        $W/nulla_gpu_cpu_first3.json --upto 3 > $W/nulla_gpu_early.log 2>&1
      if grep -q '"pass": true' $W/nulla_gpu_cpu_first3.json; then
        EARLY=1; log "gpu: early check passed"; echo "early check passed $(date '+%F %T')" >> $W/nulla_gpu.status
      else
        log "gpu: early check FAILED; stopping the GPU run"; echo "early check FAILED $(date '+%F %T')" >> $W/nulla_gpu.status
        kill $GPID; wait $GPID; break
      fi
    fi
  fi
  sleep 20
done
wait $GPID
rc=$?
echo "gpu exit=$rc $(date '+%F %T')" >> $W/nulla_gpu.status
log "gpu: exit=$rc"
GPID=
restore
# 3b. full comparison over the draws the CPU file holds now (the choice itself is made as fixed in §15)
if [ $rc = 0 ]; then
  [ -f $CPUF ] || CPUF=$W/surrogates_20261112_nulla/surrogates_nulla.npy
  ~/AmrGamal/env/venv/bin/python -I code/austin/production/check_gpu_cpu_draws_abs.py $OUT/surrogates_nulla.npy $CPUF \
    $W/nulla_gpu_cpu_all.json > $W/nulla_gpu_all.log 2>&1
  echo "full comparison exit=$? $(date '+%F %T')" >> $W/nulla_gpu.status
fi
exit 0
