"""Word counting helpers for Markdown and plain text manuscripts."""

from __future__ import annotations

import re

_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")
_LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WORD_RE = re.compile(r"[\w]+(?:['’\-][\w]+)*", re.UNICODE)
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]")


def count_words(text: str) -> int:
    """Count manuscript words while ignoring common Markdown syntax.

    CJK characters are counted as word-like units because whitespace-delimited
    counts dramatically undercount Chinese, Japanese, and Korean manuscripts.
    """
    plain = markdown_to_plain_text(text)
    latin_words = _WORD_RE.findall(_CJK_RE.sub(" ", plain))
    cjk_units = _CJK_RE.findall(plain)
    return len(latin_words) + len(cjk_units)


def markdown_to_plain_text(text: str) -> str:
    """Strip common Markdown markup while preserving readable text."""
    plain = _CODE_FENCE_RE.sub(" ", text)
    plain = _INLINE_CODE_RE.sub(" ", plain)
    plain = _LINK_RE.sub(r"\1", plain)
    plain = _HTML_TAG_RE.sub(" ", plain)
    plain = re.sub(r"^\s{0,3}#{1,6}\s+", "", plain, flags=re.MULTILINE)
    plain = re.sub(r"^\s{0,3}>\s?", "", plain, flags=re.MULTILINE)
    plain = re.sub(r"[*_~#|]", " ", plain)
    plain = re.sub(r"\s+", " ", plain)
    return plain.strip()
