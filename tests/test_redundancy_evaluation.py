"""Tests for interval-based redundancy evaluation."""

import unittest

from src.evaluation.redundancy import evaluate_redundancy_predictions


TRUTH = [{"start_time": 10.0, "end_time": 15.0, "is_redundant": True}]
PREDICTION = [{"start_time": 10.0, "end_time": 15.0, "score": 0.9}]


class RedundancyEvaluationTest(unittest.TestCase):
    def test_exact_match_scores_perfectly(self) -> None:
        result = evaluate_redundancy_predictions(PREDICTION, TRUTH)

        self.assertEqual(result["precision"], 1.0)
        self.assertEqual(result["recall"], 1.0)
        self.assertEqual(result["f1"], 1.0)

    def test_missed_prediction_is_false_negative(self) -> None:
        result = evaluate_redundancy_predictions([], TRUTH)

        self.assertEqual(result["false_negatives"], 1)
        self.assertEqual(result["recall"], 0.0)

    def test_false_positive_lowers_precision(self) -> None:
        result = evaluate_redundancy_predictions(
            PREDICTION + [{"start_time": 30.0, "end_time": 35.0, "score": 0.8}], TRUTH
        )

        self.assertEqual(result["false_positives"], 1)
        self.assertEqual(result["precision"], 0.5)

    def test_timestamp_tolerance_matches_nearby_interval(self) -> None:
        shifted_prediction = [{"start_time": 10.4, "end_time": 15.4, "score": 0.8}]

        self.assertEqual(evaluate_redundancy_predictions(shifted_prediction, TRUTH)["true_positives"], 0)
        result = evaluate_redundancy_predictions(
            shifted_prediction, TRUTH, timestamp_tolerance=0.5
        )
        self.assertEqual(result["true_positives"], 1)


if __name__ == "__main__":
    unittest.main()
