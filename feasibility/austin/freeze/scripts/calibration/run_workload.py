"""Cell-complete scheduling, device provenance, heartbeats and durable progress.

The core simulator/model/null settings remain in frozen run_calibration.py.
This execution-only driver never reads interim p values or changes parameters.
"""
import os
for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[name] = "1"
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import concurrent.futures
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import threading
import multiprocessing as mp

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
from run_calibration import specifications, source_hashes, run_job, atomic_json

TERMINAL = "term_53f7922c-998c-4810-bf01-2471e7f9f41a"
TASK = "task_1cec1d8f45c8"
DISPATCH = "ctx_45b006adbb93"


def lifecycle(kind, subject, body, phase=None):
    cmd = ["orca-ide", "orchestration", "send", "--from", TERMINAL,
           "--type", kind, "--subject", subject, "--body", body,
           "--task-id", TASK, "--dispatch-id", DISPATCH]
    if phase:
        cmd += ["--phase", phase]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def gpu_free():
    try:
        out = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], text=True, timeout=15)
        return int(out.splitlines()[0])
    except Exception:
        return 0


def ram_available_gib():
    with open("/proc/meminfo") as stream:
        available_kib = int(next(line.split()[1] for line in stream if line.startswith("MemAvailable:")))
    return available_kib/1024**2


def device_policy():
    # Coordinator execution policy, read at each cell start: cells allowed on the
    # GPU path and the CPU refit pool size for them. Missing file means CPU only.
    path = HERE/"device_policy.json"
    if not path.exists():
        return set(), 0
    policy = json.loads(path.read_text())
    return set(policy.get("gpu_cells", [])), int(policy.get("gpu_refit_workers", 0))


