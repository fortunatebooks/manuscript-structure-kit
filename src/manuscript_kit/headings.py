"""Markdown heading detection, chapter-level inference, and TOC cleanup."""

from __future__ import annotations

import re
from dataclasses import dataclass

CHAPTER_KEYWORDS = {
    "chapter",
    "chapitre",
    "capítulo",
    "capitulo",
    "capitolo",
    "kapitel",
    "prologue",
    "prolog",
    "prólogo",
    "prologo",
    "epilogue",
    "épilogue",
    "epílogo",
    "epilogo",
    "part",
    "parte",
    "partie",
    "book",
    "buch",
    "livre",
    "libro",
}

FRONTMATTER_KEYWORDS = {
    "about the author",
    "acknowledgements",
    "acknowledgments",
    "also by",
    "colophon",
    "contents",
    "copyright",
    "dedication",
    "imprint",
    "table of contents",
    "title page",
    "works by",
}

NUMBER_WORDS = {
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "un",
    "deux",
    "trois",
    "quatre",
    "cinq",
    "sept",
    "huit",
    "neuf",
    "dix",
    "uno",
    "dos",
    "tres",
    "cuatro",
    "cinco",
    "seis",
    "siete",
    "ocho",
    "nueve",
    "dieci",
}

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_ROMAN_RE = re.compile(r"\b[ivxlcdm]+\b", re.IGNORECASE)
_DIGIT_RE = re.compile(r"\b\d+\b")
_TOC_LINE_RE = re.compile(
    r"""
    ^\s*
    (?:[-*+]\s*)?
    (?:\[[^\]]+\]\([^)]*\)|[^\n]{1,120}?)
    (?:\s*(?:\.{2,}|\s{2,}|—+)\s*)
    (?:\d+|[ivxlcdm]+)
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)
_TOC_HEADING_RE = re.compile(r"^#{1,6}\s+(?:contents|table of contents)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class Heading:
    """A Markdown ATX heading found in a manuscript."""

    level: int
    text: str
    line_number: int


def find_markdown_headings(markdown_text: str) -> list[Heading]:
    """Return all Markdown ATX headings with 1-based line numbers."""
    headings: list[Heading] = []
    for line_number, line in enumerate(markdown_text.splitlines(), start=1):
        match = _HEADING_RE.match(line.strip())
        if match:
            headings.append(
                Heading(
                    level=len(match.group(1)),
                    text=match.group(2).strip(),
                    line_number=line_number,
                )
            )
    return headings


def is_chapterlike_heading(text: str) -> bool:
    """Return True when a heading looks like a chapter, part, prologue, or epilogue."""
    normalized = _normalize_label(text)
    if not normalized:
        return False
    if any(keyword in normalized for keyword in CHAPTER_KEYWORDS):
        return True
    if _DIGIT_RE.search(normalized) or _ROMAN_RE.search(normalized):
        return len(normalized) <= 80
    if any(word in normalized.split() for word in NUMBER_WORDS):
        return len(normalized) <= 80
    return False


def is_frontmatter_heading(text: str) -> bool:
    """Return True for common frontmatter/backmatter headings."""
    normalized = _normalize_label(text)
    return any(keyword in normalized for keyword in FRONTMATTER_KEYWORDS)


def detect_chapter_heading_level(markdown_text: str) -> int | None:
    """Infer which Markdown heading level is most likely used for chapters.

    The heuristic scores H1-H3 headings by chapter-like labels, numbering, and
    frequency while discounting frontmatter headings. Returns ``None`` if there
    are no headings at those levels.
    """
    headings = [heading for heading in find_markdown_headings(markdown_text) if heading.level <= 3]
    if not headings:
        return None

    best_level: int | None = None
    best_score = float("-inf")
    for level in (1, 2, 3):
        level_headings = [heading for heading in headings if heading.level == level]
        if not level_headings:
            continue
        score = _score_heading_level(level_headings)
        # Prefer shallower headings on a tie because most Markdown manuscripts use H1/H2 chapters.
        if score > best_score:
            best_level = level
            best_score = score
    return best_level


def normalize_heading_hierarchy(markdown_text: str, chapter_level: int | None = None) -> str:
    """Promote the detected chapter heading level to H1 and adjust descendants.

    Heading levels above the detected chapter level are left alone so title pages
    or document titles are not unexpectedly demoted. Levels below the chapter
    level are shifted upward by the same amount, preserving relative hierarchy.
    """
    detected = chapter_level if chapter_level is not None else detect_chapter_heading_level(markdown_text)
    if not detected or detected == 1:
        return markdown_text
    if detected < 1 or detected > 6:
        raise ValueError("chapter_level must be between 1 and 6")

    shift = detected - 1
    normalized_lines: list[str] = []
    for line in markdown_text.splitlines():
        match = _HEADING_RE.match(line.strip())
        if not match:
            normalized_lines.append(line)
            continue
        level = len(match.group(1))
        title = match.group(2).strip()
        if level >= detected:
            level = max(1, level - shift)
        normalized_lines.append(f"{'#' * level} {title}")
    return "\n".join(normalized_lines) + ("\n" if markdown_text.endswith("\n") else "")


def clean_toc_artifacts(markdown_text: str) -> str:
    """Remove common generated table-of-contents blocks from Markdown.

    The cleaner removes a heading named ``Contents``/``Table of Contents`` and
    following link/page-number lines until body prose or the next real heading.
    It also removes standalone TOC-looking lines elsewhere in the first part of
    a manuscript, where generated TOCs are usually found.
    """
    lines = markdown_text.splitlines()
    output: list[str] = []
    skipping_toc = False
    skipped_any = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        if _TOC_HEADING_RE.match(stripped):
            skipping_toc = True
            skipped_any = True
            continue

        if skipping_toc:
            if not stripped:
                continue
            if _HEADING_RE.match(stripped) and not _TOC_HEADING_RE.match(stripped):
                skipping_toc = False
                output.append(line)
                continue
            if _looks_like_toc_line(stripped):
                skipped_any = True
                continue
            # A short non-heading line after a TOC heading may be a plain TOC entry.
            if len(stripped) <= 120 and index < 200:
                skipped_any = True
                continue
            skipping_toc = False
            output.append(line)
            continue

        if index < 200 and _looks_like_toc_line(stripped):
            skipped_any = True
            continue
        output.append(line)

    text = "\n".join(output)
    if markdown_text.endswith("\n") and not text.endswith("\n"):
        text += "\n"
    return _collapse_excess_blank_lines(text) if skipped_any else markdown_text


def _score_heading_level(headings: list[Heading]) -> float:
    chapterish = sum(1 for heading in headings if is_chapterlike_heading(heading.text))
    frontmatter = sum(1 for heading in headings if is_frontmatter_heading(heading.text))
    short_titles = sum(1 for heading in headings if len(heading.text.strip()) <= 80)
    count = len(headings)
    score = chapterish * 3.0 + short_titles * 0.35 + min(count, 12) * 0.25 - frontmatter * 2.0
    if count >= 5 and chapterish / count >= 0.4:
        score += 3.0
    if count >= 10:
        score += 1.5
    return score


def _looks_like_toc_line(stripped: str) -> bool:
    if not stripped:
        return False
    if _TOC_LINE_RE.match(stripped):
        return True
    return bool(re.match(r"^[-*+]\s+\[[^\]]+\]\(#[^)]+\)\s*$", stripped))


def _normalize_label(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().casefold())


def _collapse_excess_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip() + ("\n" if text.endswith("\n") else "")
