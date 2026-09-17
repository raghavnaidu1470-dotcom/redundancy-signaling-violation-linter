"""Token and embedding redundancy candidate detection."""

from __future__ import annotations

import re
from typing import Any, Iterable


TOKEN_PATTERN = re.compile(r"\b\w+\b")
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-MiniLM-L3-v2"


def _tokens(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


def token_overlap_score(spoken_text: str, onscreen_text: str) -> float:
    """Return the Jaccard overlap of normalized text tokens."""
    spoken_tokens = _tokens(spoken_text)
    onscreen_tokens = _tokens(onscreen_text)
    union = spoken_tokens | onscreen_tokens
    return len(spoken_tokens & onscreen_tokens) / len(union) if union else 0.0


def _cosine_similarity(first: Iterable[float], second: Iterable[float]) -> float:
    first_values = [float(value) for value in first]
    second_values = [float(value) for value in second]
    if len(first_values) != len(second_values):
        raise ValueError("Embedding vectors must have the same length.")

    dot_product = sum(a * b for a, b in zip(first_values, second_values))
    first_norm = sum(value * value for value in first_values) ** 0.5
    second_norm = sum(value * value for value in second_values) ** 0.5
    if first_norm == 0 or second_norm == 0:
        return 0.0
    return max(-1.0, min(1.0, dot_product / (first_norm * second_norm)))


def embedding_similarity(
    spoken_text: str,
    onscreen_text: str,
    *,
    model: Any | None = None,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> float:
    """Return sentence-embedding cosine similarity for two text strings."""
    if model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError("sentence-transformers is required. Install requirements.txt.") from error
        model = SentenceTransformer(model_name)

    embeddings = model.encode([spoken_text, onscreen_text], normalize_embeddings=True)
    return _cosine_similarity(embeddings[0], embeddings[1])


def detect_redundancy_violations(
    aligned_records: Iterable[dict[str, Any]],
    *,
    max_time_delta: float = 5.0,
    min_overlap: float = 0.5,
    scoring_method: str = "token",
    embedding_model: Any | None = None,
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> list[dict[str, Any]]:
    """Return ranked spoken/on-screen overlap candidates from aligned scenes.

    An aligned record provides one scene interval for both modalities. Its duration
    is used as the time-co-occurrence proxy and must not exceed ``max_time_delta``.
    ``scoring_method`` is either ``token`` (Jaccard overlap) or ``embedding``
    (sentence-embedding cosine similarity).
    """
    if max_time_delta < 0:
        raise ValueError("max_time_delta must be non-negative")
    if not 0.0 <= min_overlap <= 1.0:
        raise ValueError("min_overlap must be between 0 and 1")
    if scoring_method not in {"token", "embedding"}:
        raise ValueError("scoring_method must be 'token' or 'embedding'")

    candidates = []
    for record in aligned_records:
        try:
            start_time = float(record["start_time"])
            end_time = float(record["end_time"])
            spoken_text = str(record["spoken_text"])
            onscreen_text = str(record["onscreen_text"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Each aligned record needs timestamps and both text fields.") from error

        if end_time < start_time:
            raise ValueError("Aligned record end_time cannot be before start_time.")
        if not spoken_text.strip() or not onscreen_text.strip():
            continue

        if scoring_method == "token":
            score = token_overlap_score(spoken_text, onscreen_text)
        else:
            score = embedding_similarity(
                spoken_text,
                onscreen_text,
                model=embedding_model,
                model_name=embedding_model_name,
            )
        if score >= min_overlap and score > 0:
            candidates.append(
                {
                    "start_time": start_time,
                    "end_time": end_time,
                    "spoken_text": spoken_text,
                    "onscreen_text": onscreen_text,
                    "score": score,
                }
            )

    return sorted(candidates, key=lambda candidate: (-candidate["score"], candidate["start_time"]))
