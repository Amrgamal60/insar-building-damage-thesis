"""Prepare reviewer workspaces, record finished reviews, or run isolated Claude reviewer calls.

Cursor (the method in use): python3 -I feasibility/miami_label_run.py --index PRIVATE_INDEX
  --cursor-prepare PRIVATE_WORKSPACE writes the rule copies plus A/chunkNNN and B/chunkNNN folders
  (chunk.txt, call.json). After the freeze: --index PRIVATE_INDEX --freeze PRIVATE_FREEZE.json
  --record PRIVATE_WORKSPACE checks every finished output against the index, copies it to its
  private calls/<chunk_id>/output.jsonl and writes its .meta.json. Only recorded outputs are merged.
The same workspace and --record serve a reviewer the user runs in the Codex CLI (Luna, 2026-10-20).
Workspaces hold only the chunks of models the user runs (Cursor, Codex); Claude Code chunks run here:
Claude launcher (Haiku, B in stage 1): --index PRIVATE_INDEX --prepare, then --freeze PRIVATE_FREEZE.json
  [--chunk ID | --all] [--workers 3] [--retry].
Stage 1 (revision 2026-10-20b): when a call stops on the Claude usage limit, no new call starts, and every B chunk
of the wave not yet checked moves unchanged to a second Grok: a stage1-fill index and its Cursor workspace are
written, and the wave is never run in Claude Code again. A chunk that fails three calls moves the same way once
no other chunk of the wave is left. --retry sets a failed output aside privately before a new call.
Each call gets its own private folder (rule copies, chunk.txt, call.json, output.jsonl). The
--restricted --safe-mode Claude instance has only Read, Write and Bash: reads are confined to that
folder, the one write allowed is its output.jsonl (an Edit rule), and the one command allowed is the
exact checker command for that folder. Any denied attempt outside the folder fails the chunk.
--probe NEW_PRIVATE_DIR [--probe-model haiku|sonnet] tests this on synthetic files, never case data.
Raw API logs, output, possible name flags and provenance stay outside the project.
"""
import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from miami_label_check import check_records, private_output, read_jsonl, vocabulary
from miami_label_chunks import RULES, build_fill, digest, fill_path, model_pins, provider, write_once

CHECKER = Path(__file__).resolve().with_name("miami_label_check.py")
RUNNERS = {"cursor": "Cursor", "codex": "the Codex CLI"}  # where the user runs reviewers for --record
MAX_CALLS = 3
# The Claude CLI ends a call at the plan's limit with HTTP 429 or "You've hit your ... limit". The per-call
# --max-budget-usd stop ("Budget limit reached") is not a usage limit. A reviewer's own reply is never scanned.
LIMIT_TEXT = re.compile(r"you.ve hit your|usage limit|rate.limit", re.IGNORECASE)


def check_command(run):
    return f"python3 -I {CHECKER} --call {Path(run).resolve()}"


def command(model, run, settings, budget):
    return ["claude", "-p", "--model", model, "--restricted", "--safe-mode", "--tools", "Read,Write,Bash",
            "--setting-sources", "", "--settings", json.dumps(settings), "--strict-mcp-config",
            "--permission-mode", "dontAsk", "--no-session-persistence", "--output-format", "json",
            "--max-budget-usd", str(budget)]


def settings_for(run):
    # Absolute paths in rules start with //. A Write(...) rule grants no write (tested 2026-10-18): use Edit.
    # The Bash rule is exact (no :*): extra arguments, another folder, redirects and compound commands are refused.
    run = Path(run).resolve()
    return {"permissions": {"allow": [f"Edit(/{run / 'output.jsonl'})", f"Bash({check_command(run)})"],
                            "defaultMode": "dontAsk"}}


def outside_denials(api, run):
    """Denied attempts aimed outside the call folder (the checker script itself excepted)."""
    run = Path(run).resolve()
    def inside(path):
        path = (run / path).resolve()
        return path == CHECKER or path == run or run in path.parents
    found = []
    for denial in api.get("permission_denials") or []:
        tool, data = denial.get("tool_name"), denial.get("tool_input") or {}
        if tool == "Bash":
            text = str(data.get("command", ""))
            paths = re.findall(r"(?<![\w.~])/[^\s\"';|&<>()`]+", text)
            if ".." in text or "~" in text or not all(inside(p) for p in paths):
                found.append(tool)
        elif not inside(str(data.get("file_path") or data.get("path") or "/")):
            found.append(tool)
    return found


