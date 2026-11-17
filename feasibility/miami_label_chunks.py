"""Build reproducible private v3 reviewer chunks and a population manifest, blind to InSAR.

Run from Alex/: python3 -I feasibility/miami_label_chunks.py --stage stage0 --out PRIVATE_DIR
  [--stage stage1 --wave 1 --raw PRIVATE_RAW --pair grok-composer]
Use --stage all --plan-only to write the 6,667-case final coverage manifest without reading dossiers.
Stage0 reuses the fixed batch dossiers. Revision 2026-10-20: stage0-candidate gives Composer,
stage0-haiku Haiku and stage0-luna Luna the stage-0 B chunks of the 250 cases; stage0-fill (wave 1, --pair
grok-grok) adds a second Grok as B if no candidate passes Q0. Stage 1 runs the pair from the pair report.
Revision 2026-10-20b: stage1-fill gives a second Grok the unchanged B chunks of a stage-1 wave that Haiku did
not finish, after a Claude usage limit or three failed calls (built by miami_label_run.py, not from the CLI).
Chunks carry the reviewer's model key; the exact model name comes from REVIEWER_MODELS.json.
All output remains outside Alex. Existing differing manifests/chunks are refused, never overwritten.
"""
import argparse
import hashlib
import json
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from miami_full_fetch import population
from miami_label_check import private_output

PROJECT = Path(__file__).resolve().parents[1]
RULES = PROJECT / "feasibility/miami/audit/label_validation"
PRIVATE = PROJECT.with_name("Alex_private")
SEED, B_SEED, MAX_CHARS, MAX_CASES = 20261020, 20261022, 120000, 25
PAIRS = ("grok-composer", "grok-haiku", "grok-luna", "grok-grok")
CANDIDATES = {"stage0-candidate": "composer", "stage0-haiku": "haiku", "stage0-luna": "luna"}
FILL_REASONS = ("usage_limit", "retry_exhausted")


def model_pins():
    return {k: v["id"] for k, v in json.loads((RULES / "REVIEWER_MODELS.json").read_text())["models"].items()}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_once(path, text):
    path = private_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text() != text:
            raise ValueError("refusing to replace an existing different input or manifest")
    else:
        with path.open("x") as handle:
            handle.write(text)


def ordered_population():
    us = population()
    if len(us) != 6667:
        raise ValueError("population changed; review the plan before continuing")
    batch = json.loads((RULES / "sample.json").read_text())["cases"]
    dev = json.loads((RULES.parent / "label_sample/sample.json").read_text())["cases"]
    if len(batch) != 250 or len(set(batch)) != 250 or len(dev) != 100 or set(batch) & set(dev):
        raise ValueError("invalid or overlapping development/batch membership")
    if not set(batch + dev) <= set(us):
        raise ValueError("sample outside population")
    groups = {"eligible": [], "before": [], "after": []}
    for cn, row in sorted(us.items()):
        if cn in set(batch):
            continue
        day = datetime.fromtimestamp(row["OPEN_DATE"] / 1000, timezone.utc).date().isoformat()
        group = "before" if day < "2018-07-05" else "after" if day > "2026-05-08" else "eligible"
        groups[group].append(cn)
    rng = random.Random(SEED)
    for cases in groups.values():
        rng.shuffle(cases)
    if [len(groups[k]) for k in ("eligible", "before", "after")] != [5971, 204, 242]:
        raise ValueError("date groups changed; review the plan before continuing")
    batch = sorted(batch)
    rng.shuffle(batch)
    stage1 = sum((groups[k] for k in ("eligible", "before", "after")), [])
    return us, batch, stage1, {k: len(v) for k, v in groups.items()}


def pack(cases, dossiers, max_chars=MAX_CHARS, max_cases=MAX_CASES):
    chunks, current, length = [], [], 0
    for cn in cases:
        text = f"===== CASE {cn} =====\n" + (Path(dossiers) / f"{cn}.txt").read_text() + "\n"
        if current and (len(current) >= max_cases or length + len(text) > max_chars):
            chunks.append(current)
            current, length = [], 0
        current.append((cn, text))
        length += len(text)
    if current:
        chunks.append(current)
    return chunks


