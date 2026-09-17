"""FFmpeg audio extraction and faster-whisper transcription helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable


DEFAULT_MODEL = "small"


def _validate_time_range(start: float | None, duration: float | None) -> None:
    if start is not None and start < 0:
        raise ValueError("start must be non-negative")
    if duration is not None and duration <= 0:
        raise ValueError("duration must be positive")


def build_ffmpeg_command(
    video_path: str | Path,
    wav_path: str | Path,
    *,
    start: float | None = None,
    duration: float | None = None,
) -> list[str]:
    """Build the FFmpeg command for an optional source-video time range."""
    _validate_time_range(start, duration)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("FFmpeg is required but was not found on PATH.")
    command = [ffmpeg, "-y"]
    if start is not None:
        command.extend(["-ss", str(start)])
    command.extend(["-i", str(video_path)])
    if duration is not None:
        command.extend(["-t", str(duration)])
    return command + ["-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav_path)]


def extract_wav(
    video_path: str | Path,
    wav_path: str | Path,
    *,
    start: float | None = None,
    duration: float | None = None,
) -> Path:
    """Extract mono 16 kHz PCM WAV audio from a video file."""
    video = Path(video_path)
    wav = Path(wav_path)
    if not video.is_file():
        raise FileNotFoundError(f"Video file not found: {video}")

    wav.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            build_ffmpeg_command(video, wav, start=start, duration=duration),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or "unknown FFmpeg error"
        raise RuntimeError(f"FFmpeg extraction failed: {message}") from error

    return wav


def _words_payload(words: Iterable[Any] | None) -> list[dict[str, Any]]:
    return [
        {"word": word.word, "start": word.start, "end": word.end}
        for word in (words or [])
    ]


def transcribe_wav(
    wav_path: str | Path,
    *,
    model_name: str = DEFAULT_MODEL,
    time_offset: float = 0.0,
) -> dict[str, Any]:
    """Transcribe WAV audio and return timestamped segments and words."""
    wav = Path(wav_path)
    if not wav.is_file():
        raise FileNotFoundError(f"Audio file not found: {wav}")

    try:
        from faster_whisper import WhisperModel

        model = WhisperModel(model_name, device="auto", compute_type="default")
        segments, info = model.transcribe(str(wav), word_timestamps=True)
        payload = [
            {
                "start": segment.start + time_offset,
                "end": segment.end + time_offset,
                "text": segment.text.strip(),
                "words": [
                    {"word": word["word"], "start": word["start"] + time_offset, "end": word["end"] + time_offset}
                    for word in _words_payload(segment.words)
                ],
            }
            for segment in segments
        ]
    except Exception as error:
        raise RuntimeError(f"Transcription failed: {error}") from error

    return {
        "source_audio": str(wav),
        "model": model_name,
        "language": info.language,
        "segments": payload,
    }


def save_transcript(transcript: dict[str, Any], output_path: str | Path) -> Path:
    """Save transcript data as UTF-8 JSON."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(transcript, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return output


def process_video(
    video_path: str | Path,
    *,
    model_name: str = DEFAULT_MODEL,
    start: float | None = None,
    duration: float | None = None,
) -> tuple[Path, Path]:
    """Extract a video's audio and save its word-timestamped transcript."""
    video = Path(video_path)
    wav_path = Path("data/audio") / f"{video.stem}.wav"
    transcript_path = Path("data/transcripts") / f"{video.stem}.json"
    extract_wav(video, wav_path, start=start, duration=duration)
    transcript = transcribe_wav(wav_path, model_name=model_name, time_offset=start or 0.0)
    return wav_path, save_transcript(transcript, transcript_path)
