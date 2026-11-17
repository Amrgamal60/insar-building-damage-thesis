"""Bounded recovery of interrupted numerical workers using saved calculation checkpoints."""
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent
RESTART = ROOT / "out/models/restart_20261010"
STATUS = RESTART / "status.json"
LOG = ROOT / "out/models/codex_resume.log"
PYTHON = ROOT.parents[1] / ".venv/bin/python"


def main():
    lock = (RESTART / "watch.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return
    state_path = RESTART / "watch_status.json"
    count = 0
    if state_path.exists():
        count = json.loads(state_path.read_text()).get("restarts", 0)
    while True:
        status = json.loads(STATUS.read_text())
        state = status["state"]
        state_path.write_text(json.dumps({"state": "watching", "restarts": count,
                                         "updated_utc": datetime.now(timezone.utc).isoformat()}, indent=2))
        if state in ("complete", "budget_exhausted"):
            return
        if state == "failed":
            text = LOG.read_text(errors="replace")
            latest = text[text.rfind("\n=== "):]
            numerical_worker = any(marker in latest for marker in
                                   ("SIGSEGV", "is out of bounds", "neither increasing nor decreasing"))
            if count >= 3 or status.get("reason") != "model process failed; consult codex_resume.log" or not numerical_worker:
                state_path.write_text(json.dumps({"state": "stopped", "restarts": count,
                                                 "reason": "restart limit or error requiring inspection"}, indent=2))
                return
            count += 1
            with (RESTART / "AUTOMATIC_RESTARTS.jsonl").open("a") as record:
                record.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "attempt": count,
                                         "previous_status": status, "jobs": 4,
                                         "change": "none; resume identical seeded calculations from checkpoints"}) + "\n")
            time.sleep(5)
            subprocess.run([str(PYTHON), "-I", "scripts/resume_real.py"], cwd=ROOT, stdin=subprocess.DEVNULL)
        time.sleep(15)


if __name__ == "__main__":
    main()
