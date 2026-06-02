"""Command-line interface for manuscript-structure-kit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from manuscript_kit.headings import (
    clean_toc_artifacts,
    detect_chapter_heading_level,
    find_markdown_headings,
    is_chapterlike_heading,
    normalize_heading_hierarchy,
)
from manuscript_kit.sampling import extract_book_sample
from manuscript_kit.scene_breaks import normalize_scene_breaks
from manuscript_kit.validation import read_text, validate_input_file
from manuscript_kit.wordcount import count_words


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manuscript-kit",
        description="Inspect, normalize, sample, and count long-form manuscript structure.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subcommands.add_parser("inspect", help="Summarize manuscript structure")
    inspect_parser.add_argument("input", help="Input .md, .txt, .docx, or .epub file")

    normalize_parser = subcommands.add_parser("normalize", help="Clean TOCs, headings, and scene breaks")
    normalize_parser.add_argument("input", help="Input .md, .txt, .docx, or .epub file")
    normalize_parser.add_argument("--out", required=True, help="Output Markdown/text path")
    normalize_parser.add_argument("--chapter-level", type=int, help="Heading level to promote to H1")

    sample_parser = subcommands.add_parser("sample", help="Extract representative text sample")
    sample_parser.add_argument("input", help="Input .md, .txt, .docx, or .epub file")
    sample_parser.add_argument("--words", type=int, default=8000, help="Target sample words")
    sample_parser.add_argument("--out", required=True, help="Output text path")

    wordcount_parser = subcommands.add_parser("wordcount", help="Count manuscript words")
    wordcount_parser.add_argument("input", help="Input .md, .txt, .docx, or .epub file")

    chapterize_parser = subcommands.add_parser(
        "chapterize", help="Prefix chapter-like headings with a numbered template"
    )
    chapterize_parser.add_argument("input", help="Input Markdown file")
    chapterize_parser.add_argument("--template", default="Chapter {n}", help="Template containing {n}")
    chapterize_parser.add_argument("--out", required=True, help="Output Markdown path")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "inspect":
            return _inspect(Path(args.input))
        if args.command == "normalize":
            return _normalize(Path(args.input), Path(args.out), args.chapter_level)
        if args.command == "sample":
            sample = extract_book_sample(args.input, total_words=args.words)
            Path(args.out).write_text(sample + "\n", encoding="utf-8")
            return 0
        if args.command == "wordcount":
            print(count_words(read_text(args.input)))
            return 0
        if args.command == "chapterize":
            return _chapterize(Path(args.input), Path(args.out), args.template)
    except Exception as exc:  # noqa: BLE001 - CLI should show concise failures.
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser.error("unknown command")
    return 2


def _inspect(path: Path) -> int:
    validation = validate_input_file(path)
    if not validation.ok:
        raise ValueError(validation.message)
    text = read_text(path)
    headings = find_markdown_headings(text)
    chapter_level = detect_chapter_heading_level(text)
    print(f"Path: {validation.path}")
    print(f"Size: {validation.size_bytes} bytes")
    print(f"Words: {count_words(text)}")
    print(f"Headings: {len(headings)}")
    print(f"Detected chapter level: {chapter_level or 'none'}")
    for level in range(1, 4):
        print(f"H{level}: {sum(1 for heading in headings if heading.level == level)}")
    return 0


def _normalize(input_path: Path, output_path: Path, chapter_level: int | None) -> int:
    text = read_text(input_path)
    text = clean_toc_artifacts(text)
    text = normalize_heading_hierarchy(text, chapter_level=chapter_level)
    text = normalize_scene_breaks(text)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return 0


def _chapterize(input_path: Path, output_path: Path, template: str) -> int:
    text = read_text(input_path)
    level = detect_chapter_heading_level(text)
    if level is None:
        raise ValueError("could not detect chapter headings")
    count = 0
    lines: list[str] = []
    marker = "#" * level
    for line in text.splitlines():
        if line.startswith(f"{marker} ") and is_chapterlike_heading(line.removeprefix(f"{marker} ")):
            count += 1
            title = template.format(n=count)
            lines.append(f"{marker} {title}")
        else:
            lines.append(line)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
