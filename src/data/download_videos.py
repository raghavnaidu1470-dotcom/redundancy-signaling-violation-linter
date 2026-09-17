"""Download lecture videos listed in a text or JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_OUTPUT_DIR = Path("data/videos")


def load_urls(url_file: str | Path) -> list[str]:
    """Load non-empty URLs from a line-delimited text or JSON list file."""
    source = Path(url_file)
    if not source.is_file():
        raise FileNotFoundError(f"URL list not found: {source}")

    if source.suffix.lower() == ".json":
        data = json.loads(source.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("urls")
        if not isinstance(data, list) or not all(isinstance(url, str) for url in data):
            raise ValueError("JSON URL list must be an array of strings or an object with a 'urls' array.")
        urls = data
    else:
        urls = [
            line.strip()
            for line in source.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]

    if not urls:
        raise ValueError("URL list is empty.")
    return urls


def output_template(output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> str:
    """Return the yt-dlp filename template for downloaded videos."""
    return str(Path(output_dir) / "%(title)s [%(id)s].%(ext)s")


def download_videos(urls: list[str], output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
    """Download each supplied URL into the requested local directory."""
    try:
        import yt_dlp
    except ImportError as error:
        raise RuntimeError("yt-dlp is required. Install requirements.txt.") from error

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    options = {
        "outtmpl": output_template(destination),
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios"]
            }
        },
    }
    with yt_dlp.YoutubeDL(options) as downloader:
        for url in urls:
            downloader.download([url])


def main() -> int:
    parser = argparse.ArgumentParser(description="Download lecture videos from a URL list.")
    parser.add_argument("url_file", type=Path, help="Text file or JSON file containing video URLs.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    try:
        download_videos(load_urls(args.url_file), args.output_dir)
    except (FileNotFoundError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
