"""Supervise a resumed real run, enforce its original budget, and build its report."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "out/models"
RESTART = MODELS / "restart_20261010"
STATUS = RESTART / "status.json"
LOG = MODELS / "codex_resume.log"
DEADLINE = datetime(2026, 10, 8, 16, 27, 20, tzinfo=ZoneInfo("Africa/Cairo")) + timedelta(days=7)
PYTHON = ROOT.parents[1] / ".venv/bin/python"
JOBS = 16  # new PC, 2026-10-14 (§14 deviation 9); was 4
# OPENBLAS_CORETYPE: the old PC's Haswell BLAS kernel; this PC's SkylakeX kernel moves ROC/PR AUC by up to 1e-7 (dev. 9)
EXECUTION_ENV = dict(os.environ, NPY_DISABLE_CPU_FEATURES="X86_V3", OPENBLAS_NUM_THREADS="1",
                     MKL_NUM_THREADS="1", OMP_NUM_THREADS="1", OPENBLAS_CORETYPE="Haswell")


def write_status(state, **values):
    progress = {}
    for tag in (MODELS / "real/checkpoints").glob("*"):
        caches = [p for p in tag.iterdir() if p.is_dir()]
        if not caches:
            continue
        cache = max(caches, key=lambda p: p.stat().st_mtime)
        counts = {stage: sum(p.stem.isdigit() for p in (cache / stage).glob("*.json"))
                  for stage in ("null", "bootstrap")}
        complete = cache / "null_complete.json"
        if complete.exists():
            try:
                meta = json.loads(complete.read_text())
                counts["null"] = meta.get("draws", meta.get("generated_draws", counts["null"]))
            except (FileNotFoundError, json.JSONDecodeError):
                pass  # Monitoring may coincide with the calculation's metadata write.
        progress[tag.name] = counts
    data = {"state": state, "updated_utc": datetime.now(timezone.utc).isoformat(),
            "supervisor_pid": os.getpid(), "deadline": DEADLINE.isoformat(),
            "numpy_disabled_cpu_features": EXECUTION_ENV["NPY_DISABLE_CPU_FEATURES"],
            "blas_threads": 1,
            "calculation_checkpoints": progress,
            "log": str(LOG), "completed": sorted(p.stem.removeprefix("result_")
                                               for p in (MODELS / "real").glob("result_*.json")), **values}
    tmp = STATUS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(STATUS)


def main():
    RESTART.mkdir(exist_ok=True)
    lock = (MODELS / "codex_resume.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit("a Codex resume supervisor is already running")
    snapshot_path = RESTART / "COMPLETED_BEFORE.json"
    snapshot = json.loads(snapshot_path.read_text())
    command = [str(PYTHON), "-I", "scripts/11_models.py", "raw", "out", "--real", "--jobs", str(JOBS)]
    print(f"Resume log: {LOG}", flush=True)
    print(f"Original secondary-analysis deadline: {DEADLINE.isoformat()}", flush=True)
    with LOG.open("a", buffering=1) as log:
        log.write(f"\n=== {datetime.now(timezone.utc).isoformat()} resume; jobs={JOBS}; OPENBLAS_CORETYPE=Haswell; original seeds and counts; repeat checks and calculation checkpoints enabled\n")
        if datetime.now(timezone.utc) >= DEADLINE:
            child = None
            timed_out, code = True, None
        else:
            child = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True, env=EXECUTION_ENV)
            write_status("running", model_pid=child.pid, command=command)
            print(f"Model process started: {child.pid}", flush=True)
            timed_out = False
            while child.poll() is None:
                if datetime.now(timezone.utc) >= DEADLINE:
                    timed_out = True
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
                    break
                write_status("running", model_pid=child.pid, command=command)
                time.sleep(15)
            code = child.returncode
        log.write(f"\nEXIT {code} {datetime.now(timezone.utc).isoformat()} budget_exhausted={timed_out}\n")
        changed = [name for name, before in snapshot.items()
                   if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != before]
        if changed:
            write_status("failed", returncode=code, reason="previously completed outputs changed", changed=changed)
            sys.exit("previously completed outputs changed")
        if code != 0 and not timed_out:
            write_status("failed", returncode=code, command=command,
                         reason="model process failed; consult codex_resume.log")
            sys.exit(f"model run failed with exit code {code}; see {LOG}")
        write_status("verifying_primary", command=command)
        verification = subprocess.run([str(PYTHON), "-I", str(RESTART / "verify_metrics.py"), "--full"],
                                      cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log,
                                      stderr=subprocess.STDOUT, env=EXECUTION_ENV)
        if verification.returncode:
            write_status("failed", returncode=verification.returncode, reason="full primary verification failed")
            sys.exit("full primary verification failed; no final report generated")
        report = subprocess.run([str(PYTHON), "-I", "scripts/12_report.py", "out", "--real"],
                                cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                env=EXECUTION_ENV)
        if report.returncode:
            write_status("failed", returncode=report.returncode, reason="report generation failed")
            sys.exit("report generation failed")
    files = sorted((MODELS / "real").glob("result_*.json")) + sorted((MODELS / "real").glob("*.csv"))
    files += [MODELS / "real/NYC_RESULT.md"]
    manifest = RESTART / "RESULT_MANIFEST.sha256"
    manifest.write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}\n" for p in files))
    write_status("budget_exhausted" if timed_out else "complete", returncode=code,
                 report=str(MODELS / "real/NYC_RESULT.md"), manifest=str(manifest),
                 primary_recomputation=str(RESTART / "FULL_PRIMARY_VERIFICATION.json"),
                 hardware_diagnosis="suspected memory fault remains unconfirmed")
    print("Report generated; completed outputs verified unchanged", flush=True)


if __name__ == "__main__":
    main()
