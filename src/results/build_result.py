"""Consolidate aligned video records and redundancy detections into UI-ready JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.redundancy.detector import DEFAULT_EMBEDDING_MODEL, detect_redundancy_violations

DEFAULT_ALIGNED_DIR = Path("data/aligned")
DEFAULT_RESULTS_DIR = Path("data/results")


def build_video_result(
    video_stem: str,
    *,
    aligned_dir: str | Path = DEFAULT_ALIGNED_DIR,
    output_dir: str | Path | None = DEFAULT_RESULTS_DIR,
    min_overlap: float = 0.20,
    scoring_method: str = "embedding",
    embedding_model: Any | None = None,
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> dict[str, Any]:
    """Load aligned records, run redundancy detector, and return consolidated result."""
    aligned_file = Path(aligned_dir) / f"{video_stem}.json"
    if not aligned_file.is_file():
        raise FileNotFoundError(f"Aligned records not found: {aligned_file}")

    with aligned_file.open(encoding="utf-8") as file:
        aligned_records = json.load(file)

    if not isinstance(aligned_records, list):
        raise ValueError(f"Aligned records in {aligned_file} must be a JSON array.")

    if embedding_model is None and scoring_method == "embedding":
        try:
            from sentence_transformers import SentenceTransformer

            embedding_model = SentenceTransformer(embedding_model_name)
        except ImportError as error:
            raise RuntimeError("sentence-transformers is required. Install requirements.txt.") from error

    violations = detect_redundancy_violations(
        aligned_records,
        min_overlap=min_overlap,
        scoring_method=scoring_method,
        embedding_model=embedding_model,
        embedding_model_name=embedding_model_name,
    )

    sorted_violations = sorted(
        [
            {
                "start_time": v["start_time"],
                "end_time": v["end_time"],
                "score": v["score"],
                "spoken_text": v["spoken_text"],
                "onscreen_text": v["onscreen_text"],
            }
            for v in violations
        ],
        key=lambda item: item["start_time"],
    )

    result = {
        "video": video_stem,
        "violations": sorted_violations,
    }

    if output_dir is not None:
        out_path = Path(output_dir) / f"{video_stem}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as file:
            json.dump(result, file, indent=2, ensure_ascii=False)
            file.write("\n")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build and save consolidated redundancy results for a video."
    )
    parser.add_argument("video_stem", help="Video stem name (without extension).")
    parser.add_argument(
        "--aligned-dir",
        type=Path,
        default=DEFAULT_ALIGNED_DIR,
        help=f"Directory containing aligned JSON files (default: {DEFAULT_ALIGNED_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help=f"Directory to save result JSON files (default: {DEFAULT_RESULTS_DIR})",
    )
    parser.add_argument(
        "--min-overlap",
        type=float,
        default=0.20,
        help="Minimum overlap threshold (default: 0.20)",
    )
    args = parser.parse_args()

    try:
        result = build_video_result(
            args.video_stem,
            aligned_dir=args.aligned_dir,
            output_dir=args.output_dir,
            min_overlap=args.min_overlap,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    out_path = Path(args.output_dir) / f"{args.video_stem}.json"
    print(f"Saved {len(result['violations'])} potential redundancy violations to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
