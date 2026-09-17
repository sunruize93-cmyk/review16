"""Deterministic parser and bounded-fetch tests; never contact OpenReview."""

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/review16/scripts/fetch_openreview.py"
SPEC = importlib.util.spec_from_file_location("fetch_openreview", SCRIPT)
fetch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch)


class ParsePublicMetadataTests(unittest.TestCase):
    def test_raw_rating_zero_and_text_are_preserved_without_scale(self):
        note = {"content": {
            "rating": {"value": "6: Weak Accept", "readers": ["everyone"]},
            "confidence": {"value": 0},
            "technical_quality": {"value": "Good"},
            "summary": {"value": "We mention a rating in prose."},
        }}
        fields = {field["field_name"]: field for field in fetch.score_fields(note)}
        self.assertEqual(fields["rating"]["value"], "6: Weak Accept")
        self.assertEqual(fields["rating"]["raw_field"], note["content"]["rating"])
        self.assertEqual(fields["confidence"]["value"], 0)
        self.assertEqual(fields["technical_quality"]["value"], "Good")
        self.assertNotIn("summary", fields)
        self.assertIsNone(fields["rating"]["scale"])
        self.assertIsNone(fields["rating"]["phase"])

    def test_pdf_current_and_edit_are_candidates_not_verified_versions(self):
        submission = {"id": "example", "content": {"pdf": {"value": "/pdf/current.pdf"}}}
        edits = [{"id": "edit1", "note": {"content": {
            "pdf": {"value": "/pdf/old.pdf"}}}}]
        candidates = fetch.pdf_candidates(submission, edits)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["url"], "https://openreview.net/pdf/current.pdf")
        self.assertEqual(candidates[1]["edit_id"], "edit1")
        self.assertFalse(any(c["submission_version_verified"] for c in candidates))
        self.assertFalse(any(c["downloaded"] for c in candidates))

    def test_malformed_pdf_is_preserved_but_not_converted_to_url(self):
        submission = {"id": "x", "content": {"pdf": {"value": "javascript:alert(1)"}}}
        result = fetch.pdf_candidates(submission, [])
        self.assertIsNone(result[0]["url"])
        self.assertEqual(result[0]["value"], "javascript:alert(1)")

    def test_metadata_does_not_infer_venue_scale_or_review_phase(self):
        submission = {"id": "x", "content": {"venue": {"value": "ICLR 2025 Poster"}}}
        metadata = fetch.build_metadata("x", submission, [], [], {"status": "partial"})
        self.assertEqual(metadata["venue"]["venue"]["value"], "ICLR 2025 Poster")
        self.assertIsNone(metadata["score_scale"])
        self.assertIsNone(metadata["score_phase"])
        self.assertFalse(metadata["submission_version_verified"])
        self.assertFalse(metadata["review_score_history_fetched"])


class BoundedCollectionTests(unittest.TestCase):
    def test_maximum_pages_is_enforced_and_truncation_is_reported(self):
        calls = []

        def getter(path, params):
            calls.append(params)
            return {"ok": True, "response": {"notes": [{}] * fetch.PAGE_SIZE, "count": 5000}}

        result = fetch.fetch_collection("/notes", {"forum": "x"}, "notes", getter)
        self.assertEqual(len(calls), fetch.MAX_PAGES)
        self.assertEqual(len(result["items"]), fetch.MAX_PAGES * fetch.PAGE_SIZE)
        self.assertTrue(result["bounded_truncation"])
        self.assertFalse(result["complete"])

    def test_partial_failure_preserves_preceding_results(self):
        responses = iter([
            {"ok": True, "response": {"notes": [{}] * fetch.PAGE_SIZE}},
            {"ok": False, "error": "HTTP 403", "http_status": 403},
        ])
        result = fetch.fetch_collection("/notes", {}, "notes", lambda *_: next(responses))
        self.assertEqual(len(result["items"]), fetch.PAGE_SIZE)
        self.assertEqual(result["failure"], "HTTP 403")
        self.assertFalse(result["complete"])
        self.assertFalse(result["bounded_truncation"])

    def test_unexpected_response_is_failure_not_empty_success(self):
        result = fetch.fetch_collection("/notes", {}, "notes", lambda *_: {"ok": True, "response": {}})
        self.assertEqual(result["failure"], "invalid_notes_response")
        self.assertFalse(result["complete"])

    def test_short_final_page_completes_collection(self):
        result = fetch.fetch_collection("/notes", {}, "notes", lambda *_: {
            "ok": True, "response": {"notes": [{"id": "one"}], "count": 1}})
        self.assertTrue(result["complete"])
        self.assertFalse(result["bounded_truncation"])


if __name__ == "__main__":
    unittest.main()
