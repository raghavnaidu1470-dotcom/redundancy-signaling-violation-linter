"""Signaling principle violation detector based on Mayer's Cognitive Multimedia Learning Theory.

Mayer's Signaling Principle states that people learn better when cues that direct
attention to the relevant elements of the material are added.

A signaling violation candidate is defined as a moment where:
1. The narrator's spoken content undergoes a significant thematic shift between
   consecutive temporal windows (low semantic cosine similarity between spoken_t
   and spoken_{t-1}),
2. WHILE the on-screen visual presentation remains completely static (no visual cue,
   highlight, or slide advance) for longer than a specified threshold (e.g. >= 15 seconds).
"""

from __future__ import annotations

from typing import Any, Iterable

from src.redundancy.detector import DEFAULT_EMBEDDING_MODEL, _cosine_similarity


def detect_signaling_violations(
    aligned_records: Iterable[dict[str, Any]],
    *,
    semantic_shift_threshold: float = 0.35,
    min_static_duration: float = 15.0,
    embedding_model: Any | None = None,
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> list[dict[str, Any]]:
    """Detect un-signaled spoken topic transitions during static visual displays.

    Args:
        aligned_records: Ordered time-window records with 'start_time', 'end_time',
            'spoken_text', and 'onscreen_text'.
        semantic_shift_threshold: Maximum consecutive spoken text similarity considered
            a significant thematic topic shift (default: 0.35).
        min_static_duration: Minimum seconds the visual display must remain unchanged
            for an unsignaled shift to qualify as a violation (default: 15.0s).
        embedding_model: Pre-loaded SentenceTransformer instance (optional).
        embedding_model_name: Model name if lazy-loading is needed.

    Returns:
        List of signaling violation candidates sorted by start_time.
    """
    records = list(aligned_records)
    if len(records) < 2:
        return []

    if embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer

            embedding_model = SentenceTransformer(embedding_model_name)
        except ImportError as error:
            raise RuntimeError("sentence-transformers is required. Install requirements.txt.") from error

    violations = []
    current_static_start = float(records[0]["start_time"])
    last_onscreen_text = str(records[0].get("onscreen_text", "")).strip()

    for i in range(1, len(records)):
        prev_rec = records[i - 1]
        curr_rec = records[i]

        curr_onscreen = str(curr_rec.get("onscreen_text", "")).strip()
        curr_spoken = str(curr_rec.get("spoken_text", "")).strip()
        prev_spoken = str(prev_rec.get("spoken_text", "")).strip()
        curr_start = float(curr_rec["start_time"])
        curr_end = float(curr_rec["end_time"])

        # Check if visual display changed
        if curr_onscreen != last_onscreen_text:
            # Visual cue or slide update occurred; reset static timer
            current_static_start = curr_start
            last_onscreen_text = curr_onscreen
            continue

        static_duration = curr_end - current_static_start

        # If narration occurred across both windows and visual remains static >= threshold
        if static_duration >= min_static_duration and curr_spoken and prev_spoken:
            # Measure semantic continuity between consecutive spoken narrations
            embeddings = embedding_model.encode([prev_spoken, curr_spoken], normalize_embeddings=True)
            continuity_score = _cosine_similarity(embeddings[0], embeddings[1])

            # A low continuity score indicates a significant thematic shift without visual signaling
            if continuity_score < semantic_shift_threshold:
                violations.append(
                    {
                        "start_time": curr_start,
                        "end_time": curr_end,
                        "static_duration": static_duration,
                        "shift_score": 1.0 - continuity_score,
                        "spoken_text": curr_spoken,
                        "previous_spoken_text": prev_spoken,
                        "static_onscreen_text": curr_onscreen,
                        "violation_type": "unsignaled_thematic_shift",
                    }
                )

    return sorted(violations, key=lambda v: (v["start_time"]))
