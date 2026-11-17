#!/bin/bash
# Restores the inference deployment stopped by gpu_stop.sh: scale sglang-vision back to 1, then put back the saved
# ArgoCD sync policies (ai-inference, then root), and wait for the pod to be ready. Run only when the user asks.
# It refuses while a project GPU job is running.
G=${1:-~/AmrGamal/work/gpu_stop_20261115}
KC="docker exec k3d-mcait-testing-server-0 kubectl"
log() { echo "$(date '+%F %T') $*" >> $G/stop.log; }
free_mib() { nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1; }
[ -s $G/sync_root.json ] && [ -s $G/sync_ai-inference.json ] || { echo "no saved policies in $G"; exit 1; }
pgrep -f "[m]ake_surrogates.py.*--backend gpu" > /dev/null && { echo "a project GPU job is running; not restored"; exit 1; }
log "restore: start (gpu free $(free_mib) MiB)"
$KC scale deploy sglang-vision -n platform-services --replicas=1 >> $G/stop.log 2>&1; log "restore: scale rc=$?"
$KC patch application ai-inference -n argocd --type merge -p "{\"spec\":{\"syncPolicy\":$(cat $G/sync_ai-inference.json)}}" >> $G/stop.log 2>&1; log "restore: ai-inference sync rc=$?"
$KC patch application root -n argocd --type merge -p "{\"spec\":{\"syncPolicy\":$(cat $G/sync_root.json)}}" >> $G/stop.log 2>&1; log "restore: root sync rc=$?"
for i in $(seq 120); do r=$($KC get deploy sglang-vision -n platform-services -o jsonpath='{.status.readyReplicas}' 2>/dev/null); [ "$r" = "1" ] && break; sleep 15; done
log "restore: readyReplicas=$r root sync=$($KC get application root -n argocd -o jsonpath='{.spec.syncPolicy}') ai-inference sync=$($KC get application ai-inference -n argocd -o jsonpath='{.spec.syncPolicy}') gpu free $(free_mib) MiB"
echo "restored $(date '+%F %T'), readyReplicas=$r" >> $G/status
cat $G/status
