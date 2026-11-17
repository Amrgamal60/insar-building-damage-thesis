#!/bin/bash
# Stops another service's inference deployment (sglang-vision, k3d cluster mcait-testing) so that the project can use the
# server GPU, at the user's request of 2026-11-15 ("stop vllm prmentatly and use gpu"). The stop is lasting: there is NO
# automatic restore. gpu_restore.sh puts the service and its ArgoCD sync policies back from the copies saved here.
# Steps (as the pauses of 2026-11-11/12): save the applications, the deployment and the sync policies; switch off
# auto-sync on `root`, then `ai-inference` (otherwise self-heal scales the service back); scale sglang-vision to 0;
# check after 60 s that the GPU is free, the replica count stays 0 and auto-sync stays off.
G=${1:-~/AmrGamal/work/gpu_stop_20261115}
KC="docker exec k3d-mcait-testing-server-0 kubectl"
mkdir -p $G
log() { echo "$(date '+%F %T') $*" >> $G/stop.log; }
free_mib() { nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1; }
[ -e $G/sync_root.json ] && { log "copies already saved in $G; not run again"; exit 1; }
$KC get application root -n argocd -o json > $G/app_root.before.json 2>> $G/stop.log || { log "save: root failed"; exit 1; }
$KC get application ai-inference -n argocd -o json > $G/app_ai-inference.before.json 2>> $G/stop.log || { log "save: ai-inference failed"; exit 1; }
$KC get deploy sglang-vision -n platform-services -o json > $G/deploy_sglang-vision.before.json 2>> $G/stop.log || { log "save: deploy failed"; exit 1; }
$KC get application root -n argocd -o jsonpath='{.spec.syncPolicy}' > $G/sync_root.json
$KC get application ai-inference -n argocd -o jsonpath='{.spec.syncPolicy}' > $G/sync_ai-inference.json
grep -q automated $G/sync_root.json && grep -q automated $G/sync_ai-inference.json || { log "save: sync policies not as expected"; exit 1; }
log "saved: root sync=$(cat $G/sync_root.json) ai-inference sync=$(cat $G/sync_ai-inference.json) replicas=$($KC get deploy sglang-vision -n platform-services -o jsonpath='{.spec.replicas}') gpu free $(free_mib) MiB"
$KC patch application root -n argocd --type merge -p '{"spec":{"syncPolicy":{"automated":null}}}' >> $G/stop.log 2>&1 || { log "root patch failed"; exit 1; }
$KC patch application ai-inference -n argocd --type merge -p '{"spec":{"syncPolicy":{"automated":null}}}' >> $G/stop.log 2>&1 || { log "ai-inference patch failed"; exit 1; }
sleep 5
$KC scale deploy sglang-vision -n platform-services --replicas=0 >> $G/stop.log 2>&1 || { log "scale failed"; exit 1; }
for i in $(seq 60); do f=$(free_mib); [ -n "$f" ] && [ "$f" -ge 22500 ] && break; sleep 10; done
sleep 60
r=$($KC get deploy sglang-vision -n platform-services -o jsonpath='{.spec.replicas}')
log "after 60 s: replicas=$r root sync=$($KC get application root -n argocd -o jsonpath='{.spec.syncPolicy}') ai-inference sync=$($KC get application ai-inference -n argocd -o jsonpath='{.spec.syncPolicy}') gpu free $(free_mib) MiB"
f=$(free_mib)
if [ -n "$f" ] && [ "$f" -ge 22500 ] && [ "$r" = "0" ]; then echo "stopped $(date '+%F %T')" > $G/status; else echo "NOT stopped cleanly $(date '+%F %T') (free $f MiB, replicas $r)" > $G/status; fi
cat $G/status
