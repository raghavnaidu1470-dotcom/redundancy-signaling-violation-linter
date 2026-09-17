"""Unit tests for input abstraction (local files and URLs)."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.data.input_manager import is_url, resolve_input


class InputManagerTest(unittest.TestCase):
    def test_identifies_urls_correctly(self) -> None:
        self.assertTrue(is_url("https://www.youtube.com/watch?v=12345"))
        self.assertTrue(is_url("http://example.com/video.mp4"))
        self.assertFalse(is_url("data/videos/lecture.mp4"))
        self.assertFalse(is_url("/path/to/local/file.mov"))

    def test_passes_through_existing_local_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_file:
            path = Path(temp_file.name)
            resolved = resolve_input(str(path))
            self.assertEqual(resolved, path.resolve())

    def test_downloads_url_via_mocked_downloader(self) -> None:
        test_url = "https://www.youtube.com/watch?v=sample"
        with tempfile.TemporaryDirectory() as temp_dir:
            expected_path = Path(temp_dir) / "sample.mp4"
            expected_path.touch()

            with patch("src.data.input_manager.download_url_to_temp") as mock_download:
                mock_download.return_value = expected_path
                resolved = resolve_input(test_url, temp_dir=temp_dir)

                mock_download.assert_called_once_with(test_url, Path(temp_dir))
                self.assertEqual(resolved, expected_path)

    def test_raises_error_for_nonexistent_source(self) -> None:
        with self.assertRaises(FileNotFoundError):
            resolve_input("nonexistent_file_path_12345.mp4")


if __name__ == "__main__":
    unittest.main()
