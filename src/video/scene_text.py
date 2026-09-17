"""Scene-based slide text extraction for instructional videos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _validate_time_range(start: float | None, duration: float | None) -> None:
    if start is not None and start < 0:
        raise ValueError("start must be non-negative")
    if duration is not None and duration <= 0:
        raise ValueError("duration must be positive")


def limit_scene_intervals(
    scenes: list[tuple[float, float]], start: float | None = None, duration: float | None = None
) -> list[tuple[float, float]]:
    """Clip scene intervals to an optional processing range."""
    _validate_time_range(start, duration)
    range_start = start or 0.0
    range_end = range_start + duration if duration is not None else float("inf")
    return [
        (max(scene_start, range_start), min(scene_end, range_end))
        for scene_start, scene_end in scenes
        if scene_end > range_start and scene_start < range_end
    ]


def detect_scenes(video_path: str | Path, *, threshold: float = 27.0) -> list[tuple[float, float]]:
    """Return detected scene start/end times in seconds."""
    source = Path(video_path)
    if not source.is_file():
        raise FileNotFoundError(f"Video file not found: {source}")

    try:
        from scenedetect import ContentDetector, SceneManager, open_video
    except ImportError as error:
        raise RuntimeError("PySceneDetect is required. Install requirements.txt.") from error

    video = open_video(str(source))
    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=threshold))
    try:
        manager.detect_scenes(video=video, show_progress=False)
        return [
            (start.get_seconds(), end.get_seconds())
            for start, end in manager.get_scene_list(start_in_scene=True)
        ]
    finally:
        release = getattr(video, "release", None)
        if callable(release):
            release()


def _representative_frame(capture: Any, start_time: float, end_time: float) -> Any:
    """Read the midpoint frame for a detected scene."""
    import cv2

    midpoint_ms = ((start_time + end_time) / 2) * 1000
    capture.set(cv2.CAP_PROP_POS_MSEC, midpoint_ms)
    success, frame = capture.read()
    if not success:
        raise RuntimeError(f"Could not read representative frame at {midpoint_ms / 1000:.2f}s")
    return frame


def _preprocess_frame(frame: Any) -> Any:
    """Increase text contrast and size for low-resolution lecture frames."""
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError("OpenCV is required. Install requirements.txt.") from error

    grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    enlarged = cv2.resize(
        grayscale, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC
    )
    denoised = cv2.GaussianBlur(enlarged, (3, 3), 0)
    _, binary = cv2.threshold(
        denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    if binary.mean() < 127:
        binary = cv2.bitwise_not(binary)
    return binary


def _ocr_frame(frame: Any) -> str:
    """Return cleaned OCR text for an OpenCV BGR frame."""
    try:
        import pytesseract
    except ImportError as error:
        raise RuntimeError("pytesseract is required. Install requirements.txt.") from error

    try:
        return pytesseract.image_to_string(_preprocess_frame(frame)).strip()
    except pytesseract.TesseractNotFoundError as error:
        raise RuntimeError("Tesseract is required but was not found on PATH.") from error


def extract_slide_text(
    video_path: str | Path,
    *,
    threshold: float = 27.0,
    start: float | None = None,
    duration: float | None = None,
) -> list[dict[str, Any]]:
    """OCR one representative frame per detected scene."""
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError("OpenCV is required. Install requirements.txt.") from error

    scenes = limit_scene_intervals(detect_scenes(video_path, threshold=threshold), start, duration)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    try:
        return [
            {
                "start_time": start_time,
                "end_time": end_time,
                "onscreen_text": _ocr_frame(_representative_frame(capture, start_time, end_time)),
            }
            for start_time, end_time in scenes
        ]
    finally:
        capture.release()


def save_ocr_results(results: list[dict[str, Any]], output_path: str | Path) -> Path:
    """Save scene OCR results as UTF-8 JSON."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return output


def process_video(
    video_path: str | Path,
    *,
    threshold: float = 27.0,
    start: float | None = None,
    duration: float | None = None,
) -> Path:
    """Extract and save scene-level on-screen text under data/ocr/."""
    source = Path(video_path)
    results = extract_slide_text(source, threshold=threshold, start=start, duration=duration)
    return save_ocr_results(results, Path("data/ocr") / f"{source.stem}.json")
