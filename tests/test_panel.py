"""Review-contract, isolation-plan and HTML-injection regression tests."""

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/review16/scripts/panel.py"
SPEC = importlib.util.spec_from_file_location("review16_panel", SCRIPT)
panel = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(panel)


def venue():
    return {
        "venue": "Synthetic test venue", "year": 2026, "track": "Fictional",
        "rubric_source": "synthetic://unit-test", "retrieved_at": "2026-09-17",
        "synthetic": True,
        "score_scale": {"values": [1, 3, 5, 8], "labels": {
            "1": "Fixture low", "3": "Fixture developing", "5": "Fixture promising", "8": "Fixture high"}},
    }


def review(identifier="dign"):
    result = panel.skeleton(identifier, True, "synthetic-test-run", "0" * 64)
    result.update(model="synthetic-fixture-no-model-called", model_family="synthetic-fixture",
                  status="assessed", score_before=5, score_after=5, domain_fit=3, confidence=3,
                  reading_coverage=["Synthetic section 1 inspected; no external sources"],
                  score_reason="A fixed fictional score to test the contract.")
    result["evidence"] = [{
        "id": "E1", "kind": "strength", "claim": "Fictional claim",
        "location": "Synthetic section 1", "observation": "A deliberately supplied toy premise.",
        "consequence": "Exercises the evidence renderer.", "severity": "info",
        "verification": "supported", "scope": "Synthetic test only", "remedy": "",
        "would_change_judgment": "This is not a real judgment.",
    }]
    return result


class VenueContractTests(unittest.TestCase):
    def test_non_contiguous_scale_is_allowed_but_intermediate_score_is_not(self):
        config = panel.validate_venue(venue())
        sample = review()
        sample["score_before"] = sample["score_after"] = 6
        with self.assertRaisesRegex(ValueError, "allowed venue score"):
            panel.validate_review(sample, config, {"dign"})

    def test_missing_label_duplicate_score_and_boolean_score_rejected(self):
        for mutation in ("missing_label", "duplicate", "boolean"):
            config = venue()
            if mutation == "missing_label":
                del config["score_scale"]["labels"]["8"]
            elif mutation == "duplicate":
                config["score_scale"]["values"].append(1.0)
            else:
                config["score_scale"]["values"][0] = True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                panel.validate_venue(config)

    def test_real_venue_needs_https_source(self):
        config = venue()
        config["synthetic"] = False
        with self.assertRaisesRegex(ValueError, "https"):
            panel.validate_venue(config)

    def test_nan_infinity_overflow_and_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            for payload in ('{"x": NaN}', '{"x": Infinity}', '{"x": 1e999}', '{"x":1,"x":2}'):
                path.write_text(payload)
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    panel.load_json(path)