def usage_limited(api, stderr=""):
    """True when a failed call ended on the Claude usage limit, so its chunk is not the reason."""
    if isinstance(api, dict) and api.get("api_error_status") == 429:
        return True
    text = str(api.get("result", "")) if isinstance(api, dict) and api.get("is_error") else ""
    return bool(LIMIT_TEXT.search(text + "\n" + stderr))


def is_checked(index, chunk_id):
    chunk = index["chunks"][chunk_id]
    output = private_output(chunk["output"])
    meta_path = output.with_suffix(".meta.json")
    if not (output.exists() and meta_path.exists()):
        return False
    meta = json.loads(meta_path.read_text())
    summary, _, _ = check_records(read_jsonl([output]), chunk["cases"], chunk["dossiers"])
    return bool(meta.get("checked") and meta.get("output_sha256") == digest(output) and not summary["failed"]
                and meta["guide_hashes"] == index["guide_hashes"] and meta["chunk_sha256"] == chunk["sha256"]
                and meta["model"] == model_pins()[chunk["model_key"]] and meta["reviewer"] == chunk["reviewer"])


def calls_made(index, chunk_id):
    """Claude calls started for a chunk: one private API log each."""
    logs = private_output(index["chunks"][chunk_id]["output"]).parent.parent.parent / "logs"
    name = re.compile(re.escape(chunk_id) + r"_[0-9a-f-]{36}\.json")
    return sum(bool(name.fullmatch(p.name)) for p in logs.glob(f"{chunk_id}_*.json")) if logs.exists() else 0


def fill_decision(unchecked, results, calls):
    """Which reason moves the wave's unfinished Claude Code chunks to Grok; None while Haiku keeps them."""
    if not unchecked:
        return None
    limits = [r for r in results if r.get("status") == "usage_limit"]
    if limits:
        return "usage_limit", {"limit_calls": sorted(r["log"] for r in limits),
                               "statuses": {r["chunk"]: r["status"] for r in results if "chunk" in r}}
    if all(calls[cn] >= MAX_CALLS for cn in unchecked):
        return "retry_exhausted", {"calls": {cn: calls[cn] for cn in unchecked}}
    return None


def move_to_grok(index_path, reason=None, evidence=None):
    """Write the wave's stage1-fill index once (if a reason is given) and its Cursor workspace."""
    target = fill_path(index_path)
    if not target.exists():
        if reason is None:
            raise ValueError("no reason to move this wave to Grok")
        evidence = dict(evidence, detected_at=datetime.now(timezone.utc).isoformat())
        unchecked = evidence.pop("unchecked")
        build_fill(index_path, unchecked, reason, evidence)
    fill = json.loads(target.read_text())
    workspace = private_output(target).parent.parent / "cursor" / f"stage1-fill_w{fill['wave']:03d}"
    folders = cursor_prepare(target, workspace)
    return {"status": "moved_to_grok", "reason": fill["fill_of"]["reason"], "chunks": len(folders),
            "cases": len(fill["cases"]), "fill_index": str(target), "workspace": str(workspace)}


def manifest(chunk_id, chunk, output):
    return json.dumps({"chunk": chunk_id, "cases": chunk["cases"], "dossiers": chunk["dossiers"],
                       "output": str(output)}, indent=2) + "\n"


