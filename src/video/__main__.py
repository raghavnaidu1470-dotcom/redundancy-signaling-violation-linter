"""CLI for bounded scene/OCR processing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .scene_text import process_video


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract scene-level OCR text from a video.")
    parser.add_argument("video_path", type=Path, metavar="VIDEO_PATH")
    parser.add_argument("--start", type=float, help="Start time in seconds.")
    parser.add_argument("--duration", type=float, help="Duration in seconds.")
    args = parser.parse_args()
    try:
        print(process_video(args.video_path, start=args.start, duration=args.duration))
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
