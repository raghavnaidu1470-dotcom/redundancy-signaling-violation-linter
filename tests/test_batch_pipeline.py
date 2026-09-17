"""Minimal orchestration test for the batch lecture pipeline."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import batch_pipeline


class BatchPipelineTest(unittest.TestCase):
    def test_processes_each_discovered_video_through_existing_stages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            videos_dir = Path(directory)
            first_video = videos_dir / "a.mp4"
            second_video = videos_dir / "b.mov"
            first_video.touch()
            second_video.touch()
            (videos_dir / "notes.txt").touch()

            with patch.object(batch_pipeline, "process_audio") as process_audio, patch.object(
                batch_pipeline, "process_ocr"
            ) as process_ocr, patch.object(batch_pipeline, "align_files") as align_files:
                process_audio.side_effect = [
                    (Path("data/audio/a.wav"), Path("data/transcripts/a.json")),
                    (Path("data/audio/b.wav"), Path("data/transcripts/b.json")),
                ]
                process_ocr.side_effect = [Path("data/ocr/a.json"), Path("data/ocr/b.json")]
                align_files.side_effect = [Path("data/aligned/a.json"), Path("data/aligned/b.json")]

                outputs = batch_pipeline.process_videos(
                    videos_dir, model_name="tiny", start=10.0, duration=60.0
                )

        self.assertEqual(outputs, [Path("data/aligned/a.json"), Path("data/aligned/b.json")])
        self.assertEqual(process_audio.call_count, 2)
        self.assertEqual(process_ocr.call_count, 2)
        self.assertEqual(align_files.call_count, 2)
        process_audio.assert_any_call(
            first_video, model_name="tiny", start=10.0, duration=60.0
        )
        process_ocr.assert_any_call(first_video, start=10.0, duration=60.0)


if __name__ == "__main__":
    unittest.main()
