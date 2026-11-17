"""Synthetic regression tests for the v3 labelling safeguards; no reviewer outputs are read.
Run from Alex/: python3 -I feasibility/test_miami_labelling.py
"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from miami_label_check import FIELDS, check_call, check_records, date_range, read_jsonl
from miami_label_chunks import MAX_CHARS, RULES, build, build_fill, digest, fill_path, ordered_population, pack
from miami_label_merge import adjudication_list, by_pair, checked_inputs, cumulative_reviews, fill_identity, merge_record, pair_decision, qualification, reasons, verify_wave_reports
from miami_label_run import calls_made, check_command, command, cursor_prepare, fill_decision, frozen_files, move_to_grok, outside_denials, run_one, settings_for, usage_limited
from miami_label_run import record as record_outputs


def record():
    return {"case": "20210205907", "category": "EVENT", "category_passage": {"line": "T1", "quote": "fire damage"},
            "element": "", "condition": "", "deficiency_basis": "", "basis_passage": None,
            "assessment": "EVENT_DAMAGE", "assessment_passage": {"line": "T1", "quote": "fire damage"},
            "assessment_date": "", "assessment_text_date": "", "approval_wording": "", "pathway": "OTHER_AGENCY",
            "open_date": "2021-03-01", "earliest_defect_date": "", "defect_passage": {"line": "T1", "quote": "fire damage"},
            "defect_text_date": "", "defect_text_passage": None,
            "building": {"label": "", "type": "UNKNOWN", "stories": None}, "complex": "NO", "complex_passage": None,
            "related": [], "confidence": "high", "note": "Undated evidence."}


class Safeguards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="miami-label-test-")
        self.root = Path(self.tmp.name)
        (self.root / "20210205907.txt").write_text(
            "H1 case type: Unsafe Structure | open date: 2021-03-01 | closed: -\n"
            "T1 alleged violation: fire damage\n"
            "A1 2021-03-03 | inspection | fire damage\n"
            "A2 2021-04-01 | report | report disapproved\n"
            "A3 2021-04-02 | report | repairs required\n")
        self.r = record()

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, rows, expected=None, vocab=None):
        return check_records(rows, expected or [self.r["case"]], self.root, vocab)

    def test_schema_and_undated_event(self):
        self.assertEqual(set(self.r), FIELDS)
        self.assertEqual(self.check([self.r])[0]["failed"], 0)

    def test_invented_date_on_undated_line_fails(self):
        self.r["earliest_defect_date"] = self.r["open_date"]
        self.assertTrue(self.check([self.r])[0]["failed"])

    def test_dated_line_must_match(self):
        self.r["defect_passage"] = {"line": "A1", "quote": "fire damage"}
        self.assertTrue(self.check([self.r])[0]["failed"])
        self.r["earliest_defect_date"] = "2021-03-03"
        self.assertEqual(self.check([self.r])[0]["failed"], 0)

    def test_missing_duplicate_and_unexpected_cases_fail(self):
        self.assertTrue(self.check([])[0]["failed"])
        self.assertTrue(self.check([self.r, self.r])[0]["failed"])
        self.r["case"] = "../forbidden"
        self.assertTrue(self.check([self.r], ["20210205907"])[0]["failed"])

    def test_bad_quote_and_required_passage_fail(self):
        self.r["category_passage"]["quote"] = "invented damage"
        self.assertTrue(self.check([self.r])[0]["failed"])
        self.r["category_passage"] = None
        self.assertTrue(self.check([self.r])[0]["failed"])

    def test_invalid_and_partial_dates(self):
        for value in ("2023-02-29", "2021-13", "2021-00", "0000", "2021-1-1"):
            with self.assertRaises(ValueError):
                date_range(value, True)
        self.assertEqual(date_range("2024-02", True)[1].day, 29)

    def test_name_flag_scans_uppercase_single_word(self):
        self.r["note"] = "SYNTHETICPERSON"
        flags = self.check([self.r], vocab={"fire", "damage", "undated", "evidence"})[2]
        self.assertTrue(any("SYNTHETICPERSON" in f["words"] for f in flags))

    def test_duplicate_json_keys_and_nan_fail(self):
        path = self.root / "test.jsonl"
        for text in ('{"case":"a","case":"b"}', '{"value":NaN}'):
            path.write_text(text)
            with self.assertRaises(ValueError):
                read_jsonl([path])

    def test_comparison_complex_disagreement_is_adjudicated(self):
        a, b = record(), record()
        a["assessment"] = b["assessment"] = "ENG_PASS_FIRST"
        a["complex"], b["complex"] = "YES", "NO"
        self.assertIn("complex", reasons(a, b))

    def test_positive_text_date_and_episode_disagreement_are_adjudicated(self):
        a, b = record(), record()
        a["category"] = b["category"] = "STRUCT_DESCRIBED"
        a["defect_text_date"] = "2020"
        a["related"] = [{"case": "12345678901", "relation": "SAME_EPISODE", "line": "F1", "reason": "Continuation."}]
        self.assertEqual(set(reasons(a, b)), {"defect_text_date", "same_episode"})

    def test_stronger_basis_keeps_its_own_passage(self):
        a, b = record(), record()
        a["category"] = b["category"] = "DEFICIENCY_UNDESCRIBED"
        a["deficiency_basis"], b["deficiency_basis"] = "DOCUMENTARY", "FINDING"
        a["basis_passage"] = {"line": "A2", "quote": "report disapproved"}
        b["basis_passage"] = {"line": "A3", "quote": "repairs required"}
        merged = merge_record(a, b, "A")
        self.assertEqual(merged["deficiency_basis"], "FINDING")
        self.assertEqual(merged["basis_passage"], b["basis_passage"])
        self.assertIn("deficiency_basis", merged["field_disagreements"])

    def test_unilateral_same_episode_is_not_merged(self):
        a, b = record(), record()
        a["related"] = [{"case": "12345678901", "relation": "SAME_EPISODE", "line": "F1", "reason": "Continuation."}]
        merged = merge_record(a, b, "A")
        self.assertEqual(merged["related"][0]["relation"], "UNCLEAR")
        self.assertIn("related", merged["field_disagreements"])

    def test_q0_undefined_kappa_does_not_pass(self):
        rows = {str(i): record() for i in range(3)}
        report = qualification(rows, rows, rows, list(rows), [])
        self.assertFalse(report["qualified"])

    def test_population_membership_and_date_order(self):
        population, batch, stage1, groups = ordered_population()
        self.assertEqual((len(population), len(batch), len(stage1)), (6667, 250, 6417))
        self.assertEqual(set(batch) | set(stage1), set(population))
        self.assertFalse(set(batch) & set(stage1))
        self.assertEqual(groups, {"eligible": 5971, "before": 204, "after": 242})

    def test_pack_limits_and_oversized_single_case(self):
        for i, size in enumerate((80000, 80000, MAX_CHARS + 1)):
            (self.root / f"{i}.txt").write_text("x" * size)
        chunks = pack(["0", "1", "2"], self.root)
        self.assertEqual([len(c) for c in chunks], [1, 1, 1])

    def test_launcher_allows_only_output_edit_and_exact_checker(self):
        run = self.root.resolve()
        settings = settings_for(run)
        cmd = command("sonnet", run, settings, .1)
        self.assertEqual(cmd[cmd.index("--tools") + 1], "Read,Write,Bash")
        self.assertIn("--restricted", cmd)
        self.assertIn("--safe-mode", cmd)
        self.assertNotIn("--add-dir", cmd)
        self.assertEqual(settings["permissions"]["allow"],
                         [f"Edit(/{run / 'output.jsonl'})", f"Bash({check_command(run)})"])
        self.assertNotIn(":*", json.dumps(settings))

    def write_call(self, output):
        call = self.root / "call"
        call.mkdir()
        (call / "call.json").write_text(json.dumps({"chunk": "c1", "cases": [self.r["case"]],
                                                    "dossiers": str(self.root), "output": str(output)}))
        (call / "output.jsonl").write_text(json.dumps(self.r) + "\n")
        return call

    def test_call_mode_reads_everything_from_manifest(self):
        call = self.write_call(self.root / "call" / "output.jsonl")
        self.assertEqual(check_call(call)[0]["failed"], 0)

    def test_call_mode_refuses_output_outside_folder(self):
        call = self.write_call(self.root / "elsewhere.jsonl")
        with self.assertRaises(ValueError):
            check_call(call)

    def test_denials_outside_folder_are_caught(self):
        run = self.root.resolve()
        def api(*denials):
            return {"permission_denials": [{"tool_name": t, "tool_input": i} for t, i in denials]}
        inside = api(("Write", {"file_path": str(run / "notes.txt")}),
                     ("Bash", {"command": f"cd {run} && {check_command(run)}"}))
        self.assertEqual(outside_denials(inside, run), [])
        for tool, data in (("Read", {"file_path": "/etc/passwd"}), ("Read", {"file_path": str(run / "../x")}),
                           ("Bash", {"command": "cat ../final.jsonl"}), ("Bash", {"command": "cat ~/x"}),
                           ("Bash", {"command": f"{check_command(run)}; cat /tmp/final.jsonl"})):
            self.assertEqual(outside_denials(api((tool, data)), run), [tool])

    def test_adjudicated_same_episode_is_preserved(self):
        a, b = record(), record()
        a["category"] = b["category"] = "STRUCT_DESCRIBED"
        a["related"] = [{"case": "12345678901", "relation": "SAME_EPISODE", "line": "F1", "reason": "Continuation."}]
        b["related"] = [{"case": "12345678901", "relation": "SEPARATE_EPISODE", "line": "F1", "reason": "New cycle."}]
        final = merge_record(a, b, "B", {"take": "A", "set": {}, "reason": "Same cycle confirmed."})
        self.assertEqual(final["related"], a["related"])
        self.assertNotIn("related", final["field_disagreements"])

    def test_multiple_missing_link_lines_are_all_checked(self):
        dossier = self.root / f"{self.r['case']}.txt"
        with dossier.open("a") as fh:
            fh.write("F- 12345678901 cited in the text, not in the bulk data\n"
                     "F- 12345678902 cited in the text, not in the bulk data\n")
        self.r["related"] = [{"case": cn, "relation": "UNCLEAR", "line": "F-", "reason": "No linked record."}
                             for cn in ("12345678901", "12345678902")]
        self.assertEqual(self.check([self.r])[0]["failed"], 0)
        self.r["related"].pop(0)
        self.assertTrue(self.check([self.r])[0]["failed"])

    def test_final_merge_keeps_wave_random_audits_required(self):
        ids = [str(i) for i in range(20)]
        a = {cn: dict(record(), category="STRUCT_DESCRIBED") for cn in ids}
        b = copy.deepcopy(a)
        why = adjudication_list(a, b, ids)
        self.assertEqual(len(why), 2)
        report = {"case_ids": ids, "guide_hashes": {}, "adjudications": why, "Q1": {"status": "pass"}}
        path = self.root / "wave.json"
        path.write_text(json.dumps(report))
        self.assertEqual(verify_wave_reports([path], a, b, ids, {}), set(why))
        report["adjudications"] = {}
        path.write_text(json.dumps(report))
        with self.assertRaises(ValueError):
            verify_wave_reports([path], a, b, ids, {})

    def test_later_wave_cannot_omit_cumulative_history(self):
        with patch("miami_label_chunks.ordered_population", return_value=({}, [], ["earlier"], {})):
            with self.assertRaises(ValueError):
                cumulative_reviews({}, {}, {}, {}, None, None, {"stage": "stage1", "wave": 2}, self.root, {})

    def test_model_alias_does_not_hide_a_changed_model(self):
        output = self.root / "output.jsonl"
        output.write_text(json.dumps(self.r) + "\n")
        import hashlib
        meta = {"reviewer": "A", "model": "sonnet", "guide_hashes": {}, "checked": True,
                "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "resolved_models": ["model-v2"]}
        output.with_suffix(".meta.json").write_text(json.dumps(meta))
        with self.assertRaises(ValueError):
            checked_inputs([output], "A", {"guide_hashes": {}, "cases": [self.r["case"]]}, self.root,
                           {"A": "sonnet"}, {"A": ["model-v1"]})

    def candidate_batch(self):
        gold = {}
        for i in range(40):
            row = record()
            row["case"] = str(i)
            row["category"] = "STRUCT_DESCRIBED" if i % 4 == 0 else "ADMIN_ONLY"
            row["assessment"] = "ENG_PASS_FIRST" if i % 4 == 1 else "NONE"
            gold[str(i)] = row
        bad = copy.deepcopy(gold)
        for r in bad.values():
            r["category"], r["assessment"] = "ADMIN_ONLY", "NONE"
        return gold, bad

    def test_grok_is_A_when_it_passes(self):
        gold, _ = self.candidate_batch()
        q = qualification(gold, gold, gold, list(gold), [])
        self.assertEqual(q["selected_A"], "grok")
        self.assertEqual(q["models"], {"A": "grok-4.7", "B": "sonnet"})

    def test_grok_failure_falls_back_to_two_sonnets(self):
        gold, bad = self.candidate_batch()
        q = qualification(bad, gold, gold, list(gold), [])
        self.assertEqual(q["selected_A"], "sonnet")
        self.assertEqual(q["models"]["A"], q["models"]["B"])
        self.assertEqual(q["base"], "B")

    def test_grok_pass_does_not_override_sonnet_failure(self):
        gold, bad = self.candidate_batch()
        q = qualification(gold, bad, gold, list(gold), [])
        self.assertFalse(q["qualified"])

    def test_composer_is_B_when_it_passes(self):
        gold, _ = self.candidate_batch()
        q = pair_decision(gold, gold, gold, list(gold), [])
        self.assertEqual((q["pair"], q["qualified"], q["fill_needed"]), ("grok-composer", True, False))
        self.assertEqual(q["models"], {"A": "grok-4.7", "B": "composer"})

    def test_composer_failure_falls_back_to_two_groks(self):
        gold, bad = self.candidate_batch()
        q = pair_decision(gold, bad, gold, list(gold), [])
        self.assertEqual((q["pair"], q["qualified"], q["fill_needed"], q["base"]), ("grok-grok", True, True, "B"))
        self.assertEqual(q["models"], {"A": "grok-4.7", "B": "grok-4.7"})

    def test_grok_failure_leaves_no_pair(self):
        gold, bad = self.candidate_batch()
        self.assertFalse(pair_decision(bad, gold, gold, list(gold), [])["qualified"])

    def test_haiku_candidate_pairs_like_composer(self):
        gold, bad = self.candidate_batch()
        q = pair_decision(gold, gold, gold, list(gold), [], "haiku")
        self.assertEqual((q["pair"], q["models"]), ("grok-haiku", {"A": "grok-4.7", "B": "claude-haiku-5-5"}))
        self.assertIn("grok_haiku", q["cross_model_agreement"])
        self.assertEqual(pair_decision(gold, bad, gold, list(gold), [], "haiku")["pair"], "grok-grok")
        with self.assertRaises(ValueError):
            pair_decision(gold, gold, gold, list(gold), [], "grok")
        q = pair_decision(gold, gold, gold, list(gold), [], "luna")
        self.assertEqual((q["pair"], q["models"]), ("grok-luna", {"A": "grok-4.7", "B": "gpt-6-luna"}))

    def test_chunk_stages_follow_the_revised_pair(self):
        cases = [self.r["case"], "20210205908", "20210205909"]
        for cn in cases[1:]:
            (self.root / f"{cn}.txt").write_text((self.root / f"{cases[0]}.txt").read_text())
        population = ({cn: {} for cn in cases}, list(cases), list(cases), {})
        def chunks(stage, wave, pair=None):
            index = build(stage, wave, self.root / "out" / f"{stage}-{pair}", dossiers=self.root, pair=pair)[1]
            return [(c["reviewer"], c["model_key"], Path(c["file"]).read_text()) for c in index["chunks"].values()]
        with patch("miami_label_chunks.ordered_population", return_value=population):
            stage0_b = [c for c in chunks("stage0", 0) if c[0] == "B"]
            self.assertEqual([c[2] for c in chunks("stage0-candidate", 0)], [c[2] for c in stage0_b])
            self.assertEqual({c[:2] for c in chunks("stage0-candidate", 0)}, {("B", "composer")})
            self.assertEqual([c[2] for c in chunks("stage0-haiku", 0)], [c[2] for c in stage0_b])
            self.assertEqual({c[:2] for c in chunks("stage0-haiku", 0)}, {("B", "haiku")})
            self.assertEqual({c[:2] for c in chunks("stage1", 1, "grok-haiku")}, {("A", "grok"), ("B", "haiku")})
            self.assertEqual([c[2] for c in chunks("stage0-luna", 0)], [c[2] for c in stage0_b])
            self.assertEqual({c[:2] for c in chunks("stage0-luna", 0)}, {("B", "luna")})
            self.assertEqual({c[:2] for c in chunks("stage1", 1, "grok-luna")}, {("A", "grok"), ("B", "luna")})
            self.assertEqual({c[:2] for c in chunks("stage0-fill", 1, "grok-grok")}, {("B", "grok")})
            self.assertEqual({c[:2] for c in chunks("stage1", 1, "grok-composer")}, {("A", "grok"), ("B", "composer")})
            self.assertEqual({c[:2] for c in chunks("stage1", 1, "grok-grok")}, {("A", "grok"), ("B", "grok")})
            for stage, wave, pair in (("stage1", 1, None), ("stage1", 1, "grok-sonnet"), ("stage0-fill", 1, "grok-composer"),
                                      ("stage0-candidate", 1, None)):
                with self.assertRaises(ValueError):
                    build(stage, wave, self.root / "refused", dossiers=self.root, pair=pair)

    def cursor_setup(self, approved=True):
        chunk_file = self.root / "chunks" / "chunk001.txt"
        chunk_file.parent.mkdir()
        chunk_file.write_text("=== CASE 20210205907\n" + (self.root / "20210205907.txt").read_text())
        chunk_id = "stage0_w000_A_chunk001"
        hashes = {name: digest(RULES / name) for name in ("PROTOCOL_v3.md", "REVIEWER_INSTRUCTIONS_v3.md")}
        index = {"guide_hashes": hashes, "cases": [self.r["case"]], "chunks": {chunk_id: {
            "cases": [self.r["case"]], "file": str(chunk_file), "sha256": digest(chunk_file), "reviewer": "A",
            "model_key": "grok", "characters": 1, "dossiers": str(self.root),
            "output": str(self.root / "calls" / chunk_id / "output.jsonl")}}}
        index_path = self.root / "index.json"
        index_path.write_text(json.dumps(index))
        freeze = self.root / "freeze.json"
        freeze.write_text(json.dumps({"approved": approved, "frozen_at": "2026-10-18",
                                      "files": {str(f): digest(f) for f in frozen_files()}}))
        workspace = self.root / "cursor"
        folder = Path(cursor_prepare(index_path, workspace)[chunk_id])
        return index, index_path, freeze, workspace, folder

    def test_cursor_workspace_holds_only_rules_and_chunk_folders(self):
        _, _, _, workspace, folder = self.cursor_setup()
        self.assertEqual(folder, workspace.resolve() / "A" / "chunk001")
        self.assertEqual(sorted(p.name for p in workspace.iterdir()),
                         ["A", "PROTOCOL_v3.md", "REVIEWER_INSTRUCTIONS_v3.md"])
        self.assertEqual(sorted(p.name for p in folder.iterdir()), ["call.json", "chunk.txt"])
        self.assertEqual(json.loads((folder / "call.json").read_text())["output"], str(folder / "output.jsonl"))
        (folder / "output.jsonl").write_text(json.dumps(self.r) + "\n")
        self.assertEqual(check_call(folder)[0]["failed"], 0)

    def test_record_freezes_a_checked_copy_the_merge_accepts(self):
        index, index_path, freeze, workspace, folder = self.cursor_setup()
        self.assertEqual(record_outputs(index_path, workspace, freeze)[0]["status"], "missing")
        (folder / "output.jsonl").write_text(json.dumps(self.r) + "\n")
        self.assertEqual(record_outputs(index_path, workspace, freeze)[0]["status"], "recorded")
        self.assertEqual(record_outputs(index_path, workspace, freeze)[0]["status"], "already_recorded")
        target = Path(index["chunks"]["stage0_w000_A_chunk001"]["output"])
        meta = json.loads(target.with_suffix(".meta.json").read_text())
        self.assertEqual((meta["model"], meta["resolved_models"]), ("grok-4.7", ["grok-4.7"]))
        values, _ = checked_inputs([target], "A", index, self.root, {"A": "grok-4.7"}, {"A": ["grok-4.7"]})
        self.assertEqual(list(values), [self.r["case"]])

    def test_record_refuses_failed_or_changed_inputs_and_unapproved_freeze(self):
        index, index_path, freeze, workspace, folder = self.cursor_setup()
        bad = dict(self.r, category_passage={"line": "T1", "quote": "not in the dossier"})
        (folder / "output.jsonl").write_text(json.dumps(bad) + "\n")
        self.assertEqual(record_outputs(index_path, workspace, freeze)[0]["status"], "check_failed")
        (folder / "output.jsonl").write_text(json.dumps(self.r) + "\n")
        (folder / "chunk.txt").write_text("edited")
        self.assertEqual(record_outputs(index_path, workspace, freeze)[0]["status"], "inputs_changed")
        self.assertFalse(Path(index["chunks"]["stage0_w000_A_chunk001"]["output"]).exists())
        unapproved = self.root / "unapproved.json"
        unapproved.write_text(json.dumps(dict(json.loads(freeze.read_text()), approved=False)))
        with self.assertRaises(ValueError):
            record_outputs(index_path, workspace, unapproved)

    def freeze_file(self):
        freeze = self.root / "freeze.json"
        freeze.write_text(json.dumps({"approved": True, "frozen_at": "2026-10-20",
                                      "files": {str(f): digest(f) for f in frozen_files()}}))
        return freeze

    def stage1_setup(self):
        """A two-case stage-1 wave: Grok A chunks for Cursor, Haiku B chunks for the Claude Code launcher."""
        out = self.root / "out"
        cases = [self.r["case"], "20210205908"]
        (self.root / f"{cases[1]}.txt").write_text((self.root / f"{cases[0]}.txt").read_text())
        hashes = {name: digest(RULES / name) for name in ("PROTOCOL_v3.md", "REVIEWER_INSTRUCTIONS_v3.md")}
        chunks = {}
        for role, key in (("A", "grok"), ("B", "haiku")):
            for n, cn in enumerate(cases if role == "A" else cases[::-1], 1):
                chunk_id = f"stage1_w001_{role}_chunk{n:03d}"
                path = out / "chunks" / role / f"chunk{n:03d}.txt"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"===== CASE {cn} =====\n" + (self.root / f"{cn}.txt").read_text())
                chunks[chunk_id] = {"cases": [cn], "file": str(path), "sha256": digest(path), "reviewer": role,
                                    "model_key": key, "characters": 1, "dossiers": str(self.root),
                                    "output": str(out / "calls" / chunk_id / "output.jsonl")}
        index = {"stage": "stage1", "wave": 1, "cases": cases, "guide_hashes": hashes, "chunks": chunks}
        index_path = out / "indices" / "stage1_wave001.json"
        index_path.parent.mkdir(parents=True)
        index_path.write_text(json.dumps(index))
        return index, index_path, out

    def test_usage_limit_is_told_apart_from_other_failures(self):
        self.assertTrue(usage_limited({"is_error": True, "api_error_status": 429, "result": ""}))
        self.assertTrue(usage_limited({"is_error": True, "result": "You've hit your session limit \u00b7 resets 6pm"}))
        self.assertTrue(usage_limited(None, "Claude AI usage limit reached|1760000000"))
        self.assertFalse(usage_limited({"is_error": True, "subtype": "error_max_budget_usd", "result": "Budget limit reached ($2)"}))
        self.assertFalse(usage_limited({"is_error": False, "result": "the dossier mentions a rate limit"}))
        self.assertFalse(usage_limited({"is_error": True, "result": "API Error: 500"}))

    def test_only_a_limit_or_exhausted_retries_move_chunks(self):
        results = [{"chunk": "b1", "status": "check_failed"}, {"chunk": "b2", "status": "not_started"}]
        limit = results + [{"chunk": "b3", "status": "usage_limit", "log": "x"}]
        self.assertIsNone(fill_decision(["b1", "b2"], results, {"b1": 1, "b2": 0}))
        self.assertIsNone(fill_decision([], limit, {}))
        self.assertEqual(fill_decision(["b1", "b2", "b3"], limit, {"b1": 1, "b2": 0, "b3": 1})[0], "usage_limit")
        self.assertEqual(fill_decision(["b1"], results, {"b1": 3}), ("retry_exhausted", {"calls": {"b1": 3}}))
        self.assertIsNone(fill_decision(["b1", "b2"], results, {"b1": 3, "b2": 2}))

    def test_cursor_workspace_and_record_skip_claude_code_chunks(self):
        _, index_path, out = self.stage1_setup()
        workspace = out / "cursor" / "stage1_w001"
        folders = cursor_prepare(index_path, workspace)
        self.assertEqual(sorted(folders), ["stage1_w001_A_chunk001", "stage1_w001_A_chunk002"])
        self.assertEqual(sorted(p.name for p in workspace.iterdir()), ["A", "PROTOCOL_v3.md", "REVIEWER_INSTRUCTIONS_v3.md"])
        self.assertEqual({r["chunk"] for r in record_outputs(index_path, workspace, self.freeze_file())}, set(folders))

    def test_launcher_runs_only_claude_code_chunks_and_stops_after_three_calls(self):
        index, index_path, out = self.stage1_setup()
        freeze = self.freeze_file()
        with self.assertRaises(ValueError):
            run_one(index_path, "stage1_w001_A_chunk001", freeze)
        stop = __import__("threading").Event()
        stop.set()
        self.assertEqual(run_one(index_path, "stage1_w001_B_chunk001", freeze, stop=stop)["status"], "not_started")
        logs = out / "logs"
        logs.mkdir()
        for i in range(3):
            (logs / f"stage1_w001_B_chunk001_{i:08d}-0000-0000-0000-000000000000.json").write_text("{}")
        (logs / "stage1_w001_B_chunk001_00000000-0000-0000-0000-000000000000.check.json").write_text("{}")
        self.assertEqual((calls_made(index, "stage1_w001_B_chunk001"), calls_made(index, "stage1_w001_B_chunk002")), (3, 0))
        self.assertEqual(run_one(index_path, "stage1_w001_B_chunk001", freeze)["status"], "retry_exhausted")

    def test_unfinished_haiku_chunks_move_unchanged_to_grok(self):
        index, index_path, out = self.stage1_setup()
        for chunk_ids, reason in ((["stage1_w001_A_chunk001"], "usage_limit"), (["stage1_w001_B_chunk002"], "content"), ([], "usage_limit")):
            with self.assertRaises(ValueError):
                build_fill(index_path, chunk_ids, reason, {})
        moved = move_to_grok(index_path, "usage_limit", {"limit_calls": [], "unchecked": ["stage1_w001_B_chunk002"]})
        self.assertEqual((moved["chunks"], moved["cases"], moved["fill_index"]), (1, 1, str(fill_path(index_path))))
        self.assertEqual(move_to_grok(index_path)["fill_index"], moved["fill_index"])  # once per wave; re-entry only prepares
        with self.assertRaises(ValueError):
            build_fill(index_path, ["stage1_w001_B_chunk001", "stage1_w001_B_chunk002"], "usage_limit", {})
        fill = json.loads(fill_path(index_path).read_text())
        source, grok = index["chunks"]["stage1_w001_B_chunk002"], fill["chunks"]["stage1-fill_w001_B_chunk002"]
        self.assertEqual([grok[k] for k in ("file", "sha256", "cases", "reviewer")], [source[k] for k in ("file", "sha256", "cases", "reviewer")])
        self.assertEqual((grok["model_key"], grok["fill_of"]["chunk"]), ("grok", "stage1_w001_B_chunk002"))
        workspace = Path(moved["workspace"])
        self.assertEqual(sorted(p.name for p in workspace.iterdir()), ["B", "PROTOCOL_v3.md", "REVIEWER_INSTRUCTIONS_v3.md"])
        (workspace / "B" / "chunk002" / "output.jsonl").write_text(json.dumps(dict(self.r, case=source["cases"][0])) + "\n")
        self.assertEqual([r["status"] for r in record_outputs(fill_path(index_path), workspace, self.freeze_file())], ["recorded"])
        self.assertEqual(json.loads(Path(grok["output"]).with_suffix(".meta.json").read_text())["fill_of"], grok["fill_of"])

    def test_merge_accepts_grok_B_only_for_moved_chunks(self):
        index, index_path, out = self.stage1_setup()
        move_to_grok(index_path, "usage_limit", {"limit_calls": [], "unchecked": ["stage1_w001_B_chunk002"]})
        fill = json.loads(fill_path(index_path).read_text())
        grok = fill["chunks"]["stage1-fill_w001_B_chunk002"]
        folder = out / "cursor" / "stage1-fill_w001" / "B" / "chunk002"
        (folder / "output.jsonl").write_text(json.dumps(dict(self.r, case=grok["cases"][0])) + "\n")
        record_outputs(fill_path(index_path), out / "cursor" / "stage1-fill_w001", self.freeze_file())
        haiku = index["chunks"]["stage1_w001_B_chunk001"]
        haiku_out = Path(haiku["output"])
        haiku_out.parent.mkdir(parents=True)
        haiku_out.write_text(json.dumps(dict(self.r, case=haiku["cases"][0])) + "\n")
        haiku_out.with_suffix(".meta.json").write_text(json.dumps({
            "reviewer": "B", "model": "claude-haiku-5-5", "resolved_models": ["claude-haiku-5-5"], "checked": True,
            "guide_hashes": index["guide_hashes"], "output_sha256": digest(haiku_out), "chunk_sha256": haiku["sha256"],
            "cases": haiku["cases"], "call_id": "x"}))
        pair = {"pair": "grok-haiku", "selected_B": "haiku", "models": {"A": "grok-4.7", "B": "claude-haiku-5-5"},
                "resolved_models": {"A": ["grok-4.7"], "B": ["claude-haiku-5-5"]}}
        identity = fill_identity(pair, index, index_path)
        paths = [haiku_out, Path(grok["output"])]
        values, provenance = checked_inputs(paths, "B", index, self.root, pair["models"], pair["resolved_models"], identity)
        self.assertEqual(set(values), set(index["cases"]))
        self.assertEqual(["fill_of" in provenance[c] for c in (haiku["cases"][0], grok["cases"][0])], [False, True])
        groups = by_pair(values, values, provenance, pair)
        self.assertEqual({k: v["cases"] for k, v in groups.items()}, {"grok-grok": 1, "grok-haiku": 1})
        for wrong in (None, dict(identity, index_sha256="another wave"), dict(identity, model="claude-haiku-5-5")):
            with self.assertRaises(ValueError):
                checked_inputs(paths, "B", index, self.root, pair["models"], pair["resolved_models"], wrong)
        with self.assertRaises(ValueError):
            checked_inputs([Path(grok["output"])], "A", dict(index, cases=grok["cases"]), self.root, None, None, identity)
        self.assertIsNone(fill_identity(dict(pair, selected_B="grok"), index, index_path))
        meta_path = Path(grok["output"]).with_suffix(".meta.json")
        meta = json.loads(meta_path.read_text())
        del meta["fill_of"]
        meta_path.write_text(json.dumps(meta))
        with self.assertRaises(ValueError):
            checked_inputs(paths, "B", index, self.root, pair["models"], pair["resolved_models"], identity)


if __name__ == "__main__":
    unittest.main()