def prepare(index_path, chunk_id):
    index = json.loads(Path(index_path).read_text())
    chunk = index["chunks"][chunk_id]
    if digest(chunk["file"]) != chunk["sha256"]:
        raise ValueError("chunk hash changed")
    output = private_output(chunk["output"])
    if output.name != "output.jsonl":
        raise ValueError("a call's output must be its folder's output.jsonl")
    run = output.parent
    for name, expected in index["guide_hashes"].items():
        if digest(RULES / name) != expected:
            raise ValueError("guide changed after chunk preparation")
        write_once(run / name, (RULES / name).read_text())
    write_once(run / "chunk.txt", Path(chunk["file"]).read_text())
    write_once(run / "call.json", manifest(chunk_id, chunk, output))
    prompt = f"""You are independent reviewer {chunk['reviewer']} of Miami-Dade Unsafe Structure case records.
Work only from PROTOCOL_v3.md, REVIEWER_INSTRUCTIONS_v3.md and chunk.txt in {run}, and your own output.jsonl.
1. Read both rule files and the ENTIRE chunk; use Read offsets if necessary. There are {len(chunk['cases'])} cases.
2. Write one complete JSON Lines record for every case, in chunk order, once each, in ONE Write call to {output}.
   Every schema field must be present. Quotes must be exact, contiguous, at most 300 characters and contain no names.
3. Check it by running exactly this command, with nothing added or changed:
   {check_command(run)}
   Fix every FAIL: a missing or extra case, a quote that is not an exact contiguous piece of its cited line
   (without the line ID), a date that does not match its cited line, or a value outside the allowed set.
   For each FLAG, decide whether the word is a person's name; if it is, choose another quote or reword the note.
   Rewrite the whole file with Write and run the command again until no FAIL remains. At this step change only
   quotes, line IDs, dates that must match their line, and format, not your judgements.
4. Never write personal names anywhere in output, notes, or your reply. Do not read, write or run anything else:
   other files, tools and commands are refused, and every refused attempt is logged.
Reply under 150 words: the record count, category/assessment counts, the checker's summary line, and hard cases
(case number and a short reason); no names or copied case text.
"""
    return index, chunk, run, output, prompt


def frozen_files():
    required = [RULES / name for name in ("PROTOCOL_v3.md", "REVIEWER_INSTRUCTIONS_v3.md", "LABELLING_PLAN.md",
                                           "REVIEWER_MODELS.json")]
    required += [Path(__file__).with_name(name) for name in (
        "miami_label_chunks.py", "miami_label_check.py", "miami_label_merge.py", "miami_label_run.py",
        "miami_passage_check.py")]
    return [p.resolve() for p in required]


def verify_freeze(path):
    freeze = json.loads(Path(path).read_text())
    if not freeze.get("approved") or not freeze.get("frozen_at"):
        raise ValueError("approved dated freeze required")
    for filename, expected in freeze["files"].items():
        if digest(filename) != expected:
            raise ValueError("frozen artifact changed")
    if not all(str(p) in freeze["files"] for p in frozen_files()):
        raise ValueError("freeze does not cover all guides, scripts and isolation launcher")
    return freeze


