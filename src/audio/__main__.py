"""CLI for extracting and transcribing a lecture video."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .transcription import DEFAULT_MODEL, process_video


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract 16 kHz mono WAV audio and save a word-timestamped transcript."
    )
    parser.add_argument("video_path", type=Path, metavar="VIDEO_PATH")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Whisper model (default: {DEFAULT_MODEL})")
    parser.add_argument("--start", type=float, help="Start time in seconds.")
    parser.add_argument("--duration", type=float, help="Duration in seconds.")
    args = parser.parse_args()

    try:
        audio_path, transcript_path = process_video(
            args.video_path, model_name=args.model, start=args.start, duration=args.duration
        )
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"Audio: {audio_path}")
    print(f"Transcript: {transcript_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
