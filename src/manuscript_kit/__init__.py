"""Reusable utilities for long-form manuscript structure cleanup."""

from manuscript_kit.headings import (
    Heading,
    clean_toc_artifacts,
    detect_chapter_heading_level,
    find_markdown_headings,
    is_chapterlike_heading,
    is_frontmatter_heading,
    normalize_heading_hierarchy,
)
from manuscript_kit.sampling import extract_book_sample, extract_text_sample
from manuscript_kit.scene_breaks import is_scene_break, normalize_scene_breaks
from manuscript_kit.validation import FileValidation, validate_input_file
from manuscript_kit.wordcount import count_words

__all__ = [
    "FileValidation",
    "Heading",
    "clean_toc_artifacts",
    "count_words",
    "detect_chapter_heading_level",
    "extract_book_sample",
    "extract_text_sample",
    "find_markdown_headings",
    "is_chapterlike_heading",
    "is_frontmatter_heading",
    "is_scene_break",
    "normalize_heading_hierarchy",
    "normalize_scene_breaks",
    "validate_input_file",
]

__version__ = "0.1.0"