def run_one(index_path, chunk_id, freeze_path, budget=2, stop=None, retry=False):
    if stop is not None and stop.is_set():
        return {"chunk": chunk_id, "status": "not_started"}
    verify_freeze(freeze_path)
    if provider(json.loads(Path(index_path).read_text())["chunks"][chunk_id]["model_key"]) != "claude-code":
        raise ValueError("the launcher runs Claude Code reviewers only")
    index, chunk, run, output, prompt = prepare(index_path, chunk_id)
    meta_path = output.with_suffix(".meta.json")
    if is_checked(index, chunk_id):
        return {"chunk": chunk_id, "status": "already_checked", "records": len(chunk["cases"])}
    if meta_path.exists() or (output.exists() and not retry):
        raise ValueError("existing incomplete/failed output: preserve privately and explicitly retry")
    calls = calls_made(index, chunk_id)
    if calls >= MAX_CALLS:
        return {"chunk": chunk_id, "status": "retry_exhausted", "calls": calls}
    if output.exists():
        # Set aside outside the call folder, so the next call cannot read the failed attempt.
        retired = run.parent / "retired" / chunk_id / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S}_output.jsonl"
        retired.parent.mkdir(parents=True, exist_ok=True)
        output.rename(retired)
    call_id = str(uuid.uuid4())
    logs = private_output(run.parent.parent / "logs")
    logs.mkdir(parents=True, exist_ok=True)
    prefix = logs / f"{chunk_id}_{call_id}"
    cmd = command(model_pins()[chunk["model_key"]], run, settings_for(run), budget)
    print(json.dumps({"chunk": chunk_id, "status": "started", "call": calls + 1}), flush=True)
    with prefix.with_suffix(".json").open("x") as out_log, prefix.with_suffix(".stderr").open("x") as err_log:
        result = subprocess.run(cmd, input=prompt, text=True, cwd=run, stdout=out_log, stderr=err_log, timeout=1800)
    returncode = result.returncode
    api_log = prefix.with_suffix(".json")
    stderr = prefix.with_suffix(".stderr").read_text(errors="replace")
    try:
        api = json.loads(api_log.read_text())
    except (ValueError, OSError):
        api = None
    api = api if isinstance(api, dict) else None
    if api is not None:
        outside = outside_denials(api, run)
        if outside:
            # Nothing outside the folder was read (it was refused), but the chunk is relabelled; keep its output privately.
            return {"chunk": chunk_id, "status": "isolation_attempt", "denied_tools": outside,
                    "cost_usd": api.get("total_cost_usd")}
    if (returncode or api is None or api.get("is_error")) and usage_limited(api, stderr):
        if stop is not None:
            stop.set()
        return {"chunk": chunk_id, "status": "usage_limit", "log": str(api_log)}
    if api is None:
        return {"chunk": chunk_id, "status": "invalid_api_log", "returncode": returncode}
    if returncode or api.get("is_error") or not output.exists():
        return {"chunk": chunk_id, "status": "call_failed", "returncode": returncode,
                "cost_usd": api.get("total_cost_usd")}
    summary, errors, flags = check_records(read_jsonl([output]), chunk["cases"], chunk["dossiers"], vocabulary())
    prefix.with_suffix(".check.json").write_text(json.dumps({"summary": summary, "errors": errors, "flags": flags}, indent=2) + "\n")
    if summary["failed"]:
        return {"chunk": chunk_id, "status": "check_failed", "summary": summary, "cost_usd": api.get("total_cost_usd")}
    meta = {"call_id": call_id, "reviewer": chunk["reviewer"], "model": model_pins()[chunk["model_key"]],
            "resolved_models": sorted(api.get("modelUsage", {})), "guide_hashes": index["guide_hashes"],
            "chunk_sha256": chunk["sha256"], "cases": chunk["cases"], "output_sha256": digest(output),
            "checked": True, "checked_at": datetime.now(timezone.utc).isoformat(),
            "permission_denials_inside_folder": len(api.get("permission_denials") or []),
            "usage": api.get("usage"), "total_cost_usd": api.get("total_cost_usd"), "log": str(api_log)}
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    return {"chunk": chunk_id, "status": "checked", "summary": summary, "cost_usd": api.get("total_cost_usd")}


def workspace_folder(root, chunk_id, chunk):
    return Path(root) / chunk["reviewer"] / f"chunk{chunk_id.rsplit('chunk', 1)[1]}"


def cursor_prepare(index_path, workspace):
    """One Cursor workspace: the two rule copies and one folder per chunk; nothing else."""
    index = json.loads(Path(index_path).read_text())
    root = private_output(workspace)
    for name, expected in index["guide_hashes"].items():
        if digest(RULES / name) != expected:
            raise ValueError("guide changed after chunk preparation")
        write_once(root / name, (RULES / name).read_text())
    folders = {}
    for chunk_id, chunk in index["chunks"].items():
        if provider(chunk["model_key"]) not in RUNNERS:
            continue  # Claude Code chunks run in the launcher, never in the user's workspace
        if digest(chunk["file"]) != chunk["sha256"]:
            raise ValueError("chunk hash changed")
        folder = workspace_folder(root, chunk_id, chunk)
        write_once(folder / "chunk.txt", Path(chunk["file"]).read_text())
        write_once(folder / "call.json", manifest(chunk_id, chunk, folder / "output.jsonl"))
        folders[chunk_id] = str(folder)
    return folders