class ReviewerContractTests(unittest.TestCase):
    def test_null_means_abstention_not_zero(self):
        sample = review()
        sample.update(status="out_of_scope", score_before=None, score_after=None,
                      confidence=None, domain_fit=0, evidence=[])
        panel.validate_review(sample, venue(), {"dign"})
        sample["score_after"] = 1
        with self.assertRaisesRegex(ValueError, "scores null"):
            panel.validate_review(sample, venue(), {"dign"})

    def test_assessed_requires_score_evidence_and_coverage(self):
        for field, value in (("score_before", None), ("evidence", []), ("reading_coverage", []),
                             ("model", None), ("confidence", True)):
            sample = review()
            sample[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                panel.validate_review(sample, venue(), {"dign"})

    def test_changed_score_requires_reason(self):
        sample = review()
        sample["score_after"] = 8
        with self.assertRaisesRegex(ValueError, "change_reason"):
            panel.validate_review(sample, venue(), {"dign"})

    def test_challenge_must_reference_known_persona_and_local_evidence(self):
        sample = review()
        sample["challenges"] = [{"from_persona": "eucr", "evidence_id": "missing", "type": "factual",
                                  "challenge": "Fixture challenge", "response": "Fixture response",
                                  "resolution": "unresolved"}]
        with self.assertRaisesRegex(ValueError, "reference evidence"):
            panel.validate_review(sample, venue(), {"dign", "eucr"})

    def test_unknown_persona_and_nonfinite_score_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown persona"):
            panel.validate_review(review("invented"), venue(), {"dign"})
        sample = review()
        sample["score_after"] = float("nan")
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            panel.validate_review(sample, venue(), {"dign"})


class PanelPreparationAndReportingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.paper = self.base / "paper.md"
        self.paper.write_text("A wholly synthetic manuscript fixture.")
        self.config = self.base / "venue.json"
        self.config.write_text(json.dumps(venue()))
        self.run = self.base / "run"
        self.manifest = panel.prepare(self.paper, self.config, self.run, 3)

    def bound_review(self, identifier="dign"):
        result = review(identifier)
        result.update(run_id=self.manifest["run_id"], manuscript_sha256=self.manifest["manuscript_sha256"])
        return result

    def test_preparation_creates_sixteen_tasks_but_zero_completed_reviews(self):
        self.assertEqual(len(self.manifest["tasks"]), 16)
        self.assertEqual(len(list((self.run / "tasks").glob("*.md"))), 16)
        self.assertEqual(len(list((self.run / "templates").glob("*.json"))), 16)
        self.assertEqual(list((self.run / "reviews").iterdir()), [])
        self.assertEqual(self.manifest["tasks"][-1]["batch"], 6)
        self.assertEqual(self.manifest["execution"], "not_performed_host_managed")
        self.assertFalse(self.manifest["isolation_verified"])
        prompt = (self.run / "tasks/dign.md").read_text()
        for phrase in ("untrusted research data", "Do not read other review files",
                       "Complete shared output contract", "same venue rubric", "sixteen independent experts"):
            self.assertIn(phrase, prompt)
        self.assertIn("theoretical paper to run benchmarks", prompt)

    def test_graph_is_complete_four_cube_and_invalid_neighbor_rejected(self):
        taxonomy = self.manifest["taxonomy"]
        self.assertEqual(len(taxonomy["challenge_pairs"]), 8)
        damaged = copy.deepcopy(taxonomy)
        damaged["personas"][0]["neighbors"][0] = "eucr"
        with self.assertRaisesRegex(ValueError, "Hamming"):
            panel.validate_personas(damaged)

    def test_partial_panel_is_explicit_without_imputation(self):
        panel.dump_json(self.run / "reviews/dign.json", self.bound_review())
        report = panel.collect_report(self.run, self.run / "reviews", demo=True)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(len(report["missing"]), 15)
        self.assertEqual(set(report["reviews"]), {"dign"})
        self.assertEqual(report["review_phase"], "initial_only")
        self.assertNotIn("average_score", report)
        self.assertNotIn("acceptance_probability", report)

    def test_synthetic_requires_demo_flag_and_duplicates_fail(self):
        panel.dump_json(self.run / "reviews/one.json", self.bound_review())
        with self.assertRaisesRegex(ValueError, "--demo"):
            panel.collect_report(self.run, self.run / "reviews")
        panel.dump_json(self.run / "reviews/two.json", self.bound_review())
        with self.assertRaisesRegex(ValueError, "Duplicate submitted persona"):
            panel.collect_report(self.run, self.run / "reviews", demo=True)

    def test_injected_script_markup_cannot_close_embedded_json(self):
        sample = self.bound_review()
        attack = '</script><script>alert("xss")</script><img src=x onerror=alert(1)>'
        sample["evidence"][0]["claim"] = attack
        panel.dump_json(self.run / "reviews/dign.json", sample)
        data = panel.collect_report(self.run, self.run / "reviews", demo=True)
        encoded = panel.safe_script_json(data)
        self.assertNotIn("</script>", encoded)
        self.assertNotIn("<img", encoded)
        self.assertEqual(json.loads(encoded)["reviews"]["dign"]["evidence"][0]["claim"], attack)
        out = self.base / "report.html"
        panel.render_report(data, out)
        html = out.read_text()
        self.assertNotIn(attack, html)
        self.assertIn("SYNTHETIC DEMONSTRATION", html)

    def test_existing_outputs_are_not_overwritten(self):
        with self.assertRaisesRegex(ValueError, "already exists"):
            panel.prepare(self.paper, self.config, self.run, 3)

    def test_acceptance_probability_anchor_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "acceptance probabilities"):
            panel.validate_anchors({"aggregate": {"acceptance_probability": 0.8}})

    def test_snapshot_stays_frozen_if_original_changes_and_tampering_fails(self):
        frozen = Path(self.manifest["manuscript"])
        self.assertNotEqual(frozen, self.paper)
        self.paper.write_text("Original author draft was revised after preparation.")
        panel.collect_report(self.run, self.run / "reviews", demo=True)
        frozen.chmod(0o644)
        frozen.write_text("Frozen snapshot was unexpectedly changed.")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            panel.collect_report(self.run, self.run / "reviews", demo=True)

    def test_reviews_from_another_run_cannot_be_attached_to_new_manuscript(self):
        panel.dump_json(self.run / "reviews/dign.json", self.bound_review())
        self.paper.write_text("An entirely different manuscript, same venue.")
        other = self.base / "another-run"
        panel.prepare(self.paper, self.config, other, 3)
        with self.assertRaisesRegex(ValueError, "run_id does not match"):
            panel.collect_report(other, self.run / "reviews", demo=True)

    def test_complete_role_coverage_does_not_imply_cross_examination(self):
        for persona in self.manifest["taxonomy"]["personas"]:
            panel.dump_json(self.run / "reviews" / (persona["id"] + ".json"), self.bound_review(persona["id"]))
        data = panel.collect_report(self.run, self.run / "reviews", demo=True)
        self.assertEqual(data["coverage_status"], "complete")
        self.assertEqual(data["review_phase"], "initial_only")
        self.assertEqual(data["cross_examination"]["completed_pair_records"], 0)

    def test_bilateral_records_required_for_all_eight_opposing_pairs(self):
        for persona in self.manifest["taxonomy"]["personas"]:
            sample = self.bound_review(persona["id"])
            sample["challenges"] = [{"from_persona": persona["opposite"], "evidence_id": "E1", "type": "scope",
                                     "challenge": "Synthetic question", "response": "Synthetic response",
                                     "resolution": "unresolved"}]
            panel.dump_json(self.run / "reviews" / (persona["id"] + ".json"), sample)
        data = panel.collect_report(self.run, self.run / "reviews", demo=True)
        self.assertEqual(data["review_phase"], "cross_examination_recorded")
        self.assertEqual(data["cross_examination"]["completed_pair_records"], 8)
        self.assertFalse(data["cross_examination"]["semantic_execution_verified"])

    def test_unknown_anchor_schema_is_not_rendered_as_a_rank(self):
        with self.assertRaisesRegex(ValueError, "Unsupported anchor schema"):
            panel.validate_anchors({"aggregate": {"acceptance_probability": None}})

    def test_anchor_uncertainty_and_shortfall_are_preserved(self):
        anchor = {
            "schema": "review16.rank-report.v1", "synthetic": True,
            "aggregate": {"sample_anchor_rank": {"best": 1, "worst": 5, "total_papers": 7, "sampled_anchors": 6},
                          "observed_comparison": {"win": 2, "tie": 0, "loss": 0, "uncertain": 4},
                          "acceptance_probability": None},
            "coverage": [{"band_id": "synthetic-band", "available": 6, "requested": 10, "selected": 6, "shortfall": 4}],
            "target_direct_anchor_pairs_planned": 2, "acceptance_probability": None,
        }
        validated = panel.validate_anchors(anchor)
        self.assertEqual(validated["aggregate"]["sample_anchor_rank"]["worst"], 5)
        self.assertEqual(validated["aggregate"]["observed_comparison"]["uncertain"], 4)
        malformed = copy.deepcopy(anchor)
        malformed["aggregate"]["sample_anchor_rank"]["worst"] = 1
        with self.assertRaisesRegex(ValueError, "direct comparisons"):
            panel.validate_anchors(malformed)


if __name__ == "__main__":
    unittest.main()
