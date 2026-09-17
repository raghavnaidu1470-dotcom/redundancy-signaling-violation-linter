"""Interval-based evaluation for redundancy detector predictions."""

from __future__ import annotations

from typing import Any, Iterable


def _interval(record: dict[str, Any]) -> tuple[float, float]:
    try:
        start_time = float(record["start_time"])
        end_time = float(record["end_time"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Each record needs numeric start_time and end_time.") from error
    if end_time < start_time:
        raise ValueError("end_time cannot be before start_time.")
    return start_time, end_time


def _matches(
    prediction: dict[str, Any], ground_truth: dict[str, Any], timestamp_tolerance: float
) -> bool:
    prediction_start, prediction_end = _interval(prediction)
    truth_start, truth_end = _interval(ground_truth)
    return (
        abs(prediction_start - truth_start) <= timestamp_tolerance
        and abs(prediction_end - truth_end) <= timestamp_tolerance
    )


def evaluate_redundancy_predictions(
    predictions: Iterable[dict[str, Any]],
    ground_truth: Iterable[dict[str, Any]],
    *,
    timestamp_tolerance: float = 0.0,
) -> dict[str, float | int]:
    """Calculate precision, recall, and F1 with one-to-one interval matching.

    Predictions from token and embedding scoring share the same timestamp fields,
    so this function intentionally does not depend on a scoring-method field.
    Only ground-truth intervals labeled ``is_redundant: true`` are positives.
    """
    if timestamp_tolerance < 0:
        raise ValueError("timestamp_tolerance must be non-negative.")

    prediction_list = list(predictions)
    positive_truth = [record for record in ground_truth if record.get("is_redundant") is True]
    unmatched_truth = set(range(len(positive_truth)))
    true_positives = 0

    for prediction in prediction_list:
        matching_index = next(
            (
                index
                for index in unmatched_truth
                if _matches(prediction, positive_truth[index], timestamp_tolerance)
            ),
            None,
        )
        if matching_index is not None:
            unmatched_truth.remove(matching_index)
            true_positives += 1

    false_positives = len(prediction_list) - true_positives
    false_negatives = len(positive_truth) - true_positives
    precision = true_positives / len(prediction_list) if prediction_list else 0.0
    recall = true_positives / len(positive_truth) if positive_truth else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