def record(index_path, workspace, freeze_path):
    """Check each finished Cursor output against the index (not call.json), then freeze a private copy."""
    verify_freeze(freeze_path)
    index = json.loads(Path(index_path).read_text())
    root = private_output(workspace)
    if any(digest(root / name) != expected for name, expected in index["guide_hashes"].items()):
        raise ValueError("a rule copy in the workspace changed")
    results = []
    for chunk_id, chunk in index["chunks"].items():
        if provider(chunk["model_key"]) not in RUNNERS:
            continue
        folder = workspace_folder(root, chunk_id, chunk)
        source, target = folder / "output.jsonl", private_output(chunk["output"])
        meta_path = target.with_suffix(".meta.json")
        status = {"chunk": chunk_id}
        if meta_path.exists():
            results.append(dict(status, status="already_recorded"))
            continue
        if not source.exists():
            results.append(dict(status, status="missing"))
            continue
        if (digest(folder / "chunk.txt") != chunk["sha256"]
                or (folder / "call.json").read_text() != manifest(chunk_id, chunk, source)):
            results.append(dict(status, status="inputs_changed"))
            continue
        text = source.read_text()
        try:
            summary, errors, flags = check_records(read_jsonl([source]), chunk["cases"], chunk["dossiers"], vocabulary())
        except ValueError:
            results.append(dict(status, status="invalid_json"))
            continue
        if summary["failed"]:
            results.append(dict(status, status="check_failed", summary=summary))
            continue
        if target.exists() and target.read_text() != text:
            results.append(dict(status, status="changed_after_recording"))
            continue
        write_once(target, text)
        write_once(target.with_suffix(".check.json"),
                   json.dumps({"summary": summary, "errors": errors, "flags": flags}, indent=2) + "\n")
        model = model_pins()[chunk["model_key"]]
        meta = {"call_id": str(uuid.uuid4()), "reviewer": chunk["reviewer"], "model": model,
                "model_key": chunk["model_key"], "resolved_models": [model],
                "model_source": f"declared: chosen by the user in {RUNNERS[provider(chunk['model_key'])]}",
                "guide_hashes": index["guide_hashes"],
                "chunk_sha256": chunk["sha256"], "cases": chunk["cases"], "output_sha256": digest(target),
                "checked": True, "checked_at": datetime.now(timezone.utc).isoformat(),
                "recorded_from": str(source), "flagged_for_names": len(flags)}
        if "fill_of" in chunk:
            meta["fill_of"] = chunk["fill_of"]  # a second Grok took this B chunk from Haiku (stage1-fill)
        write_once(meta_path, json.dumps(meta, indent=2) + "\n")
        results.append(dict(status, status="recorded", summary=summary))
    return results


PROBE_CASE = "X0000000001"
PROBE_DOSSIER = ("H1 case type: Unsafe Structure | open date: 2021-03-01 | closed: -\n"
                 "T1 alleged violation: fire damage\n")
PROBE_RECORD = {
    "case": PROBE_CASE, "category": "EVENT", "category_passage": {"line": "T1", "quote": "fire damage"},
    "element": "", "condition": "", "deficiency_basis": "", "basis_passage": None,
    "assessment": "EVENT_DAMAGE", "assessment_passage": {"line": "T1", "quote": "fire damage"},
    "assessment_date": "", "assessment_text_date": "", "approval_wording": "", "pathway": "OTHER_AGENCY",
    "open_date": "2021-03-01", "earliest_defect_date": "", "defect_passage": {"line": "T1", "quote": "fire damage"},
    "defect_text_date": "", "defect_text_passage": None, "building": {"label": "", "type": "UNKNOWN", "stories": None},
    "complex": "NO", "complex_passage": None, "related": [], "confidence": "high", "note": "Synthetic probe."}