def build(stage, wave, out, raw=None, dossiers=None, pair=None, plan_only=False):
    out = private_output(out)
    us, batch, stage1, groups = ordered_population()
    if stage == "all":
        if not plan_only:
            raise ValueError("all is a coverage manifest; use --plan-only")
        cases, roles = sorted(us), []
    elif stage == "stage0":
        cases, roles = batch, ["A", "B"]
    elif stage in CANDIDATES:
        if wave != 0:
            raise ValueError("a candidate test reviews the stage-0 B chunks, wave 0")
        cases, roles = batch, ["B"]
    elif stage == "stage0-fill":
        if pair != "grok-grok" or wave != 1:
            raise ValueError("stage0-fill is for B/Grok after Composer fails, in wave 1")
        cases, roles = batch, ["B"]
    else:
        if not 1 <= wave <= 13:
            raise ValueError("stage1 wave must be 1..13")
        if pair not in PAIRS:
            raise ValueError("stage1 needs the qualified pair, grok-composer or grok-grok")
        cases, roles = stage1[(wave - 1) * 500:wave * 500], ["A", "B"]
    if dossiers is None:
        dossiers = PRIVATE / ("miami_dossiers_validation" if stage.startswith("stage0") else "miami_dossiers_full")
    dossiers = Path(dossiers).resolve()
    hashes = {name: digest(RULES / name) for name in ("PROTOCOL_v3.md", "REVIEWER_INSTRUCTIONS_v3.md")}
    index = {"schema": 1, "stage": stage, "wave": wave, "population_size": len(us), "cases": cases,
             "groups": groups, "seed": SEED, "b_seed": B_SEED, "guide_hashes": hashes, "chunks": {}}
    if not plan_only:
        missing = [cn for cn in cases if not (dossiers / f"{cn}.txt").exists()]
        if missing:
            if stage.startswith("stage0") or not raw:
                raise ValueError(f"{len(missing)} dossiers missing; supply --raw for stage1")
            subprocess.run([sys.executable, "-I", str(PROJECT / "feasibility/miami_case_dossier.py"),
                            "--raw", str(Path(raw).resolve()), "--out", str(dossiers), *missing], check=True)
        for slot in roles:
            role = slot[0]
            order = list(cases)
            if role == "B":
                random.Random(B_SEED).shuffle(order)
            # Stage0 qualified Grok and Sonnet; the candidate tests and the Grok fill review only B.
            if stage == "stage0":
                model_key = {"A": "grok", "B": "sonnet"}[slot]
            elif stage in CANDIDATES:
                model_key = CANDIDATES[stage]
            else:
                model_key = pair.split("-")[0 if role == "A" else 1]
            model_pins()[model_key]  # the key must exist in REVIEWER_MODELS.json
            for number, entries in enumerate(pack(order, dossiers), 1):
                chunk_id = f"{stage}_w{wave:03d}_{slot}_chunk{number:03d}"
                path = out / "chunks" / stage / f"wave{wave:03d}" / slot / f"chunk{number:03d}.txt"
                text = "".join(t for _, t in entries)
                write_once(path, text)
                index["chunks"][chunk_id] = {
                    "cases": [cn for cn, _ in entries], "file": str(path), "sha256": digest(path),
                    "reviewer": role, "model_key": model_key, "characters": len(text), "dossiers": str(dossiers),
                    "output": str(out / "calls" / chunk_id / "output.jsonl"),
                }
    target = out / "indices" / f"{stage}_wave{wave:03d}.json"
    write_once(target, json.dumps(index, indent=2) + "\n")
    return target, index


def provider(model_key):
    return json.loads((RULES / "REVIEWER_MODELS.json").read_text())["models"][model_key]["provider"]


def fill_path(index_path):
    index_path = Path(index_path).resolve()
    wave = json.loads(index_path.read_text())["wave"]
    return index_path.parent / f"stage1-fill_wave{wave:03d}.json"


def build_fill(index_path, chunk_ids, reason, evidence):
    """Give a second Grok the identical chunk files of stage-1 B chunks that Haiku did not finish (once per wave)."""
    index_path = private_output(index_path)
    index = json.loads(index_path.read_text())
    if index.get("stage") != "stage1" or reason not in FILL_REASONS or not chunk_ids:
        raise ValueError("only unfinished stage-1 Claude Code B chunks move to Grok, after a limit or exhausted retries")
    out = index_path.parent.parent
    fill = dict(index, stage="stage1-fill", chunks={}, fill_of={
        "index": str(index_path), "index_sha256": digest(index_path), "reason": reason, "evidence": evidence})
    moved = set()
    for chunk_id in sorted(chunk_ids):
        chunk = index["chunks"][chunk_id]
        if chunk["reviewer"] != "B" or provider(chunk["model_key"]) != "claude-code":
            raise ValueError("only Claude Code B chunks move to Grok")
        if digest(chunk["file"]) != chunk["sha256"]:
            raise ValueError("chunk hash changed")
        new_id = "stage1-fill" + chunk_id[len("stage1"):]
        fill["chunks"][new_id] = dict(chunk, model_key="grok", output=str(out / "calls" / new_id / "output.jsonl"),
                                      fill_of={"chunk": chunk_id, "index_sha256": digest(index_path)})
        moved.update(chunk["cases"])
    fill["cases"] = [cn for cn in index["cases"] if cn in moved]
    target = fill_path(index_path)
    write_once(target, json.dumps(fill, indent=2) + "\n")
    return target, fill


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", choices=("stage0", *CANDIDATES, "stage0-fill", "stage1", "all"), required=True)
    ap.add_argument("--wave", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--raw")
    ap.add_argument("--dossiers")
    ap.add_argument("--pair", choices=PAIRS, help="stage-1 pair from the pair report; grok-grok for stage0-fill")
    ap.add_argument("--plan-only", action="store_true")
    a = ap.parse_args()
    try:
        target, index = build(a.stage, a.wave, a.out, a.raw, a.dossiers, a.pair, a.plan_only)
        print(json.dumps({"index": str(target), "cases": len(index["cases"]), "chunks": len(index["chunks"]),
                          "groups": index["groups"], "guide_hashes": index["guide_hashes"]}))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"FAIL {type(exc).__name__}: cannot build immutable chunks; inspect inputs privately", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
