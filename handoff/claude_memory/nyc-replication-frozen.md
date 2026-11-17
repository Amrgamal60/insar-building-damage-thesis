---
name: nyc-replication-frozen
description: "NYC replication plan frozen 2026-10-08; decoy done; real run primary done (p=0.418), crashed in s8 from suspected RAM fault, resumed 2026-10-10"
metadata:
  node_type: memory
  type: project
  originSessionId: 0e738ef5-b527-4bcd-85f1-62fb477ec0b7
  modified: 2026-10-11T05:53:18.430Z
---

Alex/feasibility/nyc/NYC_REPLICATION_PLAN.md was approved by the supervisor and frozen on 2026-10-08. The read-only copy is freeze/NYC_REPLICATION_PLAN_frozen.md (SHA-256 59a2aa1a…). The primary population is the older-building domain (65 events at 250 m, 64 risk sets).

Status on 2026-10-08:
- Checkpoint 2 is done (MANIFEST_PART2 3049dada…).
- The InSAR stage is done (out/insar/MANIFEST bbd5f50a…).
- The decoy is done (out/models/decoy/MANIFEST 57390ac7…; DECOY_REPORT.md).
- §14 deviations:
  1. Connected-component rule.
  2. Reduced decoy draw counts.
  3. The bootstrap's block labels were pyarrow strings that arrived corrupted in joblib workers; they are now integer codes.
- The real run (§13 step 5) started 2026-10-08 16:27. It runs detached (setsid); the log is out/models/real_run.log, and the code is hashed in out/models/CODE_REAL_RUN.sha256 (39e85bdb…).
  - It takes about 3 days; the random forest is last and takes about 2.6 days.
  - If it stops, rerun the same command (`../../.venv/bin/python -I scripts/11_models.py raw out --real --jobs 16`). Finished analyses are skipped. Log any code fix in §14 with before and after values.
  - 2026-10-08 16:52 it crashed in s8 (primary already done: p = 0.418, not replicated). Suspected non-ECC RAM bit-39 flips (same signature as the decoy crash), logged as §14 deviation 4. The user said to stop diagnosing; it was resumed unchanged 2026-10-10 17:52, detached (setsid) via scratchpad launch_real.sh. Budget for secondaries ends ~2026-10-15 16:27.
  - The live log is out/models/real_run_live.log (copied every minute from the running process by scratchpad mirror_log.sh): a `sed -i` on real_run.log on 10-10 replaced its inode, so the process writes to the deleted file. Never edit a log in place while a run writes to it. Merge the two logs at the end.
  - When it ends: run `scripts/12_report.py out --real` to get NYC_RESULT.md, record the result and hashes in §15, and update this memory.
  - 2026-10-11: it crashed again 10-10 21:50 in s2's bootstrap; Codex then resumed it 5 times overnight (checkpoints, repeat checks, 4 jobs; §14 dev 5–8) and every attempt crashed (bit-39 RAM fault). The user is moving the project to another PC. Full state and resume steps: Alex/HANDOFF.md (copies of memory, scratchpad, transcripts in Alex/handoff/).

**Why:** this is a preregistered replication. Every change after the freeze goes in §14, with whether any NYC result had been seen.
**How to apply:** never edit the frozen copy; follow §13's order. The user asked (2026-10-08) to loop until the plan is done, with Sonnet subagents for side work. Never tune after results. See also [[gpu-allowed]].
