"""Minimal transcript JSON structure test."""

import json
import tempfile
import unittest
from pathlib import Path

from src.audio.transcription import build_ffmpeg_command, save_transcript


class TranscriptJsonTest(unittest.TestCase):
    def test_range_adds_ffmpeg_seek_and_duration(self) -> None:
        command = build_ffmpeg_command("lecture.mp4", "clip.wav", start=12.5, duration=30.0)
        self.assertEqual(command[command.index("-ss") + 1], "12.5")
        self.assertEqual(command[command.index("-t") + 1], "30.0")

    def test_saved_transcript_preserves_word_timestamps(self) -> None:
        transcript = {
            "source_audio": "data/audio/lesson.wav",
            "model": "small",
            "language": "en",
            "segments": [
                {
                    "start": 0.0,
                    "end": 0.5,
                    "text": "Hello",
                    "words": [{"word": "Hello", "start": 0.0, "end": 0.5}],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            output = save_transcript(transcript, Path(directory) / "transcript.json")
            saved = json.loads(output.read_text(encoding="utf-8"))

        word = saved["segments"][0]["words"][0]
        self.assertEqual(set(word), {"word", "start", "end"})
        self.assertEqual(word["word"], "Hello")


if __name__ == "__main__":
    unittest.main()
