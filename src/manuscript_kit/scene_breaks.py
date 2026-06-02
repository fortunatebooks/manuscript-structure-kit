"""Scene-break detection and normalization for Markdown manuscripts."""

from __future__ import annotations

import re

_SCENE_BREAK_PATTERNS = [
    re.compile(r"^\s*\*\s*\*\s*\*\.?\s*$"),
    re.compile(r"^\s*(?:\\\*\s*){3}\.?\s*$"),
    re.compile(r"^\s*\\\*\\\*\\\*\s*$"),
    re.compile(r"^\s*[-_]{3,}\s*$"),
    re.compile(r"^\s*(?:—\s*){3,}\s*$"),
    re.compile(r"^\s*(?:–\s*){3,}\s*$"),
    re.compile(r"^\s*[⁂❦❧✦✧✶✷✸✹✺✻✼✽✾✿]+\s*$"),
]


def is_scene_break(line: str) -> bool:
    """Return True if a line consists only of a scene-break marker."""
    return any(pattern.match(line) for pattern in _SCENE_BREAK_PATTERNS)


def normalize_scene_breaks(markdown_text: str, marker: str = "***") -> str:
    """Normalize ornamental scene breaks and deduplicate adjacent breaks.

    Only standalone marker lines are normalized, so inline Markdown emphasis such
    as ``***very important***`` is preserved.
    """
    lines = markdown_text.split("\n")
    normalized: list[str] = []
    previous_was_break = False

    for line in lines:
        if is_scene_break(line):
            if not previous_was_break:
                normalized.append(marker)
            previous_was_break = True
            continue
        normalized.append(line)
        if line.strip():
            previous_was_break = False

    return "\n".join(normalized)
