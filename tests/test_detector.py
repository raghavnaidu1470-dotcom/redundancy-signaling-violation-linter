"""Unit tests for token-overlap redundancy candidates."""

import unittest

from src.redundancy.detector import detect_redundancy_violations


class RedundancyDetectorTest(unittest.TestCase):
    def test_returns_clear_token_overlap(self) -> None:
        candidates = detect_redundancy_violations(
            [
                {
                    "start_time": 0.0,
                    "end_time": 3.0,
                    "spoken_text": "Mitochondria produce energy",
                    "onscreen_text": "Mitochondria produce energy",
                }
            ]
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["score"], 1.0)

    def test_omits_non_overlapping_text(self) -> None:
        candidates = detect_redundancy_violations(
            [
                {
                    "start_time": 0.0,
                    "end_time": 3.0,
                    "spoken_text": "Mitochondria produce energy",
                    "onscreen_text": "Photosynthesis needs sunlight",
                }
            ]
        )

        self.assertEqual(candidates, [])

    def test_omits_records_with_empty_text(self) -> None:
        candidates = detect_redundancy_violations(
            [
                {
                    "start_time": 0.0,
                    "end_time": 3.0,
                    "spoken_text": "   ",
                    "onscreen_text": "Slide title",
                },
                {
                    "start_time": 3.0,
                    "end_time": 5.0,
                    "spoken_text": "Spoken explanation",
                    "onscreen_text": "",
                },
            ]
        )

        self.assertEqual(candidates, [])

    def test_respects_score_threshold(self) -> None:
        record = {
            "start_time": 0.0,
            "end_time": 3.0,
            "spoken_text": "Plants need water sunlight",
            "onscreen_text": "Plants need water soil",
        }

        self.assertEqual(detect_redundancy_violations([record], min_overlap=0.7), [])
        self.assertEqual(len(detect_redundancy_violations([record], min_overlap=0.6)), 1)

    def test_embedding_scoring_uses_configured_model(self) -> None:
        class FixedEmbeddingModel:
            def encode(self, texts, normalize_embeddings=True):
                self.texts = texts
                self.normalized = normalize_embeddings
                return [[1.0, 0.0], [0.8, 0.6]]

        model = FixedEmbeddingModel()
        candidates = detect_redundancy_violations(
            [
                {
                    "start_time": 0.0,
                    "end_time": 3.0,
                    "spoken_text": "spoken explanation",
                    "onscreen_text": "different slide wording",
                }
            ],
            scoring_method="embedding",
            embedding_model=model,
            min_overlap=0.75,
        )

        self.assertEqual(model.texts, ["spoken explanation", "different slide wording"])
        self.assertTrue(model.normalized)
        self.assertEqual(len(candidates), 1)
        self.assertAlmostEqual(candidates[0]["score"], 0.8)

    def test_rejects_unknown_scoring_method(self) -> None:
        with self.assertRaises(ValueError):
            detect_redundancy_violations([], scoring_method="unknown")


if __name__ == "__main__":
    unittest.main()
