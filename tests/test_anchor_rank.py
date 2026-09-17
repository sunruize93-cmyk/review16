"""Behavioral checks for blinding, sampling, plans, and conservative reporting."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/review16/scripts/anchor_rank.py"
SPEC = importlib.util.spec_from_file_location("anchor_rank", SCRIPT)
ar = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ar)


class AnchorRankTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def put(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def fixture(self, count=4):
        papers = []
        for i in range(count):
            name = f"source-{i}.txt"
            (self.root / name).write_text(f"Anonymous full paper. Distinct method and result number {i}.", encoding="utf-8")
            papers.append({"id": f"original-{i}", "blinded_text_path": name,
                           "blinding_checked": True, "submission_version_verified": True,
                           "material_level": "fulltext", "human_scores": [1 if i % 2 == 0 else 5],
                           "provenance": f"https://example.invalid/submission/{i}"})
        corpus = {"schema": "review16.anchor-corpus.v1", "venue": "SYNTHETIC-VENUE", "year": 2026,
                  "track": "synthetic-track", "review_phase": "initial", "synthetic": True,
                  "score_scale": {"name": "synthetic-1-5", "min": 1, "max": 5, "higher_is_better": True},
                  "bands": [{"id": "low", "lower": 1, "upper": 3}, {"id": "high", "lower": 3, "upper": 5}],
                  "papers": papers}
        (self.root / "target.txt").write_text("Anonymous target method. This distinct technical text has no identity.", encoding="utf-8")
        target = {"schema": "review16.target.v1", "id": "original-target", "blinded_text_path": "target.txt",
                  "blinding_checked": True, "material_level": "fulltext", "synthetic": True}
        return self.put("corpus.json", corpus), self.put("target.json", target)

    def run_package(self, count=4, **kwargs):
        corpus, target = self.fixture(count)
        out = self.root / "run"
        result = ar.prepare(corpus, target, out, seed=100, **kwargs)
        return out, result

    def plan(self, out, all_pairs=True):
        path = out / "public/plan.json"
        ar.plan_pairs(out / "public/manifest.json", path, neighbors=1, all_pairs=all_pairs, seed=222)
        return path, ar.read_json(path)

    def decisions(self, out, plan, relations=None, reviewer="R1", family="same-model"):
        mapping = ar.read_json(out / "private/mapping.json")
        target = next(p["anonymous_id"] for p in mapping["papers"] if p["is_target"])
        rows = []
        for pair in plan["comparisons"]:
            if target in (pair["left"], pair["right"]):
                anchor = pair["right"] if pair["left"] == target else pair["left"]
                rel = (relations or {}).get(anchor, "win")
                decision = rel if rel in ("tie", "abstain") else (
                    "left" if pair["left"] == (target if rel == "win" else anchor) else "right")
            else:
                decision = "tie"
            rows.append({"comparison_id": pair["comparison_id"], "reviewer_id": reviewer,
                         "model_family": family, "decision": decision,
                         "recognized_paper": False,
                         "evidence": "SYNTHETIC TEST: method section and result table support the specified relation."})
        return target, rows

    def report(self, out, plan_path, rows, name="report.json"):
        decisions_path = self.put("decisions.json", {"schema": "review16.pair-decisions.v1", "decisions": rows})
        return ar.summarize(plan_path, decisions_path, out / "private/mapping.json", self.root / name)

    def test_shortfall_is_reported_and_no_replacement(self):
        out, result = self.run_package()
        self.assertEqual(result["sampled_anchors"], 4)
        self.assertEqual([b["shortfall"] for b in result["coverage"]], [8, 8])
        mapping = ar.read_json(out / "private/mapping.json")
        self.assertEqual(len({p["id"] for p in mapping["papers"]}), 5)
        self.assertIsNone(result["acceptance_probability"])

    def test_default_ten_per_band_and_boundary_means(self):
        corpus_path, target = self.fixture(30)
        corpus = ar.read_json(corpus_path)
        corpus["papers"][0]["human_scores"] = [1, 5]  # mean 3 belongs to high band
        self.put("corpus.json", corpus)
        result = ar.prepare(corpus_path, target, self.root / "run", seed=1)
        self.assertEqual([b["available"] for b in result["coverage"]], [14, 16])
        self.assertEqual([b["selected"] for b in result["coverage"]], [10, 10])

    def test_public_only_contains_anonymous_material(self):
        out, _ = self.run_package()
        manifest = ar.read_json(out / "public/manifest.json")
        self.assertEqual(set(manifest), {"schema", "papers"})
        for item in manifest["papers"]:
            self.assertEqual(set(item), {"anonymous_id", "text_path", "material_level"})
            self.assertTrue((out / "public" / item["text_path"]).is_file())
        public_json = json.dumps(manifest)
        for leak in ("original-", "SYNTHETIC-VENUE", "human_scores", "is_target", "example.invalid", "source-"):
            self.assertNotIn(leak, public_json)
        self.assertEqual((out / "private").stat().st_mode & 0o777, 0o700)
        self.assertEqual((out / "private/mapping.json").stat().st_mode & 0o777, 0o600)

    def test_no_output_overwrite_or_symlink_following(self):
        corpus, target = self.fixture()
        out = self.root / "existing"
        out.mkdir()
        with self.assertRaises(ar.ValidationError):
            ar.prepare(corpus, target, out)
        link = self.root / "link"
        link.symlink_to(self.root / "absent")
        with self.assertRaises(ar.ValidationError):
            ar.prepare(corpus, target, link)
        saved = self.put("saved.json", {"original": True})
        with self.assertRaises(FileExistsError):
            ar.write_new(saved, {"overwrite": True})
        self.assertEqual(ar.read_json(saved), {"original": True})

    def test_duplicate_json_keys_and_nonfinite_rejected(self):
        for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e999}'):
            path = self.root / "invalid.json"
            path.write_text(text, encoding="utf-8")
            with self.subTest(text=text), self.assertRaises(ar.ValidationError):
                ar.read_json(path)

    def test_invalid_scores_rejected(self):
        corpus_path, _ = self.fixture()
        baseline = ar.read_json(corpus_path)
        for bad in (0, 6, True, "3", None, float("inf"), float("nan")):
            corpus = copy.deepcopy(baseline)
            corpus["papers"][0]["human_scores"] = [bad]
            self.put("corpus.json", corpus)
            with self.subTest(bad=bad), self.assertRaises(ar.ValidationError):
                ar.load_corpus(corpus_path)

    def test_discrete_score_values_reject_in_range_illegal_scores(self):
        corpus_path, _ = self.fixture()
        corpus = ar.read_json(corpus_path)
        corpus["score_scale"]["values"] = [1, 3, 5]
        corpus["papers"][0]["human_scores"] = [1, 3]
        self.put("corpus.json", corpus)
        _, _, papers = ar.load_corpus(corpus_path)
        self.assertEqual(papers[0]["human_score_mean"], 2)
        corpus["papers"][0]["human_scores"] = [2]
        self.put("corpus.json", corpus)
        with self.assertRaisesRegex(ar.ValidationError, "not in score_scale.values"):
            ar.load_corpus(corpus_path)

    def test_discrete_scale_rejects_invalid_value_sets(self):
        corpus_path, _ = self.fixture()
        baseline = ar.read_json(corpus_path)
        for values in ([], [1, 1.0, 5], [1, True, 5], [1, 6], ["1", 5], None):
            corpus = copy.deepcopy(baseline)
            corpus["score_scale"]["values"] = values
            self.put("corpus.json", corpus)
            with self.subTest(values=values), self.assertRaises(ar.ValidationError):
                ar.load_corpus(corpus_path)

    def test_score_bands_cannot_overlap_or_leave_gaps(self):
        corpus_path, _ = self.fixture()
        baseline = ar.read_json(corpus_path)
        for lower in (2, 4):
            corpus = copy.deepcopy(baseline)
            corpus["bands"][1]["lower"] = lower
            self.put("corpus.json", corpus)
            with self.assertRaises(ar.ValidationError):
                ar.load_corpus(corpus_path)

    def test_submission_and_blinding_declarations_required(self):
        corpus_path, _ = self.fixture()
        baseline = ar.read_json(corpus_path)
        for field in ("submission_version_verified", "blinding_checked"):
            corpus = copy.deepcopy(baseline)
            corpus["papers"][0][field] = False
            self.put("corpus.json", corpus)
            with self.assertRaises(ar.ValidationError):
                ar.load_corpus(corpus_path)

    def test_abstracts_cannot_masquerade_as_fulltext_comparisons(self):
        corpus_path, target_path = self.fixture()
        target = ar.read_json(target_path)
        target["material_level"] = "abstract"
        self.put("target.json", target)
        with self.assertRaisesRegex(ar.ValidationError, "abstention"):
            ar.prepare(corpus_path, target_path, self.root / "run")

    def test_duplicate_anchor_or_target_rejected_even_with_whitespace(self):
        corpus_path, target_path = self.fixture()
        same = (self.root / "source-0.txt").read_text()
        (self.root / "target.txt").write_text(" \n" + same.replace(" ", "  ") + "\n")
        with self.assertRaisesRegex(ar.ValidationError, "duplicates"):
            ar.prepare(corpus_path, target_path, self.root / "run")
        (self.root / "source-1.txt").write_text(same)
        with self.assertRaisesRegex(ar.ValidationError, "duplicate"):
            ar.load_corpus(corpus_path)

    def test_plan_is_balanced_connected_and_reversed_for_many_sizes(self):
        for size in range(2, 15):
            with self.subTest(size=size):
                ids = [f"P{i:016x}" for i in range(size)]
                for paper in ids:
                    (self.root / (paper + ".txt")).write_text("Synthetic text " + paper)
                manifest = self.put(f"public-{size}.json", {"schema": "review16.blind-package.v1", "papers": [
                    {"anonymous_id": p, "text_path": p + ".txt", "material_level": "fulltext"} for p in ids]})
                plan_path = self.root / f"plan-{size}.json"
                ar.plan_pairs(manifest, plan_path, neighbors=2, seed=44)
                plan, by_id = ar.load_plan(plan_path)  # validates balance, connectivity, reverse
                directed = {(p["left"], p["right"]) for p in by_id.values()}
                self.assertTrue(all((b, a) in directed for a, b in directed))
                self.assertLessEqual(len(plan["comparisons"]), size*4)

    def test_sparse_win_does_not_imply_first_place(self):
        out, _ = self.run_package(count=6)
        plan_path, plan = self.plan(out, all_pairs=False)
        _, rows = self.decisions(out, plan)
        report = self.report(out, plan_path, rows)
        self.assertEqual(report["aggregate"]["observed_comparison"], {"win": 2, "tie": 0, "loss": 0, "uncertain": 4})
        self.assertEqual(report["aggregate"]["sample_anchor_rank"]["best"], 1)
        self.assertEqual(report["aggregate"]["sample_anchor_rank"]["worst"], 5)

    def test_ties_and_abstentions_survive_and_bound_rank(self):
        out, _ = self.run_package()
        plan_path, plan = self.plan(out)
        target, _ = self.decisions(out, plan)
        anchors = sorted(set(plan["anonymous_ids"])-{target})
        _, rows = self.decisions(out, plan, dict(zip(anchors, ["win", "loss", "tie", "abstain"])))
        report = self.report(out, plan_path, rows)
        aggregate = report["aggregate"]
        self.assertEqual(aggregate["observed_comparison"], {"win": 1, "tie": 1, "loss": 1, "uncertain": 1})
        self.assertEqual((aggregate["sample_anchor_rank"]["best"], aggregate["sample_anchor_rank"]["worst"]), (2, 4))
        self.assertIsNone(report["acceptance_probability"])

    def test_position_bias_becomes_reversal_conflict(self):
        out, _ = self.run_package()
        plan_path, plan = self.plan(out)
        target, rows = self.decisions(out, plan)
        target_cids = {c["comparison_id"] for c in plan["comparisons"] if target in (c["left"], c["right"])}
        for row in rows:
            if row["comparison_id"] in target_cids:
                row["decision"] = "left"
        report = self.report(out, plan_path, rows)
        self.assertEqual(report["aggregate"]["observed_comparison"]["uncertain"], 4)
        self.assertEqual(report["per_reviewer"]["R1"]["pair_diagnostics"]["reversal_conflict"], 4)

    def test_recognition_in_either_orientation_is_uncertain(self):
        out, _ = self.run_package()
        plan_path, plan = self.plan(out)
        target, rows = self.decisions(out, plan)
        target_cid = next(c["comparison_id"] for c in plan["comparisons"] if target == c["left"])
        next(row for row in rows if row["comparison_id"] == target_cid)["recognized_paper"] = True
        report = self.report(out, plan_path, rows)
        self.assertEqual(report["aggregate"]["observed_comparison"]["uncertain"], 1)
        self.assertEqual(report["aggregate"]["sample_anchor_rank"]["worst"], 2)
        self.assertEqual(report["per_reviewer"]["R1"]["pair_diagnostics"]["recognized"], 1)
        self.assertEqual(sum(d["status"] == "recognized" for d in report["reversal_diagnostics"]), 1)

    def test_recognition_declaration_is_required_and_boolean(self):
        out, _ = self.run_package()
        plan_path, plan = self.plan(out)
        _, rows = self.decisions(out, plan)
        _, by_id = ar.load_plan(plan_path)
        missing = dict(rows[0])
        missing.pop("recognized_paper")
        for invalid in (missing, dict(rows[0], recognized_paper=0), dict(rows[0], recognized_paper="false")):
            path = self.put("bad.json", {"schema": "review16.pair-decisions.v1", "decisions": [invalid]})
            with self.assertRaises(ar.ValidationError):
                ar.load_decisions(path, by_id)

    def test_sixteen_roles_remain_one_model_family(self):
        out, _ = self.run_package()
        plan_path, plan = self.plan(out)
        rows = []
        for i in range(16):
            _, result = self.decisions(out, plan, reviewer=f"R{i}")
            rows.extend(result)
        report = self.report(out, plan_path, rows)
        self.assertEqual(report["reviewer_count"], 16)
        self.assertEqual(report["model_family_count"], 1)
        self.assertIsNone(report["acceptance_probability"])
        self.assertNotIn("confidence_interval", report)

    def test_disagreement_between_roles_remains_uncertain(self):
        out, _ = self.run_package()
        plan_path, plan = self.plan(out)
        target, rows = self.decisions(out, plan, reviewer="optimist")
        relations = {a: "loss" for a in plan["anonymous_ids"] if a != target}
        _, second = self.decisions(out, plan, relations, reviewer="skeptic")
        report = self.report(out, plan_path, rows+second)
        self.assertEqual(report["aggregate"]["observed_comparison"]["uncertain"], 4)
        self.assertEqual(report["per_reviewer"]["optimist"]["sample_anchor_rank"]["worst"], 1)
        self.assertEqual(report["per_reviewer"]["skeptic"]["sample_anchor_rank"]["best"], 5)

    def test_missing_reverse_and_no_decisions_give_uncertainty(self):
        out, _ = self.run_package()
        plan_path, plan = self.plan(out)
        report = self.report(out, plan_path, [])
        self.assertEqual(report["aggregate"]["sample_anchor_rank"]["worst"], 5)
        self.assertEqual(report["model_family_count"], 0)
        target, rows = self.decisions(out, plan)
        target_cid = next(c["comparison_id"] for c in plan["comparisons"] if target == c["left"])
        rows = [r for r in rows if r["comparison_id"] != target_cid]
        report = self.report(out, plan_path, rows, name="incomplete.json")
        self.assertEqual(report["per_reviewer"]["R1"]["observed_comparison"]["uncertain"], 1)
        self.assertEqual(report["per_reviewer"]["R1"]["missing_comparison_count"], 1)
        self.assertEqual(report["aggregate"]["observed_comparison"]["uncertain"], 4)

    def test_undeclared_partial_plan_does_not_produce_narrow_rank(self):
        out, _ = self.run_package()
        plan_path, plan = self.plan(out)
        target, rows = self.decisions(out, plan)
        target_cids = {c["comparison_id"] for c in plan["comparisons"] if target in (c["left"], c["right"])}
        partial = [r for r in rows if r["comparison_id"] in target_cids]
        report = self.report(out, plan_path, partial)
        reviewer = report["per_reviewer"]["R1"]
        self.assertEqual(reviewer["observed_comparison"]["win"], 4)
        self.assertEqual(reviewer["sample_anchor_rank"]["worst"], 5)
        self.assertEqual(reviewer["rank_status"], "incomplete-plan-unconstrained")
        self.assertFalse(reviewer["plan_complete"])
        self.assertFalse(report["run_complete_for_observed_configurations"])
        self.assertEqual(report["aggregate"]["sample_anchor_rank"]["worst"], 5)

    def test_decisions_reject_unplanned_duplicate_or_changed_family(self):
        out, _ = self.run_package()
        plan_path, plan = self.plan(out)
        _, rows = self.decisions(out, plan)
        _, by_id = ar.load_plan(plan_path)
        invalid_sets = [rows+[rows[0]], [dict(rows[0], comparison_id="not-planned")],
                        [rows[0], dict(rows[1], model_family="other-model")],
                        [dict(rows[0], evidence=" ")], [dict(rows[0], decision="accept")]]
        for bad in invalid_sets:
            path = self.put("bad.json", {"schema": "review16.pair-decisions.v1", "decisions": bad})
            with self.assertRaises(ar.ValidationError):
                ar.load_decisions(path, by_id)

    def test_tampered_plan_without_reversal_rejected(self):
        out, _ = self.run_package()
        plan_path, plan = self.plan(out)
        plan["comparisons"].pop()
        plan_path.write_text(json.dumps(plan))
        with self.assertRaisesRegex(ar.ValidationError, "reverse"):
            ar.load_plan(plan_path)

    def test_private_mapping_must_match_plan(self):
        out, _ = self.run_package()
        plan_path, plan = self.plan(out)
        _, rows = self.decisions(out, plan)
        mapping = ar.read_json(out / "private/mapping.json")
        mapping["papers"][0]["anonymous_id"] = "Pwrong"
        (out / "private/mapping.json").write_text(json.dumps(mapping))
        with self.assertRaisesRegex(ar.ValidationError, "IDs differ"):
            self.report(out, plan_path, rows)

    def test_public_material_paths_cannot_escape_package(self):
        out, _ = self.run_package()
        manifest_path = out / "public/manifest.json"
        manifest = ar.read_json(manifest_path)
        manifest["papers"][0]["text_path"] = "../private/mapping.json"
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ar.ValidationError, "inside the public"):
            ar.load_public(manifest_path)


if __name__ == "__main__":
    unittest.main()
