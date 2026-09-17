"""Timestamp-based alignment of transcript words and OCR scene text."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def _transcript_words(transcript: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """Yield word-level timestamp entries from a transcript payload."""
    for segment in transcript.get("segments", []):
        yield from segment.get("words", [])


def spoken_text_for_interval(
    transcript: dict[str, Any], start_time: float, end_time: float
) -> str:
    """Join words whose start timestamps fall within a scene interval."""
    words = [
        word.get("word", "").strip()
        for word in _transcript_words(transcript)
        if start_time <= word.get("start", -1) < end_time
    ]
    return " ".join(word for word in words if word)


def align_transcript_to_ocr(
    transcript: dict[str, Any],
    ocr_scenes: list[dict[str, Any]],
    *,
    window_size: float = 5.0,
) -> list[dict[str, Any]]:
    """Create fixed-size spoken/on-screen text windows within each OCR scene."""
    if window_size <= 0:
        raise ValueError("window_size must be positive.")

    aligned = []
    for scene in ocr_scenes:
        try:
            start_time = scene["start_time"]
            end_time = scene["end_time"]
            onscreen_text = scene["onscreen_text"]
        except KeyError as error:
            raise ValueError(f"OCR scene is missing required field: {error.args[0]}") from error

        window_start = start_time
        while window_start < end_time:
            window_end = min(window_start + window_size, end_time)
            aligned.append(
                {
                    "start_time": window_start,
                    "end_time": window_end,
                    "spoken_text": spoken_text_for_interval(
                        transcript, window_start, window_end
                    ),
                    "onscreen_text": onscreen_text,
                }
            )
            window_start = window_end
    return aligned


def save_aligned_results(results: list[dict[str, Any]], output_path: str | Path) -> Path:
    """Save aligned records as UTF-8 JSON."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return output


def align_files(
    transcript_path: str | Path,
    ocr_path: str | Path,
    *,
    output_dir: str | Path = "data/aligned",
    window_size: float = 5.0,
) -> Path:
    """Load transcript/OCR JSON files, align them, and save the result."""
    transcript_file = Path(transcript_path)
    ocr_file = Path(ocr_path)
    if not transcript_file.is_file():
        raise FileNotFoundError(f"Transcript JSON not found: {transcript_file}")
    if not ocr_file.is_file():
        raise FileNotFoundError(f"OCR JSON not found: {ocr_file}")

    with transcript_file.open(encoding="utf-8") as file:
        transcript = json.load(file)
    with ocr_file.open(encoding="utf-8") as file:
        ocr_scenes = json.load(file)

    if not isinstance(transcript, dict) or not isinstance(ocr_scenes, list):
        raise ValueError("Transcript must be an object and OCR data must be a list.")

    results = align_transcript_to_ocr(
        transcript, ocr_scenes, window_size=window_size
    )
    return save_aligned_results(results, Path(output_dir) / transcript_file.name)