def run_cpu(job):
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    path, cached, elapsed = run_job(job)
    p = Path(path)
    record = json.loads(p.read_text())
    if "execution_backend" not in record:
        record["execution_backend"] = "cpu"
        record["execution_driver_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        atomic_json(p, record)
    return path, cached, elapsed


def groups(config):
    a = specifications(config, "A")
    s = specifications(config, "S")
    b = specifications(config, "B")
    for cell in range(8):
        yield f"A_{cell:02d}", [spec for spec in a if spec[1] == cell], config["execution"]["a_cpu_workers"]
    for cell in config["a"]["scale_cells"]["cell_ids"]:
        yield f"A_{cell:02d}", [spec for spec in s if spec[1] == cell], config["execution"]["scale_cpu_workers"]
    yield "B_00", b, config["execution"]["b_cpu_workers"]
    for cell in (8, 9):
        yield f"A_{cell:02d}", [spec for spec in a if spec[1] == cell], config["execution"]["a_cpu_workers"]


def monitor(stop, state):
    last_hb = 0.
    while not stop.is_set():
        if time.time()-last_hb >= 3600:
            lifecycle("heartbeat", "Calibration running", json.dumps(state, sort_keys=True), "implementing")
            last_hb = time.time()
        try:
            checked = subprocess.run(["orca-ide", "orchestration", "check", "--terminal", TERMINAL, "--json"],
                                     capture_output=True, text=True, timeout=30)
            content = json.loads(checked.stdout)
            if content.get("result", {}).get("count", 0):
                atomic_json(HERE/"coordinator_inbox.json", content)
                print("COORDINATOR MESSAGE WAITING: coordinator_inbox.json", flush=True)
        except Exception as exc:
            print(f"Monitor checkpoint: {exc!r}", flush=True)
        stop.wait(60)
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cells", nargs="*", help="Optional subset of named cells, for exact resume")
    ap.add_argument("--workers", type=int, default=10, help="Small Test A and power CPU cap; execution only")
    ap.add_argument("--scale-workers", type=int, default=6, help="Scale cell CPU cap; execution only")
    ap.add_argument("--b-workers", type=int, default=8, help="Test B CPU cap; execution only")
    args = ap.parse_args()
    if not (HERE/"coordinator_go.txt").exists():
        raise RuntimeError("Coordinator go required")
    config = json.loads((HERE/"design.json").read_text())
    fingerprint = source_hashes()
    folder = HERE/"records"
    start = time.time()
    completed = 0
    all_groups = list(groups(config))
    state = dict(status="running", completed_this_run=0, cell="starting", interim_results_inspected=False)
    stop = threading.Event()
    thread = threading.Thread(target=monitor, args=(stop, state), daemon=True)
    thread.start()
    try:
        for label, specs, configured_workers in all_groups:
            if args.cells and label not in args.cells:
                continue
            configured_workers = (args.scale_workers if label in ("A_10", "A_11")
                                  else args.b_workers if label == "B_00" else args.workers)
            available = ram_available_gib()
            workers = configured_workers if available >= 4.0 else min(configured_workers, max(2, configured_workers//2))
            # Enforce cell completion before launching any task in the next cell.
            jobs = [(config, spec, fingerprint, str(folder)) for spec in specs]
            gpu_cells, gpu_refit_workers = device_policy()
            gpu_allowed = label in gpu_cells
            # CPU batches keep the design's worker count; only GPU refits use a larger pool.
            pool_workers = max(workers, gpu_refit_workers) if gpu_allowed else workers
            state.update(cell=label, cell_complete=0, cell_total=len(specs), cpu_workers=workers,
                         gpu_allowed=gpu_allowed, pool_workers=pool_workers)
            print(json.dumps(dict(event="cell_start", cell=label, datasets=len(specs), workers=workers,
                                  gpu_allowed=gpu_allowed, pool_workers=pool_workers,
                                  ram_available_gib=available,
                                  gpu_free_mib=gpu_free(), utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))), flush=True)
            with ProcessPoolExecutor(max_workers=pool_workers, mp_context=mp.get_context("spawn")) as pool:
                cell_done = 0
                todo = list(jobs)
                while todo:
                    from gpu_execution import ready, run_gpu_job
                    if gpu_allowed and ready(label):
                        job = todo.pop(0)
                        try:
                            state["device"] = "gpu+cpu_refits"
                            batch_results = [run_gpu_job(job, pool)]
                        except (MemoryError, ArithmeticError) as exc:
                            print(json.dumps(dict(event="gpu_fallback", cell=label, reason=str(exc))), flush=True)
                            state["device"] = "cpu_fallback"
                            batch_results = [pool.submit(run_cpu, job).result()]
                    else:
                        state["device"] = "cpu"
                        batch, todo = todo[:workers], todo[workers:]
                        futures = [pool.submit(run_cpu, job) for job in batch]
                        batch_results = []
                        for future in as_completed(futures):
                            batch_results.append(future.result())
                    for path, cached, elapsed in batch_results:
                        completed += 1
                        cell_done += 1
                        progress = dict(event="dataset_complete", cell=label, cell_complete=cell_done,
                            cell_total=len(specs), completed_this_run=completed, cached=cached,
                            dataset_seconds=elapsed, wall_seconds=time.time()-start, path=path,
                            utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
                        print(json.dumps(progress), flush=True)
                        atomic_json(HERE/"progress.json", progress)
                        state.update(cell_complete=cell_done, completed_this_run=completed,
                                     latest_dataset_seconds=elapsed, wall_seconds=time.time()-start)
            atomic_json(HERE/f"complete_{label}.json", dict(cell=label, datasets=len(specs),
                source_hashes=fingerprint, finished_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
            lifecycle("heartbeat", "Calibration cell complete",
                f"Completed {label}: {cell_done}/{len(specs)} datasets. CPU cap {workers}; RAM available at cell start {available:.1f} GiB.",
                "implementing")
        atomic_json(HERE/"workload_complete.json", dict(status="complete", completed_this_run=completed,
            wall_seconds=time.time()-start, source_hashes=fingerprint))
        print("WORKLOAD COMPLETE", flush=True)
    except Exception as exc:
        lifecycle("escalation", "Calibration execution failed", repr(exc))
        raise
    finally:
        stop.set()
        thread.join(timeout=35)


if __name__ == "__main__":
    main()
