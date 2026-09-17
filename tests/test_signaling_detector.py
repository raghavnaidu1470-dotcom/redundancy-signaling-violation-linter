"""Unit tests for Mayer's signaling violation detector."""

import unittest

from src.signaling.detector import detect_signaling_violations


class FixedEmbeddingModel:
    def encode(self, texts, normalize_embeddings=True):
        if any("new topic" in t for t in texts):
            # Low continuity (thematic shift)
            return [[1.0, 0.0], [0.1, 0.994987]]
        # High continuity
        return [[1.0, 0.0], [0.95, 0.31225]]


class SignalingDetectorTest(unittest.TestCase):
    def test_detects_unsignaled_thematic_shift_during_static_visual(self) -> None:
        records = [
            {
                "start_time": 0.0,
                "end_time": 5.0,
                "spoken_text": "First concept introduction",
                "onscreen_text": "Static Slide 1",
            },
            {
                "start_time": 5.0,
                "end_time": 10.0,
                "spoken_text": "Continuing first concept",
                "onscreen_text": "Static Slide 1",
            },
            {
                "start_time": 10.0,
                "end_time": 15.0,
                "spoken_text": "Still elaborating first concept",
                "onscreen_text": "Static Slide 1",
            },
            {
                "start_time": 15.0,
                "end_time": 20.0,
                "spoken_text": "Completely new topic without any slide change",
                "onscreen_text": "Static Slide 1",
            },
        ]

        model = FixedEmbeddingModel()
        violations = detect_signaling_violations(
            records,
            semantic_shift_threshold=0.35,
            min_static_duration=15.0,
            embedding_model=model,
        )

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["start_time"], 15.0)
        self.assertEqual(violations[0]["end_time"], 20.0)
        self.assertEqual(violations[0]["violation_type"], "unsignaled_thematic_shift")
        self.assertAlmostEqual(violations[0]["shift_score"], 0.9, places=2)

    def test_resets_static_timer_when_visual_slide_changes(self) -> None:
        records = [
            {
                "start_time": 0.0,
                "end_time": 10.0,
                "spoken_text": "Topic A discussion",
                "onscreen_text": "Slide A",
            },
            {
                "start_time": 10.0,
                "end_time": 20.0,
                "spoken_text": "Topic B discussion",
                "onscreen_text": "Slide B - New Slide Cue",  # Visual changed!
            },
        ]

        model = FixedEmbeddingModel()
        violations = detect_signaling_violations(
            records,
            min_static_duration=15.0,
            embedding_model=model,
        )

        # Slide changed, so static duration was reset (only 10s on Slide B < 15s)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
