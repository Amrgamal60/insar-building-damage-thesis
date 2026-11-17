# Coordinator execution notes

Execution only. Nothing here changes a simulation, model, null or decision setting; the
source fingerprint (`run_calibration.source_hashes()`) is unchanged and was checked
against the existing records before the restart.

## 2026-11-01, GPU freed and scheduling changed

- About 19:20Z the user scaled the vLLM deployment down, freeing about 23 GB of GPU
  memory. The calibration Codex worker had run out of credits by then ("Your workspace
  is out of credits"); the coordinator (Claude) took over running the workload.
  `run_workload.py` kept running on its own throughout.
- Measured, small city, GPU path (`gpu_execution.run_a_gpu`, one dataset at a time, refits
  on the 16-process pool): datasets A_05_0192 to A_05_0194 took 33.2, 26.6 and 26.7 s.
  CPU/GPU first-draw differences were at most 1.5e-14 (tolerance 1e-11). The CPU path in
  the same cell finished 16 datasets every 285–327 s, about 20 s per dataset. The GPU path
  is therefore slower for the small cells. For Test B, `run_b_gpu` sends all 99 refits of
  a dataset to one pool worker, which would serialise the slowest part.
- Change to `run_workload.py` (not part of the fingerprint):
  - `device_policy.json`, read at each cell start, lists the cells allowed on the GPU path
    and the refit pool size for them. Without the file every cell runs on CPU. CPU batches
    keep the design's worker counts.
  - Heartbeats every 3600 s instead of 300 s.
- The run was stopped by PID at 19:34Z between GPU datasets and restarted (PID 340741,
  log `workload_run_r2.log`; the earlier log `workload_run.log` is kept). Completed
  records are reused through the existing resume check. Records A_05_0192 to A_05_0194
  carry `execution_backend: gpu`; all earlier records are CPU.
- 4x-city GPU pilot (scratchpad script, replicate 9999, outside the design; timings only,
  result not saved; 8 refit workers while the 16 small-cell CPU workers were running):
  82.2 s per dataset (registered null 40.5 s, conditional 38.8 s; equality 2.1e-14 and
  5.8e-15). The worker's 5-draw CPU benchmark extrapolates to about 1,200 s per 4x dataset
  on one CPU worker, about 200 s per dataset across 6 workers.
- `device_policy.json` set at 19:40Z: GPU path for A_10 and A_11 only, 16 refit workers.
  Small Test A cells, power cells and Test B stay on CPU.
- Worker restart at 2026-11-01 19:37:29Z (after coordinator ownership handoff): PID 365198, detached with `setsid nohup .venv/bin/python -I feasibility/austin/scripts/calibration/run_workload.py --workers 16 --scale-workers 6 --b-workers 8`, log `workload_run_r3.log`. First cell: A_00, 200 datasets, 16 workers, GPU disallowed, 8.39 GiB MemAvailable, 23,118 MiB GPU free. This restart uses the same design/source fingerprint; completed records resume in place.

## 2026-11-02, memory kill during Test B and restart

- Test B with 8 workers (about 1.3–1.5 GB each) pushed the machine into thrashing: swap
  full, memory pressure "full" about 30%, Test B datasets about 3,000 s instead of the
  benchmarked few hundred. About 14 GB of RAM was held by other projects' files in the
  tmpfs `/tmp`, and about 2.75 GB by an idle embedding server.
- At 02:29Z systemd-oomd killed the Codex worker's terminal scope (16 processes: the agent,
  driver PID 365198 and the Test B pool). The kernel OOM killer also killed an unrelated
  Java process. All 1,816 completed records were checked afterwards: readable, status
  complete, no temporary files. The Test B batch in progress was lost.
- The coordinator restarted the driver at 02:30Z in its own systemd user scope
  (`systemd-run --user --scope --unit=austin-calib-r4`) so that a memory kill cannot take it
  together with an interactive terminal: `run_workload.py --workers 16 --scale-workers 6
  --b-workers 6`, log `workload_run_r4.log`, driver PID 2757570. Test B uses 6 workers instead
  of 8 to leave memory headroom. Scientific settings and the source fingerprint are unchanged.
- 2026-11-02 08:16Z: at the user's request the whole scope was paused with SIGSTOP
  (`systemctl --user kill --signal=SIGSTOP austin-calib-r4.scope`) at Test B 144/200, after a
  10-core runtime CPU cap had been set. Resume with SIGCONT; in-flight datasets continue.
- 2026-11-02 ~08:20Z: the user needed the RAM, so the scope was stopped
  (`systemctl --user stop austin-calib-r4.scope`). 144/200 Test B records kept; no temporary
  files or shared-memory segments left. The in-flight batch is redone on resume.

## 2026-11-06, resume (r5)

- 2026-11-06 18:59Z: the coordinator resumed the run in a new systemd user scope
  (`systemd-run --user --scope --unit=austin-calib-r5`): `run_workload.py --workers 16
  --scale-workers 6 --b-workers 6`, log `workload_run_r5.log`, driver PID 1381714. Same
  source fingerprint and scientific settings. At start: 10.45 GiB MemAvailable, 1,006 MiB GPU
  free (the vLLM server was running again). No GPU was needed: A_10 and A_11, the only cells
  allowed on the GPU path, were already complete, and `device_policy.json` was not changed.
- All Test A null cells and A_10/A_11 were read back from their records (cached). Test B
  ran the remaining 56 datasets (144 kept + 56 = 200) and finished at 20:58:33Z. The power
  cells then ran on 16 CPU workers: A_08 (100 datasets) 20:58Z–21:27Z, A_09 from 21:27Z.
- The user had chosen the conditional null (b) on 2026-11-06, before this resume, from the
  completed null cells (`coordinator_rule_check.json`, branch 3). The remaining cells are
  Test B and power; they cannot change that selection.
