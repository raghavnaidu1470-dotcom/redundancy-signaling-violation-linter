"""Minimal smoke test for the alignment CLI."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from src.alignment import __main__ as alignment_cli


class AlignmentCliTest(unittest.TestCase):
    def test_passes_positional_json_paths_to_existing_alignment_function(self) -> None:
        transcript = Path("data/transcripts/lecture.json")
        ocr = Path("data/ocr/lecture.json")
        output = Path("data/aligned/lecture.json")

        with patch.object(sys, "argv", ["alignment", str(transcript), str(ocr)]):
            with patch.object(alignment_cli, "align_files", return_value=output) as align_files:
                self.assertEqual(alignment_cli.main(), 0)

        align_files.assert_called_once_with(transcript, ocr)


if __name__ == "__main__":
    unittest.main()