def probe(root, model="haiku"):
    """Denial test on the real call layout with synthetic files; a unique token marks every forbidden file."""
    root = private_output(root)
    root.mkdir(parents=True)  # must be new
    token = "FORBIDDEN_" + uuid.uuid4().hex
    run, sibling, dossiers, labels = root / "calls/probe_A", root / "calls/probe_B", root / "dossiers", root / "labels"
    for folder in (run, sibling, dossiers, labels):
        folder.mkdir(parents=True)
    (dossiers / f"{PROBE_CASE}.txt").write_text(PROBE_DOSSIER)
    chunk, output, manifest = run / "chunk.txt", run / "output.jsonl", run / "call.json"
    chunk.write_text(f"===== CASE {PROBE_CASE} =====\n{PROBE_DOSSIER}\nALLOWED_SYNTHETIC_MARKER\n")
    manifest.write_text(json.dumps({"chunk": "probe_A", "cases": [PROBE_CASE], "dossiers": str(dossiers),
                                    "output": str(output)}) + "\n")
    forbidden = {"sibling": sibling / "output.jsonl", "labels": labels / "final.jsonl", "parent": root / "parent.txt"}
    for path in forbidden.values():
        path.write_text(token + "\n")
    before = {p: p.read_text() for p in (manifest, *forbidden.values())}
    check, record = check_command(run), json.dumps(PROBE_RECORD)
    steps = [  # name, tool, key, value, expected to be refused
        ("read_own_chunk", "Read", "file_path", str(chunk), False),
        ("read_sibling_output", "Read", "file_path", str(forbidden["sibling"]), True),
        ("read_label_file", "Read", "file_path", str(forbidden["labels"]), True),
        ("read_parent_file", "Read", "file_path", str(forbidden["parent"]), True),
        ("write_own_output", "Write", "file_path", str(output), False),
        ("write_manifest", "Write", "file_path", str(manifest), True),
        ("write_other_own_file", "Write", "file_path", str(run / "notes.txt"), True),
        # A new file: writing the existing sibling output is stopped earlier by Write's read-first guard.
        ("write_sibling_folder", "Write", "file_path", str(sibling / "notes.txt"), True),
        ("exact_checker", "Bash", "command", check, False),
        ("cat_label_file", "Bash", "command", f"cat {forbidden['labels']}", True),
        ("checker_then_cat", "Bash", "command", f"{check}; cat {forbidden['labels']}", True),
        ("checker_and_cat", "Bash", "command", f"{check} && cat {forbidden['labels']}", True),
        ("checker_extra_argument", "Bash", "command", f"{check} {forbidden['labels']}", True),
        ("checker_other_call", "Bash", "command", check_command(sibling), True),
        ("checker_redirect", "Bash", "command", f"{check} > {run / 'x.txt'}", True),
    ]
    lines = []
    for i, (_, tool, _, value, _) in enumerate(steps, 1):
        if tool == "Read":
            lines.append(f"{i}. Read {value}")
        elif value == str(output):
            lines.append(f"{i}. Write to {value} exactly this one line: {record}")
        elif tool == "Write":
            lines.append(f"{i}. Write the text PROBE to {value}")
        else:
            lines.append(f"{i}. Bash, exactly: {value}")
    prompt = ("This is a permissions test on synthetic files, not real data. Make exactly these tool calls, one "
              "per step, in this order, with the exact paths and commands given. Continue after any refusal, and "
              "do not retry a refused step or try anything else.\n" + "\n".join(lines) +
              "\nThen reply with the step numbers that were refused.")
    cmd = command(model, run, settings_for(run), .50)
    cmd[cmd.index("json")] = "stream-json"
    cmd.append("--verbose")
    with (root / "probe.stream.jsonl").open("x") as log, (root / "probe.stderr").open("x") as err:
        result = subprocess.run(cmd, input=prompt, text=True, cwd=run, stdout=log, stderr=err, timeout=600)
    stream = (root / "probe.stream.jsonl").read_text()
    events = [json.loads(line) for line in stream.splitlines() if line.strip()]
    tools = next((e.get("tools") for e in events if e.get("type") == "system" and e.get("subtype") == "init"), None)
    final = next((e for e in reversed(events) if e.get("type") == "result"), {})
    denied = {d.get("tool_use_id") for d in final.get("permission_denials") or []}
    uses, results = [], {}
    for event in events:
        message = event.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "tool_use":
                uses.append(block)
            elif block.get("type") == "tool_result":
                results[block.get("tool_use_id")] = json.dumps(block.get("content"))
    checks = {}
    for name, tool, key, value, refused in steps:
        match = [u for u in uses if u.get("name") == tool and str(u.get("input", {}).get(key, "")).strip() == value]
        checks[name] = bool(match) and all((u.get("id") in denied) == refused for u in match)
    exact = [u for u in uses if u.get("name") == "Bash" and u.get("input", {}).get("command", "").strip() == check]
    checks.update({
        "only_read_write_bash": sorted(tools or []) == ["Bash", "Read", "Write"],
        "own_chunk_content_seen": any("ALLOWED_SYNTHETIC_MARKER" in results.get(u.get("id"), "") for u in uses),
        "checker_read_dossier_and_passed": any('\\"failed\\": 0' in results.get(u.get("id"), "") for u in exact),
        "output_written": output.exists() and json.loads(output.read_text()) == PROBE_RECORD,
        "forbidden_and_manifest_unchanged": all(p.read_text() == text for p, text in before.items()),
        "no_extra_files": not any(p.exists() for p in (run / "notes.txt", run / "x.txt", sibling / "notes.txt")),
        "token_never_seen": token not in stream,
    })
    report = {"model": model, "returncode": result.returncode, "cost_usd": final.get("total_cost_usd"),
              "denials": len(denied), "checks": checks, "passed": not result.returncode and all(checks.values())}
    (root / "probe_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if report["passed"] else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--freeze")
    ap.add_argument("--chunk")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--workers", type=int, choices=range(1, 6), default=1)
    ap.add_argument("--max-budget-usd", type=float, default=2)
    ap.add_argument("--retry", action="store_true", help="set failed outputs aside privately and call again")
    ap.add_argument("--probe")
    ap.add_argument("--probe-model", choices=("haiku", "sonnet"), default="haiku")
    ap.add_argument("--cursor-prepare", metavar="WORKSPACE")
    ap.add_argument("--record", metavar="WORKSPACE")
    a = ap.parse_args()
    try:
        if a.probe:
            return probe(a.probe, a.probe_model)
        if not a.index:
            raise ValueError("index required")
        if a.cursor_prepare:
            folders = cursor_prepare(a.index, a.cursor_prepare)
            print(json.dumps({"workspace": str(private_output(a.cursor_prepare)), "chunk_folders": len(folders)}))
            return 0
        if a.record:
            results = record(a.index, a.record, a.freeze)
            for result in results:
                print(json.dumps(result))
            return 0 if all(r["status"] in ("recorded", "already_recorded") for r in results) else 1
        index = json.loads(Path(a.index).read_text())
        claude = [cn for cn, c in index["chunks"].items() if provider(c["model_key"]) == "claude-code"]
        chunks = [a.chunk] if a.chunk else claude if a.all or a.prepare else []
        if not chunks or not set(chunks) <= set(claude):
            raise ValueError("choose --chunk, --all or --prepare, for Claude Code chunks only")
        if a.prepare:
            for cn in chunks:
                prepare(a.index, cn)
            print(json.dumps({"prepared": len(chunks), "reviewers_started": 0}))
            return 0
        verify_freeze(a.freeze)
        stage1 = index["stage"] == "stage1"
        if stage1 and fill_path(a.index).exists():
            print(json.dumps(move_to_grok(a.index)), flush=True)  # this wave's B already went to Grok
            return 3
        stop, results = threading.Event(), []
        with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
            futures = {pool.submit(run_one, a.index, cn, a.freeze, a.max_budget_usd, stop, a.retry): cn for cn in chunks}
            for f in concurrent.futures.as_completed(futures):
                try:
                    result = f.result()
                except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
                    result = {"chunk": futures[f], "status": "failed", "details": "inspect private per-call logs"}
                print(json.dumps(result), flush=True)
                results.append(result)
        if stage1:
            unchecked = [cn for cn in claude if not is_checked(index, cn)]
            decision = fill_decision(unchecked, results, {cn: calls_made(index, cn) for cn in unchecked})
            if decision:
                reason, evidence = decision
                print(json.dumps(move_to_grok(a.index, reason, dict(evidence, unchecked=unchecked))), flush=True)
                return 3
        return 1 if any(r["status"] not in ("checked", "already_checked") for r in results) else 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
        print("FAIL launcher configuration, freeze or isolation probe; inspect private logs", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
