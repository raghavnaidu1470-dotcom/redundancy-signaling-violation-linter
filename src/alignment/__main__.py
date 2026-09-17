"""CLI for timestamp-based transcript/OCR alignment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .transcript_ocr import align_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Align transcript and OCR JSON files.")
    parser.add_argument("transcript_json", type=Path, metavar="TRANSCRIPT_JSON")
    parser.add_argument("ocr_json", type=Path, metavar="OCR_JSON")
    args = parser.parse_args()

    try:
        output_path = align_files(args.transcript_json, args.ocr_json)
    except (FileNotFoundError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
