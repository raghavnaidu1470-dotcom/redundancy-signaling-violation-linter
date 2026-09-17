"""Unit tests for live analysis runner with mocked pipeline stages."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.results.pipeline_runner import analyze_video


class PipelineRunnerTest(unittest.TestCase):
    @patch("src.results.pipeline_runner.extract_wav")
    @patch("src.results.pipeline_runner.transcribe_wav")
    @patch("src.results.pipeline_runner.extract_slide_text")
    @patch("src.results.pipeline_runner.get_cached_embedding_model")
    def test_runs_end_to_end_analysis(
        self,
        mock_embedding_model,
        mock_extract_slide_text,
        mock_transcribe_wav,
        mock_extract_wav,
    ) -> None:
        with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_video:
            video_path = Path(temp_video.name)

            mock_transcribe_wav.return_value = {
                "segments": [
                    {
                        "words": [
                            {"word": "Linear", "start": 1.0, "end": 1.5},
                            {"word": "algebra", "start": 1.5, "end": 2.0},
                        ]
                    }
                ]
            }
            mock_extract_slide_text.return_value = [
                {"start_time": 0.0, "end_time": 5.0, "onscreen_text": "Linear Algebra"}
            ]

            fake_model = MagicMock()
            fake_model.encode.return_value = [[1.0, 0.0], [0.8, 0.6]]
            mock_embedding_model.return_value = fake_model

            result = analyze_video(video_path, start=0.0, duration=5.0, min_overlap=0.20)

            self.assertEqual(result["video_stem"], video_path.stem)
            self.assertEqual(len(result["violations"]), 1)
            self.assertEqual(result["violations"][0]["spoken_text"], "Linear algebra")
            self.assertEqual(result["violations"][0]["onscreen_text"], "Linear Algebra")
            self.assertAlmostEqual(result["violations"][0]["score"], 0.8)


if __name__ == "__main__":
    unittest.main()
