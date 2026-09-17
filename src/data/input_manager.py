"""Input abstraction for local video files and downloadable URLs."""

from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.parse import urlparse


def is_url(source: str) -> bool:
    """Check if the source string represents an HTTP/HTTPS URL."""
    parsed = urlparse(source.strip())
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def download_url_to_temp(url: str, output_dir: str | Path) -> Path:
    """Download a video URL to a target temporary directory using yt-dlp.

    The caller is responsible for cleaning up the downloaded file or temporary
    directory when finished with it.
    """
    try:
        import yt_dlp
    except ImportError as error:
        raise RuntimeError("yt-dlp is required to download video URLs. Install requirements.txt.") from error

    destination_dir = Path(output_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    template = str(destination_dir / "%(id)s.%(ext)s")

    options = {
        "outtmpl": template,
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "quiet": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios"]
            }
        },
    }

    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=True)
        if not info:
            raise RuntimeError(f"Failed to extract video info from URL: {url}")
        filename = downloader.prepare_filename(info)
        downloaded_path = Path(filename)
        if not downloaded_path.is_file():
            # Sometimes yt-dlp changes extension to mp4 or mkv
            candidates = list(destination_dir.glob(f"{info.get('id', '')}.*"))
            if candidates:
                return candidates[0]
            raise FileNotFoundError(f"Expected downloaded video at {downloaded_path}, but not found.")
        return downloaded_path


def resolve_input(source: str, temp_dir: str | Path | None = None) -> Path:
    """Resolve a source string (local file path or web URL) to a concrete local Path.

    - If ``source`` is an existing local file path, it is returned as a Path object.
    - If ``source`` is a web URL, it is downloaded into ``temp_dir`` (or a new
      temporary directory if None).
    - Note: The caller is responsible for any cleanup of temporary files created
      during URL resolution.
    """
    cleaned_source = source.strip()
    local_path = Path(cleaned_source)

    if local_path.is_file():
        return local_path.resolve()

    if is_url(cleaned_source):
        target_dir = Path(temp_dir) if temp_dir is not None else Path(tempfile.mkdtemp(prefix="lecture_input_"))
        return download_url_to_temp(cleaned_source, target_dir)

    raise FileNotFoundError(f"Input source '{source}' is neither an existing file nor a valid URL.")
