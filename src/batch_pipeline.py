"""Batch runner for the existing lecture video processing stages."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.alignment.transcript_ocr import align_files
from src.audio.transcription import DEFAULT_MODEL, process_video as process_audio
from src.video.scene_text import process_video as process_ocr


VIDEO_SUFFIXES = {".mp4", ".m4v", ".mkv", ".mov", ".webm"}


def discover_videos(videos_dir: str | Path = "data/videos") -> list[Path]:
    """Return supported video files from the dataset directory in name order."""
    directory = Path(videos_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"Video directory not found: {directory}")
    return sorted(path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES)


def process_videos(
    videos_dir: str | Path = "data/videos",
    *,
    model_name: str = DEFAULT_MODEL,
    start: float | None = None,
    duration: float | None = None,
) -> list[Path]:
    """Run audio, OCR, and alignment stages for every discovered video."""
    aligned_outputs = []
    for video_path in discover_videos(videos_dir):
        _, transcript_path = process_audio(
            video_path, model_name=model_name, start=start, duration=duration
        )
        ocr_path = process_ocr(video_path, start=start, duration=duration)
        aligned_outputs.append(align_files(transcript_path, ocr_path))
    return aligned_outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the lecture processing pipeline for all dataset videos.")
    parser.add_argument("--videos-dir", type=Path, default=Path("data/videos"))
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Whisper model (default: {DEFAULT_MODEL})")
    parser.add_argument("--start", type=float, help="Start time in seconds.")
    parser.add_argument("--duration", type=float, help="Duration in seconds.")
    args = parser.parse_args()

    try:
        outputs = process_videos(
            args.videos_dir,
            model_name=args.model,
            start=args.start,
            duration=args.duration,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        parser.error(str(error))

    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
