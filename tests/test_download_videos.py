"""Minimal tests for lecture-video URL list handling."""

import tempfile
import unittest
from pathlib import Path

from src.data.download_videos import load_urls, output_template


class DownloadVideosTest(unittest.TestCase):
    def test_loads_text_urls_and_builds_destination_template(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            url_file = Path(directory) / "urls.txt"
            url_file.write_text("# lectures\nhttps://example.org/one\n\nhttps://example.org/two\n")
            urls = load_urls(url_file)

        self.assertEqual(urls, ["https://example.org/one", "https://example.org/two"])
        self.assertEqual(
            output_template("data/videos"), "data/videos/%(title)s [%(id)s].%(ext)s"
        )

    def test_loads_json_urls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            url_file = Path(directory) / "urls.json"
            url_file.write_text('{"urls": ["https://example.org/lecture"]}')
            self.assertEqual(load_urls(url_file), ["https://example.org/lecture"])


if __name__ == "__main__":
    unittest.main()
