"""End-to-end live analysis runner for arbitrary video files."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from src.alignment.transcript_ocr import align_transcript_to_ocr
from src.audio.transcription import DEFAULT_MODEL as DEFAULT_WHISPER_MODEL, extract_wav, transcribe_wav
from src.redundancy.detector import DEFAULT_EMBEDDING_MODEL, detect_redundancy_violations
from src.video.scene_text import extract_slide_text

_CACHED_EMBEDDING_MODEL = None


def get_cached_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL) -> Any:
    """Lazily load and cache the sentence-transformers model."""
    global _CACHED_EMBEDDING_MODEL
    if _CACHED_EMBEDDING_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer

            _CACHED_EMBEDDING_MODEL = SentenceTransformer(model_name)
        except ImportError as error:
            raise RuntimeError("sentence-transformers is required. Install requirements.txt.") from error
    return _CACHED_EMBEDDING_MODEL


def analyze_video(
    video_path: str | Path,
    *,
    start: float | None = 0.0,
    duration: float | None = 60.0,
    min_overlap: float = 0.20,
    whisper_model: str = "tiny",  # Use fast model for interactive live demos by default
    progress_callback: Any | None = None,
) -> dict[str, Any]:
    """Execute end-to-end analysis on an arbitrary video file for an optional time range."""
    path = Path(video_path)
    if not path.is_file():
        raise FileNotFoundError(f"Video file not found: {path}")

    def notify(step: str) -> None:
        if callable(progress_callback):
            progress_callback(step)

    with tempfile.TemporaryDirectory(prefix="linter_analysis_") as temp_dir:
        temp_wav = Path(temp_dir) / f"{path.stem}.wav"

        # 1. Extract audio
        notify("Extracting audio...")
        extract_wav(path, temp_wav, start=start, duration=duration)

        # 2. Transcribe speech
        notify("Transcribing speech with Whisper...")
        transcript = transcribe_wav(
            temp_wav,
            model_name=whisper_model,
            time_offset=start or 0.0,
        )

        # 3. Scene Detection & OCR
        notify("Detecting visual scenes and running OCR...")
        ocr_scenes = extract_slide_text(
            path,
            start=start,
            duration=duration,
        )

        # 4. Align Transcripts and Slides
        notify("Aligning narration with on-screen slide text...")
        aligned_records = align_transcript_to_ocr(transcript, ocr_scenes, window_size=5.0)

        # 5. Redundancy Detection
        notify("Analyzing redundancy with semantic embeddings...")
        model = get_cached_embedding_model()
        violations = detect_redundancy_violations(
            aligned_records,
            min_overlap=min_overlap,
            scoring_method="embedding",
            embedding_model=model,
        )

    sorted_violations = sorted(
        [
            {
                "start_time": v["start_time"],
                "end_time": v["end_time"],
                "score": float(v["score"]),
                "spoken_text": str(v["spoken_text"]),
                "onscreen_text": str(v["onscreen_text"]),
            }
            for v in violations
        ],
        key=lambda item: item["start_time"],
    )

    return {
        "video": path.name,
        "video_stem": path.stem,
        "start": start,
        "duration": duration,
        "violations": sorted_violations,
    }
