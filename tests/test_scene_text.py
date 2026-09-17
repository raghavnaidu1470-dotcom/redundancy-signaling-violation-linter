"""Minimal JSON structure test for slide-text extraction output."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.video.scene_text import (
    _preprocess_frame,
    detect_scenes_fixed_cadence,
    limit_scene_intervals,
    save_ocr_results,
)


class SceneTextJsonTest(unittest.TestCase):
    def test_preprocesses_dark_lecture_frame_for_ocr(self) -> None:
        frame = np.zeros((50, 100, 3), dtype=np.uint8)
        frame[15:35, 20:80] = 255

        processed = _preprocess_frame(frame)

        self.assertEqual(processed.shape, (100, 200))
        self.assertEqual(processed.ndim, 2)
        self.assertTrue(set(np.unique(processed)).issubset({0, 255}))
        self.assertGreater(processed.mean(), 127)

    def test_limits_scenes_to_requested_range(self) -> None:
        self.assertEqual(limit_scene_intervals([(0.0, 4.0), (4.0, 9.0)], 2.0, 4.0), [(2.0, 4.0), (4.0, 6.0)])

    def test_detect_scenes_fixed_cadence_generates_uniform_windows(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_file:
            path = Path(temp_file.name)
            windows = detect_scenes_fixed_cadence(path, interval_seconds=10.0, start=0.0, duration=35.0)
            self.assertEqual(
                windows,
                [(0.0, 10.0), (10.0, 20.0), (20.0, 30.0), (30.0, 35.0)],
            )

    def test_saved_results_have_scene_text_fields(self) -> None:
        results = [{"start_time": 0.0, "end_time": 5.0, "onscreen_text": "Slide title"}]
        with tempfile.TemporaryDirectory() as directory:
            output = save_ocr_results(results, Path(directory) / "slides.json")
            saved = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(set(saved[0]), {"start_time", "end_time", "onscreen_text"})
        self.assertEqual(saved[0]["onscreen_text"], "Slide title")


if __name__ == "__main__":
    unittest.main()
