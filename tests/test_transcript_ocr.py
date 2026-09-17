"""Tests for timestamp-based transcript/OCR alignment."""

import json
import tempfile
import unittest
from pathlib import Path

from src.alignment.transcript_ocr import (
    align_transcript_to_ocr,
    save_aligned_results,
    spoken_text_for_interval,
)


TRANSCRIPT = {
    "segments": [
        {
            "words": [
                {"word": "First", "start": 0.2, "end": 0.5},
                {"word": "slide", "start": 1.0, "end": 1.4},
                {"word": "Second", "start": 2.0, "end": 2.4},
            ]
        }
    ]
}


class TranscriptOcrAlignmentTest(unittest.TestCase):
    def test_groups_words_by_scene_start_time(self) -> None:
        self.assertEqual(spoken_text_for_interval(TRANSCRIPT, 0.0, 2.0), "First slide")
        self.assertEqual(spoken_text_for_interval(TRANSCRIPT, 2.0, 4.0), "Second")

    def test_aligned_output_has_required_fields(self) -> None:
        records = align_transcript_to_ocr(
            TRANSCRIPT,
            [{"start_time": 0.0, "end_time": 2.0, "onscreen_text": "Title"}],
        )
        with tempfile.TemporaryDirectory() as directory:
            output = save_aligned_results(records, Path(directory) / "aligned.json")
            saved = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(
            set(saved[0]), {"start_time", "end_time", "spoken_text", "onscreen_text"}
        )
        self.assertEqual(saved[0]["spoken_text"], "First slide")

    def test_subdivides_scene_into_configurable_windows(self) -> None:
        transcript = {
            "segments": [
                {
                    "words": [
                        {"word": "one", "start": 1.0, "end": 1.2},
                        {"word": "two", "start": 5.0, "end": 5.2},
                        {"word": "three", "start": 10.0, "end": 10.2},
                    ]
                }
            ]
        }

        records = align_transcript_to_ocr(
            transcript,
            [{"start_time": 0.0, "end_time": 12.0, "onscreen_text": "Repeated slide"}],
            window_size=5.0,
        )

        self.assertEqual(
            [(record["start_time"], record["end_time"]) for record in records],
            [(0.0, 5.0), (5.0, 10.0), (10.0, 12.0)],
        )
        self.assertEqual([record["spoken_text"] for record in records], ["one", "two", "three"])
        self.assertTrue(all(record["onscreen_text"] == "Repeated slide" for record in records))


if __name__ == "__main__":
    unittest.main()
