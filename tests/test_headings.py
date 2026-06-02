from pathlib import Path

from manuscript_kit import (
    clean_toc_artifacts,
    detect_chapter_heading_level,
    find_markdown_headings,
    normalize_heading_hierarchy,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_detects_chapter_heading_level() -> None:
    text = (FIXTURES / "chapter_headings.md").read_text(encoding="utf-8")

    assert detect_chapter_heading_level(text) == 2


def test_normalizes_detected_chapter_level_to_h1() -> None:
    text = (FIXTURES / "chapter_headings.md").read_text(encoding="utf-8")

    normalized = normalize_heading_hierarchy(text)

    assert "# Chapter 1" in normalized
    assert "## A smaller scene" in normalized
    assert "## Chapter 1" not in normalized


def test_finds_markdown_headings_with_line_numbers() -> None:
    headings = find_markdown_headings("# Title\n\n## Chapter 1\n")

    assert headings[0].text == "Title"
    assert headings[0].line_number == 1
    assert headings[1].level == 2


def test_cleans_generated_toc_block() -> None:
    text = (FIXTURES / "generated_toc.md").read_text(encoding="utf-8")

    cleaned = clean_toc_artifacts(text)

    assert "Contents" not in cleaned
    assert "........" not in cleaned
    assert "Actual prose starts here." in cleaned
