"""Representative text sampling for long manuscripts."""

from __future__ import annotations

import re
from pathlib import Path

from manuscript_kit.validation import read_text
from manuscript_kit.wordcount import count_words

MAX_WORDS_PER_PARAGRAPH_CHUNK = 800


def extract_book_sample(
    path: str | Path,
    total_words: int = 8000,
    beginning_pct: float = 0.40,
    middle_pct: float = 0.20,
    later_pct: float = 0.40,
    middle_start_position: float = 0.45,
    later_start_position: float = 0.70,
) -> str:
    """Read a manuscript file and extract a beginning/middle/later sample."""
    return extract_text_sample(
        read_text(path),
        total_words=total_words,
        beginning_pct=beginning_pct,
        middle_pct=middle_pct,
        later_pct=later_pct,
        middle_start_position=middle_start_position,
        later_start_position=later_start_position,
    )


def extract_text_sample(
    text: str,
    total_words: int = 8000,
    beginning_pct: float = 0.40,
    middle_pct: float = 0.20,
    later_pct: float = 0.40,
    middle_start_position: float = 0.45,
    later_start_position: float = 0.70,
) -> str:
    """Extract representative text from the beginning, middle, and later manuscript.

    Short manuscripts are returned whole. Long manuscripts are sampled on
    paragraph boundaries and marked with human-readable dividers.
    """
    if total_words <= 0:
        raise ValueError("total_words must be positive")
    pct_total = beginning_pct + middle_pct + later_pct
    if not 0.95 <= pct_total <= 1.05:
        raise ValueError("segment percentages must sum to approximately 1.0")

    paragraphs = _split_into_paragraphs(text)
    if not paragraphs:
        return ""
    chunk_limit = max(200, min(MAX_WORDS_PER_PARAGRAPH_CHUNK, max(1, total_words // 6)))
    paragraphs = _chunk_oversized_paragraphs(paragraphs, max_words_per_chunk=chunk_limit)

    full_word_count = sum(count_words(paragraph) for paragraph in paragraphs)
    if full_word_count <= total_words:
        return text.strip()

    total_paragraphs = len(paragraphs)
    middle_start = _bounded_start(int(total_paragraphs * middle_start_position), total_paragraphs)
    later_start = _bounded_start(int(total_paragraphs * later_start_position), total_paragraphs)
    if total_paragraphs >= 3:
        middle_start = max(1, min(middle_start, total_paragraphs - 2))
        later_start = max(middle_start + 1, min(later_start, total_paragraphs - 1))

    used_signatures: set[str] = set()
    beginning_text, _ = _extract_segment(paragraphs, 0, int(total_words * beginning_pct))
    if signature := _segment_signature(beginning_text):
        used_signatures.add(signature)

    middle_text, _, middle_used = _extract_unique_segment(
        paragraphs, middle_start, int(total_words * middle_pct), used_signatures
    )
    later_text, _, later_used = _extract_unique_segment(
        paragraphs, later_start, int(total_words * later_pct), used_signatures
    )

    return (
        "===== EXTRACT 1 - BEGINNING OF BOOK =====\n\n"
        f"{beginning_text}\n\n"
        f"===== EXTRACT 2 - FROM MIDDLE OF BOOK (around {_percent(middle_used, total_paragraphs)}%) =====\n\n"
        f"{middle_text}\n\n"
        f"===== EXTRACT 3 - FROM LATER IN BOOK (around {_percent(later_used, total_paragraphs)}%) =====\n\n"
        f"{later_text}"
    ).strip()


def _split_into_paragraphs(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n+", normalized)]
    return [paragraph for paragraph in paragraphs if paragraph]


def _chunk_oversized_paragraphs(paragraphs: list[str], max_words_per_chunk: int) -> list[str]:
    chunked: list[str] = []
    for paragraph in paragraphs:
        words = paragraph.split()
        if len(words) <= max_words_per_chunk:
            chunked.append(paragraph)
            continue
        for start in range(0, len(words), max_words_per_chunk):
            chunked.append(" ".join(words[start : start + max_words_per_chunk]))
    return chunked


def _extract_segment(
    paragraphs: list[str], start_index: int, target_words: int, tolerance: float = 0.10
) -> tuple[str, int]:
    if start_index >= len(paragraphs):
        return "", 0
    min_words = max(1, int(target_words * (1 - tolerance)))
    max_words = max(min_words, int(target_words * (1 + tolerance)))
    collected: list[str] = []
    words = 0

    for paragraph in paragraphs[start_index:]:
        paragraph_words = count_words(paragraph)
        potential = words + paragraph_words
        if words >= min_words:
            if potential <= max_words and abs(potential - target_words) < abs(words - target_words):
                collected.append(paragraph)
                words = potential
            break
        collected.append(paragraph)
        words = potential
        if words > max_words:
            break
    return "\n\n".join(collected), words


def _extract_unique_segment(
    paragraphs: list[str], preferred_start: int, target_words: int, used_signatures: set[str]
) -> tuple[str, int, int]:
    starts = [preferred_start]
    for offset in range(1, len(paragraphs)):
        if preferred_start - offset >= 0:
            starts.append(preferred_start - offset)
        if preferred_start + offset < len(paragraphs):
            starts.append(preferred_start + offset)

    for start in starts:
        text, words = _extract_segment(paragraphs, start, target_words)
        signature = _segment_signature(text)
        if signature not in used_signatures:
            if signature:
                used_signatures.add(signature)
            return text, words, start
    text, words = _extract_segment(paragraphs, preferred_start, target_words)
    return text, words, preferred_start


def _segment_signature(text: str) -> str:
    normalized = " ".join(text.split())
    if not normalized:
        return ""
    return f"{len(normalized)}:{normalized[:240]}:{normalized[-240:]}"


def _bounded_start(index: int, total: int) -> int:
    return max(0, min(index, max(0, total - 1)))


def _percent(index: int, total: int) -> int:
    if total <= 1:
        return 0
    return round((index / (total - 1)) * 100)
