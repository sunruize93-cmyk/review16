import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("peerread", Path(__file__).parents[1] / "skills/review16/scripts/fetch_peerread.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PeerReadTests(unittest.TestCase):
    def test_only_original_official_recommendations(self):
        base = {"OTHER_KEYS": "ICLR 2017 conference AnonReviewer2", "RECOMMENDATION": 5, "DATE": "20 Dec 2016"}
        payload = {"reviews": [base, {**base, "is_meta_review": True},
                    {**base, "OTHER_KEYS": "ICLR 2017 pcs"},
                    {"OTHER_KEYS": base["OTHER_KEYS"], "SOUNDNESS_CORRECTNESS": 5},
                    {**base, "RECOMMENDATION": True}, {**base, "RECOMMENDATION": 11}]}
        result = module.recommendations(payload)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["score"], 5)
        self.assertIsNone(result[0]["review_phase"])

    def test_preserves_multiple_entries_without_guessing_phase(self):
        reviews = [{"OTHER_KEYS": "ICLR 2017 conference AnonReviewer1", "RECOMMENDATION": v} for v in (4, 6)]
        self.assertEqual([x["score"] for x in module.recommendations({"reviews": reviews})], [4, 6])

    def test_empty(self):
        self.assertEqual(module.recommendations({}), [])


if __name__ == "__main__":
    unittest.main()
