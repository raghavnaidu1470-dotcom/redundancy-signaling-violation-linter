"""OCR text cleaning and garbage filtering utilities."""

from __future__ import annotations

import re


def clean_ocr_text(text: str) -> str:
    """Clean raw OCR text by filtering standalone symbols, noise tokens, and invalid lines.

    Args:
        text: Raw OCR string extracted from a frame.

    Returns:
        Cleaned, human-readable OCR text with normalized whitespace.
    """
    if not text:
        return ""

    cleaned_lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Remove common standalone OCR noise and geometric symbols
        line = re.sub(r"[\~\|\_\\\^\*\<\>\{\}\[\]\=\+\#\$\%\@]+", " ", line)

        # Normalize multiple dashes or bullet approximations
        line = re.sub(r"-{2,}", "-", line)

        tokens = line.split()
        valid_tokens = []
        for tok in tokens:
            cleaned_tok = tok.strip(".,:;!?\"'()[]{}")
            # Filter isolated 1-character non-word artifacts (allow 'a', 'I', or single digits)
            if len(cleaned_tok) == 1 and cleaned_tok.lower() not in {"a", "i"} and not cleaned_tok.isdigit():
                continue
            # Filter tokens that contain zero alphanumeric characters
            if not any(c.isalnum() for c in cleaned_tok):
                continue
            valid_tokens.append(tok)

        if valid_tokens:
            cleaned_line = " ".join(valid_tokens).strip()
            # Require at least one token with 2+ alphanumeric characters
            has_substantive_word = any(len(re.sub(r"[^\w]", "", t)) >= 2 for t in valid_tokens)
            if has_substantive_word and len(cleaned_line) >= 3:
                cleaned_lines.append(cleaned_line)

    result = "\n".join(cleaned_lines).strip()
    return result


def is_valid_slide_text(text: str, min_words: int = 2) -> bool:
    """Check if the text has sufficient density to be treated as legitimate slide content."""
    if not text:
        return False
    words = [w for w in text.split() if any(c.isalpha() for c in w) and len(w) >= 2]
    return len(words) >= min_words
